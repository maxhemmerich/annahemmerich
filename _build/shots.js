// Render + MEASURE pages of the Anna Hemmerich site, then save screenshots.
// Measurements catch what an eyeball misses; the screenshots then get looked at.
//   node shots.js <baseUrl> <outDir> [tag]
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const CHROME = process.env.CHROME_EXE;
const base = process.argv[2] || 'http://127.0.0.1:8899';
const outDir = process.argv[3] || 'shots';
const tag = process.argv[4] || 'site';

const VIEWPORTS = [
  ['desktop', 1440, 1000],
  ['laptop', 1280, 900],
  ['phone', 390, 844],
];

const ROUTES = ['/', '/work/pear-juice/', '/list-of-works/', '/about/'];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ executablePath: CHROME });
  let bad = 0;

  for (const [label, w, h] of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    const failed = [];
    page.on('requestfailed', (r) => failed.push(r.url() + ' :: ' + (r.failure() || {}).errorText));
    page.on('response', (r) => { if (r.status() >= 400) failed.push(r.status() + ' ' + r.url()); });
    const consoleErrors = [];
    page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message));

    for (const route of ROUTES) {
      await page.goto(base + route, { waitUntil: 'load' });
      await page.waitForTimeout(400);
      const m = await page.evaluate(() => {
        const de = document.documentElement;
        const over = de.scrollWidth - window.innerWidth;
        // find the elements that actually stick out past the viewport
        const offenders = [];
        document.querySelectorAll('body *').forEach((el) => {
          const r = el.getBoundingClientRect();
          if (r.width > 0 && (r.right > window.innerWidth + 1.5 || r.left < -1.5)) {
            offenders.push({
              tag: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : ''),
              left: Math.round(r.left), right: Math.round(r.right),
            });
          }
        });
        const wm = document.querySelector('.wordmark');
        const imgs = [...document.querySelectorAll('img')];
        return {
          docW: de.scrollWidth, vw: window.innerWidth, docH: de.scrollHeight,
          over, offenders: offenders.slice(0, 8),
          wordmark: wm ? { w: Math.round(wm.getBoundingClientRect().width), h: Math.round(wm.getBoundingClientRect().height) } : null,
          imgCount: imgs.length,
          brokenImgs: imgs.filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.currentSrc || i.src),
          font: getComputedStyle(document.body).fontFamily,
          bodyBg: getComputedStyle(document.body).backgroundColor,
        };
      });
      const overFlag = m.over > 1;
      if (overFlag) bad++;
      console.log(
        `${label.padEnd(8)} ${route.padEnd(22)} docW=${String(m.docW).padStart(5)} vw=${String(m.vw).padStart(4)}` +
        ` h=${String(m.docH).padStart(6)}  overflow=${overFlag ? 'YES +' + m.over + 'px' : 'no'}` +
        `  imgs=${m.imgCount} broken=${m.brokenImgs.length}  wordmark=${m.wordmark ? m.wordmark.w + 'x' + m.wordmark.h : '-'}`
      );
      if (m.offenders.length) m.offenders.forEach((o) => console.log(`           offending: ${o.tag} [${o.left} .. ${o.right}]`));
      if (m.brokenImgs.length) m.brokenImgs.slice(0, 5).forEach((u) => console.log(`           broken img: ${u}`));
      await page.screenshot({ path: path.join(outDir, `${tag}-${label}-${route.replace(/[/]/g, '_') || '_root'}.png`), fullPage: label === 'phone' ? false : true });
    }
    if (failed.length) { bad++; console.log(`  ${label}: FAILED REQUESTS\n` + failed.slice(0, 10).map((f) => '    ' + f).join('\n')); }
    if (consoleErrors.length) { console.log(`  ${label}: JS ERRORS\n` + consoleErrors.slice(0, 5).map((f) => '    ' + f).join('\n')); }
    await ctx.close();
  }
  await browser.close();
  console.log(bad ? `\n${bad} problem(s)` : '\nclean at every width');
  process.exit(bad ? 1 : 0);
})();
