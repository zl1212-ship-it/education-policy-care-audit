"""UK exposure: non-UK-domicile share per provider from the archived HESA Figure 7
CSV (2021/22). Use the All/All/All/All aggregate rows; share = Total Non-UK / Total.
Match to the UK institutions in our sample and fill intl_share."""
import csv, re, os
HERE = os.path.dirname(os.path.abspath(__file__))

HESA = os.path.join(HERE, "uk_hesa.csv")
FRAME = os.path.join(HERE, "data", "sample_frame.csv")

# distinctive matcher per sample institution -> avoids Brookes/Metropolitan/Trent etc.
MATCH = {
    "University of Oxford": "university of oxford",
    "University of Cambridge": "university of cambridge",
    "Imperial College London": "imperial college",
    "University College London": "university college london",
    "University of Edinburgh": "university of edinburgh",
    "University of St Andrews": "university of st andrews",
    "University of Manchester": "university of manchester",
    "University of Bristol": "university of bristol",
    "University of Birmingham": "university of birmingham",
    "University of Nottingham": "university of nottingham",
    "Cardiff University": "cardiff university",
    "University of Glasgow": "university of glasgow",
    "Durham University": "durham",
    "University of Southampton": "university of southampton",
}


def norm(s):
    s = re.sub(r"\bthe\b", "", str(s).lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z]+", " ", s)).strip()


# parse HESA: per provider, the All/All/All/All totals
prov = {}
with open(HESA, encoding="utf-8-sig") as f:
    r = csv.reader(f)
    for row in r:
        if len(row) >= 8 and row[0] == "UKPRN":
            break  # header consumed
    for row in r:
        if len(row) < 8:
            continue
        ukprn, name, level, mode, country, region, domicile, number = row[:8]
        if level == "All" and mode == "All" and country == "All" and region == "All":
            try:
                n = float(number)
            except ValueError:
                continue
            prov.setdefault(norm(name), {})[domicile] = n

# resolve each sample institution to a provider (shortest normalized name containing matcher)
def find(matcher):
    cands = [p for p in prov if matcher in p and "Total" in prov[p] and "Total Non-UK" in prov[p]]
    return min(cands, key=len) if cands else None


frame = list(csv.DictReader(open(FRAME)))
cols = list(frame[0].keys())
matched, unmatched = [], []
shares = {}
for inst, matcher in MATCH.items():
    p = find(matcher)
    if p and prov[p].get("Total", 0) > 0:
        shares[inst] = prov[p]["Total Non-UK"] / prov[p]["Total"]

for row in frame:
    if row["country"] != "UK":
        continue
    if row["institution"] in shares:
        row["intl_share"] = round(shares[row["institution"]], 4)
        row["exposure_year"] = 2021
        matched.append((row["institution"], row["intl_share"]))
    else:
        unmatched.append(row["institution"])

with open(FRAME, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(frame)

print(f"UK institutions in sample matched to HESA: {len(matched)}")
for n, s in sorted(matched, key=lambda x: -x[1]):
    print(f"   {n:<32} intl_share = {s:.1%}")
if unmatched:
    print("UNMATCHED (not in final sample or no HESA row):", unmatched)
