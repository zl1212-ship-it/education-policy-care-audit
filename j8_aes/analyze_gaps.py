"""Machine-minus-human score gaps by writer subgroup (the core audit).

What this measures
------------------
For every essay we have a HUMAN score and an out-of-fold MACHINE score from
each AES family (run_scorers.py). The audit quantity is the signed residual

    gap = machine score - human score

and how its mean differs between a focal and a reference group (e.g. ELL vs
non-ELL writers). If the machine reproduced its human training signal
group-neutrally, the mean gap would be the same across groups. Metrics:

  raw differential   mean gap (focal) - mean gap (reference).
  conditional        the same differential computed within human-score strata
  differential       and averaged over the focal group's strata weights, so
                     essays are compared only to essays human raters scored
                     identically. This separates a group effect from
                     regression-to-the-mean shrinkage, which mechanically
                     inflates machine scores for any low-scoring group.
  SMD                standardized mean difference between machine and human
                     scores within each group, per the Williamson, Xi &
                     Breyer (2012) industry evaluation framework
                     (|SMD| >= 0.15 is that framework's review flag).
  agreement          QWK, exact agreement, Pearson r, RMSE by group: whether
                     the machine measures some groups more noisily.

Inference: nonparametric bootstrap over essays within group (B=1000,
percentile 95% CIs, fixed seed). Identification: this is an audit of a
measurement instrument on fixed public corpora, not a causal claim about
students. Models were trained on the pooled population (as deployed engines
are); subgroup analysis restricts to essays with the relevant label.

A decision layer converts scores into pass/fail at integer cutoffs
(PERSUADE holistic scale 1-6) and reports demotion rates: the share of
essays a human rater passed that the machine fails.

Input : data/panel_persuade.csv, data/machine_scores_persuade.csv,
        data/panel_ellipse.csv,  data/machine_scores_ellipse.csv
Output: data/results_gaps.csv      (group-level + differential metrics)
        data/results_decision.csv  (pass/demotion rates by cutoff)

Run run_scorers.py first.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

DATA = Path(__file__).parent / "data"
FAMILIES = ["handfeat", "tfidf", "embed"]
PROTOCOLS = ["oof", "lopo"]
SEED = 8
B = 1000

# corpus -> dimension -> (focal groups, reference group)
CONTRASTS = {
    "persuade": {
        "ell_status": (["Yes"], "No"),
        "economically_disadvantaged": (["Economically disadvantaged"],
                                       "Not economically disadvantaged"),
        "student_disability_status": (["Identified as having disability"],
                                      "Not identified as having disability"),
        "gender": (["F"], "M"),
        "race_ethnicity": (["Hispanic/Latino", "Black/African American",
                            "Asian/Pacific Islander"], "White"),
    },
    # ELLIPSE writers are all English learners; contrasts are within-ELL.
    "ellipse": {
        "SES": (["Economically disadvantaged"],
                "Not economically disadvantaged"),
        "gender": (["Female"], "Male"),
        "race_ethnicity": (["Hispanic/Latino", "Black/African American",
                            "Asian/Pacific Islander"], "White"),
    },
}

CUTOFFS = [3, 4, 5]  # PERSUADE holistic pass marks for the decision layer


def _strata(y: np.ndarray) -> np.ndarray:
    """Human-score strata as small ints (doubling keeps half points exact)."""
    return np.round(y * 2).astype(int)


def _cond_diff(gap_f, st_f, gap_r, st_r) -> float:
    """Conditional differential: per-stratum (focal-ref) mean-gap difference,
    averaged with the focal group's stratum weights; strata that one group
    lacks are dropped."""
    total, weight = 0.0, 0
    for s in np.unique(st_f):
        sel_r = st_r == s
        if not sel_r.any():
            continue
        sel_f = st_f == s
        total += sel_f.sum() * (gap_f[sel_f].mean() - gap_r[sel_r].mean())
        weight += sel_f.sum()
    return total / weight if weight else np.nan


def _boot_ci(stat_fn, rng, *arrays) -> tuple:
    """Percentile bootstrap CI; resamples each (per-group) array block."""
    vals = []
    for _ in range(B):
        res = []
        for block in arrays:  # block = tuple of aligned arrays for one group
            n = len(block[0])
            idx = rng.integers(0, n, n)
            res.append(tuple(a[idx] for a in block))
        vals.append(stat_fn(*res))
    return (float(np.nanpercentile(vals, 2.5)),
            float(np.nanpercentile(vals, 97.5)))


def group_metrics(human, pred) -> dict:
    h2, p2 = _strata(human), _strata(pred)
    var = (np.var(pred, ddof=1) + np.var(human, ddof=1)) / 2
    return {
        "mean_human": human.mean(),
        "mean_machine": pred.mean(),
        "mean_gap": (pred - human).mean(),
        "smd": (pred.mean() - human.mean()) / np.sqrt(var),
        "qwk": cohen_kappa_score(h2, p2, weights="quadratic"),
        "exact": (h2 == p2).mean(),
        "pearson_r": np.corrcoef(human, pred)[0, 1],
        "rmse": float(np.sqrt(((pred - human) ** 2).mean())),
    }


def audit_corpus(corpus, panel, scores, key, human_col, out_rows, dec_rows):
    df = panel.merge(scores, left_on=key, right_on=key, how="inner")
    rng = np.random.default_rng(SEED)

    for fam in FAMILIES:
        for proto in PROTOCOLS:
            pred_col = f"pred_{fam}_{proto}"
            for dim, (focals, ref) in CONTRASTS[corpus].items():
                sub = df.dropna(subset=[dim, pred_col])
                ref_rows = sub[sub[dim] == ref]
                h_r = ref_rows[human_col].to_numpy(float)
                p_r = ref_rows[pred_col].to_numpy(float)

                for grp, rows in [(ref, ref_rows)] + [
                        (f, sub[sub[dim] == f]) for f in focals]:
                    h = rows[human_col].to_numpy(float)
                    p = rows[pred_col].to_numpy(float)
                    for metric, value in group_metrics(h, p).items():
                        out_rows.append(dict(
                            corpus=corpus, family=fam, protocol=proto,
                            dimension=dim, group=grp, metric=metric,
                            value=round(float(value), 4), ci_lo=None,
                            ci_hi=None, n=len(rows)))

                for focal in focals:
                    f_rows = sub[sub[dim] == focal]
                    h_f = f_rows[human_col].to_numpy(float)
                    p_f = f_rows[pred_col].to_numpy(float)
                    gap_f, gap_r = p_f - h_f, p_r - h_r
                    st_f, st_r = _strata(h_f), _strata(h_r)

                    raw = gap_f.mean() - gap_r.mean()
                    lo, hi = _boot_ci(
                        lambda bf, br: bf[0].mean() - br[0].mean(),
                        rng, (gap_f,), (gap_r,))
                    out_rows.append(dict(
                        corpus=corpus, family=fam, protocol=proto,
                        dimension=dim, group=f"{focal} - {ref}",
                        metric="raw_differential", value=round(raw, 4),
                        ci_lo=round(lo, 4), ci_hi=round(hi, 4), n=len(f_rows)))

                    cond = _cond_diff(gap_f, st_f, gap_r, st_r)
                    lo, hi = _boot_ci(
                        lambda bf, br: _cond_diff(bf[0], bf[1], br[0], br[1]),
                        rng, (gap_f, st_f), (gap_r, st_r))
                    out_rows.append(dict(
                        corpus=corpus, family=fam, protocol=proto,
                        dimension=dim, group=f"{focal} - {ref}",
                        metric="conditional_differential",
                        value=round(float(cond), 4),
                        ci_lo=round(lo, 4), ci_hi=round(hi, 4), n=len(f_rows)))

                    # Decision layer: pass/fail at integer cutoffs.
                    if corpus != "persuade":
                        continue
                    for cut in CUTOFFS:
                        for grp, h, p in [(focal, h_f, p_f), (ref, h_r, p_r)]:
                            hp = h >= cut
                            mp = np.round(p) >= cut
                            demote = (hp & ~mp).sum() / max(hp.sum(), 1)
                            promote = (~hp & mp).sum() / max((~hp).sum(), 1)
                            dec_rows.append(dict(
                                corpus=corpus, family=fam, protocol=proto,
                                dimension=dim, group=grp, cutoff=cut,
                                human_pass=round(hp.mean(), 4),
                                machine_pass=round(mp.mean(), 4),
                                demotion_rate=round(float(demote), 4),
                                promotion_rate=round(float(promote), 4),
                                n=len(h)))

                        def _demote_diff(bf, br):
                            out = []
                            for h, p in (bf, br):
                                hp, mp = h >= cut, np.round(p) >= cut
                                out.append((hp & ~mp).sum() / max(hp.sum(), 1))
                            return out[0] - out[1]

                        d = _demote_diff((h_f, p_f), (h_r, p_r))
                        lo, hi = _boot_ci(_demote_diff, rng,
                                          (h_f, p_f), (h_r, p_r))
                        dec_rows.append(dict(
                            corpus=corpus, family=fam, protocol=proto,
                            dimension=dim, group=f"{focal} - {ref}",
                            cutoff=cut, human_pass=None, machine_pass=None,
                            demotion_rate=round(float(d), 4),
                            promotion_rate=None, n=len(h_f),
                            ci_lo=round(lo, 4), ci_hi=round(hi, 4)))


def main() -> int:
    needed = ["panel_persuade.csv", "machine_scores_persuade.csv",
              "panel_ellipse.csv", "machine_scores_ellipse.csv"]
    for f in needed:
        if not (DATA / f).exists():
            print(f"Missing data/{f}. Run run_scorers.py first.",
                  file=sys.stderr)
            return 1

    out_rows, dec_rows = [], []

    audit_corpus("persuade",
                 pd.read_csv(DATA / "panel_persuade.csv"),
                 pd.read_csv(DATA / "machine_scores_persuade.csv"),
                 "panel_id", "holistic_essay_score", out_rows, dec_rows)
    audit_corpus("ellipse",
                 pd.read_csv(DATA / "panel_ellipse.csv"),
                 pd.read_csv(DATA / "machine_scores_ellipse.csv"),
                 "text_id_kaggle", "Overall", out_rows, dec_rows)

    gaps = pd.DataFrame(out_rows)
    gaps.to_csv(DATA / "results_gaps.csv", index=False)
    dec = pd.DataFrame(dec_rows)
    dec.to_csv(DATA / "results_decision.csv", index=False)
    print(f"Wrote results_gaps.csv ({len(gaps)}) and "
          f"results_decision.csv ({len(dec)})")

    # Console headline: PERSUADE ELL contrast, out-of-fold.
    head = gaps[(gaps.corpus == "persuade") & (gaps.dimension == "ell_status")
                & (gaps.protocol == "oof")]
    print("\n=== PERSUADE ELL vs non-ELL (out-of-fold) ===")
    for fam in FAMILIES:
        sub = head[head.family == fam].set_index(["group", "metric"]).value
        print(f"\n  [{fam}]")
        print(f"    mean gap   ELL {sub.get(('Yes', 'mean_gap'), np.nan):+.3f}"
              f"  non-ELL {sub.get(('No', 'mean_gap'), np.nan):+.3f}")
        for m in ["raw_differential", "conditional_differential"]:
            row = head[(head.family == fam) & (head.metric == m)]
            if len(row):
                r = row.iloc[0]
                print(f"    {m:<26}{r.value:+.3f}  "
                      f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]")
        for g in ["Yes", "No"]:
            print(f"    QWK {g:<4} {sub.get((g, 'qwk'), np.nan):.3f}"
                  f"   SMD {sub.get((g, 'smd'), np.nan):+.3f}")

    d = dec[(dec.corpus == "persuade") & (dec.dimension == "ell_status")
            & (dec.protocol == "oof") & (dec.cutoff == 4)]
    print("\n=== Decision layer, cutoff 4 of 6 (out-of-fold) ===")
    for fam in FAMILIES:
        s = d[d.family == fam]
        try:
            ell = s[s.group == "Yes"].iloc[0]
            non = s[s.group == "No"].iloc[0]
            diff = s[s.group == "Yes - No"].iloc[0]
            print(f"  [{fam}] demotion ELL {ell.demotion_rate:.1%} vs "
                  f"non-ELL {non.demotion_rate:.1%}  "
                  f"(diff {diff.demotion_rate:+.1%})")
        except IndexError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
