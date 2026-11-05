"""Supplementary material for the revision, generated from the analysis CSVs (symmetric design).
Sections: S1 boilerplate (shares + audited pages); S2 normalization audit + full top terms; S3 page
design (pages, US page sources, prevalence by rule, with PDFs and PDF capture dates, window and
vocabulary sensitivity, US curated vs screened); S4 convergence (endpoint tests with length
equalization and Commonwealth-only columns, per-system gaps, pair matrices overall and by page
type, placebos, balanced pool, and the pair structure checked for the small British pool and for
text length); S5 crawl density and adoption; S6 exposure robustness."""
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
AN2 = AN   # pair-structure checks (pair_structure_checks.py) write here too
FIGDIR = REV / "draft"   # the balanced-pool figure is included only where a draft folder holds it
SYS = ["US", "UK", "AU", "CA"]; SYSN = {"US": "United States", "UK": "United Kingdom", "AU": "Australia", "CA": "Canada"}
PROV = ["prohibition", "detector_surveillance", "misconduct_framing", "sanction", "permitted_use", "disclosure", "appeal", "l2_protection"]
PN = {"prohibition": "Prohibition", "detector_surveillance": "Detector", "misconduct_framing": "Misconduct", "sanction": "Sanction", "permitted_use": "Permitted", "disclosure": "Disclosure", "appeal": "Appeal", "l2_protection": "Multilingual"}
def tex(s): return str(s).replace("\\", "").replace("_", "\\_").replace("&", "\\&").replace("%", "\\%").replace("#", "\\#")
from decimal import Decimal, ROUND_HALF_UP
def rnd(x, d): return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))  # a share such as 76/160 = 0.475 stored as 0.47499... rounds as 0.475, half up
def f4(x): return "" if pd.isna(x) else f"{rnd(x, 4):.4f}"
def f2(x): return "" if pd.isna(x) else f"{rnd(x, 2):.2f}"
def f3(x): return "" if pd.isna(x) else f"{rnd(x, 3):.3f}"
def sg(x): return "" if pd.isna(x) else f"{rnd(x, 3):+.3f}"
def fp(x): return "" if pd.isna(x) else ("<0.001" if x < 0.001 else f"{rnd(x, 3):.3f}")  # permutation p (2,000 draws: smallest 1/2001)
def nw(k): return ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][k] if 0 <= k < 10 else str(k)
def table(cols, rows, caption, spec=None):
    spec = spec or ("l" + "r" * (len(cols) - 1))
    wide = len(cols) >= 12; size = r"\footnotesize" if len(cols) >= 9 else r"\small"
    out = [(r"\begin{landscape}" if wide else "") + r"\begin{table}[H]\centering\caption{" + caption + r"}" + size + "\n" + r"\fittable{\begin{tabular}{" + spec + r"}\toprule" + "\n" + " & ".join(cols) + r" \\ \midrule" + "\n"]
    for r in rows: out.append(" & ".join(str(x) for x in r) + r" \\" + "\n")
    out.append(r"\bottomrule\end{tabular}}\end{table}" + (r"\end{landscape}" if wide else "") + "\n"); return "".join(out)
parts = [r"""\documentclass[12pt]{article}\PassOptionsToPackage{hyphens}{url}
\usepackage[margin=1in]{geometry}\usepackage{mathptmx}\usepackage{booktabs,longtable,array,graphicx,float,pdflscape}\usepackage{caption}\captionsetup{labelformat=empty,labelsep=none,justification=raggedright,singlelinecheck=false}\usepackage[hidelinks]{hyperref}
\newsavebox{\tblbox}\newcommand{\fittable}[1]{\sbox{\tblbox}{#1}\ifdim\wd\tblbox>\linewidth\resizebox{\linewidth}{!}{\usebox{\tblbox}}\else\usebox{\tblbox}\fi}
\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}
\begin{document}
\begin{center}{\large\bfseries Supplementary material}\\[4pt]
Supplementary tables for the J9 AI-policy analysis\end{center}
"""]
# ---------------- S1
c = pd.read_csv(AN / "contamination_summary.csv"); c = c[c.subset == "all snapshots"].set_index("system")
parts.append(r"\section*{S1. Navigation boilerplate}" + "\n" + "Table S1a: for every archived snapshot of the study (the original retrieval, the curated United States pages and the versions in force at quarter ends, each capture counted once), the share of words the extractor keeps and the share of provision flags obtained without navigation removal that disappear once it is removed (full vocabulary, 400-character window), with the number of such flags in parentheses. PDF documents are read with the same PDF text extractor in both arms. Table S1b: sixteen audited pages (four per system, random seed 0) with word counts before and after navigation removal and the content rule that selected the main region; the removed blocks are listed in the replication folder (output/validate\\_extract.md).\n")
parts.append(table(["System", "Snapshots", "Words kept"] + [PN[p] for p in PROV], [[tex(SYSN[s]), int(c.loc[s].n_snapshots), f2(c.loc[s].words_kept_share)] + [f"{f2(c.loc[s][f'{p}_lost_share'])} ({int(c.loc[s][f'{p}_raw_n'])})" for p in PROV] for s in SYS], "S1a. Share of flags that came from navigation, by system (every archived snapshot; in parentheses, the number of flags before navigation removal)."))
v = (RP / "validate_extract.md").read_text() if (RP / "validate_extract.md").exists() else ""
audit = re.findall(r"## (\w\w) \| (.+?) \| (\w+) \| (\d+)\n\nURL: (.+?)  \nraw words (\d+), clean words (\d+), content rule `(.+?)`", v)
if audit:
    parts.append(table(["System", "Institution", "Page", "Capture", "Raw words", "Clean words", "Content rule"], [[s, tex(i[:34]), pt, ts[:8], rw, cw, tex(rule[:34])] for s, i, pt, ts, url, rw, cw, rule in audit], "S1b. The sixteen audited pages: words before and after navigation removal and the rule that selected the main region.", "llllrrl"))
