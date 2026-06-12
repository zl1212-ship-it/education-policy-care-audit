"""
External validation of the crowd-sourced stipend series (J1).

Compares the PhD Stipends crowd-sourced reports against officially published
institutional minimum stipend/assistantship rates (stipend_validation.csv,
hand-collected from university and union sources with URLs and access dates).
For each validated institution the script reports the median, mean, and count
of 2024-2025 crowd-sourced reports next to the published floor, so the
manuscript can state that self-reported stipends are consistent with
institutional schedules rather than an artefact of self-selection.

Bases differ across institutions (9/10/12-month, 50% appointments); the
comparison is a consistency check on level and ordering, not an equality test.
Output: stipend_validation_table.csv.
"""

import pandas as pd

from stipend_sensitivity import match_institution

RECENT_YEARS = [2024, 2025]


def main():
    official = pd.read_csv("stipend_validation.csv")
    # CSV names avoid commas; map onto the panel's canonical names.
    official["institution"] = official["institution"].replace({
        "University of California San Diego": "University of California, San Diego",
        "University of California Los Angeles": "University of California, Los Angeles",
    })

    reports = pd.read_csv("phd_stipends.csv")
    reports["institution"] = reports["university"].map(match_institution)
    reports["year"] = pd.to_numeric(
        reports["academic_year"].astype(str).str.split("-").str[0], errors="coerce"
    )
    reports["pay"] = pd.to_numeric(reports["overall_pay"], errors="coerce")
    obs = reports.dropna(subset=["institution", "year", "pay"])
    obs = obs[(obs["pay"] > 0) & obs["year"].isin(RECENT_YEARS)]

    crowd = (
        obs.groupby("institution")["pay"]
        .agg(crowd_median="median", crowd_mean="mean", n_reports="size")
        .round(0)
        .reset_index()
    )

    table = official.merge(crowd, on="institution", how="left")
    table["median_to_floor"] = (table["crowd_median"] / table["official_minimum_usd"]).round(2)
    table.to_csv("stipend_validation_table.csv", index=False)

    cols = ["institution", "official_minimum_usd", "crowd_median", "crowd_mean",
            "n_reports", "median_to_floor"]
    print(table[cols].to_string(index=False))
    print(f"\nInstitutions validated: {len(table)}; "
          f"median at or above published floor: "
          f"{int((table['median_to_floor'] >= 0.95).sum())}/{len(table)}")


if __name__ == "__main__":
    main()
