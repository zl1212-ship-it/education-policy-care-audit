"""
Editor revision #5: own-robustness for the one positive coefficient that survives multiple-comparison
correction, the Pell share at less-selective institutions (+1.75, z=3.0 in Table het). Reports that
subgroup's event study (pre-adoption trend) and its persistence-restricted estimate, so the
"carries the same pre-trend caveat" claim is backed rather than asserted. Treated subgroup
(less-selective adopters) vs the full not-yet/never control pool, same C&S machinery. Writes
data/pell_subgroup.csv.
"""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
rng = np.random.default_rng(7); B = 500; YEAR_MAX = 2019; COHORTS = [2016, 2017, 2018, 2019]


def cells(adm, outcome, treated_set, Goverride=None):
    d = adm[adm.year <= YEAR_MAX]
    wide = d.pivot_table(index="unitid", columns="year", values=outcome)
    allu = list(wide.index); N = len(allu); pos = {u: i for i, u in enumerate(allu)}
    Gmap = Goverride if Goverride is not None else d.groupby("unitid")["G"].first()
    G = np.array([Gmap.get(u, 0) for u in allu], float)
    inT = np.array([1.0 if u in treated_set else 0.0 for u in allu])
    col = {y: j for j, y in enumerate(wide.columns)}; Y = wide.to_numpy(float)
    T, C, TD, CD, post, evt = [], [], [], [], [], []
    for g in COHORTS:
        if (g - 1) not in col: continue
        jb = col[g - 1]
        for t in sorted(wide.columns):
            if t not in col: continue
            dd = Y[:, col[t]] - Y[:, jb]; v = ~np.isnan(dd)
            tre = ((G == g) & (inT == 1) & v).astype(float)
            ctr = (((G == 0) | (G > t)) & (G != g) & v).astype(float)
            f = np.where(v, dd, 0.0)
            T.append(tre); C.append(ctr); TD.append(tre * f); CD.append(ctr * f); post.append(t >= g); evt.append(t - g)
    return (list(map(np.array, (T, C, TD, CD))), np.array(post), np.array(evt), allu, N, pos, G, inT)


def estimate(adm, outcome, treated_set, Goverride=None):
    (Tm, Cm, TDm, CDm), post, evt, allu, N, pos, G, inT = cells(adm, outcome, treated_set, Goverride)

    def agg(W, mask):
        td = Tm @ W; cd = Cm @ W; fe = (td >= 1) & (cd >= 5)
        with np.errstate(divide="ignore", invalid="ignore"):
            a = (TDm @ W) / np.where(td > 0, td, 1) - (CDm @ W) / np.where(cd > 0, cd, 1)
        w = np.where(fe & mask[:, None], td, 0.0); num = (np.where(fe, a, 0.0) * w).sum(0); den = w.sum(0)
        return np.where(den > 0, num / den, np.nan)

    overall = float(agg(np.ones((N, 1)), post)[0])
    au = np.array(allu); Wb = np.empty((N, B))
    for b in range(B):
        s = rng.choice(au, size=N, replace=True); Wb[:, b] = np.bincount([pos[u] for u in s], minlength=N)
    ob = agg(Wb, post); ob = ob[~np.isnan(ob)]; se = ob.std(ddof=1)
    one = np.ones((N, 1)); es = {}
    for e in sorted(set(evt.tolist())):
        val = agg(one, evt == e)
        if not np.isnan(val[0]): es[e] = float(val[0])
    ntr = int(sum(((G == g) & (inT == 1)).sum() for g in COHORTS))
    return overall, se, ntr, es


def main():
    adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
    adm["adoption_year"] = pd.to_numeric(adm["adoption_year"], errors="coerce")
    adm["admit_rate"] = pd.to_numeric(adm["admit_rate"], errors="coerce") * 100
    pell = pd.read_csv(os.path.join(DATA, "pell_panel.csv"))
    adm = adm.merge(pell, on=["unitid", "year"], how="left")
    adm["G"] = adm["adoption_year"].fillna(0).astype(int)

    treated = set(adm.loc[adm.G.isin(COHORTS), "unitid"])
    a15 = adm[adm.year == 2015].set_index("unitid")["admit_rate"]
    med = a15[a15.index.isin(treated)].dropna().median()
    less_sel = set(a15[(a15 >= med) & (a15.index.isin(treated))].index)

    o, se, n, es = estimate(adm, "pell_share", less_sel)
    print(f"less-selective Pell ATT {o:+.3f} (SE {se:.3f}, z={o/se:+.2f}, n_tr={n}) [reproduces Table het]")
    pre = {e: round(es[e], 2) for e in sorted(es) if e < 0}
    print(f"  event study pre-adoption: {pre}")
    print(f"  event study post: {{e: round(es[e],2) for e>=0}} -> {{ {', '.join(f'{e}:{es[e]:.2f}' for e in sorted(es) if e>=0)} }}")

    # persistence >=2yr for this subgroup
    rq = pd.read_csv(os.path.join(DATA, "admissions_panel.csv")); rq["reqt"] = pd.to_numeric(rq["reqt_test_scores"], errors="coerce")
    Gp = {}
    for u, gdf in rq.groupby("unitid"):
        yc = gdf.set_index("year")["reqt"].to_dict(); seen = False; ad = 0
        for y in sorted(yc):
            if yc[y] in (1, 2): seen = True
            if yc[y] == 3 and seen and ad == 0 and yc.get(y + 1) == 3: ad = y
        Gp[u] = ad if (ad and ad <= 2019) else 0
    op, sep, np_, _ = estimate(adm, "pell_share", less_sel, Goverride=pd.Series(Gp))
    print(f"  persistence>=2yr: ATT {op:+.3f} (SE {sep:.3f}, z={op/sep:+.2f}, n_tr={np_})")

    pd.DataFrame([
        {"spec": "less_sel_pell", "att": round(o, 3), "se": round(se, 3), "z": round(o / se, 2), "n": n},
        {"spec": "less_sel_pell_persist2yr", "att": round(op, 3), "se": round(sep, 3), "z": round(op / sep, 2), "n": np_},
    ]).to_csv(os.path.join(DATA, "pell_subgroup.csv"), index=False)
    pd.DataFrame([{"event_time": e, "coef": round(es[e], 3)} for e in sorted(es)]).to_csv(
        os.path.join(DATA, "pell_subgroup_event.csv"), index=False)
    print("wrote data/pell_subgroup.csv and pell_subgroup_event.csv")


if __name__ == "__main__":
    main()
