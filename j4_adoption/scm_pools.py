"""
Donor-pool and specification robustness for the two headline synthetic-control cases:
  gsu_grad : Georgia State, six-year graduation rate, adoption 2012
  csu_ret  : CSU system (campus-mean), first-year retention, adoption 2018
Estimator and identification are identical to scm_all.py: a synthetic control fit to the
pre-treatment OUTCOME PATH only (convex donor weights, SLSQP), donor pools of never-treated
large public four-year institutions outside the treated state; inference by placebo
permutation on the post/pre RMSPE ratio under the standard rule (exclude placebos with
pre-RMSPE > 2x the treated unit's; placebos with pre-RMSPE of exactly 0 count as +inf,
i.e. more extreme than the treated unit -- conservative for a null result).

Variants:
  (i)   leave-one-out: drop each donor with weight > 5% (from scm_<case>_weights.csv)
  (ii)  drop suspect donors jointly (GSU pool): Temple 216339 and South Texas College
        409315 (single-year IPEDS glitches: values of 1.000/0.500 out of line with the
        surrounding series) and College of Southern Nevada (former 2-year college,
        grad rates 5-16%, an odd anchor for GSU)
  (iii) pool definition: GSU with inst_size {4,5} instead of size-5-only; CSU size-5-only
  (iv)  region: GSU excluding SREB Southern states / SREB-only; CSU excluding the West
  (v)   nearest-neighbor pre-screen K in {25, 50, 100} (mirrors screening_sensitivity.py)
  (vi)  shorter pre-window: GSU 2006-2011; CSU 2006-2017
  (vii) GSU treatment dated 2011 (EAB contract signed 2011; go-live Aug 2012), pre 2004-2010

Placebo p is computed for variants (ii), (iii), (vi), (vii); the base rows are read from
scm_summary.csv (same estimator, computed by scm_all.py). Leave-one-out, region, and
screen variants report NA for p to keep runtime sane (logged below).

Runs offline from data/raw_*.csv; the IPEDS directory is cached to data/raw_directory.csv.
Writes data/scm_pools.csv and data/scm_gsu_grad_t2011_series.csv.
"""
import os, json, urllib.request, numpy as np, pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
YEARS = list(range(2004, 2021)); yi = {y: i for i, y in enumerate(YEARS)}
SREB = {"AL", "AR", "DE", "FL", "GA", "KY", "LA", "MD", "MS", "MO",
        "NC", "OK", "SC", "TN", "TX", "VA", "WV"}          # SREB member states
WEST = {"AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NM", "NV",
        "OR", "UT", "WA", "WY"}                             # Census West region

# ---------- directory (cached) ----------
dir_path = os.path.join(DATA, "raw_directory.csv")
if not os.path.exists(dir_path):
    url = "https://educationdata.urban.org/api/v1/college-university/ipeds/directory/2021/?inst_control=1"
    rows = []
    while url:
        with urllib.request.urlopen(url, timeout=120) as r:
            d = json.load(r)
        rows += d["results"]; url = d.get("next")
    pd.DataFrame([(x["unitid"], x.get("inst_name"), x.get("state_abbr"),
                   x.get("institution_level"), x.get("inst_size")) for x in rows],
                 columns=["unitid", "inst_name", "state_abbr", "institution_level",
                          "inst_size"]).to_csv(dir_path, index=False)
dirr = pd.read_csv(dir_path)
name_of = dict(zip(dirr.unitid, dirr.inst_name))
pub4 = dirr[dirr.institution_level == 4]
size5 = dict(zip(pub4[pub4.inst_size == 5].unitid, pub4[pub4.inst_size == 5].state_abbr))
large = dict(zip(pub4[pub4.inst_size.isin([4, 5])].unitid,
                 pub4[pub4.inst_size.isin([4, 5])].state_abbr))

exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
csu_ids = set(pd.read_csv(os.path.join(DATA, "csu_staging.csv"))["unitid"].tolist())

def load(name):
    df = pd.read_csv(os.path.join(DATA, f"raw_{name}.csv"))
    return {(int(r.uid), int(r.year)): r.val for r in df.itertuples()}
grad_t, ret = load("grad_t"), load("ret")

def series(src, u):
    return np.array([src[(u, y)] for y in YEARS]) if all((u, y) in src for y in YEARS) else None

