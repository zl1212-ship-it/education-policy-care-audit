"""
J4 matched-control robustness. Threat: treated systems had rising retention BEFORE
adopting (positive pre-trends). Fix: match each treated institution to never-treated
controls with similar pre-adoption retention LEVEL and SLOPE (2011-2017), then re-run
Callaway-Sant'Anna on the matched sample and check whether pre-trends flatten and the
higher-need effect survives.

Scope: cohorts 2018 + 2019 only (the identifying core); early adopters GSU 2012 and
UW-Milwaukee 2013 dropped (2 noisy units). 2020 (COVID) dropped in a robustness pass.
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
PREW = list(range(2011, 2018))     # pre-window for matching: 2011-2017
K = 5                              # nearest never-treated neighbours per treated
rng = np.random.default_rng(7); B = 400

df = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
df.loc[df.adoption_year > 2020, "adoption_year"] = np.nan
G = df.groupby("unitid")["adoption_year"].first().fillna(0).astype(int)
wide = df.pivot_table(index="unitid", columns="year", values="retention_rate")

# drop early adopters; treated = 2018/2019 cohorts; control candidates = never-treated
treated = [u for u in wide.index if G[u] in (2018, 2019)]
ctrl_cand = [u for u in wide.index if G[u] == 0]


def level_slope(u):
    ys = [y for y in PREW if y in wide.columns and pd.notna(wide.loc[u, y])]
    if len(ys) < 4:
        return None
    v = [wide.loc[u, y] for y in ys]
    return np.mean(v), np.polyfit(ys, v, 1)[0]

feat = {u: level_slope(u) for u in treated + ctrl_cand}
feat = {u: f for u, f in feat.items() if f is not None}
treated = [u for u in treated if u in feat]
ctrl_cand = [u for u in ctrl_cand if u in feat]

# standardize (level, slope)
L = np.array([feat[u] for u in feat]); mu = L.mean(0); sd = L.std(0)
z = {u: (np.array(feat[u]) - mu) / sd for u in feat}

# k-NN match (with replacement); matched control pool = union of neighbours
matched = set()
for t in treated:
    d = sorted(ctrl_cand, key=lambda c: np.sum((z[t] - z[c]) ** 2))
    matched.update(d[:K])
matched = sorted(matched)
print(f"treated {len(treated)}  matched never-treated controls {len(matched)} "
      f"(from {len(ctrl_cand)} candidates)")

# balance check
def avg(units, j): return np.mean([feat[u][j] for u in units])
print(f"  level  treated {avg(treated,0):.3f} vs matched {avg(matched,0):.3f} "
      f"(all-ctrl {avg(ctrl_cand,0):.3f})")
print(f"  slope  treated {avg(treated,1)*100:+.2f}pp/yr vs matched {avg(matched,1)*100:+.2f} "
      f"(all-ctrl {avg(ctrl_cand,1)*100:+.2f})")

cohorts = [2018, 2019]
sample = treated + matched
Gm = {u: (G[u] if G[u] in cohorts else 0) for u in sample}
wsamp = wide.loc[sample]
years = sorted(df.year.unique())


def att_sub(g, t, tr_units, all_units, Gv, W):
    base = g - 1
    if base not in W.columns or t not in W.columns:
        return None
    yb, yt = W[base], W[t]
    tre = [u for u in tr_units if pd.notna(yb[u]) and pd.notna(yt[u])]
    con = [u for u in all_units if Gv[u] == 0 and pd.notna(yb[u]) and pd.notna(yt[u])]
    if len(tre) < 1 or len(con) < 5:
        return None
    return (yt[tre] - yb[tre]).mean() - (yt[con] - yb[con]).mean(), len(tre)


def aggregate(all_units, Gv, W, tr_filter=None, drop2020=False):
    tu = tr_filter if tr_filter is not None else all_units
    es, post = {}, []
    yrs = [y for y in years if not (drop2020 and y == 2020)]
    for g in cohorts:
        gu = [u for u in tu if Gv[u] == g]
        if not gu:
            continue
        for t in yrs:
            r = att_sub(g, t, gu, all_units, Gv, W)
            if r is None:
                continue
            a, w = r
            es.setdefault(t - g, []).append((a, w))
            if t >= g:
                post.append((a, w))
    wm = lambda P: float(np.average([x[0] for x in P], weights=[x[1] for x in P])) if P else np.nan
    return wm(post), {e: wm(v) for e, v in es.items()}


def boot(all_units, Gv, tr_filter=None, drop2020=False):
    out = []
    for _ in range(B):
        s = rng.choice(all_units, len(all_units), replace=True)
        Wb = wide.loc[s].reset_index(drop=True)
        Gb = {i: Gv[u] for i, u in enumerate(s)}
        idx = list(range(len(s)))
        tf = None
        if tr_filter is not None:
            keep = set(tr_filter); tf = [i for i, u in enumerate(s) if u in keep]
        o, _ = aggregate(idx, Gb, Wb, tr_filter=tf, drop2020=drop2020)
        if not np.isnan(o):
            out.append(o)
    out = np.array(out)
    return out.std(ddof=1), np.percentile(out, [2.5, 97.5])


o, es = aggregate(sample, Gm, wsamp)
se, ci = boot(sample, Gm)
print(f"\n=== Matched CS overall post ATT === {o*100:+.2f} pp  SE {se*100:.2f} "
      f"95% CI [{ci[0]*100:+.2f},{ci[1]*100:+.2f}]")
print("event study (ref t-1):")
for e in sorted(es):
    print(f"  t{e:+d} [{'pre ' if e<0 else 'post'}]: {es[e]*100:+6.2f} pp")

od, _ = aggregate(sample, Gm, wsamp, drop2020=True)
sed, _ = boot(sample, Gm, drop2020=True)
print(f"\n[robustness] drop COVID 2020: ATT {od*100:+.2f} pp (SE {sed*100:.2f})")

# heterogeneity by baseline retention, within matched sample
base_ret = {u: feat[u][0] for u in treated}
medb = np.median(list(base_ret.values()))
for lab, grp in [("LOW baseline (higher-need)", [u for u in treated if base_ret[u] <= medb]),
                 ("HIGH baseline", [u for u in treated if base_ret[u] > medb])]:
    oo, _ = aggregate(sample, Gm, wsamp, tr_filter=grp)
    ss, cc = boot(sample, Gm, tr_filter=grp)
    print(f"[Heterogeneity] {lab}: ATT {oo*100:+.2f} pp (SE {ss*100:.2f}) n={len(grp)}")
