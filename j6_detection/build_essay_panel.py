"""Assemble Liang et al. (2023) human essays into J6's analysis panel.

What this builds and why
------------------------
Every essay in the three anchor corpora is HUMAN-written, so any detector that
scores one above the decision threshold is producing a FALSE accusation. This
script pairs each essay with (a) the author's native vs non-native English
status, which is fixed by the source corpus, and (b) the AI-probability assigned
by each of the seven detectors Liang et al. (2023) scored. analyze_detection.py
then reads this panel and measures how the false-positive (false-accusation)
rate splits by native vs non-native status.

Native status is a corpus-level fact here, not an essay-level inference:
  - TOEFL_real_91             -> non-native (essays by TOEFL test takers)
  - HewlettStudentEssay_real_88 -> native   (US 8th-grade writing assessment)
  - CollegeEssay_real_70      -> native     (US college admission essays)

CS224N_real_145 is downloaded too but excluded from the panel: its authors are a
mixed-L1 graduate population, so it does not carry a clean native/non-native
label. It is available for later robustness work, not the primary contrast.

Input : data/anchor/Data_and_Results/Human_Data/<corpus>/{data.json,<detector>.json}
Output: data/essays_panel.csv  (one row per essay; raw essay text is NOT
        re-published, only length and the detector scores)

Run fetch_anchor_data.py first. Stdlib + pandas only.
"""
import json
import sys
from pathlib import Path

import pandas as pd

HUMAN = Path(__file__).parent / "data" / "anchor" / "Data_and_Results" / "Human_Data"
OUT = Path(__file__).parent / "data" / "essays_panel.csv"

# Corpus -> native English status. Only essays with a clean L1 label enter the panel.
CORPORA = {
    "TOEFL_real_91": "non-native",
    "HewlettStudentEssay_real_88": "native",
    "CollegeEssay_real_70": "native",
}

# The seven detectors Liang et al. (2023) scored; each stores P(AI-generated) in "score".
DETECTORS = ["HFOpenAI", "GPTZero", "Crossplag", "ZeroGPT", "OriginalityAI", "Quil", "Sapling"]


def _load(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_corpus(corpus: str, l1: str) -> pd.DataFrame:
    cdir = HUMAN / corpus
    docs = _load(cdir / "data.json")
    n = len(docs)
    rows = []
    for i, d in enumerate(docs):
        text = d["document"]
        rows.append(
            {
                "essay_id": f"{corpus}/{i:03d}",
                "corpus": corpus,
                "l1_status": l1,
                "n_words": len(text.split()),
                "n_chars": len(text),
            }
        )
    df = pd.DataFrame(rows)

    for det in DETECTORS:
        scored = _load(cdir / f"{det}.json")
        if len(scored) != n:
            raise ValueError(f"{corpus}/{det}: {len(scored)} scores vs {n} essays")
        # Detector files are index-aligned to data.json; verify by document text.
        for i in range(n):
            if scored[i].get("document") != docs[i]["document"]:
                raise ValueError(f"{corpus}/{det}: document mismatch at row {i}")
        df[det] = [scored[i]["score"] for i in range(n)]

    return df


def main() -> int:
    if not HUMAN.exists():
        print(f"Missing {HUMAN}. Run fetch_anchor_data.py first.", file=sys.stderr)
        return 1

    parts = [build_corpus(c, l1) for c, l1 in CORPORA.items()]
    panel = pd.concat(parts, ignore_index=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False)

    print(f"Wrote {OUT}  ({len(panel)} essays)")
    print(panel.groupby(["l1_status", "corpus"]).size().to_string())
    print("\nMean P(AI) by L1 status across the seven detectors:")
    print(panel.groupby("l1_status")[DETECTORS].mean().round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
