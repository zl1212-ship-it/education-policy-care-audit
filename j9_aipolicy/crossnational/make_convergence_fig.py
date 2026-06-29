"""Figure: convergence of AI-policy text over event time, within-system and
cross-system, 4-system panel. Flat pre-shock baseline anchors the post-shock rise."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

XN = Path(__file__).parent
OUT = XN  # write alongside this script
d = pd.read_csv(XN / "results_convergence_over_time.csv")

fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.axvline(0, color="0.6", lw=1, ls="--")
ax.text(0.15, ax.get_ylim()[1], "", fontsize=8)
ax.plot(d["event_q"], d["within_cos"], "-o", ms=4, color="#1f4e79", label="Within-system")
ax.plot(d["event_q"], d["cross_cos"], "-s", ms=4, color="#c55a11", label="Cross-system")
pre = d[d["event_q"] < 0]["all_cos"].mean()
ax.axhline(pre, color="0.7", lw=0.8, ls=":")
ax.text(-7, pre + 0.002, f"pre-shock baseline ({pre:.2f})", fontsize=7.5, color="0.4")
ax.set_xlabel("Event time (quarters from the ChatGPT shock)")
ax.set_ylabel("Mean pairwise cosine similarity of AI text")
ax.set_xticks(range(-7, 9, 2))
ax.legend(frameon=False, fontsize=9, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_convergence.pdf")
fig.savefig(OUT / "fig_convergence.png", dpi=200)
print("wrote fig_convergence.pdf/.png to", OUT)
