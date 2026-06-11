"""Fetch and archive the vendor documentation behind J7's consequence mapping.

Reads data/vendor_registry.csv (curated vendor-authored public pages: how face
detection / identity verification outcomes become flags, alerts, or gates), fetches
each page, and archives extracted text under data/vendor_raw/<slug>.txt with a
provenance header (URL, access timestamp, HTTP status, sha256 of the raw HTML).
Live pages change; the stored text at the access date is the evidence of record
behind every code in data/vendor_corpus.csv (rule mirrored from the J6 policy
layer). Coding follows CODEBOOK_vendor.md; codes carry verbatim support passages
checked against these archives.

Re-running refreshes only missing archives unless --refetch is given, so the
committed evidence is not silently replaced.
"""

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date
from html.parser import HTMLParser

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "data", "vendor_registry.csv")
RAW_DIR = os.path.join(HERE, "data", "vendor_raw")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer"}
    BLOCK = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr",
             "br", "section", "article"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skipping = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skipping += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skipping:
            self.skipping -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skipping:
            self.parts.append(data)


def html_to_text(html):
    p = TextExtractor()
    p.feed(html)
    text = "".join(p.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en-US,en"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return r.status, raw


ZENDESK_ARTICLE = re.compile(
    r"^(https://[^/]+)/hc/([a-z-]+)/articles/(\d+)")


def fetch_with_fallback(url):
    """Zendesk help centers 403 plain crawlers but expose the same article
    bodies through their public JSON API; fall back to it transparently."""
    try:
        return fetch(url), False
    except urllib.error.HTTPError as e:
        m = ZENDESK_ARTICLE.match(url)
        if e.code != 403 or not m:
            raise
        host, locale, art = m.groups()
        api = f"{host}/api/v2/help_center/{locale}/articles/{art}.json"
        status, raw = fetch(api)
        doc = json.loads(raw)["article"]
        html = f"<h1>{doc.get('title', '')}</h1>\n" + (doc.get("body") or "")
        return (status, html.encode("utf-8")), True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    args = ap.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)
    reg = pd.read_csv(REGISTRY)
    for _, row in reg.iterrows():
        out = os.path.join(RAW_DIR, f"{row['slug']}.txt")
        if os.path.exists(out) and not args.refetch:
            print(f"keep   {row['slug']}")
            continue
        try:
            (status, raw), via_api = fetch_with_fallback(row["url"])
        except Exception as e:
            print(f"FAIL   {row['slug']}: {e}")
            continue
        text = html_to_text(raw.decode("utf-8", errors="replace"))
        header = (f"SOURCE_URL: {row['url']}\n"
                  f"VENDOR: {row['vendor']} | PRODUCT: {row['product']}\n"
                  f"ACCESS_DATE: {date.today().isoformat()}\n"
                  f"HTTP_STATUS: {status}"
                  + (" (zendesk help-center JSON API)" if via_api else "") + "\n"
                  f"RAW_HTML_SHA256: {hashlib.sha256(raw).hexdigest()}\n"
                  + "-" * 72 + "\n")
        with open(out, "w") as fh:
            fh.write(header + text)
        print(f"fetched {row['slug']}: {len(text)} chars")

if __name__ == "__main__":
    main()