# ---------------- S2
sp = pd.read_csv(AN / "seed_spelling_changes.csv"); tr = pd.read_csv(AN / "seed_term_removal_counts.csv")  # the sample (seed_convergence.py)
parts.append(r"\section*{S2. Normalization of the AI-scoped text}" + "\n")
parts.append(table(["System", "Conversions (count)"], [[tex(SYSN[s]), tex(", ".join(f"{a} to {b} ({n})" for a, b, n in zip(sp[sp.system == s].head(10)["from"], sp[sp.system == s].head(10)["to"], sp[sp.system == s].head(10)["n"])))] for s in SYS], "S2a. Most frequent spelling conversions (British to American) by system, counted over the full cleaned text of every snapshot of the sample; the AI-scoped text is cut from the converted text.", "p{1.1in}p{5.2in}"))
parts.append(table(["Step", "System", "Terms (count)"], [[step, tex(SYSN[s]), tex(", ".join(f"{t} ({n})" for t, n in zip(tr[(tr.rung == step) & (tr.system == s)].head(12).term, tr[(tr.rung == step) & (tr.system == s)].head(12).n)))] for step in ("L3", "L4") for s in SYS], "S2b. Most frequently removed terms in the AI-scoped text of every snapshot of the sample (full vocabulary): roles, bodies and regulators (L3); names, places and administrative vocabulary (L4). The strict-vocabulary text (S7) removes the same terms.", "p{0.5in}p{0.9in}p{4.9in}"))
if (AN2 / "seed_top_terms.csv").exists():
    tt = pd.read_csv(AN2 / "seed_top_terms.csv")
    for rung in ("S7", "S7x"):
        if (tt.rung == rung).any():
            parts.append(table(["System", "Terms with the highest mean TF-IDF relative to the other systems (rank 1 to 30)"], [[tex(SYSN[s]), tex(", ".join(tt[(tt.rung == rung) & (tt.system == s)].sort_values("rank").term.head(30)))] for s in SYS], f"S2{'c' if rung == 'S7' else 'd'}. Discriminating terms at the endpoint, variant {rung} ({'strict AI vocabulary' if rung == 'S7' else 'strict vocabulary with the AI-naming words and AI product names removed'}).", "p{1.1in}p{5.2in}"))
