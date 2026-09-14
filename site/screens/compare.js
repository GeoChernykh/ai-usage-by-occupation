// Screen 2 - "Compare": where Claude sits against the human entry bar, one
// occupation against another, and how a share moved across releases. Only
// reachable when series.json exists; app.js feature-detects it.

import * as data from '../lib/data.js';
import { state, setState, index, why } from '../app.js';
import { download } from '../lib/csv.js';
import { baseOption, axisPlain, axisValue, render as draw, C } from '../lib/charts.js';
import { pct, num, esc } from '../lib/format.js';

let series = null;

const BARS = [
  ['pct', 'Usage share (%)'],
  ['human_only_time_mean', 'Unaided (h)'],
  ['human_with_ai_time_mean', 'With Claude (min)'],
  ['speedup', 'Speed-up (x)'],
  ['ai_autonomy_mean', 'Autonomy (0-5)'],
  ['collaboration_bucket_automation_pct', 'Automation (%)'],
  ['use_case_coursework_pct', 'Coursework (%)'],
];

const METHOD_SENTENCE = {
  id: 'The current release joins tasks to occupations by O*NET Task ID; earlier releases, ' +
      'which publish no task ids, by task text',
  text: 'Every release joins tasks to occupations by task text, so all points use one method',
};

const g = (o, k) => (o && k in o ? o[k] : null);

export async function render(host) {
  if (!series) series = await data.series();
  const a = state.compareA || state.soc;
  const b = state.compareB || pickOther(a);
  host.innerHTML = `
    <div class="row one"><div class="card" id="scatterCard"></div></div>
    <div class="row one"><div class="card" id="pairCard"></div></div>
    <div class="row one"><div class="card" id="slopeCard"></div></div>
    <div class="row one" style="justify-items:end">
      <button id="csv" style="all:unset;cursor:pointer;font-size:14px;color:#5F5F5F">
        Download this screen as CSV</button>
    </div>`;
  host.querySelector('#csv').onclick = () => exportCsv(a, b);
  paintScatter(host);
  paintPair(host, a, b);
  await paintSlope(host);
}

function pickOther(a) {
  const alt = index.occupations.find(o => o.soc !== a && o.pct);
  return alt ? alt.soc : a;
}

function paintScatter(host) {
  const rows = index.occupations.filter(o =>
    o.hum_edu !== undefined && o.ai_edu !== undefined);
  const size = o => Math.max(4, Math.min(40, Math.sqrt(o.pct || 0) * 14));
  const maxEdu = Math.max(...rows.flatMap(o => [o.hum_edu, o.ai_edu]), 1);
  host.querySelector('#scatterCard').innerHTML = `
    <h2>Claude against the human entry bar ${why('ai_autonomy_mean')}</h2>
    <p class="cap">Years of education. Points above the parity line are occupations where
      Claude operates above the education level the job usually asks of a person.</p>
    <div class="chart" id="scatter" style="height:420px"></div>`;
  draw(host.querySelector('#scatter'), Object.assign(baseOption(), {
    tooltip: { trigger: 'item', formatter: p =>
      `${esc(p.data.title)}<br>Human: ${num(p.data.value[0], 1)} y<br>` +
      `Claude: ${num(p.data.value[1], 1)} y<br>Usage share: ${pct(p.data.pct)}` },
    xAxis: axisValue({ type: 'value', name: 'Human education (years)',
      nameLocation: 'middle', nameGap: 30, nameTextStyle: { color: C.muted } }),
    yAxis: axisValue({ type: 'value', name: 'Claude education (years)',
      nameLocation: 'middle', nameGap: 36, nameTextStyle: { color: C.muted } }),
    series: [{
      type: 'scatter',
      data: rows.map(o => ({
        value: [o.hum_edu, o.ai_edu], title: o.title, soc: o.soc, pct: o.pct,
        symbolSize: size(o),
        itemStyle: { color: o.soc === state.soc ? C.highlight : C.blueGrey,
                     opacity: o.soc === state.soc ? 1 : 0.6 },
      })),
      markLine: {
        silent: true, symbol: 'none',
        label: { formatter: 'parity', color: C.muted, position: 'end' },
        lineStyle: { color: C.inert, type: 'solid' },
        data: [[{ coord: [0, 0] }, { coord: [maxEdu, maxEdu] }]],
      },
    }],
  })).off('click').on('click', p => {
    if (p.data && p.data.soc) setState({ soc: p.data.soc, compareA: p.data.soc });
  });
}

