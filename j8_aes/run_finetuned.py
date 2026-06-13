"""Fourth scoring family: a fine-tuned transformer (the deployable modern engine).

Why this exists
---------------
run_scorers.py covers feature-based and frozen-embedding engines. Operational
scoring is moving to fine-tuned transformers, and the literature this paper
converses with scores essays with fine-tuned and prompted models. To test
whether the conditional penalty and the decision asymmetry are an artifact of
the older engine families, this script adds a fine-tuned engine and scores
every essay out-of-fold with it.

The encoder is the SAME MiniLM used frozen by the `embed` family; here it is
fine-tuned end to end with a regression head. The contrast is therefore clean:
`embed` is the encoder held frozen, `finetuned` is the encoder adapted to the
scoring task. Any difference between them is the effect of fine-tuning, not of
the architecture.

Protocol: out-of-fold only, reusing the EXACT fold assignments written by
run_scorers.py (the `fold` column of machine_scores_*.csv), so the fine-tuned
out-of-fold scores are aligned with the other engines and with the benchmark
(which uses out-of-fold scores). Leave-one-prompt-out transfer is not run for
the fine-tuned engine: refitting a transformer once per prompt is far more
costly than for the linear engines, and the other three families carry the
transfer robustness. This is stated in the manuscript.

Fine-tuning is not bit-deterministic on this hardware (MPS); the seed is set
for best-effort reproducibility. Rerunning will reproduce the substantive
result, not necessarily byte-identical predictions.

Input : data/panel_*.csv, data/machine_scores_*.csv (must exist; run
        run_scorers.py first), data/raw/ (essay text)
Output: adds column pred_finetuned_oof to data/machine_scores_{persuade,
        ellipse}.csv; appends finetuned rows to data/scorer_quality.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import cohen_kappa_score
from transformers import AutoModel, AutoTokenizer

import run_scorers as rs

HERE = Path(__file__).parent
DATA = HERE / "data"

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"  # same pin as embed
SEED = 8
MAX_LEN = 256
BATCH = 32
EPOCHS = 4
LR_ENCODER = 3e-5
LR_HEAD = 1e-3
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


def _seed():
    torch.manual_seed(SEED)
    np.random.seed(SEED)


class Regressor(nn.Module):
    """The fine-tuned twin of the frozen `embed` engine: the same MiniLM
    encoder with the same mean pooling, but trainable, plus a linear head."""

    def __init__(self):
        super().__init__()
        self.enc = AutoModel.from_pretrained(MODEL, revision=REVISION)
        self.head = nn.Linear(self.enc.config.hidden_size, 1)

    def forward(self, input_ids, attention_mask):
        hidden = self.enc(input_ids=input_ids,
                          attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.unsqueeze(-1)
        pooled = (hidden * mask).sum(1) / mask.sum(1)
        return self.head(pooled).squeeze(-1)


def fit_fold(train_texts, train_y, test_texts, lo, hi):
    """Fine-tune a fresh MiniLM regressor on the train fold, predict the test
    fold. The target is standardized with the train fold's mean and sd so the
    head learns the full score range; predictions are mapped back and clipped.
    Returns predictions for test_texts in order."""
    tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = Regressor().to(DEVICE)
    opt = torch.optim.AdamW([
        {"params": model.enc.parameters(), "lr": LR_ENCODER},
        {"params": model.head.parameters(), "lr": LR_HEAD},
    ])
    mu, sd = float(np.mean(train_y)), float(np.std(train_y) + 1e-6)
    yz = torch.tensor((train_y - mu) / sd, dtype=torch.float32, device=DEVICE)

    n = len(train_texts)
    rng = np.random.default_rng(SEED)
    model.train()
    for epoch in range(EPOCHS):
        order = rng.permutation(n)
        for i in range(0, n, BATCH):
            idx = order[i:i + BATCH]
            enc = tok([train_texts[j] for j in idx], padding=True,
                      truncation=True, max_length=MAX_LEN,
                      return_tensors="pt").to(DEVICE)
            pred = model(enc["input_ids"], enc["attention_mask"])
            loss = ((pred - yz[idx]) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        print(f"    epoch {epoch + 1}/{EPOCHS} done", flush=True)

    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(test_texts), BATCH):
            enc = tok(test_texts[i:i + BATCH], padding=True, truncation=True,
                      max_length=MAX_LEN, return_tensors="pt").to(DEVICE)
            z = model(enc["input_ids"], enc["attention_mask"]).cpu().numpy()
            out.append(z * sd + mu)
    return np.clip(np.concatenate(out), lo, hi)


def score_corpus(name, key, score_col, texts, lo, hi):
    path = DATA / f"machine_scores_{name}.csv"
    ms = pd.read_csv(path)
    if "fold" not in ms:
        raise ValueError(f"{path} has no fold column; run run_scorers.py first")
    texts = texts.loc[ms[key]]  # align to row order of machine_scores
    y = ms["human"].to_numpy(float)
    pred = np.full(len(ms), np.nan)

    for k in sorted(ms["fold"].unique()):
        tr = (ms["fold"] != k).to_numpy()
        te = (ms["fold"] == k).to_numpy()
        _seed()
        pred[te] = fit_fold([texts.iloc[i] for i in np.where(tr)[0]],
                            y[tr],
                            [texts.iloc[i] for i in np.where(te)[0]],
                            lo, hi)
        print(f"  {name}: oof fold {int(k) + 1} done", flush=True)

    ms["pred_finetuned_oof"] = pred
    ms.to_csv(path, index=False)

    y2 = np.round(y * 2).astype(int)
    p2 = np.round(pred * 2).astype(int)
    qrow = {"corpus": name, "family": "finetuned", "protocol": "oof",
            "qwk": round(cohen_kappa_score(y2, p2, weights="quadratic"), 4),
            "pearson_r": round(float(np.corrcoef(y, pred)[0, 1]), 4),
            "rmse": round(float(np.sqrt(((y - pred) ** 2).mean())), 4),
            "n": len(ms)}
    print(f"  {name} finetuned: QWK {qrow['qwk']} r {qrow['pearson_r']} "
          f"RMSE {qrow['rmse']}", flush=True)
    return qrow


def main() -> int:
    for f in ["machine_scores_persuade.csv", "machine_scores_ellipse.csv"]:
        if not (DATA / f).exists():
            print(f"Missing data/{f}. Run run_scorers.py first.",
                  file=sys.stderr)
            return 1
    print(f"Device: {DEVICE}")

    qrows = []
    print("ELLIPSE fine-tuning ...")
    qrows.append(score_corpus(
        "ellipse", "text_id_kaggle", "Overall",
        rs.load_texts_ellipse(), 1.0, 5.0))
    print("PERSUADE fine-tuning ...")
    qrows.append(score_corpus(
        "persuade", "panel_id", "holistic_essay_score",
        rs.load_texts_persuade(), 1.0, 6.0))

    qpath = DATA / "scorer_quality.csv"
    q = pd.read_csv(qpath)
    q = q[q.family != "finetuned"]  # idempotent re-run
    q = pd.concat([q, pd.DataFrame(qrows)], ignore_index=True)
    q.to_csv(qpath, index=False)
    print("Updated scorer_quality.csv with finetuned rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
