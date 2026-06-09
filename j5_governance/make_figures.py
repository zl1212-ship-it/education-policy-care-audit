"""
J5 figures (built from data/governance_panel.csv and data/results_summary.csv):
  Figure 1: the accountability-representation gap -- Authority Index vs Representation Index
            for all 47 state boards, by selection regime, with the 45-degree parity line.
  Figure 2: the asymmetry -- share of boards holding each form of AUTHORITY vs share offering
            each REPRESENTATION mechanism.
  Figure 3: (a) enrollment-weighted share of students by board regime (who cannot elect their
            board); (b) the demographic null -- representation does not track the share of
            students of color.
Outputs: ../paper/blinded-manuscript/j5_figure{1,2,3}.{pdf,png}
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

df = pd.read_csv(os.path.join(DATA, "governance_panel.csv"))
b = df[df.board_exists == 1].copy()
res = dict(zip(pd.read_csv(os.path.join(DATA, "results_summary.csv")).metric,
               pd.read_csv(os.path.join(DATA, "results_summary.csv")).value))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200)
    plt.close(fig)


# ---------- Figure 1: authority vs representation ----------
MARK = {"governor": ("o", "0.35", "Governor-appointed"),
        "legislative": ("s", "0.0", "Legislature-appointed"),
        "elected": ("^", "0.0", "Publicly elected"),
        "hybrid": ("D", "0.55", "Hybrid")}
fig, ax = plt.subplots(figsize=(7, 5.6))
# quadrant plot: midpoint crosshairs (no diagonal; the two indices are not subtracted)
ax.axvline(0.5, color="0.6", linewidth=1, linestyle="--", zorder=1)
ax.axhline(0.5, color="0.6", linewidth=1, linestyle="--", zorder=1)
ax.fill_between([-0.03, 0.5], 0.5, 1.06, color="0.92", zorder=0)   # high-authority, low-representation
n_q = int(((b.auth_index > 0.5) & (b.rep_index < 0.5)).sum())
jit = np.random.default_rng(3).normal(0, 0.006, len(b))
for reg, (mk, col, lab) in MARK.items():
    s = b[b.board_regime == reg]
    ax.scatter(s.rep_index + jit[s.index.map(lambda i: list(b.index).index(i))],
               s.auth_index, marker=mk, facecolor=("none" if reg in ("elected",) else col),
               edgecolor=col, s=55, linewidths=1.3, label=lab, zorder=3)
for st, dx, dy in [("New York", 0.012, -0.03), ("South Carolina", 0.012, 0.015),
                   ("Missouri", 0.012, 0.0), ("Texas", 0.012, 0.0),
                   ("Washington", 0.012, -0.01)]:
    r = b[b.state == st].iloc[0]
    ax.annotate(st, (r.rep_index, r.auth_index), xytext=(r.rep_index + dx, r.auth_index + dy),
                fontsize=8.5, color="0.2")
ax.text(0.485, 0.55, f"high authority,\nlow representation\n({n_q} of {len(b)} boards)",
        ha="right", va="bottom", fontsize=9.5, color="0.4", style="italic")
ax.set_xlabel("Representation Index  (directly elected, voting student, voting teacher)")
ax.set_ylabel("Authority Index  (standards, licensure, constitutional entrenchment)")
ax.set_xlim(-0.03, 1.03); ax.set_ylim(-0.03, 1.08)
ax.legend(loc="lower right", frameon=False, fontsize=9)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_title("Figure 1. Authority versus representation across 47 state boards", fontsize=11)
save(fig, "j5_figure1")

# ---------- Figure 2: authority vs representation asymmetry ----------
fig, ax = plt.subplots(figsize=(7.6, 4.4))
pct_lic_direct = (b.auth_licensure == "SBE").mean() * 100   # direct board control only (excl. PSC)
rep_items = [("Directly elected\nby the public", res["pct_boards_is_elected"]),
             ("Voting teacher\nmember", res["pct_boards_teacher_voting"]),
             ("Voting student\nmember", res["pct_boards_student_voting"])]
auth_items = [("Adopts academic\nstandards", res["pct_boards_set_standards"]),
              ("Directly controls\nteacher licensure", pct_lic_direct),
              ("Constitutionally\nentrenched", res["pct_boards_constitutional"])]
labels = [x[0] for x in auth_items] + [x[0] for x in rep_items]
vals = [x[1] for x in auth_items] + [x[1] for x in rep_items]
colors = ["0.25"] * 3 + ["0.7"] * 3
y = np.arange(len(labels))[::-1]
ax.barh(y, vals, color=colors, edgecolor="black", linewidth=0.6)
for yi, v in zip(y, vals):
    ax.text(v + 1.5, yi, f"{v:.0f}%", va="center", fontsize=9)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9)
ax.axhline(2.5, color="black", linewidth=0.7)
ax.text(62, 3.0, "AUTHORITY HELD", ha="left", fontsize=9.5, color="0.25", fontweight="bold")
ax.text(40, 1.0, "REPRESENTATION OFFERED", ha="left", fontsize=9.5, color="0.5", fontweight="bold")
ax.set_xlim(0, 105); ax.set_xlabel("Share of 47 state boards (%)")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_title("Figure 2. Boards hold pervasive authority but offer scarce representation", fontsize=11)
save(fig, "j5_figure2")

# ---------- Figure 3: exposure + demographic null ----------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
order = ["elected", "hybrid", "governor", "legislative", "none"]
names = {"elected": "Publicly\nelected", "hybrid": "Hybrid", "governor": "Governor-\nappointed",
         "legislative": "Legislature-\nappointed", "none": "No state\nboard"}
sh = df.groupby("board_regime").enrollment_2021.sum() / df.enrollment_2021.sum() * 100
vals = [sh.get(o, 0) for o in order]
cols = ["0.2"] + ["0.55"] * 4
ax[0].bar(range(len(order)), vals, color=cols, edgecolor="black", linewidth=0.6)
for i, v in enumerate(vals):
    ax[0].text(i, v + 0.8, f"{v:.1f}%", ha="center", fontsize=9)
ax[0].set_xticks(range(len(order))); ax[0].set_xticklabels([names[o] for o in order], fontsize=8.5)
ax[0].set_ylabel("Share of U.S. public-school students (%)"); ax[0].set_ylim(0, 70)
ax[0].annotate(f"{res['pct_students_no_elected_board']:.0f}% of students cannot\ndirectly elect their board",
               (3.0, 45), fontsize=9.5, color="0.2", ha="center")
ax[0].spines["top"].set_visible(False); ax[0].spines["right"].set_visible(False)
ax[0].set_title("(a) Who governs the governed", fontsize=10.5)

ax[1].scatter(b.pct_students_of_color, b.rep_index, s=45, facecolor="0.6",
              edgecolor="black", linewidths=0.6)
z = np.polyfit(b.pct_students_of_color, b.rep_index, 1)
xs = np.array([b.pct_students_of_color.min(), b.pct_students_of_color.max()])
ax[1].plot(xs, np.polyval(z, xs), color="black", linewidth=1.3, linestyle="--")
ax[1].set_xlabel("Students of color (% of state enrollment)")
ax[1].set_ylabel("Representation Index")
ax[1].text(0.04, 0.92, f"slope n.s. (p = {res['ols_soc_p']:.2f})", transform=ax[1].transAxes,
           fontsize=9.5, color="0.2")
ax[1].spines["top"].set_visible(False); ax[1].spines["right"].set_visible(False)
ax[1].set_title("(b) Representation does not track the demography of the governed", fontsize=10.5)
save(fig, "j5_figure3")

# ---------- Figure 4: the algorithmic accountability layer ----------
order = [("A-F", "A-F letter grade"), ("Star", "1-5 star"), ("Index", "Numeric index"),
         ("Descriptive", "Descriptive labels"), ("FederalTiers", "Federal tiers only"),
         ("Dashboard", "Dashboard / none")]
cnt = b.rating_category.value_counts()
vals = [int(cnt.get(k, 0)) for k, _ in order]
labs = [lab for _, lab in order]
algo = [True, True, True, False, False, False]
fig, ax = plt.subplots(figsize=(7.4, 4.3))
y = np.arange(len(order))[::-1]
ax.barh(y, vals, color=["0.25" if a else "0.7" for a in algo], edgecolor="black", linewidth=0.6)
for yi, v in zip(y, vals):
    ax.text(v + 0.2, yi, str(v), va="center", fontsize=9)
ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=9.5)
n_algo = sum(v for v, a in zip(vals, algo) if a)
ax.text(0.985, 0.95, f"formula-driven grade:\n{n_algo} of {len(b)} boards ({n_algo/len(b)*100:.0f}%)",
        transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color="0.2", fontweight="bold")
ax.text(0.985, 0.74, f"adoption unrelated to\nrepresentation (p = {res['rep_algo_diff_p']:.2f})",
        transform=ax.transAxes, ha="right", va="top", fontsize=9, color="0.4", style="italic")
ax.set_xlabel("Number of state boards"); ax.set_xlim(0, max(vals) + 3)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_title("Figure 4. Half of state boards grade schools by a single formula", fontsize=11)
save(fig, "j5_figure4")

print("wrote j5_figure1/2/3/4 (pdf+png) to", os.path.abspath(OUT))
