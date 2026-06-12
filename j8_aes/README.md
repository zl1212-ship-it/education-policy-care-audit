# Automated essay scoring: machine-vs-human score-gap audit

Audits how automated essay scoring (AES) models differ from human raters across
writer subgroups. Standard AES model families are trained to predict the human
score on two public scored-essay corpora; every essay then receives an
out-of-fold machine score (the model that scores an essay never saw it in
training), and the machine-minus-human score difference is compared across
writer subgroups (English-learner status, race/ethnicity, economic
disadvantage, disability, gender). A second layer uses double-rated essays to
benchmark the machine's group-patterned disagreement against the disagreement
between two trained human raters.

## Pipeline

```
fetch_corpora.py     # download PERSUADE 2.0 + ELLIPSE releases -> data/raw/ (gitignored)
build_panel.py       # essay-level panels: ids, human scores, demographics (no essay text)
run_scorers.py       # 3 AES families, out-of-fold + leave-one-prompt-out machine scores
analyze_gaps.py      # machine-minus-human gaps by subgroup; SMD; decision layer
analyze_benchmark.py # human second-rater benchmark + analytic-dimension mechanism
make_figures.py      # figures -> ../paper/blinded-manuscript/
make_tables.py       # tables  -> data/table_*.csv
```

## Scoring protocol

- Families: `handfeat` (transparent hand-crafted features + ridge), `tfidf`
  (word/char n-gram TF-IDF + ridge), `embed` (frozen MiniLM embeddings +
  ridge head). All trained only to reproduce the corpus's human scores.
- Protocols: `oof` (5-fold out-of-fold, fixed seed) and `lopo`
  (leave-one-prompt-out transfer). `data/scorer_quality.csv` records QWK,
  Pearson r, and RMSE per family/protocol so gap results are read against
  engine quality.

## Data

- `data/panel_persuade.csv` — one row per PERSUADE 2.0 essay: human holistic
  score (1-6), task, prompt, writer demographics. Key = `panel_id`
  (`<release>/<essay_id>`; the raw releases' ids collide once).
- `data/panel_ellipse.csv` — one row per ELLIPSE essay: Overall + six analytic
  scores (1-5, half steps), writer demographics. All ELLIPSE writers are
  English language learners.
- `data/rater_pairs.csv` — the two independent human ratings behind each
  released ELLIPSE essay, joined to demographics.
- `data/machine_scores_{persuade,ellipse}.csv` — out-of-fold and
  leave-one-prompt-out machine scores per family, keyed to the panels.
- `data/results_gaps.csv` — group-level metrics (mean gap, SMD, QWK, exact
  agreement, r, RMSE) and focal-minus-reference differentials (raw and
  conditional-on-human-score) with bootstrap 95% CIs.
- `data/results_decision.csv` — pass/fail decision layer at integer cutoffs:
  human and machine pass rates, demotion and promotion rates by group.
- `data/results_benchmark.csv` — second-opinion benchmark (human rater 2 vs
  machine, same essays) and machine-residual vs analytic-dimension partial
  correlations.

Essay text is never committed: `data/raw/` is gitignored and reproducible by
rerunning `fetch_corpora.py`; the panels carry ids, scores, and demographics
only. Corpus citations, licenses, and the embedding-model pin are in
`SOURCES.md`.
