# annahemmerich.com

Anna Hemmerich's painting portfolio. A static site, no build step at deploy
time — GitHub Pages serves the repository root directly.

    index.html            the index of all twenty works
    work/<slug>/          one page per work
    list-of-works/        the numbered list, as in the portfolio document
    about/                about the work, and contact
    404.html
    assets/art/           the paintings, webp + jpeg, at 900 and 1600
    assets/css/site.css   the whole design
    _build/               generators and the design research (not served)

## Design

The design is taken from the seven reference sites Anna sent (flatfix,
erlendpederkvam, cameronplatter, tareklakhrissi, hughfrost, zartnan,
ailsaogden — all Cargo). Read together they share one house style, and the site
follows it rather than inventing anything:

- **white ground.** No tint, no texture, near enough to plain white.
  `_build/refs/report.md` records what each reference actually declares.
- **one neutral grotesque at small sizes.** Cargo's own scale is used —
  14.5 / 12 / 11.5px. Regular weight. Nothing is bold-display.
- **no interface chrome at all.** No bars, cards, boxes, borders, shadows or
  radii. Across all seven references the only glyphs that appear are an up
  arrow and a return mark.
- **photographs flush to the page edge**, in tight masonry columns.
- **a text-only nav**, sitting in a line under the name.
- **captions** set in the portfolio document's own format —
  *Title, medium, height × width in, year* — under each image.

The one place the site departs from the references: the page ground is
`#f4f3f0` rather than `#ffffff`. Anna's paintings are photographed against a
light wall and several are near-white canvases, so on pure white the
photographs lose their edge entirely. Measured, every one of the twenty now
sits 16–67 ΔLuminance clear of the page. See `_build/edge_test.js`.

## Adding or changing work

1. Edit `_build/works.json` — it is the only content file.
   Each entry needs `slug`, `title`, `medium`, `dims`, `year`, `n`.
2. Drop the photograph into `assets/art/` and run `_build/make_images.py`
   (it reads from a source folder; adjust `SRC` at the top).
3. Run `_build/bake_accents.py` to record each image's pixel dimensions, then
   `_build/build.py` to regenerate every page, the sitemap, and the CNAME.

## Tools

    python _build/build.py          regenerate all pages from works.json
    python _build/bake_accents.py   record intrinsic image sizes
    python _build/make_images.py    build webp/jpeg derivatives at 900 and 1600
    python _build/make_og.py        build the social card
    python _build/read_refs.py      re-fetch the reference sites' own CSS
    node   _build/shots.js          measure every page at three widths
    node   _build/edge_test.js      measure image-to-ground separation
    node   _build/look.js           capture viewport screenshots to check by eye

`shots.js` fails the run on any horizontal overflow at 1440, 1280 or 390.

## A direction that was tried and abandoned

`_build/crop.py` auto-detects the painting's bounds inside each photograph and
crops the wall away. It got 18 of 20 right. It was dropped anyway: several of
these paintings contain large pale passages that are the same colour as the
wall behind them, so a colour-based detector cannot tell them apart, and the
follow-up trim pass (`_build/trim_wall.py`) started cutting into the canvases.
The detection is not separable by colour on this body of work. The photographs
are used whole, as they are in the portfolio document.

## Deploying

Live now at **https://maxhemmerich.github.io/annahemmerich/** — Pages serves
`main` at the repo root, no build step.

The custom domain is **not** connected yet. `CNAME` is parked at
`_build/CNAME.for-domain` on purpose: with it in the published tree GitHub
adopts `annahemmerich.com` and 301s the github.io URL there, and that domain
still resolves to an unused Shopify store, so nothing would be reachable at all.

To switch it over, both halves in one go:

1. At the domain's DNS panel, replace the current records —

   | type | name | value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | maxhemmerich.github.io |

   The records to remove are an A record pointing at `23.227.38.65` and a
   `www` CNAME pointing at `shops.myshopify.com` — both are Shopify's. The
   domain has **no MX records**, so no mail depends on them.

2. `cp _build/CNAME.for-domain CNAME`, set `site.base` to `""` in
   `_build/works.json`, re-run `python _build/build.py`, commit and push.
   GitHub then issues the TLS certificate, which takes a few minutes.

## Not yet done

- The contact address is a placeholder and nothing sends from it.
- There is no biography. The About page describes the work from the work
  itself; a paragraph in Anna's own words is still needed.
- Set `site.base` back to `/annahemmerich` if the custom domain is ever dropped.