y_gsu = series(grad_t, GSU)
csu_series = np.array([np.mean([ret[(u, y)] for u in csu_ids if (u, y) in ret]) for y in YEARS])
gsu_pool = {u for u, st in size5.items() if u not in exclude and st != "GA"}
csu_pool = {u for u, st in large.items() if u not in exclude and st != "CA"}


def synth_w(target, Z, pre_idx):
    Zp, tp = Z[pre_idx], target[pre_idx]
    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    r = minimize(lambda w: float(np.sum((tp - Zp @ w) ** 2)), np.full(Z.shape[1], 1 / Z.shape[1]),
                 method="SLSQP", bounds=[(0, 1)] * Z.shape[1], constraints=cons,
                 options={"maxiter": 800, "ftol": 1e-12})
    return r.x


def run_variant(case, variant, src, treated, donor_ids, pre_years, adopt,
                screen_k=None, want_p=False, save_series=None):
    pre_idx = [yi[y] for y in pre_years]; post_idx = [yi[y] for y in YEARS if y >= adopt]
    donors = {u: s for u in donor_ids if (s := series(src, u)) is not None}
    if screen_k:
        tp = treated[pre_idx]
        donors = dict(sorted(donors.items(),
                             key=lambda kv: float(np.mean((tp - kv[1][pre_idx]) ** 2)))[:screen_k])
    DU = sorted(donors); Z = np.array([donors[u] for u in DU]).T
    w = synth_w(treated, Z, pre_idx); synth = Z @ w
    pre_rmspe = np.sqrt(np.mean((treated[pre_idx] - synth[pre_idx]) ** 2))
    norm_rmspe = pre_rmspe / treated[pre_idx].mean()
    avg_gap = (treated[post_idx] - synth[post_idx]).mean()
    p = np.nan
    if want_p:
        g_post = np.sqrt(np.mean((treated[post_idx] - synth[post_idx]) ** 2))
        g_ratio = g_post / pre_rmspe
        prs, rats = [], []
        for j in range(len(DU)):
            ww = synth_w(donors[DU[j]], np.delete(Z, j, axis=1), pre_idx)
            s = np.delete(Z, j, axis=1) @ ww
            pr = np.sqrt(np.mean((donors[DU[j]][pre_idx] - s[pre_idx]) ** 2))
            po = np.sqrt(np.mean((donors[DU[j]][post_idx] - s[post_idx]) ** 2))
            prs.append(pr); rats.append(po / pr if pr > 0 else np.inf)
        prs, rats = np.array(prs), np.array(rats)
        keep = prs <= 2 * pre_rmspe
        p = (np.sum(rats[keep] >= g_ratio) + 1) / (keep.sum() + 1)
    if save_series:
        pd.DataFrame({"year": YEARS, "real": treated, "synth": synth}).to_csv(
            os.path.join(DATA, save_series), index=False)
    print(f"{case:8s} {variant:28s} donors={len(DU):4d}  pre-RMSPE={pre_rmspe*100:5.2f}pp "
          f"(norm {norm_rmspe*100:4.2f}%)  avg post gap={avg_gap*100:+5.2f}pp  "
          f"p={'NA' if np.isnan(p) else f'{p:.3f}'}", flush=True)
    return {"case": case, "variant": variant, "n_donors": len(DU), "pre_rmspe": pre_rmspe,
            "norm_rmspe": norm_rmspe, "avg_post_gap": avg_gap, "placebo_p": p}


rows = []
# base rows: read from scm_summary.csv (computed by scm_all.py with the same estimator)
summ = pd.read_csv(os.path.join(DATA, "scm_summary.csv")).set_index("name")
for case in ["gsu_grad", "csu_ret"]:
    r = summ.loc[case]
    rows.append({"case": case, "variant": "base", "n_donors": int(r.donors),
                 "pre_rmspe": r.pre_rmspe, "norm_rmspe": r.norm_rmspe,
                 "avg_post_gap": r.avg_gap, "placebo_p": r.p})
    print(f"{case:8s} {'base (from scm_all.py)':28s} donors={int(r.donors):4d}  "
          f"pre-RMSPE={r.pre_rmspe*100:5.2f}pp (norm {r.norm_rmspe*100:4.2f}%)  "
          f"avg post gap={r.avg_gap*100:+5.2f}pp  p={r.p:.3f}", flush=True)

