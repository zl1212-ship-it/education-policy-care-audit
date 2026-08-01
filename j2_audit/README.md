# Disparate-impact audit of college completion (four-fifths rule)

Applies the EEOC Four-Fifths (4/5ths) adverse-impact rule to college completion outcomes:
per institution-year, the ratio of each subgroup's completion rate to the White (or
non-Pell) reference rate, flagging ratios below 0.80. A predictive layer models which
institutional features anticipate a flag.

All inputs are public: IPEDS Graduation Rates (150% of normal time) and Outcome Measures
(6-year completion), retrieved through the Urban Institute Education Data API (no key),
cohort years 2018–2022. Every output regenerates from these scripts.

## Run order

1. `build_disparate_impact.py` — builds the frozen institution-year panel
2. `pell_audit.py` — income (Pell vs non-Pell) audit, prints national summary
3. `predict_failure.py` — merges institutional features, fits the predictive layer
4. `multiyear_predict.py` — pooled 2018–2022 model with year fixed effects
5. `robustness_audit.py` — ratio-vs-absolute-gap and cohort-size robustness

## Designs

| Script | Design | Output |
|---|---|---|
| `build_disparate_impact.py` | Four-fifths ratio per institution-year, subgroup vs White completion, flag < 0.80 | `disparate_impact_panel.csv` |
| `pell_audit.py` | Same rule on income: Pell vs non-Pell 6-year completion (Outcome Measures) | stdout summary |
| `predict_failure.py` | Logistic regression (odds ratios) + gradient boosting (5-fold CV AUC) on 2022 failure | `predict_features_2022.csv`, stdout |
| `multiyear_predict.py` | Pooled logit 2018–2022 with year fixed effects; stability of correlates | stdout |
| `robustness_audit.py` | Parallel absolute pp-gap audit; tier concentration; cohort-size sensitivity; strict highest-rate-group reference variant; pooled 2020–2022 entering-cohorts audit | stdout |

Data note: in the API's 2021 grad-rates release, `cohort_rev` is coded -1 (missing) for all
2-year institutions (`institution_level` 2, `subcohort` -2), so the 30-student cohort screen
in `build_disparate_impact.py` excludes that sector and the 2021 panel (1,669 institution-years)
covers 4-year institutions only; completion rates for the excluded institutions are present
upstream under `cohort_adj_150pct`, and all other years are unaffected. `robustness_audit.py`
section 6 re-sizes the 2021 screen on `cohort_adj_150pct`, restoring coverage in line with
adjacent years.

A second data note: `disparate_impact_panel.csv` is a frozen build, while parts of
`robustness_audit.py`, `predict_failure.py`, and `multiyear_predict.py` re-query the live API
at run time. Upstream IPEDS revisions can therefore shift live-pull results slightly against
the frozen panel (e.g., the 2022 Black-White baseline reads 1,004/1,518 from the live API as of
2026-07 vs 1,006/1,518 in the frozen panel), which matters most for shares near a rounding
boundary.
