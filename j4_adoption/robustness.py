"""
J4 robustness: (1) Sun & Abraham (2021) interaction-weighted event study on the matched
sample, as a heterogeneity-robust check on Callaway-Sant'Anna; (2) heterogeneity by %Pell.
Matching (treated 2018/19 -> 5 nearest never-treated on 2011-17 retention level+slope) is
recomputed here, identical to match_did.py.
"""
import os, urllib.request, json, numpy as np, pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
PREW = list(range(2011, 2018)); K = 5; B = 400; rng = np.random.default_rng(7)

df = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
df.loc[df.adoption_year > 2020, "adoption_year"] = np.nan
G = df.groupby("unitid")["adoption_year"].first().fillna(0).astype(int)
wide = df.pivot_table(index="unitid", columns="year", values="retention_rate")
years = sorted(df.year.unique())

# ---- recompute matched sample ----
treated = [u for u in wide.index if G[u] in (2018, 2019)]
ctrl_cand = [u for u in wide.index if G[u] == 0]
def lvslope(u):
    ys = [y for y in PREW if y in wide.columns and pd.notna(wide.loc[u, y])]
    if len(ys) < 4: return None
    v = [wide.loc[u, y] for y in ys]
    return np.mean(v), np.polyfit(ys, v, 1)[0]
feat = {u: lvslope(u) for u in treated + ctrl_cand}; feat = {u: f for u, f in feat.items() if f}
treated = [u for u in treated if u in feat]; ctrl_cand = [u for u in ctrl_cand if u in feat]
L = np.array(list(feat.values())); mu, sd = L.mean(0), L.std(0)
z = {u: (np.array(feat[u]) - mu) / sd for u in feat}
matched = set()
for t in treated:
    matched.update(sorted(ctrl_cand, key=lambda c: np.sum((z[t] - z[c]) ** 2))[:K])
matched = sorted(matched)
sample = treated + matched
Gm = {u: (G[u] if G[u] in (2018, 2019) else 0) for u in sample}
print(f"matched sample: {len(treated)} treated + {len(matched)} controls")

# ================= (1) Sun-Abraham IW event study =================
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
    # IW aggregation: per event time e, weight cohort coef by cohort size share
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
# cluster bootstrap
bs = []
for _ in range(B):
    s = rng.choice(sample, len(sample), replace=True)
    Wb = wide.loc[s].reset_index(drop=True)
    Gb = {i: Gm[u] for i, u in enumerate(s)}
    try:
        a, _ = sa_estimate(list(range(len(s))), Gb, Wb)
        if not np.isnan(a): bs.append(a)
    except Exception:
        pass
bs = np.array(bs)
print(f"\n=== Sun-Abraham overall post ATT === {sa_att*100:+.2f} pp  "
      f"SE {bs.std(ddof=1)*100:.2f}  95% CI [{np.percentile(bs,2.5)*100:+.2f},{np.percentile(bs,97.5)*100:+.2f}]")
print("SA event study (ref t-1):")
for e in sorted(sa_es):
    print(f"  t{e:+d} [{'pre ' if e<0 else 'post'}]: {sa_es[e]*100:+6.2f} pp")

# ================= (2) %Pell heterogeneity =================
# CAVEAT: the SFA-derived Pell share below is unreliable (Pell-recipient numerator and
# FTFT retention-cohort denominator cover different populations, inflating the level:
# observed median ~0.68 is implausibly high). It is NOT used in the paper; %URM is the
# trustworthy composition split. Retained only to document the attempt.
pell_path = os.path.join(DATA, "pell_share.csv")
if not os.path.exists(pell_path):
    url = ("https://educationdata.urban.org/api/v1/college-university/ipeds/"
           "sfa-grants-and-net-price/2016/?type_of_aid=3&income_level=99")
    rows = []
    while url:
        with urllib.request.urlopen(url, timeout=120) as r: d = json.load(r)
        rows += d["results"]; url = d.get("next")
    pell_n = {x["unitid"]: x.get("number_of_students") for x in rows if x.get("number_of_students")}
    # denominator = FTFT cohort from retention file (prev_cohort), 2016
    coh = {}
    u2 = ("https://educationdata.urban.org/api/v1/college-university/ipeds/"
          "fall-retention/2016/?ftpt=1")
    while u2:
        with urllib.request.urlopen(u2, timeout=120) as r: d = json.load(r)
        for x in d["results"]:
            if x["ftpt"] == 1 and x.get("prev_cohort"): coh[x["unitid"]] = x["prev_cohort"]
        u2 = d.get("next")
    out = [(u, pell_n[u] / coh[u]) for u in pell_n if u in coh and coh[u] > 0]
    pd.DataFrame(out, columns=["unitid", "pell_share"]).to_csv(pell_path, index=False)
pell = pd.read_csv(pell_path).set_index("unitid")["pell_share"]
ps = pell[(pell >= 0) & (pell <= 1)]
print(f"\n%Pell sanity: n={len(ps)} median={ps.median():.2f} "
      f"p10={ps.quantile(.1):.2f} p90={ps.quantile(.9):.2f} (expect ~0.1-0.8)")

# matched-CS aggregate by Pell split (reuse simple CS on matched sample)
def att_sub(g, t, tr, allu, Gv, W):
    base = g - 1
    if base not in W.columns or t not in W.columns: return None
    yb, yt = W[base], W[t]
    a = [u for u in tr if pd.notna(yb[u]) and pd.notna(yt[u])]
    c = [u for u in allu if Gv[u] == 0 and pd.notna(yb[u]) and pd.notna(yt[u])]
    if len(a) < 1 or len(c) < 5: return None
    return (yt[a] - yb[a]).mean() - (yt[c] - yb[c]).mean(), len(a)
def agg(allu, Gv, W, trf):
    post = []
    for g in (2018, 2019):
        gu = [u for u in trf if Gv[u] == g]
        for t in years:
            if t < g: continue
            r = att_sub(g, t, gu, allu, Gv, W)
            if r: post.append(r)
    return float(np.average([p[0] for p in post], weights=[p[1] for p in post])) if post else np.nan
def boot_grp(grp):
    out = []
    for _ in range(B):
        s = rng.choice(sample, len(sample), replace=True)
        Wb = wide.loc[s].reset_index(drop=True); Gb = {i: Gm[u] for i, u in enumerate(s)}
        keep = set(grp); tf = [i for i, u in enumerate(s) if u in keep]
        a = agg(list(range(len(s))), Gb, Wb, tf)
        if not np.isnan(a): out.append(a)
    return np.std(out, ddof=1)

tre_p = [u for u in treated if u in ps.index]
medp = np.median([ps[u] for u in tre_p])
for lab, grp in [("HIGH %Pell treated", [u for u in tre_p if ps[u] > medp]),
                 ("LOW %Pell treated", [u for u in tre_p if ps[u] <= medp])]:
    o = agg(sample, Gm, wide.loc[sample], grp)
    print(f"[Heterogeneity %Pell] {lab}: ATT {o*100:+.2f} pp (SE {boot_grp(grp)*100:.2f}) n={len(grp)}")
