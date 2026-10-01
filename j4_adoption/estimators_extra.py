"""
J4 alternative DiD estimators: show the retention
finding is not an artifact of the Callaway-Sant'Anna estimator.

New estimators implemented here:

(1) Sun & Abraham (2021) interaction-weighted (IW) event study on the FULL panel
    (736 public 4-years, 2009-2020; cohorts GSU 2012, UW-Milwaukee 2013, 19 CSU 2018,
    8 UW 2019). Same machinery as robustness.py's matched-sample sa_estimate, extended
    to all four cohorts: saturated cohort-by-event-time dummies (ref e=-1, e<=-7
    binned), unit and year fixed effects absorbed by Frisch-Waugh-Lovell unit
    demeaning (verified once against the full-dummy OLS), CATT(g,e) aggregated with
    cohort-size weights. The overall post ATT weights every (g, e>=0) CATT by cohort
    size, mirroring cs_did.py's overall aggregation, so the two numbers are
    comparable. Identification: cohort-specific parallel trends vs never-treated
    publics; no anticipation at e=-1; IW aggregation is robust to treatment-effect
    heterogeneity across cohorts (no negative TWFE weights). Inference: clustered
    (institution) bootstrap, B=400, percentile CI (repo pattern).

(2) Stacked DiD (Cengiz, Dube, Lindner & Zipperer 2019). One clean 2x2 dataset per
    adoption cohort g inside a fixed event window e in [-4, +2]: treated = cohort-g
    adopters; clean controls = institutions never treated OR adopting after g+2
    (not yet treated anywhere in the window; earlier-treated cohorts excluded).
    Window choice: +2 is the longest post horizon the CSU 2018 cohort supports (panel
    ends 2020) and -4 the longest pre window the UW-Milwaukee 2013 cohort supports
    (panel starts 2009); GSU 2012 lacks e=-4 and the UW 2019 cohort lacks e=+2, so
    those stacks are one year shorter, which stacking tolerates because every stack
    carries its own fixed effects. OLS of retention on treat x post with
    stack-by-unit and stack-by-year fixed effects (absorbed by alternating
    projections, the reghdfe algorithm; equivalent to dummy-variable OLS), SE
    clustered by institution across stacks with the CR1 small-sample correction
    G/(G-1) x (N-1)/(N-K). Drop-2020 (COVID) variant excludes calendar 2020.
    Identification: within-window parallel trends between each cohort and its clean
    controls; clean controls remove the already-treated contamination that biases
    TWFE under staggered timing.

(3) de Chaisemartin & D'Haultfoeuille (2020) DID_M, instantaneous effect. For each
    switch year t, first switchers (G=t) vs not-yet-switched (never-treated or G>t),
    outcome change from t-1 to t, cells weighted by switcher count. This panel has NO
    treatment reversals (adoption is an absorbing state; adoption_year is constant
    within institution), so DID_M consists of the joiner contrasts only and its cells
    coincide with CS ATT(g,g); dynamic effects are already covered by the CS and SA
    event studies, so only the instantaneous DID_M is reported. Inference: clustered
    (institution) bootstrap, B=999, percentile CI.

Replicated estimators (so data/estimator_comparison.csv is built entirely by this
script, with identical specifications and rng seeds as the source scripts; the
numbers match their printed output):
    TWFE static, full panel          -> analyze_did.py
    TWFE static, matched sample      -> wild_cluster.py (incl. state-level wild
                                        cluster restricted bootstrap p, Webb weights)
    CS overall post ATT, full panel  -> cs_did.py    (vectorized, same seed => same draws)
    CS overall post ATT, matched     -> match_did.py (vectorized, same seed => same draws)
    SA IW overall post ATT, matched  -> robustness.py (verbatim sa_estimate)

Outputs: data/estimators_extra.csv (new estimators), data/estimator_comparison.csv
(consolidated table), data/sa_full_event_study.csv. No existing file is modified.
"""
import os, numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
B = 400          # default bootstrap reps (repo pattern)
B_DCDH = 999     # DID_M is cheap; use more reps
Z = 1.96

