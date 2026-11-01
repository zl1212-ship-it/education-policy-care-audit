"""
Synthetic control for the California State University (CSU) system on first-year retention:
(a) a variant that drops the four campuses with undated pre-2018 EAB use from the treated
aggregate, on the original 2004-2020 window; (b) the base and drop-four versions on a window
extended to 2024 with the 2021-2024 IPEDS releases.

Estimator. Identical to the csu_ret case of scm_all.py: convex donor weights (non-negative,
summing to one) chosen by SLSQP to match the treated unit's pre-period outcome path
(2004-2017), no covariates; placebo-in-space permutation with three exclusion rules
(primary: drop placebos whose pre-RMSPE exceeds twice the treated unit's, perfect
interpolators kept as +inf ratios; drop-well-fit: drop placebos with pre-RMSPE below 1e-6;
no exclusion).

Treated unit. The unweighted mean of first-year retention across the CSU campuses in
data/csu_staging.csv, as in scm_all.py: all 23 campuses, or the 19 campuses left after
removing Fullerton (110565), Long Beach (110583), Los Angeles (110592) and San Bernardino
(110510), whose EAB use predates the 2018 system rollout on undated contracts.

Exposure. Retention year Y is the fall-Y re-enrollment of the cohort that entered in fall
Y-1. Retention year 2018 is the fall 2017 entrants, whose first year overlapped the 2018
rollout only in part; 2019 onward are cohorts that entered after the rollout began.

Donor pool. Public four-year institutions in IPEDS size categories 4-5 outside California
that never appear in treatment_panel.csv or csu_staging.csv, with a complete retention
series over the window. For the extended window the seven University of Maine System
campuses are also removed, because some of them used the platform by January 2021 without a
datable adoption. Retention values below zero in the 2021-2024 releases are IPEDS missing
codes and are treated as missing.

Identification. The synthetic CSU is assumed to track what CSU retention would have been
without the rollout, conditional on the 2004-2017 match. The extended window adds pandemic
years (fall 2020 to fall 2022) and possible undated later adopters among the donors, so the
extended estimates are descriptive checks, not a stronger test.

Outputs: data/scm_csu_ret_ext_summary.csv (one row per variant), data/scm_csu_ret_ext_series.csv,
and per-variant weights and ratios files. Usage: python3 scm_csu_ret_ext.py [variant ...]
with variants among orig_all23, orig_drop4, ext_all23, ext_drop4 (default: all four).
"""
import os, sys
import numpy as np, pandas as pd
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
EARLY4 = {110565, 110583, 110592, 110510}
MAINE = {161217, 161226, 161235, 161244, 161253, 161341, 161554}
PRE_YEARS = list(range(2004, 2018))
ADOPT = 2018


def load_ret():
    d = {}
    for f in ("raw_ret.csv", "raw_ret_ext.csv"):
        df = pd.read_csv(os.path.join(DATA, f))
        for r in df.itertuples():
            v = float(r.val)
            if v >= 0:
                d[(int(r.uid), int(r.year))] = v
    return d


ret = load_ret()
dirr = pd.read_csv(os.path.join(DATA, "raw_directory.csv"))
inst_name = dict(zip(dirr.unitid, dirr.inst_name)); inst_state = dict(zip(dirr.unitid, dirr.state_abbr))
pub4 = dirr[dirr.institution_level == 4]
large = dict(zip(pub4[pub4.inst_size.isin([4, 5])].unitid, pub4[pub4.inst_size.isin([4, 5])].state_abbr))
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
csu_ids = sorted(set(pd.read_csv(os.path.join(DATA, "csu_staging.csv"))["unitid"].tolist()))
assert len(csu_ids) == 23


def synth_w(target, Z, pre_idx):
    Zp, tp = Z[pre_idx], target[pre_idx]
    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    r = minimize(lambda w: float(np.sum((tp - Zp @ w) ** 2)), np.full(Z.shape[1], 1 / Z.shape[1]),
                 method="SLSQP", bounds=[(0, 1)] * Z.shape[1], constraints=cons,
                 options={"maxiter": 800, "ftol": 1e-12})
    return r.x


