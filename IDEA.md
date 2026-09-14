# AI Time Machine — product idea

**Course:** Computational Social Science · Homework #1
**Service reviewed:** Hugging Face Datasets (https://huggingface.co/datasets)
**Dataset:** `Anthropic/EconomicIndex` — https://huggingface.co/datasets/Anthropic/EconomicIndex
**Prototype level targeted:** working web front-end (max 15 points)
**Status of the numbers below:** every figure was computed locally from
`data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv` on 14.09.2026 unless marked otherwise.

---

## 1. One-sentence pitch

Type in an occupation and see how many hours of its work AI already absorbs — measured, not
predicted, from Anthropic's published telemetry of real Claude conversations.

---

## 2. Why this and not the obvious thing

The obvious product on this dataset is an "AI exposure explorer": pick an occupation, look at a
usage percentage. Three problems with it.

1. It restates what Anthropic already publishes in its own Economic Index reports, so it adds no
   value on top of the source.
2. A percentage is not actionable. "Your occupation accounts for 1.67% of Claude usage" tells a
   student nothing about what to do.
3. Everyone who picks this dataset builds it.

The dataset's most interesting columns are almost never used, because they only appear in the
2026 releases and are buried among 52 metric ids:

| `metric_id` | Unit | What it enables |
|---|---|---|
| `human_only_time_mean` | hours | How long the task takes a person unaided |
| `human_with_ai_time_mean` | minutes | How long it takes with Claude |
| `human_education_years_mean` | years | Education a human needs for the task |
| `ai_education_years_mean` | years | Education-equivalent level AI demonstrates |
| `ai_autonomy_mean` | 1–5 | How autonomously AI completes it |
| `collaboration_bucket_automation_pct` / `..._augmentation_pct` | % | Replacement vs assistance |
| `use_case_coursework_pct` | % | Share of usage that is study/homework |
| `usage_per_capita_index` | index | Usage relative to working-age population (country level) |
| `artifact_*_pct` (32 labels) | % | What Claude actually produced |

The first two turn exposure into **time**, which is a unit people can act on. That is the product.

---

## 3. Audience, problem, value

**Primary audience.** Students choosing a specialisation and early-career specialists deciding
where to move next.
**Secondary.** Career advisers and curriculum planners; L&D / HR teams planning reskilling.

**Problem.** "Will AI take my job" is answered either by opinion pieces or by a single exposure
percentage. The measurements that would actually help — how long a task takes with and without AI,
how autonomously AI performs it, whether the pattern is automation or augmentation — exist in this
dataset, but only as 1,636,573 rows of long-format CSV spread over seven release folders with
changing schemas. There is no interface over it; anything outside Anthropic's own PDF reports
requires downloading 664 MB and writing pandas.

**Value.**

- **Hours instead of percentages.** For Computer Programmers the work delegated to Claude takes
  **9.1 hours unaided and 52 minutes with AI** — a factor of 10.5. For Document Management
  Specialists, 2.1 hours against 13 minutes.
- **Measured behaviour, not a survey.** These are aggregates over real conversations, refreshed
  monthly, with no message text and no user identifiers.
- **A Ukrainian answer.** Ukraine is covered at country level — Anthropic AI Usage Index **0.78**
  (78% of what its working-age population share would predict), rank **68 of 121** in May 2026,
  **18.8%** of conversations classified as coursework. No Ukrainian source publishes anything
  comparable.

---

## 4. Data

### 4.1 Repository

| | |
|---|---|
| Repo | `Anthropic/EconomicIndex` on Hugging Face |
| Authors | Anthropic economic research team — Massenkoff, Lyubich, Sacher, Hitzig, Zhang, Heller, McCrory |
| Size | 664 MB, 83 files |
| Licence | CC-BY (data), MIT (code) |
| Last updated | 26.06.2026 |
| Structure | append-only, one folder per release: `release_2025_02_10`, `release_2025_03_27`, `release_2025_09_15`, `release_2026_01_15`, `release_2026_03_24`, `release_2026_06_26`, plus a version-independent `labor_market_impacts/` |

### 4.2 Schema of the current release

`data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv` — 219 MB, 1,636,573 rows.

```
date_start, date_end, geo_id, geo_level, category_name,
hierarchy_level, metric_id, value, node_name, node_external_id
```

One row = one metric value for one geography × category node.

| Dimension | Values (verified in the file) |
|---|---|
| Period | two calendar months: 2026-04-01 → 2026-05-01, 2026-05-01 → 2026-06-01 |
| `geo_level` | `global` (554,941 rows), `country` (673,272), `subregion` (408,360) |
| Countries | **121**, ISO-3166 alpha-3; `UKR` present with 7,765 rows |
| `category_name` | `onet` (744,544), `request` (465,202), `soc_occupation` (353,817), `overall` (73,010) |
| Nodes at level 0 | 2,713 O*NET tasks · 718 SOC detailed occupations · 1,007 request topics |
| `metric_id` | 52 distinct metrics (list in §2 and in the release's `data_documentation.md`) |

A companion file `aei_1p_api_2026-06-26.csv` (77 MB) carries the same metrics for first-party API
usage, global only.

### 4.3 Important limits (state these in the report and the video)

- **Publication thresholds.** A missing cell means the value did not meet Anthropic's aggregation
  or sample floor, **not** that it is zero. At country level the full metric set is published only
  for `overall` and for the coarse levels (GWA / Major request topic / SOC major group); the finer
  breakdowns are published as `pct` only.
- **Releases are not a continuous time series.** Releases 3–5 are one-week snapshots, release 6 is
  monthly aggregates, and the underlying models differ. The time axis must be labelled "as
  published per release".
- **The population is Claude users, not the labour force.** Shares describe Claude usage, not the
  economy. Wording throughout the UI must be "of Claude usage", never "of all work".
- **US-centric taxonomies.** O*NET and SOC are US classifications applied worldwide.

---

## 5. Metric definitions

Let an occupation *o* have usage share `pct_o`, and let its tasks be *t*.

| Metric | Formula | Unit |
|---|---|---|
| Speed-up factor | `human_only_time_mean × 60 / human_with_ai_time_mean` | × |
| Time saved per task | `human_only_time_mean − human_with_ai_time_mean / 60` | hours |
| Weighted time saved | `Σ_t (pct_t / 100) × time_saved_t` | hours |
| Education gap | `ai_education_years_mean − human_education_years_mean` | years |
| Autonomy | `ai_autonomy_mean` as published | 1–5 |
| Automation share | `collaboration_bucket_automation_pct` | % |
| Country index | `usage_per_capita_index` as published | 1.0 = proportional |
| Coursework share | `use_case_coursework_pct` | % |
| Release delta | metric(release *n*) − metric(release *n−1*) | same as metric |

### Reference values computed from the May 2026 global slice

717 of 718 occupations have the full metric set.

| Occupation | SOC | Usage % | Unaided | With AI | Speed-up |
|---|---|---|---|---|---|
| Document Management Specialists | 15-1299.03 | 5.10 | 2.05 h | 13.3 min | 9.2× |
| Librarians and Media Collections Specialists | 25-4022.00 | 4.22 | 2.41 h | 20.5 min | 7.1× |
| Editors | 27-3041.00 | 2.58 | 4.88 h | 46.2 min | 6.3× |
| Computer Systems Analysts | 15-1211.00 | 1.91 | 5.21 h | 66.4 min | 4.7× |
| Computer Programmers | 15-1251.00 | 1.67 | 9.12 h | 52.4 min | 10.5× |
| Software Developers | 15-1252.00 | 0.35 | 5.90 h | 47.8 min | 7.4× |
| Lawyers | 23-1011.00 | 0.62 | 5.83 h | 54.1 min | 6.5× |
| Accountants and Auditors | 13-2011.00 | 0.12 | 9.49 h | 47.1 min | 12.1× |
| Computer Science Teachers, Postsecondary | 25-1021.00 | 0.01 | 5.21 h | 48.1 min | 6.5× |

Country level, May 2026, `overall`:

| | Ukraine | Rank | Top |
|---|---|---|---|
| AI Usage Index | 0.78 | 68 / 121 | AUS 6.40, SGP 5.81, CHE 5.02 |
| Share of global usage | 0.47% | 38 / 121 | USA 20.16%, IND 7.12%, FRA 3.95% |
| Coursework share | 18.77% | 67 / 121 | TUN 51.52%, DZA 47.12%, IDN 45.88% |
| Work share | 40.61% | 64 / 121 | BRA 57.35%, ARE 54.63%, ISR 53.32% |
| Automation share | 48.90% | 67 / 121 | ZWE 57.63%, MNG 57.44%, UGA 56.02% |

---

## 6. Screens

### Screen 1 — Time card (the hook)

- Search field with autocomplete over 718 occupations (plus direct search of 2,713 O*NET tasks).
- Hero: one paired horizontal bar putting the unaided duration and the assisted duration on the
  same axis, with the speed-up factor set large beside it.
- KPI row: usage share, autonomy (1–5), automation share, coursework share.
- Ranked task table with inline bars: the O*NET tasks behind the occupation, sorted by time saved,
  so the user sees which parts of the job are being delegated and which are untouched.
- A "how this is calculated" popover on every KPI, quoting the `metric_id` it comes from.

### Screen 2 — Compare

- Scatter: `human_education_years_mean` (x) against `ai_education_years_mean` (y), parity diagonal
  drawn, point size by usage share. Points above the line are jobs where AI already operates above
  the human entry bar.
- Two-occupation comparison on identical axes.
- Slope chart of the same occupation across the six releases, explicitly labelled as discrete
  published snapshots.

### Screen 3 — Geography

- World choropleth of `usage_per_capita_index` with a diverging scale centred on 1.0, Ukraine
  pinned by default.
- Ranked country table with the selected metric.
- Stacked bar of work / personal / coursework, and the artifact mix underneath.
- Metric switch: usage index, usage share, automation share, coursework share.

### Cross-cutting

- URL state (`?occ=15-1251&geo=UKR&metric=usage_index`) so any view is shareable.
- CSV export of the slice currently on screen.
- Light/dark theme, responsive down to phone width.
- Persistent footer: source, release date, licence, and the suppression notice from §4.3.

---

## 7. Controls

| Control | Values |
|---|---|
| Occupation / task search | 718 SOC occupations, 2,713 O*NET tasks |
| Geography | global · 121 countries · subregions (default UKR) |
| Source | `claude_ai` (consumer + Cowork, has geography) vs `1p_api` (enterprise, global only) |
| Release | six releases, 02.2025 → 06.2026 |
| Month | within the current release: April or May 2026 |
| Hierarchy level | Task · DWA · IWA · GWA |
| Map metric | usage index · usage share · automation share · coursework share |

---

## 8. Implementation

### 8.1 Architecture

Front-end only. No server, no database — but **real data**, not mock data.

```
664 MB repo  →  build_data.py (pandas, run once, offline)  →  ~1.2 MB of JSON  →  static SPA
```

This satisfies the "working web front-end" tier (backend not required, static data allowed) while
the numbers on screen are the genuine published values. The build script ships in the repository so
the grader can see how the JSON was derived.

### 8.2 Precomputed files (sizes measured, not estimated)

| File | Contents | Size |
|---|---|---|
| `occupations.json` | 718 occupations × core metrics | **174 KB** |
| `tasks.json` | 2,713 O*NET tasks × core metrics | **817 KB** |
| `countries.json` | 121 countries × `overall` metrics | ~40 KB |
| `occ_tasks.json` | occupation → task mapping (from `release_2025_02_10/onet_task_mappings.csv`) | ~200 KB |
| `releases.json` | per-occupation series across the six releases | ~150 KB |
| `artifacts.json` | artifact mix, global and per country | ~60 KB |

Total under 1.5 MB — loads instantly, fits in any static host.

### 8.3 Stack

- Vite + React (or plain TS if preferred — nothing here needs a framework).
- **Apache ECharts** for every chart: it covers the world map, scatter, bar, slope and gauge in one
  library, so there is no second charting dependency and no manual GeoJSON handling.
- `fuse.js` for fuzzy occupation search.
- Deployment: GitHub Pages or Vercel; the link goes in the report.

### 8.4 Build order (three days to the 17.09 deadline)

| Day | Work |
|---|---|
| 1 | `build_data.py`: load the release CSVs, pivot long → wide, compute derived metrics, emit the JSON files. Verify a handful of values by hand against the raw CSV. |
| 2 | Screen 1 end to end (search, hero bar, KPI row, task table), then Screen 3 (map). Screen 2 if time allows. |
| 3 | Polish: URL state, CSV export, dark mode, methodology popovers, footer. Deploy. Record the video. |

Screens 1 and 3 alone are a complete, defensible submission; Screen 2 and the release timeline are
the margin.

### 8.5 Reuse for the second product

The Ukrainian vehicle-registration dashboard (service 1) uses the same shell: same React app, same
ECharts setup, same precompute pattern, one extra route. Building both at the front-end level costs
roughly 1.3× one of them, and avoids the risk of the lower level capping the grade.

---

## 9. Demo script (≤ 2 minutes)

1. **0:00–0:20** — Problem. "Will AI take my job" answered by opinion pieces; the real measurements
   are locked in 1.6 million rows of CSV.
2. **0:20–0:40** — The data. Hugging Face → `Anthropic/EconomicIndex`, 664 MB, CC-BY, monthly,
   121 countries. Show the raw CSV for two seconds — it is unreadable, and that is the point.
3. **0:40–1:20** — The product. Type "Computer Programmers": 9.1 hours → 52 minutes. Open the task
   table. Then type **"Computer Science Teachers, Postsecondary"** — 5.2 hours → 48 minutes, and
   53% of that usage is coursework. (Choosing the instructor's own occupation lands.)
4. **1:20–1:40** — Ukraine on the map: index 0.78, rank 68 of 121.
5. **1:40–2:00** — How it is built: pandas precompute → 1.2 MB JSON → static front-end; the
   caveats from §4.3, stated out loud.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Sparse cells at country level make a view look broken | Detect and show an explicit "not published at this grain" state, never a zero |
| Schema differs between releases | The release timeline reads only the fields that exist in all six; everything else uses the current release |
| Someone reads shares as shares of the economy | Fixed wording "of Claude usage" plus a permanent footnote |
| Time metrics are model estimates, not stopwatch measurements | Say so in the methodology popover and in the video |
| Scope creep across six modules | Screens 1 and 3 are the committed scope; the rest is optional |

---

## 11. Sources

- Dataset: https://huggingface.co/datasets/Anthropic/EconomicIndex
- Release documentation: `data/release_2026_06_26/data_documentation.md`
- Citation: Massenkoff, Lyubich, Sacher, Hitzig, Zhang, Heller, McCrory —
  *Anthropic Economic Index report: Cadences*, 26.06.2026,
  https://www.anthropic.com/research/economic-index-june-2026-report
