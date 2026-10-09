"""Fetch the policy-relevant PDFs linked from each institution's endpoint pages (cross-national
curated pages + US curated seed pages) from the Wayback Machine, nearest capture on or before
2026-03-31, and score their text on the provision lexicon. Polite and resumable.
Outputs: policy_pdf_index.csv (one row per PDF link attempted), policy_pdfs/<unitid>/<slug>__<ts>.pdf,
policy_pdf_scores.csv (clean + strict scores per retrieved PDF)."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import csv, io, json, re, sys, time, urllib.error, urllib.parse, urllib.request, datetime as dt
from pathlib import Path
from urllib.parse import urljoin
import pandas as pd
OUTDIR = AN / "policy_pdfs"; INDEX = AN / "policy_pdf_index.csv"; SCORES = AN / "policy_pdf_scores.csv"; LOG = AN / "fetch_policy_pdfs.log"
sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B
CDX = "http://web.archive.org/web/timemap/cdx"; WB = "http://web.archive.org/web/{ts}id_/{url}"
UA = "j9-crossnational-revision (academic research)"
ENDPOINT = "20260331235959"; CDX_SLEEP, DL_SLEEP, MAX_PER_INST = 2.0, 2.5, 3
POLICY = re.compile(r"integrity|misconduct|conduct|plagiar|honest|cheat|\bai\b|artificial|generative|chatgpt|policy|policies|procedure|regulation|code|guideline|guidance|rule|statute|ordinance|handbook|assessment|discipline", re.I)
STRONG = re.compile(r"integrity|misconduct|plagiar|honest|cheat|\bai\b|artificial|generative|chatgpt|academic conduct|student conduct", re.I)
STRICT_AI = re.compile(r"artificial intelligence|generative a\.?i\.?|gen(?:erative)?\s?ai|chat\s?gpt|large language model|\bllms?\b|\bgpt\b", re.I)
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
            last = e
            if e.code in (404, 403, 410, 400):
                raise  # permanent: the archived copy does not exist
            wait = (90 if e.code in (503, 429) else backoff) * (i + 1)
            log(f"   HTTP {e.code} {url[:70]}; wait {wait}s"); time.sleep(wait)
        except (ValueError, UnicodeError):  # malformed address: permanent
            raise
        except Exception as e:
            last = e; log(f"   {type(e).__name__} {url[:70]}; wait {backoff*(i+1)}s"); time.sleep(backoff * (i + 1))
    raise last
def slug(u): return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"^https?://", "", u)).strip("_")[:80]

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


def endpoint_pages():
    """(system, unitid, institution, page_key, real_url, local_path) of the latest capture per page."""
    rows = []
    sc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
    sc = sc[sc.pipeline == "XN"]; sc["ts"] = pd.to_datetime(sc["timestamp"], format="%Y%m%d%H%M%S")
    sc["page_key"] = sc["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
    for r in sc[sc.ts <= "2026-03-31"].sort_values("ts").groupby(["unitid", "page_key"]).tail(1).itertuples(index=False):
        rows.append((r.system, r.unitid, r.institution, r.page_key, r.original_url, str(XN / r.local_path)))
    seed = AN / "seed_snapshot_index.csv"
    if seed.exists():
        si = pd.read_csv(seed, dtype={"unitid": str, "timestamp": str})
        si = si[si["bytes"].fillna(0) > 0]; si["ts"] = pd.to_datetime(si["timestamp"], format="%Y%m%d%H%M%S")
        si["page_key"] = si["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
        for r in si[si.ts <= "2026-03-31"].sort_values("ts").groupby(["unitid", "page_key"]).tail(1).itertuples(index=False):
            rows.append(("US", r.unitid, r.institution, r.page_key, r.original_url, str(AN / r.local_path)))
    return rows

def pdf_links(path, base_url):
    try: root = E._parse(E._read_bytes(Path(path)))
    except Exception: return []
    if root is None: return []
    out, seen = [], set()
    for a in root.iter("a"):
        href = a.get("href") or ""
        if not re.search(r"\.pdf(\?|#|$)", href, re.I): continue
        full = urljoin(base_url if str(base_url).startswith("http") else "https://" + str(base_url), href.strip())
        full = urllib.parse.quote(full.split("#")[0], safe=":/?&=%+~@!$,;()*'[]")
        if full in seen: continue
        seen.add(full)
        anchor = " ".join(a.text_content().split())[:200]
        if POLICY.search(anchor) or POLICY.search(href):
            out.append((full, anchor, 2 if (STRONG.search(anchor) or STRONG.search(href)) else 1))
    out.sort(key=lambda x: -x[2])
    return out

def main():
    OUTDIR.mkdir(exist_ok=True)
    cols = ["system", "unitid", "institution", "page_key", "pdf_url", "anchor", "priority", "status", "timestamp", "local_path", "bytes"]
    done = set()
    if INDEX.exists():
        done = set(zip(pd.read_csv(INDEX, dtype=str).unitid, pd.read_csv(INDEX, dtype=str).pdf_url))
    else:
        with open(INDEX, "w", newline="") as f: csv.DictWriter(f, fieldnames=cols).writeheader()
    pages = endpoint_pages()
    panel = set(pd.read_csv(PIPE / "data/panel.csv", dtype=str).unitid) | set(pd.read_csv(XN / "data/panel.csv", dtype=str).unitid)
    if (AN / "seed_samples.csv").exists():
        panel |= set(pd.read_csv(AN / "seed_samples.csv", dtype=str).unitid)
    pages = [pg for pg in pages if pg[1] in panel]
    log(f"=== fetch_policy_pdfs start: {len(pages)} endpoint pages, {len(done)} PDFs already attempted ===")
    per_inst = {}
    for system, uid, inst, pk, url, path in pages:
        for full, anchor, prio in pdf_links(path, url):
            per_inst.setdefault(uid, []).append((system, inst, pk, full, anchor, prio))
    todo = []
    for uid, lst in per_inst.items():
        seen = set(); kept = []
        for item in sorted(lst, key=lambda x: -x[5]):
            if item[3] in seen: continue
            seen.add(item[3]); kept.append(item)
            if len(kept) >= MAX_PER_INST: break
        todo += [(uid,) + k for k in kept]
    log(f"{len(todo)} PDF links across {len(per_inst)} institutions (cap {MAX_PER_INST} per institution)")
    for uid, system, inst, pk, full, anchor, prio in todo:
        if (uid, full) in done: continue
        row = {"system": system, "unitid": uid, "institution": inst, "page_key": pk, "pdf_url": full, "anchor": anchor, "priority": prio,
               "status": "", "timestamp": "", "local_path": "", "bytes": 0}
        try:
            q = {"url": full, "output": "json", "from": "20210101", "to": "20260701", "fl": "timestamp,statuscode,mimetype,digest",
                 "filter": "statuscode:200", "collapse": "digest"}
            caps = [c for c in parse_cdx_body(_get(CDX + "?" + urllib.parse.urlencode(q))) if len(c) >= 4]
        except Exception as e:
            caps = []; row["status"] = f"cdx_error:{type(e).__name__}"
        time.sleep(CDX_SLEEP)
        caps = [c for c in caps if c[0] <= ENDPOINT] or caps
        if not caps:
            row["status"] = row["status"] or "not_archived"
        else:
            ts = sorted(caps, key=lambda c: c[0])[-1][0]
            dest = OUTDIR / uid; dest.mkdir(exist_ok=True); fpath = dest / f"{slug(full)}__{ts}.pdf"
            try:
                if not fpath.exists():
                    fpath.write_bytes(_get(WB.format(ts=ts, url=full))); time.sleep(DL_SLEEP)
                row.update({"status": "ok" if fpath.read_bytes()[:5] == b"%PDF-" else "not_pdf", "timestamp": ts, "local_path": str(fpath.relative_to(AN)), "bytes": fpath.stat().st_size})
            except Exception as e:
                row["status"] = f"download_error:{type(e).__name__}"
        with open(INDEX, "a", newline="") as f: csv.DictWriter(f, fieldnames=cols).writerow(row)
        log(f"  {system} {inst[:30]:<30} {row['status']:<14} {anchor[:50]}")
    # score retrieved PDFs
    idx = pd.read_csv(INDEX, dtype=str); idx = idx[idx.status == "ok"]
    rows = []
    for r in idx.itertuples(index=False):
        text = E._text_from_string(E._pdf_text((AN / r.local_path).read_bytes()))
        sc = B.score_text(text, 400)
        B.AI_TERMS, keep = STRICT_AI, B.AI_TERMS
        try: ss = B.score_text(text, 400)
        finally: B.AI_TERMS = keep
        row = {"system": r.system, "unitid": r.unitid, "institution": r.institution, "pdf_url": r.pdf_url, "anchor": r.anchor, "timestamp": r.timestamp,
               "words": len(text.split()), "ai_addressed_clean": sc["ai_addressed"], "ai_addressed_clean_strict": ss["ai_addressed"]}
        for p in B.PROVISIONS: row[f"{p}_present_clean"] = sc[p + "_present"]; row[f"{p}_present_clean_strict"] = ss[p + "_present"]
        rows.append(row)
    pd.DataFrame(rows).to_csv(SCORES, index=False)
    log(f"=== fetch_policy_pdfs end: {len(rows)} PDFs scored ===")
if __name__ == "__main__":
    main()