def run(variant):
    window = 2020 if variant.startswith("orig") else 2024
    years = list(range(2004, window + 1)); yi = {y: i for i, y in enumerate(years)}
    ids = csu_ids if variant.endswith("all23") else [u for u in csu_ids if u not in EARLY4]
    treated, n_present = [], []
    for y in years:
        vals = [ret[(u, y)] for u in ids if (u, y) in ret]
        treated.append(np.mean(vals)); n_present.append(len(vals))
    treated = np.array(treated)
    drop = set(MAINE) if window == 2024 else set()
    donors = {}
    for u, st in large.items():
        if u in exclude or u in drop or st == "CA":
            continue
        if all((u, y) in ret for y in years):
            donors[u] = np.array([ret[(u, y)] for y in years])
    pre_idx = [yi[y] for y in PRE_YEARS]; post_idx = [yi[y] for y in years if y >= ADOPT]
    full_idx = [yi[y] for y in years if y >= ADOPT + 1]
    DU = sorted(donors); Z = np.array([donors[u] for u in DU]).T
    w = synth_w(treated, Z, pre_idx); synth = Z @ w
    gap = treated - synth
    pre_rmspe = np.sqrt(np.mean(gap[pre_idx] ** 2))

    def fit(t, Zm):
        ww = synth_w(t, Zm, pre_idx); s = Zm @ ww
        pr = np.sqrt(np.mean((t[pre_idx] - s[pre_idx]) ** 2))
        po = np.sqrt(np.mean((t[post_idx] - s[post_idx]) ** 2))
        return pr, po
    g_pre, g_post = fit(treated, Z); g_ratio = g_post / g_pre
    prs, pos = [], []
    for j, u in enumerate(DU):
        pr, po = fit(donors[u], np.delete(Z, j, axis=1)); prs.append(pr); pos.append(po)
    prs = np.array(prs); pos = np.array(pos)
    ratios = np.full(len(prs), np.inf); nz = prs > 0; ratios[nz] = pos[nz] / prs[nz]

    def perm_p(mask):
        r = ratios[mask]
        return (np.sum(r >= g_ratio) + 1) / (len(r) + 1)
    m_std = prs <= 2 * pre_rmspe; m_dwf = prs > 1e-6
    row = {"variant": variant, "window": f"2004-{window}", "n_treated_campuses": len(ids),
           "min_campuses_present": int(min(n_present)), "donors": len(DU),
           "pre_rmspe": pre_rmspe, "norm_rmspe": pre_rmspe / treated[pre_idx].mean(),
           "avg_gap_post": gap[post_idx].mean(), "avg_gap_full_exposure": gap[full_idx].mean(),
           "ratio": g_ratio, "p": perm_p(m_std), "n_p": int(m_std.sum()),
           "p_dropwellfit": perm_p(m_dwf), "p_all": perm_p(np.ones(len(prs), bool))}
    for y in years:
        if y >= ADOPT:
            row[f"gap_{y}"] = gap[yi[y]]
    pd.DataFrame({"unitid": DU, "pre_rmspe": prs, "post_rmspe": pos, "ratio": ratios}) \
        .to_csv(os.path.join(DATA, f"scm_csu_ret_ext_{variant}_ratios.csv"), index=False)
    wdf = pd.DataFrame({"unitid": DU, "name": [inst_name.get(u) for u in DU],
                        "state": [inst_state.get(u) for u in DU], "weight": w})
    wdf[wdf.weight > 1e-4].sort_values("weight", ascending=False) \
        .to_csv(os.path.join(DATA, f"scm_csu_ret_ext_{variant}_weights.csv"), index=False)
    pd.DataFrame({"year": years, "real": treated, "synth": synth, "gap": gap, "campuses": n_present}) \
        .to_csv(os.path.join(DATA, f"scm_csu_ret_ext_{variant}_series.csv"), index=False)
    print(f"=== {variant}: donors {len(DU)}, pre-RMSPE {pre_rmspe*100:.2f} pp, "
          f"avg post gap {row['avg_gap_post']*100:+.2f} pp, p {row['p']:.3f} / {row['p_dropwellfit']:.3f} / "
          f"{row['p_all']:.3f}", flush=True)
    return row


if __name__ == "__main__":
    variants = sys.argv[1:] or ["orig_all23", "orig_drop4", "ext_all23", "ext_drop4"]
    rows = [run(v) for v in variants]
    out = os.path.join(DATA, "scm_csu_ret_ext_summary.csv")
    old = pd.read_csv(out) if os.path.exists(out) else pd.DataFrame()
    if len(old):
        old = old[~old.variant.isin(variants)]
    pd.concat([old, pd.DataFrame(rows)], ignore_index=True).sort_values("variant") \
        .to_csv(out, index=False)
    print("saved", out)
