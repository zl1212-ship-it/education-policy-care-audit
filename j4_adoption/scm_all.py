"""
Consolidated synthetic-control diagnostics for the revision. Runs four cases and saves,
for each, the treated/synthetic series, the full placebo gap matrix (for a spaghetti plot),
donor count, top donor weights, the MSPE-ratio placebo distribution, and the permutation
p-value. Cases:
  gsu_grad  : Georgia State, six-year graduation rate (overall)        [main result]
  gsu_black : Georgia State, six-year graduation rate, Black students  [equity test, Major 4]
  gsu_ret   : Georgia State, first-year retention (outcome calibration, Major 6)
  csu_ret   : California State University system, first-year retention  [main result]
All inputs are real IPEDS data via the Urban Institute Education Data API.
"""
import os, json, urllib.request, numpy as np, pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
YEARS = list(range(2004, 2021))
yi = {y: i for i, y in enumerate(YEARS)}


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


# universe: large public 4-year, exclude known adopters
dirr = pull(f"{BASE}/directory/2021/?inst_control=1")
# Two donor pools: size==5 (largest) for single-institution GSU cases to avoid the
# overfitting a very large pool produces; size in {4,5} for the CSU system aggregate.
large = {x["unitid"]: x.get("state_abbr") for x in dirr
         if x.get("institution_level") == 4 and x.get("inst_size") in (4, 5)}
size5 = {x["unitid"]: x.get("state_abbr") for x in dirr
         if x.get("institution_level") == 4 and x.get("inst_size") == 5}
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
csu_ids = set(pd.read_csv(os.path.join(DATA, "csu_staging.csv"))["unitid"].tolist())

def cache(name, puller):
    p = os.path.join(DATA, f"raw_{name}.csv")
    if os.path.exists(p):
        df = pd.read_csv(p); return {(int(r.uid), int(r.year)): r.val for r in df.itertuples()}
    d = puller(); pd.DataFrame([(u, y, v) for (u, y), v in d.items()],
                               columns=["uid", "year", "val"]).to_csv(p, index=False)
    return d


print("pulling/caching grad-rates (overall, Black) and retention ...", flush=True)
def _pull_gt():
    d = {}
    for y in YEARS:
        for x in pull(f"{BASE}/grad-rates/{y}/?race=99&sex=99"):
            v = x.get("completion_rate_150pct")
            if v is not None: d[(x["unitid"], y)] = v
        print(f"  gt {y}", flush=True)
    return d
def _pull_gb():
    d = {}
    for y in YEARS:
        for x in pull(f"{BASE}/grad-rates/{y}/?race=2&sex=99"):
            v = x.get("completion_rate_150pct")
            if v is not None: d[(x["unitid"], y)] = v
        print(f"  gb {y}", flush=True)
    return d
def _pull_ret():
    d = {}
    for y in YEARS:
        for x in pull(f"{BASE}/fall-retention/{y}/?ftpt=1"):
            if x.get("retention_rate") is not None: d[(x["unitid"], y)] = x["retention_rate"]
        print(f"  ret {y}", flush=True)
    return d
grad_t = cache("grad_t", _pull_gt)
grad_b = cache("grad_b", _pull_gb)
ret = cache("ret", _pull_ret)


def series(src, uid):
    return np.array([src[(uid, y)] for y in YEARS]) if all((uid, y) in src for y in YEARS) else None


def synth_w(target, Z, pre_idx):
    Zp, tp = Z[pre_idx], target[pre_idx]
    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    r = minimize(lambda w: float(np.sum((tp - Zp @ w) ** 2)), np.full(Z.shape[1], 1 / Z.shape[1]),
                 method="SLSQP", bounds=[(0, 1)] * Z.shape[1], constraints=cons,
                 options={"maxiter": 800, "ftol": 1e-12})
    return r.x


