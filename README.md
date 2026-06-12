# Funding Without Care

This repository holds the data-construction scripts and the assembled dataset for the paper:

*"Funding Without Care: A Critical Policy Audit of Doctoral Stipend Adequacy and Institutional Hospitality."*

The paper is a descriptive critical policy audit. Everything here is built from publicly auditable sources so that each figure in the paper can
be reproduced from source.

## What the paper measures

The audit assembles a balanced descriptive panel of 22 elite U.S. Carnegie R1 universities
across 2019–2025.

* **Doctoral stipend living-wage adequacy.** For each report, the *living-wage
  ratio* is the reported stipend expressed relative to a single-adult local living wage. These
  ratios come from the crowd-sourced PhD Stipends repository (4,495 reports across the cohort)
  and are aggregated to institutional means. This ratio, not the dollar level alone, is the
  audit's primary measure, because it captures the *adequacy* of support relative to local cost
  of living. At the cohort mean the ratio is about 1.32; the finding is in the distribution,
  where about one report in seven falls below a local living wage and the highest-cost public
  flagships sit barely above parity.
  
* **Institutional federal funding (`H_f`).** Total federal award amounts per
  institution per fiscal year from the USASpending.gov API. These establish the resource scale
  of the institutions and are deliberately *not* set against stipends as an opposed quantity,
  since federal research awards themselves fund a large share of stipends, tuition, and
  personnel.

* **Supporting context.** Graduate enrolment from IPEDS via the Urban Institute Education Data
  API (2019–2022); research-doctorate counts from the NSF NCSES Survey of Earned Doctorates
  (2019–2023).

`governance_matrix.csv` also carries a descriptive log ratio `S_r = log((H_f + 1) / ((H_s /
cost_index) * N_g))`. It is a transparency artefact for the funding context.

## Files

| File | Contents |
|---|---|
| `scrape_stipends.py` | Pulls PhD Stipends reports → `phd_stipends.csv` (includes `lw_ratio`) |
| `scrape_usaspending.py` | Pulls federal award totals per institution from USASpending.gov |
| `build_matrix.py` | Assembles `governance_matrix.csv` from the real sources above |
| `institutions_config.json` | Institution name mappings and baseline enrolment seed |
| `phd_stipends.csv` | Raw stipend reports with living-wage ratios |
| `lw_ratio_by_institution.csv` | Institutional mean living-wage ratio and report counts |
| `ipeds_grad_enrollment.csv` | Graduate enrolment, IPEDS via Urban Institute (2019–2022) |
| `sed_doctorates.csv` | Research doctorates awarded, NSF SED (2019–2023) |
| `governance_matrix.csv` | Assembled institution-year panel used by the paper |
| `stipend_sensitivity.py` | Extrapolation-sensitivity check → `stipend_sensitivity.csv` (all 154 US cells observed) |
| `stipend_validation.py` | Validates crowd-sourced reports against published institutional floors → `stipend_validation_table.csv` |
| `stipend_validation.csv` | Officially published minimum stipend rates (10 institutions, source URLs + access dates) |
| `lw_distribution.py` | Per-institution living-wage ratio distribution (median, share below 1.0) → `lw_distribution.csv` |

## Reproduce

```bash
git clone https://github.com/zl1212-ship-it/education-policy-care-audit
cd education-policy-care-audit
git checkout paper-data-v2          # frozen snapshot matching the manuscript
# (paper-data-v1 matches the originally submitted version, before the validation files)

pip install requests
python build_matrix.py              # rebuilds governance_matrix.csv from source
```

The tag `paper-data-v2` is the frozen, version-tagged snapshot the paper cites; checking it out
reproduces the exact figures reported, independent of any later data refresh.

## Sources

* PhD Stipends — <https://www.phdstipends.com/> (stipends and living-wage ratios)
* USASpending.gov API — <https://api.usaspending.gov/> (federal awards)
* IPEDS via Urban Institute Education Data Portal — <https://educationdata.urban.org/>
* NSF NCSES Survey of Earned Doctorates — <https://ncses.nsf.gov/>