# ---------- shared panel prep (identical to cs_did.py) ----------
df = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
df.loc[df.adoption_year > 2020, "adoption_year"] = np.nan   # post-window adopters = control
df["G"] = df.adoption_year.fillna(0).astype(int)
wide = df.pivot_table(index="unitid", columns="year", values="retention_rate")
Gser = df.groupby("unitid")["G"].first()
ST = df.groupby("unitid")["state"].first()
years = sorted(df.year.unique())
cohorts = sorted(c for c in Gser.unique() if c != 0)
allu = list(wide.index)
YM = wide.values.astype(float)
Gfull = Gser.loc[wide.index].values
ycol = {y: j for j, y in enumerate(wide.columns)}
print(f"institutions {len(allu)}  cohorts {cohorts}  "
      f"cohort sizes { {c: int((Gfull == c).sum()) for c in cohorts} }")

rows_extra, rows_cmp = [], []


def ci_str(lo, hi):
    return f"[{lo*100:+.2f}, {hi*100:+.2f}]"


# =====================================================================
# A. Replications of existing estimators (for the comparison table)
# =====================================================================

# ---- A1. TWFE static, full panel (specification of analyze_did.py) ----
d0 = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
d0["adoption_year"] = pd.to_numeric(d0["adoption_year"], errors="coerce")
late = d0.adoption_year > 2020
d0.loc[late, "treated"] = 0; d0.loc[late, "adoption_year"] = np.nan
d0["treat_post"] = ((d0.treated == 1) & (d0.year >= d0.adoption_year)).astype(int)
m1 = smf.ols("retention_rate ~ treat_post + C(unitid) + C(year)", data=d0) \
        .fit(cov_type="cluster", cov_kwds={"groups": d0["unitid"]})
b1, se1, p1 = m1.params["treat_post"], m1.bse["treat_post"], m1.pvalues["treat_post"]
print(f"\n[A1] TWFE static, full panel: {b1*100:+.2f} pp  SE {se1*100:.2f}  p={p1:.3f}")
rows_cmp.append(("TWFE static", "full panel (736)", b1, b1 - Z*se1, b1 + Z*se1, 29,
                 f"analyze_did.py spec; cluster by institution; p={p1:.3f}; biased under "
                 "staggered timing (Goodman-Bacon), reported as benchmark only"))

# ---- A2. matched sample (verbatim construction from robustness.py / match_did.py) ----
PREW = list(range(2011, 2018)); K = 5
treated = [u for u in wide.index if Gser[u] in (2018, 2019)]
ctrl_cand = [u for u in wide.index if Gser[u] == 0]
def lvslope(u):
    ys = [y for y in PREW if y in wide.columns and pd.notna(wide.loc[u, y])]
    if len(ys) < 4: return None
    v = [wide.loc[u, y] for y in ys]
    return np.mean(v), np.polyfit(ys, v, 1)[0]
feat = {u: lvslope(u) for u in treated + ctrl_cand}; feat = {u: f for u, f in feat.items() if f}
treated = [u for u in treated if u in feat]; ctrl_cand = [u for u in ctrl_cand if u in feat]
L = np.array(list(feat.values())); muL, sdL = L.mean(0), L.std(0)
z = {u: (np.array(feat[u]) - muL) / sdL for u in feat}
matched = set()
for t in treated:
    matched.update(sorted(ctrl_cand, key=lambda c: np.sum((z[t] - z[c]) ** 2))[:K])
matched = sorted(matched)
sample = treated + matched
Gm = {u: (Gser[u] if Gser[u] in (2018, 2019) else 0) for u in sample}
print(f"[A2] matched sample: {len(treated)} treated + {len(matched)} controls")

# ---- A3. TWFE static, matched sample + state-level WCR p (spec of wild_cluster.py) ----
recs = []
for u in sample:
    g = Gser[u]
    for y in years:
        if y in wide.columns and pd.notna(wide.loc[u, y]):
            tp = 1 if (g in (2018, 2019) and y >= g) else 0
            recs.append((u, y, ST[u], wide.loc[u, y], tp))
