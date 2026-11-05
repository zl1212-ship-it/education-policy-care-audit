"""Symmetric page design: every institution observed on one curated integrity page and (where one
exists) one curated AI guidance page. US pages come from seed_snapshot_index.csv (fetch_us_seeds.py),
cross-national pages from the committed pipeline. Scores the seed snapshots (clean + strict), builds
the institution-by-quarter panels, the endpoint prevalence table (with and without linked policy
PDFs), and the US event-study panel. The versions in force at quarter ends that the original
retrieval missed (fetch_quarter_versions.py) are scored and merged with the retrieved versions. The
corrections in sample_corrections.py (one institution left out, three page types corrected) are
applied before the sample is drawn. seed_samples.csv
also flags (page_rule) the institutions that meet the entry rule page by page, and the prevalence
table adds that sample as a robustness row. Outputs: scored_seed.csv, seed_panel_<variant>.csv,
seed_prevalence.csv, seed_samples.csv, seed_pages.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import csv, re, sys, time, subprocess
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(REV))
import extract_clean as E
import sample_corrections as SCOR
B = E.B
SHOCK = pd.Timestamp("2022-11-30"); ENDPOINT = pd.Timestamp("2026-03-31")
PROV = list(B.PROVISIONS.keys()); RESTR, PROC = B.RESTRICTIVE, B.PROCEDURAL; SYSTEMS = ["US", "UK", "AU", "CA"]
STRICT_AI = re.compile(r"artificial intelligence|generative a\.?i\.?|gen(?:erative)?\s?ai|chat\s?gpt|large language model|\bllms?\b|\bgpt\b", re.I)
QENDS = pd.period_range("2021Q1", "2026Q1", freq="Q").to_timestamp(how="end")
def event_quarter(ts): return (ts.year - 2022) * 4 + (ts.quarter - 4)
def score_strict(text, window=400):
    keep = B.AI_TERMS; B.AI_TERMS = STRICT_AI
    try: return B.score_text(text, window)
    finally: B.AI_TERMS = keep

# ---------------------------------------------------------------- 1. score the seed snapshots and the quarter-end versions
def score_index(idx_file, pipeline, out_file):
    idx = pd.read_csv(AN / idx_file, dtype={"unitid": str, "timestamp": str})
    idx["bytes"] = pd.to_numeric(idx["bytes"], errors="coerce").fillna(0); idx = idx[idx["bytes"] > 0]
    idx = idx.drop_duplicates(["unitid", "local_path"])
    rows = []
    for i, r in enumerate(idx.itertuples(index=False), 1):
        path = AN / r.local_path
        if not path.exists(): continue
        try: raw = B.extract_text(path)
        except Exception: raw = ""
        try: clean, rule = E.extract_clean_info(path)
        except Exception as e: clean, rule = "", f"error:{type(e).__name__}"
        sr, sc, ss = B.score_text(raw, 400), B.score_text(clean, 400), score_strict(clean, 400)
        s2, s8 = score_strict(clean, 200), score_strict(clean, 800)
        row = {"pipeline": pipeline, "system": getattr(r, "system", "US"), "institution": r.institution, "unitid": r.unitid, "page_type": r.page_type,
               "original_url": r.original_url, "local_path": r.local_path, "timestamp": r.timestamp, "words_raw": len(raw.split()),
               "words_clean": len(clean.split()), "rule_fired": rule, "ai_addressed_raw": sr["ai_addressed"], "n_ai_terms_raw": sr["n_ai_terms"],
               "ai_addressed_clean": sc["ai_addressed"], "n_ai_terms_clean": sc["n_ai_terms"], "ai_addressed_clean_strict": ss["ai_addressed"],
               "n_ai_terms_clean_strict": ss["n_ai_terms"]}
        for p in PROV:
            row[f"{p}_raw"] = sr[p]; row[f"{p}_present_raw"] = sr[p + "_present"]; row[f"{p}_clean"] = sc[p]; row[f"{p}_present_clean"] = sc[p + "_present"]
            row[f"{p}_present_clean_strict"] = ss[p + "_present"]
            row[f"{p}_present_clean_strict_w200"] = s2[p + "_present"]; row[f"{p}_present_clean_strict_w800"] = s8[p + "_present"]
        rows.append(row)
        if i % 200 == 0: print(f"  scored {i}/{len(idx)}", flush=True)
    d = pd.DataFrame(rows); d.to_csv(AN / out_file, index=False); return d

def score_seed(): return score_index("seed_snapshot_index.csv", "USSEED", "scored_seed.csv")
def score_quarter_versions(): return score_index("quarter_versions_index.csv", "QV", "scored_quarter_versions.csv")

# ---------------------------------------------------------------- 2. assemble the symmetric snapshot table
BACKFILL = "--backfill" in sys.argv  # US institutions whose curated page was never archived: use the best policy page found by discovery


def assemble():
    seed = pd.read_csv(AN / "scored_seed.csv", dtype={"unitid": str, "timestamp": str})
    allsc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
    xn = allsc[allsc.pipeline == "XN"]
    cols = [c for c in seed.columns if c in xn.columns]
    parts = [seed[cols], xn[cols]]
    if BACKFILL:
        us = allsc[allsc.pipeline == "US"].copy(); us["page_key"] = us["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
        matched = pd.read_csv(AN / "matched_policy_pages_us.csv", dtype=str)
        have = seed.groupby(["unitid", "page_type"]).size().reset_index()[["unitid", "page_type"]]
        have = set(zip(have.unitid, have.page_type))
        keep = []
        for r in matched.itertuples(index=False):
            pt = us[(us.unitid == r.unitid) & (us.page_key == r.page_key)]["page_type"]
            if len(pt) and (r.unitid, pt.iloc[0]) not in have:
                keep.append((r.unitid, r.page_key))
        back = us[[(u, k) in set(keep) for u, k in zip(us.unitid, us.page_key)]]
        back = back.assign(pipeline="USBACKFILL")
        print(f"backfill: {back.groupby(['unitid']).size().shape[0]} US institutions get {len(keep)} discovered policy pages for types the curated page did not cover", flush=True)
        pd.DataFrame(keep, columns=["unitid", "page_key"]).to_csv(AN / "seed_backfill_pages.csv", index=False)
        parts.append(back[cols])
    if (AN / "scored_quarter_versions.csv").exists():  # versions in force at quarter ends that the original retrieval missed
        parts.append(pd.read_csv(AN / "scored_quarter_versions.csv", dtype={"unitid": str, "timestamp": str})[cols])
    sc = pd.concat(parts, ignore_index=True)
    sc["ts"] = pd.to_datetime(sc["timestamp"], format="%Y%m%d%H%M%S")
    sc["page_key"] = sc["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
    return sc

def feasibility(sc):
    """pre-shock capture on any page AND page alive on/after the shock (CDX has_post from the seed
    coverage for the US, the committed coverage files for the cross-national pipeline, or any
    downloaded capture on/after the shock)."""
    n_pre = sc[sc.ts < SHOCK].groupby("unitid").size()
    haspost = (sc[sc.ts >= SHOCK].groupby("unitid").size() > 0).astype(int).to_dict()
    for f in (AN / "seed_coverage.csv", XN / "data/coverage.csv"):
        if f.exists():
            c = pd.read_csv(f, dtype={"unitid": str}); c = c[c.n_captures > 0]
            for uid, hp in c.groupby("unitid")["has_post"].max().items():
                uid = str(uid).replace(".0", ""); haspost[uid] = max(haspost.get(uid, 0), int(hp))
    uids = [u for u in sc.unitid.unique() if n_pre.get(u, 0) >= 1 and haspost.get(u, 0) == 1]
    return sorted(uids)

def page_rule(sc):
    """The entry rule applied page by page (robustness): institutions with one tracked page captured
    before the shock and still captured on or after it, by a downloaded capture or a capture listing
    (curated and cross-national pages: the coverage files, matched by institution and recorded page
    type; screened pages: their listing in screened_cdx_captures.csv, matched by page key)."""
    listed = set()
    for f in (AN / "seed_coverage.csv", XN / "data/coverage.csv"):
        if f.exists():
            c = pd.read_csv(f, dtype={"unitid": str}); c = c[(c.n_captures > 0) & (c.has_post == 1)]
            listed |= {(str(u).replace(".0", ""), t) for u, t in zip(c.unitid, c.page_type)}
    listed_keys = set()
    if (AN / "screened_cdx_captures.csv").exists():
        l = pd.read_csv(AN / "screened_cdx_captures.csv", dtype=str)
        listed_keys = set(l[pd.to_datetime(l.timestamp, format="%Y%m%d%H%M%S", errors="coerce") >= SHOCK].page_key)
    ok = set()
    for (u, k), g in sc.groupby(["unitid", "page_key"]):
        alive = (g.ts >= SHOCK).any() or (g.pipeline.iloc[0] == "USBACKFILL" and k in listed_keys) or (g.pipeline.iloc[0] != "USBACKFILL" and (u, g.page_type.iloc[0]) in listed)
        if (g.ts < SHOCK).any() and alive: ok.add(u)
    return ok

def build_panel(sc, uids, suffix, meta):
    pres = [f"{p}_present{suffix}" for p in PROV]
    aa = "ai_addressed_clean_strict" if "strict" in suffix else ("ai_addressed_clean" if "clean" in suffix else "ai_addressed_raw")
    nai = "n_ai_terms_clean_strict" if "strict" in suffix else ("n_ai_terms_clean" if "clean" in suffix else "n_ai_terms_raw")
    if suffix.endswith(("_w200", "_w800")):  # XN rows carry the window columns under a different name
        pass
    carry = [aa, nai, "words_clean"] + pres
    rows = []
    for uid in uids:
        series = []
        for pk, sp in sc[sc.unitid == uid].groupby("page_key"):
            sp = sp.sort_values("ts")
            asof = pd.merge_asof(pd.DataFrame({"ts": QENDS}), sp[["ts"] + carry], on="ts", direction="backward")
            asof[carry] = asof[carry].fillna(0); series.append(asof)
        agg = pd.concat(series).groupby("ts", as_index=False)[carry].max()
        agg = agg.rename(columns={aa: "ai_addressed", nai: "n_ai_terms", "words_clean": "text_len", **{f"{p}_present{suffix}": f"{p}_present" for p in PROV}})
        agg["restrictive_idx"] = agg[[f"{p}_present" for p in RESTR]].sum(axis=1); agg["procedural_idx"] = agg[[f"{p}_present" for p in PROC]].sum(axis=1)
        agg["net_restrictiveness"] = agg["restrictive_idx"] - agg["procedural_idx"]; agg["ai_governance_intensity"] = agg["restrictive_idx"] + agg["procedural_idx"]
        agg["unitid"] = uid; agg["quarter"] = agg["ts"].dt.to_period("Q").astype(str); agg["event_q"] = agg["ts"].apply(event_quarter); agg["post"] = (agg["event_q"] >= 0).astype(int)
        rows.append(agg)
    panel = pd.concat(rows, ignore_index=True).merge(meta, on="unitid", how="left").drop(columns=["ts"]).sort_values(["unitid", "event_q"])
    front = ["institution", "unitid", "state", "control", "carnegie", "quarter", "event_q", "post", "intl_share", "total_enroll"]
    return panel[front + [c for c in panel.columns if c not in front]]

def main():
    t0 = time.time()
    if not (AN / "scored_seed.csv").exists() or "--rescore" in sys.argv:
        score_seed()
    if (AN / "quarter_versions_index.csv").exists() and (not (AN / "scored_quarter_versions.csv").exists() or "--rescore" in sys.argv):
        score_quarter_versions()
    sc = assemble()
    frame = pd.concat([pd.read_csv(PIPE / "data/sample_frame.csv", dtype=str), pd.read_csv(XN / "data/sample_frame.csv", dtype=str)], ignore_index=True)
    frame["unitid"] = frame["unitid"].astype(str)
    meta = frame[["institution", "state", "control", "carnegie", "unitid", "intl_share", "total_enroll"]].drop_duplicates("unitid")
    meta.loc[meta.unitid.astype(float) < 9000000, "state"] = meta.loc[meta.unitid.astype(float) < 9000000, "state"]  # US state kept
    sysmap = sc.groupby("unitid")["system"].first().to_dict()
    same_page = page_rule(sc)  # on the recorded page types, which the coverage files use
    sc["page_type"] = [SCOR.page_type(u, k, t) for u, k, t in zip(sc.unitid, sc.page_key, sc.page_type)]
    uids = [u for u in feasibility(sc) if u not in SCOR.EXCLUDE]
    for u, why in SCOR.EXCLUDE.items(): print("left out:", u, why)
    samples = pd.DataFrame({"unitid": uids}); samples["system"] = samples.unitid.map(sysmap); samples["institution"] = samples.unitid.map(sc.groupby("unitid")["institution"].first().to_dict())
    samples["page_rule"] = samples.unitid.isin(same_page).astype(int)
    print("entry rule page by page: fails for", samples[samples.page_rule == 0][["system", "institution"]].values.tolist())
    samples.to_csv(AN / "seed_samples.csv", index=False)
    # staleness of the endpoint: the latest capture of any tracked page on or before the endpoint, from the capture
    # listings where they exist and from the retrieved versions otherwise
    lst = pd.concat([pd.read_csv(AN / f, dtype=str)[["page_key", "timestamp"]] for f in ("cdx_captures.csv", "seed_cdx_captures.csv", "screened_cdx_captures.csv") if (AN / f).exists()])
    lst["ts"] = pd.to_datetime(lst.timestamp, format="%Y%m%d%H%M%S", errors="coerce")
    tracked = sc[sc.unitid.isin(uids)][["unitid", "page_key"]].drop_duplicates()
    caps = pd.concat([sc[["unitid", "page_key", "ts"]], tracked.merge(lst[["page_key", "ts"]], on="page_key")], ignore_index=True)
    lastcap = caps[caps.ts <= QENDS[-1]].groupby("unitid").ts.max()
    st = samples.assign(last_capture=samples.unitid.map(lastcap)); st["stale_before_2025"] = (st.last_capture < "2025-01-01").astype(int)
    st.to_csv(AN / "seed_staleness.csv", index=False)
    print("latest capture before 2025:", st.groupby("system").stale_before_2025.agg(["sum", "size"]).reindex(SYSTEMS).to_dict("index"))
    pages = sc.groupby(["system", "unitid", "institution", "page_type", "page_key"]).agg(n_caps=("ts", "size"), first=("ts", "min"), last=("ts", "max"), any_ai_strict=("ai_addressed_clean_strict", "max")).reset_index()
    pages["in_sample"] = pages.unitid.isin(uids).astype(int); pages.to_csv(AN / "seed_pages.csv", index=False)
    print("=== symmetric design: sample by system ===\n", samples.groupby("system").size().reindex(SYSTEMS).to_string())
    print("pages per institution (sample):\n", pages[pages.in_sample == 1].groupby(["system", "unitid"]).size().groupby("system").agg(["mean", "max"]).reindex(SYSTEMS).to_string())
    # panels and endpoint prevalence
    results = []
    panels = {}
    for suffix, label in (("_raw", "raw"), ("_clean", "clean"), ("_clean_strict", "clean_strict"), ("_clean_strict_w200", "clean_strict_w200"), ("_clean_strict_w800", "clean_strict_w800")):
        panel = build_panel(sc, uids, suffix, meta); panels[label] = panel; panel.to_csv(AN / f"seed_panel_{label}.csv", index=False)
        last = panel.sort_values("event_q").groupby("unitid").tail(1); last["system"] = last.unitid.map(sysmap)
        out = last.groupby("system").agg(n=("unitid", "size"), ai_addressed=("ai_addressed", "mean"), **{p: (f"{p}_present", "mean") for p in PROV},
                                         restrictive_idx=("restrictive_idx", "mean"), procedural_idx=("procedural_idx", "mean")).reindex(SYSTEMS)
        out.insert(0, "rule", f"seed design, {label}"); results.append(out.reset_index())
    # with linked policy PDFs (endpoint only): institution flag = max over pages and its retrieved PDFs
    pdf_scores = AN / "policy_pdf_scores.csv"
    if pdf_scores.exists():
        ps = pd.read_csv(pdf_scores, dtype={"unitid": str})
        for suffix, label in (("_clean", "clean"), ("_clean_strict", "clean_strict")):
            last = panels[label].sort_values("event_q").groupby("unitid").tail(1).set_index("unitid")
            aa = "ai_addressed_clean_strict" if "strict" in suffix else "ai_addressed_clean"
            pmax = ps.groupby("unitid").agg(**{"ai_addressed": (aa, "max")}, **{p: (f"{p}_present{suffix}", "max") for p in PROV})
            merged = last.copy()
            for uid in merged.index:
                if uid in pmax.index:
                    merged.loc[uid, "ai_addressed"] = max(merged.loc[uid, "ai_addressed"], pmax.loc[uid, "ai_addressed"])
                    for p in PROV: merged.loc[uid, f"{p}_present"] = max(merged.loc[uid, f"{p}_present"], pmax.loc[uid, p])
            merged["restrictive_idx"] = merged[[f"{p}_present" for p in RESTR]].sum(axis=1); merged["procedural_idx"] = merged[[f"{p}_present" for p in PROC]].sum(axis=1)
            merged["system"] = [sysmap[u] for u in merged.index]
            out = merged.groupby("system").agg(n=("ai_addressed", "size"), ai_addressed=("ai_addressed", "mean"), **{p: (f"{p}_present", "mean") for p in PROV},
                                               restrictive_idx=("restrictive_idx", "mean"), procedural_idx=("procedural_idx", "mean")).reindex(SYSTEMS)
            out.insert(0, "rule", f"seed design + linked policy PDFs, {label}"); results.append(out.reset_index())
        cov = ps[ps.unitid.isin(set(uids))].groupby("system")["unitid"].nunique().reindex(SYSTEMS); print("sample institutions with >=1 retrieved policy PDF:", cov.to_dict())
    # robustness: only the institutions that meet the entry rule page by page
    last = panels["clean_strict"].sort_values("event_q").groupby("unitid").tail(1); last = last[last.unitid.isin(same_page)].copy(); last["system"] = last.unitid.map(sysmap)
    out = last.groupby("system").agg(n=("unitid", "size"), ai_addressed=("ai_addressed", "mean"), **{p: (f"{p}_present", "mean") for p in PROV},
                                     restrictive_idx=("restrictive_idx", "mean"), procedural_idx=("procedural_idx", "mean")).reindex(SYSTEMS)
    out.insert(0, "rule", "seed design, entry on one page, clean_strict"); results.append(out.reset_index())
    prev = pd.concat(results, ignore_index=True); prev.to_csv(AN / "seed_prevalence.csv", index=False)
    pd.set_option("display.width", 250); print("\n=== endpoint prevalence, symmetric design ===\n", prev.round(3).to_string(index=False))
    # US event study on the seed panels
    summary = []
    for label in ("clean", "clean_strict"):
        us = panels[label][panels[label].unitid.map(sysmap) == "US"].copy()
        us = us[us.intl_share.notna()]
        pth = AN / f"seed_panel_us_{label}.csv"; us.to_csv(pth, index=False)
        res = AN / f"results_event_study_seed_{label}.csv"
        if res.exists(): res.unlink()  # never fall back on an earlier run's results
        r = subprocess.run(["/usr/bin/python3", str(REV / "event_study_runner.py"), str(pth), str(res)], capture_output=True, text=True, cwd=str(PIPE))
        if r.returncode != 0 or not res.exists(): sys.exit(f"event study failed ({label}):\n{r.stderr.strip()[-800:]}")
        print(f"--- event study (seed, {label}): {us.unitid.nunique()} institutions\n{r.stdout.strip()[-900:]}\n{r.stderr.strip()[-300:]}")
        if res.exists():
            d = pd.read_csv(res)
            for row in d[d.kind.isin(["did_exposure_x_post", "placebo_2021Q4"])].itertuples(index=False):
                summary.append({"variant": f"seed_{label}", "n_inst": us.unitid.nunique(), "outcome": row.outcome, "kind": row.kind, "coef": round(row.coef, 3), "se": round(row.se, 3), "ci_lo": round(row.ci_lo, 3), "ci_hi": round(row.ci_hi, 3), "p": round(row.pval, 3)})
    pd.DataFrame(summary).to_csv(AN / "event_study_seed.csv", index=False)
    print(pd.DataFrame(summary)[lambda d: d.kind == "did_exposure_x_post"].to_string(index=False) if summary else "no event study rows")
    print("done", f"{time.time()-t0:.0f}s")
if __name__ == "__main__":
    main()
