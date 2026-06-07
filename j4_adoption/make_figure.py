"""
Figure 1: synthetic control plots for Georgia State (graduation rate) and the California
State University system (retention). Real vs synthetic series, with a vertical line at
adoption. Built from scm_gsu_series.csv and scm_csu_series.csv (real IPEDS data).
"""
import os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")


def load(fn):
    yrs, real, syn = [], [], []
    with open(os.path.join(DATA, fn)) as f:
        for r in csv.DictReader(f):
            yrs.append(int(r["year"])); real.append(float(r["real"]) * 100); syn.append(float(r["synth"]) * 100)
    return yrs, real, syn


fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
plt.rcParams.update({"font.size": 11})

for a, (fn, adopt, title, ylab) in zip(ax, [
        ("scm_gsu_series.csv", 2012, "(a) Georgia State University", "Six-year graduation rate (%)"),
        ("scm_csu_series.csv", 2018, "(b) California State University system", "First-year retention (%)")]):
    yrs, real, syn = load(fn)
    a.plot(yrs, real, "-", color="black", linewidth=2, label="Actual")
    a.plot(yrs, syn, "--", color="gray", linewidth=2, label="Synthetic control")
    a.axvline(adopt, color="black", linewidth=0.8, linestyle=":")
    a.text(adopt + 0.1, a.get_ylim()[0], "adoption", rotation=90, va="bottom", fontsize=8)
    a.set_title(title, fontsize=11)
    a.set_xlabel("Year"); a.set_ylabel(ylab)
    a.legend(frameon=False, loc="lower right", fontsize=9)
    a.spines["top"].set_visible(False); a.spines["right"].set_visible(False)

plt.tight_layout()
out = os.path.join(HERE, "..", "paper", "blinded-manuscript", "j4_figure1.pdf")
plt.savefig(out, bbox_inches="tight")
plt.savefig(os.path.join(HERE, "j4_figure1.png"), dpi=150, bbox_inches="tight")
print("saved", os.path.abspath(out))
