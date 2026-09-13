# AGENT PLAN — AI usage explorer for occupations

Executable plan for a coding agent. Working directory: `C:\PythonProjects\CSS\Anthopic Usage`.
Deliverable: a static web front-end over a precomputed slice of the Anthropic Economic Index.
No backend. No framework. No build step for the page itself.

---

## 0. Rules

1. **Never modify anything under `data/`.** It is the source corpus, read-only.
2. **Never invent a `metric_id`, column name, or SOC code.** Every identifier used in code must
   have been observed in Task 1's probe output. If something you need is not in the probe output,
   stop and report.
3. **A missing metric means "not published", never 0.** This applies in the build script
   (omit the key) and in the UI (render a grey "not published" chip).
4. **Do not proceed past a GATE** until its acceptance criteria pass. If they fail, follow the
   `On failure` branch; if that also fails, stop and report rather than improvising.
5. Write all intermediate findings to files in the repo, not only to stdout — later tasks read them.
6. Keep the page dependency-free except Plotly from CDN, and the Python side dependency-free
   except pandas.
7. **A virtual environment already exists at `.venv/` in the repo root. Install every package into
   it and run every Python command through it.** Never install into the system interpreter, never
   invoke a bare `python`. On this machine (Windows) that means `.venv\Scripts\python.exe`; the
   POSIX equivalent is `.venv/bin/python`. Record every package you install in `requirements.txt`.

---

## 1. Environment and schema probe  ⟶ GATE

**Goal:** confirm every assumption this plan rests on before writing any product code.

**Do:**

Use the existing virtual environment at `.venv/`. Activate it, or call its interpreter by path —
either is fine, but be consistent, and never fall back to a system `python`:

```bat
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install pandas
python -m pip freeze > requirements.txt
python -c "import sys, pandas; print(sys.executable); print(pandas.__version__)"
```

The printed `sys.executable` must point inside `.venv`. If it does not, the environment is not
active — stop and fix that before continuing. pandas is the only dependency this project needs;
if a later task genuinely requires another package, install it into `.venv` and regenerate
`requirements.txt`.

Write and run `probe.py`. It must read the two large CSVs **in chunks** and never load one whole:

```python
import pandas as pd

reader = pd.read_csv(path, sep=";", dtype=str, chunksize=500_000)
```

`dtype=str` is deliberate — it prevents mixed-type warnings and keeps `hierarchy_level`
comparable as the string `"0"`. Convert `value` with `pd.to_numeric(..., errors="coerce")`
only after filtering.

Accumulate distinct values across chunks into Python `set`s and counts into a running total;
do not concatenate the chunks. Append results to `probe_results.md`:

Source files:
- `data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv`
- `data/release_2026_06_26/data/aei_1p_api_2026-06-26.csv`
- `data/labor_market_impacts/job_exposure.csv`
- `data/release_2025_02_10/wage_data.csv`

Report, for each of the two big CSVs:
1. Total row count.
2. Distinct `category_name`, `geo_level`, `hierarchy_level`, `date_start`.
3. Full sorted list of distinct `metric_id` (expect 53).
4. Row count for the target slice:
   `category_name='soc_occupation' AND hierarchy_level=0 AND geo_id='GLOBAL'`.
5. Distinct count of `node_name` in that slice.
6. Ten sample `node_external_id` values from that slice — **record the exact format**
   (`11-1011` vs `11-1011.00`).
7. For one occupation in that slice, the full list of `metric_id` present, per `date_start`.

And for the lookups:
8. `job_exposure.csv` — header, row count, ten sample `occ_code` values.
9. `wage_data.csv` — header, row count, ten sample `SOCcode` values.
10. Overlap counts after normalising codes by stripping a trailing `.00` from all three sides:
    how many of the slice's occupations match `job_exposure`, how many match `wage_data`.

