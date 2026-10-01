"""
J4 first-pass DiD: effect of adopting an EAB early-alert/predictive system on
first-time full-time retention, public 4-year institutions, 2009-2020.

(1) Static two-way fixed-effects DiD (treat x post), SE clustered by institution.
(2) Event study relative to adoption year (ref = t-1) for pre-trends + dynamics.

TWFE is a benchmark; with staggered timing it can be biased (Goodman-Bacon).
Callaway-Sant'Anna is the intended robustness check (needs the `differences` pkg).
"""
import os, numpy as np, pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
df = pd.read_csv(os.path.join(DATA, "retention_panel.csv"))

# Adopters beyond the sample window (e.g., Georgia Tech 2025) act as controls here.
df.loc[(df.adoption_year != "") & (pd.to_numeric(df.adoption_year, errors="coerce") > 2020),
       ["treated", "adoption_year"]] = [0, ""]
df["adoption_year"] = pd.to_numeric(df["adoption_year"], errors="coerce")
df["treat_post"] = ((df.treated == 1) & (df.year >= df.adoption_year)).astype(int)

print(f"institutions: {df.unitid.nunique()}  treated: {df[df.treated==1].unitid.nunique()}")
print("treated cohorts:", dict(sorted(
    df[df.treated == 1].groupby("adoption_year")["unitid"].nunique().items())))

# ---- (1) Static TWFE DiD ----
m1 = smf.ols("retention_rate ~ treat_post + C(unitid) + C(year)", data=df) \
        .fit(cov_type="cluster", cov_kwds={"groups": df["unitid"]})
b, se, p = m1.params["treat_post"], m1.bse["treat_post"], m1.pvalues["treat_post"]
print("\n=== Static TWFE DiD ===")
print(f"  ATT(treat_post) = {b:+.4f}  (SE {se:.4f}, p={p:.3f})  "
      f"=> {b*100:+.2f} pp retention")

# ---- (2) Event study ----
d = df[df.treated == 1].copy()
df["evt"] = (df.year - df.adoption_year)
# bin endpoints, reference = -1
def binv(e):
    if pd.isna(e): return np.nan
    e = int(e)
    if e <= -6: return -6
    if e >= 4:  return 4
    return e
df["evt_b"] = df["evt"].apply(binv)
ev = df.copy()
ev["evt_b"] = ev["evt_b"].fillna("ctrl")
# build dummies for each event time except reference -1 and the control bucket
dums = pd.get_dummies(ev["evt_b"], prefix="e")
for col in ["e_-1.0", "e_ctrl", "e_-1", "e_-1.0"]:
    if col in dums: dums = dums.drop(columns=col)
X = pd.concat([dums, pd.get_dummies(ev["unitid"], prefix="u", drop_first=True),
               pd.get_dummies(ev["year"], prefix="y", drop_first=True)], axis=1)
X = sm.add_constant(X.astype(float))
m2 = sm.OLS(ev["retention_rate"].values, X.values) \
       .fit(cov_type="cluster", cov_kwds={"groups": ev["unitid"].values})
names = ["const"] + list(X.columns[1:])
print("\n=== Event study (ref = t-1), retention pp ===")
rows = []
for i, nm in enumerate(names):
    if nm.startswith("e_"):
        et = nm.replace("e_", "").replace(".0", "")
        rows.append((float(et), m2.params[i], m2.bse[i]))
for et, co, se_ in sorted(rows):
    star = "*" if abs(co / se_) > 1.96 else " "
    tag = "  <-- pre" if et < 0 else ("  <-- post" if et >= 0 else "")
    print(f"  t{int(et):+d}: {co*100:+6.2f} pp (SE {se_*100:4.2f}){star}{tag}")
pd.DataFrame(rows, columns=["event_time", "coef", "se"]).sort_values("event_time") \
  .to_csv(os.path.join(DATA, "event_study.csv"), index=False)
print("\nsaved data/event_study.csv")
