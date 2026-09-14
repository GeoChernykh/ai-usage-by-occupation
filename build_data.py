"""Precompute the static JSON payload the AI Time Machine front-end reads.

One chunked pass per release CSV, then everything is derived in memory. See
PLAN.md section 4 for the output contract.

Run: .venv\\Scripts\\python.exe build_data.py
"""

import json
import os
import re
import shutil
import time
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
RELEASE = "release_2026_06_26"
SRC_FILES = {
    "claude_ai": f"data/{RELEASE}/data/aei_claude_ai_2026-06-26.csv",
    "1p_api": f"data/{RELEASE}/data/aei_1p_api_2026-06-26.csv",
}
OUT = os.path.join(ROOT, "site", "data")
OCC_DIR = os.path.join(OUT, "occ")
LOG = os.path.join(ROOT, "build_log.txt")

COLS = ["date_start", "geo_id", "geo_level", "category_name",
        "hierarchy_level", "metric_id", "value", "node_name", "node_external_id"]

TASK_METRICS = ["pct", "human_only_time_mean", "human_with_ai_time_mean",
                "ai_autonomy_mean", "collaboration_bucket_automation_pct",
                "use_case_coursework_pct"]

SUBREGION_METRICS = ["usage_pct", "use_case_work_pct", "use_case_personal_pct",
                     "use_case_coursework_pct", "collaboration_bucket_automation_pct",
                     "collaboration_bucket_augmentation_pct", "ai_autonomy_mean",
                     "human_only_time_mean", "human_with_ai_time_mean"]

# Fixtures from PLAN.md section 1.4, printed on every run so a corpus mismatch
# shows up before 746 files are written.
FIXTURES = ["15-1299.03", "25-4022", "27-3041", "15-1211", "15-1251",
            "15-1252", "23-1011", "13-2011", "25-1021"]

_log_lines = []


def log(msg):
    print(msg)
    _log_lines.append(msg)


def norm_soc(x):
    x = str(x).strip()
    return x[:-3] if x.endswith(".00") else x


def norm_task(s):
    return re.sub(r"\s+", " ", str(s).strip().lower()).rstrip(".")


def r(v, nd=4):
    """Round for JSON, or None when the value is missing or not finite."""
    if v is None or pd.isna(v):
        return None
    v = float(v)
    if v in (float("inf"), float("-inf")):
        return None
    return round(v, nd)


def blob(row):
    """A metric_id -> value dict with absent metrics omitted, never zeroed."""
    return {k: r(v) for k, v in row.items() if r(v) is not None}


def derive(m):
    """Derived metrics, each emitted only when both of its inputs are present."""
    d = {}
    h_only, h_ai = m.get("human_only_time_mean"), m.get("human_with_ai_time_mean")
    if h_only is not None and h_ai:
        d["speedup"] = r(h_only * 60 / h_ai)
        d["time_saved_h"] = r(h_only - h_ai / 60)
    ai_edu, hum_edu = m.get("ai_education_years_mean"), m.get("human_education_years_mean")
    if ai_edu is not None and hum_edu is not None:
        d["edu_gap"] = r(ai_edu - hum_edu)
    return d


