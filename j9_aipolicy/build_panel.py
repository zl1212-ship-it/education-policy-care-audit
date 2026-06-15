"""Score archived snapshots on the provision lexicon and build the quarterly panel.

Two outputs:
  data/panel_snapshots.csv - one row per distinct content version: extracted text
      length, the AI-proximity-scoped provision codes (presence 0/1 + hit counts),
      and the derived restrictiveness indices (CODEBOOK_policy.md).
  data/panel.csv - institution x calendar-quarter panel. The policy state in a
      quarter is the most recent snapshot on or before the quarter end
      (forward-fill / as-of join), so an irregular sequence of page versions
      becomes a balanced grid for the event study. Carries event time relative to
      the ChatGPT shock (2022-11-30, in 2022Q4) and the exposure covariate.

Feasibility filter: an institution enters data/panel.csv only if it has at least
one snapshot before AND one on/after the shock (so the within-page change is
identified). Dropped institutions are listed.

The lexicon lives in one block below so CODEBOOK_policy.md and the code cannot
drift. Stdlib + pandas only.
"""
import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
FRAME = HERE / "data" / "sample_frame.csv"
INDEX = HERE / "data" / "snapshot_index.csv"
COVERAGE = HERE / "data" / "coverage.csv"
OUT_SNAP = HERE / "data" / "panel_snapshots.csv"
OUT_PANEL = HERE / "data" / "panel.csv"

SHOCK = pd.Timestamp("2022-11-30")
WINDOW = 400  # chars: AI-proximity scoping window (CODEBOOK_policy.md)

# ---- lexicon (mirrors CODEBOOK_policy.md) ----------------------------------
AI_TERMS = re.compile(
    r"artificial intelligence|generative a\.?i\.?|gen(?:erative)? ai|chat\s?gpt|"
    r"large language model|\bllms?\b|\bgpt\b|\bA\.I\.\b|\bAI\b", re.I)

PROVISIONS = {
    # restrictive / surveillant
    "prohibition": re.compile(
        r"prohibit|forbidden|not permitted|not allowed|may not use|is not allowed|"
        r"\bban(?:ned|s)?\b|unauthorized use|impermissible|disallow", re.I),
    "detector_surveillance": re.compile(
        r"\bdetector\b|\bdetection\b|turnitin|gptzero|originality report|"
        r"ai[\s-]?detection|detection (?:tool|software)|plagiarism detect", re.I),
    "misconduct_framing": re.compile(
        r"plagiar|academic misconduct|academic dishonest|integrity violation|"
        r"cheating|unauthorized assistance|misrepresent", re.I),
    "sanction": re.compile(
        r"sanction|penalt|failing grade|fail the (?:course|assignment|class)|"
        r"grade of (?:zero|f\b)|zero on the (?:assignment|exam)|suspension|suspended|"
        r"expulsion|expelled|disciplinary (?:action|probation|sanction|measure|consequence|charge)|"
        r"dismissal", re.I),
    # permissive / procedural / protective
    "permitted_use": re.compile(
        r"(?<!not )(?<!no )permitted|you may use|students? may use|"
        r"may use (?:ai|generative|chat|these|the|such|it)|are allowed to use|is allowed|"
        r"encouraged to use|with permission|instructor'?s? discretion|at the discretion|"
        r"depends on the (?:course|instructor)|with the approval|when authorized|"
        r"appropriate use|responsible use", re.I),
    "disclosure": re.compile(
        r"disclos|acknowledge[ds]?\s+(?:the\s+|any\s+|their\s+|its\s+|your\s+)?use|"
        r"cit(?:e|ing|ation)s?\s+(?:the\s+|any\s+|its\s+)?(?:use|tool|ai|source)|"
        r"document\s+(?:your|the|all|its|their)\s+use|declare\s+(?:the|any|your|its)\s+use|"
        r"properly\s+(?:cite|credit|attribute)|"
        r"with\s+(?:proper\s+)?(?:attribution|disclosure|acknowledgment|acknowledgement)", re.I),
    "appeal": re.compile(
        r"\bappeal|\bhearing\b|grievance|\bcontest\b|review board|"
        r"right to respond|due process|reconsideration", re.I),
    "l2_protection": re.compile(
        r"english language learner|multilingual|non[\s-]?native|first language|"
        r"\besl\b|second[\s-]?language|english as a (?:second|additional)|"
        r"international student", re.I),
}
RESTRICTIVE = ["prohibition", "detector_surveillance", "misconduct_framing", "sanction"]
PROCEDURAL = ["permitted_use", "disclosure", "appeal", "l2_protection"]
# ---------------------------------------------------------------------------


