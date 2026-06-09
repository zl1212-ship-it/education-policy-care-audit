"""
Build the entering-class Pell-share panel (institution-year), 2009-2019, the income/SES equity
outcome the reviewers asked for. Source: IPEDS Student Financial Aid for first-time, full-time
degree-seeking undergraduates (Urban Institute `sfa-ftft`), type_of_aid = 5 (Pell grant),
percent_of_students. This is the share of the entering full-time class receiving a Pell grant, the
standard institution-level proxy for low-income access.

Output: data/pell_panel.csv (unitid, year, pell_share in percent).
"""
import urllib.request, json, csv, time, os

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
YEARS = list(range(2009, 2020))


def pull(path):
    url = f"{BASE}/{path}"; out = []
    while url:
        for a in range(6):
            try:
                with urllib.request.urlopen(url, timeout=180) as r:
                    d = json.load(r)
                break
            except Exception:
                if a == 5:
                    raise
                time.sleep(3 * (a + 1))
        out += d["results"]; url = d.get("next")
    return out


rows = []
for y in YEARS:
    recs = pull(f"sfa-ftft/{y}/?type_of_aid=5&per_page=20000")
    n = 0
    for x in recs:
        if x.get("type_of_aid") != 5:
            continue
        p = x.get("percent_of_students")
        if p is not None and p >= 0:
            rows.append({"unitid": x["unitid"], "year": y, "pell_share": round(p * 100, 4)})
            n += 1
    print(f"  {y}: {n} institutions", flush=True)

out_path = os.path.join(DATA, "pell_panel.csv")
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["unitid", "year", "pell_share"]); w.writeheader(); w.writerows(rows)
print(f"\nwrote {out_path}  rows: {len(rows)}  institutions: {len({r['unitid'] for r in rows})}")
