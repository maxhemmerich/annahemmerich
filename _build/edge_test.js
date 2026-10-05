// Objective test of the one issue that matters for THIS body of work:
// her photographs are taken against a light wall, so on a light page the
// thumbnail edge can vanish. Measure the actual rendered pixels.
'use strict';
const fs = require('fs');
const { chromium } = require('playwright-core');
const { PNG } = require('pngjs');

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME_EXE });
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  await p.goto('http://127.0.0.1:8899/', { waitUntil: 'load' });
  await p.waitForTimeout(600);
  // walk the whole page so every lazy image has actually decoded before we sample
  await p.evaluate(async () => {
    const step = window.innerHeight * 0.8;
    for (let y = 0; y < document.body.scrollHeight; y += step) {
      window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 260));
    }
    window.scrollTo(0, 0);
  });
  await p.waitForTimeout(2500);
  const notLoaded = await p.evaluate(() =>
    [...document.querySelectorAll('.index img')].filter((i) => !i.complete || i.naturalWidth === 0).length);
  console.log('images still not decoded:', notLoaded);

  const rects = await p.evaluate(() =>
    [...document.querySelectorAll('.index figure')].map((f) => {
      const i = f.querySelector('img').getBoundingClientRect();
      const c = f.querySelector('figcaption');
      return {
        title: c.querySelector('b').textContent,
        x: Math.round(i.left), y: Math.round(i.top),
        w: Math.round(i.width), h: Math.round(i.height),
      };
    }));
  const bg = await p.evaluate(() => getComputedStyle(document.body).backgroundColor);
  const buf = await p.screenshot({ fullPage: true });
  const png = PNG.sync.read(buf);
  fs.writeFileSync('D:/Anna Website/.shots/home-full.png', buf);

  const px = (x, y) => {
    const i = (png.width * y + x) << 2;
    return [png.data[i], png.data[i + 1], png.data[i + 2]];
  };
  const mean = (x0, y0, x1, y1) => {
    let r = 0, g = 0, bb = 0, n = 0;
    for (let y = Math.max(0, y0); y < Math.min(png.height, y1); y++)
      for (let x = Math.max(0, x0); x < Math.min(png.width, x1); x++) {
        const c = px(x, y); r += c[0]; g += c[1]; bb += c[2]; n++;
      }
    return n ? [r / n, g / n, bb / n] : [0, 0, 0];
  };
  const lum = (c) => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  const hex = (c) => '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

  console.log('page ground =', bg, '=> sampled outside first tile:', hex(mean(2, rects[0].y + 4, 8, rects[0].y + 20)));
  console.log('');
  console.log('title'.padEnd(26), 'edge-in', '  ground-out', '  dLum', '  verdict');
  const band = 5;
  for (const r of rects) {
    // just inside the top-left corner of the photograph (the wall in her photo)
    const inn = mean(r.x + 3, r.y + 3, r.x + 3 + band, r.y + 3 + band);
    // just outside it (the page)
    const out = mean(Math.max(0, r.x - 8), r.y + 3, Math.max(1, r.x - 2), r.y + 3 + band);
    const d = Math.abs(lum(inn) - lum(out));
    let verdict = 'CLOSE - edge will vanish';
    if (d >= 12) verdict = 'clear';
    else if (d >= 5) verdict = 'thin but visible';
    console.log(
      r.title.slice(0, 25).padEnd(26),
      hex(inn).padEnd(9),
      hex(out).padEnd(11),
      d.toFixed(1).padStart(6),
      '  ' + verdict);
  }

  // sanity: is image content actually rendering? stddev of a painting's area
  const r3 = rects.find((r) => r.title.startsWith('Pear')) || rects[2];
  const m = mean(r3.x + 20, r3.y + 20, r3.x + r3.w - 20, r3.y + r3.h - 20);
  let v = 0, n = 0;
  for (let y = r3.y + 20; y < r3.y + r3.h - 20; y += 3)
    for (let x = r3.x + 20; x < r3.x + r3.w - 20; x += 3) {
      const l = lum(px(x, y)); v += (l - lum(m)) ** 2; n++;
    }
  console.log('\nrendering check on "' + r3.title + '": mean', hex(m), 'stddev', Math.sqrt(v / n).toFixed(1),
    Math.sqrt(v / n) > 15 ? '(image is rendering, lots of tone)' : '(SUSPECT: flat)');

  await b.close();
})();
