# J2 — Disparate-impact audit of college completion (four-fifths rule)

Does U.S. higher education show disparate impact in completion outcomes by race and income,
judged by the standard the law already uses for employment? The audit imports the EEOC
Four-Fifths (4/5ths) adverse-impact rule into education policy: per institution-year, the
ratio of each subgroup's completion rate to the White (or non-Pell) reference rate, flagging
ratios below 0.80. A predictive layer then asks which institutional features anticipate
failing the test.

All inputs are public: IPEDS Graduation Rates (150% of normal time) and Outcome Measures
(6-year completion), retrieved through the Urban Institute Education Data API (no key),
cohort years 2018–2022. Every number in the paper regenerates from these scripts.

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
| `robustness_audit.py` | Parallel absolute pp-gap audit; tier concentration; cohort-size sensitivity | stdout |
