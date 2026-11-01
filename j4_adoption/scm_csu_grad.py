"""
Synthetic control for the California State University (CSU) system on the SIX-YEAR
GRADUATION RATE, a supplementary case that extends the scm_all.py design to the
completion outcome now that the first fully exposed CSU cohort is observable.

Estimator. Abadie, Diamond and Hainmueller (2010) synthetic control: convex donor
weights (non-negative, summing to one) chosen by SLSQP to minimize the squared
distance between the treated unit's PRE-PERIOD outcome path and the weighted donor
path, with no covariates (identical to synth_w in scm_all.py). Inference is the
permutation (placebo-in-space) test: every donor is treated in turn, the post/pre
RMSPE ratio is computed for each, and the p-value is the share of placebo ratios at
least as large as the treated unit's. Three exclusion rules are reported, as in
scm_all.py: p [PRIMARY] drops placebos whose pre-RMSPE exceeds 2x the treated unit's
and keeps perfect interpolators as +inf ratios; p_dropwellfit drops placebos with
pre-RMSPE < 1e-6 (legacy); p_all applies no exclusion.

Identification. The synthetic CSU is assumed to track what CSU completion would have
been without the 2018 system-wide EAB Navigate rollout, conditional on the 2004-2017
pre-period match (no covariate balance is imposed). Two features limit the causal
reading and are the reason this case is reported as descriptive in the supplement:
(1) only one post observation, the 2023 label (fall 2018 entrants), is a fully exposed
cohort; labels 2018-2022 are cohorts that entered in fall 2013-2017 and met Navigate
part-way through their studies; (2) four CSU campuses (Fullerton 110565, Long Beach
110583, Los Angeles 110592, San Bernardino 110510) used EAB before 2018 on undated
contracts, so the treated pre-period is partly contaminated; a variant drops them from
the treated aggregate. The 2023 cohort also spent its third to fifth years in the
pandemic, and the CSU Graduation Initiative 2025 (announced 2015-2016) bundles many
completion interventions with the Navigate rollout.

Outcome. Bachelor's-subcohort (subcohort=2) 150%-of-normal-time completion rate for
full-time, first-time students, race=99 and sex=99, computed from counts as
completers_150pct / cohort_adj_150pct (the published rate is rounded to whole
percents). Urban Institute Education Data Portal "year" label t = entering cohort t-5,
status as of August 31 of t+1. The PRIMARY treated series is the POOLED rate across the
23 campuses in data/csu_staging.csv (sum of completers over sum of adjusted cohort,
i.e. cohort-weighted); the simple campus mean is reported as a secondary series because
scm_all.py's csu_ret case uses a campus mean for retention.

Donor pool. Public four-year institutions (directory year 2021, inst_control=1,
institution_level=4) with inst_size in (4, 5), outside California, never in
data/treatment_panel.csv or data/csu_staging.csv, with a complete 2004-2023 series.

Data. Grad-rates for every year 2004-2023 are pulled once and cached to NEW files
data/raw_grad_counts_ext.csv (uid, year, cohort_year, completers, cohort) and
data/raw_grad_t_ext.csv (uid, year, val); the existing data/raw_grad_t.csv (2004-2020)
is read only for a consistency check and is never modified. The IPEDS directory is
read from data/raw_directory.csv (pulled if absent).

Outputs. data/scm_csu_grad_series.csv, data/scm_csu_grad_placebo.csv,
data/scm_csu_grad_ratios.csv, data/scm_csu_grad_weights.csv (primary variant),
variant files with a _<variant> suffix, data/scm_csu_grad_summary.csv (one row per
variant), data/scm_csu_grad_campus_coverage.csv, and the figure
j4_supp_csu_grad.png/.pdf in the pipeline directory. Run from this directory with
python3 scm_csu_grad.py; the run is deterministic given the cached pulls.
"""
import os, json, urllib.request, numpy as np, pandas as pd
from scipy.optimize import minimize
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
YEARS = list(range(2004, 2024))          # own window; scm_all.py keeps 2004-2020
yi = {y: i for i, y in enumerate(YEARS)}
PRE_YEARS = list(range(2004, 2018))      # entering cohorts 1999-2012
ADOPT = 2018                             # first label whose cohort was in school at rollout
FULL_EXPOSURE = 2023                     # fall 2018 entrants
EARLY4 = {110565, 110583, 110592, 110510}


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


