"""Robustness battery for both layers.

RDD (the causal layer):
  - bandwidth sensitivity (the estimate should not swing with the window),
  - local quadratic (polynomial robustness),
  - donut holes (drop schools nearest the cutoff, against boundary ties),
  - placebo cutoffs on the control side (fake lines should show no jump),
  - minimum detectable effect at the primary bandwidth (so a null is a powered null,
    not an underpowered one).

Weight space (the descriptive layer):
  - re-identify at the bottom 3 / 5 / 10 percent and report how the identified set and
    its poverty concentration move with the threshold,
  - the label's poverty concentration versus the school population.

Outputs data/results_robustness.csv.

Run:  python3 robustness.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_rdd import llr

HERE = Path(__file__).parent
PANEL = HERE / "data" / "rdd_panel.csv"
INST = HERE / "data" / "label_instability.csv"
OUT = HERE / "data" / "results_robustness.csv"

OUTCOMES = ["got_funds", "award", "next_score"]


def rdd_robustness(rows):
    # primary stratum = elementary/middle (homogeneous running variable; analyze_rdd.py)
    df = pd.read_csv(PANEL, dtype={"ncessch": str})
    df = df[df["is_high"] == 0].copy()
    h0 = 1.0
    for oc in OUTCOMES:
        # bandwidth sweep
        for h in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
            r = llr(df, oc, h)
            rows.append((f"rdd:{oc}", f"bandwidth h={h}", "tau", r["tau"]))
            rows.append((f"rdd:{oc}", f"bandwidth h={h}", "se", r["se"]))
        # local quadratic
        r = llr(df, oc, h0, poly=2)
        rows.append((f"rdd:{oc}", "local quadratic h=1.0", "tau", r["tau"]))
        rows.append((f"rdd:{oc}", "local quadratic h=1.0", "se", r["se"]))
        # donut
        for dn in (0.1, 0.2):
            r = llr(df, oc, h0, donut=dn)
            rows.append((f"rdd:{oc}", f"donut {dn} h=1.0", "tau", r["tau"]))
            rows.append((f"rdd:{oc}", f"donut {dn} h=1.0", "se", r["se"]))
        # minimum detectable effect (2.8 * SE ~ 80% power, 5% two-sided)
        r = llr(df, oc, h0)
        rows.append((f"rdd:{oc}", "h=1.0", "mde_80pct", 2.8 * r["se"]))

    # placebo cutoffs on the control side (recenter at fake lines, no real treatment)
    ctrl = df[df["running"] > 0].copy()
    for q in (0.25, 0.5, 0.75):
        fake = ctrl["running"].quantile(q)
        p = ctrl.copy()
        p["running"] = p["running"] - fake
        for oc in ("got_funds", "next_score"):
            r = llr(p, oc, 1.0)
            rows.append((f"placebo:{oc}", f"fake cutoff q={q}", "tau", r["tau"]))
            rows.append((f"placebo:{oc}", f"fake cutoff q={q}", "se", r["se"]))


def weight_threshold_robustness(rows):
    d = pd.read_csv(INST, dtype={"ncessch": str})
    pop_pov = d["econ_disadv_share"].mean()
    rows.append(("weight:population", "all Title I", "mean_poverty", pop_pov))
    for thr in (0.03, 0.05, 0.10):
        ident = d["pct_within_state"] <= thr
        sub = d[ident]
        rows.append((f"weight:bottom_{int(thr*100)}pct", "threshold", "n_identified", int(ident.sum())))
        rows.append((f"weight:bottom_{int(thr*100)}pct", "threshold", "mean_poverty_identified", sub["econ_disadv_share"].mean()))
        rows.append((f"weight:bottom_{int(thr*100)}pct", "threshold", "poverty_concentration_ratio", sub["econ_disadv_share"].mean() / pop_pov))
    # how unstable the baseline label is overall
    base = d[d["identified_baseline"] == 1]
    rows.append(("weight:instability", "baseline-identified", "flip_rate", base["flip"].mean()))
    rows.append(("weight:instability", "baseline-identified", "mean_identify_freq", base["identify_freq"].mean()))


def main():
    rows = []
    rdd_robustness(rows)
    weight_threshold_robustness(rows)
    out = pd.DataFrame(rows, columns=["analysis", "specification", "statistic", "value"])
    out.to_csv(OUT, index=False)

    # console summary of the RDD stability + placebo
    print("RDD bandwidth stability (tau):")
    for oc in OUTCOMES:
        taus = out[(out.analysis == f"rdd:{oc}") &
                   out.specification.str.startswith("bandwidth") &
                   (out.statistic == "tau")]["value"]
        print(f"  {oc:<12} range [{taus.min():+.3g}, {taus.max():+.3g}]")
    pl = out[out.analysis.str.startswith("placebo")].pivot_table(
        index=["analysis", "specification"], columns="statistic", values="value")
    pl["t"] = (pl["tau"] / pl["se"]).abs()
    print(f"placebo cutoffs: max |t| = {pl['t'].max():.2f} (should be < 1.96)")
    print("weight-threshold poverty concentration (identified / population):")
    for thr in (3, 5, 10):
        v = out[(out.analysis == f"weight:bottom_{thr}pct") &
                (out.statistic == "poverty_concentration_ratio")]["value"]
        if len(v):
            print(f"  bottom {thr}%: {v.iloc[0]:.2f}x")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
