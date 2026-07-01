"""Cross-national doctoral-stipend adequacy audit.

Design: descriptive policy audit, not causal inference. For each governance
regime the reference doctoral stipend (a nationally set floor, or, for the US,
the institution-set distribution) is expressed as an adequacy ratio against a
local cost-of-living benchmark. No treatment effect is estimated.

Two-tier benchmark, by data availability, not by choice of convenience:
  Tier A (basic-needs living wage): US (MIT Living Wage Calculator, single
    adult), UK (Living Wage Foundation real Living Wage), Canada (Ontario /
    BC Living Wage Networks). Three independent national basic-needs
    calculators; the reference household differs (MIT single-adult vs the
    LWF/CLWN household-weighted models), so cross-tier levels are compared
    as "each regime against its own recognised basic-needs standard," not as
    an identical metric.
  Tier B (statutory minimum wage): Australia (Fair Work national minimum
    wage) and Japan (Tokyo regional minimum wage), where no basic-needs
    living-wage body publishes a comparable figure. The benchmark is a
    full-time minimum-wage income; a stipend near or below it is the sharper,
    more conservative test.

Benchmark annual income uses each source's own full-time-week convention
(hours_per_week x weeks), stored per row. Stipends are compared gross; several
are tax-exempt (UK, Australia) or tax-advantaged (Canada scholarships), which
raises effective adequacy by a few points relative to the gross ratio reported
here and is noted as a limitation rather than adjusted for.

Inputs : crossnational_stipends.csv, living_wage_intl.csv,
         ../lw_ratio_by_institution.csv (US institution-level ratios)
Output : crossnational_ratios.csv
"""

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load():
    stip = pd.read_csv(os.path.join(HERE, "crossnational_stipends.csv"))
    lw = pd.read_csv(os.path.join(HERE, "living_wage_intl.csv"))
    return stip, lw


def build_intl(stip, lw):
    """Merge every stipend row to every same-country, same-year benchmark row."""
    lw = lw.copy()
    lw["benchmark_annual_local"] = (
        lw["hourly_local"] * lw["hours_per_week"] * lw["weeks"]
    )
    merged = stip.merge(
        lw[["country", "year", "region", "benchmark_type",
            "benchmark_annual_local", "hours_per_week", "source"]],
        on=["country", "year"], how="inner", suffixes=("_stipend", "_benchmark"),
    )
    merged["adequacy_ratio"] = (
        merged["stipend_annual_local"] / merged["benchmark_annual_local"]
    ).round(3)
    return merged


def us_rows():
    """US enters as an institution-set distribution; lw_ratio is already the
    stipend / MIT-single-adult-living-wage ratio, so it needs no benchmark join."""
    us = pd.read_csv(os.path.join(ROOT, "lw_ratio_by_institution.csv"))
    r = us["lw_ratio_mean"]
    lo_name = us.loc[r.idxmin(), "institution"]
    hi_name = us.loc[r.idxmax(), "institution"]
    n_inst = len(us)
    below = int((r < 1.0).sum())
    tmpl = dict(country="US", year=2024,
                tier="institution_set", currency="USD",
                benchmark_type="basic_needs_livingwage",
                source_benchmark="MIT Living Wage Calculator (single adult)")
    return pd.DataFrame([
        {**tmpl, "program": f"22 R1 cohort mean (n={n_inst} institutions)",
         "region": "cohort", "adequacy_ratio": round(r.mean(), 3)},
        {**tmpl, "program": f"cohort minimum ({lo_name})",
         "region": "flagship_low", "adequacy_ratio": round(r.min(), 3)},
        {**tmpl, "program": f"cohort maximum ({hi_name})",
         "region": "flagship_high", "adequacy_ratio": round(r.max(), 3)},
    ]), below, n_inst


def main():
    stip, lw = load()
    intl = build_intl(stip, lw)
    us, us_below, us_n = us_rows()

    keep = ["country", "year", "program", "tier", "region", "benchmark_type",
            "stipend_annual_local", "benchmark_annual_local", "currency",
            "adequacy_ratio"]
    out = pd.concat([intl.reindex(columns=keep), us.reindex(columns=keep)],
                    ignore_index=True, sort=False)
    out = out.sort_values(["country", "year", "program", "region"])
    out.to_csv(os.path.join(HERE, "crossnational_ratios.csv"), index=False)

    # --- 2024 anchor-year snapshot -----------------------------------------
    print("=== Cross-national doctoral-stipend adequacy, 2024 anchor year ===")
    print("(adequacy_ratio = reference stipend / local cost-of-living benchmark)\n")
    snap = out[(out["year"] == 2024)].copy()
    for _, row in snap.iterrows():
        tag = "living-wage" if row["benchmark_type"] == "basic_needs_livingwage" else "min-wage"
        print(f"  {row['country']:>2}  {row['program'][:52]:<52} "
              f"{row['region']:<13} ratio={row['adequacy_ratio']:.2f}  [{tag}]")
    print(f"\n  US cohort: {us_below} of {us_n} institutions have a mean ratio below 1.00.")

    below1 = out[out["adequacy_ratio"] < 1.0]
    print(f"\n  Rows below parity (ratio < 1.00): {len(below1)} of {len(out)}.")
    print("  Wrote crossnational_ratios.csv")


if __name__ == "__main__":
    main()