# ===== directory (cached by scm_pools.py; pulled only if absent) =====
dir_path = os.path.join(DATA, "raw_directory.csv")
if not os.path.exists(dir_path):
    rows = pull(f"{BASE}/directory/2021/?inst_control=1")
    pd.DataFrame([(x["unitid"], x.get("inst_name"), x.get("state_abbr"),
                   x.get("institution_level"), x.get("inst_size")) for x in rows],
                 columns=["unitid", "inst_name", "state_abbr", "institution_level",
                          "inst_size"]).to_csv(dir_path, index=False)
dirr = pd.read_csv(dir_path)
inst_name = dict(zip(dirr.unitid, dirr.inst_name)); inst_state = dict(zip(dirr.unitid, dirr.state_abbr))
pub4 = dirr[dirr.institution_level == 4]
large = dict(zip(pub4[pub4.inst_size.isin([4, 5])].unitid, pub4[pub4.inst_size.isin([4, 5])].state_abbr))
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
csu = pd.read_csv(os.path.join(DATA, "csu_staging.csv"))
csu_ids = sorted(set(csu["unitid"].tolist())); csu_name = dict(zip(csu.unitid, csu.institution))
assert len(csu_ids) == 23, len(csu_ids)


# ===== grad-rate counts 2004-2023, cached incrementally per year =====
def load_grad_counts(years):
    """Return a DataFrame (uid, year, cohort_year, completers, cohort, val) for the
    requested years, pulling and appending any year missing from the cache so that an
    interrupted run loses at most one year."""
    cpath = os.path.join(DATA, "raw_grad_counts_ext.csv"); vpath = os.path.join(DATA, "raw_grad_t_ext.csv")
    cols = ["uid", "year", "cohort_year", "completers", "cohort"]
    have = pd.read_csv(cpath) if os.path.exists(cpath) else pd.DataFrame(columns=cols)
    done = set(have.year.astype(int).tolist()) if len(have) else set()
    for y in years:
        if y in done: continue
        rows = []
        for x in pull(f"{BASE}/grad-rates/{y}/?race=99&sex=99&subcohort=2"):
            c, n = x.get("completers_150pct"), x.get("cohort_adj_150pct")
            if c is not None and n is not None and c >= 0 and n > 0:
                rows.append((x["unitid"], y, x.get("cohort_year"), c, n))
        new = pd.DataFrame(rows, columns=cols)
        have = pd.concat([have, new], ignore_index=True)
        have.sort_values(["year", "uid"]).to_csv(cpath, index=False)
        print(f"  pulled grad-rates {y}: {len(new)} rows (cached)", flush=True)
    have = have.astype({"uid": int, "year": int, "completers": float, "cohort": float})
    have["val"] = have.completers / have.cohort
    have[["uid", "year", "val"]].sort_values(["year", "uid"]).to_csv(vpath, index=False)
    return have[have.year.isin(years)]


print("loading grad-rate counts 2004-2023 ...", flush=True)
gc = load_grad_counts(YEARS)
grad = {(int(r.uid), int(r.year)): r.val for r in gc.itertuples()}
counts = {(int(r.uid), int(r.year)): (r.completers, r.cohort) for r in gc.itertuples()}

# consistency check against the cache the paper's main results were built from
old = pd.read_csv(os.path.join(DATA, "raw_grad_t.csv"))
oldd = {(int(r.uid), int(r.year)): r.val for r in old.itertuples()}
common = [k for k in oldd if k in grad]
maxdiff = max(abs(oldd[k] - grad[k]) for k in common) if common else float("nan")
print(f"  overlap with raw_grad_t.csv (2004-2020): {len(common)} of {len(oldd)} cached keys matched, "
      f"{len(oldd) - len(common)} old keys absent in new pull, max |diff| = {maxdiff:.2e}", flush=True)


