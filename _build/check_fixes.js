'use strict';
// Checks the exact things flagged: the name not printed twice on About, the
// body-of-work line only on the index, no duplicated nav item in the footer,
// and her real address in both places it appears.
const { chromium } = require('playwright-core');

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME_EXE });
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  let bad = 0;
  const check = (ok, msg) => { if (!ok) bad++; console.log((ok ? '  ok   ' : '  FAIL ') + msg); };

  for (const route of ['', 'work/pear-juice/', 'cv/', 'about/', '404.html']) {
    // served from the site root (the custom domain is live, so site.base is "");
    // run with a local server on 8899: python -m http.server 8899
    await p.goto('http://127.0.0.1:8899/' + route, { waitUntil: 'load' });
    await p.waitForTimeout(250);
    const m = await p.evaluate(() => {
      const txt = document.body.innerText;
      const name = 'Anna Hemmerich';
      const occurrences = txt.split(name).length - 1;
      return {
        title: document.title,
        h1s: [...document.querySelectorAll('h1')].map((e) => e.textContent.trim()),
        metaLines: document.querySelectorAll('.top__meta').length,
        nav: [...document.querySelectorAll('nav a')].map((a) => a.textContent.trim()),
        footer: [...document.querySelectorAll('.tail > *')].map((e) => e.textContent.trim()),
        nameOccurrences: occurrences,
        hasEmail: txt.includes('annahemmi03@gmail.com'),
        mailtos: [...document.querySelectorAll('a[href^="mailto:"]')].map((a) => a.getAttribute('href')),
      };
    });
    console.log(`\n/${route}   h1=${JSON.stringify(m.h1s)}  "Anna Hemmerich" x${m.nameOccurrences}  metaLines=${m.metaLines}`);
    console.log(`  nav=${JSON.stringify(m.nav)}`);
    console.log(`  footer=${JSON.stringify(m.footer)}`);
    check(m.h1s.length === 1, `exactly one h1`);
    // the work pages use a slimmer header nav; the 404 page carries its links
    // in the body because it can be served at any depth
    const wantNav = route === '404.html' ? 0 : 3;
    check(m.nav.length === wantNav, `nav has ${wantNav} items, no duplicate destination`);
    check(!m.nav.includes('Contact'), `Contact is not a nav item pointing at About`);
    check(m.footer.filter((f) => f === 'List of works').length === 0, `footer does not repeat the nav`);
    const wantMeta = route === '' ? 1 : 0;
    check(m.metaLines === wantMeta, `body-of-work line appears ${wantMeta} time(s) here`);
    if (route === '' || route === 'about/') check(m.nameOccurrences <= 2, `name not printed repeatedly`);
    if (route === 'about/') check(!m.h1s.includes('Anna Hemmerich'), `About h1 is not the name again`);
    if (route === '' || route === 'about/') check(m.hasEmail, `her address is present`);
  }
  await b.close();
  console.log(bad ? `\n${bad} failure(s)` : '\nall flagged issues cleared');
  process.exit(bad ? 1 : 0);
})();
