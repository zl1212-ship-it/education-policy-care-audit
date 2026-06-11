"""Consequence mapping: how a face-detection failure becomes a student's problem.

Tabulates the vendor codes (data/vendor_corpus.csv, coded per CODEBOOK_vendor.md
against the archived text in data/vendor_raw/) and joins them to the measured
detection layer. The bridge is mechanical, not statistical: for every vendor whose
documentation records an automatic event when no face is detected, the probability
of that event is the face detector's miss rate, so the group ratio of flag
exposure equals the measured miss-rate ratio from analyze_detection.py. The join
states the implied per-check flag-rate ratios (Black/White and dark/very-light
ITA) at native exposure and at the dimmest condition for each open detector.

Caveat carried from the README: commercial engines are closed; the implied ratios
describe the open detector families the same vision stack builds on, not any named
vendor's model.

Output: data/vendor_results.csv (kind in {distribution, bridge}).
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "data", "vendor_corpus.csv")
DETECTION = os.path.join(HERE, "data", "results_summary.csv")
OUT_CSV = os.path.join(HERE, "data", "vendor_results.csv")

DIMENSIONS = ["noface_flag", "id_gate", "consequence_path", "human_review",
              "lighting_burden", "bias_acknowledgment"]


def main():
    corpus = pd.read_csv(CORPUS)
    n = len(corpus)
    rows = []
    print(f"{n} vendors coded\n")
    for dim in DIMENSIONS:
        counts = corpus[dim].fillna("not_documented").value_counts()
        for code, k in counts.items():
            rows.append({"kind": "distribution", "dimension": dim, "code": code,
                         "n_vendors": int(k),
                         "vendors": "|".join(corpus.loc[corpus[dim] == code,
                                                        "vendor"])})
        print(f"{dim}: " + ", ".join(f"{c}={k}" for c, k in counts.items()))

    auto = corpus[corpus["noface_flag"] == "automatic_flag"]["vendor"]
    det = pd.read_csv(DETECTION)
    bridge = det[(det["kind"] == "contrast") & (det["sample"] == "all")
                 & (det["exposure"].isin([1.0, 0.15]))]
    print(f"\nBridge: {len(auto)} of {n} vendors document an automatic no-face "
          "event; for them the per-check flag-rate ratio is the detector's "
          "miss-rate ratio:")
    for _, r in bridge.iterrows():
        rows.append({"kind": "bridge", "dimension": "implied_flag_ratio",
                     "code": f"{r['detector']}@exp{r['exposure']}",
                     "stratifier": r["stratifier"], "group": r["group"],
                     "rate_dark": r["miss_rate"], "rate_light":
                     r["comparison_rate"], "ratio": r["ratio"],
                     "p_fisher": r["p_fisher"],
                     "vendors": "|".join(auto)})
        print(f"  {r['detector']:<10} exp={r['exposure']:<5} {r['stratifier']:<9}"
              f" {r['group']}: {r['miss_rate']:.2%} vs "
              f"{r['comparison_rate']:.2%} (x{r['ratio']})")

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"\nwrote -> {OUT_CSV}")

if __name__ == "__main__":
    main()