dw = pd.DataFrame(recs, columns=["unit", "year", "state", "Y", "treat_post"])
states = sorted(dw.state.unique())
Xw = pd.concat([dw[["treat_post"]],
                pd.get_dummies(dw.unit, prefix="u", drop_first=True),
                pd.get_dummies(dw.year, prefix="y", drop_first=True)], axis=1).astype(float)
Xw = sm.add_constant(Xw)
yw = dw.Y.values; Xv = Xw.values
m_state = sm.OLS(yw, Xv).fit(cov_type="cluster", cov_kwds={"groups": dw.state.values})
m_unit = sm.OLS(yw, Xv).fit(cov_type="cluster", cov_kwds={"groups": dw.unit.values})
bw, sew_state, tw = m_state.params[1], m_state.bse[1], m_state.params[1] / m_state.bse[1]
sew_unit = m_unit.bse[1]
# fast exact sandwich for the WCR loop: V11 = c * sum_g (sum_i z_i e_i)^2, z = X a1
XtX = Xv.T @ Xv
a1 = np.linalg.solve(XtX, np.eye(Xv.shape[1])[:, 1])
zrow = Xv @ a1
scode = pd.factorize(dw.state, sort=True)[0]
pinvX = np.linalg.pinv(Xv)
def t_fast(yv):
    bb = pinvX @ yv
    e = yv - Xv @ bb
    s_g = np.bincount(scode, weights=zrow * e, minlength=len(states))
    return bb[1] / np.sqrt(c_emp * (s_g ** 2).sum())
resid_main = yw - Xv @ (pinvX @ yw)
s_g0 = np.bincount(scode, weights=zrow * resid_main, minlength=len(states))
c_emp = sew_state ** 2 / (s_g0 ** 2).sum()          # statsmodels' CR correction, backed out
assert abs(t_fast(yw) - tw) < 1e-8, "fast sandwich does not replicate statsmodels t"
Xr = Xw.drop(columns=["treat_post"])
m0 = sm.OLS(yw, Xr.values).fit()
yhat0, uhat = m0.fittedvalues, m0.resid
webb = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
rng_w = np.random.default_rng(7)                    # same seed/draws as wild_cluster.py
cnt = 0
for _ in range(999):
    w = {s: rng_w.choice(webb) for s in states}
    ystar = yhat0 + np.array([w[s] for s in dw.state.values]) * uhat
    if abs(t_fast(ystar)) >= abs(tw):
        cnt += 1
p_wcr = (cnt + 1) / (999 + 1)
print(f"[A3] TWFE static, matched: {bw*100:+.2f} pp  SE(inst) {sew_unit*100:.2f}  "
      f"SE(state) {sew_state*100:.2f}  WCR p={p_wcr:.3f}")
rows_cmp.append(("TWFE static", "matched (27 treated + 111 controls)", bw,
                 bw - Z*sew_unit, bw + Z*sew_unit, 27,
                 f"wild_cluster.py spec; CI from institution-clustered SE; state-clustered "
                 f"SE {sew_state*100:.2f}; state-level WCR (Webb, B=999) p={p_wcr:.3f}"))

# ---- A4. CS overall post ATT, full panel (cs_did.py, vectorized, same seed) ----
def cs_overall_full(Y, Ga):
    num = den = 0.0
    for g in cohorts:
        bcol = ycol.get(g - 1)
        if bcol is None: continue
        for t in years:
            if t < g: continue
            d = Y[:, ycol[t]] - Y[:, bcol]
            fin = np.isfinite(d)
            tm = fin & (Ga == g)
            cm = fin & ((Ga == 0) | (Ga > t))
            nt, nc = int(tm.sum()), int(cm.sum())
            if nt < 1 or nc < 5: continue
            num += (d[tm].mean() - d[cm].mean()) * nt; den += nt
    return num / den if den else np.nan

