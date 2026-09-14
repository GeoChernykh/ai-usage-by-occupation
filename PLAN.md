# AGENT PLAN — "AI Time Machine" (v0.3)

Executable plan for a coding agent. Working directory: `C:\PythonProjects\CSS\Anthopic Usage`.
Product spec: `IDEA.md`. Visual spec: `dashboard-style-prompt.md` (**binding**, see §0.4).
Deliverable: a static, three-screen web front-end over a precomputed slice of the Anthropic
Economic Index, deployed to GitHub Pages **from the `v0.3` branch**.

Everything in §1 was verified against the local corpus on 15.09.2026 before this plan was
written. Treat §1 as ground truth and **do not re-scan the 219 MB CSV to re-derive it**.

---

## 0. Rules

1. **Branch discipline.** All work happens on `v0.3`. Never `git merge`, never `git rebase` onto
   another branch, never push to `main` or `v0.2`. See §2.1 — `v0.3` currently tracks
   `origin/v0.2`, which must be fixed **before any push**.
2. **Never modify anything under `data/`.** It is the read-only source corpus and it is
   gitignored (`/data/`).
3. **Never invent a `metric_id`, column name, SOC code or O\*NET Task ID.** Every identifier in
   code must appear in §1 or in a file you have opened. If you need one that is not there, stop
   and report.
4. **A missing metric means "not published", never 0.** In the build script: omit the key. In the
   UI: render a grey "not published" chip. A real published `0.0` must still render as `0.0%`.
5. **Do not proceed past a GATE** until its acceptance criteria pass. Each gate has an
   `On failure` branch; if that also fails, stop and report rather than improvising.
6. **Python runs only through `.venv`.** `.venv\Scripts\python.exe` (POSIX: `.venv/bin/python`).
   Never a bare `python`. Every package you install goes into `.venv` **and** into
   `requirements.txt` (`.venv\Scripts\python.exe -m pip freeze > requirements.txt`).
   The current pinned set is pandas + its transitive deps; nothing else is needed — downloads use
   `urllib.request` (stdlib), JSON uses `json` (stdlib).
7. **No npm, no bundler, no framework** — see §0.3.
8. Write findings to files in the repo (`BUILD_NOTES.md`), not only to stdout.

### 0.1 Deadline and staging

The submission deadline is **17.09.2026**. Build in this order and commit after each stage, so
that an incomplete later stage never breaks an earlier one:

| Stage | Contents | Status |
|---|---|---|
| A | §2 repo hygiene + §3 crosswalks | required |
| B | §4 `build_data.py` core outputs + §5 shell + §6 Screen 1 | **committed scope** |
| C | §7 Screen 3 (Geography) | **committed scope** |
| D | §8 `series.json` + Screen 2 (Compare) | margin — if it is not finished, the tab is hidden |
| E | §9 cross-cutting polish, §10 deploy, §11 handoff | required |

Stage D must degrade cleanly: if `site/data/series.json` is absent, the app hides the Compare tab
and everything else still works. Never ship a tab that throws.

### 0.2 What already exists

- `.venv/` with pandas 3.0.5 / numpy 2.5.3 on Python 3.14.2 — use it, do not recreate it.
- `.github/workflows/pages.yml` — Actions-based Pages deploy of `site/`, currently triggered on
  `main` only. §2.3 changes it.
- `build_data.py` (v0.2, at repo root) — it builds a **different, single-screen** product. Treat
  it as reference material for chunked reading only; §4 replaces it wholesale.
- The working tree has the entire v0.2 `site/` deleted and `IDEA.md` rewritten. §2.2 commits that.
- Live v0.2 page: https://geochernykh.github.io/ai-usage-by-occupation/ — deploying from `v0.3`
  replaces what is served there. That is intended and authorised.

### 0.3 Stack — settled, do not relitigate

- **No bundler, no framework, no npm.** Plain ES modules (`<script type="module">`), served
  verbatim by the existing Pages workflow. A Vite/React build would add a build step, a `base`
  path and a workflow rewrite, and buys nothing here.
- **Apache ECharts 5.6.0**, vendored (not CDN) at `site/vendor/echarts.min.js` — 1,010 KB, fetched
  once from `https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js` and committed. UMD
  build, loaded with a classic `<script>` before the module entry, exposing `window.echarts`.
  Vendoring pins the version and keeps the page working offline while the demo video is recorded.
- **No `fuse.js`.** Case-insensitive substring + token-prefix match over 746 titles is enough;
  write ~20 lines in `lib/search.js`.
- All fetch paths are **relative** (`data/index.json`, never `/data/index.json`) — the site is
  served from `/ai-usage-by-occupation/`, so a leading slash 404s.

### 0.4 Visual contract

`dashboard-style-prompt.md` is **binding** for all visual decisions: the grey page/slab frame, the
left icon rail, the six-hex palette, the white radius-8 cards, the stripped charts, the type
scale, and the whole "Avoid" list. Where it and `IDEA.md` disagree, it wins. Concretely:

- **Light only.** IDEA §6's "light/dark theme" line is **dropped**. Do not build a theme toggle.
- **No emoji anywhere**, no trend arrows, no green/red deltas, no icons inside KPI cards, no
  gradients, no hover lifts, no entrance animations.
- Rail icons are inline SVG line icons (24px, `stroke: currentColor`, 1.5px), not emoji, not an
  icon font.
- IDEA §6's remaining cross-cutting items (URL state, CSV export, responsive to 400px,
  methodology popovers, persistent footer) all stay — they are behaviour, not aesthetics.

---

## 1. Ground truth (verified 15.09.2026 — do not re-derive)

### 1.1 The current release file

`data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv` — 219 MB, **comma-delimited**
(not semicolon), 10 columns:

```
date_start,date_end,geo_id,geo_level,category_name,hierarchy_level,metric_id,value,node_name,node_external_id
```

| Fact | Value |
|---|---|
| Rows, `claude_ai` | **1,636,573** |
| Rows, `aei_1p_api_2026-06-26.csv` (77 MB) | **491,705** |
| `date_start` | `2026-04-01`, `2026-05-01` (`date_end` = +1 month) |
| `geo_level` | `global`, `country` (**121** ISO-3166 alpha-3), `subregion` (**652**, ISO 3166-2 style, e.g. `UA-30`) |
| `category_name` | `onet`, `overall`, `request`, `soc_occupation` |
| `metric_id` | **53** distinct file-wide |

`hierarchy_level` is **finest-first**: `0` = O\*NET Task / detailed SOC occupation / detailed
request topic. Read it as a **string** (`"0"`), never as an int.

### 1.2 Which metrics are published where — this is the trap

