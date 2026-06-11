"""Emit the J6 LaTeX tables from the committed result CSVs (reproducible).

  j6_table1.tex      Table 1: detector false-accusation rate by detector and L1 status.
  j6_table2.tex      Table 2: the eleven flagships that clear the governance floor.
  j6_tableS1_body.tex  Supplementary Table S1 body (longtable): all 50 flagships coded.

Outputs to ../paper/blinded-manuscript/. Run after analyze_detection.py and
analyze_policy.py. Tables 1 and 2 are \\input in the manuscript; the S1 body is
\\input in the standalone supplementary document.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "paper", "blinded-manuscript")
DETECTORS = ["HFOpenAI", "GPTZero", "Crossplag", "ZeroGPT", "OriginalityAI", "Quil", "Sapling"]


def esc(s):
    return str(s).replace("&", "\\&").replace("_", "\\_")


# ---------- Table 1: detector ----------
det = pd.read_csv(os.path.join(DATA, "results_summary.csv"))


def fpr(detector, group):
    r = det[(det.analysis == "fpr_by_detector") & (det.detector == detector)
            & (det.threshold == 0.50) & (det.group == group)]
    return float(r["value"].iloc[0]) * 100


def fold(detector):
    r = det[(det.analysis == "fpr_gap_fold") & (det.detector == detector) & (det.threshold == 0.50)]
    return float(r["value"].iloc[0])


lines = [r"\begin{table}[H]\centering",
         r"\caption{False-accusation rate on human-written essays, by detector and the author's "
         r"English status (decision threshold 0.50). Every essay is human-written, so each flag is a "
         r"false accusation.}",
         r"\label{tab:detector}", r"\small",
         r"\begin{tabular}{lccc}", r"\toprule",
         r"Detector & Non-native (\%) & Native (\%) & Fold gap \\", r"\midrule"]
for d in DETECTORS:
    disp = d.replace("Quil", "Quil.org")
    lines.append(f"{disp} & {fpr(d,'non-native'):.1f} & {fpr(d,'native'):.1f} & {fold(d):.1f} \\\\")
pnn = float(det[(det.analysis=="fpr_pooled_mean7")&(det.threshold==0.50)&(det.group=="non-native")]["value"].iloc[0])*100
pna = float(det[(det.analysis=="fpr_pooled_mean7")&(det.threshold==0.50)&(det.group=="native")]["value"].iloc[0])*100
pfold = float(det[(det.analysis=="fpr_pooled_gap_fold")&(det.threshold==0.50)]["value"].iloc[0])
lines += [r"\midrule",
          f"Pooled (mean of 7) & {pnn:.1f} & {pna:.1f} & {pfold:.1f} \\\\",
          r"\bottomrule", r"\end{tabular}",
          r"\\[3pt]\footnotesize \textit{Note.} Non-native $n=91$ (TOEFL); native $n=158$ (US "
          r"essays). Detector names follow the released data. Fold gaps are computed from unrounded "
          r"rates, so they can differ from the ratio of the rounded columns. Eighteen of 91 "
          r"non-native essays were flagged by all seven detectors; no native "
          r"essay was flagged unanimously at any threshold. The pooled gap widens from 10.4-fold at "
          r"threshold 0.25 to 26.4-fold at 0.90.",
          r"\end{table}"]
open(os.path.join(OUT, "j6_table1.tex"), "w").write("\n".join(lines) + "\n")


# ---------- Table 2: the eleven that clear the floor ----------
cor = pd.read_csv(os.path.join(DATA, "policy_corpus.csv"), dtype=str).fillna("")


def floor_of(r):
    if r.detector_admissibility == "prohibited":
        return "Binding ban on detector evidence"
    if r.l2_protection == "explicit":
        return "Explicit multilingual protection"
    if r.burden_of_proof == "institution":
        return "Flag may not be the sole basis"
    return None


cleared = [(r.institution, r.state, floor_of(r)) for _, r in cor.iterrows() if floor_of(r)]
order = {"Binding ban on detector evidence": 0, "Explicit multilingual protection": 1,
         "Flag may not be the sole basis": 2}
cleared.sort(key=lambda x: (order[x[2]], x[0]))
t2 = [r"\begin{table}[H]\centering",
      r"\caption{The eleven flagships that place a floor between a 16.9-fold biased flag and a "
      r"multilingual writer, and the floor that clears each. The other thirty-nine place none.}",
      r"\label{tab:cleared}", r"\small", r"\begin{tabular}{lll}", r"\toprule",
      r"Institution & State & Clearing floor \\", r"\midrule"]
for inst, st, fl in cleared:
    t2.append(f"{esc(inst)} & {st} & {fl} \\\\")
t2 += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(OUT, "j6_table2.tex"), "w").write("\n".join(t2) + "\n")


# ---------- Supplementary Table S1: all 50 ----------
ABBR = {"detector_admissibility": {"prohibited": "prohib.", "advisory": "advis.",
        "silent": "silent", "admissible": "admiss."}}
s1 = [r"\begin{longtable}{p{4.7cm}cccccc c}",
      r"\caption{Governance codes for all fifty public flagship universities. "
      r"Adm = detector admissibility; Burd = burden of proof; App = appeal pathway; L2 = multilingual "
      r"protection; Locus = decision locus; Vac = in the governance vacuum. Source URLs and verbatim "
      r"supporting passages accompany each code in the released policy corpus; see the Data "
      r"Availability Statement.}"
      r"\label{tab:s1}\\",
      r"\toprule",
      r"Institution & St & Adm & Burd & App & L2 & Locus & Vac \\", r"\midrule", r"\endfirsthead",
      r"\toprule Institution & St & Adm & Burd & App & L2 & Locus & Vac \\ \midrule \endhead",
      r"\bottomrule \endfoot"]
adm_ab = ABBR["detector_admissibility"]
for _, r in cor.sort_values("institution").iterrows():
    vac = "yes" if (r.detector_admissibility != "prohibited" and r.l2_protection != "explicit"
                    and r.burden_of_proof != "institution") else "no"
    s1.append(f"{esc(r.institution)} & {r.state} & {adm_ab.get(r.detector_admissibility, r.detector_admissibility)} "
              f"& {esc(r.burden_of_proof)} & {esc(r.appeal_pathway)} & {esc(r.l2_protection)} "
              f"& {esc(r.decision_locus)} & {vac} \\\\")
s1.append(r"\end{longtable}")
open(os.path.join(OUT, "j6_tableS1_body.tex"), "w").write("\n".join(s1) + "\n")

print("Wrote j6_table1.tex, j6_table2.tex, j6_tableS1_body.tex to", os.path.normpath(OUT))
print(f"Cleared institutions: {len(cleared)}")
