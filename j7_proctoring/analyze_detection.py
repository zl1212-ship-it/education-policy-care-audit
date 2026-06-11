"""Detection-failure rates by skin tone: the J7 estimand and inference.

Estimand: the probability that a detector returns "no face" on an image that
contains exactly one face (a guaranteed miss, the proctoring "no face detected"
flag), contrasted across skin-tone strata. Identification is by direct measurement:
the full FairFace validation set is enumerated, every image holds one face by
dataset construction, and the detector is a deterministic function of the image, so
group differences in the miss rate are measured, not estimated from a sample of a
larger frame. Inference (Wilson intervals, Fisher exact tests) treats the images as
draws from the population of webcam-like face photographs.

Strata come from data/face_panel.csv two ways, reported in parallel:
- tone_bin: image-derived ITA mapped to the six Del Bino categories (relative
  ordering; see build_face_panel.py for the calibration caveat);
- race: FairFace's author-assigned perceived-race label (independent of our
  pixel pipeline).

For each detector x exposure: per-stratum miss rates with 95% Wilson intervals; the
darkest-vs-lightest tone contrast and the Black-vs-White contrast (risk difference,
fold ratio, Fisher exact p); and the Spearman rank correlation between continuous
ITA and detection as a binning-free trend check.

Every block is computed twice: on the full panel (sample=all) and on adults only
(sample=adult, FairFace age 20+). Children photograph lighter on ITA and are harder
to detect (smaller faces), so age can confound the tone gradient; the adult
restriction is the robustness check that holds the examinee population fixed, and
it matches the proctoring setting (exam-takers are adults).

Output: data/results_summary.csv (kind in {rate, contrast, trend}).
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL_CSV = os.path.join(HERE, "data", "face_panel.csv")
OUTCOMES_CSV = os.path.join(HERE, "data", "detection_outcomes.csv")
OUT_CSV = os.path.join(HERE, "data", "results_summary.csv")

TONE_ORDER = ["very_light", "light", "intermediate", "tan", "brown", "dark"]
RACE_ORDER = ["White", "East Asian", "Latino_Hispanic", "Middle Eastern",
              "Southeast Asian", "Indian", "Black"]
CHILD_AGES = ["0-2", "3-9", "10-19"]


def wilson(misses, n, z=1.959963984540054):
    if n == 0:
        return np.nan, np.nan
    p = misses / n
    den = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    return center - half, center + half


def contrast(d, group_col, g_dark, g_light):
    a = d[d[group_col] == g_dark]
    b = d[d[group_col] == g_light]
    ma, na = int((1 - a["detected"]).sum()), len(a)
    mb, nb = int((1 - b["detected"]).sum()), len(b)
    ra, rb = ma / na, mb / nb
    _, p = stats.fisher_exact([[ma, na - ma], [mb, nb - mb]])
    return {
        "group": f"{g_dark} vs {g_light}", "n": na + nb,
        "miss_rate": round(ra, 4), "comparison_rate": round(rb, 4),
        "risk_diff": round(ra - rb, 4),
        "ratio": round(ra / rb, 2) if rb > 0 else np.inf,
        "p_fisher": p,
    }


def main():
    panel = pd.read_csv(PANEL_CSV)
    outcomes = pd.read_csv(OUTCOMES_CSV)
    d = outcomes.merge(panel, on="file", how="left")

    rows = []
    samples = {"all": d, "adult": d[~d["age"].isin(CHILD_AGES)]}
    for sample, ds in samples.items():
        for (det, exp), g in ds.groupby(["detector", "exposure"]):
            for strat, order in (("tone_bin", TONE_ORDER), ("race", RACE_ORDER)):
                for grp in order:
                    gg = g[g[strat] == grp]
                    n = len(gg)
                    misses = int((1 - gg["detected"]).sum())
                    lo, hi = wilson(misses, n)
                    rows.append({"kind": "rate", "sample": sample, "detector": det,
                                 "exposure": exp, "stratifier": strat, "group": grp,
                                 "n": n, "misses": misses,
                                 "miss_rate": round(misses / n, 4),
                                 "wilson_lo": round(lo, 4),
                                 "wilson_hi": round(hi, 4)})
            for strat, g_dark, g_light in (("tone_bin", "dark", "very_light"),
                                           ("race", "Black", "White")):
                c = contrast(g, strat, g_dark, g_light)
                c.update({"kind": "contrast", "sample": sample, "detector": det,
                          "exposure": exp, "stratifier": strat})
                rows.append(c)
            rho, p = stats.spearmanr(g["ita"], g["detected"])
            rows.append({"kind": "trend", "sample": sample, "detector": det,
                         "exposure": exp, "stratifier": "ita_continuous",
                         "group": "spearman", "n": len(g),
                         "ratio": round(rho, 4), "p_fisher": p})

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {len(out)} rows -> {OUT_CSV}\n")

    for sample, ds in samples.items():
        for (det, exp), g in ds.groupby(["detector", "exposure"]):
            overall = 1 - g["detected"].mean()
            print(f"=== [{sample}] {det} exposure={exp} "
                  f"overall miss {overall:.3%}")
            t = (g.assign(miss=1 - g["detected"]).groupby("tone_bin")["miss"]
                 .agg(["mean", "count"]).reindex(TONE_ORDER))
            print(t.rename(columns={"mean": "miss_rate", "count": "n"}).to_string())
            cr = [r for r in rows if r["kind"] == "contrast"
                  and r["sample"] == sample and r["detector"] == det
                  and r["exposure"] == exp]
            for c in cr:
                print(f"  {c['stratifier']}: {c['group']} "
                      f"{c['miss_rate']:.3%} vs {c['comparison_rate']:.3%} "
                      f"(x{c['ratio']}, p={c['p_fisher']:.2g})")
            print()

if __name__ == "__main__":
    main()
