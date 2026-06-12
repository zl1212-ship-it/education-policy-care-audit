"""
Mechanism check for the URM-denominator concern: did test-optional adopters expand
international (nonresident) enrollment, which under an all-students denominator would have diluted
the URM share? Staggered DiD on the nonresident share of the entering class.
"""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
rng = np.random.default_rng(7); B = 500; YEAR_MAX = 2019; COHORTS = [2016, 2017, 2018, 2019]


def cs(adm, outcome):
    d = adm[adm.year <= YEAR_MAX]; wide = d.pivot_table(index="unitid", columns="year", values=outcome)
    allu = list(wide.index); N = len(allu); pos = {u: i for i, u in enumerate(allu)}
    G = np.array([d.groupby("unitid")["G"].first().get(u, 0) for u in allu], float)
    col = {y: j for j, y in enumerate(wide.columns)}; Y = wide.to_numpy(float)
    T, C, TD, CD, post = [], [], [], [], []
    for g in COHORTS:
        if (g - 1) not in col: continue
        jb = col[g - 1]
        for t in sorted(wide.columns):
            if t not in col: continue
            dd = Y[:, col[t]] - Y[:, jb]; v = ~np.isnan(dd)
            tre = ((G == g) & v).astype(float); ctr = (((G == 0) | (G > t)) & (G != g) & v).astype(float)
            f = np.where(v, dd, 0.0); T.append(tre); C.append(ctr); TD.append(tre*f); CD.append(ctr*f); post.append(t >= g)
    Tm, Cm, TDm, CDm = map(np.array, (T, C, TD, CD)); post = np.array(post)
    def agg(W):
        td = Tm@W; cd = Cm@W; fe = (td >= 1) & (cd >= 5)
        with np.errstate(divide="ignore", invalid="ignore"):
            a = (TDm@W)/np.where(td > 0, td, 1) - (CDm@W)/np.where(cd > 0, cd, 1)
        w = np.where(fe & post[:, None], td, 0.0); return np.where(w.sum(0) > 0, (np.where(fe, a, 0.0)*w).sum(0)/w.sum(0), np.nan)
    o = float(agg(np.ones((N, 1)))[0]); au = np.array(allu); Wb = np.empty((N, B))
    for b in range(B):
        s = rng.choice(au, size=N, replace=True); Wb[:, b] = np.bincount([pos[u] for u in s], minlength=N)
    ob = agg(Wb); ob = ob[~np.isnan(ob)]; return o, ob.std(ddof=1)


adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
adm["adoption_year"] = pd.to_numeric(adm["adoption_year"], errors="coerce")
comp = pd.read_csv(os.path.join(DATA, "composition_panel.csv"))
comp["share_nonres"] = comp["share_nonres"] * 100
adm = adm.merge(comp[["unitid", "year", "share_nonres"]], on=["unitid", "year"], how="left")
adm["G"] = adm["adoption_year"].fillna(0).astype(int)
o, se = cs(adm, "share_nonres")
print(f"Nonresident (international) share DiD: ATT {o:+.3f}pp  SE {se:.3f}  z={o/se:+.2f}")
print("(>0 and significant would confirm the dilution mechanism build_composition.py guards against)")
