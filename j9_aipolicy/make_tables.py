"""Tables for the AI-policy event study (written to data/table_*.csv).

  table_1: sample description by stratum (control x Carnegie) - institutions,
           mean exposure (nonresident-alien share), snapshots, pre/post coverage.
  table_2: event-study DiD summary - per outcome, the exposure x post estimate
           with clustered SE, the joint pre-trend test, and the placebo.
  table_3: descriptive governance - endpoint provision prevalence and the
           baseline-to-endpoint change.

Run after build_panel.py, analyze_event_study.py, analyze_descriptive.py.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"


def table_1():
    frame = pd.read_csv(DATA / "sample_frame.csv")
    panel = pd.read_csv(DATA / "panel.csv")
    idx = pd.read_csv(DATA / "snapshot_index.csv")
    idx = idx[idx["bytes"].notna() & (idx["bytes"] > 0)]
    kept = set(panel["unitid"].unique())
    frame = frame[frame["unitid"].isin(kept)].copy()
    snap_n = idx.groupby("unitid").size()
    pre = idx[idx["timestamp"].astype(str) < "20221130000000"].groupby("unitid").size()
    rows = []
    for (ctrl, carn), g in frame.groupby(["control", "carnegie"]):
        uids = g["unitid"]
        rows.append({
            "control": ctrl, "carnegie": carn, "n_institutions": len(g),
            "mean_intl_share": round(g["intl_share"].mean(), 4),
            "mean_snapshots": round(snap_n.reindex(uids).mean(), 1),
            "mean_pre_snapshots": round(pre.reindex(uids).fillna(0).mean(), 1),
        })
    out = pd.DataFrame(rows).sort_values(["control", "carnegie"])
    total = {"control": "ALL", "carnegie": "",
             "n_institutions": len(frame),
             "mean_intl_share": round(frame["intl_share"].mean(), 4),
             "mean_snapshots": round(snap_n.reindex(frame["unitid"]).mean(), 1),
             "mean_pre_snapshots": round(pre.reindex(frame["unitid"]).fillna(0).mean(), 1)}
    out = pd.concat([out, pd.DataFrame([total])], ignore_index=True)
    out.to_csv(DATA / "table_1.csv", index=False)
    return out


def table_2():
    es = pd.read_csv(DATA / "results_event_study.csv")
    rows = []
    for outcome, g in es.groupby("outcome"):
        did = g[g["kind"] == "did_exposure_x_post"]
        late = g[(g["kind"] == "event_bin") & (g["event_q"] == 6)]  # q6-8 differential
        pl = g[g["kind"] == "placebo_2021Q4"]
        rows.append({
            "outcome": outcome,
            "did_coef": round(did["coef"].iloc[0], 4) if len(did) else np.nan,
            "did_se": round(did["se"].iloc[0], 4) if len(did) else np.nan,
            "did_p": round(did["pval"].iloc[0], 4) if len(did) else np.nan,
            "late_q6_8_coef": round(late["coef"].iloc[0], 4) if len(late) else np.nan,
            "late_q6_8_p": round(late["pval"].iloc[0], 4) if len(late) else np.nan,
            "placebo_coef": round(pl["coef"].iloc[0], 4) if len(pl) else np.nan,
            "placebo_p": round(pl["pval"].iloc[0], 4) if len(pl) else np.nan,
        })
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "table_2.csv", index=False)
    return out


def table_3():
    d = pd.read_csv(DATA / "results_descriptive.csv")
    end = d[d["section"] == "endpoint"].set_index("metric")["value"]
    chg = d[(d["section"] == "change")].set_index("metric")["value"]
    provisions = ["prohibition", "detector_surveillance", "misconduct_framing",
                  "sanction", "permitted_use", "disclosure", "appeal", "l2_protection"]
    rows = [{"metric": "ai_addressed",
             "endpoint_rate": end.get("ai_addressed_rate", np.nan),
             "baseline_to_endpoint_delta": chg.get("ai_addressed_endpoint", np.nan)
             - chg.get("ai_addressed_baseline", np.nan)
             if "ai_addressed_endpoint" in chg.index else np.nan}]
    for c in provisions:
        rows.append({"metric": c,
                     "endpoint_rate": end.get(c + "_rate", np.nan),
                     "baseline_to_endpoint_delta": chg.get(c + "_delta", np.nan)})
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "table_3.csv", index=False)
    return out


def main():
    t1 = table_1(); print("table_1 (sample by stratum):\n", t1.to_string(index=False), "\n")
    t2 = table_2(); print("table_2 (event-study DiD):\n", t2.to_string(index=False), "\n")
    t3 = table_3(); print("table_3 (descriptive governance):\n", t3.to_string(index=False))
    print("\nWrote data/table_{1,2,3}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