cs_full = cs_overall_full(YM, Gfull)
rng_csf = np.random.default_rng(7)                  # same seed/draws as cs_did.py boot()
bs = []
for _ in range(B):
    samp = rng_csf.choice(allu, size=len(allu), replace=True)
    idx = wide.index.get_indexer(samp)
    e = cs_overall_full(YM[idx], Gfull[idx])
    if not np.isnan(e): bs.append(e)
bs = np.array(bs)
cs_full_ci = np.percentile(bs, [2.5, 97.5])
print(f"[A4] CS overall, full panel: {cs_full*100:+.2f} pp  SE {bs.std(ddof=1)*100:.2f}  "
      f"95% CI {ci_str(*cs_full_ci)}")
rows_cmp.append(("Callaway-Sant'Anna overall post ATT", "full panel (736)", cs_full,
                 cs_full_ci[0], cs_full_ci[1], 29,
                 "cs_did.py replication (same seed); not-yet-treated controls; "
                 "cluster bootstrap B=400"))

# ---- A5. CS overall post ATT, matched sample (match_did.py, vectorized, same seed) ----
Gm_arr = np.array([Gm[u] for u in sample])
Wm = wide.loc[sample].values.astype(float)
def cs_overall_matched(Y, Ga):
    num = den = 0.0
    for g in (2018, 2019):
        bcol = ycol[g - 1]
        for t in years:
            if t < g: continue
            d = Y[:, ycol[t]] - Y[:, bcol]
            fin = np.isfinite(d)
            tm = fin & (Ga == g)
            cm = fin & (Ga == 0)
            nt, nc = int(tm.sum()), int(cm.sum())
            if nt < 1 or nc < 5: continue
            num += (d[tm].mean() - d[cm].mean()) * nt; den += nt
    return num / den if den else np.nan

cs_m = cs_overall_matched(Wm, Gm_arr)
rng_csm = np.random.default_rng(7)                  # same seed/draws as match_did.py boot()
bs = []
for _ in range(B):
    samp = rng_csm.choice(sample, len(sample), replace=True)
    e = cs_overall_matched(wide.loc[samp].values.astype(float),
                           np.array([Gm[u] for u in samp]))
    if not np.isnan(e): bs.append(e)
bs = np.array(bs)
cs_m_ci = np.percentile(bs, [2.5, 97.5])
print(f"[A5] CS overall, matched: {cs_m*100:+.2f} pp  SE {bs.std(ddof=1)*100:.2f}  "
      f"95% CI {ci_str(*cs_m_ci)}")
rows_cmp.append(("Callaway-Sant'Anna overall post ATT", "matched (27 + 111)", cs_m,
                 cs_m_ci[0], cs_m_ci[1], 27,
                 "match_did.py replication (same seed); never-treated matched controls; "
                 "cluster bootstrap B=400"))

# ---- A6. Sun-Abraham IW, matched sample (verbatim sa_estimate from robustness.py) ----
def sa_estimate(units, Gv, Wd):
    rec = []
    for u in units:
        g = Gv[u]
        for y in years:
            if y in Wd.columns and pd.notna(Wd.loc[u, y]):
                e = (y - g) if g else np.nan
                rec.append((u, y, Wd.loc[u, y], g, e))
    d = pd.DataFrame(rec, columns=["u", "y", "Y", "g", "e"])
    def lab(r):
        if r.g == 0: return "ctrl"
        e = int(r.e)
        if e <= -7: e = -7
        if e == -1: return "ref"
        return f"g{int(r.g)}_e{e}"
    d["lab"] = d.apply(lab, axis=1)
    Dlab = pd.get_dummies(d["lab"]).drop(columns=[c for c in ["ctrl", "ref"] if c in d["lab"].unique()], errors="ignore")
    X = pd.concat([Dlab,
                   pd.get_dummies(d["u"], prefix="u", drop_first=True),
                   pd.get_dummies(d["y"], prefix="y", drop_first=True)], axis=1).astype(float)
    X = sm.add_constant(X)
    m = sm.OLS(d["Y"].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d["u"].values})
    coef = dict(zip(X.columns, m.params))
    nsize = {g: sum(1 for u in units if Gv[u] == g) for g in (2018, 2019)}
    es = {}
    for e in range(-7, 3):
        if e == -1:
            es[e] = 0.0; continue
        parts = []
        for g in (2018, 2019):
            key = f"g{g}_e{e}"
            if key in coef:
                parts.append((coef[key], nsize[g]))
        if parts:
            es[e] = float(np.average([p[0] for p in parts], weights=[p[1] for p in parts]))
    post = [es[e] for e in (0, 1, 2) if e in es]
    return float(np.mean(post)) if post else np.nan, es

