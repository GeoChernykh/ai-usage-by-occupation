// Screen 1 - "Time card": what the work of one occupation costs with and
// without Claude, and which of its O*NET tasks show up in Claude usage.

import * as data from '../lib/data.js';
import { state, setState, index, why } from '../app.js';
import { match } from '../lib/search.js';
import { download } from '../lib/csv.js';
import { baseOption, axisPlain, axisValue, render as draw, sparkline, C, rankColor }
  from '../lib/charts.js';
import { pct, num, factor, hours, minutes, monthLabel, humanise, esc, chip }
  from '../lib/format.js';

let taskIndex = null;      // tasks.json, loaded on first search keystroke
let seriesData;
let scrollToTask = null;

const KPIS = [
  ['Usage share', 'pct', v => pct(v)],
  ['Autonomy', 'ai_autonomy_mean', v => num(v, 1) + (v === null ? '' : ' / 5')],
  ['Automation share', 'collaboration_bucket_automation_pct', v => pct(v, 1)],
  ['Coursework share', 'use_case_coursework_pct', v => pct(v, 1)],
];

const g = (obj, key) => (obj && key in obj ? obj[key] : null);

export async function render(host) {
  const occ = index.occupations.find(o => o.soc === state.soc);
  host.innerHTML = `
    <div class="search">
      <input id="q" type="search" autocomplete="off" placeholder="Search occupations and tasks"
        aria-label="Search occupations and tasks" aria-expanded="false">
      <div class="results" id="results" hidden role="listbox"></div>
    </div>
    <div class="row kpi" id="kpis"></div>
    <div class="row one"><div class="card" id="heroCard"></div></div>
    <div class="row one"><div class="card" id="taskCard"></div></div>
    <div class="row two">
      <div class="card" id="collabCard"></div>
      <div class="card" id="artifactCard"></div>
    </div>
    <div class="row one" style="justify-items:end">
      <button class="seg" id="csv" style="all:unset;cursor:pointer;font-size:14px;color:#5F5F5F">
        Download this screen as CSV</button>
    </div>`;
  wireSearch(host);
  host.querySelector('#csv').onclick = () => exportCsv();

  const doc = await data.occupation(state.soc);
  if (state.soc !== doc.soc) return;
  paint(host, doc, occ);
}

// ---------- search ----------

function wireSearch(host) {
  const input = host.querySelector('#q');
  const box = host.querySelector('#results');
  let items = [];
  let sel = -1;

  const close = () => { box.hidden = true; input.setAttribute('aria-expanded', 'false'); };

  async function run() {
    const q = input.value;
    if (!taskIndex && q.trim().length >= 2) taskIndex = await data.tasks();
    const occs = match(index.occupations, o => o.title, q);
    const tks = taskIndex ? match(taskIndex, t => t.text, q) : [];
    items = [...occs.map(o => ({ kind: 'occ', row: o })),
             ...tks.map(t => ({ kind: 'task', row: t }))];
    sel = -1;
    if (!items.length) return close();
    let html = '';
    if (occs.length) html += '<div class="grp">Occupations</div>' + occs.map((o, i) =>
      `<div class="item" data-i="${i}" role="option">${esc(o.title)}
        <span class="sub">${pct(o.pct)}</span></div>`).join('');
    if (tks.length) html += '<div class="grp">Tasks</div>' + tks.map((t, i) =>
      `<div class="item" data-i="${occs.length + i}" role="option">${esc(t.text)}
        <span class="sub">${esc(t.occ_title || 'no occupation mapped')}</span></div>`).join('');
    box.innerHTML = html;
    box.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  function choose(i) {
    const it = items[i];
    if (!it) return;
    close();
    input.value = '';
    if (it.kind === 'occ') setState({ soc: it.row.soc });
    else if (it.row.soc) { scrollToTask = it.row.id; setState({ soc: it.row.soc }); }
  }

  input.addEventListener('input', run);
  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') return close();
    if (e.key === 'Enter') return choose(sel < 0 ? 0 : sel);
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    e.preventDefault();
    sel = Math.max(0, Math.min(items.length - 1, sel + (e.key === 'ArrowDown' ? 1 : -1)));
    box.querySelectorAll('.item').forEach(el =>
      el.classList.toggle('sel', Number(el.dataset.i) === sel));
  });
  box.addEventListener('click', e => {
    const el = e.target.closest('.item');
    if (el) choose(Number(el.dataset.i));
  });
}

// ---------- painting ----------

