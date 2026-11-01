"""
J4 supplement: difference-in-differences re-estimated on a retention panel extended to 2024.

The main text keeps the 2009-2020 window and none of its numbers change here. This script
builds a parallel panel (data/retention_panel_ext.csv, 2009-2024) with exactly the logic of
build_outcome_panel.py and re-runs three estimators from the pipeline on it, writing the
results to new files only. Existing scripts and data files are not touched.

Panel. Universe = IPEDS directory 2021, public (inst_control=1), four-or-more-year
(institution_level=4), read from the cached data/raw_directory.csv (pulled again and cached
to data/raw_directory_ext.csv only if that file is absent). Outcome = Urban Institute
Education Data API fall-retention, full-time (ftpt=1) retention_rate. Values for 2009-2020
are read from data/raw_ret.csv, which reproduces data/retention_panel.csv exactly; 2021-2024
are pulled once and cached in data/raw_ret_ext.csv (uid, year, val) as served. The API's
2021-2024 rows carry IPEDS missing codes in retention_rate (-1 missing, -2 not applicable,
-3 suppressed) that the 2009-2020 pull did not; negative values are treated as missing when
the panel is assembled, and zeros are kept as in the original panel. Treatment = adoption
year from data/treatment_panel.csv rows with date_confidence firm or firm_system.

Treatment rules for the extended window. Institutions with a recorded adoption year inside
2021-2024 would be dropped from the sample rather than kept as tiny new cohorts (none exist
in treatment_panel.csv at present). Adoption years after 2024 (Georgia Tech, 2025) stay in
the not-yet-treated control pool, as the main text treats adoptions after 2020. The seven
University of Maine System campuses had undated EAB Navigate use by January 2021, so every
estimate is run twice: maine_rule = keep (Maine campuses in the control pool, as in the
main text) and maine_rule = drop (the seven unitids removed from the panel).

Estimators (copied from cs_did.py, match_did.py and wild_cluster.py, vectorized with numpy
but drawing the same bootstrap samples in the same order from seed 7, so the 2009-2020
window recomputed here must reproduce the manuscript numbers).
  (1) Callaway and Sant'Anna (2021) staggered DiD on the full panel:
      ATT(g,t) = E[Y_t - Y_{g-1} | G=g] - E[Y_t - Y_{g-1} | never-treated or G>t, G!=g];
      overall post ATT and event study aggregated with cohort-size weights; institution-
      clustered bootstrap (B=400) for the SE and percentile 95% CI.
  (2) Matched design: treated = 2018 and 2019 cohorts; each treated institution matched to
      its K=5 nearest never-treated institutions on standardized 2011-2017 retention level
      and slope; Callaway and Sant'Anna with never-treated matched controls; same bootstrap.
  (3) Static two-way fixed-effects DiD on the matched sample, retention on treat x post with
      institution and year fixed effects; inference clustered by state with a wild cluster
      restricted bootstrap (Webb six-point weights, B=999), the few-treated-clusters remedy.
Variants on the extended window: all post years 2009-2024; post period excluding the
pandemic years 2020-2022; post period limited to event times 0 to 2 (the horizons the
original window can observe for the 2018 cohort); and the original 2009-2020 window
recomputed from the extended file as a reproduction check.

Identification. Parallel trends between adopters and (matched) non-adopting public
four-year institutions, conditional on institution and year effects; no anticipation at
event time -1; adoption is an absorbing state. The matched design conditions parallel
trends on pre-adoption level and slope. The extended window adds two threats the main
text avoids: calendar years 2020-2022 mix the adoption effect with pandemic shocks to
retention that differ across states and systems, and the longer post period admits
undated later adopters (Maine among the known ones, others likely undetected) into the
control pool, which attenuates the comparison. These are the reasons the main text keeps
the 2009-2020 window and the extended estimates appear in the supplement only.

Outputs (all new): data/retention_panel_ext.csv, data/raw_ret_ext.csv,
data/extended_window_estimates.csv, data/extended_window_event_study.csv,
j4_supp_event_ext.png and j4_supp_event_ext.pdf (matched event study, original vs
extended window, Maine campuses kept). Column notes for the estimates file: for the two
Callaway and Sant'Anna rows ci_lo/ci_hi are the percentile bootstrap interval and se_pp
the bootstrap SD; for the TWFE rows ci_lo/ci_hi are beta +/- 1.96 x the institution-
clustered SE, se_pp the state-clustered SE, and p_state_wcr the wild cluster restricted
bootstrap p-value. All effects are in percentage points of the retention rate.
"""
import os, csv, json, time, urllib.request
import numpy as np, pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

