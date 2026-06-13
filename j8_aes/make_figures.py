"""J8 figures.

  Figure 1: the core gap -- mean machine-minus-human score difference for ELL
            and non-ELL writers, per scoring family (PERSUADE, out-of-fold),
            with the raw and conditional differentials and 95% CIs.
  Figure 2: the decision layer -- demotion rate (human-passed essays the
            machine fails) for ELL vs non-ELL writers at the pass mark, per
            family, with the differential.
  Figure 3: the second-opinion benchmark (ELLIPSE double-rated essays),
            two panels. (a) signed second-opinion differential across every
            subgroup contrast, for a human rater and each machine family,
            showing the human rater's own tilt on the race contrasts.
            (b) the direct paired test, (machine differential) minus (human
            differential), whose CIs all cross zero.

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

FAMILIES = ["handfeat", "tfidf", "embed", "finetuned"]
FAMILY_LABEL = {"handfeat": "Hand features\n+ ridge",
                "tfidf": "TF-IDF\n+ ridge",
                "embed": "Frozen\nembedding",
                "finetuned": "Fine-tuned\ntransformer"}
ELL, NON = "#b2182b", "#2166ac"  # focal red, reference blue
CUT = 4


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".tiff"), dpi=600,
                bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
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

SHORT = {"handfeat": "Hand features", "tfidf": "TF-IDF", "embed": "Frozen embed",
         "finetuned": "Fine-tuned"}
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


# ---------- Figure 3: second-opinion benchmark (ELLIPSE), honest two-panel ----------
# Contrasts shown, top to bottom; the race contrasts are included so the human
# rater's own tilt is visible, not only the SES contrast where it is null.
CONTRASTS = [
    ("SES", "Economically disadvantaged - Not economically disadvantaged",
     "Economic disadvantage"),
    ("gender", "Female - Male", "Gender (F - M)"),
    ("race_ethnicity", "Hispanic/Latino - White", "Hispanic/Latino - White"),
    ("race_ethnicity", "Black/African American - White",
     "Black - White"),
    ("race_ethnicity", "Asian/Pacific Islander - White", "Asian/PI - White"),
]
fams = ["human", "handfeat", "tfidf", "embed", "finetuned"]
fam_disp = {"human": "Human rater 2", "handfeat": "Hand features",
            "tfidf": "TF-IDF", "embed": "Frozen embedding",
            "finetuned": "Fine-tuned transformer"}
fam_col = {"human": NON, "handfeat": "#7b3294", "tfidf": "#e08214",
           "embed": "#c51b7d", "finetuned": "#1b7837"}

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5.0), sharey=True)


def _offsets(fams_here):
    """Even vertical offsets within a contrast row, top source highest."""
    n = len(fams_here)
    span = 0.62
    pos = np.linspace(span / 2, -span / 2, n)
    return {f: pos[i] for i, f in enumerate(fams_here)}


def forest(ax, analysis, fams_here, title, xlabel):
    base = np.arange(len(CONTRASTS))
    off = _offsets(fams_here)
    for fam in fams_here:
        xs, ys, lo, hi = [], [], [], []
        for k, (dim, grp, _) in enumerate(CONTRASTS):
            r = bench[(bench.analysis == analysis)
                      & (bench.second_opinion == fam)
                      & (bench.dimension == dim) & (bench.group == grp)]
            if not len(r):
                continue
            xs.append(float(r.value.iloc[0]))
            ys.append(base[k] + off[fam])
            lo.append(float(r.ci_lo.iloc[0]))
            hi.append(float(r.ci_hi.iloc[0]))
        xs = np.array(xs)
        ax.errorbar(xs, ys, xerr=[xs - np.array(lo), np.array(hi) - xs],
                    fmt="o", ms=4.0, color=fam_col[fam], ecolor=fam_col[fam],
                    elinewidth=1.0, capsize=2, label=fam_disp[fam])
    ax.axvline(0, color="0.3", lw=0.9, ls="--")
    ax.set_yticks(base)
    ax.set_yticklabels([c[2] for c in CONTRASTS], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=9.5)
    ax.set_title(title, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)


forest(a1, "second_opinion", fams,
       "(a) Second-opinion differential, by source",
       "Second $-$ first rating differential (points, 95% CI)")
forest(a2, "machine_minus_human_paired", ["handfeat", "tfidf", "embed", "finetuned"],
       "(b) Machine tilt minus human tilt (paired)",
       "(machine $-$ human) differential (points, 95% CI)")
handles, labels = a1.get_legend_handles_labels()
fig.legend(handles, labels, frameon=False, fontsize=9, ncol=5,
           loc="lower center", bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(bottom=0.22)
save(fig, "j8_figure3")

print("Wrote j8_figure{1,2,3}.{pdf,png,tiff} to", os.path.normpath(OUT))
