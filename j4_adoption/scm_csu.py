"""
Synthetic control for the California State University system (system-wide EAB Navigate
adoption, 2018) as a second canonical case. Treated unit = the CSU system, measured as the
mean first-year retention across its campuses each year. The synthetic CSU is a weighted
average of REAL never-treated large public four-year universities outside California.

Caveat: CSU adopted in 2018, so the post-period is short (2018-2020) and includes COVID,
and eight CSU campuses used EAB before 2018 (pre-period contamination). This case
corroborates rather than strongly tests. Outcome: IPEDS full-time retention (real data).
"""
import os, json, urllib.request, numpy as np, pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
YEARS = list(range(2004, 2021)); PRE = list(range(2004, 2018)); POST = [2018, 2019, 2020]
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"


def pull(url):
    out = []
    while url:
        for a in range(6):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    d = json.load(r); break
            except Exception:
                if a == 5: raise
        out += d["results"]; url = d.get("next")
    return out


csu_ids = set(pd.read_csv(os.path.join(DATA, "csu_staging.csv"))["unitid"].tolist())
dirr = pull(f"{BASE}/directory/2021/?inst_control=1")
large = {x["unitid"]: x.get("state_abbr") for x in dirr
         if x.get("institution_level") == 4 and x.get("inst_size") in (4, 5)}
exclude = set(csu_ids)
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
donor_ids = {u for u, st in large.items() if u not in exclude and st != "CA"}
print(f"donor pool (large public 4yr, non-CA, never-treated): {len(donor_ids)}", flush=True)

ret = {}
for y in YEARS:
    for x in pull(f"{BASE}/fall-retention/{y}/?ftpt=1"):
        if x.get("retention_rate") is not None:
            ret[(x["unitid"], y)] = x["retention_rate"]
    print(f"  {y} pulled", flush=True)

# treated = mean CSU campus retention per year
csu_series = []
for y in YEARS:
    vals = [ret[(u, y)] for u in csu_ids if (u, y) in ret]
    csu_series.append(np.mean(vals) if vals else np.nan)
y_csu = np.array(csu_series)
print(f"CSU aggregate retention series complete: {not np.isnan(y_csu).any()}", flush=True)

def series(u):
    return np.array([ret[(u, y)] for y in YEARS]) if all((u, y) in ret for y in YEARS) else None
donors = {u: s for u in donor_ids if (s := series(u)) is not None}
print(f"balanced donors: {len(donors)}", flush=True)

DU = sorted(donors); Z = np.array([donors[u] for u in DU]).T
yi = {y: i for i, y in enumerate(YEARS)}
pre_idx = [yi[y] for y in PRE]; post_idx = [yi[y] for y in POST]


def synth_weights(target, Zmat):
    Zp, tp = Zmat[pre_idx], target[pre_idx]
    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    r = minimize(lambda w: float(np.sum((tp - Zp @ w) ** 2)), np.full(Zmat.shape[1], 1 / Zmat.shape[1]),
                 method="SLSQP", bounds=[(0, 1)] * Zmat.shape[1], constraints=cons,
                 options={"maxiter": 800, "ftol": 1e-12})
    return r.x


w = synth_weights(y_csu, Z); synth = Z @ w
pre_rmspe = np.sqrt(np.mean((y_csu[pre_idx] - synth[pre_idx]) ** 2))
print(f"\n=== CSU synthetic control: first-year retention ===")
print(f"pre-period (2004-2017) RMSPE: {pre_rmspe*100:.2f} pp")
print("top donor weights:")
for u, wi in sorted(zip(DU, w), key=lambda t: -t[1])[:6]:
    if wi > 0.01: print(f"   {u}  {wi:.3f}  ({large.get(u)})")
print("\nyear  realCSU  synth   gap(pp)")
for y in YEARS:
    i = yi[y]
    print(f"  {y}  {y_csu[i]*100:5.1f}  {synth[i]*100:5.1f}  {(y_csu[i]-synth[i])*100:+5.1f}  {'post' if y>=2018 else 'pre'}")
print(f"\naverage post-2018 gap: {(y_csu[post_idx]-synth[post_idx]).mean()*100:+.2f} pp")

import csv as _csv
with open(os.path.join(DATA, "scm_csu_series.csv"), "w", newline="") as _f:
    _w = _csv.writer(_f); _w.writerow(["year", "real", "synth"])
    for y in YEARS:
        _w.writerow([y, round(float(y_csu[yi[y]]), 4), round(float(synth[yi[y]]), 4)])

def ratio(target, Zmat):
    ww = synth_weights(target, Zmat); s = Zmat @ ww
    pr = np.sqrt(np.mean((target[pre_idx] - s[pre_idx]) ** 2))
    po = np.sqrt(np.mean((target[post_idx] - s[post_idx]) ** 2))
    return (po / pr) if pr > 1e-6 else np.nan
g = ratio(y_csu, Z)
rs = np.array([r for j in range(len(DU)) if not np.isnan(r := ratio(donors[DU[j]], np.delete(Z, j, axis=1)))])
p = (np.sum(rs >= g) + 1) / (len(rs) + 1)
print(f"\nplacebo inference: CSU post/pre RMSPE ratio = {g:.2f}; rank among {len(rs)} placebos -> p = {p:.3f}")