T_START = time.time()
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
YEARS_ORIG = list(range(2009, 2021))
YEARS_EXT = list(range(2009, 2025))
PULL_YEARS = [y for y in YEARS_EXT if y > 2020]
DIR_YEAR = 2021
PREW = list(range(2011, 2018)); K = 5
MATCH_COHORTS = (2018, 2019)
B_CS = 400; B_WCR = 999; SEED = 7
PANDEMIC = (2020, 2021, 2022)
MAX_E_SHORT = 2


def pull(url):
    out = []
    while url:
        for a in range(6):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    d = json.load(r); break
            except Exception:
                if a == 5: raise
                time.sleep(4 * (a + 1))
        out += d["results"]; url = d.get("next")
    return out


def stamp(msg):
    print(f"[{time.time() - T_START:7.1f}s] {msg}", flush=True)


# ------------------------------------------------------------------ 1. panel 2009-2024
dir_path = os.path.join(DATA, "raw_directory.csv")
if not os.path.exists(dir_path):
    dir_path = os.path.join(DATA, "raw_directory_ext.csv")
    if not os.path.exists(dir_path):
        stamp("pulling directory")
        dirr = pull(f"{BASE}/directory/{DIR_YEAR}/?inst_control=1")
        pd.DataFrame([(x["unitid"], x.get("inst_name"), x.get("state_abbr"),
                       x.get("institution_level"), x.get("inst_size")) for x in dirr],
                     columns=["unitid", "inst_name", "state_abbr", "institution_level",
                              "inst_size"]).to_csv(dir_path, index=False)
dirdf = pd.read_csv(dir_path)
uni = {int(r.unitid): r.state_abbr for r in dirdf.itertuples() if r.institution_level == 4}
stamp(f"public 4-year universe: {len(uni)}")

maine = dirdf[(dirdf.state_abbr == "ME")
              & dirdf.inst_name.str.contains("University of Maine|University of Southern Maine")
              & ~dirdf.inst_name.str.contains("Central Office")]
MAINE = sorted(int(u) for u in maine.unitid)
assert len(MAINE) == 7, MAINE
stamp(f"University of Maine System campuses: {MAINE}")

adopt, system = {}, {}
with open(os.path.join(DATA, "treatment_panel.csv")) as f:
    for r in csv.DictReader(f):
        if r["adoption_year"] and r["date_confidence"] in ("firm", "firm_system"):
            adopt[int(r["unitid"])] = int(float(r["adoption_year"]))
            system[int(r["unitid"])] = r["system"]
stamp(f"treated (firm year): {len(adopt)}; adoption years {sorted(set(adopt.values()))}")

# retention 2009-2020 from the existing raw cache
raw = pd.read_csv(os.path.join(DATA, "raw_ret.csv"))
ret = {}
for r in raw[raw.year.isin(YEARS_ORIG)].itertuples():
    if int(r.uid) in uni and pd.notna(r.val):
        ret[(int(r.uid), int(r.year))] = float(r.val)

