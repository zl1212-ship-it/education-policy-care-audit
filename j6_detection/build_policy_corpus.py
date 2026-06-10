"""Fetch public university integrity/AI policy texts into J6's governance corpus.

Reproducibility contract
------------------------
This script does NOT code policies. It fetches the raw policy text from the real,
public URLs listed in data/policy_registry.csv, stores each verbatim with its
provenance, and emits data/policy_corpus.csv with the provenance columns filled
and the four codebook columns BLANK. Coding is content analysis done against the
stored text per CODEBOOK_policy.md; every code must cite a passage in the stored
file. Nothing here invents a code or a number.

Registry (input, curated by hand from real institution pages):
    data/policy_registry.csv  with columns: institution,state,control,policy_type,url[,secondary_url]

Outputs:
    data/policy_raw/<slug>.txt   verbatim fetched text (gitignored; re-fetchable)
    data/policy_corpus.csv       provenance + blank code columns, ready to code

Stdlib only. Re-run is idempotent; pins nothing remote except the registry URLs,
so record access_date and sha256 for every row.
"""
import csv
import hashlib
import re
import sys
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).parent
REGISTRY = HERE / "data" / "policy_registry.csv"
RAW_DIR = HERE / "data" / "policy_raw"
OUT = HERE / "data" / "policy_corpus.csv"

CODE_COLUMNS = ["detector_admissibility", "burden_of_proof", "appeal_pathway", "l2_protection"]
SUPPORT_COLUMNS = ["support_passage", "coder", "notes"]
PROV_COLUMNS = ["institution", "state", "control", "policy_type", "url", "secondary_url",
                "access_date", "http_status", "sha256", "n_chars"]


class _TextExtractor(HTMLParser):
    """Strip tags, drop script/style, collapse whitespace."""

    def __init__(self):
        super().__init__()
        self._skip = 0
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self._buf.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", "\n".join(self._buf))).strip()


def _slug(institution: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", institution.lower()).strip("-")


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "j6-policy-fetch (academic audit)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        status = r.status
    body = raw.decode("utf-8", errors="replace")
    if "<html" in body[:2000].lower() or "<body" in body.lower():
        p = _TextExtractor()
        p.feed(body)
        text = p.text()
    else:  # plain text / already-extracted
        text = body
    return status, text


def main() -> int:
    if not REGISTRY.exists():
        print(f"Missing {REGISTRY}. Add real institution policy URLs first "
              f"(columns: institution,state,control,policy_type,url[,secondary_url]).",
              file=sys.stderr)
        return 1
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with open(REGISTRY, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("institution")]
    if not rows:
        print(f"{REGISTRY} has no institutions yet.", file=sys.stderr)
        return 1

    today = date.today().isoformat()
    out_rows = []
    ok = 0
    for r in rows:
        inst, url = r["institution"], r["url"].strip()
        slug = _slug(inst)
        if not url:  # institution in the frame but URL not sourced yet
            out_rows.append({
                "institution": inst, "state": r.get("state", ""), "control": r.get("control", ""),
                "policy_type": r.get("policy_type", ""), "url": "", "secondary_url": "",
                "access_date": today, "http_status": "PENDING", "sha256": "", "n_chars": 0,
                **{c: "" for c in CODE_COLUMNS}, **{c: "" for c in SUPPORT_COLUMNS},
            })
            print(f"  [PENDING] {inst}: no URL in registry yet")
            continue
        sec = r.get("secondary_url", "").strip()
        try:
            status, text = fetch(url)
            parts = [f"### PRIMARY {url}\n{text}"]
            if sec:  # conduct/appeal process page, for burden_of_proof + appeal_pathway
                try:
                    s2, t2 = fetch(sec)
                    parts.append(f"\n\n### SECONDARY {sec}\n{t2}")
                    status = f"{status}+{s2}"
                except Exception as e2:
                    parts.append(f"\n\n### SECONDARY {sec}\nFETCH-FAILED: {e2}")
                    status = f"{status}+ERR"
            combined = "\n".join(parts)
            (RAW_DIR / f"{slug}.txt").write_text(combined, encoding="utf-8")
            sha = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
            n = len(combined)
            ok += 1
            print(f"  [{status}] {inst}: {n} chars -> {slug}.txt")
        except Exception as e:
            status, sha, n = f"ERR:{type(e).__name__}", "", 0
            print(f"  [FAIL] {inst}: {e}", file=sys.stderr)
        out_rows.append({
            "institution": inst, "state": r.get("state", ""), "control": r.get("control", ""),
            "policy_type": r.get("policy_type", ""), "url": url,
            "secondary_url": r.get("secondary_url", ""), "access_date": today,
            "http_status": status, "sha256": sha, "n_chars": n,
            **{c: "" for c in CODE_COLUMNS}, **{c: "" for c in SUPPORT_COLUMNS},
        })

    # Preserve existing codes if policy_corpus.csv already coded: merge by institution.
    existing = {}
    if OUT.exists():
        with open(OUT, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing[row["institution"]] = row
    for row in out_rows:
        prior = existing.get(row["institution"])
        if prior:
            for c in CODE_COLUMNS + SUPPORT_COLUMNS:
                if prior.get(c):
                    row[c] = prior[c]

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PROV_COLUMNS + CODE_COLUMNS + SUPPORT_COLUMNS)
        w.writeheader()
        w.writerows(out_rows)

    print(f"\nFetched {ok}/{len(rows)} policies -> {OUT}")
    print(f"Now code the blank columns per CODEBOOK_policy.md, then run analyze_policy.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
