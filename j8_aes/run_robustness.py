"""Robustness of the fine-tuned engine's English-learner penalty (PERSUADE).

Why this exists
---------------
The headline includes a fine-tuned transformer. A skeptical reading is that its
penalty is a single-run artifact: one seed, a compact MiniLM at modest compute,
the lowest agreement of the four engines, and a global calibration offset (its
non-English-learner mean gap is +0.168 against near zero for the others). This
script answers that two ways, both on PERSUADE (the corpus that carries the
English-learner contrast):

  multi-seed   the same MiniLM fine-tuned engine, five seeds, so the conditional
               penalty and the demotion differential are reported as a mean and
               spread rather than a single number. Seed 8 reuses the canonical
               run already in machine_scores_persuade.csv; four more are trained.
  larger model a DistilBERT encoder (66M vs MiniLM's 22M), fine-tuned the same
               way, so the penalty is not specific to one small encoder.

For each run the script recomputes, out-of-fold on the stored folds:
  qwk            quadratic weighted kappa (engine quality),
  nonEL_offset   the non-English-learner mean machine-minus-human gap (the
                 calibration offset the review flagged),
  cond_diff      the conditional English-learner differential (the penalty),
                 which is a relative quantity and so is invariant to the offset,
  demotion_diff  the English-learner minus other demotion differential at a
                 pass mark of 4.

Output: data/robustness_finetuned.csv (one row per model-seed). Appended as runs
finish, so a crash keeps completed rows. Fine-tuning is not bit-deterministic on
MPS; seeds are set for best effort.

Input : data/panel_persuade.csv, data/machine_scores_persuade.csv (run
        run_scorers.py and run_finetuned.py first), data/raw/
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
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

MODELS = {
    "minilm": ("sentence-transformers/all-MiniLM-L6-v2",
               "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"),
    "distilbert": ("distilbert-base-uncased", "main"),
}
# (model, seed); seed 8 minilm is the canonical run already on disk (reused).
RUNS = [("minilm", 8), ("minilm", 1), ("minilm", 2), ("minilm", 3),
        ("minilm", 4), ("distilbert", 8)]
MAX_LEN = 256
BATCH = 32
EPOCHS = 4
LR_ENCODER = 3e-5
LR_HEAD = 1e-3
CUT = 4
OUT = DATA / "robustness_finetuned.csv"


class Regressor(nn.Module):
    def __init__(self, name, revision):
        super().__init__()
        self.enc = AutoModel.from_pretrained(name, revision=revision)
        self.head = nn.Linear(self.enc.config.hidden_size, 1)

    def forward(self, input_ids, attention_mask):
        hidden = self.enc(input_ids=input_ids,
                          attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.unsqueeze(-1)
        pooled = (hidden * mask).sum(1) / mask.sum(1)
        return self.head(pooled).squeeze(-1)


def fit_fold(name, revision, seed, train_texts, train_y, test_texts, lo, hi):
    torch.manual_seed(seed)
    np.random.seed(seed)
    tok = AutoTokenizer.from_pretrained(name, revision=revision)
    model = Regressor(name, revision).to(DEVICE)
    opt = torch.optim.AdamW([
        {"params": model.enc.parameters(), "lr": LR_ENCODER},
        {"params": model.head.parameters(), "lr": LR_HEAD},
    ])
    mu, sd = float(np.mean(train_y)), float(np.std(train_y) + 1e-6)
    yz = torch.tensor((train_y - mu) / sd, dtype=torch.float32, device=DEVICE)
    rng = np.random.default_rng(seed)
    n = len(train_texts)
    model.train()
    for _ in range(EPOCHS):
        order = rng.permutation(n)
        for i in range(0, n, BATCH):
            idx = order[i:i + BATCH]
            enc = tok([train_texts[j] for j in idx], padding=True,
                      truncation=True, max_length=MAX_LEN,
                      return_tensors="pt").to(DEVICE)
            loss = ((model(enc["input_ids"], enc["attention_mask"])
                     - yz[idx]) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(test_texts), BATCH):
            enc = tok(test_texts[i:i + BATCH], padding=True, truncation=True,
                      max_length=MAX_LEN, return_tensors="pt").to(DEVICE)
            z = model(enc["input_ids"], enc["attention_mask"]).cpu().numpy()
            out.append(z * sd + mu)
    return np.clip(np.concatenate(out), lo, hi)


def oof_predict(name, revision, seed, texts, ms):
    pred = np.full(len(ms), np.nan)
    y = ms["human"].to_numpy(float)
    for k in sorted(ms["fold"].unique()):
        tr = (ms["fold"] != k).to_numpy()
        te = (ms["fold"] == k).to_numpy()
        pred[te] = fit_fold(name, revision, seed,
                            [texts.iloc[i] for i in np.where(tr)[0]], y[tr],
                            [texts.iloc[i] for i in np.where(te)[0]], 1.0, 6.0)
        print(f"    fold {int(k) + 1} done", flush=True)
    return pred


def metrics(df, pred):
    """Conditional EL differential, demotion differential, non-EL offset, QWK."""
    d = df.assign(pred=pred).dropna(subset=["ell_status", "pred"])
    y = d.holistic_essay_score.to_numpy(float)
    p = d.pred.to_numpy(float)
    ell = (d.ell_status == "Yes").to_numpy()
    non = (d.ell_status == "No").to_numpy()
    gap = p - y
    st = np.round(y * 2).astype(int)

    # conditional differential: within human-score strata, focal-weighted
    total, weight = 0.0, 0
    for s in np.unique(st[ell]):
        r = non & (st == s)
        f = ell & (st == s)
        if r.sum() and f.sum():
            total += f.sum() * (gap[f].mean() - gap[r].mean())
            weight += f.sum()
    cond = total / weight if weight else np.nan

    def demote(mask):
        hp = y[mask] >= CUT
        mp = np.round(p[mask]) >= CUT
        return (hp & ~mp).sum() / max(hp.sum(), 1)
    demo_diff = demote(ell) - demote(non)

    y2 = np.round(y * 2).astype(int)
    p2 = np.round(p * 2).astype(int)
    return {
        "qwk": round(cohen_kappa_score(y2, p2, weights="quadratic"), 4),
        "nonEL_offset": round(float(gap[non].mean()), 4),
        "cond_diff": round(float(cond), 4),
        "demotion_diff": round(float(demo_diff), 4),
        "n": int(mask_n(ell, non)),
    }


def mask_n(ell, non):
    return ell.sum() + non.sum()


def main() -> int:
    panel = pd.read_csv(DATA / "panel_persuade.csv")
    ms = pd.read_csv(DATA / "machine_scores_persuade.csv")
    df = panel.merge(ms[["panel_id", "fold", "human"]], on="panel_id")
    texts = rs.load_texts_persuade().loc[ms["panel_id"]]

    rows = []
    if OUT.exists():
        rows = pd.read_csv(OUT).to_dict("records")
    done = {(r["model"], r["seed"]) for r in rows}

    for name_key, seed in RUNS:
        if (name_key, seed) in done:
            print(f"skip {name_key} seed {seed} (already in {OUT.name})")
            continue
        print(f"=== {name_key} seed {seed} ===", flush=True)
        if name_key == "minilm" and seed == 8 and "pred_finetuned_oof" in ms:
            pred = ms["pred_finetuned_oof"].to_numpy(float)  # canonical reuse
            print("  reusing canonical seed-8 predictions")
        else:
            name, rev = MODELS[name_key]
            pred = oof_predict(name, rev, seed, texts, ms)
        m = metrics(df, pred)
        m.update(model=name_key, seed=seed)
        rows.append(m)
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(f"  {name_key} s{seed}: QWK {m['qwk']} offset {m['nonEL_offset']}"
              f" cond {m['cond_diff']} demote_diff {m['demotion_diff']}",
              flush=True)

    r = pd.DataFrame(rows)
    mm = r[r.model == "minilm"]
    print("\n=== MiniLM multi-seed (n={}) ===".format(len(mm)))
    for col in ["qwk", "nonEL_offset", "cond_diff", "demotion_diff"]:
        print(f"  {col:<14} mean {mm[col].mean():+.4f}  SD {mm[col].std():.4f}"
              f"  range [{mm[col].min():+.4f}, {mm[col].max():+.4f}]")
    db = r[r.model == "distilbert"]
    if len(db):
        print("\n=== DistilBERT (larger encoder) ===")
        print(db[["seed", "qwk", "nonEL_offset", "cond_diff",
                  "demotion_diff"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