# ---------------- S3
parts.append(r"\section*{S3. Page design and the endpoint prevalence of provisions}" + "\n")
ps = pd.read_csv(AN / "pages_summary.csv")
parts.append(table(["Page set", "System", "Institutions", "Mean", "Median", "Max", "AI pages (mean)"], [[tex(lab), s, int(r.inst), f2(r.pages_mean), f2(r.pages_median), int(r.pages_max), f2(r.ai_pages_mean)] for lab in ["all tracked", "non-junk and not inert", "policy-like (US: URL + content screen)"] for s in SYS for r in [ps[(ps.page_set == lab) & (ps.system == s)].iloc[0]] if len(ps[(ps.page_set == lab) & (ps.system == s)])], "S3a. Pages per institution by system under the submitted page design, kept as a robustness check: automated discovery under each United States institution's hosts, the committed curated pages elsewhere.", "llrrrrr"))
if (AN / "seed_backfill_pages.csv").exists():
    pg = pd.read_csv(AN / "seed_pages.csv", dtype=str); pg = pg[(pg.in_sample == "1") & (pg.system == "US")]
    sc = pd.read_csv(AN / "scored_seed.csv", dtype={"unitid": str}); sc["page_key"] = sc.local_path.apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
    bf = pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str); key2url = dict(zip(pd.read_csv(AN / "url_set.csv", dtype=str).page_key, pd.read_csv(AN / "url_set.csv", dtype=str).query_url.fillna("")))
    if (AN / "screened_cdx_captures.csv").exists():  # the screened pages' addresses, as listed
        _s = pd.read_csv(AN / "screened_cdx_captures.csv", dtype=str).drop_duplicates("page_key")
        for _k, _u in zip(_s.page_key, _s.query_url.fillna("")):
            if _u.startswith("http") and not (key2url.get(_k) or "").startswith("http"): key2url[_k] = _u
    if (AN / "pages_per_institution.csv").exists():
        _pp = pd.read_csv(AN / "pages_per_institution.csv", dtype=str)
        for _k, _u in zip(_pp.page_key, _pp.real_url.fillna("")):
            if _u.startswith("http") and not (key2url.get(_k) or "").startswith("http"): key2url[_k] = _u
    for _f in ("seed_snapshot_index.csv", "scored_raw_vs_clean.csv"):
        _d = pd.read_csv(AN / _f, dtype=str)
        for _lp, _u in zip(_d.local_path, _d.original_url.fillna("")):
            _k = Path(_lp).stem.rsplit("__", 1)[0]
            if _u.startswith("http") and not (key2url.get(_k) or "").startswith("http"): key2url[_k] = _u
    _pipe = globals().get("PIPE") or AN.parents[4] / "j9_aipolicy"; _raw = _pipe / "data" / "snapshots_raw"
    for _k in list(pg.page_key):
        if (key2url.get(_k) or "").startswith("http"): continue
        _hits = sorted(_raw.glob(f"*/*/{_k}__*.html")) if _raw.exists() else []
        for _h in reversed(_hits):
            try:
                import lxml.html as _LH
                _t = _LH.parse(str(_h)).getroot()
                _c = _t.xpath('//link[@rel="canonical"]/@href') or _t.xpath('//meta[@property="og:url"]/@content')
                if _c and str(_c[0]).strip().startswith("http"): key2url[_k] = str(_c[0]).strip().split("?")[0]; break
            except Exception: continue
    pg["source"] = np.where(pg.page_key.isin(set(sc.page_key)), "curated", "screened discovery")
    pg["url"] = [key2url.get(k, "") or k for k in pg.page_key]
    parts.append(r"\begin{longtable}{p{1.6in}p{0.55in}p{1.0in}p{2.6in}}\caption{S3b. United States pages in the sample, by source (curated page where archived; otherwise the screened page found by automated search). Pages whose original address was not recorded and whose archived copy carries no canonical address are listed by their page key, the address with punctuation replaced by underscores.}\\ \toprule Institution & Type & Source & Address \\ \midrule \endhead" + "\n")
    for r in pg.sort_values(["institution", "page_type"]).itertuples(index=False): parts.append(f"{tex(r.institution)} & {r.page_type} & {r.source} & \\path{{{r.url}}} \\\\\n")
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
    _second = sp2.rule.str.contains("linked policy PDFs|entry on one page")
    parts.append(prev_table(sp2[~_second], "S3c. Endpoint prevalence under the tracked-page design: navigation not removed (raw), full vocabulary (clean), strict vocabulary (clean\_strict, the manuscript's Table 2), and the strict vocabulary at 200- and 800-character windows."))
    parts.append(prev_table(sp2[_second], "S3c (continued). Endpoint prevalence with the policy documents linked from the endpoint pages as PDFs (in the United States, from the curated pages only), and, in the last rows, only the institutions that meet the entry rule page by page (entry on one page: the United States institutions observed after the shock only on an AI guidance page first archived after it are left out)."))
    parts.append("Note on Table S3c. The appeal cells are lexicon hits, and on reading none is an appeal route written into an AI rule. On the pages, under the strict vocabulary, the United States hit is a list of office links on an integrity landing page (`Appealing Possible Academic Dishonesty') beside a link headed `Generative AI - What to Know', which also supplies that institution's misconduct-framing flag, and the Canadian hit is the word `hearing' in a warning that misconduct may lead to `a hearing with more significant sanctions'. The linked PDFs add, under the strict vocabulary, the heading `Future considerations' of a how-to guide, which the PDF text extraction runs together into a string containing `reconsideration'; under the full vocabulary, the verb `appeals to' in a linked EDUCAUSE article captured before the shock and, in Canada, an academic integrity (`AI') infographic captured in January 2022. The multilingual cells are one United States teaching page warning that some responses to AI may disadvantage English-language learners (strict vocabulary) and, under the full vocabulary, two more teaching pages warning that detectors misread non-native speakers; the linked PDFs add a teaching handout suggesting that AI tools may help students who are non-native English speakers. The strict vocabulary also matches GenAI written as one word, which the full vocabulary of the submitted design misses, so a few strict cells exceed the full ones.\n\n")
if (AN / "policy_pdf_scores.csv").exists():
    pdf = pd.read_csv(AN / "policy_pdf_scores.csv", dtype={"unitid": str}); ss = pd.read_csv(AN / "seed_samples.csv", dtype=str); pdf = pdf[pdf.unitid.isin(set(ss.unitid))]
    pdf["year"] = pdf.timestamp.astype(str).str[:4]
    g = pdf.groupby("system").agg(documents=("pdf_url", "size"), institutions=("unitid", "nunique"), post_shock=("post_shock_capture", "sum"), with_strict_ai=("ai_addressed_clean_strict", "sum")).reindex(SYS).fillna(0).astype(int)
    parts.append(table(["System", "Documents", "Institutions", "Captured after the shock", "With strict AI text"], [[tex(SYSN[s])] + [int(g.loc[s, c]) for c in g.columns] for s in SYS], "S3d. Linked policy documents retrieved from the archive (sample institutions): count, institutions, captures dated on or after 30 November 2022, and documents carrying strict AI vocabulary."))
if (AN / "seed_prevalence_by_source.csv").exists():
    parts.append(prev_table(pd.read_csv(AN / "seed_prevalence_by_source.csv"), "S3e. United States endpoint prevalence by page source: institutions observed on curated pages only, on screened discovered pages only, or on one page of each (both); strict vocabulary."))
