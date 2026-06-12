"""
Extrapolation-sensitivity check for the H_s stipend series (J1).

build_matrix.py fills institution-year stipend cells from phdstipends.com
reports where available and otherwise extrapolates from the 2019 baseline at a
fixed 3% annual rate. This script reports (a) the share of US cohort cells that
are extrapolated rather than observed, and (b) the cohort stipend means and
2019->2025 growth recomputed on observed cells only, so the manuscript can
state that the headline growth figure is not an artefact of the 3% fill rule.

Descriptive only; no model is estimated. Inputs: phd_stipends.csv (raw report
dump), institutions_config.json, governance_matrix.csv. Output:
stipend_sensitivity.csv plus a printed summary.
"""

import json

import numpy as np
import pandas as pd

YEARS = list(range(2019, 2026))

# Mirrors STIPEND_NAME_MAP in build_matrix.py exactly.
STIPEND_NAME_MAP = {
    "Stanford University": ["stanford"],
    "Harvard University": ["harvard"],
    "Massachusetts Institute of Technology": ["mit", "massachusetts institute of technology"],
    "California Institute of Technology": ["caltech", "california institute of technology"],
    "Princeton University": ["princeton"],
    "Yale University": ["yale"],
    "Columbia University": ["columbia university"],
    "University of Chicago": ["university of chicago"],
    "University of Pennsylvania": ["university of pennsylvania"],
    "Cornell University": ["cornell"],
    "Johns Hopkins University": ["johns hopkins"],
    "Duke University": ["duke"],
    "Northwestern University": ["northwestern university"],
    "University of Michigan": ["university of michigan"],
    "University of Texas at Austin": ["university of texas - austin", "university of texas at austin"],
    "University of Washington": ["university of washington"],
    "University of Illinois Urbana-Champaign": ["university of illinois", "uiuc"],
    "Ohio State University": ["ohio state"],
    "Penn State University": ["penn state", "pennsylvania state"],
    "University of California, Berkeley": ["university of california - berkeley", "uc berkeley"],
    "University of California, Los Angeles": ["university of california - los angeles", "ucla"],
    "University of California, San Diego": ["university of california - san diego", "ucsd"],
}


def match_institution(uni_raw):
    uni_raw = str(uni_raw).lower()
    for inst_name, keywords in STIPEND_NAME_MAP.items():
        if any(kw in uni_raw for kw in keywords):
            return inst_name
    return None


def main():
    reports = pd.read_csv("phd_stipends.csv")
    reports["institution"] = reports["university"].map(match_institution)
    reports["year"] = pd.to_numeric(
        reports["academic_year"].astype(str).str.split("-").str[0], errors="coerce"
    )
    reports["pay"] = pd.to_numeric(reports["overall_pay"], errors="coerce")
    obs = reports.dropna(subset=["institution", "year", "pay"])
    obs = obs[(obs["pay"] > 0) & obs["year"].isin(YEARS)]

    observed = (
        obs.groupby(["institution", "year"])["pay"]
        .agg(["mean", "size"])
        .rename(columns={"mean": "observed_mean", "size": "n_reports"})
        .reset_index()
    )

    cfg = json.load(open("institutions_config.json"))["institutions"]
    us = [c["name"] for c in cfg if c["country"] == "US"]
    grid = pd.MultiIndex.from_product([us, YEARS], names=["institution", "year"]).to_frame(index=False)
    grid = grid.merge(observed, on=["institution", "year"], how="left")
    grid["extrapolated"] = grid["observed_mean"].isna()

    matrix = pd.read_csv("governance_matrix.csv")
    matrix = matrix[matrix["country"] == "US"][["institution", "time_period", "H_s"]]
    grid = grid.merge(matrix, left_on=["institution", "year"], right_on=["institution", "time_period"])

    share_extrap = grid["extrapolated"].mean()
    by_year = grid.groupby("year").agg(
        matrix_mean=("H_s", "mean"),
        observed_mean=("observed_mean", "mean"),
        n_observed_cells=("extrapolated", lambda x: int((~x).sum())),
    )
    g_matrix = matrix_growth = by_year.loc[2025, "matrix_mean"] / by_year.loc[2019, "matrix_mean"] - 1
    g_obs = by_year.loc[2025, "observed_mean"] / by_year.loc[2019, "observed_mean"] - 1

    # Balanced observed-only growth: institutions observed in both endpoint years.
    both = grid.pivot(index="institution", columns="year", values="observed_mean")[[2019, 2025]].dropna()
    g_balanced = both[2025].mean() / both[2019].mean() - 1

    grid.drop(columns=["time_period"]).to_csv("stipend_sensitivity.csv", index=False)

    print(f"US cohort cells: {len(grid)} ({len(us)} institutions x {len(YEARS)} years)")
    print(f"Extrapolated cells: {int(grid['extrapolated'].sum())} ({share_extrap:.1%})")
    print(by_year.round(0))
    print(f"2019->2025 growth, matrix series (with 3% fill): {g_matrix:.1%}")
    print(f"2019->2025 growth, observed cells only:          {g_obs:.1%}")
    print(f"2019->2025 growth, balanced observed panel (n={len(both)}): {g_balanced:.1%}")


if __name__ == "__main__":
    main()
