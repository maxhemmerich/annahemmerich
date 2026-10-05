'use strict';
const { chromium } = require('playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME_EXE });

  // ---- the list page: do the markers and the titles share a column? ----
  let p = await b.newPage({ viewport: { width: 1100, height: 1000 } });
  await p.goto('http://127.0.0.1:8899/list-of-works/', { waitUntil: 'load' });
  await p.waitForTimeout(300);
  const list = await p.evaluate(() => {
    const items = [...document.querySelectorAll('.olist li')];
    return items.map((li, i) => {
      const a = li.querySelector('a');
      const liR = li.getBoundingClientRect();
      const aR = a.getBoundingClientRect();
      // first character of the title, via a range, so the title's true ink start
      const r = document.createRange();
      r.selectNodeContents(a);
      const first = r.getClientRects()[0];
      const cs = getComputedStyle(li, '::before');
      return {
        n: i + 1,
        liLeft: Math.round(liR.left),
        titleInkLeft: first ? Math.round(first.left) : null,
        liWidth: Math.round(liR.width),
        markerAlign: cs.textAlign,
        markerWidth: Math.round(parseFloat(cs.width) || 0),
        fontSize: getComputedStyle(a).fontSize,
        color: getComputedStyle(li).color,
      };
    });
  });
  const titleStarts = [...new Set(list.map((x) => x.titleInkLeft))];
  console.log('LIST: distinct title start x =', titleStarts, '(1 value means every title lines up)');
  console.log('      marker text-align =', list[0].markerAlign, '| li color =', list[0].color, '| li fs =', list[0].fontSize);
  console.log('      first 3 + 10th:', JSON.stringify(list.filter((x) => [1, 2, 3, 10, 20].includes(x.n))));
  await p.close();

  // ---- home: caption metrics, column count, image separation ----
  p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  await p.goto('http://127.0.0.1:8899/', { waitUntil: 'load' });
  await p.waitForTimeout(500);
  const home = await p.evaluate(() => {
    const caps = [...document.querySelectorAll('.index figcaption')];
    const figs = [...document.querySelectorAll('.index figure')];
    const tops = [...new Set(figs.map((f) => Math.round(f.getBoundingClientRect().top)))];
    const cs = getComputedStyle(caps[0]);
    // how many figures start in the first row-band => column count
    const byTop = {};
    figs.forEach((f) => { const t = Math.round(f.getBoundingClientRect().top); byTop[t] = (byTop[t] || 0) + 1; });
    const firstBand = byTop[Math.min(...Object.keys(byTop).map(Number))];
    // gaps: caption bottom -> next image top, vs image bottom -> caption top
    const f0 = figs[0];
    const img = f0.querySelector('img');
    const figc = f0.querySelector('figcaption');
    return {
      columns: firstBand,
      capFontSize: cs.fontSize, capColor: cs.color, capLineHeight: cs.lineHeight,
      capLines: caps.slice(0, 8).map((c) => Math.round(c.getBoundingClientRect().height / parseFloat(getComputedStyle(c).lineHeight))),
      gapImgToCap: Math.round(figc.getBoundingClientRect().top - img.getBoundingClientRect().bottom),
      figWidth: Math.round(f0.getBoundingClientRect().width),
      bodyBg: getComputedStyle(document.body).backgroundColor,
      backtop: !!document.querySelector('.backtop'),
      topArrow: !!document.querySelector('.top__top'),
    };
  });
  console.log('\nHOME:', JSON.stringify(home, null, 1));
  await p.close();

  // ---- phone ----
  p = await b.newPage({ viewport: { width: 390, height: 844 } });
  await p.goto('http://127.0.0.1:8899/', { waitUntil: 'load' });
  await p.waitForTimeout(400);
  const phone = await p.evaluate(() => {
    const figs = [...document.querySelectorAll('.index figure')];
    const byTop = {};
    figs.forEach((f) => { const t = Math.round(f.getBoundingClientRect().top); byTop[t] = (byTop[t] || 0) + 1; });
    const cap = document.querySelector('.index figcaption');
    const navA = document.querySelector('.top__nav a');
    const nr = navA.getBoundingClientRect();
    return {
      columns: Math.max(...Object.values(byTop)),
      figWidth: Math.round(figs[0].getBoundingClientRect().width),
      capFs: getComputedStyle(cap).fontSize, capColor: getComputedStyle(cap).color,
      navTapH: Math.round(nr.height),
      docH: document.documentElement.scrollHeight,
    };
  });
  console.log('\nPHONE:', JSON.stringify(phone, null, 1));
  await p.close();
  await b.close();
})();
