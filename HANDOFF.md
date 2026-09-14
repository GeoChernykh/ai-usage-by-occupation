# Handoff — AI Time Machine (v0.3)

Live URL: <https://geochernykh.github.io/ai-usage-by-occupation/>
Branch: `v0.3`. `main` (`6bf9451`) and `v0.2` (`99cc0c2`) are untouched.

## One outstanding action, and it is not in the code

The `github-pages` environment allows deployments from `main` only, so every push to `v0.3` builds
green and then fails at the deploy step in about three seconds. Fix it once:

**Settings → Environments → github-pages → Deployment branches → Add `v0.3`**, then re-run the most
recent *Deploy Pages* run on `v0.3`.

Until that is done, the live URL still serves the old v0.2 build. Everything else is finished and
verified locally.

## What shipped

| Screen | State |
|---|---|
| 1 — Time card | shipped: search over 746 occupations and 2,823 tasks, four KPI cards, the time-compression hero, the ranked task table, collaboration and artifact mixes, methodology popovers, CSV export |
| 2 — Compare | shipped: education scatter with the parity line, two-occupation bars, the seven-point release slope chart with its permanent caveat |
| 3 — Geography | shipped: world choropleth bound by ISO3, ranked country table, use-case and artifact panels, the Ukrainian subregion table |

Nothing from the plan's committed scope was dropped. Out-of-scope items (subregion choropleth,
task→DWA rollups, cross-release request topics, wage joins, confidence intervals) were not built,
as specified.

## Data pipeline

| Stage | Figure |
|---|---|
| `aei_claude_ai_2026-06-26.csv` | 1,636,573 rows read, 408,270 kept |
| `aei_1p_api_2026-06-26.csv` | 491,705 rows read, 289,159 kept |
| Slices | occupations 140,639 · major groups 4,386 · tasks 261,013 · countries 12,220 · subregions 60,686 |
| Task → occupation join | **100.0%** of the 2,823 task ids resolved through O\*NET 30.0 |
| Occupation universe | 746 (718 `claude_ai`, 701 `1p_api`), 655 with at least one task |
| Cross-release text join | 17,139 unambiguous O\*NET texts; 67.1–90.8 pp matched per release |
| Runtime | `build_data.py` ~7 s, `build_series.py` ~40 s |

Payload: **9.49 MB** across 752 files — 746 occupation files plus five payloads and
`world.geojson`. That is the byte total GATE 2 measures, against a 12 MB ceiling. `du` reports
11.9 MB for the same directory; the difference is block allocation over 746 small files, not
content. `site/vendor/echarts.min.js` adds 1.0 MB outside `site/data`.

`verify_data.py` passes every GATE 2 assertion, including all nine §1.4 occupation fixtures with
their task counts, the seven §1.5 country figures, and the Ukrainian subregion totals.

## Series method decision

`method = "text"`. The Task ID join and the text join agree closely in magnitude — median absolute
difference **0.039 pp** across the top 50 occupations — but a top-10 occupation moves **26** ranks
between them, which trips §8.1's three-rank threshold. Every point in the series therefore uses the
text join, and the panel caveat says so. Screen 1's task table keeps the Task ID join.

## Demo script, checked against the built page

| Claim | On screen |
|---|---|
| Computer Programmers: 9.1 h → 52 min | 9.12 h → 52.4 min, 10.5× |
| Computer Science Teachers, Postsecondary: 5.2 h → 48 min, 53% coursework | 5.21 h → 48.09 min, 53.07% coursework |
| Ukraine: index 0.78, rank 68 of 121 | 0.78, rank 68 of 121 |
| Document Management Specialists | 2.05 h → 13.3 min, 9.2×, 12 tasks |

## Regenerating

```bat
.venv\Scripts\python.exe fetch_lookups.py
.venv\Scripts\python.exe build_data.py
.venv\Scripts\python.exe build_series.py
.venv\Scripts\python.exe verify_data.py
```

`requirements.txt`: `numpy==2.5.3`, `pandas==3.0.5`, `python-dateutil==2.9.0.post0`, `six==1.17.0`,
`tzdata==2026.4`. Nothing was added to the environment for this work — the downloads use
`urllib.request` and the outputs use `json`.

`uitest.js` (Node plus `playwright-core` and a Playwright Chromium build) drives all three screens
headless and asserts the figures above; it is a development aid and is not deployed.

See `BUILD_NOTES.md` for the gate results and every deviation from the plan.
