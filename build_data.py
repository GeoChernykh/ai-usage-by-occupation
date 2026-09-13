"""Build static JSON slice for the occupation explorer. Idempotent, run as:
    .venv\\Scripts\\python.exe build_data.py

Source schema notes (see probe_results.md for the full probe):
- All source CSVs are comma-delimited, not semicolon.
- The per-node usage share inside the soc_occupation/hierarchy_level=0/geo_id=GLOBAL
  slice is carried under metric_id "pct" (there is no "usage_pct" in that slice --
  usage_pct only exists at category_name="overall"). We surface it in our own
  output under the app-level key "usage_pct" everywhere except the raw per-occupation
  metrics blob, where the real metric_id "pct" is kept verbatim (Rule 2: never
  invent a metric_id).
- wage_data.csv: JobZone==-1 and ChanceAuto==-1 are "missing" sentinels, not real
  values -- omit those keys rather than emit -1. isBright (True/False) is the
  actual Bright-Outlook flag; JobForecast is a projected-employment count, not a
  label, so "forecast" is derived from isBright instead.
- major_group_trend: no release other than 2026_06_26 has usage data at the detailed
  occupation level (see probe_results.md), so a real quarter/year comparison isn't
  buildable. The one extra real data point is release_2025_09_15's enriched Aug-2025
  file, which has usage share at SOC-*major-group* granularity only (23 groups,
  facet=soc_occupation level=0, variable=soc_pct). We roll the two detailed months up
  to the same major-group granularity (median of "pct" across occupations sharing a
  JobFamily) so all three points are on the same footing, and expose it as its own
  index.json block, never blended into per-occupation metrics.
- global_trends: none of the six releases has multi-point occupation-level data, but
  three families of GLOBAL (non-occupation) metrics genuinely are comparable across
  releases (verified numerically, not assumed from column names -- see
  probe_results.md "v0.2: global_trends"):
  1. automation_pct/augmentation_pct: documented formula in this release's own
     data_documentation.md is automation% = (directive+feedback_loop)/(100-none)*100,
     augmentation% = (task_iteration+learning+validation)/(100-none)*100. Verified
     exact against this release's own precomputed collaboration_bucket_*_pct. Applied
     to the two 2025 report CSVs and the two 2026 raw weekly snapshots, which only
     ship the six raw components. release_2025_02_10's V1 snapshot sums to only
     84.2% (not ~100% like every later snapshot) for an undocumented reason -- kept
     UNNORMALIZED with an explicit "unnormalized" flag rather than dividing by a
     denominator we can't verify.
  2. top_onet_tasks: onet_task node/cluster text is verbatim O*NET task-statement
     text, confirmed byte-identical for the same task across every release checked.
     Matched case-insensitively (2026_06_26 title-cases the text, earlier releases
     don't) across all 6 real time points for the top tasks by May-2026 share.
  3. usage_patterns: use_case_{work,personal,coursework}_pct, ai_autonomy_mean,
     human_only_time_mean, human_with_ai_time_mean, human_only_ability_pct,
     multitasking_pct exist at GLOBAL/level-0 in the two 2026 raw weekly files under
     the same variable names as this release's metric_ids (3 points: Nov 2025,
     Feb 2026, Apr/May 2026). task_success_pct exists in the weekly files but nowhere
     in this release, so it only gets 2 points (Nov 2025, Feb 2026).
  Explicitly NOT built: request/topic-level trends -- verified each release reruns
  its own clustering with a fresh, non-overlapping label taxonomy (different wording
  per release, short phrases only in this release), so a "topic over time" chart
  would compare incompatible categories under a false appearance of continuity.
"""
import json
import math
from pathlib import Path

import pandas as pd

RELEASE_DIR = "data/release_2026_06_26/data"
FILES = {
    "claude_ai": f"{RELEASE_DIR}/aei_claude_ai_2026-06-26.csv",
    "1p_api": f"{RELEASE_DIR}/aei_1p_api_2026-06-26.csv",
}
JOB_EXPOSURE_PATH = "data/labor_market_impacts/job_exposure.csv"
WAGE_DATA_PATH = "data/release_2025_02_10/wage_data.csv"
MAJOR_GROUP_TREND_PATH = ("data/release_2025_09_15/data/output/"
                           "aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv")
