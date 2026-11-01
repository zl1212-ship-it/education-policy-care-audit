"""
How much of Georgia State's pre-2012 rise in the six-year graduation rate was shared by the
donor pool? Descriptive comparison of changes over the paper's year labels (label t = entering
cohort t-5) for Georgia State, the 109-donor pool of the base synthetic control, and the
weighted synthetic unit. Reads the cached pipeline files only (no network).

Output: data/pre2012_rise_donors.csv (one row per period: Georgia State change, donor mean,
donor median, share of donors with a change of at least 10 and at least 5 points, synthetic
change, number of donors).
"""
import os, csv, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940

g = {(int(r["uid"]), int(r["year"])): float(r["val"])
     for r in csv.DictReader(open(os.path.join(DATA, "raw_grad_t.csv")))}
donors = [int(c[1:]) for c in open(os.path.join(DATA, "scm_gsu_grad_placebo.csv")).readline().strip().split(",")
          if c.startswith("p")]
w = {int(r["unitid"]): float(r["weight"])
     for r in csv.DictReader(open(os.path.join(DATA, "scm_gsu_grad_weights.csv")))}


def chg(u, a, b):
    return (g[(u, b)] - g[(u, a)]) * 100 if (u, a) in g and (u, b) in g else None


out = []
for a, b in [(2004, 2011), (2004, 2012), (2012, 2019), (2012, 2020)]:
    ds = [x for x in (chg(u, a, b) for u in donors) if x is not None]
    synth = sum(w.get(u, 0) * (g[(u, b)] - g[(u, a)]) * 100 for u in donors if (u, a) in g and (u, b) in g)
    row = {"period": f"{a}-{b}", "gsu_change_pp": round(chg(GSU, a, b), 2),
           "donor_mean_pp": round(st.mean(ds), 2), "donor_median_pp": round(st.median(ds), 2),
           "share_donors_ge_10pp": round(sum(x >= 10 for x in ds) / len(ds), 3),
           "share_donors_ge_5pp": round(sum(x >= 5 for x in ds) / len(ds), 3),
           "synthetic_change_pp": round(synth, 2), "n_donors": len(ds)}
    out.append(row); print(row)

with open(os.path.join(DATA, "pre2012_rise_donors.csv"), "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(out[0].keys())); wr.writeheader(); wr.writerows(out)
print("saved data/pre2012_rise_donors.csv")
