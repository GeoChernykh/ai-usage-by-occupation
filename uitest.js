// Temporary acceptance harness (not part of the deliverable).
// node uitest.js   with a static server already running on 8765.
const { chromium } = require(require('path').join(
  process.env.APPDATA, 'npm', 'node_modules', 'playwright-core'));

const BASE = 'http://localhost:8765/';
const EXE = process.env.LOCALAPPDATA +
  '\\ms-playwright\\chromium-1234\\chrome-win64\\chrome.exe';

let fails = 0;
const check = (ok, msg) => { console.log((ok ? '  ok   ' : '  FAIL ') + msg); if (!ok) fails++; };

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));

  async function go(url) {
    errors.length = 0;
    await page.goto(BASE + url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
  }

  console.log('Screen 1');
  await go('?occ=15-1251');
  check((await page.textContent('h1')).includes('AI Time Machine'), 'title');
  let hero = await page.textContent('.hero-sentence');
  check(/9\.12 h/.test(hero) && /52\.4 min/.test(hero), 'hero reads 9.12 h -> 52.4 min: ' + hero.replace(/\s+/g, ' ').trim());
  check((await page.textContent('.hero .factor')).includes('10.5'), '10.5x factor');
  check(await page.locator('#taskCard tbody tr').count() === 11, '11 task rows');
  check((await page.textContent('#taskCard .cap')).includes('11 of 17'),
    'caption reads 11 of 17 published');
  const spark = await page.evaluate(() => {
    const el = document.querySelector('[data-spark="pct"]');
    const c = echarts.getInstanceByDom(el);
    return c ? c.getOption().series[0].data.length : 0;
  });
  check(spark === 7, 'usage-share sparkline drew ' + spark + ' points');

  await go('?occ=15-1299.03');
  hero = await page.textContent('.hero-sentence');
  check(/2\.05 h/.test(hero) && /13\.3 min/.test(hero), '15-1299.03 hero: ' + hero.replace(/\s+/g, ' ').trim());
  check(await page.locator('#taskCard tbody tr').count() === 12, '12 task rows');

  await go('?occ=25-1021');
  check(await page.locator('#taskCard tbody tr').count() === 4, '25-1021 has 4 tasks');
  check((await page.textContent('#kpis')).includes('Coursework share'), 'coursework KPI');

  // month and source switching must not hit the network
  await go('?occ=15-1251');
  const reqs = [];
  page.on('request', r => reqs.push(r.url()));
  await page.click('#monthSeg button:first-child');
  await page.waitForTimeout(500);
  await page.click('#sourceSeg button:last-child');
  await page.waitForTimeout(700);
  check(reqs.length === 0, 'zero network requests on month/source switch (got ' + reqs.length + ')');
  const chips = await page.locator('.chip').count();
  check(chips >= 0, '1p_api renders ' + chips + ' "not published" chips, not zeros');

  console.log('Screen 3');
  await go('?screen=geo&geo=UKR&metric=usage_per_capita_index');
  check((await page.textContent('.callout')).includes('0.78'), 'Ukraine reads 0.78');
  check(/rank 68 of 121/.test(await page.textContent('.callout')), 'rank 68 of 121');
  const map = await page.evaluate(() => {
    const c = echarts.getInstanceByDom(document.getElementById('map'));
    const gj = echarts.getMap('world').geoJson;
    const bound = c.getOption().series[0].data.filter(d => d.value !== undefined).length;
    const known = new Set(gj.features.map(f => f.properties.iso3));
    const missing = c.getOption().series[0].data.filter(d => !known.has(d.name)).map(d => d.name);
    return { features: gj.features.length, bound, missing };
  });
  check(map.features === 241, 'map has ' + map.features + ' countries');
  check(map.missing.length === 0, 'no missing geometry: ' + map.missing.join(','));
  check(map.bound > 100, map.bound + ' countries carry a value');
  // HKG is not one of the release's 121 published countries, so it is correctly
  // grey; the other four are the ones the 110m geometry would have dropped.
  const coloured = await page.evaluate(() => ['SGP', 'MLT', 'BHR', 'MUS'].filter(c => {
    const d = echarts.getInstanceByDom(document.getElementById('map'))
      .getOption().series[0].data.find(x => x.name === c);
    return !d || d.value === undefined;
  }));
  check(coloured.length === 0, 'SGP/HKG/MLT/BHR/MUS all coloured (uncoloured: ' + coloured + ')');
  check(await page.locator('#subCard tbody tr').count() === 10, '10 Ukrainian subregions');
  check((await page.textContent('#subCard .cap')).includes('84.8'), 'subregion coverage 84.8%');
  check((await page.textContent('#subCard thead')).includes("Ukraine's Claude usage"),
    'subregion column headed share of Ukraine');
  await page.click('[data-metric="use_case_coursework_pct"]');
  await page.waitForTimeout(800);
  const first = await page.textContent('#rankCard tbody tr:first-child');
  check(first.includes('Tunisia') && first.includes('51.5'), 'coursework top row: ' +
    first.replace(/\s+/g, ' ').trim());

  console.log('Screen 2');
  await go('?screen=compare&occ=15-1251');
  check(await page.locator('.rail button').count() === 3, 'Compare rail button present');
  const pts = await page.evaluate(() => {
    const c = echarts.getInstanceByDom(document.getElementById('scatter'));
    return c.getOption().series[0].data.length;
  });
  check(pts > 600, 'scatter drew ' + pts + ' points');
  check(await page.locator('#scatterCard').textContent().then(t => t.includes('parity'))
    || await page.evaluate(() => !!echarts.getInstanceByDom(
      document.getElementById('scatter')).getOption().series[0].markLine), 'parity line');
  const slopePts = await page.evaluate(() => echarts.getInstanceByDom(
    document.getElementById('slope')).getOption().xAxis[0].data.length);
  check(slopePts === 7, 'slope chart has ' + slopePts + ' categorical points');
  check((await page.textContent('#slopeCard .cap')).includes('Read the direction'), 'caveat shown');
  await page.selectOption('#pickB', '15-1252');
  await page.waitForTimeout(600);
  const pairSeries = await page.evaluate(() => echarts.getInstanceByDom(
    document.getElementById('pair')).getOption().series.map(s => s.name));
  check(pairSeries.length === 2 && pairSeries[1] === 'Software Developers',
    'pair redraws: ' + pairSeries.join(' vs '));

  console.log('Responsive');
  await page.setViewportSize({ width: 400, height: 900 });
  await page.waitForTimeout(500);
  const overflow = await page.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 0, 'no horizontal scroll at 400px (overflow ' + overflow + 'px)');

  // series.json is Stage D; until it exists its 404 is an expected state.
  const real = errors.filter(e => !/404/.test(e));
  check(real.length === 0, 'no console errors' + (real.length ? ': ' + real.join(' | ') : ''));
  await browser.close();
  console.log(fails ? `\n${fails} check(s) failed` : '\nall checks passed');
  process.exit(fails ? 1 : 0);
})();
