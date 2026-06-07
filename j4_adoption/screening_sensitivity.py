"""
Sensitivity of the screened-donor synthetic controls (GSU Black graduation rate; GSU
retention) to the screening size K. Loads cached IPEDS data. Shows whether the qualitative
conclusions hold across K in {20, 25, 30, 40, 60}.
"""
import os, numpy as np, pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940; YEARS = list(range(2004, 2021)); yi = {y: i for i, y in enumerate(YEARS)}
PRE = list(range(2004, 2012)); pre_idx = [yi[y] for y in PRE]; post_idx = [yi[y] for y in YEARS if y >= 2012]


def load(name):
    df = pd.read_csv(os.path.join(DATA, f"raw_{name}.csv"))
    return {(int(r.uid), int(r.year)): r.val for r in df.itertuples()}


grad_b, ret = load("grad_b"), load("ret")
import json, urllib.request
dirr = json.load(urllib.request.urlopen(
    "https://educationdata.urban.org/api/v1/college-university/ipeds/directory/2021/?inst_control=1", timeout=120))["results"]
size5 = {x["unitid"] for x in dirr if x.get("institution_level") == 4 and x.get("inst_size") == 5
         and x.get("state_abbr") != "GA"}
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
donor_ids = size5 - exclude


def series(src, u):
    return np.array([src[(u, y)] for y in YEARS]) if all((u, y) in src for y in YEARS) else None


def synth(target, Z):
    Zp, tp = Z[pre_idx], target[pre_idx]
    r = minimize(lambda w: float(np.sum((tp - Zp @ w) ** 2)), np.full(Z.shape[1], 1/Z.shape[1]),
                 method="SLSQP", bounds=[(0,1)]*Z.shape[1], constraints={"type":"eq","fun":lambda w:w.sum()-1},
                 options={"maxiter":600,"ftol":1e-11})
    return Z @ r.x


def run(src, label, Ks):
    t = series(src, GSU)
    donors = {u: s for u in donor_ids if (s := series(src, u)) is not None}
    tp = t[pre_idx]
    order = sorted(donors, key=lambda u: float(np.mean((tp - donors[u][pre_idx])**2)))
    print(f"\n{label} (full pool {len(donors)} donors):")
    print(f"{'K':>4}{'pre-RMSPE(pp)':>14}{'avg post gap(pp)':>18}{'placebo p':>11}")
    for K in Ks:
        DU = order[:K]; Z = np.array([donors[u] for u in DU]).T
        s = synth(t, Z)
        pr = np.sqrt(np.mean((t[pre_idx]-s[pre_idx])**2)); gap = (t[post_idx]-s[post_idx]).mean()
        # placebo within the K-pool
        def ratio(tt, Zm):
            ss = synth(tt, Zm); p = np.sqrt(np.mean((tt[pre_idx]-ss[pre_idx])**2))
            return (np.sqrt(np.mean((tt[post_idx]-ss[post_idx])**2))/p if p>1e-6 else np.nan)
        g = ratio(t, Z); rs = [r for j in range(len(DU)) if not np.isnan(r:=ratio(donors[DU[j]], np.delete(Z,j,axis=1)))]
        p = (np.sum(np.array(rs) >= g)+1)/(len(rs)+1)
        print(f"{K:>4}{pr*100:>14.2f}{gap*100:>18.2f}{p:>11.3f}")


run(grad_b, "GSU Black graduation rate", [20, 25, 30, 40, 60])
run(ret, "GSU first-year retention", [20, 25, 30, 40, 60])
print("\n(stable sign across K = robust to the screening choice)")
