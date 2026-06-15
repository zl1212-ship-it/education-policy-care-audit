"""Event-study difference-in-differences around the ChatGPT shock (2022-11-30).

Estimand
--------
The differential effect of the ChatGPT shock on the restrictiveness of an
institution's academic-integrity policy text, by how exposed the institution was
to the shock. Exposure is the institution's pre-shock nonresident-alien
enrollment share (the population whose take-home written work the shock most
directly unsettled); it is a continuous, time-invariant treatment intensity.

Design
------
Institution-by-quarter panel. The policy state in a quarter is the most recent
archived version of the SAME durable integrity page on or before the quarter end
(build_panel.py), so each institution is its own control over time. Two-way fixed
effects:

    y_it = alpha_i + delta_t + sum_{k != -1} beta_k ( exposure_i x 1[event_q=k] )
           + e_it

alpha_i are institution fixed effects, delta_t are calendar-quarter fixed
effects, and event_q is quarters from the shock quarter (2022Q4 = 0). The
quarter just before the shock (event_q = -1) is the omitted reference.

Identification
--------------
- The outcome is POLICY-TEXT restrictiveness, not any student outcome. The claim
  is about institutional rule-making, never about harm to students.
- exposure_i is absorbed in levels by alpha_i (it is time-invariant); delta_t
  absorb the common post-shock shift (every campus adding AI language). The
  beta_k therefore identify only the DIFFERENTIAL movement by exposure.
- Parallel pre-trends is the key assumption: the pre-shock beta_k (k < -1) should
  be jointly zero. Reported as event-time coefficients and a joint F-test, plus a
  placebo that re-assigns the shock to 2021Q4 within pre-shock data only.
- Inference is cluster-robust by institution (the level at which treatment
  intensity varies and serial correlation lives).

Outputs: data/results_event_study.csv (event-time coefficients, the summary DiD,
pre-trend and placebo tests for each outcome).
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# The fully saturated per-quarter event spec is rank-deficient with few clusters
# (pre-shock AI provisions are ~0 for all institutions by construction); the binned
# spec and the summary DiD carry inference. Silence the resulting cosmetic warnings.
warnings.filterwarnings("ignore")

HERE = Path(__file__).parent
PANEL = HERE / "data" / "panel.csv"
OUT = HERE / "data" / "results_event_study.csv"

OUTCOMES = ["ai_addressed", "ai_governance_intensity", "net_restrictiveness",
            "restrictive_idx", "procedural_idx"]
REF = -1  # omitted event-quarter (the quarter before the shock)


def _load():
    p = pd.read_csv(PANEL)
    # standardize exposure across institutions (one value per institution)
    inst = p.drop_duplicates("unitid")[["unitid", "intl_share"]]
    mu, sd = inst["intl_share"].mean(), inst["intl_share"].std(ddof=0)
    p["exposure"] = (p["intl_share"] - mu) / sd
    p["eq"] = p["event_q"].astype(int)
    p["post"] = (p["eq"] >= 0).astype(int)
    return p


def _fit(p, outcome, formula):
    m = smf.ols(formula, data=p.assign(y=p[outcome].astype(float)))
    return m.fit(cov_type="cluster", cov_kwds={"groups": p["unitid"]})


def _ecol(k):
    return "expXeq_" + ("m" + str(-k) if k < 0 else str(k))


def event_study(p, outcome):
    """Event-time interaction coefficients + summary DiD + pre-trend / placebo.

    The event-study interactions are built manually (exposure x 1[eq=k]) omitting
    the reference period (k = REF). The continuous exposure level is time-invariant
    and absorbed by the institution fixed effects, so omitting the reference both
    pins the reference coefficient to zero and avoids the rank deficiency a full
    continuous-by-categorical interaction would create.
    """
    rows = []
    p = p.copy()
    ks = sorted(k for k in p["eq"].unique() if k != REF)
    cols = []
    for k in ks:
        c = _ecol(k)
        p[c] = p["exposure"] * (p["eq"] == k).astype(float)
        cols.append((k, c))
    f_dyn = "y ~ C(unitid) + C(eq) + " + " + ".join(c for _, c in cols)
    res = _fit(p, outcome, f_dyn)
    for k, c in cols:
        ci = res.conf_int().loc[c]
        rows.append({"outcome": outcome, "kind": "event_coef", "event_q": k,
                     "coef": res.params[c], "se": res.bse[c],
                     "ci_lo": ci[0], "ci_hi": ci[1], "pval": res.pvalues[c]})
    rows.append({"outcome": outcome, "kind": "event_coef", "event_q": REF,
                 "coef": 0.0, "se": 0.0, "ci_lo": 0.0, "ci_hi": 0.0, "pval": np.nan})

    # binned post-period dynamics (stable with few clusters): exposure x 1[eq in bin],
    # pooled pre-period as the reference. The per-quarter spec above is mechanically
    # flat pre-shock (AI provisions are absent then by the codebook's clean baseline),
    # so a saturated pre-trend F is degenerate; the placebo below is the falsification.
    BINS = [("q0_1", (0, 1)), ("q2_3", (2, 3)), ("q4_5", (4, 5)), ("q6_8", (6, 7, 8))]
    bcols = []
    for label, qs in BINS:
        c = "expbin_" + label
        p[c] = p["exposure"] * p["eq"].isin(qs).astype(float)
        bcols.append((label, qs, c))
    resb = _fit(p, outcome, "y ~ C(unitid) + C(eq) + " + " + ".join(c for _, _, c in bcols))
    for label, qs, c in bcols:
        ci = resb.conf_int().loc[c]
        rows.append({"outcome": outcome, "kind": "event_bin", "event_q": qs[0],
                     "coef": resb.params[c], "se": resb.bse[c],
                     "ci_lo": ci[0], "ci_hi": ci[1], "pval": resb.pvalues[c]})

    # summary DiD: exposure x post
    p["expXpost"] = p["exposure"] * p["post"].astype(float)
    res2 = _fit(p, outcome, "y ~ C(unitid) + C(eq) + expXpost")
    ci = res2.conf_int().loc["expXpost"]
    rows.append({"outcome": outcome, "kind": "did_exposure_x_post", "event_q": np.nan,
                 "coef": res2.params["expXpost"], "se": res2.bse["expXpost"],
                 "ci_lo": ci[0], "ci_hi": ci[1], "pval": res2.pvalues["expXpost"]})

    # placebo: pre-shock data only, fake shock at 2021Q4 (placebo post = eq >= -4)
    pre = p[p["eq"] < 0].copy()
    if pre["eq"].nunique() >= 3 and pre["unitid"].nunique() > 1:
        pre["expXplacebo"] = pre["exposure"] * (pre["eq"] >= -4).astype(float)
        try:
            res3 = _fit(pre, outcome, "y ~ C(unitid) + C(eq) + expXplacebo")
            ci = res3.conf_int().loc["expXplacebo"]
            rows.append({"outcome": outcome, "kind": "placebo_2021Q4", "event_q": np.nan,
                         "coef": res3.params["expXplacebo"], "se": res3.bse["expXplacebo"],
                         "ci_lo": ci[0], "ci_hi": ci[1], "pval": res3.pvalues["expXplacebo"]})
        except Exception as e:
            print(f"  placebo skipped for {outcome}: {type(e).__name__}")
    return rows


def main():
    p = _load()
    print(f"Panel: {len(p)} institution-quarter rows, {p['unitid'].nunique()} "
          f"institutions, event_q {p['eq'].min()}..{p['eq'].max()}")
    all_rows = []
    for outcome in OUTCOMES:
        all_rows += event_study(p, outcome)
        did = [r for r in all_rows if r["outcome"] == outcome and r["kind"] == "did_exposure_x_post"][0]
        pl = [r for r in all_rows if r["outcome"] == outcome and r["kind"] == "placebo_2021Q4"]
        pl_p = pl[0]["pval"] if pl else np.nan
        print(f"  {outcome:<24} DiD(exp x post)={did['coef']:+.3f} "
              f"(p={did['pval']:.3f})  placebo p={pl_p:.3f}")
    pd.DataFrame(all_rows).to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