sa_att, sa_es = sa_estimate(sample, Gm, wide.loc[sample])
rng_sa = np.random.default_rng(7)                   # same seed/draws as robustness.py
bs = []
for _ in range(B):
    s = rng_sa.choice(sample, len(sample), replace=True)
    Wb = wide.loc[s].reset_index(drop=True)
    Gb = {i: Gm[u] for i, u in enumerate(s)}
    try:
        a, _ = sa_estimate(list(range(len(s))), Gb, Wb)
        if not np.isnan(a): bs.append(a)
    except Exception:
        pass
bs = np.array(bs)
sa_m_ci = np.percentile(bs, [2.5, 97.5])
print(f"[A6] SA IW, matched: {sa_att*100:+.2f} pp  SE {bs.std(ddof=1)*100:.2f}  "
      f"95% CI {ci_str(*sa_m_ci)}")
rows_cmp.append(("Sun-Abraham IW overall post ATT", "matched (27 + 111)", sa_att,
                 sa_m_ci[0], sa_m_ci[1], 27,
                 "robustness.py replication (verbatim, same seed); mean of e=0..2; "
                 "cluster bootstrap B=400"))

# =====================================================================
# B. NEW (1): Sun-Abraham IW event study, FULL panel
# =====================================================================
finm = np.isfinite(YM)
obs_u, obs_t = np.where(finm)                       # sorted by unit position
obs_y = YM[obs_u, obs_t]
yrs_arr = np.array(list(wide.columns))
obs_year = yrs_arr[obs_t]
obs_g = Gfull[obs_u]
n_obs = len(obs_u)
# cohort-by-binned-event labels (ref e=-1, e<=-7 binned to -7, as in robustness.py)
ebin = np.where(obs_g > 0, np.maximum(obs_year - obs_g, -7), 0)
labels = sorted({(int(g), int(e)) for g, e in zip(obs_g[obs_g > 0], ebin[obs_g > 0])
                 if e != -1})
lab2col = {le: i for i, le in enumerate(labels)}
labcol = np.full(n_obs, -1)
for i in range(n_obs):
    if obs_g[i] > 0 and ebin[i] != -1:
        labcol[i] = lab2col[(int(obs_g[i]), int(ebin[i]))]
E = np.zeros((n_obs, len(labels)))
sel = labcol >= 0
E[np.where(sel)[0], labcol[sel]] = 1.0
Yd = (obs_year[:, None] == yrs_arr[None, 1:]).astype(float)   # year dummies, drop first
Mfull = np.hstack([E, Yd])
ncols_E = len(labels)

def _fwl_coefs(rowidx, uid, nunits):
    """Unit-FE absorption by demeaning (FWL), then OLS of demeaned Y on demeaned X."""
    M = Mfull[rowidx]; yv = obs_y[rowidx]
    cntu = np.bincount(uid, minlength=nunits).astype(float)
    Mm = np.empty_like(M)
    for j in range(M.shape[1]):
        Mm[:, j] = (np.bincount(uid, weights=M[:, j], minlength=nunits) / cntu)[uid]
    ym = (np.bincount(uid, weights=yv, minlength=nunits) / cntu)[uid]
    beta, *_ = np.linalg.lstsq(M - Mm, yv - ym, rcond=None)
    present = M[:, :ncols_E].sum(0) > 0
    return beta[:ncols_E], present

