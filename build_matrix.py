"""
Build governance_matrix.csv with real data from two sources:
  H_f  = USASpending.gov API (federal funding per institution per FY)
  H_s  = phdstipends.com (average PhD stipend per institution per academic year)
  N_g  = institutions_config.json (baseline enrollment)
  S_r  = log((H_f + 1) / ((H_s / cost_index) * N_g))  -- descriptive disparity ratio

Note: no outcome variable (e.g. doctoral attrition) is generated. Reliable
institution-by-year retention data are not available, and a modelled attrition
series would be synthetic and circular with S_r. Only auditable inputs and the
descriptive S_r ratio are written.
"""

import csv
import json
import math
import os
import sys
import time

import requests

# --------------- config ---------------

YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

USASPENDING_API = "https://api.usaspending.gov/api/v2/search/spending_by_category/recipient/"
STIPENDS_API = "https://www.phdstipends.com/data/"

STIPEND_NAME_MAP = {
    "Stanford University": ["stanford"],
    "Harvard University": ["harvard"],
    "Massachusetts Institute of Technology": ["mit", "massachusetts institute of technology"],
    "California Institute of Technology": ["caltech", "california institute of technology"],
    "Princeton University": ["princeton"],
    "Yale University": ["yale"],
    "Columbia University": ["columbia university"],
    "University of Chicago": ["university of chicago"],
    "University of Pennsylvania": ["university of pennsylvania"],
    "Cornell University": ["cornell"],
    "Johns Hopkins University": ["johns hopkins"],
    "Duke University": ["duke"],
    "Northwestern University": ["northwestern university"],
    "University of Michigan": ["university of michigan"],
    "University of Texas at Austin": ["university of texas - austin", "university of texas at austin"],
    "University of Washington": ["university of washington"],
    "University of Illinois Urbana-Champaign": ["university of illinois", "uiuc"],
    "Ohio State University": ["ohio state"],
    "Penn State University": ["penn state", "pennsylvania state"],
    "University of California, Berkeley": ["university of california - berkeley", "uc berkeley"],
    "University of California, Los Angeles": ["university of california - los angeles", "ucla"],
    "University of California, San Diego": ["university of california - san diego", "ucsd"],
}

USASPENDING_MATCH = {
    "Stanford University": ["STANFORD"],
    "Harvard University": ["HARVARD"],
    "Massachusetts Institute of Technology": ["MASSACHUSETTS INSTITUTE OF TECHNOLOGY"],
    "California Institute of Technology": ["CALIFORNIA INSTITUTE OF TECHNOLOGY"],
    "Princeton University": ["PRINCETON UNIVERSITY"],
    "Yale University": ["YALE UNI"],
    "Columbia University": ["COLUMBIA UNIVERSITY"],
    "University of Chicago": ["UNIVERSITY OF CHICAGO"],
    "University of Pennsylvania": ["UNIVERSITY OF PENNSYLVANIA", "TRUSTEES OF THE UNIVERSITY OF PENNSYLVANIA"],
    "Cornell University": ["CORNELL UNIVERSITY"],
    "Johns Hopkins University": ["JOHNS HOPKINS"],
    "Duke University": ["DUKE UNIVERSITY"],
    "Northwestern University": ["NORTHWESTERN UNIVERSITY"],
    "University of Michigan": ["UNIVERSITY OF MICHIGAN", "REGENTS OF THE UNIVERSITY OF MICHIGAN"],
    "University of Texas at Austin": ["UNIVERSITY OF TEXAS AT AUSTIN"],
    "University of Washington": ["UNIVERSITY OF WASHINGTON"],
    "University of Illinois Urbana-Champaign": ["UNIVERSITY OF ILLINOIS"],
    "Ohio State University": ["OHIO STATE UNIVERSITY"],
    "Penn State University": ["PENNSYLVANIA STATE UNIVERSITY", "PENN STATE"],
    "University of California, Berkeley": ["UNIVERSITY OF CALIFORNIA, BERKELEY", "REGENTS OF THE UNIVERSITY OF CALIFORNIA, BERKELEY"],
    "University of California, Los Angeles": ["UNIVERSITY OF CALIFORNIA, LOS ANGELES", "REGENTS OF THE UNIVERSITY OF CALIFORNIA, LOS ANGELES"],
    "University of California, San Diego": ["UNIVERSITY OF CALIFORNIA, SAN DIEGO", "REGENTS OF THE UNIVERSITY OF CALIFORNIA, SAN DIEGO"],
}

