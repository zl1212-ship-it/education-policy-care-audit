#!/usr/bin/python3
"""Wayback CDX capture lists for every tracked page (reviewer point 4, crawl density).

CDX API only (http://web.archive.org/cdx/search/cdx). Never fetches page HTML.
One request at a time, 1.5 s between requests, exponential backoff (60 s .. 15 min)
on HTTP 429/503/5xx or connection errors. Resumable: per-URL rows are appended to
analysis/cdx_captures.csv and a done-list (analysis/cdx_done.csv) lets a rerun skip
finished URLs. Writes only inside the revision workspace.

Stages
  0. url_set.csv      : one row per (system, unitid, page_type, page_key, query_url).
                        page_key = the on-disk slug used by the pipelines
                        (snapshots_raw/<unitid>/<page_type>/<slug>__<ts>.html), which is
                        also what the US snapshot_index stores in original_url.
                        US slugs are mapped back to real URLs from coverage.csv,
                        coverage_pre2026.csv, the sample frame, the canonical/og:url tag
                        inside the locally stored HTML, and finally a CDX prefix search
                        with a regex built from the slug (stage 1). XN pages are queried
                        with the curated seed URL (all original_url variants in the XN
                        index came back from that one CDX query, so they share a urlkey).
  1. url_resolution.csv: result of the CDX prefix+regex discovery for unresolved US slugs.
  2. cdx_captures.csv / cdx_done.csv : the capture lists.
"""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import csv
import datetime as dt
import gzip
import html as htmlmod
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import pandas as pd


CDX = "http://web.archive.org/web/timemap/cdx"
UA = "j9-crossnational-revision (academic research)"
FROM, TO = "20210101", "20260701"
SLEEP = 1.5
BACKOFFS = [60, 120, 240, 480, 900]
MAX_ATTEMPTS = 8

URLSET = AN / "url_set.csv"
RESOLVE = AN / "url_resolution.csv"
CAPT = AN / "cdx_captures.csv"
DONE = AN / "cdx_done.csv"
LOG = AN / "cdx_fetch.log"

CAPT_COLS = ["system", "unitid", "institution", "page_type", "page_key", "query_url",
             "timestamp", "statuscode", "digest", "mimetype", "length"]
DONE_COLS = ["system", "unitid", "page_type", "page_key", "query_url", "http_status",
             "n_rows", "fetched_at", "elapsed_s"]

CANON = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']'
    r'|<meta[^>]+property=["\']og:url["\'][^>]*content=["\']([^"\']+)["\']'
    r'|href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', re.I)


def log(msg):
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def slug(url):
    return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"^https?://", "", url)).strip("_")[:80]


# ----------------------------------------------------------------------------- network
def cdx_request(params, timeout=120):
    """Return (http_status, body). Backs off on 429/503/5xx and connection errors."""
    api = CDX + "?" + urllib.parse.urlencode(params)
    attempt = 0
    while True:
        try:
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.getcode(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) or e.code >= 500:
                if attempt >= MAX_ATTEMPTS:
                    return e.code, None
                wait = BACKOFFS[min(attempt, len(BACKOFFS) - 1)]
                attempt += 1
                log(f"  HTTP {e.code}; backoff {wait}s (attempt {attempt})")
                time.sleep(wait)
                continue
            return e.code, ""
        except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as e:
            if attempt >= MAX_ATTEMPTS:
                return -1, None
            wait = BACKOFFS[min(attempt, len(BACKOFFS) - 1)]
            attempt += 1
            log(f"  {type(e).__name__}: {str(e)[:80]}; backoff {wait}s (attempt {attempt})")
            time.sleep(wait)


def parse_json_rows(body):
    body = (body or "").strip()
    if not body:
        return []
    if body.startswith("["):
        try:
            rows = json.loads(body)
        except json.JSONDecodeError:
            return []
        return rows[1:] if isinstance(rows, list) and len(rows) > 1 else []
    return [line.split() for line in body.splitlines() if line.strip()]


