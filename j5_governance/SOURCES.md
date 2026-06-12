# Data sources — (governance representation audit)

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

## 3. School-accountability rating type
`data/state_accountability_2024.csv`
- **Source:** Education Commission of the States (ECS), *50-State Comparison: States' School
  Accountability Systems* (2024), "Rating System" field.
  URL: https://reports.ecs.org/comparisons/states-school-accountability-systems-2024
- **Coverage:** 50 states + DC. Each state's summative rating type transcribed from the ECS
  "Rating System" column: A-F letter grade (6), 1-5 star (4), numeric/index (14), descriptive
  labels (12), federal tiers of support only (14), dashboard / no summative (1, California).
- **Derived:** `algorithmic_grade` = 1 if the state reduces school performance to a single
  formula-driven score/letter/star (A-F, star, or numeric index), else 0. `summative_any` = 1 if
  the state assigns any single summative rating (adds descriptive labels), else 0.

## 4. Academic-standard stringency (governance output)
`data/state_proficiency_stringency.csv`
- **Source:** NCES, *Mapping State Proficiency Standards Onto the NAEP Scales: Results From the
  2019 NAEP Reading and Mathematics Assessments* (NCES 2021-036), Technical Notes Table A-1.
  URL: https://nces.ed.gov/nationsreportcard/subject/publications/studies/pdf/2021036a.pdf
- **Field:** `naep_g4_math_equiv` = the NAEP-scale equivalent of each state's grade-4 mathematics
  "proficient" cut (higher = more demanding standard). Grade-4 math chosen for coverage (only New
  Hampshire unmapped). This is a board-discretionary policy output (the board sets/approves the
  state's academic standards), used to test the representative-bureaucracy prediction.

## Coding rules
Coded variables are derived from the raw NASBE strings in `build_governance_panel.py`; the raw
columns are retained in the panel so every coded value is traceable to its source text.
- `board_regime`: elected (all voting members chosen by public ballot), hybrid (mix of elected
  and appointed), legislative (appointed by the legislature), governor (appointed by the
  governor, with or without senate confirmation), none (no state board).
- `frac_elected_public`: fraction of voting members chosen by general-public ballot. Washington's
  members elected by local school-board members / private schools are counted as 0 here (not a
  general-public election) and given partial credit in a robustness check.
