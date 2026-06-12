"""Score every essay with three automated-essay-scoring model families.

What this does and why
----------------------
Trains standard AES models to predict the HUMAN score from essay text, then
records each model's OUT-OF-FOLD prediction for every essay (5-fold CV, fixed
seed): each essay is scored by a model that never saw it during training, as
a deployed engine would. analyze_gaps.py then compares machine and human
scores by writer subgroup. Three families span the design space commercial
engines occupy:

  handfeat - transparent hand-crafted text features (length, lexical
             diversity, word frequency proxies, punctuation, a dictionary
             out-of-vocabulary share) + ridge regression; e-rater-style.
  tfidf    - TF-IDF word 1-2 grams and character 3-5 grams + ridge; the
             strong classic text-regression baseline.
  embed    - frozen MiniLM sentence-transformer embeddings (mean-pooled,
             truncated at 512 tokens) + ridge head; the neural family,
             CPU-feasible. Model revision pinned below.

Two scoring protocols per corpus:
  oof  - 5-fold out-of-fold (random folds stratified by score): engine
         trained on the same population and prompts it scores.
  lopo - leave-one-prompt-out: engine never saw the prompt it scores
         (the deployment-realistic transfer setting; robustness).

The audit treats the machine score as a measurement of the essay, not of the
student: no causal claim. Models are trained on ALL essays (including rows
with missing demographics, as deployment would); subgroup analysis later
restricts to labeled rows.

Input : data/panel_persuade.csv, data/panel_ellipse.csv, data/raw/
Output: data/machine_scores_persuade.csv  (panel_id, human, fold,
        pred_<fam>_oof, pred_<fam>_lopo)
        data/machine_scores_ellipse.csv   (text_id_kaggle, human, ditto)
        data/scorer_quality.csv           (QWK / r / RMSE per family,
        protocol, corpus - the models must be competitive for the audit
        to speak to deployed practice)
Cache : data/cache/  (MiniLM embeddings; delete to recompute)

Run build_panel.py first. ~30-60 min on CPU for the embedding pass.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import StratifiedKFold

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
DATA = HERE / "data"
CACHE = HERE / "data" / "cache"

SEED = 8
N_FOLDS = 5
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_REVISION = "main"  # TODO: pin to a commit SHA at manuscript freeze
FAMILIES = ["handfeat", "tfidf", "embed"]

WORDS = re.compile(r"[A-Za-z']+")
SENTS = re.compile(r"[.!?]+")


# ---------------------------------------------------------------- text load
def load_texts_persuade() -> pd.Series:
    """full_text per panel_id, from the raw releases (text is not in git)."""
    parts = []
    for split, fname in [
        ("train", "persuade_2.0_human_scores_demo_id_github.csv"),
        ("test", "persuade_corpus_2.0_test.csv"),
    ]:
        df = pd.read_csv(RAW / fname, usecols=["essay_id", "full_text"])
        df = df.drop_duplicates("essay_id")
        df.index = split + "/" + df.essay_id.astype(str)
        parts.append(df.full_text)
    return pd.concat(parts)


def load_texts_ellipse() -> pd.Series:
    parts = []
    for fname in ["ELLIPSE_Final_github_train.csv",
                  "ELLIPSE_Final_github_test.csv"]:
        df = pd.read_csv(RAW / fname,
                         usecols=["text_id_kaggle", "full_text"])
        parts.append(df.set_index("text_id_kaggle").full_text)
    return pd.concat(parts)


# ------------------------------------------------------------------ features
def _dictionary() -> set:
    """macOS system word list; OOV share proxies spelling/nonword density."""
    path = Path("/usr/share/dict/words")
    if not path.exists():
        return set()
    return {w.strip().lower() for w in path.read_text().splitlines()}


def hand_features(texts: pd.Series) -> np.ndarray:
    dic = _dictionary()
    rows = []
    for t in texts:
        words = WORDS.findall(t)
        lw = [w.lower() for w in words]
        n = max(len(words), 1)
        n_sent = max(len([s for s in SENTS.split(t) if s.strip()]), 1)
        wlen = [len(w) for w in words]
        rows.append([
            np.log1p(len(words)),                       # length
            np.log1p(len(t)),
            np.mean(wlen) if wlen else 0.0,             # word length
            np.mean([l > 6 for l in wlen]) if wlen else 0.0,
            len(set(lw)) / n,                           # type-token ratio
            len(words) / n_sent,                        # sentence length
            t.count(",") / n,                           # punctuation rates
            t.count(";") / n,
            (t.count('"') + t.count("'")) / n,
            t.count("\n\n") + t.count("\r\n\r\n"),      # paragraphing
            np.mean([w not in dic for w in lw]) if dic and lw else 0.0,  # OOV
            np.mean([w[0].isupper() for w in words]) if words else 0.0,
        ])
    return np.asarray(rows)


def embed_features(texts: pd.Series, cache_name: str) -> np.ndarray:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"{cache_name}.npy"
    if cache.exists():
        emb = np.load(cache)
        if len(emb) == len(texts):
            return emb
    import torch
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(max(torch.get_num_threads(), 4))
    tok = AutoTokenizer.from_pretrained(EMBED_MODEL, revision=EMBED_REVISION)
    model = AutoModel.from_pretrained(EMBED_MODEL, revision=EMBED_REVISION)
    model.eval()
    out = []
    batch, bs = list(texts), 64
    with torch.no_grad():
        for i in range(0, len(batch), bs):
            enc = tok(batch[i:i + bs], padding=True, truncation=True,
                      max_length=512, return_tensors="pt")
            hidden = model(**enc).last_hidden_state
            mask = enc.attention_mask.unsqueeze(-1)
            pooled = (hidden * mask).sum(1) / mask.sum(1)
            out.append(pooled.numpy())
            if (i // bs) % 20 == 0:
                print(f"    embed {i}/{len(batch)}", flush=True)
    emb = np.vstack(out)
    np.save(cache, emb)
    return emb


# ------------------------------------------------------------------- scoring
def _fit_predict(family: str, texts: pd.Series, X, train_idx, test_idx,
                 y: np.ndarray) -> np.ndarray:
    if family == "tfidf":
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=5,
                              sublinear_tf=True)
        cvec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                               min_df=5, sublinear_tf=True, max_features=200000)
        from scipy.sparse import hstack
        tr_texts = texts.iloc[train_idx]
        te_texts = texts.iloc[test_idx]
        Xtr = hstack([vec.fit_transform(tr_texts), cvec.fit_transform(tr_texts)])
        Xte = hstack([vec.transform(te_texts), cvec.transform(te_texts)])
        m = Ridge(alpha=1.0, solver="sparse_cg")
        m.fit(Xtr, y[train_idx])
        return m.predict(Xte)
    mu = X[train_idx].mean(0)
    sd = X[train_idx].std(0) + 1e-9
    m = Ridge(alpha=10.0)
    m.fit((X[train_idx] - mu) / sd, y[train_idx])
    return m.predict((X[test_idx] - mu) / sd)


def score_corpus(name: str, texts: pd.Series, y: np.ndarray,
                 prompts: np.ndarray, lo: float, hi: float) -> pd.DataFrame:
    """Out-of-fold + leave-one-prompt-out predictions for all families."""
    feats = {
        "handfeat": hand_features(texts),
        "tfidf": None,  # vectorizer must be refit inside each fold
        "embed": embed_features(texts, f"embed_{name}"),
    }
    res = pd.DataFrame(index=texts.index)
    res["human"] = y

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    strata = np.round(y * 2).astype(int)  # halves-safe stratification
    res["fold"] = -1
    for k, (tr, te) in enumerate(skf.split(np.zeros(len(y)), strata)):
        res.iloc[te, res.columns.get_loc("fold")] = k
        for fam in FAMILIES:
            col = f"pred_{fam}_oof"
            if col not in res:
                res[col] = np.nan
            pred = _fit_predict(fam, texts, feats[fam], tr, te, y)
            res.iloc[te, res.columns.get_loc(col)] = np.clip(pred, lo, hi)
        print(f"  {name}: oof fold {k + 1}/{N_FOLDS} done", flush=True)

    for p in np.unique(prompts):
        te = np.where(prompts == p)[0]
        tr = np.where(prompts != p)[0]
        for fam in FAMILIES:
            col = f"pred_{fam}_lopo"
            if col not in res:
                res[col] = np.nan
            pred = _fit_predict(fam, texts, feats[fam], tr, te, y)
            res.iloc[te, res.columns.get_loc(col)] = np.clip(pred, lo, hi)
        print(f"  {name}: lopo prompt '{str(p)[:40]}' done", flush=True)
    return res


def quality(res: pd.DataFrame, corpus: str) -> pd.DataFrame:
    """QWK (on a doubled integer scale to respect half-point scores),
    Pearson r and RMSE per family and protocol."""
    rows = []
    y2 = np.round(res.human * 2).astype(int)
    for fam in FAMILIES:
        for proto in ["oof", "lopo"]:
            pred = res[f"pred_{fam}_{proto}"]
            p2 = np.round(pred * 2).astype(int)
            rows.append({
                "corpus": corpus, "family": fam, "protocol": proto,
                "qwk": round(cohen_kappa_score(y2, p2, weights="quadratic"), 4),
                "pearson_r": round(np.corrcoef(res.human, pred)[0, 1], 4),
                "rmse": round(float(np.sqrt(((res.human - pred) ** 2).mean())), 4),
                "n": len(res),
            })
    return pd.DataFrame(rows)


def main() -> int:
    for f in ["panel_persuade.csv", "panel_ellipse.csv"]:
        if not (DATA / f).exists():
            print(f"Missing data/{f}. Run build_panel.py first.",
                  file=sys.stderr)
            return 1

    qual = []

    print("ELLIPSE ...")
    panel = pd.read_csv(DATA / "panel_ellipse.csv")
    texts = load_texts_ellipse().loc[panel.text_id_kaggle]
    res = score_corpus("ellipse", texts, panel.Overall.to_numpy(),
                       panel.prompt.to_numpy(), 1.0, 5.0)
    res.index.name = "text_id_kaggle"
    res.reset_index().to_csv(DATA / "machine_scores_ellipse.csv", index=False)
    qual.append(quality(res, "ellipse"))

    print("PERSUADE 2.0 ...")
    panel = pd.read_csv(DATA / "panel_persuade.csv")
    texts = load_texts_persuade().loc[panel.panel_id]
    res = score_corpus("persuade", texts,
                       panel.holistic_essay_score.to_numpy().astype(float),
                       panel.prompt_name.to_numpy(), 1.0, 6.0)
    res.index.name = "panel_id"
    res.reset_index().to_csv(DATA / "machine_scores_persuade.csv", index=False)
    qual.append(quality(res, "persuade"))

    q = pd.concat(qual, ignore_index=True)
    q.to_csv(DATA / "scorer_quality.csv", index=False)
    print("\nScorer quality (the audit needs competitive engines):")
    print(q.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
