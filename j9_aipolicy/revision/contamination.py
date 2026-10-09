"""How much of the provision coding came from navigation boilerplate: raw vs clean flags per
snapshot, by system and provision; endpoint-only subset; and worked examples of the reviewer's
case (an appeal or misconduct hit that sits in a removed menu)."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import re, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B
PROV = list(B.PROVISIONS.keys())
SYSTEMS = ["US", "UK", "AU", "CA"]
sc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str})
sc["ts"] = pd.to_datetime(sc["timestamp"], format="%Y%m%d%H%M%S")
sc["page_key"] = sc["local_path"].apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
panel_uids = set(pd.read_csv(PIPE / "data/panel.csv", dtype=str).unitid) | set(pd.read_csv(XN / "data/panel.csv", dtype=str).unitid)
ep = sc[(sc.ts <= "2026-03-31") & (sc.unitid.isin(panel_uids))].sort_values("ts").groupby(["unitid", "page_key"]).tail(1)
rows = []
for label, d in (("all snapshots", sc), ("endpoint pages of panel institutions (as of 2026Q1)", ep)):
    for s in SYSTEMS:
        ds = d[d.system == s]
        ai_raw = ds[ds.ai_addressed_raw == 1]
        r = {"subset": label, "system": s, "n_snapshots": len(ds), "n_ai_raw": len(ai_raw),
             "ai_addressed_lost": int(((ds.ai_addressed_raw == 1) & (ds.ai_addressed_clean == 0)).sum()),
             "ai_addressed_gained": int(((ds.ai_addressed_raw == 0) & (ds.ai_addressed_clean == 1)).sum()),
             "words_raw_mean": round(ds.words_raw.mean()), "words_clean_mean": round(ds.words_clean.mean()),
             "words_kept_share": round(ds.words_clean.sum() / max(1, ds.words_raw.sum()), 3)}
        for p in PROV:
            raw1 = ds[f"{p}_present_raw"] == 1; cl1 = ds[f"{p}_present_clean"] == 1
            r[f"{p}_raw_n"] = int(raw1.sum()); r[f"{p}_lost"] = int((raw1 & ~cl1).sum()); r[f"{p}_gained"] = int((~raw1 & cl1).sum())
            r[f"{p}_lost_share"] = round((raw1 & ~cl1).sum() / max(1, raw1.sum()), 3)
            r[f"{p}_hits_raw"] = int(ds[f"{p}_raw"].sum()); r[f"{p}_hits_clean"] = int(ds[f"{p}_clean"].sum())
            r[f"{p}_hits_vanished_share"] = round(1 - ds[f"{p}_clean"].sum() / max(1, ds[f"{p}_raw"].sum()), 3)
        rows.append(r)
out = pd.DataFrame(rows); out.to_csv(AN / "contamination_summary.csv", index=False)
pd.set_option("display.width", 250)
cols = ["subset", "system", "n_snapshots", "n_ai_raw", "ai_addressed_lost", "words_kept_share"] + [f"{p}_lost_share" for p in PROV]
print("=== share of raw presence flags that vanish under the clean extractor ===")
print(out[cols].to_string(index=False))
cols2 = ["subset", "system"] + [f"{p}_hits_vanished_share" for p in PROV]
print("\n=== share of raw regex hits (counts) that vanish ===")
print(out[cols2].to_string(index=False))
print("\n=== rule fired ===")
print(sc.groupby("system")["rule_fired"].value_counts().groupby(level=0).head(4).to_string())

# worked examples: appeal / misconduct present in raw but absent in clean; show the raw passage near the AI term
def passages(text, prov, window=400, k=2):
    spans = [(m.start(), m.end()) for m in B.AI_TERMS.finditer(text)]
    centers = [(a + b) / 2 for a, b in spans]
    out = []
    for m in B.PROVISIONS[prov].finditer(text):
        c = (m.start() + m.end()) / 2
        if any(abs(c - ac) <= window for ac in centers):
            out.append(text[max(0, m.start() - 160): m.end() + 160])
            if len(out) >= k:
                break
    return out
ex_rows = []
for prov in ("appeal", "misconduct_framing", "detector_surveillance", "l2_protection"):
    cand = ep[(ep[f"{prov}_present_raw"] == 1) & (ep[f"{prov}_present_clean"] == 0)]
    for r in cand.sample(min(4, len(cand)), random_state=0).itertuples(index=False):
        base = PIPE if r.pipeline == "US" else XN
        raw = B.extract_text(base / r.local_path)
        for ptxt in passages(raw, prov)[:1]:
            ex_rows.append({"provision": prov, "system": r.system, "institution": r.institution, "page_type": r.page_type,
                            "timestamp": r.timestamp, "raw_passage": ptxt})
ex = pd.DataFrame(ex_rows); ex.to_csv(AN / "contamination_examples.csv", index=False)
print("\n=== examples of flags that came from removed blocks (raw passage around the hit) ===")
for r in ex.itertuples(index=False):
    print(f"[{r.provision} | {r.system} | {r.institution} | {r.page_type} {r.timestamp}]\n    ...{r.raw_passage}...")
