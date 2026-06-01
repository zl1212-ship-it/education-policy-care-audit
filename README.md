# Educational Care Audit

This repository contains the replication code, structured panel datasets, and automated verification pipelines for the paper:  
*"Redistributing Educational Care: A Comparative Policy Audit of Funding, Staffing, and Implementation Rules in the United States and Japan."*

The codebase models how macro-industrial transformations—specifically the U.S. CHIPS and Science Act and Japan's Society 5.0 framework—alter localized institutional resource allocation profiles and drive doctoral pipeline attrition.

## Key Metrics

The analytical framework operationalizes two structural indicators to evaluate systemic pipeline strain:

*   **Logarithmically Scaled Sovereignty Ratio ($S_r$):** Evaluates structural per-capita fiscal divergence across capitalization layers.
    $$S_r = \ln\left(\frac{H_f}{H_s \cdot N_g}\right)$$
    Where $H_f$ is total macro-infrastructure asset funding, $H_s$ is individual baseline student subsistence support, and $N_g$ tracks aggregate active graduate enrollment fields.
    
*   **Survival-to-Study Ratio ($R_{ss}$):** Models explicit zero-sum weekly individual temporal trade-offs ($T_{\text{total}} = 168 \text{ hours}$) forced by administrative workload automation.
    $$R_{ss} = \frac{T_s}{T_r + \delta}$$
    Where $T_s$ captures uncompensated survival gig-labor hours, $T_r$ maps active funded hours dedicated to scientific discovery, and $\delta = 1$ stabilizes the boundary framework during full funding withdrawal intervals.

## Econometric Design

We evaluate the structural "life stall" hypothesis using a Two-Way Fixed Effects (TWFE) panel regression design tracking historical policy cutoffs:

$$Y_{it} = \alpha_i + \gamma_t + \beta_1 \text{PostPolicy}_{it} + \beta_2 S_{r, it} + \epsilon_{it}$$

*   **$Y_{it}$:** Doctoral pipeline attrition indicator matrix for institution $i$ across temporal window $t$.
*   **$\alpha_i$ & $\gamma_t$:** Entity and time-trend fixed effects parameters capturing time-invariant institutional factors and global shocks.
*   **$\text{PostPolicy}_{it}$:** Step-treatment binary indicator tracking post-2022 policy activation windows.
*   **Variance Corrective:** Standard errors are evaluated using Huber-White robust estimation ($HC1$) to control for small-sample heteroskedasticity.

## Repository Architecture

*   `metrics_engine.py`: Core processing pipeline executing live API audits and estimating the TWFE panel regressions.
*   `governance_matrix.csv`: Standardized historical panel tracking parameters across target elite research centers ($N=8$).
*   `.github/workflows/run_audit.yml`: Automated GitHub Actions runner validating script execution environment on push.

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