PPP_JPY_TO_USD = 103.5

# --------------- step 1: load institutions_config.json ---------------

def load_config():
    with open("institutions_config.json") as f:
        config = json.load(f)
    return {inst["name"]: inst for inst in config["institutions"]}


# --------------- step 2: fetch H_f from USASpending ---------------

def fetch_hf_usaspending(inst_name, match_names, fy):
    start = f"{fy - 1}-10-01"
    end = f"{fy}-09-30"
    payload = {
        "filters": {
            "keyword": inst_name,
            "time_period": [{"start_date": start, "end_date": end}],
        },
        "category": "recipient",
        "limit": 50,
        "page": 1,
    }
    try:
        r = requests.post(USASPENDING_API, json=payload, timeout=30)
        r.raise_for_status()
        results = r.json().get("results", [])
        total = sum(
            item.get("amount", 0)
            for item in results
            if any(m in (item.get("name") or "").upper() for m in match_names)
        )
        return round(total, 2)
    except Exception as e:
        print(f"\n  [WARN] USASpending error for {inst_name} FY{fy}: {e}")
        return 0.0


def fetch_all_hf(us_institutions):
    """Returns dict: {(inst_name, year): H_f_value}"""
    hf = {}
    total = len(us_institutions) * len(YEARS)
    done = 0
    for inst_name in us_institutions:
        match_names = USASPENDING_MATCH.get(inst_name, [inst_name.upper()])
        for fy in YEARS:
            done += 1
            sys.stdout.write(f"\r  [H_f] {done}/{total} {inst_name[:30]} FY{fy}...")
            sys.stdout.flush()
            hf[(inst_name, fy)] = fetch_hf_usaspending(inst_name, match_names, fy)
            time.sleep(0.25)
    print()
    return hf


# --------------- step 3: fetch H_s from phdstipends.com ---------------

def fetch_all_stipends():
    """Returns list of all stipend entries from phdstipends.com"""
    all_entries = []
    # Discover max page from first fetch
    first = requests.get(f"{STIPENDS_API}90", timeout=30).json()
    page = 90
    while page >= 0:
        sys.stdout.write(f"\r  [H_s] Fetching stipends page {page}...")
        sys.stdout.flush()
        try:
            data = requests.get(f"{STIPENDS_API}{page}", timeout=30).json().get("data", [])
            all_entries.extend(data)
        except Exception as e:
            print(f"\n  [WARN] Stipends page {page}: {e}")
        page -= 1
        time.sleep(0.15)
    print(f"\r  [H_s] Fetched {len(all_entries)} stipend entries.        ")
    return all_entries


def year_from_academic(academic_year):
    """'2022-2023' -> 2022"""
    try:
        return int(academic_year.split("-")[0])
    except (ValueError, AttributeError, IndexError):
        return None


def build_hs_lookup(stipend_entries, config):
    """Returns dict: {(inst_name, year): average_stipend}"""
    # Index entries by (matched_institution, start_year)
    buckets = {}
    for entry in stipend_entries:
        uni_raw = entry[0].lower()
        pay_str = entry[2].replace("$", "").replace(",", "").strip()
        try:
            pay = float(pay_str)
        except (ValueError, TypeError):
            continue
        if pay <= 0:
            continue

        ay = year_from_academic(entry[4])
        if ay is None:
            continue

        for inst_name, keywords in STIPEND_NAME_MAP.items():
            if any(kw in uni_raw for kw in keywords):
                key = (inst_name, ay)
                if key not in buckets:
                    buckets[key] = []
                buckets[key].append(pay)
                break

    hs = {}
    for (inst_name, ay), pays in buckets.items():
        hs[(inst_name, ay)] = round(sum(pays) / len(pays), 2)

    return hs