def sa_full_agg(coefs, present, Ng):
    es = {}
    num = den = 0.0
    n012 = d012 = 0.0
    for (g, e), c in zip(labels, coefs):
        i = lab2col[(g, e)]
        if not present[i] or Ng.get(g, 0) == 0: continue
        es.setdefault(e, []).append((c, Ng[g]))
        if e >= 0:
            num += c * Ng[g]; den += Ng[g]
            if e <= 2:
                n012 += c * Ng[g]; d012 += Ng[g]
    es_agg = {e: float(np.average([p[0] for p in v], weights=[p[1] for p in v]))
              for e, v in es.items()}
    es_agg[-1] = 0.0
    return (num / den if den else np.nan,
            n012 / d012 if d012 else np.nan, es_agg)

all_rows = np.arange(n_obs)
uid_full = obs_u
coefs0, present0 = _fwl_coefs(all_rows, uid_full, len(allu))
# one-time verification: FWL coefficients equal the full-dummy OLS coefficients
Xchk = np.hstack([Mfull, (obs_u[:, None] == np.arange(1, len(allu))[None, :]).astype(float)])
bchk = sm.OLS(obs_y, sm.add_constant(Xchk)).fit().params[1:1 + ncols_E]
assert np.allclose(coefs0, bchk, atol=1e-7), "FWL does not replicate full-dummy OLS"
print("\n[B] FWL absorption verified against full-dummy OLS (max diff "
      f"{np.abs(coefs0 - bchk).max():.2e})")

Ng0 = {g: int((Gfull == g).sum()) for g in cohorts}
saf_all, saf_012, saf_es = sa_full_agg(coefs0, present0, Ng0)
# bootstrap (cluster = institution), resampled units relabeled as distinct
starts = np.searchsorted(obs_u, np.arange(len(allu)))
ends = np.searchsorted(obs_u, np.arange(len(allu)) + 1)
counts_u = ends - starts
rng_saf = np.random.default_rng(7)
bs_all, bs_012 = [], []
for _ in range(B):
    p = rng_saf.integers(0, len(allu), len(allu))
    rowidx = np.concatenate([np.arange(starts[k], ends[k]) for k in p])
    uid = np.repeat(np.arange(len(allu)), counts_u[p])
    cf, pr = _fwl_coefs(rowidx, uid, len(allu))
    Ng = {g: int((Gfull[p] == g).sum()) for g in cohorts}
    a, a12, _ = sa_full_agg(cf, pr, Ng)
    if not np.isnan(a): bs_all.append(a)
    if not np.isnan(a12): bs_012.append(a12)
bs_all = np.array(bs_all); bs_012 = np.array(bs_012)
saf_ci = np.percentile(bs_all, [2.5, 97.5])
saf_ci12 = np.percentile(bs_012, [2.5, 97.5])
print(f"[B] SA IW, FULL panel, overall post (all horizons): {saf_all*100:+.2f} pp  "
      f"SE {bs_all.std(ddof=1)*100:.2f}  95% CI {ci_str(*saf_ci)}")
print(f"    variant e=0..2 only (matched-comparable):      {saf_012*100:+.2f} pp  "
      f"SE {bs_012.std(ddof=1)*100:.2f}  95% CI {ci_str(*saf_ci12)}")
print("    SA full event study (ref t-1):")
for e in sorted(saf_es):
    print(f"      t{e:+d} [{'pre ' if e < 0 else 'post'}]: {saf_es[e]*100:+6.2f} pp")
pd.DataFrame([(e, saf_es[e]) for e in sorted(saf_es)], columns=["event_time", "att"]) \
  .to_csv(os.path.join(DATA, "sa_full_event_study.csv"), index=False)