def run_case(name, src, treated_series, donor_ids, exclude_state, pre_years, adopt, screen_k=None):
    pre_idx = [yi[y] for y in pre_years]; post_idx = [yi[y] for y in YEARS if y >= adopt]
    donors = {u: s for u in donor_ids if (s := series(src, u)) is not None}
    if screen_k:  # pre-screen to the K donors closest to the treated unit's pre-period path,
        # which avoids the perfect interpolation a large donor pool can produce (overfitting).
        tp = treated_series[pre_idx]
        donors = dict(sorted(donors.items(),
                             key=lambda kv: float(np.mean((tp - kv[1][pre_idx]) ** 2)))[:screen_k])
    DU = sorted(donors); Z = np.array([donors[u] for u in DU]).T
    w = synth_w(treated_series, Z, pre_idx); synth = Z @ w
    pre_rmspe = np.sqrt(np.mean((treated_series[pre_idx] - synth[pre_idx]) ** 2))
    avg_gap = (treated_series[post_idx] - synth[post_idx]).mean()

    def ratio(t, Zm):
        ww = synth_w(t, Zm, pre_idx); s = Zm @ ww
        pr = np.sqrt(np.mean((t[pre_idx] - s[pre_idx]) ** 2))
        po = np.sqrt(np.mean((t[post_idx] - s[post_idx]) ** 2))
        return (po / pr if pr > 1e-6 else np.nan), (t - s)
    g_ratio, t_gap = ratio(treated_series, Z)
    ratios, placebo_gaps = [], {}
    for j, u in enumerate(DU):
        rr, gap = ratio(donors[u], np.delete(Z, j, axis=1))
        if not np.isnan(rr): ratios.append(rr); placebo_gaps[u] = gap
    ratios = np.array(ratios)
    p = (np.sum(ratios >= g_ratio) + 1) / (len(ratios) + 1)
    # save series + placebo gaps
    pd.DataFrame({"year": YEARS, "real": treated_series, "synth": synth}).to_csv(
        os.path.join(DATA, f"scm_{name}_series.csv"), index=False)
    pg = pd.DataFrame({"year": YEARS, "treated": t_gap})
    for u, gap in placebo_gaps.items(): pg[f"p{u}"] = gap
    pg.to_csv(os.path.join(DATA, f"scm_{name}_placebo.csv"), index=False)
    pd.DataFrame({"ratio": ratios}).to_csv(os.path.join(DATA, f"scm_{name}_ratios.csv"), index=False)
    top = sorted(zip(DU, w), key=lambda t: -t[1])[:5]
    print(f"\n=== {name} === donors={len(DU)}  pre-RMSPE={pre_rmspe*100:.2f}pp  "
          f"avg post gap={avg_gap*100:+.2f}pp  ratio={g_ratio:.2f}  placebo p={p:.3f}")
    print("   top weights:", [(u, round(wi, 2)) for u, wi in top if wi > 0.02])
    return {"name": name, "donors": len(DU), "pre_rmspe": pre_rmspe, "avg_gap": avg_gap,
            "ratio": g_ratio, "p": p}


res = []
# GSU cases: donors = large public non-GA
gsu_donors = {u for u, st in size5.items() if u not in exclude and st != "GA"}
yg = series(grad_t, GSU); yb = series(grad_b, GSU); yr = series(ret, GSU)
res.append(run_case("gsu_grad", grad_t, yg, gsu_donors, "GA", range(2004, 2012), 2012))
res.append(run_case("gsu_black", grad_b, yb, gsu_donors, "GA", range(2004, 2012), 2012, screen_k=25))
res.append(run_case("gsu_ret", ret, yr, gsu_donors, "GA", range(2004, 2012), 2012, screen_k=25))
# CSU: treated = mean retention across CSU campuses; donors non-CA
csu_series = np.array([np.mean([ret[(u, y)] for u in csu_ids if (u, y) in ret]) for y in YEARS])
csu_donors = {u for u, st in large.items() if u not in exclude and st != "CA"}
res.append(run_case("csu_ret", ret, csu_series, csu_donors, "CA", range(2004, 2018), 2018))

# equity timeline (Black grad rate, raw)
print("\n=== GSU Black grad rate timeline ===")
print(f"  2004={yb[yi[2004]]*100:.1f}  2012={yb[yi[2012]]*100:.1f}  2019={yb[yi[2019]]*100:.1f}")
print(f"  pre 2004->2012: {(yb[yi[2012]]-yb[yi[2004]])*100:+.1f}pp   post 2012->2019: {(yb[yi[2019]]-yb[yi[2012]])*100:+.1f}pp")
pd.DataFrame(res).to_csv(os.path.join(DATA, "scm_summary.csv"), index=False)
print("\nsaved series, placebo, ratios, summary to data/")
