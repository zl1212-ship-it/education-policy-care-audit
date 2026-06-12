"""Human-rater disagreement benchmark and dimension mechanism (ELLIPSE).

What this measures
------------------
The gap audit (analyze_gaps.py) can be read two ways: the machine is biased,
or some groups' essays are simply harder to score. ELLIPSE ships the two
independent human ratings behind each released essay, which identifies a
benchmark: treat one rater as the first opinion and ask how a SECOND OPINION
differs by writer subgroup when that second opinion is (a) another trained
human rater or (b) the machine.

  human benchmark   mean(rater2 - rater1) by subgroup, and its focal-minus-
                    reference differential. Rater order is arbitrary, so this
                    centers near zero; the question is whether it differs BY
                    GROUP (it should not, if human disagreement is noise).
  machine           mean(machine - rater1) by subgroup and the same
                    differential, on the SAME double-rated essays, using the
                    out-of-fold machine scores.
  |disagreement|    mean |rater1 - rater2| by subgroup: whether some groups'
                    essays are intrinsically harder to rate (higher rater
                    noise), which would caution against any second-opinion
                    comparison.

Dimension mechanism: correlation between the machine residual
(machine - Overall) and each human analytic score (Cohesion, Syntax,
Vocabulary, Phraseology, Grammar, Conventions), partialling out Overall:
which proficiency dimensions does the machine systematically under- or
over-credit?

Inference: bootstrap percentile CIs (B=1000, fixed seed), essays resampled
within group. Same caveat as the gap audit: measurement audit on a fixed
public corpus, no causal claim.

Input : data/rater_pairs.csv, data/panel_ellipse.csv,
        data/machine_scores_ellipse.csv
Output: data/results_benchmark.csv

Run run_scorers.py first.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
FAMILIES = ["handfeat", "tfidf", "embed"]
SEED = 8
B = 1000

CONTRASTS = {
    "SES": (["Economically disadvantaged"], "Not economically disadvantaged"),
    "gender": (["Female"], "Male"),
    "race_ethnicity": (["Hispanic/Latino", "Black/African American",
                        "Asian/Pacific Islander"], "White"),
}
DIMS = ["Cohesion", "Syntax", "Vocabulary", "Phraseology", "Grammar",
        "Conventions"]


def _boot_diff_ci(rng, a: np.ndarray, b: np.ndarray) -> tuple:
    """CI for mean(a) - mean(b) with independent within-group resampling."""
    vals = [a[rng.integers(0, len(a), len(a))].mean()
            - b[rng.integers(0, len(b), len(b))].mean() for _ in range(B)]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def _partial_corr(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> float:
    """corr(x, y) after regressing z out of both."""
    zx = np.polyval(np.polyfit(z, x, 1), z)
    zy = np.polyval(np.polyfit(z, y, 1), z)
    return float(np.corrcoef(x - zx, y - zy)[0, 1])


def main() -> int:
    for f in ["rater_pairs.csv", "machine_scores_ellipse.csv",
              "panel_ellipse.csv"]:
        if not (DATA / f).exists():
            print(f"Missing data/{f}. Run run_scorers.py first.",
                  file=sys.stderr)
            return 1

    pairs = pd.read_csv(DATA / "rater_pairs.csv")
    scores = pd.read_csv(DATA / "machine_scores_ellipse.csv")
    df = pairs.merge(scores, on="text_id_kaggle", how="inner")
    rng = np.random.default_rng(SEED)
    rows = []

    second = {"human": df.Overall_2.to_numpy(float)}
    for fam in FAMILIES:
        second[fam] = df[f"pred_{fam}_oof"].to_numpy(float)
    r1 = df.Overall_1.to_numpy(float)
    absdis = np.abs(df.Overall_1 - df.Overall_2).to_numpy(float)

    for dim, (focals, ref) in CONTRASTS.items():
        ref_sel = (df[dim] == ref).to_numpy()
        for focal in focals:
            f_sel = (df[dim] == focal).to_numpy()
            for opinion, sec in second.items():
                gap = sec - r1
                diff = gap[f_sel].mean() - gap[ref_sel].mean()
                lo, hi = _boot_diff_ci(rng, gap[f_sel], gap[ref_sel])
                rows.append(dict(
                    analysis="second_opinion", second_opinion=opinion,
                    dimension=dim, group=f"{focal} - {ref}",
                    value=round(float(diff), 4), ci_lo=round(lo, 4),
                    ci_hi=round(hi, 4), n=int(f_sel.sum())))
            diff = absdis[f_sel].mean() - absdis[ref_sel].mean()
            lo, hi = _boot_diff_ci(rng, absdis[f_sel], absdis[ref_sel])
            rows.append(dict(
                analysis="abs_disagreement", second_opinion="human",
                dimension=dim, group=f"{focal} - {ref}",
                value=round(float(diff), 4), ci_lo=round(lo, 4),
                ci_hi=round(hi, 4), n=int(f_sel.sum())))

    # Dimension mechanism on the full released corpus.
    panel = pd.read_csv(DATA / "panel_ellipse.csv").merge(
        scores, on="text_id_kaggle", how="inner")
    overall = panel.Overall.to_numpy(float)
    for fam in FAMILIES:
        resid = panel[f"pred_{fam}_oof"].to_numpy(float) - overall
        for d in DIMS:
            x = panel[d].to_numpy(float)
            rows.append(dict(
                analysis="dimension_partial_corr", second_opinion=fam,
                dimension=d, group="all",
                value=round(_partial_corr(resid, x, overall), 4),
                ci_lo=None, ci_hi=None, n=len(panel)))

    out = pd.DataFrame(rows)
    out.to_csv(DATA / "results_benchmark.csv", index=False)
    print(f"Wrote results_benchmark.csv ({len(out)} rows)")

    print("\n=== Second-opinion differential, SES "
          "(econ. disadvantaged - not), ELLIPSE double-rated essays ===")
    ses = out[(out.analysis == "second_opinion") & (out.dimension == "SES")]
    for _, r in ses.iterrows():
        print(f"  {r.second_opinion:<9} {r.value:+.3f}  "
              f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]")

    print("\n=== Machine residual vs analytic dimension "
          "(partial corr, Overall held fixed) ===")
    mech = out[out.analysis == "dimension_partial_corr"]
    piv = mech.pivot_table(index="dimension", columns="second_opinion",
                           values="value")
    print(piv.round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
