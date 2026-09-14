// Screen 3 - "Geography": where Claude is used, and how intensely relative to
// the working-age population. The source toggle is hidden here: the Enterprise
// API file is published globally only.

import * as data from '../lib/data.js';
import { state, setState, index, why } from '../app.js';
import { download } from '../lib/csv.js';
import { baseOption, axisPlain, axisValue, render as draw, C, rankColor }
  from '../lib/charts.js';
import { pct, num, humanise, esc, chip } from '../lib/format.js';

const METRICS = [
  ['usage_per_capita_index', 'Usage per capita', v => num(v, 2)],
  ['usage_pct', 'Share of global usage', v => pct(v)],
  ['collaboration_bucket_automation_pct', 'Automation share', v => pct(v, 1)],
  ['use_case_coursework_pct', 'Coursework share', v => pct(v, 1)],
];

// 1.0 is a bucket edge on purpose: it reads as "usage proportional to the
// working-age population". The palette allows one hue, so the meaning comes
// from that edge and its legend label, not from a second colour.
const INDEX_BUCKETS = [0, 0.5, 1.0, 2.0, 4.0];
const RAMP = [C.inert, C.cyan, C.blueGrey, C.blue, '#2A4E6B'];

let world = null, countries = null, subs = null;

const g = (o, k) => (o && k in o ? o[k] : null);
const fmt = key => (METRICS.find(m => m[0] === key) || [, , v => num(v, 2)])[2];

export async function render(host) {
  host.innerHTML = `
    <div class="seg small" id="metricSeg" role="group" aria-label="Map metric">
      ${METRICS.map(([k, label]) =>
        `<button data-metric="${k}" aria-pressed="${k === state.mapMetric}">${label}</button>`
      ).join('')}
    </div>
    <div class="row two" style="margin-top:20px;grid-template-columns:1.7fr 1fr">
      <div class="card" id="mapCard"></div>
      <div class="card" id="rankCard"></div>
    </div>
    <div class="row two">
      <div class="card" id="useCard"></div>
      <div class="card" id="subCard"></div>
    </div>
    <div class="row one" style="justify-items:end">
      <button id="csv" style="all:unset;cursor:pointer;font-size:14px;color:#5F5F5F">
        Download this screen as CSV</button>
    </div>`;

  host.querySelector('#metricSeg').addEventListener('click', e => {
    const b = e.target.closest('[data-metric]');
    if (b) setState({ mapMetric: b.dataset.metric });
  });
  host.querySelector('#csv').onclick = () => exportCsv();

  if (!world) [world, countries, subs] = await Promise.all(
    [data.world(), data.countries(), data.subregions()]);
  if (!echarts.getMap('world')) echarts.registerMap('world', world, {});

  const rows = countries.countries.map(c => ({
    iso3: c.iso3, name: c.name, m: c.m[state.month] || {},
  }));
  paintMap(host, rows);
  paintRanks(host, rows);
  paintUseCases(host, rows);
  paintSubregions(host);
}

