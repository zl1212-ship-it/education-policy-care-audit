"""Descriptive first stage: the lowest-performing label is formula-made.

Builds the summative composite from the indicators (CODEBOOK_indicators.md),
reconstructs the ESSA bottom-five-percent-of-Title-I identification rule, then sweeps
the indicator weights over the envelope of real state designs and measures how the
set of identified schools moves across the school poverty distribution. The weight
choice, not just the school, decides who carries the label; the sweep quantifies how
much of the label is a weighting artifact and where on the poverty distribution the
relabeling lands.

Outputs:
  data/label_instability.csv - one row per Title I school: baseline composite, within
      state percentile, baseline identification, identify_freq (share of weight draws
      identifying the school), flip flag, poverty intensity and decile.
  data/weight_draws.csv       - one row per weight draw: the four weights and the
      poverty composition of the identified set under them.

Run:  python3 weight_space.py [--draws 2000] [--seed 0]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
FRAME = HERE / "data" / "school_frame.csv"
IND = HERE / "data" / "indicators.csv"
OUT_INST = HERE / "data" / "label_instability.csv"
OUT_DRAWS = HERE / "data" / "weight_draws.csv"

IND_KEYS = ["achievement", "grad", "quality", "growth_proxy"]
W_BASELINE = np.array([0.40, 0.20, 0.10, 0.30])          # CODEBOOK_indicators.md
ENVELOPE = np.array([[0.20, 0.60],   # achievement
                     [0.00, 0.35],   # grad
                     [0.05, 0.25],   # quality
                     [0.00, 0.50]])  # growth_proxy  (real state-design ranges)
BOTTOM = 0.05      # lowest 5% of Title I schools (the ESSA rule)
GRAD_FLOOR = 67.0  # statutory graduation-rate floor for high schools


def build_panel():
    frame = pd.read_csv(FRAME, dtype={"ncessch": str})
    ind = pd.read_csv(IND, dtype={"ncessch": str})
    df = frame.merge(ind, on="ncessch", how="inner", suffixes=("", "_ind"))

    # growth proxy: within-state percentile of the year-over-year achievement change
    df["growth_raw"] = df["achievement"] - df["achievement_prior"]
    df["growth_proxy"] = (
        df.groupby("state")["growth_raw"].rank(pct=True) * 100)

    # Title I universe with a usable composite (at least achievement present)
    df = df[(df["title_i_eligible"] == 1) & df["achievement"].notna()].copy()
    return df.reset_index(drop=True)


def composite(values, mask, w):
    """Weighted mean over present indicators, weights renormalized to the present set."""
    denom = mask @ w
    numer = (values * mask) @ w
    out = np.full(len(values), np.nan)
    ok = denom > 0
    out[ok] = numer[ok] / denom[ok]
    return out


def identify(comp, state_codes, is_high, grad):
    """Bottom-5% of Title I within state, plus the high-school graduation floor."""
    s = pd.Series(comp)
    pct = s.groupby(state_codes).rank(pct=True, method="first")
    flagged = (pct <= BOTTOM).to_numpy()
    floor = (is_high == 1) & (grad < GRAD_FLOOR)
    return flagged | floor


def draw_weights(rng):
    w = rng.uniform(ENVELOPE[:, 0], ENVELOPE[:, 1])
    return w / w.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    df = build_panel()
    values = df[IND_KEYS].to_numpy(dtype=float)
    mask = (~np.isnan(values)).astype(float)
    values = np.nan_to_num(values, nan=0.0)
    state = df["state"].to_numpy()
    is_high = df["is_high"].to_numpy()
    grad = df["grad"].fillna(np.inf).to_numpy()  # missing grad never trips the floor

    # baseline
    df["composite"] = composite(values, mask, W_BASELINE)
    df["pct_within_state"] = (
        df.groupby("state")["composite"].rank(pct=True, method="first"))
    df["identified_baseline"] = identify(
        df["composite"].to_numpy(), state, is_high, grad).astype(int)

    # poverty distribution (over the Title I sample)
    df["poverty_decile"] = (
        pd.qcut(df["econ_disadv_share"].rank(method="first"), 10, labels=False) + 1)
    top_q = df["econ_disadv_share"] >= df["econ_disadv_share"].quantile(0.75)

    # weight sweep
    rng = np.random.default_rng(args.seed)
    hits = np.zeros(len(df), dtype=int)
    draws = []
    for d in range(args.draws):
        w = draw_weights(rng)
        comp = composite(values, mask, w)
        ident = identify(comp, state, is_high, grad)
        hits += ident
        ident_pov = df.loc[ident, "econ_disadv_share"]
        draws.append({
            "draw": d,
            "w_achievement": w[0], "w_grad": w[1],
            "w_quality": w[2], "w_growth": w[3],
            "n_identified": int(ident.sum()),
            "mean_poverty_identified": float(ident_pov.mean()),
            "share_identified_top_pov_quartile": float(
                (top_q & ident).sum() / max(ident.sum(), 1)),
        })

    df["identify_freq"] = hits / args.draws
    df["flip"] = ((df["identify_freq"] > 0) & (df["identify_freq"] < 1)).astype(int)

    # mechanical baseline: how much of the flipping is just cutoff fuzz that any 5% rule
    # produces? Re-run with only SMALL perturbations of the baseline weights (each weight
    # wiggled by up to +/- 0.05, renormalized). Flipping under tiny perturbations is the
    # mechanical part; the gap up to the full-envelope flip rate is what the breadth of
    # real state designs adds.
    narrow_hits = np.zeros(len(df), dtype=int)
    for _ in range(args.draws):
        wn = np.clip(W_BASELINE + rng.uniform(-0.05, 0.05, 4), 0, None)
        wn = wn / wn.sum()
        narrow_hits += identify(composite(values, mask, wn), state, is_high, grad)
    narrow_freq = narrow_hits / args.draws
    base = df["identified_baseline"].to_numpy() == 1
    full_flip = float((df["flip"].to_numpy()[base]).mean())
    narrow_flip = float((((narrow_freq > 0) & (narrow_freq < 1))[base]).mean())

    cols = ["ncessch", "state", "is_high", "enrollment", "econ_disadv_share",
            "poverty_decile", "achievement", "grad", "quality", "growth_proxy",
            "composite", "pct_within_state", "identified_baseline",
            "identify_freq", "flip"]
    df[cols].to_csv(OUT_INST, index=False)
    pd.DataFrame(draws).to_csv(OUT_DRAWS, index=False)

    n_id = int(df["identified_baseline"].sum())
    n_flip = int(df["flip"].sum())
    print(f"label_instability.csv: {len(df):,} Title I schools, "
          f"{n_id:,} identified at baseline, {n_flip:,} ever flip across "
          f"{args.draws} weight draws ({n_flip / max(n_id,1):.1%} of baseline count)")
    print(f"flip among baseline-identified: full envelope {full_flip:.1%} vs "
          f"narrow perturbation {narrow_flip:.1%} (the gap is the breadth of real designs)")
    print(f"weight_draws.csv: {args.draws} draws -> {OUT_DRAWS}")


if __name__ == "__main__":
    main()
