"""
Build the state-board governance panel (50 states + DC).

Parses the NASBE State Education Governance Matrix (July 2024) into coded variables, merges
NCES enrollment and demographics, the ECS school-accountability rating type, and the NCES
NAEP-mapped grade-4 math proficiency cut, and computes two 0-1 indices:

  rep_index   0.50 * frac_elected_public + 0.25 * student_voice + 0.25 * teacher_voice
              (seat voice: voting seat = 1, nonvoting seat = 0.5, none = 0)
  auth_index  mean(standards adoption, teacher licensure, constitutional establishment)

Inputs : data/nasbe_governance_matrix_2024.csv, data/state_demographics.csv,
         data/state_accountability_2024.csv, data/state_proficiency_stringency.csv
Output : data/governance_panel.csv (one row per state; raw NASBE strings kept for tracing)
"""
import os, re
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# keep_default_na=False so the literal strings "None"/"NA" in the matrix are preserved
gov = pd.read_csv(os.path.join(DATA, "nasbe_governance_matrix_2024.csv"), keep_default_na=False)
dem = pd.read_csv(os.path.join(DATA, "state_demographics.csv"))   # blank Alaska FRL -> NaN

# Board-selection regime, classified from the NASBE matrix (51 units).
ELECTED = {"AL", "CO", "KS", "MI", "NE", "TX", "UT", "DC"}   # all voting members by public ballot
HYBRID = {"LA", "NV", "OH", "WA"}                            # publicly elected subset + appointed
LEGISLATIVE = {"NY", "SC"}                                   # appointed by the legislature
NONE = {"MN", "NM", "ND", "WI"}                              # no state board


def first_int(s):
    """Leading integer of the voting-members string (principal voting membership)."""
    m = re.search(r"\d+", str(s))
    return int(m.group()) if m else np.nan


def board_regime(row):
    a = row.state_abbr
    if a in NONE:
        return "none"
    if a in ELECTED:
        return "elected"
    if a in HYBRID:
        return "hybrid"
    if a in LEGISLATIVE:
        return "legislative"
    return "governor"   # appointed by the governor (with/without senate confirmation)


def frac_elected_public(row):
    """Fraction of voting members chosen by a general-public ballot."""
    reg = row.board_regime
    if reg == "elected":
        return 1.0
    if reg in ("governor", "legislative", "none"):
        return 0.0
    # hybrid boards: elected seat counts taken from the NASBE text
    n = row.n_voting
    elected_n = {
        "louisiana": 8,   # 8 elected by nonpartisan ballot; governor appoints 3
        "nevada": 4,      # 4 elected; governor appoints 3
        "ohio": 11,       # 11 elected by nonpartisan ballot; governor appoints 8
        "washington": 0,  # 5 chosen by local school boards / 1 by private schools, not a public ballot
    }.get(str(row.state).lower())
    if elected_n is not None and pd.notna(n) and n > 0:
        return round(elected_n / n, 4)
    return np.nan


def has_voting_student(s):
    """A student inside the voting membership: present before any 'plus N nonvoting' clause.
    NASBE lists such students within the 'number of voting members' column (e.g. MD, TN);
    students appearing only after 'plus ... nonvoting' do not vote."""
    head = re.split(r"\bplus\b", str(s).lower())[0]
    return int("student" in head and "nonvoting" not in head)


def has_voting_teacher(s):
    """A teacher inside the voting membership, i.e. before any 'plus N nonvoting members' clause."""
    head = re.split(r"\bplus\b", str(s).lower())[0]
    return int("teacher" in head and "nonvoting" not in head)


def has_any_student(s):
    return int("student" in str(s).lower())


def has_any_teacher(s):
    return int("teacher" in str(s).lower())


gov["board_regime"] = gov.apply(board_regime, axis=1)
gov["board_exists"] = (gov.board_regime != "none").astype(int)
gov["n_voting"] = gov.n_voting_raw.apply(first_int)
gov["frac_elected_public"] = gov.apply(frac_elected_public, axis=1)
gov["student_voting"] = gov.n_voting_raw.apply(has_voting_student)
gov["teacher_voting"] = gov.n_voting_raw.apply(has_voting_teacher)
gov["student_present"] = gov.n_voting_raw.apply(has_any_student)
gov["teacher_present"] = gov.n_voting_raw.apply(has_any_teacher)
# seat voice: voting seat = 1, nonvoting seat = 0.5, none = 0
gov["student_voice"] = np.where(gov.student_voting == 1, 1.0, np.where(gov.student_present == 1, 0.5, 0.0))
gov["teacher_voice"] = np.where(gov.teacher_voting == 1, 1.0, np.where(gov.teacher_present == 1, 0.5, 0.0))
gov["term_years"] = pd.to_numeric(gov.term_raw, errors="coerce")
gov["constitutional"] = gov.established_raw.str.contains("Constitution", na=False).astype(int)


