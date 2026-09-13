# AI exposure explorer for occupations

HW#1 (Computational Social Science) — product idea built on Hugging Face Datasets.

## Repository

**Hugging Face Datasets** — https://huggingface.co/datasets (own choice, not present in the list of sources).
Community-driven machine-learning data hub; every dataset is a Git repository with a dataset card and an in-browser viewer.

## Dataset

**Name:** Anthropic/EconomicIndex — the Anthropic Economic Index

**Link:** https://huggingface.co/datasets/Anthropic/EconomicIndex

**Author / provider:** Anthropic (economic research team). Licence: MIT for code, CC-BY for the data; ~17.4k downloads and 565 likes on the review date; last updated 26.06.2026.

**Data type:** structured tabular data — tidy long-format CSV files in an append-only Git repository, one folder per release.

**Size:** 664 MB in 83 files: `labor_market_impacts/` (1.9 MB, version-independent), `release_2025_02_10` (5 MB), `release_2025_03_27` (10 MB), `release_2025_09_15` (61 MB), `release_2026_01_15` (142 MB), `release_2026_03_24` (147 MB) and `release_2026_06_26` (297 MB, the latest).

**Description:** The dataset measures how AI is actually used for work: anonymised Claude conversations are classified into O*NET tasks and SOC occupations and published as aggregated usage shares per geography, per task hierarchy and per request topic. The latest release uses the schema `date_start, date_end, geo_id, geo_level, category_name, hierarchy_level, metric_id, value, node_name, node_external_id`, for two sources — consumer (`claude_ai`, global / country / subregion) and enterprise API (`1p_api`, global). Older releases are kept and are still needed: the wage, BLS employment, SOC structure and O*NET lookup tables live in `release_2025_02_10` and `release_2025_09_15`, the automation-vs-augmentation tables in the 2025 releases, and stacking the releases gives a time axis from Aug 2025 to May 2026.

## Who is the product for?

Students choosing a specialisation, career advisers, universities planning curricula, and HR / L&D teams planning reskilling.

## What problem does it solve?

"Will AI take my job" is currently answered with opinion pieces. This dataset contains measured usage per O*NET task and per SOC occupation, by country and region — but only as raw metric rows spread over seven releases with different schemas, so nobody outside research will ever open it.

## What value does it provide?

It lets a person look up their own occupation and see which of its tasks are already being delegated to AI, whether that usage looks like automation or augmentation, how the share moved over the last ten months, and how their country compares with the global average — evidence instead of speculation, and a concrete list of which skills to keep and which to add.

> **Caveat for the time axis:** releases 3–5 are one-week snapshots while release 6 contains monthly aggregates, and the underlying model versions differ between releases — the trend must be presented as "as published per release", not as a continuous series.

## Key features

- Occupation search → task-level breakdown, ranked by usage share.
- Automation vs augmentation split per occupation (from the 2025 release tables).
- Trend across releases: the same occupation measured from Aug 2025 to May 2026.
- Country and subregion comparison against the global baseline.
- Join to the wage and employment tables: how much of the wage bill sits in high-usage tasks.
- Reskilling hint: neighbouring occupations with lower AI usage and comparable wage.

## Key metrics

- Usage share, %, per task and per occupation.
- Automation share vs augmentation share.
- Change against the previous release.
- Country index vs global average.
- Wage-weighted exposure and employment covered.

## Visualizations

- Treemap — task hierarchy (task → DWA → IWA → GWA) by usage.
- Slope chart — the same occupation across releases.
- Choropleth — usage by country.
- Scatter — median wage vs AI usage, with employment as point size.
- KPI row — headline metrics for the selected occupation.

## Controls

- Occupation or task search.
- Country / subregion.
- Release or date.
- Source: consumer `claude_ai` vs enterprise `1p_api`.
- Hierarchy level (overall / onet / request / soc_occupation).

## Notes

- Releases are append-only: older folders stay needed for wage, employment, SOC and O*NET lookup tables.
- Data lives in `./data`.
