import requests
import csv
import time
import sys

BASE_URL = "https://www.phdstipends.com/data/"

HEADERS_ROW = [
    "university",
    "department",
    "overall_pay",
    "lw_ratio",
    "academic_year",
    "program_year",
    "comments",
    "gross_pay_12m",
    "gross_pay_9m",
    "gross_pay_3m",
    "fees",
]


def clean_money(val):
    if not val or val.strip() == "":
        return ""
    return val.replace("$", "").replace(",", "").strip()


def fetch_page(page_num):
    r = requests.get(f"{BASE_URL}{page_num}", timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])


def main():
    first_page = fetch_page(90)
    if not first_page:
        print("ERROR: could not fetch first page")
        return

    all_rows = []

    for page in range(90, -1, -1):
        sys.stdout.write(f"\r[{90 - page + 1}/91] Fetching page {page}...")
        sys.stdout.flush()
        try:
            rows = fetch_page(page)
            all_rows.extend(rows)
        except Exception as e:
            print(f"\n  ERROR on page {page}: {e}")
        time.sleep(0.2)

    print(f"\n\nFetched {len(all_rows)} total entries. Writing CSV...")

    with open("phd_stipends.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS_ROW)
        for row in all_rows:
            cleaned = [
                row[0],                    # university
                row[1],                    # department
                clean_money(row[2]),       # overall_pay
                row[3],                    # lw_ratio
                row[4],                    # academic_year
                row[5],                    # program_year
                row[6],                    # comments
                clean_money(row[7]),       # gross_pay_12m
                clean_money(row[8]),       # gross_pay_9m
                clean_money(row[9]),       # gross_pay_3m
                clean_money(row[10]),      # fees
            ]
            writer.writerow(cleaned)

    print(f"Done! phd_stipends.csv written with {len(all_rows)} rows.")

    print("\nSample data:")
    for row in all_rows[:5]:
        print(f"  {row[0]:50s} {row[1]:30s} {row[2]:>10s}  LW:{row[3]:>5s}  {row[4]}")


if __name__ == "__main__":
    main()