note_saf = ("cohort-size-weighted CATT(g,e) over all post horizons; e<=-7 binned; "
            f"e=0..2 variant {saf_012*100:+.2f} pp CI {ci_str(*saf_ci12)}; "
            "never-treated controls; cluster bootstrap B=400")
rows_extra.append(("Sun-Abraham IW overall post ATT", "full panel (736)", saf_all,
                   saf_ci[0], saf_ci[1], 29, note_saf))
rows_cmp.append(("Sun-Abraham IW overall post ATT", "full panel (736)", saf_all,
                 saf_ci[0], saf_ci[1], 29, note_saf))

# =====================================================================
# C. NEW (2): Stacked DiD (Cengiz et al. 2019), window e in [-4, +2]
# =====================================================================
def stacked_did(drop2020=False):
    st_stack, st_unit, st_year, st_y, st_tp = [], [], [], [], []
    diag = []
    for g in cohorts:
        yrs_w = [y for y in years if g - 4 <= y <= g + 2 and not (drop2020 and y == 2020)]
        umask = (Gfull == g) | (Gfull == 0) | (Gfull > g + 2)
        upos = np.where(umask)[0]
        for j, y in ((ycol[y], y) for y in yrs_w):
            fin = np.isfinite(YM[upos, j])
            keep = upos[fin]
            st_stack += [g] * len(keep)
            st_unit += list(keep)
            st_year += [y] * len(keep)
            st_y += list(YM[keep, j])
            st_tp += list(((Gfull[keep] == g) & (y >= g)).astype(float))
        diag.append((g, int((Gfull[upos] == g).sum()),
                     int(((Gfull[upos] == 0) | (Gfull[upos] > g + 2)).sum()),
                     yrs_w[0], yrs_w[-1]))
    stk = np.array(st_stack); unit = np.array(st_unit); yr = np.array(st_year)
    yv = np.array(st_y); x = np.array(st_tp)
    su = pd.factorize(stk * 10000 + unit, sort=True)[0]
    sy = pd.factorize(stk * 10000 + yr, sort=True)[0]
    n_su, n_sy = su.max() + 1, sy.max() + 1
    c1 = np.bincount(su).astype(float); c2 = np.bincount(sy).astype(float)
    def demean(v):
        v = v.copy()
        for _ in range(2000):
            m1 = np.bincount(su, weights=v, minlength=n_su) / c1
            v -= m1[su]
            m2 = np.bincount(sy, weights=v, minlength=n_sy) / c2
            v -= m2[sy]
            if max(np.abs(m1).max(), np.abs(m2).max()) < 1e-12:
                return v
        raise RuntimeError("two-way demeaning did not converge")
    xd, yd_ = demean(x), demean(yv)
    sxx = float(xd @ xd)
    b = float(xd @ yd_) / sxx
    resid = yd_ - b * xd
    cl = pd.factorize(unit, sort=True)[0]          # cluster = institution, across stacks
    s_g = np.bincount(cl, weights=xd * resid)
    Gn = cl.max() + 1; N = len(yv)
    Kp = 1 + n_su + n_sy - len(cohorts)            # treat + absorbed FE params
    corr = (Gn / (Gn - 1)) * ((N - 1) / (N - Kp))
    se = np.sqrt(corr * (s_g ** 2).sum()) / sxx
    return b, se, diag, N, Gn

b_st, se_st, diag, N_st, G_st = stacked_did(False)
b_st0, se_st0, _, N_st0, _ = stacked_did(True)
print(f"\n[C] stacked DiD, window [-4,+2]:")
for g, nt, nc, y0, y1 in diag:
    print(f"    stack {g}: {nt} treated, {nc} clean controls, years {y0}-{y1}")
print(f"    ATT {b_st*100:+.2f} pp  SE {se_st*100:.2f}  "
      f"95% CI {ci_str(b_st - Z*se_st, b_st + Z*se_st)}  (N={N_st}, {G_st} clusters)")
print(f"    drop 2020: ATT {b_st0*100:+.2f} pp  SE {se_st0*100:.2f}  "
      f"95% CI {ci_str(b_st0 - Z*se_st0, b_st0 + Z*se_st0)}  (N={N_st0})")