# ===== treated series: CSU system, pooled and campus mean =====
def csu_aggregate(ids):
    pooled, mean, cov = [], [], []
    for y in YEARS:
        present = [u for u in ids if (u, y) in counts]
        c = sum(counts[(u, y)][0] for u in present); n = sum(counts[(u, y)][1] for u in present)
        pooled.append(c / n); mean.append(np.mean([grad[(u, y)] for u in present]))
        cov.append((y, len(present), ";".join(str(u) for u in ids if u not in present)))
    return np.array(pooled), np.array(mean), cov


real_pooled, real_mean, coverage = csu_aggregate(csu_ids)
no_early = [u for u in csu_ids if u not in EARLY4]
real_pooled_d4, real_mean_d4, _ = csu_aggregate(no_early)
covdf = pd.DataFrame(coverage, columns=["year", "n_campuses_present", "missing_unitids"])
covdf.to_csv(os.path.join(DATA, "scm_csu_grad_campus_coverage.csv"), index=False)
print("campus coverage by year:", {int(y): int(n) for y, n, _ in coverage})
print("years with fewer than 23 campuses:",
      [(int(y), m) for y, n, m in coverage if n < 23] or "none")


def series(src, uid):
    return np.array([src[(uid, y)] for y in YEARS]) if all((uid, y) in src for y in YEARS) else None


def synth_w(target, Z, pre_idx):
    Zp, tp = Z[pre_idx], target[pre_idx]
    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    r = minimize(lambda w: float(np.sum((tp - Zp @ w) ** 2)), np.full(Z.shape[1], 1 / Z.shape[1]),
                 method="SLSQP", bounds=[(0, 1)] * Z.shape[1], constraints=cons,
                 options={"maxiter": 800, "ftol": 1e-12})
    return r.x


def exposure(y):
    if y < ADOPT: return "pre"
    return "full" if y >= FULL_EXPOSURE else "partial"


