# J6 — AI-writing-detector bias and governance audit

Two coordinated audit pipelines:

1. **Detector layer.** Re-scores public corpora of human-written essays (so any positive is
   a false positive) with open-source AI-writing detectors and records the false-positive
   rate by the author's native / non-native English status, per detector and threshold.
2. **Governance layer.** Collects the academic-integrity / AI policies of the 50 state
   flagship public universities and codes each for how detector output is treated:
   admissibility as evidence, burden of proof, appeal pathway, and protection for
   multilingual writers (protocol in `CODEBOOK_policy.md`).

A joint analysis crosses the two layers (detector false-positive gaps x policy
admissibility codes).

## Pipeline
```
fetch_anchor_data.py    # download Liang et al. (2023) public human-essay corpora (verbatim)
build_essay_panel.py    # assemble essays -> panel + native/non-native label + provenance
run_detectors.py        # score every human essay with current open detectors -> AI-probability
analyze_detection.py    # false-positive rate by L1 status; calibration -> data/results_summary.csv
build_policy_corpus.py  # collect public university integrity/AI policies -> coded panel
analyze_policy.py       # joint exposure (FPR gap x policy admissibility) -> data/results_summary.csv
make_figures.py         # Figures -> ../paper/blinded-manuscript/j6_figure{1,2,3}.{pdf,png}
```

## Data
- `data/essays_panel.csv` — one row per human essay: native/non-native label, source corpus, length, and per-detector AI-probability scores (provenance via corpus).
- `data/results_summary.csv` — detector-layer statistics (false-positive rate by L1 status, per-detector + pooled + unanimous-flag, threshold sensitivity).
- `data/policy_registry.csv` — input: curated institution policy URLs (institution, state, control, policy_type, url).
- `data/policy_corpus.csv` — fetched policies with provenance + the codebook columns, coded per `CODEBOOK_policy.md`.
- `data/policy_results.csv` — governance-layer statistics (code distributions, permissiveness index, joint exposure).
- `data/policy_corpus_secondcoder.csv`, `data/policy_corpus_handcoder.csv` — independent second-coder pass over a random fifth of the census and an author hand-recode of the same institutions, both from the stored text.
- `data/kappa_results.csv`, `data/kappa_results_human.csv` — per-dimension inter-rater agreement for those passes.

Detectors are open-source and version-pinned (see `SOURCES.md`). Essay corpora are public.
Codes are auditable against the fetched policy text archived under `data/policy_raw/`.
