# J5 — Accountability Without Representation

A representation audit of American state education governance. Who holds the authority to make
the rules for public schools, and how democratically representative are the bodies that hold it?

The audit treats the **state board of education** as the unit of governance and asks two things
of each of the 50 states + DC: (1) how much consequential **authority** the board holds
(adopting academic standards, controlling teacher licensure, constitutional entrenchment), and
(2) how much **representation** it offers the governed (direct public election of members, a
voting student seat, a voting teacher seat). The gap between the two is the paper's object.

## Pipeline
```
build_governance_panel.py   # parse NASBE matrix -> coded vars + indices; merge NCES demographics
analyze_governance.py       # all reported statistics -> data/results_summary.csv
make_figures.py             # Figures 1-3 -> ../paper/blinded-manuscript/j5_figure{1,2,3}.{pdf,png}
```

## Data
- `data/nasbe_governance_matrix_2024.csv` — NASBE State Education Governance Matrix (July 2024), verbatim.
- `data/state_demographics.csv` — NCES enrollment, % White, % FRL by state.
- `data/governance_panel.csv` — built panel (coded variables + indices + raw provenance columns).
- `data/results_summary.csv` — every number cited in the paper.

See `SOURCES.md` for provenance and `results.md` for the headline findings.

## Headline
Only 17% of state boards are directly elected; 12.8% seat a voting student and 12.8% a voting
teacher; yet 92% adopt academic standards and 70% directly control teacher licensure.
Representation and authority are rank-independent (Spearman -0.02); 30/47 boards combine high
authority with low representation. No evidence the deficit is concentrated on students of color
(p = 0.46); it is broad-based. And 49% of boards now grade schools by a single formula
(A-F / star / index), reaching 48% of students, regardless of representation (p = 0.59).
