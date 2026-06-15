# University AI / academic-integrity policy: a ChatGPT-shock event study

Builds an institution-by-time panel of academic-integrity governance text and
measures how it changed around the public release of ChatGPT (2022-11-30). For
each institution two kinds of page are tracked through time with dated snapshots
from the Internet Archive Wayback Machine: the durable academic-integrity /
honor-code / conduct page, and the institution's generative-AI guidance page.
Both are located by Wayback prefix discovery (the exact archived URL of a policy
page is hard to guess, so the pipeline takes the canonical page URLs the CDX
server reports under each curated stem and keeps the integrity and AI pages).
Every snapshot is converted to text and scored on a transparent provision lexicon
(`CODEBOOK_policy.md`) for how restrictive / surveillant versus permissive /
procedural the policy is toward student AI use. The institution-quarter outcome is
the max across the institution's pages, so AI language is captured wherever it
lands. The panel feeds an event-study difference-in-differences with a continuous
differential-exposure intensity (the pre-shock share of an institution's
enrollment most exposed to the shock). A second layer reads the endpoint
descriptively into a governance typology (silent / restrictive-leaning /
procedural-leaning, detector stance, disclosure-versus-ban, appeal, multilingual
protection).

The unit, corpus, and outcome are kept disjoint from `j6_detection/`: that
pipeline is a cross-sectional census of the 50 public state flagships coded for
how detector output is treated. This one tracks a different set of institutions
(the flagships are excluded; coverage concentrates the realized sample in research
universities) and a different construct: how governance text itself moved over
time around a shock. See the overlap note in `build_sample.py`.

## Pipeline

```
build_sample.py        # institution frame (Carnegie x control) + integrity & AI-guidance
                       #   URL stems + IPEDS exposure covariate -> data/sample_frame.csv
fetch_snapshots.py     # Wayback prefix discovery of integrity + AI pages, then dated
                       #   snapshots -> data/snapshots_raw/ (gitignored) +
                       #   data/snapshot_index.csv + data/coverage.csv  (--probe = no downloads)
build_panel.py         # stdlib HTML->text + provision lexicon, per page; institution-quarter
                       #   max across pages (forward-filled) -> data/panel.csv
analyze_event_study.py # event-study DiD around 2022-11-30; two-way FE; pre-trends;
                       #   differential-exposure interaction -> data/results_event_study.csv
analyze_descriptive.py # endpoint governance typology / provision prevalence (descriptive)
robustness.py          # placebo timing, window sensitivity, leave-one-out, alternate exposure
make_figures.py        # figures -> ../paper/blinded-manuscript/J9/
make_tables.py         # tables  -> data/table_*.csv
```

## Identification (stated in full in `analyze_event_study.py`)

- Outcome is **policy-text restrictiveness, not student outcomes.** The causal
  claim is about institutional rule-making, never about harm to students.
- The institution-quarter outcome is the **max across the institution's tracked
  pages**, forward-filled from dated snapshots. The durable integrity page anchors
  a pre-shock baseline that exists across the shock; an AI-guidance page created
  only after the shock contributes zero before it exists, so the rise it produces
  is part of the post-shock signal, not a pre-trend artifact.
- Two-way (institution and calendar-period) fixed effects; identification of the
  differential-exposure effect rests on parallel pre-trends, checked with the
  pre-period event-time coefficients and a placebo-timing falsification.

## Data

- `data/sample_frame.csv` - one row per institution: name, state, control,
  Carnegie type, integrity and AI-guidance URL stems, IPEDS UnitID, and the
  exposure covariate (nonresident-alien enrollment share).
- `data/coverage.csv` - one row per discovered page: capture counts, first/last
  capture, whether captured post-shock. Drives the feasibility filter.
- `data/snapshot_index.csv` - one row per Wayback capture kept: institution,
  page_type, capture timestamp, HTTP status, content digest, original and archived
  URL, local path (provenance).
- `data/panel.csv` - one row per (institution, quarter): event time relative to
  the shock, the provision presence flags and sub-indices (max across the
  institution's pages), and the composite restrictiveness / intensity. Auditable
  against the archived text under `data/snapshots_raw/` (gitignored, regenerate
  with `fetch_snapshots.py`).
- `data/results_event_study.csv` - event-time coefficients and the
  differential-exposure DiD estimate with clustered inference.
- `data/results_descriptive.csv` - endpoint provision prevalence and the
  governance typology counts.

Snapshot HTML is never committed: `data/snapshots_raw/` is gitignored and fully
reproducible from `data/snapshot_index.csv` by rerunning `fetch_snapshots.py`;
the panel carries timestamps, digests, and coded counts only. Source APIs,
access dates, and the shock date are in `SOURCES.md`.
