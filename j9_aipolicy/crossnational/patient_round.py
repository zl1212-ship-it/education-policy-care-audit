"""Generic patient verify+download round for one curated seed file.
Usage: python3 patient_round.py <seeds.csv> <COUNTRY>
seeds.csv columns: institution,domain,integ_url,ai_url
Waits until the Wayback IP is usable, then capture-counts each exact seed (low
volume, long spacing) and downloads survivors into the pilot dataset (appends to
sample_frame.csv / snapshot_index.csv / coverage.csv). Resumable. Stdlib."""
import csv, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
PILOT = HERE / "data"
FRAME, INDEX, COVERAGE, RAW = PILOT / "sample_frame.csv", PILOT / "snapshot_index.csv", PILOT / "coverage.csv", PILOT / "snapshots_raw"
CDX = "http://web.archive.org/cdx/search/cdx"
WB = "http://web.archive.org/web/{ts}id_/{url}"
FROM, TO, SHOCK = "20210101", "20260701", "20221130000000"
UA = "j9-crossnational-patient (academic research)"
PROBE_URL = "https://www.ox.ac.uk/students/academic/conduct"
MAX_SNAPS, CAP_SLEEP, DL_SLEEP = 16, 12.0, 4.0

SEEDS_FILE, COUNTRY = Path(sys.argv[1]), sys.argv[2]


def _get(url, timeout=60, retries=3, backoff=10):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e; time.sleep(backoff * (i + 1))
    raise last


def caps(url):
    q = {"url": url, "output": "json", "from": FROM, "to": TO,
         "fl": "timestamp,statuscode,digest,original", "filter": "statuscode:200", "collapse": "timestamp:8"}
    raw = _get(CDX + "?" + urllib.parse.urlencode(q)).decode("utf-8", "replace")
    rows = json.loads(raw) if raw.strip() else []
    return rows[1:] if len(rows) > 1 else []


def wait_until_ok(max_tries=12, interval=300):
    for i in range(max_tries):
        try:
            if len(caps(PROBE_URL)) > 5:
                print(f"IP ok after {i} waits", flush=True); return True
        except Exception as e:
            print(f"  probe {i}: {type(e).__name__}", flush=True)
        print(f"  throttled, sleep {interval}s ({i+1}/{max_tries})", flush=True); time.sleep(interval)
    return False


def distinct(rows, mx):
    seen = {}
    for ts, sc, d, o in rows:
        if d not in seen or ts < seen[d][0]:
            seen[d] = (ts, sc, d, o)
    out = sorted(seen.values(), key=lambda r: r[0])
    if mx and len(out) > mx:
        idx = sorted({round(i * (len(out) - 1) / (mx - 1)) for i in range(mx)})
        out = [out[i] for i in idx]
    return out


def slug(u):
    return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"^https?://", "", u)).strip("_")[:80]


def main():
    existing = {r["institution"] for r in csv.DictReader(open(FRAME))}
    next_uid = max(int(r["unitid"]) for r in csv.DictReader(open(FRAME))) + 1
    seeds = [r for r in csv.DictReader(open(SEEDS_FILE)) if r["institution"] not in existing]
    print(f"{len(seeds)} new {COUNTRY} seeds", flush=True)
    if not seeds:
        print("nothing new", flush=True); return
    if not wait_until_ok():
        print("still throttled; abort (resumable)", flush=True); return
    idx_rows, cov_rows, frame_rows = [], [], []
    for s in seeds:
        uid = next_uid; next_uid += 1; added = False
        for ptype, url in [("integrity", s["integ_url"]), ("ai", s.get("ai_url", ""))]:
            if not url:
                continue
            try:
                cp = caps(url)
            except Exception:
                cp = []
            time.sleep(CAP_SLEEP)
            ts_all = sorted(c[0] for c in cp); n_post = sum(t >= SHOCK for t in ts_all)
            vers = distinct(cp, MAX_SNAPS)
            cov_rows.append({"institution": s["institution"], "unitid": uid, "page_type": ptype, "url": url,
                             "n_captures": len(ts_all), "n_post_captures": n_post,
                             "first_capture": ts_all[0] if ts_all else "", "last_capture": ts_all[-1] if ts_all else "",
                             "has_post": int(n_post > 0), "n_versions": len(vers)})
            if not ts_all:
                continue
            outdir = RAW / str(uid) / ptype; outdir.mkdir(parents=True, exist_ok=True)
            for ts, sc, d, o in vers:
                dest = outdir / f"{slug(url)}__{ts}.html"
                if not (dest.exists() and dest.stat().st_size > 0):
                    try:
                        dest.write_bytes(_get(WB.format(ts=ts, url=o))); time.sleep(DL_SLEEP)
                    except Exception:
                        continue
                idx_rows.append({"institution": s["institution"], "unitid": uid, "state": COUNTRY,
                                 "control": "Public", "carnegie": "R1", "page_type": ptype, "timestamp": ts,
                                 "statuscode": "200", "digest": d, "original_url": o, "archived_url": "",
                                 "local_path": str(dest.relative_to(HERE)), "bytes": dest.stat().st_size})
                added = True
        frame_rows.append({"institution": s["institution"], "state": COUNTRY, "control": "Public", "carnegie": "R1",
                           "country": COUNTRY, "domain": s["domain"], "integrity_url": s["integ_url"],
                           "guidance_url": s.get("ai_url", ""), "pilot": 1, "unitid": uid, "exposure_year": 2022,
                           "total_enroll": "", "nonresident_alien": "", "intl_share": ""})
        print(f"{COUNTRY} {s['institution'][:30]:<30} added={added}", flush=True)
    with open(INDEX, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=["institution","unitid","state","control","carnegie","page_type","timestamp","statuscode","digest","original_url","archived_url","local_path","bytes"]).writerows(idx_rows)
    with open(COVERAGE, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=["institution","unitid","page_type","url","n_captures","n_post_captures","first_capture","last_capture","has_post","n_versions"]).writerows(cov_rows)
    with open(FRAME, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=["institution","state","control","carnegie","country","domain","integrity_url","guidance_url","pilot","unitid","exposure_year","total_enroll","nonresident_alien","intl_share"]).writerows(frame_rows)
    print(f"\nDONE: +{len(frame_rows)} institutions, +{len(idx_rows)} snapshots", flush=True)


if __name__ == "__main__":
    main()
