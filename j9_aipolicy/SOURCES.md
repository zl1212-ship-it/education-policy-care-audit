# sources and provenance

## The shock

- **ChatGPT public release: 2022-11-30** (OpenAI). This is the event date for the
  event study. All event time is measured in days/quarters relative to this date.

## Policy text (the panel)

- **Internet Archive Wayback Machine** - dated snapshots of each institution's
  academic-integrity / honor-code / conduct page and its generative-AI guidance
  page.
  - CDX server (capture listing): `http://web.archive.org/cdx/search/cdx`
    (query parameters documented at https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server).
    `fetch_snapshots.py` first does prefix discovery (`matchType=prefix`,
    `collapse=urlkey`) under each curated stem to recover the canonical page URLs
    the archive actually holds (an exact-match query misses a page when a path
    token or trailing slash differs), keeping the integrity and AI pages. It then
    lists each page's captures (`collapse=timestamp:8`, one per day) and keeps one
    snapshot per distinct content digest.
  - Snapshot retrieval: `http://web.archive.org/web/<timestamp>id_/<url>`
    (the `id_` flavor returns the archived bytes without the Wayback navigation
    chrome, so the extracted policy text is the page as captured).
  - Captures are public; each kept capture's timestamp and digest are recorded in
    `data/snapshot_index.csv` and per-page coverage in `data/coverage.csv`. No
    login or key.
- The curated URL stems (integrity page and AI-guidance page) are in
  `build_sample.py` with each institution's Carnegie type and control. Because an
  institution's policy state is the max across its pages, an unmatched stem only
  contributes zero; it does not bias the panel.

## Exposure covariate

- **IPEDS via the Urban Institute Education Data Portal**
  (`https://educationdata.urban.org/api/v1/college-university/ipeds`). Fall
  enrollment by race; `race=8` is Nonresident alien and `race=99` is Total, so the
  exposure intensity is the nonresident-alien share of total fall enrollment for
  the pre-shock year. UnitIDs are resolved from the IPEDS directory by state plus
  normalized name; unresolved ones are pinned in an override map. Public API, no key.
  - (The `race` coding mirrors `j6_detection/build_ipeds_covariate.py`: `8` is the
    nonresident-alien code; `9` is race-unknown, which must not be used.)

## Carnegie classification

- **Carnegie Classification of Institutions of Higher Education** basic type and
  control, used only to define the sampling strata recorded in `data/sample_frame.csv`.
  Values are curated per institution in `build_sample.py` from the public
  classification listing (https://carnegieclassifications.acenet.edu/).

## Environment

- Python 3.9.6; pandas, numpy, scipy, statsmodels, matplotlib. HTML is parsed with
  the standard library (`html.parser`), so the pipeline has no third-party
  scraping dependency. All network access is to the public APIs above.
