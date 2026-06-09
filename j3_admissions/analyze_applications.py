"""
Revision item 2: does test-optional raise application volume (and reported selectivity)?
This turns the "legitimacy by metric / benefits institutions, not students" claim from rhetoric
into a tested DiD. Outcome: 100*ln(applicants), so the ATT reads as an approximate percent change;
admit rate (reported selectivity) is already in Table 1. Same C&S machinery as analyze_pell.py.
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
rng = np.random.default_rng(7); B = 500; YEAR_MAX = 2019; COHORTS = [2016, 2017, 2018, 2019]


def load():
    adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
    adm["adoption_year"] = pd.to_numeric(adm["adoption_year"], errors="coerce")
    adm["control"] = pd.to_numeric(adm["control"], errors="coerce")
    adm["applied"] = pd.to_numeric(adm["applied"], errors="coerce")
    adm["enrolled"] = pd.to_numeric(adm["enrolled"], errors="coerce")
    adm["ln_applied"] = np.where(adm["applied"] > 0, 100 * np.log(adm["applied"]), np.nan)
    adm["ln_enrolled"] = np.where(adm["enrolled"] > 0, 100 * np.log(adm["enrolled"]), np.nan)
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
    T, C, TD, CD, post, es_e = [], [], [], [], [], []
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
            T.append(tre); C.append(ctr); TD.append(tre * f); CD.append(ctr * f); post.append(t >= g); es_e.append(t - g)
    Tm, Cm, TDm, CDm = map(np.array, (T, C, TD, CD)); post = np.array(post); es_e = np.array(es_e)

    def agg(W, mask):
        tden = Tm @ W; cden = Cm @ W; feas = (tden >= 1) & (cden >= 5)
        with np.errstate(divide="ignore", invalid="ignore"):
            att = (TDm @ W) / np.where(tden > 0, tden, 1) - (CDm @ W) / np.where(cden > 0, cden, 1)
        w = np.where(feas & mask[:, None], tden, 0.0); num = (np.where(feas, att, 0.0) * w).sum(0); den = w.sum(0)
        return np.where(den > 0, num / den, np.nan)

    overall = float(agg(np.ones((N, 1)), post)[0])
    au = np.array(allu); Wb = np.empty((N, B))
    for b in range(B):
        s = rng.choice(au, size=N, replace=True); Wb[:, b] = np.bincount([pos[u] for u in s], minlength=N)
    ob = agg(Wb, post); ob = ob[~np.isnan(ob)]; se = ob.std(ddof=1)
    # event study (point)
    es = {}
    one = np.ones((N, 1))
    for e in sorted(set(es_e.tolist())):
        v = agg(one, es_e == e)
        if not np.isnan(v[0]):
            es[e] = float(v[0])
    ntr = int(sum((G == g).sum() for g in COHORTS))
    return overall, se, ntr, es


def main():
    adm = load()
    z975, z80 = 1.95996, 0.84162
    for oc, lab in [("ln_applied", "log applications (x100 ~ %)"), ("ln_enrolled", "log enrollment")]:
        o, se, ntr, es = cs(adm, oc)
        print(f"\n=== {lab} ===")
        print(f"  ATT {o:+.2f}  SE {se:.2f}  z={o/se:+.2f}  (n_treated={ntr})  MDE80={ (z975+z80)*se:.2f}")
        print("  event study:", {e: round(es[e], 1) for e in sorted(es)})
        if oc == "ln_applied":
            arch = [{"spec": "overall", "att": round(o, 3), "se": round(se, 3), "z": round(o / se, 2), "n_treated": ntr}]
            for cval, l in [(1, "public"), (2, "private")]:
                u = set(adm.loc[adm.control == cval, "unitid"])
                oa, sea, na, _ = cs(adm, oc, units=u)
                print(f"  within {l:8s}: ATT {oa:+.2f} SE {sea:.2f} z={oa/sea:+.2f} (n_tr={na})")
                arch.append({"spec": f"within_{l}", "att": round(oa, 3), "se": round(sea, 3), "z": round(oa / sea, 2), "n_treated": na})
            # persistence
            rq = pd.read_csv(os.path.join(DATA, "admissions_panel.csv")); rq["reqt"] = pd.to_numeric(rq["reqt_test_scores"], errors="coerce")
            byinst = {uu: g.set_index("year")["reqt"].to_dict() for uu, g in rq.groupby("unitid")}
            Gp = {}
            for uu, yc in byinst.items():
                seen = False; ad = 0
                for y in sorted(yc):
                    if yc[y] in (1, 2): seen = True
                    if yc[y] == 3 and seen and ad == 0 and yc.get(y + 1) == 3: ad = y
                Gp[uu] = ad if (ad and ad <= 2019) else 0
            op, sep, npr, _ = cs(adm, oc, Goverride=pd.Series(Gp))
            print(f"  persistence>=2yr: ATT {op:+.2f} SE {sep:.2f} z={op/sep:+.2f} (n_tr={npr})")
            arch.append({"spec": "persist2yr", "att": round(op, 3), "se": round(sep, 3), "z": round(op / sep, 2), "n_treated": npr})
            pd.DataFrame(arch).to_csv(os.path.join(DATA, "applications_did.csv"), index=False)
    print("\nwrote data/applications_did.csv")


if __name__ == "__main__":
    main()
