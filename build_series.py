"""Reconstruct per-occupation usage shares across the six published releases.

Each release re-clusters usage into its own O*NET task set, and only the current
one publishes task ids. The bridge is the task text: normalised and looked up in
the O*NET 30.0 statements, which give a unique SOC for 17,139 texts. Shares are
renormalised within the matched subset of each release, because matched coverage
ranges from 67 to 91 percentage points.

Separate entry point from build_data.py on purpose: if this fails, Screens 1 and
3 are untouched and the app simply hides the Compare tab.

Run: .venv\\Scripts\\python.exe build_series.py
"""

import json
import os
import re
import statistics

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site", "data", "series.json")
NOTES = os.path.join(ROOT, "BUILD_NOTES.md")

WEEKLY_COLS = ["geo_id", "facet", "level", "variable", "cluster_name", "value"]

# key, label, release, window, path, kind
POINTS = [
    ("2025-02", "Feb 2025", "release_2025_02_10", "task_pct_v1",
     "data/release_2025_03_27/task_pct_v1.csv", "pair"),
    ("2025-03", "Mar 2025", "release_2025_03_27", "task_pct_v2",
     "data/release_2025_03_27/task_pct_v2.csv", "pair"),
    ("2025-08", "Aug 2025", "release_2025_09_15", "2025-08-04 to 2025-08-11",
     "data/release_2025_09_15/data/output/aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv",
     "weekly"),
    ("2025-11", "Nov 2025", "release_2026_01_15", "2025-11-13 to 2025-11-20",
     "data/release_2026_01_15/data/intermediate/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv",
     "weekly"),
    ("2026-02", "Feb 2026", "release_2026_03_24", "2026-02-05 to 2026-02-12",
     "data/release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv", "weekly"),
    ("2026-04", "Apr 2026", "release_2026_06_26", "2026-04-01",
     "data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv", "current"),
    ("2026-05", "May 2026", "release_2026_06_26", "2026-05-01",
     "data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv", "current"),
]


def norm_soc(x):
    x = str(x).strip()
    return x[:-3] if x.endswith(".00") else x


def norm_task(s):
    return re.sub(r"\s+", " ", str(s).strip().lower()).rstrip(".")


def onet_maps():
    st = pd.read_csv(os.path.join(ROOT, "lookups", "onet30_task_statements.txt"),
                     sep="\t", dtype=str)
    st["soc"] = st["O*NET-SOC Code"].str.strip().map(norm_soc)
    st["norm"] = st["Task"].map(norm_task)
    by_id = dict(zip(st["Task ID"].str.strip(), st["soc"]))
    counts = st.groupby("norm")["soc"].nunique()
    unambiguous = set(counts[counts == 1].index)
    by_text = {n: s for n, s in zip(st["norm"], st["soc"]) if n in unambiguous}
    print(f"O*NET 30.0: {len(by_id)} task ids, {len(by_text)} unambiguous texts "
          f"({len(counts) - len(by_text)} dropped as ambiguous)")
    return by_id, by_text


def read_point(path, kind, window):
    """Return a DataFrame of task-level global shares: text, pct[, id]."""
    full = os.path.join(ROOT, path)
    if kind == "pair":
        df = pd.read_csv(full)
        return pd.DataFrame({"text": df["task_name"], "pct": df["pct"]})
    if kind == "weekly":
        parts = []
        for chunk in pd.read_csv(full, usecols=WEEKLY_COLS, dtype=str, chunksize=400_000):
            m = ((chunk["geo_id"] == "GLOBAL") & (chunk["facet"] == "onet_task")
                 & (chunk["level"] == "0") & (chunk["variable"] == "onet_task_pct"))
            if m.any():
                parts.append(chunk.loc[m, ["cluster_name", "value"]])
        df = pd.concat(parts, ignore_index=True)
        return pd.DataFrame({"text": df["cluster_name"],
                             "pct": pd.to_numeric(df["value"], errors="coerce")}).dropna()
    parts = []
    cols = ["date_start", "geo_id", "category_name", "hierarchy_level",
            "metric_id", "value", "node_name", "node_external_id"]
    for chunk in pd.read_csv(full, usecols=cols, dtype=str, chunksize=400_000):
        m = ((chunk["geo_id"] == "GLOBAL") & (chunk["category_name"] == "onet")
             & (chunk["hierarchy_level"] == "0") & (chunk["metric_id"] == "pct")
             & (chunk["date_start"] == window))
        if m.any():
            parts.append(chunk.loc[m, ["node_name", "node_external_id", "value"]])
    df = pd.concat(parts, ignore_index=True)
    return pd.DataFrame({"text": df["node_name"], "id": df["node_external_id"],
                         "pct": pd.to_numeric(df["value"], errors="coerce")}).dropna(
        subset=["pct"])


