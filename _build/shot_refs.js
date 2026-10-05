'use strict';
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright-core');
const CHROME = process.env.CHROME_EXE;
const outDir = process.argv[2] || 'D:/Anna Website/_build/refs/shots';
fs.mkdirSync(outDir, { recursive: true });

const SITES = [
  ['flatfix',         'https://flatfix.biz/'],
  ['erlendpederkvam', 'https://erlendpederkvam.com/'],
  ['cameronplatter',  'https://cameronplatter.com/HOME-2'],
  ['tareklakhrissi',  'https://tareklakhrissi.com/'],
  ['hughfrost',       'https://hughfrost.net/'],
  ['zartnan',         'https://zartnan.com/menu'],
  ['ailsaogden',      'https://ailsaogden.studio/'],
];

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  for (const [name, url] of SITES) {
    for (const [vp, w, h] of [['desk', 1440, 1000], ['phone', 390, 844]]) {
      const ctx = await browser.newContext({
        viewport: { width: w, height: h },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      });
      const page = await ctx.newPage();
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(2500);
        // scroll through to trigger lazy loads, then back to top
        await page.evaluate(async () => {
          const step = window.innerHeight * 0.9;
          for (let y = 0; y < document.body.scrollHeight; y += step) {
            window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 220));
          }
          window.scrollTo(0, 0);
        });
        await page.waitForTimeout(1800);
        const info = await page.evaluate(() => {
          const b = getComputedStyle(document.body);
          return {
            bg: b.backgroundColor, color: b.color, font: b.fontFamily.slice(0, 70),
            size: b.fontSize,
            docH: document.documentElement.scrollHeight,
            nImg: document.querySelectorAll('img').length,
            nBg: [...document.querySelectorAll('*')].filter((e) => getComputedStyle(e).backgroundImage !== 'none').length,
            title: document.title,
          };
        });
        await page.screenshot({ path: path.join(outDir, `${name}-${vp}-top.png`) });
        await page.evaluate(() => window.scrollTo(0, Math.round(window.innerHeight * 1.15)));
        await page.waitForTimeout(900);
        await page.screenshot({ path: path.join(outDir, `${name}-${vp}-mid.png`) });
        console.log(`${name.padEnd(17)} ${vp.padEnd(6)} bg=${info.bg} color=${info.color} size=${info.size} h=${info.docH} img=${info.nImg} bgimg=${info.nBg} font=${info.font}`);
      } catch (e) {
        console.log(`${name.padEnd(17)} ${vp.padEnd(6)} FAILED: ${String(e.message).slice(0, 110)}`);
      }
      await ctx.close();
    }
  }
  await browser.close();
  console.log('\nshots -> ' + outDir);
})();