pr = pd.read_csv(AN / "prevalence_by_pagerule.csv"); rules = [x for x in pr.rule.unique() if x.startswith(("(a)", "(a2)", "(b)", "(h)", "(k)"))]
parts.append(prev_table(pr[pr.rule.isin(rules)], "S3f. Endpoint prevalence under the submitted page design (automated discovery in the United States; robustness): the submitted coding (a), the corrected filter (a2), navigation removed (b), strict vocabulary (h), policy pages matched one per type (k). Computed on the original retrieval, without the versions in force at quarter ends added in this revision, so its Commonwealth rows differ slightly from those of Table S3c; and with the revised extractor, which reads the three Commonwealth policy documents held as PDFs with a PDF extractor in both arms, so five Australian cells of row (a) differ from the submitted version's Table 2 (which read .74, .16, .53, .21 and .26 for addresses AI, prohibition, misconduct, sanction and permitted use)."))
if (AN / "unscoped_remedies.csv").exists():
    u = pd.read_csv(AN / "unscoped_remedies.csv")
    parts.append(table(["System", "Addressing AI ($n$)", "Appeal, anywhere", "Appeal, in window", "Multilingual, anywhere", "Multilingual, in window"], [[tex(SYSN[r.system]), int(r.n_inst_addressing_ai), f2(r.appeal_anywhere), f2(r.appeal_scoped), f2(r.l2_anywhere), f2(r.l2_scoped)] for r in u.itertuples(index=False)], "S3g. Remedy language on the AI-addressing endpoint pages: anywhere on the page versus within the AI-scoped window (share of institutions)."))
if (AN / "second_coder_r1.csv").exists():
    s2 = pd.read_csv(AN / "second_coder_r1.csv")
    parts.append(table(["Provision", "$n$", "Prevalence (primary)", "Raw agreement", "Cohen's kappa", "Gwet's AC1"], [[tex(r.provision), int(r.n), f4(r.prevalence_primary), f4(r.raw_agreement), ("n/a" if r.prevalence_primary == 0 and r.raw_agreement == 1 else f3(r.cohen_kappa)), f3(r.gwet_ac1)] for r in s2.itertuples(index=False)], "S3h. Agreement between the primary lexicon and an independently specified rule set on 80 random cleaned snapshots carrying strict AI text; prevalence and agreement are shares of 80 decisions (640 pooled), given to four decimals because they are exact multiples of 1/80. Cohen's kappa is undefined (n/a) where neither rule set flags the provision in any snapshot."))
# ---------------- S4
parts.append(r"\section*{S4. Convergence}" + "\n" + "Variants: S1 navigation removed; S4 fully normalized (spelling, roles and bodies, names and places, administrative vocabulary); S7 normalized with the strict AI vocabulary (the manuscript's Figure 1); S7x additionally removes the AI-naming words themselves (AI, artificial intelligence, generative, GenAI, LLM, large language model, chatbot) and the names of AI products and their makers (ChatGPT, GPT, OpenAI, Anthropic, Copilot, Bard, Gemini, Claude, NotebookLM, Grammarly, QuillBot, Perplexity, DeepSeek, Midjourney, DALL-E, Bing, and Val, RMIT's chatbot). The AI-scoped text of a capture joins the passages within 300 characters of an AI term, with overlapping passages merged, so that no stretch of text enters twice. Endpoint tests on all pages are computed on the last-quarter documents of the same TF-IDF fit as Figure 1; the page-type tests (the full-text columns of Tables S4b and S4c, the :integrity and :ai rows of Table S4d, and Tables S4f and S4g) refit the vectorizer on all quarterly documents of that page type and use its last-quarter rows; the 300-word cuts (Tables S4a to S4c) and the 600-word placebo texts (Table S4h) refit the vectorizer on the truncated documents. Tables S4j to S4m check the pair structure of Table S4e for the small British pool and for text length; their 300- and 600-word cuts refit the vectorizer in the same way. An institution's document joins the latest capture of each tracked page on or before the end of the quarter; the placebo texts of Table S4h use the latest capture on or before the endpoint, and the pre-shock text (Tables S4h, S4k and S4l) is that of the integrity pages. $p$ values are from 2,000 label permutations.\n")
if (AN2 / "seed_convergence_endpoint.csv").exists():
    e = pd.read_csv(AN2 / "seed_convergence_endpoint.csv"); e0 = e[e.get("gap").notna()] if "gap" in e.columns else e
    rows = []
    for r in e0.itertuples(index=False):
        rows.append([r.rung, int(r.n), int(r.n_us), f3(r.within), f3(r.cross), sg(r.gap), fp(r.p), sg(getattr(r, "gap_t300", np.nan)), fp(getattr(r, "p_t300", np.nan)), sg(getattr(r, "cw_gap", np.nan)), fp(getattr(r, "cw_p", np.nan)), sg(getattr(r, "cw_gap_t300", np.nan)), fp(getattr(r, "cw_p_t300", np.nan)), sg(getattr(r, "usrest", np.nan)), fp(getattr(r, "usrest_p", np.nan)), sg(getattr(r, "usrest_t300", np.nan)), fp(getattr(r, "usrest_p_t300", np.nan))])
    parts.append(table(["Variant", "$n$", "US", "Within", "Cross", "Gap", "$p$", "Gap, 300 w", "$p$", "Cw. gap", "$p$", "Cw. gap, 300 w", "$p$", "US-vs-rest", "$p$", "US-vs-rest, 300 w", "$p$"], rows, "S4a. Endpoint tests on all pages: pooled same-country gap, Commonwealth-only (Cw.) gap and the United States contrast, on full text and on text cut to 300 words.", "lrrrrrrrrrrrrrrrr"))
    for lab in ("integrity", "ai"):
        rr = [r for r in e.itertuples(index=False) if not pd.isna(getattr(r, f"{lab}_gap", np.nan))]
        if rr:
            parts.append(table(["Variant", "$n$", "US", "Within", "Cross", "Gap", "$p$", "Gap, 300 w", "$p$", "Cw. gap", "$p$", "US-vs-rest", "$p$", "US-vs-rest, 300 w", "$p$", "US-vs-rest, 600 w", "$p$"], [[r.rung, int(getattr(r, f"{lab}_n")), int(getattr(r, f"{lab}_n_us")), f3(getattr(r, f"{lab}_within")), f3(getattr(r, f"{lab}_cross")), sg(getattr(r, f"{lab}_gap")), fp(getattr(r, f"{lab}_p")), sg(getattr(r, f"{lab}_gap_t300")), fp(getattr(r, f"{lab}_p_t300")), sg(getattr(r, f"{lab}_cw_gap", np.nan)), fp(getattr(r, f"{lab}_cw_p", np.nan)), sg(getattr(r, f"{lab}_usrest")), fp(getattr(r, f"{lab}_usrest_p")), sg(getattr(r, f"{lab}_usrest_t300", np.nan)), fp(getattr(r, f"{lab}_usrest_p_t300", np.nan)), sg(getattr(r, f"{lab}_usrest_t600", np.nan)), fp(getattr(r, f"{lab}_usrest_p_t600", np.nan))] for r in rr], f"S4{'b' if lab == 'integrity' else 'c'}. Endpoint tests on {('AI guidance' if lab == 'ai' else 'integrity')} pages only, with the United States contrast also on text cut to 300 and 600 words.", "lrrrrrrrrrrrrrrrr"))
