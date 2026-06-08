"""
J3 figures (built from the real result CSVs):
  Figure 1: Callaway-Sant'Anna event studies -- (a) SAT submission rate, (b) entering-class
            %URM. Panel (a) shows the measurement break at adoption; panel (b) shows no break,
            only the continuation of a pre-existing trend.
  Figure 2: synthetic control for George Washington University, entering-class %URM, real vs
            synthetic, with the 2016 adoption marked.
Outputs go to the blinded-manuscript folder as j3_figure1.pdf and j3_figure2.pdf.
"""
import os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "paper", "blinded-manuscript")
plt.rcParams.update({"font.size": 11})


def load_event(fn):
    e, a = [], []
    with open(os.path.join(DATA, fn)) as f:
        for r in csv.DictReader(f):
            e.append(int(r["event_time"])); a.append(float(r["att"]))
    return e, a


# ---------- Figure 1: event studies ----------
fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
for a, (fn, title, ylab) in zip(ax, [
        ("did_event_sat_pct_submit.csv", "(a) SAT submission rate", "ATT (percentage points)"),
        ("did_event_share_urm.csv", "(b) Entering-class %URM", "ATT (percentage points)")]):
    e, att = load_event(fn)
    a.axhline(0, color="gray", linewidth=0.7)
    a.axvline(-0.5, color="black", linewidth=0.8, linestyle=":")
    a.plot(e, att, "o-", color="black", linewidth=1.6, markersize=4)
    a.text(-0.4, a.get_ylim()[1], "adoption", rotation=90, va="top", fontsize=8)
    a.set_title(title, fontsize=11)
    a.set_xlabel("Years relative to adoption"); a.set_ylabel(ylab)
    a.spines["top"].set_visible(False); a.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "j3_figure1.pdf"), bbox_inches="tight")
print("wrote j3_figure1.pdf")

# ---------- Figure 2: synthetic control, two flagship adopters ----------
def load_scm(fn):
    yrs, real, syn = [], [], []
    with open(os.path.join(DATA, fn)) as f:
        for r in csv.DictReader(f):
            yrs.append(int(r["year"])); real.append(float(r["real"])); syn.append(float(r["synth"]))
    return yrs, real, syn

fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
for a, (fn, lab, p) in zip(ax, [
        ("scm_gw_share_urm.csv", "(a) George Washington U. (selective private)", 0.32),
        ("scm_montclair_share_urm.csv", "(b) Montclair State U. (broad-access public)", 0.38)]):
    yrs, real, syn = load_scm(fn)
    a.plot(yrs, real, "-", color="black", linewidth=2, label="Actual")
    a.plot(yrs, syn, "--", color="gray", linewidth=2, label="Synthetic control")
    a.axvline(2016, color="black", linewidth=0.8, linestyle=":")
    a.text(2016.1, a.get_ylim()[0], "test-optional (2016)", rotation=90, va="bottom", fontsize=8)
    a.set_title(f"{lab}\nplacebo $p={p}$", fontsize=10)
    a.set_xlabel("Year"); a.set_ylabel("URM share of entering class (%)")
    a.legend(frameon=False, loc="lower right", fontsize=9)
    a.spines["top"].set_visible(False); a.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "j3_figure2.pdf"), bbox_inches="tight")
print("wrote j3_figure2.pdf")
