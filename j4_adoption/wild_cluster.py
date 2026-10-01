"""
Few-treated-clusters inference for J4. Treatment is assigned at the state-system level
(CSU = California 2018; UW = Wisconsin 2019), so the institution-clustered bootstrap
overstates precision. This script clusters at the STATE level and runs a wild cluster
restricted (WCR) bootstrap with Webb 6-point weights (MacKinnon & Webb), the standard
remedy when the number of treated clusters is small.

Specification: static DiD on the matched sample,
    retention_it = beta * treat_post_it + unit FE + year FE + e_it,
with inference clustered by state.
"""
import os, numpy as np, pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
PREW = list(range(2011, 2018)); K = 5; B = 999
rng = np.random.default_rng(7)

df = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))
df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
df.loc[df.adoption_year > 2020, "adoption_year"] = np.nan
G = df.groupby("unitid")["adoption_year"].first().fillna(0).astype(int)
ST = df.groupby("unitid")["state"].first()
wide = df.pivot_table(index="unitid", columns="year", values="retention_rate")

# rebuild matched sample (2018/2019 treated cohorts + 5-NN never-treated on 2011-17 level+slope)
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
sample = treated + sorted(matched)

# long data on matched sample
rows = []
for u in sample:
    g = G[u]
    for y in sorted(df.year.unique()):
        if y in wide.columns and pd.notna(wide.loc[u, y]):
            tp = 1 if (g in (2018, 2019) and y >= g) else 0
            rows.append((u, y, ST[u], wide.loc[u, y], tp))
d = pd.DataFrame(rows, columns=["unit", "year", "state", "Y", "treat_post"])
states = sorted(d.state.unique())
treated_states = sorted(d.loc[d.treat_post == 1, "state"].unique())
print(f"matched sample: {len(sample)} institutions, {len(states)} states")
print(f"TREATED states (clusters that identify the effect): {treated_states}  "
      f"-> {len(treated_states)} treated clusters")

# design matrix: treat_post + unit FE + year FE
X = pd.concat([d[["treat_post"]],
               pd.get_dummies(d.unit, prefix="u", drop_first=True),
               pd.get_dummies(d.year, prefix="y", drop_first=True)], axis=1).astype(float)
X = sm.add_constant(X)
y = d.Y.values
sid = d.state.values

def fit_t(yv):
    m = sm.OLS(yv, X.values).fit(cov_type="cluster", cov_kwds={"groups": sid})
    return m.params[1], m.bse[1], m.params[1] / m.bse[1]  # beta, se, t (treat_post is col 1)

b_hat, se_state, t_hat = fit_t(y)
# institution-clustered SE for contrast
m_u = sm.OLS(y, X.values).fit(cov_type="cluster", cov_kwds={"groups": d.unit.values})
print(f"\nstatic DiD on matched sample: beta = {b_hat*100:+.2f} pp")
print(f"  SE clustered by INSTITUTION: {m_u.bse[1]*100:.2f}  (t={b_hat/m_u.bse[1]:.2f})  <- overstates precision")
print(f"  SE clustered by STATE:       {se_state*100:.2f}  (t={t_hat:.2f})  <- correct level")

# WCR bootstrap, Webb 6-point weights, null imposed (restricted)
Xr = X.drop(columns=["treat_post"])
m0 = sm.OLS(y, Xr.values).fit()
yhat0, uhat = m0.fittedvalues, m0.resid
webb = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
cnt = 0
for _ in range(B):
    w = {s: rng.choice(webb) for s in states}
    ystar = yhat0 + np.array([w[s] for s in sid]) * uhat
    _, _, tstar = fit_t(ystar)
    if abs(tstar) >= abs(t_hat):
        cnt += 1
p_wcr = (cnt + 1) / (B + 1)
print(f"\nWild cluster restricted bootstrap (Webb, {B} reps), clustered by state:")
print(f"  p-value for H0: beta = 0  ->  {p_wcr:.3f}")
print("  (with only %d treated clusters, few-cluster inference is itself unreliable;" % len(treated_states))
print("   read this as: the effect is NOT robustly distinguishable from zero once")
print("   uncertainty is taken at the level treatment was actually assigned.)")
