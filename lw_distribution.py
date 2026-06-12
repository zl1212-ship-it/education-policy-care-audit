"""
Living-wage ratio distribution by institution (J1).

Extends the institutional living-wage summary with the median ratio and the
share of reports below parity (ratio < 1.0), so the manuscript's Table 1 can
show where sub-living-wage reports concentrate instead of only the mean.
Replicates the report set behind lw_ratio_by_institution.csv (matched
institution, lw_ratio > 0, all available academic years) and asserts the
recomputed means and counts agree with that file before writing.

Descriptive only. Inputs: phd_stipends.csv, lw_ratio_by_institution.csv.
Output: lw_distribution.csv.
"""

import pandas as pd

from stipend_sensitivity import match_institution


def main():
    reports = pd.read_csv("phd_stipends.csv")
    reports["institution"] = reports["university"].map(match_institution)
    reports["lw_ratio"] = pd.to_numeric(reports["lw_ratio"], errors="coerce")
    obs = reports.dropna(subset=["institution", "lw_ratio"])
    obs = obs[obs["lw_ratio"] > 0]

    dist = (
        obs.groupby("institution")["lw_ratio"]
        .agg(
            lw_ratio_mean="mean",
            lw_ratio_median="median",
            share_below_1=lambda x: (x < 1.0).mean(),
            n_reports="size",
        )
        .round({"lw_ratio_mean": 3, "lw_ratio_median": 3, "share_below_1": 3})
        .reset_index()
    )

    published = pd.read_csv("lw_ratio_by_institution.csv")
    check = dist.merge(published, on="institution", suffixes=("", "_pub"))
    assert len(check) == len(published), "institution sets differ"
    assert (check["n_reports"] == check["n_reports_pub"]).all(), "report counts differ"
    assert (check["lw_ratio_mean"].sub(check["lw_ratio_mean_pub"]).abs() < 0.005).all(), \
        "means diverge from lw_ratio_by_institution.csv"

    dist = dist.sort_values("lw_ratio_mean")
    dist.to_csv("lw_distribution.csv", index=False)
    overall = (obs["lw_ratio"] < 1.0).mean()
    print(dist.to_string(index=False))
    print(f"\ntotal reports: {len(obs)}; overall share below 1.0: {overall:.3f}")


if __name__ == "__main__":
    main()
