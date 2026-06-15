"""Manuscript tables from the committed results CSVs -> data/table_*.csv.

  table_gradient   - identification prevalence and label instability by poverty decile
  table_rdd        - RDD estimates at the cutoff (first stage, outcomes, by poverty)
  table_robustness - RDD bandwidth/polynomial/donut/placebo summary

Run:  python3 make_tables.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
D = HERE / "data"


def table_gradient():
    d = pd.read_csv(D / "label_instability.csv")
    by = d.groupby("poverty_decile").agg(
        schools=("identified_baseline", "size"),
        mean_poverty=("econ_disadv_share", "mean"),
        identified_pct=("identified_baseline", lambda s: 100 * s.mean()),
        ever_flip_pct=("flip", lambda s: 100 * s.mean()),
    ).round(2).reset_index()
    by.to_csv(D / "table_gradient.csv", index=False)
    return by


def table_rdd():
    # primary specification = elementary/middle stratum, per state (each state has its
    # own running-variable scale and bandwidth).
    r = pd.read_csv(D / "results_rdd.csv")
    keep = r[r["specification"] == "elem_middle primary"].pivot_table(
        index=["state", "outcome"], columns="statistic", values="value")
    cols = [c for c in ["tau", "se", "t", "n", "n_treated_in_window", "bandwidth"]
            if c in keep.columns]
    keep = keep[cols].dropna(subset=["tau"]).round(4).reset_index()
    # the first-stage treat jump is meaningful only where treatment is the official flag;
    # drop it for reconstructed-rule states (sharp by construction).
    design = pd.read_csv(D / "rdd_panel.csv").drop_duplicates("state").set_index("state")["design"]
    recon = set(design[design == "reconstructed_rule"].index)
    keep = keep[~((keep["outcome"] == "treat") & keep["state"].isin(recon))]
    keep.to_csv(D / "table_rdd.csv", index=False)
    return keep


def table_robustness():
    r = pd.read_csv(D / "results_robustness.csv")
    rdd = r[r["analysis"].str.startswith("rdd:")].pivot_table(
        index=["analysis", "specification"], columns="statistic", values="value")
    rdd = rdd.round(4).reset_index()
    rdd.to_csv(D / "table_robustness.csv", index=False)
    return rdd


def main():
    g = table_gradient()
    print("table_gradient.csv:")
    print(g.to_string(index=False))
    print("\ntable_rdd.csv:")
    print(table_rdd().to_string(index=False))
    print("\ntable_robustness.csv: written")
    table_robustness()
    print(f"\n-> {D}/table_*.csv")


if __name__ == "__main__":
    main()
