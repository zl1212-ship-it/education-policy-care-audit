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
    wide = adm.pivot_table(index="unitid", columns="year", values=outcome)
    G = adm.groupby("unitid")["G"].first()
    allu = list(wide.index)

    def att(g, t, treated_units, Gv, w):
        base = g - 1
        if base not in w.columns or t not in w.columns:
            return None
        yb, yt = w[base], w[t]
        tr = [u for u in treated_units if u in yb.index and pd.notna(yb[u]) and pd.notna(yt[u])]
        ctrl = [u for u in w.index if (Gv[u] == 0 or Gv[u] > t) and Gv[u] != g
                and pd.notna(yb[u]) and pd.notna(yt[u])]
        if len(tr) < 1 or len(ctrl) < 5:
            return None
        return (yt[tr] - yb[tr]).mean() - (yt[ctrl] - yb[ctrl]).mean(), len(tr)

    def aggregate(w, Gv, idx):
        es, post = {}, []
        for g in cohorts:
            gunits = [u for u in idx if Gv[u] == g]
            if not gunits:
                continue
            for t in years:
                r = att(g, t, gunits, Gv, w)
                if r is None:
                    continue
                a, n = r
                es.setdefault(t - g, []).append((a, n))
                if t >= g:
                    post.append((a, n))
        def wm(p):
            if not p:
                return np.nan
            a = np.array([x[0] for x in p]); ww = np.array([x[1] for x in p], float)
            return float((a * ww).sum() / ww.sum())
        return wm(post), {e: wm(v) for e, v in es.items()}

    overall, es = aggregate(wide, G, allu)

    # clustered (by institution) bootstrap
    ests = []
    for _ in range(B):
        samp = rng.choice(allu, size=len(allu), replace=True)
        wb = wide.loc[samp].reset_index(drop=True)
        Gb = pd.Series([G[u] for u in samp])
        o, _ = aggregate(wb, Gb, list(wb.index))
        if not np.isnan(o):
            ests.append(o)
    ests = np.array(ests)
    se = ests.std(ddof=1)
    ci = np.percentile(ests, [2.5, 97.5])
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
    pd.DataFrame([(e, es[e]) for e in sorted(es)], columns=["event_time", "att"]) \
        .to_csv(os.path.join(DATA, f"did_event_{oc}.csv"), index=False)

pd.DataFrame(summary).to_csv(os.path.join(DATA, "did_results.csv"), index=False)
print("\nwrote data/did_results.csv and per-outcome event-study files")
