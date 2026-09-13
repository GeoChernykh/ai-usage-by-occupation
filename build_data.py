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
