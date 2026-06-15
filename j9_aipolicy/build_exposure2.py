"""Second, conceptually distinct exposure proxy: the share of an institution's
degrees in writing-reliant fields.

The headline exposure proxy is the nonresident enrollment share. A reviewer-proof
test needs a second measure that captures a different facet of exposure to the
shock: how much of the institution's teaching rests on take-home written work. This
pulls completions by two-digit CIP for the pre-shock year (IPEDS via the Urban
Institute) and computes the share of degrees awarded in writing-reliant fields
(humanities, social sciences, communication, area/ethnic studies, and the visual
and performing arts). analyze with robustness.py (alt_exposure).

Output: data/exposure2.csv (unitid, total_degrees, writing_share). Stdlib only.
"""
import csv
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
PANEL = HERE / "data" / "panel.csv"
OUT = HERE / "data" / "exposure2.csv"
YEAR = 2021  # pre-shock degree mix
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds/completions-cip-2"
# two-digit CIP families that rely on take-home written work
WRITING_CIP = {4, 5, 9, 16, 23, 24, 38, 42, 45, 50, 54}


def get(uid, tries=4):
    url = f"{BASE}/{YEAR}/?unitid={uid}"
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())["results"]
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def writing_share(uid):
    tot = defaultdict(float)
    for r in get(uid):
        # race=99 and sex=99 are the all-students totals; majornum=1 avoids
        # double-counting second majors; sum awards across award levels
        if r["race"] == 99 and r["sex"] == 99 and r["majornum"] == 1 and r["awards"]:
            cip2 = int(r["cipcode"]) // 10000
            tot[cip2] += r["awards"]
    total = sum(tot.values())
    wi = sum(v for c, v in tot.items() if c in WRITING_CIP)
    return total, (round(wi / total, 4) if total else None)


def main():
    uids = sorted(set(int(u) for u in __import__("pandas").read_csv(PANEL)["unitid"]))
    rows = []
    for uid in uids:
        try:
            total, share = writing_share(uid)
        except Exception as e:
            print(f"  ! {uid}: {type(e).__name__}")
            total, share = None, None
        rows.append({"unitid": uid, "total_degrees": total, "writing_share": share})
        print(f"  {uid}  degrees={total}  writing_share={share}")
        time.sleep(0.4)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["unitid", "total_degrees", "writing_share"])
        w.writeheader()
        w.writerows(rows)
    n = sum(r["writing_share"] is not None for r in rows)
    print(f"\nWrote {OUT}  ({n}/{len(rows)} with writing_share)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
