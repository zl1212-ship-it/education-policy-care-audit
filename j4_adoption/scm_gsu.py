"""
Synthetic control for Georgia State University, the canonical predictive-analytics
success case. Outcome: IPEDS six-year (150%) graduation rate (the outcome GSU's story is
about), 2004-2020. GSU adopted GPS Advising / EAB in 2012. The synthetic GSU is a weighted
average of REAL never-treated LARGE public four-year universities (inst_size = 5), with
weights chosen to match GSU's actual graduation rate over 2004-2011.

No fabricated data: every input is real IPEDS graduation-rate data (Urban Education Data API).
Inference: placebo permutation on the post/pre RMSPE ratio (Abadie).
"""
import os, json, urllib.request, numpy as np, pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
YEARS = list(range(2004, 2021)); PRE = list(range(2004, 2012)); POST = list(range(2012, 2021))
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


# donor universe: LARGE (inst_size=5) public 4-year, non-GA, never in our adopter list
dirr = pull(f"{BASE}/directory/2021/?inst_control=1")
large = {x["unitid"]: x.get("state_abbr") for x in dirr
         if x.get("institution_level") == 4 and x.get("inst_size") == 5}
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    p = os.path.join(DATA, f)
    if os.path.exists(p): exclude |= set(pd.read_csv(p)["unitid"].tolist())
donor_ids = {u for u, st in large.items() if u not in exclude and st != "GA"}
print(f"donor pool (large public 4yr, non-GA, never-treated): {len(donor_ids)}", flush=True)

# 6-year grad rate (total), 2004-2020
grad = {}
for y in YEARS:
    for x in pull(f"{BASE}/grad-rates/{y}/?race=99&sex=99"):
        v = x.get("completion_rate_150pct")
        if v is not None: grad[(x["unitid"], y)] = v
    print(f"  {y} pulled", flush=True)

def series(u):
    return np.array([grad[(u, y)] for y in YEARS]) if all((u, y) in grad for y in YEARS) else None
y_gsu = series(GSU)
donors = {u: s for u in donor_ids if (s := series(u)) is not None}
print(f"GSU complete: {y_gsu is not None}; balanced donors: {len(donors)}", flush=True)

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


w = synth_weights(y_gsu, Z); synth = Z @ w
pre_rmspe = np.sqrt(np.mean((y_gsu[pre_idx] - synth[pre_idx]) ** 2))
print(f"\n=== GSU synthetic control: 6-year graduation rate ===")
print(f"pre-period (2004-2011) RMSPE: {pre_rmspe*100:.2f} pp")
print("top donor weights:")
for u, wi in sorted(zip(DU, w), key=lambda t: -t[1])[:6]:
    if wi > 0.01: print(f"   {u}  {wi:.3f}  ({large.get(u)})")
print("\nyear  realGSU  synth   gap(pp)")
for y in YEARS:
    i = yi[y]
    print(f"  {y}  {y_gsu[i]*100:5.1f}  {synth[i]*100:5.1f}  {(y_gsu[i]-synth[i])*100:+5.1f}  {'post' if y>=2012 else 'pre'}")
print(f"\naverage post-2012 gap (real - synthetic): {(y_gsu[post_idx]-synth[post_idx]).mean()*100:+.2f} pp")

import csv as _csv
with open(os.path.join(DATA, "scm_gsu_series.csv"), "w", newline="") as _f:
    _w = _csv.writer(_f); _w.writerow(["year", "real", "synth"])
    for y in YEARS:
        _w.writerow([y, round(float(y_gsu[yi[y]]), 4), round(float(synth[yi[y]]), 4)])

# placebo permutation (post/pre RMSPE ratio)
def ratio(target, Zmat):
    ww = synth_weights(target, Zmat); s = Zmat @ ww
    pr = np.sqrt(np.mean((target[pre_idx] - s[pre_idx]) ** 2))
    po = np.sqrt(np.mean((target[post_idx] - s[post_idx]) ** 2))
    return (po / pr, pr) if pr > 1e-6 else (np.nan, pr)
g_ratio, _ = ratio(y_gsu, Z)
rs = []
for j in range(len(DU)):
    rr, pr = ratio(donors[DU[j]], np.delete(Z, j, axis=1))
    if not np.isnan(rr): rs.append(rr)
rs = np.array(rs)
p = (np.sum(rs >= g_ratio) + 1) / (len(rs) + 1)
print(f"\nplacebo inference: GSU post/pre RMSPE ratio = {g_ratio:.2f}; "
      f"rank among {len(rs)} placebos -> p = {p:.3f}")
print("(large GSU ratio + small p would mean a real divergence; here check the SIGN of the gap)")
