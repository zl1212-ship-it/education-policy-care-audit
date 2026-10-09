"""United States endpoint prevalence by page source (curated page vs screened discovered page),
strict vocabulary, on the symmetric design. Writes seed_prevalence_by_source.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
from pathlib import Path
import pandas as pd
PROV = ["prohibition", "detector_surveillance", "misconduct_framing", "sanction", "permitted_use", "disclosure", "appeal", "l2_protection"]
ss = pd.read_csv(AN / "seed_samples.csv", dtype=str); us = set(ss[ss.system == "US"].unitid)
sc = pd.read_csv(AN / "scored_seed.csv", dtype={"unitid": str}); bf = pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str)
p = pd.read_csv(AN / "seed_panel_clean_strict.csv", dtype={"unitid": str}); last = p.sort_values("event_q").groupby("unitid").tail(1); last = last[last.unitid.isin(us)]
def source(u):
    a, b = u in set(sc.unitid), u in set(bf.unitid)
    return "curated only" if a and not b else ("screened only" if b and not a else "both")
last["source"] = last.unitid.map(source)
rows = []
for src, d in last.groupby("source"):
    r = {"rule": f"US by page source: {src}", "system": "US", "n": len(d), "ai_addressed": d.ai_addressed.mean()}
    for pv in PROV: r[pv] = d[f"{pv}_present"].mean()
    r["restrictive_idx"] = d.restrictive_idx.mean(); r["procedural_idx"] = d.procedural_idx.mean(); rows.append(r)
out = pd.DataFrame(rows); out.to_csv(AN / "seed_prevalence_by_source.csv", index=False); print(out.round(2).to_string(index=False))
