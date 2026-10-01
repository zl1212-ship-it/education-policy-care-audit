"""Pooled predictive model 2018-2022 (year fixed effects) for Black-student
4/5ths failure, to show the institutional correlates are stable over time."""
import os, urllib.request, json, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
def fetch(u,t=6):
    for a in range(t):
        try:
            with urllib.request.urlopen(u,timeout=120) as r: return json.load(r)
        except Exception:
            if a==t-1: raise
            time.sleep(4*(a+1))
def pull(path):
    u=f"https://educationdata.urban.org/api/v1/college-university/ipeds/{path}"; out=[]
    while u:
        d=fetch(u); out+=d["results"]; u=d.get("next")
    return out
panel=pd.read_csv(os.path.join(HERE, "disparate_impact_panel.csv"))
panel=panel[panel.black_fail.notna()].copy()
frames=[]
for y in [2018,2019,2020,2021,2022]:
    d=pd.DataFrame(pull(f"directory/{y}/"))[["unitid","inst_control","hbcu"]]
    a=pd.DataFrame(pull(f"admissions-enrollment/{y}/?sex=99"))
    a=a.groupby("unitid").agg(applied=("number_applied","max"),admitted=("number_admitted","max"),
                              enrolled=("number_enrolled_total","max")).reset_index()
    m=panel[panel.year==y].merge(d,on="unitid",how="left").merge(a,on="unitid",how="left")
    frames.append(m); print(f"year {y} merged",flush=True)
df=pd.concat(frames,ignore_index=True)
df["admit_rate"]=(df["admitted"]/df["applied"]).clip(0,1)
df["open_admission"]=df["applied"].isna().astype(int)
df["admit_rate"]=df["admit_rate"].fillna(1.0)
df["log_enroll"]=np.log1p(df["enrolled"].fillna(df["enrolled"].median()))
df["hbcu_flag"]=(df["hbcu"]==1).astype(int)
df["for_profit"]=(df["inst_control"]==3).astype(int)
df["private_nonprofit"]=(df["inst_control"]==2).astype(int)
y=df["black_fail"].astype(int)
import statsmodels.api as sm
feat=["admit_rate","open_admission","log_enroll","hbcu_flag","for_profit","private_nonprofit","white_rate"]
X=df[feat].astype(float).fillna(df[feat].astype(float).median())
# year fixed effects
yd=pd.get_dummies(df["year"],prefix="yr",drop_first=True).astype(float)
Xf=pd.concat([X,yd],axis=1)
logit=sm.Logit(y,sm.add_constant(Xf)).fit(disp=0)
OR=np.exp(logit.params)
print(f"\n=== POOLED logistic 2018-2022 (N={len(df)} institution-years, year FE) ===")
for k in feat:
    print(f"  {k:18s} OR={OR[k]:6.2f}  p={logit.pvalues[k]:.2g}")
print(f"  (pseudo-R2 = {logit.prsquared:.3f})")

# diagnostics: in-sample classification at 0.5 and collinearity (VIF) of the design matrix
from statsmodels.stats.outliers_influence import variance_inflation_factor
ct=logit.pred_table(threshold=0.5)  # rows=actual, cols=predicted
tn,fp,fn,tp=ct[0,0],ct[0,1],ct[1,0],ct[1,1]
base=max(y.mean(),1-y.mean())  # null model predicts the majority class
print(f"\n=== DIAGNOSTICS ===")
print(f"  pred_table at 0.5: TN={tn:.0f} FP={fp:.0f} FN={fn:.0f} TP={tp:.0f}")
print(f"  accuracy = {(tn+tp)/ct.sum():.3f}  (null-model base rate = {base:.3f})")
print(f"  sensitivity = {tp/(tp+fn):.3f}  specificity = {tn/(tn+fp):.3f}")
Xc=sm.add_constant(Xf).values.astype(float)
vif=pd.Series([variance_inflation_factor(Xc,i) for i in range(1,Xc.shape[1])],index=Xf.columns)
print("  VIF (constant excluded):")
for k in feat:
    print(f"    {k:18s} {vif[k]:6.2f}")
yv=vif[yd.columns]
print(f"    year dummies       {yv.min():.2f}-{yv.max():.2f} ({yd.columns[0]}..{yd.columns[-1]})")
