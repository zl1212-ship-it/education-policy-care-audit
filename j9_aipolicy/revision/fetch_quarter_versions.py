"""Retrieve, for every tracked page of the sample, the version in force at the end of each quarter
from 2021Q1 to 2026Q1 whenever the corpus the design reads lacks it. The original retrieval kept the
earliest capture of each distinct version of a page, at most 16 per page and evenly spaced (20 for
the five curated United States pages retrieved first, before the cap was lowered; the screened United
States pages keep the versions the parent pipeline retrieved, up to 26), and the first cross-national
batch was retrieved with a capture window that ended on 1 January 2025, so for some pages the version
in force at a quarter's end was never read. The corpus the design reads is the curated United States
pages, the cross-national pages, and the parent pipeline's captures of the screened pages
(seed_backfill_pages.csv). For each page, quarter ends are walked in order: L = the latest listed
capture on or before the quarter's end, D = the latest capture on or before it in the corpus (with
the versions already chosen for earlier quarter ends added); L is retrieved when there is no D, or
when L is later than D and its digest differs (digests from the capture listings, matched by
timestamp). A version the parent pipeline already retrieved is copied from its file instead of
downloaded again. The screened United States pages had no capture listing, so they are listed first
(the same CDX query as fetch_us_seeds.py; three pages whose address was not recorded are found by a
prefix query matched on the page key).
Outputs: output/screened_cdx_captures.csv, output/quarter_versions_index.csv and
output/quarter_versions_raw/ (raw HTML, not committed; regenerable with this script)."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
import csv, json, re, time, urllib.error, urllib.parse, urllib.request, datetime as dt
from pathlib import Path
import pandas as pd
RAW = AN / "quarter_versions_raw"; INDEX = AN / "quarter_versions_index.csv"; LISTING = AN / "screened_cdx_captures.csv"; LOG = AN / "fetch_quarter_versions.log"
CDX = "http://web.archive.org/web/timemap/cdx"; WB = "http://web.archive.org/web/{ts}id_/{url}"
FROM, TO = "20210101", "20260701"
UA = "j9-crossnational-revision (academic research)"
CAP_SLEEP, DL_SLEEP = 8.0, 2.5
QENDS = pd.period_range("2021Q1", "2026Q1", freq="Q").to_timestamp(how="end")
# screened pages whose original address was not recorded: host and path prefix to list, matched on the page key
PREFIX = {"integrity_duke_edu": "integrity.duke.edu/",
          "academicintegrity_ucsd_edu_choose_integrity_gen_ai": "academicintegrity.ucsd.edu/choose-integrity/",
          "www_stonybrook_edu_commcms_academic_integrity_generative_ai_index_php_accordion_": "www.stonybrook.edu/commcms/academic_integrity/"}


def log(m):
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {m}"; print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")


def _get(url, timeout=60, retries=6, backoff=20):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()
        except urllib.error.HTTPError as e:
            last = e; wait = (90 if e.code in (503, 429) else backoff) * (i + 1)
            log(f"   HTTP {e.code} on {url[:80]}; wait {wait}s"); time.sleep(wait)
        except Exception as e:
            last = e; log(f"   {type(e).__name__} on {url[:80]}; wait {backoff*(i+1)}s"); time.sleep(backoff * (i + 1))
    raise last


def slug(u): return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"^https?://", "", u)).strip("_")[:80]


def listing(url, prefix=False):
    q = {"url": url, "from": FROM, "to": TO, "fl": "timestamp,statuscode,digest,original", "filter": "statuscode:200", "collapse": "timestamp:8"}
    if prefix: q["matchType"] = "prefix"
    body = _get(CDX + "?" + urllib.parse.urlencode(q)).decode("utf-8", "replace").strip()
    if body.startswith("["): return [r for r in json.loads(body)[1:] if len(r) >= 4]
    return [ln.split() for ln in body.splitlines() if len(ln.split()) >= 4]


def screened_listings(pages):
    """CDX listing of each screened United States page (no listing existed for them)."""
    if LISTING.exists(): return pd.read_csv(LISTING, dtype=str)
    ui = pd.read_csv(PIPE / "data/snapshot_index.csv", dtype=str); ui["page_key"] = ui.local_path.apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
    known = {}
    for f in ("url_set.csv", "pages_per_institution.csv"):
        d = pd.read_csv(AN / f, dtype=str)
        col = "query_url" if "query_url" in d.columns else "real_url"
        for k, u in zip(d.page_key, d[col].fillna("")):
            if u.startswith("http"): known.setdefault(k, u)
    rows = []
    for r in pages.itertuples(index=False):
        if r.page_key in PREFIX:
            got = [x for x in listing(PREFIX[r.page_key], prefix=True) if slug(x[3]) == r.page_key]
        else:
            u = known.get(r.page_key) or canonical(ui[ui.page_key == r.page_key])
            got = listing(u) if u else []
        for ts, sc, dg, orig in got:
            rows.append({"system": "US", "unitid": r.unitid, "institution": r.institution, "page_type": r.page_type, "page_key": r.page_key,
                         "query_url": orig, "timestamp": ts, "statuscode": sc, "digest": dg})
        log(f"listed {r.page_key[:60]}: {len(got)} captures"); time.sleep(CAP_SLEEP)
    d = pd.DataFrame(rows, columns=["system", "unitid", "institution", "page_type", "page_key", "query_url", "timestamp", "statuscode", "digest"])
    d.to_csv(LISTING, index=False); return d


def canonical(snaps):
    """The page's own address, from the canonical link or og:url of its latest retrieved copy."""
    import lxml.html as LH
    for p in reversed(sorted(snaps.local_path)):
        try:
            t = LH.parse(str(PIPE / p)).getroot()
            c = t.xpath('//link[@rel="canonical"]/@href') or t.xpath('//meta[@property="og:url"]/@content')
            if c and str(c[0]).strip().startswith("http"): return str(c[0]).strip()
        except Exception: continue
    return ""


