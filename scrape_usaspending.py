import requests
import csv
import time
import sys

API_URL = "https://api.usaspending.gov/api/v2/search/spending_by_category/recipient/"

INSTITUTIONS = {
    "Stanford University": ["STANFORD", "LELAND STANFORD"],
    "Harvard University": ["HARVARD"],
    "Massachusetts Institute of Technology": ["MASSACHUSETTS INSTITUTE OF TECHNOLOGY", "MIT"],
    "California Institute of Technology": ["CALIFORNIA INSTITUTE OF TECHNOLOGY", "CALTECH"],
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

FISCAL_YEARS = list(range(2019, 2026))

FIELDS = ["institution", "country", "fiscal_year", "federal_funding_total", "award_count", "top_awarding_agency"]


def fetch_recipient_spending(keyword, fy):
    start = f"{fy - 1}-10-01"
    end = f"{fy}-09-30"
    payload = {
        "filters": {
            "keyword": keyword,
            "time_period": [{"start_date": start, "end_date": end}],
        },
        "category": "recipient",
        "limit": 50,
        "page": 1,
    }
    r = requests.post(API_URL, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("results", [])


def match_institution(results, match_names):
    total = 0.0
    count = 0
    for r in results:
        name_upper = (r.get("name") or "").upper()
        if any(m in name_upper for m in match_names):
            total += r.get("amount", 0)
            count += 1
    return total, count


def fetch_top_agency(keyword, match_names, fy):
    start = f"{fy - 1}-10-01"
    end = f"{fy}-09-30"
    payload = {
        "filters": {
            "keyword": keyword,
            "time_period": [{"start_date": start, "end_date": end}],
        },
        "category": "awarding_agency",
        "limit": 5,
        "page": 1,
    }
    try:
        r = requests.post(
            "https://api.usaspending.gov/api/v2/search/spending_by_category/awarding_agency/",
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if results:
            return results[0].get("name", "N/A")
    except Exception:
        pass
    return "N/A"


def main():
    rows = []
    total = len(INSTITUTIONS) * len(FISCAL_YEARS)
    done = 0

    for inst_name, match_names in INSTITUTIONS.items():
        keyword = inst_name
        for fy in FISCAL_YEARS:
            done += 1
            sys.stdout.write(f"\r[{done}/{total}] {inst_name} FY{fy}...")
            sys.stdout.flush()

            try:
                results = fetch_recipient_spending(keyword, fy)
                funding, award_count = match_institution(results, match_names)
            except Exception as e:
                print(f"\n  ERROR: {e}")
                funding, award_count = 0.0, 0

            rows.append({
                "institution": inst_name,
                "country": "US",
                "fiscal_year": fy,
                "federal_funding_total": round(funding, 2),
                "award_count": award_count,
                "top_awarding_agency": "N/A",
            })

            time.sleep(0.3)

    print(f"\n\nFetched {len(rows)} records. Writing CSV...")

    with open("governance_matrix.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done! governance_matrix.csv updated with {len(rows)} rows.")

    print("\nSample data:")
    for row in rows[:7]:
        print(f"  {row['institution']:45s} FY{row['fiscal_year']}  ${row['federal_funding_total']:>15,.2f}  ({row['award_count']} awards)")


if __name__ == "__main__":
    main()
