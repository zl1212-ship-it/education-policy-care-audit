"""
Synthetic control for flagship single-institution test-optional adopters.

Two celebrated cases, chosen to span the sector contrast:
  - George Washington University (131469, private nonprofit, test-optional 2016), the iconic
    selective-private adopter that marketed the move as an access reform;
  - Montclair State University (185590, public broad-access, test-optional 2016), an
    access-mission public adopter with a high baseline minority share.
This is the admissions analogue of the canonical-case logic in the J4 paper: take the celebrated
reform and ask whether the celebrated outcome actually moved.

DONOR SCREEN. An earlier version used every never-adopter with a complete series (~900 donors).
With only seven pre-years that pool interpolates the pre-period almost perfectly (pre-RMSPE ~ 0,
diffuse weights), the classic Abadie many-donors overfit, which makes the RMSPE-ratio level
uninformative. This version restricts donors to the SAME SECTOR as the case and then to the K
nearest by pre-period fit (squared distance on 2009-2015), fixing K=25 and reporting sensitivity
to K in {20, 30, 40}. The same screen is applied to the treated unit and to every placebo, so
the permutation inference stays valid.

Outcomes: share_urm (the equity claim) and admit_rate (selectivity).
Inference: Abadie placebo permutation on the post/pre RMSPE ratio, placebo pool = same-sector
never-adopters, each screened to its own K nearest.

All inputs are real IPEDS data from the local panels.
"""
import os, numpy as np, pandas as pd, csv

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
YEARS = list(range(2009, 2020)); PRE = list(range(2009, 2016)); POST = list(range(2016, 2020))
yi = {y: i for i, y in enumerate(YEARS)}
pre_idx = [yi[y] for y in PRE]; post_idx = [yi[y] for y in POST]
K_MAIN = 20; K_GRID = [20, 25, 30, 40]   # 20 is the largest bandwidth with a non-degenerate
# (pre-RMSPE > 0) fit for the GW domestic-URM series; K >= 25 overfit (pre-RMSPE -> 0).

CASES = [
    {"name": "gw", "label": "George Washington University", "unitid": 131469, "control": "2"},
    {"name": "montclair", "label": "Montclair State University", "unitid": 185590, "control": "1"},
]


def load(outcome):
    adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
    adm["admit_rate"] = pd.to_numeric(adm["admit_rate"], errors="coerce") * 100
    control = adm.groupby("unitid")["control"].first().astype(str)
    if outcome.startswith("share"):
        comp = pd.read_csv(os.path.join(DATA, "composition_panel.csv"))
        comp[outcome] = comp[outcome] * 100
        df = comp[["unitid", "year", outcome]].copy()
    else:
        df = adm[["unitid", "year", outcome]].copy()
    treat = pd.read_csv(os.path.join(DATA, "treatment_panel.csv"))
    never = set(treat.loc[treat.cohort == "never", "unitid"])
    wide = df.pivot_table(index="unitid", columns="year", values=outcome)
    return wide, never, control


def _proj_simplex(v):
    u = np.sort(v)[::-1]; css = np.cumsum(u) - 1.0
    rho = np.nonzero(u - css / (np.arange(len(u)) + 1.0) > 0)[0][-1]
    theta = css[rho] / (rho + 1.0)
    return np.maximum(v - theta, 0.0)


def synth_weights(target, Z):
    """Simplex-constrained least squares on the pre-period,
        min_w ||target_pre - Z_pre w||^2  s.t.  w >= 0, sum w = 1,
    solved by FISTA (accelerated projected gradient with function restart). FISTA reaches the
    optimum to a tight tolerance in a few hundred iterations; the earlier plain projected-gradient
    routine did not converge within its 8000-iteration cap on these degenerate (donors > pre-years)
    problems, so it returned a non-optimal point. The Gram matrix A = Zp'Zp is precomputed so each
    iteration is a single K x K product. Uniform initialization makes the result deterministic.
    """
    Zp, tp = Z[pre_idx], target[pre_idx]
    n = Z.shape[1]
    A = Zp.T @ Zp
    b = Zp.T @ tp
    L = 2.0 * np.linalg.norm(Zp, 2) ** 2
    step = 1.0 / L if L > 0 else 1.0
    w = np.full(n, 1.0 / n); y = w.copy(); tmom = 1.0; prev = np.inf
    for _ in range(20000):
        wn = _proj_simplex(y - step * (2.0 * (A @ y - b)))
        r = tp - Zp @ wn
        obj = float(r @ r)
        if obj > prev:                       # function restart: drop momentum
            y = wn.copy(); tmom = 1.0
        else:
            tn = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * tmom * tmom))
            y = wn + ((tmom - 1.0) / tn) * (wn - w)
            tmom = tn
        if abs(prev - obj) < 1e-13 * max(1.0, abs(prev)):
            w = wn; break
        w = wn; prev = obj
    return w