def run_case(variant, treated_series, donors, suffix):
    pre_idx = [yi[y] for y in PRE_YEARS]; post_idx = [yi[y] for y in YEARS if y >= ADOPT]
    partial_idx = [yi[y] for y in YEARS if ADOPT <= y < FULL_EXPOSURE]
    DU = sorted(donors); Z = np.array([donors[u] for u in DU]).T
    w = synth_w(treated_series, Z, pre_idx); synth = Z @ w
    pre_rmspe = np.sqrt(np.mean((treated_series[pre_idx] - synth[pre_idx]) ** 2))
    norm_rmspe = pre_rmspe / treated_series[pre_idx].mean()
    gap = treated_series - synth

    def fit(t, Zm):
        ww = synth_w(t, Zm, pre_idx); s = Zm @ ww
        pr = np.sqrt(np.mean((t[pre_idx] - s[pre_idx]) ** 2))
        po = np.sqrt(np.mean((t[post_idx] - s[post_idx]) ** 2))
        return pr, po, (t - s)
    g_pre, g_post, t_gap = fit(treated_series, Z)
    g_ratio = g_post / g_pre
    prs, pos, placebo_gaps = [], [], {}
    for j, u in enumerate(DU):
        pr, po, g = fit(donors[u], np.delete(Z, j, axis=1))
        prs.append(pr); pos.append(po); placebo_gaps[u] = g
    prs = np.array(prs); pos = np.array(pos)
    ratios = np.full(len(prs), np.inf); nz = prs > 0; ratios[nz] = pos[nz] / prs[nz]

    def perm_p(mask):
        r = ratios[mask]
        return (np.sum(r >= g_ratio) + 1) / (len(r) + 1)
    m_std = prs <= 2 * pre_rmspe; m_dwf = prs > 1e-6; m_all = np.ones(len(prs), bool)
    p_std, p_dwf, p_all = perm_p(m_std), perm_p(m_dwf), perm_p(m_all)
    # rank of the 2023 (single fully exposed point) gap among placebo gaps in that year
    g23 = t_gap[yi[FULL_EXPOSURE]]
    pg23 = np.array([placebo_gaps[u][yi[FULL_EXPOSURE]] for u in DU])
    share_abs_ge_2023 = (np.sum(np.abs(pg23) >= abs(g23)) + 1) / (len(pg23) + 1)

    pg = pd.DataFrame({"year": YEARS, "treated": t_gap, **{f"p{u}": g for u, g in placebo_gaps.items()}})
    pg.to_csv(os.path.join(DATA, f"scm_csu_grad{suffix}_placebo.csv"), index=False)
    pd.DataFrame({"unitid": DU, "pre_rmspe": prs, "post_rmspe": pos, "ratio": ratios}) \
        .to_csv(os.path.join(DATA, f"scm_csu_grad{suffix}_ratios.csv"), index=False)
    wdf = pd.DataFrame({"unitid": DU, "name": [inst_name.get(u) for u in DU],
                        "state": [inst_state.get(u) for u in DU], "weight": w})
    wdf[wdf.weight > 1e-4].sort_values("weight", ascending=False) \
        .to_csv(os.path.join(DATA, f"scm_csu_grad{suffix}_weights.csv"), index=False)
    top = sorted(zip(DU, w), key=lambda t: -t[1])[:6]
    print(f"\n=== csu_grad [{variant}] === donors={len(DU)}  pre-RMSPE={pre_rmspe*100:.2f}pp "
          f"(normalized {norm_rmspe*100:.2f}%)  ratio={g_ratio:.2f}")
    print("   post gaps (pp):", {y: round(gap[yi[y]] * 100, 2) for y in YEARS if y >= ADOPT})
    print(f"   avg gap 2018-2022 (partial) = {gap[partial_idx].mean()*100:+.2f}pp   "
          f"2023 gap (full exposure) = {gap[yi[FULL_EXPOSURE]]*100:+.2f}pp   "
          f"avg gap 2018-2023 = {gap[post_idx].mean()*100:+.2f}pp")
    print(f"   placebo p: standard(primary)={p_std:.3f} [n={int(m_std.sum())}]  "
          f"legacy-dropwellfit={p_dwf:.3f} [n={int(m_dwf.sum())}]  all={p_all:.3f} [n={len(prs)}]  "
          f"share of placebo |gap2023| >= treated = {share_abs_ge_2023:.3f}")
    print("   top weights:", [(u, inst_name.get(u), round(wi, 3)) for u, wi in top if wi > 0.01])
    row = {"variant": variant, "donors": len(DU), "n_weights_gt_1e4": int((w > 1e-4).sum()),
           "pre_rmspe": pre_rmspe, "norm_rmspe": norm_rmspe,
           "avg_gap_2018_2022_partial": gap[partial_idx].mean(), "gap_2023_full": gap[yi[FULL_EXPOSURE]],
           "avg_gap_2018_2023": gap[post_idx].mean(), "ratio": g_ratio,
           "p": p_std, "n_p": int(m_std.sum()), "p_dropwellfit": p_dwf, "n_dropwellfit": int(m_dwf.sum()),
           "p_all": p_all, "n_all": len(prs), "share_placebo_absgap2023_ge_treated": share_abs_ge_2023,
           "real_2017": treated_series[yi[2017]], "real_2023": treated_series[yi[FULL_EXPOSURE]],
           "synth_2023": synth[yi[FULL_EXPOSURE]]}
    for y in YEARS:
        if y >= ADOPT: row[f"gap_{y}"] = gap[yi[y]]
    return row, synth


# donor pool: large public four-year outside CA, never treated, complete 2004-2023
donors = {u: s for u, st in large.items() if u not in exclude and st != "CA"
          and (s := series(grad, u)) is not None}
n_cand = sum(1 for u, st in large.items() if u not in exclude and st != "CA")
print(f"\ndonor pool: {len(donors)} with complete 2004-2023 series out of {n_cand} eligible non-CA large publics")

