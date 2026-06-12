# Adoption-timing data — availability recon

Goal: decide whether we can date algorithmic-system adoption for **enough institutions**
to support staggered DiD (rough floor: ~150–200 treated institutions with credible dates,
plus never-/not-yet-treated controls). This file is the recon log; fill it before coding.

## Vendors to track (the "treatment")

| Vendor / platform | Type | Notes |
|---|---|---|
| EAB Navigate (Navigate360) | early-alert + advising | largest footprint; many public clients |
| Civitas Learning | predictive analytics | published client list / case studies |
| Starfish (Hobsons / EAB) | early-alert | merged into EAB; watch double-counting |
| Hobsons / Ellucian retention | advising/CRM | |
| Other (add as found) | | |

## Source channels — fill coverage estimate per channel

| Channel | How to query | Est. # institutions datable | Date precision | Effort |
|---|---|---|---|---|
| USASpending procurement | reuse `../scrape_usaspending.py`, vendor name search | ? | contract start date | low |
| State public-records / FOIA | per-state contract portals for public unis | ? | contract date | high |
| Vendor client lists / case studies | scrape vendor sites, archive.org snapshots | ? | announcement year | low |
| Trade press (IHE, Chronicle) | search adoption announcements | ? | article date ≈ rollout | medium |

## Decision gate

- **PASS** → enough credible dates → Strand A staggered DiD.
- **FAIL** → pivot to Strand B allocation-audit design.

## Recon results (run 2026-06-06)

**Channel verdicts:**

| Channel | Verdict | Evidence |
|---|---|---|
| USASpending procurement | ✗ DEAD | Universities buy these with institutional funds, not federal awards. Keyword probe returned only noise: "Education Advisory Board" → unrelated federal grants TO universities; "Hobsons" → state Depts of Transportation. Not procurement data. |
| Vendor public client lists | ~ PARTIAL | EAB publishes counts (Navigate360 **850+** institutions; EAB overall 2,100) but **no comprehensive named list with dates**. appsruntheworld.com has a commercial customer DB (paywalled). |
| Governing-board / regents minutes | ✓ STRONG (public unis) | Exact contract approval dates. E.g., UW System Board of Regents approved EAB renewal Jun 2023 (through Dec 2028). |
| State procurement portals | ✓ GOOD (public unis) | Public-records contracts datable per institution. |
| University press / .edu pages | ✓ GOOD (year precision) | Many institutions document adoption publicly (e.g., UTSA Civitas partnership press release 2020). Year-level, fine for annual DiD. |

**GATE = conditional PASS.** Treatment is datable but only via a **hand-built, institution-by-
institution** collection (no API dump). This labor is exactly why the dataset is a novel,
creditable contribution.

**Scope decision driven by the recon:**
- **Population:** U.S. **public 4-year institutions** — best records transparency (regents
  minutes + state FOIA) AND best IPEDS outcome coverage. Clean, coherent DiD population.
- **Primary treatment vendor:** **EAB Navigate360** (largest footprint, best-documented,
  850+); Civitas as a secondary/robustness vendor.
- **Date sources, in priority order:** (1) governing-board minutes, (2) state procurement
  portal, (3) press/.edu. Each record carries its source in the panel columns.
- Never-treated + not-yet-treated public 4-years are plentiful → valid Callaway–Sant'Anna controls.
