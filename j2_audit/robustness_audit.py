"""Pass-2 robustness for the completion disparate-impact audit:
(1) parallel ABSOLUTE percentage-point-gap audit; (2) ratio vs. absolute-gap
concentration by completion and selectivity tier; (3) cohort-size sensitivity;
(4) reference-group variant: strict EEOC highest-rate-group reference instead of
the White reference; (5) pooled entering cohorts 2020-2022 (student-weighted rates)
against the single-year 2022 audit; (6) 2021 coverage sensitivity: the 30-student
screen sized on cohort_adj_150pct, since the 2021 release codes cohort_rev as
missing for the whole 2-year sector. Addresses the central methodological concern
that a ratio metric is mechanically more likely to fail at low-baseline
institutions. Real IPEDS data."""
import os, csv, urllib.request, json, time
import statistics as st
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__)) + "/"
P = {(r["unitid"], r["year"]): r for r in csv.DictReader(open(BASE + "disparate_impact_panel.csv"))}
F = {r["unitid"]: r for r in csv.DictReader(open(BASE + "predict_features_2022.csv"))}
def f(x):
    try: return float(x)
    except: return None

rows = []
for (uid, yr), r in P.items():
    if yr != "2022": continue
    w, b, di = f(r["white_rate"]), f(r["black_rate"]), f(r["black_di"])
    a = f(F[uid]["admit_rate"]) if uid in F else None
    if None in (w, b, di): continue
    rows.append({"w": w, "b": b, "di": di, "gap": w - b, "admit": a})
N = len(rows)

print("=== 1. Prevalence: ratio vs. absolute-gap ===")
print(f"  ratio (<0.80): {round(100*sum(1 for r in rows if r['di']<0.80)/N)}%")
for thr in (0.10, 0.15, 0.20):
    print(f"  absolute gap > {int(thr*100)}pp: {round(100*sum(1 for r in rows if r['gap']>thr)/N)}%")
fails = [r["gap"] for r in rows if r["di"] < 0.80]
print(f"  median abs gap among ratio-fails: {round(100*st.median(fails))}pp; share <10pp: {round(100*sum(1 for g in fails if g<0.10)/len(fails))}%")

def conc(key, tiers, label):
    print(f"\n=== Concentration by {label} (ratio-fail vs. gap>15pp vs. mean gap) ===")
    agg = defaultdict(lambda: [0, 0, 0, 0.0])
    for r in rows:
        v = r[key]
        if v is None: continue
        t = tiers(v); g = agg[t]
        g[0] += 1; g[1] += r["di"] < 0.80; g[2] += r["gap"] > 0.15; g[3] += r["gap"]
    for t in tiers.order:
        n, rf, gf, sg = agg[t]
        if n: print(f"  {t:<8} N={n:<5} ratio={round(100*rf/n)}%  gap>15pp={round(100*gf/n)}%  mean_gap={round(100*sg/n)}pp")

def ctier(w): return "<40%" if w<0.40 else "40-60%" if w<0.60 else "60-80%" if w<0.80 else ">80%"
ctier.order = ["<40%","40-60%","60-80%",">80%"]
def stier(a): return "<25%" if a<0.25 else "25-50%" if a<0.50 else "50-75%" if a<0.75 else ">75%"
stier.order = ["<25%","25-50%","50-75%",">75%"]
conc("w", ctier, "overall completion")
conc("admit", stier, "selectivity")

# 3. cohort-size sensitivity (re-pulls 2022 cohort sizes)
def fetch(u, t=6):
    for a in range(t):
        try:
            with urllib.request.urlopen(u, timeout=120) as r: return json.load(r)
        except Exception:
            if a == t-1: raise
            time.sleep(4*(a+1))
def pull(p):
    u = f"https://educationdata.urban.org/api/v1/college-university/ipeds/{p}"; o = []
    while u: d = fetch(u); o += d["results"]; u = d.get("next")
    return o
print("\n=== 3. Cohort-size sensitivity (Black, 2022) ===")
rate = defaultdict(dict); coh = defaultdict(dict)
for rc in (2, 1):
    for x in pull(f"grad-rates/2022/?sex=99&race={rc}"):
        rt = x.get("completion_rate_150pct"); cz = x.get("cohort_rev") or 0
        if rt is not None and (rc not in coh[x["unitid"]] or cz > coh[x["unitid"]][rc]):
            rate[x["unitid"]][rc] = rt; coh[x["unitid"]][rc] = cz
for MIN in (30, 50, 100):
    tot = fl = 0
    for uid, m in rate.items():
        if 1 in m and 2 in m and coh[uid].get(1, 0) >= MIN and coh[uid].get(2, 0) >= MIN and m[1] > 0:
            tot += 1; fl += m[2]/m[1] < 0.80
    print(f"  cohort>={MIN}: N={tot}, fail={round(100*fl/tot)}%")

