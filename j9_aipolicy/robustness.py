"""Robustness and falsification checks for the AI-policy event study.

(a) Proximity-window sensitivity: re-score every snapshot at windows 200 / 400 /
    800 chars and report how much the endpoint indices move (the lexicon should
    not hinge on the 400-char default).
(b) Leave-one-institution-out of the summary DiD: the exposure x post estimate
    for each primary outcome, recomputed dropping each institution, with min/max.
(c) Alternate exposure coding: high-versus-low exposure tercile (binary) DiD,
    so the result does not depend on the continuous standardization.
(d) Audit export: a random sample of snapshots with their extracted text and the
    codes, for a hand check of the deterministic lexicon (data/audit_sample.csv).

Run after build_panel.py and analyze_event_study.py. Output: data/robustness.csv
(+ data/audit_sample.csv).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import build_panel as bp

HERE = Path(__file__).parent
DATA = HERE / "data"
PANEL = DATA / "panel.csv"
SNAP_INDEX = DATA / "snapshot_index.csv"
OUT = DATA / "robustness.csv"
AUDIT = DATA / "audit_sample.csv"

PRIMARY = ["ai_governance_intensity", "net_restrictiveness"]
RNG = np.random.default_rng(20221130)


def _load_panel():
    p = pd.read_csv(PANEL)
    inst = p.drop_duplicates("unitid")[["unitid", "intl_share"]]
    mu, sd = inst["intl_share"].mean(), inst["intl_share"].std(ddof=0)
    p["exposure"] = (p["intl_share"] - mu) / sd
    p["eq"] = p["event_q"].astype(int)
    p["post"] = (p["eq"] >= 0).astype(int)
    return p


def _did(p, outcome, treat="exposure"):
    m = smf.ols(f"y ~ C(unitid) + C(eq) + {treat}:post",
                data=p.assign(y=p[outcome].astype(float)))
    r = m.fit(cov_type="cluster", cov_kwds={"groups": p["unitid"]})
    t = f"{treat}:post"
    return r.params[t], r.pvalues[t]


def window_sensitivity(rows):
    idx = pd.read_csv(SNAP_INDEX)
    idx = idx[idx["bytes"].notna() & (idx["bytes"] > 0)]
    idx["timestamp"] = idx["timestamp"].astype(str)
    endpoint = idx.sort_values("timestamp").groupby("unitid").tail(1)
    for win in (200, 400, 800):
        vals = {"net_restrictiveness": [], "ai_governance_intensity": []}
        for r in endpoint.itertuples(index=False):
            path = HERE / r.local_path
            if not path.exists():
                continue
            s = bp.score_text(bp.extract_text(path), window=win)
            vals["net_restrictiveness"].append(s["net_restrictiveness"])
            vals["ai_governance_intensity"].append(s["ai_governance_intensity"])
        for metric, v in vals.items():
            rows.append({"check": "window_sensitivity", "param": f"window={win}",
                         "outcome": metric, "value": round(np.mean(v), 4),
                         "extra": f"n={len(v)}"})


def loo(rows, p):
    for outcome in PRIMARY:
        ests = []
        for uid in p["unitid"].unique():
            try:
                b, _ = _did(p[p["unitid"] != uid], outcome)
                ests.append(b)
            except Exception:
                pass
        full, fp = _did(p, outcome)
        rows.append({"check": "leave_one_out", "param": "min/full/max",
                     "outcome": outcome,
                     "value": round(full, 4),
                     "extra": f"min={min(ests):.4f} max={max(ests):.4f} full_p={fp:.3f}"})


def binary_exposure(rows, p):
    inst = p.drop_duplicates("unitid")[["unitid", "intl_share"]].copy()
    inst["terc"] = pd.qcut(inst["intl_share"], 3, labels=[0, 1, 2], duplicates="drop")
    hi_lo = inst[inst["terc"].isin([0, 2])].copy()
    hi_lo["high_exp"] = (hi_lo["terc"] == 2).astype(int)
    q = p.merge(hi_lo[["unitid", "high_exp"]], on="unitid", how="inner")
    for outcome in PRIMARY:
        try:
            b, pv = _did(q, outcome, treat="high_exp")
            rows.append({"check": "binary_exposure_hi_vs_lo", "param": "high_exp:post",
                         "outcome": outcome, "value": round(b, 4),
                         "extra": f"p={pv:.3f} n_inst={q['unitid'].nunique()}"})
        except Exception as e:
            rows.append({"check": "binary_exposure_hi_vs_lo", "param": "high_exp:post",
                         "outcome": outcome, "value": np.nan, "extra": str(e)})


def audit_export(p):
    idx = pd.read_csv(SNAP_INDEX)
    idx = idx[idx["bytes"].notna() & (idx["bytes"] > 0)
              & idx["unitid"].isin(p["unitid"].unique())]
    sample = idx.sample(min(20, len(idx)), random_state=20221130)
    out = []
    for r in sample.itertuples(index=False):
        path = HERE / r.local_path
        if not path.exists():
            continue
        text = bp.extract_text(path)
        s = bp.score_text(text)
        out.append({"institution": r.institution, "timestamp": r.timestamp,
                    "ai_addressed": s["ai_addressed"],
                    "restrictive_idx": s["restrictive_idx"],
                    "procedural_idx": s["procedural_idx"],
                    "net_restrictiveness": s["net_restrictiveness"],
                    "text_excerpt": text[:1200]})
    pd.DataFrame(out).to_csv(AUDIT, index=False)
    print(f"Wrote {AUDIT} ({len(out)} snapshots for hand check)")


def validate_lexicon(p):
    """Face-validity audit: for a random sample of snapshots, record each AI-scoped
    provision that fires with its matched span and surrounding context, so the codes
    can be read against the text. Output: data/audit_spans.csv."""
    idx = pd.read_csv(SNAP_INDEX)
    idx = idx[idx["bytes"].notna() & (idx["bytes"] > 0)
              & idx["unitid"].isin(p["unitid"].unique())]
    sample = idx.sample(min(60, len(idx)), random_state=7)
    out = []
    for r in sample.itertuples(index=False):
        path = HERE / r.local_path
        if not path.exists():
            continue
        text = bp.extract_text(path)
        centers = [(m.start() + m.end()) / 2 for m in bp.AI_TERMS.finditer(text)]
        if not centers:
            continue
        for name, pat in bp.PROVISIONS.items():
            for m in pat.finditer(text):
                c = (m.start() + m.end()) / 2
                if any(abs(c - a) <= bp.WINDOW for a in centers):
                    out.append({"institution": r.institution, "timestamp": r.timestamp,
                                "provision": name, "match": m.group(0),
                                "context": text[max(0, m.start() - 70):m.end() + 70].strip()})
                    break
        if len(out) >= 50:
            break
    pd.DataFrame(out).to_csv(DATA / "audit_spans.csv", index=False)
    print(f"Wrote {DATA / 'audit_spans.csv'} ({len(out)} flagged-provision passages for the face-validity read)")


def wealth_type_controls(rows, p):
    """Is the exposure null just wealth/type collinearity? Re-estimate exposure x post
    while controlling for private x post, R1 x post, and log-enrollment x post."""
    p = p.copy()
    p["priv"] = (p["control"] == "Private").astype(float)
    p["r1"] = (p["carnegie"] == "R1").astype(float)
    p["lne"] = np.log(p["total_enroll"])
    p["lne"] = p["lne"] - p.drop_duplicates("unitid")["lne"].mean()
    p["expXpost"] = p["exposure"] * p["post"]
    for c in ("priv", "r1", "lne"):
        p[c + "Xpost"] = p[c] * p["post"]
    f = "y ~ C(unitid) + C(eq) + expXpost + privXpost + r1Xpost + lneXpost"
    for outcome in PRIMARY + ["restrictive_idx"]:
        r = smf.ols(f, data=p.assign(y=p[outcome].astype(float))).fit(
            cov_type="cluster", cov_kwds={"groups": p["unitid"]})
        ci = r.conf_int().loc["expXpost"]
        rows.append({"check": "wealth_type_controls",
                     "param": "exp x post | +priv/R1/lnEnroll x post", "outcome": outcome,
                     "value": round(r.params["expXpost"], 4),
                     "extra": f"p={r.pvalues['expXpost']:.3f} CI[{ci[0]:.3f},{ci[1]:.3f}]"})


def main():
    p = _load_panel()
    rows = []
    window_sensitivity(rows)
    loo(rows, p)
    binary_exposure(rows, p)
    wealth_type_controls(rows, p)
    validate_lexicon(p)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    audit_export(p)
    print(f"Wrote {OUT}")
    print(pd.DataFrame(rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
