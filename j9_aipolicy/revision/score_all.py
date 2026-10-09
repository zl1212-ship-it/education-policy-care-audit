"""Re-score every archived snapshot (US + cross-national) on the provision lexicon under the
raw extractor and the boilerplate-stripped extractor, at proximity windows 400 (main), 200 and
800. One row per index row with bytes > 0 whose file exists. Writes scored_raw_vs_clean.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import csv, sys, time
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B
OUT = AN / "scored_raw_vs_clean.csv"
PROV = list(B.PROVISIONS.keys())
import re
STRICT_AI = re.compile(r"artificial intelligence|generative a\.?i\.?|gen(?:erative)?\s?ai|chat\s?gpt|"
                       r"large language model|\bllms?\b|\bgpt\b", re.I)  # no bare AI / A.I.
_AI_FULL = B.AI_TERMS
def score_strict(text, window=400):
    B.AI_TERMS = STRICT_AI
    try:
        return B.score_text(text, window)
    finally:
        B.AI_TERMS = _AI_FULL

def load(base, system_of):
    d = pd.read_csv(base / "data" / "snapshot_index.csv", dtype=str)
    d["bytes"] = pd.to_numeric(d["bytes"], errors="coerce").fillna(0)
    d = d[d["bytes"] > 0].copy()
    d["system"] = d.apply(system_of, axis=1)
    d["abspath"] = d["local_path"].apply(lambda p: str(base / p))
    d["pipeline"] = "US" if base == PIPE else "XN"
    return d

idx = pd.concat([load(PIPE, lambda r: "US"), load(XN, lambda r: r["state"])], ignore_index=True)
idx = idx[idx["abspath"].apply(lambda p: Path(p).exists())].reset_index(drop=True)
print("rows to score:", len(idx), flush=True)

cols = ["pipeline", "system", "institution", "unitid", "page_type", "original_url", "local_path",
        "timestamp", "words_raw", "words_clean", "rule_fired",
        "ai_addressed_raw", "n_ai_terms_raw", "ai_addressed_clean", "n_ai_terms_clean",
        "ai_addressed_clean_strict", "n_ai_terms_clean_strict"]
for p in PROV:
    cols += [f"{p}_raw", f"{p}_present_raw", f"{p}_clean", f"{p}_present_clean",
             f"{p}_present_clean_w200", f"{p}_present_clean_w800", f"{p}_present_clean_strict"]
t0 = time.time()
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for i, r in enumerate(idx.itertuples(index=False), 1):
        path = Path(r.abspath)
        try:
            raw = B.extract_text(path)
        except Exception as e:
            raw = ""
        try:
            clean, rule = E.extract_clean_info(path)
        except Exception as e:
            clean, rule = "", f"error:{type(e).__name__}"
        sr = B.score_text(raw, 400)
        sc = B.score_text(clean, 400)
        s2 = B.score_text(clean, 200)
        s8 = B.score_text(clean, 800)
        ss = score_strict(clean, 400)
        row = {"pipeline": r.pipeline, "system": r.system, "institution": r.institution,
               "unitid": r.unitid, "page_type": r.page_type, "original_url": r.original_url,
               "local_path": r.local_path, "timestamp": r.timestamp,
               "words_raw": len(raw.split()), "words_clean": len(clean.split()), "rule_fired": rule,
               "ai_addressed_raw": sr["ai_addressed"], "n_ai_terms_raw": sr["n_ai_terms"],
               "ai_addressed_clean": sc["ai_addressed"], "n_ai_terms_clean": sc["n_ai_terms"],
               "ai_addressed_clean_strict": ss["ai_addressed"], "n_ai_terms_clean_strict": ss["n_ai_terms"]}
        for p in PROV:
            row[f"{p}_raw"] = sr[p]; row[f"{p}_present_raw"] = sr[p + "_present"]
            row[f"{p}_clean"] = sc[p]; row[f"{p}_present_clean"] = sc[p + "_present"]
            row[f"{p}_present_clean_w200"] = s2[p + "_present"]
            row[f"{p}_present_clean_w800"] = s8[p + "_present"]
            row[f"{p}_present_clean_strict"] = ss[p + "_present"]
        w.writerow(row)
        if i % 200 == 0 or i == len(idx):
            print(f"  {i}/{len(idx)}  {time.time()-t0:.0f}s", flush=True)
print("done", OUT, flush=True)