`usage_pct` and `usage_per_capita_index` exist **only** at `category_name='overall'`.
Inside every node category the per-node share is carried under the bare metric id **`pct`**.
Use `"pct"` verbatim in any `metrics` blob; `usage_pct` may appear only as an app-level derived
field name.

At `geo_id='GLOBAL'`:

| Slice | Rows | Nodes | Metrics |
|---|---|---|---|
| `soc_occupation` L0 (detailed occupation) | 72,107 | **718** | 51 (incl. `pct`) |
| `soc_occupation` L1 (SOC major group, ext id = `"15"`) | 2,244 | 23 | 51 |
| `onet` L0 (Task, ext id = numeric **O\*NET Task ID**) | 261,013 | **2,823** (2,713 in May) | 51 |
| `onet` L1 (DWA, ext id `4.A.1.a.2.I01.D05`) | 71,070 | — | 51 |
| `onet` L2 (IWA, ext id `4.A.3.b.6.I09`) | 20,599 | — | 51 |
| `onet` L3 (GWA, ext id `4.A.3.a.2`) | 3,570 | ~37 | 51 |
| `request` L0/L1/L2 (ext id = UUID) | 102,406 / 19,788 / 2,040 | — | 51 |
| `overall` L0 | — | 1 | **52** (incl. `usage_pct`, `usage_per_capita_index`; no `pct`) |

The DWA/IWA/GWA ids are prefix-nested (`4.A.1.a.2.I01` + `.D05`), so the ladder above Task level
is derivable by string prefix with no extra file. Task → DWA is **not** derivable — do not try.

**At `geo_level='country'` the coverage inverts.** The full 51-metric set is published only at the
*coarse* levels; the fine levels carry `pct` only:

| Country slice | Rows | Metrics |
|---|---|---|
| `overall` L0 | 12,220 | **52** (235 rows per metric = 121 countries × 2 months, 7 suppressed) |
| `soc_occupation` L0 | 34,253 | `pct` only |
| `soc_occupation` L1 | 162,097 | 51 |
| `onet` L0 / L1 / L2 | 33,886 / 21,795 / 13,259 | `pct` only |
| `onet` L3 (GWA) | 182,122 | 51 |
| `request` L2 | 155,220 | 51 |

`aei_1p_api_2026-06-26.csv` is **`geo_level='global'` only** — the source toggle must not appear
on Screen 3.

### 1.3 The 52 / 53 metric ids

`ai_autonomy_mean`, `ai_education_years_mean`, `human_education_years_mean`,
`human_only_ability_pct`, `human_only_time_mean` (hours), `human_with_ai_time_mean` (minutes),
`multitasking_pct`, `pct`, `usage_pct`, `usage_per_capita_index`,
`use_case_{work,personal,coursework}_pct`,
`collaboration_bucket_{automation,augmentation}_pct`,
`collaboration_{directive,feedback_loop,task_iteration,learning,validation,none}_pct`,
and **34** `artifact_*_pct`:
`academic_paper_or_thesis`, `advice_or_recommendation`, `analysis_or_summary`, `app_or_website`,
`audio_or_music`, `blog_or_article`, `chart_or_visualization`, `code_fix_or_debug`,
`config_or_infra`, `creative_writing`, `data_or_spreadsheet`, `document_or_report`,
`educational_material`, `email_or_message`, `explanation_or_answer`, `game_or_interactive`,
`idea_or_brainstorm`, `image_or_graphic`, `marketing_or_social_content`, `math_or_calculation`,
`ml_or_ai_system`, `none`, `other`, `plan_or_strategy`, `presentation_or_slides`,
`recipe_or_meal_plan`, `resume_or_job_application`, `script_or_snippet`, `sql_or_database_query`,
`translation`, `ui_or_design_mockup`, `video_or_animation`.

### 1.4 Verified occupation values (`claude_ai`, GLOBAL, `2026-05-01`)

Every figure in `IDEA.md` §5 reproduced exactly. Use these as regression fixtures.

| SOC (`node_external_id`) | Title | `pct` | `human_only_time_mean` | `human_with_ai_time_mean` | speed-up |
|---|---|---|---|---|---|
| `15-1299.03` | Document Management Specialists | 5.10 | 2.05 h | 13.3 min | 9.2× |
| `25-4022.00` | Librarians and Media Collections Specialists | 4.22 | 2.41 h | 20.5 min | 7.1× |
| `27-3041.00` | Editors | 2.58 | 4.88 h | 46.2 min | 6.3× |
| `15-1211.00` | Computer Systems Analysts | 1.91 | 5.21 h | 66.4 min | 4.7× |
| `15-1251.00` | Computer Programmers | 1.67 | 9.12 h | 52.4 min | 10.5× |
| `15-1252.00` | Software Developers | 0.35 | 5.90 h | 47.8 min | 7.4× |
| `23-1011.00` | Lawyers | 0.62 | 5.83 h | 54.1 min | 6.5× |
| `13-2011.00` | Accountants and Auditors | 0.12 | 9.49 h | 47.1 min | 12.1× |
| `25-1021.00` | Computer Science Teachers, Postsecondary | 0.01 | 5.21 h | 48.1 min | 6.5× |

- `pct` over all 718 occupations sums to **98.51**; over all 2,713 May tasks to **94.32**.
  These are shares of total geography usage, so the correct roll-up is **SUM, not mean**.
- **717 of 718** occupations have both time metrics in May.
- Occupation universe: 718 in `claude_ai`, 701 in `1p_api`, **union = 746** (`1p_api` is not a
  subset). Every screen's occupation list is the union.

### 1.5 Country values (`claude_ai`, `country`/`overall`, `2026-05-01`)

| Metric | UKR | Rank | Top 3 |
|---|---|---|---|
| `usage_per_capita_index` | 0.78 | 68 / 121 | AUS 6.40, SGP 5.81, CHE 5.02 |
| `usage_pct` | 0.47 | 38 / 121 | USA 20.16, IND 7.12, FRA 3.95 |
| `use_case_coursework_pct` | 18.77 | 67 / 121 | TUN 51.52, DZA 47.12, IDN 45.88 |
| `use_case_work_pct` | 40.61 | 64 / 121 | BRA 57.35, ARE 54.63, ISR 53.32 |
| `collaboration_bucket_automation_pct` | 48.90 | 67 / 121 | ZWE 57.63, MNG 57.44, UGA 56.02 |

Ukraine also has **10 subregions** (`UA-05, UA-12, UA-26, UA-30, UA-32, UA-46, UA-51, UA-53,
UA-63, UA-71`) at `overall` level — a free Ukrainian panel that needs no map (§7.4). Two
subregion-specific rules, both verified:

- **`usage_per_capita_index` is published for only 51 of the 652 subregions** (US states) and for
  **none** of the Ukrainian oblasts — there is no per-subregion working-age denominator. Every
  other metric covers all 652 (`usage_pct` covers 649). Do not put it in the subregion core set;
  it is expected-absent, not a bug.
