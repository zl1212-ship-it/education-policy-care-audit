"""Exposure analysis on the US seed panel (clean strict): main interaction, covariate-adjusted
interaction (private control x post, log enrollment x post), leave-one-institution-out range,
institution-cluster bootstrap p, late-quarter (q12-13) interaction, US-only exposure terciles at the
endpoint, outcome standard deviations for the bound, and the UK/AU endpoint correlations with
Fisher confidence intervals; the main interaction on the institutions that meet the entry rule
page by page (seed_samples.csv page_rule); and the main interaction provision by provision, for
permitted use and disclosure together, and for the procedural index without the institution whose
removal moves it most (the leave-one-out minimum). Estimates are stored to six decimals. Writes
exposure_robustness.csv, exposure_terciles.csv, exposure_corr.csv, exposure_page_rule.csv,
exposure_by_provision.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import warnings, sys
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
p = pd.read_csv(AN / "seed_panel_us_clean_strict.csv", dtype={"unitid": str}); p = p[p.intl_share.notna()].copy()
inst = p.drop_duplicates("unitid"); mu, sd = inst.intl_share.mean(), inst.intl_share.std(ddof=0)
p["exposure"] = (p.intl_share - mu) / sd; p["eq"] = p.event_q.astype(int); p["post"] = (p["eq"] >= 0).astype(int); p["expXpost"] = p["exposure"] * p["post"]
p["private"] = (p.control.str.lower() == "private").astype(int); p["logenr"] = np.log(pd.to_numeric(p.total_enroll, errors="coerce")).fillna(np.log(pd.to_numeric(p.total_enroll, errors="coerce")).median())
p["privXpost"] = p.private * p.post; p["enrXpost"] = (p.logenr - p.logenr.mean()) * p.post
p["late"] = p["eq"].isin([12, 13]).astype(int); p["expXlate"] = p["exposure"] * p["late"]; p["expXearly"] = p.exposure * ((p["eq"] >= 0) & (p["eq"] <= 11)).astype(int)
OUT = ["net_restrictiveness", "restrictive_idx", "procedural_idx", "ai_governance_intensity", "ai_addressed"]
rows = []
def fit(df, y, rhs):
    m = smf.ols(f"{y} ~ C(unitid) + C(eq) + {rhs}", data=df).fit(cov_type="cluster", cov_kwds={"groups": df.unitid}); return m
rng = np.random.default_rng(2026); uids = p.unitid.unique()
for y in OUT:
    m = fit(p, y, "expXpost"); b, se = m.params["expXpost"], m.bse["expXpost"]
    ma = fit(p, y, "expXpost + privXpost + enrXpost"); ba, sea = ma.params["expXpost"], ma.bse["expXpost"]
    ml = fit(p, y, "expXearly + expXlate"); bl, sel = ml.params["expXlate"], ml.bse["expXlate"]
    loo = [smf.ols(f"{y} ~ C(unitid) + C(eq) + expXpost", data=p[p.unitid != u]).fit().params["expXpost"] for u in uids]
    boots = []
    for _ in range(500):
        samp = rng.choice(uids, len(uids), replace=True)
        df = pd.concat([p[p.unitid == u].assign(unitid=f"{u}_{j}") for j, u in enumerate(samp)])
        try: boots.append(smf.ols(f"{y} ~ C(unitid) + C(eq) + expXpost", data=df).fit().params["expXpost"])
        except Exception: pass
    boots = np.array(boots); sd_all = p[y].std(ddof=0); sd_post = p[p.post == 1][y].std(ddof=0); sd_end = p[p["eq"] == 13][y].std(ddof=0)
    rows.append({"outcome": y, "n_inst": p.unitid.nunique(), "coef": round(b, 6), "se_cluster": round(se, 6), "p": round(m.pvalues["expXpost"], 6), "ci_lo": round(b - 1.96 * se, 6), "ci_hi": round(b + 1.96 * se, 6),
                 "coef_adjusted": round(ba, 6), "se_adjusted": round(sea, 6), "coef_late_q12_13": round(bl, 6), "se_late": round(sel, 6), "ci_lo_late": round(bl - 1.96 * sel, 6), "ci_hi_late": round(bl + 1.96 * sel, 6),
                 "loo_min": round(min(loo), 6), "loo_min_unitid": uids[int(np.argmin(loo))], "loo_max": round(max(loo), 6), "boot_ci_lo": round(float(np.percentile(boots, 2.5)), 6), "boot_ci_hi": round(float(np.percentile(boots, 97.5)), 6),
                 "boot_p_two_sided": round(float(2 * min(np.mean(boots <= 0), np.mean(boots >= 0))), 6), "sd_all_quarters": round(sd_all, 6), "sd_post": round(sd_post, 6), "sd_endpoint": round(sd_end, 6)})
r = pd.DataFrame(rows); r.to_csv(AN / "exposure_robustness.csv", index=False); pd.set_option("display.width", 250); print(r.to_string(index=False))
inst = inst.assign(terc=pd.qcut(inst.intl_share, 3, labels=["low", "middle", "high"]))
pp = p.merge(inst[["unitid", "terc"]], on="unitid"); end = pp[pp["eq"] == 13]
t = end.groupby("terc", observed=True)[["ai_governance_intensity", "restrictive_idx", "procedural_idx", "net_restrictiveness", "ai_addressed"]].mean().round(2)
t["n"] = end.groupby("terc", observed=True).size(); t.to_csv(AN / "exposure_terciles.csv"); print("\nUS-only endpoint by exposure tercile:\n", t.to_string())
print("Carnegie in the US sample:", inst.carnegie.value_counts().to_dict())
# endpoint correlations UK/AU with Fisher CI
ss = pd.read_csv(AN / "seed_samples.csv", dtype=str); full = pd.read_csv(AN / "seed_panel_clean_strict.csv", dtype={"unitid": str}); full["system"] = full.unitid.map(dict(zip(ss.unitid, ss.system)))
last = full.sort_values("event_q").groupby("unitid").tail(1); crows = []
for s in ("UK", "AU", "US"):
    d = last[(last.system == s) & last.intl_share.notna()]
    for y in ("restrictive_idx", "procedural_idx", "net_restrictiveness", "ai_governance_intensity"):
        r_ = np.corrcoef(d.intl_share.astype(float), d[y])[0, 1]; n = len(d); z = np.arctanh(r_); se = 1 / np.sqrt(n - 3)
        crows.append({"system": s, "n": n, "outcome": y, "r": round(r_, 2), "ci_lo": round(np.tanh(z - 1.96 * se), 2), "ci_hi": round(np.tanh(z + 1.96 * se), 2), "n_with_any_provision": int((d[y] > 0).sum())})
c = pd.DataFrame(crows); c.to_csv(AN / "exposure_corr.csv", index=False); print("\n", c.to_string(index=False))
# entry rule applied page by page: drop the institutions observed after the shock only on a page first captured after it
same = set(ss[ss.page_rule == "1"].unitid); q = p[p.unitid.isin(same)]; prow = []
for y in OUT:
    m = fit(q, y, "expXpost"); b, se = m.params["expXpost"], m.bse["expXpost"]
    prow.append({"outcome": y, "n_inst": q.unitid.nunique(), "coef": round(b, 6), "se_cluster": round(se, 6), "ci_lo": round(b - 1.96 * se, 6), "ci_hi": round(b + 1.96 * se, 6), "p": round(m.pvalues["expXpost"], 6)})
pr = pd.DataFrame(prow); pr.to_csv(AN / "exposure_page_rule.csv", index=False); print("\nentry rule page by page:\n", pr.to_string(index=False))
# provision by provision (the procedural index is the sum of its four provisions, so their interactions add up to it)
sys.path.insert(0, str(XN)); import build_panel as B
p["permitted_plus_disclosure"] = p.permitted_use_present + p.disclosure_present
drop = r.set_index("outcome").loc["procedural_idx", "loo_min_unitid"]; vrow = []
for y, d, lab in [(f"{x}_present", p, "") for x in B.RESTRICTIVE + B.PROCEDURAL] + [("permitted_plus_disclosure", p, ""), ("procedural_idx", p[p.unitid != drop], drop)]:
    m = fit(d, y, "expXpost"); b, se = m.params["expXpost"], m.bse["expXpost"]
    vrow.append({"outcome": y, "without_unitid": lab, "without_institution": p[p.unitid == lab].institution.iloc[0] if lab else "", "n_inst": d.unitid.nunique(),
                 "coef": round(b, 6), "se_cluster": round(se, 6), "ci_lo": round(b - 1.96 * se, 6), "ci_hi": round(b + 1.96 * se, 6), "p": round(m.pvalues["expXpost"], 6),
                 "n_inst_flagged_endpoint": int(d[d["eq"] == 13][y].gt(0).sum()) if y.endswith("_present") else np.nan})
v = pd.DataFrame(vrow); v.to_csv(AN / "exposure_by_provision.csv", index=False); print("\nprovision by provision:\n", v.to_string(index=False))
