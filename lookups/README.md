# Lookups

External reference data, downloaded once by `fetch_lookups.py` and committed so
that `build_data.py` runs offline and GitHub Pages can serve the site without a
build step.

| File | Source | Retrieved | Version | Licence |
|---|---|---|---|---|
| `onet30_task_statements.txt` | <https://www.onetcenter.org/dl_files/database/db_30_0_text/Task%20Statements.txt> | 2026-09-15 | O*NET 30.0 Database | CC BY 4.0, U.S. Department of Labor / Employment and Training Administration |
| `../site/data/world.geojson` | <https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson> | 2026-09-15 | Natural Earth 50m admin-0 countries | Public domain (CC0) |
| `../site/vendor/echarts.min.js` | <https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js> | 2026-09-15 | Apache ECharts 5.6.0 (UMD) | Apache-2.0 |

`world.geojson` is a trimmed derivative: properties reduced to `iso3` and `name`,
coordinates rounded to two decimal places, and the Antarctica feature dropped.
