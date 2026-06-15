# Codebook: indicators, composite, and the weight sweep

This file is the single definition of how raw federal columns become the indicators,
the summative composite, the reconstructed identification flag, and the Monte-Carlo
weight sweep. `build_indicators.py` and `weight_space.py` mirror these definitions in
code; the code and this file must not drift.

## Indicators (school level, 0-100 scale, higher = better)

| key | construct | source column(s) | notes |
|---|---|---|---|
| `achv_math` | math proficiency | `math_test_pct_prof_midpt` | EDFacts range midpoint |
| `achv_read` | reading proficiency | `read_test_pct_prof_midpt` | EDFacts range midpoint |
| `achievement` | academic achievement | mean(`achv_math`, `achv_read`) | the two-subject mean |
| `grad` | graduation | `grad_rate_midpt` (ACGR) | high schools only |
| `quality` | school quality / success | `100 - chronic_absent_rate` | CRDC; absenteeism inverted so higher = better |

- All indicators are oriented so that **higher is better** (absenteeism is inverted).
- A school enters an indicator only when the underlying count is non-null; the
  composite is taken over the indicators a school actually has (see below), so an
  elementary school without a graduation cohort is not penalized for missing `grad`.
- `econ_disadv_share` (poverty intensity, 0-1) is `econ-disadvantaged valid test
  count / all-student valid test count`. It is a **covariate / moderator**, never an
  indicator in the composite.

## Baseline composite

The baseline weights mirror the most common ESSA elementary/middle design (the
modal published weighting), normalized over the indicators a school has:

```
w_baseline = { achievement: 0.40, grad: 0.20, quality: 0.10, growth_proxy: 0.30 }
```

- `growth_proxy` is the within-state-standardized year-over-year change in
  `achievement` (current minus prior available year), rescaled to 0-100 by percentile;
  where a prior year is unavailable the weight mass is renormalized onto the present
  indicators. Growth is a proxy because true state growth models are proprietary; the
  weight sweep below is the point, not the exact growth metric.
- For a school missing some indicators, the present weights are renormalized to sum to
  one before the weighted average, so the composite is always on the same 0-100 scale.

## Reconstructed identification flag

- Within each **state**, restrict to **Title I schools** (`title_i_eligible == 1`).
- Rank by the baseline composite; the **lowest five percent** are flagged
  `identified_baseline = 1` (the ESSA lowest-performing rule). High schools with
  `grad < 67` are additionally flagged (the statutory graduation floor).
- This is a descriptive reconstruction, not a state's official list (SOURCES.md).

## Monte-Carlo weight sweep (label instability)

Draw `N = 2000` weight vectors over the four indicator slots. Each indicator's weight
is drawn uniformly within an envelope set to the range that real published state ESSA
designs use (`achievement 0.20-0.60`, `growth 0.00-0.50`, `grad 0.00-0.35`,
`quality 0.05-0.25`; the envelope constants are documented at the top of
`weight_space.py`), then the drawn vector is renormalized to sum to one (projected to
the simplex). The baseline vector lies inside this envelope. For each draw:

1. recompute the composite with the drawn weights (same renormalization for missing
   indicators),
2. re-identify the bottom five percent of Title I schools within each state,
3. record, per school, whether it is identified.

Per-school outputs:

- `identify_freq` = share of the `N` draws in which the school is identified (0-1).
  A school with `identify_freq` near 0 or 1 is **label-stable**; values in between are
  **formula-made** (identification depends on the weight choice).
- `flip` = 1 if the school is identified under some draws and not others.

Per-draw outputs: the indicator weights and the poverty composition of the identified
set (mean `econ_disadv_share`, and the share of identified schools in the top poverty
quartile), so the sweep shows how reweighting redistributes the label across the
poverty distribution.

## Years

Each component is pulled for the most recent pre-pandemic accountability year with full
coverage and, separately, the most recent available year; `build_indicators.py` records
the source year per component in `indicators.csv`. Accountability ratings were paused in
2019-20 and 2020-21, so the primary national snapshot uses 2018-19 assessment and
graduation data with the nearest CRDC collection.