function picker(id, value) {
  return `<select id="${id}" style="font:inherit;padding:6px 8px;border:0;border-radius:6px;
    background:#EDEDEE;color:#2B2B2B;max-width:100%">
    ${index.occupations.map(o =>
      `<option value="${o.soc}" ${o.soc === value ? 'selected' : ''}>${esc(o.title)}</option>`
    ).join('')}</select>`;
}

async function paintPair(host, a, b) {
  const card = host.querySelector('#pairCard');
  card.innerHTML = `
    <h2>Two occupations side by side</h2>
    <div class="legend" style="justify-content:center;gap:24px">
      <span><i style="background:${C.blue}"></i>${picker('pickA', a)}</span>
      <span><i style="background:${C.blueGrey}"></i>${picker('pickB', b)}</span>
    </div>
    <div class="chart" id="pair" style="height:360px"></div>`;
  card.querySelector('#pickA').onchange = e =>
    setState({ compareA: e.target.value, soc: e.target.value });
  card.querySelector('#pickB').onchange = e => setState({ compareB: e.target.value });

  const [da, db] = await Promise.all([data.occupation(a), data.occupation(b)]);
  const val = (doc, key) => {
    const m = g(doc.metrics[state.source], state.month) || {};
    const d = g(doc.derived[state.source], state.month) || {};
    return key === 'speedup' ? g(d, 'speedup') : g(m, key);
  };
  const labels = BARS.map(x => x[1]).reverse();
  const pull = doc => BARS.map(x => val(doc, x[0])).reverse();
  draw(card.querySelector('#pair'), Object.assign(baseOption(), {
    tooltip: { trigger: 'axis' },
    xAxis: axisValue({ type: 'value' }),
    yAxis: axisPlain({ type: 'category', data: labels }),
    series: [
      { name: da.title, type: 'bar', barWidth: 12, data: pull(da),
        itemStyle: { color: C.blue } },
      { name: db.title, type: 'bar', barWidth: 12, data: pull(db),
        itemStyle: { color: C.blueGrey } },
    ],
  }));
}

async function paintSlope(host) {
  const card = host.querySelector('#slopeCard');
  const pts = series.points;
  const values = series.occupations[state.soc] || pts.map(() => null);
  const occ = index.occupations.find(o => o.soc === state.soc);
  card.innerHTML = `
    <h2>${esc(occ ? occ.title : state.soc)} across releases</h2>
    <div class="chart" id="slope"></div>
    <p class="cap" style="text-align:left;line-height:1.55">
      Each release re-clusters usage into its own O*NET task set (2,618&ndash;3,514 tasks) and is
      published as a discrete snapshot, not a continuous series. Shares are renormalised over the
      tasks that map to an occupation in that release (67&ndash;91% of usage). Read the direction,
      not the precise level. ${esc(METHOD_SENTENCE[series.method] || '')}.</p>`;
  draw(card.querySelector('#slope'), Object.assign(baseOption(), {
    tooltip: { trigger: 'axis', valueFormatter: v => (v === null ? 'not published'
      : v.toFixed(2) + '%') },
    xAxis: axisPlain({ type: 'category', data: pts.map(p => p.label),
      axisLabel: { color: C.muted, interval: Math.max(1, Math.floor(pts.length / 5) - 1) } }),
    yAxis: axisValue({ type: 'value', axisLabel: { formatter: '{value}%', color: C.muted } }),
    series: [{ type: 'line', data: values, connectNulls: false,
      symbolSize: 7, lineStyle: { width: 2, color: C.blue },
      itemStyle: { color: C.blue } }],
  }));
}

async function exportCsv(a, b) {
  const [da, db] = await Promise.all([data.occupation(a), data.occupation(b)]);
  const rows = [];
  for (const doc of [da, db]) {
    for (const [key] of BARS) {
      const m = g(doc.metrics[state.source], state.month) || {};
      const d = g(doc.derived[state.source], state.month) || {};
      rows.push([doc.soc, doc.title, state.source, state.month, key,
                 key === 'speedup' ? g(d, 'speedup') : g(m, key)]);
    }
  }
  download(`ai-time-machine_compare_${a}_${state.month}.csv`,
    ['soc', 'title', 'source', 'month', 'metric_id', 'value'], rows);
}
