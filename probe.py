"""Schema probe for plan.md Task 1. Read-only against data/. Chunked, no full-file loads."""
import pandas as pd

BIG_FILES = {
    "claude_ai": "data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv",
    "1p_api": "data/release_2026_06_26/data/aei_1p_api_2026-06-26.csv",
}
JOB_EXPOSURE = "data/labor_market_impacts/job_exposure.csv"
WAGE_DATA = "data/release_2025_02_10/wage_data.csv"

CHUNKSIZE = 500_000


def norm_soc(code):
    if code is None:
        return None
    c = str(code).strip()
    if c.endswith(".00"):
        c = c[:-3]
    return c


def probe_big(path, label):
    total_rows = 0
    category_names = set()
    geo_levels = set()
    hierarchy_levels = set()
    date_starts = set()
    metric_ids = set()
    slice_rows = 0
    slice_node_names = set()
    slice_samples = []
    slice_external_ids = set()
    per_occ_metrics = {}  # node_name -> {date_start: set(metric_id)}

    for chunk in pd.read_csv(path, sep=",", dtype=str, chunksize=CHUNKSIZE):
        total_rows += len(chunk)
        category_names.update(chunk["category_name"].dropna().unique())
        if "geo_level" in chunk.columns:
            geo_levels.update(chunk["geo_level"].dropna().unique())
        hierarchy_levels.update(chunk["hierarchy_level"].dropna().unique())
        date_starts.update(chunk["date_start"].dropna().unique())
        metric_ids.update(chunk["metric_id"].dropna().unique())

        mask = (
            (chunk["category_name"] == "soc_occupation")
            & (chunk["hierarchy_level"] == "0")
            & (chunk["geo_id"] == "GLOBAL")
        )
        sl = chunk.loc[mask]
        slice_rows += len(sl)
        slice_node_names.update(sl["node_name"].dropna().unique())
        slice_external_ids.update(sl["node_external_id"].dropna().unique())
        if len(slice_samples) < 10:
            need = 10 - len(slice_samples)
            slice_samples.extend(sl["node_external_id"].dropna().unique()[:need].tolist())

        for node_name, sub in sl.groupby("node_name"):
            d = per_occ_metrics.setdefault(node_name, {})
            for date_start, sub2 in sub.groupby("date_start"):
                d.setdefault(date_start, set()).update(sub2["metric_id"].dropna().unique())

    sample_occ = None
    if per_occ_metrics:
        sample_occ = sorted(per_occ_metrics.keys())[0]

    return {
        "label": label,
        "total_rows": total_rows,
        "category_names": category_names,
        "geo_levels": geo_levels,
        "hierarchy_levels": hierarchy_levels,
        "date_starts": date_starts,
        "metric_ids": metric_ids,
        "slice_rows": slice_rows,
        "slice_node_names": slice_node_names,
        "slice_samples": slice_samples,
        "slice_external_ids": slice_external_ids,
        "sample_occ": sample_occ,
        "sample_occ_metrics": per_occ_metrics.get(sample_occ) if sample_occ else None,
    }


def probe_lookup(path, code_col):
    df = pd.read_csv(path, dtype=str)
    header = list(df.columns)
    row_count = len(df)
    samples = df[code_col].dropna().unique()[:10].tolist()
    codes = set(norm_soc(c) for c in df[code_col].dropna().unique())
    return header, row_count, samples, codes


def main():
    lines = []
    lines.append(f"# Probe results\n")

    results = {}
    for label, path in BIG_FILES.items():
        r = probe_big(path, label)
        results[label] = r
        lines.append(f"## {label} ({path})\n")
        lines.append(f"- Total row count: {r['total_rows']}\n")
        lines.append(f"- Distinct category_name: {sorted(r['category_names'])}\n")
        lines.append(f"- Distinct geo_level: {sorted(r['geo_levels'])}\n")
        lines.append(f"- Distinct hierarchy_level: {sorted(r['hierarchy_levels'])}\n")
        lines.append(f"- Distinct date_start: {sorted(r['date_starts'])}\n")
        lines.append(f"- Distinct metric_id count: {len(r['metric_ids'])}\n")
        lines.append(f"- Full sorted metric_id list:\n")
        for m in sorted(r["metric_ids"]):
            lines.append(f"  - {m}\n")
        lines.append(
            f"- Target slice (soc_occupation, hierarchy_level=0, geo_id=GLOBAL) row count: {r['slice_rows']}\n"
        )
        lines.append(f"- Distinct node_name in slice: {len(r['slice_node_names'])}\n")
        lines.append(f"- Ten sample node_external_id values: {r['slice_samples']}\n")
        if r["sample_occ"] is not None:
            lines.append(f"- Sample occupation for per-date metric listing: {r['sample_occ']}\n")
            for date_start, metrics in sorted(r["sample_occ_metrics"].items()):
                lines.append(f"  - {date_start}: {sorted(metrics)}\n")
        lines.append("\n")

    je_header, je_rows, je_samples, je_codes = probe_lookup(JOB_EXPOSURE, "occ_code")
    lines.append(f"## job_exposure.csv\n")
    lines.append(f"- Header: {je_header}\n")
    lines.append(f"- Row count: {je_rows}\n")
    lines.append(f"- Ten sample occ_code values: {je_samples}\n\n")

    wd_header, wd_rows, wd_samples, wd_codes = probe_lookup(WAGE_DATA, "SOCcode")
    lines.append(f"## wage_data.csv\n")
    lines.append(f"- Header: {wd_header}\n")
    lines.append(f"- Row count: {wd_rows}\n")
    lines.append(f"- Ten sample SOCcode values: {wd_samples}\n\n")

    lines.append("## Overlap after normalisation (strip trailing .00)\n")
    for label, r in results.items():
        slice_codes = set(norm_soc(x) for x in r["slice_external_ids"])
        n = len(slice_codes)
        je_match = len(slice_codes & je_codes)
        wd_match = len(slice_codes & wd_codes)
        je_pct = 100 * je_match / n if n else 0
        wd_pct = 100 * wd_match / n if n else 0
        lines.append(
            f"- {label}: slice codes={n}, job_exposure match={je_match} ({je_pct:.1f}%), "
            f"wage_data match={wd_match} ({wd_pct:.1f}%)\n"
        )
    lines.append("\n")

    with open("probe_results.md", "a", encoding="utf-8") as f:
        f.writelines(lines)

    print("".join(lines))
    return results, je_codes, wd_codes


if __name__ == "__main__":
    main()