note_st = ("4 cohort stacks; clean controls = never-treated or adopting after g+2; "
           "stack-by-unit and stack-by-year FE; CI from institution-clustered CR1 SE; "
           "GSU stack lacks e=-4, UW-2019 stack lacks e=+2 (panel edges)")
rows_extra.append(("Stacked DiD (Cengiz et al.)", "full panel, window [-4,+2]", b_st,
                   b_st - Z*se_st, b_st + Z*se_st, 29, note_st))
rows_extra.append(("Stacked DiD (Cengiz et al.), drop 2020", "full panel, window [-4,+2]",
                   b_st0, b_st0 - Z*se_st0, b_st0 + Z*se_st0, 29,
                   "COVID robustness: calendar year 2020 excluded from every stack"))
rows_cmp.append(("Stacked DiD (Cengiz et al.)", "full panel, window [-4,+2]", b_st,
                 b_st - Z*se_st, b_st + Z*se_st, 29,
                 note_st + f"; drop-2020 variant {b_st0*100:+.2f} pp "
                 f"CI {ci_str(b_st0 - Z*se_st0, b_st0 + Z*se_st0)}"))

# =====================================================================
# D. NEW (3): de Chaisemartin-D'Haultfoeuille DID_M, instantaneous
# =====================================================================
def did_m(Y, Ga):
    num = den = 0.0
    for t in cohorts:
        d = Y[:, ycol[t]] - Y[:, ycol[t - 1]]
        fin = np.isfinite(d)
        tm = fin & (Ga == t)                        # first switchers at t
        cm = fin & ((Ga == 0) | (Ga > t))           # not yet switched at t
        nt, nc = int(tm.sum()), int(cm.sum())
        if nt < 1 or nc < 5: continue
        num += (d[tm].mean() - d[cm].mean()) * nt; den += nt
    return num / den if den else np.nan

dm = did_m(YM, Gfull)
rng_dm = np.random.default_rng(7)
bs = []
for _ in range(B_DCDH):
    p = rng_dm.integers(0, len(allu), len(allu))
    e = did_m(YM[p], Gfull[p])
    if not np.isnan(e): bs.append(e)
bs = np.array(bs)
dm_ci = np.percentile(bs, [2.5, 97.5])
print(f"\n[D] dCdH DID_M (instantaneous): {dm*100:+.2f} pp  SE {bs.std(ddof=1)*100:.2f}  "
      f"95% CI {ci_str(*dm_ci)}")
note_dm = ("switchers-vs-not-yet-switched at each adoption year, weighted by switcher "
           "count; no treatment reversals in this panel so DID_M = joiner cells and "
           "coincides with CS ATT(g,g); dynamics covered by CS/SA event studies; "
           "cluster bootstrap B=999")
rows_extra.append(("dCdH DID_M instantaneous", "full panel (736)", dm,
                   dm_ci[0], dm_ci[1], 29, note_dm))
rows_cmp.append(("dCdH DID_M instantaneous", "full panel (736)", dm,
                 dm_ci[0], dm_ci[1], 29, note_dm))

# =====================================================================
# E. write outputs
# =====================================================================
cols = ["estimator", "sample", "att_pp", "ci_lo", "ci_hi", "n_treated", "notes"]
def to_pp(rows):
    return pd.DataFrame([(a, b, round(c * 100, 3), round(d * 100, 3), round(e * 100, 3),
                          f, g) for a, b, c, d, e, f, g in rows], columns=cols)
to_pp(rows_extra).to_csv(os.path.join(DATA, "estimators_extra.csv"), index=False)
to_pp(rows_cmp).to_csv(os.path.join(DATA, "estimator_comparison.csv"), index=False)
print(f"\nsaved data/estimators_extra.csv ({len(rows_extra)} rows), "
      f"data/estimator_comparison.csv ({len(rows_cmp)} rows), "
      "data/sa_full_event_study.csv")
