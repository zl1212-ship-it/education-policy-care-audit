"""
Revision items 4 and 5.
(4) Heterogeneity: report group-level ATT (URM and Pell) by selectivity tier (baseline admit rate)
    and by baseline minority-enrollment tier (a minority-serving proxy; IPEDS exposes no formal MSI
    flag beyond HBCU/tribal, which almost no adopter is). Treated subgroup vs the full not-yet/never
    control pool. Answers "does the pooled null average over offsetting heterogeneity?"
(5) URM definition sensitivity: recompute URM excluding "two or more races" (race code 7) and
    re-estimate the DiD, since the two-or-more category is a contested component of URM.
Same Callaway-Sant'Anna machinery as the other scripts.
"""
import os, urllib.request, json, time, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
rng = np.random.default_rng(7); B = 400; YEAR_MAX = 2019; COHORTS = [2016, 2017, 2018, 2019]


def pull(path):
    url = f"{BASE}/{path}"; out = []
    while url:
        for a in range(6):
            try:
                with urllib.request.urlopen(url, timeout=180) as r:
                    d = json.load(r)
                break
            except Exception:
                if a == 5: raise
                time.sleep(3 * (a + 1))
        out += d["results"]; url = d.get("next")
    return out


def load():
    adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
    adm["adoption_year"] = pd.to_numeric(adm["adoption_year"], errors="coerce")
    adm["control"] = pd.to_numeric(adm["control"], errors="coerce")
    adm["admit_rate"] = pd.to_numeric(adm["admit_rate"], errors="coerce") * 100
    comp = pd.read_csv(os.path.join(DATA, "composition_panel.csv"))
    comp["share_urm"] = comp["share_urm"] * 100
    pell = pd.read_csv(os.path.join(DATA, "pell_panel.csv"))
    adm = adm.merge(comp[["unitid", "year", "share_urm", "entering_total", "domestic_total"]], on=["unitid", "year"], how="left")
    adm = adm.merge(pell, on=["unitid", "year"], how="left")
    adm["G"] = adm["adoption_year"].fillna(0).astype(int)
    return adm


def add_urm_excl(adm):
    """share_urm minus the two-or-more (race=7) share, both in percent of entering class."""
    s7 = {}
    for y in range(2009, 2020):
        recs = pull(f"fall-enrollment/{y}/1/race/sex/?class_level=1&degree_seeking=1&ftpt=99&sex=99&race=7&per_page=20000")
        for x in recs:
            if x.get("race") == 7:
                s7[(x["unitid"], y)] = x.get("enrollment_fall") or 0
    adm["n7"] = adm.apply(lambda r: s7.get((r["unitid"], r["year"]), np.nan), axis=1)
    # share_urm now uses the domestic denominator, so the two-or-more share must too
    adm["share7"] = np.where(adm["domestic_total"] > 0, 100 * adm["n7"] / adm["domestic_total"], np.nan)
    adm["urm_excl"] = adm["share_urm"] - adm["share7"]
    return adm


def cs(adm, outcome, treated_set=None, Goverride=None):
    d = adm[adm.year <= YEAR_MAX]
    wide = d.pivot_table(index="unitid", columns="year", values=outcome)
    allu = list(wide.index); N = len(allu); pos = {u: i for i, u in enumerate(allu)}
    Gmap = Goverride if Goverride is not None else d.groupby("unitid")["G"].first()
    G = np.array([Gmap.get(u, 0) for u in allu], float)
    inT = np.array([1.0 if (treated_set is None or u in treated_set) else 0.0 for u in allu])
    col = {y: j for j, y in enumerate(wide.columns)}; Y = wide.to_numpy(float)
    T, C, TD, CD, post = [], [], [], [], []
    for g in COHORTS:
        if (g - 1) not in col: continue
        jb = col[g - 1]
        for t in sorted(wide.columns):
            if t not in col: continue
            dd = Y[:, col[t]] - Y[:, jb]; v = ~np.isnan(dd)
            tre = ((G == g) & (inT == 1) & v).astype(float)
            ctr = (((G == 0) | (G > t)) & (G != g) & v).astype(float)   # full control pool
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
    ntr = int(sum(((G == g) & (inT == 1)).sum() for g in COHORTS))
    return overall, se, ntr


def main():
    adm = load()
    base = adm[adm.year == 2015]
    treated = set(adm.loc[adm.G.isin(COHORTS), "unitid"])
    admit15 = base.set_index("unitid")["admit_rate"]; urm15 = base.set_index("unitid")["share_urm"]
    tr_admit = admit15[admit15.index.isin(treated)].dropna(); tr_urm = urm15[urm15.index.isin(treated)].dropna()
    med_a, med_u = tr_admit.median(), tr_urm.median()
    grp = {
        "more-selective (admit<med)": set(tr_admit[tr_admit < med_a].index),
        "less-selective (admit>=med)": set(tr_admit[tr_admit >= med_a].index),
        "higher-minority (URM>=med)": set(tr_urm[tr_urm >= med_u].index),
        "lower-minority (URM<med)": set(tr_urm[tr_urm < med_u].index),
    }
    print(f"=== (4) Heterogeneity (treated subgroup vs full control pool) ===")
    print(f"  selectivity split at admit={med_a:.0f}%, minority split at URM={med_u:.0f}%")
    rows = []
    for oc in ["share_urm", "pell_share"]:
        for lab, st in grp.items():
            o, se, n = cs(adm, oc, treated_set=st)
            z = o / se if se else np.nan
            print(f"  {oc:11s} [{lab:28s}] ATT {o:+.2f} SE {se:.2f} z={z:+.2f} (n_tr={n})")
            rows.append({"outcome": oc, "group": lab, "att": round(o, 3), "se": round(se, 3), "z": round(z, 2), "n": n})
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "revision_heterogeneity.csv"), index=False)

    print("\n=== (5) URM excluding two-or-more races ===")
    adm = add_urm_excl(adm)
    o, se, n = cs(adm, "urm_excl")
    print(f"  URM (excl. two-or-more) ATT {o:+.3f} SE {se:.3f} z={o/se:+.2f} (n_tr={n})")
    print(f"  (main URM incl. two-or-more was +0.55, SE 0.41)")
    pd.DataFrame([{"outcome": "urm_excl_twomore", "att": round(o, 4), "se": round(se, 4), "z": round(o/se, 2), "n": n}]
                 ).to_csv(os.path.join(DATA, "revision_urm_excl.csv"), index=False)
    print("\nwrote data/revision_heterogeneity.csv and revision_urm_excl.csv")


if __name__ == "__main__":
    main()
