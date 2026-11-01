"""
Georgia State University six-year graduation rate by race, IPEDS bachelor's-degree-seeking
cohort (subcohort 2), computed from counts as completers within 150% of normal time over the
adjusted cohort, for graduation-rate labels 2000-2023 (label = entering cohort year plus five).
Race codes follow the Urban Institute portal: 1 White, 2 Black, 3 Hispanic, 99 total.

Output: data/gsu_race_series.csv (year, cohort_year, race, completers, cohort, rate).
"""
import os, json, time, csv, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
RACES = {1: "White", 2: "Black", 3: "Hispanic", 99: "Total"}


def pull(url):
    for a in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)["results"]
        except Exception:
            if a == 5: raise
            time.sleep(4 * (a + 1))


rows = []
for y in range(2000, 2024):
    for x in pull(f"{BASE}/grad-rates/{y}/?unitid=139940&sex=99&subcohort=2"):
        rc = x.get("race")
        if rc in RACES:
            c, n = x.get("completers_150pct"), x.get("cohort_adj_150pct")
            if c is not None and n and c >= 0 and n > 0:
                rows.append({"year": y, "cohort_year": x.get("cohort_year"), "race": RACES[rc],
                             "completers": c, "cohort": n, "rate": round(100 * c / n, 1)})
    time.sleep(0.4)
with open(os.path.join(DATA, "gsu_race_series.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
tab = {}
for r in rows:
    tab.setdefault(r["year"], {})[r["race"]] = r["rate"]
for y in sorted(tab):
    print(y, tab[y])
print("saved data/gsu_race_series.csv")
