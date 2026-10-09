"""Print every number the revised manuscript quotes, from the CSVs, so a data refresh can be
checked line by line against the text (draft/main-r1.tex) and the response letter."""
from pathlib import Path
import numpy as np, pandas as pd
AN = Path(__file__).parent
def f(x, d=2): return "" if pd.isna(x) else f"{x:.{d}f}"
ss = pd.read_csv(AN / "seed_samples.csv", dtype=str); pg = pd.read_csv(AN / "seed_pages.csv", dtype=str); pg = pg[pg.in_sample == "1"]
sc = pd.read_csv(AN / "scored_seed.csv", dtype=str); sc["page_key"] = sc.local_path.apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
bf = pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str) if (AN / "seed_backfill_pages.csv").exists() else pd.DataFrame(columns=["unitid", "page_key"])
us = set(ss[ss.system == "US"].unitid)
print("SAMPLE:", ss.groupby("system").size().reindex(["US", "UK", "AU", "CA"]).to_dict(), "total", len(ss))
print("US sources: curated only", len((us & set(sc.unitid)) - set(bf.unitid)), "| backfill only", len((us & set(bf.unitid)) - set(sc.unitid)), "| both", len(us & set(sc.unitid) & set(bf.unitid)))
print("PAGES by system/type:", pg.groupby(["system", "page_type"]).size().to_dict())
prev = pd.read_csv(AN / "seed_prevalence.csv")
for rule in prev.rule.unique():
    d = prev[prev.rule == rule].set_index("system").reindex(["US", "UK", "AU", "CA"])
    print(f"PREVALENCE [{rule}]: n", d.n.tolist(), "| addresses AI", [f(x) for x in d.ai_addressed], "| misconduct", [f(x) for x in d.misconduct_framing], "| prohibition", [f(x) for x in d.prohibition], "| detector", [f(x) for x in d.detector_surveillance], "| sanction", [f(x) for x in d.sanction], "| permitted", [f(x) for x in d.permitted_use], "| disclosure", [f(x) for x in d.disclosure], "| appeal", [f(x) for x in d.appeal], "| L2", [f(x) for x in d.l2_protection], "| restr idx", [f(x) for x in d.restrictive_idx], "| proc idx", [f(x) for x in d.procedural_idx])
g = pd.read_csv(AN / "seed_convergence_groups.csv"); g = g[g.rung == "S7"]
for grp in g.group.unique():
    gg = g[g.group == grp].sort_values("event_q"); print(f"GROUP {grp}: q1 {f(gg[gg.event_q == 1].mean_cos.iloc[0] if (gg.event_q == 1).any() else np.nan, 3)} q2 {f(gg[gg.event_q == 2].mean_cos.iloc[0] if (gg.event_q == 2).any() else np.nan, 3)} q13 {f(gg[gg.event_q == 13].mean_cos.iloc[0], 3)}")
se = pd.read_csv(AN / "seed_convergence_series.csv"); s7 = se[se.rung == "S7"]; print("SERIES S7: first q", int(s7.event_q.min()), "n at q1", int(s7[s7.event_q == s7.event_q.min()].n_inst.iloc[0]), "n at q13", int(s7[s7.event_q == 13].n_inst.iloc[0]))
ep = pd.read_csv(AN / "seed_convergence_endpoint.csv")
for r in ep[ep.gap.notna()].itertuples(index=False):
    print(f"ENDPOINT {r.rung}: n {int(r.n)} (US {int(r.n_us)}) within {f(r.within,3)} cross {f(r.cross,3)} gap {r.gap:+.3f} p {f(r.p,3)} | t300 {r.gap_t300:+.3f} p {f(r.p_t300,3)} t600 {r.gap_t600:+.3f} p {f(r.p_t600,3)} | Cw {getattr(r,'cw_gap',np.nan):+.3f} p {f(getattr(r,'cw_p',np.nan),3)} Cw t300 {getattr(r,'cw_gap_t300',np.nan):+.3f} p {f(getattr(r,'cw_p_t300',np.nan),3)} | US-vs-rest {r.usrest:+.3f} p {f(r.usrest_p,3)} t300 {r.usrest_t300:+.3f} p {f(r.usrest_p_t300,3)} | words US {r.words_median_US:.0f} nonUS {r.words_median_nonUS:.0f}")