# ----------------------------------------------------------------------------- stage 0
def build_url_set():
    if URLSET.exists():
        return pd.read_csv(URLSET, dtype=str)
    rows = []
    # ---------------- US (PIPE)
    P = pd.read_csv(PIPE / "data/snapshot_index.csv", dtype=str)
    P = P[P["bytes"].astype(int) > 0]
    pages = (P[["unitid", "institution", "page_type", "original_url"]]
             .drop_duplicates(["unitid", "page_type", "original_url"])
             .rename(columns={"original_url": "page_key"}))
    cands = []
    for f, src in ((PIPE / "data/coverage.csv", "coverage"),
                   (PIPE / "data/coverage_pre2026.csv", "coverage_pre2026")):
        C = pd.read_csv(f, dtype=str)
        cands.append(C[["unitid", "page_type", "url"]].assign(src=src))
    F = pd.read_csv(PIPE / "data/sample_frame.csv", dtype=str)
    fr = []
    for _, r in F.iterrows():
        for pt, col in (("integrity", "integrity_url"), ("ai", "guidance_url")):
            if isinstance(r[col], str) and r[col]:
                fr.append({"unitid": r["unitid"], "page_type": pt, "url": r[col], "src": "frame"})
    cands.append(pd.DataFrame(fr))
    C = pd.concat(cands).drop_duplicates(["unitid", "page_type", "url"])
    C["page_key"] = C["url"].map(slug)
    for _, pg in pages.iterrows():
        hits = C[(C.unitid == pg.unitid) & (C.page_type == pg.page_type) & (C.page_key == pg.page_key)]
        urls = list(dict.fromkeys(hits.url.tolist()))
        src = "|".join(sorted(set(hits.src))) if urls else ""
        if not urls:
            # canonical / og:url tags in the locally stored HTML (read-only, local files)
            files = P[(P.unitid == pg.unitid) & (P.page_type == pg.page_type)
                      & (P.original_url == pg.page_key)].local_path.tolist()
            found = set()
            for lp in files:
                raw = (PIPE / lp).read_bytes()
                if raw[:2] == b"\x1f\x8b":
                    try:
                        raw = gzip.decompress(raw)
                    except Exception:
                        pass
                txt = raw.decode("utf-8", "ignore")
                for m in CANON.finditer(txt):
                    u = htmlmod.unescape(next(x for x in m.groups() if x))
                    if slug(u) == pg.page_key:
                        found.add(u)
            urls = sorted(found, key=len)[:1]
            src = "html_canonical" if urls else ""
        if urls:
            for u in urls[:5]:
                rows.append({"system": "US", "unitid": pg.unitid, "institution": pg.institution,
                             "page_type": pg.page_type, "page_key": pg.page_key,
                             "query_url": u, "url_source": src, "n_urls_for_page": len(urls[:5])})
        else:
            rows.append({"system": "US", "unitid": pg.unitid, "institution": pg.institution,
                         "page_type": pg.page_type, "page_key": pg.page_key,
                         "query_url": "", "url_source": "unresolved", "n_urls_for_page": 0})
    # ---------------- UK / AU / CA (XN)
    X = pd.read_csv(XN / "data/snapshot_index.csv", dtype=str)
    X = X[X["bytes"].astype(int) > 0].copy()
    X["page_key"] = X.local_path.str.extract(r"/([^/]+)__\d{14}\.html$")[0]
    FX = pd.read_csv(XN / "data/sample_frame.csv", dtype=str)
    seeds = {}
    for _, r in FX.iterrows():
        for pt, col in (("integrity", "integrity_url"), ("ai", "guidance_url")):
            if isinstance(r[col], str) and r[col]:
                seeds[(r["unitid"], pt, slug(r[col]))] = r[col]
    for (uid, pt, pk), grp in X.groupby(["unitid", "page_type", "page_key"]):
        variants = Counter(grp.original_url).most_common()
        seed = seeds.get((uid, pt, pk))
        if seed:
            q, src = seed, "frame_seed"
        else:
            q, src = variants[0][0], "index_variant"
        rows.append({"system": grp.state.iloc[0], "unitid": uid, "institution": grp.institution.iloc[0],
                     "page_type": pt, "page_key": pk, "query_url": q, "url_source": src,
                     "n_urls_for_page": 1,
                     "n_index_variants": len(variants),
                     "index_variants": "|".join(v for v, _ in variants)})
    df = pd.DataFrame(rows)
    df.to_csv(URLSET, index=False)
    return df