# 4. reference-group variant: strict EEOC practice compares each group to the
# HIGHEST-rate group, not to White. The panel build writes a subgroup's rate only
# when its cohort met the 30-student minimum (blank otherwise), so a non-empty
# rate already encodes eligibility; the max is taken over qualifying groups only.
print("\n=== 4. Reference-group variant (Black, 2022): White vs. highest-rate reference ===")
GROUPS = ("white", "black", "hispanic", "asian")
nb = fw = fh = 0
for (uid, yr), r in P.items():
    if yr != "2022": continue
    b = f(r["black_rate"])
    if b is None: continue
    hi = max(v for v in (f(r[g + "_rate"]) for g in GROUPS) if v is not None)
    nb += 1; fw += f(r["black_di"]) < 0.80; fh += b/hi < 0.80
print(f"  White reference:        N={nb}, fail={fw} ({round(100*fw/nb)}%)")
print(f"  highest-rate reference: N={nb}, fail={fh} ({round(100*fh/nb)}%)")

# 5. pooled entering cohorts 2020-2022: per institution-race, sum implied
# completers (rate x cohort; completion_rate_150pct is on a 0-1 scale) and
# cohorts across years, then audit the student-weighted pooled rates with the
# same 30-student minimum applied to the POOLED cohorts of reference and subgroup.
# Per (unitid, year, race) the largest revised cohort is kept, as in the panel build.
print("\n=== 5. Pooled entering cohorts 2020-2022 (4/5ths on pooled rates) ===")
comp = defaultdict(lambda: defaultdict(float)); pooled = defaultdict(lambda: defaultdict(int))
for yy in (2020, 2021, 2022):
    br = defaultdict(dict); bc = defaultdict(dict)
    for rc in (1, 2, 3, 4):
        for x in pull(f"grad-rates/{yy}/?sex=99&race={rc}"):
            rt = x.get("completion_rate_150pct"); cz = x.get("cohort_rev") or 0
            if rt is not None and (rc not in bc[x["unitid"]] or cz > bc[x["unitid"]][rc]):
                br[x["unitid"]][rc] = rt; bc[x["unitid"]][rc] = cz
    for uid, m in br.items():
        for rc in m:
            comp[uid][rc] += m[rc] * bc[uid][rc]; pooled[uid][rc] += bc[uid][rc]
aud22 = {r["unitid"] for (u, yr), r in P.items() if yr == "2022" and f(r["black_rate"]) is not None}
for rc, nm in ((2, "Black"), (3, "Hispanic"), (4, "Asian")):
    tot = fl = nr = fr = 0
    for uid, m in pooled.items():
        if m.get(1, 0) >= 30 and m.get(rc, 0) >= 30 and comp[uid][1] > 0:
            fail = (comp[uid][rc]/m[rc]) / (comp[uid][1]/m[1]) < 0.80
            tot += 1; fl += fail
            if rc == 2 and str(uid) in aud22: nr += 1; fr += fail
    print(f"  {nm:<8} pooled: N={tot}, fail={fl} ({round(100*fl/tot)}%)")
    if rc == 2:
        print(f"  {nm:<8} single-year 2022: N={len(aud22)}; pooled restricted to those institutions: N={nr}, fail={fr} ({round(100*fr/nr)}%)")

# 6. 2021 coverage sensitivity: the 2021 release codes cohort_rev = -1 (missing)
# for the entire 2-year sector, so the panel's 2021 year is effectively 4-year
# institutions only. Re-size the 30-student screen on cohort_adj_150pct, which
# is populated for that sector, and recompute the 2021 audit at full coverage.
print("\n=== 6. 2021 coverage sensitivity (screen sized on cohort_adj_150pct) ===")
rate6 = defaultdict(dict); adj6 = defaultdict(dict)
for rc in (1, 2, 3, 4):
    for x in pull(f"grad-rates/2021/?sex=99&race={rc}"):
        rt = x.get("completion_rate_150pct"); ca = x.get("cohort_adj_150pct") or 0
        if rt is not None and ca > 0 and (rc not in adj6[x["unitid"]] or ca > adj6[x["unitid"]][rc]):
            rate6[x["unitid"]][rc] = rt; adj6[x["unitid"]][rc] = ca
for rc, nm in ((2, "Black"), (3, "Hispanic"), (4, "Asian")):
    tot = fl = 0
    for uid, m in rate6.items():
        if 1 in m and rc in m and adj6[uid].get(1, 0) >= 30 and adj6[uid].get(rc, 0) >= 30 and m[1] > 0:
            tot += 1; fl += m[rc] / m[1] < 0.80
    print(f"  {nm:<8} N={tot}, fail={fl} ({round(100*fl/tot)}%)")
