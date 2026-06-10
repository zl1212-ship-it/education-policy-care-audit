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
PERMISSIVE_ADMIS = {"admissible": 2, "advisory": 1, "prohibited": 0, "silent": 0}


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


def permissiveness(row) -> float:
    s = PERMISSIVE_ADMIS.get(row["detector_admissibility"], 0)
    s += 1 if row["burden_of_proof"] == "student" else 0
    s += 1 if row["appeal_pathway"] == "none" else 0
    s += {"none": 1, "generic_fairness": 0.5, "explicit": 0}.get(row["l2_protection"], 0)
    return s


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

    for dim in ["detector_admissibility", "burden_of_proof", "appeal_pathway", "l2_protection"]:
        for value, cnt in coded[dim].value_counts().items():
            emit("dimension_distribution", dim, value, cnt)

    coded["permissiveness"] = coded.apply(permissiveness, axis=1)
    for value, cnt in coded["permissiveness"].value_counts().sort_index().items():
        emit("permissiveness_index", "0_to_5", str(value), cnt)

    # Cross-tab admissibility x L2 protection.
    for adm in sorted(coded["detector_admissibility"].unique()):
        for l2 in sorted(coded["l2_protection"].unique()):
            cnt = ((coded.detector_admissibility == adm) & (coded.l2_protection == l2)).sum()
            if cnt:
                emit("admissibility_x_l2", adm, l2, cnt)

    # Joint-exposure cell.
    exposed = coded[
        (coded.detector_admissibility == "admissible")
        & ((coded.burden_of_proof == "student") | (coded.appeal_pathway == "none"))
        & (coded.l2_protection != "explicit")
    ]
    emit("joint_exposure", "admissible & (student-burden|no-appeal) & no-explicit-L2",
         "exposed", len(exposed))

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"\nWrote {OUT} ({len(out)} rows)")
    print(f"\nDetector-admissibility distribution:")
    print(coded["detector_admissibility"].value_counts().to_string())
    print(f"\nJoint exposure: {len(exposed)}/{n_coded} institutions admit detector output as "
          f"evidence, put the writer at risk (student burden or no appeal), and give multilingual "
          f"writers no explicit protection.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