function paintMap(host, rows) {
  const key = state.mapMetric;
  const values = rows.map(r => g(r.m, key)).filter(v => v !== null);
  const max = Math.max(...values, 1);
  const bounds = key === 'usage_per_capita_index'
    ? INDEX_BUCKETS
    : [0, max * 0.2, max * 0.4, max * 0.6, max * 0.8];
  const digits = key === 'usage_per_capita_index' ? 1 : 2;
  const pieces = bounds.map((lo, i) => {
    const hi = i + 1 < bounds.length ? bounds[i + 1] : undefined;
    let text = hi === undefined ? `${lo.toFixed(digits)} and over`
      : `${lo.toFixed(digits)} to ${hi.toFixed(digits)}`;
    if (key === 'usage_per_capita_index' && i === 2) text += '  (1.0 = proportional)';
    return { gte: lo, lt: hi, color: RAMP[i], label: text };
  }).reverse();

  const sel = rows.find(r => r.iso3 === state.geo);
  const selValue = sel ? g(sel.m, key) : null;
  const rank = sel && selValue !== null
    ? rows.filter(r => (g(r.m, key) ?? -Infinity) > selValue).length + 1 : null;

  host.querySelector('#mapCard').innerHTML = `
    <h2>${esc(label(key))} by country ${why(key)}</h2>
    <div class="chart map" id="map"></div>
    <p class="callout"><span class="big">${selValue === null ? chip() : fmt(key)(selValue)}</span>
      ${esc(sel ? sel.name : state.geo)}${rank ? ` &mdash; rank ${rank} of ${rows.length}` : ''}</p>`;

  draw(host.querySelector('#map'), Object.assign(baseOption(), {
    tooltip: {
      trigger: 'item',
      formatter: p => `${esc(p.name)}<br>${esc(label(key))}: ` +
        (p.value === undefined || Number.isNaN(p.value) ? 'not published' : fmt(key)(p.value)),
    },
    visualMap: {
      type: 'piecewise', pieces, left: 8, bottom: 8, itemWidth: 14, itemHeight: 12,
      textStyle: { color: C.muted, fontSize: 13 },
    },
    series: [{
      type: 'map', map: 'world', nameProperty: 'iso3', roam: false,
      emphasis: { label: { show: false }, itemStyle: { areaColor: C.highlight } },
      select: { label: { show: false }, itemStyle: { areaColor: C.highlight } },
      selectedMode: 'single',
      itemStyle: { areaColor: C.inert, borderColor: '#FFFFFF', borderWidth: 0.5 },
      data: rows.map(r => ({
        name: r.iso3, value: g(r.m, key) ?? undefined,
        selected: r.iso3 === state.geo,
      })),
    }],
  })).off('click').on('click', p => {
    if (p.name) setState({ geo: p.name });
  });
}

function label(key) {
  const m = METRICS.find(x => x[0] === key);
  return m ? m[1] : humanise(key);
}

function paintRanks(host, rows) {
  const key = state.mapMetric;
  const sorted = [...rows].filter(r => g(r.m, key) !== null)
    .sort((a, b) => b.m[key] - a.m[key]);
  host.querySelector('#rankCard').innerHTML = `
    <h2>Ranked countries</h2>
    <div class="scroll"><table>
      <thead><tr><th>#</th><th>Country</th><th>${esc(label(key))}</th>
        <th>Usage share</th></tr></thead>
      <tbody>${sorted.map((r, i) => `
        <tr tabindex="0" data-iso="${r.iso3}" class="${r.iso3 === state.geo ? 'sel' : ''}">
          <td>${i + 1}</td><td>${esc(r.name)}</td>
          <td>${fmt(key)(r.m[key])}</td><td>${pct(g(r.m, 'usage_pct'))}</td></tr>`).join('')}
      </tbody></table></div>`;
  const tbody = host.querySelector('#rankCard tbody');
  const pick = e => {
    const tr = e.target.closest('tr[data-iso]');
    if (tr && (e.type === 'click' || e.key === 'Enter')) setState({ geo: tr.dataset.iso });
  };
  tbody.addEventListener('click', pick);
  tbody.addEventListener('keydown', pick);
  const selRow = tbody.querySelector('tr.sel');
  if (selRow) selRow.scrollIntoView({ block: 'center' });
}

