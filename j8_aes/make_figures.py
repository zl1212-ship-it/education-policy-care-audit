"""J8 figures.

  Figure 1: the core gap -- mean machine-minus-human score difference for ELL
            and non-ELL writers, per scoring family (PERSUADE, out-of-fold),
            with the raw and conditional differentials and 95% CIs.
  Figure 2: the decision layer -- demotion rate (human-passed essays the
            machine fails) for ELL vs non-ELL writers at the pass mark, per
            family, with the differential.
  Figure 3: the second-opinion benchmark -- how a second opinion differs by
            writer SES when the second opinion is a human rater vs each
            machine family (ELLIPSE double-rated essays), with 95% CIs.

Inputs : data/results_gaps.csv, data/results_decision.csv,
         data/results_benchmark.csv
Outputs: ../paper/blinded-manuscript/J8/j8_figure{1,2,3}.{pdf,png,tiff}
Run after analyze_gaps.py and analyze_benchmark.py.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "paper", "blinded-manuscript", "J8")
os.makedirs(OUT, exist_ok=True)  # gitignored on a fresh clone
plt.rcParams.update({"font.size": 11, "font.family": "serif"})

FAMILIES = ["handfeat", "tfidf", "embed"]
FAMILY_LABEL = {"handfeat": "Hand features\n+ ridge",
                "tfidf": "TF-IDF\n+ ridge",
                "embed": "Embedding\n+ ridge"}
ELL, NON = "#b2182b", "#2166ac"  # focal red, reference blue
CUT = 4


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200)
    fig.savefig(os.path.join(OUT, name + ".tiff"), dpi=600,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


gaps = pd.read_csv(os.path.join(DATA, "results_gaps.csv"))
dec = pd.read_csv(os.path.join(DATA, "results_decision.csv"))
bench = pd.read_csv(os.path.join(DATA, "results_benchmark.csv"))


def gap_val(fam, group, metric, proto="oof"):
    r = gaps[(gaps.corpus == "persuade") & (gaps.dimension == "ell_status")
             & (gaps.family == fam) & (gaps.protocol == proto)
             & (gaps.group == group) & (gaps.metric == metric)]
    return r.iloc[0]


# ---------- Figure 1: machine-minus-human gap by ELL status ----------
fig, (a1, a2) = plt.subplots(
    1, 2, figsize=(9.5, 4.0), gridspec_kw={"width_ratios": [1.3, 1]})

x = np.arange(len(FAMILIES))
w = 0.38
ell_n = int(gap_val("embed", "Yes", "mean_gap").n)
non_n = int(gap_val("embed", "No", "mean_gap").n)
ell = [gap_val(f, "Yes", "mean_gap").value for f in FAMILIES]
non = [gap_val(f, "No", "mean_gap").value for f in FAMILIES]
a1.bar(x - w / 2, ell, w, color=ELL, label=f"English learners (n={ell_n:,})")
a1.bar(x + w / 2, non, w, color=NON, label=f"Non-EL (n={non_n:,})")
a1.axhline(0, color="0.3", lw=0.8)
a1.set_xticks(x)
a1.set_xticklabels([FAMILY_LABEL[f] for f in FAMILIES], fontsize=9)
a1.set_ylabel("Mean machine $-$ human score (1-6 scale)")
a1.set_title("(a) Signed gap by group, out-of-fold", fontsize=10)
a1.legend(frameon=False, fontsize=9)
a1.spines[["top", "right"]].set_visible(False)

SHORT = {"handfeat": "Hand features", "tfidf": "TF-IDF", "embed": "Embedding"}
ypos = np.arange(len(FAMILIES) * 2)
labels, vals, los, his = [], [], [], []
for f in FAMILIES:
    for metric, tag in [("raw_differential", "raw"),
                        ("conditional_differential", "same human score")]:
        r = gap_val(f, "Yes - No", metric)
        labels.append(f"{SHORT[f]}, {tag}")
        vals.append(r.value)
        los.append(r.ci_lo)
        his.append(r.ci_hi)
a2.errorbar(vals, ypos,
            xerr=[np.array(vals) - np.array(los),
                  np.array(his) - np.array(vals)],
            fmt="o", color="0.15", ecolor="0.45", capsize=3)
a2.axvline(0, color="0.3", lw=0.8, ls="--")
a2.set_yticks(ypos)
a2.set_yticklabels(labels, fontsize=8.5)
a2.invert_yaxis()
a2.set_xlabel("EL $-$ non-EL differential (score points)")
a2.set_title("(b) Differentials, 95% CI", fontsize=10)
a2.spines[["top", "right"]].set_visible(False)
save(fig, "j8_figure1")


# ---------- Figure 2: demotion rates at the pass mark ----------
fig, ax = plt.subplots(figsize=(7.2, 4.2))
sub = dec[(dec.corpus == "persuade") & (dec.dimension == "ell_status")
          & (dec.protocol == "oof") & (dec.cutoff == CUT)]
ell_r = [float(sub[(sub.family == f) & (sub.group == "Yes")
                   ].demotion_rate.iloc[0]) for f in FAMILIES]
non_r = [float(sub[(sub.family == f) & (sub.group == "No")
                   ].demotion_rate.iloc[0]) for f in FAMILIES]
ax.bar(x - w / 2, [v * 100 for v in ell_r], w, color=ELL,
       label="English learners")
ax.bar(x + w / 2, [v * 100 for v in non_r], w, color=NON, label="Non-EL")
for i, f in enumerate(FAMILIES):
    d = sub[(sub.family == f) & (sub.group == "Yes - No")]
    if len(d):
        ax.text(i, max(ell_r[i], non_r[i]) * 100 + 1.0,
                f"+{float(d.demotion_rate.iloc[0])*100:.1f} pp",
                ha="center", fontsize=9, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels([FAMILY_LABEL[f] for f in FAMILIES], fontsize=9.5)
ax.set_ylabel("Human-passed essays failed by machine (%)")
ax.set_title(f"Demotion at the pass mark ({CUT} of 6), out-of-fold",
             fontsize=10.5)
ax.legend(frameon=False, fontsize=9.5)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "j8_figure2")


# ---------- Figure 3: second-opinion benchmark (ELLIPSE) ----------
fig, ax = plt.subplots(figsize=(7.0, 4.0))
order = ["human", "handfeat", "tfidf", "embed"]
disp = {"human": "Second human rater", "handfeat": "Machine: hand features",
        "tfidf": "Machine: TF-IDF", "embed": "Machine: embedding"}
sub = bench[(bench.analysis == "second_opinion") & (bench.dimension == "SES")]
vals = [float(sub[sub.second_opinion == o].value.iloc[0]) for o in order]
los = [float(sub[sub.second_opinion == o].ci_lo.iloc[0]) for o in order]
his = [float(sub[sub.second_opinion == o].ci_hi.iloc[0]) for o in order]
ypos = np.arange(len(order))
colors = [NON] + [ELL] * 3
ax.errorbar(vals, ypos,
            xerr=[np.array(vals) - np.array(los),
                  np.array(his) - np.array(vals)],
            fmt="none", ecolor="0.45", capsize=3)
ax.scatter(vals, ypos, c=colors, s=55, zorder=3)
ax.axvline(0, color="0.3", lw=0.8, ls="--")
ax.set_yticks(ypos)
ax.set_yticklabels([disp[o] for o in order], fontsize=9.5)
ax.invert_yaxis()
ax.set_xlabel("Second-opinion differential by SES (score points, 95% CI)")
ax.set_title("A human second opinion is group-neutral; the machines tilt\n"
             "(ELLIPSE double-rated essays, all writers English learners)",
             fontsize=10.5)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "j8_figure3")

print("Wrote j8_figure{1,2,3}.{pdf,png,tiff} to", os.path.normpath(OUT))
