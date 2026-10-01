"""Robustness: a third human corpus sharpens the mechanism of the language penalty.

CS224N_real_145 is 145 graduate technical essays (Stanford NLP course final
reports), a population with many international authors writing sophisticated,
fluent English. If the detector penalty fell on international or technical writing
as such, this corpus would be misflagged heavily. It is not. This script computes
the pooled false-accusation rate for the three human corpora over the FIVE detectors
scored for all of them (CS224N lacks Quil and Sapling), so the comparison is
apples to apples, and writes the result to data/results_summary.csv.

Reads data/essays_panel.csv (native/non-native) and the CS224N detector scores under
data/anchor/. Run after build_essay_panel.py.
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
PANEL = HERE / "data" / "essays_panel.csv"
CS = HERE / "data" / "anchor" / "Data_and_Results" / "Human_Data" / "CS224N_real_145"
OUT = HERE / "data" / "results_summary.csv"
SHARED = ["HFOpenAI", "GPTZero", "Crossplag", "ZeroGPT", "OriginalityAI"]  # present in all 3 corpora
TAU = 0.50


def pooled_fpr(flag_by_detector):
    """Mean over detectors of the share of essays flagged (> tau)."""
    return sum(flag_by_detector) / len(flag_by_detector)


def main() -> int:
    if not PANEL.exists() or not CS.exists():
        print("Need essays_panel.csv and the CS224N anchor corpus.", file=sys.stderr)
        return 1
    panel = pd.read_csv(PANEL)

    rows = []  # (group, n, pooled_fpr over SHARED)
    for grp in ("native", "non-native"):
        sub = panel[panel.l1_status == grp]
        per = [(sub[d] > TAU).mean() for d in SHARED]
        rows.append((grp, len(sub), pooled_fpr(per)))

    # CS224N from the anchor scores.
    n_cs = len(json.load(open(CS / "data.json")))
    per_cs = []
    for d in SHARED:
        s = json.load(open(CS / f"{d}.json"))
        per_cs.append(sum(1 for e in s if (e.get("score") or 0) > TAU) / len(s))
    rows.append(("mixed-CS224N", n_cs, pooled_fpr(per_cs)))

    print(f"Pooled false-accusation rate over the {len(SHARED)} shared detectors (tau={TAU}):")
    for grp, n, fpr in rows:
        print(f"  {grp:<16} {fpr:>6.1%}   (n={n})")

    # Append to results_summary.csv as robustness rows.
    res = pd.read_csv(OUT)
    res = res[res.analysis != "cs224n_robustness_pooled5"]
    add = pd.DataFrame([{"analysis": "cs224n_robustness_pooled5", "detector": "mean_of_5",
                         "threshold": TAU, "group": grp, "value": round(fpr, 4),
                         "count": None, "n_group": n} for grp, n, fpr in rows])
    pd.concat([res, add], ignore_index=True).to_csv(OUT, index=False)
    print(f"\nWrote robustness rows to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