GSU_PRE, GSU_ADOPT = range(2004, 2012), 2012
CSU_PRE, CSU_ADOPT = range(2004, 2018), 2018

# (i) leave-one-out, weight > 5% (p = NA, logged: runtime economy)
for case, src, treated, pool, pre, adopt in [
        ("gsu_grad", grad_t, y_gsu, gsu_pool, GSU_PRE, GSU_ADOPT),
        ("csu_ret", ret, csu_series, csu_pool, CSU_PRE, CSU_ADOPT)]:
    wdf = pd.read_csv(os.path.join(DATA, f"scm_{case}_weights.csv"))
    for _, r in wdf[wdf.weight > 0.05].iterrows():
        rows.append(run_variant(case, f"loo_drop_{r['name']}", src, treated,
                                pool - {int(r.unitid)}, pre, adopt))

# (ii) drop suspect donors jointly (GSU pool); p computed
csn = int(dirr[dirr.inst_name.str.contains("College of Southern Nevada", na=False)].unitid.iloc[0])
suspects = {216339, 409315, csn}
rows.append(run_variant("gsu_grad", "drop_suspects", grad_t, y_gsu,
                        gsu_pool - suspects, GSU_PRE, GSU_ADOPT, want_p=True))

# (iii) pool definition; p computed
rows.append(run_variant("gsu_grad", "pool_size45", grad_t, y_gsu,
                        {u for u, st in large.items() if u not in exclude and st != "GA"},
                        GSU_PRE, GSU_ADOPT, want_p=True))
rows.append(run_variant("csu_ret", "pool_size5only", ret, csu_series,
                        {u for u, st in size5.items() if u not in exclude and st != "CA"},
                        CSU_PRE, CSU_ADOPT, want_p=True))

# (iv) region (p = NA, logged: runtime economy)
rows.append(run_variant("gsu_grad", "region_exSREB", grad_t, y_gsu,
                        {u for u in gsu_pool if size5[u] not in SREB}, GSU_PRE, GSU_ADOPT))
rows.append(run_variant("gsu_grad", "region_SREBonly", grad_t, y_gsu,
                        {u for u in gsu_pool if size5[u] in SREB}, GSU_PRE, GSU_ADOPT))
rows.append(run_variant("csu_ret", "region_exWest", ret, csu_series,
                        {u for u in csu_pool if large[u] not in WEST}, CSU_PRE, CSU_ADOPT))

# (v) nearest-neighbor pre-screen (p = NA, logged: runtime economy)
for k in (25, 50, 100):
    rows.append(run_variant("gsu_grad", f"screen_k{k}", grad_t, y_gsu, gsu_pool,
                            GSU_PRE, GSU_ADOPT, screen_k=k))
    rows.append(run_variant("csu_ret", f"screen_k{k}", ret, csu_series, csu_pool,
                            CSU_PRE, CSU_ADOPT, screen_k=k))

# (vi) shorter pre-window; p computed
rows.append(run_variant("gsu_grad", "prewindow_2006_2011", grad_t, y_gsu, gsu_pool,
                        range(2006, 2012), GSU_ADOPT, want_p=True))
rows.append(run_variant("csu_ret", "prewindow_2006_2017", ret, csu_series, csu_pool,
                        range(2006, 2018), CSU_ADOPT, want_p=True))

# (vii) GSU treatment dated 2011 (contract year); p computed, series saved
rows.append(run_variant("gsu_grad", "treat2011", grad_t, y_gsu, gsu_pool,
                        range(2004, 2011), 2011, want_p=True,
                        save_series="scm_gsu_grad_t2011_series.csv"))
t11 = pd.read_csv(os.path.join(DATA, "scm_gsu_grad_t2011_series.csv"))
print("\ntreat2011 gap path (pp):")
for _, r in t11[t11.year >= 2011].iterrows():
    print(f"  {int(r.year)}: {(r.real - r.synth)*100:+.2f}")

out = pd.DataFrame(rows)
out.to_csv(os.path.join(DATA, "scm_pools.csv"), index=False)
print(f"\nsaved data/scm_pools.csv ({len(out)} rows)")
