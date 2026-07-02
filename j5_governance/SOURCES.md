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

## 5. Board-composition rules (educator representation)
`data/board_composition_rules_2026.csv`
- **What:** for each of the 47 boards, whether state law **mandates** educator/stakeholder seats,
  **bars** current educators/school employees from serving, and whether it seats a **voting** or
  **advisory** teacher. Current as of July 2026.
- **Source:** each row cites the governing statute where verified (e.g. NV `NRS 385.021`, OR
  `ORS 326.021`, NH `RSA 21-N:10`, IN `Ind. Code 20-19-2-2`, MD `Md. Educ. 2-202` + 2019 SB529),
  otherwise the NASBE *State Education Governance Matrix* (2024) and the Education Week compilation
  "How Many Seats Do Teachers Get on the State Board of Ed.?" (2018), in the `rule_source` column.
- **Caveat:** NASBE reports that eight states expressly prohibit teachers; seven are verified here
  from statute (`educator_bar`). Voting-teacher seats (AZ, MD, MS, NV, TN, WY) reconcile the NASBE
  2024 matrix (6 states) with EdWeek 2018 (4); MD (SB529, 2019) and NV (NRS 385.021, an appointed
  voting seat reserved for a teacher) are the two additions, both confirmed against statute.

## 6. Current board-member occupational background (partial census)
`data/board_members_2026.csv`
- **What:** one row per identified current board member: `occupation_note` (the biographical
  detail), `occ_category`, `is_educator` (1 if a current/former teacher, principal, superintendent,
  or education professor/administrator), the official roster URL in `source`, and `as_of` = 2026-07.
- **Source:** official state board-of-education membership rosters (the `source` URL) cross-checked
  against member biographies, Ballotpedia, and local news, collected July 2026.
- **Coverage (report honestly):** occupation is identifiable for a **minority of seats** (182
  members across 41 boards; median board coverage ~36% of voting seats). **Ohio and Montana**
  rosters were not machine-accessible and carry no rows (coverage n/a). Appointed boards turn over,
  so a member is coded as of the roster date. These figures are a **descriptive supplement** to the
  formal-rule layer, not a precise census; `analyze_composition.py` reports every statistic with its
  coverage. No occupations are imputed; unidentifiable members are omitted, not guessed.

## Coding rules
Coded variables are derived from the raw NASBE strings in `build_governance_panel.py`; the raw
columns are retained in the panel so every coded value is traceable to its source text.
- `board_regime`: elected (all voting members chosen by public ballot), hybrid (mix of elected
  and appointed), legislative (appointed by the legislature), governor (appointed by the
  governor, with or without senate confirmation), none (no state board).
- `frac_elected_public`: fraction of voting members chosen by general-public ballot. Washington's
  members elected by local school-board members / private schools are counted as 0 here (not a
  general-public election) and given partial credit in a robustness check.
