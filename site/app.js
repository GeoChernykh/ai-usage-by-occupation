// Static data explorer. No backend, no build step. Loads site/data/index.json once,
// then site/data/occ/<soc>.json per occupation selection.

const USAGE_METRIC_ID = "pct"; // see probe_results.md: within this slice the usage
// share lives under metric_id "pct", not "usage_pct" (that only exists at
// category_name="overall"). Kept verbatim from the source, never invented.

const COLLAB_METRICS = [
  "collaboration_directive_pct",
  "collaboration_feedback_loop_pct",
  "collaboration_task_iteration_pct",
  "collaboration_learning_pct",
  "collaboration_validation_pct",
  "collaboration_none_pct",
];

const SOURCE_COMPARE_METRICS = [
  USAGE_METRIC_ID,
  "collaboration_bucket_automation_pct",
  "ai_autonomy_mean",
  "use_case_work_pct",
];

const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };

const SOURCE_LABELS = { claude_ai: "Consumer (Claude apps)", "1p_api": "Enterprise API" };

let indexData = null;
let currentSoc = null;
let currentOccData = null;
let currentSource = "claude_ai";
let currentMonth = "2026-05-01";
const occCache = new Map();

function humanizeArtifact(metricId) {
  let s = metricId.replace(/^artifact_/, "").replace(/_pct$/, "");
  s = s.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function humanizeCollab(metricId) {
  let s = metricId.replace(/^collaboration_/, "").replace(/_pct$/, "");
  s = s.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function metricVal(occData, source, month, metricId) {
  const v = occData?.metrics?.[source]?.[month]?.[metricId];
  return v === undefined ? undefined : v;
}

function chip(val, formatter) {
  if (val === undefined || val === null) {
    return '<span class="not-published">not published</span>';
  }
  return formatter(val);
}

function fmtPct(v) { return v.toFixed(1) + "%"; }
function fmtNum(v) { return v.toFixed(2); }
function fmtMoney(v) { return "$" + Math.round(v).toLocaleString(); }

function deltaHtml(aprVal, mayVal, unit) {
  if (aprVal === undefined || mayVal === undefined) return "";
  const d = mayVal - aprVal;
  if (Math.abs(d) < 1e-9) return '<div class="delta">▬ 0' + unit + ' Apr→May</div>';
  const cls = d > 0 ? "up" : "down";
  const arrow = d > 0 ? "▲" : "▼";
  return `<div class="delta ${cls}">${arrow} ${Math.abs(d).toFixed(1)}${unit} Apr→May</div>`;
}

async function loadIndex() {
  const res = await fetch("data/index.json");
  indexData = await res.json();
}

async function loadOcc(soc) {
  if (occCache.has(soc)) return occCache.get(soc);
  const res = await fetch(`data/occ/${soc}.json`);
  const data = await res.json();
  occCache.set(soc, data);
  return data;
}

function populateSearch() {
  const list = document.getElementById("occ-list");
  list.innerHTML = "";
  for (const occ of indexData.occupations) {
    const opt = document.createElement("option");
    opt.value = `${occ.title} (${occ.soc})`;
    list.appendChild(opt);
  }
}

function socFromSearchText(text) {
  const m = text.match(/\(([^()]+)\)\s*$/);
  if (!m) return null;
  const candidate = m[1];
  const found = indexData.occupations.find((o) => o.soc === candidate);
  return found ? candidate : null;
}

async function selectOccupation(soc, updateUrl = true) {
  const data = await loadOcc(soc);
  currentSoc = soc;
  currentOccData = data;
  document.getElementById("empty-state").hidden = true;
  document.getElementById("panels").hidden = false;
  if (updateUrl) {
    const url = new URL(window.location);
    url.searchParams.set("soc", soc);
    history.replaceState(null, "", url);
  }
  renderAll();
}

function renderAll() {
  if (!currentOccData) return;
  renderKpiRow();
  renderTimeCompression();
  renderAutoAug();
  renderCollab();
  renderArtifactMix();
  renderSourceCompare();
  renderSkillGap();
  renderMajorGroupTrend();
  renderNeighbours();
}

function renderKpiRow() {
  const d = currentOccData;
  const usageApr = metricVal(d, currentSource, "2026-04-01", USAGE_METRIC_ID);
  const usageMay = metricVal(d, currentSource, "2026-05-01", USAGE_METRIC_ID);
  const usageNow = metricVal(d, currentSource, currentMonth, USAGE_METRIC_ID);

  const autoApr = metricVal(d, currentSource, "2026-04-01", "collaboration_bucket_automation_pct");
  const autoMay = metricVal(d, currentSource, "2026-05-01", "collaboration_bucket_automation_pct");
  const augNow = metricVal(d, currentSource, currentMonth, "collaboration_bucket_augmentation_pct");
  const autoNow = metricVal(d, currentSource, currentMonth, "collaboration_bucket_automation_pct");

  const exposure = d.exposure;
  const salary = d.wage?.median_salary;

  const html = `
    <div class="kpi">
      <div class="label">Exposure score</div>
      <div class="value">${chip(exposure, (v) => v.toFixed(3))}</div>
    </div>
    <div class="kpi">
      <div class="label">Usage %</div>
      <div class="value">${chip(usageNow, fmtPct)}</div>
      ${deltaHtml(usageApr, usageMay, "pp")}
    </div>
    <div class="kpi">
      <div class="label">Automation vs augmentation</div>
      <div class="value">${chip(autoNow, fmtPct)} / ${chip(augNow, fmtPct)}</div>
      ${deltaHtml(autoApr, autoMay, "pp")}
    </div>
    <div class="kpi">
      <div class="label">Median salary</div>
      <div class="value">${chip(salary, fmtMoney)}</div>
    </div>
  `;
  document.getElementById("kpi-row").innerHTML = html;
}

function renderTimeCompression() {
  const d = currentOccData;
  const hoursOnly = metricVal(d, currentSource, currentMonth, "human_only_time_mean");
  const minsWithAi = metricVal(d, currentSource, currentMonth, "human_with_ai_time_mean");
  const el = document.getElementById("time-compression");

  const headline = document.createElement("div");
  headline.className = "headline";
  if (hoursOnly === undefined || minsWithAi === undefined) {
    headline.innerHTML = chip(undefined, () => "");
  } else {
    headline.textContent = `Without AI: ${hoursOnly.toFixed(1)} hours. With Claude: ${minsWithAi.toFixed(0)} minutes.`;
  }
  el.innerHTML = "";
  el.appendChild(headline);

  const median = indexData.medians?.[currentSource]?.[currentMonth]?.["human_with_ai_time_mean"];
  if (minsWithAi !== undefined && median !== undefined) {
    const div = document.createElement("div");
    div.id = "time-compare-chart";
    el.appendChild(div);
    Plotly.newPlot(div, [{
      type: "bar", orientation: "h",
      y: ["This occupation", "All-occupation median"],
      x: [minsWithAi, median],
      marker: { color: ["#7aa2f7", "#4b5163"] },
    }], baseLayout({ xaxis: { title: "Minutes with AI" }, height: 160 }), PLOTLY_CONFIG);
  }
}

function renderAutoAug() {
  const d = currentOccData;
  const auto = metricVal(d, currentSource, currentMonth, "collaboration_bucket_automation_pct");
  const aug = metricVal(d, currentSource, currentMonth, "collaboration_bucket_augmentation_pct");
  const div = document.getElementById("auto-aug-chart");
  if (auto === undefined && aug === undefined) {
    div.innerHTML = chip(undefined, () => "");
    return;
  }
  div.innerHTML = "";
  Plotly.newPlot(div, [
    { type: "bar", orientation: "h", y: ["Share"], x: [auto ?? 0], name: "Automation", marker: { color: "#ff7b72" } },
    { type: "bar", orientation: "h", y: ["Share"], x: [aug ?? 0], name: "Augmentation", marker: { color: "#7aa2f7" } },
  ], baseLayout({ barmode: "stack", xaxis: { title: "%" }, height: 160 }), PLOTLY_CONFIG);
}

function renderCollab() {
  const d = currentOccData;
  const vals = COLLAB_METRICS.map((m) => metricVal(d, currentSource, currentMonth, m));
  const div = document.getElementById("collab-chart");
  if (vals.every((v) => v === undefined)) {
    div.innerHTML = chip(undefined, () => "");
    return;
  }
  div.innerHTML = "";
  Plotly.newPlot(div, [{
    type: "bar",
    x: COLLAB_METRICS.map(humanizeCollab),
    y: vals.map((v) => v ?? 0),
    marker: { color: "#7aa2f7" },
  }], baseLayout({ yaxis: { title: "%" }, height: 260 }), PLOTLY_CONFIG);
}

function renderArtifactMix() {
  const d = currentOccData;
  const metrics = d.metrics?.[currentSource]?.[currentMonth] ?? {};
  const artifactEntries = Object.entries(metrics).filter(([k]) => k.startsWith("artifact_"));
  const div = document.getElementById("artifact-chart");
  if (artifactEntries.length === 0) {
    div.innerHTML = chip(undefined, () => "");
    return;
  }
  artifactEntries.sort((a, b) => b[1] - a[1]);
  const top8 = artifactEntries.slice(0, 8).reverse();
  div.innerHTML = "";
  Plotly.newPlot(div, [{
    type: "bar", orientation: "h",
    x: top8.map(([, v]) => v),
    y: top8.map(([k]) => humanizeArtifact(k)),
    marker: { color: "#7aa2f7" },
  }], baseLayout({ xaxis: { title: "%" }, height: 320 }), PLOTLY_CONFIG);
}

function renderSourceCompare() {
  const d = currentOccData;
  const div = document.getElementById("source-compare-chart");
  const claudeVals = SOURCE_COMPARE_METRICS.map((m) => metricVal(d, "claude_ai", currentMonth, m));
  const apiVals = SOURCE_COMPARE_METRICS.map((m) => metricVal(d, "1p_api", currentMonth, m));
  if (claudeVals.every((v) => v === undefined) && apiVals.every((v) => v === undefined)) {
    div.innerHTML = chip(undefined, () => "");
    return;
  }
  const niceLabels = ["Usage %", "Automation %", "AI autonomy (mean)", "Work use case %"];
  div.innerHTML = "";
  Plotly.newPlot(div, [
    { type: "bar", orientation: "h", y: niceLabels, x: claudeVals.map((v) => v ?? 0), name: SOURCE_LABELS.claude_ai, marker: { color: "#7aa2f7" } },
    { type: "bar", orientation: "h", y: niceLabels, x: apiVals.map((v) => -(v ?? 0)), name: SOURCE_LABELS["1p_api"], marker: { color: "#ff7b72" } },
  ], baseLayout({ barmode: "overlay", height: 260 }), PLOTLY_CONFIG);
}

function renderSkillGap() {
  const d = currentOccData;
  const humanEdu = metricVal(d, currentSource, currentMonth, "human_education_years_mean");
  const aiEdu = metricVal(d, currentSource, currentMonth, "ai_education_years_mean");
  const humanAbility = metricVal(d, currentSource, currentMonth, "human_only_ability_pct");
  const aiAutonomy = metricVal(d, currentSource, currentMonth, "ai_autonomy_mean");
  const el = document.getElementById("skill-gap");
  el.innerHTML = `
    <div class="readouts">
      <p>Human-only ability score: ${chip(humanAbility, fmtPct)}</p>
      <p>AI autonomy (mean): ${chip(aiAutonomy, fmtNum)}</p>
    </div>
    <div id="skill-gap-chart"></div>
  `;
  if (humanEdu !== undefined || aiEdu !== undefined) {
    Plotly.newPlot(document.getElementById("skill-gap-chart"), [{
      type: "bar",
      x: ["Human education (years)", "AI education (years)"],
      y: [humanEdu ?? 0, aiEdu ?? 0],
      marker: { color: ["#7aa2f7", "#ff7b72"] },
    }], baseLayout({ height: 220 }), PLOTLY_CONFIG);
  }
}

const PERIOD_MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function formatPeriod(dateStr) {
  const [y, m] = dateStr.split("-");
  return `${PERIOD_MONTH_NAMES[parseInt(m, 10) - 1]} ${y}`;
}

function renderMajorGroupTrend() {
  const panel = document.getElementById("major-group-trend-panel");
  const div = document.getElementById("major-group-trend-chart");
  const jobFamily = currentOccData.wage?.job_family;
  const trend = jobFamily ? indexData.major_group_trend?.[jobFamily] : undefined;
  if (!trend) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  const periods = Object.keys(trend).sort();
  div.innerHTML = "";
  Plotly.newPlot(div, [{
    type: "scatter", mode: "lines+markers",
    x: periods.map(formatPeriod),
    y: periods.map((p) => trend[p]),
    marker: { color: "#7aa2f7" }, line: { color: "#7aa2f7" },
  }], baseLayout({ yaxis: { title: "% of category usage" }, height: 220, margin: { l: 60, r: 20, t: 10, b: 40 } }), PLOTLY_CONFIG);
}

function renderNeighbours() {
  const panel = document.getElementById("neighbours-panel");
  const tbody = document.querySelector("#neighbours-table tbody");
  const neighbours = currentOccData.neighbours;
  if (!neighbours || neighbours.length === 0) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  tbody.innerHTML = neighbours.map((n) => `
    <tr>
      <td>${n.title}</td>
      <td>${fmtPct(n.automation_pct)}</td>
      <td>${fmtMoney(n.salary)}</td>
    </tr>
  `).join("");
}

function baseLayout(overrides) {
  return Object.assign({
    autosize: true,
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#e7e9ee" },
    margin: { l: 140, r: 20, t: 10, b: 30 },
    showlegend: false,
    height: 200,
  }, overrides);
}

function downloadCsv() {
  if (!currentOccData) return;
  const rows = [["source", "month", "metric_id", "value"]];
  for (const source of indexData.sources) {
    for (const month of indexData.months) {
      const m = currentOccData.metrics?.[source]?.[month] ?? {};
      for (const [metricId, value] of Object.entries(m)) {
        rows.push([source, month, metricId, value]);
      }
    }
  }
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${currentSoc}_metrics.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function wireControls() {
  document.querySelectorAll("#source-toggle .toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#source-toggle .toggle").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentSource = btn.dataset.source;
      renderAll();
    });
  });
  document.getElementById("month-toggle").addEventListener("click", (e) => {
    const btn = e.target.closest(".toggle");
    if (!btn) return;
    document.querySelectorAll("#month-toggle .toggle").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentMonth = btn.dataset.month;
    renderAll();
  });

  const search = document.getElementById("occ-search");
  search.addEventListener("change", () => {
    const soc = socFromSearchText(search.value);
    if (soc) selectOccupation(soc);
  });

  document.getElementById("download-csv").addEventListener("click", downloadCsv);
}

function populatePeriodToggle() {
  const container = document.getElementById("month-toggle");
  container.innerHTML = "";
  currentMonth = indexData.months[indexData.months.length - 1];
  for (const month of indexData.months) {
    const btn = document.createElement("button");
    btn.className = "toggle" + (month === currentMonth ? " active" : "");
    btn.dataset.month = month;
    btn.textContent = formatPeriod(month);
    container.appendChild(btn);
  }
}

async function init() {
  await loadIndex();
  populateSearch();
  populatePeriodToggle();
  wireControls();
  const params = new URLSearchParams(window.location.search);
  const socParam = params.get("soc");
  if (socParam && indexData.occupations.some((o) => o.soc === socParam)) {
    const occ = indexData.occupations.find((o) => o.soc === socParam);
    document.getElementById("occ-search").value = `${occ.title} (${occ.soc})`;
    await selectOccupation(socParam, false);
  }
}

init();