- **Subregion `usage_pct` is a share of the parent *country*, not of global usage.** It sums to
  ~100 per country (FR 100.51, US 100.42, DE 100.02). Ukraine's 10 published oblasts sum to
  **84.82** — the rest fell below publication thresholds. Label it "share of <Country>'s Claude
  usage" and state the published coverage. `UA-30` (Kyiv city) May = 29.79.

### 1.6 The occupation ↔ task bridge — the key finding

`node_external_id` at `category_name='onet', hierarchy_level='0'` is the **numeric O\*NET Task
ID**. That is the join to occupations. `IDEA.md` §8.2 is **wrong** to name
`onet_task_mappings.csv` — that file is only `task_name,pct` (and is byte-identical to
`release_2025_03_27/task_pct_v1.csv`, both 461,306 bytes).

**Both in-repo `onet_task_statements.csv` copies are O\*NET v20.1 / 2010-SOC and must not be used
for this join.** Anthropic's own `release_2025_09_15/code/preprocess_onet.py` pins v20.1. They
contain **zero** `15-12xx` codes, so Computer Programmers, Software Developers, Computer Systems
Analysts, Document Management Specialists, Accountants and Auditors and Librarians — i.e. the
entire demo script — resolve to **0 tasks**.

Measured comparison over the 2,823 task ids:

| Source | Task IDs matched | Occupations with ≥1 task | May `pct` attributable | `15-1251` |
|---|---|---|---|---|
| in-repo v20.1 | 1,765 (62.5%) | 483 / 718 | 49.8 of 94.3 | **0 tasks** |
| **O\*NET 30.0** | **2,823 (100.0%)** | **655 / 718** | **94.3 of 94.3** | **11 tasks** |

Use O\*NET 30.0: `https://www.onetcenter.org/dl_files/database/db_30_0_text/Task%20Statements.txt`
— tab-separated, 2,697 KB, columns `O*NET-SOC Code, Task ID, Task, Task Type,
Incumbents Responding, Date, Domain Source`; 18,797 rows, 923 SOC codes, Task ID unique.
Every task maps to exactly one SOC. Tasks per occupation: median 3, max 20.
`db_31_0_text` returns 404 as of 15.09.2026 — 30.0 is current.

Normalised-text map (needed for the older releases in §8): lowercase, collapse whitespace, strip a
trailing period → **17,139** unambiguous texts (398 texts map to >1 SOC and are dropped).

### 1.7 Cross-release task shares (input to §8)

Per-occupation shares **are** reconstructible across releases by mapping each release's task text
through the O\*NET 30.0 text map. Measured:

| Point | File | `facet`/`variable` or columns | Tasks | Text-matched | Matched `pct` | Occupations |
|---|---|---|---|---|---|---|
| Feb 2025 | `release_2025_03_27/task_pct_v1.csv` | `task_name,pct` | 3,514 | 80.1% | 74.3 | 654 |
| Mar 2025 | `release_2025_03_27/task_pct_v2.csv` | `task_name,pct` | 3,365 | 79.7% | 71.7 | 662 |
| Aug 2025 | `release_2025_09_15/data/output/aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv` | `facet='onet_task', level='0', variable='onet_task_pct'` | 2,618 | 79.1% | 68.0 | 602 |
| Nov 2025 | `release_2026_01_15/data/intermediate/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv` | same | 3,170 | 79.1% | 67.1 | 628 |
| Feb 2026 | `release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv` | same | 3,260 | 79.4% | 68.3 | 628 |
| Apr/May 2026 | `release_2026_06_26` | `category_name='onet', hierarchy_level='0', metric_id='pct'` | 2,713 (May) | 96.1% text / **100% by Task ID** | 90.8 text | 638 |

The three weekly files share the schema
`geo_id,geography,date_start,date_end,platform_and_product,facet,level,variable,cluster_name,value`
with `cluster_name` holding the task text; filter `geo_id='GLOBAL'`. `task_pct_v*.csv` values are
already percentages summing to 100.

### 1.8 World map

- Natural Earth **110m** is disqualified: it has no feature for **SGP, HKG, MLT, BHR, MUS**, and
  SGP is rank 2 on the usage index.
- Use **50m**:
  `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson`
  — 3,011 KB raw, 242 features, **all 121 dataset codes matched**. Public domain (CC0).
- ISO3 per feature: first non-`-99` of `ISO_A3_EH`, `ISO_A3`, `ADM0_A3`.
- Stripping properties to `{iso3, name}` and rounding coordinates to 2 dp yields **1,445 KB**
  (3 dp → 1,638 KB). Drop the `ATA` (Antarctica) feature.
- `data/release_2025_09_15/data/intermediate/iso_country_codes.csv`
  (`iso_alpha_2,iso_alpha_3,country_name`) is a local ISO3 → name crosswalk — no external
  country-name list is needed.

---

## 2. Stage A — repo hygiene ⟶ GATE 0

### 2.1 Fix the branch upstream *first*

`git branch -vv` currently reports `* v0.3 99cc0c2 [origin/v0.2]`. A bare `git push` from `v0.3`
would push onto `origin/v0.2`. Before anything else:

```bat
git rev-parse --abbrev-ref HEAD                   :: must print v0.3
git push -u origin v0.3                           :: creates origin/v0.3 and re-points upstream
git branch -vv                                    :: must now print [origin/v0.3]
```

### 2.2 Commit the pending working tree

The tree has ~750 deletions (all of v0.2's `site/`, plus `HANDOFF.md`, `probe.py`,
`probe_results.md`, `build_log.txt`) and a rewritten `IDEA.md`, plus untracked
`dashboard-style-prompt.md` and this `PLAN.md`. The v0.2 artefacts remain in history on `main`
and `v0.2`; this is a deliberate clean slate.

```bat
git add -A
git commit -m "v0.3: clear v0.2 site, adopt AI Time Machine spec"
git push
```

### 2.3 Make Pages deploy from `v0.3`

Edit `.github/workflows/pages.yml` — change `branches: [main]` to `branches: [main, v0.3]`.
Leave everything else (permissions, `concurrency`, `upload-pages-artifact` with `path: site`)
as is.

Then confirm the `github-pages` **environment** allows `v0.3`. If its deployment-branch policy is
restricted to the default branch, the build goes green and `actions/deploy-pages` still fails.

```bat
gh api repos/GeoChernykh/ai-usage-by-occupation/environments/github-pages
```

If `deployment_branch_policy` is not `null`, add `v0.3`:

```bat
gh api -X POST repos/GeoChernykh/ai-usage-by-occupation/environments/github-pages/deployment-branch-policies -f name=v0.3
```

