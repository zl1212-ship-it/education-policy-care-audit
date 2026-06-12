# sources and provenance

## Scored-essay corpora (both CC BY-NC-SA 4.0, Learning Agency Lab releases)

- **PERSUADE 2.0** — 25,995 argumentative essays by U.S. 6th-12th grade
  students, 15 prompts, two task types; human holistic score (1-6) and writer
  demographics (gender, grade, ELL status, race/ethnicity, economic
  disadvantage, disability = IEP/504 per the release README).
  - Repo: https://github.com/scrosseye/persuade_corpus_2.0 (CSVs hosted on
    Google Drive, links and the test-zip password in that README)
  - Paper: Crossley, S. A., Baffour, P., Tian, Y., Franklin, A., Benner, M., &
    Boser, U. (2024). A large-scale corpus for assessing written argumentation:
    PERSUADE 2.0. *Assessing Writing*, 61, 100865.
  - The release is discourse-element-level; `build_panel.py` deduplicates to
    one row per essay. One `essay_id` collides across the train and test
    releases with different text, so the panel key is `<release>/<essay_id>`.

- **ELLIPSE** — 6,482 released essays by English-language-learner students
  (grades 8-12, 44 prompts), human Overall + six analytic proficiency scores
  (cohesion, syntax, vocabulary, phraseology, grammar, conventions; 1-5 in
  half steps) and writer demographics (gender, grade, race/ethnicity, economic
  status). The companion raw file holds the two independent ratings per essay
  for the full ~8.9k scoring effort (rater ids anonymized).
  - Repo: https://github.com/scrosseye/ELLIPSE-Corpus (files in-repo, zip
    passwords in that README)
  - Paper: Crossley, S. A., Tian, Y., Baffour, P., Franklin, A., Kim, Y.,
    Morris, W., Benner, M., Picou, A., & Boser, U. (2023). Measuring second
    language proficiency using the ELLIPSE corpus. *International Journal of
    Learner Corpus Research*, 9(2), 248-269.

Both corpora are pinned (fetch_corpora.py): the ELLIPSE git ref is pinned to
commit `dc3b8f0b` and the PERSUADE Drive files are versioned by the release
README.

## Models (run_scorers.py)

- `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face) — frozen encoder for
  the `embed` family; mean-pooled last hidden state, 512-token truncation.
  Revision pinned to `1110a243` in run_scorers.py.
- `handfeat` and `tfidf` families are defined entirely in `run_scorers.py`
  (scikit-learn ridge regression on transparent features / TF-IDF n-grams);
  the macOS `/usr/share/dict/words` list supplies the out-of-vocabulary
  feature.

## Evaluation frameworks the metrics follow

- Williamson, D. M., Xi, X., & Breyer, F. J. (2012). A framework for
  evaluation and use of automated scoring. *Educational Measurement: Issues
  and Practice*, 31(1), 2-13. (standardized mean difference flag)
- Loukina, A., Madnani, N., & Zechner, K. (2019). The many dimensions of
  algorithmic fairness in educational applications. *Proc. 14th Workshop on
  Innovative Use of NLP for Building Educational Applications*, 1-10.
  (overall vs conditional score-difference fairness metrics)