def scan(path, source):
    """Single chunked pass keeping every slice this build needs from one file."""
    parts = []
    rows = 0
    for chunk in pd.read_csv(path, usecols=COLS, dtype=str, chunksize=400_000):
        rows += len(chunk)
        cat, lvl = chunk["category_name"], chunk["hierarchy_level"]
        keep = (
            ((chunk["geo_id"] == "GLOBAL")
             & (((cat == "soc_occupation") & lvl.isin(["0", "1"]))
                | ((cat == "onet") & (lvl == "0"))))
            | (chunk["geo_level"].isin(["country", "subregion"]) & (cat == "overall"))
        )
        if keep.any():
            parts.append(chunk.loc[keep])
    df = pd.concat(parts, ignore_index=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["source"] = source
    log(f"{source}: {rows:,} rows read, {len(df):,} kept")
    return df


def wide(df, index):
    return df.pivot_table(index=index, columns="metric_id", values="value",
                          aggfunc="first")


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    if os.path.isdir(OCC_DIR):
        shutil.rmtree(OCC_DIR)          # only occ/ is cleared: world.geojson and
    os.makedirs(OCC_DIR)                # series.json come from other scripts

    frames = {s: scan(os.path.join(ROOT, p), s) for s, p in SRC_FILES.items()}
    all_df = pd.concat(frames.values(), ignore_index=True)

    is_global = all_df["geo_id"] == "GLOBAL"
    occ = all_df[is_global & (all_df["category_name"] == "soc_occupation")
                 & (all_df["hierarchy_level"] == "0")].copy()
    major = all_df[is_global & (all_df["category_name"] == "soc_occupation")
                   & (all_df["hierarchy_level"] == "1")]
    task = all_df[is_global & (all_df["category_name"] == "onet")
                  & (all_df["hierarchy_level"] == "0")
                  & (all_df["source"] == "claude_ai")].copy()
    country = all_df[(all_df["geo_level"] == "country")
                     & (all_df["source"] == "claude_ai")]
    subregion = all_df[(all_df["geo_level"] == "subregion")
                       & (all_df["source"] == "claude_ai")]
    for name, d in [("occupations", occ), ("major groups", major), ("tasks", task),
                    ("countries", country), ("subregions", subregion)]:
        log(f"slice {name}: {len(d):,} rows")

    occ["soc"] = occ["node_external_id"].map(norm_soc)
    months = sorted(all_df["date_start"].unique())
    latest = months[-1]
    log(f"months: {months}")

    titles = dict(zip(occ["soc"], occ["node_name"]))
    major_groups = {str(k).strip(): v for k, v in
                    zip(major["node_external_id"], major["node_name"])}

    # --- task -> occupation join, by O*NET Task ID (PLAN section 1.6) ---
    st = pd.read_csv(os.path.join(ROOT, "lookups", "onet30_task_statements.txt"),
                     sep="\t", dtype=str)
    st["soc"] = st["O*NET-SOC Code"].str.strip().map(norm_soc)
    by_id = dict(zip(st["Task ID"].str.strip(), st["soc"]))
    onet_totals = st.groupby("soc").size().to_dict()   # tasks O*NET lists per occupation
    task["soc"] = task["node_external_id"].str.strip().map(by_id)
    hit = task["soc"].notna().mean()
    log(f"task join hit rate: {hit:.1%}")
    assert hit >= 0.99, f"task join hit rate {hit:.1%} below 99%"

    # --- wide tables ---
    occ_w = wide(occ, ["source", "date_start", "soc"])
    task_w = wide(task, ["date_start", "node_external_id"])
    country_w = wide(country, ["date_start", "geo_id"])
    sub_w = wide(subregion, ["date_start", "geo_id"])

    task_text = dict(zip(task["node_external_id"], task["node_name"]))
    task_soc = dict(zip(task["node_external_id"], task["soc"]))

    # --- per-task derived values, used to rank each occupation's task table ---
    task_rows = {}
    for (month, tid), row in task_w.iterrows():
        m = blob(row)
        task_rows.setdefault(tid, {})[month] = m

    socs = sorted({s for s in occ["soc"].unique()})
    log(f"occupation universe: {len(socs)} codes "
        f"(claude_ai {occ[occ.source == 'claude_ai']['soc'].nunique()}, "
        f"1p_api {occ[occ.source == '1p_api']['soc'].nunique()})")

    tasks_by_soc = {}
    for tid, soc in task_soc.items():
        if soc:
            tasks_by_soc.setdefault(soc, []).append(tid)

    # --- occ/<soc>.json ---
    n_with_tasks = 0
    n_task_rows = 0
    fixture_report = {}
    for soc in socs:
        metrics, derived = {}, {}
        for source in SRC_FILES:
            metrics[source], derived[source] = {}, {}
            for month in months:
                key = (source, month, soc)
                m = blob(occ_w.loc[key]) if key in occ_w.index else {}
                metrics[source][month] = m
                d = derive(m)
                if d:
                    derived[source][month] = d

        tasks = []
        for tid in tasks_by_soc.get(soc, []):
            per_month = {mo: {k: v for k, v in task_rows[tid].get(mo, {}).items()
                              if k in TASK_METRICS}
                         for mo in months if task_rows[tid].get(mo)}
            tasks.append({"id": tid, "text": task_text[tid], "m": per_month})
        # rank by time saved in the latest month, ties by usage share
        def rank(t):
            m = t["m"].get(latest, {})
            d = derive(m)
            return (-(d.get("time_saved_h") or -1e9), -(m.get("pct") or 0))
        tasks.sort(key=rank)
        if tasks:
            n_with_tasks += 1
            n_task_rows += len(tasks)

        # usage-weighted time saved across the occupation's mapped tasks
        for source in SRC_FILES:
            for month in months:
                num = den = 0.0
                for t in tasks:
                    m = t["m"].get(month, {})
                    ts = derive(m).get("time_saved_h")
                    if ts is not None and m.get("pct"):
                        num += m["pct"] * ts
                        den += m["pct"]
                if den and source == "claude_ai":
                    derived.setdefault(source, {}).setdefault(month, {})
                    derived[source][month]["weighted_time_saved"] = r(num / den)

        doc = {"soc": soc, "title": titles.get(soc, soc), "mg": soc[:2],
               "metrics": metrics, "tasks": tasks, "derived": derived}
        with open(os.path.join(OCC_DIR, f"{soc}.json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, separators=(",", ":"), allow_nan=False)

        if soc in FIXTURES:
            m = metrics["claude_ai"][latest]
            fixture_report[soc] = (m.get("pct"), m.get("human_only_time_mean"),
                                   m.get("human_with_ai_time_mean"),
                                   derived["claude_ai"].get(latest, {}).get("speedup"),
                                   len(tasks))

    log(f"occupation files: {len(socs)}, with >=1 task: {n_with_tasks}, "
        f"task rows: {n_task_rows}")
    log("fixture check (claude_ai, latest month): soc pct h_only h_ai speedup n_tasks")
    for soc in FIXTURES:
        log(f"  {soc:12} {fixture_report.get(soc)}")

    # --- index.json ---
    occ_list = []
    for soc in socs:
        row, srcs = None, []
        for source in SRC_FILES:
            if (source, latest, soc) in occ_w.index:
                srcs.append(source)
                if row is None:
                    row = blob(occ_w.loc[(source, latest, soc)])
        row = row or {}
        entry = {"soc": soc, "title": titles.get(soc, soc), "mg": soc[:2],
                 "n_tasks": len(tasks_by_soc.get(soc, [])),
                 "n_onet": int(onet_totals.get(soc, 0)), "src": srcs}
        for key, metric in [("pct", "pct"), ("h_only", "human_only_time_mean"),
                            ("h_ai", "human_with_ai_time_mean"),
                            ("autonomy", "ai_autonomy_mean"),
                            ("automation", "collaboration_bucket_automation_pct"),
                            ("coursework", "use_case_coursework_pct"),
                            ("hum_edu", "human_education_years_mean"),
                            ("ai_edu", "ai_education_years_mean")]:
            if metric in row:
                entry[key] = row[metric]
        d = derive(row)
        if "speedup" in d:
            entry["speedup"] = d["speedup"]
        occ_list.append(entry)
    occ_list.sort(key=lambda e: -(e.get("pct") or 0))

    medians = {}
    for source in SRC_FILES:
        medians[source] = {}
        for month in months:
            sub = occ_w[(occ_w.index.get_level_values(0) == source)
                        & (occ_w.index.get_level_values(1) == month)]
            if len(sub):
                medians[source][month] = blob(sub.median(numeric_only=True))

    index = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_release": RELEASE,
        "release_label": "26.06.2026",
        "months": months,
        "sources": list(SRC_FILES),
        "source_rows": {"claude_ai": 1636573, "1p_api": 491705},
        "counts": {"occupations": len(socs), "tasks": len(task_text),
                   "countries": int(country["geo_id"].nunique()),
                   "subregions": int(subregion["geo_id"].nunique()),
                   "occupations_with_tasks": n_with_tasks},
        "medians": medians,
        "major_groups": major_groups,
        "occupations": occ_list,
    }
    write(index, "index.json")

    # --- tasks.json ---
    tasks_all = []
    for tid, text in task_text.items():
        m = task_rows.get(tid, {}).get(latest, {})
        soc = task_soc.get(tid)
        e = {"id": tid, "text": text}
        if soc and soc in titles:
            e["soc"] = soc
            e["occ_title"] = titles[soc]
        for key, metric in [("pct", "pct"), ("h_only", "human_only_time_mean"),
                            ("h_ai", "human_with_ai_time_mean"),
                            ("autonomy", "ai_autonomy_mean"),
                            ("automation", "collaboration_bucket_automation_pct")]:
            if metric in m:
                e[key] = m[metric]
        d = derive(m)
        if "speedup" in d:
            e["speedup"] = d["speedup"]
        tasks_all.append(e)
    tasks_all.sort(key=lambda e: -(e.get("pct") or 0))
    write(tasks_all, "tasks.json")

    # --- countries.json / subregions.json ---
    iso = pd.read_csv(os.path.join(ROOT, "data", "release_2025_09_15", "data",
                                   "intermediate", "iso_country_codes.csv"), dtype=str)
    name_by_iso3 = dict(zip(iso["iso_alpha_3"], iso["country_name"]))
    iso3_by_iso2 = dict(zip(iso["iso_alpha_2"], iso["iso_alpha_3"]))
    world = json.load(open(os.path.join(OUT, "world.geojson"), encoding="utf-8"))
    for f in world["features"]:
        name_by_iso3.setdefault(f["properties"]["iso3"], f["properties"]["name"])

    countries = []
    for code in sorted(country["geo_id"].unique()):
        m = {mo: (blob(country_w.loc[(mo, code)]) if (mo, code) in country_w.index else {})
             for mo in months}
        countries.append({"iso3": code, "name": name_by_iso3.get(code, code), "m": m})
    write({"metrics": sorted({k for c in countries for mo in c["m"].values() for k in mo}),
           "countries": countries}, "countries.json")

    subs, totals = [], {}
    for code in sorted(subregion["geo_id"].unique()):
        m = {}
        for mo in months:
            row = blob(sub_w.loc[(mo, code)]) if (mo, code) in sub_w.index else {}
            m[mo] = {k: v for k, v in row.items() if k in SUBREGION_METRICS}
        iso2 = code.split("-")[0]
        parent = iso3_by_iso2.get(iso2, iso2)
        subs.append({"code": code, "country": parent,
                     "name": code, "m": m})
        totals.setdefault(parent, {})
        for mo in months:
            totals[parent][mo] = r(totals[parent].get(mo, 0) + (m[mo].get("usage_pct") or 0))
    write({"metrics": SUBREGION_METRICS, "subregions": subs,
           "usage_pct_published_total": totals}, "subregions.json")

    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(OUT) for f in fs)
    log(f"site/data total: {total / 1024 / 1024:.2f} MB")
    log(f"elapsed: {time.time() - t0:.1f}s")
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"\n=== build_data.py {datetime.now().isoformat()} ===\n")
        fh.write("\n".join(_log_lines) + "\n")


def write(obj, name):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, separators=(",", ":"), allow_nan=False)
    log(f"wrote {name}: {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    main()
