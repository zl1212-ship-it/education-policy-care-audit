"""Automated second coder for inter-rater reliability of the provision codes.

The primary lexicon (build_panel.py) is one operationalization of each provision.
This script applies a SECOND, independently specified rule set, a different surface
vocabulary for the same constructs, under the same AI-proximity scoping, to a random
sample of snapshots, and compares its present/absent code for each provision against
the primary coder. It reports, per provision, raw agreement, Cohen's kappa, and
Gwet's AC1 (kappa is deflated for rare provisions by the base-rate paradox, so the
two agreement statistics are reported alongside it).

This is an independent automated coder, not a human; it tests whether the codes
depend on the specific wording of one lexicon, not on human judgment.

Output: data/second_coder_kappa.csv
"""
import sys
import re
from pathlib import Path

import numpy as np
import pandas as pd

import build_panel as bp

HERE = Path(__file__).parent
DATA = HERE / "data"
N_SAMPLE = 80

# Independently specified patterns: same constructs, different surface vocabulary.
SECOND = {
    "prohibition": re.compile(
        r"\bban(?:ned|s|ning)?\b|barred|disallow|not allow|may not|cannot use|can't use|"
        r"off[- ]limits|without permission|is not acceptable|never use", re.I),
    "detector_surveillance": re.compile(
        r"\bdetect(?:ed|ing|or|ion)?\b|turnitin|gptzero|copyleaks|originality|ai checker|"
        r"ai score|similarity (?:score|report)|flagged", re.I),
    "misconduct_framing": re.compile(
        r"cheat|dishonest|misconduct|integrity violation|unauthorized aid|academic offense|"
        r"\bfraud\b|passing off|breach of", re.I),
    "sanction": re.compile(
        r"penal|sanction|\bfail(?:ed|ing|s)?\b|zero on|suspend|expel|dismiss|"
        r"disciplinary (?:action|process|measure)|referred to|consequence", re.I),
    "permitted_use": re.compile(
        r"\ballow(?:ed|s|ing)?\b|encourage|acceptable to use|free to use|welcome to use|"
        r"may use (?:it|ai|these|the tool)|with (?:prior )?approval|when appropriate", re.I),
    "disclosure": re.compile(
        r"acknowledge|\bcredit\b|give credit|\bcit(?:e|ed|ing|ation)\b|attribut|"
        r"note (?:that|the|any) use|state (?:that|the|any) use|be transparent|reveal (?:the|any) use", re.I),
    "appeal": re.compile(
        r"appeal|grievance|hearing|contest|dispute the|due process|review board|"
        r"right to respond|reconsider", re.I),
    "l2_protection": re.compile(
        r"multilingual|english language learner|non[- ]?native|\besl\b|second[- ]?language|"
        r"international student|first language|english as a", re.I),
}
PROV = ["prohibition", "detector_surveillance", "misconduct_framing", "sanction",
        "permitted_use", "disclosure", "appeal", "l2_protection"]


def code_second(text, window=bp.WINDOW):
    centers = [(m.start() + m.end()) / 2 for m in bp.AI_TERMS.finditer(text)]
    out = {}
    for name, pat in SECOND.items():
        present = 0
        if centers:
            for m in pat.finditer(text):
                c = (m.start() + m.end()) / 2
                if any(abs(c - a) <= window for a in centers):
                    present = 1
                    break
        out[name] = present
    return out


def gwet_ac1(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = np.mean(a == b)
    pi = (a.mean() + b.mean()) / 2.0
    pe = 2 * pi * (1 - pi)
    return (po - pe) / (1 - pe) if (1 - pe) else 1.0


def cohen_kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = np.mean(a == b)
    pa1, pb1 = a.mean(), b.mean()
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if (1 - pe) else 1.0


def main():
    idx = pd.read_csv(DATA / "snapshot_index.csv")
    keep = set(pd.read_csv(DATA / "panel.csv")["unitid"].unique())
    idx = idx[idx["bytes"].notna() & (idx["bytes"] > 0) & idx["unitid"].isin(keep)]
    sample = idx.sample(min(N_SAMPLE, len(idx)), random_state=11)

    prim, sec = [], []
    for r in sample.itertuples(index=False):
        p = HERE / r.local_path
        if not p.exists():
            continue
        t = bp.extract_text(p)
        s1 = bp.score_text(t)
        s2 = code_second(t)
        prim.append({k: s1[k + "_present"] for k in PROV})
        sec.append(s2)
    P = pd.DataFrame(prim)
    S = pd.DataFrame(sec)

    rows = []
    for k in PROV:
        a, b = P[k].values, S[k].values
        rows.append({"provision": k, "n": len(a),
                     "primary_rate": round(a.mean(), 3), "second_rate": round(b.mean(), 3),
                     "raw_agreement": round(float(np.mean(a == b)), 3),
                     "cohen_kappa": round(cohen_kappa(a, b), 3),
                     "gwet_ac1": round(gwet_ac1(a, b), 3)})
    # overall (pooled across provisions)
    alla = P.values.ravel()
    allb = S.values.ravel()
    rows.append({"provision": "POOLED", "n": len(alla),
                 "primary_rate": round(alla.mean(), 3), "second_rate": round(allb.mean(), 3),
                 "raw_agreement": round(float(np.mean(alla == allb)), 3),
                 "cohen_kappa": round(cohen_kappa(alla, allb), 3),
                 "gwet_ac1": round(gwet_ac1(alla, allb), 3)})
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "second_coder_kappa.csv", index=False)
    print(f"Independent second coder on {len(P)} snapshots:")
    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
