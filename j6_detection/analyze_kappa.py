"""Intercoder reliability for the J6 governance codes (Cohen's kappa).

Two modes.

  python3 analyze_kappa.py template
      Draws a reproducible random 20% sample (10 of 50) of the coded institutions
      and writes data/policy_corpus_secondcoder_template.csv: institution, state,
      url, the five code columns left blank, and a coder column. Hand this file and
      CODEBOOK_policy.md (plus the stored text in data/policy_raw/, or the live
      URLs) to a second coder who codes the five dimensions independently, blind to
      the first-pass codes.

  python3 analyze_kappa.py
      Reads the filled file data/policy_corpus_secondcoder.csv and computes Cohen's
      kappa and percent agreement per dimension against the codes of record in
      data/policy_corpus.csv, over the institutions both files cover. Writes
      data/kappa_results.csv.

Kappa is computed directly (no sklearn dependency): kappa = (po - pe)/(1 - pe),
where po is observed agreement and pe is chance agreement from the two coders'
marginal distributions. Report the per-dimension kappa in the manuscript's methods
and resolve disagreements against the verbatim passage.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
CORPUS = HERE / "data" / "policy_corpus.csv"
TEMPLATE = HERE / "data" / "policy_corpus_secondcoder_template.csv"
SECOND = HERE / "data" / "policy_corpus_secondcoder.csv"
OUT = HERE / "data" / "kappa_results.csv"
DIMENSIONS = ["detector_admissibility", "burden_of_proof", "appeal_pathway",
              "l2_protection", "decision_locus"]
SEED, FRACTION = 2026, 0.20


def cohens_kappa(a, b):
    """Cohen's kappa for two equal-length sequences of categorical labels."""
    pairs = [(x, y) for x, y in zip(a, b) if x != "" and y != ""]
    n = len(pairs)
    if n == 0:
        return float("nan"), 0, 0.0
    po = sum(x == y for x, y in pairs) / n
    cats = set(x for x, _ in pairs) | set(y for _, y in pairs)
    pe = sum((sum(x == c for x, _ in pairs) / n) * (sum(y == c for _, y in pairs) / n)
             for c in cats)
    kappa = 1.0 if pe == 1 else (po - pe) / (1 - pe)
    return round(kappa, 3), n, round(po, 3)


def make_template() -> int:
    df = pd.read_csv(CORPUS, dtype=str).fillna("")
    coded = df[df.detector_admissibility != ""]
    k = max(1, round(len(coded) * FRACTION))
    sample = coded.sample(n=k, random_state=SEED).sort_values("institution")
    out = sample[["institution", "state", "url"]].copy()
    for d in DIMENSIONS:
        out[d] = ""
    out["coder"] = ""
    out.to_csv(TEMPLATE, index=False)
    print(f"Wrote {TEMPLATE}  ({k} institutions, seed={SEED})")
    print("Give it + CODEBOOK_policy.md to a second coder; they fill the five code "
          "columns blind, save as data/policy_corpus_secondcoder.csv, then re-run.")
    return 0


def compute() -> int:
    if not SECOND.exists():
        print(f"Missing {SECOND}. Run 'analyze_kappa.py template', have a second coder "
              f"fill it, and save it as {SECOND.name}.", file=sys.stderr)
        return 1
    rec = pd.read_csv(CORPUS, dtype=str).fillna("").set_index("institution")
    sec = pd.read_csv(SECOND, dtype=str).fillna("").set_index("institution")
    both = [i for i in sec.index if i in rec.index]
    rows = []
    print(f"Intercoder reliability over {len(both)} institutions:\n")
    print(f"  {'dimension':<24}{'kappa':>8}{'%agree':>9}{'n':>5}")
    for d in DIMENSIONS:
        kappa, n, po = cohens_kappa([rec.loc[i, d] for i in both],
                                    [sec.loc[i, d] for i in both])
        rows.append({"dimension": d, "cohens_kappa": kappa, "pct_agreement": po, "n": n})
        print(f"  {d:<24}{kappa:>8}{po:>9.0%}{n:>5}")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(make_template() if len(sys.argv) > 1 and sys.argv[1] == "template" else compute())
