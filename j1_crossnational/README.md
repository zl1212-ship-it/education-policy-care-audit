# Cross-national doctoral-stipend adequacy audit

A cross-national extension of the repository-root stipend pipeline. It expresses
each governance regime's reference doctoral stipend as an **adequacy ratio**
against a local cost-of-living benchmark. The design is a descriptive policy
audit: no treatment effect is estimated and no causal claim is made.

The US layer is unchanged and lives at the repository root (see the root
`README.md`); this directory adds the UK, Canada, Australia, and Japan reference
floors and joins the US institution-level ratios in for comparison.

## Two-tier benchmark (by data availability)

| Tier | Benchmark | Countries |
|---|---|---|
| A | Basic-needs living wage (independent national calculators) | US (MIT Living Wage Calculator, single adult); UK (Living Wage Foundation real Living Wage); Canada (Ontario / BC Living Wage Networks) |
| B | Statutory minimum wage, full-time | Australia (Fair Work national minimum wage); Japan (Tokyo regional minimum wage) |

Reference households differ across the Tier-A calculators (MIT single-adult vs
the LWF/CLWN household-weighted models), so levels are read as "each regime
against its own recognised basic-needs standard," not as one identical metric.
Benchmark annual income uses each source's own full-time convention
(`hours_per_week` x `weeks`), stored per row. Stipends are compared gross;
several are tax-exempt (UK, Australia) or tax-advantaged (Canadian
scholarships), which raises effective adequacy by a few points and is recorded
as a limitation rather than adjusted for.

## Files

| File | Contents |
|---|---|
| `crossnational_stipends.csv` | Reference doctoral stipend per country/year/program, with `source_url` + `accessed` |
| `living_wage_intl.csv` | Cost-of-living benchmark per country/region/year (hourly + full-time convention), with sources |
| `build_crossnational.py` | Annualises benchmarks, joins stipend x benchmark on country+year, pulls US institution ratios from `../lw_ratio_by_institution.csv`, writes `crossnational_ratios.csv` |
| `crossnational_ratios.csv` | Output: adequacy ratio per stipend-program x benchmark-region x year |
| `SOURCES.md` | Every figure's public source and access date |

## Reproduce

```bash
# from the repository root, the US inputs must already be built (see root README)
python3 j1_crossnational/build_crossnational.py
```

The script prints a 2024 anchor-year snapshot (the most recent year for which
every regime's stipend and benchmark are on solid, single-source footing) and
writes `crossnational_ratios.csv`.

## Coverage notes

- US and UK carry a full 2019-2025 series. Canada is encoded at its long-frozen
  pre-2024 values and the post-2024 harmonised value (the increase took effect
  2024-09-01). Australia carries the full 2019-2025 series from the Department of
  Education historical-rates table; 2021, 2023, 2024, and 2025 are additionally
  confirmed against a second source, and 2019, 2020, and 2022 rest on the
  historical-rates table alone (see SOURCES.md). Japan carries the full
  2019-2025 series (JSPS DC stipend fixed at 200,000 yen/month against the Tokyo
  prefectural minimum wage each year).
- The 2024 anchor year is the only year on fully single-source footing for all
  five regimes; it is the basis for the headline cross-national snapshot.
