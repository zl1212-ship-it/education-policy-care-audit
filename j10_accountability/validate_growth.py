"""Validate the growth proxy against an official Student Growth Percentile.

The dose-response (weight_dose.py) and the weight sweep use a growth proxy, the
within-state percentile of a school's year-over-year achievement change, because real
state growth models are proprietary. A reviewer can fairly ask whether that proxy tracks
the growth measures states actually use. Washington publishes an official median Student
Growth Percentile (SGP) per school in its WSIF files, so we correlate the proxy against
it for Washington's elementary/middle schools. A positive correlation means the proxy
captures the same ordering of schools that the official growth measure does, which is what
the dose-response relies on.

Caveat (stated honestly in the manuscript): the proxy is built from the 2017-2018
achievement change (the panel's pre-pandemic year), while the official median SGP that is
machine-readable in the WSIF files is the 2022-2023 run. Because school growth shifts across
several years, the cross-year correlation is a conservative lower bound on the same-period
agreement, not the same-period correlation itself.

Output: prints Pearson and Spearman correlations; writes data/results_growth_validation.csv.

Run:  python3 validate_growth.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from weight_space import build_panel
from build_rdd_states import socrata, crosswalk_wa

HERE = Path(__file__).parent
FRAME = HERE / "data" / "school_frame.csv"
OUT = HERE / "data" / "results_growth_validation.csv"


def main():
    # my growth proxy for WA elementary/middle Title I schools
    panel = build_panel()
    frame = pd.read_csv(FRAME, dtype={"ncessch": str, "seasch": str})
    wa = panel[(panel["state"] == "WA") & (panel["is_high"] == 0)][
        ["ncessch", "growth_proxy"]].copy()

    # official WA median SGP (ELA + math), from the WSIF 2023 run
    w = socrata("data.wa.gov", "gvbz-svet", where="student_group='All Students'")
    for c in ("growth_ela_median_sgp", "growth_math_median_sgp"):
        w[c] = pd.to_numeric(w.get(c), errors="coerce")
    w["official_sgp"] = w[["growth_ela_median_sgp", "growth_math_median_sgp"]].mean(axis=1)
    w["school_code"] = w["school_code"].astype(str)

    cw = crosswalk_wa(frame)  # ncessch <-> WA school_code
    d = (wa.merge(cw[["ncessch", "school_code"]], on="ncessch", how="left")
           .merge(w[["school_code", "official_sgp"]], on="school_code", how="inner")
           .dropna(subset=["growth_proxy", "official_sgp"]))

    pear = stats.pearsonr(d["growth_proxy"], d["official_sgp"])
    spear = stats.spearmanr(d["growth_proxy"], d["official_sgp"])
    rows = [("WA", "n_schools", len(d)),
            ("WA", "pearson_r", pear[0]), ("WA", "pearson_p", pear[1]),
            ("WA", "spearman_rho", spear.correlation), ("WA", "spearman_p", spear.pvalue)]
    pd.DataFrame(rows, columns=["state", "statistic", "value"]).to_csv(OUT, index=False)

    print(f"growth-proxy validation against official median SGP (Washington):")
    print(f"  n = {len(d)} elementary/middle schools")
    print(f"  Pearson r  = {pear[0]:+.3f} (p = {pear[1]:.1e})")
    print(f"  Spearman rho = {spear.correlation:+.3f} (p = {spear.pvalue:.1e})")
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()
