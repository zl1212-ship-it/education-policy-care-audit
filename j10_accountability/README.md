# State ESSA school-accountability ratings: a regression-discontinuity audit at the identification threshold

Builds a national school-level panel of the indicators that feed state ESSA
report-card formulas and studies two things: (1) how the set of schools carrying
the lowest accountability label moves when the formula's indicator weights are
changed, and (2) what crossing a state's identification line does to a school,
estimated by regression discontinuity where a state publishes a single continuous
summative index with a hard cutoff.

The pipeline has two layers, kept distinct on purpose.

**National layer (descriptive first stage).** From public federal collections it
assembles, for every regular school, the components a state composite is built
from: academic achievement (math and reading percent proficient), graduation
(adjusted-cohort graduation rate), and a school-quality proxy (chronic
absenteeism). It forms a transparent composite, ranks schools within their own
state among Title I schools, and reconstructs the ESSA "lowest-performing"
identification rule (bottom five percent of Title I schools). It then re-computes
that label under a Monte-Carlo sweep of alternative weight vectors and reads how
the label redistributes across the school poverty distribution. A school's poverty
intensity is measured from the economically-disadvantaged share of its tested
students (the free/reduced-lunch count is unusable under Community Eligibility, so
it is carried only as a secondary check where present).

**State layer (causal).** Where a state publishes a continuous accountability
index per school plus the identification flag and a downstream outcome, the
pipeline assembles a school-level running-variable panel and estimates a
regression discontinuity at the identification line. The core comparison is
whether the discontinuity differs for high-poverty versus low-poverty schools. The
RDD runs only in states that genuinely supply a cutoff; states without a single
continuous index are not forced into one. A staggered difference-in-differences on
formula-revision dates is kept as a fallback design where no clean discontinuity
exists.

## Pipeline

```
build_frame.py        # national school frame from CCD (IDs, level, enrollment,
                      #   Title I status, locale, charter) -> data/school_frame.csv
build_indicators.py   # achievement (math/read % proficient), ACGR graduation,
                      #   chronic absenteeism, econ-disadvantaged poverty share
                      #   -> data/indicators.csv  (raw pulls cached in data/raw/)
weight_space.py       # composite + within-state Title I percentile + reconstructed
                      #   bottom-5% identification flag + Monte-Carlo reweighting
                      #   -> data/label_instability.csv, data/weight_draws.csv
analyze_gradient.py   # poverty gradient of the identification label (prevalence by
                      #   poverty decile; logit) -> data/results_gradient.csv
build_rdd_states.py   # per curated state: continuous index + identification flag +
                      #   downstream outcome -> data/rdd_panel.csv (state files cached)
analyze_rdd.py        # RDD at the identification line; poverty heterogeneity;
                      #   validity battery -> data/results_rdd.csv
robustness.py         # bandwidth/polynomial/donut/placebo-cutoff, leave-one-state-out,
                      #   alternate poverty measure, alternate composite weights
make_figures.py       # figures -> ../paper/blinded-manuscript/J10/
make_tables.py        # tables  -> data/table_*.csv
```

## Identification (stated in full in `analyze_rdd.py`)

- The running variable is the **state's own continuous accountability index**;
  treatment is crossing the published identification line; the outcome is a
  next-period school-level consequence. Identification rests on schools just above
  and just below the line being comparable, checked with a density test for sorting
  at the cutoff (McCrary), continuity of predetermined covariates, and
  bandwidth/polynomial sensitivity.
- The **reconstructed** bottom-five-percent flag in the national layer is a
  descriptive device for the weight-space sweep, not the causal estimand. It uses
  the public ESSA rule (lowest 5% of Title I schools by the summative composite) to
  show the label is formula-made; it is not claimed to reproduce any state's
  official list exactly.
- Poverty heterogeneity is pre-registered as the primary moderator: the estimand is
  whether the RDD effect, and the density of schools at the margin, differ across
  the poverty distribution.

## Data

- `data/school_frame.csv` - one row per regular school: NCES id, state, level,
  enrollment, Title I status and eligibility, locale, charter, virtual flag.
- `data/indicators.csv` - one row per school: math/reading percent proficient,
  adjusted-cohort graduation rate, chronic-absenteeism rate, economically
  disadvantaged share, with the source-year of each component.
- `data/label_instability.csv` - one row per school: baseline composite, within-state
  Title I percentile, baseline identification flag, and the share of weight draws in
  which the school is identified (label instability), with poverty decile.
- `data/weight_draws.csv` - one row per weight draw: the indicator weights and the
  poverty composition of the identified set under those weights.
- `data/results_gradient.csv` - identification prevalence by poverty decile and the
  logit poverty gradient.
- `data/rdd_panel.csv` - one row per (state, school): centered running variable,
  identification flag, outcome, poverty intensity, predetermined covariates.
- `data/results_rdd.csv` - RDD point estimates (pooled and by poverty), bandwidths,
  density-test and covariate-continuity diagnostics.

Raw API pages and per-state report-card downloads are cached under `data/raw/`
(gitignored) and are fully regenerable by the fetchers; the committed CSVs carry the
coded indicators and provenance years only. Source APIs, file specifications, and
access dates are in `SOURCES.md`; the composite and weight-sweep definitions are in
`CODEBOOK_indicators.md`.
