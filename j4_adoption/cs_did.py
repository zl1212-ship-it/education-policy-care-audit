"""
Callaway & Sant'Anna (2021) staggered DiD, hand-implemented, for J4.

ATT(g,t) = [E(Y_t - Y_{g-1} | G=g)] - [E(Y_t - Y_{g-1} | not-yet-treated)]
  control set for (g,t) = never-treated OR G>t, excluding cohort g.
Aggregations: event-study (by t-g) and overall post ATT, cohort-size weighted.
Inference: clustered (by institution) multiplier-free bootstrap, B reps.

Heterogeneity: same estimator with treated restricted to a subgroup
  (a) low vs high baseline pre-adoption retention,
  (b) low vs high %URM (Black+Hispanic+AmInd+NHPI+two-or-more share, IPEDS 2016).
"""
import os, urllib.request, json, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
B = 400
rng = np.random.default_rng(7)

df = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
df.loc[df.adoption_year > 2020, "adoption_year"] = np.nan          # post-window adopters = control
df["G"] = df.adoption_year.fillna(0).astype(int)                  # 0 = never-treated

wide = df.pivot_table(index="unitid", columns="year", values="retention_rate")
G = df.groupby("unitid")["G"].first()
years = sorted(df.year.unique())
cohorts = sorted(c for c in G.unique() if c != 0)
print(f"institutions {wide.shape[0]}  cohorts {cohorts}  "
      f"cohort sizes { {c:int((G==c).sum()) for c in cohorts} }")


def aggregate(units, Gv, treated_filter=None):
    """Return overall post ATT and event-study dict, cohort-size weighted."""
    tu = units if treated_filter is None else treated_filter
    es = {}                                   # event_time -> [(att, w), ...]
    post = []                                 # (att, w) for t>=g
    for g in cohorts:
        gunits = [u for u in tu if Gv[u] == g]
        if not gunits:
            continue
        for t in years:
            r = _att_sub(g, t, gunits, units, Gv)   # treated from subgroup, controls from full pool
            if r is None:
                continue
            att, w = r
            e = t - g
            es.setdefault(e, []).append((att, w))
            if t >= g:
                post.append((att, w))
    def wm(pairs):
        a = np.array([x[0] for x in pairs]); w = np.array([x[1] for x in pairs], float)
        return float((a * w).sum() / w.sum()) if len(pairs) else np.nan
    es_agg = {e: wm(v) for e, v in es.items()}
    return wm(post), es_agg


def _att_sub(g, t, treated_units, all_units, Gv):
    base = g - 1
    if base not in wide.columns or t not in wide.columns:
        return None
    yb, yt = wide[base], wide[t]
    treated = [u for u in treated_units if pd.notna(yb[u]) and pd.notna(yt[u])]
    control = [u for u in all_units if (Gv[u] == 0 or Gv[u] > t) and Gv[u] != g
               and pd.notna(yb[u]) and pd.notna(yt[u])]
    if len(treated) < 1 or len(control) < 5:
        return None
    return (yt[treated] - yb[treated]).mean() - (yt[control] - yb[control]).mean(), len(treated)


def boot(units, Gv, treated_filter=None):
    """Clustered bootstrap SE for the overall post ATT."""
    base_units = list(units)
    ests = []
    for _ in range(B):
        samp = rng.choice(base_units, size=len(base_units), replace=True)
        # relabel duplicates as distinct units so they enter means with multiplicity
        wide_b = wide.loc[samp].reset_index(drop=True)
        Gb = pd.Series([Gv[u] for u in samp])
        tf = None
        if treated_filter is not None:
            keepset = set(treated_filter)
            tf = [i for i, u in enumerate(samp) if u in keepset]
        # rebind globals for the helper via closure-free recompute
        ests.append(_overall_on(wide_b, Gb, tf))
    ests = np.array([e for e in ests if not np.isnan(e)])
    return ests.std(ddof=1), np.percentile(ests, [2.5, 97.5])


