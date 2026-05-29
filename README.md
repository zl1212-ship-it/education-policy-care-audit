# Educational Care Audit

[![Execute Policy Metrics Pipeline](https://github.com)](https://github.com)

This repository contains the replication code, datasets, and automated testing workflows for the paper: *"Redistributing Educational Care: A Comparative Policy Audit of Funding, Staffing, and Implementation Rules in the United States and Japan."*

The codebase models how macro-industrial shifts—specifically the U.S. CHIPS Act and Japan's Society 5.0 framework—impact doctoral pipeline retention when evaluated against UNESCO benchmarks.

---

## Key Metrics

The analysis operationalizes two structural tracking metrics to study institutional pipeline attrition:

* **Sovereignty Ratio ($S_r$):** Tracks structural capital-to-stipend divergence.
  $$S_r = \frac{H_f}{H_s}$$
  Where $H_f$ is macro-infrastructure funding and $H_s$ is direct student subsistence stipends.

* **Survival to Study Ratio ($R_{ss}$):** Models individual time-allocation trade-offs forced by administrative automation.
  $$R_{ss} = \frac{T_s}{T_r}$$
  Where $T_s$ is uncompensated gig-labor time spent covering basic cost-of-living gaps, and $T_r$ is active research hours.

---

## Regression Model

We test the "life stall" hypothesis using an ordinary least squares (OLS) panel design across major U.S. research institutions ($N=8$). 

$$Y_{it} = \alpha + \beta_1 \text{Time}_{it} + \beta_2 \text{Policy}_{it} + \beta_3 S_{r,it} + \epsilon_{it}$$

* **$Y_{it}$:** Doctoral pipeline attrition rate for institution $i$ at time $t$.
* **$\text{Policy}_{it}$:** A step-treatment dummy tracking the shift after legislative funding activation.
* **Variance Corrective:** Standard errors are evaluated using Huber-White robust estimation (**HC1**) to control for cross-unit heteroskedasticity within our small institutional cohort.

---

## Files

* `metrics_engine.py`: Core Python script running the OLS regressions with HC1 robust standard errors.
* `governance_matrix.csv`: Structured panel dataset tracking metrics across Stanford, UW, UC Berkeley, and Harvard.
* `.github/workflows/run_audit.yml`: GitHub Actions workflow validating the execution environment on push.

---

## Setup & Replication

Run the engine locally using standard Python 3.10+:

```bash
git clone https://github.com
cd education-policy-care-audit

# Install dependencies
pip install numpy pandas statsmodels

# Run the regression pipeline
python metrics_engine.py
```

---

## Next Steps

This panel framework serves as a structural stepping stone for expanding causal inference models into enterprise settings. Future work uses these baselines to scale into **Causal Machine Learning (CausalML / DoWhy)** environments:
* **Propensity Score Matching (PSM):** Auditing selection bias and labor churn within corporate automated talent software.
* **Regression Discontinuity (RDD):** Using rigid algorithmic assessment cutoffs to isolate the causal impact of autonomous management software on white-collar displacement.
