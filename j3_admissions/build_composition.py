"""
Build the entering-class racial-composition outcome panel (institution-year), 2009-2022.

Source: Urban Institute Education Data API,
  fall-enrollment/{year}/1/race/sex/  (level_of_study = 1, undergraduate)
filtered server-side to the ENTERING degree-seeking cohort:
  class_level = 1 (first-time), degree_seeking = 1, ftpt = 99 (full+part total),
  sex = 99 (both sexes).
This yields, for each institution-year, the racial composition of the first-time
degree-seeking entering class -- the admissions flow the reform is meant to move.

Shares use a DOMESTIC, KNOWN-RACE denominator: domestic_total = total (race 99) minus nonresident
(international, code 8) minus unknown race (code 9). This prevents an expansion of international
enrollment from mechanically diluting the URM share. The nonresident and unknown
shares (over the all-students total) are stored separately as diagnostics.

Urban race codes: 1 White, 2 Black, 3 Hispanic, 4 Asian, 5 Am.Indian/Alaska,
  6 Pacific Islander, 7 Two or more, 8 Nonresident, 9 Unknown, 99 Total.
URM = Black + Hispanic + Am.Indian + Pacific Islander + Two-or-more (over domestic known race).

Output: data/composition_panel.csv
  unitid, year, entering_total, domestic_total, share_black, share_hisp, share_urm, share_white,
  share_asian, share_nonres, share_unknown
"""
import urllib.request, json, csv, time, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
YEARS = list(range(2009, 2023))
URM = {2, 3, 5, 6, 7}


def pull(path):
    url = f"{BASE}/{path}"
    out = []
    while url:
        for a in range(6):
            try:
                with urllib.request.urlopen(url, timeout=300) as r:
                    d = json.load(r)
                break
            except Exception:
                if a == 5:
                    raise
                time.sleep(3 * (a + 1))
        out += d["results"]
        url = d.get("next")
    return out


def num(x):
    try:
        v = float(x)
        return v if v >= 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def main():
    rows = []
    for y in YEARS:
        recs = pull(f"fall-enrollment/{y}/1/race/sex/"
                    f"?class_level=1&degree_seeking=1&ftpt=99&sex=99&per_page=20000")
        bycount = defaultdict(dict)        # unitid -> {race: count}
        for x in recs:
            # guard in code in case the API ignores a filter
            if not (x.get("class_level") == 1 and x.get("degree_seeking") == 1
                    and x.get("ftpt") == 99 and x.get("sex") == 99):
                continue
            bycount[x["unitid"]][x.get("race")] = num(x.get("enrollment_fall"))
        for uid, rc in bycount.items():
            tot = rc.get(99) or sum(v for k, v in rc.items() if k != 99)
            if not tot or tot <= 0:
                continue
            nonres = rc.get(8, 0.0); unknown = rc.get(9, 0.0)
            # Composition shares use a DOMESTIC, KNOWN-RACE denominator: total minus nonresident
            # (international, code 8) and unknown race (code 9). The concern is that the
            # all-students denominator (race=99) mechanically dilutes URM share when adopters expand
            # international enrollment, which could manufacture a null. dom = tot - nonres - unknown.
            dom = tot - nonres - unknown
            if dom <= 0:
                continue
            urm = sum(rc.get(k, 0.0) for k in URM)
            rows.append({
                "unitid": uid, "year": y, "entering_total": int(tot), "domestic_total": int(dom),
                "share_black": round(rc.get(2, 0.0) / dom, 5),
                "share_hisp": round(rc.get(3, 0.0) / dom, 5),
                "share_urm": round(urm / dom, 5),
                "share_white": round(rc.get(1, 0.0) / dom, 5),
                "share_asian": round(rc.get(4, 0.0) / dom, 5),
                "share_nonres": round(nonres / tot, 5),
                "share_unknown": round(unknown / tot, 5),
            })
        print(f"  {y}: {len(bycount)} institutions", flush=True)

    out_path = os.path.join(DATA, "composition_panel.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote {out_path}  rows: {len(rows)}  "
          f"institutions: {len({r['unitid'] for r in rows})}")


if __name__ == "__main__":
    main()
