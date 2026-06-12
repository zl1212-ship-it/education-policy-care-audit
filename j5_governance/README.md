# State board authority and representation audit

Codes the NASBE State Education Governance Matrix (50 states + DC) into governance variables
and two indices: the rulemaking authority each state board of education holds (adopting
academic standards, controlling teacher licensure, constitutional entrenchment) and the
representation it offers (direct public election of members, a voting student seat, a voting
teacher seat). NCES state demographics are merged in, and all reported statistics are
computed from the coded panel.

## Pipeline
```
build_governance_panel.py   # parse NASBE matrix -> coded vars + indices; merge NCES demographics
analyze_governance.py       # all computed statistics -> data/results_summary.csv
make_figures.py             # Figures 1-3 -> ../paper/blinded-manuscript/j5_figure{1,2,3}.{pdf,png}
```

## Data
- `data/nasbe_governance_matrix_2024.csv` — NASBE State Education Governance Matrix (July 2024), verbatim.
- `data/state_demographics.csv` — NCES enrollment, % White, % FRL by state.
- `data/governance_panel.csv` — built panel (coded variables + indices + raw provenance columns).
- `data/results_summary.csv` — all computed statistics.

See `SOURCES.md` for provenance.