MAJOR_GROUP_TREND_DATE = "2025-08-01"
# release_2025_09_15 spells this SOC major group differently from wage_data.JobFamily.
JOB_FAMILY_ALIASES = {"Educational Instruction and Library": "Education, Training, and Library"}

V1_AUTOMATION_PATH = "data/release_2025_02_10/automation_vs_augmentation.csv"
V1_DATE = "2025-02-10"
V2_AUTOMATION_PATH = "data/release_2025_03_27/automation_vs_augmentation_v2.csv"
V2_DATE = "2025-03-27"
V1_TASK_PATH = "data/release_2025_02_10/onet_task_mappings.csv"
V2_TASK_PATH = "data/release_2025_03_27/task_pct_v2.csv"
AUG_2025_ENRICHED_PATH = MAJOR_GROUP_TREND_PATH  # same file as major_group_trend
AUG_2025_DATE = "2025-08-04"
NOV_2025_PATH = "data/release_2026_01_15/data/intermediate/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv"
NOV_2025_DATE = "2025-11-13"
FEB_2026_PATH = "data/release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv"
FEB_2026_DATE = "2026-02-05"

POINT_LABELS = {
    V1_DATE: "Feb 2025 (V1 report)",
    V2_DATE: "Mar 2025 (V2 report)",
    AUG_2025_DATE: "Aug 2025 (V3 report)",
    NOV_2025_DATE: "Nov 2025",
    FEB_2026_DATE: "Feb 2026",
    "2026-04-01": "Apr 2026",
    "2026-05-01": "May 2026",
}

TOP_TASK_COUNT = 6
NOT_A_TASK = {"none", "not_classified"}


def norm_task(text):
    return text.strip().lower()

COLS = ["node_name", "node_external_id", "metric_id", "date_start", "value",
        "category_name", "hierarchy_level", "geo_id"]
KEEP = ["node_name", "node_external_id", "metric_id", "date_start", "value"]

CHUNKSIZE = 500_000
USAGE_METRIC_ID = "pct"
NEIGHBOUR_SOURCE = "claude_ai"
NEIGHBOUR_MONTH = "2026-05-01"

OUT_DIR = Path("site/data")
OCC_DIR = OUT_DIR / "occ"


def norm_soc(code):
    c = str(code).strip()
    return c[:-3] if c.endswith(".00") else c


def extract(path):
    parts = []
    for chunk in pd.read_csv(path, usecols=COLS, dtype=str, chunksize=CHUNKSIZE):
        mask = ((chunk["category_name"] == "soc_occupation")
                & (chunk["hierarchy_level"] == "0")
                & (chunk["geo_id"] == "GLOBAL"))
        parts.append(chunk.loc[mask, KEEP])
    parts = [p for p in parts if not p.empty]
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=KEEP)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["soc"] = df["node_external_id"].map(norm_soc)
    return df


def extract_category(path, category_name, hierarchy_level=None, metric_id=None):
    """GLOBAL-only rows for one category_name from the main release, chunked."""
    parts = []
    for chunk in pd.read_csv(path, usecols=COLS, dtype=str, chunksize=CHUNKSIZE):
        mask = (chunk["category_name"] == category_name) & (chunk["geo_id"] == "GLOBAL")
        if hierarchy_level is not None:
            mask &= chunk["hierarchy_level"] == hierarchy_level
        if metric_id is not None:
            mask &= chunk["metric_id"] == metric_id
        parts.append(chunk.loc[mask, KEEP])
    parts = [p for p in parts if not p.empty]
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=KEEP)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["value"])


def load_job_exposure():
    df = pd.read_csv(JOB_EXPOSURE_PATH, dtype=str)
    df["soc"] = df["occ_code"].map(norm_soc)
    df["observed_exposure"] = pd.to_numeric(df["observed_exposure"], errors="coerce")
    return df.set_index("soc")


