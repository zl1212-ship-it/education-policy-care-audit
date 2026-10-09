"""Re-score the retrieved policy PDFs (after the strict-regex fix) and record each PDF's capture
date relative to the shock."""
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
idx = pd.read_csv(AN / "policy_pdf_index.csv", dtype=str); idx = idx[idx.status == "ok"]
rows = []
for r in idx.itertuples(index=False):
    text = E._text_from_string(E._pdf_text((AN / r.local_path).read_bytes()))
    sc = B.score_text(text, 400); keep = B.AI_TERMS; B.AI_TERMS = STRICT
    try: ss = B.score_text(text, 400)
    finally: B.AI_TERMS = keep
    row = {"system": r.system, "unitid": r.unitid, "institution": r.institution, "pdf_url": r.pdf_url, "anchor": r.anchor, "timestamp": r.timestamp,
           "post_shock_capture": int(str(r.timestamp) >= "20221130"), "words": len(text.split()), "ai_addressed_clean": sc["ai_addressed"], "ai_addressed_clean_strict": ss["ai_addressed"]}
    for p in B.PROVISIONS: row[f"{p}_present_clean"] = sc[p + "_present"]; row[f"{p}_present_clean_strict"] = ss[p + "_present"]
    rows.append(row)
d = pd.DataFrame(rows); d.to_csv(AN / "policy_pdf_scores.csv", index=False)
print("PDFs scored:", len(d), "| post-shock captures:", int(d.post_shock_capture.sum()), "| with strict AI text:", int(d.ai_addressed_clean_strict.sum()), "| by system:", d.groupby("system").size().to_dict())
