"""Fetch the external lookups the build needs, once, and commit the results.

/data/ is gitignored and the Pages runner never runs Python, so anything
build_data.py reads at build time must be committed. This script downloads the
O*NET 30.0 task statements, the Natural Earth 50m country outlines (trimmed) and
the vendored ECharts bundle. It is idempotent: an existing non-empty target is
left alone.

Run: .venv\\Scripts\\python.exe fetch_lookups.py
"""

import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
LOOKUPS = os.path.join(ROOT, "lookups")
SITE_DATA = os.path.join(ROOT, "site", "data")
VENDOR = os.path.join(ROOT, "site", "vendor")
CACHE = os.path.join(ROOT, "data", ".cache")

ONET_URL = "https://www.onetcenter.org/dl_files/database/db_30_0_text/Task%20Statements.txt"
ONET_FALLBACK = "https://www.onetcenter.org/dl_files/database/db_29_0_text/Task%20Statements.txt"
NE_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
          "geojson/ne_50m_admin_0_countries.geojson")
NE_FALLBACK = ("https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/"
               "geojson/ne_50m_admin_0_countries.geojson")
ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"


def exists(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def download(url, path, fallback=None):
    """Fetch url to path. Retries once, then tries fallback. Returns the url used."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for candidate in [url, url, fallback]:
        if candidate is None:
            continue
        try:
            req = urllib.request.Request(candidate, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(path, "wb") as fh:
                fh.write(data)
            print(f"  downloaded {len(data) // 1024} KB from {candidate}")
            return candidate
        except Exception as exc:  # noqa: BLE001 - report and try the next candidate
            print(f"  failed ({exc}): {candidate}")
    raise SystemExit(f"could not download {path} - see PLAN.md section 3 'On failure'")


def round_coords(node, nd=2):
    """Round every coordinate in a nested GeoJSON coordinate array."""
    if isinstance(node, (int, float)):
        return round(node, nd)
    return [round_coords(child, nd) for child in node]


def trim_geojson(src, dst):
    with open(src, encoding="utf-8") as fh:
        gj = json.load(fh)
    features = []
    for feat in gj["features"]:
        props = feat["properties"]
        iso3 = next((props.get(k) for k in ("ISO_A3_EH", "ISO_A3", "ADM0_A3")
                     if props.get(k) and props.get(k) != "-99"), None)
        if iso3 == "ATA" or not iso3:
            continue
        features.append({
            "type": "Feature",
            "properties": {"iso3": iso3, "name": props.get("NAME")},
            "geometry": {"type": feat["geometry"]["type"],
                         "coordinates": round_coords(feat["geometry"]["coordinates"])},
        })
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": features}, fh,
                  separators=(",", ":"))
    print(f"  wrote {len(features)} features, {os.path.getsize(dst) // 1024} KB")


README = """# Lookups

External reference data, downloaded once by `fetch_lookups.py` and committed so
that `build_data.py` runs offline and GitHub Pages can serve the site without a
build step.

| File | Source | Retrieved | Version | Licence |
|---|---|---|---|---|
| `onet30_task_statements.txt` | <{onet}> | {date} | O*NET 30.0 Database | CC BY 4.0, U.S. Department of Labor / Employment and Training Administration |
| `../site/data/world.geojson` | <{ne}> | {date} | Natural Earth 50m admin-0 countries | Public domain (CC0) |
| `../site/vendor/echarts.min.js` | <{echarts}> | {date} | Apache ECharts 5.6.0 (UMD) | Apache-2.0 |

`world.geojson` is a trimmed derivative: properties reduced to `iso3` and `name`,
coordinates rounded to two decimal places, and the Antarctica feature dropped.
"""


def main():
    print("O*NET 30.0 task statements")
    onet = os.path.join(LOOKUPS, "onet30_task_statements.txt")
    onet_url = ONET_URL
    if exists(onet):
        print("  present, skipping")
    else:
        onet_url = download(ONET_URL, onet, ONET_FALLBACK)

    print("Natural Earth 50m countries")
    world = os.path.join(SITE_DATA, "world.geojson")
    ne_url = NE_URL
    if exists(world):
        print("  present, skipping")
    else:
        raw = os.path.join(CACHE, "ne_50m.geojson")
        if not exists(raw):
            ne_url = download(NE_URL, raw, NE_FALLBACK)
        trim_geojson(raw, world)

    print("ECharts 5.6.0")
    echarts = os.path.join(VENDOR, "echarts.min.js")
    if exists(echarts):
        print("  present, skipping")
    else:
        download(ECHARTS_URL, echarts)

    with open(os.path.join(LOOKUPS, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(README.format(onet=onet_url, ne=ne_url, echarts=ECHARTS_URL,
                               date="2026-09-15"))
    print("done")


if __name__ == "__main__":
    sys.exit(main())
