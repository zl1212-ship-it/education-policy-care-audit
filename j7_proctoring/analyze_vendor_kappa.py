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
      Reads the filled data/vendor_corpus_secondcoder.csv and computes percent
      agreement (per dimension and overall) and Cohen's kappa against the codes
      of record in data/vendor_corpus.csv. Writes data/vendor_kappa_results.csv.

The design is a single primary coder. The second pass can be either (a) an
independent person, giving inter-rater reliability (the stronger claim, as in
the J6 governance audit), or (b) the same author re-coding after a washout
interval and blind to the originals, giving intra-rater reliability. Report
whichever it is, honestly, in Methods. Either way the codebook plus the archived
text in data/vendor_raw/ keep every code checkable.

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


def analyze():
    if not FILLED.exists():
        sys.exit(f"missing {FILLED}\nRun `python3 analyze_vendor_kappa.py template` "
                 "first, fill it in, and save it under that name.")
    second = pd.read_csv(FILLED)
    second["code"] = second["code"].astype(str).str.strip()
    orig = pd.read_csv(CORPUS).set_index("vendor")

    # long table of (vendor, dimension, code_orig, code_2nd)
    recs = []
    for _, r in second.iterrows():
        recs.append({"vendor": r["vendor"], "dimension": r["dimension"],
                     "code_2nd": r["code"],
                     "code_orig": str(orig.loc[r["vendor"], r["dimension"]])})
    d = pd.DataFrame(recs)

    rows = []
    for dim in DIMS:
        sub = d[d["dimension"] == dim]
        agree = (sub["code_orig"] == sub["code_2nd"]).mean()
        k, _ = cohens_kappa(sub["code_orig"], sub["code_2nd"])
        rows.append({"dimension": dim, "n": len(sub),
                     "percent_agreement": round(agree, 3),
                     "cohens_kappa": round(k, 3)})
    overall_k, overall_po = cohens_kappa(d["code_orig"], d["code_2nd"])
    rows.append({"dimension": "OVERALL", "n": len(d),
                 "percent_agreement": round(overall_po, 3),
                 "cohens_kappa": round(overall_k, 3)})

    res = pd.DataFrame(rows)
    res.to_csv(OUT, index=False)
    print(res.to_string(index=False))
    print(f"\nwrote -> {OUT}")
    disagree = d[d["code_orig"] != d["code_2nd"]]
    if len(disagree):
        print("\nDisagreements (resolve against the verbatim passage in "
              "vendor_corpus.csv):")
        print(disagree.to_string(index=False))
    else:
        print("\nNo disagreements: the two passes are identical on all 30 cells.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "template":
        make_template()
    else:
        analyze()