def load_wage_data():
    df = pd.read_csv(WAGE_DATA_PATH, dtype=str)
    df["soc"] = df["SOCcode"].map(norm_soc)
    for col in ["MedianSalary", "JobZone", "ChanceAuto"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Prefer exact .00 base-code rows when duplicates exist after normalisation.
    df["is_base"] = df["SOCcode"].str.strip().str.endswith(".00")
    df = df.sort_values("is_base", ascending=False).drop_duplicates("soc", keep="first")
    return df.set_index("soc")


def load_major_group_trend():
    """soc_pct per SOC major group (wage_data.JobFamily spelling) for Aug 2025, GLOBAL."""
    df = pd.read_csv(MAJOR_GROUP_TREND_PATH, dtype=str)
    mask = ((df["facet"] == "soc_occupation") & (df["level"] == "0")
             & (df["geo_id"] == "GLOBAL") & (df["variable"] == "soc_pct"))
    sl = df.loc[mask, ["cluster_name", "value"]].copy()
    sl["value"] = pd.to_numeric(sl["value"], errors="coerce")
    sl["job_family"] = sl["cluster_name"].map(lambda c: JOB_FAMILY_ALIASES.get(c, c))
    return {row.job_family: clean(row.value) for row in sl.itertuples()
            if row.job_family != "not_classified"}


def clean(v):
    """None if missing/NaN/inf, else a plain float/str safe for json.dump(allow_nan=False)."""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, str):
        return v
    return float(v)


def wage_block(row):
    if row is None:
        return None
    block = {}
    salary = clean(row["MedianSalary"])
    if salary is not None:
        block["median_salary"] = salary
    if isinstance(row["JobFamily"], str) and row["JobFamily"]:
        block["job_family"] = row["JobFamily"]
    zone = clean(row["JobZone"])
    if zone is not None and zone != -1:
        block["job_zone"] = zone
    chance = clean(row["ChanceAuto"])
    if chance is not None and chance != -1:
        block["chance_auto"] = chance
    block["forecast"] = "Bright" if row["isBright"] == "True" else "Not bright"
    return block


def automation_from_components(directive, feedback_loop, task_iteration, learning,
                                validation, none, normalize=True):
    automation_raw = directive + feedback_loop
    augmentation_raw = task_iteration + learning + validation
    if not normalize:
        return automation_raw, augmentation_raw
    classifiable = 100.0 - none
    return automation_raw / classifiable * 100.0, augmentation_raw / classifiable * 100.0


def read_v1_v2_automation(path):
    df = pd.read_csv(path, dtype=str)
    df["pct"] = pd.to_numeric(df["pct"], errors="coerce")
    vals = df.set_index("interaction_type")["pct"]
    return {k: float(vals.get(k, 0.0)) for k in
            ("directive", "feedback loop", "task iteration", "learning", "validation", "none")}


WEEKLY_COLS = ["facet", "level", "geo_id", "variable", "cluster_name", "value"]
WEEKLY_FACETS_NEEDED = {"collaboration", "collaboration_automation_augmentation", "onet_task",
                         "use_case", "ai_autonomy", "human_only_time", "human_with_ai_time",
                         "human_only_ability", "multitasking", "task_success"}


def load_weekly_slice(path):
    """One chunked pass over a ~100MB weekly aei_raw_*.csv, keeping only the GLOBAL rows
    for the facets this build needs -- every other read below operates on this in-memory
    slice instead of re-reading the file from disk."""
    parts = []
    for chunk in pd.read_csv(path, usecols=WEEKLY_COLS, dtype=str, chunksize=CHUNKSIZE):
        mask = (chunk["geo_id"] == "GLOBAL") & (chunk["facet"].isin(WEEKLY_FACETS_NEEDED))
        parts.append(chunk.loc[mask])
    parts = [p for p in parts if not p.empty]
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=WEEKLY_COLS)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def read_weekly_collaboration(slice_df):
    """Raw collaboration_pct components at GLOBAL/level 0."""
    sl = slice_df[(slice_df["facet"] == "collaboration") & (slice_df["level"] == "0")
                  & (slice_df["variable"] == "collaboration_pct")]
    vals = sl.set_index("cluster_name")["value"]
    return {
        "directive": float(vals.get("directive", 0.0)),
        "feedback loop": float(vals.get("feedback_loop", 0.0)),
        "task iteration": float(vals.get("task_iteration", 0.0)),
        "learning": float(vals.get("learning", 0.0)),
        "validation": float(vals.get("validation", 0.0)),
        "none": float(vals.get("none", 0.0)),
    }


