const path = require('path');
const { chromium } = require(path.join(process.env.APPDATA, 'npm', 'node_modules', 'playwright-core'));
const EXE = path.join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium-1234', 'chrome-win64', 'chrome.exe');
(async () => {
  const b = await chromium.launch({ executablePath: EXE });
  const p = await b.newPage({ viewport: { width: 1600, height: 1200 } });
  for (const [name, url] of [['time', '?occ=15-1251'], ['geo', '?screen=geo&geo=UKR'], ['compare', '?screen=compare']]) {
    await p.goto('http://localhost:8765/' + url, { waitUntil: 'networkidle' });
    await p.waitForTimeout(1500);
    await p.screenshot({ path: path.join(process.argv[2], name + '.png'), fullPage: true });
  }
  await b.close();
})();
