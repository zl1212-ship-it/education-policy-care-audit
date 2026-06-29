"""J9 figures.

  Figure 1: event-study coefficients - the differential effect of the ChatGPT
            shock by exposure, by event quarter, for the two primary outcomes
            (AI-governance intensity and net restrictiveness), 95% CI, with the
            shock and the omitted reference quarter marked.
  Figure 2: raw trends - mean AI-governance intensity over event time by
            exposure tercile (the visual parallel-trends-then-divergence).
  Figure 3: descriptive governance - (a) endpoint provision prevalence,
            restrictive versus procedural; (b) endpoint regime typology counts.

Inputs : data/results_event_study.csv, data/panel.csv, data/results_descriptive.csv
Outputs: ../paper/blinded-manuscript/J9/j9_figure{1,2,3}.{pdf,png}
Run after analyze_event_study.py and analyze_descriptive.py.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "paper", "blinded-manuscript", "J9")
os.makedirs(OUT, exist_ok=True)  # gitignored on a fresh clone
plt.rcParams.update({"font.size": 11, "font.family": "serif"})

RED, BLUE, GREY = "#b2182b", "#2166ac", "0.35"
RESTRICTIVE = ["prohibition", "detector_surveillance", "misconduct_framing", "sanction"]
PROCEDURAL = ["permitted_use", "disclosure", "appeal", "l2_protection"]
PROV_LABEL = {"prohibition": "Prohibition", "detector_surveillance": "Detector use",
              "misconduct_framing": "Misconduct framing", "sanction": "Sanction",
              "permitted_use": "Permitted use", "disclosure": "Disclosure route",
              "appeal": "Appeal pathway", "l2_protection": "Multilingual protection"}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


es = pd.read_csv(os.path.join(DATA, "results_event_study.csv"))
panel = pd.read_csv(os.path.join(DATA, "panel.csv"))
desc = pd.read_csv(os.path.join(DATA, "results_descriptive.csv"))


# ---------- Figure 1: event-study coefficients ----------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
specs = [("ai_governance_intensity", "AI-governance intensity (0-8)", "AI-governance intensity"),
         ("net_restrictiveness", "Net restrictiveness ($-$4 to +4)", "Net restrictiveness")]
for ax, (outcome, ylab, title) in zip(axes, specs):
    g = es[(es["outcome"] == outcome) & (es["kind"] == "event_coef")].sort_values("event_q")
    x = g["event_q"].to_numpy()
    y = g["coef"].to_numpy()
    # pre-shock coefficients are mechanically ~0 (AI provisions absent by construction);
    # their cluster-robust CIs are degenerate, so draw them without error bars
    lo = g["ci_lo"].fillna(g["coef"]).to_numpy()
    hi = g["ci_hi"].fillna(g["coef"]).to_numpy()
    y = np.where(np.abs(y) < 1e-9, 0.0, y)
    ax.axhline(0, color="0.6", lw=0.8)
    ax.axvline(-0.5, color=RED, lw=1.0, ls="--", label="ChatGPT shock")
    ax.errorbar(x, y, yerr=[np.clip(y - lo, 0, None), np.clip(hi - y, 0, None)],
                fmt="o-", color=BLUE, ecolor="0.55", capsize=2, ms=4, lw=1.0)
    ax.set_xlabel("Quarters from shock (2022Q4 = 0)")
    ax.set_ylabel(f"Per-SD-exposure effect\non {ylab}", fontsize=9.5)
    ax.set_title(title, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
axes[0].legend(frameon=False, fontsize=9)
save(fig, "j9_figure1")


# ---------- Figure 2: raw trends by exposure tercile ----------
inst = panel.drop_duplicates("unitid")[["unitid", "intl_share"]].copy()
inst["terc"] = pd.qcut(inst["intl_share"], 3, labels=["Low", "Mid", "High"],
                       duplicates="drop")
p2 = panel.merge(inst[["unitid", "terc"]], on="unitid")
fig, ax = plt.subplots(figsize=(7.6, 4.4))
colors = {"Low": BLUE, "Mid": "0.5", "High": RED}
for t in ["Low", "Mid", "High"]:
    sub = p2[p2["terc"] == t].groupby("event_q")["ai_governance_intensity"].mean()
    if len(sub):
        ax.plot(sub.index, sub.values, "o-", color=colors[t], ms=4, lw=1.3,
                label=f"{t} exposure")
ax.axvline(-0.5, color=RED, lw=1.0, ls="--")
ax.text(-0.4, ax.get_ylim()[1] * 0.95, "ChatGPT shock", color=RED, fontsize=9)
ax.set_xlabel("Quarters from shock (2022Q4 = 0)")
ax.set_ylabel("Mean AI-governance intensity (0-8)")
ax.set_title("Integrity-policy AI content over time, by exposure tercile", fontsize=10.5)
ax.legend(frameon=False, fontsize=9.5)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "j9_figure2")


# ---------- Figure 3: descriptive governance ----------
end = desc[desc["section"] == "endpoint"].set_index("metric")["value"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4),
                             gridspec_kw={"width_ratios": [1.4, 1]})
# sort within each family by endpoint prevalence (descending), restrictive then procedural
rate = lambda c: float(end.get(c + "_rate", np.nan)) * 100
restr = sorted(RESTRICTIVE, key=rate, reverse=True)
proc = sorted(PROCEDURAL, key=rate, reverse=True)
provs = restr + proc
rates = [rate(c) for c in provs]
cols = [RED] * len(restr) + [BLUE] * len(proc)
ypos = np.arange(len(provs))
a1.barh(ypos, rates, color=cols)
a1.set_yticks(ypos)
a1.set_yticklabels([PROV_LABEL[c] for c in provs], fontsize=9)
a1.invert_yaxis()
a1.set_xlabel("Endpoint prevalence (% of institutions)")
a1.set_title("(a) Provisions at the endpoint", fontsize=10)
a1.spines[["top", "right"]].set_visible(False)
from matplotlib.patches import Patch
a1.legend(handles=[Patch(color=RED, label="Restrictive"),
                   Patch(color=BLUE, label="Procedural")],
          frameon=False, fontsize=8.5, loc="lower right")

reg = desc[(desc["section"] == "regime") & (desc["group"] == "all")]
order = ["Silent", "Restrictive-leaning", "Mixed", "Procedural-leaning"]
reg = reg[reg["metric"].isin(order)].set_index("metric")["value"].reindex(order).dropna()
a2.bar(range(len(reg)), reg.values,
       color=[GREY, RED, "#999999", BLUE][:len(reg)])
a2.set_xticks(range(len(reg)))
a2.set_xticklabels(reg.index, rotation=30, ha="right", fontsize=8.5)
a2.set_ylabel("Institutions")
a2.set_title("(b) Endpoint regime", fontsize=10)
a2.spines[["top", "right"]].set_visible(False)
save(fig, "j9_figure3")


# ---------- Figure 4: convergence of AI policy language ----------
conv = pd.read_csv(os.path.join(DATA, "results_convergence.csv"))
conv = conv[conv["mean_cosine"].notna()]
fig, ax = plt.subplots(figsize=(7.6, 4.4))
ax.axvline(-0.5, color=RED, lw=1.0, ls="--", label="ChatGPT shock")
ax.plot(conv["event_q"], conv["mean_cosine"], "o-", color=BLUE, ms=4, lw=1.3)
ax.set_xlabel("Quarters from shock (2022Q4 = 0)")
ax.set_ylabel("Mean pairwise TF-IDF cosine similarity")
ax.set_title("Convergence of AI policy language across institutions", fontsize=10.5)
ax.legend(frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "j9_figure4")

print("Wrote j9_figure{1,2,3,4}.{pdf,png} to", os.path.normpath(OUT))
