"""Boilerplate-stripped text extraction for the archived policy pages.

extract_text_raw(path)   -> the pipeline's original extractor (build_panel.extract_text):
                            drops script/style/noscript/head/title only; keeps navigation,
                            headers, footers, sidebars and link lists.
extract_text_clean(path) -> same decoding, then: (1) drop structural boilerplate elements
                            (nav, header, footer, aside, forms, hidden elements, elements whose
                            ARIA role or id/class marks them as navigation, menus, cookie bars,
                            breadcrumbs, social links, pagination and so on); (2) prefer the
                            main-content region when a page declares one and it holds at least
                            150 words; (3) drop any remaining block that is mostly link text
                            (anchor share above 0.5) and short (under 50 words), so menus and
                            link lists go while paragraphs with inline links stay.
Returns single-space-collapsed text exactly like build_panel.extract_text so that
build_panel.score_text can be applied unchanged. extract_clean_info(path) also returns which
rule selected the content region.
"""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import gzip
import re
import sys
from pathlib import Path

import lxml.html
from lxml import etree

if str(XN) not in sys.path:
    sys.path.insert(0, str(XN))
import build_panel as B  # noqa: E402

BOILER_TAGS = {"script", "style", "noscript", "head", "title", "nav", "header", "footer",
               "aside", "form", "button", "select", "option", "iframe", "svg", "template",
               "meta", "link", "input", "label", "textarea", "video", "audio", "canvas",
               "map", "object", "embed", "menu", "dialog"}
BOILER_ROLES = {"navigation", "banner", "contentinfo", "menu", "menubar", "menuitem",
                "complementary", "search", "searchbox", "toolbar", "dialog", "alertdialog"}
# role=tablist / tab are NOT boilerplate: accordion and tab widgets wrap real policy text
BOILER_ATTR = re.compile(
    r"(?<![a-z])(nav|navbar|navigation|menu|menus|megamenu|mega-menu|footer|sidebar|side-nav|"
    r"sidenav|subnav|sub-nav|breadcrumb|breadcrumbs|cookie|cookies|skip-link|skiplink|skip-to|"
    r"toolbar|social|share|sharing|masthead|utility|utility-nav|topbar|top-bar|modal|popup|"
    r"pop-up|related-links|related-content|pagination|pager|site-header|site-footer|"
    r"page-footer|page-header|global-nav|globalnav|global-header|global-footer|quicklinks|"
    r"quick-links|offcanvas|off-canvas|hamburger|searchbar|search-bar|site-search|"
    r"back-to-top|alert-banner|emergency|announcement-bar|secondary-nav|secondarynav|"
    r"primary-nav|primarynav|main-nav|mainnav|left-nav|leftnav|right-nav|rightnav|"
    r"local-nav|localnav|section-nav|sectionnav|site-nav|sitenav|header-nav|footer-nav|"
    r"login|signin|sign-in)(?![a-z])", re.I)
BLOCK = {"p", "div", "li", "ul", "ol", "section", "article", "main", "td", "th", "tr",
         "table", "dl", "dd", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre",
         "figure", "figcaption", "details", "summary", "br", "hr", "body", "html", "center",
         "fieldset", "legend", "address", "caption", "thead", "tbody", "tfoot"}
LD_BLOCK = {"p", "div", "li", "ul", "ol", "section", "td", "dl", "dd", "dt", "table", "tr",
            "span", "small", "strong", "em", "b", "i"}
MAIN_XPATHS = [
    "//main", "//*[@role='main']", "//*[@id='content']", "//*[@id='main-content']",
    "//*[@id='maincontent']", "//*[@id='main']", "//*[@id='page-content']",
    "//*[@id='primary']", "//*[@id='mainContent']", "//article",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' main-content ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' page-content ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' content ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' entry-content ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' article-content ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' field--name-body ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' node__content ')]",
]
MIN_MAIN_WORDS = 150
LD_RULES = ((0.8, 80), (0.6, 25))  # (anchor share above, words below)
MENU_ANCHOR_WORDS = 10  # a link-dense block whose links average 10+ words each is a card grid, not a menu


def _read_bytes(path):
    raw = Path(path).read_bytes()
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    return raw


def _parse(raw):
    try:
        root = lxml.html.document_fromstring(raw)
    except (etree.ParserError, ValueError):
        for enc in ("utf-8", "latin-1"):
            try:
                html = raw.decode(enc)
                break
            except UnicodeDecodeError:
                html = raw.decode("utf-8", "ignore")
        try:
            root = lxml.html.document_fromstring(html)
        except (etree.ParserError, ValueError):
            return None
    return root


def _is_boiler(el, doc_words=None):
    tag = el.tag if isinstance(el.tag, str) else ""
    if tag in ("body", "html"):
        return False
    if tag in BOILER_TAGS:
        return True
    a = el.attrib
    role = (a.get("role") or "").lower()
    if role in BOILER_ROLES:
        return True
    # hidden / aria-hidden / display:none are NOT treated as boilerplate: collapsed accordion
    # panels and tabbed sections carry real policy text that the raw extractor also reads
    ident = " ".join(x for x in (a.get("id", ""), a.get("class", "")) if x)
    if ident and BOILER_ATTR.search(ident):
        # an id/class hit on a wrapper that holds most of the page (Drupal body classes such as
        # "one-sidebar sidebar-second", page wrappers) is not boilerplate; keep it and let the
        # rules inside it do the work
        if doc_words and _words(el) >= 0.6 * doc_words and _words(el) >= 150:
            return False
        return True
    return False


def _words(el):
    return len(el.text_content().split())


