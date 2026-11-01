"""
Georgia State University admissions profile, 2001-2015, from IPEDS via the Urban Institute
Education Data Portal (admissions-enrollment and admissions-requirements endpoints).

Purpose: descriptive context for the pre-2012 rise in Georgia State's graduation rate
(applications, admit rate, enrolled first-time students, SAT and ACT percentiles). No
estimation; the series are reported as served, with one caveat printed below: IPEDS
carries some admissions years forward unchanged (2001=2002, 2004=2005, 2006=2007,
2010=2011 in these fields), so differences inside those pairs are not informative.

Output: data/gsu_admissions.csv (year, applied, admitted, admit_rate, enrolled_ft,
sat_cr_25, sat_cr_75, sat_math_25, sat_math_75, act_comp_25, act_comp_75).
"""
import os, json, time, urllib.request, csv

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
GSU = 139940
YEARS = list(range(2001, 2016))


def pull(url):
    for a in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)["results"]
        except Exception:
            if a == 5: raise
            time.sleep(4 * (a + 1))


rows = []
for y in YEARS:
    adm = pull(f"{BASE}/admissions-enrollment/{y}/?unitid={GSU}&sex=99")
    req = pull(f"{BASE}/admissions-requirements/{y}/?unitid={GSU}")
    a = adm[0] if adm else {}
    r = req[0] if req else {}
    applied, admitted = a.get("number_applied"), a.get("number_admitted")
    rate = round(admitted / applied, 3) if applied and admitted and applied > 0 else None
    rows.append({
        "year": y, "applied": applied, "admitted": admitted, "admit_rate": rate,
        "enrolled_ft": a.get("number_enrolled_ft"),
        "sat_cr_25": r.get("sat_crit_read_25_pctl"), "sat_cr_75": r.get("sat_crit_read_75_pctl"),
        "sat_math_25": r.get("sat_math_25_pctl"), "sat_math_75": r.get("sat_math_75_pctl"),
        "act_comp_25": r.get("act_composite_25_pctl"), "act_comp_75": r.get("act_composite_75_pctl"),
    })
    print(rows[-1], flush=True)
    time.sleep(0.5)

with open(os.path.join(DATA, "gsu_admissions.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

first, last = rows[0], [x for x in rows if x["year"] == 2012][0]
if first["applied"] and last["applied"]:
    print(f"applications 2001 -> 2012: {first['applied']} -> {last['applied']} "
          f"({(last['applied'] / first['applied'] - 1) * 100:+.0f}%)")
rates = [x["admit_rate"] for x in rows if x["admit_rate"] and 2001 <= x["year"] <= 2012]
print(f"admit rate 2001-2012: min {min(rates):.2f} max {max(rates):.2f} (2009 is an outlier year in the served data)")
print("saved data/gsu_admissions.csv")