# retention 2021-2024: cached pull
ext_path = os.path.join(DATA, "raw_ret_ext.csv")
parts = [pd.read_csv(ext_path)] if os.path.exists(ext_path) else []
have = set(parts[0].year.unique()) if parts else set()
for y in PULL_YEARS:
    if y in have:
        continue
    rows = pull(f"{BASE}/fall-retention/{y}/?ftpt=1")
    add = pd.DataFrame([(x["unitid"], y, x["retention_rate"]) for x in rows
                        if x.get("retention_rate") is not None], columns=["uid", "year", "val"])
    parts.append(add)
    pd.concat(parts, ignore_index=True).to_csv(ext_path, index=False)
    stamp(f"  pulled fall-retention {y}: {len(rows)} rows, {len(add)} with a rate (cached)")
cache = pd.concat(parts, ignore_index=True)
n_codes = int((cache.val < 0).sum())
stamp(f"raw_ret_ext.csv: {len(cache)} rows, {n_codes} negative missing codes dropped "
      f"(values {sorted(cache.loc[cache.val < 0, 'val'].unique())})")
for r in cache.itertuples():
    if int(r.year) in PULL_YEARS and int(r.uid) in uni and pd.notna(r.val) and r.val >= 0:
        ret[(int(r.uid), int(r.year))] = float(r.val)

out = []
for (uid, y), rr in sorted(ret.items()):
    ay = adopt.get(uid)
    out.append({"unitid": uid, "year": y, "state": uni.get(uid), "retention_rate": rr,
                "system": system.get(uid, ""), "adoption_year": ay if ay else "",
                "treated": 1 if ay else 0, "post": 1 if (ay and y >= ay) else 0,
                "event_time": (y - ay) if ay else ""})
