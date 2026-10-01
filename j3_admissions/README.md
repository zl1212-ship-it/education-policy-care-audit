# IPEDS admissions and entering-class panels

Three institution-year panels assembled from public IPEDS files through the Urban Institute
Education Data API (no key needed). Each script writes one CSV to `data/`.

## Build order

```
python3 build_admissions_panel.py   # admissions volumes, requirements, score profile -> data/admissions_panel.csv
python3 build_composition.py        # entering-class race/ethnicity shares -> data/composition_panel.csv
python3 build_pell.py               # entering-class Pell share -> data/pell_panel.csv
```

Python 3.9+, standard library only.

## Data

- `data/admissions_panel.csv`: four-year institutions, 2009-2022. Applicants, admits and
  enrollees (all-students totals), admit and yield rates, female share of enrollees,
  `reqt_test_scores` and `open_adm` (see notes below), SAT (reading plus math) and ACT
  composite 25th and 75th percentiles, and SAT/ACT percent submitting. Source: IPEDS
  admissions-enrollment, admissions-requirements and directory files.
- `data/composition_panel.csv`: all institutions reporting, 2009-2022. First-time,
  degree-seeking entering class: total, domestic known-race total, and race/ethnicity
  shares. Source: IPEDS fall enrollment by race.
- `data/pell_panel.csv`: all institutions reporting, 2009-2019. Percent of first-time,
  full-time degree-seeking undergraduates receiving a Pell grant. Source: IPEDS Student
  Financial Aid (`sfa-ftft`).

## Variable notes

- `control`: 1 public, 2 private nonprofit, 3 private for-profit.
- `reqt_test_scores`: IPEDS code for the test-score admission requirement, kept for codes 0 to 3;
  any other value is blank. Code labels follow the Urban Institute codebook.
- `open_adm`: IPEDS open-admissions code as reported; negative values are IPEDS
  missing or not-applicable codes.
- Race/ethnicity shares use a domestic, known-race denominator (total minus nonresident and
  unknown race). `share_nonres` and `share_unknown` use the all-students total.
- `share_urm`: Black, Hispanic, American Indian/Alaska Native, Pacific Islander, and two or
  more races.
