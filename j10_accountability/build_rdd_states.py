"""Per-state running-variable panel for the regression-discontinuity layer.

A state enters the RDD only when it publishes a single continuous accountability
index per school, the official identification flag, and a downstream outcome. Each
state is a spec in STATES below: the public data resource(s), the column mapping, and
the cutoff convention. The first wired state is Washington, whose School Improvement
Framework (WSIF) publishes a continuous composite score (`_YYYY_score`), the official
annual identification, and a Title I flag; the OSPI "1003 Funds" report card gives the
school-improvement funding outcome. Data come from the state open-data (Socrata)
portal, cached under data/raw/rdd/.

The reconstructed national rule (weight_space.py) shows the label is formula-made; this
layer asks what crossing a state's *own* identification line does, using the state's own
continuous index as the running variable. NCES ids are crosswalked in so the poverty
measure from indicators.csv (econ_disadv_share) can moderate the effect.

Output: data/rdd_panel.csv (one row per state x school).

Run:  python3 build_rdd_states.py            # all wired states
      python3 build_rdd_states.py --states WA
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw" / "rdd"
FRAME = HERE / "data" / "school_frame.csv"
IND = HERE / "data" / "indicators.csv"
OUT = HERE / "data" / "rdd_panel.csv"

# ---- per-state RDD specs ---------------------------------------------------
# Each Socrata resource is data.<state>.gov/resource/<id>.json . The treatment is the
# state's score-based comprehensive (CSI) identification; the cutoff is read from the
# data as the score boundary between identified and not (build_panel_WA).
STATES = {
    "WA": {
        "domain": "data.wa.gov",
        "wsif_id": "gvbz-svet",      # WSIF 2023 Run: _2023_score, _2023_annual_identification, _2023_titlei
        "wsif_next_id": "8v2t-vz3j", # WSIF 2024 Annual: _2024_score (next-cycle outcome)
        "funds_id": "wyhw-h6xs",     # Report Card 1003 Funds 2023-24 (post-identification funding)
        "year": "2023",
        "next_year": "2024",
    },
}


def socrata(domain, rid, select=None, where=None, limit=60000):
    url = f"https://{domain}/resource/{rid}.json?$limit={limit}"
    if select:
        url += "&$select=" + select.replace(" ", "%20")
    if where:
        url += "&$where=" + where.replace(" ", "%20")
    cache = RAW / f"{domain}_{rid}.json"
    if cache.exists():
        return pd.DataFrame(json.loads(cache.read_text()))
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                rows = json.loads(r.read().decode())
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows))
    return pd.DataFrame(rows)


def crosswalk_wa(frame):
    """NCES ncessch <-> WA WSIF school_code via the CCD state school id (seasch)."""
    wa = frame[frame["state"] == "WA"].copy()
    wa["school_code"] = wa["seasch"].astype(str).str.split("-").str[-1]
    return wa[["ncessch", "school_code", "enrollment", "is_high"]]


def build_panel_WA(spec, frame, ind):
    y, ny = spec["year"], spec["next_year"]
    w = socrata(spec["domain"], spec["wsif_id"], where=f"student_group='All Students'")
    w = w.copy()
    w["score"] = pd.to_numeric(w[f"_{y}_score"], errors="coerce")
    w["ident"] = w[f"_{y}_annual_identification"].astype(str)
    w["titlei"] = w.get(f"_{y}_titlei", False)
    w["grad_rate"] = pd.to_numeric(w.get("grad_fouryear_rate"), errors="coerce")
    w = w.dropna(subset=["score"])

    # treatment = score-based comprehensive (CSI). The LowGrad / opt-out comprehensive
    # paths are a separate rule, not the score cutoff, so they are dropped to keep the
    # running-variable design sharp.
    pure_csi = w["ident"].str.fullmatch(r"Support Tier 3: Comprehensive")
    lowgrad = w["ident"].str.contains("LowGrad", na=False)
    w = w[~lowgrad].copy()
    w["treat"] = pure_csi[~lowgrad].astype(int).values

    # cutoff: the score where identification crosses from majority-treated to
    # majority-control. The lowest-5% rule leaves ties at the threshold score, so the
    # boundary is taken at the midpoint of the two adjacent distinct scores that bracket
    # the 0.5 treat-rate crossing (a single max/min would collapse on the tie).
    rate = w.groupby("score")["treat"].mean().sort_index()
    treated_scores = rate.index[rate >= 0.5]
    control_scores = rate.index[rate < 0.5]
    lo = treated_scores.max()                       # highest majority-treated score
    hi = control_scores[control_scores > lo].min()  # next majority-control score
    c = 0.5 * (lo + hi)
    w["running"] = w["score"] - c
    w["cutoff"] = c
    # sharpness: share of schools whose treatment matches the score rule (score < c)
    sharp = float((w["treat"] == (w["score"] < c).astype(int)).mean())

    # next-cycle score (achievement-consequence outcome)
    nxt = socrata(spec["domain"], spec["wsif_next_id"],
                  where="student_group='All Students'")
    nxt = nxt[["school_code", f"_{ny}_score"]].copy()
    nxt["next_score"] = pd.to_numeric(nxt[f"_{ny}_score"], errors="coerce")

    # 1003 improvement funding (funding-consequence outcome)
    f1003 = socrata(spec["domain"], spec["funds_id"])
    f1003 = f1003[["school_code", "_1003_award"]].copy()
    f1003["award"] = pd.to_numeric(f1003["_1003_award"], errors="coerce").fillna(0)
    f1003 = f1003.groupby("school_code", as_index=False)["award"].sum()
    f1003["got_funds"] = (f1003["award"] > 0).astype(int)

    # crosswalk to NCES + poverty
    cw = crosswalk_wa(frame)
    pov = ind[["ncessch", "econ_disadv_share", "achievement"]]
    w["school_code"] = w["school_code"].astype(str)
    panel = (w.merge(nxt, on="school_code", how="left")
               .merge(f1003[["school_code", "award", "got_funds"]], on="school_code", how="left")
               .merge(cw, on="school_code", how="left")
               .merge(pov, on="ncessch", how="left"))
    panel["got_funds"] = panel["got_funds"].fillna(0).astype(int)
    panel["award"] = panel["award"].fillna(0.0)
    panel["state"] = "WA"
    panel["sharpness"] = sharp
    keep = ["state", "ncessch", "school_code", "school_name", "score", "running",
            "cutoff", "treat", "titlei", "grad_rate", "econ_disadv_share",
            "achievement", "enrollment", "is_high", "next_score", "award",
            "got_funds", "sharpness"]
    return panel[[c for c in keep if c in panel.columns]]


BUILDERS = {"WA": build_panel_WA}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", nargs="*", default=list(STATES))
    args = ap.parse_args()
    frame = pd.read_csv(FRAME, dtype={"ncessch": str, "seasch": str})
    ind = pd.read_csv(IND, dtype={"ncessch": str})

    panels = []
    for st in args.states:
        st = st.upper()
        panel = BUILDERS[st](STATES[st], frame, ind)
        panels.append(panel)
        n, t = len(panel), int(panel["treat"].sum())
        print(f"  {st}: {n} schools, {t} identified (CSI), "
              f"sharpness {panel['sharpness'].iloc[0]:.3f}, cutoff "
              f"{panel['cutoff'].iloc[0]:.3f}", file=sys.stderr)

    out = pd.concat(panels, ignore_index=True)
    out.to_csv(OUT, index=False)
    miss = out["econ_disadv_share"].isna().mean()
    print(f"\nrdd_panel.csv: {len(out)} schools across {out['state'].nunique()} state(s); "
          f"poverty merged for {1-miss:.0%} -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