panel_path = os.path.join(DATA, "retention_panel_ext.csv")
with open(panel_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
panel = pd.read_csv(panel_path)
stamp(f"extended panel: {len(panel)} rows, {panel.unitid.nunique()} institutions, "
      f"years {panel.year.min()}-{panel.year.max()}")
print(panel.groupby("year").unitid.nunique().to_string())

# reproduction check against the submitted panel
old = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
chk = old.merge(panel[panel.year <= 2020], on=["unitid", "year"], how="outer",
                suffixes=("_old", "_ext"), indicator=True)
n_only_old = int((chk._merge == "left_only").sum()); n_only_ext = int((chk._merge == "right_only").sum())
both = chk[chk._merge == "both"]
n_mis = int((np.abs(both.retention_rate_old - both.retention_rate_ext) > 1e-9).sum())
stamp(f"2009-2020 check vs retention_panel.csv: rows only in old {n_only_old}, only in ext "
      f"{n_only_ext}, value mismatches {n_mis}")
MISMATCH = n_only_old + n_only_ext + n_mis


# ------------------------------------------------------------------ 2. estimators
def arrays(years, maine_rule):
    """Wide outcome matrix and cohort vector for a window and a Maine rule."""
    df = panel[panel.year.isin(years)].copy()
    if maine_rule == "drop":
        df = df[~df.unitid.isin(MAINE)]
    df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
    hi = max(years)
    dropped = sorted(df.loc[(df.adoption_year > 2020) & (df.adoption_year <= hi), "unitid"].unique())
    df = df[~df.unitid.isin(dropped)]                      # 2021-hi adopters: dropped
    df.loc[df.adoption_year > hi, "adoption_year"] = np.nan  # later adopters: controls
    G = df.groupby("unitid")["adoption_year"].first().fillna(0).astype(int)
    wide = df.pivot_table(index="unitid", columns="year", values="retention_rate")
    wide = wide.reindex(columns=years)
    ST = df.groupby("unitid")["state"].first()
    return wide, G.loc[wide.index], ST.loc[wide.index], dropped


def cs_core(Y, Gv, yrs, cohorts, nyt, drop_years=(), max_e=None):
    """Callaway-Sant'Anna ATT(g,t), overall post ATT and event study, cohort-size weights.
    nyt=True: controls = never-treated or not-yet-treated (cs_did.py);
    nyt=False: controls = never-treated only (match_did.py)."""
    col = {y: i for i, y in enumerate(yrs)}
    post, es = [], {}
    for g in cohorts:
        if (g - 1) not in col:
            continue
        tg = Gv == g
        if not tg.any():
            continue
        yb = Y[:, col[g - 1]]
        for t in yrs:
            if t in drop_years:
                continue
            yt = Y[:, col[t]]
            ok = ~np.isnan(yb) & ~np.isnan(yt)
            tr = tg & ok
            cm = (((Gv == 0) | (Gv > t)) & (Gv != g) & ok) if nyt else ((Gv == 0) & ok)
            nt, nc = int(tr.sum()), int(cm.sum())
            if nt < 1 or nc < 5:
                continue
            att = (yt[tr] - yb[tr]).mean() - (yt[cm] - yb[cm]).mean()
            e = t - g
            es.setdefault(e, []).append((att, nt))
            if t >= g and (max_e is None or e <= max_e):
                post.append((att, nt))
    wm = lambda P: float(np.average([x[0] for x in P], weights=[x[1] for x in P])) if P else np.nan
    return wm(post), {e: wm(v) for e, v in es.items()}


def cs_boot(Y, Gv, units, yrs, cohorts, nyt, B, **kw):
    """Institution-clustered bootstrap; same draw sequence as cs_did.py / match_did.py."""
    rng = np.random.default_rng(SEED)
    pos = {u: i for i, u in enumerate(units)}
    ests = []
    for _ in range(B):
        samp = rng.choice(units, size=len(units), replace=True)
        idx = np.fromiter((pos[u] for u in samp), int, len(samp))
        o, _ = cs_core(Y[idx], Gv[idx], yrs, cohorts, nyt, **kw)
        if not np.isnan(o):
            ests.append(o)
    ests = np.array(ests)
    return float(ests.std(ddof=1)), np.percentile(ests, [2.5, 97.5])


def match_sample(wide, G):
    """k-NN matching of match_did.py: 2018/2019 cohorts to never-treated on 2011-17 level+slope."""
    treated = [u for u in wide.index if G[u] in MATCH_COHORTS]
    ctrl = [u for u in wide.index if G[u] == 0]

    def level_slope(u):
        ys = [y for y in PREW if y in wide.columns and pd.notna(wide.loc[u, y])]
        if len(ys) < 4:
            return None
        v = [wide.loc[u, y] for y in ys]
        return np.mean(v), np.polyfit(ys, v, 1)[0]
    feat = {u: level_slope(u) for u in treated + ctrl}
    feat = {u: f for u, f in feat.items() if f is not None}
    treated = [u for u in treated if u in feat]; ctrl = [u for u in ctrl if u in feat]
    L = np.array([feat[u] for u in feat]); mu = L.mean(0); sd = L.std(0)
    z = {u: (np.array(feat[u]) - mu) / sd for u in feat}
    matched = set()
    for t in treated:
        d = sorted(ctrl, key=lambda c: np.sum((z[t] - z[c]) ** 2))
        matched.update(d[:K])
    return treated, sorted(matched), feat


def wcr(wide, G, ST, sample, yrs, drop_years=(), max_e=None):
    """Static TWFE DiD on the matched sample; state-clustered wild cluster restricted
    bootstrap with Webb weights (wild_cluster.py)."""
    rows = []
    for u in sample:
        g = int(G[u])
        for y in yrs:
            if y in drop_years or pd.isna(wide.loc[u, y]):
                continue
            if g in MATCH_COHORTS and max_e is not None and y - g > max_e:
                continue
            tp = 1 if (g in MATCH_COHORTS and y >= g) else 0
            rows.append((u, y, ST[u], wide.loc[u, y], tp))
    d = pd.DataFrame(rows, columns=["unit", "year", "state", "Y", "treat_post"])
    states = sorted(d.state.unique())
    X = pd.concat([d[["treat_post"]], pd.get_dummies(d.unit, prefix="u", drop_first=True),
                   pd.get_dummies(d.year, prefix="y", drop_first=True)], axis=1).astype(float)
    X = sm.add_constant(X); Xv = X.values
    y = d.Y.values; sid = d.state.values

    def fit_t(yv):
        m = sm.OLS(yv, Xv).fit(cov_type="cluster", cov_kwds={"groups": sid})
        return m.params[1], m.bse[1], m.params[1] / m.bse[1]
    b, se_state, t_hat = fit_t(y)
    m_u = sm.OLS(y, Xv).fit(cov_type="cluster", cov_kwds={"groups": d.unit.values})
    se_unit = m_u.bse[1]
    Xr = X.drop(columns=["treat_post"]).values
    m0 = sm.OLS(y, Xr).fit(); yhat0, uhat = m0.fittedvalues, m0.resid
    webb = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    rng = np.random.default_rng(SEED); cnt = 0
    for _ in range(B_WCR):
        w = {s: rng.choice(webb) for s in states}
        ystar = yhat0 + np.array([w[s] for s in sid]) * uhat
        if abs(fit_t(ystar)[2]) >= abs(t_hat):
            cnt += 1
    p = (cnt + 1) / (B_WCR + 1)
    ntr = d.loc[d.treat_post == 1, "unit"].nunique()
    return b, se_unit, se_state, p, ntr, d.unit.nunique() - ntr, len(states)


# ------------------------------------------------------------------ 3. run
VARIANTS = [  # (window label, years, variant label, drop_years, max_e)
    ("2009-2024", YEARS_EXT, "all post years", (), None),
    ("2009-2024", YEARS_EXT, "post excl. 2020-2022", PANDEMIC, None),
    ("2009-2024", YEARS_EXT, "post t+0..t+2", (), MAX_E_SHORT),
    ("2009-2020", YEARS_ORIG, "all post years (reproduction)", (), None),
]
est_rows, es_rows, fig_es = [], [], {}
for maine_rule in ("keep", "drop"):
    for window, yrs, variant, dropy, max_e in VARIANTS:
        wide, G, ST, dropped_units = arrays(yrs, maine_rule)
        Y = wide.values.astype(float); Gv = G.values; units = list(wide.index)
        cohorts = sorted(int(c) for c in set(Gv) if c != 0)
        tag = f"maine={maine_rule} window={window} variant='{variant}'"
        stamp(f"--- {tag}: {len(units)} institutions, cohorts "
              f"{ {c: int((Gv == c).sum()) for c in cohorts} }, dropped 2021-{max(yrs)} adopters {dropped_units}")

        # (a) full-panel CS
        o, es = cs_core(Y, Gv, yrs, cohorts, True, dropy, max_e)
        se, ci = cs_boot(Y, Gv, units, yrs, cohorts, True, B_CS, drop_years=dropy, max_e=max_e)
        n_tr = int((Gv != 0).sum())
        est_rows.append(["Callaway-Sant'Anna overall post ATT", f"full panel ({len(units)})",
                         window, variant, maine_rule, o * 100, ci[0] * 100, ci[1] * 100, se * 100,
                         "", n_tr, len(units) - n_tr])
        stamp(f"  CS full: {o*100:+.3f} pp  SE {se*100:.3f}  CI [{ci[0]*100:+.3f}, {ci[1]*100:+.3f}]")
        if variant.startswith("all post"):
            es_rows += [[f"cs_full_{window}", maine_rule, e, es[e] * 100] for e in sorted(es)]

        # (b) matched CS
        treated, matched, feat = match_sample(wide, G)
        sample = treated + matched
        Gm = np.array([G[u] if G[u] in MATCH_COHORTS else 0 for u in sample])
        Ym = wide.loc[sample].values.astype(float)
        om, esm = cs_core(Ym, Gm, yrs, list(MATCH_COHORTS), False, dropy, max_e)
        sem, cim = cs_boot(Ym, Gm, sample, yrs, list(MATCH_COHORTS), False, B_CS,
                           drop_years=dropy, max_e=max_e)
        est_rows.append(["Callaway-Sant'Anna overall post ATT",
                         f"matched ({len(treated)} + {len(matched)})", window, variant, maine_rule,
                         om * 100, cim[0] * 100, cim[1] * 100, sem * 100, "", len(treated), len(matched)])
        stamp(f"  CS matched ({len(treated)} + {len(matched)}): {om*100:+.3f} pp  SE {sem*100:.3f}  "
              f"CI [{cim[0]*100:+.3f}, {cim[1]*100:+.3f}]")
        if variant.startswith("all post"):
            es_rows += [[f"matched_{window}", maine_rule, e, esm[e] * 100] for e in sorted(esm)]
            if maine_rule == "keep":
                fig_es[window] = esm

        # (c) matched TWFE with state WCR
        Gs = pd.Series(Gm, index=sample)
        b, se_u, se_s, p, ntr, nco, nst = wcr(wide, Gs, ST, sample, yrs, dropy, max_e)
        est_rows.append(["TWFE static (state WCR bootstrap)", f"matched ({ntr} + {nco}, {nst} states)",
                         window, variant, maine_rule, b * 100, (b - 1.96 * se_u) * 100,
                         (b + 1.96 * se_u) * 100, se_s * 100, round(p, 4), ntr, nco])
        stamp(f"  TWFE matched: {b*100:+.3f} pp  SE(inst) {se_u*100:.3f}  SE(state) {se_s*100:.3f}  "
              f"WCR p = {p:.3f}")

cols = ["estimator", "sample", "window", "variant", "maine_rule", "att_pp", "ci_lo", "ci_hi",
        "se_pp", "p_state_wcr", "n_treated", "n_control"]
est = pd.DataFrame(est_rows, columns=cols)
for c in ("att_pp", "ci_lo", "ci_hi", "se_pp"):
    est[c] = est[c].astype(float).round(3)
est.to_csv(os.path.join(DATA, "extended_window_estimates.csv"), index=False)
esdf = pd.DataFrame(es_rows, columns=["design", "maine_rule", "event_time", "att_pp"])
esdf["att_pp"] = esdf.att_pp.round(4)
esdf.to_csv(os.path.join(DATA, "extended_window_event_study.csv"), index=False)
stamp("saved data/extended_window_estimates.csv and data/extended_window_event_study.csv")

# ------------------------------------------------------------------ 4. figure
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.axvspan(1.5, 4.5, color="0.92", zorder=0)
for window, es, style, col, mk, ms, z, lab in [
        ("2009-2024", fig_es["2009-2024"], "-", "black", "o", 6, 2, "Extended window (2009-2024)"),
        ("2009-2020", fig_es["2009-2020"], "--", "0.45", "s", 4, 3, "Original window (2009-2020)")]:
    xs = sorted(es)
    ax.plot(xs, [es[e] * 100 for e in xs], style, color=col, linewidth=1.6, marker=mk,
            markersize=ms, markerfacecolor="white" if window == "2009-2020" else col,
            label=lab, zorder=z)
ax.axhline(0, color="black", linewidth=0.6)
ax.axvline(-0.5, color="black", linewidth=0.8, linestyle=":")
lo = ax.get_ylim()[0]
ax.text(3, lo + 0.05, "calendar 2020-2022\n(2018 cohort)", ha="center", va="bottom", fontsize=7.5, color="0.3")
ax.set_xlabel("Years since adoption (reference t-1)")
ax.set_ylabel("ATT on full-time retention (pp)")
ax.set_title("Matched Callaway-Sant'Anna event study, 2018 and 2019 cohorts", fontsize=11)
ax.legend(frameon=False, fontsize=9, loc="upper left")
ax.set_xticks(sorted(fig_es["2009-2024"]))
plt.tight_layout()
plt.savefig(os.path.join(HERE, "j4_supp_event_ext.png"), dpi=150, bbox_inches="tight")
plt.savefig(os.path.join(HERE, "j4_supp_event_ext.pdf"), bbox_inches="tight")
stamp("saved j4_supp_event_ext.png/.pdf")

print("\n" + est.to_string(index=False))
print(f"\npanel reproduction mismatches (2009-2020): {MISMATCH}")
stamp(f"done; total runtime {(time.time() - T_START)/60:.1f} min")