def read_weekly_global_metric(slice_df, facet, variable, cluster_name=None):
    mask = (slice_df["facet"] == facet) & (slice_df["level"] == "0") & (slice_df["variable"] == variable)
    if cluster_name is not None:
        mask &= slice_df["cluster_name"] == cluster_name
    sl = slice_df.loc[mask, "value"]
    if sl.empty:
        return None
    return clean(sl.iloc[0])


def read_weekly_onet_tasks(slice_df):
    """{normalized task text: pct} at GLOBAL/level 0."""
    sl = slice_df[(slice_df["facet"] == "onet_task") & (slice_df["level"] == "0")
                  & (slice_df["variable"] == "onet_task_pct")]
    out = {}
    for cluster_name, value in zip(sl["cluster_name"], sl["value"]):
        if cluster_name in NOT_A_TASK:
            continue
        v = clean(value)
        if v is not None:
            out[norm_task(cluster_name)] = v
    return out


def read_report_csv_tasks(path):
    df = pd.read_csv(path, dtype=str)
    df["pct"] = pd.to_numeric(df["pct"], errors="coerce")
    return {norm_task(t): float(p) for t, p in zip(df["task_name"], df["pct"]) if pd.notna(p)}


def overall_metric(overall_df, date_start, metric_id):
    row = overall_df[(overall_df["date_start"] == date_start) & (overall_df["metric_id"] == metric_id)]
    if row.empty:
        return None
    return clean(row["value"].iloc[0])