if (AN2 / "seed_per_system_gap.csv").exists():
    ps2 = pd.read_csv(AN2 / "seed_per_system_gap.csv")
    parts.append(table(["Variant", "System", "$n$", "Same-country pairs", "Cross pairs", "Same mean", "Cross mean", "Gap", "$p$"], [[tex(r.rung), r.system, int(r.n_inst), int(r.same_pairs), int(r.cross_pairs), f3(r.same_mean), f3(r.cross_mean), sg(r.gap), fp(r.p)] for r in ps2.itertuples(index=False)], "S4d. Per-system decomposition at the endpoint: mean similarity among pairs within the system minus pairs between that system and the others, with a permutation $p$. Rows suffixed :integrity and :ai restrict the pool to that page type; a system appears only where it has at least three same-system pairs. The United States rows repeat the US-vs-rest contrasts of Tables S4a to S4c with a separate draw of 2,000 permutations, so their $p$ values differ slightly.", "llrrrrrrr"))
if (AN2 / "seed_system_pair_matrix.csv").exists():
    mx = pd.read_csv(AN2 / "seed_system_pair_matrix.csv")
    for pages_lab in ("all", "integrity", "ai"):
        m = mx[(mx.rung == "S7") & (mx.pages == pages_lab)]
        if len(m):
            small = {a: int(float(n)) for a, b, n in zip(m.sys_a, m.sys_b, m.n_pairs) if a == b and int(float(n)) <= 3} if "n_pairs" in m.columns else {}
            npairs = m.pivot(index="sys_a", columns="sys_b", values="n_pairs").reindex(index=SYS, columns=SYS)
            m = m.pivot(index="sys_a", columns="sys_b", values="mean_cos").reindex(index=SYS, columns=SYS)
            note = ""
            if pages_lab == "all" and (AN2 / "seed_endpoint_composition.csv").exists():
                comp = pd.read_csv(AN2 / "seed_endpoint_composition.csv"); comp = comp[comp.rung == "S7"].set_index("system").n_inst_end
                note = (" Institutions carrying AI text at the endpoint: " + ", ".join(f"{SYSN[k]} {int(comp[k])}" for k in SYS)
                        + f"; the British diagonal cell therefore rests on {int(npairs.loc['UK', 'UK'])} pairs among {nw(int(comp['UK']))} institutions (Table S4m leaves each out in turn).")
            parts.append(table([""] + SYS, [[a] + [f3(m.loc[a, b]) for b in SYS] for a in SYS], "S4" + {'all': 'e', 'integrity': 'f', 'ai': 'g'}.get(pages_lab, 'e') + f". Mean pairwise cosine similarity by system pair at the endpoint, variant S7, {('AI guidance pages' if pages_lab == 'ai' else ('integrity pages' if pages_lab == 'integrity' else 'all pages'))}." + (" Diagonal cells for " + ", ".join(f"{k} ({v} pair{'s' if v != 1 else ''})" for k, v in small.items()) + " rest on three pairs or fewer." if small else "") + note, "lrrrr"))
if (AN2 / "seed_placebo_text.csv").exists():
    pl = pd.read_csv(AN2 / "seed_placebo_text.csv")
    parts.append(table(["Variant", "Text", "$n$", "Gap", "$p$", "Cw. gap", "$p$", "US-vs-rest", "$p$"], [[r.rung, tex(r.text), int(r.n_inst), sg(r.gap), fp(r.p), sg(getattr(r, "cw_gap", np.nan)), fp(getattr(r, "cw_p", np.nan)), sg(getattr(r, "usrest", np.nan)), fp(getattr(r, "usrest_p", np.nan))] for r in pl.itertuples(index=False)], "S4h. Placebo texts on the sample institutions, each cut to 600 words: the AI-scoped text, the non-AI text of the same endpoint pages, the pre-shock integrity-page text, and the paired difference (AI minus non-AI) for the same institution pairs. The AI, non-AI and paired rows cover the institutions whose endpoint pages carry both kinds of text; an institution whose endpoint text lies entirely within the AI windows is left out of them.", "llrrrrrrr"))
if (FIGDIR / "fig_convergence_balanced_r1.pdf").exists():
    parts.append(r"\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_convergence_balanced_r1.pdf}\caption{S4i. Convergence by pair type on a balanced pool: institutions carrying AI text in every quarter from the fifth quarter after the shock to the end of the window.}\end{figure}" + "\n")
