"""
Why does synthetic GSU flatten after 2012? Decomposes the synthetic control's slope into
its weighted donors. For every donor with weight > 2% in the gsu_grad synthetic control
(weights from scm_gsu_grad_weights.csv, produced by scm_all.py): OLS slope of the
six-year graduation rate on year over 2004-2011 (pre) and over 2012-2020 (post), in
pp/yr, plus rows for the weighted synthetic (exact series from scm_gsu_grad_series.csv),
GSU itself, and the unweighted mean of the full donor pool (reconstructed as in
scm_all.py). Also prints the weighted-donor path 2011-2015: graduation rates observed in
2013-2014 belong to 2007-2008 entry cohorts (Great Recession), a candidate mechanical
story for the synthetic's post-2012 deceleration.
Offline from data/raw_grad_t.csv and data/raw_directory.csv.
Writes data/scm_gsu_donor_slopes.csv.
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
YEARS = np.array(range(2004, 2021)); yi = {y: i for i, y in enumerate(YEARS)}
PRE = [yi[y] for y in range(2004, 2012)]; POST = [yi[y] for y in range(2012, 2021)]

df = pd.read_csv(os.path.join(DATA, "raw_grad_t.csv"))
grad = {(int(r.uid), int(r.year)): r.val for r in df.itertuples()}


def series(u):
    return np.array([grad[(u, y)] for y in YEARS]) if all((u, y) in grad for y in YEARS) else None


def slope(v, idx):
    return float(np.polyfit(YEARS[idx], v[idx] * 100, 1)[0])  # pp per year


# full pool, as in scm_all.py
dirr = pd.read_csv(os.path.join(DATA, "raw_directory.csv"))
pub4 = dirr[dirr.institution_level == 4]
size5 = dict(zip(pub4[pub4.inst_size == 5].unitid, pub4[pub4.inst_size == 5].state_abbr))
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
pool = {u: s for u, st in size5.items()
        if u not in exclude and st != "GA" and (s := series(u)) is not None}
pool_mean = np.mean([pool[u] for u in sorted(pool)], axis=0)

wdf = pd.read_csv(os.path.join(DATA, "scm_gsu_grad_weights.csv"))
top = wdf[wdf.weight > 0.02]
syn = pd.read_csv(os.path.join(DATA, "scm_gsu_grad_series.csv"))
y_syn = syn["synth"].values; y_gsu = syn["real"].values

rows = []
for _, r in top.iterrows():
    s = pool[int(r.unitid)]
    rows.append({"name": r["name"], "weight": r.weight,
                 "pre_slope_2004_2011": slope(s, PRE), "post_slope_2012_2020": slope(s, POST)})
rows.append({"name": "SYNTHETIC (weighted donors)", "weight": top.weight.sum(),
             "pre_slope_2004_2011": slope(y_syn, PRE), "post_slope_2012_2020": slope(y_syn, POST)})
rows.append({"name": "Georgia State (treated)", "weight": np.nan,
             "pre_slope_2004_2011": slope(y_gsu, PRE), "post_slope_2012_2020": slope(y_gsu, POST)})
rows.append({"name": f"Unweighted pool mean ({len(pool)} donors)", "weight": np.nan,
             "pre_slope_2004_2011": slope(pool_mean, PRE), "post_slope_2012_2020": slope(pool_mean, POST)})
out = pd.DataFrame(rows)
out["accel"] = out.post_slope_2012_2020 - out.pre_slope_2004_2011
out.to_csv(os.path.join(DATA, "scm_gsu_donor_slopes.csv"), index=False)
print(out.to_string(index=False, float_format=lambda x: f"{x:6.3f}"))

# Great Recession cohort check: 2013-2014 grad rates = 2007-2008 entrants
print("\nweighted-donor path 2011-2015 (%, change vs 2012 in parens):")
for _, r in top.iterrows():
    s = pool[int(r.unitid)] * 100
    v = {y: s[yi[y]] for y in range(2011, 2016)}
    print(f"  {r['name'][:40]:40s} w={r.weight:.2f}  " +
          "  ".join(f"{y}:{v[y]:5.1f}" for y in range(2011, 2016)) +
          f"   d13={v[2013]-v[2012]:+.1f} d14={v[2014]-v[2012]:+.1f}")
s = y_syn * 100; v = {y: s[yi[y]] for y in range(2011, 2016)}
print(f"  {'SYNTHETIC':40s} w={top.weight.sum():.2f}  " +
      "  ".join(f"{y}:{v[y]:5.1f}" for y in range(2011, 2016)) +
      f"   d13={v[2013]-v[2012]:+.1f} d14={v[2014]-v[2012]:+.1f}")
print("\nsaved data/scm_gsu_donor_slopes.csv")
