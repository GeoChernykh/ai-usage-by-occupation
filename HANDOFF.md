# Handoff — AI usage by occupation explorer

## Live prototype

https://geochernykh.github.io/ai-usage-by-occupation/

Verified end to end: page, `data/index.json`, and a sample `data/occ/<soc>.json`
all return HTTP 200 and parse; deep link e.g.
`?soc=15-1252` selects that occupation on load.

## v0.2 (branch `v0.2`, not yet merged to `main`/live)

User asked for quarter/year comparison instead of just Apr vs May. Investigated
every other release under `data/`: none has a real multi-point time series at
the detailed-occupation level (see `probe_results.md`, "v0.2: major_group_trend
addition"). `release_2026_01_15`/`release_2026_03_24` have zero occupation
facets; `release_2025_09_15` has one extra real point (Aug 2025) but only at
SOC-major-group granularity (23 groups); older releases are static lookups
with no date axis. Rather than fabricate quarters from two months of data,
shipped:
- The month/period toggle is now generated from `indexData.months` instead of
  hardcoded HTML, so it already scales if a future release adds more
  comparable months — no app.js change needed, just re-running
  `build_data.py`.
- A new "Usage trend by job family (coarse groups only)" panel using the one
  real extra data point, rolled up correctly (the detailed months are summed,
  not averaged, per occupation within a `JobFamily`, matching `pct`'s
  documented share-of-total semantics — confirmed detailed `pct` sums to
  ~98.5 across all occupations, same basis as the major-group `soc_pct`
  summing to 100.0). Hidden when the occupation has no `wage_data` match.
  Carries an explicit on-panel caveat about cross-release comparability.

### Global trends (new "Trends" tab, all six releases)

User then asked what real trends *all* the data supports, not just occupation
level. Found and built three genuinely comparable GLOBAL (non-occupation)
metric families — a new tab, independent of the occupation picker:

1. **Automation vs augmentation**, 7 points, Feb 2025 → May 2026. Derived via
   a documented, verified-exact formula (automation% = (directive +
   feedback_loop) / (100 − none) × 100) for the two report-era CSVs and the
   two 2026 raw weekly snapshots that only ship the raw components. Feb 2025
   (V1) is flagged `unnormalized: true` — its six components sum to 84%, not
   ~100% like every later snapshot, for an undocumented reason — and shown
   unscaled rather than guessed-and-rescaled.
2. **Top O\*NET tasks**, up to 6 points each, same 6 real dates. Task text
   confirmed verbatim-stable across every release. Caveat shown on-panel:
   each release re-clusters into a different total task-bucket count
   (2,713–5,236), so a task's share can shift partly from re-bucketing, not
   only real usage change.
3. **Usage patterns** (use_case mix, task success, AI autonomy, human-only/
   with-AI time, human-only ability, multitasking) — 2–3 points each
   (Nov 2025 → May 2026; most of these don't exist before the 2026 weekly
   snapshots).

Explicitly not built: request/topic-level trends over time — verified each
release reruns its own clustering with a non-overlapping label taxonomy, so
comparing "top topics" across releases would compare incompatible categories.

Performance note: the two 2026 weekly raw files are ~100 MB each; refactored
from ~10 full-file re-reads per file down to one chunked pass
(`load_weekly_slice`) with everything else operating in-memory. Full
`build_data.py` run: ~14.5s.

## Source data

| Source | Total rows | Slice rows (soc_occupation, hierarchy_level=0, geo_id=GLOBAL) |
|---|---|---|
| `aei_claude_ai_2026-06-26.csv` | 1,636,573 | 72,107 |
| `aei_1p_api_2026-06-26.csv` | 491,705 | 68,532 |

Occupation universe: 718 distinct SOC codes in the `claude_ai` slice, 701 in
`1p_api`; union across both = **746** (`1p_api` is not a subset of `claude_ai`).
Every occupation in the union got one `site/data/occ/<soc>.json` file.

## Output

- `site/data/index.json` + 746 `site/data/occ/*.json` files.
- Total payload: **5,860,833 bytes** (~5.9 MB), well under the 20 MB budget.
- Reskilling neighbours computed for 516 of the 746 occupations (the rest lack
  a `wage_data` match, a pinned-month automation value, or any same-family
  lower-automation candidate within ±25% salary).

## Scope: nothing dropped, three documented substitutions

All 9 panels from `plan.md` shipped. Three real-data deviations from the
plan's assumptions, all recorded in full in `probe_results.md`:

1. **Delimiter**: source CSVs are comma-delimited, not semicolon as the plan
   assumed.
2. **Usage metric**: inside the target slice, the per-occupation usage share
   is carried under metric_id `"pct"`, not `"usage_pct"` (`usage_pct` only
   exists at `category_name="overall"`). Kept as `"pct"` verbatim in every
   `metrics` blob (never invented); surfaced as the app-level field
   `usage_pct` only in `index.json`'s flat occupation summaries.
3. **Wage forecast**: `wage_data.csv`'s `JobForecast` column is a projected
   employment count, not a label, so `wage.forecast` ("Bright" / "Not bright")
   is derived from the `isBright` boolean column instead.

Also: `JobZone == -1` and `ChanceAuto == -1` are missing-value sentinels in
`wage_data.csv` — omitted from output rather than written as `-1`.

## Regenerating everything

```bat
.venv\Scripts\python.exe probe.py
.venv\Scripts\python.exe build_data.py
```

(POSIX: `.venv/bin/python probe.py` / `build_data.py`.)

`requirements.txt` (pandas + transitive deps, already installed into `.venv`):

```
numpy==2.5.3
pandas==3.0.5
python-dateutil==2.9.0.post0
six==1.17.0
tzdata==2026.4
```

## Deploy notes

GitHub Pages' "Deploy from a branch" source only offers `/(root)` or `/docs`,
not `/site`, so deployment uses the Actions-based Pages source instead:
`.github/workflows/pages.yml` uploads `site/` as the Pages artifact on every
push to `main`. Repo Settings → Pages → Source must be **"GitHub Actions"**,
not "Deploy from a branch".

## What the reviewer will see (no screenshots taken — no browser UI tool was
available this session; verified instead via a headless Puppeteer smoke test)

- **Software Developers (15-1252)**: KPI row shows exposure 0.288, usage 0.3%
  (▲0.0pp Apr→May), automation/augmentation 60.8%/39.2% (▲0.4pp), salary
  chip reads "not published" (no `wage_data` match for this SOC — reskilling
  panel correctly hidden). Time-compression panel: "Without AI: 5.9 hours.
  With Claude: 48 minutes," plus a bar comparing against the all-occupation
  median.
- **Acute Care Nurses (29-1141)**: salary $71,730 renders normally, automation
  41.8%/augmentation 58.2% (▼1.9pp Apr→May), reskilling neighbours panel shown.
- **Refuse and Recyclable Material Collectors (53-7081)**: usage_pct is a real
  0.0% (rendered as "0.0%", not a grey "not published" chip — confirms the
  zero-vs-missing distinction holds), automation 96.3%.
- Toggling source/month re-renders instantly with zero network requests
  (checked via response-listener instrumentation). CSV download produces a
  205-line file (header + one row per source×month×metric). Page has no
  horizontal scroll at 400px width.
