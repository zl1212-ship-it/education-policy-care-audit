"""
Coverage / missingness by outcome and treatment status, 2009-2019.
Computed from the existing panels (no API pull). Shows that the admissions-reported outcomes
(applications, admit rate, score submission) have lower and selection-prone coverage because
open-admission and less-selective institutions do not report them, while the enrollment-reported
outcomes (racial composition, Pell) are near-universal. Writes data/coverage.csv.
"""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
YEARS = list(range(2009, 2020))

adm = pd.read_csv(os.path.join(DATA, "panel_treated.csv"))
for c in ["applied", "admit_rate", "sat_pct_submit", "act_pct_submit"]:
    adm[c] = pd.to_numeric(adm[c], errors="coerce")
comp = pd.read_csv(os.path.join(DATA, "composition_panel.csv"))
pell = pd.read_csv(os.path.join(DATA, "pell_panel.csv"))
treat = pd.read_csv(os.path.join(DATA, "treatment_panel.csv"))

treated = set(treat.loc[treat.cohort == "pre_covid", "unitid"])
never = set(treat.loc[treat.cohort == "never", "unitid"])
panel = {
    "Applications": adm[["unitid", "year", "applied"]].rename(columns={"applied": "v"}),
    "Admit rate": adm[["unitid", "year", "admit_rate"]].rename(columns={"admit_rate": "v"}),
    "SAT submission": adm[["unitid", "year", "sat_pct_submit"]].rename(columns={"sat_pct_submit": "v"}),
    "ACT submission": adm[["unitid", "year", "act_pct_submit"]].rename(columns={"act_pct_submit": "v"}),
    "Entering %URM": comp[["unitid", "year", "share_urm"]].rename(columns={"share_urm": "v"}),
    "Entering %Pell": pell[["unitid", "year", "pell_share"]].rename(columns={"pell_share": "v"}),
}


def coverage(df, group):
    d = df[(df.unitid.isin(group)) & (df.year.between(2009, 2019))]
    nonmiss = d.dropna(subset=["v"])
    inst_years = len(group) * len(YEARS)
    return len(nonmiss), 100 * len(nonmiss) / inst_years


rows = []
for name, df in panel.items():
    nt, ct = coverage(df, treated); nn, cn = coverage(df, never)
    rows.append({"outcome": name, "treated_inst_years": nt, "treated_cov_pct": round(ct, 0),
                 "never_inst_years": nn, "never_cov_pct": round(cn, 0)})
    print(f"  {name:16s} treated {nt:5d} ({ct:3.0f}%)   never {nn:6d} ({cn:3.0f}%)")
pd.DataFrame(rows).to_csv(os.path.join(DATA, "coverage.csv"), index=False)
print("\nwrote data/coverage.csv")
