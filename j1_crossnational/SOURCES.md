# Sources

All figures are public and hand-collected with the access date 2026-07-01.
The `source_url` and `accessed` columns in the CSVs carry the per-row citation;
this file summarises the canonical source per series.

## Doctoral stipends

- **UK, UKRI minimum doctoral stipend** (2019/20-2024/25): UKRI published
  minimum-stipend table,
  <https://www.ukri.org/wp-content/uploads/2025/01/UKRI_290125_Minimum-stipend-levels-to-2024-25.csv>.
  2025/26 (£20,780): UKRI news release,
  <https://www.ukri.org/news/ukri-is-increasing-phd-stipends-and-improving-student-support/>.
- **Canada, tri-agency CGS-D / PGS-D**: values held at CAD 35,000 (CGS-D) and
  21,000 (PGS-D) for roughly two decades; raised to CAD 40,000 effective
  2024-09-01 and harmonised as CGRS-D. Government of Canada announcement,
  <https://www.canada.ca/en/innovation-science-economic-development/news/2024/05/government-of-canada-announces-details-of-increase-in-award-values-for-federal-scholarships-and-fellowships.html>.
- **Australia, RTP stipend base rate**: Department of Education historical
  stipend rates,
  <https://www.education.gov.au/research-block-grants/resources/historical-stipend-rates-postgraduate-scholarships>.
  Full 2019-2025 series encoded from the historical-rates table: 2019 (27,596),
  2020 (28,092), 2021 (28,597), 2022 (28,854), 2023 (29,863), 2024 (32,192),
  2025 (33,637). 2021, 2023, 2024, and 2025 are additionally confirmed against a
  second source; 2019, 2020, and 2022 rest on the Department of Education
  historical-rates table alone (a live second-source confirmation is pending, as
  the table did not load during assembly), and they fit the confirmed 2021 anchor
  and the published indexation sequence.
- **Japan, JSPS DC research fellowship**: 200,000 yen/month, JSPS,
  <https://www.jsps.go.jp/english/e-pd/>.

## Cost-of-living benchmarks

- **UK, Living Wage Foundation real Living Wage** (UK and London hourly rates):
  <https://www.livingwage.org.uk/what-real-living-wage> and the annual
  announcements. Full-time convention 37.5 h/week.
- **Canada, Ontario Living Wage Network** (Greater Toronto Area) and
  **Living Wage for Families BC / Canadian Living Wage Network** (Metro
  Vancouver): <https://www.ontariolivingwage.ca/rates>,
  <https://www.livingwage.ca/rates>. Full-time convention 35 h/week.
- **Australia, Fair Work national minimum wage**:
  <https://www.fairwork.gov.au/pay-and-wages/minimum-wages>. Standard week 38 h.
- **Japan, Tokyo regional minimum wage** (MHLW, prefectural rate): full 2019-2025
  series in yen per hour: 1,013 (2019), 1,013 (2020, held at the 2019 level),
  1,041 (2021), 1,072 (2022), 1,113 (2023), 1,163 (2024), 1,226 (2025).
  <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/minimumichiran/>.
  Standard week 40 h. JSPS DC stipend held at 200,000 yen/month throughout.
- **US, MIT Living Wage Calculator** (single adult, county level): applied in
  the repository-root pipeline; the resulting per-institution ratios are read in
  from `../lw_ratio_by_institution.csv`.
