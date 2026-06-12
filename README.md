# Education-Policy Audit Series — Replication Data and Code

This repository holds the data-construction and analysis code for a series of independent
education-policy audit papers. Every figure and number each paper reports is reproducible
from public sources by running the scripts here; each paper's data-availability statement
points to this repository.

Each paper has its own pipeline directory with its own README (research question, data
sources, run order). The pipelines are independent: each builds its own panel from its own
public-source pulls, and no data file is shared or reused across papers. Files that happen
to share a name in different directories (e.g. `treatment_panel.csv`, `results_summary.csv`)
are unrelated artifacts of different pipelines.

## The papers

| Directory | What it audits | Primary public sources |
|---|---|---|
| repo root (J1) | Doctoral stipend adequacy relative to the local living wage at 22 elite R1 universities | PhD Stipends, USASpending.gov, IPEDS, NSF SED |
| [`j2_audit/`](j2_audit/) | Completion outcomes by race and income against the EEOC four-fifths rule | IPEDS Graduation Rates / Outcome Measures (Urban Institute API) |
| [`j3_admissions/`](j3_admissions/) | Whether test-optional admissions changed the measurement of merit or the composition of access | IPEDS admissions and enrollment panels |
| [`j4_adoption/`](j4_adoption/) | The causal effect of adopting predictive-advising systems on completion gaps | Dated vendor/system contracts + IPEDS outcomes |
| [`j5_governance/`](j5_governance/) | Authority versus democratic representation across the 50 state boards of education | NASBE State Education Governance Matrix + NCES |
| [`j6_detection/`](j6_detection/) | AI-writing-detector false-positive rates by language background, and the university policies that give the flag force | Public human-written essay corpora + 50 flagship integrity policies |
| [`j7_proctoring/`](j7_proctoring/) | Face-detection miss rates by skin tone in the presence-check step of remote proctoring, and how vendors turn a miss into a consequence | FairFace validation set + open detectors + vendor documentation |

Paper titles and venues are deliberately not listed while manuscripts are under review;
each directory README identifies its study by question and design.

**Start with the README inside each directory.** It states the research question, the
identification or audit design, and the exact script run order (panels first, then analysis,
then figures). Figure scripts write into a gitignored `paper/` folder and create it if absent.

Per-pipeline findings narratives (`results.md`) are kept private until publication; the
numbers behind them regenerate from the committed scripts and data.

## Frozen tags

Submitted manuscripts cite frozen snapshots so later data refreshes never silently change a
reported number. `paper-data-v1` and `paper-data-v2` freeze the J1 stipend panel (v2 matches
the current manuscript). Pipelines commit their assembled panels, so any
commit reachable from a paper's access date reproduces that paper's inputs.

## J1 — Doctoral stipend adequacy audit (repo root)

The first paper predates the per-directory layout, so its pipeline lives at the repository
root; the frozen tags and the manuscript's reproduction instructions reference these paths.

The audit assembles a balanced descriptive panel of 22 elite U.S. Carnegie R1 universities
across 2019–2025. For each stipend report, the *living-wage ratio* expresses the reported
stipend relative to a single-adult local living wage (PhD Stipends repository, 4,495 reports),
aggregated to institutional means. This adequacy ratio is the primary measure. Institutional
federal funding totals (USASpending.gov) establish resource scale and are deliberately not
set against stipends as an opposed quantity. Graduate enrollment (IPEDS via Urban Institute)
and research-doctorate counts (NSF SED) provide context. `governance_matrix.csv` is J1's
assembled institution-year panel (distinct from J5's `nasbe_governance_matrix_2024.csv`,
which is a different paper's source file).

| File | Contents |
|---|---|
| `scrape_stipends.py` | Pulls PhD Stipends reports → `phd_stipends.csv` (includes `lw_ratio`) |
| `scrape_usaspending.py` | Pulls federal award totals per institution from USASpending.gov |
| `build_matrix.py` | Assembles `governance_matrix.csv` from the sources above |
| `institutions_config.json` | Institution name mappings and baseline enrolment seed |
| `phd_stipends.csv` | Raw stipend reports with living-wage ratios |
| `lw_ratio_by_institution.csv` | Institutional mean living-wage ratio and report counts |
| `ipeds_grad_enrollment.csv` | Graduate enrolment, IPEDS via Urban Institute (2019–2022) |
| `sed_doctorates.csv` | Research doctorates awarded, NSF SED (2019–2023) |
| `governance_matrix.csv` | Assembled institution-year panel used by the paper |
| `stipend_sensitivity.py` | Extrapolation-sensitivity check → `stipend_sensitivity.csv` |
| `stipend_validation.py` | Validates crowd-sourced reports against published institutional floors → `stipend_validation_table.csv` |
| `stipend_validation.csv` | Officially published minimum stipend rates (10 institutions, source URLs + access dates) |
| `lw_distribution.py` | Per-institution living-wage ratio distribution → `lw_distribution.csv` |

### Reproduce J1

```bash
git clone https://github.com/zl1212-ship-it/education-policy-care-audit
cd education-policy-care-audit
git checkout paper-data-v2          # frozen snapshot matching the manuscript

pip install requests
python build_matrix.py              # rebuilds governance_matrix.csv from source
```

## Environment

Python 3.9+; numpy, pandas, scipy, matplotlib (plus per-pipeline extras noted in each
README). No build system: scripts run directly with `python3`, in the order each pipeline's
README gives.

## Sources (J1)

* PhD Stipends — <https://www.phdstipends.com/> (stipends and living-wage ratios)
* USASpending.gov API — <https://api.usaspending.gov/> (federal awards)
* IPEDS via Urban Institute Education Data Portal — <https://educationdata.urban.org/>
* NSF NCSES Survey of Earned Doctorates — <https://ncses.nsf.gov/>

Sources for J2–J7 are documented in each pipeline's README and `SOURCES.md`.
