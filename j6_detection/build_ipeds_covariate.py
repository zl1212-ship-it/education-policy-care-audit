"""Merge IPEDS international-enrollment share onto the 50 flagships (J6 covariate).

Why: the governance layer asks whether the campuses whose students are most
exposed to the detector bias (highest nonresident/international enrollment) have
more or less protective AI policy. This pulls each flagship's nonresident-alien
share of fall enrollment from the public Urban Institute Education Data API
(IPEDS), keyed by UnitID, so analyze_policy.py can test exposure vs protection.

Source: Urban Institute Education Data Portal, IPEDS fall-enrollment by race
(race=9 is Nonresident alien; race=99 is Total). UnitIDs are resolved from the
IPEDS directory by state + normalized name match; unresolved ones are listed for
manual entry in UNITID_OVERRIDE.

Output: data/ipeds_covariate.csv (institution, state, unitid, year,
total_enroll, nonresident_alien, intl_share). Stdlib only.
"""
import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REGISTRY = HERE / "data" / "policy_registry.csv"
OUT = HERE / "data" / "ipeds_covariate.csv"
YEAR = 2022
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"

STATE_FIPS = {
    "AL": 1, "AK": 2, "AZ": 4, "AR": 5, "CA": 6, "CO": 8, "CT": 9, "DE": 10,
    "FL": 12, "GA": 13, "HI": 15, "ID": 16, "IL": 17, "IN": 18, "IA": 19,
    "KS": 20, "KY": 21, "LA": 22, "ME": 23, "MD": 24, "MA": 25, "MI": 26,
    "MN": 27, "MS": 28, "MO": 29, "MT": 30, "NE": 31, "NV": 32, "NH": 33,
    "NJ": 34, "NM": 35, "NY": 36, "NC": 37, "ND": 38, "OH": 39, "OK": 40,
    "OR": 41, "PA": 42, "RI": 44, "SC": 45, "SD": 46, "TN": 47, "TX": 48,
    "UT": 49, "VT": 50, "VA": 51, "WA": 53, "WV": 54, "WI": 55, "WY": 56,
}

# UnitIDs that name-matching cannot resolve unambiguously; verified from IPEDS.
UNITID_OVERRIDE = {
    "University at Buffalo": 196088,            # SUNY at Buffalo
    "Louisiana State University": 159391,       # LSU and A&M College
}


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def norm(s: str) -> str:
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(the|at|main campus|and agricultural|mechanical college)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def resolve_unitid(inst, fips, cache):
    if inst in UNITID_OVERRIDE:
        return UNITID_OVERRIDE[inst]
    if fips not in cache:
        d = get(f"{BASE}/directory/{YEAR}/?fips={fips}")
        cache[fips] = [r for r in d["results"] if r.get("inst_control") == 1]
    target = norm(inst)
    cands = cache[fips]
    # exact, then prefix, then token-superset match on normalized names
    for r in cands:
        if norm(r["inst_name"]) == target:
            return r["unitid"]
    for r in cands:
        if norm(r["inst_name"]).startswith(target):
            return r["unitid"]
    tset = set(target.split())
    best = [r for r in cands if tset <= set(norm(r["inst_name"]).split())]
    return best[0]["unitid"] if len(best) == 1 else None


def intl_share(unitid: int):
    d = get(f"{BASE}/fall-enrollment/{YEAR}/99/race/?unitid={unitid}")
    agg = [x for x in d["results"]
           if x["ftpt"] == 99 and x["degree_seeking"] == 99
           and x["class_level"] == 99 and x["sex"] == 99]
    by_race = {x["race"]: x["enrollment_fall"] for x in agg}
    total, nra = by_race.get(99), by_race.get(8)  # race=8 nonresident alien; 9 is race-unknown
    if not total or nra is None:
        return None, None, None
    return total, nra, round(nra / total, 4)


def main() -> int:
    with open(REGISTRY, newline="", encoding="utf-8") as f:
        regs = [r for r in csv.DictReader(f) if r.get("institution")]

    cache, rows, missing = {}, [], []
    for r in regs:
        inst, st = r["institution"], r["state"]
        fips = STATE_FIPS.get(st)
        uid = resolve_unitid(inst, fips, cache) if fips else None
        if not uid:
            missing.append(inst)
            continue
        total, nra, share = intl_share(uid)
        rows.append({"institution": inst, "state": st, "unitid": uid, "year": YEAR,
                     "total_enroll": total, "nonresident_alien": nra, "intl_share": share})
        print(f"  {inst:<42} unitid={uid}  intl={share:.1%}" if share is not None
              else f"  {inst:<42} unitid={uid}  (no enrollment)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["institution", "state", "unitid", "year",
                                          "total_enroll", "nonresident_alien", "intl_share"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT}  ({len(rows)}/{len(regs)} flagships)")
    if missing:
        print(f"UNRESOLVED unitids ({len(missing)}) -> add to UNITID_OVERRIDE: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
