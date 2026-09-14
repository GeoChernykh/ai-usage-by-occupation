"""Check the built payload against PLAN.md GATE 2. Standard library only.

Run: .venv\\Scripts\\python.exe verify_data.py   (exits non-zero on any failure)
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site", "data")
MONTH = "2026-05-01"

failures = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        failures.append(msg)


def near(a, b, tol):
    return a is not None and abs(a - b) <= tol


def load(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as fh:
        return json.load(fh)


# PLAN.md section 1.4: soc -> pct, human_only_time_mean, human_with_ai_time_mean,
# speedup, task count.
FIXTURES = {
    "15-1299.03": (5.10, 2.05, 13.3, 9.2, 12),
    "25-4022": (4.22, 2.41, 20.5, 7.1, 8),
    "27-3041": (2.58, 4.88, 46.2, 6.3, 10),
    "15-1211": (1.91, 5.21, 66.4, 4.7, 16),
    "15-1251": (1.67, 9.12, 52.4, 10.5, 11),
    "15-1252": (0.35, 5.90, 47.8, 7.4, 9),
    "23-1011": (0.62, 5.83, 54.1, 6.5, 7),
    "13-2011": (0.12, 9.49, 47.1, 12.1, 13),
    "25-1021": (0.01, 5.21, 48.1, 6.5, 4),
}

COUNTRY_FIXTURES = {
    ("UKR", "usage_per_capita_index"): 0.78,
    ("UKR", "usage_pct"): 0.47,
    ("UKR", "use_case_coursework_pct"): 18.77,
    ("UKR", "use_case_work_pct"): 40.61,
    ("UKR", "collaboration_bucket_automation_pct"): 48.90,
    ("AUS", "usage_per_capita_index"): 6.40,
    ("USA", "usage_pct"): 20.16,
}


def main():
    print("index.json")
    index = load("index.json")
    occs = index["occupations"]
    check(len(occs) == 746, f"746 occupations (got {len(occs)})")
    check(index["counts"]["tasks"] == 2823, f"2823 tasks (got {index['counts']['tasks']})")
    check(index["counts"]["countries"] == 121,
          f"121 countries (got {index['counts']['countries']})")
    check(index["counts"]["occupations_with_tasks"] >= 655,
          f">=655 occupations with tasks (got {index['counts']['occupations_with_tasks']})")
    total_pct = sum(o.get("pct", 0) for o in occs if "claude_ai" in o["src"])
    check(near(total_pct, 98.51, 0.05), f"sum of pct is 98.51 (got {total_pct:.2f})")
    for source in index["sources"]:
        for month in index["months"]:
            check(bool(index["medians"].get(source, {}).get(month)),
                  f"medians present for {source} {month}")

    print("occ/*.json")
    files = os.listdir(os.path.join(OUT, "occ"))
    check(len(files) == len(occs), f"one file per occupation (got {len(files)})")
    n_with_tasks = n_tasks = 0
    for o in occs:
        path = os.path.join(OUT, "occ", o["soc"] + ".json")
        if not os.path.isfile(path):
            check(False, f"missing occ/{o['soc']}.json")
            continue
        raw = open(path, encoding="utf-8").read()
        if "NaN" in raw or "Infinity" in raw or '"nan"' in raw:
            check(False, f"occ/{o['soc']}.json contains NaN/Infinity")
        doc = json.loads(raw)
        if doc["tasks"]:
            n_with_tasks += 1
            n_tasks += len(doc["tasks"])
        for source in index["sources"]:
            for month in index["months"]:
                if month not in doc["metrics"].get(source, {}):
                    check(False, f"occ/{o['soc']}.json missing {source} {month}")
    check(n_with_tasks >= 655, f">=655 files with tasks (got {n_with_tasks})")
    check(n_tasks >= 2500, f">=2500 task rows (got {n_tasks})")

    print("fixtures (PLAN section 1.4)")
    for soc, (pct, h_only, h_ai, speedup, n) in FIXTURES.items():
        doc = load(os.path.join("occ", soc + ".json"))
        m = doc["metrics"]["claude_ai"][MONTH]
        d = doc["derived"]["claude_ai"][MONTH]
        check(near(m.get("pct"), pct, 0.01), f"{soc} pct {pct} (got {m.get('pct')})")
        check(near(m.get("human_only_time_mean"), h_only, 0.01),
              f"{soc} human_only_time_mean {h_only} (got {m.get('human_only_time_mean')})")
        check(near(m.get("human_with_ai_time_mean"), h_ai, 0.05),
              f"{soc} human_with_ai_time_mean {h_ai} (got {m.get('human_with_ai_time_mean')})")
        check(near(d.get("speedup"), speedup, 0.1),
              f"{soc} speedup {speedup} (got {d.get('speedup')})")
        check(len(doc["tasks"]) == n, f"{soc} has {n} tasks (got {len(doc['tasks'])})")

    print("countries.json")
    countries = {c["iso3"]: c for c in load("countries.json")["countries"]}
    check(len(countries) == 121, f"121 countries (got {len(countries)})")
    for (code, metric), expected in COUNTRY_FIXTURES.items():
        got = countries.get(code, {}).get("m", {}).get(MONTH, {}).get(metric)
        check(near(got, expected, 0.01), f"{code} {metric} {expected} (got {got})")

    print("subregions.json")
    sub = load("subregions.json")
    rows = {s["code"]: s for s in sub["subregions"]}
    check(len(rows) == 652, f"652 subregions (got {len(rows)})")
    ua = [c for c in rows if c.startswith("UA-")]
    check(len(ua) == 10, f"10 Ukrainian subregions (got {len(ua)})")
    check(near(rows.get("UA-30", {}).get("m", {}).get(MONTH, {}).get("usage_pct"),
               29.79, 0.01),
          f"UA-30 usage_pct 29.79 (got {rows.get('UA-30', {}).get('m', {}).get(MONTH, {}).get('usage_pct')})")
    ua_total = sub["usage_pct_published_total"].get("UKR", {}).get(MONTH)
    check(near(ua_total, 84.82, 0.05), f"UKR published total 84.82 (got {ua_total})")
    check(not any("usage_per_capita_index" in mo
                  for s in sub["subregions"] for mo in s["m"].values()),
          "no subregion carries usage_per_capita_index")

    print("payload size")
    size = sum(os.path.getsize(os.path.join(dp, f))
               for dp, _, fs in os.walk(OUT) for f in fs)
    check(size < 12 * 1024 * 1024, f"site/data under 12 MB (got {size / 1024 / 1024:.2f} MB)")

    print()
    if failures:
        print(f"{len(failures)} check(s) failed")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
