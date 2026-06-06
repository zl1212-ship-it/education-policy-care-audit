"""
J4 semi-automated adoption-date collector (human-in-the-loop).

Pipeline:
  1. scan  — given seed source URLs (regents minutes, state procurement, .edu/press),
             fetch each (HTML or PDF), find ed-tech vendor mentions near 4-digit years,
             and APPEND machine-proposed rows to data/candidates_review.csv.
  2. (human) open candidates_review.csv, confirm the real adoption year + source,
             set verified=yes, fix the year. THIS STEP IS MANDATORY.
  3. promote — move verified=yes rows into data/adoption_panel.csv, resolving each
             institution's real IPEDS unitid via the Urban Institute Education Data API.

The scanner writes only to the review queue; rows enter adoption_panel.csv via the
promote step, after a human confirms the year against the cited source.

Usage:
  python collect_regents.py scan      # reads data/sources_seed.csv -> candidates_review.csv
  python collect_regents.py promote   # verified candidates -> adoption_panel.csv
"""
import csv, io, os, re, sys, time, json, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SEED = os.path.join(DATA, "sources_seed.csv")          # institution,url[,fips]
CANDIDATES = os.path.join(DATA, "candidates_review.csv")
PANEL = os.path.join(DATA, "adoption_panel.csv")

# vendor -> regex of platform name variants
VENDORS = {
    "EAB": r"\b(EAB|Education Advisory Board|Navigate\s?360|Navigate|Student Success Collaborative|SSC Campus)\b",
    "Civitas": r"\bCivitas( Learning)?\b|\bInspire\b",
    "Starfish": r"\bStarfish\b",
    "Hobsons": r"\bHobsons\b|\bStarfish Retention\b",
}
YEAR = re.compile(r"\b(20[0-2]\d)\b")
PANEL_COLS = ["unitid", "institution", "state", "control", "vendor", "platform",
              "adoption_year", "date_precision", "source_type", "source_url",
              "source_quote", "verified_by", "verified_date", "notes"]
CAND_COLS = ["institution", "vendor", "candidate_year", "source_url", "snippet",
             "verified", "confirmed_year", "notes"]


def fetch_text(url):
    """Return plain text of an HTML or PDF page (best effort)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ctype = r.headers.get("Content-Type", "").lower()
        raw = r.read()
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:
            return f"[[PDF parse failed: {e}]]"
    html = raw.decode("utf-8", "ignore")
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", html)


def scan_url(institution, url):
    """Yield candidate dicts: every vendor mention with the nearest years + snippet."""
    try:
        text = fetch_text(url)
    except Exception as e:
        print(f"  ! fetch failed {url}: {e}")
        return
    text = re.sub(r"\s+", " ", text)
    for vendor, pat in VENDORS.items():
        for m in re.finditer(pat, text, flags=re.I):
            lo, hi = max(0, m.start() - 250), min(len(text), m.end() + 250)
            window = text[lo:hi]
            years = sorted(set(YEAR.findall(window)))
            if not years:
                continue
            yield {
                "institution": institution,
                "vendor": vendor,
                "candidate_year": "|".join(years),   # human picks the right one
                "source_url": url,
                "snippet": window.strip()[:300],
                "verified": "", "confirmed_year": "", "notes": "",
            }


def cmd_scan():
    if not os.path.exists(SEED):
        sys.exit(f"missing {SEED} (columns: institution,url[,fips])")
    rows = []
    with open(SEED) as f:
        for s in csv.DictReader(f):
            if not s.get("url"):
                continue
            print(f"scan {s['institution']}: {s['url']}")
            rows += list(scan_url(s["institution"], s["url"]))
            time.sleep(0.5)
    # dedupe against existing review file
    seen = set()
    if os.path.exists(CANDIDATES):
        with open(CANDIDATES) as f:
            for r in csv.DictReader(f):
                seen.add((r["institution"], r["vendor"], r["source_url"]))
    new = [r for r in rows if (r["institution"], r["vendor"], r["source_url"]) not in seen]
    write_header = not os.path.exists(CANDIDATES)
    with open(CANDIDATES, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAND_COLS)
        if write_header:
            w.writeheader()
        w.writerows(new)
    print(f"\n+{len(new)} candidates -> {CANDIDATES}. "
          f"Now verify each (set verified=yes, confirmed_year) before promote.")


def resolve_unitid(name, fips=None):
    """Map an institution name to its real IPEDS unitid via the Urban API."""
    base = "https://educationdata.urban.org/api/v1/college-university/ipeds/directory/2021/"
    url = base + (f"?fips={fips}" if fips else "")
    best = None
    while url:
        with urllib.request.urlopen(url, timeout=90) as r:
            d = json.load(r)
        for x in d["results"]:
            if name.lower() == (x["inst_name"] or "").lower():
                return x["unitid"], x.get("state_abbr"), x.get("inst_control")
            if name.lower() in (x["inst_name"] or "").lower() and best is None:
                best = (x["unitid"], x.get("state_abbr"), x.get("inst_control"))
        url = d.get("next") if not best else None
    return best if best else (None, None, None)


def cmd_promote():
    if not os.path.exists(CANDIDATES):
        sys.exit("no candidates_review.csv yet")
    with open(CANDIDATES) as f:
        cands = [r for r in csv.DictReader(f) if r.get("verified", "").lower() == "yes"]
    if not cands:
        sys.exit("no rows marked verified=yes")
    existing = set()
    if os.path.exists(PANEL):
        with open(PANEL) as f:
            for r in csv.DictReader(f):
                existing.add((r["institution"], r["vendor"]))
    out = []
    for c in cands:
        if (c["institution"], c["vendor"]) in existing:
            continue
        uid, st, ctrl = resolve_unitid(c["institution"])
        out.append({
            "unitid": uid, "institution": c["institution"], "state": st,
            "control": ctrl, "vendor": c["vendor"], "platform": "",
            "adoption_year": c.get("confirmed_year") or c.get("candidate_year"),
            "date_precision": "year", "source_type": "", "source_url": c["source_url"],
            "source_quote": c.get("snippet", ""), "verified_by": "manual",
            "verified_date": time.strftime("%Y-%m-%d"), "notes": c.get("notes", ""),
        })
    write_header = not os.path.exists(PANEL)
    with open(PANEL, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PANEL_COLS)
        if write_header:
            w.writeheader()
        w.writerows(out)
    print(f"+{len(out)} verified rows -> {PANEL}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    {"scan": cmd_scan, "promote": cmd_promote}.get(cmd, cmd_scan)()
