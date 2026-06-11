"""J6 figures.

  Figure 1: detector layer -- false-accusation (false-positive) rate on human essays
            by native vs non-native English status, per detector and pooled (tau=0.50).
  Figure 2: governance layer -- (a) how the 50 flagships treat detector output as
            evidence; (b) the ten that escape the governance vacuum, by the floor that
            clears them (binding ban / explicit multilingual protection / corroboration).
  Figure 3: joint exposure -- the vacuum does not track exposure: governance-vacuum rate
            by international-enrollment tercile, with mean international share.

Inputs : data/results_summary.csv, data/policy_results.csv, data/policy_corpus.csv
Outputs: ../paper/blinded-manuscript/j6_figure{1,2,3}.{pdf,png,tiff}
Run after analyze_detection.py, analyze_policy.py, build_ipeds_covariate.py.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "paper", "blinded-manuscript")
plt.rcParams.update({"font.size": 11, "font.family": "serif"})

DETECTORS = ["HFOpenAI", "GPTZero", "Crossplag", "ZeroGPT", "OriginalityAI", "Quil", "Sapling"]
NN, NA = "#b2182b", "#2166ac"  # non-native (red), native (blue)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200)
    fig.savefig(os.path.join(OUT, name + ".tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


det = pd.read_csv(os.path.join(DATA, "results_summary.csv"))
pol = pd.read_csv(os.path.join(DATA, "policy_results.csv"))
corpus = pd.read_csv(os.path.join(DATA, "policy_corpus.csv"), dtype=str).fillna("")
coded = corpus[corpus.detector_admissibility != ""].copy()


# ---------- Figure 1: detector false-accusation rate by L1 status ----------
def fpr(detector, group):
    r = det[(det.analysis == "fpr_by_detector") & (det.detector == detector)
            & (det.threshold == 0.50) & (det.group == group)]
    return float(r["value"].iloc[0])


nn = [fpr(d, "non-native") for d in DETECTORS]
na = [fpr(d, "native") for d in DETECTORS]
pooled_nn = float(det[(det.analysis == "fpr_pooled_mean7") & (det.threshold == 0.50)
                      & (det.group == "non-native")]["value"].iloc[0])
pooled_na = float(det[(det.analysis == "fpr_pooled_mean7") & (det.threshold == 0.50)
                      & (det.group == "native")]["value"].iloc[0])

labels = [d.replace("Quil", "Quil.org") for d in DETECTORS] + ["Pooled\n(mean of 7)"]
nn_all, na_all = nn + [pooled_nn], na + [pooled_na]
x = np.arange(len(labels))
w = 0.4
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.bar(x - w / 2, [v * 100 for v in nn_all], w, color=NN, label="Non-native (TOEFL, n=91)")
ax.bar(x + w / 2, [v * 100 for v in na_all], w, color=NA, label="Native (US, n=158)")
ax.axvline(len(DETECTORS) - 0.5, color="0.7", lw=0.8, ls="--")
ax.set_ylabel("Human essays flagged as AI (%)")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9)
ax.set_title("False accusation rate on human-written essays, by author's English status "
             "(threshold 0.50)", fontsize=10.5)
ax.legend(frameon=False, fontsize=9.5)
ax.spines[["top", "right"]].set_visible(False)
ax.annotate(f"{pooled_nn*100:.0f}% vs {pooled_na*100:.0f}%\n({pooled_nn/pooled_na:.1f}x)",
            xy=(len(DETECTORS), pooled_nn * 100), xytext=(len(DETECTORS) - 0.3, pooled_nn * 100 + 6),
            fontsize=9, fontweight="bold")
save(fig, "j6_figure1")


# ---------- Figure 2: governance ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.0))

# (a) admissibility distribution
order = ["admissible", "silent", "advisory", "prohibited"]
disp = {"admissible": "Admissible\n(endorsed)", "silent": "Silent",
        "advisory": "Advisory\n(discredited)", "prohibited": "Prohibited\n(banned)"}
cnt = coded.detector_admissibility.value_counts()
vals = [int(cnt.get(k, 0)) for k in order]
colors = ["#b2182b", "#ef8a62", "#67a9cf", "#2166ac"]
a1.bar(range(len(order)), vals, color=colors)
a1.set_xticks(range(len(order)))
a1.set_xticklabels([disp[k] for k in order], fontsize=9)
for i, v in enumerate(vals):
    a1.text(i, v + 0.5, str(v), ha="center", fontsize=9)
a1.set_ylabel("Flagship universities (of 50)")
a1.set_title("(a) Is detector output usable as evidence?", fontsize=10)
a1.spines[["top", "right"]].set_visible(False)

# (b) the vacuum and the floors that clear it
ban = (coded.detector_admissibility == "prohibited").sum()
expl = ((coded.l2_protection == "explicit") & (coded.detector_admissibility != "prohibited")).sum()
corr = ((coded.burden_of_proof == "institution") & (coded.l2_protection != "explicit")
        & (coded.detector_admissibility != "prohibited")).sum()
vac = len(coded) - ban - expl - corr
seg = [("Governance\nvacuum", vac, "#b2182b"), ("Binding ban", ban, "#2166ac"),
       ("Explicit L2\nprotection", expl, "#2166ac"), ("Corroboration\nrequired", corr, "#2166ac")]
a2.bar(range(len(seg)), [s[1] for s in seg], color=[s[2] for s in seg])
a2.set_xticks(range(len(seg)))
a2.set_xticklabels([s[0] for s in seg], fontsize=9)
for i, s in enumerate(seg):
    a2.text(i, s[1] + 0.5, str(s[1]), ha="center", fontsize=9)
a2.set_ylabel("Flagship universities (of 50)")
a2.set_title("(b) The vacuum, and the floors that clear it", fontsize=10)
a2.spines[["top", "right"]].set_visible(False)
save(fig, "j6_figure2")


# ---------- Figure 3: exposure does not predict protection ----------
ter = pol[pol.metric == "vacuum_rate_by_intl_tercile"].set_index("dimension")
order3 = ["low", "mid", "high"]
rates = [float(ter.loc[t, "share"]) * 100 for t in order3]
sp = pol[pol.metric == "spearman_intl_vs_vacuumindex"].set_index("dimension")["share"]
fig, ax = plt.subplots(figsize=(6.2, 4.2))
ax.bar(range(3), rates, color=["#fddbc7", "#ef8a62", "#b2182b"], width=0.6)
for i, v in enumerate(rates):
    ax.text(i, v + 1.2, f"{v:.0f}%", ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(range(3))
ax.set_xticklabels(["Low\nintl. enrollment", "Mid", "High\nintl. enrollment"], fontsize=9.5)
ax.set_ylabel("In the governance vacuum (%)")
ax.set_ylim(0, 100)
ax.set_title("Protection does not track exposure\n"
             f"(Spearman intl. share vs vacuum index = {sp.get('rho')}, p = {sp.get('p')})",
             fontsize=10.5)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "j6_figure3")

print("Wrote j6_figure{1,2,3}.{pdf,png,tiff} to", os.path.normpath(OUT))