If `gh` is unavailable or unauthenticated, tell the user to do it in
**Settings → Environments → github-pages → Deployment branches** and continue; do not block.

**GATE 0 acceptance:**
- `git branch -vv` shows `v0.3 ... [origin/v0.3]`.
- `git status --short` is clean.
- `origin/main` and `origin/v0.2` are unchanged (`git log --oneline -1 origin/main` still
  `6bf9451`; `origin/v0.2` still `99cc0c2`).
- `.venv\Scripts\python.exe -c "import sys,pandas;print(sys.executable)"` prints a path inside
  `.venv`.

**On failure:** if `git push -u origin v0.3` is rejected, do **not** force-push; report.

---

## 3. Stage A — crosswalks ⟶ GATE 1

`/data/` is gitignored, and the Pages runner never runs Python, so every input the build needs
must either live under `data/` (local only) or be **committed**. Downloads happen once, here, and
their outputs are committed so `build_data.py` reproduces offline.

Write **`fetch_lookups.py`** at the repo root. Idempotent: if the target exists and is non-empty,
skip the download and say so.

1. **O\*NET 30.0 Task Statements** → `lookups/onet30_task_statements.txt` (verbatim, ~2,697 KB).
   `urllib.request` with `User-Agent: Mozilla/5.0`, 60 s timeout.
2. **Natural Earth 50m countries** → download to `data/.cache/ne_50m.geojson` (gitignored), then
   emit the trimmed map to **`site/data/world.geojson`**:
   - keep only `properties = {"iso3": <first non "-99" of ISO_A3_EH|ISO_A3|ADM0_A3>,
     "name": <NAME>}`;
   - round every coordinate to 2 dp (recursive helper over the nested coordinate arrays);
   - drop the feature whose `iso3 == "ATA"`;
   - `json.dumps(..., separators=(",", ":"))`.
3. **`lookups/README.md`** recording, for each file: source URL, retrieval date, version and
   licence — O\*NET 30.0 Database, U.S. DOL/ETA, **CC BY 4.0**; Natural Earth, **public domain**.

**GATE 1 acceptance:**
- `lookups/onet30_task_statements.txt` parses with `pd.read_csv(..., sep="\t", dtype=str)` →
  18,797 rows, 923 distinct `O*NET-SOC Code`, 18,797 distinct `Task ID`.
- `15-1251.00` has 17 rows, `15-1252.00` 17, `15-1299.03` 23, `13-2011.00` 29.
- `site/data/world.geojson` parses, has **241** features (242 minus ATA), every feature has a
  non-empty `properties.iso3`, and the file is **≤ 1,600 KB**.
- All 121 country codes from §1.5's source slice are present in the geojson (compute the set
  difference; it must be empty).

**On failure:**
- onetcenter.org unreachable → retry once; then try `db_29_0_text` (verified reachable, same
  schema) and record the substitution in `BUILD_NOTES.md`. Do **not** fall back to the in-repo
  v20.1 file — §1.6 shows it destroys the demo.
- Natural Earth raw URL unreachable → try
  `https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_50m_admin_0_countries.geojson`.
  If both fail, ship Screens 1+2 and replace the map with the ranked country table (§7.3), noting
  it in `BUILD_NOTES.md`.

---

## 4. Stage B — `build_data.py` ⟶ GATE 2

Replace the existing `build_data.py` entirely. Runnable as
`.venv\Scripts\python.exe build_data.py`, idempotent, no arguments.

**Idempotence rule:** a rerun may delete and regenerate **`site/data/occ/` only** — so a shrinking
occupation set leaves no stale files behind. It must never clear `site/data/` itself:
`world.geojson` comes from `fetch_lookups.py` (§3) and `series.json` from `build_series.py` (§8),
and wiping either would silently break the map or the Compare tab.

### 4.1 Reading the big files

One chunked pass per source file. Never load one whole.

```python
COLS = ["date_start", "geo_id", "geo_level", "category_name",
        "hierarchy_level", "metric_id", "value", "node_name", "node_external_id"]

def scan(path, keep):                      # keep(chunk) -> boolean mask
    parts = []
    for chunk in pd.read_csv(path, usecols=COLS, dtype=str, chunksize=400_000):
        m = keep(chunk)
        if m.any():
            parts.append(chunk.loc[m])
    df = pd.concat(parts, ignore_index=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["value"])
```

`dtype=str` is deliberate: it keeps `hierarchy_level` comparable as `"0"` and avoids mixed-type
warnings. Collect **all** slices needed from a file in that single pass (global occupations,
global tasks, country `overall`, subregion `overall`) — do not re-read the file per slice.

Slices to keep:

| Name | Filter |
|---|---|
| `occ_global` | `geo_id=='GLOBAL' & category_name=='soc_occupation' & hierarchy_level=='0'` |
| `task_global` | `geo_id=='GLOBAL' & category_name=='onet' & hierarchy_level=='0'` |
| `major_global` | `geo_id=='GLOBAL' & category_name=='soc_occupation' & hierarchy_level=='1'` |
| `country_overall` | `geo_level=='country' & category_name=='overall'` (claude_ai only) |
| `subregion_overall` | `geo_level=='subregion' & category_name=='overall'` (claude_ai only) |

### 4.2 Shared helpers

- `norm_soc(x)` → strip, remove a trailing `.00` (keep `.01`, `.03`, …). `15-1252.00` → `15-1252`;
  `15-1299.03` stays.
- `norm_task(s)` → `re.sub(r"\s+", " ", s.strip().lower()).rstrip(".")`.
- `r(v, nd=4)` → `None` if NaN/inf else `round(float(v), nd)`. **Never** emit `NaN`, `Infinity`,
  or `"nan"` — `json.dump` writes bare `NaN` by default, so pass `allow_nan=False` and let it
  raise if a bad value slips through.
- `wide(df)` → `df.pivot_table(index=[...], columns="metric_id", values="value", aggfunc="first")`.
- Derived metrics, computed only when **both** inputs are present (otherwise omit the key):
  - `speedup = human_only_time_mean * 60 / human_with_ai_time_mean`
  - `time_saved_h = human_only_time_mean - human_with_ai_time_mean / 60`
  - `edu_gap = ai_education_years_mean - human_education_years_mean`
- **Weighted time saved** (IDEA §5's formula sums raw global shares and is dimensionally
  meaningless — use the normalised form):
  `weighted_time_saved = Σ_t(pct_t × time_saved_t) / Σ_t(pct_t)` over the occupation's mapped
  tasks that have both time metrics. Unit: hours per delegated task, usage-weighted.
  The **hero card never uses this** — it uses the published occupation-level
  `human_only_time_mean` / `human_with_ai_time_mean` directly.

