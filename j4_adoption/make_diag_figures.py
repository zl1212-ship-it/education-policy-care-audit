"""
Diagnostic figures for the matching and SCM robustness set.
Figure 2: synthetic-control placebo "spaghetti" plots for Georgia State (graduation) and the
          California State system (retention) -- treated gap (bold) against all placebo gaps.
Figure 3: Georgia State six-year graduation rate by race over time, showing that the gains and
          the closing of gaps preceded the 2012 adoption.
All inputs are real IPEDS data.
"""
import os, csv, json, urllib.request
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
MAN = os.path.join(HERE, "..", "paper", "blinded-manuscript")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"


# ---------- Figure 2: placebo spaghetti ----------
def load_placebo(name):
    rows = list(csv.DictReader(open(os.path.join(DATA, f"scm_{name}_placebo.csv"))))
    years = [int(r["year"]) for r in rows]
    treated = [float(r["treated"]) * 100 for r in rows]
    pcols = [c for c in rows[0] if c.startswith("p")]
    placebos = {c: [float(r[c]) * 100 for r in rows] for c in pcols}
    return years, treated, placebos


fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
for a, (name, adopt, title) in zip(ax, [
        ("gsu_grad", 2012, "(a) Georgia State, graduation rate"),
        ("csu_ret", 2018, "(b) California State system, retention")]):
    years, treated, placebos = load_placebo(name)
    for c, g in placebos.items():
        a.plot(years, g, color="0.8", linewidth=0.5, zorder=1)
    a.plot(years, treated, color="black", linewidth=2.2, zorder=3, label="Treated unit")
    a.axhline(0, color="black", linewidth=0.6); a.axvline(adopt, color="black", linewidth=0.8, linestyle=":")
    a.set_title(title, fontsize=11); a.set_xlabel("Year"); a.set_ylabel("Gap from synthetic (pp)")
    a.legend(frameon=False, loc="upper left", fontsize=9)
    a.spines["top"].set_visible(False); a.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(MAN, "j4_figure2.pdf"), bbox_inches="tight")
plt.savefig(os.path.join(HERE, "j4_figure2.png"), dpi=150, bbox_inches="tight")
print("saved figure 2 (placebo spaghetti)")


# ---------- Figure 3: GSU graduation rate by race ----------
def grad(y, race):
    u = f"{BASE}/grad-rates/{y}/?unitid=139940&race={race}&sex=99"
    with urllib.request.urlopen(u, timeout=90) as r:
        d = json.load(r)["results"]
    v = [x.get("completion_rate_150pct") for x in d if x.get("completion_rate_150pct") is not None]
    return v[0] * 100 if v else None

YEARS = list(range(2004, 2021))
races = {1: ("White", "-", "0.5"), 2: ("Black", "-", "black"), 3: ("Hispanic", "--", "0.4")}
fig2, ax2 = plt.subplots(figsize=(6.5, 4.2))
for rc, (lab, ls, col) in races.items():
    ys = [(y, grad(y, rc)) for y in YEARS]
    ys = [(y, v) for y, v in ys if v is not None]
    ax2.plot([y for y, _ in ys], [v for _, v in ys], ls, color=col, linewidth=2, label=lab)
ax2.axvline(2012, color="black", linewidth=0.8, linestyle=":")
ax2.text(2012.1, ax2.get_ylim()[0], "GPS Advising adopted", rotation=90, va="bottom", fontsize=8)
ax2.set_xlabel("Year"); ax2.set_ylabel("Six-year graduation rate (%)")
ax2.set_title("Georgia State graduation rate by race", fontsize=11)
ax2.legend(frameon=False, fontsize=9)
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(MAN, "j4_figure3.pdf"), bbox_inches="tight")
plt.savefig(os.path.join(HERE, "j4_figure3.png"), dpi=150, bbox_inches="tight")
print("saved figure 3 (graduation by race)")