class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "head", "title"}
    BLOCK = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "section"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def extract_text(path):
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":  # some Wayback id_ responses are stored gzip-compressed
        import gzip
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    for enc in ("utf-8", "latin-1"):
        try:
            html = raw.decode(enc)
            break
        except UnicodeDecodeError:
            html = raw.decode("utf-8", "ignore")
    p = _Text()
    try:
        p.feed(html)
    except Exception:
        pass
    text = " ".join("".join(p.parts).split())  # collapse all whitespace to single spaces
    return text


def ai_spans(text):
    return [(m.start(), m.end()) for m in AI_TERMS.finditer(text)]


def score_text(text, window=WINDOW):
    spans = ai_spans(text)
    centers = [(a + b) / 2 for a, b in spans]
    out = {"ai_addressed": int(bool(spans)), "n_ai_terms": len(spans),
           "text_len": len(text.split())}
    for name, pat in PROVISIONS.items():
        hits = 0
        for m in pat.finditer(text):
            c = (m.start() + m.end()) / 2
            if any(abs(c - ac) <= window for ac in centers):
                hits += 1
        out[name] = hits
        out[name + "_present"] = int(hits > 0)
    out["restrictive_idx"] = sum(out[n + "_present"] for n in RESTRICTIVE)
    out["procedural_idx"] = sum(out[n + "_present"] for n in PROCEDURAL)
    out["net_restrictiveness"] = out["restrictive_idx"] - out["procedural_idx"]
    out["ai_governance_intensity"] = out["restrictive_idx"] + out["procedural_idx"]
    return out


def event_quarter(ts):
    """Integer quarter offset from 2022Q4 (the shock quarter = 0)."""
    return (ts.year - 2022) * 4 + (ts.quarter - 4)