# ----------------------------------------------------------------------------- stage 1
def regex_from_slug(pk):
    toks = pk.split("_")
    return "https?://" + "[^A-Za-z0-9]+".join(re.escape(t) for t in toks) + ".*"


def host_from_slug(pk):
    toks = pk.split("_")
    i = toks.index("edu") if "edu" in toks else 2
    host = ".".join(toks[: i + 1])
    return host[4:] if host.startswith("www.") else host


def resolve_unresolved(df):
    prior = {}
    if RESOLVE.exists():
        R = pd.read_csv(RESOLVE, dtype=str).fillna("")
        prior = {r.page_key: r for r in R.itertuples(index=False)}
    todo = df[(df.url_source == "unresolved")].drop_duplicates(["unitid", "page_type", "page_key"])
    log(f"stage 1: {len(todo)} unresolved US slugs, {len(prior)} already attempted")
    new_rows = []
    for pg in todo.itertuples(index=False):
        if pg.page_key in prior:
            continue
        host = host_from_slug(pg.page_key)
        params = {"url": host + "/", "matchType": "prefix", "output": "json", "from": FROM, "to": TO,
                  "fl": "original", "filter": ["statuscode:200", "original:" + regex_from_slug(pg.page_key)],
                  "collapse": "urlkey", "limit": "50"}
        t0 = time.time()
        api_params = urllib.parse.urlencode(params, doseq=True)
        status, body = cdx_request_raw(api_params, timeout=180)
        found = []
        if body:
            for r in parse_json_rows(body):
                u = r[0]
                if slug(u) == pg.page_key:
                    found.append(u)
        found = list(dict.fromkeys(found))[:5]
        log(f"  resolve {pg.page_key[:60]:<60} host={host} status={status} found={len(found)} "
            f"({time.time() - t0:.1f}s)")
        new_rows.append({"page_key": pg.page_key, "unitid": pg.unitid, "page_type": pg.page_type,
                         "host": host, "http_status": status, "urls": "|".join(found),
                         "resolved_at": dt.datetime.now().isoformat(timespec="seconds")})
        time.sleep(SLEEP)
    if new_rows:
        R = pd.DataFrame(new_rows)
        if RESOLVE.exists():
            R = pd.concat([pd.read_csv(RESOLVE, dtype=str).fillna(""), R])
        R.to_csv(RESOLVE, index=False)
    # fold resolutions into the url set
    if RESOLVE.exists():
        R = pd.read_csv(RESOLVE, dtype=str).fillna("")
        add = []
        for r in R.itertuples(index=False):
            urls = [u for u in r.urls.split("|") if u]
            mask = (df.page_key == r.page_key) & (df.unitid == r.unitid) & (df.page_type == r.page_type)
            if urls and mask.any():
                base = df[mask].iloc[0].to_dict()
                df = df[~mask]
                for u in urls:
                    add.append({**base, "query_url": u, "url_source": "cdx_prefix_regex",
                                "n_urls_for_page": len(urls)})
        if add:
            df = pd.concat([df, pd.DataFrame(add)], ignore_index=True)
        df.to_csv(URLSET, index=False)
    return df


def cdx_request_raw(encoded_params, timeout=120):
    api = CDX + "?" + encoded_params
    attempt = 0
    while True:
        try:
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.getcode(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) or e.code >= 500:
                if attempt >= 3:
                    return e.code, None
                wait = BACKOFFS[min(attempt, len(BACKOFFS) - 1)]
                attempt += 1
                log(f"  HTTP {e.code}; backoff {wait}s (attempt {attempt})")
                time.sleep(wait)
                continue
            return e.code, ""
        except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as e:
            if attempt >= 3:
                return -1, None
            wait = BACKOFFS[min(attempt, len(BACKOFFS) - 1)]
            attempt += 1
            log(f"  {type(e).__name__}: {str(e)[:80]}; backoff {wait}s (attempt {attempt})")
            time.sleep(wait)


