# Education-Policy Audit Series: Replication Data and Code

This repository holds the data-construction and analysis code for a set of independent
education-policy audit pipelines. Every figure and number in the associated papers is
reproducible from public sources by running the scripts here; each paper's
data-availability statement points to this repository.

Each pipeline has its own directory and README (data sources, build steps, run order).
The pipelines are independent: each builds its own panel from its own
public-source pulls, and no data file is shared or reused across pipelines. Files that share
a name in different pipeline directories (for example `run_detectors.py` in `j6_detection/`
and `j7_proctoring/`, or `robustness.py` in `j4_adoption/`, `j9_aipolicy/`, and
`j10_accountability/`) are unrelated.

## The pipelines

| Directory | What it computes | Primary public sources |
|---|---|---|
| repo root | Raw doctoral stipend reports plus institution-level enrollment and doctorate counts, with the fetch scripts | PhD Stipends, USASpending.gov, IPEDS, NSF SED |
| [`j2_audit/`](j2_audit/) | Institution-year four-fifths (adverse-impact) screen on completion rates by race and income, plus a predictive layer | IPEDS Graduation Rates / Outcome Measures (Urban Institute API) |
| [`j3_admissions/`](j3_admissions/) | Institution-year panels of admissions volumes and requirements, entering-class race/ethnicity shares, and entering-class Pell share | IPEDS admissions, fall enrollment, and student financial aid files (Urban Institute API) |
| [`j4_adoption/`](j4_adoption/) | Dated adoption panel for predictive-advising systems; staggered DiD on retention and completion-gap outcomes | Dated vendor/system contracts + IPEDS outcomes |
| [`j5_governance/`](j5_governance/) | Coded state-board governance panel from the NASBE matrix, merged with state enrollment, demographic, and accountability data | NASBE State Education Governance Matrix + NCES + ECS |
| [`j6_detection/`](j6_detection/) | Open AI-writing detectors scored over public human-essay corpora by language background; coded census of university integrity/AI policies | Public human-written essay corpora + 50 flagship integrity policies |
| [`j7_proctoring/`](j7_proctoring/) | Per-image outcomes of open face detectors and 1:1 face verifiers under controlled exposure changes, with a per-image skin-tone measure | FairFace validation set + LFW + open detector and verifier weights |
| [`j9_aipolicy/`](j9_aipolicy/) | Institution-by-quarter panel of university academic-integrity and generative-AI guidance page text, scored on a provision lexicon, with each institution's nonresident enrollment share; a cross-national extension adds UK, Australian, and Canadian universities | Internet Archive Wayback Machine snapshots + IPEDS (Urban Institute API) + Carnegie Classification; HESA and Australian Department of Education enrollment data |
| [`j10_accountability/`](j10_accountability/) | National school-level panel of the indicators used in state ESSA accountability formulas (math and reading proficiency, graduation rate, chronic absenteeism, economically disadvantaged share), plus school-level state accountability-index data for Washington and Connecticut | NCES CCD, EDFacts, and CRDC (Urban Institute API) + NCES table of state ESSA indicator weights + Washington and Connecticut open-data portals |

**Start with the README inside each directory.** It gives the data sources and the script
run order, and for pipelines with analysis code, the estimator or audit design. Figure scripts
that save outside their own directory write to a gitignored `paper/` folder at the repo root
and create it if absent.

## Repo root

These files predate the per-directory layout. They are raw pulls and hand-collected tables
from the public sources listed below. The two fetch scripts need `requests`.

| File | Contents |
|---|---|
| `scrape_stipends.py` | Pulls PhD Stipends reports → `phd_stipends.csv` |
| `phd_stipends.csv` | Raw stipend reports with living-wage ratios (`lw_ratio`) |
| `scrape_usaspending.py` | Pulls federal award totals per institution and fiscal year from USASpending.gov |
| `ipeds_grad_enrollment.csv` | Graduate enrollment, IPEDS via Urban Institute (2019-2022) |
| `sed_doctorates.csv` | Research doctorates awarded, NSF SED (2019-2023) |
| `stipend_validation.csv` | Published minimum stipend rates for 10 institutions, with source URLs and access dates |

`j1_crossnational/` holds reference stipend and cost-of-living tables for the UK, Canada,
Australia, and Japan.

## Environment

Python 3.9+; numpy, pandas, scipy, matplotlib (plus per-pipeline extras noted in each
README). No build system: scripts run directly with `python3`, in the order each pipeline's
README gives.

## Sources

* PhD Stipends: <https://www.phdstipends.com/> (stipends and living-wage ratios)
* USASpending.gov API: <https://api.usaspending.gov/> (federal awards)
* IPEDS via Urban Institute Education Data Portal: <https://educationdata.urban.org/>
* NSF NCSES Survey of Earned Doctorates: <https://ncses.nsf.gov/>

Each pipeline's sources are documented in its README and, where present, its `SOURCES.md`.
