"""Fetch the CURATED US seed pages (integrity_url + guidance_url from PIPE/data/sample_frame.csv)
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
from the Wayback Machine, exactly as the cross-national pipeline did (patient_round.py logic):
one CDX capture listing per page (daily-collapsed, status 200), earliest capture per distinct
digest, at most 20 versions, raw id_ HTML downloaded into WS/analysis/seed_snapshots_raw/.
Polite: 12 s between CDX calls, 4 s between downloads, long backoff on errors; resumable."""
import csv, json, re, sys, time, urllib.error, urllib.parse, urllib.request, datetime as dt
from pathlib import Path
import pandas as pd
RAW = AN / "seed_snapshots_raw"; INDEX = AN / "seed_snapshot_index.csv"; COV = AN / "seed_coverage.csv"; LOG = AN / "fetch_us_seeds.log"
LISTING = AN / "seed_cdx_captures.csv"  # every status-200 capture (daily-collapsed) per seed page: the crawl-density data for the US
CDX = "http://web.archive.org/web/timemap/cdx"  # alias of the CDX server that stayed up during the 2026-10-08 outage of cdx/search/cdx
CDX_FALLBACK = "http://web.archive.org/cdx/search/cdx"; WB = "http://web.archive.org/web/{ts}id_/{url}"
FROM, TO, SHOCK = "20210101", "20260701", "20221130000000"
UA = "j9-crossnational-revision (academic research)"
MAX_SNAPS, CAP_SLEEP, DL_SLEEP = 16, 8.0, 2.5
def log(m):
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {m}"; print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")
def _get(url, timeout=60, retries=6, backoff=20):
    """Internet Archive outages return HTTP 503 'Temporarily Offline'; wait longer on those so the
    attempts are not burned while the archive is down."""
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

def parse_cdx_body(raw):
    """The cdx/search endpoint answers JSON; the timemap/cdx alias answers space-separated lines.
    Return a list of field lists either way."""
    body = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
    body = body.strip()
    if not body:
        return []
    if body.startswith("["):
        rows = json.loads(body)
        return rows[1:] if len(rows) > 1 else []
    return [line.split() for line in body.splitlines() if line.strip()]


def caps(url):
    q = {"url": url, "output": "json", "from": FROM, "to": TO, "fl": "timestamp,statuscode,digest,original", "filter": "statuscode:200", "collapse": "timestamp:8"}
    rows = parse_cdx_body(_get(CDX + "?" + urllib.parse.urlencode(q)))
    rows = [r for r in rows if len(r) >= 4]
    if not rows:
        # canary: accept an empty answer only if a known richly archived page answers normally
        # at the same moment; otherwise the endpoint is degraded, so wait and retry this page
        for attempt in range(6):
            try:
                cq = {"url": "https://provost.asu.edu/academic-integrity", "from": FROM, "to": TO, "fl": "timestamp,statuscode", "filter": "statuscode:200", "collapse": "timestamp:8"}
                canary = parse_cdx_body(_get(CDX + "?" + urllib.parse.urlencode(cq), retries=1))
            except Exception:
                canary = []
            if len(canary) >= 5:
                time.sleep(CAP_SLEEP)
                rows = [r for r in parse_cdx_body(_get(CDX + "?" + urllib.parse.urlencode(q))) if len(r) >= 4]
                if rows:
                    return rows
                return []  # confirmed empty while the archive answers normally
            log(f"   listing endpoint degraded (canary empty); wait {120 * (attempt + 1)}s"); time.sleep(120 * (attempt + 1))
        raise RuntimeError("listing endpoint degraded")
    return rows
def distinct(rows, mx):
    seen = {}
    for ts, sc, d, o in rows:
        if d not in seen or ts < seen[d][0]: seen[d] = (ts, sc, d, o)
    out = sorted(seen.values(), key=lambda r: r[0])
    if mx and len(out) > mx:
        idx = sorted({round(i * (len(out) - 1) / (mx - 1)) for i in range(mx)}); out = [out[i] for i in idx]
    return out