**Acceptance criteria:**
- `aei_claude_ai` row count = 1,636,573; `aei_1p_api` row count = 491,705.
- `category_name` distinct set = `{onet, overall, request, soc_occupation}`.
- `date_start` distinct set = `{2026-04-01, 2026-05-01}`.
- The metric list contains `usage_pct`, `collaboration_bucket_automation_pct`,
  `collaboration_bucket_augmentation_pct`, `human_only_time_mean`, `human_with_ai_time_mean`,
  `ai_autonomy_mean`, `use_case_work_pct`, and at least 20 `artifact_*_pct` metrics.
- The target slice is non-empty and covers ≥ 500 distinct `node_name`.
- After normalisation, ≥ 60 % of slice occupations match `job_exposure` **and** ≥ 60 % match
  `wage_data`.

**On failure:**
- Row counts differ → the local copy differs from the surveyed one. Record actual counts in
  `probe_results.md`, use those everywhere downstream, continue.
- Code-match rate below 60 % → try matching on `node_name` ↔ `job_exposure.title` /
  `wage_data.JobName` (case-insensitive, trimmed). If that also fails, drop the exposure score
  and the reskilling panel from scope, note it in `probe_results.md`, and continue with the
  remaining panels.
- Target slice empty → re-check `hierarchy_level` type (it may be read as string `'0'`).

---

## 2. Build script `build_data.py`

**Goal:** turn ~283 MB of CSV into a few MB of static JSON.

**Do:** write `build_data.py` at the repo root. It must be idempotent and runnable as
`python build_data.py`.

Steps inside it:

1. Extract the target slice from both big CSVs, chunked, keeping only the columns needed:
   ```python
   COLS = ["node_name", "node_external_id", "metric_id", "date_start", "value",
           "category_name", "hierarchy_level", "geo_id"]
   KEEP = ["node_name", "node_external_id", "metric_id", "date_start", "value"]

   def extract(path):
       parts = []
       for chunk in pd.read_csv(path, sep=";", usecols=COLS, dtype=str,
                                chunksize=500_000):
           mask = ((chunk["category_name"] == "soc_occupation")
                   & (chunk["hierarchy_level"] == "0")
                   & (chunk["geo_id"] == "GLOBAL"))
           parts.append(chunk.loc[mask, KEEP])
       df = pd.concat(parts, ignore_index=True)
       df["value"] = pd.to_numeric(df["value"], errors="coerce")
       return df.dropna(subset=["value"])
   ```
   `usecols` plus `chunksize` keeps peak memory in the low hundreds of MB. The surviving slice is
   roughly 85 k rows, so every later step operates on a small frame.
2. Normalise SOC codes with a single helper (strip whitespace, strip a trailing `.00`).
3. Load `job_exposure.csv` (`occ_code`, `title`, `observed_exposure`) and `wage_data.csv`
   (`SOCcode`, `JobName`, `JobFamily`, `JobZone`, `MedianSalary`, `ChanceAuto`, `JobForecast`).
4. Compute all-occupation medians, per source and per month, for every metric — used by the
   comparison bars in the UI: `df.groupby(["date_start", "metric_id"])["value"].median()`.
5. Compute reskilling neighbours per occupation: same `JobFamily`, `collaboration_bucket_automation_pct`
   lower than the subject's, `MedianSalary` within ±25 % of the subject's. Take the three with the
   lowest automation %. Omit the key entirely if `wage_data` did not match.
6. Write output (see schemas below), creating `site/data/occ/`.
7. Print to stdout, and append to `build_log.txt`: source row counts, slice row counts, occupation
   count, number of files written, total output bytes.

### `site/data/index.json`

```json
{
  "generated_at": "2026-09-13T18:00:00Z",
  "source_release": "release_2026_06_26",
  "source_rows": { "claude_ai": 1636573, "1p_api": 491705 },
  "months": ["2026-04-01", "2026-05-01"],
  "sources": ["claude_ai", "1p_api"],
  "medians": {
    "claude_ai": { "2026-05-01": { "human_only_time_mean": 2.1, "…": 0.0 } }
  },
  "occupations": [
    {
      "soc": "15-1252",
      "title": "Software Developers",
      "exposure": 0.41,
      "usage_pct": 3.2,
      "automation_pct": 38.1,
      "salary": 132270,
      "job_family": "Computer and Mathematical"
    }
  ]
}
```