def main():
    frame = pd.read_csv(FRAME)
    idx = pd.read_csv(INDEX, dtype={"unitid": "Int64"})
    idx = idx[idx["bytes"].notna() & (idx["bytes"] > 0)].copy()
    idx["ts"] = pd.to_datetime(idx["timestamp"], format="%Y%m%d%H%M%S")

    # --- snapshot-level scoring (per page) ---
    snap_rows = []
    for r in idx.itertuples(index=False):
        path = HERE / r.local_path
        if not path.exists():
            continue
        scores = score_text(extract_text(path))
        snap_rows.append({"institution": r.institution, "unitid": r.unitid,
                          "page_type": r.page_type, "original_url": r.original_url,
                          "timestamp": r.timestamp, "ts": r.ts, **scores})
    snaps = pd.DataFrame(snap_rows).sort_values(
        ["unitid", "original_url", "ts"]).reset_index(drop=True)
    snaps.drop(columns=["ts"]).to_csv(OUT_SNAP, index=False)
    print(f"Scored {len(snaps)} snapshots across {snaps['unitid'].nunique()} institutions")

    # --- feasibility filter ---
    # The institution-quarter outcome is the union (max) across the institution's
    # tracked pages, so an institution enters if ANY page has a distinct version
    # BEFORE the shock and ANY page is still captured (alive) AT/AFTER the shock.
    # A frozen page is a valid non-responder; the forward-fill carries its content.
    cov = pd.read_csv(COVERAGE, dtype={"unitid": "Int64"})
    cov = cov[cov["n_captures"] > 0].copy()
    cov["first_ts"] = pd.to_datetime(cov["first_capture"].astype(str),
                                     format="%Y%m%d%H%M%S", errors="coerce")
    cov["last_ts"] = pd.to_datetime(cov["last_capture"].astype(str),
                                    format="%Y%m%d%H%M%S", errors="coerce")
    inst_first = cov.groupby("unitid")["first_ts"].min()
    inst_last = cov.groupby("unitid")["last_ts"].max()
    inst_haspost = cov.groupby("unitid")["has_post"].max()
    n_pre = snaps[snaps["ts"] < SHOCK].groupby("unitid").size()
    keep = [uid for uid in snaps["unitid"].unique()
            if n_pre.get(uid, 0) >= 1 and int(inst_haspost.get(uid, 0)) == 1]
    dropped = sorted(set(snaps["unitid"]) - set(keep))
    print(f"Pass feasibility filter (pre-version & live post-shock): {len(keep)}; "
          f"dropped: {dropped}")

    # --- quarterly forward-fill per page, then union (max) across pages ---
    PRESENCE = [n + "_present" for n in RESTRICTIVE + PROCEDURAL]
    carry = ["ai_addressed", "n_ai_terms", "text_len"] + PRESENCE
    qends = pd.period_range("2021Q1", "2024Q4", freq="Q").to_timestamp(how="end").normalize()
    panel_rows = []
    for uid in keep:
        lo, hi = inst_first.get(uid), inst_last.get(uid)
        grid = qends[(qends >= lo) & (qends <= hi)] if pd.notna(lo) and pd.notna(hi) else qends
        if len(grid) == 0:
            continue
        page_series = []
        for pg, sp in snaps[snaps["unitid"] == uid].groupby("original_url"):
            sp = sp.sort_values("ts")
            asof = pd.merge_asof(pd.DataFrame({"ts": grid}), sp[["ts"] + carry],
                                 on="ts", direction="backward")
            asof[carry] = asof[carry].fillna(0)  # page absent / not yet created -> zeros
            page_series.append(asof)
        agg = pd.concat(page_series).groupby("ts", as_index=False)[carry].max()
        agg["restrictive_idx"] = agg[[n + "_present" for n in RESTRICTIVE]].sum(axis=1)
        agg["procedural_idx"] = agg[[n + "_present" for n in PROCEDURAL]].sum(axis=1)
        agg["net_restrictiveness"] = agg["restrictive_idx"] - agg["procedural_idx"]
        agg["ai_governance_intensity"] = agg["restrictive_idx"] + agg["procedural_idx"]
        agg["unitid"] = uid
        agg["quarter"] = agg["ts"].dt.to_period("Q").astype(str)
        agg["event_q"] = agg["ts"].apply(event_quarter)
        agg["post"] = (agg["event_q"] >= 0).astype(int)
        panel_rows.append(agg)
    panel = pd.concat(panel_rows, ignore_index=True)

    meta = frame[["institution", "state", "control", "carnegie", "unitid",
                  "intl_share", "total_enroll"]].copy()
    panel = panel.merge(meta, on="unitid", how="left")
    int_cols = PRESENCE + ["ai_addressed", "restrictive_idx", "procedural_idx",
                           "net_restrictiveness", "ai_governance_intensity"]
    for c in int_cols:
        panel[c] = panel[c].round().astype("Int64")
    panel = panel.drop(columns=["ts"]).sort_values(["unitid", "event_q"])
    front = ["institution", "unitid", "state", "control", "carnegie", "quarter",
             "event_q", "post", "intl_share", "total_enroll"]
    panel = panel[front + [c for c in panel.columns if c not in front]]
    panel.to_csv(OUT_PANEL, index=False)
    print(f"Wrote {OUT_PANEL}  ({len(panel)} institution-quarter rows, "
          f"{panel['unitid'].nunique()} institutions, "
          f"event_q {panel['event_q'].min()}..{panel['event_q'].max()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