function paint(host, doc, occ) {
  const m = g(doc.metrics[state.source], state.month) || {};
  const d = g(doc.derived[state.source], state.month) || {};
  const other = index.months.find(x => x !== state.month);
  const prev = g(doc.metrics[state.source], other) || {};
  const med = g(index.medians[state.source], state.month) || {};

  host.querySelector('#kpis').innerHTML = KPIS.map(([label, key, fmt]) => `
    <div class="card kpi-card">
      <div class="label">${label} ${why(key)}</div>
      <div class="value">${key in m ? fmt(m[key]) : chip()}</div>
      <div class="prev">${key in prev
        ? monthLabel(other) + ': ' + fmt(prev[key]) : ''}</div>
      <div class="spark" data-spark="${key}"></div>
    </div>`).join('');
  paintSparkline(host);

  paintHero(host, doc, m, d, med);
  paintTasks(host, doc);
  paintCollaboration(host, m);
  paintArtifacts(host, m);
}

async function paintSparkline(host) {
  const el = host.querySelector('[data-spark="pct"]');
  if (!el) return;
  if (seriesData === undefined) seriesData = await data.series();
  const pts = seriesData && seriesData.occupations[state.soc];
  if (!pts || pts.filter(v => v !== null).length < 3) return;
  sparkline(el, pts);
}

function paintHero(host, doc, m, d, med) {
  const unaided = 'human_only_time_mean' in m ? m.human_only_time_mean * 60 : null;
  const assisted = g(m, 'human_with_ai_time_mean');
  const medUnaided = 'human_only_time_mean' in med ? med.human_only_time_mean * 60 : null;
  host.querySelector('#heroCard').innerHTML = `
    <h2>Time compression &mdash; ${esc(doc.title)} ${why('human_only_time_mean')}</h2>
    <div class="hero">
      <div class="chart short" id="heroChart"></div>
      <div class="factor">${factor(g(d, 'speedup'))}<small>faster with Claude</small></div>
    </div>
    <p class="hero-sentence">Work Claude is asked to do for this occupation takes
      <b>${hours(g(m, 'human_only_time_mean'))}</b> unaided and
      <b>${minutes(assisted)}</b> with Claude.</p>`;

  const rows = [
    ['Median occupation, unaided', medUnaided, C.inert],
    ['With Claude', assisted, C.blueGrey],
    ['Unaided', unaided, C.blue],
  ];
  draw(host.querySelector('#heroChart'), Object.assign(baseOption(), {
    grid: { left: 8, right: 60, top: 8, bottom: 8, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'none' },
               valueFormatter: v => Math.round(v) + ' min' },
    xAxis: axisPlain({ type: 'value', name: '' }),
    yAxis: axisPlain({ type: 'category', data: rows.map(r => r[0]) }),
    series: [{
      type: 'bar', barWidth: 24,
      data: rows.map(r => ({ value: r[1], itemStyle: { color: r[2] } })),
    }],
  }));
}

function paintTasks(host, doc) {
  const card = host.querySelector('#taskCard');
  const total = index.occupations.find(o => o.soc === doc.soc);
  const head = `<h2>Tasks behind this occupation ${why('human_only_time_mean')}</h2>
    <p class="cap">O*NET tasks behind this occupation that appear in Claude usage &mdash;
      <b>${doc.tasks.length} of ${total && total.n_onet ? total.n_onet : doc.tasks.length}</b> published;
      the rest did not meet publication thresholds.</p>`;
  if (!doc.tasks.length) {
    card.innerHTML = head + `<p class="empty">No O*NET task for this occupation met
      Anthropic's publication thresholds in this release.</p>`;
    return;
  }
  const rows = doc.tasks.map(t => {
    const m = t.m[state.month] || {};
    const saved = 'human_only_time_mean' in m && 'human_with_ai_time_mean' in m
      ? m.human_only_time_mean - m.human_with_ai_time_mean / 60 : null;
    const sp = saved !== null ? m.human_only_time_mean * 60 / m.human_with_ai_time_mean : null;
    return { t, m, saved, sp };
  });
  const maxSaved = Math.max(...rows.map(r => r.saved || 0), 0.01);
  card.innerHTML = head + `<div class="scroll"><table>
    <thead><tr><th>Task</th><th>Unaided</th><th>With Claude</th><th>Saved</th>
      <th>Speed-up</th><th>Share</th><th></th></tr></thead>
    <tbody>${rows.map((r, i) => `<tr id="task-${esc(r.t.id)}">
      <td class="trunc" title="${esc(r.t.text)}">${esc(r.t.text)}</td>
      <td>${hours(g(r.m, 'human_only_time_mean'))}</td>
      <td>${minutes(g(r.m, 'human_with_ai_time_mean'))}</td>
      <td>${hours(r.saved)}</td>
      <td>${factor(r.sp)}</td>
      <td>${pct(g(r.m, 'pct'))}</td>
      <td class="bar"><div style="width:${Math.max(0, (r.saved || 0) / maxSaved * 100)}%;
        background:${rankColor(Math.floor(i / Math.max(1, rows.length / 4)))}"></div></td>
    </tr>`).join('')}</tbody></table></div>`;

  if (scrollToTask) {
    const el = card.querySelector('#task-' + CSS.escape(scrollToTask));
    if (el) { el.classList.add('sel'); el.scrollIntoView({ block: 'center' }); }
    scrollToTask = null;
  }
}