`occupations` is sorted by `usage_pct` descending. Keys whose source value was absent are omitted.

### `site/data/occ/<soc>.json`

Filename uses the normalised code with `-` preserved, e.g. `15-1252.json`.

```json
{
  "soc": "15-1252",
  "title": "Software Developers",
  "exposure": 0.41,
  "wage": {
    "median_salary": 132270, "job_family": "Computer and Mathematical",
    "job_zone": 4, "chance_auto": 0.04, "forecast": "Bright"
  },
  "neighbours": [
    { "soc": "15-1211", "title": "Computer Systems Analysts",
      "automation_pct": 29.4, "salary": 103790 }
  ],
  "metrics": {
    "claude_ai": {
      "2026-04-01": { "usage_pct": 3.1, "collaboration_bucket_automation_pct": 37.8 },
      "2026-05-01": { "usage_pct": 3.2, "collaboration_bucket_automation_pct": 38.1 }
    },
    "1p_api": { "2026-04-01": {}, "2026-05-01": {} }
  }
}
```

**Acceptance criteria:**
- `.venv\Scripts\python.exe build_data.py` completes without error in under 10 minutes.
- `site/data/index.json` exists, parses, and `occupations` length equals the distinct `node_name`
  count recorded in `probe_results.md`.
- One `site/data/occ/*.json` exists per entry in `occupations`; every file parses.
- Total size of `site/data/` is under 20 MB.
- Spot-check: pick three occupations at random; each has ≥ 20 metrics for
  `claude_ai` / `2026-05-01`.
- No value in any output is `NaN`, `Infinity`, or the string `"nan"`.

**On failure:** if the process exhausts memory, lower `chunksize` to 100_000 and confirm `usecols`
is being passed — reading all ten columns roughly triples peak memory. Do not reduce the number of
metrics kept. If `pd.concat` warns about empty or all-NA entries, filter empty parts out before
concatenating rather than suppressing the warning.

---

## 3. Front end `site/index.html`, `site/app.js`, `site/style.css`

**Goal:** a single-page explorer. Load `index.json` once, fetch one occupation file on selection.

Controls, fixed at the top: occupation search/select; source toggle
(`claude_ai` = "Consumer (Claude apps)" / `1p_api` = "Enterprise API"); month toggle (Apr / May).
Changing source or month re-renders from already-loaded JSON — no refetch.

Panels, in this order:

1. **KPI row** — exposure score, `usage_pct`, automation vs augmentation %, median salary.
   Each KPI shows an Apr→May delta arrow (▲/▼ plus the point difference).
2. **Time compression** — headline. `human_only_time_mean` (hours) → `human_with_ai_time_mean`
   (minutes), rendered as a large sentence, plus a horizontal bar comparing the occupation to the
   all-occupation median from `index.json.medians`.
3. **Automation vs augmentation** — 100 % stacked horizontal bar from the two
   `collaboration_bucket_*_pct` metrics.
4. **Collaboration patterns** — bar chart of the six `collaboration_{directive,feedback_loop,
   task_iteration,learning,validation,none}_pct`.
5. **Artifact mix** — top 8 `artifact_*_pct` by value, horizontal bars, label humanised
   (`artifact_code_fix_or_debug_pct` → "Code fix or debug"). Title: "What AI actually produces
   for this job".
6. **Consumer vs enterprise** — diverging horizontal bars comparing `claude_ai` and `1p_api`
   for the same occupation on a fixed set of metrics: `usage_pct`,
   `collaboration_bucket_automation_pct`, `ai_autonomy_mean`, `use_case_work_pct`.
   Ignores the source toggle; always shows both.
7. **Skill gap** — `human_education_years_mean` vs `ai_education_years_mean`, plus
   `human_only_ability_pct` and `ai_autonomy_mean` as labelled readouts.