if (AN2 / "seed_convergence_balanced.csv").exists():
    bp = pd.read_csv(AN2 / "seed_convergence_balanced.csv"); bp = bp[bp.rung == "S7"]
    if len(bp):
        GR = ["US-US", "US-Commonwealth", "Commonwealth same country", "Commonwealth cross country"]
        piv = bp.pivot(index="event_q", columns="group", values="mean_cos"); qs = [q for q in (5, 9, 13) if q in piv.index]
        parts.append(table(["Pair type"] + [f"Quarter {q}" for q in qs], [[tex(g)] + [f3(piv.loc[q, g]) for q in qs] for g in GR if g in piv.columns], f"S4i (values). Mean pairwise cosine similarity by pair type on the balanced pool of Figure S4i ({int(bp.n_inst.iloc[0])} institutions, variant S7), in the fifth and ninth quarters after the shock and at the end of the window.", "l" + "r" * len(qs)))
if (AN2 / "pair_matrix_by_length.csv").exists():
    TX = {"full": "Full text", "cut 300": "Cut to 300 words", "cut 600": "Cut to 600 words", "pre-shock page text, cut 600": "Pre-shock integrity pages, 600 words"}
    pm0 = pd.read_csv(AN2 / "pair_matrix_by_length.csv"); rows_j = []
    for cut, lab in (("cut 300", "300 words"), ("cut 600", "600 words")):
        pm = pm0[pm0.text == cut].pivot(index="sys_a", columns="sys_b", values="mean_cos").reindex(index=SYS, columns=SYS)
        rows_j += [[lab if a == SYS[0] else "", a] + [f3(pm.loc[a, b]) for b in SYS] for a in SYS]
    parts.append(table(["Text cut to", ""] + SYS, rows_j, "S4j. Mean pairwise cosine similarity by system pair at the endpoint, variant S7, all pages, with every institution's text cut to its first 300 or 600 words (the full-text version is Table S4e).", "llrrrr"))
    pg = pd.read_csv(AN2 / "pair_groups_by_length.csv").rename(columns={"US-US mean": "us", "Cw same country mean": "cw_same", "Cw cross country mean": "cw_cross", "US-Cw mean": "us_cw", "Cw cross minus US-Cw": "block"})
    parts.append(table(["Text", "$n$", "US pairs", "Cw. same-country", "Cw. cross-country", "US-Cw.", "Cw. cross minus US-Cw.", "$p$"], [[TX[r.text], int(r.n_inst), f3(r.us), f3(r.cw_same), f3(r.cw_cross), f3(r.us_cw), sg(r.block), fp(r.p)] for r in pg.itertuples(index=False)], "S4k. Pair groups at the endpoint (variant S7, all pages), by text length, and on the pre-shock integrity-page text of all sample institutions, cut to 600 words: mean similarity of United States pairs, Commonwealth (Cw.) pairs in the same country, Commonwealth pairs in different countries, and pairs of a United States and a Commonwealth institution. The last two columns ask whether the Commonwealth systems group together apart from the United States: Commonwealth cross-country minus United States-Commonwealth similarity, with a permutation $p$ (system labels shuffled over all institutions).", "lrrrrrrr"))
    pz = pd.read_csv(AN2 / "per_system_gap_by_length.csv")
    parts.append(table(["Text", "System", "$n$", "Same-country pairs", "Same mean", "Cross mean", "Gap", "$p$"], [[TX[r.text], r.system, int(r.n_inst), int(r.same_pairs), f3(r.same_mean), f3(r.cross_mean), sg(r.gap), fp(r.p)] for r in pz.itertuples(index=False)], "S4l. Per-system decomposition as in Table S4d (variant S7, all pages), by text length, and on the pre-shock integrity-page text of all sample institutions, cut to 600 words. The United States rows on full text, at 300 words, and on the pre-shock text repeat the US-vs-rest contrasts of Tables S4a and S4h with a separate draw of 2,000 permutations, so their $p$ values differ slightly.", "llrrrrrr"))
    lo = pd.read_csv(AN2 / "british_row_leave_one_out.csv"); bc = pd.read_csv(AN2 / "british_us_contrast.csv").iloc[0]
    pi = pd.read_csv(AN2 / "pair_per_institution.csv"); pu = pi[pi.system == "UK"].copy()
    closer = set(pu[pu.to_US > pu[["to_AU", "to_CA"]].mean(axis=1)].institution); longest = set(pu.nlargest(len(closer), "words").institution)
    tail = (f" the {nw(len(closer))} British institutions closer to American than to Australian and Canadian text are the {nw(len(closer))} with the longest AI text." if closer == longest
            else f" {nw(len(closer))} of the {nw(len(pu))} British institutions are closer to American than to Australian and Canadian text.")
    parts.append(table(["Left out", "Words", "UK-UK", "UK-US", "UK-AU", "UK-CA"], [[("none" if r.left_out == "none" else tex(r.left_out)), ("" if pd.isna(r.words_left_out) else int(r.words_left_out)), f3(r.UK_UK), f3(r.UK_US), f3(r.UK_AU), f3(r.UK_CA)] for r in lo.itertuples(index=False)], f"S4m. The British row of Table S4e with each of the six British institutions left out in turn (variant S7, all pages, full text), with the length in words of the left-out institution's AI text. On full text, British-American pairs exceed British-Australian and British-Canadian pairs by {bc.value:+.3f} ($p$ = {fp(bc.p)}, system labels shuffled among the non-British institutions), and" + tail, "lrrrrr"))
