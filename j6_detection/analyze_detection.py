"""False-accusation rate by native vs non-native English status (J6 detector layer).

What this measures
------------------
Reads data/essays_panel.csv. Every essay is human-written, so a detector that
scores one above the decision threshold tau is FALSELY accusing a human author.
A detector "flags" an essay when its AI-probability exceeds tau (primary tau =
0.50). The false-positive rate (FPR) for a group is the share of that group's
human essays a detector flags. The audit quantity is the GAP in FPR between
non-native and native writers:

  - per detector (seven 2023 detectors),
  - pooled as the mean FPR across the seven detectors,
  - the UNANIMOUS-flag rate: the share of essays every one of the seven detectors
    flags (the configuration an instructor is most likely to treat as proof),
  - the majority-flag rate (>= 4 of 7).

This is a measurement of detector behavior on a fixed public corpus, not a causal
claim. Threshold sensitivity (tau in {0.25, 0.50, 0.75, 0.90}) is reported so the
headline does not hinge on one cutoff. Every number is written to
data/results_summary.csv.

Run build_essay_panel.py first.
"""
import sys
from pathlib import Path

import pandas as pd

PANEL = Path(__file__).parent / "data" / "essays_panel.csv"
OUT = Path(__file__).parent / "data" / "results_summary.csv"

DETECTORS = ["HFOpenAI", "GPTZero", "Crossplag", "ZeroGPT", "OriginalityAI", "Quil", "Sapling"]
THRESHOLDS = [0.25, 0.50, 0.75, 0.90]
PRIMARY = 0.50
GROUPS = ["non-native", "native"]


def _ratio(num: float, den: float) -> float:
    """Fold-difference non-native/native; inf when native FPR is exactly zero."""
    return float("inf") if den == 0 else round(num / den, 2)


def main() -> int:
    if not PANEL.exists():
        print(f"Missing {PANEL}. Run build_essay_panel.py first.", file=sys.stderr)
        return 1
    panel = pd.read_csv(PANEL)
    n = panel.groupby("l1_status").size().to_dict()  # {'native':158,'non-native':91}

    rows = []

    def emit(analysis, detector, threshold, group, value, count=None):
        rows.append(
            {
                "analysis": analysis,
                "detector": detector,
                "threshold": threshold,
                "group": group,
                "value": value,
                "count": count,
                "n_group": n.get(group),
            }
        )

    # Per-essay flag matrix at each threshold: how many of the seven detectors flag it.
    for tau in THRESHOLDS:
        flags = pd.DataFrame(
            {det: (panel[det] > tau).astype(int) for det in DETECTORS}, index=panel.index
        )
        n_flagged = flags.sum(axis=1)
        unanimous = (n_flagged == len(DETECTORS)).astype(int)
        majority = (n_flagged >= 4).astype(int)
        grp = panel["l1_status"]

        # Per-detector FPR by group, and the non-native/native fold gap.
        for det in DETECTORS:
            fpr = {g: flags.loc[grp == g, det].mean() for g in GROUPS}
            for g in GROUPS:
                emit("fpr_by_detector", det, tau, g, round(fpr[g], 4),
                     int(flags.loc[grp == g, det].sum()))
            emit("fpr_gap_fold", det, tau, "non-native/native",
                 _ratio(fpr["non-native"], fpr["native"]))

        # Pooled across the seven detectors (mean per-detector FPR).
        pooled = {
            g: pd.Series({det: flags.loc[grp == g, det].mean() for det in DETECTORS}).mean()
            for g in GROUPS
        }
        for g in GROUPS:
            emit("fpr_pooled_mean7", "mean_of_7", tau, g, round(pooled[g], 4))
        emit("fpr_pooled_gap_fold", "mean_of_7", tau, "non-native/native",
             _ratio(pooled["non-native"], pooled["native"]))

        # Unanimous (all seven) and majority (>= 4 of 7) flag rates by group.
        for label, series in (("all_7", unanimous), ("ge4_of_7", majority)):
            for g in GROUPS:
                sel = series[grp == g]
                emit(f"flag_{label}", label, tau, g, round(sel.mean(), 4), int(sel.sum()))

    panel_out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel_out.to_csv(OUT, index=False)

    # Console summary at the primary threshold.
    print(f"Wrote {OUT}  ({len(panel_out)} rows)")
    print(f"\nGroup sizes: {n}")
    print(f"\n=== Primary threshold tau = {PRIMARY} ===")
    print("\nPer-detector false-accusation rate (human essays flagged as AI):")
    hdr = f"  {'detector':<14}{'non-native':>12}{'native':>10}{'fold':>8}"
    print(hdr)
    sub = panel_out[(panel_out.threshold == PRIMARY)]
    for det in DETECTORS:
        nn = sub[(sub.analysis == "fpr_by_detector") & (sub.detector == det) &
                 (sub.group == "non-native")]["value"].iloc[0]
        na = sub[(sub.analysis == "fpr_by_detector") & (sub.detector == det) &
                 (sub.group == "native")]["value"].iloc[0]
        fold = sub[(sub.analysis == "fpr_gap_fold") & (sub.detector == det)]["value"].iloc[0]
        print(f"  {det:<14}{nn:>12.1%}{na:>10.1%}{fold:>8}")

    pooled_nn = sub[(sub.analysis == "fpr_pooled_mean7") & (sub.group == "non-native")]["value"].iloc[0]
    pooled_na = sub[(sub.analysis == "fpr_pooled_mean7") & (sub.group == "native")]["value"].iloc[0]
    pooled_fold = sub[sub.analysis == "fpr_pooled_gap_fold"]["value"].iloc[0]
    una_nn = sub[(sub.analysis == "flag_all_7") & (sub.group == "non-native")]
    una_na = sub[(sub.analysis == "flag_all_7") & (sub.group == "native")]
    print("\nHeadline:")
    print(f"  Pooled mean false-accusation rate: non-native {pooled_nn:.1%} vs "
          f"native {pooled_na:.1%}  ({pooled_fold}x)")
    print(f"  Flagged by ALL seven detectors: "
          f"non-native {int(una_nn['count'].iloc[0])}/{n['non-native']} "
          f"({una_nn['value'].iloc[0]:.1%}) vs "
          f"native {int(una_na['count'].iloc[0])}/{n['native']} "
          f"({una_na['value'].iloc[0]:.1%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