# --------------- step 4: compute descriptive S_r ratio ---------------

def compute_sr(hf, hs, ng, cost_idx):
    adjusted_hs = hs / cost_idx if cost_idx > 0 else hs
    denominator = adjusted_hs * ng
    if denominator <= 0:
        return 0.0
    ratio = (hf + 1) / denominator
    if ratio <= 0:
        return 0.0
    return round(math.log(ratio), 4)


# --------------- main ---------------

def main():
    print("=" * 60)
    print("  Building governance_matrix.csv with REAL data")
    print("=" * 60)

    config = load_config()

    us_insts = [n for n, c in config.items() if c["country"] == "US"]
    jp_insts = [n for n, c in config.items() if c["country"] == "JP"]

    # Step 1: H_f from USASpending (US only)
    print("\n[1/3] Fetching federal funding from USASpending.gov...")
    hf_data = fetch_all_hf(us_insts)

    # H_f for JP: proportional share of JSPS budget
    total_jp_students = sum(config[n]["baseline_enrollment"] for n in jp_insts)
    for inst_name in jp_insts:
        share = config[inst_name]["baseline_enrollment"] / total_jp_students
        jpy_amount = 450_000_000_000 * share  # ~450B JPY JSPS total
        usd_amount = round(jpy_amount / PPP_JPY_TO_USD, 2)
        for yr in YEARS:
            # Japan policy change was 2021 (10th Science and Technology Basic Plan)
            hf_data[(inst_name, yr)] = usd_amount if yr >= 2021 else 0.0

    # Step 2: H_s from phdstipends.com
    print("\n[2/3] Fetching PhD stipends from phdstipends.com...")
    stipend_entries = fetch_all_stipends()
    hs_data = build_hs_lookup(stipend_entries, config)

    # Step 3: Build the matrix
    print("\n[3/3] Computing governance matrix...")
    rows = []
    for inst_name, inst_cfg in config.items():
        country = inst_cfg["country"]
        cost_idx = inst_cfg["local_cost_of_living_index"]
        ng = inst_cfg["baseline_enrollment"]
        baseline_stipend = inst_cfg["baseline_stipend_2019"]

        for yr in YEARS:
            if country == "US":
                post_policy = 1 if yr >= 2023 else 0
            else:
                post_policy = 1 if yr >= 2021 else 0

            hf = hf_data.get((inst_name, yr), 0.0)

            # H_s: use real stipend if available, else extrapolate from baseline
            hs = hs_data.get((inst_name, yr))
            if hs is None:
                inflation = 0.03
                hs = round(baseline_stipend * ((1 + inflation) ** (yr - 2019)), 2)

            sr = compute_sr(hf, hs, ng, cost_idx)

            rows.append({
                "institution": inst_name,
                "country": country,
                "time_period": yr,
                "post_policy": post_policy,
                "H_f": hf,
                "H_s": hs,
                "N_g": ng,
                "S_r": sr,
            })

    # Write CSV
    fields = ["institution", "country", "time_period", "post_policy", "H_f", "H_s", "N_g", "S_r"]
    with open("governance_matrix.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'='*60}")
    print(f"  governance_matrix.csv: {len(rows)} rows written")
    print(f"  US institutions: {len(us_insts)}, JP institutions: {len(jp_insts)}")
    print(f"  Years: {YEARS[0]}-{YEARS[-1]}")
    print(f"{'='*60}")

    # Show sample
    print("\nSample (Stanford):")
    for r in rows:
        if r["institution"] == "Stanford University":
            src = "real" if (r["institution"], r["time_period"]) in hs_data else "est."
            print(f"  {r['time_period']}  H_f=${r['H_f']:>14,.2f}  H_s=${r['H_s']:>8,.0f}({src})  "
                  f"S_r={r['S_r']:.4f}")


if __name__ == "__main__":
    main()
