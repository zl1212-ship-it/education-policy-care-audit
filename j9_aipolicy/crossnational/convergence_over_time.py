"""Convergence over event time: mean pairwise AI-text similarity (TF-IDF cosine) by
event quarter, within-system and cross-system, on the 4-system panel; with an
institution-cluster bootstrap on the post-shock slope, a topic-strip robustness check,
a fixed-cohort (balanced-panel) check, and a country-label permutation test of the
within-vs-cross gap. Reads US (../) + cross-national (./) snapshots. Stdlib + sklearn."""
import sys, csv
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

XN = Path(__file__).resolve().parent           # crossnational/
REPO = XN.parent                                # j9_aipolicy/ (US pipeline)
sys.path.insert(0, str(XN))
import build_panel as B
AIWIN = 300
SHOCK = pd.Timestamp("2022-11-30")


def ai_text(path):
    t = B.extract_text(path)
    sp = [(m.start(), m.end()) for m in B.AI_TERMS.finditer(t)]
    return " ".join(t[max(0, s - AIWIN):e + AIWIN] for s, e in sp).lower()


def load(index_csv, base, system_of):
    rows = [r for r in csv.DictReader(open(index_csv)) if r.get("bytes") not in ("", "0", None)]
    out = []
    for r in rows:
        p = base / r["local_path"]
        if p.exists():
            out.append({"uid": str(r["unitid"]), "sys": system_of(r), "url": r["original_url"],
                        "ts": pd.to_datetime(r["timestamp"], format="%Y%m%d%H%M%S"), "path": p})
    return out


snaps = load(REPO / "data" / "snapshot_index.csv", REPO, lambda r: "US")
snaps += load(XN / "data" / "snapshot_index.csv", XN, lambda r: r["state"])
snaps = pd.DataFrame(snaps)
sysmap = snaps.groupby("uid")["sys"].first().to_dict()
print("institutions:", snaps["uid"].nunique(), "snapshots:", len(snaps))

# institution x event-quarter AI doc (as-of latest snapshot per page on/before quarter end)
qs = [pd.Period("2022Q4", freq="Q") + k for k in range(-7, 9)]
qends = {k: (pd.Period("2022Q4", freq="Q") + k).to_timestamp(how="end").normalize() for k in range(-7, 9)}
cache = {}
def text_of(path):
    if path not in cache:
        cache[path] = ai_text(path)
    return cache[path]

docs = []
for uid, g in snaps.groupby("uid"):
    for k, qe in qends.items():
        parts = []
        for url, gp in g.groupby("url"):
            sub = gp[gp["ts"] <= qe]
            if len(sub):
                parts.append(text_of(sub.sort_values("ts").iloc[-1]["path"]))
        doc = " ".join(p for p in parts if p).strip()
        if doc:
            docs.append({"uid": uid, "sys": sysmap[uid], "event_q": k, "doc": doc})
docs = pd.DataFrame(docs).reset_index(drop=True)

vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english", max_features=5000)
X = vec.fit_transform(docs["doc"])

rows = []
for k in range(-7, 9):
    sub = docs[docs["event_q"] == k]
    if sub["uid"].nunique() < 4:
        continue
    idx = sub.index.to_numpy()
    S = cosine_similarity(X[idx])
    sysv = sub["sys"].to_numpy()
    win, cro = [], []
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            (win if sysv[i] == sysv[j] else cro).append(S[i, j])
    rows.append({"event_q": k, "n_inst": sub["uid"].nunique(),
                 "within_cos": round(np.mean(win), 4) if win else np.nan,
                 "cross_cos": round(np.mean(cro), 4) if cro else np.nan,
                 "all_cos": round(S[np.triu_indices_from(S, 1)].mean(), 4)})
out = pd.DataFrame(rows)
out.to_csv(XN / "results_convergence_over_time.csv", index=False)
print(out.to_string(index=False))

pre = out[out["event_q"] < 0]["all_cos"].mean()
post = out[out["event_q"] >= 6]["all_cos"].mean()
print(f"\nbaseline (pre-shock mean all_cos) = {pre:.3f}")
print(f"late post (q6-8 mean all_cos)     = {post:.3f}  ({(post/pre-1)*100:.0f}% above baseline)")
# simple post-shock slope on all_cos
postdf = out[out["event_q"] >= 0].dropna(subset=["all_cos"])
if len(postdf) >= 4:
    sl = np.polyfit(postdf["event_q"], postdf["all_cos"], 1)[0]
    print(f"post-shock slope (all_cos ~ event_q) = {sl:+.4f}/quarter")


