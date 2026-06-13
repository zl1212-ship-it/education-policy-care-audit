"""Placebo-controlled benchmark for the rater-substitution effect (ELLIPSE).

Estimand
--------
The differential rater-substitution effect: holding a single essay fixed (its
latent quality is whatever it is), replace the rater who scores it, a human,
with a machine, and ask how the score changes and whether that change differs
by the writer's group. This script estimates the group-differential version of
that effect on the second-opinion scale, with a human-rater placebo.

Identification
--------------
Within-essay design. Each essay is its own control: the SAME text is scored two
ways, so any machine-minus-human difference is a property of the rater, not of
the writing. true quality is held fixed by construction.

ELLIPSE ships two independent human ratings per released essay, which supplies a
PLACEBO. Take rater 1 as the first opinion. Substituting a second human rater in
the second-opinion slot is the placebo treatment; substituting a machine is the
treatment. If some groups' essays are simply harder to score, both substitutions
move together and the placebo absorbs it. The contrast of interest is therefore
a DIFFERENCE-IN-DIFFERENCES: [machine second-opinion group differential] minus
[human second-opinion group differential], on the same essays. The statistic
machine_minus_human_paired computed below IS that DiD estimate.

  human (placebo)   mean(rater2 - rater1) by subgroup and its focal-minus-
                    reference differential. Rater order is arbitrary, so this
                    centers near zero; a nonzero group differential would mean
                    human second opinions are themselves group-patterned.
  machine           mean(machine - rater1) by subgroup and the same
                    differential, on the SAME double-rated essays, out-of-fold.
  |disagreement|    mean |rater1 - rater2| by subgroup: whether some groups'
                    essays are intrinsically noisier to rate (a falsification
                    check on the placebo).
  machine_minus_    the DiD estimate: (machine differential) minus (human
  human_paired      differential), recomputed on the SAME resampled essays each
                    replicate so it is paired. Comparing a machine CI that
                    excludes zero with a human CI that includes zero is NOT a
                    test of their difference (Gelman and Stern, 2006); this DiD
                    is. Computed for every dimension, not only SES.

Dimension mechanism (descriptive): partial correlation between the machine
residual (machine - Overall) and each human analytic score (Cohesion, Syntax,
Vocabulary, Phraseology, Grammar, Conventions), holding Overall fixed. This
names where the machine and the human reading part company; it is correlational,
not a proven causal mechanism.

Scope: this identifies the causal effect of substituting the measuring
instrument (human -> machine) on the score and, in analyze_gaps.py, on the
pass/fail decision. It does NOT identify any effect on a student's latent
ability or on real downstream outcomes (placement, graduation), which would
require the engine to be deployed and students followed.

Inference: bootstrap percentile CIs (B=1000, fixed seed), essays resampled
within group; the DiD resamples both contrasts on the same draw.

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


def _boot_paired_ci(rng, fidx, ridx, machine, human, r1) -> tuple:
    """CI for (machine differential) - (human differential), the DIRECT test of
    whether the machine's second-opinion tilt exceeds a human rater's.

    Both differentials are recomputed on the SAME resampled essays each
    replicate, so the comparison is paired rather than two independent CIs.
    Comparing "machine CI excludes zero" with "human CI includes zero" is the
    Gelman and Stern (2006) error; this statistic tests the difference itself.
    """
    vals = []
    for _ in range(B):
        fb = fidx[rng.integers(0, len(fidx), len(fidx))]
        rb = ridx[rng.integers(0, len(ridx), len(ridx))]
        machine_diff = ((machine[fb] - r1[fb]).mean()
                        - (machine[rb] - r1[rb]).mean())
        human_diff = ((human[fb] - r1[fb]).mean()
                      - (human[rb] - r1[rb]).mean())
        vals.append(machine_diff - human_diff)
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

            # Direct paired test: does the machine's tilt exceed the human
            # rater's on the SAME essays? (avoids the Gelman-Stern error)
            fidx = np.where(f_sel)[0]
            ridx = np.where(ref_sel)[0]
            human = second["human"]
            for fam in FAMILIES:
                machine = second[fam]
                d = ((machine[f_sel] - r1[f_sel]).mean()
                     - (machine[ref_sel] - r1[ref_sel]).mean()) - (
                     (human[f_sel] - r1[f_sel]).mean()
                     - (human[ref_sel] - r1[ref_sel]).mean())
                lo, hi = _boot_paired_ci(rng, fidx, ridx, machine, human, r1)
                rows.append(dict(
                    analysis="machine_minus_human_paired", second_opinion=fam,
                    dimension=dim, group=f"{focal} - {ref}",
                    value=round(float(d), 4), ci_lo=round(lo, 4),
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

    print("\n=== Second-opinion differential, all dimensions, "
          "ELLIPSE double-rated essays ===")
    so = out[out.analysis == "second_opinion"]
    for dim in CONTRASTS:
        for _, r in so[so.dimension == dim].iterrows():
            flag = "" if (r.ci_lo <= 0 <= r.ci_hi) else "  <-- excludes 0"
            print(f"  {dim:<14} {r.second_opinion:<9} {r.value:+.3f}  "
                  f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]{flag}")

    print("\n=== DIRECT test: (machine differential) - (human differential), "
          "paired, all CIs should be read for whether they exclude 0 ===")
    mh = out[out.analysis == "machine_minus_human_paired"]
    for _, r in mh.iterrows():
        flag = "" if (r.ci_lo <= 0 <= r.ci_hi) else "  <-- excludes 0"
        print(f"  {r.dimension:<14} {r.second_opinion:<9} {r.value:+.3f}  "
              f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]{flag}")

    print("\n=== Machine residual vs analytic dimension "
          "(partial corr, Overall held fixed) ===")
    mech = out[out.analysis == "dimension_partial_corr"]
    piv = mech.pivot_table(index="dimension", columns="second_opinion",
                           values="value")
    print(piv.round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
