"""
Build the J3 admissions panel (institution-year), 2009-2022.

Sources (all public, via the Urban Institute Education Data API, which mirrors IPEDS):
  - admissions-enrollment   : applicants, admits, enrollees (by sex -> summed)
  - admissions-requirements : reqt_test_scores (the test-optional policy field),
                              open_admissions_policy, SAT/ACT 25/75 percentiles,
                              sat/act_percent_submitting
  - directory               : state, control, institution_level (restrict to 4-year)

Treatment definition (fully reproducible from IPEDS):
  reqt_test_scores codes -> 1 Required, 2 Recommended, 3 Neither required nor recommended
  (= test-optional/test-blind), 0 N/A. An institution is "test-optional" in a year when
  reqt_test_scores == 3. The adoption year is the first such year that follows a year coded
  1 or 2 (a genuine policy flip, not a missing-to-3 jump). Pre-2020 flips are the clean,
  voluntary adopters; 2020-2021 flips are the COVID wave (flagged for the analysis).

Output: data/admissions_panel.csv (one row per unitid-year).
"""
import urllib.request, json, csv, time, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
YEARS = list(range(2009, 2023))
DIR_YEAR = 2021


def pull(path):
    """Paginated GET with retry; path is appended to BASE."""
    url = f"{BASE}/{path}"
    out = []
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
        out += d["results"]
        url = d.get("next")
    return out


def num(x):
    try:
        v = float(x)
        return v if v >= 0 else None        # IPEDS uses negatives for missing/NA
    except (TypeError, ValueError):
        return None


# 1. Universe: 4-year institutions (institution_level == 4 in this API), with state/control
dirr = pull(f"directory/{DIR_YEAR}/?per_page=10000")
uni = {x["unitid"]: (x.get("state_abbr"), x.get("inst_control"))
       for x in dirr if x.get("institution_level") == 4}
print(f"4-year universe: {len(uni)}", flush=True)

# 2. Admissions volumes (by sex -> sum to institution-year)
vol = {}  # (unitid, year) -> dict of summed counts
for y in YEARS:
    rows = pull(f"admissions-enrollment/{y}/?per_page=10000")
    for x in rows:
        uid = x["unitid"]
        if uid not in uni:
            continue
        k = (uid, y)
        d = vol.setdefault(k, {"applied": 0.0, "admitted": 0.0, "enrolled": 0.0,
                               "enr_f": 0.0, "any": False})
        ap, ad, en = num(x.get("number_applied")), num(x.get("number_admitted")), num(x.get("number_enrolled_total"))
        if ap is not None: d["applied"] += ap; d["any"] = True
        if ad is not None: d["admitted"] += ad; d["any"] = True
        if en is not None:
            d["enrolled"] += en; d["any"] = True
            if x.get("sex") == 2:           # 2 = female in IPEDS
                d["enr_f"] += en
    print(f"  admissions-enrollment {y}: {len(rows)} rows", flush=True)

# 3. Admissions requirements (policy + score profile)
req = {}  # (unitid, year) -> dict
for y in YEARS:
    rows = pull(f"admissions-requirements/{y}/?per_page=10000")
    for x in rows:
        uid = x["unitid"]
        if uid not in uni:
            continue
        # reqt_test_scores valid categories are 0/1/2/3; IPEDS uses negatives (-1,-2)
        # as missing/not-applicable sentinels -> treat those as missing.
        rts = x.get("reqt_test_scores")
        rts = rts if rts in (0, 1, 2, 3) else None
        req[(uid, y)] = {
            "reqt_test_scores": rts,
            "open_adm": x.get("open_admissions_policy"),
            "sat_cr_25": num(x.get("sat_crit_read_25_pctl")),
            "sat_cr_75": num(x.get("sat_crit_read_75_pctl")),
            "sat_math_25": num(x.get("sat_math_25_pctl")),
            "sat_math_75": num(x.get("sat_math_75_pctl")),
            "act_25": num(x.get("act_composite_25_pctl")),
            "act_75": num(x.get("act_composite_75_pctl")),
            "sat_pct_submit": num(x.get("sat_percent_submitting")),
            "act_pct_submit": num(x.get("act_percent_submitting")),
        }
    print(f"  admissions-requirements {y}: {len(rows)} rows", flush=True)

# 4. Assemble long panel
keys = sorted(set(vol) | set(req))
rows = []
for (uid, y) in keys:
    st, ctrl = uni[uid]
    v = vol.get((uid, y), {})
    rq = req.get((uid, y), {})
    applied, admitted, enrolled = v.get("applied"), v.get("admitted"), v.get("enrolled")
    enr_f = v.get("enr_f")
    admit_rate = (admitted / applied) if applied else None
    yield_rate = (enrolled / admitted) if admitted else None
    female_share = (enr_f / enrolled) if enrolled else None
    sat25 = (rq.get("sat_cr_25") + rq.get("sat_math_25")) if (rq.get("sat_cr_25") and rq.get("sat_math_25")) else None
    sat75 = (rq.get("sat_cr_75") + rq.get("sat_math_75")) if (rq.get("sat_cr_75") and rq.get("sat_math_75")) else None
    rows.append({
        "unitid": uid, "year": y, "state": st, "control": ctrl,
        "applied": applied if (v.get("any")) else "",
        "admitted": admitted if (v.get("any")) else "",
        "enrolled": enrolled if (v.get("any")) else "",
        "admit_rate": round(admit_rate, 4) if admit_rate is not None else "",
        "yield_rate": round(yield_rate, 4) if yield_rate is not None else "",
        "female_share": round(female_share, 4) if female_share is not None else "",
        "reqt_test_scores": rq.get("reqt_test_scores", ""),
        "open_adm": rq.get("open_adm", ""),
        "sat_total_25": sat25 if sat25 else "",
        "sat_total_75": sat75 if sat75 else "",
        "act_25": rq.get("act_25") or "",
        "act_75": rq.get("act_75") or "",
        "sat_pct_submit": rq.get("sat_pct_submit") if rq.get("sat_pct_submit") is not None else "",
        "act_pct_submit": rq.get("act_pct_submit") if rq.get("act_pct_submit") is not None else "",
    })

os.makedirs(DATA, exist_ok=True)
out_path = os.path.join(DATA, "admissions_panel.csv")
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"\nwrote {out_path}")
print(f"rows: {len(rows)}  institutions: {len({r['unitid'] for r in rows})}")
print(f"years: {min(r['year'] for r in rows)}-{max(r['year'] for r in rows)}")
n_to = sum(1 for r in rows if str(r['reqt_test_scores']) == '3')
print(f"institution-years coded test-optional (reqt==3): {n_to}")