# ---- inference: institution-cluster bootstrap on the post-shock slope ----
def quarter_allcos(Xmat, dfsub):
    o = {}
    for k in range(-7, 9):
        s = dfsub[dfsub["event_q"] == k]
        if s["uid"].nunique() >= 4:
            S = cosine_similarity(Xmat[s.index.to_numpy()])
            o[k] = S[np.triu_indices_from(S, 1)].mean()
    return o


def post_slope_of(series):
    pts = [(k, v) for k, v in series.items() if k >= 0]
    if len(pts) < 4:
        return np.nan
    ks, vs = zip(*pts)
    return np.polyfit(ks, vs, 1)[0]


obs = post_slope_of(quarter_allcos(X, docs))
rng = np.random.default_rng(7)
uids = docs["uid"].unique()
bs = []
for _ in range(400):
    keep = set(rng.choice(uids, len(uids), replace=True))
    sl_b = post_slope_of(quarter_allcos(X, docs[docs["uid"].isin(keep)]))
    if not np.isnan(sl_b):
        bs.append(sl_b)
bs = np.array(bs)
print(f"\n[inference] post-shock slope {obs:+.4f}/qtr; institution bootstrap 95% CI "
      f"[{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]; share of resamples > 0 = {np.mean(bs>0):.2f}")

# ---- topic-strip robustness: remove the bare AI nouns, keep governance language ----
from sklearn.feature_extraction import text as _t
AI_NOUNS = {"ai", "generative", "artificial", "intelligence", "chatgpt", "gpt", "chat",
            "llm", "llms", "genai", "gen"}
vec2 = TfidfVectorizer(ngram_range=(1, 2), min_df=3,
                       stop_words=list(_t.ENGLISH_STOP_WORDS.union(AI_NOUNS)), max_features=5000)
X2 = vec2.fit_transform(docs["doc"])
s2 = quarter_allcos(X2, docs)
pre2 = np.mean([v for k, v in s2.items() if k < 0])
post2 = np.mean([v for k, v in s2.items() if k >= 6])
print(f"[topic-strip] AI nouns removed: pre-shock {pre2:.3f} -> late post {post2:.3f} "
      f"({(post2/pre2-1)*100:.0f}% above baseline), post-shock slope {post_slope_of(s2):+.4f}/qtr")

# ---- composition check: fix the cohort of early AI-addressers, track THEIR similarity ----
cohort = set(docs[docs["event_q"].between(0, 2)]["uid"].unique())
coh = docs[docs["uid"].isin(cohort)]
cs = quarter_allcos(X, coh)
print(f"\n[fixed cohort] {len(cohort)} institutions addressing AI by q2, tracked on a balanced set:")
for k in sorted(cs):
    print(f"  q{k:+d}: cos={cs[k]:.4f} (n={coh[coh.event_q==k].uid.nunique()})")
print(f"  fixed-cohort post-shock slope = {post_slope_of(cs):+.4f}/qtr")

# ---- permutation test: shuffle country labels on the within-vs-cross gap (endpoint docs) ----
endpoint = docs.sort_values("event_q").groupby("uid").tail(1).reset_index(drop=True)
Xe = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english",
                     max_features=4000).fit_transform(endpoint["doc"])
Se = cosine_similarity(Xe)
sysv = endpoint["sys"].to_numpy()
def within_minus_cross(labels):
    w, c = [], []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            (w if labels[i] == labels[j] else c).append(Se[i, j])
    return np.mean(w) - np.mean(c), np.mean(w), np.mean(c)
obs, w0, c0 = within_minus_cross(sysv)
rng2 = np.random.default_rng(3)
perm = np.array([within_minus_cross(rng2.permutation(sysv))[0] for _ in range(2000)])
p = np.mean(np.abs(perm) >= abs(obs))
print(f"\n[permutation/transnational] endpoint within={w0:.3f} cross={c0:.3f}, within-minus-cross={obs:+.4f}; "
      f"country-label-shuffle null 95% [{np.percentile(perm,2.5):+.4f},{np.percentile(perm,97.5):+.4f}], two-sided p={p:.3f}")
print("  (large p => within-vs-cross gap not distinguishable from a country-label permutation null)")
