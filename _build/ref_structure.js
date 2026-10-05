'use strict'
// Records the two structural facts the README claims about the references,
// off the sites themselves: the page set (their own nav) and the number of
// columns their work grids run at 1440 and 390.
//
// Needs playwright-core and CHROME_EXE, like shots.js and shot_refs.js:
//     CHROME_EXE="C:/Program Files/Google/Chrome/Application/chrome.exe" \
//       node _build/ref_structure.js
const { chromium } = require('playwright-core');

const CHROME = process.env.CHROME_EXE;
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

// the page of each site that shows the most work
const SITES = [
  ['flatfix',         'https://flatfix.biz/All-Paintings'],
  ['erlendpederkvam', 'https://erlendpederkvam.com/drawings'],
  ['cameronplatter',  'https://cameronplatter.com/Drawing'],
  ['tareklakhrissi',  'https://tareklakhrissi.com/Works'],
  ['hughfrost',       'https://hughfrost.net/projects'],
  ['zartnan',         'https://zartnan.com/years'],
  ['ailsaogden',      'https://ailsaogden.studio/'],
];

const probe = () => {
  const nav = [...document.querySelectorAll('nav a, header a')]
    .map((a) => a.textContent.trim().replace(/\s+/g, ' '))
    .filter((t) => t && t.length < 24);
  const imgs = [...document.querySelectorAll('img')].map((i) => {
    const r = i.getBoundingClientRect();
    return { l: Math.round(r.left), t: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) };
  }).filter((i) => i.w > 80 && i.h > 80);
  let cols = null;
  if (imgs.length) {
    const rows = {};
    for (const i of imgs) { const k = Math.round(i.t / 150) * 150; (rows[k] = rows[k] || new Set()).add(i.l); }
    cols = Math.max(...Object.values(rows).map((s) => s.size));
  }
  const textIndex = !imgs.length && /(19|20)\d\d/.test(document.body.innerText);
  return { nav: [...new Set(nav)].slice(0, 10).join(' | '), cols, nImgs: imgs.length,
           pageType: imgs.length ? 'grid' : (textIndex ? 'text index' : 'no work shown') };
};

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  for (const [name, url] of SITES) {
    const out = [];
    for (const w of [1440, 390]) {
      const ctx = await browser.newContext({ viewport: { width: w, height: 1000 }, userAgent: UA });
      const p = await ctx.newPage();
      try {
        await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await p.waitForTimeout(2500);
        await p.evaluate(async () => {
          const s = innerHeight * 0.9;
          for (let y = 0; y < document.body.scrollHeight; y += s) { scrollTo(0, y); await new Promise((r) => setTimeout(r, 200)); }
          scrollTo(0, 0);
        });
        await p.waitForTimeout(2500);
        const m = await p.evaluate(probe);
        out.push({ w, ...m });
      } catch (e) { out.push({ w, error: String(e.message).slice(0, 60) }); }
      await ctx.close();
    }
    const d = out[0], m = out[1];
    console.log(`${name.padEnd(16)} ${String(d.cols).padStart(4)} cols @1440  ${String(m.cols).padStart(4)} @390  ${d.pageType.padEnd(11)} nav: ${d.nav}`);
  }
  await browser.close();
})();
