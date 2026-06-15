"""Descriptive governance layer: what the policy text looks like, and what changed.

This is the descriptive leg (it says WHAT moved; the causal magnitude is in
analyze_event_study.py). It works from the union (institution-quarter) panel, so
every statistic is on the same outcome the event study uses (the max across the
institution's tracked integrity and AI-guidance pages).

1. Endpoint prevalence: in each institution's last observed quarter, the share
   whose policy addresses AI at all and the share carrying each provision.
2. Baseline-to-endpoint change: the same provisions in the last pre-shock quarter
   versus the last observed quarter, a within-institution delta.
3. Regime typology of the endpoint: Silent / Restrictive-leaning / Procedural-
   leaning / Mixed, by control, Carnegie type, and exposure tercile.

Output: data/results_descriptive.csv (long form: section, group, metric, value).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
PANEL = HERE / "data" / "panel.csv"
OUT = HERE / "data" / "results_descriptive.csv"

RESTRICTIVE = ["prohibition", "detector_surveillance", "misconduct_framing", "sanction"]
PROCEDURAL = ["permitted_use", "disclosure", "appeal", "l2_protection"]
PROVISIONS = RESTRICTIVE + PROCEDURAL


def regime(row):
    if row["ai_addressed"] == 0:
        return "Silent"
    if row["restrictive_idx"] > row["procedural_idx"]:
        return "Restrictive-leaning"
    if row["procedural_idx"] > row["restrictive_idx"]:
        return "Procedural-leaning"
    return "Mixed"


def main():
    p = pd.read_csv(PANEL)
    endpoint = p.sort_values("event_q").groupby("unitid").tail(1).set_index("unitid")
    pre = p[p["event_q"] < 0]
    baseline = pre.sort_values("event_q").groupby("unitid").tail(1).set_index("unitid")

    rows = []

    def add(section, group, metric, value):
        rows.append({"section": section, "group": group, "metric": metric, "value": value})

    n = len(endpoint)
    add("scope", "all", "n_institutions", n)
    add("endpoint", "all", "ai_addressed_rate", round(endpoint["ai_addressed"].mean(), 4))
    for c in PROVISIONS:
        add("endpoint", "all", c + "_rate", round(endpoint[c + "_present"].mean(), 4))
    add("endpoint", "all", "mean_net_restrictiveness",
        round(endpoint["net_restrictiveness"].mean(), 4))
    add("endpoint", "all", "mean_ai_governance_intensity",
        round(endpoint["ai_governance_intensity"].mean(), 4))

    matched = baseline.index.intersection(endpoint.index)
    add("change", "all", "n_with_baseline", len(matched))
    add("change", "all", "ai_addressed_baseline",
        round(baseline.loc[matched, "ai_addressed"].mean(), 4))
    add("change", "all", "ai_addressed_endpoint",
        round(endpoint.loc[matched, "ai_addressed"].mean(), 4))
    for c in PROVISIONS:
        b = baseline.loc[matched, c + "_present"].mean()
        e = endpoint.loc[matched, c + "_present"].mean()
        add("change", "all", c + "_delta", round(e - b, 4))

    endpoint = endpoint.copy()
    endpoint["regime"] = endpoint.apply(regime, axis=1)
    for r, cnt in endpoint["regime"].value_counts().items():
        add("regime", "all", r, int(cnt))
    for dim in ("control", "carnegie"):
        for gval, sub in endpoint.groupby(dim):
            for r, cnt in sub["regime"].value_counts().items():
                add("regime", f"{dim}={gval}", r, int(cnt))
    if endpoint["intl_share"].nunique() >= 3:
        endpoint["exp_tercile"] = pd.qcut(endpoint["intl_share"], 3,
                                          labels=["low", "mid", "high"], duplicates="drop")
        for gval, sub in endpoint.groupby("exp_tercile", observed=True):
            add("regime", f"exposure={gval}", "mean_net_restrictiveness",
                round(sub["net_restrictiveness"].mean(), 4))
            add("regime", f"exposure={gval}", "ai_addressed_rate",
                round(sub["ai_addressed"].mean(), 4))

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Wrote {OUT}  ({len(rows)} rows; {n} institutions)")
    print(f"  endpoint AI-addressed rate: {endpoint['ai_addressed'].mean():.0%}")
    print("  endpoint regimes:", dict(endpoint["regime"].value_counts()))
    print("  endpoint provision prevalence:")
    for c in PROVISIONS:
        print(f"    {c:<22} {endpoint[c + '_present'].mean():.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
