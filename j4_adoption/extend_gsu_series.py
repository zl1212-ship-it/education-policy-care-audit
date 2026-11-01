"""
Extend the Georgia State six-year graduation series and its synthetic counterpart from
the paper's 2004-2020 window to 2023, and write the full-time retention series to 2024,
for the supplement. Nothing the main analysis reports is re-estimated.

Estimator. The gsu_grad synthetic control of scm_all.py is re-fit with the same inputs
(donor pool = public four-year institutions with inst_size 5 outside Georgia, not in
data/treatment_panel.csv or data/csu_staging.csv, complete 2004-2020 series in the
cached data/raw_grad_t.csv; pre-period 2004-2011; convex weights by SLSQP on the
pre-period outcome path only, synth_w copied verbatim). The script checks that the
re-fit reproduces data/scm_gsu_grad_weights.csv and the synthetic path in
data/scm_gsu_grad_series.csv, then carries the SAME weights forward to the newly
released years 2021-2023 (synthetic = weighted donor average in each year). Weights
depend only on the pre-period, so the extension adds three gap points and changes
neither the weights nor the pre-RMSPE; the placebo p-value in data/scm_summary.csv
refers to the 2012-2020 post-period and is not recomputed here.

Identification. As in scm_all.py: the synthetic Georgia State is assumed to track the
graduation rate Georgia State would have had without the August 2012 GPS Advising
launch, conditional on the 2004-2011 match. Year label t is the fall t-5 entering
cohort with status as of August 31 of t+1; labels 2012-2016 are cohorts that met GPS
Advising part-way through their studies, and 2017 onward are cohorts that entered after
the launch (fully exposed). The 2020-2023 labels (fall 2015-2018 entrants) spent part of
their six-year windows in the pandemic.

Donor availability. If a donor with weight > 1e-4 lacks a 2021-2023 observation, the
synthetic value for that year is the weighted average over the available donors with
weights renormalized to sum to one, and the row is flagged in the note column.

Data. 2004-2020 graduation rates from data/raw_grad_t.csv (read only); 2021-2023 from
data/raw_grad_t_ext.csv, pulled and cached (together with data/raw_grad_counts_ext.csv)
by the same loader scm_csu_grad.py uses if the cache is missing. Retention: 2004-2020
from data/raw_ret.csv (read only); 2021-2024 fall-retention (ftpt=1) pulled and cached
to a NEW data/raw_ret_ext.csv. Directory from data/raw_directory.csv.

Outputs. data/scm_gsu_grad_ext_series.csv (year, cohort_year, exposure, real, synth,
gap, note), data/scm_gsu_grad_ext_weight_check.csv (re-fit vs saved weights),
data/gsu_retention_ext.csv (year, entering_fall, retention, source), and the figure
j4_supp_gsu_ext.png/.pdf with markers at label 2012 (launch) and 2017 (first fully
exposed cohort). Run from this directory with python3 extend_gsu_series.py.
"""
import os, json, urllib.request, numpy as np, pandas as pd
from scipy.optimize import minimize
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
FIT_YEARS = list(range(2004, 2021))      # scm_all.py window
PRE_YEARS = list(range(2004, 2012)); LAUNCH = 2012; FULL_EXPOSURE = 2017
EXT_YEARS = [2021, 2022, 2023]
ALL_YEARS = FIT_YEARS + EXT_YEARS
RET_YEARS_NEW = [2021, 2022, 2023, 2024]
yi = {y: i for i, y in enumerate(FIT_YEARS)}


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


# ===== directory and donor pool, as in scm_all.py =====
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
size5 = dict(zip(pub4[pub4.inst_size == 5].unitid, pub4[pub4.inst_size == 5].state_abbr))
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())

# ===== graduation rates: paper cache (2004-2020) + extension cache (2021-2023) =====
old = pd.read_csv(os.path.join(DATA, "raw_grad_t.csv"))
grad_fit = {(int(r.uid), int(r.year)): r.val for r in old.itertuples()}


def load_grad_counts(years):
    """Same loader as scm_csu_grad.py: pull and append any year missing from the cache."""
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


print("loading extension grad-rates 2021-2023 ...", flush=True)
ext = load_grad_counts(EXT_YEARS)
grad_ext = {(int(r.uid), int(r.year)): r.val for r in ext.itertuples()}
gsu_counts = {int(r.year): (int(r.completers), int(r.cohort)) for r in ext.itertuples() if r.uid == GSU}


