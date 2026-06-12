# J4 — Predictive-advising adoption audit (completion gaps)

Replication code and data for the predictive-advising adoption audit.
Manuscript is kept in the private `blinded-manuscript` repo, not here.

## Research question

When a higher-education institution **adopts a predictive / early-alert algorithmic
system** (e.g., EAB Navigate, Civitas Learning, Starfish/Hobsons), does that adoption
**reduce or reproduce** racial and Pell completion gaps?

The paper treats educational algorithms as *governance technologies that reallocate
institutional attention* ("algorithmic opportunity allocation"). It is therefore NOT an
audit of outcome disparity; it estimates the
**causal effect of adopting algorithmic governance** on the distribution of opportunity.

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

## Literature positioning

See `literature.md`. Closest work — Vasquez, Gándara et al. (2025), *Selling Student Success*
— is qualitative (vendor marketing). J4 is the causal complement: do these systems actually
narrow equity gaps, or just market that they do? Not scooped.

## Design (Strand B — mechanism chapter)

FOIA'd contracts / vendor validation docs: *what features the model scores, what
thresholds flag students, who receives attention.* Makes "allocation of attention"
concrete rather than inferred. Descriptive, not causal.

## The novel asset to collect: adoption timing

A panel of **which U.S. institutions adopted which predictive/early-alert platform, and when.**
This dataset does not exist publicly and is the paper's original empirical contribution.

Candidate sources (to be vetted in the availability recon — see `adoption_sources.md`):
- USASpending procurement records (reuse `../scrape_usaspending.py`)
- State-level FOIA / public-records contracts for public institutions
- Vendor public client lists, case studies, press releases
- Higher-ed trade press (Inside Higher Ed, Chronicle) adoption announcements

## Status

- [ ] Availability recon — can we date adoption for enough institutions for DiD? (gate)
- [ ] Build adoption panel
- [ ] Merge with IPEDS outcome panels
- [ ] Staggered DiD + event study
- [ ] Strand B FOIA mechanism evidence
- [ ] Draft manuscript (private repo)

## Notes

Every adoption record carries its source (URL / FOIA reference / contract ID) in the
`source_url` / `source_quote` columns. If coverage proves insufficient for credible DiD,
the design pivots to an allocation-audit framing.
