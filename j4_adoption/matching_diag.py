"""
Matching diagnostics for the revision: post-matching balance and a matched event study.
Rebuilds the matched comparison (treated 2018/2019 cohorts matched to their 5 nearest
never-treated neighbors on 2011-2017 retention level and slope), reports balance on level
and slope, and computes the Callaway-Sant'Anna event-study coefficients on the matched
sample (no bootstrap; for the pre-trend figure). Saves a CSV and Figure 4.
"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
MAN = os.path.join(HERE, "..", "paper", "blinded-manuscript")
PREW = list(range(2011, 2018)); K = 5

df = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
df.loc[df.adoption_year > 2020, "adoption_year"] = np.nan
G = df.groupby("unitid")["adoption_year"].first().fillna(0).astype(int)
wide = df.pivot_table(index="unitid", columns="year", values="retention_rate")
years = sorted(df.year.unique())

treated = [u for u in wide.index if G[u] in (2018, 2019)]
ctrl = [u for u in wide.index if G[u] == 0]
def lvslope(u):
    ys = [y for y in PREW if y in wide.columns and pd.notna(wide.loc[u, y])]
    if len(ys) < 4: return None
    v = [wide.loc[u, y] for y in ys]
    return np.mean(v), np.polyfit(ys, v, 1)[0]
feat = {u: lvslope(u) for u in treated + ctrl}; feat = {u: f for u, f in feat.items() if f}
treated = [u for u in treated if u in feat]; ctrl = [u for u in ctrl if u in feat]
L = np.array(list(feat.values())); mu, sd = L.mean(0), L.std(0)
z = {u: (np.array(feat[u]) - mu) / sd for u in feat}
matched = set()
for t in treated:
    matched.update(sorted(ctrl, key=lambda c: np.sum((z[t] - z[c]) ** 2))[:K])
matched = sorted(matched)

def avg(units, j): return np.mean([feat[u][j] for u in units])
print("=== Post-matching balance (first-year retention) ===")
print(f"{'group':<22}{'level':>8}{'slope (pp/yr)':>16}")
for lab, grp in [("Treated", treated), ("Matched controls", matched), ("All controls", ctrl)]:
    print(f"{lab:<22}{avg(grp,0):>8.3f}{avg(grp,1)*100:>16.2f}")
bal = pd.DataFrame([(lab, round(avg(grp,0),3), round(avg(grp,1)*100,2))
                    for lab, grp in [("Treated",treated),("Matched controls",matched),("All controls",ctrl)]],
                   columns=["group","level","slope_pp_yr"])
bal.to_csv(os.path.join(DATA, "matching_balance.csv"), index=False)

# event study on matched sample (treated vs never-treated controls), CS group-time, no bootstrap
sample = treated + matched
Gm = {u: (G[u] if G[u] in (2018, 2019) else 0) for u in sample}
def att(g, t, tr, allu):
    base = g - 1
    if base not in wide.columns or t not in wide.columns: return None
    yb, yt = wide[base], wide[t]
    a = [u for u in tr if pd.notna(yb[u]) and pd.notna(yt[u])]
    c = [u for u in allu if Gm[u] == 0 and pd.notna(yb[u]) and pd.notna(yt[u])]
    if len(a) < 1 or len(c) < 5: return None
    return (yt[a]-yb[a]).mean() - (yt[c]-yb[c]).mean(), len(a)
es = {}
for g in (2018, 2019):
    gu = [u for u in treated if Gm[u] == g]
    for t in years:
        r = att(g, t, gu, sample)
        if r: es.setdefault(t-g, []).append(r)
ev = {e: float(np.average([x[0] for x in v], weights=[x[1] for x in v])) for e, v in es.items()}
evd = pd.DataFrame(sorted(ev.items()), columns=["event_time","att"]); evd.to_csv(os.path.join(DATA,"matched_event_study.csv"),index=False)
print("\nmatched event study (ref t-1):")
for e in sorted(ev): print(f"  t{e:+d}: {ev[e]*100:+.2f} pp")

fig, ax = plt.subplots(figsize=(6.5, 4))
es_sorted = sorted([e for e in ev if -7 <= e <= 2])
ax.axhline(0, color="0.6", linewidth=0.8); ax.axvline(-0.5, color="0.6", linewidth=0.8, linestyle=":")
ax.plot(es_sorted, [ev[e]*100 for e in es_sorted], "o-", color="black")
ax.set_xlabel("Years relative to adoption"); ax.set_ylabel("Effect on retention (pp)")
ax.set_title("Matched event study", fontsize=11)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(MAN, "j4_figure4.pdf"), bbox_inches="tight")
plt.savefig(os.path.join(HERE, "j4_figure4.png"), dpi=150, bbox_inches="tight")
print("saved matching_balance.csv, matched_event_study.csv, figure 4")