8. **Reskilling neighbours** — table from `neighbours`: title, automation %, median salary.
   Hidden entirely if the key is absent.
9. **Download** — button producing a CSV of the currently selected occupation's metrics
   (all sources, all months) via a client-side `Blob`. No library.

**Required behaviours:**
- Any metric absent from the JSON renders as a grey "not published" chip. Never 0, never blank,
  never `undefined`.
- Deep link: `?soc=15-1252` selects that occupation on load; selecting updates the URL via
  `history.replaceState`.
- Page is usable at 400 px width — panels stack to one column.
- Footer, always visible, verbatim:
  > Measures Claude usage among Claude users, mapped onto US O\*NET/SOC classifications — not AI
  > exposure of an occupation in general. The Enterprise API source excludes Claude Code, which
  > understates developer occupations. Cells that did not meet publication thresholds are shown as
  > "not published", not as zero. Source: Anthropic Economic Index, release 2026-06-26, CC-BY.

**Acceptance criteria:**
- Served with `python -m http.server` from `site/`, the page loads with no console errors.
- Selecting three different occupations re-renders all panels with plausible values.
- An occupation with sparse `1p_api` data shows "not published" chips rather than zeros or blanks.
- Toggling source and month changes the charts without a network request (verify in devtools).
- The CSV download produces a file with a header row and one row per metric.

---

## 4. Deploy

**Do:**
1. `git init` at the repo root if absent. Add `.gitignore` containing `/data/`, `.venv/`,
   `__pycache__/` and `*.pyc`. Anchor the data rule with a leading slash — an unanchored `data/`
   also ignores `site/data/` and the deployed page will 404 on every JSON file.
2. Commit `build_data.py`, `probe.py`, `probe_results.md`, `build_log.txt`, `requirements.txt`,
   `site/**`, `IDEA.md`, `plan.md`. Do not commit `.venv/` or anything under `data/`.
3. Create a GitHub repo with a URL-safe name (the current folder name contains a space and a
   typo — do not reuse it), push, enable GitHub Pages serving from `/site` on the default branch.
4. Wait for the Pages build, then fetch the public URL and confirm HTTP 200 for
   `index.html`, `data/index.json`, and one `data/occ/*.json`.

**Acceptance criteria:** the public URL renders the page and one occupation loads end to end
in a fresh browser profile.

**On failure:** if Pages returns 404 for the JSON, confirm `site/data/` was committed
(check it is not swallowed by a `data/` ignore rule — the ignore rule must be anchored: `/data/`).

---

## 5. Handoff report

Write `HANDOFF.md` containing:
- The public prototype URL.
- Source row counts and slice counts, copied from `build_log.txt`.
- Output payload size and occupation count.
- Which panels were dropped, if any, and why (from Task 1's failure branches).
- The exact command to regenerate everything, including the `.venv` interpreter path, and the
  contents of `requirements.txt`.
- Three screenshots' worth of description, or the screenshots themselves, for the report PDF.

---

## Out of scope — do not build

- Any backend, server, or API.
- Multi-release time series. Releases 4–5 use the schema
  `geo_id;geography;date_start;date_end;platform_and_product;facet;level;variable;cluster_name;value`
  and would need a crosswalk. The Apr→May comparison inside release 6 replaces it.
- The 2025 `automation_vs_augmentation*.csv` tables — superseded by `collaboration_bucket_*_pct`.
- O\*NET task-level breakdown per occupation — requires an unverified Task ID ↔ SOC join.
- `bls_employment_may_2023.csv` — 22 rows, major groups only, cannot weight detailed occupations.
- Country choropleth, treemaps, any `category_name` other than `soc_occupation`.

## Escalate to the human

Stop and report instead of guessing if:
- Task 1 acceptance fails and both failure branches fail.
- Any source file under `data/` is missing or unreadable.
- `site/data/` would exceed 20 MB.
- GitHub credentials or repo creation permissions are unavailable.