# ---------------- S5
if (AN / "density_summary.csv").exists():
    ds = pd.read_csv(AN / "density_summary.csv")
    parts.append(r"\section*{S5. Crawl density and interval-censored adoption}" + "\n")
    parts.append(table(["System", "Period", "Mean captures", "Median", "Share of page-quarters with none", "Share with none, from first capture", "Median days between captures"], [[r.system, tex(r.period), f2(r.mean_captures), f2(r.median_captures), f2(r.share_zero), f2(r.share_zero_from_first), f2(r.median_gap_days)] for r in ds.itertuples(index=False)], "S5a. Captures per page and quarter by system and period (daily-collapsed captures), on the sample's tracked pages. The capture grid runs from 2021Q1 to 2026Q2, one quarter past the panel endpoint. The share of page-quarters with no capture is given over every quarter of the grid and over the quarters from each page's first listed capture on; the first counts the quarters before a page existed, as for most AI guidance pages before the shock, as missing captures." + (" Over all periods, the share with no capture from each page's first capture is " + ", ".join(f"{f2(r.share_zero_from_first)} ({SYSN[r.system]})" for r in pd.read_csv(AN / "density_overall.csv").itertuples(index=False)) + "." if (AN / "density_overall.csv").exists() else ""), "llrrrrr"))
    if (AN / "density_summary_by_pagetype.csv").exists():
        dp = pd.read_csv(AN / "density_summary_by_pagetype.csv")
        parts.append(table(["System", "Page type", "Mean captures", "Median", "Share with none", "Share with none, from first capture"], [[r.system, r.page_type, f2(r.mean_captures), f2(r.median_captures), f2(r.share_zero), f2(r.share_zero_from_first)] for r in dp.itertuples(index=False)], "S5b. Captures per page and quarter by page type (every quarter of the grid, and from each page's first listed capture on).", "llrrrr"))
    if (AN / "density_exposure_correlation.csv").exists():
        dc = pd.read_csv(AN / "density_exposure_correlation.csv"); dc = dc[dc.density == "density_all"]
        parts.append(table(["System", "$n$", "Pearson $r$", "$p$", "Spearman", "$p$"], [[r.system, int(r.n), f2(r.pearson_r), f3(r.pearson_p), f2(r.spearman_rho), f3(r.spearman_p)] for r in dc.itertuples(index=False)], "S5c. Capture density (mean captures per page-quarter) against the international share of enrollment, sample institutions (the United States, the United Kingdom and Australia; no institution-level international share is published for Canada).", "lrrrrr"))
    if (AN / "adoption_summary.csv").exists():
        ad = pd.read_csv(AN / "adoption_summary.csv"); ad = ad[ad.flag == "clean_strict"]
        parts.append(table(["System", "Adopters", "Left-censored", "Interval width, median (days)", "Lag mean $R$", "Lag mean, midpoint", "Lag mean $L$", "Within 2 q. ($R$)", "Within 2 q. (mid)"], [[r.system, int(r.n_adopters), int(r.left_censored), f2(r.width_days_median), f2(r.lag_mean_q_R), f2(r.lag_mean_q_mid), f2(r.lag_mean_q_L), f2(r.share_within2q_q_R), f2(r.share_within2q_q_mid)] for r in ad.itertuples(index=False)], "S5d. Adoption timing under three conventions (strict vocabulary): the forward-fill convention $R$, the interval midpoint, and the left bound $L$; left-censored adopters have no capture of the page before the one carrying AI text, so the width, midpoint and $L$ columns are computed on the other adopters. Institutions whose tracked pages already carried AI text before the shock have no adoption date and are left out" + (f" ({nw(int(ad[ad.system == 'ALL'].n_pre_shock_positive_excluded.iloc[0]))} under the strict vocabulary)." if (ad.system == "ALL").any() else "."), "lrrrrrrrr"))
    if (AN / "adoption_turnbull.csv").exists():
        tb = pd.read_csv(AN / "adoption_turnbull.csv")
        if "subset" in tb.columns:
            for sub in tb.subset.unique():
                t = tb[(tb.subset == sub) & (tb.event_q.between(1, 8))]
                parts.append(table(["Quarter", "Turnbull mass", "Turnbull CDF", "Forward-fill mass", "Forward-fill CDF"], [[int(r.event_q), f3(r.turnbull_mass), f3(r.turnbull_cdf), f3(r.forward_fill_mass), f3(r.forward_fill_cdf)] for r in t.itertuples(index=False)], f"S5{'e' if sub == 'all' else 'f'}. Adoption-time distribution, quarters 1 to 8: Turnbull estimate versus forward-fill (strict vocabulary), {'all adopters' if sub == 'all' else 'adopters with an observed pre-change capture'} ($n$ = {int(t.n_adopters.iloc[0])}). Each adoption lies in the quarters from that of the last capture of the page before the change (quarter 0, the shock quarter 2022Q4, if that capture predates the shock) to that of the first capture carrying AI text" + ("; adopters with no earlier capture of the page are bounded below by the shock quarter." if sub == "all" else "."), "lrrrr"))
