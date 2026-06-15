# sources and provenance

All national components come from public federal collections, served through the
Urban Institute Education Data Portal so a single request convention covers every
state. Per-state report-card files for the RDD layer come from the state education
agency. No login or API key is used anywhere.

## National layer

- **NCES Common Core of Data (CCD)** via the Urban Institute Education Data Portal
  (`https://educationdata.urban.org/api/v1/schools/ccd/directory/{year}/`). One row
  per school: NCES id (`ncessch`), state (`fips`), school level, enrollment, Title I
  status (`title_i_status`) and eligibility (`title_i_eligible`, `title_i_schoolwide`),
  urban-centric locale, charter and virtual flags. This is the school frame and the
  universe over which the identification rule is reconstructed.

- **EDFacts assessments** via the same portal
  (`/schools/edfacts/assessments/{year}/{grade_edfacts}/`, grade `99` = all grades).
  Math and reading proficiency are released as disclosure-protected ranges
  (`*_test_pct_prof_low`, `*_test_pct_prof_high`); the audit uses the published
  midpoint (`*_test_pct_prof_midpt`) and carries the range width so the binning is
  auditable. The economically-disadvantaged subgroup counts come from the
  `/special-populations/` variant of the same endpoint; the poverty intensity is the
  economically-disadvantaged share of valid test-takers (Community Eligibility makes
  the CCD free/reduced-lunch count null for many schools, so it is not the primary
  poverty measure).

- **EDFacts adjusted-cohort graduation rate (ACGR)** via the portal
  (`/schools/edfacts/grad-rates/{year}/`). Released as a range; the audit uses
  `grad_rate_midpt`. Applies to schools with a graduating cohort (the high-school
  graduation indicator in state composites).

- **Civil Rights Data Collection (CRDC)** via the portal
  (`/schools/crdc/chronic-absenteeism/{year}/...`). Chronic-absenteeism counts give
  the school-quality / student-success proxy that many state composites weight. CRDC
  is biennial; the access year is recorded per row.

## State layer (RDD)

Each state is a spec in `build_rdd_states.py` (open-data resource ids, column mapping,
cutoff convention, access via the state Socrata portal). A state enters the RDD only when
it publishes a continuous accountability index per school with a hard identification
cutoff and a downstream outcome. Two designs are distinguished by the `design` column:
`official_flag` (treatment is the state's published identification) and
`reconstructed_rule` (no machine-readable flag, so the cutoff is reconstructed from the
state's own published lowest-5%-of-Title-I rule applied to the index).

- **Washington (`official_flag`).** WA School Improvement Framework (WSIF) on
  `data.wa.gov`: the 2023 Run (`gvbz-svet`) gives the continuous composite `_2023_score`
  (running variable), the official `_2023_annual_identification` (treatment, comprehensive
  support), and `_2023_titlei`; the 2024 Annual run (`8v2t-vz3j`) gives the next-cycle
  `_2024_score`; the Report Card 1003 Funds 2023-24 file (`wyhw-h6xs`) gives the
  school-improvement funding outcome.

- **Connecticut (`reconstructed_rule`).** Next Generation Accountability System on
  `data.ct.gov` (`h28j-iix5`): `outcomeratepct` (total points over possible, 0-100) is
  the continuous accountability index; school-year rows (`category='SchoolTot'`) across
  years give the next-year index as the outcome. CT does not publish a machine-readable
  comprehensive-support flag, so the cutoff is the fifth percentile of the index among
  Title I schools (CT's published rule) and treatment is below that line.

- **NCES crosswalk.** State school codes are matched to NCES `ncessch` through the CCD
  state school id (`seasch`): the code after the dash equals the WA WSIF `school_code` and
  (zero-padded to seven digits) the CT NGA `schoolcode`. This carries the poverty measure
  from `indicators.csv` into the state panel.

## The identification rule

- **ESSA "lowest-performing" / Comprehensive Support and Improvement (CSI).** Federal
  law identifies, at least once every three years, the lowest-performing five percent
  of Title I schools (plus all high schools below a graduation-rate floor). The
  national layer reconstructs the bottom-five-percent-of-Title-I rule from the public
  composite to show the label is a function of the weights; the state layer uses each
  state's own published identification flag as the treatment.

## Environment

- Python 3.9.6; pandas, numpy, scipy, statsmodels, matplotlib. Only the standard
  library is used for HTTP (`urllib`) and parsing, so the pipeline has no third-party
  scraping dependency. All network access is to the public endpoints above.