function paintCollaboration(host, m) {
  const card = host.querySelector('#collabCard');
  const a = g(m, 'collaboration_bucket_automation_pct');
  const b = g(m, 'collaboration_bucket_augmentation_pct');
  card.innerHTML = `<h2>Automation and augmentation
      ${why('collaboration_bucket_automation_pct')}</h2>
    <div class="legend"><span><i style="background:${C.blue}"></i>Automation</span>
      <span><i style="background:${C.blueGrey}"></i>Augmentation</span></div>
    <div class="chart" id="collabChart" style="height:110px"></div>
    <p class="cap">${a === null ? 'not published'
      : pct(a, 1) + ' automation, ' + pct(b, 1) + ' augmentation'}</p>`;
  if (a === null && b === null) return;
  draw(card.querySelector('#collabChart'), Object.assign(baseOption(), {
    grid: { left: 8, right: 8, top: 40, bottom: 8, containLabel: true },
    tooltip: { trigger: 'axis', valueFormatter: v => v.toFixed(1) + '%' },
    xAxis: axisPlain({ type: 'value', max: 100, axisLabel: { show: false } }),
    yAxis: axisPlain({ type: 'category', data: [''] }),
    series: [
      { name: 'Automation', type: 'bar', stack: 'x', barWidth: 40,
        data: [a], itemStyle: { color: C.blue } },
      { name: 'Augmentation', type: 'bar', stack: 'x', barWidth: 40,
        data: [b], itemStyle: { color: C.blueGrey } },
    ],
  }));
}

function topArtifacts(m, n = 8) {
  return Object.entries(m)
    .filter(([k]) => k.startsWith('artifact_') && k !== 'artifact_none_pct')
    .sort((x, y) => y[1] - x[1]).slice(0, n);
}

function paintArtifacts(host, m) {
  const card = host.querySelector('#artifactCard');
  const top = topArtifacts(m);
  card.innerHTML = `<h2>What Claude actually produces for this job ${why('artifact_x_pct')}</h2>
    ${top.length ? '<div class="chart" id="artChart"></div>'
      : '<p class="empty">Not published for this occupation.</p>'}`;
  if (!top.length) return;
  const asc = [...top].reverse();
  draw(card.querySelector('#artChart'), Object.assign(baseOption(), {
    tooltip: { trigger: 'axis', valueFormatter: v => v.toFixed(1) + '%' },
    xAxis: axisPlain({ type: 'value', axisLabel: { formatter: '{value}%', color: C.muted } }),
    yAxis: axisPlain({ type: 'category', data: asc.map(([k]) => humanise(k)) }),
    series: [{ type: 'bar', barWidth: 24,
      data: asc.map(([, v], i) => ({ value: v,
        itemStyle: { color: rankColor(Math.floor((asc.length - 1 - i) / (asc.length / 4))) } })) }],
  }));
}

// ---------- CSV ----------

async function exportCsv() {
  const doc = await data.occupation(state.soc);
  const rows = [];
  for (const source of index.sources) {
    for (const month of index.months) {
      for (const [k, v] of Object.entries(doc.metrics[source][month] || {})) {
        rows.push(['occupation', doc.soc, doc.title, source, month, k, v]);
      }
    }
  }
  for (const t of doc.tasks) {
    for (const [month, m] of Object.entries(t.m)) {
      for (const [k, v] of Object.entries(m)) {
        rows.push(['task', t.id, t.text, 'claude_ai', month, k, v]);
      }
    }
  }
  download(`ai-time-machine_time_${state.soc}_${state.month}.csv`,
    ['level', 'id', 'name', 'source', 'month', 'metric_id', 'value'], rows);
}
