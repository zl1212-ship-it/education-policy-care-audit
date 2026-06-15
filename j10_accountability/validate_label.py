"""Validate the reconstructed identification list against an official state list.

The national layer reconstructs the ESSA lowest-five-percent rule with a transparent
composite, and is explicit that this is a stylized device, not any state's official list.
A reviewer can fairly ask how close the reconstruction comes to a real list. Washington
publishes its official comprehensive-support designation in the same year as the panel's
data (the 2018 WSIF run), so we compare the schools our reconstruction flags in Washington
against Washington's official comprehensive-support schools.

The comparison is same-year (both 2018) to avoid confounding the reconstruction with drift
over time. We report precision (the share of reconstructed-flagged schools that are
officially identified), recall (the share of officially identified schools the
reconstruction flags), and the base rate (the share of schools identified at all), so the
precision can be read against chance.

Output: prints the metrics; writes data/results_label_validation.csv.

Run:  python3 validate_label.py
"""
from pathlib import Path

import pandas as pd

from build_rdd_states import socrata

HERE = Path(__file__).parent
INST = HERE / "data" / "label_instability.csv"
FRAME = HERE / "data" / "school_frame.csv"
OUT = HERE / "data" / "results_label_validation.csv"


def main():
    li = pd.read_csv(INST, dtype={"ncessch": str})
    mine = li[(li["state"] == "WA") & (li["identified_baseline"] == 1)].copy()

    frame = pd.read_csv(FRAME, dtype={"ncessch": str, "seasch": str})
    wa = frame[frame["state"] == "WA"].copy()
    wa["school_code"] = wa["seasch"].astype(str).str.split("-").str[-1]
    mine = mine.merge(wa[["ncessch", "school_code"]], on="ncessch", how="left")

    # Washington's official comprehensive-support list, same year as the panel (2018 WSIF run)
    w = socrata("data.wa.gov", "52db-bekd", where="student_group='All Students'")
    w["school_code"] = w["school_code"].astype(str)
    w["official"] = w["support_tier"].astype(str).str.contains("Comprehensive")

    A = set(mine["school_code"].dropna())          # reconstructed bottom-5%
    B = set(w.loc[w["official"], "school_code"])    # official comprehensive support
    inter = len(A & B)
    base_rate = w["official"].mean()
    precision = inter / len(A)
    recall = inter / len(B)
    rows = [
        ("reconstructed_n", len(A)), ("official_n", len(B)), ("intersection", inter),
        ("precision", precision), ("recall", recall),
        ("jaccard", inter / len(A | B)), ("base_rate", base_rate),
        ("precision_over_base_rate", precision / base_rate),
    ]
    pd.DataFrame(rows, columns=["statistic", "value"]).to_csv(OUT, index=False)

    print("reconstruction vs Washington's official 2018 comprehensive-support list:")
    print(f"  reconstructed flagged: {len(A)}   official: {len(B)}   overlap: {inter}")
    print(f"  precision = {precision:.2f} (share of flagged that are officially identified)")
    print(f"  recall    = {recall:.2f} (official list is broader: it folds in low-graduation"
          f" and other rules beyond the bottom 5%)")
    print(f"  base rate = {base_rate:.2f}; precision is {precision/base_rate:.1f}x chance")
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()
