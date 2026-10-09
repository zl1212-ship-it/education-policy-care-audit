"""Validation of the provision codes on the cleaned, one-page-per-type design:
(a) second coder: the pipeline's independently specified rule set (second_coder.py) applied to a
    random sample of 80 cleaned snapshots from the symmetric design, agreement / kappa / AC1;
(b) unscoped counts: appeal and multilingual language anywhere on the AI-addressing endpoint pages
    (not within the AI window), to bound what the proximity rule leaves out;
(c) a 40-passage audit sample of flagged passages (clean strict) for a hand reading;
(d) the one pre-shock AI-positive page (passage and date).
Writes second_coder_r1.csv, unscoped_remedies.csv, audit_sample_r1.csv, preshock_positive_r1.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import sys, re
from pathlib import Path
import numpy as np, pandas as pd
AN = AN; sys.path.insert(0, str(REV))
PIPE = PIPE; XN = PIPE / "crossnational"; sys.path.insert(0, str(PIPE))
import extract_clean as E
B = E.B
import second_coder as SC  # the pipeline's alternative rule set
STRICT = re.compile(r"artificial intelligence|generative a\.?i\.?|gen(?:erative)?\s?ai|chat\s?gpt|large language model|\bllms?\b|\bgpt\b", re.I)
PROV = list(B.PROVISIONS.keys())
seed = pd.read_csv(AN / "scored_seed.csv", dtype={"unitid": str, "timestamp": str}); seed["base"] = str(AN)
allsc = pd.read_csv(AN / "scored_raw_vs_clean.csv", dtype={"unitid": str, "timestamp": str}); allsc["page_key"] = allsc.local_path.apply(lambda p: Path(p).stem.rsplit("__", 1)[0])
xn = allsc[allsc.pipeline == "XN"].copy(); xn["base"] = str(XN)
bf = set(map(tuple, pd.read_csv(AN / "seed_backfill_pages.csv", dtype=str).values)) if (AN / "seed_backfill_pages.csv").exists() else set()
back = allsc[(allsc.pipeline == "US") & [(u, k) in bf for u, k in zip(allsc.unitid, allsc.page_key)]].copy(); back["base"] = str(PIPE)
sample = set(pd.read_csv(AN / "seed_samples.csv", dtype=str).unitid)
snaps = pd.concat([seed, xn, back], ignore_index=True); snaps = snaps[snaps.unitid.isin(sample)].copy()
snaps["ts"] = pd.to_datetime(snaps.timestamp, format="%Y%m%d%H%M%S")
def clean_text(r): return E.extract_text_clean(Path(r.base) / r.local_path)
def strict_score(text, window=400):
    keep = B.AI_TERMS; B.AI_TERMS = STRICT
    try: return B.score_text(text, window)
    finally: B.AI_TERMS = keep
def strict_second(text, window=400):
    keep = B.AI_TERMS; B.AI_TERMS = STRICT
    try: return SC.code_second(text, window)
    finally: B.AI_TERMS = keep
# (a) second coder on 80 random cleaned snapshots that carry strict AI text (so the comparison is on scoped codes)
pool = snaps[snaps.ai_addressed_clean_strict.astype(int) == 1]
samp = pool.sample(min(80, len(pool)), random_state=11)
A, Bc = [], []
for r in samp.itertuples(index=False):
    t = clean_text(r); a = strict_score(t); b = strict_second(t)
    A.append([a[p + "_present"] for p in PROV]); Bc.append([int(b[p]) if not isinstance(b[p], dict) else int(b[p]["present"]) for p in PROV]) if False else Bc.append([int(bool(b[p + "_present"] if (p + "_present") in b else b[p])) for p in PROV])
A, Bc = np.array(A), np.array(Bc)
rows = []
for j, p in enumerate(PROV):
    a, b = A[:, j], Bc[:, j]
    rows.append({"provision": p, "n": len(a), "prevalence_primary": round(a.mean(), 3), "raw_agreement": round(float(np.mean(a == b)), 3), "cohen_kappa": round(SC.cohen_kappa(a, b), 3), "gwet_ac1": round(SC.gwet_ac1(a, b), 3)})
rows.append({"provision": "pooled", "n": A.size, "prevalence_primary": round(A.mean(), 3), "raw_agreement": round(float(np.mean(A == Bc)), 3), "cohen_kappa": round(SC.cohen_kappa(A.ravel(), Bc.ravel()), 3), "gwet_ac1": round(SC.gwet_ac1(A.ravel(), Bc.ravel()), 3)})
sc_df = pd.DataFrame(rows); sc_df.to_csv(AN / "second_coder_r1.csv", index=False); print("=== second coder (cleaned, strict, 80 AI-addressing snapshots) ===\n", sc_df.to_string(index=False))
# (b) unscoped remedy language on AI-addressing endpoint pages
ep = snaps[snaps.ts <= "2026-03-31"].sort_values("ts").groupby(["unitid", "page_key" if "page_key" in snaps.columns else "local_path"]).tail(1)
ep = ep[ep.ai_addressed_clean_strict.astype(int) == 1]
ss = pd.read_csv(AN / "seed_samples.csv", dtype=str); sysmap = dict(zip(ss.unitid, ss.system))
urows = []
for r in ep.itertuples(index=False):
    t = clean_text(r)
    urows.append({"system": sysmap[r.unitid], "unitid": r.unitid, "institution": r.institution, "page_type": r.page_type,
                  "appeal_anywhere": int(bool(B.PROVISIONS["appeal"].search(t))), "l2_anywhere": int(bool(B.PROVISIONS["l2_protection"].search(t))),
                  "appeal_scoped": int(r.appeal_present_clean_strict), "l2_scoped": int(r.l2_protection_present_clean_strict)})
u = pd.DataFrame(urows); inst = u.groupby(["system", "unitid"])[["appeal_anywhere", "l2_anywhere", "appeal_scoped", "l2_scoped"]].max().reset_index()
summ = inst.groupby("system")[["appeal_anywhere", "l2_anywhere", "appeal_scoped", "l2_scoped"]].mean().round(2); summ["n_inst_addressing_ai"] = inst.groupby("system").size()
summ.to_csv(AN / "unscoped_remedies.csv"); print("\n=== remedy language anywhere on the AI-addressing endpoint pages vs within the AI window ===\n", summ.to_string())
# (c) audit sample of 40 flagged passages (strict, window 400) with the matched provision and the passage
rng = np.random.default_rng(40); arows = []
flagged = []
for r in snaps.itertuples(index=False):
    for p in PROV:
        if int(getattr(r, f"{p}_present_clean_strict")) == 1: flagged.append((r, p))
pick = [flagged[i] for i in rng.choice(len(flagged), min(40, len(flagged)), replace=False)]
for r, p in pick:
    t = clean_text(r); spans = [(m.start(), m.end()) for m in STRICT.finditer(t)]; centers = [(a + b) / 2 for a, b in spans]
    for m in B.PROVISIONS[p].finditer(t):
        c = (m.start() + m.end()) / 2
        if any(abs(c - ac) <= 400 for ac in centers):
            arows.append({"system": sysmap.get(r.unitid, ""), "institution": r.institution, "page_type": r.page_type, "timestamp": r.timestamp, "provision": p, "match": m.group(0), "passage": t[max(0, m.start() - 220): m.end() + 220]}); break
pd.DataFrame(arows).to_csv(AN / "audit_sample_r1.csv", index=False); print("\naudit sample written:", len(arows), "passages")
# (d) pre-shock positives under the strict vocabulary
pre = snaps[(snaps.ts < "2022-11-30") & (snaps.ai_addressed_clean_strict.astype(int) == 1)]
prows = []
for r in pre.sort_values("ts").itertuples(index=False):
    t = clean_text(r); m = STRICT.search(t)
    prows.append({"system": sysmap.get(r.unitid, ""), "institution": r.institution, "page_type": r.page_type, "timestamp": r.timestamp, "match": m.group(0) if m else "", "passage": t[max(0, m.start() - 250): m.end() + 250] if m else ""})
pd.DataFrame(prows).to_csv(AN / "preshock_positive_r1.csv", index=False)
for x in prows[:3]: print("\nPRE-SHOCK:", x["institution"], x["timestamp"], "|", x["passage"][:400])
