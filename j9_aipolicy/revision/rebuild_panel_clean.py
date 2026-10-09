"""Rebuild the US institution-by-quarter panel (same layout as PIPE/data/panel.csv) from the
re-scored snapshots under several score variants, then run the pipeline's event study on each.
Variants: raw (must replicate data/panel.csv), clean, clean_strict, clean_matched (US seed pages
only), clean_strict_matched_junkdropped. Writes panel_<variant>.csv, results_event_study_<variant>.csv,
and event_study_variants.csv (the summary DiD rows side by side)."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import re, sys, subprocess
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B
SHOCK = pd.Timestamp("2022-11-30")
PROV = list(B.PROVISIONS.keys()); RESTR, PROC = B.RESTRICTIVE, B.PROCEDURAL
sc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
sc = sc[sc.pipeline == "US"].copy()
sc["ts"] = pd.to_datetime(sc["timestamp"], format="%Y%m%d%H%M%S")
sc["page_key"] = sc["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
frame = pd.read_csv(PIPE / "data/sample_frame.csv", dtype={"unitid": str})
cov = pd.read_csv(PIPE / "data/coverage.csv", dtype={"unitid": str}); cov = cov[cov.n_captures > 0].copy()
cov["first_ts"] = pd.to_datetime(cov["first_capture"].astype(str), format="%Y%m%d%H%M%S", errors="coerce")
cov["last_ts"] = pd.to_datetime(cov["last_capture"].astype(str), format="%Y%m%d%H%M%S", errors="coerce")
inst_first = cov.groupby("unitid")["first_ts"].min(); inst_last = cov.groupby("unitid")["last_ts"].max(); inst_haspost = cov.groupby("unitid")["has_post"].max()
QENDS = pd.period_range("2021Q1", "2026Q1", freq="Q").to_timestamp(how="end").normalize()
matched = set(map(tuple, pd.read_csv(AN / "matched_pages_us.csv", dtype=str).values))
junk = set(map(tuple, pd.read_csv(AN / "junk_pages.csv", dtype=str).values))
policy = set(map(tuple, pd.read_csv(AN / "policy_pages.csv", dtype=str).values))
matched_policy = set(map(tuple, pd.read_csv(AN / "matched_policy_pages_us.csv", dtype=str).values))
def event_quarter(ts): return (ts.year - 2022) * 4 + (ts.quarter - 4)

samples = pd.read_csv(AN / "panel_samples.csv", dtype={"unitid": str})
UIDS_ORIG = sorted(samples[(samples.in_original_filter == 1) & (samples.system == "US")].unitid)
UIDS_FIXED = sorted(samples[(samples.in_corrected_filter == 1) & (samples.system == "US")].unitid)

def build(snaps, suffix, aa_col, nai_col, len_col, uids):
    pres = [f"{p}_present{suffix}" for p in PROV]
    carry = [aa_col, nai_col, len_col] + pres
    rows = []
    for uid in uids:
        grid = QENDS
        series = []
        for pg, sp in snaps[snaps["unitid"] == uid].groupby("page_key"):
            sp = sp.sort_values("ts")
            asof = pd.merge_asof(pd.DataFrame({"ts": grid}), sp[["ts"] + carry], on="ts", direction="backward")
            asof[carry] = asof[carry].fillna(0); series.append(asof)
        if not series:  # institution kept in the sample but with no page under this rule: zeros on the grid
            series = [pd.DataFrame({"ts": grid, **{c: 0 for c in carry}})]
        agg = pd.concat(series).groupby("ts", as_index=False)[carry].max()
        agg = agg.rename(columns={aa_col: "ai_addressed", nai_col: "n_ai_terms", len_col: "text_len", **{f"{p}_present{suffix}": f"{p}_present" for p in PROV}})
        agg["restrictive_idx"] = agg[[f"{p}_present" for p in RESTR]].sum(axis=1)
        agg["procedural_idx"] = agg[[f"{p}_present" for p in PROC]].sum(axis=1)
        agg["net_restrictiveness"] = agg["restrictive_idx"] - agg["procedural_idx"]
        agg["ai_governance_intensity"] = agg["restrictive_idx"] + agg["procedural_idx"]
        agg["unitid"] = uid; agg["quarter"] = agg["ts"].dt.to_period("Q").astype(str)
        agg["event_q"] = agg["ts"].apply(event_quarter); agg["post"] = (agg["event_q"] >= 0).astype(int)
        rows.append(agg)
    panel = pd.concat(rows, ignore_index=True)
    meta = frame[["institution", "state", "control", "carnegie", "unitid", "intl_share", "total_enroll"]]
    panel = panel.merge(meta, on="unitid", how="left").drop(columns=["ts"]).sort_values(["unitid", "event_q"])
    front = ["institution", "unitid", "state", "control", "carnegie", "quarter", "event_q", "post", "intl_share", "total_enroll"]
    return panel[front + [c for c in panel.columns if c not in front]]

variants = {
    "raw": (sc, "_raw", "ai_addressed_raw", "n_ai_terms_raw", "words_raw", UIDS_ORIG),
    "raw_corrected_filter": (sc, "_raw", "ai_addressed_raw", "n_ai_terms_raw", "words_raw", UIDS_FIXED),
    "clean": (sc, "_clean", "ai_addressed_clean", "n_ai_terms_clean", "words_clean", UIDS_FIXED),
    "clean_strict": (sc, "_clean_strict", "ai_addressed_clean_strict", "n_ai_terms_clean_strict", "words_clean", UIDS_FIXED),
    "clean_strict_policy_pages": (sc[[(u, k) in policy for u, k in zip(sc.unitid, sc.page_key)]], "_clean_strict", "ai_addressed_clean_strict", "n_ai_terms_clean_strict", "words_clean", UIDS_FIXED),
    "clean_strict_policy_matched": (sc[[(u, k) in matched_policy for u, k in zip(sc.unitid, sc.page_key)]], "_clean_strict", "ai_addressed_clean_strict", "n_ai_terms_clean_strict", "words_clean", UIDS_FIXED),
}
# a patched copy of the pipeline's event-study script that takes the panel path from argv
src = (PIPE / "analyze_event_study.py").read_text()
src = src.replace('PANEL = HERE / "data" / "panel.csv"', 'PANEL = Path(sys.argv[1])').replace('OUT = HERE / "data" / "results_event_study.csv"', 'OUT = Path(sys.argv[2])')
(AN / "event_study_runner.py").write_text(src)
summary = []
for name, (snaps, suf, aa, nai, ln, uids) in variants.items():
    panel = build(snaps, suf, aa, nai, ln, uids)
    out = AN / f"panel_{name}.csv"; panel.to_csv(out, index=False)
    if name == "raw":
        comm = pd.read_csv(PIPE / "data/panel.csv", dtype={"unitid": str})
        m = comm.merge(panel, on=["unitid", "event_q"], suffixes=("_c", "_n"))
        diffs = {c: int((m[f"{c}_c"] != m[f"{c}_n"]).sum()) for c in ["ai_addressed", "restrictive_idx", "procedural_idx", "net_restrictiveness"]}
        print(f"raw replication vs committed panel.csv: rows committed {len(comm)}, rebuilt {len(panel)}, merged {len(m)}, mismatches {diffs}", flush=True)
    res = AN / f"results_event_study_{name}.csv"
    r = subprocess.run(["/usr/bin/python3", str(AN / "event_study_runner.py"), str(out), str(res)], capture_output=True, text=True, cwd=str(PIPE))
    print(f"--- {name}: {panel.unitid.nunique()} institutions, {len(panel)} rows\n{r.stdout.strip()[:1500]}\n{r.stderr.strip()[-600:]}", flush=True)
    if res.exists():
        d = pd.read_csv(res)
        for kind in ("did_exposure_x_post", "placebo_2021Q4"):
            for row in d[d.kind == kind].itertuples(index=False):
                summary.append({"variant": name, "n_inst": panel.unitid.nunique(), "outcome": row.outcome, "kind": kind, "coef": round(row.coef, 3), "se": round(row.se, 3), "ci_lo": round(row.ci_lo, 3), "ci_hi": round(row.ci_hi, 3), "p": round(row.pval, 3)})
s = pd.DataFrame(summary); s.to_csv(AN / "event_study_variants.csv", index=False)
pd.set_option("display.width", 200)
print(s[s.kind == "did_exposure_x_post"].to_string(index=False))
