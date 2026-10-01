# Data sources

All data are public. No values are imputed.

## 1. State board of education governance rules
`data/nasbe_governance_matrix_2024.csv`
- Source: National Association of State Boards of Education (NASBE), *State Education
  Governance Matrix*, updated July 2024.
  URL: https://nyc3.digitaloceanspaces.com/nasbe/2024/06/Governance-matrix-July-2024.pdf
- Coverage: 50 states and the District of Columbia (territories in the source are omitted).
- Fields transcribed verbatim: selection of state board members; selection of the chief state
  school officer (CSSO); selection of the board chair; number of voting members (with student
  and teacher seats noted); length of term; whether the board is established in statute or
  constitution; authority for teacher licensure; authority for academic-standards adoption.
- Abbreviations (NASBE): SBE = state board of education; SEA = state education agency;
  CSSO = chief state school officer; PSC = professional standards commission.

## 2. State public-school enrollment and student demographics
`data/state_demographics.csv`
- Enrollment (`enrollment_2021`) and percent White (`pct_white_2021`): NCES *Digest of
  Education Statistics* 2022, Tables 203.20 and 203.70 (public elementary/secondary, fall 2021).
  The panel derives `pct_students_of_color` as 100 minus percent White.
- Percent eligible for free or reduced-price lunch (`pct_frl_2122`): NCES *Digest* 2022,
  Table 204.10 (2021-22). Values for 2021-22 are affected by pandemic-era universal meals and
  the Community Eligibility Provision. Alaska is suppressed in the source (blank here).

## 3. School-accountability rating type
`data/state_accountability_2024.csv`
- Source: Education Commission of the States (ECS), *50-State Comparison: States' School
  Accountability Systems* (2024), "Rating System" field.
  URL: https://reports.ecs.org/comparisons/states-school-accountability-systems-2024
- Coverage: 50 states and DC. `rating_raw` is the ECS text; `rating_category` groups it as
  A-F, Star, Index, Descriptive, FederalTiers, or Dashboard.

## 4. Proficiency-standard mapping
`data/state_proficiency_stringency.csv`
- Source: NCES, *Mapping State Proficiency Standards Onto the NAEP Scales: Results From the
  2019 NAEP Reading and Mathematics Assessments* (NCES 2021-036), Technical Notes Table A-1.
  URL: https://nces.ed.gov/nationsreportcard/subject/publications/studies/pdf/2021036a.pdf
- Field: `naep_g4_math_equiv` is the NAEP-scale equivalent of each state's grade-4 mathematics
  "proficient" cut score. New Hampshire is not mapped in the source.

## 5. Board-composition rules
`data/board_composition_rules_2026.csv`
- One row per state with a state board: whether state law requires educator or other
  stakeholder seats (`educator_mandate`), bars current educators or school employees from
  serving (`educator_bar`), and seats a voting or advisory teacher (`teacher_seat`).
  Current as of July 2026.
- Source: the governing statute where verified, otherwise the NASBE matrix (2024), the
  Education Week compilation "How Many Seats Do Teachers Get on the State Board of Ed.?" (2018),
  or both. A few rows also cite a 2025 state board roster or a 2025 news report. The
  `rule_source` column gives the citation for each row.

## Coding rules
`build_governance_panel.py` derives the coded variables from the raw NASBE strings; the raw
columns stay in the panel so every coded value can be traced to its source text.
- `board_regime`: elected (all voting members chosen by public ballot), hybrid (mix of elected
  and appointed), legislative (appointed by the legislature), governor (appointed by the
  governor, with or without senate confirmation), none (no state board).
- `frac_elected_public`: share of voting members chosen by general-public ballot. Washington's
  members chosen by local school-board members or private schools count as 0 here;
  `rep_index_altWA` uses an alternative coding that counts them as elected.
- `student_voice`, `teacher_voice`: 1 for a voting seat, 0.5 for a nonvoting seat, 0 for none.
- `rep_index` = 0.50 * `frac_elected_public` + 0.25 * `student_voice` + 0.25 * `teacher_voice`;
  `rep_index_equal` is the unweighted mean of the same three items.
- `auth_index`: mean of standards-adoption authority, teacher-licensure authority (SBE = 1,
  PSC = 0.5, otherwise 0), and constitutional establishment. `gap` = `auth_index` - `rep_index`.
- `algorithmic_grade` = 1 for A-F, Star, or Index ratings; `summative_any` also counts Descriptive.
- Indices are blank for states without a state board.
