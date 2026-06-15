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

    conv = []
    for q, sub in docs.groupby("event_q"):
        if len(sub) < 3:
            conv.append({"event_q": q, "n_addressing": len(sub), "mean_cosine": np.nan})
            continue
        M = X[sub.index.to_numpy()]
        S = cosine_similarity(M)
        iu = np.triu_indices_from(S, k=1)
        conv.append({"event_q": q, "n_addressing": len(sub),
                     "mean_cosine": round(float(S[iu].mean()), 4)})
    conv = pd.DataFrame(conv).sort_values("event_q")
    conv.to_csv(DATA / "results_convergence.csv", index=False)

    # convergence trend across post-shock quarters with enough institutions
    post = conv[(conv["event_q"] >= 0) & conv["mean_cosine"].notna()]
    slope = pval = np.nan
    if len(post) >= 4:
        r = smf.ols("mean_cosine ~ event_q", data=post).fit()
        slope, pval = r.params["event_q"], r.pvalues["event_q"]

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
    print("\nmean pairwise cosine similarity among AI-addressing institutions, by event quarter:")
    print(conv.to_string(index=False))
    print(f"\npost-shock convergence trend: slope={slope:+.4f} per quarter (p={pval:.3f})"
          if not np.isnan(slope) else "\n(insufficient post-shock quarters for a trend)")
    print(f"\nmost widely shared endpoint phrases (>= 3 institutions):")
    print(shared.head(12).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
