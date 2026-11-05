# Revision analyses (one-page-per-type design, cleaned text, crawl density, convergence checks)

These scripts extend the parent pipeline for the current version of the analysis. They read the parent
pipeline's committed files (`../data/`, `../crossnational/data/`) and write everything to
`output/`. Raw page HTML and retrieved PDFs are not committed (gitignored, regenerable with the
fetchers below); the assembled CSV products are.

## Run order

1. `extract_clean.py`: boilerplate-stripped text extraction (navigation, headers, footers,
   sidebars, link-dense menus removed; PDFs read with pypdf by both the raw and the cleaned
   extractor; captures stored gzip- or deflate-compressed are decompressed). Imported by the others.
2. `score_all.py`: re-scores every snapshot of the parent pipeline on the provision lexicon,
   raw and cleaned, at windows 200/400/800 and under the strict AI vocabulary
   (`output/scored_raw_vs_clean.csv`).
3. `fetch_cdx.py`: the capture listing of every page of the parent pipeline (`output/url_set.csv`,
   `output/cdx_captures.csv`), read by the steps below.
4. `pages_audit.py`: classifies the automatically discovered United States pages and recomputes
   endpoint prevalence under alternative page rules (robustness design on the original retrieval);
   `validate_extract.py` audits 16 pages.
5. `fetch_us_seeds.py`: fetches the curated United States pages (`../data/sample_frame.csv`
   integrity_url / guidance_url) from the Internet Archive (listing via the timemap endpoint,
   earliest capture per distinct digest, at most 16 versions per page, evenly spaced; the five pages
   fetched first kept 20); `output/seed_snapshot_index.csv`, `output/seed_coverage.csv`,
   `output/seed_cdx_captures.csv`.
6. `seed_design.py --rescore --backfill`: scores the curated pages and lists the tracked pages
   (`output/seed_pages.csv`) and the screened discovered pages used where a curated page was never
   archived (`output/seed_backfill_pages.csv`).
7. `fetch_quarter_versions.py`: lists the screened United States pages
   (`output/screened_cdx_captures.csv`) and retrieves, for every tracked page, the version in force at
   the end of each quarter when the corpus the design reads lacks it
   (`output/quarter_versions_index.csv`).
8. `fetch_policy_pdfs.py` then `rescore_pdfs.py`: policy documents linked from the endpoint versions
   of the curated pages as PDFs (up to three per institution, nearest capture to the end of the
   window).
9. `seed_design.py --rescore --backfill` again: scores the quarter-end versions
   (`output/scored_quarter_versions.csv`), merges them with the rest, and builds the symmetric design
   (curated page where archived, otherwise the screened discovered page), panels and endpoint
   prevalence (`output/seed_prevalence.csv`, with and without linked PDFs, and for the institutions
   that meet the entry rule page by page), the latest capture per institution
   (`output/seed_staleness.csv`, from the capture listings), and the United States event study on the
   design (through the helper `event_study_runner.py`). `sample_corrections.py` lists the
   institution left out of this design and the pages whose type is corrected, with the reason for
   each; the scripts of this design apply it (the discovered-pages robustness design keeps its own
   page rule). `prevalence_by_source.py` splits the United States by page source.
10. `seed_convergence.py`: convergence by pair type, balanced pool, endpoint tests on the
   last-quarter documents (full text, cut to 300 and 600 words, Commonwealth-only, United States
   contrast), per-system and page-type decompositions, placebo texts, and the normalization audit
   on the sample. `pair_structure_checks.py` breaks the endpoint pair matrix down by institution
   (the British row with each British institution left out) and repeats the pair matrix, pair
   groups, and per-system gaps with every text cut to 300 and 600 words and on the pre-shock
   integrity-page text. `convergence_ladder.py` and `paired_matched.py` run the same normalization
   ladder on the automatically discovered pages (robustness).
11. `crawl_density.py`: captures per page and quarter, density against exposure, interval-censored
   adoption dates and a Turnbull estimate.
12. `exposure_robustness.py`, `validation_r1.py`, `rebuild_panel_clean.py`, `contamination.py`:
   exposure robustness (including the interaction on the institutions that meet the entry rule page
   by page, `output/exposure_page_rule.csv`, and provision by provision,
   `output/exposure_by_provision.csv`), validation of the codes on the cleaned text, event-study
   variants on the discovered pages, and the share of flags that came from navigation.
13. `make_figures_r1.py`, `make_supplement.py`, `numbers_manifest.py`: figures, supplementary
   tables, and the list of every number the paper quotes.

Stdlib + pandas, numpy, scikit-learn, statsmodels, scipy, lxml, pypdf, matplotlib (Python 3.9).