def series(src, uid):
    return np.array([src[(uid, y)] for y in FIT_YEARS]) if all((uid, y) in src for y in FIT_YEARS) else None


def synth_w(target, Z, pre_idx):
    Zp, tp = Z[pre_idx], target[pre_idx]
    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    r = minimize(lambda w: float(np.sum((tp - Zp @ w) ** 2)), np.full(Z.shape[1], 1 / Z.shape[1]),
                 method="SLSQP", bounds=[(0, 1)] * Z.shape[1], constraints=cons,
                 options={"maxiter": 800, "ftol": 1e-12})
    return r.x


# ===== re-fit gsu_grad exactly as scm_all.py =====
gsu_donor_ids = {u for u, st in size5.items() if u not in exclude and st != "GA"}
donors = {u: s for u in gsu_donor_ids if (s := series(grad_fit, u)) is not None}
DU = sorted(donors); Z = np.array([donors[u] for u in DU]).T
yg = series(grad_fit, GSU)
pre_idx = [yi[y] for y in PRE_YEARS]
w = synth_w(yg, Z, pre_idx); synth_fit = Z @ w
pre_rmspe = np.sqrt(np.mean((yg[pre_idx] - synth_fit[pre_idx]) ** 2))
print(f"re-fit gsu_grad: donors={len(DU)}  pre-RMSPE={pre_rmspe*100:.3f}pp", flush=True)

saved_w = pd.read_csv(os.path.join(DATA, "scm_gsu_grad_weights.csv"))
saved = dict(zip(saved_w.unitid, saved_w.weight))
wc = pd.DataFrame({"unitid": DU, "name": [inst_name.get(u) for u in DU], "weight_refit": w,
                   "weight_saved": [saved.get(u, 0.0) for u in DU]})
wc["abs_diff"] = (wc.weight_refit - wc.weight_saved).abs()
wc.sort_values("weight_refit", ascending=False).to_csv(
    os.path.join(DATA, "scm_gsu_grad_ext_weight_check.csv"), index=False)
saved_s = pd.read_csv(os.path.join(DATA, "scm_gsu_grad_series.csv"))
synth_diff = float(np.max(np.abs(saved_s.synth.values - synth_fit)))
real_diff = float(np.max(np.abs(saved_s.real.values - yg)))
print(f"  max |weight re-fit - saved| = {wc.abs_diff.max():.2e} (saved file lists weights > 1e-4 only)")
print(f"  max |synth re-fit - saved series| = {synth_diff:.2e}; max |real - saved| = {real_diff:.2e}")
print("  top weights:", [(u, inst_name.get(u), round(wi, 3)) for u, wi in
                        sorted(zip(DU, w), key=lambda t: -t[1])[:7] if wi > 1e-3])

# ===== extend to 2021-2023 with the same weights =====
rows = []
for y in ALL_YEARS:
    if y in yi:
        real, synth, note = yg[yi[y]], synth_fit[yi[y]], "paper window (scm_all.py)"
    else:
        real = grad_ext.get((GSU, y))
        avail = np.array([(u, y) in grad_ext for u in DU])
        missing_w = [(u, wi) for u, wi, a in zip(DU, w, avail) if not a and wi > 1e-4]
        wsum = w[avail].sum()
        synth = float(np.sum([w[i] * grad_ext[(u, y)] for i, u in enumerate(DU) if avail[i]]) / wsum)
        note = (f"extension, {int(avail.sum())}/{len(DU)} donors present, available weight {wsum:.4f}"
                if not missing_w else
                "extension, RENORMALIZED over available donors: missing "
                + "; ".join(f"{u} {inst_name.get(u)} w={wi:.3f}" for u, wi in missing_w)
                + f"; {int(avail.sum())}/{len(DU)} donors present, available weight {wsum:.4f}")
        c, n = gsu_counts.get(y, (None, None))
        note += f"; Georgia State {c}/{n}"
    if y < LAUNCH: expo = "pre"
    elif y < FULL_EXPOSURE: expo = "partial (entered before launch)"
    else: expo = "full (entered after launch)"
    rows.append({"year": y, "cohort_year": y - 5, "exposure": expo, "real": real, "synth": synth,
                 "gap": real - synth, "note": note})
