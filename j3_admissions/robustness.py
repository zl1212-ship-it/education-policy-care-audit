"""
Robustness for the J3 equity result (entering-class %URM), addressing the positive
pre-trend visible in the headline event study.

(1) Matched-control DiD. For each pre-COVID adopter, pick its 5 nearest never-adopters by
    standardized distance on TWO features of the 2009-2015 %URM series -- the mean LEVEL and
    the OLS SLOPE. Matching on the slope (not only the level) is what guards against
    attributing a pre-existing diversity trajectory to the policy. Re-estimate the
    Callaway-Sant'Anna overall ATT against the matched pool and report the balance table.

(2) Placebo-in-time. Re-assign each adopter a fake adoption 3 years before its true year and
    re-estimate; a true effect should vanish at the placebo date (the coefficient should be
    statistically indistinguishable from zero), confirming parallel pre-trends.

Writes data/matched_balance.csv and prints both checks.
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
rng = np.random.default_rng(11)
PRE = list(range(2009, 2016))
TREAT_COHORTS = [2016, 2017, 2018, 2019]
B = 500


def load_urm():
    comp = pd.read_csv(os.path.join(DATA, "composition_panel.csv"))
    comp["share_urm"] = comp["share_urm"] * 100
    treat = pd.read_csv(os.path.join(DATA, "treatment_panel.csv"))
    adopt = treat.set_index("unitid")["adoption_year"]
    cohort = treat.set_index("unitid")["cohort"]
    wide = comp.pivot_table(index="unitid", columns="year", values="share_urm")
    wide = wide[[y for y in range(2009, 2020) if y in wide.columns]]
    return wide, adopt, cohort


def level_slope(row):
    ys = np.array(PRE, float); v = row[PRE].to_numpy(float)
    if np.isnan(v).any():
        return None
    slope = np.polyfit(ys - ys.mean(), v, 1)[0]
    return v.mean(), slope


def _cells(wide, Gmap, idx, years, cohorts):
    """Precompute (g,t) post-cell matrices for the vectorized C&S; see analyze_did.py."""
    units = list(idx); N = len(units); pos = {u: i for i, u in enumerate(units)}
    G = np.array([Gmap[u] for u in units], float)
    col_of = {y: j for j, y in enumerate(wide.columns)}
    Y = wide.loc[units].to_numpy(float)
    T, C, TD, CD = [], [], [], []
    for g in cohorts:
        if (g - 1) not in col_of:
            continue
        jb = col_of[g - 1]
        for t in years:
            if t not in col_of or t < g:
                continue
            d = Y[:, col_of[t]] - Y[:, jb]
            valid = ~np.isnan(d)
            tre = ((G == g) & valid).astype(float)
            ctr = (((G == 0) | (G > t)) & (G != g) & valid).astype(float)
            df = np.where(valid, d, 0.0)
            T.append(tre); C.append(ctr); TD.append(tre * df); CD.append(ctr * df)
    return (np.array(T), np.array(C), np.array(TD), np.array(CD), pos, N, units)


def _agg(cells, W):
    Tm, Cm, TD, CD = cells[0], cells[1], cells[2], cells[3]
    if Tm.size == 0:
        return np.full(W.shape[1], np.nan)
    tden = Tm @ W; cden = Cm @ W
    feas = (tden >= 1) & (cden >= 5)
    with np.errstate(divide="ignore", invalid="ignore"):
        att = (TD @ W) / np.where(tden > 0, tden, 1) - (CD @ W) / np.where(cden > 0, cden, 1)
    w = np.where(feas, tden, 0.0)
    num = (np.where(feas, att, 0.0) * w).sum(0); den = w.sum(0)
    return np.where(den > 0, num / den, np.nan)


def cs_overall(wide, G, idx, years, cohorts):
    cells = _cells(wide, G, idx, years, cohorts)
    return float(_agg(cells, np.ones((cells[5], 1)))[0])


def boot(wide, Gmap, idx, years, cohorts):
    cells = _cells(wide, Gmap, idx, years, cohorts)
    pos, N = cells[4], cells[5]
    base = list(idx)
    Wb = np.empty((N, B))
    for b in range(B):
        samp = rng.choice(base, size=len(base), replace=True)
        Wb[:, b] = np.bincount([pos[u] for u in samp], minlength=N)
    ob = _agg(cells, Wb)
    ob = ob[~np.isnan(ob)]
    return ob.std(ddof=1)


def main():
    wide, adopt, cohort = load_urm()
    years = sorted(wide.columns)

    treated = [u for u in wide.index if cohort.get(u) == "pre_covid"
               and level_slope(wide.loc[u]) is not None]
    never = [u for u in wide.index if cohort.get(u) == "never"
             and level_slope(wide.loc[u]) is not None]

    feat = {u: level_slope(wide.loc[u]) for u in treated + never}
    L = np.array([feat[u][0] for u in treated + never])
    S = np.array([feat[u][1] for u in treated + never])
    lmu, lsd = L.mean(), L.std(); smu, ssd = S.mean(), S.std()

    def z(u):
        l, s = feat[u]
        return np.array([(l - lmu) / lsd, (s - smu) / ssd])

    # nearest 5 never-adopters per treated unit (by standardized level+slope)
    matched = set()
    for u in treated:
        zu = z(u)
        d = sorted(never, key=lambda c: np.sum((zu - z(c)) ** 2))
        matched.update(d[:5])
    matched = list(matched)

    # balance
    def avg(group, f):
        return np.mean([feat[u][f] for u in group])
    bal = pd.DataFrame([
        {"group": "treated (pre-COVID adopters)", "n": len(treated),
         "urm_level_0915": round(avg(treated, 0), 2), "urm_slope_0915": round(avg(treated, 1), 3)},
        {"group": "all never-adopters", "n": len(never),
         "urm_level_0915": round(avg(never, 0), 2), "urm_slope_0915": round(avg(never, 1), 3)},
        {"group": "matched never-adopters", "n": len(matched),
         "urm_level_0915": round(avg(matched, 0), 2), "urm_slope_0915": round(avg(matched, 1), 3)},
    ])
    bal.to_csv(os.path.join(DATA, "matched_balance.csv"), index=False)
    print("=== Balance on 2009-2015 %URM (level and slope) ===")
    print(bal.to_string(index=False))

    # matched CS DiD
    pool = treated + matched
    Gm = {u: (int(adopt[u]) if cohort.get(u) == "pre_covid" else 0) for u in pool}
    wsub = wide.loc[pool]
    att_m = cs_overall(wsub, pd.Series(Gm), pool, years, TREAT_COHORTS)
    se_m = boot(wsub, Gm, pool, years, TREAT_COHORTS)
    print(f"\n[Matched DiD] %URM overall ATT = {att_m:+.3f} pp  SE {se_m:.3f}  "
          f"z={att_m/se_m:+.2f}  (treated {len(treated)}, matched controls {len(matched)})")

    # placebo-in-time: fake adoption 3 years early, controls = never-adopters only,
    # outcome years restricted to before true adoption so the placebo window is clean
    allu = treated + never
    Gp = {u: (int(adopt[u]) - 3 if cohort.get(u) == "pre_covid" else 0) for u in allu}
    placebo_cohorts = sorted(set(Gp[u] for u in treated))
    yrs_pl = [y for y in years if y <= 2015]            # strictly pre-adoption period
    wpl = wide.loc[allu]
    att_p = cs_overall(wpl, pd.Series(Gp), allu, yrs_pl, placebo_cohorts)
    se_p = boot(wpl, Gp, allu, yrs_pl, placebo_cohorts)
    print(f"\n[Placebo-in-time, adoption-3yr, pre-period only] %URM 'ATT' = {att_p:+.3f} pp  "
          f"SE {se_p:.3f}  z={att_p/se_p:+.2f}  (should be ~0 if pre-trends are parallel)")


if __name__ == "__main__":
    main()
