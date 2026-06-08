"""
Callaway & Sant'Anna (2021) staggered DiD for J3 (test-optional adoption).

Identification window is pre-COVID: treated cohorts are the voluntary adopters of 2016-2019
(reqt_test_scores flip 1/2 -> 3), outcomes are observed 2009-2019, and the COVID test-optional
wave (2020-2021) is excluded so it cannot confound the estimate. Controls for each (g,t) are
not-yet-treated institutions (never-adopters or adopters with G>t, which includes the COVID/post
adopters while still untreated). Treatment is set at the institution, so inference is a
clustered (by institution) bootstrap.

  ATT(g,t) = [E(Y_t - Y_{g-1} | G=g)] - [E(Y_t - Y_{g-1} | not-yet-treated)]
Aggregations: event-study (by t-g) and overall post ATT, cohort-size weighted.

Outcomes (institution-year):
  admit_rate, yield_rate, sat_pct_submit   (admissions panel)
  share_urm, share_black, share_hisp       (entering-class composition panel)

Writes data/did_results.csv (overall ATT per outcome) and data/did_event_<outcome>.csv.
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
B = 500
rng = np.random.default_rng(7)
YEAR_MAX = 2019                     # pre-COVID window
TREAT_COHORTS = [2016, 2017, 2018, 2019]

# ---- assemble panel: admissions + composition ----
adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
adm["adoption_year"] = pd.to_numeric(adm["adoption_year"], errors="coerce")
for c in ["admit_rate", "yield_rate", "sat_pct_submit", "female_share"]:
    adm[c] = pd.to_numeric(adm[c], errors="coerce")
# percentage-point scale for rates stored as proportions
adm["admit_rate"] = adm["admit_rate"] * 100
adm["yield_rate"] = adm["yield_rate"] * 100

comp_path = os.path.join(DATA, "composition_panel.csv")
if os.path.exists(comp_path):
    comp = pd.read_csv(comp_path)
    for c in ["share_urm", "share_black", "share_hisp"]:
        comp[c] = comp[c] * 100
    adm = adm.merge(comp[["unitid", "year", "share_urm", "share_black", "share_hisp"]],
                    on=["unitid", "year"], how="left")

# G: cohort year for ALL adopters; treated-of-interest are 2016-2019. Adopters in 2020+
# (COVID/post) keep their true G so they act as not-yet-treated controls for t<=2019.
adm["G"] = adm["adoption_year"].fillna(0).astype(int)
adm = adm[adm.year <= YEAR_MAX].copy()

years = sorted(adm.year.unique())
cohorts = TREAT_COHORTS
Gser = adm.groupby("unitid")["G"].first()
print(f"window {min(years)}-{max(years)}  treat cohorts {cohorts}  "
      f"cohort sizes { {c:int((Gser==c).sum()) for c in cohorts} }  "
      f"not-yet/never pool { int((Gser==0).sum()) + int((Gser>YEAR_MAX).sum()) }")


def run_outcome(outcome):
    # Vectorized Callaway-Sant'Anna. The group-time ATT is a difference of weighted means;
    # a clustered bootstrap that resamples institutions is exactly a reweighting of those
    # means by each institution's resample multiplicity. So we precompute, for every (g,t)
    # cell, the per-institution difference d_i = Y_{i,t} - Y_{i,g-1} and the treated/control
    # masks, then evaluate all B bootstrap reps as matrix products against a count-weight
    # matrix. Drawing the SAME rng.choice resamples as the loop version reproduces its
    # numbers exactly, because mean-over-duplicated-rows == count-weighted mean.
    wide = adm.pivot_table(index="unitid", columns="year", values=outcome)
    allu = list(wide.index)
    N = len(allu)
    pos = {u: i for i, u in enumerate(allu)}
    G = adm.groupby("unitid")["G"].first().reindex(allu).to_numpy()
    col_of = {y: j for j, y in enumerate(wide.columns)}
    Y = wide.to_numpy(float)

    cell_TD, cell_CD, cell_T, cell_C, cell_e, cell_post = [], [], [], [], [], []
    for g in cohorts:
        if (g - 1) not in col_of:
            continue
        jb = col_of[g - 1]
        for t in years:
            if t not in col_of:
                continue
            d = Y[:, col_of[t]] - Y[:, jb]
            valid = ~np.isnan(d)
            tre = ((G == g) & valid).astype(float)
            ctr = (((G == 0) | (G > t)) & (G != g) & valid).astype(float)
            df = np.where(valid, d, 0.0)
            cell_T.append(tre); cell_C.append(ctr)
            cell_TD.append(tre * df); cell_CD.append(ctr * df)
            cell_e.append(t - g); cell_post.append(t >= g)
    Tm = np.array(cell_T); Cm = np.array(cell_C)            # cells x N
    TD = np.array(cell_TD); CD = np.array(cell_CD)
    e_arr = np.array(cell_e); post_arr = np.array(cell_post)

    def agg(W):                                             # W: N x B -> overall (B,)
        tden = Tm @ W; cden = Cm @ W
        feas = (tden >= 1) & (cden >= 5)
        with np.errstate(divide="ignore", invalid="ignore"):
            att = (TD @ W) / np.where(tden > 0, tden, 1) - (CD @ W) / np.where(cden > 0, cden, 1)
        wcell = np.where(feas & post_arr[:, None], tden, 0.0)
        num = (np.where(feas, att, 0.0) * wcell).sum(0); den = wcell.sum(0)
        return np.where(den > 0, num / den, np.nan)

    overall = float(agg(np.ones((N, 1)))[0])

    # event study (point estimate): same feasibility, weighted by treated count, by event time
    w1 = np.ones((N, 1))
    tden = (Tm @ w1).ravel(); cden = (Cm @ w1).ravel()
    feas = (tden >= 1) & (cden >= 5)
    with np.errstate(divide="ignore", invalid="ignore"):
        attp = ((TD @ w1).ravel() / np.where(tden > 0, tden, 1)
                - (CD @ w1).ravel() / np.where(cden > 0, cden, 1))
    es = {}
    for e in sorted(set(e_arr.tolist())):
        m = (e_arr == e) & feas
        w = tden[m]
        if w.sum() > 0:
            es[e] = float((attp[m] * w).sum() / w.sum())

    # clustered bootstrap: replicate the exact rng.choice draws, as count weights
    allu_arr = np.array(allu)
    Wb = np.empty((N, B))
    for b in range(B):
        samp = rng.choice(allu_arr, size=N, replace=True)
        Wb[:, b] = np.bincount([pos[u] for u in samp], minlength=N)
    ob = agg(Wb)
    ob = ob[~np.isnan(ob)]
    se = ob.std(ddof=1)
    ci = np.percentile(ob, [2.5, 97.5])
    n_treated = sum(int((G == c).sum()) for c in cohorts)
    return overall, se, ci, es, n_treated


OUTCOMES = ["admit_rate", "yield_rate", "sat_pct_submit"]
if os.path.exists(comp_path):
    OUTCOMES += ["share_urm", "share_black", "share_hisp"]

summary = []
for oc in OUTCOMES:
    if oc not in adm.columns or adm[oc].notna().sum() == 0:
        continue
    overall, se, ci, es, ntr = run_outcome(oc)
    z = overall / se if se else float("nan")
    print(f"\n=== {oc} ===")
    print(f"  overall post ATT = {overall:+.3f}  SE {se:.3f}  "
          f"95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]  z={z:+.2f}  (n_treated={ntr})")
    print("  event study:")
    for e in sorted(es):
        tag = "pre " if e < 0 else "post"
        print(f"    t{e:+d} [{tag}]: {es[e]:+.3f}")
    summary.append({"outcome": oc, "att": round(overall, 4), "se": round(se, 4),
                    "ci_lo": round(ci[0], 4), "ci_hi": round(ci[1], 4),
                    "z": round(z, 2), "n_treated": ntr})
    pd.DataFrame([(e, round(es[e], 6)) for e in sorted(es)], columns=["event_time", "att"]) \
        .to_csv(os.path.join(DATA, f"did_event_{oc}.csv"), index=False)

pd.DataFrame(summary).to_csv(os.path.join(DATA, "did_results.csv"), index=False)
print("\nwrote data/did_results.csv and per-outcome event-study files")