### 4.3 The task → occupation join

```python
st = pd.read_csv("lookups/onet30_task_statements.txt", sep="\t", dtype=str)
st["soc"] = st["O*NET-SOC Code"].str.strip().map(norm_soc)
by_id = dict(zip(st["Task ID"].str.strip(), st["soc"]))
task_soc = task_global["node_external_id"].map(by_id)      # expect 100% hit
```

Assert the hit rate is ≥ 99%; log it. A task whose SOC is not in the 746-occupation universe is
kept in `tasks.json` but attached to no occupation.

### 4.4 Outputs

All under `site/data/`. Round every number to 4 decimals. Omit absent keys entirely.

**`index.json`**

```json
{
  "generated_at": "2026-09-15T12:00:00Z",
  "source_release": "release_2026_06_26",
  "release_label": "26.06.2026",
  "months": ["2026-04-01", "2026-05-01"],
  "sources": ["claude_ai", "1p_api"],
  "source_rows": {"claude_ai": 1636573, "1p_api": 491705},
  "counts": {"occupations": 746, "tasks": 2823, "countries": 121, "subregions": 652,
             "occupations_with_tasks": 655},
  "medians": {"claude_ai": {"2026-05-01": {"human_only_time_mean": 0.0, "...": 0.0}}},
  "major_groups": {"15": "Computer and Mathematical"},
  "occupations": [
    {"soc": "15-1251", "title": "Computer Programmers", "mg": "15",
     "pct": 1.67, "h_only": 9.12, "h_ai": 52.4, "speedup": 10.5,
     "autonomy": 0.0, "automation": 0.0, "coursework": 0.0,
     "hum_edu": 0.0, "ai_edu": 0.0, "n_tasks": 11, "src": ["claude_ai", "1p_api"]}
  ]
}
```

- `occupations`: the 746-code union, sorted by `pct` descending, values from
  `claude_ai` / `2026-05-01` (fall back to `1p_api` only for codes absent from `claude_ai`, and
  mark them via `src`). This array drives search, the Compare scatter and the country/occupation
  tables — keep it flat and short-keyed.
- `medians`: per source × month, the median across occupations of each of the 51 metrics, for the
  "vs all occupations" comparison bars.
- `major_groups`: SOC 2-digit → title, from `major_global`'s `node_name`.

**`occ/<soc>.json`** — one per occupation (`15-1299.03.json`, `15-1251.json`):

```json
{
  "soc": "15-1251", "title": "Computer Programmers", "mg": "15",
  "metrics": {
    "claude_ai": {"2026-04-01": {"pct": 1.62, "human_only_time_mean": 9.0},
                  "2026-05-01": {"pct": 1.67, "human_only_time_mean": 9.12}},
    "1p_api":    {"2026-05-01": {}}
  },
  "tasks": [
    {"id": "18924", "text": "Write, update, and maintain computer programs...",
     "m": {"2026-05-01": {"pct": 0.31, "human_only_time_mean": 6.2,
                          "human_with_ai_time_mean": 38.0, "ai_autonomy_mean": 3.1,
                          "collaboration_bucket_automation_pct": 61.0},
           "2026-04-01": {"pct": 0.29}}}
  ],
  "derived": {"claude_ai": {"2026-05-01": {"speedup": 10.5, "time_saved_h": 8.25,
                                           "edu_gap": 0.0, "weighted_time_saved": 0.0}}}
}
```

- `metrics` carries the **full 51-metric set** per source × month, keys verbatim as `metric_id`.
- `tasks` sorted by `time_saved_h` descending (May), ties broken by `pct` descending; task metric
  set = `pct, human_only_time_mean, human_with_ai_time_mean, ai_autonomy_mean,
  collaboration_bucket_automation_pct, use_case_coursework_pct`.
- A source with no data for the occupation gets `{}` for that month — the UI shows
  "not published", never zeros.

**`tasks.json`** — all 2,823 tasks for direct task search:
`[{"id", "text", "soc", "occ_title", "pct", "h_only", "h_ai", "speedup", "autonomy",
"automation"}]`, May values, sorted by `pct` desc. `soc`/`occ_title` omitted if unmapped.

**`countries.json`**

```json
{"metrics": ["usage_per_capita_index", "usage_pct", "..."],
 "countries": [{"iso3": "UKR", "name": "Ukraine",
                "m": {"2026-05-01": {"usage_per_capita_index": 0.78}, "2026-04-01": {}}}]}
```
All 52 `overall` metrics, both months. Names from
`data/release_2025_09_15/data/intermediate/iso_country_codes.csv`, keyed on `iso_alpha_3`; if a
code is missing there, fall back to the geojson `name`, then to the ISO3 itself.

**`subregions.json`** — same shape, 652 entries, but only the core metric set: `usage_pct`,
`use_case_{work,personal,coursework}_pct`, `collaboration_bucket_{automation,augmentation}_pct`,
`ai_autonomy_mean`, `human_only_time_mean`, `human_with_ai_time_mean` — plus `country` (the
alpha-2 prefix before the dash, mapped to ISO3 via `iso_country_codes.csv`). Keeps the file
~200 KB. **`usage_per_capita_index` is deliberately excluded** (§1.5: 51 of 652 subregions, none
Ukrainian). Emit, per country, `usage_pct_published_total` (e.g. `UA` → 84.82) so the UI can state
how much of that country's usage the published subregions cover.

### 4.5 Logging

Print and append to `build_log.txt`: source row counts, per-slice row counts, task-join hit rate,
occupation/task/country/subregion counts, files written, total bytes under `site/data/`, and
wall-clock seconds.

**GATE 2 acceptance** — write **`verify_data.py`** (stdlib only) that asserts all of this and
exits non-zero on any failure:

- Build completes in < 10 minutes, no exception, no pandas `FutureWarning` left unhandled.
- `index.json.occupations` has **746** entries; `counts.tasks` == 2,823; `counts.countries` == 121.
- One `occ/*.json` per entry; every file parses; no `NaN`/`Infinity`/`"nan"` anywhere (grep the
  raw bytes for `NaN` and `Infinity`).
- Fixture check — for each row of §1.4, `occ/<soc>.json` reproduces `pct`, `human_only_time_mean`
  and `human_with_ai_time_mean` to ±0.01, and `derived.speedup` to ±0.1.
- `15-1251` has **11** tasks, `15-1252` 9, `15-1299.03` 12, `15-1211` 16, `13-2011` 13,
  `25-4022` 8, `27-3041` 10, `23-1011` 7, `25-1021` 4.
- **≥ 655** occupation files have ≥ 1 task (655 was measured over the 718 `claude_ai` codes; the
  emitted universe is the 746-code union, so a few of the 28 `1p_api`-only codes may add to it).
  `sum(len(tasks))` ≥ 2,500.
