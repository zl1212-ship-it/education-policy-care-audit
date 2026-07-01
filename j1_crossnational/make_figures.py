"""Figures for the cross-national doctoral-stipend adequacy audit.

Reads crossnational_ratios.csv (produced by build_crossnational.py) and emits,
as both .png and .pdf into the gitignored repo-root paper/ folder:

  fig_crossnational_2024   the 2024 adequacy snapshot across regimes, with a
                           parity line: how far each regime's reference doctoral
                           floor sits from its own local cost-of-living standard.
  fig_crossnational_trend  adequacy ratio over time (UK national/London, AU,
                           Canada), showing the floor sitting flat below parity
                           and the discrete jumps that arrive only when policy is
                           forced to move.

Descriptive audit only; no estimate is plotted.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "paper")
os.makedirs(OUT, exist_ok=True)

TIER_A = "#1f5c99"   # basic-needs living wage
TIER_B = "#b5651d"   # statutory minimum wage
US_C = "#2e7d32"     # US institution-set


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)


def fig_2024(df):
    d = df[df["year"] == 2024].copy()
    # de-duplicate Canada (CGS-D and PGS-D coincide at 40k in 2024); keep CGS-D
    d = d[~d["program"].str.startswith("PGS-D")]
    labels, ratios, colors = [], [], []
    order = [
        ("US", "cohort", "US elite R1, cohort mean"),
        ("US", "flagship_low", "US elite R1, lowest flagship"),
        ("CA", "Toronto", "Canada CGS-D (Toronto)"),
        ("CA", "Vancouver", "Canada CGS-D (Vancouver)"),
        ("UK", "national", "UK UKRI minimum (national)"),
        ("UK", "London", "UK UKRI minimum (London)"),
        ("AU", "national", "Australia RTP base"),
        ("JP", "Tokyo", "Japan JSPS DC (Tokyo)"),
    ]
    for country, region, label in order:
        row = d[(d["country"] == country) & (d["region"] == region)]
        if row.empty:
            continue
        r = float(row["adequacy_ratio"].iloc[0])
        bt = row["benchmark_type"].iloc[0]
        labels.append(label)
        ratios.append(r)
        colors.append(US_C if country == "US" else (TIER_A if bt == "basic_needs_livingwage" else TIER_B))

    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    y = range(len(labels))
    ax.barh(list(y), ratios, color=colors, height=0.62)
    ax.axvline(1.0, color="#444", lw=1.2, ls="--")
    ax.text(1.01, -0.42, "cost-of-living parity", fontsize=8, color="#444")
    for i, r in enumerate(ratios):
        ax.text(r + 0.01, i, f"{r:.2f}", va="center", fontsize=8.5)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.75)
    ax.set_xlabel("Adequacy ratio: reference doctoral stipend / local cost-of-living benchmark (2024)")
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=US_C, label="US, institution-set (MIT single-adult living wage)"),
        Patch(color=TIER_A, label="Basic-needs living wage (UK LWF, Canada LWN)"),
        Patch(color=TIER_B, label="Statutory minimum wage, full-time (AU, JP)"),
    ], fontsize=7.6, loc="center right", framealpha=0.95)
    ax.set_title("Doctoral stipend adequacy ratios by funding regime, 2024", fontsize=11)
    save(fig, "fig_crossnational_2024")


def fig_trend(df):
    fig, ax = plt.subplots(figsize=(8.2, 4.6))

    def series(country, region, program_prefix=None):
        s = df[(df["country"] == country) & (df["region"] == region)]
        if program_prefix:
            s = s[s["program"].str.startswith(program_prefix)]
        return s.sort_values("year")

    uk_n = series("UK", "national")
    uk_l = series("UK", "London")
    au = series("AU", "national")
    ca = series("CA", "Toronto", "CGS-D")
    jp = series("JP", "Tokyo")

    ax.plot(uk_n["year"], uk_n["adequacy_ratio"], "-o", color=TIER_A, label="UK UKRI min (national)")
    ax.plot(uk_l["year"], uk_l["adequacy_ratio"], "--o", color=TIER_A, alpha=0.7, label="UK UKRI min (London)")
    ax.plot(au["year"], au["adequacy_ratio"], "-s", color=TIER_B, label="Australia RTP (vs min wage)")
    ax.plot(ca["year"], ca["adequacy_ratio"], "-^", color="#7a3b8f", label="Canada CGS-D (Toronto)")
    ax.plot(jp["year"], jp["adequacy_ratio"], "-D", color="#c0392b", label="Japan JSPS DC (vs Tokyo min wage)")

    # annotate the forced jump: Canada PGS-D 2023 -> 2024
    pgs23 = df[(df["country"] == "CA") & (df["program"].str.startswith("PGS-D")) &
               (df["year"] == 2023) & (df["region"] == "Toronto")]
    if not pgs23.empty:
        r = float(pgs23["adequacy_ratio"].iloc[0])
        ax.plot([2023], [r], "x", color="#7a3b8f", ms=9, mew=2)
        ax.annotate("Canada PGS-D held at CAD 21,000 to 2023 (0.46);\nraised to CAD 40,000 by the 2024 federal budget",
                    xy=(2023, r), xytext=(2019.6, 0.30), fontsize=7.6, color="#7a3b8f",
                    arrowprops=dict(arrowstyle="->", color="#7a3b8f", lw=1))

    ax.axhline(1.0, color="#444", lw=1.1, ls="--")
    ax.text(2019.0, 1.02, "cost-of-living parity", fontsize=8, color="#444")
    ax.set_ylim(0.2, 1.15)
    ax.set_xlabel("Year")
    ax.set_ylabel("Adequacy ratio")
    ax.set_title("Doctoral stipend adequacy ratio over time, 2019-2025", fontsize=11)
    ax.legend(fontsize=8, loc="lower right", ncol=1, framealpha=0.9)
    save(fig, "fig_crossnational_trend")


def main():
    df = pd.read_csv(os.path.join(HERE, "crossnational_ratios.csv"))
    fig_2024(df)
    fig_trend(df)
    print(f"Wrote fig_crossnational_2024.(png|pdf) and fig_crossnational_trend.(png|pdf) into {OUT}")


if __name__ == "__main__":
    main()
