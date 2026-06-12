# J3 — The Measure Moved, the Boundary Did Not (test-optional admissions and the construction of merit)

Replication code and data for the test-optional admissions audit.
Manuscript text is kept in the private `paper/blinded-manuscript` folder, not here; the findings
narrative (`results.md`) is gitignored until publication. Everything in this directory is
reproducible from public IPEDS data.

## Research question

When a university adopts **test-optional admissions** — removing a disclosed, externally validated
criterion — does it **redistribute access** or merely **relocate discretion**? The paper treats
admissions as a governance arrangement that constructs merit, and tests whether the reform changed
the *measurement* of merit or the *boundary* of opportunity.

## Treatment (fully reproducible from the federal record)

Adoption is dated from the IPEDS admissions-requirements field `reqt_test_scores`
(1 = required, 2 = recommended, 3 = neither required nor recommended). An institution is
test-optional from the first year the field flips from 1/2 to 3, requiring a prior 1/2 year so the
flip is a genuine policy change. The clean identification sample is the **237 voluntary adopters of
2016–2019**; the 2020–2021 pandemic wave is excluded and enters only as not-yet-treated controls.

## Designs

| Design | Script | What it identifies |
|---|---|---|
| Staggered DiD (Callaway–Sant'Anna) | `analyze_did.py` | ATT of adoption on admit rate, yield, SAT submission, entering-class %URM/%Black/%Hispanic; institution-clustered bootstrap |
| Robustness (matched + placebo-in-time) | `robustness.py` | whether the %URM result is a pre-trend artifact (it is) |
| Synthetic control (two flagship adopters) | `scm_gw.py` | George Washington U. (private) + Montclair State U. (public); same-sector donor screen, K-nearest with K∈{20,25,30,40} sensitivity; Abadie placebo permutation |
| Adoption logit (MLE + AME) | `adoption_logit.py` | the treatment-assignment mechanism e(z); who adopts and why |
| Fuzzy RDD (estimator validated) | `rdd.py` | local-linear/triangular-kernel RD, IK bandwidth, McCrary density test, covariate balance, bandwidth sensitivity. **Validated on the public Senate benchmark** (recovers the ~+7pp incumbency effect). Not applied to admissions: a clean cutoff needs restricted applicant micro-data (state SLDS / Texas Top-Ten-Percent ERC files), which IPEDS lacks. Ready to run on such data. |

## Pipeline (run in order)

```
python3 build_admissions_panel.py   # IPEDS admissions volumes + requirements -> data/admissions_panel.csv
python3 build_treatment.py          # derive adoption year from reqt_test_scores -> data/treatment_panel.csv, panel_treated.csv
python3 build_composition.py        # entering-class race composition -> data/composition_panel.csv
python3 analyze_did.py              # staggered DiD -> data/did_results.csv, did_event_*.csv
python3 robustness.py               # matched DiD + placebo-in-time -> data/matched_balance.csv
python3 scm_gw.py                   # synthetic control -> data/scm_gw_*.csv
python3 adoption_logit.py           # adoption logit -> data/adoption_logit_ame.csv
python3 rdd.py                      # RDD estimator, validated on public Senate benchmark
python3 make_figures.py             # j3_figure1.pdf (event studies), j3_figure2.pdf (two-case SCM)
```

All data come from the Urban Institute Education Data API, which mirrors IPEDS.

## Headline finding

Test-optional adoption changed the **measurement** of merit (SAT submission **−9.5 pp**, z = −5.8)
but not the **boundary** of opportunity: entering-class composition, admit rate, and yield show no
detectable effect once a pre-existing diversification trend is accounted for; the flagship GW case
is a null; and adoption is selected on **sector and lower selectivity, not baseline diversity**.
Discretion was relocated; who enrolls did not change.

## Data note

IPEDS reports race for entrants but not for applicants or admits, so the composition outcome is the
first-time degree-seeking entering class, not the admitted pool — a limitation stated in the
manuscript.
