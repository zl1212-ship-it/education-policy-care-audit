"""Detection-failure rates by the gender x race intersection.

Motivation: the foundational Gender Shades audit found commercial face systems
worst on darker-skinned women, an intersectional pattern. The main J7 detection
analysis (analyze_detection.py) stratifies by skin tone and by perceived race
separately. This script adds the gender x race cross so the manuscript can state,
from its own data, whether the detection burden compounds for women of color or is
carried by race/tone regardless of gender.

Estimand: same as analyze_detection.py, the probability a detector returns "no face"
on a one-face image, here contrasted across gender x race cells. Miss = 1 - detected.
Identification is by direct enumeration of the FairFace validation panel; gender and
race are the dataset authors' labels (face_panel.csv). Inference: Wilson intervals on
cell rates, Fisher exact tests on the focal contrasts.

Focal contrasts (Haar and the modern detectors, at full and dim exposure):
- Black women vs White men      (the Gender Shades extremes)
- Black women vs Black men      (does gender add within the most-affected race)
- White women vs White men      (does gender add within the least-affected race)
- Black women vs White women    (race within women)

Reported on adults only (FairFace age 20+), the proctored-exam population, with the
full panel as a check.

Output: data/results_gender_race.csv (kind in {cell, contrast}).
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL_CSV = os.path.join(HERE, "data", "face_panel.csv")
OUTCOMES_CSV = os.path.join(HERE, "data", "detection_outcomes.csv")
OUT_CSV = os.path.join(HERE, "data", "results_gender_race.csv")

CHILD_AGES = ["0-2", "3-9", "10-19"]
DETECTORS = ["haar", "yunet", "mtcnn", "mediapipe"]
EXPOSURES = [1.0, 0.15]
RACES = ["White", "East Asian", "Latino_Hispanic", "Middle Eastern",
         "Southeast Asian", "Indian", "Black"]


def wilson(misses, n, z=1.959963984540054):
    if n == 0:
        return np.nan, np.nan
    p = misses / n
    den = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    return center - half, center + half


def cell(g, race, gender):
    gg = g[(g["race"] == race) & (g["gender"] == gender)]
    n = len(gg)
    misses = int((1 - gg["detected"]).sum())
    lo, hi = wilson(misses, n)
    return misses, n, (misses / n if n else np.nan), lo, hi


def contrast(g, ra, ga, rb, gb):
    a = g[(g["race"] == ra) & (g["gender"] == ga)]
    b = g[(g["race"] == rb) & (g["gender"] == gb)]
    ma, na = int((1 - a["detected"]).sum()), len(a)
    mb, nb = int((1 - b["detected"]).sum()), len(b)
    ra_, rb_ = ma / na, mb / nb
    _, p = stats.fisher_exact([[ma, na - ma], [mb, nb - mb]])
    return {"a": f"{ra} {ga}", "b": f"{rb} {gb}", "n": na + nb,
            "rate_a": round(ra_, 4), "rate_b": round(rb_, 4),
            "risk_diff": round(ra_ - rb_, 4),
            "ratio": round(ra_ / rb_, 2) if rb_ > 0 else np.inf,
            "p_fisher": p}


CONTRASTS = [("Black", "Female", "White", "Male"),
             ("Black", "Female", "Black", "Male"),
             ("White", "Female", "White", "Male"),
             ("Black", "Female", "White", "Female")]


def main():
    panel = pd.read_csv(PANEL_CSV)
    outcomes = pd.read_csv(OUTCOMES_CSV)
    d = outcomes.merge(panel, on="file", how="left")

    rows = []
    samples = {"adult": d[~d["age"].isin(CHILD_AGES)], "all": d}
    for sample, ds in samples.items():
        for det in DETECTORS:
            for exp in EXPOSURES:
                g = ds[(ds["detector"] == det) & (ds["exposure"] == exp)]
                if g.empty:
                    continue
                for race in RACES:
                    for gender in ("Female", "Male"):
                        m, n, r, lo, hi = cell(g, race, gender)
                        rows.append({"kind": "cell", "sample": sample,
                                     "detector": det, "exposure": exp,
                                     "race": race, "gender": gender, "n": n,
                                     "misses": m,
                                     "miss_rate": round(r, 4) if n else np.nan,
                                     "wilson_lo": round(lo, 4) if n else np.nan,
                                     "wilson_hi": round(hi, 4) if n else np.nan})
                for ra, ga, rb, gb in CONTRASTS:
                    c = contrast(g, ra, ga, rb, gb)
                    c.update({"kind": "contrast", "sample": sample,
                              "detector": det, "exposure": exp})
                    rows.append(c)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {len(out)} rows -> {OUT_CSV}\n")

    # console summary: the four corners + focal contrasts, adults
    for det in DETECTORS:
        for exp in EXPOSURES:
            g = samples["adult"][(samples["adult"]["detector"] == det)
                                 & (samples["adult"]["exposure"] == exp)]
            if g.empty:
                continue
            print(f"=== [adult] {det} exposure={exp} ===")
            for race in ("Black", "White"):
                for gender in ("Female", "Male"):
                    m, n, r, lo, hi = cell(g, race, gender)
                    print(f"  {race:5s} {gender:6s}: miss {r:.3%}  "
                          f"[{lo:.3%}, {hi:.3%}]  n={n}")
            for ra, ga, rb, gb in CONTRASTS:
                c = contrast(g, ra, ga, rb, gb)
                print(f"    {c['a']} vs {c['b']}: {c['rate_a']:.3%} vs "
                      f"{c['rate_b']:.3%} (x{c['ratio']}, p={c['p_fisher']:.2g})")
            print()


if __name__ == "__main__":
    main()
