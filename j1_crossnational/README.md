# Cross-national stipend and cost-of-living tables

Hand-collected reference tables for the UK, Canada, Australia, and Japan, 2019-2025.
Every row carries its public source URL and access date.

| File | Contents |
|---|---|
| `crossnational_stipends.csv` | Reference doctoral stipend per country, year, and program, with `source_url` and `accessed` |
| `living_wage_intl.csv` | Cost-of-living benchmark per country, region, and year (hourly rate plus the source's full-time hours convention), with sources |
| `SOURCES.md` | Canonical public source for each series |

Benchmarks are of two types: a basic-needs living wage (UK Living Wage Foundation; Ontario
and British Columbia living-wage networks) and a full-time statutory minimum wage (Australia
Fair Work national minimum wage; Tokyo prefectural minimum wage). Annual benchmark income is
`hourly_local` x `hours_per_week` x `weeks`, using the values stored in each row. Coverage
varies by series; see the `year` column.

The U.S. stipend reports are in `../phd_stipends.csv` (see the root README).
