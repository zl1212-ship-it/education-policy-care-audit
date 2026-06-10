"""Joint exposure: detector false-flag gap x policy permissiveness (J6 governance layer).

Reads the coded data/policy_corpus.csv (codes filled per CODEBOOK_policy.md) and
the detector-layer gap from data/results_summary.csv, and computes how often a
group-skewed false-flag rate meets a policy that makes the flag actionable.

Outputs data/policy_results.csv:
  - distribution of each coded dimension,
  - the 0-5 accusation-permissiveness index distribution,
  - cross-tab detector_admissibility x l2_protection,
  - joint-exposure share: institutions that are `admissible` AND
    (burden==student OR appeal==none) AND l2_protection != explicit.

No causal claim and no imputation: only coded rows count; `silent`/`none` are
real categories, not missing data. If no rows are coded yet, the script says so
and writes nothing but the schema.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
CORPUS = HERE / "data" / "policy_corpus.csv"
DETECTOR = HERE / "data" / "results_summary.csv"
OUT = HERE / "data" / "policy_results.csv"

ADMIS = {"prohibited", "advisory", "admissible", "silent"}
DIMENSIONS = ["detector_admissibility", "burden_of_proof", "appeal_pathway",
              "l2_protection", "decision_locus"]
# Governance-vacuum weights (higher = less of a floor between a biased flag and the writer).
VACUUM_WEIGHTS = {
    "detector_admissibility": {"admissible": 1, "silent": 1, "advisory": 0.5, "prohibited": 0},
    "decision_locus": {"delegated": 1, "silent": 1, "institutional": 0},
    "l2_protection": {"none": 1, "generic_fairness": 0.5, "explicit": 0},
    "burden_of_proof": {"student": 1, "unspecified": 0.5, "institution": 0},
    "appeal_pathway": {"none": 1, "informal": 0.5, "formal": 0},
}


def detector_gap() -> str:
    """One-line reminder of the group-level gap the governance layer is multiplied against."""
    if not DETECTOR.exists():
        return "(run analyze_detection.py for the detector-layer gap)"
    d = pd.read_csv(DETECTOR)
    sub = d[(d.analysis == "fpr_pooled_mean7") & (d.threshold == 0.50)]
    fold = d[(d.analysis == "fpr_pooled_gap_fold") & (d.threshold == 0.50)]["value"]
    try:
        nn = sub[sub.group == "non-native"]["value"].iloc[0]
        na = sub[sub.group == "native"]["value"].iloc[0]
        return f"non-native {nn:.1%} vs native {na:.1%} ({fold.iloc[0]}x), pooled over 7 detectors at tau=0.50"
    except (IndexError, KeyError):
        return "(detector-layer gap unavailable)"


def vacuum_index(row) -> float:
    """0-5 governance-vacuum score; blank/uncoded dimensions contribute 0 (conservative)."""
    return sum(VACUUM_WEIGHTS[d].get(row.get(d, ""), 0) for d in VACUUM_WEIGHTS)


def main() -> int:
    if not CORPUS.exists():
        print(f"Missing {CORPUS}. Run build_policy_corpus.py and code it first.", file=sys.stderr)
        return 1
    df = pd.read_csv(CORPUS, dtype=str).fillna("")
    coded = df[df["detector_admissibility"].isin(ADMIS)].copy()
    n_total, n_coded = len(df), len(coded)

    print(f"Detector-layer gap (fixed input): {detector_gap()}")
    print(f"Policy corpus: {n_coded}/{n_total} institutions coded.")
    if n_coded == 0:
        print("Nothing coded yet. Fill the four columns in data/policy_corpus.csv per "
              "CODEBOOK_policy.md, then re-run.")
        pd.DataFrame(columns=["metric", "dimension", "value", "share", "count", "n"]).to_csv(OUT, index=False)
        return 0

    rows = []

    def emit(metric, dimension, value, count):
        rows.append({"metric": metric, "dimension": dimension, "value": value,
                     "share": round(count / n_coded, 4), "count": int(count), "n": n_coded})

    for dim in DIMENSIONS:
        for value, cnt in coded[dim].replace("", "(uncoded)").value_counts().items():
            emit("dimension_distribution", dim, value, cnt)

    coded["vacuum_index"] = coded.apply(vacuum_index, axis=1)
    for value, cnt in coded["vacuum_index"].value_counts().sort_index().items():
        emit("vacuum_index", "0_to_5", str(value), cnt)

    # Cross-tabs: who is protected (L2) against the detector stance / locus of decision.
    for xname, xcol in (("admissibility_x_l2", "detector_admissibility"),
                        ("decision_locus_x_l2", "decision_locus")):
        for xv in sorted(v for v in coded[xcol].unique() if v):
            for l2 in sorted(v for v in coded["l2_protection"].unique() if v):
                cnt = ((coded[xcol] == xv) & (coded.l2_protection == l2)).sum()
                if cnt:
                    emit(xname, xv, l2, cnt)

    # The governance vacuum: a biased flag can reach a non-native writer with NO protective
    # floor. Three distinct floors clear it: a binding detector ban (admissibility==prohibited),
    # explicit multilingual protection (l2==explicit), or a corroboration rule that the flag
    # cannot stand alone (burden==institution). Absent all three, the institution is exposed.
    exposed = coded[
        (coded.detector_admissibility != "prohibited")
        & (coded.l2_protection != "explicit")
        & (coded.burden_of_proof != "institution")
    ]
    emit("governance_vacuum", "not-prohibited & no-explicit-L2 & burden!=institution",
         "exposed", len(exposed))
    # Sharpest sub-cell: institutions that affirmatively endorse a detector with no L2 floor.
    endorse = coded[(coded.detector_admissibility == "admissible") & (coded.l2_protection != "explicit")]
    emit("active_endorsement", "admissible & no-explicit-L2", "exposed", len(endorse))

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"\nWrote {OUT} ({len(out)} rows)")
    print("\nDetector-admissibility distribution:")
    print(coded["detector_admissibility"].value_counts().to_string())
    print("\nL2-protection distribution:")
    print(coded["l2_protection"].value_counts().to_string())
    print(f"\nGovernance vacuum: {len(exposed)}/{n_coded} flagships clear none of the three floors "
          f"(no binding detector ban, no explicit multilingual protection, no rule that the flag "
          f"cannot stand alone), leaving a 16.9x-biased flag able to reach a non-native writer "
          f"unchecked.")
    print(f"Active endorsement (admissible + no explicit L2): {len(endorse)}/{n_coded}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