def slug(u): return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"^https?://", "", u)).strip("_")[:80]
def main():
    RAW.mkdir(exist_ok=True)
    frame = pd.read_csv(PIPE / "data/sample_frame.csv", dtype=str)
    ps = pd.read_csv(AN / "panel_samples.csv", dtype=str)
    panel = set(ps[(ps.in_corrected_filter == "1") & (ps.system == "US")].unitid)  # the 56 US institutions under the corrected feasibility filter
    frame["in_panel"] = frame.unitid.isin(panel).astype(int)
    frame = frame[frame.in_panel == 1].sort_values("unitid")  # 2026-10-08: panel institutions only, the archive is too slow today for all 102
    done = set()
    if COV.exists():
        cv = pd.read_csv(COV, dtype=str)
        if "n_saved" in cv.columns:
            full = cv[(cv.n_versions.astype(int) > 0) & (cv.n_saved.astype(int) >= cv.n_versions.astype(int))]
            empties = cv[cv.n_versions.astype(int) == 0].groupby(["unitid", "page_type"]).size()
            confirmed_empty = set(empties[empties >= 2].index)
            done = set(zip(full.unitid, full.page_type)) | confirmed_empty
        else:
            done = set(zip(cv.unitid, cv.page_type))
    idx_cols = ["institution", "unitid", "state", "control", "carnegie", "page_type", "timestamp", "statuscode", "digest", "original_url", "archived_url", "local_path", "bytes"]
    cov_cols = ["institution", "unitid", "page_type", "url", "n_captures", "n_post_captures", "first_capture", "last_capture", "has_post", "n_versions", "n_saved"]
    for f, cols in ((INDEX, idx_cols), (COV, cov_cols)):
        if not f.exists():
            with open(f, "w", newline="") as fh: csv.DictWriter(fh, fieldnames=cols).writeheader()
    indexed = set(pd.read_csv(INDEX, dtype=str).local_path) if INDEX.exists() else set()
    log(f"=== fetch_us_seeds start: {len(frame)} institutions, {len(done)} pages done ===")
    for r in frame.itertuples(index=False):
        for ptype, url in (("integrity", r.integrity_url), ("ai", getattr(r, "guidance_url", ""))):
            if not isinstance(url, str) or not url or (r.unitid, ptype) in done: continue
            try: cp = caps(url)
            except Exception as e: log(f"  caps failed {r.institution} {ptype}: {type(e).__name__}"); continue
            time.sleep(CAP_SLEEP)
            ts_all = sorted(c[0] for c in cp); n_post = sum(t >= SHOCK for t in ts_all); vers = distinct(cp, MAX_SNAPS)
            if cp:
                newfile = not LISTING.exists()
                with open(LISTING, "a", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=["system", "unitid", "institution", "page_type", "page_key", "query_url", "timestamp", "statuscode", "digest"])
                    if newfile: w.writeheader()
                    for ts, sc, d, o in cp:
                        w.writerow({"system": "US", "unitid": r.unitid, "institution": r.institution, "page_type": ptype, "page_key": slug(url), "query_url": url, "timestamp": ts, "statuscode": sc, "digest": d})
            outdir = RAW / str(r.unitid) / ptype; outdir.mkdir(parents=True, exist_ok=True); n_ok = 0
            for ts, sc, d, o in vers:
                dest = outdir / f"{slug(url)}__{ts}.html"
                if not (dest.exists() and dest.stat().st_size > 0):
                    try: dest.write_bytes(_get(WB.format(ts=ts, url=o))); time.sleep(DL_SLEEP)
                    except Exception as e: log(f"    snapshot {ts} failed: {type(e).__name__}"); continue
                if str(dest.relative_to(AN)) in indexed:
                    n_ok += 1; continue
                indexed.add(str(dest.relative_to(AN)))
                with open(INDEX, "a", newline="") as fh:
                    csv.DictWriter(fh, fieldnames=idx_cols).writerow({"institution": r.institution, "unitid": r.unitid, "state": r.state, "control": r.control, "carnegie": r.carnegie, "page_type": ptype, "timestamp": ts, "statuscode": "200", "digest": d, "original_url": o, "archived_url": "", "local_path": str(dest.relative_to(AN)), "bytes": dest.stat().st_size})
                n_ok += 1
            with open(COV, "a", newline="") as fh:
                csv.DictWriter(fh, fieldnames=cov_cols).writerow({"institution": r.institution, "unitid": r.unitid, "page_type": ptype, "url": url, "n_captures": len(ts_all), "n_post_captures": n_post, "first_capture": ts_all[0] if ts_all else "", "last_capture": ts_all[-1] if ts_all else "", "has_post": int(n_post > 0), "n_versions": len(vers), "n_saved": n_ok})
            log(f"  {r.institution[:40]:<40} {ptype:<9} captures={len(ts_all)} versions={len(vers)} saved={n_ok} panel={r.in_panel}")
    log("=== fetch_us_seeds end ===")
if __name__ == "__main__":
    main()