# ----------------------------------------------------------------------------- stage 2
def fetch_captures(df):
    panel_uids = set(pd.read_csv(PIPE / "data/panel.csv", dtype=str).unitid) | \
        set(pd.read_csv(XN / "data/panel.csv", dtype=str).unitid)
    work = df[df.query_url.fillna("") != ""].copy()
    work["in_panel"] = work.unitid.isin(panel_uids).astype(int)
    work["sys_order"] = work.system.map({"UK": 0, "AU": 1, "CA": 2, "US": 3})
    work = work.sort_values(["sys_order", "in_panel", "unitid", "page_type", "page_key", "query_url"],
                            ascending=[True, False, True, True, True, True])
    done = set()
    if DONE.exists():
        D = pd.read_csv(DONE, dtype=str)
        done = set(zip(D.page_key, D.query_url))
    if not CAPT.exists():
        with open(CAPT, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CAPT_COLS).writeheader()
    if not DONE.exists():
        with open(DONE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=DONE_COLS).writeheader()
    todo = [r for r in work.itertuples(index=False) if (r.page_key, r.query_url) not in done]
    log(f"stage 2: {len(work)} query URLs, {len(done)} done, {len(todo)} to fetch")
    t_start = time.time()
    for i, r in enumerate(todo, 1):
        params = {"url": r.query_url, "output": "json", "from": FROM, "to": TO,
                  "fl": "timestamp,statuscode,digest,mimetype,length", "filter": "statuscode:200"}
        t0 = time.time()
        status, body = cdx_request(params)
        if body is None:
            log(f"  GIVING UP (not marked done) {r.system} {r.unitid} {r.page_key[:50]} status={status}")
            time.sleep(SLEEP)
            continue
        rows = parse_json_rows(body)
        with open(CAPT, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAPT_COLS)
            for row in rows:
                ts, sc, dg, mt, ln = (list(row) + [""] * 5)[:5]
                w.writerow({"system": r.system, "unitid": r.unitid, "institution": r.institution,
                            "page_type": r.page_type, "page_key": r.page_key, "query_url": r.query_url,
                            "timestamp": ts, "statuscode": sc, "digest": dg, "mimetype": mt, "length": ln})
        with open(DONE, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=DONE_COLS).writerow(
                {"system": r.system, "unitid": r.unitid, "page_type": r.page_type, "page_key": r.page_key,
                 "query_url": r.query_url, "http_status": status, "n_rows": len(rows),
                 "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
                 "elapsed_s": round(time.time() - t0, 2)})
        el = time.time() - t_start
        log(f"  [{i}/{len(todo)}] {r.system} {r.unitid} {r.page_type} {r.page_key[:45]:<45} "
            f"status={status} rows={len(rows)} ({time.time() - t0:.1f}s; total {el / 60:.1f} min)")
        time.sleep(SLEEP)
    log("stage 2 finished")


def main():
    AN.mkdir(parents=True, exist_ok=True)
    log("=== fetch_cdx.py start ===")
    df = build_url_set()
    log(f"stage 0: url_set has {len(df)} rows; "
        f"{df.groupby('system').page_key.nunique().to_dict()} distinct page keys per system; "
        f"unresolved={int((df.url_source == 'unresolved').sum())}")
    # stage 1 (resolving 20 junk US slugs) skipped on 2026-10-08: Wayback CDX returned 502/504 and those pages are junk
    log(f"after stage 1: unresolved={int((df.url_source == 'unresolved').sum())}, "
        f"query URLs={int((df.query_url.fillna('') != '').sum())}")
    fetch_captures(df)
    log("=== fetch_cdx.py end ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