def main():
    pages = pd.read_csv(AN / "seed_pages.csv", dtype=str); pages = pages[pages.in_sample == "1"]
    lists = [pd.read_csv(AN / "cdx_captures.csv", dtype=str), pd.read_csv(AN / "seed_cdx_captures.csv", dtype=str)]
    have_list = set(lists[0].page_key) | set(lists[1].page_key)
    lists.append(screened_listings(pages[~pages.page_key.isin(have_list)]))
    lst = pd.concat([d[["page_key", "query_url", "timestamp", "digest"]] for d in lists], ignore_index=True).dropna(subset=["timestamp"])
    lst = lst[lst.page_key.isin(set(pages.page_key))].copy(); lst["ts"] = pd.to_datetime(lst.timestamp, format="%Y%m%d%H%M%S", errors="coerce")
    ldig = {(k, t): g for k, t, g in zip(lst.page_key, lst.timestamp, lst.digest) if isinstance(g, str) and g}
    bf = pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str); backfill = set(zip(bf.unitid, bf.page_key))
    got, parent = [], {}
    for f, base, only_backfill in ((XN / "data/snapshot_index.csv", XN, False), (AN / "seed_snapshot_index.csv", AN, False), (PIPE / "data/snapshot_index.csv", PIPE, True)):
        d = pd.read_csv(f, dtype=str); d = d[pd.to_numeric(d.bytes, errors="coerce").fillna(0) > 0]
        d["page_key"] = d.local_path.apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
        if base == PIPE:
            parent = {(k, t): base / lp for k, t, lp in zip(d.page_key, d.timestamp, d.local_path) if (base / lp).exists()}
        if only_backfill: d = d[[(u, k) in backfill for u, k in zip(d.unitid, d.page_key)]]
        d = d[[(base / lp).exists() for lp in d.local_path]]
        d["digest"] = [g if isinstance(g, str) and g else ldig.get((k, t)) for g, k, t in zip(d.digest, d.page_key, d.timestamp)]
        got.append(d[["page_key", "timestamp", "digest"]])
    got = pd.concat(got, ignore_index=True); got["ts"] = pd.to_datetime(got.timestamp, format="%Y%m%d%H%M%S", errors="coerce")
    need = {}
    for r in pages.itertuples(index=False):
        L, D = lst[lst.page_key == r.page_key].sort_values("ts"), got[got.page_key == r.page_key][["ts", "digest"]]
        for qe in QENDS:
            l, d = L[L.ts <= qe], D[D.ts <= qe].sort_values("ts")
            if l.empty: continue
            l = l.iloc[-1]
            if d.empty or (l.ts > d.iloc[-1].ts and l.digest != d.iloc[-1].digest):
                need[(r.page_key, l.timestamp)] = {"system": r.system, "unitid": r.unitid, "institution": r.institution, "page_type": r.page_type,
                                                   "page_key": r.page_key, "timestamp": l.timestamp, "digest": l.digest, "original_url": l.query_url}
                D = pd.concat([D, pd.DataFrame({"ts": [l.ts], "digest": [l.digest]})], ignore_index=True)
    log(f"versions to retrieve: {len(need)} on {len({k[0] for k in need})} pages")
    rows = []
    for (pk, ts), m in sorted(need.items()):
        rel = Path("quarter_versions_raw") / m["unitid"] / f"{pk}__{ts}.html"; dest = AN / rel; dest.parent.mkdir(parents=True, exist_ok=True)
        src = "copied from the parent retrieval" if (pk, ts) in parent else "downloaded"
        if not dest.exists() or dest.stat().st_size == 0:
            try:
                if (pk, ts) in parent: dest.write_bytes(parent[(pk, ts)].read_bytes())
                else: dest.write_bytes(_get(WB.format(ts=ts, url=m["original_url"]))); time.sleep(DL_SLEEP)
            except Exception as e:
                log(f"   failed {pk[:60]} {ts}: {type(e).__name__}")
        rows.append({**m, "source": src, "local_path": str(rel), "bytes": dest.stat().st_size if dest.exists() else 0})
    pd.DataFrame(rows).to_csv(INDEX, index=False)
    log(f"retrieved {sum(1 for x in rows if x['bytes'] > 0)} of {len(rows)}")


if __name__ == "__main__":
    main()