# ---------------- S6
parts.append(r"\section*{S6. The exposure differential}" + "\n")
if (AN / "exposure_robustness.csv").exists():
    er = pd.read_csv(AN / "exposure_robustness.csv")
    parts.append(table(["Outcome", "$n$", "Coef.", "SE", "$p$", "95\\% interval", "Adjusted coef.", "SE", "Late (q12--13) coef.", "Late, 95\\% interval", "LOO min", "LOO max", "Bootstrap 95\\%", "Bootstrap $p$"], [[tex(r.outcome), int(r.n_inst), sg(r.coef), f3(r.se_cluster), f3(r.p), f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", sg(r.coef_adjusted), f3(r.se_adjusted), sg(r.coef_late_q12_13), f"[{r.ci_lo_late:+.2f}, {r.ci_hi_late:+.2f}]", sg(r.loo_min), sg(r.loo_max), f"[{r.boot_ci_lo:+.2f}, {r.boot_ci_hi:+.2f}]", f3(r.boot_p_two_sided)] for r in er.itertuples(index=False)], "S6a. United States event study on the tracked-page design (strict vocabulary): exposure $\\times$ post coefficient with institution-clustered SE, $p$ and 95\\% interval; adjusted for private control $\\times$ post and log enrollment $\\times$ post; the late-quarter (12 to 13) interaction and its interval; leave-one-institution-out range; institution bootstrap (500 draws).", "lrrrrrrrrrrrrr"))
    if (AN / "exposure_terciles.csv").exists():
        et = pd.read_csv(AN / "exposure_terciles.csv")
        parts.append(table(["Tercile", "$n$", "Governance intensity", "Restrictive index", "Procedural index", "Net restrictiveness", "Addresses AI"], [[r.terc, int(r.n), f2(r.ai_governance_intensity), f2(r.restrictive_idx), f2(r.procedural_idx), f2(r.net_restrictiveness), f2(r.ai_addressed)] for r in et.itertuples(index=False)], "S6b. United States endpoint means by exposure tercile (strict vocabulary).", "lrrrrrr"))
    if (AN / "exposure_corr.csv").exists():
        ec = pd.read_csv(AN / "exposure_corr.csv")
        parts.append(table(["System", "$n$", "Outcome", "$r$", "95\\% interval", "Institutions with a value above zero"], [[r.system, int(r.n), tex(r.outcome), f2(r.r), f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", int(r.n_with_any_provision)] for r in ec.itertuples(index=False)], "S6c. Endpoint correlations between the international share and the provision indices, by system (the United Kingdom, Australia and the United States; no institution-level international share is published for Canada), with Fisher intervals.", "lrlrrr"))
ev = pd.read_csv(AN / "event_study_variants.csv"); ev = ev[ev.kind == "did_exposure_x_post"]
parts.append(table(["Rule (automated discovery design)", "$n$", "Outcome", "Coef.", "SE", "$p$"], [[tex(r.variant), int(r.n_inst), tex(r.outcome), sg(r.coef), f3(r.se), f3(r.p)] for r in ev.itertuples(index=False)], "S6d. Exposure $\\times$ post coefficients under the automated discovery design (robustness), computed on its original retrieval and sample (" + f"{int(ev.n_inst.max())}" + " United States institutions, among them the one institution left out of the tracked-page design); 30 coefficients (six page rules by five outcomes) are shown, so individual $p$ values near 0.05 should be read with that in mind.", "lrlrrr"))
if (AN / "exposure_page_rule.csv").exists():
    epr = pd.read_csv(AN / "exposure_page_rule.csv")
    parts.append(table(["Outcome", "$n$", "Coef.", "SE", "95\\% interval", "$p$"], [[tex(r.outcome), int(r.n_inst), sg(r.coef), f3(r.se_cluster), f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", f3(r.p)] for r in epr.itertuples(index=False)], "S6e. Exposure $\\times$ post coefficients (institution-clustered SE) on the United States institutions that meet the entry rule page by page: those observed after the shock only on an AI guidance page first archived after it are left out. Exposure is standardized on all United States institutions, as in Table S6a.", "lrrrrr"))
if (AN / "exposure_by_provision.csv").exists():
    eb = pd.read_csv(AN / "exposure_by_provision.csv", dtype={"without_unitid": str})
    def _lab(r): return tex(r.outcome.replace("_present", "")) + (f" without {tex(r.without_institution)}" if isinstance(r.without_institution, str) and r.without_institution else "")
    parts.append(table(["Outcome", "$n$", "Coef.", "SE", "95\\% interval", "$p$", "Flagged at the endpoint"], [[_lab(r), int(r.n_inst), sg(r.coef), f3(r.se_cluster), f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", f3(r.p), ("" if pd.isna(r.n_inst_flagged_endpoint) else int(r.n_inst_flagged_endpoint))] for r in eb.itertuples(index=False)], "S6f. Exposure $\\times$ post coefficients (institution-clustered SE) provision by provision on the United States panel of Table S6a: each provision's presence, permitted use and disclosure together, and the procedural index without the institution whose removal moves it most (the leave-one-out minimum of Table S6a). The four procedural provisions add up to the procedural index, so their coefficients add up to its coefficient. The last column counts the institutions flagged at the endpoint.", "lrrrrrr"))
parts.append(r"\end{document}" + "\n")
_tex = "".join(parts).replace(" [Table 2]", "")
_tex = re.sub(r"(\\section\*\{S4\. Convergence\}\n[^\n]+\n)(\\begin\{landscape\})", r"\2\1", _tex)  # the S4 heading and its paragraph share the first landscape page
_tex = re.sub(r"(\\section\*\{[^}]*\})\n(\\begin\{landscape\})", r"\2\1", _tex)  # a heading directly before a landscape table goes with it
OUT.write_text(_tex); print("wrote", OUT)
