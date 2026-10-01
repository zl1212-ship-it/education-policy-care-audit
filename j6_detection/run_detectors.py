"""Current-detector extension: does the 2023 language penalty persist in newer open detectors?

Re-scores the same 249 human essays (TOEFL non-native, US native) with current
open-source AI-text detectors from Hugging Face and recomputes the false-accusation
rate by native vs non-native English status. If the gap survives in models released
after the 2023 audit, the bias is not an artifact of one detector generation.

Detectors are version-pinned by revision where possible (see REVISIONS). Essays are
truncated to the model's 512-token limit, the standard input for these classifiers.
Requires torch + transformers (heavier than the rest of the pipeline); install
separately. Outputs data/detector_scores_current.csv and appends summary rows to
data/results_summary.csv.

Run fetch_anchor_data.py first.
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
HUMAN = HERE / "data" / "anchor" / "Data_and_Results" / "Human_Data"
OUT_SCORES = HERE / "data" / "detector_scores_current.csv"
OUT_SUMMARY = HERE / "data" / "results_summary.csv"
CORPORA = {"TOEFL_real_91": "non-native",
           "HewlettStudentEssay_real_88": "native",
           "CollegeEssay_real_70": "native"}
# Candidate current open detectors; unavailable ones are skipped and reported.
MODELS = [
    "openai-community/roberta-base-openai-detector",
    "openai-community/roberta-large-openai-detector",
    "fakespot-ai/roberta-base-ai-text-detection-v1",
    "Hello-SimpleAI/chatgpt-detector-roberta",
]
TAU = 0.50


def load_essays():
    rows = []
    for corpus, l1 in CORPORA.items():
        for i, d in enumerate(json.load(open(HUMAN / corpus / "data.json"))):
            rows.append({"essay_id": f"{corpus}/{i:03d}", "l1_status": l1, "text": d["document"]})
    return rows


def ai_label_index(model):
    """Index of the 'AI/fake/machine-generated' class from the model config."""
    id2 = {int(k): v.lower() for k, v in model.config.id2label.items()}
    for idx, name in id2.items():
        if any(t in name for t in ("fake", "chatgpt", "ai", "machine", "gpt", "label_1")):
            return idx
    return max(id2)  # fall back to the higher index


def main() -> int:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        print("Needs torch + transformers. Install, then re-run.", file=sys.stderr)
        return 1
    if not HUMAN.exists():
        print("Run fetch_anchor_data.py first.", file=sys.stderr)
        return 1

    essays = load_essays()
    print(f"Scoring {len(essays)} essays with up to {len(MODELS)} current detectors.")
    scored, ran = {e["essay_id"]: {"l1_status": e["l1_status"]} for e in essays}, []

    for name in MODELS:
        try:
            tok = AutoTokenizer.from_pretrained(name)
            mdl = AutoModelForSequenceClassification.from_pretrained(name)
            mdl.eval()
            ai_idx = ai_label_index(mdl)
        except Exception as e:
            print(f"  [skip] {name}: {type(e).__name__} {e}")
            continue
        short = name.split("/")[-1]
        with torch.no_grad():
            for e in essays:
                enc = tok(e["text"], truncation=True, max_length=512, return_tensors="pt")
                p = torch.softmax(mdl(**enc).logits, dim=-1)[0, ai_idx].item()
                scored[e["essay_id"]][short] = round(p, 6)
        ran.append(short)
        print(f"  [ok] {short}")

    if not ran:
        print("No detectors ran (downloads failed?).", file=sys.stderr)
        return 1

    with open(OUT_SCORES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["essay_id", "l1_status"] + ran)
        w.writeheader()
        for eid, row in scored.items():
            w.writerow({"essay_id": eid, **row})

    # False-accusation rate by L1 status, per detector and pooled.
    def fpr(detector, group):
        vals = [r[detector] for r in scored.values()
                if r["l1_status"] == group and detector in r]
        return sum(v > TAU for v in vals) / len(vals)

    print(f"\nFalse-accusation rate (tau={TAU}), current detectors:")
    print(f"  {'detector':<40}{'non-native':>12}{'native':>9}{'fold':>7}")
    summ = []
    for d in ran:
        nn, na = fpr(d, "non-native"), fpr(d, "native")
        fold = float("inf") if na == 0 else nn / na
        print(f"  {d:<40}{nn:>12.1%}{na:>9.1%}{fold:>7.1f}")
        summ += [{"analysis": "current_detector_fpr", "detector": d, "threshold": TAU,
                  "group": g, "value": round(v, 4), "count": None, "n_group": None}
                 for g, v in (("non-native", nn), ("native", na))]
    # A detector that flags most human native essays (native FPR > 0.5) is degenerate: it cannot
    # discriminate, so it carries no usable bias signal and is excluded from the pooled estimate.
    discriminating = [d for d in ran if fpr(d, "native") <= 0.5]
    degenerate = [d for d in ran if d not in discriminating]
    if degenerate:
        print(f"  [excluded as non-discriminating, native FPR > 50%: {', '.join(degenerate)}]")
    pooled_nn = sum(fpr(d, "non-native") for d in discriminating) / len(discriminating)
    pooled_na = sum(fpr(d, "native") for d in discriminating) / len(discriminating)
    fold = float("inf") if pooled_na == 0 else pooled_nn / pooled_na
    print(f"  {'POOLED (mean of ' + str(len(discriminating)) + ' discriminating)':<40}"
          f"{pooled_nn:>12.1%}{pooled_na:>9.1%}{fold:>7.1f}")
    summ += [{"analysis": "current_detector_pooled", "detector": f"mean_of_{len(discriminating)}_discriminating",
              "threshold": TAU, "group": g, "value": round(v, 4), "count": None, "n_group": None}
             for g, v in (("non-native", pooled_nn), ("native", pooled_na))]

    import pandas as pd
    res = pd.read_csv(OUT_SUMMARY)
    res = res[~res.analysis.isin(["current_detector_fpr", "current_detector_pooled"])]
    pd.concat([res, pd.DataFrame(summ)], ignore_index=True).to_csv(OUT_SUMMARY, index=False)
    print(f"\nWrote {OUT_SCORES} and appended summary rows to {OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
