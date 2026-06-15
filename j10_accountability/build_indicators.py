"""School-level accountability indicators from public federal collections.

Assembles, for every school in data/school_frame.csv, the components a state ESSA
composite is built from (CODEBOOK_indicators.md):

  achievement  - math and reading percent proficient (EDFacts assessments, grade 99)
  grad         - adjusted-cohort graduation rate (EDFacts ACGR)
  quality      - 100 - chronic-absenteeism rate (CRDC, inverted so higher = better)
  econ_disadv_share - economically-disadvantaged share of tested students (poverty)

EDFacts and CRDC release small cells as negative suppression codes; those are read as
missing. Proficiency and graduation are published as disclosure ranges and the audit
uses the range midpoint, carrying num_valid so the binning stays auditable. Raw
per-state, per-endpoint JSON is cached under data/raw/indicators/.

Run:  python3 build_indicators.py
      python3 build_indicators.py --assess-year 2018 --crdc-year 2017 --states OH MS

Source + column meanings: SOURCES.md. Stdlib networking (urllib) + pandas only.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw" / "indicators"
FRAME = HERE / "data" / "school_frame.csv"
OUT = HERE / "data" / "indicators.csv"
BASE = "https://educationdata.urban.org/api/v1"

# default source years: last pre-pause accountability cycle (SY2018-19) + nearest CRDC
DEFAULT_ASSESS = 2018
DEFAULT_PRIOR = 2017  # prior achievement year, for the growth proxy
DEFAULT_GRAD = 2018
DEFAULT_CRDC = 2017


def fetch(path, fips, year, tag, extra=""):
    """Page an Urban portal endpoint for one state; cache the concatenated rows."""
    cache = RAW / f"{tag}_{year}_{fips:02d}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    rows = []
    url = f"{BASE}/{path}?fips={fips}&limit=10000{extra}"
    while url:
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    payload = json.loads(r.read().decode())
                break
            except (urllib.error.URLError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        rows.extend(payload.get("results", []))
        url = payload.get("next")
        if url:
            time.sleep(0.3)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows))
    return rows


def clean(v):
    """EDFacts/CRDC negative codes (-1,-2,-3,-9) mark suppressed/missing cells."""
    v = pd.to_numeric(v, errors="coerce")
    return v.where(v >= 0)


def all_students(df):
    """Keep the all-students marginal; tolerate empty / schema-variant responses."""
    if df.empty or "econ_disadvantaged" not in df.columns:
        return df.iloc[0:0]
    return df[df["econ_disadvantaged"] == 99].copy()


def achievement_table(fips, year):
    """Math + reading proficiency (all students) and the poverty share."""
    base = all_students(pd.DataFrame(fetch(
        f"schools/edfacts/assessments/{year}/grade-99/", fips, year, "assess")))
    if base.empty:
        return pd.DataFrame(columns=["ncessch", "achievement", "achv_n",
                                     "math_prof", "read_prof", "econ_disadv_share"])
    for s in ("math", "read"):
        base[f"{s}_prof"] = clean(base[f"{s}_test_pct_prof_midpt"])
        base[f"{s}_n"] = clean(base[f"{s}_test_num_valid"])
    base["achievement"] = base[["math_prof", "read_prof"]].mean(axis=1)
    base["achv_n"] = base[["math_n", "read_n"]].max(axis=1)

    # economically-disadvantaged marginal (other special-pop dims held at 99)
    sp = pd.DataFrame(fetch(
        f"schools/edfacts/assessments/{year}/grade-99/special-populations/",
        fips, year, "assess_sp", extra="&econ_disadvantaged=1"))
    dims = ["race", "sex", "lep", "disability", "homeless", "migrant",
            "foster_care", "military_connected"]
    if not sp.empty and all(d in sp.columns for d in dims):
        keep = (sp[dims] == 99).all(axis=1)
        sp = sp[keep].copy()
        sp["econ_n"] = clean(sp["math_test_num_valid"]).fillna(
            clean(sp["read_test_num_valid"]))
        sp = sp.groupby("ncessch", as_index=False)["econ_n"].max()
    else:
        sp = pd.DataFrame(columns=["ncessch", "econ_n"])

    t = base[["ncessch", "achievement", "achv_n", "math_prof", "read_prof"]].merge(
        sp, on="ncessch", how="left")
    t["all_n"] = base.set_index("ncessch").loc[t["ncessch"], "achv_n"].values
    t["econ_disadv_share"] = (t["econ_n"] / t["all_n"]).clip(upper=1.0)
    return t.drop(columns=["econ_n", "all_n"])


def prior_achievement(fips, year):
    """All-student achievement for a prior year (the growth-proxy baseline)."""
    base = pd.DataFrame(fetch(
        f"schools/edfacts/assessments/{year}/grade-99/", fips, year, "assess"))
    base = all_students(base)
    if base.empty:
        return pd.DataFrame(columns=["ncessch", "achievement_prior"])
    for s in ("math", "read"):
        base[f"{s}_prof"] = clean(base[f"{s}_test_pct_prof_midpt"])
    base["achievement_prior"] = base[["math_prof", "read_prof"]].mean(axis=1)
    return base[["ncessch", "achievement_prior"]].dropna(subset=["achievement_prior"])


def grad_table(fips, year):
    g = all_students(pd.DataFrame(
        fetch(f"schools/edfacts/grad-rates/{year}/", fips, year, "grad")))
    if g.empty:
        return pd.DataFrame(columns=["ncessch", "grad"])
    g["grad"] = clean(g["grad_rate_midpt"])
    g = g.dropna(subset=["grad"]).groupby("ncessch", as_index=False)["grad"].mean()
    return g


def quality_table(fips, year, enroll):
    c = pd.DataFrame(fetch(
        f"schools/crdc/chronic-absenteeism/{year}/race/sex/", fips, year, "crdc",
        extra="&race=99&sex=99"))
    sub_dims = [d for d in ("disability", "lep", "homeless") if d in c.columns]
    if c.empty or "students_chronically_absent" not in c.columns:
        return pd.DataFrame(columns=["ncessch", "quality", "chronic_absent_rate"])
    keep = (c[sub_dims] == 99).all(axis=1) if sub_dims else pd.Series(True, index=c.index)
    c = c[keep].copy()
    c["absent"] = clean(c["students_chronically_absent"])
    c = c.groupby("ncessch", as_index=False)["absent"].max()
    c = c.merge(enroll, on="ncessch", how="left")
    c["chronic_absent_rate"] = (100 * c["absent"] / c["enrollment"]).clip(0, 100)
    c["quality"] = 100 - c["chronic_absent_rate"]
    return c[["ncessch", "quality", "chronic_absent_rate"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assess-year", type=int, default=DEFAULT_ASSESS)
    ap.add_argument("--prior-assess-year", type=int, default=DEFAULT_PRIOR)
    ap.add_argument("--grad-year", type=int, default=DEFAULT_GRAD)
    ap.add_argument("--crdc-year", type=int, default=DEFAULT_CRDC)
    ap.add_argument("--states", nargs="*")
    args = ap.parse_args()

    frame = pd.read_csv(FRAME, dtype={"ncessch": str})
    if args.states:
        frame = frame[frame["state"].isin([s.upper() for s in args.states])]
    enroll = frame[["ncessch", "enrollment"]].copy()

    out = []
    for fips, sub in frame.groupby("fips"):
        fips = int(fips)
        a = achievement_table(fips, args.assess_year)
        p = prior_achievement(fips, args.prior_assess_year)
        g = grad_table(fips, args.grad_year)
        q = quality_table(fips, args.crdc_year, enroll[enroll.ncessch.isin(sub.ncessch)])
        m = a.merge(p, on="ncessch", how="left").merge(
            g, on="ncessch", how="outer").merge(q, on="ncessch", how="outer")
        m["fips"] = fips
        out.append(m)
        print(f"  fips {fips:>2}: achv {a.achievement.notna().sum():>5}  "
              f"grad {g.grad.notna().sum():>5}  qual {q.quality.notna().sum():>5}",
              file=sys.stderr)

    ind = pd.concat(out, ignore_index=True)
    ind["assess_year"] = args.assess_year
    ind["grad_year"] = args.grad_year
    ind["crdc_year"] = args.crdc_year
    ind = ind[ind["ncessch"].isin(frame["ncessch"])].copy()
    ind.to_csv(OUT, index=False)
    print(f"\nindicators.csv: {len(ind):,} schools  "
          f"(achievement {ind.achievement.notna().sum():,}, "
          f"grad {ind.grad.notna().sum():,}, quality {ind.quality.notna().sum():,}, "
          f"poverty {ind.econ_disadv_share.notna().sum():,}) -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