def shares(df, soc_col):
    """Renormalise within the matched subset, so points stay comparable."""
    matched = df[df[soc_col].notna()]
    total = matched["pct"].sum()
    by_soc = matched.groupby(soc_col)["pct"].sum() * 100 / total
    return by_soc.to_dict(), total


def main():
    by_id, by_text = onet_maps()
    points, series, notes = [], {}, []
    id_join = text_join = None

    for key, label, release, window, path, kind in POINTS:
        df = read_point(path, kind, window)
        raw_total = df["pct"].sum()
        df["soc_text"] = df["text"].map(norm_task).map(by_text)
        by_soc, matched = shares(df, "soc_text")
        matched_rate = df["soc_text"].notna().mean()
        print(f"{label}: {len(df)} tasks, pct sums to {raw_total:.1f}, "
              f"{matched_rate:.1%} text-matched carrying {matched:.1f} pp, "
              f"{len(by_soc)} occupations")
        # The weekly files carry a platform_and_product column; a bad geography
        # filter would double-count, so their shares must still sum to ~100.
        # The current release publishes only the nodes that met its thresholds,
        # so its raw total is below 100 by design.
        if kind == "weekly" and not 95 <= raw_total <= 105:
            notes.append(f"- {label}: task `pct` sums to {raw_total:.1f}, not ~100 "
                         f"- check the geography filter on `{path}`.")
        points.append({"key": key, "label": label, "release": release, "window": window,
                       "matched_pct": round(matched, 1), "n_tasks": int(len(df))})
        series[key] = by_soc
        if key == "2026-05":
            df["soc_id"] = df["id"].map(by_id)
            id_join, _ = shares(df, "soc_id")
            text_join = by_soc

    # Method consistency: is the Task ID join close enough to the text join that
    # mixing the two across the series would be safe?
    top50 = sorted(id_join, key=id_join.get, reverse=True)[:50]
    diffs = [abs(id_join[s] - text_join.get(s, 0.0)) for s in top50]
    median_diff = statistics.median(diffs)
    id_rank = {s: i for i, s in enumerate(sorted(id_join, key=id_join.get, reverse=True))}
    text_rank = {s: i for i, s in enumerate(sorted(text_join, key=text_join.get,
                                                   reverse=True))}
    top10 = sorted(id_join, key=id_join.get, reverse=True)[:10]
    max_move = max(abs(id_rank[s] - text_rank.get(s, len(text_rank))) for s in top10)
    method = "text" if (median_diff > 0.5 or max_move > 3) else "id"
    print(f"method check: median |difference| over the top 50 = {median_diff:.3f} pp, "
          f"largest top-10 rank move = {max_move} -> method '{method}'")

    if method == "id":
        series["2026-05"] = id_join
        df_apr = read_point(POINTS[5][4], "current", POINTS[5][3])
        df_apr["soc_id"] = df_apr["id"].map(by_id)
        series["2026-04"], _ = shares(df_apr, "soc_id")

    keys = [p["key"] for p in points]
    socs = sorted({s for pt in series.values() for s in pt})
    out = {
        "points": points,
        "method": method,
        "occupations": {s: [round(series[k][s], 4) if s in series[k] else None
                            for k in keys] for s in socs},
        "global": {},
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"), allow_nan=False)
    print(f"wrote series.json: {os.path.getsize(OUT) // 1024} KB, "
          f"{len(socs)} occupations over {len(points)} points")

    with open(NOTES, "a", encoding="utf-8") as fh:
        fh.write("\n## build_series.py method check\n\n")
        fh.write(f"- Median absolute difference in `share_r` across the top 50 occupations, "
                 f"Task ID join against text join, May 2026: **{median_diff:.3f} pp**.\n")
        fh.write(f"- Largest rank change among the top 10 occupations: **{max_move}**.\n")
        fh.write(f"- Decision: `method = \"{method}\"`"
                 + (" - the two joins agree closely enough that the current release keeps its "
                    "Task ID join while earlier releases, which publish no task ids, use text.\n"
                    if method == "id" else
                    " - the joins disagree, so every point uses the text join; method "
                    "consistency matters more than per-point accuracy in a time series.\n"))
        for n in notes:
            fh.write(n + "\n")


if __name__ == "__main__":
    main()
