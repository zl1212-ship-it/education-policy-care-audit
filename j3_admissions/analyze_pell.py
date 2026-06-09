"""
Pell-share (income/SES) outcome: staggered DiD + MDE/equivalence + within-sector + persistence.
Same Callaway-Sant'Anna machinery as reviewer_revisions.py. Answers the reviewers' "hard wound":
test-optional's core equity claim is about low-income students, so the entering-class Pell share
is the most policy-relevant outcome.
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
rng = np.random.default_rng(7); B = 500; YEAR_MAX = 2019; COHORTS = [2016, 2017, 2018, 2019]


def load():
    adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
    adm["adoption_year"] = pd.to_numeric(adm["adoption_year"], errors="coerce")
    adm["control"] = pd.to_numeric(adm["control"], errors="coerce")
    pell = pd.read_csv(os.path.join(DATA, "pell_panel.csv"))
    adm = adm.merge(pell, on=["unitid", "year"], how="left")
    adm["G"] = adm["adoption_year"].fillna(0).astype(int)
    return adm


def cs(adm, outcome, units=None, Goverride=None):
    d = adm if units is None else adm[adm.unitid.isin(units)]
    d = d[d.year <= YEAR_MAX]
    wide = d.pivot_table(index="unitid", columns="year", values=outcome)
    allu = list(wide.index); N = len(allu); pos = {u: i for i, u in enumerate(allu)}
    Gmap = Goverride if Goverride is not None else d.groupby("unitid")["G"].first()
    G = np.array([Gmap.get(u, 0) for u in allu], float)
    col = {y: j for j, y in enumerate(wide.columns)}; Y = wide.to_numpy(float)
    T, C, TD, CD, post = [], [], [], [], []
    for g in COHORTS:
        if (g - 1) not in col:
            continue
        jb = col[g - 1]
        for t in sorted(wide.columns):
            if t not in col:
                continue
            dd = Y[:, col[t]] - Y[:, jb]; v = ~np.isnan(dd)
            tre = ((G == g) & v).astype(float); ctr = (((G == 0) | (G > t)) & (G != g) & v).astype(float)
            f = np.where(v, dd, 0.0)
            T.append(tre); C.append(ctr); TD.append(tre * f); CD.append(ctr * f); post.append(t >= g)
    Tm, Cm, TDm, CDm = map(np.array, (T, C, TD, CD)); post = np.array(post)

    def agg(W):
        tden = Tm @ W; cden = Cm @ W; feas = (tden >= 1) & (cden >= 5)
        with np.errstate(divide="ignore", invalid="ignore"):
            att = (TDm @ W) / np.where(tden > 0, tden, 1) - (CDm @ W) / np.where(cden > 0, cden, 1)
        w = np.where(feas & post[:, None], tden, 0.0); num = (np.where(feas, att, 0.0) * w).sum(0); den = w.sum(0)
        return np.where(den > 0, num / den, np.nan)

    overall = float(agg(np.ones((N, 1)))[0])
    au = np.array(allu); Wb = np.empty((N, B))
    for b in range(B):
        s = rng.choice(au, size=N, replace=True); Wb[:, b] = np.bincount([pos[u] for u in s], minlength=N)
    ob = agg(Wb); ob = ob[~np.isnan(ob)]; se = ob.std(ddof=1)
    ntr = int(sum((G == g).sum() for g in COHORTS))
    return overall, se, ntr


def main():
    adm = load()
    z975, z80, z95 = 1.95996, 0.84162, 1.64485
    o, se, ntr = cs(adm, "pell_share")
    mde = (z975 + z80) * se; equiv = abs(o) + z95 * se
    print(f"=== Pell share (entering FTFT) — staggered DiD ===")
    print(f"  ATT {o:+.3f} pp  SE {se:.3f}  z={o/se:+.2f}  (n_treated={ntr})")
    print(f"  MDE(80%) {mde:.2f}pp | equivalent to 0 within +/-{equiv:.2f}pp")
    print("  within-sector:")
    for cval, lab in [(1, "public"), (2, "private-nonprofit")]:
        units = set(adm.loc[adm.control == cval, "unitid"])
        os_, ses_, n_ = cs(adm, "pell_share", units=units)
        print(f"    {lab:17s} ATT {os_:+.3f} SE {ses_:.3f} z={os_/ses_:+.2f} (n_tr={n_})")
    # persistence >=2yr (reuse derived G from admissions reqt)
    rq = pd.read_csv(os.path.join(DATA, "admissions_panel.csv"))
    rq["reqt"] = pd.to_numeric(rq["reqt_test_scores"], errors="coerce")
    byinst = {u: g.set_index("year")["reqt"].to_dict() for u, g in rq.groupby("unitid")}
    Gp = {}
    for u, yc in byinst.items():
        seen = False; adopt = 0
        for y in sorted(yc):
            c = yc[y]
            if c in (1, 2): seen = True
            if c == 3 and seen and adopt == 0 and yc.get(y + 1) == 3: adopt = y
        Gp[u] = adopt if (adopt and adopt <= 2019) else 0
    op, sep, np_ = cs(adm, "pell_share", Goverride=pd.Series(Gp))
    print(f"  persistence>=2yr: ATT {op:+.3f} SE {sep:.3f} z={op/sep:+.2f} (n_tr={np_})")
    pd.DataFrame([{"outcome": "pell_share", "att": round(o, 4), "se": round(se, 4),
                   "mde80": round(mde, 3), "equiv_margin": round(equiv, 3), "n_treated": ntr}]
                 ).to_csv(os.path.join(DATA, "pell_did.csv"), index=False)
    print("wrote data/pell_did.csv")


if __name__ == "__main__":
    main()