function paintUseCases(host, rows) {
  const row = rows.find(r => r.iso3 === state.geo);
  const m = row ? row.m : {};
  const parts = [
    ['Work', g(m, 'use_case_work_pct'), C.blue],
    ['Personal', g(m, 'use_case_personal_pct'), C.blueGrey],
    ['Coursework', g(m, 'use_case_coursework_pct'), C.cyan],
  ];
  const top = Object.entries(m).filter(([k]) => k.startsWith('artifact_')
    && k !== 'artifact_none_pct').sort((a, b) => b[1] - a[1]).slice(0, 8).reverse();
  host.querySelector('#useCard').innerHTML = `
    <h2>What Claude is used for in ${esc(row ? row.name : state.geo)}
      ${why('use_case_work_pct')}</h2>
    <div class="legend">${parts.map(p =>
      `<span><i style="background:${p[2]}"></i>${p[0]}</span>`).join('')}</div>
    <div class="chart" id="useChart" style="height:110px"></div>
    ${top.length ? '<div class="chart" id="artChart"></div>'
      : '<p class="empty">Artifact mix not published for this country.</p>'}`;

  draw(host.querySelector('#useChart'), Object.assign(baseOption(), {
    grid: { left: 8, right: 8, top: 8, bottom: 8, containLabel: true },
    tooltip: { trigger: 'axis', valueFormatter: v => v.toFixed(1) + '%' },
    xAxis: axisPlain({ type: 'value', max: 100, axisLabel: { show: false } }),
    yAxis: axisPlain({ type: 'category', data: [''] }),
    series: parts.map(p => ({ name: p[0], type: 'bar', stack: 'x', barWidth: 40,
      data: [p[1]], itemStyle: { color: p[2] } })),
  }));

  if (!top.length) return;
  draw(host.querySelector('#artChart'), Object.assign(baseOption(), {
    tooltip: { trigger: 'axis', valueFormatter: v => v.toFixed(1) + '%' },
    xAxis: axisValue({ type: 'value', axisLabel: { formatter: '{value}%', color: C.muted } }),
    yAxis: axisPlain({ type: 'category', data: top.map(([k]) => humanise(k)) }),
    series: [{ type: 'bar', barWidth: 24, data: top.map(([, v], i) => ({ value: v,
      itemStyle: { color: rankColor(Math.floor((top.length - 1 - i) / (top.length / 4))) } })) }],
  }));
}

function paintSubregions(host) {
  const card = host.querySelector('#subCard');
  const rows = subs.subregions.filter(s => s.country === state.geo);
  const country = countries.countries.find(c => c.iso3 === state.geo);
  const name = country ? country.name : state.geo;
  if (!rows.length) { card.hidden = true; return; }
  card.hidden = false;
  const total = (subs.usage_pct_published_total[state.geo] || {})[state.month];
  const sorted = [...rows].sort((a, b) =>
    (g(b.m[state.month], 'usage_pct') ?? -1) - (g(a.m[state.month], 'usage_pct') ?? -1));
  card.innerHTML = `
    <h2>Subregions of ${esc(name)} ${why('usage_pct')}</h2>
    <p class="cap">${rows.length} published subregions covering
      ${total === undefined || total === null ? 'an unreported share' : total.toFixed(1) + '%'}
      of the country's usage; the rest did not meet publication thresholds.</p>
    <div class="scroll"><table>
      <thead><tr><th>Subregion</th><th>Share of ${esc(name)}'s Claude usage</th>
        <th>Automation</th><th>Coursework</th></tr></thead>
      <tbody>${sorted.map(s => {
        const m = s.m[state.month] || {};
        return `<tr><td>${esc(s.code)}</td><td>${pct(g(m, 'usage_pct'))}</td>
          <td>${pct(g(m, 'collaboration_bucket_automation_pct'), 1)}</td>
          <td>${pct(g(m, 'use_case_coursework_pct'), 1)}</td></tr>`;
      }).join('')}</tbody></table></div>`;
}

function exportCsv() {
  const rows = [];
  for (const c of countries.countries) {
    for (const [k, v] of Object.entries(c.m[state.month] || {})) {
      rows.push([c.iso3, c.name, state.month, k, v]);
    }
  }
  download(`ai-time-machine_geo_${state.geo}_${state.month}.csv`,
    ['iso3', 'country', 'month', 'metric_id', 'value'], rows);
}
