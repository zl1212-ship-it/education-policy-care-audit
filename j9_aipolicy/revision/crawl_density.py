"""Wayback crawl density and interval-censored adoption (reviewer point 4), from cdx_captures.csv.
Writes captures_per_page_quarter.csv, density_summary.csv, density_vs_exposure.csv,
adoption_intervals.csv, adoption_summary.csv, adoption_turnbull.csv, cdx_completeness.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats as st

SHOCK = pd.Timestamp("2022-11-30")
SYSTEMS = ["US", "UK", "AU", "CA"]
CAP = {"US": 16, "UK": 16, "AU": 16, "CA": 16}

cdx = pd.read_csv(AN / "cdx_captures.csv", dtype=str)
done = pd.read_csv(AN / "cdx_done.csv", dtype=str)
urlset = pd.read_csv(AN / "url_set.csv", dtype=str)
cdx = cdx[cdx.system != "US"]; done = done[done.system != "US"]; urlset = urlset[urlset.system != "US"]
# US pages: the curated seed pages, listed by fetch_us_seeds.py (daily-collapsed); re-list any complete page without rows
seed_list = pd.read_csv(AN / "seed_cdx_captures.csv", dtype=str) if (AN / "seed_cdx_captures.csv").exists() else pd.DataFrame(columns=cdx.columns)
seed_cov = pd.read_csv(AN / "seed_coverage.csv", dtype=str)
seed_cov["page_key"] = seed_cov["url"].apply(lambda u: __import__("re").sub(r"[^A-Za-z0-9]+", "_", __import__("re").sub(r"^https?://", "", u)).strip("_")[:80])
missing = seed_cov[(seed_cov.n_captures.astype(int) > 0) & (~seed_cov.page_key.isin(set(seed_list.page_key)))]
if len(missing):
    import json, time, urllib.parse, urllib.request
    rows = []
    for r in missing.itertuples(index=False):
        q = {"url": r.url, "output": "json", "from": "20210101", "to": "20260701", "fl": "timestamp,statuscode,digest", "filter": "statuscode:200", "collapse": "timestamp:8"}
        for attempt in range(5):
            try:
                req = urllib.request.Request("http://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(q), headers={"User-Agent": "j9-crossnational-revision (academic research)"})
                with urllib.request.urlopen(req, timeout=60) as resp: body = resp.read().decode("utf-8", "replace")
                caps = json.loads(body)[1:] if body.strip() else []
                for ts, sc, d in caps:
                    rows.append({"system": "US", "unitid": r.unitid, "institution": r.institution, "page_type": r.page_type, "page_key": r.page_key, "query_url": r.url, "timestamp": ts, "statuscode": sc, "digest": d})
                break
            except Exception:
                time.sleep(20 * (attempt + 1))
        time.sleep(3)
    if rows:
        seed_list = pd.concat([seed_list, pd.DataFrame(rows)], ignore_index=True); seed_list.to_csv(AN / "seed_cdx_captures.csv", index=False)
cdx = pd.concat([cdx, seed_list[cdx.columns.intersection(seed_list.columns)]], ignore_index=True)
# daily collapse for every system (the seed listings are already daily-collapsed)
cdx["day"] = cdx["timestamp"].str[:8]; cdx = cdx.drop_duplicates(["page_key", "day"])
done = pd.concat([done, seed_cov.rename(columns={"url": "query_url"}).assign(system="US")[["system", "unitid", "page_type", "page_key", "query_url"]]], ignore_index=True)
urlset = pd.concat([urlset, seed_cov.rename(columns={"url": "query_url"}).assign(system="US")[["system", "unitid", "page_type", "page_key", "query_url"]]], ignore_index=True)
cdx["ts"] = pd.to_datetime(cdx["timestamp"], format="%Y%m%d%H%M%S", errors="coerce")
cdx = cdx.dropna(subset=["ts"])
cdx = cdx[(cdx.ts >= "2021-01-01") & (cdx.ts < "2026-07-01")]
cdx["quarter"] = cdx["ts"].dt.to_period("Q")
# completeness
tot = urlset.groupby("system")["page_key"].nunique()
fin = done.groupby("system")["page_key"].nunique()
comp = pd.DataFrame({"pages_in_url_set": tot, "pages_fetched": fin}).reindex(SYSTEMS)
comp["share"] = (comp.pages_fetched / comp.pages_in_url_set).round(3)
comp.to_csv(AN / "cdx_completeness.csv"); print("=== CDX completeness ===\n", comp)

# (a) captures per page per quarter
pages = done[["system", "unitid", "page_type", "page_key"]].drop_duplicates()
quarters = pd.period_range("2021Q1", "2026Q2", freq="Q")
grid = pages.merge(pd.DataFrame({"quarter": quarters}), how="cross")
cnt = cdx.groupby(["page_key", "quarter"]).agg(n_captures=("timestamp", "size"), n_digests=("digest", "nunique")).reset_index()
pq = grid.merge(cnt, on=["page_key", "quarter"], how="left").fillna({"n_captures": 0, "n_digests": 0})
def period(q):
    if q <= pd.Period("2022Q3", freq="Q"): return "pre-shock 2021Q1-2022Q3"
    if q <= pd.Period("2024Q4", freq="Q"): return "shock-to-plateau 2022Q4-2024Q4"
    return "late 2025Q1-2026Q2"
pq["period"] = pq["quarter"].apply(period)
pq.to_csv(AN / "captures_per_page_quarter.csv", index=False)
# gaps between successive captures per page
cdx_s = cdx.sort_values(["page_key", "ts"])
cdx_s["gap_days"] = cdx_s.groupby("page_key")["ts"].diff().dt.days
cdx_s["period"] = cdx_s["quarter"].apply(period)
gap = cdx_s.groupby(["system", "period"])["gap_days"].median().rename("median_gap_days")
summ = pq.groupby(["system", "period"]).agg(page_quarters=("n_captures", "size"), mean_captures=("n_captures", "mean"),
                                           median_captures=("n_captures", "median"), share_zero=("n_captures", lambda s: (s == 0).mean()),
                                           mean_digests=("n_digests", "mean")).join(gap)
summ_pt = pq.groupby(["system", "page_type"]).agg(mean_captures=("n_captures", "mean"), median_captures=("n_captures", "median"),
                                                   share_zero=("n_captures", lambda s: (s == 0).mean()))
summ.round(3).to_csv(AN / "density_summary.csv"); summ_pt.round(3).to_csv(AN / "density_summary_by_pagetype.csv")
print("\n=== captures per page-quarter by system and period ===\n", summ.round(2).to_string())
print("\n=== by page type ===\n", summ_pt.round(2).to_string())

# (b) density vs exposure
inst = pq.groupby(["system", "unitid"]).agg(density_all=("n_captures", "mean")).reset_index()
mid = pq[pq.period.str.startswith("shock")].groupby(["system", "unitid"]).agg(density_mid=("n_captures", "mean")).reset_index()
inst = inst.merge(mid, on=["system", "unitid"], how="left")
fr = pd.concat([pd.read_csv(PIPE / "data/sample_frame.csv", dtype=str), pd.read_csv(XN / "data/sample_frame.csv", dtype=str)])
fr = fr[["unitid", "intl_share", "total_enroll"]].drop_duplicates("unitid")
inst = inst.merge(fr, on="unitid", how="left")
inst["intl_share"] = pd.to_numeric(inst["intl_share"], errors="coerce"); inst["total_enroll"] = pd.to_numeric(inst["total_enroll"], errors="coerce")
inst.to_csv(AN / "density_vs_exposure.csv", index=False)
sample_uids = set(pd.read_csv(AN / "seed_samples.csv", dtype=str).unitid) if (AN / "seed_samples.csv").exists() else set(inst.unitid)
inst = inst[inst.unitid.isin(sample_uids)]
rows = []
for s in SYSTEMS:
    d = inst[(inst.system == s)].dropna(subset=["intl_share"])
    for col in ("density_all", "density_mid"):
        dd = d.dropna(subset=[col])
        if len(dd) >= 5:
            pr = st.pearsonr(dd.intl_share, dd[col]); sp = st.spearmanr(dd.intl_share, dd[col])
            slope = np.polyfit(dd.intl_share, np.log1p(dd[col]), 1)[0]
            rows.append({"system": s, "density": col, "n": len(dd), "pearson_r": round(pr[0], 3), "pearson_p": round(pr[1], 3),
                         "spearman_rho": round(sp[0], 3), "spearman_p": round(sp[1], 3), "ols_slope_log1p_density_on_share": round(slope, 3)})
    d2 = inst[(inst.system == s)].dropna(subset=["total_enroll", "density_all"])
    if len(d2) >= 5:
        sp = st.spearmanr(d2.total_enroll, d2.density_all)
        rows.append({"system": s, "density": "density_all vs total_enroll", "n": len(d2), "pearson_r": np.nan, "pearson_p": np.nan,
                     "spearman_rho": round(sp[0], 3), "spearman_p": round(sp[1], 3), "ols_slope_log1p_density_on_share": np.nan})
corr = pd.DataFrame(rows); corr.to_csv(AN / "density_exposure_correlation.csv", index=False)
print("\n=== crawl density vs exposure ===\n", corr.to_string(index=False))

# (c) interval-censored adoption
allsc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
allsc["page_key"] = allsc["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
sc = allsc[allsc.pipeline == "XN"]
if (AN / "scored_seed.csv").exists():
    seed = pd.read_csv(AN / "scored_seed.csv", dtype={"unitid": str, "timestamp": str}); seed["page_key"] = seed["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
    sc = pd.concat([sc, seed], ignore_index=True)
if (AN / "seed_backfill_pages.csv").exists():  # US institutions observed on a screened discovered page
    keep = set(map(tuple, pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str).values))
    back = allsc[(allsc.pipeline == "US") & [(u, k) in keep for u, k in zip(allsc.unitid, allsc.page_key)]]
    sc = pd.concat([sc, back], ignore_index=True)
sc["ts"] = pd.to_datetime(sc["timestamp"], format="%Y%m%d%H%M%S")
panel_uids = sorted(set(pd.read_csv(AN / "seed_samples.csv", dtype=str).unitid)) if (AN / "seed_samples.csv").exists() else sorted(set(sc.unitid))
def eq(ts):
    return (ts.year - 2022) * 4 + (ts.quarter - 4)
rows = []
for flagcol, lab in (("ai_addressed_raw", "raw"), ("ai_addressed_clean", "clean"), ("ai_addressed_clean_strict", "clean_strict")):
    for uid in panel_uids:
        s = sc[sc.unitid == uid]
        if len(s) == 0:
            continue
        sysname = s["system"].iloc[0]
        pre_pos = int((s[(s[flagcol] == 1) & (s.ts < SHOCK)]).shape[0] > 0)
        post = s[(s[flagcol] == 1) & (s.ts >= SHOCK)].sort_values("ts")
        if len(post) == 0:
            rows.append({"flag": lab, "unitid": uid, "system": sysname, "adopted": 0, "pre_shock_positive": pre_pos})
            continue
        first = post.iloc[0]
        R = first["ts"]; pk = first["page_key"]
        c = cdx[(cdx.page_key == pk) & (cdx.ts < R)]
        L = c["ts"].max() if len(c) else pd.NaT
        ndig = cdx[cdx.page_key == pk]["digest"].nunique()
        mid = L + (R - L) / 2 if pd.notna(L) else pd.NaT
        rows.append({"flag": lab, "unitid": uid, "system": sysname, "adopted": 1, "pre_shock_positive": pre_pos, "page_key": pk,
                     "R": R, "L": L, "width_days": (R - L).days if pd.notna(L) else np.nan,
                     "q_R": eq(R), "q_mid": eq(mid) if pd.notna(mid) else np.nan, "q_L": eq(L) if pd.notna(L) else np.nan,
                     "cdx_distinct_digests": ndig, "exceeds_download_cap": int(ndig > CAP[sysname]),
                     "L_left_censored": int(pd.isna(L))})
ad = pd.DataFrame(rows); ad.to_csv(AN / "adoption_intervals.csv", index=False)
summ_rows = []
for lab in ("raw", "clean", "clean_strict"):
    a = ad[(ad.flag == lab) & (ad.adopted == 1)].copy()
    for s in SYSTEMS + ["ALL"]:
        d = a if s == "ALL" else a[a.system == s]
        if len(d) == 0:
            continue
        r = {"flag": lab, "system": s, "n_adopters": len(d), "n_pre_shock_positive": int(d.pre_shock_positive.sum()),
             "width_days_median": d.width_days.median(), "width_days_q25": d.width_days.quantile(.25), "width_days_q75": d.width_days.quantile(.75),
             "left_censored": int(d.L_left_censored.sum()), "exceeds_cap": int(d.exceeds_download_cap.sum())}
        for conv in ("q_R", "q_mid", "q_L"):
            q = d[conv].dropna().clip(lower=0)
            r[f"lag_mean_{conv}"] = round(q.mean(), 2); r[f"lag_median_{conv}"] = q.median(); r[f"share_within2q_{conv}"] = round((q <= 2).mean(), 2)
        r["n_quarter_changes_mid_vs_R"] = int((d.q_mid.notna() & (d.q_mid != d.q_R)).sum())
        summ_rows.append(r)
asum = pd.DataFrame(summ_rows); asum.to_csv(AN / "adoption_summary.csv", index=False)
print("\n=== adoption timing under R (forward-fill), midpoint, L ===\n", asum.to_string(index=False))

# (d) Turnbull-style EM on quarter bins for the clean-strict adopters (intervals (q_L, q_R], clipped at 0);
# left-censored adopters (page created after the shock, no earlier capture) get the interval [0, q_R]
tb_rows = []
for subset in ("all", "not_left_censored"):
    a = ad[(ad.flag == "clean_strict") & (ad.adopted == 1)].copy()
    if subset == "not_left_censored": a = a[a.L_left_censored == 0]
    a["lo"] = a["q_L"].fillna(-8).clip(lower=-1).astype(int) + 1
    a["hi"] = a["q_R"].astype(int); a.loc[a.lo > a.hi, "lo"] = a.hi
    if len(a) < 5: continue
    bins = list(range(int(a.lo.min()), int(a.hi.max()) + 1)); pm = np.ones(len(bins)) / len(bins)
    for _ in range(500):
        num = np.zeros(len(bins))
        for lo, hi in zip(a.lo, a.hi):
            m = np.array([(lo <= b <= hi) for b in bins], float); w = pm * m
            if w.sum() > 0: num += w / w.sum()
        pm = num / num.sum()
    ff = a["hi"].value_counts(normalize=True).reindex(bins).fillna(0).values
    for b_, tm, tc, fm, fc in zip(bins, pm, np.cumsum(pm), ff, np.cumsum(ff)):
        tb_rows.append({"subset": subset, "n_adopters": len(a), "event_q": b_, "turnbull_mass": round(tm, 4), "turnbull_cdf": round(tc, 4), "forward_fill_mass": round(fm, 4), "forward_fill_cdf": round(fc, 4)})
tb = pd.DataFrame(tb_rows); tb.to_csv(AN / "adoption_turnbull.csv", index=False)
print("\n=== adoption-time distribution: Turnbull vs forward-fill (clean-strict adopters) ===\n", tb[tb.event_q <= 6].to_string(index=False))
print("done")
