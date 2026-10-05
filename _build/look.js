'use strict';
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright-core');
const base = process.argv[2], outDir = process.argv[3];
fs.mkdirSync(outDir, { recursive: true });

const SHOTS = [
  ['home-top',    '/',               1500, 1000, null],
  ['home-scroll', '/',               1500, 1000, '.index figure:nth-child(9)'],
  ['work',        '/work/pear-juice/', 1500, 1000, null],
  ['work-tall',   '/work/personal-highway/', 1500, 1000, null],
  ['list',        '/list-of-works/', 1100, 1000, null],
  ['about',       '/about/',         1100, 1000, null],
  ['p-home',      '/',                390, 844, null],
  ['p-work',      '/work/pear-juice/',390, 844, null],
  ['p-list',      '/list-of-works/',  390, 844, null],
];

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_EXE });
  for (const [name, route, w, h, sel] of SHOTS) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.goto(base + route, { waitUntil: 'load' });
    await page.waitForTimeout(500);
    if (sel) {
      const el = await page.$(sel);
      if (el) {
        await el.scrollIntoViewIfNeeded();
        await page.evaluate(() => window.scrollBy(0, -140));
        await page.waitForTimeout(400);
      } else console.log('  !! missing selector ' + sel);
    }
    await page.screenshot({ path: path.join(outDir, name + '.png') });
    await page.close();
  }
  await browser.close();
  console.log('shots ->', outDir);
})();
