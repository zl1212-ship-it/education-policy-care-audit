# Education-Policy Audit Series — Replication Data and Code

This repository holds the data-construction and analysis code for a set of independent
education-policy audit pipelines. Every figure and number in the associated manuscripts is
reproducible from public sources by running the scripts here; each manuscript's
data-availability statement points to this repository.

Each pipeline has its own directory and README (data sources, build steps, run order).
The pipelines are independent: each builds its own panel from its own
public-source pulls, and no data file is shared or reused across papers. Files that happen
to share a name in different directories (e.g. `treatment_panel.csv`, `results_summary.csv`)
are unrelated artifacts of different pipelines.

## The pipelines

| Directory | What it computes | Primary public sources |
|---|---|---|
| repo root (J1) | Institution-year panel of doctoral stipend reports scored against single-adult local living wages, with funding and enrollment context | PhD Stipends, USASpending.gov, IPEDS, NSF SED |
| [`j2_audit/`](j2_audit/) | Institution-year four-fifths (adverse-impact) screen on completion rates by race and income, plus a predictive layer | IPEDS Graduation Rates / Outcome Measures (Urban Institute API) |
| [`j3_admissions/`](j3_admissions/) | Staggered DiD and synthetic control on admissions and entering-class composition outcomes around test-optional adoption | IPEDS admissions and enrollment panels |
| [`j4_adoption/`](j4_adoption/) | Dated adoption panel for predictive-advising systems; staggered DiD on retention and completion-gap outcomes | Dated vendor/system contracts + IPEDS outcomes |
| [`j5_governance/`](j5_governance/) | Coded state-board governance panel (authority and representation indices) merged with state demographics | NASBE State Education Governance Matrix + NCES |
| [`j6_detection/`](j6_detection/) | Open AI-writing detectors scored over public human-essay corpora by language background; coded census of university integrity/AI policies | Public human-written essay corpora + 50 flagship integrity policies |
| [`j7_proctoring/`](j7_proctoring/) | Open face detectors benchmarked under exposure degradation with skin-tone stratification; 1:1 verification benchmark; coded vendor-documentation mapping | FairFace validation set + open detectors + vendor documentation |

Paper titles, venues, research questions, and findings are deliberately not described here
while manuscripts are under review; each directory README documents the build, not the paper.

**Start with the README inside each directory.** It documents the estimator or audit design,
the data sources, and the exact script run order (panels first, then analysis, then figures). Figure scripts write into a gitignored `paper/` folder and create it if absent.

## Frozen tags

Submitted manuscripts cite frozen snapshots so later data refreshes never silently change a
reported number. `paper-data-v1` and `paper-data-v2` freeze the J1 stipend panel (v2 matches
the current manuscript). Pipelines commit their assembled panels, so any
commit reachable from a paper's access date reproduces that paper's inputs.

## J1 — Doctoral stipend adequacy audit (repo root)

This pipeline predates the per-directory layout, so it lives at the repository root; the
frozen tags reference these paths.

The pipeline assembles a descriptive institution-year panel of doctoral stipend reports at
U.S. research universities. For each report, the *living-wage ratio* expresses the reported
stipend relative to a single-adult local living wage (crowd-sourced PhD Stipends repository),
aggregated to institutional means; this adequacy ratio is the primary measure. Institutional
federal funding totals (USASpending.gov) establish resource scale, and graduate enrollment
(IPEDS via Urban Institute) and research-doctorate counts (NSF SED) provide context.
`governance_matrix.csv` is the assembled institution-year panel (distinct from J5's
`nasbe_governance_matrix_2024.csv`, which is a different pipeline's source file).

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
