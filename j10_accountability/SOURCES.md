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

- **State education agency report cards / accountability files.** For each state in
  the RDD set, the continuous summative accountability index per school, the official
  identification flag (Comprehensive Support and Improvement and related categories),
  and at least one downstream outcome are taken from the state's published
  accountability data files. The curated per-state file URLs, the index column, the
  identification column, and the cutoff convention are recorded in `build_rdd_states.py`
  with the access date. A state enters the RDD only when it publishes a single
  continuous index with a hard identification cutoff; otherwise it is excluded from the
  causal layer (it still contributes to the national descriptive layer).

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
