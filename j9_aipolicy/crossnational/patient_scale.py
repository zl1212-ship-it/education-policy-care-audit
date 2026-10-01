"""Patient sample grower: WAIT until the Wayback IP recovers (probe a known-good URL
every 5 min, up to ~1h), then verify + download CURATED EXACT seeds at low volume
(1 capture query each, long spacing). Grows the pilot dataset in place so build_panel
picks up old+new together. Resumable. Stdlib."""
import csv, json, re, time, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
PILOT = HERE / "data"
FRAME = PILOT / "sample_frame.csv"
INDEX = PILOT / "snapshot_index.csv"
COVERAGE = PILOT / "coverage.csv"
RAW = PILOT / "snapshots_raw"
UK_SEEDS = HERE / "uk_seeds.csv"
CDX = "http://web.archive.org/cdx/search/cdx"
WB = "http://web.archive.org/web/{ts}id_/{url}"
FROM, TO, SHOCK = "20210101", "20260701", "20221130000000"
UA = "j9-crossnational-patient (academic research)"
PROBE_URL = "https://www.ox.ac.uk/students/academic/conduct"   # known richly-archived
MAX_SNAPS, CAP_SLEEP, DL_SLEEP = 16, 12.0, 4.0

# CA: construct the proven academicintegrity.<domain> subdomain seed
CA = [("McGill University", "mcgill.ca"), ("University of Alberta", "ualberta.ca"),
      ("Western University", "uwo.ca"), ("University of Calgary", "ucalgary.ca"),
      ("University of Ottawa", "uottawa.ca"), ("Dalhousie University", "dal.ca"),
      ("University of Saskatchewan", "usask.ca"), ("Simon Fraser University", "sfu.ca"),
      ("University of Victoria", "uvic.ca"), ("York University", "yorku.ca"),
      ("Concordia University", "concordia.ca"), ("Carleton University", "carleton.ca"),
      ("Memorial University of Newfoundland", "mun.ca")]


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
         "fl": "timestamp,statuscode,digest,original",
         "filter": "statuscode:200", "collapse": "timestamp:8"}
    raw = _get(CDX + "?" + urllib.parse.urlencode(q)).decode("utf-8", "replace")
    rows = json.loads(raw) if raw.strip() else []
    return rows[1:] if len(rows) > 1 else []


def wait_until_ok(max_tries=12, interval=300):
    for i in range(max_tries):
        try:
            c = caps(PROBE_URL)
            if len(c) > 5:
                print(f"IP recovered (probe={len(c)} captures) after {i} waits", flush=True)
                return True
        except Exception as e:
            print(f"  probe {i}: {type(e).__name__}", flush=True)
        print(f"  still throttled, sleeping {interval}s (try {i+1}/{max_tries})", flush=True)
        time.sleep(interval)
    return False


def distinct(caps_rows, mx):
    seen = {}
    for ts, sc, digest, original in caps_rows:
        if digest not in seen or ts < seen[digest][0]:
            seen[digest] = (ts, sc, digest, original)
    out = sorted(seen.values(), key=lambda r: r[0])
    if mx and len(out) > mx:
        idx = sorted({round(i * (len(out) - 1) / (mx - 1)) for i in range(mx)})
        out = [out[i] for i in idx]
    return out


def slug(url):
    return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"^https?://", "", url)).strip("_")[:80]


def load_seeds():
    seeds = []
    for r in csv.DictReader(open(UK_SEEDS)):
        seeds.append({"institution": r["institution"], "country": "UK", "control": "Public",
                      "carnegie": "R1", "domain": r["domain"], "integ": r["integ_url"], "ai": r.get("ai_url", "")})
    for name, dom in CA:
        seeds.append({"institution": name, "country": "CA", "control": "Public",
                      "carnegie": "R1", "domain": dom, "integ": f"https://academicintegrity.{dom}/", "ai": ""})
    return seeds


def main():
    existing = {r["institution"] for r in csv.DictReader(open(FRAME))}
    next_uid = max(int(r["unitid"]) for r in csv.DictReader(open(FRAME))) + 1
    seeds = [s for s in load_seeds() if s["institution"] not in existing]
    print(f"{len(seeds)} new exact seeds to verify (UK curated + CA constructed)", flush=True)
    if not wait_until_ok():
        print("IP still throttled after max wait; aborting (resumable, rerun later).", flush=True)
        return
    idx_rows, cov_rows, frame_rows = [], [], []
    for s in seeds:
        uid = next_uid; next_uid += 1
        added = False
        for ptype, url in [("integrity", s["integ"]), ("ai", s["ai"])]:
            if not url:
                continue
            try:
                cp = caps(url)
            except Exception:
                cp = []
            time.sleep(CAP_SLEEP)
            ts_all = sorted(c[0] for c in cp)
            n_post = sum(t >= SHOCK for t in ts_all)
            vers = distinct(cp, MAX_SNAPS)
            cov_rows.append({"institution": s["institution"], "unitid": uid, "page_type": ptype, "url": url,
                             "n_captures": len(ts_all), "n_post_captures": n_post,
                             "first_capture": ts_all[0] if ts_all else "", "last_capture": ts_all[-1] if ts_all else "",
                             "has_post": int(n_post > 0), "n_versions": len(vers)})
            if not ts_all:
                continue
            outdir = RAW / str(uid) / ptype; outdir.mkdir(parents=True, exist_ok=True)
            for ts, sc, digest, original in vers:
                dest = outdir / f"{slug(url)}__{ts}.html"
                if not (dest.exists() and dest.stat().st_size > 0):
                    try:
                        dest.write_bytes(_get(WB.format(ts=ts, url=original))); time.sleep(DL_SLEEP)
                    except Exception:
                        continue
                idx_rows.append({"institution": s["institution"], "unitid": uid, "state": s["country"],
                                 "control": s["control"], "carnegie": s["carnegie"], "page_type": ptype,
                                 "timestamp": ts, "statuscode": "200", "digest": digest, "original_url": original,
                                 "archived_url": "", "local_path": str(dest.relative_to(HERE)),
                                 "bytes": dest.stat().st_size})
                added = True
        frame_rows.append({"institution": s["institution"], "state": s["country"], "control": s["control"],
                           "carnegie": s["carnegie"], "country": s["country"], "domain": s["domain"],
                           "integrity_url": s["integ"], "guidance_url": s["ai"], "pilot": 1, "unitid": uid,
                           "exposure_year": 2022, "total_enroll": "", "nonresident_alien": "", "intl_share": ""})
        print(f"{s['country']} {s['institution'][:30]:<30} added={added}", flush=True)
    # append to pilot data files
    with open(INDEX, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=["institution","unitid","state","control","carnegie","page_type","timestamp","statuscode","digest","original_url","archived_url","local_path","bytes"]).writerows(idx_rows)
    with open(COVERAGE, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=["institution","unitid","page_type","url","n_captures","n_post_captures","first_capture","last_capture","has_post","n_versions"]).writerows(cov_rows)
    with open(FRAME, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=["institution","state","control","carnegie","country","domain","integrity_url","guidance_url","pilot","unitid","exposure_year","total_enroll","nonresident_alien","intl_share"]).writerows(frame_rows)
    print(f"\nDONE: appended {len(frame_rows)} institutions, {len(idx_rows)} snapshots", flush=True)


if __name__ == "__main__":
    main()