- Σ `pct` over `index.json.occupations` (May, claude_ai) is 98.51 ± 0.05.
- `countries.json`: `UKR` May `usage_per_capita_index` == 0.78, `usage_pct` == 0.47,
  `use_case_coursework_pct` == 18.77, `use_case_work_pct` == 40.61,
  `collaboration_bucket_automation_pct` == 48.90; `AUS` index 6.40, `USA` usage 20.16.
- `subregions.json` contains all 652 codes including the 10 `UA-*`; `UA-30` May `usage_pct` ==
  29.79; the `UA` published total == 84.82 ± 0.05; no entry carries `usage_per_capita_index`.
- Total `site/data/` **< 12 MB** (expect ~6–8 MB including `world.geojson`).

**On failure:** memory pressure → drop `chunksize` to 150,000 and confirm `usecols` is passed.
Do not reduce the metric set. Empty slice → `hierarchy_level` is being compared as an int.

---

## 5. Stage B — app shell

```
site/
  index.html
  style.css
  app.js                 entry: state, routing, rail, header
  lib/  data.js  format.js  search.js  charts.js  csv.js
  screens/  time.js  compare.js  geo.js
  vendor/  echarts.min.js          (5.6.0 UMD, committed)
  data/   index.json  occ/*.json  tasks.json  countries.json  subregions.json
          series.json  world.geojson
```

- `index.html`: `<script src="vendor/echarts.min.js"></script>` then
  `<script type="module" src="app.js"></script>`.
- **State** (single object, the only source of truth):
  `{screen, soc, source, month, geo, mapMetric, compareA, compareB}`.
  Defaults: `screen='time'`, `soc='15-1251'`, `source='claude_ai'`, `month='2026-05-01'`,
  `geo='UKR'`, `mapMetric='usage_per_capita_index'`.
- **Loading**: `index.json` once at boot; `occ/<soc>.json` on selection (cache in a `Map`);
  `tasks.json`, `countries.json`, `subregions.json`, `series.json`, `world.geojson` lazily on
  first use of the screen that needs them. Changing `source` or `month` **must not** trigger a
  fetch — re-render from memory.
- **Compare tab is feature-detected, not flagged.** At boot, `fetch('data/series.json')`; render
  the Compare rail button only on a 200 that parses. No `has_series` field anywhere — Stage B
  cannot know whether Stage D will run, so a flag would be wrong exactly when it matters. A 404
  here is an expected state, not an error: catch it and log nothing louder than a `console.info`.
- **Frame** (`dashboard-style-prompt.md`): `#EDEDEE` page → `#E4E5E7` slab, radius 40, generous
  margin; left icon rail of white 72px radius-20 buttons straddling the slab edge, 16px apart,
  active button filled `#A9BCCB` with a white icon; page title ~64px/700 top-left; segmented pill
  control top-right, selected pill `#A9BCCB`.
- The segmented control is the **month** switch, built from `index.json.months` (never hardcoded).
  The source toggle is a second, smaller segmented control beneath it, labelled
  "Consumer (Claude apps)" / "Enterprise API"; it is **hidden on Screen 3**.
- **Cards**: white, radius 8, `0 1px 3px rgba(0,0,0,0.08)`, no border, 20px padding, one elevation.
- **Charts** (`lib/charts.js` exports a `baseOption()` every chart spreads):
  no chart border, no plot-area fill, no axis lines, no vertical gridlines, at most one dotted
  horizontal gridline at a round value, 4–5 sparse x labels, no data labels, default tooltip,
  legend only for multi-series (row of small filled circles, top-left inside the card).
  Categorical series descend the ladder `#3B6E93 → #A9C0D2 → #93DCF2 → #E0E0E0`.
  `#2F88F7` appears **at most once per screen**. Text `#2B2B2B`; ticks/small labels `#6B6B6B`.
  Every chart gets a `ResizeObserver` → `chart.resize()`.
- `prefers-reduced-motion` respected (`animation: false` on every ECharts option when it matches);
  visible keyboard focus on rail buttons, pills, search and table rows.
- Responsive: below ~1100px the multi-column rows stack, KPI cards go two-up, and the rail
  collapses to a top bar. No horizontal page scroll at 400px; tables scroll inside their card.

---

## 6. Stage B — Screen 1 "Time card"

Title: **AI Time Machine**. This screen must work end to end before anything else starts.

1. **Search** — text input over `index.json.occupations` (746) plus, once `tasks.json` is loaded,
   the 2,823 tasks; results grouped "Occupations" / "Tasks", max 8 each, case-insensitive
   substring + token-prefix, ranked by `pct` descending. Keyboard: ↑/↓/Enter/Esc. Selecting a task
   navigates to its occupation and scrolls to that row in the task table.
