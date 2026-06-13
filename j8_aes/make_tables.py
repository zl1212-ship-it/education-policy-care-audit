"""Manuscript tables, written as data/table_*.csv.

  Table 1: corpus descriptives -- essays, human-score mean/SD, and subgroup
           shares per corpus.
  Table 2: scorer quality -- QWK, Pearson r, RMSE per family and protocol
           (gap results must be read against engine quality).
  Table 3: machine-minus-human gaps -- per-group mean gap, SMD, QWK, and the
           raw + conditional focal-minus-reference differentials with 95% CIs
           (primary contrast and protocol ordered first).
  Table 4: decision layer -- human/machine pass rates and demotion rates by
           group and cutoff, with the demotion differential.

Inputs : data/panel_*.csv, data/scorer_quality.csv, data/results_gaps.csv,
         data/results_decision.csv
Outputs: data/table_{1,2,3,4}.csv
Run after analyze_gaps.py.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
FAMILIES = ["handfeat", "tfidf", "embed", "finetuned"]


def table1() -> pd.DataFrame:
    rows = []
    p = pd.read_csv(DATA / "panel_persuade.csv")
    e = pd.read_csv(DATA / "panel_ellipse.csv")
    for corpus, df, score, dims in [
        ("PERSUADE 2.0", p, "holistic_essay_score",
         ["ell_status", "race_ethnicity", "economically_disadvantaged",
          "student_disability_status", "gender"]),
        ("ELLIPSE", e, "Overall",
         ["SES", "race_ethnicity", "gender", "grade"]),
    ]:
        rows.append({"corpus": corpus, "variable": "essays",
                     "level": "", "value": len(df)})
        rows.append({"corpus": corpus, "variable": "human score mean (SD)",
                     "level": "",
                     "value": f"{df[score].mean():.2f} ({df[score].std():.2f})"})
        for d in dims:
            for level, n in df[d].value_counts(dropna=False).items():
                rows.append({
                    "corpus": corpus, "variable": d,
                    "level": "missing" if pd.isna(level) else str(level),
                    "value": f"{n} ({n / len(df):.1%})"})
    return pd.DataFrame(rows)


def table3(gaps: pd.DataFrame) -> pd.DataFrame:
    keep_groups = ["mean_gap", "smd", "qwk"]
    rows = []
    for (corpus, dim), sub in gaps.groupby(["corpus", "dimension"],
                                           sort=False):
        for fam in FAMILIES:
            for proto in ["oof", "lopo"]:
                s = sub[(sub.family == fam) & (sub.protocol == proto)]
                for grp in s.group.unique():
                    g = s[s.group == grp]
                    row = {"corpus": corpus, "dimension": dim,
                           "family": fam, "protocol": proto, "group": grp,
                           "n": int(g.n.iloc[0])}
                    if " - " in grp:  # differential rows
                        for m in ["raw_differential",
                                  "conditional_differential"]:
                            r = g[g.metric == m]
                            if len(r):
                                row[m] = (f"{r.value.iloc[0]:+.3f} "
                                          f"[{r.ci_lo.iloc[0]:+.3f}, "
                                          f"{r.ci_hi.iloc[0]:+.3f}]")
                    else:
                        for m in keep_groups:
                            r = g[g.metric == m]
                            if len(r):
                                row[m] = r.value.iloc[0]
                    rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    for f in ["scorer_quality.csv", "results_gaps.csv",
              "results_decision.csv"]:
        if not (DATA / f).exists():
            print(f"Missing data/{f}. Run analyze_gaps.py first.",
                  file=sys.stderr)
            return 1

    t1 = table1()
    t1.to_csv(DATA / "table_1.csv", index=False)

    t2 = pd.read_csv(DATA / "scorer_quality.csv")
    t2.to_csv(DATA / "table_2.csv", index=False)

    gaps = pd.read_csv(DATA / "results_gaps.csv")
    t3 = table3(gaps)
    t3.to_csv(DATA / "table_3.csv", index=False)

    t4 = pd.read_csv(DATA / "results_decision.csv")
    t4.to_csv(DATA / "table_4.csv", index=False)

    for i, t in enumerate([t1, t2, t3, t4], 1):
        print(f"table_{i}.csv: {len(t)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
