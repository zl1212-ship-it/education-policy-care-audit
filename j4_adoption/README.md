# Predictive-advising adoption audit (completion gaps)

Replication code and data for the predictive-advising adoption audit.

## What the pipeline estimates

Staggered difference-in-differences effects of adopting a predictive / early-alert
advising system (e.g., EAB Navigate, Civitas Learning, Starfish/Hobsons) on retention
and on racial and Pell completion gaps, from a dated adoption panel assembled here.

## Design (Strand A — primary, causal)

- **Treatment timing comes from system-wide contracts.** Per-campus exact adoption dates
  proved unrecoverable at scale (search gives only "before year X"; vendor-subdomain
  Wayback snapshots post-date true adoption). State-system-wide adoptions (e.g., CSU 2018,
  UW 2019) are cleanly datable from press/board minutes and each cover many campuses — these
  drive the staggered timing. See `data/systems_adoption.csv`.
- **Treatment:** campus-by-year indicator = its system adopted system-wide in year T (or the
  campus adopted standalone where datable, e.g., Georgia State 2012).
- **Outcome:** primary = first-to-second-year retention (responds fast, proximate to the
  attention-reallocation mechanism); secondary = racial/Pell completion gaps built from
  public IPEDS graduation-rate and Pell tables (Urban Institute Education Data API).
- **Panel ~2010–2023.** Need pre-adoption baseline for parallel-trends; flag/exclude COVID
  cohorts (2020–22) as a confounder.
- **Estimator:** Callaway–Sant'Anna (2021) staggered DiD + event-study leads/lags;
  not-yet-treated systems (e.g., Hawaii 2025) as controls. TWFE benchmark only.
- **Robustness:** drop known early-adopter campuses (bounded measurement error);
  pre-trend tests.

## Design (Strand B — mechanism evidence)

FOIA'd contracts / vendor validation docs: *what features the model scores, what
thresholds flag students, who receives attention.* Makes "allocation of attention"
concrete rather than inferred. Descriptive, not causal.

## The adoption-timing panel

A panel of **which U.S. institutions adopted which predictive/early-alert platform, and
when**, assembled from sourced public records (see `adoption_sources.md`):
- USASpending procurement records
- State-level FOIA / public-records contracts for public institutions
- Vendor public client lists, case studies, press releases
- Higher-ed trade press (Inside Higher Ed, Chronicle) adoption announcements

## Notes

Every adoption record carries its source (URL / FOIA reference / contract ID) in the
`source_url` / `source_quote` columns. If coverage proves insufficient for credible DiD,
the design pivots to an allocation-audit framing.
