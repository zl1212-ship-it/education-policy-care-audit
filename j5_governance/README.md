# State board governance panel

Builds a state-level panel (50 states and DC) of state board of education governance
variables coded from the NASBE State Education Governance Matrix, merged with state
enrollment, demographic, school-accountability, and proficiency-standard data from public
sources.

## Build
```
build_governance_panel.py    # code the NASBE matrix, merge state data -> data/governance_panel.csv
```

Requires Python 3.9+ with numpy and pandas.

## Data
- `data/nasbe_governance_matrix_2024.csv`: NASBE State Education Governance Matrix (July 2024), transcribed verbatim.
- `data/state_demographics.csv`: NCES enrollment, percent White, and percent FRL by state.
- `data/state_accountability_2024.csv`: ECS school-accountability rating type by state (2024).
- `data/state_proficiency_stringency.csv`: NCES NAEP-scale equivalent of each state's grade-4 math proficiency cut.
- `data/board_composition_rules_2026.csv`: rules on educator and other stakeholder seats for each state board, with a source citation for each row.
- `data/governance_panel.csv`: built panel (coded variables, indices, and the raw NASBE text).

See `SOURCES.md` for sources and coding rules.
