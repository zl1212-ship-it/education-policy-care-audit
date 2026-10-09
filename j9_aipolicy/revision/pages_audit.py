"""Pages per institution, junk / duplicate / policy-like classification, endpoint prevalence under
alternative page rules (with the corrected feasibility filter), linked policy PDFs, and the
max-over-pages note (reviewer points 5b, 5c). Reads scored_raw_vs_clean.csv and the committed
pipeline files. Writes pages_per_institution.csv, pages_summary.csv, prevalence_by_pagerule.csv,
panel_samples.csv, matched_policy_pages_us.csv, policy_pages.csv, junk_pages.csv, matched_pages_us.csv,
pdf_links.csv, pdf_links_summary.csv, maxpages_note.csv, staleness.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import re, sys
from pathlib import Path
from urllib.parse import urljoin
import numpy as np, pandas as pd
import lxml.html

sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B
SHOCK = pd.Timestamp("2022-11-30")
PROV = list(B.PROVISIONS.keys())
RESTR, PROC = B.RESTRICTIVE, B.PROCEDURAL
SYSTEMS = ["US", "UK", "AU", "CA"]
pd.set_option("display.width", 250)

sc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
sc["ts"] = pd.to_datetime(sc["timestamp"], format="%Y%m%d%H%M%S")
sc["page_key"] = sc["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
urlset = pd.read_csv(AN / "url_set.csv", dtype=str)
key2url = dict(zip(urlset["page_key"], urlset["query_url"].fillna("")))
sc["real_url"] = sc.apply(lambda r: r["original_url"] if r["pipeline"] == "XN" else (key2url.get(r["page_key"], "") or r["original_url"]), axis=1)

def norm_url(u):
    u = str(u).lower().strip()
    u = re.sub(r"^https?://", "", u); u = re.sub(r"^www\.", "", u)
    u = u.split("#")[0].split("?")[0]
    u = re.sub(r"/(index\.(html?|php|aspx?))?$", "", u)
    return u

# ----------------------------------------------------------------------------- (1) pages
JUNK_URL = re.compile(
    r"robots\.txt|\?q=|/catalog/\?|search_field|/f/subject|/f/author|/degree-charts/|/costs/|/costs$|"
    r"/certificate-programs/|/browse/|honor-society|reappointment|-embed$|/profile|/directory|sitemap|\.xml$|/feed|"
    r"/archive/20\d\d-20\d\d/.*(computer-science|artificial-intel|mit-research|courses?)|/courses?/[a-z]{2,5}-?\d|eeo-courses|"
    r"/tag/|/author/|/category/|/page/\d|/print/|/node/\d+/revisions|\?page=\d|/people/|/staff/[a-z]|inauguration|/calendar", re.I)
PROGRAM_URL = re.compile(
    r"catalog|bulletin|/programs?/|/program\b|certificate|degree|/courses?\b|/course\b|/majors?\b|/minors?\b|admission|tuition|"
    r"honors|honours|conducting|award|symposium|/events?\b|/event/|/people/|/staff/|/archive/|-embed$|/print/|/search", re.I)
INTEG_CONTENT = re.compile(r"academic integrity|academic misconduct|plagiar|honor code|honour code|academic honesty|academic dishonesty|"
                           r"cheating|code of conduct|student conduct|academic conduct|contract cheating|collusion", re.I)

pages = sc.groupby(["pipeline", "system", "institution", "unitid", "page_type", "page_key"]).agg(
    real_url=("real_url", "first"), local_path_last=("local_path", "last"), n_caps=("ts", "size"), first_ts=("ts", "min"), last_ts=("ts", "max"),
    any_ai_clean=("ai_addressed_clean", "max"), any_ai_raw=("ai_addressed_raw", "max"), any_ai_strict=("ai_addressed_clean_strict", "max"),
    words_clean_max=("words_clean", "max")).reset_index()
anyprov = sc.groupby(["unitid", "page_key"])[[f"{p}_present_raw" for p in PROV]].max().max(axis=1).rename("any_prov_raw").reset_index()
pages = pages.merge(anyprov, on=["unitid", "page_key"], how="left")
# content check on the latest capture's clean text (integrity vocabulary)
def integ_hits(row):
    base = PIPE if row["pipeline"] == "US" else XN
    try:
        return len(INTEG_CONTENT.findall(E.extract_text_clean(base / row["local_path_last"])))
    except Exception:
        return 0
pages["integ_content_hits"] = pages.apply(integ_hits, axis=1)
pages["canon"] = pages["real_url"].apply(norm_url)
pages["junk_url"] = pages["real_url"].apply(lambda u: bool(JUNK_URL.search(str(u)))).astype(int)
pages["inert"] = ((pages["any_ai_clean"] == 0) & (pages["any_ai_raw"] == 0) & (pages["any_prov_raw"] == 0)).astype(int)
pages["junk"] = ((pages["junk_url"] == 1) | ((pages["page_type"] == "ai") & (pages["any_ai_raw"] == 0))).astype(int)
# duplicates: same institution + same canonical URL (http/https/www/trailing-slash/utm variants): keep the most captured
pages["duplicate"] = 0
for (uid, canon), g in pages.groupby(["unitid", "canon"]):
    if len(g) > 1:
        keep = g.sort_values(["n_caps", "page_key"], ascending=[False, True]).index[0]
        pages.loc[[i for i in g.index if i != keep], "duplicate"] = 1
pages["program_url"] = pages["real_url"].apply(lambda u: bool(PROGRAM_URL.search(str(u)))).astype(int)
us = pages.pipeline == "US"
pages["policy_like"] = 1
pages.loc[us, "policy_like"] = ((pages.loc[us, "junk"] == 0) & (pages.loc[us, "duplicate"] == 0) & (pages.loc[us, "program_url"] == 0)
                                & (((pages.loc[us, "page_type"] == "integrity") & (pages.loc[us, "integ_content_hits"] >= 2))
                                   | ((pages.loc[us, "page_type"] == "ai") & (pages.loc[us, "any_ai_strict"] == 1)))).astype(int)
panel_orig = set(pd.read_csv(PIPE / "data/panel.csv", dtype=str).unitid) | set(pd.read_csv(XN / "data/panel.csv", dtype=str).unitid)
pages["in_panel"] = pages["unitid"].isin(panel_orig).astype(int)
pages.to_csv(AN / "pages_per_institution.csv", index=False)

def summarize_pages(df, label):
    g = df.groupby(["system", "unitid"]).agg(n=("page_key", "size"), n_ai=("page_type", lambda s: (s == "ai").sum()), n_integ=("page_type", lambda s: (s == "integrity").sum()))
    out = g.groupby("system").agg(inst=("n", "size"), pages_mean=("n", "mean"), pages_median=("n", "median"), pages_min=("n", "min"), pages_max=("n", "max"),
                                  ai_pages_mean=("n_ai", "mean"), integ_pages_mean=("n_integ", "mean")).reindex(SYSTEMS)
    out.insert(0, "page_set", label); return out.reset_index()
ps = pd.concat([summarize_pages(pages, "all tracked"), summarize_pages(pages[pages.duplicate == 0], "distinct canonical URLs"),
                summarize_pages(pages[(pages.junk == 0) & (pages.duplicate == 0)], "non-junk"),
                summarize_pages(pages[(pages.junk == 0) & (pages.inert == 0) & (pages.duplicate == 0)], "non-junk and not inert"),
                summarize_pages(pages[pages.policy_like == 1], "policy-like (US: URL + content screen)"),
                summarize_pages(pages[pages.in_panel == 1], "all tracked, panel institutions only")])
ps.to_csv(AN / "pages_summary.csv", index=False)
print("=== pages per institution ===\n" + ps.round(2).to_string(index=False))
print("\njunk:", pages.groupby("system")["junk"].sum().to_dict(), " inert:", pages.groupby("system")["inert"].sum().to_dict(),
      " duplicates:", pages.groupby("system")["duplicate"].sum().to_dict(), " program-URL (US):", int(pages[us]["program_url"].sum()))
print("US pages policy-like by type:", pages[us].groupby("page_type")["policy_like"].agg(["sum", "size"]).to_dict())
print("US integrity pages whose URL says honors/honours/honor-society:", int(pages[us & (pages.page_type == "integrity")].real_url.str.contains(r"honors|honours|honor-society", case=False, na=False).sum()), "of", int((us & (pages.page_type == "integrity")).sum()))
print("US AI pages whose URL is catalog/program/course/certificate/degree:", int(pages[us & (pages.page_type == "ai")].real_url.str.contains(r"catalog|bulletin|/programs?/|certificate|degree|/courses?/|/majors?/|/minors?/", case=False, na=False).sum()), "of", int((us & (pages.page_type == "ai")).sum()))

# ----------------------------------------------------------------------------- (2) feasibility filters and endpoint prevalence
def load_cov(path):
    c = pd.read_csv(path, dtype={"unitid": str}); c = c[c["n_captures"] > 0].copy()
    c["unitid"] = c["unitid"].astype(str).str.replace(r"\.0$", "", regex=True)
    return c
cov_main = pd.concat([load_cov(PIPE / "data/coverage.csv"), load_cov(XN / "data/coverage.csv")], ignore_index=True)
cov_pre = load_cov(PIPE / "data/coverage_pre2026.csv") if (PIPE / "data/coverage_pre2026.csv").exists() else cov_main.iloc[0:0]
haspost_main = cov_main.groupby("unitid")["has_post"].max()
haspost_idx = (sc[sc.ts >= SHOCK].groupby("unitid").size() > 0).astype(int)
haspost_pre = cov_pre.groupby("unitid")["has_post"].max() if len(cov_pre) else pd.Series(dtype=int)
n_pre = sc[sc.ts < SHOCK].groupby("unitid").size()
all_uids = list(sc["unitid"].unique())
uids_orig = [u for u in all_uids if n_pre.get(u, 0) >= 1 and int(haspost_main.get(u, 0)) == 1]
uids_fixed = [u for u in all_uids if n_pre.get(u, 0) >= 1 and max(int(haspost_main.get(u, 0)), int(haspost_idx.get(u, 0)), int(haspost_pre.get(u, 0))) == 1]
sysmap = sc.groupby("unitid")["system"].first().to_dict()
samples = pd.DataFrame({"unitid": sorted(set(uids_orig) | set(uids_fixed))})
samples["system"] = samples.unitid.map(sysmap); samples["in_original_filter"] = samples.unitid.isin(uids_orig).astype(int); samples["in_corrected_filter"] = samples.unitid.isin(uids_fixed).astype(int)
samples["institution"] = samples.unitid.map(sc.groupby("unitid")["institution"].first().to_dict())
samples.to_csv(AN / "panel_samples.csv", index=False)
print(f"\nfeasibility filter: original {len(uids_orig)} (matches committed 110: {set(uids_orig) == panel_orig}); corrected {len(uids_fixed)}; restored:",
      samples[(samples.in_original_filter == 0) & (samples.in_corrected_filter == 1)][["system", "institution"]].values.tolist())
QENDS = pd.period_range("2021Q1", "2026Q1", freq="Q").to_timestamp(how="end")
def event_quarter(ts): return (ts.year - 2022) * 4 + (ts.quarter - 4)

def build_endpoint(snaps, suffix, uids, label):
    """build_panel.main's logic: per page forward-fill on the full quarterly grid, max over pages,
    last row per institution; institutions in `uids` with no page in `snaps` get a zero row."""
    pres = [f"{p}_present{suffix}" for p in PROV]
    aa = "ai_addressed_clean_strict" if "strict" in suffix else ("ai_addressed_clean" if "clean" in suffix else "ai_addressed_raw")
    carry = pres + [aa]
    rows = []
    for uid in uids:
        series = []
        for pg, sp in snaps[snaps["unitid"] == uid].groupby("page_key"):
            sp = sp.sort_values("ts")
            asof = pd.merge_asof(pd.DataFrame({"ts": QENDS}), sp[["ts"] + carry], on="ts", direction="backward")
            asof[carry] = asof[carry].fillna(0); series.append(asof)
        if series:
            agg = pd.concat(series).groupby("ts", as_index=False)[carry].max(); last = agg.iloc[-1]
        else:
            last = pd.Series({c: 0 for c in carry})
        r = {"unitid": uid, "system": sysmap[uid], "ai_addressed": last[aa], "has_page": int(bool(series))}
        for p in PROV: r[p] = last[f"{p}_present{suffix}"]
        r["restrictive_idx"] = sum(r[p] for p in RESTR); r["procedural_idx"] = sum(r[p] for p in PROC); rows.append(r)
    d = pd.DataFrame(rows)
    out = d.groupby("system").agg(n=("unitid", "size"), n_with_page=("has_page", "sum"), ai_addressed=("ai_addressed", "mean"), **{p: (p, "mean") for p in PROV},
                                  restrictive_idx=("restrictive_idx", "mean"), procedural_idx=("procedural_idx", "mean")).reindex(SYSTEMS)
    out.insert(0, "rule", label); return out.reset_index(), d

results, inst_level = [], {}
comm = pd.concat([pd.read_csv(PIPE / "data/panel.csv", dtype={"unitid": str}), pd.read_csv(XN / "data/panel.csv", dtype={"unitid": str})])
comm["system"] = comm["unitid"].map(sysmap)
last = comm.sort_values("event_q").groupby("unitid").tail(1)
rep = last.groupby("system").agg(n=("unitid", "size"), ai_addressed=("ai_addressed", "mean"), **{p: (f"{p}_present", "mean") for p in PROV},
                                 restrictive_idx=("restrictive_idx", "mean"), procedural_idx=("procedural_idx", "mean")).reindex(SYSTEMS)
rep.insert(0, "rule", "committed panel.csv (last row per institution)"); rep.insert(2, "n_with_page", rep["n"]); results.append(rep.reset_index())
r_a, d_a = build_endpoint(sc, "_raw", uids_orig, "(a) raw text, all pages, original filter [Table 2]"); results.append(r_a); inst_level["a"] = d_a
diff = (r_a.set_index("system").drop(columns=["rule", "n_with_page"]) - rep.drop(columns=["rule", "n_with_page"])).abs().max().max()
print(f"\n=== replication of Table 2 from the committed panels: max abs difference = {diff:.4f} ===")
r_a2, _ = build_endpoint(sc, "_raw", uids_fixed, "(a2) raw text, all pages, corrected filter"); results.append(r_a2)
r_b, d_b = build_endpoint(sc, "_clean", uids_fixed, "(b) clean text, all pages"); results.append(r_b); inst_level["b"] = d_b
r_c, _ = build_endpoint(sc[sc.page_type == "integrity"], "_clean", uids_fixed, "(c) clean text, integrity pages only"); results.append(r_c)
r_d, _ = build_endpoint(sc[sc.page_type == "ai"], "_clean", uids_fixed, "(d) clean text, AI pages only (zero where no AI page)"); results.append(r_d)
# matched selections for the US: seed by normalized URL (equality, then prefix), else the best policy-like page by content
frame_us = pd.read_csv(PIPE / "data/sample_frame.csv", dtype=str)
def pick_pages(policy_only):
    keep, attrition = set(), []
    for r in frame_us.itertuples(index=False):
        uid = str(r.unitid)
        inst_pages = pages[(pages.unitid == uid) & (pages.duplicate == 0)]
        if policy_only: inst_pages = inst_pages[inst_pages.policy_like == 1]
        for ptype, seed in (("integrity", r.integrity_url), ("ai", getattr(r, "guidance_url", ""))):
            cand = inst_pages[inst_pages.page_type == ptype]
            if len(cand) == 0:
                attrition.append((uid, ptype)); continue
            hit = pd.DataFrame()
            if isinstance(seed, str) and seed:
                ns = norm_url(seed); hit = cand[cand.canon == ns]
                if len(hit) == 0: hit = cand[cand.canon.str.startswith(ns + "/")]
            if len(hit) == 0:
                score = cand["integ_content_hits"] if ptype == "integrity" else cand["any_ai_strict"] * 1000 + cand["words_clean_max"]
                hit = cand.assign(_s=score).sort_values("_s", ascending=False).head(1)
            keep.add((uid, hit.iloc[0]["page_key"]))
    return keep, attrition
keep_e, attr_e = pick_pages(policy_only=False)
keep_k, attr_k = pick_pages(policy_only=True)
pd.DataFrame(sorted(keep_e), columns=["unitid", "page_key"]).to_csv(AN / "matched_pages_us.csv", index=False)
pd.DataFrame(sorted(keep_k), columns=["unitid", "page_key"]).to_csv(AN / "matched_policy_pages_us.csv", index=False)
policy_keys = set(zip(pages[pages.policy_like == 1].unitid, pages[pages.policy_like == 1].page_key))
pd.DataFrame(sorted(policy_keys), columns=["unitid", "page_key"]).to_csv(AN / "policy_pages.csv", index=False)
junk_keys = set(zip(pages[(pages.junk == 1) | (pages.duplicate == 1)].unitid, pages[(pages.junk == 1) | (pages.duplicate == 1)].page_key))
pd.DataFrame(sorted(junk_keys), columns=["unitid", "page_key"]).to_csv(AN / "junk_pages.csv", index=False)
mask_e = (sc.pipeline == "XN") | sc.apply(lambda r: (r["unitid"], r["page_key"]) in keep_e, axis=1)
mask_k = (sc.pipeline == "XN") | sc.apply(lambda r: (r["unitid"], r["page_key"]) in keep_k, axis=1)
mask_g = sc.apply(lambda r: (r["unitid"], r["page_key"]) not in junk_keys, axis=1)
mask_j = sc.apply(lambda r: (r["unitid"], r["page_key"]) in policy_keys, axis=1)
r_e, d_e = build_endpoint(sc[mask_e], "_clean", uids_fixed, "(e) clean text, US matched 1 integrity + 1 AI page (seed or best page)"); results.append(r_e); inst_level["e"] = d_e
r_f2, _ = build_endpoint(sc, "_clean_w200", uids_fixed, "(f) clean text, window 200"); results.append(r_f2)
r_f8, _ = build_endpoint(sc, "_clean_w800", uids_fixed, "(f) clean text, window 800"); results.append(r_f8)
r_g, _ = build_endpoint(sc[mask_g], "_clean", uids_fixed, "(g) clean text, junk and duplicate pages dropped"); results.append(r_g)
r_h, _ = build_endpoint(sc, "_clean_strict", uids_fixed, "(h) clean text, strict AI terms (no bare AI), all pages"); results.append(r_h)
r_j, d_j = build_endpoint(sc[mask_j], "_clean_strict", uids_fixed, "(j) clean, strict AI terms, US policy-like pages only"); results.append(r_j); inst_level["j"] = d_j
r_k, d_k = build_endpoint(sc[mask_k], "_clean_strict", uids_fixed, "(k) clean, strict AI terms, US policy-like matched 1+1"); results.append(r_k); inst_level["k"] = d_k
prev = pd.concat(results, ignore_index=True); prev.to_csv(AN / "prevalence_by_pagerule.csv", index=False)
print("\n=== endpoint prevalence by page rule ===\n" + prev.round(3).to_string(index=False))
print("\nmatched-page attrition (US institutions lacking a page of the type): rule e", len(attr_e), "rule k", len(attr_k),
      "| rule k AI pages missing for:", sorted({sysmap.get(u, '') + ':' + str(u) for u, t in attr_k if t == 'ai'})[:60])

# ----------------------------------------------------------------------------- staleness of the forward-filled endpoint (point 4)
last_cap = sc[sc.ts <= "2026-03-31"].groupby("unitid")["ts"].max().rename("last_capture")
st = samples.merge(last_cap, on="unitid", how="left"); st["stale_before_2025"] = (st.last_capture < "2025-01-01").astype(int)
st_s = st[st.in_corrected_filter == 1].groupby("system").agg(n=("unitid", "size"), last_capture_median=("last_capture", "median"), stale_before_2025=("stale_before_2025", "sum")).reindex(SYSTEMS)
st.to_csv(AN / "staleness.csv", index=False); print("\n=== endpoint staleness (last downloaded capture per institution) ===\n" + st_s.to_string())

# ----------------------------------------------------------------------------- (4) max-over-pages note
note = []
endpoint_pages = sc[sc.ts <= "2026-03-31"].sort_values("ts").groupby(["unitid", "page_key"]).tail(1)
endpoint_pages = endpoint_pages[endpoint_pages.unitid.isin(uids_fixed)]
for p in PROV + ["ai_addressed"]:
    col = f"{p}_present_clean" if p != "ai_addressed" else "ai_addressed_clean"
    per_inst = endpoint_pages.groupby(["system", "unitid"])[col].sum(); multi = endpoint_pages.groupby(["system", "unitid"])["page_key"].nunique()
    for s in SYSTEMS:
        pi = per_inst.xs(s, level="system") if s in per_inst.index.get_level_values(0) else pd.Series(dtype=float)
        mu = multi.xs(s, level="system") if s in multi.index.get_level_values(0) else pd.Series(dtype=float)
        flagged = pi[pi > 0]
        note.append({"provision": p, "system": s, "inst_flagged_any_page": int((pi > 0).sum()), "flag_from_exactly_one_page": int((flagged == 1).sum()),
                     "flag_from_two_plus_pages": int((flagged >= 2).sum()), "inst_with_multiple_pages": int((mu > 1).sum())})
note = pd.DataFrame(note)
us_b = d_b[d_b.system == "US"].set_index("unitid"); us_k = d_k[d_k.system == "US"].set_index("unitid")
lost = {p: int(((us_b[p] == 1) & (us_k.reindex(us_b.index)[p].fillna(0) == 0)).sum()) for p in PROV + ["ai_addressed"]}
note["us_flags_lost_under_rule_k"] = note["provision"].map(lost).where(note["system"] == "US"); note.to_csv(AN / "maxpages_note.csv", index=False)
print("\n=== US endpoint flags (rule b) lost under the policy-like matched design (rule k), same institutions ===\n", lost)

# ----------------------------------------------------------------------------- (3) linked PDFs
POLICY = re.compile(r"integrity|misconduct|conduct|plagiar|honest|cheat|\bai\b|artificial|generative|chatgpt|policy|policies|procedure|regulation|code|guideline|guidance|rule|statute|ordinance|handbook|assessment|discipline", re.I)
rows = []
ep = sc[sc.ts <= "2026-03-31"].sort_values("ts").groupby(["unitid", "page_key"]).tail(1)
for r in ep.itertuples(index=False):
    base = PIPE if r.pipeline == "US" else XN
    try: root = E._parse(E._read_bytes(base / r.local_path))
    except Exception: root = None
    if root is None: continue
    seen = set()
    for a in root.iter("a"):
        href = a.get("href") or ""
        if not re.search(r"\.pdf(\?|#|$)", href, re.I): continue
        full = urljoin(r.real_url if str(r.real_url).startswith("http") else "https://" + str(r.real_url), href)
        if full in seen: continue
        seen.add(full)
        anchor = " ".join(a.text_content().split())[:200]
        rows.append({"system": r.system, "institution": r.institution, "unitid": r.unitid, "page_type": r.page_type, "page_key": r.page_key,
                     "page_words_clean": r.words_clean, "pdf_url": full, "anchor": anchor, "policy_relevant": int(bool(POLICY.search(anchor) or POLICY.search(href)))})
pdf = pd.DataFrame(rows); pdf["in_panel"] = pdf["unitid"].isin(uids_fixed).astype(int); pdf.to_csv(AN / "pdf_links.csv", index=False)
inst_all = ep[ep.unitid.isin(uids_fixed)].groupby("system")["unitid"].nunique().reindex(SYSTEMS)
pdf_p = pdf[pdf.in_panel == 1]; pdf_rel = pdf_p[pdf_p.policy_relevant == 1]
summ = pd.DataFrame({"panel_institutions": inst_all, "inst_linking_any_pdf": pdf_p.groupby("system")["unitid"].nunique().reindex(SYSTEMS).fillna(0).astype(int),
                     "inst_linking_policy_pdf": pdf_rel.groupby("system")["unitid"].nunique().reindex(SYSTEMS).fillna(0).astype(int),
                     "policy_pdf_links_per_inst": (pdf_rel.groupby("system").size().reindex(SYSTEMS).fillna(0) / inst_all).round(2)})
summ["share_inst_linking_policy_pdf"] = (summ["inst_linking_policy_pdf"] / summ["panel_institutions"]).round(2)
short = ep[(ep.page_type == "integrity") & (ep.words_clean < 400)]; short_keys = set(zip(short.unitid, short.page_key))
pdf_rel_short = pdf_rel[[(u, k) in short_keys for u, k in zip(pdf_rel.unitid, pdf_rel.page_key)]]
summ["inst_short_integrity_page_linking_policy_pdf"] = pdf_rel_short.groupby("system")["unitid"].nunique().reindex(SYSTEMS).fillna(0).astype(int)
summ.to_csv(AN / "pdf_links_summary.csv")
print("\n=== linked PDFs at the endpoint (panel institutions, corrected filter) ===\n" + summ.to_string())
for s in SYSTEMS: print(s, pdf_rel[pdf_rel.system == s]["anchor"].str.lower().value_counts().head(6).to_dict())
print("\ntracked pages that are PDFs:", pages[pages.real_url.str.contains(r"\.pdf", case=False, na=False)][["system", "institution", "page_type"]].drop_duplicates().values.tolist())
print("done")