def build_global_trends(overall_df, onet_task_df):
    aug2025_slice = load_weekly_slice(AUG_2025_ENRICHED_PATH)
    nov2025_slice = load_weekly_slice(NOV_2025_PATH)
    feb2026_slice = load_weekly_slice(FEB_2026_PATH)

    # 1. automation vs augmentation, 7 points.
    v1 = read_v1_v2_automation(V1_AUTOMATION_PATH)
    v1_auto, v1_aug = automation_from_components(v1["directive"], v1["feedback loop"], v1["task iteration"],
                                                  v1["learning"], v1["validation"], v1["none"], normalize=False)
    v2 = read_v1_v2_automation(V2_AUTOMATION_PATH)
    v2_auto, v2_aug = automation_from_components(v2["directive"], v2["feedback loop"], v2["task iteration"],
                                                  v2["learning"], v2["validation"], v2["none"])
    aug2025_auto = read_weekly_global_metric(aug2025_slice, "collaboration_automation_augmentation",
                                              "automation_pct", "automation")
    aug2025_aug = read_weekly_global_metric(aug2025_slice, "collaboration_automation_augmentation",
                                             "augmentation_pct", "augmentation")
    nov2025 = read_weekly_collaboration(nov2025_slice)
    nov2025_auto, nov2025_aug = automation_from_components(nov2025["directive"], nov2025["feedback loop"],
                                                            nov2025["task iteration"], nov2025["learning"],
                                                            nov2025["validation"], nov2025["none"])
    feb2026 = read_weekly_collaboration(feb2026_slice)
    feb2026_auto, feb2026_aug = automation_from_components(feb2026["directive"], feb2026["feedback loop"],
                                                            feb2026["task iteration"], feb2026["learning"],
                                                            feb2026["validation"], feb2026["none"])

    automation_augmentation = [
        {"date": V1_DATE, "label": POINT_LABELS[V1_DATE], "source_release": "release_2025_02_10",
         "automation_pct": clean(v1_auto), "augmentation_pct": clean(v1_aug), "unnormalized": True},
        {"date": V2_DATE, "label": POINT_LABELS[V2_DATE], "source_release": "release_2025_03_27",
         "automation_pct": clean(v2_auto), "augmentation_pct": clean(v2_aug)},
        {"date": AUG_2025_DATE, "label": POINT_LABELS[AUG_2025_DATE], "source_release": "release_2025_09_15",
         "automation_pct": aug2025_auto, "augmentation_pct": aug2025_aug},
        {"date": NOV_2025_DATE, "label": POINT_LABELS[NOV_2025_DATE], "source_release": "release_2026_01_15",
         "automation_pct": clean(nov2025_auto), "augmentation_pct": clean(nov2025_aug)},
        {"date": FEB_2026_DATE, "label": POINT_LABELS[FEB_2026_DATE], "source_release": "release_2026_03_24",
         "automation_pct": clean(feb2026_auto), "augmentation_pct": clean(feb2026_aug)},
    ]
    for month in ("2026-04-01", "2026-05-01"):
        automation_augmentation.append({
            "date": month, "label": POINT_LABELS[month], "source_release": "release_2026_06_26",
            "automation_pct": overall_metric(overall_df, month, "collaboration_bucket_automation_pct"),
            "augmentation_pct": overall_metric(overall_df, month, "collaboration_bucket_augmentation_pct"),
        })

    # 2. usage patterns, 2-3 points each (only the two 2026 weekly snapshots + this release).
    nov2025_success = read_weekly_global_metric(nov2025_slice, "task_success", "task_success_pct", "yes")
    feb2026_success = read_weekly_global_metric(feb2026_slice, "task_success", "task_success_pct", "yes")
    usage_metric_ids = ["use_case_work_pct", "use_case_personal_pct", "use_case_coursework_pct",
                         "ai_autonomy_mean", "human_only_time_mean", "human_with_ai_time_mean",
                         "human_only_ability_pct", "multitasking_pct"]
    weekly_facet_variable = {
        "use_case_work_pct": ("use_case", "use_case_pct", "work"),
        "use_case_personal_pct": ("use_case", "use_case_pct", "personal"),
        "use_case_coursework_pct": ("use_case", "use_case_pct", "coursework"),
        "ai_autonomy_mean": ("ai_autonomy", "ai_autonomy_mean", None),
        "human_only_time_mean": ("human_only_time", "human_only_time_mean", None),
        "human_with_ai_time_mean": ("human_with_ai_time", "human_with_ai_time_mean", None),
        "human_only_ability_pct": ("human_only_ability", "human_only_ability_pct", "yes"),
        "multitasking_pct": ("multitasking", "multitasking_pct", "yes"),
    }
    task_success_points = {NOV_2025_DATE: nov2025_success, FEB_2026_DATE: feb2026_success}
    usage_patterns = {"task_success_pct": {k: v for k, v in task_success_points.items() if v is not None}}
    for metric_id in usage_metric_ids:
        facet, variable, cluster = weekly_facet_variable[metric_id]
        points = {
            NOV_2025_DATE: read_weekly_global_metric(nov2025_slice, facet, variable, cluster),
            FEB_2026_DATE: read_weekly_global_metric(feb2026_slice, facet, variable, cluster),
        }
        for month in ("2026-04-01", "2026-05-01"):
            points[month] = overall_metric(overall_df, month, metric_id)
        usage_patterns[metric_id] = {k: v for k, v in points.items() if v is not None}

    # 3. top O*NET tasks, up to 6 points each.
    v1_tasks = read_report_csv_tasks(V1_TASK_PATH)
    v2_tasks = read_report_csv_tasks(V2_TASK_PATH)
    aug2025_tasks = read_weekly_onet_tasks(aug2025_slice)
    nov2025_tasks = read_weekly_onet_tasks(nov2025_slice)
    feb2026_tasks = read_weekly_onet_tasks(feb2026_slice)

    latest = onet_task_df[onet_task_df["date_start"] == "2026-05-01"].nlargest(TOP_TASK_COUNT, "value")
    top_tasks = []
    for _, row in latest.iterrows():
        key = norm_task(row["node_name"])
        points = {}
        if key in v1_tasks:
            points[V1_DATE] = v1_tasks[key]
        if key in v2_tasks:
            points[V2_DATE] = v2_tasks[key]
        if key in aug2025_tasks:
            points[AUG_2025_DATE] = aug2025_tasks[key]
        if key in nov2025_tasks:
            points[NOV_2025_DATE] = nov2025_tasks[key]
        if key in feb2026_tasks:
            points[FEB_2026_DATE] = feb2026_tasks[key]
        for _, r2 in onet_task_df[onet_task_df["node_name"] == row["node_name"]].iterrows():
            points[r2["date_start"]] = clean(r2["value"])
        top_tasks.append({"task": row["node_name"], "points": points})

    return {
        "automation_augmentation": automation_augmentation,
        "usage_patterns": usage_patterns,
        "top_onet_tasks": top_tasks,
        "point_labels": POINT_LABELS,
    }


