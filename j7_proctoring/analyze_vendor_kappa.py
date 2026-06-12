"""Intercoder reliability for the J7 vendor consequence codes (Cohen's kappa).

Two modes.

  python3 analyze_vendor_kappa.py template
      Writes data/vendor_corpus_secondcoder_template.csv: one row per
      (vendor, dimension), the codebook options for that dimension, the source
      document slugs, and a blank `code` column. Hand this file and
      CODEBOOK_vendor.md (plus the stored text in data/vendor_raw/) to a second
      coder, who fills `code` for all 30 cells independently, blind to the codes
      of record.

  python3 analyze_vendor_kappa.py
      Reads every filled pass saved as data/vendor_corpus_<name>.csv (for example
      _coder_a, _coder_b, _codex), plus the AI-assisted codes of record, and computes
      pairwise percent agreement and Cohen's kappa. Each pass is labeled human or
      LLM from its filename; the human-human pair is the inter-rater statistic to
      report, and any pair involving an LLM is a cross-check only, never pooled
      into the human number. Writes data/vendor_kappa_results.csv.

Honest reporting: the human-human pair (e.g. the author and an independent second
coder) is the inter-rater reliability. An LLM pass may be run as an extra
cross-check, but it must be disclosed as an LLM and kept out of the human kappa.
The codebook plus the archived text in data/vendor_raw/ keep every code checkable.

Cohen's kappa is computed directly (no sklearn): kappa = (po - pe) / (1 - pe),
where po is observed agreement and pe is chance agreement from the two coders'
marginal label distributions.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
CORPUS = HERE / "data" / "vendor_corpus.csv"
TEMPLATE = HERE / "data" / "vendor_corpus_secondcoder_template.csv"
FILLED = HERE / "data" / "vendor_corpus_secondcoder.csv"
OUT = HERE / "data" / "vendor_kappa_results.csv"

DIMS = ["noface_flag", "id_gate", "consequence_path", "human_review",
        "lighting_burden", "bias_acknowledgment"]

# verbatim-evidence column for each dimension in vendor_corpus.csv
SUPPORT = {"noface_flag": "noface_support", "id_gate": "id_support",
           "consequence_path": "consequence_support",
           "human_review": "human_support",
           "lighting_burden": "lighting_support",
           "bias_acknowledgment": "bias_support"}

# codebook option sets (see CODEBOOK_vendor.md)
OPTIONS = {
    "noface_flag": ["automatic_flag", "proctor_alert", "not_documented"],
    "id_gate": ["blocks_entry", "flag_proceed", "human_fallback", "not_documented"],
    "consequence_path": ["suspicion_score", "vendor_review", "instructor_review",
                         "not_documented"],
    "human_review": ["yes_documented", "not_documented"],
    "lighting_burden": ["yes", "no"],
    "bias_acknowledgment": ["acknowledged", "deflected", "silent"],
}


def make_template():
    corpus = pd.read_csv(CORPUS)
    rows = []
    for _, r in corpus.iterrows():
        for dim in DIMS:
            rows.append({
                "vendor": r["vendor"],
                "dimension": dim,
                "options": " | ".join(OPTIONS[dim]),
                # the archived evidence passage for this cell, so the coder can
                # judge from the text without reading all 14 documents. For a
                # fully independent inter-rater pass, blank this column and have
                # the coder read data/vendor_raw/<slug>.txt instead.
                "evidence_passage": str(r.get(SUPPORT[dim], "")).strip(),
                "source_docs": r["docs"],
                "code": "",  # coder fills this, one value from `options`
            })
    out = pd.DataFrame(rows)
    out.to_csv(TEMPLATE, index=False)
    print(f"wrote {len(out)} blank cells -> {TEMPLATE}")
    print("Fill the `code` column for every row (pick one value from `options`),")
    print("reading data/vendor_raw/<slug>.txt for each vendor in `source_docs`.")
    print("Save as data/vendor_corpus_secondcoder.csv, then run "
          "`python3 analyze_vendor_kappa.py`.")


def cohens_kappa(a, b):
    """Cohen's kappa for two equal-length label sequences."""
    a, b = list(a), list(b)
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    labels = set(a) | set(b)
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po


def coder_kind(name):
    """Label a pass as human or LLM from its filename, so the LLM cross-check is
    never silently pooled with the human inter-rater statistic."""
    low = name.lower()
    if any(k in low for k in ("codex", "gpt", "llm", "claude", "ai")):
        return "LLM"
    return "human"


def load_pass(path):
    """Read a filled template into a (vendor, dimension) -> code map."""
    df = pd.read_csv(path)
    df["code"] = df["code"].astype(str).str.strip()
    return {(r["vendor"], r["dimension"]): r["code"] for _, r in df.iterrows()}


def pair_stats(a, b):
    """Per-dimension and overall percent agreement + Cohen's kappa for two maps
    over the cells they share."""
    cells = sorted(set(a) & set(b))
    rows = []
    for dim in DIMS + ["OVERALL"]:
        keys = cells if dim == "OVERALL" else [c for c in cells if c[1] == dim]
        if not keys:
            continue
        ca = [a[k] for k in keys]
        cb = [b[k] for k in keys]
        k, po = cohens_kappa(ca, cb)
        rows.append({"dimension": dim, "n": len(keys),
                     "percent_agreement": round(po, 3),
                     "cohens_kappa": round(k, 3)})
    return pd.DataFrame(rows)


def analyze():
    import glob
    # collect every filled pass: data/vendor_corpus_<name>.csv (not the template,
    # not the AI codes of record itself)
    passes = {}
    for f in sorted(glob.glob(str(HERE / "data" / "vendor_corpus_*.csv"))):
        name = Path(f).stem.replace("vendor_corpus_", "")
        if name.endswith("_template"):
            continue
        passes[name] = load_pass(f)
    # the original AI-assisted codes of record, in long form
    corpus = pd.read_csv(CORPUS).set_index("vendor")
    passes["ai_record"] = {(v, dim): str(corpus.loc[v, dim])
                           for v in corpus.index for dim in DIMS}

    if len(passes) < 2:
        sys.exit("Need at least one filled pass besides the AI record. Save coder "
                 "files as data/vendor_corpus_<name>.csv (e.g. _coder_a, _coder_b, "
                 "_codex), then rerun.")

    names = list(passes)
    print("passes found:", {n: coder_kind(n) for n in names}, "\n")
    all_rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            kinds = f"{coder_kind(a)}-{coder_kind(b)}"
            stats = pair_stats(passes[a], passes[b])
            tag = " <== HUMAN INTER-RATER" if kinds == "human-human" else ""
            print(f"=== {a} vs {b}  ({kinds}){tag} ===")
            print(stats.to_string(index=False), "\n")
            for _, r in stats.iterrows():
                all_rows.append({"pass_a": a, "pass_b": b, "pair_kind": kinds,
                                 **r.to_dict()})
    pd.DataFrame(all_rows).to_csv(OUT, index=False)
    print(f"wrote -> {OUT}")
    print("\nFor the manuscript: report the human-human pair as the inter-rater "
          "kappa. Any pair involving an LLM is a cross-check only and must be "
          "described as such, never pooled into the human statistic.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "template":
        make_template()
    else:
        analyze()
