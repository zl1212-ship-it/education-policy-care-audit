"""Assemble the two scored-essay corpora into essay-level analysis panels.

What this builds and why
------------------------
Both corpora pair student essays with HUMAN scores and writer demographics.
run_scorers.py later attaches machine (AES) scores to the same essay ids, and
analyze_gaps.py measures how the machine-minus-human score difference splits
by the writer's English-learner status and other subgroups.

1. PERSUADE 2.0 ships at the discourse-element level (one row per annotated
   argument element, full text repeated). This script deduplicates to one row
   per essay and keeps the holistic score (1-6), task, prompt, and writer
   demographics: gender, grade, ELL status, race/ethnicity, economic
   disadvantage, disability (IEP/504). Train and test releases are pooled;
   `competition_set` preserves provenance.
2. ELLIPSE is essay-level already (Overall + six analytic scores on a 1-5
   scale, in 0.5 steps; all writers are English language learners). Train and
   test releases are pooled; `set` preserves provenance.
3. The ELLIPSE raw-rater file holds the two independent ratings behind each
   essay in the full ~9k scoring effort. Joining it to the final corpus
   metadata by text id gives a human-vs-human disagreement benchmark with
   demographics, against which the machine-vs-human gap is later compared.

Essay text is NOT written into the panels: it stays under data/raw/
(gitignored), and scripts that need it re-read it from there by essay id.
The committed panels carry ids, scores, and demographics only.

Cleaning: ELL status values of NaN or blank are recoded to missing and those
essays are excluded from subgroup contrasts but kept for model training
(models should see the full population they would score in deployment).

Input : data/raw/  (run fetch_corpora.py first)
Output: data/panel_persuade.csv, data/panel_ellipse.csv, data/rater_pairs.csv
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent / "data" / "raw"
DATA = Path(__file__).parent / "data"

PERSUADE_FILES = {
    "train": "persuade_2.0_human_scores_demo_id_github.csv",
    "test": "persuade_corpus_2.0_test.csv",
}
PERSUADE_COLS = [
    "essay_id", "competition_set", "holistic_essay_score", "task",
    "prompt_name", "gender", "grade_level", "ell_status", "race_ethnicity",
    "economically_disadvantaged", "student_disability_status",
    "essay_word_count",
]

ELLIPSE_FILES = {
    "train": "ELLIPSE_Final_github_train.csv",
    "test": "ELLIPSE_Final_github_test.csv",
}
ELLIPSE_SCORES = ["Overall", "Cohesion", "Syntax", "Vocabulary",
                  "Phraseology", "Grammar", "Conventions"]
ELLIPSE_COLS = (["text_id_kaggle", "set", "task", "prompt", "gender", "grade",
                 "race_ethnicity", "SES", "num_words"] + ELLIPSE_SCORES)


def build_persuade() -> pd.DataFrame:
    parts = []
    for split, fname in PERSUADE_FILES.items():
        df = pd.read_csv(RAW / fname, usecols=PERSUADE_COLS)
        df = df.drop_duplicates("essay_id")
        # essay_id alone is not unique across the two releases (one collision
        # with different text), so the panel key is "<release>/<essay_id>".
        df.insert(0, "panel_id", split + "/" + df.essay_id.astype(str))
        parts.append(df)
    panel = pd.concat(parts, ignore_index=True)
    if panel.panel_id.duplicated().any():
        raise ValueError("panel_id collides across PERSUADE releases")
    # ELL status: keep Yes/No, recode blanks and NaN to missing.
    ell = panel.ell_status.astype(str).str.strip()
    panel["ell_status"] = ell.where(ell.isin(["Yes", "No"]))
    return panel


def build_ellipse() -> pd.DataFrame:
    parts = []
    for split, fname in ELLIPSE_FILES.items():
        df = pd.read_csv(RAW / fname, usecols=ELLIPSE_COLS)
        parts.append(df)
    panel = pd.concat(parts, ignore_index=True)
    if panel.text_id_kaggle.duplicated().any():
        raise ValueError("text_id_kaggle collides across ELLIPSE releases")
    return panel


def build_rater_pairs(ellipse: pd.DataFrame) -> pd.DataFrame:
    """Two independent human ratings per essay, joined to demographics.

    Only essays that (a) carry both ratings in the raw scoring file and
    (b) appear in the final released corpus (reliable texts with metadata)
    enter the benchmark.
    """
    raw = pd.read_csv(RAW / "ellipsis_raw_rater_scores_anon_all_essay.csv")
    pairs = raw.dropna(subset=["Overall_1", "Overall_2"])[
        ["text_id_kaggle", "Rater_1", "Rater_2",
         "Overall_1", "Overall_2"]].copy()
    meta = ellipse[["text_id_kaggle", "gender", "grade", "race_ethnicity",
                    "SES", "prompt"]]
    pairs = pairs.merge(meta, on="text_id_kaggle", how="inner")
    return pairs


def main() -> int:
    if not RAW.exists():
        print(f"Missing {RAW}. Run fetch_corpora.py first.", file=sys.stderr)
        return 1

    persuade = build_persuade()
    persuade.to_csv(DATA / "panel_persuade.csv", index=False)
    print(f"panel_persuade.csv: {len(persuade)} essays")
    print("  ELL status:", persuade.ell_status.value_counts(dropna=False).to_dict())
    print("  mean holistic by ELL:",
          persuade.groupby("ell_status").holistic_essay_score.mean()
          .round(3).to_dict())

    ellipse = build_ellipse()
    ellipse.to_csv(DATA / "panel_ellipse.csv", index=False)
    print(f"panel_ellipse.csv: {len(ellipse)} essays "
          f"(all writers are English language learners)")
    print("  mean Overall:", round(ellipse.Overall.mean(), 3))

    pairs = build_rater_pairs(ellipse)
    pairs.to_csv(DATA / "rater_pairs.csv", index=False)
    print(f"rater_pairs.csv: {len(pairs)} double-rated essays with metadata")
    print("  exact agreement:",
          round((pairs.Overall_1 == pairs.Overall_2).mean(), 3),
          "| mean |r1-r2|:",
          round((pairs.Overall_1 - pairs.Overall_2).abs().mean(), 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
