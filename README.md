**Transnational Policy Analysis Datasets**

This repository houses the qualitative comparative analytical matrices, transnational policy tracking parameters, and conceptual evaluation engines supporting the manuscript: "Redistributing Educational Care: A Comparative Policy Audit of Funding, Staffing, and Implementation Rules in the United States and Japan."

**Overview**

This framework provides a dual metric baseline to model algorithmic bureaucracy and institutional precarity within modern STEM pipelines. It evaluates the qualitative policy divergence between the United States CHIPS and Science Act and Japan's Society 5.0 initiatives against UNESCO Global Education Monitoring benchmarks.

**Theoretical Architecture**

The engine operationalizes two primary structural foundations equations:

1. Sovereignty Ratio ($S_r$): Evaluates macro fiscal resource extraction boundaries.
   $$S_r = \frac{H_f}{H_s}$$
   Where $H_f$ is institutional infrastructure funding allocations and $H_s$ is direct human capital student subsistence support.

2. Survival to Study Ratio ($R_{ss}$): Models temporal precarity thresholds.
   $$R_{ss} = \frac{T_{s}}{T_{r}}$$
   Where $T_{s}$ denotes the hours forced into secondary subsistence labor, and $T_{r}$ signifies active hours dedicated to scholarly investigation.

**File Registry**

`metrics_engine.py`: Functional core runtime calculator mapping $S_r$ and $R_{ss}$ thresholds.
`governance_matrix.csv`: Structured tabular spreadsheet tracking comparative policy variables across national regimes.

**Usage**

To run the automated policy diagnostics calculations engine, execute via any standard Python 3.x console environment:
```bash
python metrics_engine.py
```
