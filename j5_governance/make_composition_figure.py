"""Figure 4: educator background per state board, colored by the state's educator RULE.
Reproducible from data/board_members_2026.csv + data/board_composition_rules_2026.csv.
Emits j5_figure4.{png,pdf} to the manuscript folder."""
import os
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
OUT  = os.path.join(HERE, "..", "paper", "blinded-manuscript", "J5")
os.makedirs(OUT, exist_ok=True)  # gitignored on a fresh clone

mem = pd.read_csv(os.path.join(DATA, "board_members_2026.csv"))
mem = mem[mem.is_educator.isin([0, 1]) & ~mem.role.isin(["student", "ex-officio"])].copy()
mem.is_educator = mem.is_educator.astype(int)
rules = pd.read_csv(os.path.join(DATA, "board_composition_rules_2026.csv"))

bl = mem.groupby("state_abbr").is_educator.agg(n="count", e="sum").reset_index()
bl["share"] = bl.e / bl.n * 100
bl = bl.merge(rules[["state_abbr", "educator_mandate", "educator_bar"]], on="state_abbr", how="left")
bl["rule"] = bl.apply(lambda r: "Mandates educators" if r.educator_mandate == 1
                      else ("Bars current educators" if r.educator_bar == 1 else "No rule"), axis=1)
bl = bl.sort_values("share")
col = {"Mandates educators": "#2c7a3f", "Bars current educators": "#b03030", "No rule": "#8a8a8a"}

fig, ax = plt.subplots(figsize=(7.2, 9))
ax.barh(bl.state_abbr, bl.share, color=[col[r] for r in bl.rule], edgecolor="white", height=0.75)
ax.axvline(bl.share.mean(), ls="--", color="black", lw=1)
ax.text(bl.share.mean() + 1.5, 0.3, f"mean {bl.share.mean():.0f}%", fontsize=9, rotation=90, va="bottom")
ax.set_xlabel("Share of identified members with an education background (%)", fontsize=10)
ax.set_xlim(0, 100); ax.set_ylabel(""); ax.tick_params(labelsize=7.5)
ax.set_title("Educator representation on state boards is bimodal and rule-driven", fontsize=11)
ax.legend(handles=[Patch(color=col[k], label=k) for k in col], fontsize=8, loc="lower right", frameon=False)
ax.text(0.5, -0.058, "Partial census; occupation identified for ~36% of seats (median per board); OH and MT not shown. "
        "Mandate boards 80% vs 45% (p=0.003).", transform=ax.transAxes, ha="center", fontsize=7, color="#555")
plt.tight_layout()
for ext in ("png", "pdf"):
    plt.savefig(os.path.join(OUT, f"j5_figure4.{ext}"), dpi=300, bbox_inches="tight")
print(f"wrote j5_figure4.png/pdf to {os.path.normpath(OUT)} ; boards plotted: {len(bl)}")