res, synths = [], {}
for variant, t, suffix in [("pooled", real_pooled, ""), ("mean", real_mean, "_mean"),
                           ("pooled_drop_early4", real_pooled_d4, "_pooled_drop_early4"),
                           ("mean_drop_early4", real_mean_d4, "_mean_drop_early4")]:
    row, s = run_case(variant, t, donors, suffix); res.append(row); synths[variant] = s

pd.DataFrame({"year": YEARS, "cohort_year": [y - 5 for y in YEARS], "exposure": [exposure(y) for y in YEARS],
              "real_pooled": real_pooled, "real_mean": real_mean, "synth": synths["pooled"],
              "gap_pooled": real_pooled - synths["pooled"], "synth_mean": synths["mean"],
              "real_pooled_drop_early4": real_pooled_d4, "synth_pooled_drop_early4": synths["pooled_drop_early4"],
              "real_mean_drop_early4": real_mean_d4, "synth_mean_drop_early4": synths["mean_drop_early4"]}) \
    .to_csv(os.path.join(DATA, "scm_csu_grad_series.csv"), index=False)
pd.DataFrame(res).to_csv(os.path.join(DATA, "scm_csu_grad_summary.csv"), index=False)
print(f"\nCSU pooled rate: 2004 {real_pooled[yi[2004]]*100:.1f}  2012 {real_pooled[yi[2012]]*100:.1f}  "
      f"2017 {real_pooled[yi[2017]]*100:.1f}  2022 {real_pooled[yi[2022]]*100:.1f}  2023 {real_pooled[yi[2023]]*100:.1f}")
print(f"CSU campus mean: 2004 {real_mean[yi[2004]]*100:.1f}  2017 {real_mean[yi[2017]]*100:.1f}  2023 {real_mean[yi[2023]]*100:.1f}")

# ===== figure: real vs synthetic, shaded partial-exposure band, marked 2023 =====
plt.rcParams.update({"font.size": 11})
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.axvspan(ADOPT - 0.5, FULL_EXPOSURE - 0.5, color="0.92", zorder=0)
ax.plot(YEARS, real_pooled * 100, "-", color="black", linewidth=2, label="Actual (pooled, 23 campuses)")
ax.plot(YEARS, synths["pooled"] * 100, "--", color="gray", linewidth=2, label="Synthetic control")
ax.plot([FULL_EXPOSURE], [real_pooled[yi[FULL_EXPOSURE]] * 100], "o", color="black", markersize=7, zorder=4)
ax.axvline(ADOPT - 0.5, color="black", linewidth=0.8, linestyle=":")
y0, y1 = ax.get_ylim()
ax.text(ADOPT - 0.6, y0, "system-wide Navigate rollout (2018)", rotation=90, va="bottom", ha="right", fontsize=8)
ax.text(ADOPT - 0.3, y0 + 0.3, "cohorts partly exposed\n(entered 2013-2017)", va="bottom", fontsize=8, color="0.3")
ax.annotate("first fully exposed cohort\n(fall 2018 entrants)", xy=(FULL_EXPOSURE, real_pooled[yi[FULL_EXPOSURE]] * 100),
            xytext=(2019.2, real_pooled[yi[FULL_EXPOSURE]] * 100 - 8), fontsize=8,
            arrowprops=dict(arrowstyle="-", color="0.4", linewidth=0.8))
ax.set_xlabel("Graduation-rate year (entering cohort year + 5)")
ax.set_ylabel("Six-year graduation rate (%)")
ax.set_title("California State University system: six-year completion", fontsize=11)
ax.legend(frameon=False, loc="upper left", fontsize=9)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xticks(list(range(2004, 2024, 2)))
plt.tight_layout()
plt.savefig(os.path.join(HERE, "j4_supp_csu_grad.pdf"), bbox_inches="tight")
plt.savefig(os.path.join(HERE, "j4_supp_csu_grad.png"), dpi=150, bbox_inches="tight")
print("\nsaved scm_csu_grad_* to data/ and j4_supp_csu_grad.png/.pdf")
