// Entry point: the single state object, URL sync, the rail and the header.

import * as data from './lib/data.js';
import { SOURCE_LABEL, monthLabel, esc } from './lib/format.js';
import * as time from './screens/time.js';
import * as geo from './screens/geo.js';
import * as compare from './screens/compare.js';

export const state = {
  screen: 'time',
  soc: '15-1251',
  source: 'claude_ai',
  month: '2026-05-01',
  geo: 'UKR',
  mapMetric: 'usage_per_capita_index',
  compareA: null,
  compareB: null,
};

export let index = null;

const SCREENS = { time, compare, geo };

const ICONS = {
  time: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  compare: '<svg viewBox="0 0 24 24"><path d="M4 19V9m6 10V5m6 14v-7m-12 7h16"/></svg>',
  geo: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 2.5 15.3 0 18-2.5-2.7-2.5-15.3 0-18z"/></svg>',
};

const TITLES = { time: 'AI Time Machine', compare: 'Compare', geo: 'Geography' };

// ---------- URL state ----------

function readUrl() {
  const p = new URLSearchParams(location.search);
  const set = (key, param, valid) => {
    const v = p.get(param);
    if (v && (!valid || valid(v))) state[key] = v;
  };
  set('screen', 'screen', v => v in SCREENS);
  set('soc', 'occ');
  set('soc', 'soc');                       // v0.2 links used ?soc=
  set('source', 'src', v => v in SOURCE_LABEL);
  set('month', 'month', v => index.months.includes(v));
  set('geo', 'geo');
  set('mapMetric', 'metric');
  if (!index.occupations.some(o => o.soc === state.soc)) state.soc = '15-1251';
  if (!index.occupations.some(o => o.soc === state.soc)) state.soc = index.occupations[0].soc;
}

function writeUrl() {
  const p = new URLSearchParams({
    screen: state.screen, occ: state.soc, src: state.source,
    month: state.month, geo: state.geo, metric: state.mapMetric,
  });
  history.replaceState(null, '', '?' + p);
}

// ---------- rendering ----------

let available = ['time', 'geo'];

export function setState(patch) {
  Object.assign(state, patch);
  writeUrl();
  render();
}

function renderRail() {
  document.getElementById('rail').innerHTML = available.map(k =>
    `<button data-screen="${k}" aria-current="${k === state.screen}" title="${TITLES[k]}"
      aria-label="${TITLES[k]}">${ICONS[k]}</button>`).join('');
}

function renderHeader() {
  document.getElementById('title').textContent = TITLES[state.screen];
  document.getElementById('monthSeg').innerHTML = index.months.map(m =>
    `<button data-month="${m}" aria-pressed="${m === state.month}">${monthLabel(m)}</button>`
  ).join('');
  const srcSeg = document.getElementById('sourceSeg');
  srcSeg.hidden = state.screen === 'geo';   // 1p_api is published globally only
  srcSeg.innerHTML = index.sources.map(s =>
    `<button data-source="${s}" aria-pressed="${s === state.source}">${SOURCE_LABEL[s]}</button>`
  ).join('');
}

function render() {
  renderRail();
  renderHeader();
  const host = document.getElementById('screen');
  SCREENS[state.screen].render(host);
}

// ---------- methodology popover ----------

const METHOD = {
  pct: ['pct', 'percent of this geography’s Claude usage',
        'Shares are shares of Claude usage, never of the economy.'],
  usage_pct: ['usage_pct', 'percent of global Claude usage', ''],
  usage_per_capita_index: ['usage_per_capita_index', 'index, 1.0 = proportional to working-age population', ''],
  ai_autonomy_mean: ['ai_autonomy_mean', 'mean score, 0–5', ''],
  collaboration_bucket_automation_pct: ['collaboration_bucket_automation_pct', 'percent of this node’s conversations', ''],
  use_case_coursework_pct: ['use_case_coursework_pct', 'percent of this node’s conversations', ''],
  use_case_work_pct: ['use_case_work_pct', 'percent of this node’s conversations', ''],
  human_only_time_mean: ['human_only_time_mean', 'hours, unaided',
    'A model estimate of how long the task would take without Claude, not a stopwatch measurement.'],
  human_with_ai_time_mean: ['human_with_ai_time_mean', 'minutes, with Claude',
    'A model estimate of how long the task takes with Claude, not a stopwatch measurement.'],
  artifact: ['artifact_*_pct', 'percent of this node’s conversations', ''],
};

export function why(metric) {
  const m = METHOD[metric] || METHOD[metric.startsWith('artifact_') ? 'artifact' : 'pct'];
  return `<button class="why" data-why="${esc(m[0])}|${esc(m[1])}|${esc(m[2])}"
    aria-label="How this is measured">?</button>`;
}

function popover(btn) {
  const pop = document.getElementById('pop');
  const [id, unit, note] = btn.dataset.why.split('|');
  pop.innerHTML = `<code>${esc(id)}</code><br>Unit: ${esc(unit)}<br>
    Source: <code>aei_${state.source}_2026-06-26.csv</code>, Anthropic Economic Index
    release 26.06.2026.${note ? '<br><br>' + esc(note) : ''}`;
  const r = btn.getBoundingClientRect();
  pop.hidden = false;
  pop.style.top = Math.min(r.bottom + 8, window.innerHeight - pop.offsetHeight - 12) + 'px';
  pop.style.left = Math.min(r.left, window.innerWidth - pop.offsetWidth - 12) + 'px';
}

// ---------- boot ----------

document.addEventListener('click', e => {
  const b = e.target.closest('button');
  const pop = document.getElementById('pop');
  if (!b || !b.dataset.why) pop.hidden = true;
  if (!b) return;
  if (b.dataset.screen) setState({ screen: b.dataset.screen });
  else if (b.dataset.month) setState({ month: b.dataset.month });
  else if (b.dataset.source) setState({ source: b.dataset.source });
  else if (b.dataset.why) popover(b);
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.getElementById('pop').hidden = true;
});

(async function boot() {
  index = await data.index();
  state.month = index.months[index.months.length - 1];
  readUrl();
  state.compareA = state.compareA || state.soc;
  // Feature-detect the Compare screen: Stage D may not have run.
  if (await data.series()) available = ['time', 'compare', 'geo'];
  else if (state.screen === 'compare') state.screen = 'time';
  writeUrl();
  render();
})();
