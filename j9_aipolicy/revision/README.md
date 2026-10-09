# Revision analyses (one-page-per-type design, cleaned text, crawl density, convergence checks)

These scripts extend the parent pipeline for the current version of the analysis. They read the parent
pipeline's committed files (`../data/`, `../crossnational/data/`) and write everything to
`output/`. Raw page HTML and retrieved PDFs are not committed (gitignored, regenerable with the
fetchers below); the assembled CSV products are.

## Run order

1. `extract_clean.py`: boilerplate-stripped text extraction (navigation, headers, footers,
   sidebars, link-dense menus removed; PDFs read with pypdf). Imported by the others.
2. `score_all.py`: re-scores every snapshot of the parent pipeline on the provision lexicon,
   raw and cleaned, at windows 200/400/800 and under the strict AI vocabulary
   (`output/scored_raw_vs_clean.csv`); `contamination.py` summarizes the share of flags that came
   from navigation; `validate_extract.py` audits 16 pages; `pages_audit.py` classifies the
   automatically discovered United States pages and recomputes endpoint prevalence under
   alternative page rules.
3. `fetch_us_seeds.py`: fetches the curated United States pages (`../data/sample_frame.csv`
   integrity_url / guidance_url) from the Internet Archive (listing via the timemap endpoint,
   earliest capture per distinct digest, at most 16 versions); `output/seed_snapshot_index.csv`,
   `output/seed_coverage.csv`, `output/seed_cdx_captures.csv`.
4. `seed_design.py --rescore --backfill`: the symmetric design (curated page where archived,
   otherwise the screened discovered page in `output/seed_backfill_pages.csv`), panels and
   endpoint prevalence (`output/seed_prevalence.csv`, with and without linked PDFs), and the
   United States event study on the design; `prevalence_by_source.py` splits the United States by
   page source.
5. `fetch_policy_pdfs.py` then `rescore_pdfs.py`: policy documents linked from the endpoint pages
   as PDFs (up to three per institution, nearest capture to the end of the window).
6. `seed_convergence.py`: convergence by pair type, balanced pool, endpoint tests on the
   last-quarter documents (full text, cut to 300 and 600 words, Commonwealth-only, United States
   contrast), per-system and page-type decompositions, placebo texts.
   `convergence_ladder.py` and `paired_matched.py` run the same normalization ladder on the
   automatically discovered pages (robustness).
7. `fetch_cdx.py` and `crawl_density.py`: captures per page and quarter, density against
   exposure, interval-censored adoption dates and a Turnbull estimate.
8. `exposure_robustness.py`, `validation_r1.py`, `rebuild_panel_clean.py`: exposure robustness,
   validation of the codes on the cleaned text, event-study variants on the discovered pages.
9. `make_figures_r1.py`, `make_supplement.py`, `numbers_manifest.py`: figures, supplementary
   tables, and the list of every number the paper quotes.

Stdlib + pandas, numpy, scikit-learn, statsmodels, scipy, lxml, pypdf (Python 3.9).
