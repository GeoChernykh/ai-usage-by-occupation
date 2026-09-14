# AI Time Machine

A static, three-screen explorer over the [Anthropic Economic
Index](https://huggingface.co/datasets/Anthropic/EconomicIndex), release 2026-06-26. It answers one
question per screen:

- **Time card** — for an occupation, how long the work Claude is asked to do takes unaided and with
  Claude, which O\*NET tasks sit behind it, and what Claude actually produces.
- **Compare** — where Claude sits against the human education bar, one occupation against another,
  and how a share moved across the six published releases.
- **Geography** — where Claude is used and how intensely relative to the working-age population,
  down to subregions where they are published.

Live: <https://geochernykh.github.io/ai-usage-by-occupation/>

## How it works

There is no backend and no build step on the server. Three Python scripts precompute a JSON payload
into `site/`, and GitHub Pages serves that directory verbatim. The front-end is plain ES modules
with a vendored copy of Apache ECharts — no npm, no bundler, no framework.

```
site/
  index.html  style.css  app.js
  lib/     data.js  format.js  search.js  charts.js  csv.js
  screens/ time.js  compare.js  geo.js
  vendor/  echarts.min.js
  data/    index.json  occ/*.json  tasks.json  countries.json
           subregions.json  series.json  world.geojson
```

## Regenerating the data

The release corpus lives under `data/` and is gitignored; everything the site needs is committed.
Run the scripts in this order, always through the virtual environment:

```bat
.venv\Scripts\python.exe fetch_lookups.py    :: O*NET 30.0, Natural Earth 50m, ECharts (idempotent)
.venv\Scripts\python.exe build_data.py       :: index.json, occ/*.json, tasks, countries, subregions
.venv\Scripts\python.exe build_series.py     :: series.json, the cross-release shares
.venv\Scripts\python.exe verify_data.py      :: asserts the payload against the release fixtures
```

`requirements.txt` pins pandas and its transitive dependencies; the downloads use `urllib.request`
and the outputs use `json`, both from the standard library.

To preview locally: `.venv\Scripts\python.exe -m http.server 8765` from inside `site/`.

`uitest.js` drives all three screens in a headless browser and checks the figures this project
claims. It needs Node and `playwright-core` plus a Playwright Chromium build; it is a development
aid, not part of the deployed site.

## What the numbers mean, and what they do not

- Shares are shares **of Claude usage**, never of the economy, and they measure Claude users rather
  than the workforce.
- The occupation mapping is onto US O\*NET/SOC classifications. It is not a claim about AI exposure
  of an occupation in general.
- Time figures are model estimates, not stopwatch measurements.
- Cells that did not meet Anthropic's publication thresholds render as "not published", never as
  zero.
- The Enterprise API source excludes Claude Code, which understates developer occupations, and is
  published globally only — so the Geography screen has no source toggle.
- Releases are discrete published snapshots, not a continuous time series. Each one re-clusters
  usage into its own O\*NET task set, so the Compare slope chart renormalises within the matched
  subset and should be read for direction, not level.
- Tasks are joined to occupations through the O\*NET 30.0 Task Statements. The two copies of
  `onet_task_statements.csv` inside the release corpus are O\*NET v20.1 on the 2010 SOC and resolve
  the entire 15-12xx software family to zero tasks; they are deliberately unused.

## Licences

Anthropic Economic Index (CC BY); O\*NET 30.0 Database, U.S. Department of Labor / ETA (CC BY 4.0);
Natural Earth country outlines (public domain); Apache ECharts 5.6.0 (Apache-2.0).