out = pd.DataFrame(rows)
out.to_csv(os.path.join(DATA, "scm_gsu_grad_ext_series.csv"), index=False)
print("\nextended series (pp):")
for r in out[out.year >= 2017].itertuples():
    print(f"  {r.year} (cohort {r.cohort_year}): real {r.real*100:.1f}  synth {r.synth*100:.1f}  "
          f"gap {r.gap*100:+.1f}   {r.note}")
post_paper = out[(out.year >= LAUNCH) & (out.year <= 2020)].gap.mean()
post_all = out[out.year >= LAUNCH].gap.mean()
print(f"  avg gap 2012-2020 = {post_paper*100:+.2f}pp (paper)  avg gap 2012-2023 = {post_all*100:+.2f}pp  "
      f"avg gap 2021-2023 = {out[out.year >= 2021].gap.mean()*100:+.2f}pp  "
      f"avg gap 2017-2023 (fully exposed) = {out[out.year >= FULL_EXPOSURE].gap.mean()*100:+.2f}pp")

# ===== retention 2004-2024 =====
ret_old = pd.read_csv(os.path.join(DATA, "raw_ret.csv"))
rpath = os.path.join(DATA, "raw_ret_ext.csv")
have = pd.read_csv(rpath) if os.path.exists(rpath) else pd.DataFrame(columns=["uid", "year", "val"])
done = set(have.year.astype(int).tolist()) if len(have) else set()
for y in RET_YEARS_NEW:
    if y in done: continue
    new = pd.DataFrame([(x["unitid"], y, x["retention_rate"]) for x in pull(f"{BASE}/fall-retention/{y}/?ftpt=1")
                        if x.get("retention_rate") is not None], columns=["uid", "year", "val"])
    have = pd.concat([have, new], ignore_index=True)
    have.sort_values(["year", "uid"]).to_csv(rpath, index=False)
    print(f"  pulled fall-retention {y} (ftpt=1): {len(new)} rows (cached)", flush=True)
have = have.astype({"uid": int, "year": int})
g_old = ret_old[ret_old.uid == GSU].sort_values("year"); g_new = have[have.uid == GSU].sort_values("year")
ret = pd.concat([pd.DataFrame({"year": g_old.year, "retention": g_old.val, "source": "data/raw_ret.csv"}),
                 pd.DataFrame({"year": g_new.year, "retention": g_new.val, "source": "data/raw_ret_ext.csv"})])
ret["entering_fall"] = ret.year - 1
ret[["year", "entering_fall", "retention", "source"]].to_csv(os.path.join(DATA, "gsu_retention_ext.csv"), index=False)
print("\nGSU full-time retention:", {int(r.year): round(r.retention, 2) for r in ret.itertuples() if r.year >= 2016})

# ===== figure =====
plt.rcParams.update({"font.size": 11})
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.axvspan(2020.5, 2023.5, color="0.92", zorder=0)
ax.plot(out.year, out.real * 100, "-", color="black", linewidth=2, label="Actual")
ax.plot(out.year, out.synth * 100, "--", color="gray", linewidth=2, label="Synthetic control")
for x, lab in [(LAUNCH, "GPS Advising launched (2012)"), (FULL_EXPOSURE, "first fully exposed cohort (2017)")]:
    ax.axvline(x, color="black", linewidth=0.8, linestyle=":")
    ax.text(x + 0.1, ax.get_ylim()[0], lab, rotation=90, va="bottom", fontsize=8)
ax.text(2020.6, ax.get_ylim()[0], "years released after\nthe 2004-2020 window", va="bottom", fontsize=8, color="0.3")
ax.set_xlabel("Graduation-rate year (entering cohort year + 5)")
ax.set_ylabel("Six-year graduation rate (%)")
ax.set_title("Georgia State University: six-year completion, 2004-2023", fontsize=11)
ax.legend(frameon=False, loc="upper left", fontsize=9)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xticks(list(range(2004, 2024, 2)))
plt.tight_layout()
plt.savefig(os.path.join(HERE, "j4_supp_gsu_ext.pdf"), bbox_inches="tight")
plt.savefig(os.path.join(HERE, "j4_supp_gsu_ext.png"), dpi=150, bbox_inches="tight")
print("\nsaved scm_gsu_grad_ext_series.csv, scm_gsu_grad_ext_weight_check.csv, gsu_retention_ext.csv, j4_supp_gsu_ext.png/.pdf")
