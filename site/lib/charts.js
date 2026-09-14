// Stripped-chart defaults from dashboard-style-prompt.md: no borders, no plot
// fill, no axis lines, no vertical gridlines, no data labels, sparse ticks.

export const C = {
  blue: '#3B6E93',
  blueGrey: '#A9C0D2',
  cyan: '#93DCF2',
  inert: '#E0E0E0',
  highlight: '#2F88F7',
  ink: '#2B2B2B',
  muted: '#5F5F5F',
};

export const LADDER = [C.blue, C.blueGrey, C.cyan, C.inert];
export const rankColor = i => LADDER[Math.min(i, LADDER.length - 1)];

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function baseOption() {
  return {
    animation: !reduced,
    textStyle: { fontFamily: '"Segoe UI", Inter, "Source Sans 3", system-ui, sans-serif',
                 color: C.ink, fontSize: 14 },
    grid: { left: 8, right: 16, top: 16, bottom: 8, containLabel: true },
    tooltip: { trigger: 'item' },
  };
}

export const axisPlain = extra => Object.assign({
  axisLine: { show: false },
  axisTick: { show: false },
  splitLine: { show: false },
  axisLabel: { color: C.muted, fontSize: 14 },
}, extra);

// At most one dotted horizontal gridline, at a round value.
export const axisValue = extra => Object.assign(axisPlain({
  splitLine: { show: true, lineStyle: { type: 'dotted', color: C.inert } },
  splitNumber: 2,
}), extra);

const observed = new WeakMap();

export function render(el, option) {
  const chart = echarts.getInstanceByDom(el) || echarts.init(el);
  chart.setOption(option, true);
  if (!observed.has(el)) {
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(el);
    observed.set(el, ro);
  }
  return chart;
}

export function sparkline(el, values) {
  render(el, Object.assign(baseOption(), {
    grid: { left: 0, right: 0, top: 4, bottom: 4 },
    tooltip: { show: false },
    xAxis: { type: 'category', show: true, boundaryGap: false,
             data: values.map((_, i) => i), axisLabel: { show: false },
             axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'value', show: false, scale: true },
    series: [{ type: 'line', data: values, showSymbol: false,
               lineStyle: { width: 2, color: C.blue }, connectNulls: true }],
  }));
}