for r in ep[ep.get('integrity_gap', pd.Series(dtype=float)).notna()].itertuples(index=False):
    print(f"ENDPOINT {r.rung} integrity pages: n {int(r.integrity_n)} gap {r.integrity_gap:+.3f} p {f(r.integrity_p,3)} Cw {getattr(r,'integrity_cw_gap',np.nan):+.3f} US-vs-rest {r.integrity_usrest:+.3f} p {f(r.integrity_usrest_p,3)}")
for r in ep[ep.get('ai_gap', pd.Series(dtype=float)).notna()].itertuples(index=False):
    print(f"ENDPOINT {r.rung} AI pages: n {int(r.ai_n)} gap {r.ai_gap:+.3f} p {f(r.ai_p,3)} US-vs-rest {r.ai_usrest:+.3f} p {f(r.ai_usrest_p,3)}")
ps_ = pd.read_csv(AN / "seed_per_system_gap.csv"); print("PER SYSTEM S7:\n", ps_[ps_.rung == "S7"].to_string(index=False))
b = pd.read_csv(AN / "seed_convergence_balanced.csv"); b = b[b.rung == "S7"]
if len(b): print("BALANCED S7 n", int(b.n_inst.iloc[0]), "\n", b.pivot(index="event_q", columns="group", values="mean_cos").round(3).loc[[5, 9, 13]].to_string())
comp = pd.read_csv(AN / "seed_endpoint_composition.csv"); print("COMPOSITION S7 q13:", comp[comp.rung == "S7"].set_index("system").n_inst_end.to_dict())
mx = pd.read_csv(AN / "seed_system_pair_matrix.csv")
for pg in ("all", "integrity", "ai"):
    m = mx[(mx.rung == "S7") & (mx.pages == pg)]
    if len(m): print(f"MATRIX S7 {pg}:\n", m.pivot(index="sys_a", columns="sys_b", values="mean_cos").round(3).to_string())
pl = pd.read_csv(AN / "seed_placebo_text.csv"); print("PLACEBO S7:\n", pl[pl.rung == "S7"].to_string(index=False))
tt = pd.read_csv(AN / "seed_top_terms.csv")
for rg in ("S7", "S7x"):
    for s in ["US", "UK", "AU", "CA"]: print("TERMS", rg, s, ", ".join(tt[(tt.rung == rg) & (tt.system == s)].sort_values("rank").term.head(10)))
es = pd.read_csv(AN / "event_study_seed.csv"); print("EVENT STUDY (seed):\n", es[es.kind == "did_exposure_x_post"][["variant", "n_inst", "outcome", "coef", "se", "ci_lo", "ci_hi", "p"]].to_string(index=False))
ev = pd.read_csv(AN / "event_study_variants.csv"); print("EVENT STUDY (discovered pages, clean_strict):\n", ev[(ev.kind == "did_exposure_x_post") & (ev.variant == "clean_strict")][["n_inst", "outcome", "coef", "se", "p"]].to_string(index=False))
p = pd.read_csv(AN / "seed_panel_clean_strict.csv", dtype={"unitid": str}); p["system"] = p.unitid.map(dict(zip(ss.unitid, ss.system)))
last = p.sort_values("event_q").groupby("unitid").tail(1)
for s in ("UK", "AU"):
    d = last[(last.system == s) & last.intl_share.notna()]; print(f"ENDPOINT CORR {s} n {len(d)}: r(intl,restrictive) {np.corrcoef(d.intl_share.astype(float), d.restrictive_idx)[0,1]:+.2f} r(intl,procedural) {np.corrcoef(d.intl_share.astype(float), d.procedural_idx)[0,1]:+.2f}")
