"""
J2: Disparate-impact audit of U.S. higher-education completion outcomes.
Real data: IPEDS Graduation Rates (150% of normal time), via the Urban Institute
Education Data API (no key). Imports the EEOC Four-Fifths (4/5ths) adverse-impact
rule into education policy: per institution-year, ratio of each subgroup's
completion rate to the White reference rate; flag < 0.80 as adverse impact.
Outputs a frozen institution-year CSV + a national summary by year.
"""
import urllib.request, json, csv, time
from collections import defaultdict

YEARS = [2018, 2019, 2020, 2021, 2022]
RACE = {1: "White", 2: "Black", 3: "Hispanic", 4: "Asian"}
REF = 1            # White = reference group
MIN_COHORT = 30    # 4/5ths rule guidance: require adequate subgroup size
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds/grad-rates/{y}/?sex=99&race={r}"

def fetch(url, tries=6):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                return json.load(resp)
        except Exception:
            if a == tries - 1:
                raise
            time.sleep(4 * (a + 1))

def pull(y, r):
    url = BASE.format(y=y, r=r); out = []
    while url:
        d = fetch(url)
        out += d["results"]; url = d.get("next")
    return out

# per (unitid, year, race): take the row with the largest revised cohort (most inclusive)
rate = defaultdict(dict); coh = defaultdict(dict)
for y in YEARS:
    for r in RACE:
        for x in pull(y, r):
            rt = x.get("completion_rate_150pct"); cz = x.get("cohort_rev") or 0
            if rt is None: continue
            key = (x["unitid"], y)
            if r not in coh[key] or cz > coh[key][r]:
                rate[key][r] = rt; coh[key][r] = cz
    print(f"year {y} pulled", flush=True)

rows = []
for (uid, y), m in rate.items():
    if REF not in m or coh[(uid,y)].get(REF,0) < MIN_COHORT or m[REF] <= 0:
        continue
    rec = {"unitid": uid, "year": y, "white_rate": m[REF], "white_cohort": coh[(uid,y)][REF]}
    for r, nm in RACE.items():
        if r == REF: continue
        if r in m and coh[(uid,y)].get(r,0) >= MIN_COHORT:
            di = round(m[r]/m[REF], 4)
            rec[f"{nm.lower()}_rate"] = m[r]
            rec[f"{nm.lower()}_di"] = di
            rec[f"{nm.lower()}_fail"] = int(di < 0.80)
    rows.append(rec)

cols = ["unitid","year","white_rate","white_cohort",
        "black_rate","black_di","black_fail",
        "hispanic_rate","hispanic_di","hispanic_fail",
        "asian_rate","asian_di","asian_fail"]
with open("/Users/yuxialiang/education-policy-care-audit/j2_audit/disparate_impact_panel.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({k: r.get(k) for k in cols})

print("\n=== NATIONAL DISPARATE-IMPACT AUDIT (real IPEDS GR 150%) ===")
print(f"institution-years in panel: {len(rows)}")
for nm in ["black","hispanic","asian"]:
    print(f"\n{nm.title()} vs White:")
    for y in YEARS:
        sub = [r for r in rows if r["year"]==y and f"{nm}_fail" in r]
        if sub:
            fails = sum(r[f"{nm}_fail"] for r in sub)
            print(f"  {y}: auditable={len(sub):4d}  fail 4/5ths={fails:4d} ({100*fails/len(sub):.0f}%)")
