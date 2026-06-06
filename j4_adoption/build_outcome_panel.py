"""
Build the J4 retention outcome panel (institution-year), 2009-2023.

Outcome: IPEDS first-time full-time retention rate (fall-retention, ftpt=1) via the
Urban Institute Education Data API. Universe: public 4-year institutions. Treatment
(adoption year) merged from data/treatment_panel.csv (firm, pre-2020 adopters).

Output: data/retention_panel.csv with columns
  unitid, year, state, retention_rate, system, adoption_year, treated, post, event_time
"""
import urllib.request, json, csv, time, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
YEARS = list(range(2009, 2021))  # Urban fall-retention currently ends at 2020
DIR_YEAR = 2021


def pull(url):
    out = []
    while url:
        for a in range(6):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    d = json.load(r); break
            except Exception:
                if a == 5: raise
                time.sleep(4 * (a + 1))
        out += d["results"]; url = d.get("next")
    return out


# 1. Universe: public 4-year institutions (inst_control=1, institution_level=1)
base = "https://educationdata.urban.org/api/v1/college-university/ipeds"
dirr = pull(f"{base}/directory/{DIR_YEAR}/?inst_control=1")
uni = {x["unitid"]: x.get("state_abbr") for x in dirr
       if x.get("institution_level") == 4}  # 4 = four-or-more-year in this API
print(f"public 4-year universe: {len(uni)}", flush=True)

# 2. Treatment map from treatment_panel.csv (firm adoption years only)
adopt, system = {}, {}
with open(os.path.join(DATA, "treatment_panel.csv")) as f:
    for r in csv.DictReader(f):
        if r["adoption_year"] and r["date_confidence"] in ("firm", "firm_system"):
            adopt[int(r["unitid"])] = int(r["adoption_year"])
            system[int(r["unitid"])] = r["system"]
print(f"treated (firm year): {len(adopt)}", flush=True)

# 3. Retention rate, full-time, per year
ret = {}
for y in YEARS:
    rows = pull(f"{base}/fall-retention/{y}/?ftpt=1")
    n = 0
    for x in rows:
        uid = x["unitid"]
        if uid in uni and x.get("retention_rate") is not None:
            ret[(uid, y)] = x["retention_rate"]; n += 1
    print(f"  {y}: {n} retention rows", flush=True)

# 4. Assemble long panel
out = []
for (uid, y), rr in sorted(ret.items()):
    ay = adopt.get(uid)
    out.append({
        "unitid": uid, "year": y, "state": uni.get(uid),
        "retention_rate": rr,
        "system": system.get(uid, ""),
        "adoption_year": ay if ay else "",
        "treated": 1 if ay else 0,
        "post": 1 if (ay and y >= ay) else 0,
        "event_time": (y - ay) if ay else "",
    })

with open(os.path.join(DATA, "retention_panel.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader(); w.writerows(out)

treated_units = {r["unitid"] for r in out if r["treated"]}
print(f"\npanel rows: {len(out)}")
print(f"institutions: {len({r['unitid'] for r in out})}  (treated {len(treated_units)})")
print(f"years: {min(r['year'] for r in out)}-{max(r['year'] for r in out)}")
