"""Discover and download dated Wayback snapshots of each institution's integrity
and AI-guidance pages.

Why prefix discovery: the exact Wayback URL of a policy page is hard to guess
(a trailing slash or path token off and an exact-match CDX query returns nothing,
even when the page is richly archived). So for each institution this first
prefix-searches under the curated integrity and AI-guidance URLs, takes the
canonical archived page URLs the CDX server actually reports, keeps the
policy-relevant ones (academic-integrity / honor / conduct pages and AI /
ChatGPT / generative-AI pages), and then fetches each of those by exact URL.
This also auto-discovers the institution's AI-guidance subpage even when it sits
under the integrity host. build_panel.py forward-fills each page and takes the
institution-quarter max, so extra unrelated pages (which score zero) are harmless.

Snapshot HTML -> data/snapshots_raw/<unitid>/<page_type>/<ts>.html (gitignored);
provenance in data/snapshot_index.csv; per-page coverage in data/coverage.csv.

Usage:
  python3 fetch_snapshots.py                 # all institutions in the frame
  python3 fetch_snapshots.py --pilot         # only the pilot subset
  python3 fetch_snapshots.py --probe         # discovery + coverage only, no downloads
Stdlib only.
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
FRAME = HERE / "data" / "sample_frame.csv"
RAW = HERE / "data" / "snapshots_raw"
INDEX = HERE / "data" / "snapshot_index.csv"
COVERAGE = HERE / "data" / "coverage.csv"

FROM, TO = "20210101", "20250101"
SHOCK = "20221130000000"
CDX = "http://web.archive.org/cdx/search/cdx"
WB = "http://web.archive.org/web/{ts}id_/{url}"
UA = "j9-aipolicy-eventstudy (academic research; contact via repo)"

ASSET = re.compile(r"\.(png|jpe?g|css|js|pdf|gif|svg|ico|woff2?|axd|xml|json|mp4|webp|zip|docx?)(\?|$)"
                   r"|email-protect|cdn-cgi|/feed/?$|\.min\.|ScriptResource|sites/default/files", re.I)
AI_TOKENS = re.compile(r"(generative.?ai|chat.?gpt|artificial.?intelligence|gen.?ai|/ai/|ai-|-ai\b|\bai\b|gpt)", re.I)
INTEG_TOKENS = re.compile(r"(integrity|honor|conduct|misconduct|plagiar|academic-honest|honesty|honor-code)", re.I)
MAX_AI_PAGES, MAX_INTEG_PAGES = 3, 3
MAX_PAGES_PER_INST = 6

# Host stems probed under each institution's base domain so the integrity and AI
# pages can be discovered without guessing an exact URL (a curated seed URL only
# has to get the host right; a wrong path is recovered by prefix discovery).
INTEG_STEMS = ["studentconduct", "integrity", "academicintegrity", "deanofstudents",
               "catalog", "honor"]
AI_STEMS = ["teaching", "provost", "ctl"]


def candidate_prefixes(domain, integrity_url, guidance_url):
    cands = [u for u in (integrity_url, guidance_url) if u]
    if domain:
        cands += [f"https://{h}.{domain}/" for h in INTEG_STEMS + AI_STEMS]
        cands.append(f"https://www.{domain}/academic-integrity")
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _get(url, timeout=45, retries=2, backoff=2):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(backoff * (i + 1))
    raise last


def discover_pages(base):
    """Prefix-search under base; return canonical policy-relevant page URLs."""
    q = {"url": base, "matchType": "prefix", "output": "json", "from": FROM, "to": TO,
         "fl": "original", "filter": "statuscode:200", "collapse": "urlkey"}
    api = CDX + "?" + urllib.parse.urlencode(q)
    rows = json.loads(_get(api))
    urls = {r[0] for r in rows[1:]} if len(rows) > 1 else set()
    ai = sorted(u for u in urls if not ASSET.search(u) and AI_TOKENS.search(u))
    integ = sorted(u for u in urls if not ASSET.search(u) and INTEG_TOKENS.search(u))
    # prefer shorter URLs (closer to the canonical policy page)
    ai.sort(key=len)
    integ.sort(key=len)
    out = []
    for u in ai[:MAX_AI_PAGES]:
        out.append(("ai", u))
    for u in integ[:MAX_INTEG_PAGES]:
        if u not in [x for _, x in out]:
            out.append(("integrity", u))
    return out


def list_captures(url):
    q = {"url": url, "output": "json", "from": FROM, "to": TO,
         "fl": "timestamp,statuscode,digest,original",
         "filter": "statuscode:200", "collapse": "timestamp:8"}
    api = CDX + "?" + urllib.parse.urlencode(q)
    rows = json.loads(_get(api))
    return rows[1:] if rows and len(rows) > 1 else []


def distinct_versions(captures, max_snaps):
    seen = {}
    for ts, sc, digest, original in captures:
        if digest not in seen or ts < seen[digest][0]:
            seen[digest] = (ts, sc, digest, original)
    out = sorted(seen.values(), key=lambda r: r[0])
    if max_snaps and len(out) > max_snaps:
        idx = sorted({round(i * (len(out) - 1) / (max_snaps - 1)) for i in range(max_snaps)})
        out = [out[i] for i in idx]
    return out


def coverage_stats(captures):
    ts = sorted(c[0] for c in captures)
    if not ts:
        return {"n_captures": 0, "n_post_captures": 0, "first_capture": "",
                "last_capture": "", "has_post": 0}
    n_post = sum(t >= SHOCK for t in ts)
    return {"n_captures": len(ts), "n_post_captures": n_post,
            "first_capture": ts[0], "last_capture": ts[-1], "has_post": int(n_post > 0)}


def slug(url):
    s = re.sub(r"^https?://", "", url)
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:80]


def reindex_from_disk(frame_by_uid):
    """Rebuild the capture index by scanning every downloaded file, so partial or
    incremental (--only-missing) runs still yield a complete index of all data on
    disk. File path is snapshots_raw/<unitid>/<page_type>/<slug>__<ts>.html."""
    rows = []
    for f in sorted(RAW.rglob("*.html")):
        if f.stat().st_size == 0:
            continue
        uid = f.parent.parent.name
        page_type = f.parent.name
        name = f.stem  # <slug>__<ts>
        ts = name.rsplit("__", 1)[-1]
        if not (len(ts) == 14 and ts.isdigit()):
            continue
        meta = frame_by_uid.get(uid, {})
        rows.append({
            "institution": meta.get("institution", ""), "unitid": uid,
            "state": meta.get("state", ""), "control": meta.get("control", ""),
            "carnegie": meta.get("carnegie", ""), "page_type": page_type,
            "timestamp": ts, "statuscode": "200", "digest": "",
            "original_url": name.rsplit("__", 1)[0],
            "archived_url": "", "local_path": str(f.relative_to(HERE)),
            "bytes": f.stat().st_size,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--max-snaps", type=int, default=20, help="cap versions per page")
    ap.add_argument("--sleep", type=float, default=0.3, help="seconds between downloads")
    ap.add_argument("--cdx-sleep", type=float, default=1.2, help="seconds between CDX calls")
    ap.add_argument("--probe", action="store_true", help="discovery + coverage only")
    ap.add_argument("--only-missing", action="store_true",
                    help="skip institutions whose snapshots are already downloaded")
    args = ap.parse_args()

    with open(FRAME, newline="", encoding="utf-8") as f:
        frame = [r for r in csv.DictReader(f)]
    if args.pilot:
        frame = [r for r in frame if r["pilot"] == "1"]
    frame_by_uid = {str(r["unitid"]): r for r in frame}

    def already_done(uid):
        d = RAW / str(uid)
        return d.is_dir() and any(p.stat().st_size > 0 for p in d.rglob("*.html"))

    RAW.mkdir(parents=True, exist_ok=True)
    coverage_rows, processed_uids = [], set()
    for r in frame:
        inst, uid = r["institution"], r["unitid"]
        if args.only_missing and already_done(uid):
            continue
        processed_uids.add(str(uid))
        pages = []  # (page_type, url)
        for base in candidate_prefixes(r.get("domain", ""), r["integrity_url"],
                                       r.get("guidance_url", "")):
            try:
                pages += discover_pages(base)
            except Exception as e:
                print(f"  ! discover failed {inst} <{base}>: {type(e).__name__}")
            time.sleep(args.cdx_sleep)
        # dedup by url (keep first label), cap per institution (AI pages first)
        seen, ai_pages, integ_pages = set(), [], []
        for ptype, url in pages:
            if url in seen:
                continue
            seen.add(url)
            (ai_pages if ptype == "ai" else integ_pages).append((ptype, url))
        uniq = (ai_pages[:MAX_AI_PAGES] + integ_pages[:MAX_INTEG_PAGES])[:MAX_PAGES_PER_INST]
        print(f"  {inst:<44} pages={len(uniq)}")
        for ptype, url in uniq:
            try:
                captures = list_captures(url)
            except Exception as e:
                print(f"      ! captures failed [{ptype}] {url}: {type(e).__name__}")
                captures = []
            time.sleep(args.cdx_sleep)
            versions = distinct_versions(captures, args.max_snaps)
            cov = coverage_stats(captures)
            coverage_rows.append({"institution": inst, "unitid": uid, "page_type": ptype,
                                  "url": url, **cov, "n_versions": len(versions)})
            if args.probe or not versions:
                continue
            outdir = RAW / str(uid) / ptype
            outdir.mkdir(parents=True, exist_ok=True)
            for ts, sc, digest, original in versions:
                dest = outdir / f"{slug(url)}__{ts}.html"
                if dest.exists() and dest.stat().st_size > 0:
                    continue
                try:
                    html = _get(WB.format(ts=ts, url=original))
                    dest.write_bytes(html)
                    time.sleep(args.sleep)
                except Exception as e:
                    print(f"        ! snapshot {ts} failed: {type(e).__name__}")

    cov_cols = ["institution", "unitid", "page_type", "url", "n_captures",
                "n_post_captures", "first_capture", "last_capture", "has_post", "n_versions"]
    # merge: keep prior coverage for institutions not processed this run
    prior = []
    if COVERAGE.exists():
        with open(COVERAGE, newline="", encoding="utf-8") as f:
            prior = [row for row in csv.DictReader(f)
                     if str(row.get("unitid")) not in processed_uids]
    with open(COVERAGE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cov_cols)
        w.writeheader()
        w.writerows(prior + coverage_rows)
    print(f"\nWrote {COVERAGE} ({len(prior) + len(coverage_rows)} page rows; "
          f"{len(processed_uids)} institutions processed this run)")
    if args.probe:
        return 0

    cols = ["institution", "unitid", "state", "control", "carnegie", "page_type",
            "timestamp", "statuscode", "digest", "original_url", "archived_url",
            "local_path", "bytes"]
    index_rows = reindex_from_disk(frame_by_uid)
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(index_rows)
    n_inst = len({r["unitid"] for r in index_rows if r["bytes"]})
    print(f"Wrote {INDEX} ({len(index_rows)} captures, {n_inst} institutions with snapshots)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
