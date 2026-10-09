"""Placebo and paired-excess tests under the matched page design (L6 text/page set) and the
strict-AI design (L7), to complement placebo_text.csv. Appends rows to placebo_text_matched.csv."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, str(REV))
import convergence_ladder as C
C.load_pagesets()
snaps = C.load(C.PIPE / "data" / "snapshot_index.csv", C.PIPE, lambda r: "US")
snaps += C.load(C.XN / "data" / "snapshot_index.csv", C.XN, lambda r: r["state"])
snaps = pd.DataFrame(snaps)
rows = []
for rung, textkey in (("L6", "L4"), ("L7", "L7"), ("L8", "L7"), ("L9", "L7")):
    sub = snaps[[C.page_allowed(u, p, rung) for u, p in zip(snaps["uid"], snaps["path"])]]
    ai_rows, non_rows, pre_rows, sysv, sysv_pre = [], [], [], [], []
    for uid, g in sub.groupby("uid"):
        sysname = g["sys"].iloc[0]
        a_parts, n_parts, p_parts = [], [], []
        for url, gp in g.groupby("url"):
            t = C.texts_of(gp.sort_values("ts").iloc[-1]["path"], sysname)
            a_parts.append(t[textkey]); n_parts.append(t["nonai_L4"])
            gpre = gp[gp["ts"] < C.SHOCK]
            if len(gpre):
                p_parts.append(C.texts_of(gpre.sort_values("ts").iloc[-1]["path"], sysname)["full_L4"])
        a = " ".join(x for x in a_parts if x).strip(); n = " ".join(x for x in n_parts if x).strip(); pr = " ".join(x for x in p_parts if x).strip()
        if a and n:
            ai_rows.append(" ".join(a.split()[:600])); non_rows.append(" ".join(n.split()[:600])); sysv.append(sysname)
        if pr:
            pre_rows.append(" ".join(pr.split()[:3000])); sysv_pre.append(sysname)
    pm_non = C.endpoint_perm(pd.Series(non_rows), sysv)
    pm_pre = C.endpoint_perm(pd.Series(pre_rows), sysv_pre)
    pm_pair = C.paired_excess(ai_rows, non_rows, sysv)
    pm_ai = C.endpoint_perm(pd.Series(ai_rows), sysv)
    pm_nonus = C.endpoint_perm(pd.Series([a for a, sy in zip(ai_rows, sysv) if sy != "US"]), [sy for sy in sysv if sy != "US"])
    rows.append({"rung": rung, "text": "ai_text_nonUS_only_cap600", "n_inst": sum(sy != "US" for sy in sysv), **{k: round(v, 4) for k, v in pm_nonus.items()}})
    for label, pm, n in (("ai_text_same_institutions_cap600", pm_ai, len(sysv)), ("nonai", pm_non, len(sysv)), ("full_pre", pm_pre, len(sysv_pre)), ("paired_excess_ai_minus_nonai_cap600", pm_pair, len(sysv))):
        rows.append({"rung": rung, "text": label, "n_inst": n, **{k: round(v, 4) for k, v in pm.items()}})
        print(f"[{rung} {label}] n={n} within {pm['within']:.3f} cross {pm['cross']:.3f} gap {pm['gap']:+.4f} null [{pm['null_lo']:+.4f},{pm['null_hi']:+.4f}] p={pm['p']:.3f}", flush=True)
pd.DataFrame(rows).to_csv(AN / "placebo_text_matched.csv", index=False)
print("done")
