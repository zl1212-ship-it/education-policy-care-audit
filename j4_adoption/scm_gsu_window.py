"""
Placebo inference for the Georgia State graduation synthetic control over sub-windows of the
post-period, using the saved base-specification outputs of scm_all.py (no re-estimation).

The base test in scm_all.py ranks the post/pre RMSPE ratio over 2012-2020. Labels 2012-2016
are cohorts that entered before GPS Advising launched; labels 2017-2020 are the cohorts that
entered after it (entering cohort = label minus five). This script recomputes the ratio with the
post-period RMSPE taken over 2017-2020 only, for the treated unit and for every placebo, and
reports the permutation p-value under the three exclusion rules used in the paper. The pre-period
RMSPE of each unit is unchanged (2004-2011 fit).

Output: data/scm_gsu_grad_window_p.csv
"""
import os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
pg = pd.read_csv(os.path.join(DATA, "scm_gsu_grad_placebo.csv"))
ra = pd.read_csv(os.path.join(DATA, "scm_gsu_grad_ratios.csv"))
pre_t = np.sqrt(np.mean(pg.loc[pg.year <= 2011, "treated"] ** 2))

rows = []
for lo, hi in [(2012, 2020), (2017, 2020)]:
    m = (pg.year >= lo) & (pg.year <= hi)
    post_t = np.sqrt(np.mean(pg.loc[m, "treated"] ** 2)); r_t = post_t / pre_t
    pre = dict(zip(ra.unitid, ra.pre_rmspe))
    rat, prs = [], []
    for c in pg.columns:
        if not c.startswith("p"):
            continue
        u = int(c[1:]); pr = pre[u]
        po = np.sqrt(np.mean(pg.loc[m, c] ** 2))
        rat.append(np.inf if pr == 0 else po / pr); prs.append(pr)
    rat = np.array(rat); prs = np.array(prs)

    def p(mask):
        return (np.sum(rat[mask] >= r_t) + 1) / (mask.sum() + 1)
    rows.append({"window": f"{lo}-{hi}", "avg_gap": pg.loc[m, "treated"].mean(), "ratio": r_t,
                 "p": p(prs <= 2 * pre_t), "n_p": int((prs <= 2 * pre_t).sum()),
                 "p_dropwellfit": p(prs > 1e-6), "p_all": p(np.ones(len(prs), bool))})
    print(rows[-1])
pd.DataFrame(rows).to_csv(os.path.join(DATA, "scm_gsu_grad_window_p.csv"), index=False)
print("saved data/scm_gsu_grad_window_p.csv")
