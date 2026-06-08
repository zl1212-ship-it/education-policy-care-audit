"""
Derive the test-optional treatment from the admissions panel.

Adoption year = the first year an institution's reqt_test_scores is coded 3 (Neither
required nor recommended) AND a prior observed year was coded 1 (Required) or 2
(Recommended). Requiring a prior 1/2 ensures we capture a genuine policy flip, not an
institution that is missing-then-3 or always-3. Institutions never coded 3 are controls.

Cohort flag:
  pre_covid  : adoption_year <= 2019  (voluntary adopters; the clean identification)
  covid      : adoption_year in {2020, 2021}
  post       : adoption_year >= 2022

Output: data/treatment_panel.csv with columns
  unitid, adoption_year, cohort, n_years_pre, ever_required
and an augmented data/panel_treated.csv (admissions_panel + treated/post/event_time).
"""
import csv, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load_panel():
    with open(os.path.join(DATA, "admissions_panel.csv")) as f:
        return list(csv.DictReader(f))


def code(r):
    c = r.get("reqt_test_scores")
    try:
        return int(c)
    except (TypeError, ValueError):
        return None


def main():
    rows = load_panel()
    byinst = defaultdict(dict)            # unitid -> {year: code}
    for r in rows:
        byinst[int(r["unitid"])][int(r["year"])] = code(r)

    treat = {}                            # unitid -> adoption_year
    ever_req = {}
    for uid, yc in byinst.items():
        years = sorted(yc)
        seen_req = False
        adopt = None
        for y in years:
            c = yc[y]
            if c in (1, 2):
                seen_req = True
            if c == 3 and seen_req and adopt is None:
                adopt = y
        ever_req[uid] = seen_req
        if adopt is not None:
            treat[uid] = adopt

    # treatment summary table
    out = []
    for uid in sorted(byinst):
        ay = treat.get(uid)
        if ay is None:
            cohort = "never"
        elif ay <= 2019:
            cohort = "pre_covid"
        elif ay in (2020, 2021):
            cohort = "covid"
        else:
            cohort = "post"
        n_pre = sum(1 for y in byinst[uid] if ay and y < ay and byinst[uid][y] is not None)
        out.append({"unitid": uid, "adoption_year": ay or "", "cohort": cohort,
                    "n_years_pre": n_pre, "ever_required": int(ever_req[uid])})

    with open(os.path.join(DATA, "treatment_panel.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["unitid", "adoption_year", "cohort",
                                          "n_years_pre", "ever_required"])
        w.writeheader(); w.writerows(out)

    # augment the long panel with treated/post/event_time
    aug = []
    for r in rows:
        uid = int(r["unitid"]); y = int(r["year"])
        ay = treat.get(uid)
        r = dict(r)
        r["adoption_year"] = ay or ""
        r["treated"] = 1 if ay else 0
        r["post"] = 1 if (ay and y >= ay) else 0
        r["event_time"] = (y - ay) if ay else ""
        aug.append(r)
    with open(os.path.join(DATA, "panel_treated.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(aug[0].keys()))
        w.writeheader(); w.writerows(aug)

    from collections import Counter
    cc = Counter(o["cohort"] for o in out)
    print("treatment cohorts:", dict(cc))
    print(f"total adopters (flip 1/2 -> 3): {sum(1 for o in out if o['adoption_year'])}")
    print("wrote data/treatment_panel.csv and data/panel_treated.csv")


if __name__ == "__main__":
    main()
