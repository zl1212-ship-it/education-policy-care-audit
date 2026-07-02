# State board authority and representation audit

Codes the NASBE State Education Governance Matrix (50 states + DC) into governance variables
and two indices: the rulemaking authority each state board of education holds (adopting
academic standards, controlling teacher licensure, constitutional entrenchment) and the
representation it offers (direct public election of members, a voting student seat, a voting
teacher seat). NCES state demographics are merged in, and all reported statistics are
computed from the coded panel.

## Pipeline
```
build_governance_panel.py    # parse NASBE matrix -> coded vars + indices; merge NCES demographics
analyze_governance.py        # all computed statistics -> data/results_summary.csv
analyze_composition.py       # board-composition layer (rules + member census) -> data/composition_results.csv
make_figures.py              # Figures 1-3 -> ../paper/blinded-manuscript/J5/j5_figure{1,2,3}.{pdf,png,tiff}
make_composition_figure.py   # Figure 4 -> ../paper/blinded-manuscript/J5/j5_figure4.{pdf,png,tiff}
```

## Data
- `data/nasbe_governance_matrix_2024.csv` — NASBE State Education Governance Matrix (July 2024), verbatim.
- `data/state_demographics.csv` — NCES enrollment, % White, % FRL by state.
- `data/governance_panel.csv` — built panel (coded variables + indices + raw provenance columns).
- `data/results_summary.csv` — all computed statistics.
- `data/board_composition_rules_2026.csv` — per-state statute rules on educator seats (mandate / bar / teacher seat), statute-cited.
- `data/board_members_2026.csv` — hand-collected member census from official rosters (source URL + as-of date per member; partial coverage, see SOURCES.md §6).
- `data/composition_results.csv` — computed composition statistics.

See `SOURCES.md` for provenance.
