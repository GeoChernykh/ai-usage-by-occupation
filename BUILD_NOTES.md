# Build notes

Deviations from `PLAN.md`, gate results, and anything that turned out to differ from §1.

## Gate results

| Gate | Result |
|---|---|
| GATE 0 — repo hygiene | pass. `v0.3` now tracks `origin/v0.3`; `origin/main` still `6bf9451`, `origin/v0.2` still `99cc0c2`. |
| GATE 1 — crosswalks | pass. 18,797 task statements / 923 SOC codes / 18,797 unique Task IDs; per-occupation counts 17 / 17 / 23 / 29 as specified. `world.geojson` 241 features, 1,368 KB, every feature carries an `iso3`, and all 121 dataset country codes are present. |
| GATE 2 — data build | pass on the first run. Every figure in §1.4 and §1.5 reproduced, including the nine per-occupation task counts. Payload 9.49 MB, build 7–10 s. |
| GATE 3 — deploy | see below. |

## Deviations

- **`gh` is not installed on this machine**, so the `github-pages` environment's
  deployment-branch policy could not be inspected or changed from here. Per §2.3 this is not a
  blocker; if the Pages deploy step fails after a green build, set
  **Settings → Environments → github-pages → Deployment branches** to allow `v0.3`.
- **`plan.md` was tracked in lowercase** while the file on disk is `PLAN.md`. Resolved by removing
  the lowercase path from the index and adding `PLAN.md`; the content is unchanged.
- **HKG is not one of the release's 121 published countries.** §7's acceptance criterion lists it
  among the countries that must be coloured on the map, but the source has no Hong Kong row at
  `geo_level='country'`. It renders correctly as "not published". SGP, MLT, BHR and MUS — the other
  four the 110m geometry would have dropped — all carry values, which is what the 50m choice was
  for.
- **Time values print at published precision** rather than one decimal place. §6's acceptance text
  asks for both `9.1 h → 52 min` and `2.05 h → 13.3 min`, which cannot both hold under one
  rounding rule, so the screen shows the published number: `9.12 h → 52.4 min`,
  `2.05 h → 13.3 min`.
- **`index.json.occupations` carries `n_onet` as well as `n_tasks`.** The task table's caption
  ("N of M published") needs the number of tasks O\*NET lists for the occupation, which is not
  derivable from the release alone; `n_tasks` is the published count and `n_onet` the O\*NET total.
- **`series.json.global` is emitted empty.** No panel in §8.2 reads it, and the older releases
  publish the global collaboration and use-case figures under incompatible variable names.
- **`build_series.py` checks the ~100 sum on the weekly files only.** The current release publishes
  only nodes that met its thresholds, so its task shares sum to 88.4 (April) and 94.3 (May) by
  design — §1.4 gives the same 94.32 figure.
- **`uitest.js` is committed although §10's file list does not name it.** It is the headless
  acceptance harness for the three screens; it needs Node and a Playwright Chromium build, is never
  served, and the Pages workflow ignores everything outside `site/`.
- **The subregion table lists ISO 3166-2 codes, not oblast names.** The release publishes no name
  for a subregion node and no local crosswalk exists; `UA-30` is Kyiv city.

## Method check — `build_series.py`

- Median absolute difference in `share_r` across the top 50 occupations, Task ID join against text
  join, May 2026: **0.039 pp**.
- Largest rank change among the top 10 occupations: **26**.
- Decision: `method = "text"`. The rank-movement threshold in §8.1 (more than 3 places for a top-10
  occupation) triggers even though the median difference is far inside tolerance, so every point in
  the series uses the text join. Screen 1's task table keeps the Task ID join, as §8.1 requires.

## Measurements

| Point | Tasks | Text-matched | Matched pp | Occupations |
|---|---|---|---|---|
| Feb 2025 | 3,514 | 80.1% | 74.3 | 654 |
| Mar 2025 | 3,365 | 79.7% | 71.7 | 662 |
| Aug 2025 | 2,618 | 79.1% | 68.0 | 602 |
| Nov 2025 | 3,170 | 79.1% | 67.1 | 628 |
| Feb 2026 | 3,260 | 79.4% | 68.3 | 628 |
| Apr 2026 | 2,410 | 96.2% | 85.0 | 608 |
| May 2026 | 2,713 | 96.1% | 90.8 | 638 |

Every one of these reproduces §1.7 exactly, including the 17,139 unambiguous O\*NET text map.