# CSSO selection regime
def csso_regime(s):
    t = str(s).lower()
    if "ballot" in t:
        return "elected"
    if "sbe appoints" in t or ("sbe" in t and "appoint" in t and "governor" not in t):
        return "board"
    if "council appoints" in t:
        return "board"
    if "mayor" in t:
        return "executive"
    return "governor"


gov["csso_regime"] = gov.sel_csso_raw.apply(csso_regime)

# Authority components
gov["auth_standards_board"] = (gov.auth_standards == "SBE").astype(int)
gov["auth_licensure_board"] = gov.auth_licensure.map(
    {"SBE": 1.0, "PSC": 0.5}).fillna(0.0)         # SEA / CSSO / None -> 0
gov.loc[gov.board_exists == 0,
        ["auth_licensure_board", "auth_standards_board", "constitutional"]] = np.nan

# ---- Indices (states with a board only) ----
W = dict(elect=0.50, student=0.25, teacher=0.25)
gov["rep_index"] = (W["elect"] * gov.frac_elected_public
                    + W["student"] * gov.student_voice
                    + W["teacher"] * gov.teacher_voice)
gov["rep_index_equal"] = gov[["frac_elected_public", "student_voice", "teacher_voice"]].mean(axis=1)
gov["auth_index"] = gov[["auth_standards_board", "auth_licensure_board", "constitutional"]].mean(axis=1)
gov.loc[gov.board_exists == 0, ["rep_index", "rep_index_equal", "auth_index"]] = np.nan
gov["gap"] = gov.auth_index - gov.rep_index

# Alternative coding: count Washington's members chosen by local school boards (5) and
# private schools (1) as elected
gov["frac_elected_alt"] = gov.frac_elected_public
wa = gov.state == "Washington"
gov.loc[wa, "frac_elected_alt"] = round(6 / gov.loc[wa, "n_voting"].iloc[0], 4)
gov["rep_index_altWA"] = (W["elect"] * gov.frac_elected_alt
                          + W["student"] * gov.student_voice
                          + W["teacher"] * gov.teacher_voice)
gov.loc[gov.board_exists == 0, "rep_index_altWA"] = np.nan

# ---- Merge NCES enrollment and demographics ----
out = gov.merge(dem, on="state_abbr", how="left")
out["pct_students_of_color"] = 100 - out["pct_white_2021"]

# ---- Merge school-accountability rating type (ECS 2024) ----
acct = pd.read_csv(os.path.join(DATA, "state_accountability_2024.csv"))[
    ["state_abbr", "rating_category", "rating_raw"]]
out = out.merge(acct, on="state_abbr", how="left")
# 1 if the rating is a single formula-based letter, star, or index score
out["algorithmic_grade"] = out.rating_category.isin(["A-F", "Star", "Index"]).astype(int)
# 1 if the state assigns any single summative rating (adds descriptive labels)
out["summative_any"] = out.rating_category.isin(["A-F", "Star", "Index", "Descriptive"]).astype(int)

# ---- Merge NAEP-mapped grade-4 math proficiency cut (NCES 2021-036) ----
stg = pd.read_csv(os.path.join(DATA, "state_proficiency_stringency.csv"))
out = out.merge(stg, on="state_abbr", how="left")

cols = ["state", "state_abbr", "board_regime", "board_exists", "csso_regime",
        "n_voting", "term_years", "constitutional",
        "frac_elected_public", "student_voting", "teacher_voting", "student_present",
        "teacher_present", "student_voice", "teacher_voice",
        "auth_standards_board", "auth_licensure_board",
        "rep_index", "rep_index_equal", "rep_index_altWA", "auth_index", "gap",
        "rating_category", "algorithmic_grade", "summative_any", "naep_g4_math_equiv",
        "enrollment_2021", "pct_white_2021", "pct_students_of_color", "pct_frl_2122",
        "sel_board_raw", "sel_csso_raw", "n_voting_raw", "term_raw", "established_raw",
        "auth_licensure", "auth_standards"]
out = out[cols]
out.to_csv(os.path.join(DATA, "governance_panel.csv"), index=False)
print(f"wrote {len(out)} rows to {os.path.join(DATA, 'governance_panel.csv')}")
