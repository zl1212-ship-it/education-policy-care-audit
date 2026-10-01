"""Direct evidence on the isomorphism mechanism: do institutions' AI policy texts
CONVERGE on a shared language after the shock?

The event study shows the written response was broad, lagged, and not graded by
exposure, a pattern consistent with institutional isomorphism. This script tests
the mechanism directly rather than by elimination. For each institution-quarter it
assembles the AI-relevant language on the tracked pages (the text within a window
of every AI term, forward-filled to the quarter), and measures how similar
institutions' AI texts are to one another. If institutions are copying a shared
template, the mean pairwise similarity among those addressing AI should rise as the
response spreads; if each campus wrote independently, it should not.

Outputs:
  data/results_convergence.csv  - per event quarter: number of institutions
      addressing AI, and the mean pairwise TF-IDF cosine similarity among them.
  data/shared_phrases.csv       - the multi-word phrases most widely shared across
      institutions' endpoint AI texts (the borrowed-template language).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import build_panel as bp

HERE = Path(__file__).parent
DATA = HERE / "data"
SHOCK = pd.Timestamp("2022-11-30")
AIWIN = 300  # chars each side of an AI term


def ai_text(path, _cache={}):
    if path in _cache:
        return _cache[path]
    t = bp.extract_text(HERE / path)
    spans = [(m.start(), m.end()) for m in bp.AI_TERMS.finditer(t)]
    out = " ".join(t[max(0, s - AIWIN):e + AIWIN] for s, e in spans).lower()
    _cache[path] = out
    return out


def event_q(ts):
    return (ts.year - 2022) * 4 + (ts.quarter - 4)


def main():
    panel = pd.read_csv(DATA / "panel.csv")
    keep = set(panel["unitid"].unique())
    idx = pd.read_csv(DATA / "snapshot_index.csv")
    idx = idx[idx["bytes"].notna() & (idx["bytes"] > 0) & idx["unitid"].isin(keep)].copy()
    idx["ts"] = pd.to_datetime(idx["timestamp"], format="%Y%m%d%H%M%S")

    qends = pd.period_range("2021Q1", "2024Q4", freq="Q").to_timestamp(how="end").normalize()
    # institution-quarter AI documents (as-of forward fill per page, unioned)
    rows = []
    for uid, g in idx.groupby("unitid"):
        for qe in qends:
            parts = []
            for url, gp in g.groupby("original_url"):
                sub = gp[gp["ts"] <= qe]
                if len(sub):
                    parts.append(ai_text(sub.sort_values("ts").iloc[-1]["local_path"]))
            doc = " ".join(p for p in parts if p).strip()
            if doc:
                rows.append({"unitid": uid, "event_q": event_q(qe), "doc": doc})
    docs = pd.DataFrame(rows)

    # global TF-IDF vocabulary so per-quarter similarities are comparable
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english", max_features=5000)
    X = vec.fit_transform(docs["doc"])
    docs = docs.reset_index(drop=True)

    def quarter_cos(frame):
        """mean pairwise cosine per event quarter for the given institution-quarter rows."""
        out = {}
        for q, sub in frame.groupby("event_q"):
            if sub["unitid"].nunique() >= 3:
                S = cosine_similarity(X[sub.index.to_numpy()])
                out[q] = float(S[np.triu_indices_from(S, k=1)].mean())
        return out

    def post_slope(frame):
        c = quarter_cos(frame)
        pts = pd.DataFrame([(q, v) for q, v in c.items() if q >= 0], columns=["q", "c"])
        return smf.ols("c ~ q", pts).fit().params["q"] if len(pts) >= 4 else np.nan

    # full-sample similarity by quarter
    allcos = quarter_cos(docs)
    nby = docs.groupby("event_q")["unitid"].nunique().to_dict()
    # incumbent cohort: institutions already addressing AI in the first 3 post quarters,
    # so a rising similarity among THEM cannot be a composition (new-entrant) artifact
    incumbents = set(docs[(docs["event_q"].between(0, 2))]["unitid"].unique())
    inccos = quarter_cos(docs[docs["unitid"].isin(incumbents)])
    conv = pd.DataFrame({"event_q": sorted(set(allcos) | set(inccos))})
    conv["n_addressing"] = conv["event_q"].map(nby)
    conv["mean_cosine"] = conv["event_q"].map(lambda q: round(allcos.get(q, np.nan), 4))
    conv["incumbent_cosine"] = conv["event_q"].map(
        lambda q: round(inccos[q], 4) if q in inccos else np.nan)
    conv.to_csv(DATA / "results_convergence.csv", index=False)

    # honest inference: cluster bootstrap over institutions (resample the institution
    # set, so pairwise non-independence is respected; no self-pairs), full and incumbent
    slope = post_slope(docs)
    inc_slope = post_slope(docs[docs["unitid"].isin(incumbents)])
    rng = np.random.default_rng(7)
    uids = docs["unitid"].unique()
    bs = []
    for _ in range(800):
        keepset = set(rng.choice(uids, len(uids), replace=True))
        s = post_slope(docs[docs["unitid"].isin(keepset)])
        if not np.isnan(s):
            bs.append(s)
    bs = np.array(bs)
    ci_lo, ci_hi, share_pos = (np.percentile(bs, 2.5), np.percentile(bs, 97.5),
                               float(np.mean(bs > 0)))

    # most widely shared phrases across endpoint (last observed) AI docs
    endpoint = docs.sort_values("event_q").groupby("unitid").tail(1)
    cv = TfidfVectorizer(ngram_range=(3, 5), min_df=2, stop_words="english")
    Xc = cv.fit_transform(endpoint["doc"])
    df_count = np.asarray((Xc > 0).sum(axis=0)).ravel()  # how many institutions use each phrase
    terms = np.array(cv.get_feature_names_out())
    order = np.argsort(-df_count)
    shared = pd.DataFrame({"phrase": terms[order][:30],
                           "n_institutions": df_count[order][:30]})
    shared = shared[shared["n_institutions"] >= 3]
    shared.to_csv(DATA / "shared_phrases.csv", index=False)

    print(f"Institution-quarter AI documents: {len(docs)} across {docs['unitid'].nunique()} institutions")
    print("\nmean pairwise cosine by event quarter (full sample / incumbent cohort):")
    print(conv.to_string(index=False))
    print(f"\npost-shock slope: full={slope:+.4f}/qtr, incumbent cohort (n={len(incumbents)})={inc_slope:+.4f}/qtr")
    print(f"institution cluster-bootstrap 95% CI for full slope: [{ci_lo:+.4f}, {ci_hi:+.4f}]; "
          f"share of resamples > 0: {share_pos:.2f}")
    print(f"\nmost widely shared endpoint phrases (>= 3 institutions):")
    print(shared.head(12).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
