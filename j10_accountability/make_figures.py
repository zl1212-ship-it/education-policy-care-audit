"""Figures for the manuscript (PNG + PDF), written to the private paper tree.

  fig_weight_instability - how often each baseline-identified school keeps the label
                           across the weight sweep (the label is formula-made)
  fig_poverty_gradient   - identification prevalence by school poverty decile
  fig_rdd_outcome        - binned RDD plot at the identification cutoff (no jump)
  fig_rdd_density        - running-variable density at the cutoff (no sorting)

Run:  python3 make_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = Path(__file__).parent
INST = HERE / "data" / "label_instability.csv"
PANEL = HERE / "data" / "rdd_panel.csv"
OUTDIR = HERE.parent / "paper" / "blinded-manuscript" / "J10"
OUTDIR.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 11, "figure.dpi": 120, "axes.grid": True,
                     "grid.alpha": 0.3})


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  {name}.png / .pdf")


def fig_weight_instability():
    d = pd.read_csv(INST)
    base = d[d["identified_baseline"] == 1]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(base["identify_freq"], bins=20, color="#4c72b0", edgecolor="white")
    ax.axvline(1.0, color="k", ls="--", lw=1)
    flip = base["flip"].mean()
    ax.set_xlabel("share of weight draws that identify the school")
    ax.set_ylabel("baseline-identified schools")
    ax.set_title(f"Label instability across weight choices\n"
                 f"{flip:.0%} of identified schools are not identified under some weights")
    save(fig, "fig_weight_instability")


def fig_poverty_gradient():
    d = pd.read_csv(INST)
    by = d.groupby("poverty_decile")["identified_baseline"].mean()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(by.index, by.values * 100, color="#c44e52", edgecolor="white")
    ax.set_xlabel("school poverty decile (1 = lowest, 10 = highest)")
    ax.set_ylabel("identified for support (%)")
    ax.set_title("The lowest-performing label rises with school poverty")
    ax.set_xticks(range(1, 11))
    save(fig, "fig_poverty_gradient")


def _binscatter(ax, df, outcome, h=1.0, nbins=20):
    d = df.loc[df["running"].between(-h, h), ["running", outcome]].dropna()
    edges = np.linspace(-h, h, nbins + 1)
    d["b"] = pd.cut(d["running"], edges)
    g = d.groupby("b", observed=True).agg(x=("running", "mean"),
                                          y=(outcome, "mean")).dropna()
    ax.scatter(g["x"], g["y"], s=18, color="#555", zorder=3)
    for side, m in (("L", d["running"] < 0), ("R", d["running"] >= 0)):
        s = d[m]
        w = 1 - s["running"].abs() / h
        X = sm.add_constant(s["running"])
        fit = sm.WLS(s[outcome], X, weights=w).fit()
        xs = np.linspace(s["running"].min(), 0 if side == "L" else s["running"].max(), 50)
        ax.plot(xs, fit.params[0] + fit.params[1] * xs,
                color="#4c72b0" if side == "L" else "#c44e52", lw=2)
    ax.axvline(0, color="k", ls="--", lw=1)


def fig_rdd_outcome():
    d = pd.read_csv(PANEL)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    _binscatter(axes[0], d, "got_funds")
    axes[0].set_title("Improvement funding")
    axes[0].set_ylabel("received 1003 funds (share)")
    _binscatter(axes[1], d, "next_score")
    axes[1].set_title("Next-cycle accountability score")
    axes[1].set_ylabel("next-cycle score")
    for ax in axes:
        ax.set_xlabel("accountability index, centered at the identification cutoff")
    fig.suptitle("At the identification line, crossing it does not jump the consequences "
                 "(left of dashed line = identified)")
    fig.tight_layout()
    save(fig, "fig_rdd_outcome")


def fig_rdd_density():
    d = pd.read_csv(PANEL)
    r = d.loc[d["running"].between(-2, 2), "running"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(r, bins=30, color="#55a868", edgecolor="white")
    ax.axvline(0, color="k", ls="--", lw=1)
    ax.set_xlabel("accountability index, centered at the identification cutoff")
    ax.set_ylabel("schools")
    ax.set_title("No bunching at the cutoff (running-variable density)")
    save(fig, "fig_rdd_density")


def main():
    print(f"writing figures -> {OUTDIR}")
    fig_weight_instability()
    fig_poverty_gradient()
    fig_rdd_outcome()
    fig_rdd_density()


if __name__ == "__main__":
    main()
