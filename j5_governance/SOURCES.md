# Data sources — J5 (governance representation audit)

All data are public and current as of June 2026. No values are imputed except where noted.

## 1. State board of education governance rules
`data/nasbe_governance_matrix_2024.csv`
- **Source:** National Association of State Boards of Education (NASBE), *State Education
  Governance Matrix*, updated July 2024.
  URL: https://nyc3.digitaloceanspaces.com/nasbe/2024/06/Governance-matrix-July-2024.pdf
- **Coverage:** 50 states + District of Columbia (territories in the source are omitted here).
- **Fields transcribed verbatim:** selection of state board members; selection of chief state
  school officer (CSSO); selection of board chair; number of voting members (with student/
  teacher seats noted); length of term; whether the board is established in statute or
  constitution; authority for teacher licensure; authority for academic-standards adoption.
- **Abbreviations (NASBE):** SBE = state board of education; SEA = state education agency;
  CSSO = chief state school officer; PSC = professional standards commission.

## 2. State public-school enrollment and student demographics
`data/state_demographics.csv`
- **Enrollment (`enrollment_2021`)** and **percent White (`pct_white_2021`)**: NCES *Digest of
  Education Statistics* 2022, Tables 203.20 and 203.70 (public elementary/secondary, fall 2021).
  `pct_students_of_color` is derived as 100 − percent White.
- **Percent eligible for free/reduced-price lunch (`pct_frl_2122`)**: NCES *Digest* 2022,
  Table 204.10 (2021-22). **Caveat:** 2021-22 FRL is distorted by pandemic-era universal meals
  and the Community Eligibility Provision (e.g., Mississippi reports 99.6%). FRL is therefore a
  noisy poverty proxy and is used only as a secondary measure; `pct_students_of_color` is the
  primary "whose interests" variable. Alaska FRL is suppressed in the source (blank here).

## Coding rules
Coded variables are derived from the raw NASBE strings in `build_governance_panel.py`; the raw
columns are retained in the panel so every coded value is traceable to its source text.
- `board_regime`: elected (all voting members chosen by public ballot), hybrid (mix of elected
  and appointed), legislative (appointed by the legislature), governor (appointed by the
  governor, with or without senate confirmation), none (no state board).
- `frac_elected_public`: fraction of voting members chosen by general-public ballot. Washington's
  members elected by local school-board members / private schools are counted as 0 here (not a
  general-public election) and given partial credit in a robustness check.
