"""Figures for the revised manuscript, from the symmetric seed design.
Figure 1: convergence over event time (rung S7: boilerplate-stripped, normalized, strict AI terms),
within- and cross-system, from the first post-shock quarter with documents, n per quarter annotated.
Figure 2: US differential-exposure event study on the seed panel (clean strict scores).
Figure 3: mean AI-governance intensity by quarter and exposure tercile (seed panel)."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
OUT = AN / "figures"; OUT.mkdir(exist_ok=True)
RUNG = sys.argv[1] if len(sys.argv) > 1 else "S7"

d = pd.read_csv(AN / "seed_convergence_series.csv"); d = d[(d.rung == RUNG) & (d.event_q >= 1)]
g = pd.read_csv(AN / "seed_convergence_groups.csv"); g = g[(g.rung == RUNG) & (g.event_q >= 1)]
fig, ax = plt.subplots(figsize=(6.6, 4.2))
styles = {"US-US": ("#1f4e79", "-o"), "Commonwealth same country": ("#2e7d32", "-s"), "Commonwealth cross country": ("#7cb342", "--^"), "US-Commonwealth": ("#c55a11", "--d")}
for grp, (col, st) in styles.items():
    gg = g[(g.group == grp) & (g.n_pairs >= 10)].sort_values("event_q")  # points with fewer than 10 pairs are not drawn
    ax.plot(gg["event_q"], gg["mean_cos"], st, ms=4, color=col, label=grp, lw=1.3)
for x, n in zip(d["event_q"], d["n_inst"]):
    ax.annotate(str(int(n)), (x, 0.004), textcoords="offset points", xytext=(0, 0), ha="center", fontsize=6.5, color="0.4")
ax.text(1, 0.012, "institutions with AI text:", fontsize=6.5, color="0.4", ha="left")
ax.set_xlabel("Quarters after the ChatGPT shock (2022Q4 = 0)")
ax.set_ylabel("Mean pairwise cosine similarity of AI-scoped text")
ax.set_xticks(range(1, int(d["event_q"].max()) + 1, 2))
ax.set_ylim(0, max(g["mean_cos"].max(), 0.2) * 1.15)
ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "fig_convergence_r1.pdf"); fig.savefig(OUT / "fig_convergence_r1.png", dpi=200)

# supplement: balanced pool (institutions carrying AI text in every quarter from 5 onward)
bp = AN / "seed_convergence_balanced.csv"
if bp.exists():
    b = pd.read_csv(bp); b = b[(b.rung == RUNG)]
    if len(b):
        fig, ax = plt.subplots(figsize=(6.6, 4.2))
        for grp, (col, st) in styles.items():
            gg = b[(b.group == grp) & (b.n_pairs >= 10)].sort_values("event_q")
            ax.plot(gg["event_q"], gg["mean_cos"], st, ms=4, color=col, label=grp, lw=1.3)
        ax.set_xlabel("Quarters after the ChatGPT shock (2022Q4 = 0)"); ax.set_ylabel("Mean pairwise cosine similarity, balanced pool")
        ax.set_title(f"Balanced pool of {int(b.n_inst.iloc[0])} institutions with AI text in every quarter from 5 on", fontsize=9)
        ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2); ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(); fig.savefig(OUT / "fig_convergence_balanced_r1.pdf"); fig.savefig(OUT / "fig_convergence_balanced_r1.png", dpi=200)

res = pd.read_csv(AN / "results_event_study_seed_clean_strict.csv")
ev = res[(res.outcome == "net_restrictiveness") & (res.kind == "event_coef")].sort_values("event_q")
fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.axhline(0, color="0.6", lw=0.8); ax.axvline(-0.5, color="0.6", lw=1, ls="--")
ax.errorbar(ev["event_q"], ev["coef"], yerr=[ev["coef"] - ev["ci_lo"], ev["ci_hi"] - ev["coef"]], fmt="o", ms=4, color="#1f4e79", ecolor="#1f4e79", elinewidth=0.9, capsize=2)
ax.set_xlabel("Quarters from the ChatGPT shock (2022Q4 = 0; reference quarter = -1)")
ax.set_ylabel("Exposure x quarter coefficient, net restrictiveness")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "fig_event_r1.pdf"); fig.savefig(OUT / "fig_event_r1.png", dpi=200)

p = pd.read_csv(AN / "seed_panel_us_clean_strict.csv", dtype={"unitid": str})
inst = p.drop_duplicates("unitid")[["unitid", "intl_share"]].dropna()
inst["tercile"] = pd.qcut(inst["intl_share"], 3, labels=["Low exposure", "Middle", "High exposure"])
pp = p.merge(inst[["unitid", "tercile"]], on="unitid")
g = pp.groupby(["event_q", "tercile"])["ai_governance_intensity"].mean().unstack()
fig, ax = plt.subplots(figsize=(6.4, 4.0))
for col, c in zip(g.columns, ["#7f7f7f", "#c55a11", "#1f4e79"]):
    ax.plot(g.index, g[col], "-o", ms=3.5, label=str(col), color=c)
ax.axvline(0, color="0.6", lw=1, ls="--")
ax.set_xlabel("Quarters from the ChatGPT shock (2022Q4 = 0)"); ax.set_ylabel("Mean AI-governance intensity (0 to 8)")
ax.legend(frameon=False, fontsize=9, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "fig_trend_r1.pdf"); fig.savefig(OUT / "fig_trend_r1.png", dpi=200)
print("figures written to", OUT)
