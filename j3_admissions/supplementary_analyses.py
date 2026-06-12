"""
Supplementary analyses backing the headline results:
  (2) MDE + equivalence (TOST) for every outcome -- distinguish informative null from underpowered.
  (3) Covariate concern: re-estimate the staggered DiD WITHIN sector (controls drawn only from the
      treated unit's own control type), since adoption is strongly selected on sector.
  (T) TWFE benchmark actually computed (two-way within estimator), to back the "benchmark" claim.
  (R) Treatment-persistence robustness: require reqt_test_scores == 3 to persist >= 2 years.
  (D) Baseline descriptive statistics, treated (pre-COVID adopters) vs never-adopters.

All reuse the same Callaway-Sant'Anna cell/agg machinery as analyze_did.py.
Outputs printed and written to data/suppl_*.csv.
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
rng = np.random.default_rng(7)
B = 500
YEAR_MAX = 2019
COHORTS = [2016, 2017, 2018, 2019]
COMP = ["share_urm", "share_black", "share_hisp"]


def load():
    adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
    adm["adoption_year"] = pd.to_numeric(adm["adoption_year"], errors="coerce")
    for c in ["admit_rate", "yield_rate", "sat_pct_submit", "control", "enrolled", "sat_total_75"]:
        adm[c] = pd.to_numeric(adm[c], errors="coerce")
    adm["admit_rate"] *= 100; adm["yield_rate"] *= 100
    comp = pd.read_csv(os.path.join(DATA, "composition_panel.csv"))
    for c in COMP:
        comp[c] = comp[c] * 100
    adm = adm.merge(comp[["unitid", "year"] + COMP], on=["unitid", "year"], how="left")
    adm["G"] = adm["adoption_year"].fillna(0).astype(int)
    return adm


def cs(adm, outcome, units=None, Goverride=None):
    """Vectorized C&S overall ATT + clustered-bootstrap SE on a (sub)sample."""
    d = adm if units is None else adm[adm.unitid.isin(units)]
    d = d[d.year <= YEAR_MAX]
    wide = d.pivot_table(index="unitid", columns="year", values=outcome)
    allu = list(wide.index); N = len(allu); pos = {u: i for i, u in enumerate(allu)}
    Gmap = (Goverride if Goverride is not None else d.groupby("unitid")["G"].first())
    G = np.array([Gmap.get(u, 0) for u in allu], float)
    col = {y: j for j, y in enumerate(wide.columns)}; Y = wide.to_numpy(float)
    T, C, TD, CD, post = [], [], [], [], []
    yrs = sorted(wide.columns)
    for g in COHORTS:
        if (g - 1) not in col:
            continue
        jb = col[g - 1]
        for t in yrs:
            if t not in col:
                continue
            dd = Y[:, col[t]] - Y[:, jb]; v = ~np.isnan(dd)
            tre = ((G == g) & v).astype(float)
            ctr = (((G == 0) | (G > t)) & (G != g) & v).astype(float)
            f = np.where(v, dd, 0.0)
            T.append(tre); C.append(ctr); TD.append(tre * f); CD.append(ctr * f); post.append(t >= g)
    Tm, Cm, TDm, CDm = map(np.array, (T, C, TD, CD)); post = np.array(post)

    def agg(W):
        tden = Tm @ W; cden = Cm @ W; feas = (tden >= 1) & (cden >= 5)
        with np.errstate(divide="ignore", invalid="ignore"):
            att = (TDm @ W) / np.where(tden > 0, tden, 1) - (CDm @ W) / np.where(cden > 0, cden, 1)
        w = np.where(feas & post[:, None], tden, 0.0)
        num = (np.where(feas, att, 0.0) * w).sum(0); den = w.sum(0)
        return np.where(den > 0, num / den, np.nan)

    overall = float(agg(np.ones((N, 1)))[0])
    Wb = np.empty((N, B))
    au = np.array(allu)
    for b in range(B):
        s = rng.choice(au, size=N, replace=True)
        Wb[:, b] = np.bincount([pos[u] for u in s], minlength=N)
    ob = agg(Wb); ob = ob[~np.isnan(ob)]
    se = ob.std(ddof=1)
    ntr = int(sum((G == g).sum() for g in COHORTS))
    return overall, se, ntr


def twfe(adm, outcome):
    """Two-way fixed-effects benchmark via double demeaning; cluster-by-institution SE."""
    d = adm[adm.year <= YEAR_MAX][["unitid", "year", outcome, "G"]].dropna(subset=[outcome]).copy()
    d["D"] = ((d.G != 0) & (d.G <= YEAR_MAX) & (d.year >= d.G)).astype(float)
    for v in [outcome, "D"]:
        d[v + "_d"] = (d[v] - d.groupby("unitid")[v].transform("mean")
                       - d.groupby("year")[v].transform("mean") + d[v].mean())
    x = d["D_d"].to_numpy(); y = d[outcome + "_d"].to_numpy()
    beta = (x @ y) / (x @ x)
    d["resid"] = y - beta * x
    # cluster-robust (by institution) SE
    sxx = x @ x
    meat = 0.0
    for _, g in d.groupby("unitid"):
        xi = g["D_d"].to_numpy(); ui = g["resid"].to_numpy()
        meat += (xi @ ui) ** 2
    se = np.sqrt(meat) / sxx
    return beta, se


def main():
    adm = load()
    never = set(adm.loc[adm.G == 0, "unitid"])

    # ---------- (2) MDE + equivalence from the main DiD SEs ----------
    res = pd.read_csv(os.path.join(DATA, "did_results.csv")).set_index("outcome")
    z975, z80, z95 = 1.95996, 0.84162, 1.64485
    print("=== (2) MDE (80% power) + equivalence (TOST) ===")
    rows = []
    for oc in res.index:
        att, se = res.loc[oc, "att"], res.loc[oc, "se"]
        mde = (z975 + z80) * se
        tost90_hi = abs(att) + z95 * se          # 90% CI outer bound; equivalence margin it clears
        rows.append({"outcome": oc, "att": att, "se": se, "mde80": round(mde, 3),
                     "equiv_margin_pp": round(tost90_hi, 3),
                     "equiv_at_2pp": "yes" if tost90_hi < 2 else "no"})
        print(f"  {oc:16s} ATT {att:+.2f} SE {se:.2f} | MDE(80%)={mde:.2f}pp | "
              f"equivalent to 0 within +/-{tost90_hi:.2f}pp | <=2pp equiv: {'YES' if tost90_hi<2 else 'no'}")
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "suppl_mde_tost.csv"), index=False)

    # ---------- (3) within-sector CS for composition ----------
    print("\n=== (3) Within-sector staggered DiD (controls same sector as treated) ===")
    sect = {1: "public", 2: "private-nonprofit"}
    out = []
    for oc in COMP:
        for cval, lab in sect.items():
            units = set(adm.loc[adm.control == cval, "unitid"])
            o, se, ntr = cs(adm, oc, units=units)
            z = o / se if se else np.nan
            out.append({"outcome": oc, "sector": lab, "att": round(o, 3), "se": round(se, 3),
                        "z": round(z, 2), "n_treated": ntr})
            print(f"  {oc:14s} [{lab:17s}] ATT {o:+.3f} SE {se:.3f} z={z:+.2f} (n_tr={ntr})")
    pd.DataFrame(out).to_csv(os.path.join(DATA, "suppl_within_sector.csv"), index=False)

    # ---------- (T) TWFE benchmark ----------
    print("\n=== (T) TWFE benchmark (biased under staggering; contrast with C&S) ===")
    tw = []
    for oc in ["admit_rate", "yield_rate", "sat_pct_submit"] + COMP:
        b, se = twfe(adm, oc)
        tw.append({"outcome": oc, "twfe_att": round(b, 3), "se": round(se, 3),
                   "z": round(b / se, 2)})
        print(f"  {oc:16s} TWFE {b:+.3f} SE {se:.3f} z={b/se:+.2f}")
    pd.DataFrame(tw).to_csv(os.path.join(DATA, "suppl_twfe.csv"), index=False)

    # ---------- (R) persistence >= 2 years ----------
    print("\n=== (R) Treatment-persistence robustness (reqt==3 must persist >=2 yrs) ===")
    rq = pd.read_csv(os.path.join(DATA, "admissions_panel.csv"))
    rq["reqt"] = pd.to_numeric(rq["reqt_test_scores"], errors="coerce")
    byinst = {u: g.set_index("year")["reqt"].to_dict() for u, g in rq.groupby("unitid")}
    Gp = {}
    for u, yc in byinst.items():
        ys = sorted(yc); seen = False; adopt = 0
        for y in ys:
            c = yc[y]
            if c in (1, 2):
                seen = True
            if c == 3 and seen and adopt == 0 and yc.get(y + 1) == 3:   # persists into next year
                adopt = y
        Gp[u] = adopt if (adopt and adopt <= 2019) else 0
    Gp = pd.Series(Gp)
    n_pre = sum(1 for u in Gp.index if Gp[u] in COHORTS)
    print(f"  persistent pre-COVID adopters: {n_pre} (vs 237 in main)")
    for oc in COMP:
        o, se, ntr = cs(adm, oc, Goverride=Gp)
        print(f"  {oc:14s} ATT {o:+.3f} SE {se:.3f} z={o/se:+.2f} (n_tr={ntr})")

    # ---------- (D) baseline descriptives ----------
    print("\n=== (D) Baseline descriptives (2015), treated pre-COVID vs never ===")
    base = adm[adm.year == 2015].copy()
    tr_ids = set(adm.loc[adm.G.isin(COHORTS), "unitid"])
    base["grp"] = base.unitid.map(lambda u: "treated" if u in tr_ids else ("never" if u in never else "other"))
    desc = []
    for grp in ["treated", "never"]:
        b = base[base.grp == grp]
        desc.append({"group": grp, "n": len(b),
                     "admit_rate": round(b.admit_rate.mean(), 1),
                     "sat75": round(b.sat_total_75.mean(), 0),
                     "enrolled": round(b.enrolled.mean(), 0),
                     "pct_private": round(100 * (b.control == 2).mean(), 0),
                     "share_urm": round(b.share_urm.mean(), 1)})
    dd = pd.DataFrame(desc); print(dd.to_string(index=False))
    dd.to_csv(os.path.join(DATA, "suppl_descriptives.csv"), index=False)
    print("\nwrote data/suppl_*.csv")


if __name__ == "__main__":
    main()
