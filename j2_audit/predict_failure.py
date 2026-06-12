"""
J2 predictive layer: which institutions fail the 4/5ths completion test for
Black students (2022)? Merges the real disparate-impact panel with real IPEDS
institutional features (directory + admissions), then fits:
  (1) statsmodels logistic regression -> interpretable odds ratios (policy story)
  (2) sklearn gradient boosting -> 5-fold CV AUC + feature importances (prediction)
All data real (Urban Institute Education Data API, IPEDS).
"""
import os, urllib.request, json, time, csv
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
YEAR = 2022

def fetch(url, tries=6):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except Exception:
            if a == tries - 1: raise
            time.sleep(4 * (a + 1))

def pull(path):
    url = f"https://educationdata.urban.org/api/v1/college-university/ipeds/{path}"
    out = []
    while url:
        d = fetch(url); out += d["results"]; url = d.get("next")
    return out

# --- outcome: 2022 Black disparate-impact failures ---
panel = pd.read_csv(os.path.join(HERE, "disparate_impact_panel.csv"))
p = panel[(panel.year == YEAR) & panel.black_fail.notna()].copy()
print(f"auditable institutions (Black, {YEAR}): {len(p)}", flush=True)

# --- features: directory ---
dirr = pd.DataFrame(pull(f"directory/{YEAR}/"))[
    ["unitid", "inst_control", "region", "hbcu", "institution_level", "inst_size"]]
print("directory pulled", flush=True)

# --- features: admissions (selectivity) ---
adm = pd.DataFrame(pull(f"admissions-enrollment/{YEAR}/?sex=99"))
adm = adm.groupby("unitid").agg(applied=("number_applied", "max"),
                                admitted=("number_admitted", "max"),
                                enrolled=("number_enrolled_total", "max")).reset_index()
print("admissions pulled", flush=True)

df = p.merge(dirr, on="unitid", how="left").merge(adm, on="unitid", how="left")

# --- feature engineering ---
df["admit_rate"] = (df["admitted"] / df["applied"]).clip(0, 1)
df["open_admission"] = df["applied"].isna().astype(int)      # no admissions data => open enrollment
df["admit_rate"] = df["admit_rate"].fillna(1.0)              # open admission = least selective
df["log_enroll"] = np.log1p(df["enrolled"].fillna(df["enrolled"].median()))
df["hbcu_flag"] = (df["hbcu"] == 1).astype(int)
df["for_profit"] = (df["inst_control"] == 3).astype(int)
df["private_nonprofit"] = (df["inst_control"] == 2).astype(int)  # public = reference
df["white_rate"] = df["white_rate"]                          # overall completion proxy
y = df["black_fail"].astype(int)

feat = ["admit_rate", "open_admission", "log_enroll", "hbcu_flag",
        "for_profit", "private_nonprofit", "white_rate"]
X = df[feat].astype(float)
X = X.fillna(X.median())

print(f"\nmodeling N = {len(X)}; outcome mean (fail rate) = {y.mean():.2f}\n", flush=True)

# (1) interpretable logistic -> odds ratios
import statsmodels.api as sm
logit = sm.Logit(y, sm.add_constant(X)).fit(disp=0)
print("=== Logistic regression (odds ratios) ===")
OR = np.exp(logit.params); ci = np.exp(logit.conf_int())
for k in logit.params.index:
    print(f"  {k:18s} OR={OR[k]:6.2f}  p={logit.pvalues[k]:.3g}  [{ci.loc[k,0]:.2f}, {ci.loc[k,1]:.2f}]")

# (2) predictive performance + importances
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score
gb = GradientBoostingClassifier(random_state=42)
auc = cross_val_score(gb, X, y, cv=5, scoring="roc_auc")
print(f"\n=== Gradient boosting: 5-fold CV AUC = {auc.mean():.3f} (+/- {auc.std():.3f}) ===")
gb.fit(X, y)
imp = sorted(zip(feat, gb.feature_importances_), key=lambda t: -t[1])
print("feature importances:")
for f, v in imp: print(f"  {f:18s} {v:.3f}")

# (3) descriptive: failure rate by selectivity tier and sector
df["fail"] = y.values
df.to_csv(os.path.join(HERE, "predict_features_2022.csv"), index=False)
print("\nsaved predict_features_2022.csv")
print("\n=== Failure rate by selectivity (admit rate) ===")
df["sel_tier"] = pd.cut(df["admit_rate"], [-0.01, 0.25, 0.50, 0.75, 1.01],
                        labels=["<25% (most selective)", "25-50%", "50-75%", ">75% (open/least)"])
print(df.groupby("sel_tier", observed=True)["fail"].agg(["mean", "size"]).round(2).to_string())
print("\n=== Failure rate by sector ===")
df["sector_lbl"] = np.where(df.for_profit == 1, "for-profit",
                            np.where(df.private_nonprofit == 1, "private NP", "public"))
print(df.groupby("sector_lbl")["fail"].agg(["mean", "size"]).round(2).to_string())
print("\n=== Failure rate by overall (White) completion tier ===")
df["compl_tier"] = pd.cut(df["white_rate"], [-0.01, 0.4, 0.6, 0.8, 1.01],
                          labels=["<40%", "40-60%", "60-80%", ">80%"])
print(df.groupby("compl_tier", observed=True)["fail"].agg(["mean", "size"]).round(2).to_string())
