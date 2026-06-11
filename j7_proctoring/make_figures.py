"""J7 figures.

  Figure 1: detection layer -- "no face" miss rate by perceived race (Black vs
            White) across the exposure sweep, one panel per open detector.
  Figure 2: the tone gradient -- Haar cascade miss rate across the six ITA tone
            bins at native exposure and at the dimmest condition.
  Figure 3: the gate vs the matcher -- group failure-rate ratio across exposure:
            detection (Black vs White miss ratio, three detectors that leave the
            floor) against 1:1 verification (T3/T1 FNMR ratio, both cascades).
            The gate diverges as the light dims; the matcher stays at parity.

Detector names in the figures match the manuscript text exactly: Haar, YuNet,
MTCNN, MediaPipe; the verification cascades are "MTCNN + InceptionResnet" and
"YuNet + SFace".

Inputs : data/results_summary.csv, data/verification_results.csv
Outputs: ../paper/blinded-manuscript/j7_figure{1,2,3}.{pdf,png,tiff}
Run after analyze_detection.py and analyze_verification.py.
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

DARK, LIGHT = "#b2182b", "#2166ac"  # darker-skin series (red), lighter (blue)
EXPOSURES = [1.0, 0.5, 0.35, 0.25, 0.15]
XLAB = [f"{e:.2f}" for e in EXPOSURES]
TONE_ORDER = ["very_light", "light", "intermediate", "tan", "brown", "dark"]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200)
    fig.savefig(os.path.join(OUT, name + ".tiff"), dpi=600,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


det = pd.read_csv(os.path.join(DATA, "results_summary.csv"))
ver = pd.read_csv(os.path.join(DATA, "verification_results.csv"))


def race_series(detector, group):
    r = det[(det["kind"] == "rate") & (det["sample"] == "all")
            & (det["detector"] == detector) & (det["stratifier"] == "race")
            & (det["group"] == group)].set_index("exposure")
    r = r.reindex(EXPOSURES)
    return (r["miss_rate"].values * 100, r["wilson_lo"].values * 100,
            r["wilson_hi"].values * 100)


# ---- Figure 1: miss rate by race across the exposure sweep, per detector ----
PANELS = [("haar", "Haar cascade (legacy webcam)"),
          ("yunet", "YuNet (lightweight production)"),
          ("mtcnn", "MTCNN (deep cascade)"),
          ("mediapipe", "MediaPipe BlazeFace (on device)")]
x = np.arange(len(EXPOSURES))
fig, axes = plt.subplots(2, 2, figsize=(8.2, 6.2), sharex=True)
for ax, (d, title) in zip(axes.ravel(), PANELS):
    for grp, col, lab in (("Black", DARK, "Black-labeled (n=1,556)"),
                          ("White", LIGHT, "White-labeled (n=2,085)")):
        y, lo, hi = race_series(d, grp)
        ax.plot(x, y, "o-", color=col, ms=4, lw=1.5, label=lab)
        ax.fill_between(x, lo, hi, color=col, alpha=0.18, lw=0)
    ax.set_title(title, fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(XLAB)
    ax.spines[["top", "right"]].set_visible(False)
for ax in axes[1]:
    ax.set_xlabel("Exposure (fraction of native illumination)")
for ax in axes[:, 0]:
    ax.set_ylabel('"No face" rate (%)')
axes[0, 0].legend(frameon=False, fontsize=9)
fig.suptitle("Face detection failure on single-face images, by perceived race, "
             "as the light dims", fontsize=11, y=0.995)
save(fig, "j7_figure1")

# ---- Figure 2: Haar miss rate across the six tone bins ----
fig, ax = plt.subplots(figsize=(8, 4.2))
w = 0.4
for off, exp, col, lab in ((-w / 2, 1.0, "0.55", "Native exposure (1.00)"),
                           (w / 2, 0.15, DARK, "Dim room (0.15)")):
    r = det[(det["kind"] == "rate") & (det["sample"] == "all")
            & (det["detector"] == "haar") & (det["stratifier"] == "tone_bin")
            & (det["exposure"] == exp)].set_index("group").reindex(TONE_ORDER)
    xx = np.arange(len(TONE_ORDER)) + off
    ax.bar(xx, r["miss_rate"] * 100, w, color=col, label=lab)
    err = np.vstack([(r["miss_rate"] - r["wilson_lo"]) * 100,
                     (r["wilson_hi"] - r["miss_rate"]) * 100])
    ax.errorbar(xx, r["miss_rate"] * 100, yerr=err, fmt="none",
                ecolor="0.25", lw=0.9, capsize=2)
ax.set_xticks(np.arange(len(TONE_ORDER)))
ax.set_xticklabels([t.replace("_", " ") for t in TONE_ORDER])
ax.set_xlabel("Skin tone bin (ITA, lightest to darkest)")
ax.set_ylabel('"No face" rate (%)')
ax.set_title("Haar cascade: the tone gradient at native exposure and in a dim room",
             fontsize=10.5)
ax.legend(frameon=False, fontsize=9.5)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "j7_figure2")

# ---- Figure 3: failure-rate ratio across exposure, gate vs matcher ----
fig, (axL, axR) = plt.subplots(1, 2, figsize=(8.4, 4.0), sharey=True)
DET_LINES = [("haar", "o-", "#b2182b", "Haar"),
             ("yunet", "s-", "#ef8a62", "YuNet"),
             ("mtcnn", "^-", "#67001f", "MTCNN")]
for d, st, col, lab in DET_LINES:
    c = (det[(det["kind"] == "contrast") & (det["sample"] == "all")
             & (det["detector"] == d) & (det["stratifier"] == "race")]
         .set_index("exposure").reindex(EXPOSURES))
    axL.plot(x, c["ratio"], st, color=col, ms=4.5, lw=1.5, label=lab)
VER_LINES = [("facenet", "o-", "#2166ac", "MTCNN + InceptionResnet"),
             ("sface", "s-", "#67a9cf", "YuNet + SFace")]
for v, st, col, lab in VER_LINES:
    c = (ver[(ver["kind"] == "contrast") & (ver["point"] == "fmr1pct")
             & (ver["verifier"] == v) & (ver["outcome"] == "fnmr")]
         .set_index("exposure").reindex(EXPOSURES))
    axR.plot(x, c["ratio"], st, color=col, ms=4.5, lw=1.5, label=lab)
for ax, title in ((axL, "Detection gate\n(Black vs White miss ratio, FairFace)"),
                  (axR, "Identity matcher\n(darkest vs lightest tercile FNMR ratio, LFW)")):
    ax.axhline(1.0, color="0.6", lw=0.9, ls="--")
    ax.set_xticks(x)
    ax.set_xticklabels(XLAB)
    ax.set_xlabel("Exposure")
    ax.set_title(title, fontsize=10)
    ax.legend(frameon=False, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
axL.set_ylabel("Group failure rate ratio")
fig.suptitle("The gap lives at the detection gate, not the matcher", fontsize=11)
save(fig, "j7_figure3")

print(f"figures written -> {os.path.abspath(OUT)}/j7_figure{{1,2,3}}.{{pdf,png,tiff}}")
