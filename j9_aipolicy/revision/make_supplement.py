"""Supplementary material for the revision, generated from the analysis CSVs (symmetric design).
Sections: S1 boilerplate (shares + audited pages); S2 normalization audit + full top terms; S3 page
design (pages, US page sources, prevalence by rule, with PDFs and PDF capture dates, window and
vocabulary sensitivity, US curated vs screened); S4 convergence (endpoint tests with length
equalization and Commonwealth-only columns, per-system gaps, pair matrices overall and by page
type, placebos, balanced pool); S5 crawl density and adoption; S6 exposure robustness."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
from pathlib import Path
import re
import numpy as np, pandas as pd
OUT = AN / "supplement_tables.tex"
SYS = ["US", "UK", "AU", "CA"]; SYSN = {"US": "United States", "UK": "United Kingdom", "AU": "Australia", "CA": "Canada"}
PROV = ["prohibition", "detector_surveillance", "misconduct_framing", "sanction", "permitted_use", "disclosure", "appeal", "l2_protection"]
PN = {"prohibition": "Prohibition", "detector_surveillance": "Detector", "misconduct_framing": "Misconduct", "sanction": "Sanction", "permitted_use": "Permitted", "disclosure": "Disclosure", "appeal": "Appeal", "l2_protection": "Multilingual"}
def tex(s): return str(s).replace("\\", "").replace("_", "\\_").replace("&", "\\&").replace("%", "\\%").replace("#", "\\#")
def f2(x): return "" if pd.isna(x) else f"{x:.2f}"
def f3(x): return "" if pd.isna(x) else f"{x:.3f}"
def sg(x): return "" if pd.isna(x) else f"{x:+.3f}"
def table(cols, rows, caption, spec=None):
    spec = spec or ("l" + "r" * (len(cols) - 1))
    out = [r"\begin{table}[H]\centering\caption{" + caption + r"}\small" + "\n" + r"\begin{tabular}{" + spec + r"}\toprule" + "\n" + " & ".join(cols) + r" \\ \midrule" + "\n"]
    for r in rows: out.append(" & ".join(str(x) for x in r) + r" \\" + "\n")
    out.append(r"\bottomrule\end{tabular}\end{table}" + "\n"); return "".join(out)
parts = [r"""\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}\usepackage{mathptmx}\usepackage{booktabs,longtable,array,graphicx,float}\usepackage[hidelinks]{hyperref}
\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}
\begin{document}
\begin{center}{\large\bfseries Supplementary material}\\[4pt]
Supplementary tables for the J9 AI-policy analysis\end{center}
"""]
# ---------------- S1
c = pd.read_csv(AN / "contamination_summary.csv"); c = c[c.subset == "all snapshots"].set_index("system")
parts.append(r"\section*{S1. Navigation boilerplate}" + "\n" + "Table S1a: for every archived snapshot, the share of words the extractor removes and the share of provision flags obtained without navigation removal that disappear once it is removed (full vocabulary, window 400). Table S1b: sixteen audited pages (four per system, random seed 0) with the words removed and the content rule that selected the main region; the removed blocks are listed in the replication folder (reports/validate\\_extract.md).\n")
parts.append(table(["System", "Snapshots", "Words kept"] + [PN[p] for p in PROV], [[tex(SYSN[s]), int(c.loc[s].n_snapshots), f2(c.loc[s].words_kept_share)] + [f2(c.loc[s][f"{p}_lost_share"]) for p in PROV] for s in SYS], "S1a. Share of flags that came from navigation, by system (all snapshots)."))
v = (AN / "validate_extract.md").read_text() if (AN / "validate_extract.md").exists() else ""
audit = re.findall(r"## (\w\w) \| (.+?) \| (\w+) \| (\d+)\n\nURL: (.+?)  \nraw words (\d+), clean words (\d+), content rule `(.+?)`", v)
if audit:
    parts.append(table(["System", "Institution", "Page", "Capture", "Raw words", "Clean words", "Content rule"], [[s, tex(i[:34]), pt, ts[:8], rw, cw, tex(rule[:34])] for s, i, pt, ts, url, rw, cw, rule in audit], "S1b. The sixteen audited pages: words before and after navigation removal and the rule that selected the main region.", "llllrrl"))
# ---------------- S2
sp = pd.read_csv(AN / "spelling_changes.csv"); tr = pd.read_csv(AN / "term_removal_counts.csv")
parts.append(r"\section*{S2. Normalization of the AI-scoped text}" + "\n")
parts.append(table(["System", "Conversions (count)"], [[tex(SYSN[s]), tex(", ".join(f"{a} to {b} ({n})" for a, b, n in zip(sp[sp.system == s].head(10)["from"], sp[sp.system == s].head(10)["to"], sp[sp.system == s].head(10)["n"])))] for s in SYS], "S2a. Most frequent spelling conversions (British to American) by system.", "p{1.1in}p{5.2in}"))
parts.append(table(["Step", "System", "Terms (count)"], [[step, tex(SYSN[s]), tex(", ".join(f"{t} ({n})" for t, n in zip(tr[(tr.rung == step) & (tr.system == s)].head(12).term, tr[(tr.rung == step) & (tr.system == s)].head(12).n)))] for step in ("L3", "L4") for s in SYS], "S2b. Most frequently removed terms: roles, bodies and regulators (L3); names, places and administrative vocabulary (L4).", "p{0.5in}p{0.9in}p{4.9in}"))
if (AN / "seed_top_terms.csv").exists():
    tt = pd.read_csv(AN / "seed_top_terms.csv")
    for rung in ("S7", "S7x"):
        if (tt.rung == rung).any():
            parts.append(table(["System", "Terms with the highest mean TF-IDF relative to the other systems (rank 1 to 30)"], [[tex(SYSN[s]), tex(", ".join(tt[(tt.rung == rung) & (tt.system == s)].sort_values("rank").term.head(30)))] for s in SYS], f"S2{'c' if rung == 'S7' else 'd'}. Discriminating terms at the endpoint, variant {rung} ({'strict AI vocabulary' if rung == 'S7' else 'strict vocabulary with the AI-naming words removed'}).", "p{1.1in}p{5.2in}"))
# ---------------- S3
parts.append(r"\section*{S3. Page design and the endpoint prevalence of provisions}" + "\n")
ps = pd.read_csv(AN / "pages_summary.csv")
parts.append(table(["Page set", "System", "Institutions", "Mean", "Median", "Max", "AI pages (mean)"], [[tex(lab), s, int(r.inst), f2(r.pages_mean), f2(r.pages_median), int(r.pages_max), f2(r.ai_pages_mean)] for lab in ["all tracked", "non-junk and not inert", "policy-like (US: URL + content screen)"] for s in SYS for r in [ps[(ps.page_set == lab) & (ps.system == s)].iloc[0]] if len(ps[(ps.page_set == lab) & (ps.system == s)])], "S3a. Pages per institution by system under the automated discovery used as a robustness check.", "llrrrrr"))
if (AN / "seed_backfill_pages.csv").exists():
    pg = pd.read_csv(AN / "seed_pages.csv", dtype=str); pg = pg[(pg.in_sample == "1") & (pg.system == "US")]
    sc = pd.read_csv(AN / "scored_seed.csv", dtype={"unitid": str}); sc["page_key"] = sc.local_path.apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
    bf = pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str); key2url = dict(zip(pd.read_csv(AN / "url_set.csv", dtype=str).page_key, pd.read_csv(AN / "url_set.csv", dtype=str).query_url.fillna("")))
    pg["source"] = np.where(pg.page_key.isin(set(sc.page_key)), "curated", "screened discovery")
    pg["url"] = [key2url.get(k, "") or k for k in pg.page_key]
    parts.append(r"\begin{longtable}{p{1.9in}p{0.55in}p{0.9in}p{3in}}\caption{S3b. United States pages in the sample, by source (curated page where archived; otherwise the screened page found by automated search).}\\ \toprule Institution & Type & Source & Address \\ \midrule \endhead" + "\n")
    for r in pg.sort_values(["institution", "page_type"]).itertuples(index=False): parts.append(f"{tex(r.institution[:40])} & {r.page_type} & {r.source} & {tex(r.url[:70])} \\\\\n")
    parts.append(r"\bottomrule\end{longtable}" + "\n")
def prev_table(df, caption, label_col="rule"):
    rows = []
    for rule in df[label_col].unique():
        for s in SYS:
            r = df[(df[label_col] == rule) & (df.system == s)]
            if len(r):
                r = r.iloc[0]; rows.append([tex(rule), s, int(r.n), f2(r.ai_addressed), f2(r.prohibition), f2(r.detector_surveillance), f2(r.misconduct_framing), f2(r.sanction), f2(r.permitted_use), f2(r.disclosure), f2(r.appeal), f2(r.l2_protection)])
    return table(["Rule", "Sys.", "$n$", "AI", "Prohib.", "Detect.", "Miscond.", "Sanct.", "Permit.", "Disclos.", "Appeal", "Multil."], rows, caption, "p{2.2in}lrrrrrrrrrr")
if (AN / "seed_prevalence.csv").exists():
    sp2 = pd.read_csv(AN / "seed_prevalence.csv")
    parts.append(prev_table(sp2, "S3c. Endpoint prevalence under the one-page-per-type design: full vocabulary (clean), strict vocabulary (clean\\_strict, the manuscript's Table 2), strict vocabulary at windows 200 and 800, and with the policy documents linked from the endpoint pages as PDFs. The with-PDF appeal cell for the United States includes one lexical hit in the table of contents of a how-to guide that a reading rejects."))
if (AN / "policy_pdf_scores.csv").exists():
    pdf = pd.read_csv(AN / "policy_pdf_scores.csv", dtype={"unitid": str}); ss = pd.read_csv(AN / "seed_samples.csv", dtype=str); pdf = pdf[pdf.unitid.isin(set(ss.unitid))]
    pdf["year"] = pdf.timestamp.astype(str).str[:4]
    g = pdf.groupby("system").agg(documents=("pdf_url", "size"), institutions=("unitid", "nunique"), post_shock=("post_shock_capture", "sum"), with_strict_ai=("ai_addressed_clean_strict", "sum")).reindex(SYS).fillna(0).astype(int)
    parts.append(table(["System", "Documents", "Institutions", "Captured after the shock", "With strict AI text"], [[tex(SYSN[s])] + [int(g.loc[s, c]) for c in g.columns] for s in SYS], "S3d. Linked policy documents retrieved from the archive (sample institutions): count, institutions, captures dated after 30 November 2022, and documents carrying strict AI vocabulary."))
if (AN / "seed_prevalence_by_source.csv").exists():
    parts.append(prev_table(pd.read_csv(AN / "seed_prevalence_by_source.csv"), "S3e. United States endpoint prevalence by page source (curated versus screened discovered pages), strict vocabulary."))
pr = pd.read_csv(AN / "prevalence_by_pagerule.csv"); rules = [x for x in pr.rule.unique() if x.startswith(("(a)", "(a2)", "(b)", "(h)", "(k)"))]
parts.append(prev_table(pr[pr.rule.isin(rules)], "S3f. Endpoint prevalence under the automated discovery design (robustness): the submitted coding (a), the corrected filter (a2), navigation removed (b), strict vocabulary (h), policy pages matched one per type (k)."))
if (AN / "unscoped_remedies.csv").exists():
    u = pd.read_csv(AN / "unscoped_remedies.csv")
    parts.append(table(["System", "Institutions addressing AI", "Appeal language anywhere on the page", "Appeal within the AI window", "Multilingual language anywhere", "Multilingual within the AI window"], [[tex(SYSN[r.system]), int(r.n_inst_addressing_ai), f2(r.appeal_anywhere), f2(r.appeal_scoped), f2(r.l2_anywhere), f2(r.l2_scoped)] for r in u.itertuples(index=False)], "S3g. Remedy language on the AI-addressing endpoint pages: anywhere on the page versus within the AI-scoped window (share of institutions)."))
if (AN / "second_coder_r1.csv").exists():
    s2 = pd.read_csv(AN / "second_coder_r1.csv")
    parts.append(table(["Provision", "$n$", "Prevalence (primary)", "Raw agreement", "Cohen's kappa", "Gwet's AC1"], [[tex(r.provision), int(r.n), f3(r.prevalence_primary), f3(r.raw_agreement), f3(r.cohen_kappa), f3(r.gwet_ac1)] for r in s2.itertuples(index=False)], "S3h. Agreement between the primary lexicon and an independently specified rule set on 80 random cleaned snapshots carrying strict AI text."))
# ---------------- S4
parts.append(r"\section*{S4. Convergence}" + "\n" + "Variants: S1 navigation removed; S4 fully normalized (spelling, roles and bodies, names and places, administrative vocabulary); S7 normalized with the strict AI vocabulary (the manuscript's figures); S7x additionally removes the AI-naming words themselves. Endpoint tests are computed on the last-quarter documents of the same TF-IDF fit as Figure 1; cut-to-300 and cut-to-600 versions refit the vectorizer on the truncated documents. $p$ values are from 2,000 label permutations.\n")
if (AN / "seed_convergence_endpoint.csv").exists():
    e = pd.read_csv(AN / "seed_convergence_endpoint.csv"); e0 = e[e.get("gap").notna()] if "gap" in e.columns else e
    rows = []
    for r in e0.itertuples(index=False):
        rows.append([r.rung, int(r.n), int(r.n_us), f3(r.within), f3(r.cross), sg(r.gap), f3(r.p), sg(getattr(r, "gap_t300", np.nan)), f3(getattr(r, "p_t300", np.nan)), sg(getattr(r, "cw_gap", np.nan)), f3(getattr(r, "cw_p", np.nan)), sg(getattr(r, "cw_gap_t300", np.nan)), f3(getattr(r, "cw_p_t300", np.nan)), sg(getattr(r, "usrest", np.nan)), f3(getattr(r, "usrest_p", np.nan)), sg(getattr(r, "usrest_t300", np.nan)), f3(getattr(r, "usrest_p_t300", np.nan))])
    parts.append(table(["Variant", "$n$", "US", "Within", "Cross", "Gap", "$p$", "Gap, 300 w", "$p$", "Cw. gap", "$p$", "Cw. gap, 300 w", "$p$", "US-vs-rest", "$p$", "US-vs-rest, 300 w", "$p$"], rows, "S4a. Endpoint tests on all pages: pooled same-country gap, Commonwealth-only (Cw.) gap and the United States contrast, on full text and on text cut to 300 words.", "lrrrrrrrrrrrrrrrr"))
    for lab in ("integrity", "ai"):
        rr = [r for r in e.itertuples(index=False) if not pd.isna(getattr(r, f"{lab}_gap", np.nan))]
        if rr:
            parts.append(table(["Variant", "$n$", "US", "Within", "Cross", "Gap", "$p$", "Gap, 300 w", "$p$", "Cw. gap", "$p$", "US-vs-rest", "$p$"], [[r.rung, int(getattr(r, f"{lab}_n")), int(getattr(r, f"{lab}_n_us")), f3(getattr(r, f"{lab}_within")), f3(getattr(r, f"{lab}_cross")), sg(getattr(r, f"{lab}_gap")), f3(getattr(r, f"{lab}_p")), sg(getattr(r, f"{lab}_gap_t300")), f3(getattr(r, f"{lab}_p_t300")), sg(getattr(r, f"{lab}_cw_gap", np.nan)), f3(getattr(r, f"{lab}_cw_p", np.nan)), sg(getattr(r, f"{lab}_usrest")), f3(getattr(r, f"{lab}_usrest_p"))] for r in rr], f"S4{'b' if lab == 'integrity' else 'c'}. Endpoint tests on {lab} pages only.", "lrrrrrrrrrrrr"))
if (AN / "seed_per_system_gap.csv").exists():
    ps2 = pd.read_csv(AN / "seed_per_system_gap.csv")
    parts.append(table(["Variant", "System", "$n$", "Same-country pairs", "Cross pairs", "Same mean", "Cross mean", "Gap", "$p$"], [[tex(r.rung), r.system, int(r.n_inst), int(r.same_pairs), int(r.cross_pairs), f3(r.same_mean), f3(r.cross_mean), sg(r.gap), f3(r.p)] for r in ps2.itertuples(index=False)], "S4d. Per-system decomposition at the endpoint: mean similarity among pairs within the system minus pairs between that system and the others, with a permutation $p$.", "llrrrrrrr"))
if (AN / "seed_system_pair_matrix.csv").exists():
    mx = pd.read_csv(AN / "seed_system_pair_matrix.csv")
    for pages_lab in ("all", "integrity", "ai"):
        m = mx[(mx.rung == "S7") & (mx.pages == pages_lab)]
        if len(m):
            m = m.pivot(index="sys_a", columns="sys_b", values="mean_cos").reindex(index=SYS, columns=SYS)
            parts.append(table([""] + SYS, [[a] + [f3(m.loc[a, b]) for b in SYS] for a in SYS], "S4" + {'all': 'e', 'integrity': 'f', 'ai': 'g'}.get(pages_lab, 'e') + f". Mean pairwise cosine similarity by system pair at the endpoint, variant S7, {pages_lab} pages.", "lrrrr"))
if (AN / "seed_placebo_text.csv").exists():
    pl = pd.read_csv(AN / "seed_placebo_text.csv")
    parts.append(table(["Variant", "Text", "$n$", "Gap", "$p$", "Cw. gap", "$p$", "US-vs-rest", "$p$"], [[r.rung, tex(r.text), int(r.n_inst), sg(r.gap), f3(r.p), sg(getattr(r, "cw_gap", np.nan)), f3(getattr(r, "cw_p", np.nan)), sg(getattr(r, "usrest", np.nan)), f3(getattr(r, "usrest_p", np.nan))] for r in pl.itertuples(index=False)], "S4h. Placebo texts on the sample institutions, each cut to 600 words: the AI-scoped text, the non-AI text of the same endpoint pages, the pre-shock page text, and the paired difference (AI minus non-AI) for the same institution pairs.", "llrrrrrrr"))
if (AN.parent / "draft" / "fig_convergence_balanced_r1.pdf").exists():
    parts.append(r"\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_convergence_balanced_r1.pdf}\caption{S4i. Convergence by pair type on a balanced pool: institutions carrying AI text in every quarter from the fifth quarter after the shock to the end of the window.}\end{figure}" + "\n")
# ---------------- S5
if (AN / "density_summary.csv").exists():
    ds = pd.read_csv(AN / "density_summary.csv")
    parts.append(r"\section*{S5. Crawl density and interval-censored adoption}" + "\n")
    parts.append(table(["System", "Period", "Mean captures", "Median", "Share of page-quarters with none", "Median days between captures"], [[r.system, tex(r.period), f2(r.mean_captures), f2(r.median_captures), f2(r.share_zero), f2(r.median_gap_days)] for r in ds.itertuples(index=False)], "S5a. Captures per page and quarter by system and period (daily-collapsed captures).", "llrrrr"))
    if (AN / "density_summary_by_pagetype.csv").exists():
        dp = pd.read_csv(AN / "density_summary_by_pagetype.csv")
        parts.append(table(["System", "Page type", "Mean captures", "Median", "Share with none"], [[r.system, r.page_type, f2(r.mean_captures), f2(r.median_captures), f2(r.share_zero)] for r in dp.itertuples(index=False)], "S5b. Captures per page and quarter by page type.", "llrrr"))
    if (AN / "density_exposure_correlation.csv").exists():
        dc = pd.read_csv(AN / "density_exposure_correlation.csv"); dc = dc[dc.density == "density_all"]
        parts.append(table(["System", "$n$", "Pearson $r$", "$p$", "Spearman", "$p$"], [[r.system, int(r.n), f2(r.pearson_r), f3(r.pearson_p), f2(r.spearman_rho), f3(r.spearman_p)] for r in dc.itertuples(index=False)], "S5c. Capture density (mean captures per page-quarter) against the international share of enrollment, sample institutions.", "lrrrrr"))
    if (AN / "adoption_summary.csv").exists():
        ad = pd.read_csv(AN / "adoption_summary.csv"); ad = ad[ad.flag == "clean_strict"]
        parts.append(table(["System", "Adopters", "Left-censored", "Interval width (days, median)", "Lag mean $R$", "Lag mean midpoint", "Lag mean $L$", "Within 2 q. ($R$)", "Within 2 q. (midpoint)"], [[r.system, int(r.n_adopters), int(r.left_censored), f2(r.width_days_median), f2(r.lag_mean_q_R), f2(r.lag_mean_q_mid), f2(r.lag_mean_q_L), f2(r.share_within2q_q_R), f2(r.share_within2q_q_mid)] for r in ad.itertuples(index=False)], "S5d. Adoption timing under three conventions (strict vocabulary): the forward-fill convention $R$, the interval midpoint, and the left bound $L$; left-censored adopters have no capture of the page before the one carrying AI text.", "lrrrrrrrr"))
    if (AN / "adoption_turnbull.csv").exists():
        tb = pd.read_csv(AN / "adoption_turnbull.csv")
        if "subset" in tb.columns:
            for sub in tb.subset.unique():
                t = tb[(tb.subset == sub) & (tb.event_q.between(1, 8))]
                parts.append(table(["Quarter", "Turnbull mass", "Turnbull CDF", "Forward-fill mass", "Forward-fill CDF"], [[int(r.event_q), f3(r.turnbull_mass), f3(r.turnbull_cdf), f3(r.forward_fill_mass), f3(r.forward_fill_cdf)] for r in t.itertuples(index=False)], f"S5{'e' if sub == 'all' else 'f'}. Adoption-time distribution, quarters 1 to 8: Turnbull estimate versus forward-fill, {'all adopters' if sub == 'all' else 'adopters with an observed pre-change capture'} ($n$ = {int(t.n_adopters.iloc[0])}).", "lrrrr"))
# ---------------- S6
parts.append(r"\section*{S6. The exposure differential}" + "\n")
if (AN / "exposure_robustness.csv").exists():
    er = pd.read_csv(AN / "exposure_robustness.csv")
    parts.append(table(["Outcome", "$n$", "Coef.", "SE", "Adjusted coef.", "SE", "Late (q12--13) coef.", "Upper 95\\%", "LOO min", "LOO max", "Bootstrap 95\\%", "Bootstrap $p$"], [[tex(r.outcome), int(r.n_inst), sg(r.coef), f3(r.se_cluster), sg(r.coef_adjusted), f3(r.se_adjusted), sg(r.coef_late_q12_13), sg(r.ci_hi_late), sg(r.loo_min), sg(r.loo_max), f"[{r.boot_ci_lo:+.2f}, {r.boot_ci_hi:+.2f}]", f3(r.boot_p_two_sided)] for r in er.itertuples(index=False)], "S6a. United States event study on the one-page-per-type design (strict vocabulary): exposure $\\times$ post coefficient with institution-clustered SE; adjusted for private control $\\times$ post and log enrollment $\\times$ post; the late-quarter (12 to 13) interaction; leave-one-institution-out range; institution bootstrap (500 draws).", "lrrrrrrrrrrr"))
    if (AN / "exposure_terciles.csv").exists():
        et = pd.read_csv(AN / "exposure_terciles.csv")
        parts.append(table(["Tercile", "$n$", "Governance intensity", "Restrictive index", "Procedural index", "Net restrictiveness", "Addresses AI"], [[r.terc, int(r.n), f2(r.ai_governance_intensity), f2(r.restrictive_idx), f2(r.procedural_idx), f2(r.net_restrictiveness), f2(r.ai_addressed)] for r in et.itertuples(index=False)], "S6b. United States endpoint means by exposure tercile (strict vocabulary).", "lrrrrrr"))
    if (AN / "exposure_corr.csv").exists():
        ec = pd.read_csv(AN / "exposure_corr.csv")
        parts.append(table(["System", "$n$", "Outcome", "$r$", "95\\% interval", "Institutions with any such provision"], [[r.system, int(r.n), tex(r.outcome), f2(r.r), f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", int(r.n_with_any_provision)] for r in ec.itertuples(index=False)], "S6c. Endpoint correlations between the international share and the provision indices, by system, with Fisher intervals.", "lrlrrr"))
ev = pd.read_csv(AN / "event_study_variants.csv"); ev = ev[ev.kind == "did_exposure_x_post"]
parts.append(table(["Rule (automated discovery design)", "$n$", "Outcome", "Coef.", "SE", "$p$"], [[tex(r.variant), int(r.n_inst), tex(r.outcome), sg(r.coef), f3(r.se), f3(r.p)] for r in ev.itertuples(index=False)], "S6d. Exposure $\\times$ post coefficients under the automated discovery design (robustness); 25 coefficients are shown, so individual $p$ values near 0.05 should be read with that in mind.", "lrlrrr"))
parts.append(r"\end{document}" + "\n")
OUT.write_text("".join(parts)); print("wrote", OUT)
