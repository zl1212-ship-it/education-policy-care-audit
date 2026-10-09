"""Add strict-vocabulary window-200/800 presence columns for the cross-national snapshots to
scored_raw_vs_clean.csv (the US seed snapshots get them in seed_design.score_seed)."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import sys, re
from pathlib import Path
import pandas as pd
AN = AN; sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B
STRICT = re.compile(r"artificial intelligence|generative a\.?i\.?|gen(?:erative)?\s?ai|chat\s?gpt|large language model|\bllms?\b|\bgpt\b", re.I)
d = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
for p in B.PROVISIONS:
    for w in (200, 800):
        col = f"{p}_present_clean_strict_w{w}"
        if col not in d.columns: d[col] = 0
keep = B.AI_TERMS
PIPE = XN.parent
d["page_key"] = d.local_path.apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
bf = set(map(tuple, pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str).values)) if (AN / "seed_backfill_pages.csv").exists() else set()
todo = list(d.index[d.pipeline == "XN"]) + [i for i in d.index[d.pipeline == "US"] if (d.at[i, "unitid"], d.at[i, "page_key"]) in bf]
for i in todo:
    clean = E.extract_text_clean((XN if d.at[i, "pipeline"] == "XN" else PIPE) / d.at[i, "local_path"])
    B.AI_TERMS = STRICT
    try:
        s2, s8 = B.score_text(clean, 200), B.score_text(clean, 800)
    finally:
        B.AI_TERMS = keep
    for p in B.PROVISIONS:
        d.at[i, f"{p}_present_clean_strict_w200"] = s2[p + "_present"]; d.at[i, f"{p}_present_clean_strict_w800"] = s8[p + "_present"]
d.drop(columns=["page_key"]).to_csv(AN / "scored_raw_vs_clean.csv", index=False); print("strict window columns added for XN and backfill rows:", len(todo))
