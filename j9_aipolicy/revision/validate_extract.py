"""Document the clean extractor on 16 endpoint pages (4 per system, seed 0): raw vs clean words,
the content rule, and the text of every removed block (first 160 chars), so the removal can be
audited by eye. Writes reports/validate_extract.md."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import random, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B

def instrumented(path):
    raw = E._read_bytes(path)
    if raw[:5] == b"%PDF-":
        return [], [], [], "pdf", E.extract_text_clean(path)
    root = E._parse(raw)
    removed1, removed2, removed3 = [], [], []
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.getparent() is None or el.tag in ("body", "html"):
            continue
        role = (el.attrib.get("role") or "").lower()
        if el.tag in E.BOILER_TAGS or role in E.BOILER_ROLES:
            if el.tag not in ("script", "style", "head", "title", "noscript", "meta", "link", "svg", "iframe"):
                t = " ".join(el.text_content().split())
                if t:
                    removed1.append((el.tag, role, t[:160]))
            try: el.drop_tree()
            except Exception: pass
    doc_words = E._words(root)
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.getparent() is None or el.tag in ("body", "html"):
            continue
        ident = " ".join(x for x in (el.attrib.get("id", ""), el.attrib.get("class", "")) if x)
        if ident and E.BOILER_ATTR.search(ident):
            n = E._words(el)
            if doc_words and n >= 0.5 * doc_words and n >= 150:
                continue
            t = " ".join(el.text_content().split())
            if t:
                removed2.append((el.tag, ident[:50], t[:160]))
            try: el.drop_tree()
            except Exception: pass
    main, rule = E._select_main(root)
    region = main if main is not None else root
    for el in list(region.iter()):
        if not isinstance(el.tag, str) or el.tag not in E.LD_BLOCK or el.getparent() is None:
            continue
        share, n, mean_anchor = E._anchor_share(el)
        if mean_anchor >= E.MENU_ANCHOR_WORDS:
            continue
        if any(share > sh and n < wd for sh, wd in E.LD_RULES):
            t = " ".join(el.text_content().split())
            if t:
                removed3.append((el.tag, f"share={share:.2f} words={n}", t[:160]))
            try: el.drop_tree()
            except Exception: pass
    return removed1, removed2, removed3, rule, E._text(region)

sc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
sc["ts"] = pd.to_datetime(sc["timestamp"], format="%Y%m%d%H%M%S")
ep = sc.sort_values("ts").groupby(["unitid"]).tail(1)
random.seed(0)
lines = ["# Clean extractor: audit of 16 endpoint pages (4 per system, seed 0)\n",
         "Rules: (1) drop nav/header/footer/aside/form and ARIA navigation, banner, contentinfo, menu, complementary, search, toolbar, dialog; "
         "(2) drop elements whose id/class marks them as navigation, menus, footers, sidebars, breadcrumbs, cookie bars, social links, pagination, "
         "unless the element holds half or more of the remaining page; (3) prefer the declared main-content region when it holds 150+ words; "
         "(4) drop remaining link-dense blocks (anchor share above 0.8 and under 80 words, or above 0.6 and under 25 words) whose links average under 10 words, "
         "so menus go but linked summary cards and paragraphs with inline links stay. PDFs stored as pages are read with pypdf.\n"]
for s in ["US", "UK", "AU", "CA"]:
    pool = ep[ep.system == s]
    for r in pool.sample(min(4, len(pool)), random_state=0).itertuples(index=False):
        base = PIPE if r.pipeline == "US" else XN
        p = base / r.local_path
        raw = B.extract_text(p)
        r1, r2, r3, rule, clean = instrumented(p)
        lines.append(f"\n## {s} | {r.institution} | {r.page_type} | {r.timestamp}\n")
        lines.append(f"URL: {r.original_url}  \nraw words {len(raw.split())}, clean words {len(clean.split())}, content rule `{rule}`\n")
        lines.append(f"\nClean text (first 400 chars): {clean[:400]}\n")
        for label, rem in (("Structural blocks removed", r1), ("Id/class-marked blocks removed", r2), ("Link-dense blocks removed", r3)):
            if rem:
                lines.append(f"\n{label} ({len(rem)}):\n")
                for tag, why, t in rem[:12]:
                    lines.append(f"- `<{tag}>` {why}: {t}")
                if len(rem) > 12:
                    lines.append(f"- ... and {len(rem) - 12} more")
(AN / "validate_extract.md").write_text("\n".join(lines))
print("wrote", RP / "validate_extract.md", len(lines), "lines")