def main():
    OCC_DIR.mkdir(parents=True, exist_ok=True)

    slices = {source: extract(path) for source, path in FILES.items()}
    source_rows = {}
    for source, path in FILES.items():
        source_rows[source] = sum(
            len(chunk) for chunk in pd.read_csv(path, usecols=["node_name"], chunksize=CHUNKSIZE)
        )

    job_exposure = load_job_exposure()
    wage_data = load_wage_data()
    major_group_aug_2025 = load_major_group_trend()
    overall_df = extract_category(FILES["claude_ai"], "overall")
    onet_task_df = extract_category(FILES["claude_ai"], "onet", hierarchy_level="0", metric_id="pct")
    global_trends = build_global_trends(overall_df, onet_task_df)

    months = sorted(set().union(*[set(df["date_start"].unique()) for df in slices.values()]))
    sources = list(FILES.keys())

    # medians per source/month/metric_id over the whole slice.
    medians = {}
    for source, df in slices.items():
        medians[source] = {}
        med = df.groupby(["date_start", "metric_id"])["value"].median()
        for (date_start, metric_id), val in med.items():
            v = clean(val)
            if v is None:
                continue
            medians[source].setdefault(date_start, {})[metric_id] = v

    # soc -> title (prefer claude_ai's node_name, fall back to 1p_api's).
    soc_title = {}
    for source in sources:
        df = slices[source]
        for soc, title in df[["soc", "node_name"]].drop_duplicates("soc").values:
            soc_title.setdefault(soc, title)

    all_socs = sorted(soc_title.keys())

    # per-occupation, per-source, per-month metric dict: soc -> source -> month -> {metric_id: value}
    metrics_by_soc = {soc: {source: {m: {} for m in months} for source in sources} for soc in all_socs}
    for source, df in slices.items():
        for soc, date_start, metric_id, value in df[["soc", "date_start", "metric_id", "value"]].itertuples(index=False):
            v = clean(value)
            if v is None:
                continue
            metrics_by_soc[soc][source][date_start][metric_id] = v

    # automation_pct per soc/source/month, used for neighbour selection and index.json.
    def automation_pct(soc, source, month):
        return metrics_by_soc[soc][source][month].get("collaboration_bucket_automation_pct")

    def usage_pct(soc, source, month):
        return metrics_by_soc[soc][source][month].get(USAGE_METRIC_ID)

    # build neighbours: same JobFamily, lower automation % (pinned source/month),
    # salary within +-25%, top 3 lowest automation. Needs wage_data on both sides.
    neighbours_by_soc = {}
    family_members = {}
    for soc in all_socs:
        if soc not in wage_data.index:
            continue
        family = wage_data.loc[soc, "JobFamily"]
        family_members.setdefault(family, []).append(soc)

    # major_group_trend: one real historical point (Aug 2025, major-group granularity)
    # plus the two detailed months rolled up to the same granularity, so all three
    # points are comparable. "pct" (USAGE_METRIC_ID) is documented as "Percentage of
    # the geography's total in this category node" -- a share-of-total metric, so the
    # correct rollup from detailed occupations to their shared major group is SUM, not
    # an average/median (per release_2026_06_26/data_documentation.md and confirmed:
    # detailed-occupation pct sums to ~98.5 across all occupations, same as Aug 2025's
    # major-group pct summing to exactly 100). Never blended into per-occupation
    # metrics -- surfaced only under this key.
    major_group_trend = {}
    for family, socs_in_family in family_members.items():
        point = {}
        if family in major_group_aug_2025:
            point[MAJOR_GROUP_TREND_DATE] = major_group_aug_2025[family]
        for month in months:
            vals = [usage_pct(s, "claude_ai", month) for s in socs_in_family]
            vals = [v for v in vals if v is not None]
            if vals:
                point[month] = clean(sum(vals))
        if len(point) >= 2:
            major_group_trend[family] = point

    for soc in all_socs:
        if soc not in wage_data.index:
            continue
        subj_auto = automation_pct(soc, NEIGHBOUR_SOURCE, NEIGHBOUR_MONTH)
        subj_salary = clean(wage_data.loc[soc, "MedianSalary"])
        if subj_auto is None or subj_salary is None:
            continue
        family = wage_data.loc[soc, "JobFamily"]
        candidates = []
        for other in family_members.get(family, []):
            if other == soc:
                continue
            other_auto = automation_pct(other, NEIGHBOUR_SOURCE, NEIGHBOUR_MONTH)
            other_salary = clean(wage_data.loc[other, "MedianSalary"])
            if other_auto is None or other_salary is None:
                continue
            if other_auto >= subj_auto:
                continue
            if not (0.75 * subj_salary <= other_salary <= 1.25 * subj_salary):
                continue
            candidates.append((other_auto, other, other_salary))
        candidates.sort(key=lambda t: t[0])
        top3 = candidates[:3]
        if top3:
            neighbours_by_soc[soc] = [
                {"soc": soc2, "title": soc_title.get(soc2, soc2),
                 "automation_pct": auto, "salary": sal}
                for auto, soc2, sal in top3
            ]

    # index.json occupations, sorted by usage_pct desc (best available: claude_ai then 1p_api, latest month first)
    def best_usage(soc):
        for source in sources:
            for month in reversed(months):
                v = usage_pct(soc, source, month)
                if v is not None:
                    return v
        return None

    def best_automation(soc):
        for source in sources:
            for month in reversed(months):
                v = automation_pct(soc, source, month)
                if v is not None:
                    return v
        return None

    occ_entries = []
    for soc in all_socs:
        entry = {"soc": soc, "title": soc_title[soc]}
        if soc in job_exposure.index:
            exp = clean(job_exposure.loc[soc, "observed_exposure"])
            if exp is not None:
                entry["exposure"] = exp
        u = best_usage(soc)
        if u is not None:
            entry["usage_pct"] = u
        a = best_automation(soc)
        if a is not None:
            entry["automation_pct"] = a
        if soc in wage_data.index:
            salary = clean(wage_data.loc[soc, "MedianSalary"])
            if salary is not None:
                entry["salary"] = salary
            family = wage_data.loc[soc, "JobFamily"]
            if isinstance(family, str) and family:
                entry["job_family"] = family
        occ_entries.append(entry)

    occ_entries.sort(key=lambda e: (e.get("usage_pct") is None, -(e.get("usage_pct") or 0)))

    index_doc = {
        "generated_at": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_release": "release_2026_06_26",
        "source_rows": source_rows,
        "months": months,
        "sources": sources,
        "medians": medians,
        "occupations": occ_entries,
        "major_group_trend": major_group_trend,
        "global_trends": global_trends,
    }

    with open(OUT_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump(index_doc, f, allow_nan=False)

    files_written = 1
    for soc in all_socs:
        doc = {"soc": soc, "title": soc_title[soc]}
        if soc in job_exposure.index:
            exp = clean(job_exposure.loc[soc, "observed_exposure"])
            if exp is not None:
                doc["exposure"] = exp
        if soc in wage_data.index:
            wb = wage_block(wage_data.loc[soc])
            if wb:
                doc["wage"] = wb
        if soc in neighbours_by_soc:
            doc["neighbours"] = neighbours_by_soc[soc]
        doc["metrics"] = metrics_by_soc[soc]
        with open(OCC_DIR / f"{soc}.json", "w", encoding="utf-8") as f:
            json.dump(doc, f, allow_nan=False)
        files_written += 1

    total_bytes = sum(p.stat().st_size for p in OUT_DIR.rglob("*.json"))

    log_lines = [
        f"source_rows: {source_rows}",
        f"slice_rows: {{'claude_ai': {len(slices['claude_ai'])}, '1p_api': {len(slices['1p_api'])}}}",
        f"occupation_count: {len(all_socs)}",
        f"files_written: {files_written}",
        f"total_output_bytes: {total_bytes}",
        f"neighbours_computed_for: {len(neighbours_by_soc)} occupations "
        f"(pinned source={NEIGHBOUR_SOURCE}, month={NEIGHBOUR_MONTH})",
        "",
    ]
    with open("build_log.txt", "a", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print("\n".join(log_lines))


if __name__ == "__main__":
    main()
