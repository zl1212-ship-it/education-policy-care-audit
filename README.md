# Educational Care Audit

This repository contains the replication code, structured panel datasets, and automated verification pipelines for the paper:
*"Funding High-Skill STEM Pipelines: A Comparative Policy Audit of Institutional Infrastructure and Doctoral Labor Support in the United States and Japan."*

The codebase models how macro-industrial transformations, specifically the U.S. CHIPS and Science Act and Japan's Society 5.0 framework, alter localized institutional resource allocation profiles and drive doctoral pipeline attrition.

## Key Metrics

The analytical framework operationalizes the structural indicator to evaluate systemic pipeline strain:

* **Funding-to-Stipend Disparity Ratio ($S_{rit}$):** Evaluates structural per-capita fiscal divergence across capitalization layers.
  $$S_{rit} = \ln \left( \frac{H_{fit} + 1}{\left( \frac{H_{sit}}{C_i} \right) \times N_{git}} \right)$$
  Where $H_{fit}$ is the total macro-infrastructure asset funding, $H_{sit}$ is individual baseline student subsistence support, $C_i$ represents local cost-of-living adjustments, and $N_{git}$ tracks active graduate enrollment headcounts.

## Econometric Design

We evaluate the structural "life stall" hypothesis using a Two-Way Fixed Effects (TWFE) panel regression design tracking historical cross-country policy cutoffs:

$$AttritionRate_{it} = \beta_0 + \beta_1 PostPolicy_{it} + \beta_2 S_{rit} + \alpha_i + \delta_t + \varepsilon_{it}$$

* **AttritionRate_{it}**: Localized doctoral pipeline attrition indicator matrix for institution $i$ across calendar year $t$.
* **$\alpha_i$ & $\delta_t$**: Entity and time-trend fixed effects parameters capturing time-invariant institutional factors and global macroeconomic shocks.
* **PostPolicy_{it}**: Step-treatment binary indicator tracking policy activation windows ($t \ge 2023$ for the United States; $t \ge 2021$ for Japan).
* **Variance Corrective**: Standard errors are evaluated using Huber-White robust estimation clustered at the institutional level ($HC1$) to control for heteroskedasticity.

## Repository Architecture

* `metrics_engine.py`: Core processing pipeline executing live API audits and estimating the TWFE panel regressions.
* `institutions_config.json`: Master lookup profile housing real postsecondary database mappings for the active cohort.
* `governance_matrix.csv`: Standardized historical panel tracking parameters across target elite research centers ($N = 33$).
* `.github/workflows/run_audit.yml`: Automated GitHub Actions runner validating script execution environment on push.

## Setup & Replication

Execute the analysis pipeline locally inside an isolated Python 3.10+ workspace:

```bash
# Clone the workspace architecture
git clone https://github.com
cd education-policy-care-audit

# Install analytical dependencies
pip install numpy pandas statsmodels requests

# Run the replication engine
python metrics_engine.py
```
