// Verify the LIVE site, not the local copy: every route, at phone and desktop,
// checking that CSS, fonts and images actually arrive.
'use strict';
const { chromium } = require('playwright-core');
const BASE = process.argv[2];
const W = [
  ['desk', 1440, 1000],
  ['phone', 390, 844],
];
const ROUTES = ['/', '/work/pear-juice/', '/work/tennis/', '/list-of-works/', '/about/', '/404.html',
                '/nope-does-not-exist/'];

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME_EXE });
  let problems = 0;
  for (const [vp, w, h] of W) {
    const ctx = await b.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    const failed = [];
    page.on('requestfailed', (r) => failed.push('FAILED ' + r.url()));
    page.on('response', (r) => { if (r.status() >= 400 && !r.url().endsWith('/nope-does-not-exist/')) failed.push(r.status() + ' ' + r.url()); });
    for (const route of ROUTES) {
      const resp = await page.goto(BASE + route, { waitUntil: 'load', timeout: 40000 });
      await page.waitForTimeout(700);
      const m = await page.evaluate(() => {
        const de = document.documentElement;
        const imgs = [...document.querySelectorAll('img')];
        const cs = getComputedStyle(document.body);
        return {
          title: document.title,
          status: null,
          docW: de.scrollWidth, vw: window.innerWidth, over: de.scrollWidth - window.innerWidth,
          font: cs.fontFamily.split(',')[0].replace(/"/g, ''),
          size: cs.fontSize,
          bg: cs.backgroundColor,
          nImg: imgs.length,
          broken: imgs.filter((i) => i.complete && i.naturalWidth === 0).length,
          loaded: imgs.filter((i) => i.naturalWidth > 0).length,
          firstImgNatural: imgs[0] ? [imgs[0].naturalWidth, imgs[0].naturalHeight] : null,
          h1: (document.querySelector('h1') || {}).textContent,
        };
      });
      const over = m.over > 1;
      if (over) problems++;
      console.log(`${vp.padEnd(6)} ${String(resp.status()).padEnd(4)} ${route.padEnd(24)} ` +
        `docW=${String(m.docW).padStart(5)} vw=${String(m.vw).padStart(4)} over=${over ? 'YES +' + m.over : 'no '}` +
        ` imgs=${m.loaded}/${m.nImg} broken=${m.broken} font=${m.font} ${m.size} bg=${m.bg}` +
        `${m.firstImgNatural ? ' img0=' + m.firstImgNatural.join('x') : ''}`);
      console.log(`       title="${m.title}" h1="${m.h1}"`);
    }
    if (failed.length) { problems++; console.log('  NETWORK PROBLEMS:\n' + failed.slice(0, 8).map((f) => '    ' + f).join('\n')); }
    await ctx.close();
  }
  await b.close();
  console.log(problems ? `\n${problems} problem(s)` : '\nLIVE SITE CLEAN');
})();