ad = p[(p.ai_addressed == 1) & (p.event_q >= 0)].groupby("unitid").event_q.min(); print("ADOPTION (forward-fill, strict): adopters", len(ad), "median q", ad.median(), "share<=2q", f((ad <= 2).mean()), "| pre-shock positives", int(p[p.event_q < 0].groupby("unitid").ai_addressed.max().sum()))
inst = p.drop_duplicates("unitid")[["unitid", "intl_share"]].dropna(); inst["terc"] = pd.qcut(inst.intl_share.astype(float), 3, labels=["low", "mid", "high"]); pp = p.merge(inst[["unitid", "terc"]], on="unitid")
print("TERCILE endpoint intensity:", pp[pp.event_q == 13].groupby("terc", observed=True).ai_governance_intensity.mean().round(2).to_dict())
if (AN / "adoption_summary.csv").exists():
    a = pd.read_csv(AN / "adoption_summary.csv"); a = a[(a.flag == "clean_strict")]
    for r in a.itertuples(index=False): print(f"INTERVALS {r.system}: adopters {int(r.n_adopters)} left-censored {int(r.left_censored)} width median {r.width_days_median:.0f} d | R mean {r.lag_mean_q_R} median {r.lag_median_q_R} within2 {r.share_within2q_q_R} | mid mean {r.lag_mean_q_mid} median {r.lag_median_q_mid} within2 {r.share_within2q_q_mid} | L mean {r.lag_mean_q_L}")
    tb = pd.read_csv(AN / "adoption_turnbull.csv")
    for sub in tb.subset.unique():
        t = tb[tb.subset == sub]; print(f"TURNBULL {sub} n {int(t.n_adopters.iloc[0])}: cdf q2 {f(t[t.event_q == 2].turnbull_cdf.iloc[0])} q4 {f(t[t.event_q == 4].turnbull_cdf.iloc[0])} | forward-fill cdf q2 {f(t[t.event_q == 2].forward_fill_cdf.iloc[0])} q4 {f(t[t.event_q == 4].forward_fill_cdf.iloc[0])}")
    ds = pd.read_csv(AN / "density_summary.csv"); print("DENSITY share_zero by system/period:\n", ds.pivot(index="system", columns="period", values="share_zero").round(2).to_string())
    print("DENSITY median captures by system (pooled periods):", ds.groupby("system").median_captures.median().to_dict())
    dc = pd.read_csv(AN / "density_exposure_correlation.csv"); print("DENSITY vs exposure (sample):", dc[dc.density == "density_all"][["system", "n", "pearson_r", "pearson_p"]].to_string(index=False))
if (AN / "policy_pdf_scores.csv").exists():
    ps = pd.read_csv(AN / "policy_pdf_scores.csv", dtype={"unitid": str}); idx = pd.read_csv(AN / "policy_pdf_index.csv", dtype=str)
    print("PDFS: attempted", len(idx), "ok", int((idx.status == "ok").sum()), "institutions with a PDF", ps.unitid.nunique(), "| by system", ps.groupby("system").unitid.nunique().to_dict())

if (AN / "exposure_robustness.csv").exists():
    er = pd.read_csv(AN / "exposure_robustness.csv"); print("EXPOSURE ROBUSTNESS:\n", er.to_string(index=False))
    print("US TERCILES:\n", pd.read_csv(AN / "exposure_terciles.csv").to_string(index=False)); print("CORR:\n", pd.read_csv(AN / "exposure_corr.csv").to_string(index=False))
if (AN / "second_coder_r1.csv").exists(): print("SECOND CODER:\n", pd.read_csv(AN / "second_coder_r1.csv").to_string(index=False))
if (AN / "unscoped_remedies.csv").exists(): print("UNSCOPED:\n", pd.read_csv(AN / "unscoped_remedies.csv").to_string(index=False))
if (AN / "seed_prevalence_by_source.csv").exists(): print("BY SOURCE:\n", pd.read_csv(AN / "seed_prevalence_by_source.csv").round(2).to_string(index=False))
if (AN / "policy_pdf_scores.csv").exists():
    pdf = pd.read_csv(AN / "policy_pdf_scores.csv", dtype={"unitid": str}); ss2 = pd.read_csv(AN / "seed_samples.csv", dtype=str); pdf = pdf[pdf.unitid.isin(set(ss2.unitid))]
    print("PDF: docs", len(pdf), "institutions", pdf.unitid.nunique(), "post-shock captures", int(pdf.post_shock_capture.sum()), "with strict AI", int(pdf.ai_addressed_clean_strict.sum()), "by system", pdf.groupby("system").unitid.nunique().to_dict())