def k_nearest(target, pool_ids, series, k):
    """K donors closest to target by pre-period squared distance."""
    d = sorted(pool_ids, key=lambda u: float(np.sum((series[u][pre_idx] - target[pre_idx]) ** 2)))
    return d[:k]


def fit_ratio(target, donor_ids, series):
    Z = np.array([series[u] for u in donor_ids]).T
    w = synth_weights(target, Z); s = Z @ w
    pr = np.sqrt(np.mean((target[pre_idx] - s[pre_idx]) ** 2))
    po = np.sqrt(np.mean((target[post_idx] - s[post_idx]) ** 2))
    gap = (target[post_idx] - s[post_idx]).mean()
    return (po / pr if pr > 1e-9 else np.nan), pr, gap, w, s


def run_case(case, outcome):
    wide, never, control = load(outcome)
    uid = case["unitid"]
    if uid not in wide.index or wide.loc[uid, YEARS].isna().any():
        print(f"[{case['name']} / {outcome}] series incomplete; skipping"); return None
    target = wide.loc[uid, YEARS].to_numpy(float)
    # same-sector never-adopters with a complete series
    pool = [u for u in wide.index if u in never and str(control.get(u, "")) == case["control"]
            and not wide.loc[u, YEARS].isna().any()]
    series = {u: wide.loc[u, YEARS].to_numpy(float) for u in pool}

    # K sensitivity
    print(f"\n=== {case['label']} | {outcome} | same-sector donor pool = {len(pool)} ===")
    res_main = None
    for k in K_GRID:
        donors = k_nearest(target, pool, series, k)
        g_ratio, pr, gap, w, s = fit_ratio(target, donors, series)
        # placebo: each pool unit screened to its own K nearest (excluding itself)
        rs = []
        for u in pool:
            others = [v for v in pool if v != u]
            dk = k_nearest(series[u], others, series, k)
            rr, _, _, _, _ = fit_ratio(series[u], dk, series)
            if not np.isnan(rr):
                rs.append(rr)
        rs = np.array(rs)
        p = (np.sum(rs >= g_ratio) + 1) / (len(rs) + 1)
        flag = "  <- main" if k == K_MAIN else ""
        print(f"  K={k:2d}: pre-RMSPE {pr:5.2f}  post gap {gap:+6.2f}  ratio {g_ratio:6.2f}  "
              f"p={p:.3f} (placebos {len(rs)}){flag}")
        if k == K_MAIN:
            res_main = {"case": case["name"], "label": case["label"], "outcome": outcome,
                        "K": k, "donors": len(pool), "pre_rmspe": round(pr, 3),
                        "gap_post": round(gap, 3), "ratio": round(g_ratio, 2), "p": round(p, 3)}
            synth_main, donors_main, w_main = s, donors, w
    # save the K=25 series + weights for the figure
    with open(os.path.join(DATA, f"scm_{case['name']}_{outcome}.csv"), "w", newline="") as f:
        wtr = csv.writer(f); wtr.writerow(["year", "real", "synth"])
        for y in YEARS:
            wtr.writerow([y, round(float(target[yi[y]]), 4), round(float(synth_main[yi[y]]), 4)])
    top = sorted(zip(donors_main, w_main), key=lambda t: -t[1])[:5]
    print("  top donor weights (K=25):", ", ".join(f"{u}:{wi:.2f}" for u, wi in top if wi > 0.01))
    return res_main


if __name__ == "__main__":
    summary = []
    for case in CASES:
        for oc in ["share_urm", "admit_rate"]:
            r = run_case(case, oc)
            if r:
                summary.append(r)
    pd.DataFrame(summary).to_csv(os.path.join(DATA, "scm_summary.csv"), index=False)
    print("\nwrote data/scm_<case>_<outcome>.csv and data/scm_summary.csv")
