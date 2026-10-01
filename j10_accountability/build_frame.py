"""National school frame from the NCES Common Core of Data (CCD).

One row per school for all states and DC, pulled from the CCD directory endpoint on
the Urban Institute Education Data Portal. The frame defines the universe over which
the ESSA identification rule is reconstructed in weight_space.py and supplies the
predetermined school characteristics (level, enrollment, Title I status, locale,
charter / virtual flags). Raw per-state JSON pages are cached under data/raw/frame/
so re-runs are free; only the assembled data/school_frame.csv is committed.

Run:  python3 build_frame.py            # all states + DC, cached
      python3 build_frame.py --year 2019
      python3 build_frame.py --states OH TX MS   # subset by USPS code

Source + column meanings: SOURCES.md. Stdlib networking (urllib) + pandas only.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw" / "frame"
OUT = HERE / "data" / "school_frame.csv"
API = "https://educationdata.urban.org/api/v1/schools/ccd/directory/{year}/"
DEFAULT_YEAR = 2019  # last pre-pause accountability year (CODEBOOK_indicators.md)

# USPS -> FIPS for the 50 states + DC (the CCD universe used here)
FIPS = {
    "AL": 1, "AK": 2, "AZ": 4, "AR": 5, "CA": 6, "CO": 8, "CT": 9, "DE": 10,
    "DC": 11, "FL": 12, "GA": 13, "HI": 15, "ID": 16, "IL": 17, "IN": 18,
    "IA": 19, "KS": 20, "KY": 21, "LA": 22, "ME": 23, "MD": 24, "MA": 25,
    "MI": 26, "MN": 27, "MS": 28, "MO": 29, "MT": 30, "NE": 31, "NV": 32,
    "NH": 33, "NJ": 34, "NM": 35, "NY": 36, "NC": 37, "ND": 38, "OH": 39,
    "OK": 40, "OR": 41, "PA": 42, "RI": 44, "SC": 45, "SD": 46, "TN": 47,
    "TX": 48, "UT": 49, "VT": 50, "VA": 51, "WA": 53, "WV": 54, "WI": 55,
    "WY": 56,
}
USPS = {v: k for k, v in FIPS.items()}

# columns kept from the directory endpoint
KEEP = [
    "ncessch", "leaid", "seasch", "state_leaid", "school_name", "lea_name", "fips",
    "school_level", "lowest_grade_offered", "highest_grade_offered",
    "school_status", "enrollment",
    "title_i_status", "title_i_eligible", "title_i_schoolwide",
    "urban_centric_locale", "charter", "magnet", "virtual",
    "free_or_reduced_price_lunch",  # secondary poverty check (mostly null under CEP)
]


def fetch_state(fips, year, pause=0.3):
    """Page the directory endpoint for one state, caching the concatenated rows."""
    cache = RAW / f"{year}_{fips:02d}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    rows, url = [], API.format(year=year) + f"?fips={fips}&limit=10000"
    while url:
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=90) as r:
                    payload = json.loads(r.read().decode())
                break
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        rows.extend(payload.get("results", []))
        url = payload.get("next")
        if url:
            time.sleep(pause)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=DEFAULT_YEAR)
    ap.add_argument("--states", nargs="*", help="USPS codes; default = all 50 + DC")
    args = ap.parse_args()

    codes = args.states or list(FIPS)
    frames = []
    for code in codes:
        fips = FIPS[code.upper()]
        rows = fetch_state(fips, args.year)
        df = pd.DataFrame(rows)
        df = df[[c for c in KEEP if c in df.columns]].copy()
        frames.append(df)
        print(f"  {code}: {len(df):>6} schools", file=sys.stderr)

    frame = pd.concat(frames, ignore_index=True)
    frame["state"] = frame["fips"].map(USPS)
    frame["year"] = args.year

    # a regular school open this year (school_status 1 = open); drop the closed/new
    frame = frame[frame["school_status"].isin([1, 3, 8])].copy()

    # high-school flag for the graduation indicator: offers grade 12
    frame["is_high"] = (frame["highest_grade_offered"] >= 12).astype(int)
    frame["title_i_eligible"] = frame["title_i_eligible"].fillna(0).astype(int)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False)
    n_t1 = int(frame["title_i_eligible"].sum())
    print(
        f"\nschool_frame.csv: {len(frame):,} schools across {frame['state'].nunique()} "
        f"states/DC ({n_t1:,} Title I eligible) -> {OUT}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