def _anchor_share(el):
    txt = el.text_content()
    n = len(txt.split())
    if n == 0:
        return 1.0, 0, 0.0
    lens = [len(x.text_content().split()) for x in el.iter("a")]
    a = sum(lens)
    mean_anchor = (a / len(lens)) if lens else 0.0
    return min(1.0, a / n), n, mean_anchor


ALWAYS_DROP = {"script", "style", "noscript", "head", "title", "iframe", "svg", "template", "meta", "link",
               "select", "option", "button", "input", "label", "textarea", "video", "audio", "canvas", "map",
               "object", "embed"}
LENIENT_TAGS = ALWAYS_DROP | {"nav", "footer"}
LENIENT_ROLES = {"navigation", "contentinfo", "menu", "menubar", "search"}


def _strip_boilerplate(root, lenient=False):
    # comments and processing instructions
    for c in list(root.iter(etree.Comment)) + list(root.iter(etree.ProcessingInstruction)):
        try:
            c.drop_tree()
        except Exception:
            pass
    # pass 1: structural boilerplate by tag and ARIA role (never by id/class). A header, form,
    # aside or complementary region that wraps half or more of the page (ASP.NET sites wrap the
    # whole page in a form; some templates put the content in a header or a role=complementary
    # column) is kept and only its inner boilerplate is removed.
    tags = LENIENT_TAGS if lenient else BOILER_TAGS
    roles = LENIENT_ROLES if lenient else BOILER_ROLES
    page_words = _words(root)
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.getparent() is None:
            continue
        if el.tag in ("body", "html"):
            continue
        role = (el.attrib.get("role") or "").lower()
        if el.tag in tags or role in roles:
            if el.tag not in ALWAYS_DROP and page_words and _words(el) >= 0.5 * page_words and _words(el) >= 150:
                continue
            try:
                el.drop_tree()
            except Exception:
                pass
    if lenient:
        return root
    # pass 2: id/class-marked boilerplate, measured against what is left; a wrapper that holds
    # half or more of the remaining page (e.g. class "right-sidebar" on the content container,
    # "dialog-off-canvas-main-canvas" around the whole page) is kept
    doc_words = _words(root)
    dropped = []
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.getparent() is None:
            continue
        if el.tag in ("body", "html"):
            continue
        ident = " ".join(x for x in (el.attrib.get("id", ""), el.attrib.get("class", "")) if x)
        if ident and BOILER_ATTR.search(ident):
            n = _words(el)
            if doc_words and n >= 0.5 * doc_words and n >= 150:
                continue
            dropped.append(el)
    gone = set()
    for el in dropped:
        if any(a in gone for a in el.iterancestors()):
            continue
        gone.add(el)
        try:
            el.drop_tree()
        except Exception:
            pass
    return root


def _prune_link_dense(root):
    gone = set()
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.tag not in LD_BLOCK or el.getparent() is None:
            continue
        if any(a in gone for a in el.iterancestors()):
            continue
        share, n, mean_anchor = _anchor_share(el)
        if mean_anchor >= MENU_ANCHOR_WORDS:
            continue  # long linked blurbs (summary cards) are content, not a menu
        if any(share > sh and n < wd for sh, wd in LD_RULES):
            gone.add(el)
            try:
                el.drop_tree()
            except Exception:
                pass
    return root


def _select_main(root):
    best, best_n, best_rule = None, 0, "body"
    for xp in MAIN_XPATHS:
        try:
            cands = root.xpath(xp)
        except Exception:
            continue
        for c in cands:
            n = _words(c)
            if n >= MIN_MAIN_WORDS and n > best_n:
                best, best_n, best_rule = c, n, xp
    return best, best_rule


_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _text(el):
    for e in el.iter():
        if isinstance(e.tag, str) and e.tag in BLOCK:
            try:
                e.text = " " + _CTRL.sub(" ", e.text or "")
                e.tail = " " + _CTRL.sub(" ", e.tail or "")
            except ValueError:
                pass
    return " ".join(_CTRL.sub(" ", el.text_content()).split())


def _pdf_text(raw):
    """Text of a PDF stored by the fetcher as if it were HTML (two curated seeds are PDFs)."""
    import io
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        return " ".join(" ".join((pg.extract_text() or "").split()) for pg in reader.pages)
    except Exception:
        return ""


_BIN_SIG = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"PK\x03\x04", b"RIFF", b"%!PS", b"\x00\x00\x00")


def _looks_binary(raw):
    head = raw[:4000]
    return raw[:4] in _BIN_SIG or raw[:3] in _BIN_SIG or b"\x00" in head


def extract_clean_info(path):
    raw = _read_bytes(path)
    if raw[:5] == b"%PDF-":
        return _text_from_string(_pdf_text(raw)), "pdf"
    if _looks_binary(raw):
        return "", "binary"  # an image or other non-text file stored as a page
    root = _parse(raw)
    if root is None:
        return "", "unparseable"
    raw_words = _words(root)
    root = _strip_boilerplate(root)
    main, rule = _select_main(root)
    region = main if main is not None else root
    region = _prune_link_dense(region)
    text = _text(region)
    # fallback: if the strict pass emptied a page that had real text, rerun leniently (only nav,
    # footer, scripts and link lists removed; no id/class rules, no header/form/aside rules)
    if raw_words >= 100 and len(text.split()) < max(30, 0.1 * raw_words):
        root2 = _strip_boilerplate(_parse(raw), lenient=True)
        main2, rule2 = _select_main(root2)
        region2 = _prune_link_dense(main2 if main2 is not None else root2)
        text2 = _text(region2)
        if len(text2.split()) > len(text.split()):
            return text2, rule2 + "|lenient"
    return text, rule


def _text_from_string(t):
    return " ".join(_CTRL.sub(" ", t).split())


def extract_text_clean(path):
    return extract_clean_info(path)[0]


def extract_text_raw(path):
    return B.extract_text(Path(path))