2. **KPI row** (4 squat cards, row 1): usage share (`pct` %), autonomy (`ai_autonomy_mean`, "x.x
   / 5"), automation share (`collaboration_bucket_automation_pct` %), coursework share
   (`use_case_coursework_pct` %). Value ~56px/600 centred, label ~20px/400 above.
   Under the number, neutral grey caption with the other month's value — e.g. "Apr 2026: 1.62%".
   **No arrows, no colour, no icons.** Where `series.json` has ≥ 3 points (usage share only),
   draw the contract's bare sparkline in the bottom third; otherwise leave that area empty.
3. **Hero — time compression** (row 2, full width): one paired horizontal bar on a single shared
   axis in minutes — unaided (`human_only_time_mean × 60`, `#3B6E93`) above assisted
   (`human_with_ai_time_mean`, `#A9C0D2`) — with the speed-up factor set large to the right
   ("10.5×", ~56px/600). Sentence beneath: "Work Claude is asked to do for this occupation takes
   **9.1 hours** unaided and **52 minutes** with Claude." A third, inert `#E0E0E0` bar shows the
   all-occupation median from `index.json.medians` for the same month and source.
4. **Ranked task table** (row 3, full width): the occupation's tasks, sorted by time saved
   descending. Columns: task text (truncated with ellipsis, full text in `title`), unaided,
   with AI, saved, speed-up, share of usage, and an inline horizontal bar for "saved" coloured by
   rank down the ladder. Bar height ~24px. Scrolls inside the card past ~12 rows with a thin grey
   rail. Header caption: "O\*NET tasks behind this occupation that appear in Claude usage —
   **N of M** published; the rest did not meet publication thresholds."
   Occupations with zero mapped tasks (~90 of 746 — `build_data.py` logs the exact count and puts
   it in `index.json.counts.occupations_with_tasks`) show that empty state, not a broken table.
5. **Automation vs augmentation** + **artifact mix** (row 4, 1 : 1): a 100% stacked horizontal bar
   from the two `collaboration_bucket_*_pct`; and the top 8 `artifact_*_pct` as horizontal bars
   with humanised labels (`artifact_code_fix_or_debug_pct` → "Code fix or debug"), titled
   "What Claude actually produces for this job".
6. **Methodology popover** on every KPI and card title: a small `?` button opening a plain white
   popover quoting the exact `metric_id`, its unit, the source file and the release date. Include
   the model-estimate caveat on the two time metrics.

**Acceptance:** with `python -m http.server` from `site/`, `?occ=15-1251` loads Computer
Programmers showing 9.1 h → 52 min, 10.5×, 11 tasks; `?occ=15-1299.03` shows 2.05 h → 13.3 min
and 12 tasks; `?occ=25-1021` shows 5.2 h → 48 min and a coursework KPI; switching month and source
re-renders with **zero** network requests (check the devtools Network tab); an occupation with no
`1p_api` data shows "not published" chips, not zeros; no console errors.

---

## 7. Stage C — Screen 3 "Geography"

The source toggle is hidden here (`1p_api` is global-only, §1.2).

1. **World choropleth**:
   ```js
   echarts.registerMap("world", worldGeoJson, {});           // fetched lazily
   // series: { type: "map", map: "world", nameProperty: "iso3", ... }
   ```
   `nameProperty: "iso3"` is what makes `data: [{name: "UKR", value: 0.78}]` bind. Do not build a
   country-name crosswalk for this.
   - `visualMap.type: "piecewise"` with boundaries **0, 0.5, 1.0, 2.0, 4.0, max** so that 1.0
     ("usage proportional to working-age population") is a bucket edge, coloured up the ladder
     `#E0E0E0 → #93DCF2 → #A9C0D2 → #3B6E93` with the top bucket darkest. The palette rule forbids
     a second hue, so the "diverging" reading comes from the 1.0 edge and the legend label
     "1.0 = proportional", not from a red/blue ramp.
   - Countries absent from the data render `#E0E0E0` with `itemStyle.areaColor` and a tooltip
     reading "not published", never 0.
   - Ukraine selected by default: highlighted with `#2F88F7` (the screen's one highlight use) and
     its value called out beside the map.
   - `roam: false`, `emphasis.label.show: false`, borders `#FFFFFF` at 0.5px.
2. **Metric switch**: `usage_per_capita_index` · `usage_pct` ·
   `collaboration_bucket_automation_pct` · `use_case_coursework_pct`. Same segmented-pill styling,
   placed above the map.
3. **Ranked country table**: rank, country, selected metric, plus usage share; the selected
   country row pinned visible and highlighted. Clicking a row selects that country.
4. **Ukraine / selected-country detail** (row 3, 1 : 1):
   - stacked horizontal bar of `use_case_{work,personal,coursework}_pct` with the artifact mix
     (top 8) underneath;
   - **subregion table** from `subregions.json` filtered to the selected country — for `UKR` that
     is 10 oblasts, `UA-30` (Kyiv city) leading at 29.79. No subregion map, and **no per-capita
     index column** (§1.5). The usage column is headed "share of Ukraine's Claude usage" — never
     "share of Claude usage" — with a caption reading "10 published subregions covering 84.8% of
     the country's usage; the rest did not meet publication thresholds", both values read from
     the data, not hardcoded. Hidden when the selected country has no subregions published.

**Acceptance:** the map renders 241 countries with no missing-geometry warnings in the console;
SGP, HKG, MLT, BHR and MUS are all coloured; Ukraine reads 0.78 and rank 68 of 121; switching the
metric to `use_case_coursework_pct` puts TUN (51.52) at the top; the subregion table shows the 10
`UA-*` rows; no horizontal scroll at 400px.

---

## 8. Stage D — `series.json` + Screen 2 "Compare"

Optional by deadline. If `site/data/series.json` is absent, the boot-time probe in §5 simply does
not render the Compare rail button — nothing else changes.

### 8.1 Building the series

Add a second entry point **`build_series.py`** (separate file, so a failure here cannot break
Stage B's outputs). It emits `site/data/series.json`.

For each of the 7 points in §1.7: read that release's task-level shares, map task text through the
O\*NET 30.0 **normalised-text** map (17,139 unambiguous entries), sum `pct` per SOC, then
**renormalise within the matched subset**:

```
share_r(occ) = 100 * Σ_t pct_t(occ) / Σ_t pct_t(all matched tasks in that release)
```

Renormalisation is mandatory: matched coverage ranges from 67.1 to 90.8 percentage points across
releases, so raw shares are not comparable.

**Method-consistency check (required).** Release 6 can be joined two ways — by Task ID (100%) and
by text (96.1%). Compute **both**, and report in `BUILD_NOTES.md` the median absolute difference
in `share_r` across the top 50 occupations and the largest top-10 rank change. If the median
difference exceeds 0.5 pp **or** any top-10 occupation moves more than 3 ranks, use the
**text join for every point in the series** (method consistency beats per-point accuracy for a
time series) and say so on the panel. Screen 1's task table keeps the Task ID join regardless.

Also verify, per weekly file, that `pct` sums to ~100 after filtering `geo_id='GLOBAL'` — these
files carry a `platform_and_product` column and a bad filter would double-count.

```json
{
  "points": [
    {"key": "2025-02", "label": "Feb 2025", "release": "release_2025_02_10",
     "window": "task_pct_v1", "matched_pct": 74.3, "n_tasks": 3514}
  ],
  "method": "text",
  "occupations": {"15-1251": [2.11, 1.98, null, 1.42, 1.51, 1.66, 1.71]},
  "global": {"automation_pct": [], "use_case_work_pct": []}
}
```

`null` = not published / no matched task at that point. Arrays are index-aligned to `points`.

### 8.2 Screen 2 panels

1. **Education scatter** (full width): x = `human_education_years_mean`,
   y = `ai_education_years_mean`, one point per occupation (May, claude_ai), `symbolSize` scaled
   by `sqrt(pct)` (clamped 4–40 px), parity diagonal drawn with `markLine` in `#E0E0E0` labelled
   "parity". Points above the line are occupations where Claude operates above the human entry
   bar. Base points `#A9C0D2` at 0.6 opacity; the selected occupation `#2F88F7`.
2. **Two-occupation comparison**: pickers A and B (A defaults to the current `soc`), grouped
   horizontal bars on identical axes for `pct`, `human_only_time_mean`,
   `human_with_ai_time_mean`, `speedup`, `ai_autonomy_mean`,
   `collaboration_bucket_automation_pct`, `use_case_coursework_pct`. A = `#3B6E93`,
   B = `#A9C0D2`.
3. **Release slope chart**: `share_r` for the selected occupation across the 7 points, x axis
   **categorical** (never a date scale — the points are not evenly spaced), 4–5 sparse labels.
   Permanent on-panel caveat, verbatim — the last sentence is filled from `series.json.method`
   (`"id"` → "the current release joins tasks to occupations by O\*NET Task ID; earlier releases,
   which publish no task ids, by task text"; `"text"` → "every release joins tasks to occupations
   by task text, so all points use one method"):
   > Each release re-clusters usage into its own O\*NET task set (2,618–3,514 tasks) and is
   > published as a discrete snapshot, not a continuous series. Shares are renormalised over the
   > tasks that map to an occupation in that release (67–91% of usage). Read the direction, not
   > the precise level. <method sentence>.

**Acceptance:** the scatter renders ~717 points with the parity line; picking two occupations
redraws both series; the slope chart shows 7 categorical points for `15-1251` with the caveat
visible; removing `site/data/series.json` hides the tab and leaves Screens 1 and 3 working.

---

## 9. Stage E — cross-cutting

1. **URL state** via `history.replaceState`, read on load and written on every state change:
   `?screen=geo&occ=15-1251&src=claude_ai&month=2026-05-01&geo=UKR&metric=usage_per_capita_index`.
   Unknown or invalid values fall back to defaults without throwing. Also accept the bare
   `?occ=` / `?soc=` form for compatibility with links already circulated from v0.2.
2. **CSV export** — a button per screen producing the slice currently on screen via a client-side
   `Blob` (no library): Screen 1 → one row per source × month × metric plus one row per task;
   Screen 2 → the compared occupations; Screen 3 → the country table. Header row always present;
   filename `ai-time-machine_<screen>_<key>_<month>.csv`.
3. **"Not published" chip** — `#E0E0E0` background, `#6B6B6B` text, the literal words
   "not published". Every renderer routes through one helper so no `undefined`, `null`, `NaN` or
   silent 0 can reach the DOM.
4. **Persistent footer**, verbatim:
   > Measures Claude usage among Claude users, mapped onto US O\*NET/SOC classifications — not AI
   > exposure of an occupation in general. Shares are shares **of Claude usage**, never of the
   > economy. The Enterprise API source excludes Claude Code, which understates developer
   > occupations, and is published globally only. Cells that did not meet Anthropic's publication
   > thresholds are shown as "not published", not as zero. Time figures are model estimates, not
   > stopwatch measurements. Releases are discrete published snapshots, not a continuous time
   > series.
   > Sources: Anthropic Economic Index, release 2026-06-26 (CC BY); O\*NET 30.0 Database, U.S.
   > Department of Labor / ETA (CC BY 4.0); country outlines from Natural Earth (public domain).
5. **README.md** at the repo root: what the product is, the live URL, how to regenerate
   (`fetch_lookups.py` → `build_data.py` → `build_series.py` → `verify_data.py`, each with the
   `.venv` interpreter path), and the §4.3 limits.

---

## 10. Stage E — deploy ⟶ GATE 3

1. Confirm `.gitignore` still anchors `/data/` with a leading slash — an unanchored `data/` would
   also swallow `site/data/` and every JSON would 404 in production.
2. Commit and push to `v0.3` (never to `main`). `site/data/**`, `site/vendor/echarts.min.js`,
   `lookups/**`, `build_data.py`, `build_series.py`, `fetch_lookups.py`, `verify_data.py`,
   `requirements.txt`, `PLAN.md`, `IDEA.md`, `README.md`, `BUILD_NOTES.md`, `build_log.txt`.
3. Watch the run: `gh run list --branch v0.3 --limit 3`, then `gh run watch <id>`.
4. Verify the deployed site over HTTP — not just locally:

```bat
curl -s -o NUL -w "%%{http_code} " https://geochernykh.github.io/ai-usage-by-occupation/
curl -s -o NUL -w "%%{http_code} " https://geochernykh.github.io/ai-usage-by-occupation/data/index.json
curl -s -o NUL -w "%%{http_code} " https://geochernykh.github.io/ai-usage-by-occupation/data/occ/15-1251.json
curl -s -o NUL -w "%%{http_code} " https://geochernykh.github.io/ai-usage-by-occupation/data/world.geojson
curl -s -o NUL -w "%%{http_code} " https://geochernykh.github.io/ai-usage-by-occupation/vendor/echarts.min.js
```

**GATE 3 acceptance:** all five return `200`; the page renders in a fresh browser profile; a deep
link (`?occ=15-1251`) resolves; the Geography screen draws the map; `origin/main` and `origin/v0.2`
are still at `6bf9451` / `99cc0c2`.

**On failure:** 404 on JSON → `site/data/` was not committed (check the ignore anchor). Deploy step
fails after a green build → the `github-pages` environment branch policy (§2.3). Blank page with a
module error → a fetch used a leading `/`.

---

## 11. Stage E — handoff

Write **`HANDOFF.md`**: live URL; the row/slice counts and join rates from `build_log.txt`; output
payload size and file counts; which panels shipped and which were dropped, with the reason; the
`series.json` method decision from §8.1 and its measured deltas; the exact regeneration commands
including the `.venv` interpreter path and `requirements.txt` contents; and the demo-script
timings from `IDEA.md` §9 checked against the built page (each claimed number confirmed on screen).

Record in `BUILD_NOTES.md`, as you go: every deviation from this plan, every gate result, and any
identifier that turned out to differ from §1.

---

## Out of scope — do not build

- Any backend, server, API, database or npm toolchain.
- Dark mode / theme toggle (§0.4).
- A subregion choropleth — admin-1 geometry for 652 units is out of budget; the subregion table
  (§7.4) replaces it.
- Task → DWA/IWA/GWA attribution per occupation: the release gives no Task→DWA edge and the
  in-repo O\*NET files do not supply one. The DWA/IWA/GWA *levels themselves* may be shown as
  standalone global breakdowns if time allows, never as a per-occupation rollup.
- Request/topic trends across releases: each release re-clusters requests with a
  non-overlapping label taxonomy, so a "top topics over time" chart would compare incompatible
  categories under a false appearance of continuity.
- `bls_employment_may_2023.csv` (22 rows, major groups only) and wage/exposure joins from v0.2 —
  the v0.3 product is about time, not salary.
- Confidence intervals: the `*_ci_lower` / `*_ci_upper` variables exist only in the weekly raw
  files, not in release 6's published metric set.

## Escalate to the human — stop and report

- GATE 0 fails, or any push would land on `main` / `v0.2`.
- Both O\*NET download fallbacks fail (§3).
- A §1.4 or §1.5 fixture does not reproduce — that means the local corpus differs from the one
  this plan was verified against, and every downstream number is suspect.
- `site/data/` would exceed 12 MB.
- GitHub credentials or the `github-pages` environment policy cannot be changed.