def _overall_on(wide_b, Gb, treated_idx):
    idx = list(wide_b.index)
    post = []
    for g in cohorts:
        gunits = [u for u in idx if Gb[u] == g] if treated_idx is None \
                 else [u for u in treated_idx if Gb[u] == g]
        if not gunits:
            continue
        for t in years:
            base = g - 1
            if base not in wide_b.columns or t not in wide_b.columns or t < g:
                continue
            yb, yt = wide_b[base], wide_b[t]
            treated = [u for u in gunits if pd.notna(yb[u]) and pd.notna(yt[u])]
            control = [u for u in idx if (Gb[u] == 0 or Gb[u] > t) and Gb[u] != g
                       and pd.notna(yb[u]) and pd.notna(yt[u])]
            if len(treated) < 1 or len(control) < 5:
                continue
            att = (yt[treated] - yb[treated]).mean() - (yt[control] - yb[control]).mean()
            post.append((att, len(treated)))
    if not post:
        return np.nan
    a = np.array([x[0] for x in post]); w = np.array([x[1] for x in post], float)
    return float((a * w).sum() / w.sum())


# ---------- main estimates ----------
allu = list(wide.index)
overall, es = aggregate(allu, G)
se, ci = boot(allu, G)
print("\n=== CS overall post ATT (not-yet-treated controls) ===")
print(f"  ATT = {overall*100:+.2f} pp   SE {se*100:.2f}   95% CI [{ci[0]*100:+.2f}, {ci[1]*100:+.2f}]")
print("\n=== CS event study (cohort-weighted) ===")
for e in sorted(es):
    tag = "pre " if e < 0 else "post"
    print(f"  t{e:+d} [{tag}]: {es[e]*100:+6.2f} pp")
pd.DataFrame([(e, es[e]) for e in sorted(es)], columns=["event_time", "att"]) \
  .to_csv(os.path.join(DATA, "cs_event_study.csv"), index=False)

# ---------- heterogeneity (a): baseline pre-adoption retention ----------
base_ret = {}
for u in allu:
    g = G[u]
    if g and (g - 1) in wide.columns and pd.notna(wide.loc[u, g - 1]):
        base_ret[u] = wide.loc[u, g - 1]
med = np.median(list(base_ret.values()))
low = [u for u in base_ret if base_ret[u] <= med]    # higher-need (weaker baseline)
high = [u for u in base_ret if base_ret[u] > med]
for label, grp in [("LOW baseline retention (higher-need)", low),
                   ("HIGH baseline retention", high)]:
    o, _ = aggregate(allu, G, treated_filter=grp)
    s, c = boot(allu, G, treated_filter=grp)
    print(f"\n[Heterogeneity A] {label}: ATT {o*100:+.2f} pp (SE {s*100:.2f}) n={len(grp)}")

# ---------- heterogeneity (b): %URM ----------
urm_path = os.path.join(DATA, "urm_composition.csv")
if not os.path.exists(urm_path):
    url = ("https://educationdata.urban.org/api/v1/college-university/ipeds/"
           "fall-enrollment/2016/1/race/?sex=99&ftpt=99&degree_seeking=99&class_level=99")
    rows = []
    while url:
        with urllib.request.urlopen(url, timeout=120) as r:
            d = json.load(r)
        rows += d["results"]; url = d.get("next")
    tot, urm = {}, {}
    for x in rows:
        u, rc, n = x["unitid"], x["race"], x.get("enrollment_fall") or 0
        if rc == 99: tot[u] = n
        elif rc in (2, 3, 5, 6, 7): urm[u] = urm.get(u, 0) + n
    pd.DataFrame([(u, urm.get(u, 0) / tot[u]) for u in tot if tot[u] > 0],
                 columns=["unitid", "urm_share"]).to_csv(urm_path, index=False)
urmdf = pd.read_csv(urm_path).set_index("unitid")["urm_share"]
tre = [u for u in allu if G[u] != 0 and u in urmdf.index]
mu = np.median([urmdf[u] for u in tre])
hi_urm = [u for u in tre if urmdf[u] > mu]
lo_urm = [u for u in tre if urmdf[u] <= mu]
for label, grp in [("HIGH %URM treated", hi_urm), ("LOW %URM treated", lo_urm)]:
    o, _ = aggregate(allu, G, treated_filter=grp)
    s, c = boot(allu, G, treated_filter=grp)
    print(f"\n[Heterogeneity B] {label}: ATT {o*100:+.2f} pp (SE {s*100:.2f}) n={len(grp)}")
