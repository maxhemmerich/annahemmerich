#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build annahemmerich.com — a static site, GitHub Pages ready.

    python _build/build.py

Design source: the seven reference sites Anna sent (all Cargo), read for their
shared house style — white ground, one small neutral grotesque, no interface
chrome, photographs bleeding to the page edge, a text-only nav. The portfolio
PDF's own caption format is kept verbatim.

URLs are RELATIVE, computed from each page's depth. A GitHub Pages project site
is served from a subpath (/annahemmerich/...), and a root-absolute href like
/assets/css/site.css then points outside the site. That failure is silent in a
local preview served from / — it cost a live deploy with no stylesheet.
Absolute URLs are used only in <link rel="canonical">, og:url, the sitemap and
robots.txt, where they are meant to name the real domain.

Content source of truth: _build/works.json
"""
import json, os, datetime, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "_build", "works.json"), encoding="utf-8") as f:
    DATA = json.load(f)

S = DATA["site"]
WORKS = DATA["works"]
DOMAIN = S["domain"]
BASE = f"https://{DOMAIN}"
# Where the site is served from right now. '/annahemmerich' on the Pages
# project URL, '' once the custom domain is live. Only the 404 page needs it,
# because a 404 can be hit at any depth, so relative links are not safe there.
PROJECT_BASE = S.get("base", "")
NOW = datetime.date.today().isoformat()
YEAR = datetime.date.today().year

# ---------------------------------------------------------------- content ---
META_LINE = ("Painting \u2014 acrylic, oil, collage and cut wood on canvas, panel "
             "and board. Twenty works, 2025\u20132026.")

ABOUT = [
    "Painting in acrylic, oil and collage, on canvas, panel and cut wood.",
    "Each painting starts from a drawn structure \u2014 a net, a fence, a grid, a "
    "scaffold. Then the surface is covered over: flat blocks of paint, pasted "
    "paper, sawn pieces of wood, and outlines laid on last and left to wobble. "
    "The drawing underneath stays half visible.",
    "The palette is mixed to stay saturated and mostly unmixed \u2014 chartreuse, "
    "vermilion, cobalt, ochre, hot pink. The structure holds the picture together "
    "while everything else is stacked on top of it.",
    "Titles point somewhere \u2014 <em>Tennis</em>, <em>Huckleberry bush</em>, "
    "<em>Garbage Collector</em> \u2014 and the painting rarely follows all the way.",
]
BIO = S.get("bio", "").strip()
EMAIL = S.get("email", "").strip()
MEDIA = ["Acrylic", "Oil", "Collage", "Cut wood", "Canvas", "Panel", "Board"]


def esc(s):
    return html.escape(str(s), quote=True)


def cap(w):
    """Her portfolio document's caption line, exactly."""
    return f"{w['title']}, {w['medium']}, {w['dims']}, {w['year']}"


def caption_html(w):
    """The same line, with the title held back in the ink colour."""
    return (f'<b>{esc(w["title"])}</b>, {esc(w["medium"])}, '
            f'{esc(w["dims"])}, {w["year"]}')


def R(prefix, path):
    """A URL to a site-root-relative path, relative to a page at `prefix`."""
    return prefix + path.lstrip("/")


# ------------------------------------------------------------------ shell ---
NAV = [("Work", ""), ("List of works", "list-of-works/"), ("About", "about/")]


def navlinks(prefix, current, links=None):
    out = []
    for label, href in (links or NAV):
        cur = ' aria-current="page"' if (href == current and "#" not in href) else ""
        target = R(prefix, href) if href else (prefix or "./")
        out.append(f'<a href="{target}"{cur}>{esc(label)}</a>')
    return "".join(out)


def nav(prefix, current, cls="top__nav", links=None):
    return (f'<nav class="{cls}" aria-label="Sections">'
            f'{navlinks(prefix, current, links)}</nav>')


def head(title, desc, path, prefix, extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta name="theme-color" content="#f4f3f0">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(S['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:image" content="{BASE}/assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}/assets/og.jpg">
<link rel="icon" href="{R(prefix, 'favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{R(prefix, 'assets/css/site.css')}">
{extra}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def top(prefix, current, as_h1=False, meta=False):
    """The one header. The name, then a line of links.

    The line describing the body of work is passed only by the index. Repeated
    on every page it reads as boilerplate, and on the work and about pages it
    says something the page itself already says."""
    name = f'<a href="{prefix or "./"}">{esc(S["name"])}</a>'
    tag = "h1" if as_h1 else "p"
    meta_html = f'\n  <p class="top__meta">{esc(META_LINE)}</p>' if meta else ""
    return f"""<header class="top" id="top">
  <{tag} class="name">{name}</{tag}>{meta_html}
  {nav(prefix, current)}
</header>
"""


def tail(prefix):
    """The footer carries the one thing the nav does not: a way to write to her."""
    return f"""<footer class="tail">
  <span>&copy; {YEAR} {esc(S['name'])}</span>
  <span>All works remain the property of the artist</span>
  <span><a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a></span>
</footer>
"""


def picture(w, prefix, sizes, loading="lazy"):
    """webp + jpeg, intrinsic size, no layout shift."""
    w_attr, h_attr = (w.get("px1600") or [1600, 1200])
    art = R(prefix, "assets/art/")
    return (
        f'<picture>'
        f'<source type="image/webp" sizes="{sizes}" '
        f'srcset="{art}{w["slug"]}-900.webp 900w, {art}{w["slug"]}-1600.webp 1600w">'
        f'<img src="{art}{w["slug"]}-900.jpg" sizes="{sizes}" '
        f'srcset="{art}{w["slug"]}-900.jpg 900w, {art}{w["slug"]}-1600.jpg 1600w" '
        f'width="{w_attr}" height="{h_attr}" alt="{esc(cap(w))}" '
        f'loading="{loading}" decoding="async">'
        f'</picture>')


# ------------------------------------------------------------------- home ---
def build_home(prefix=""):
    figs = []
    for w in WORKS:
        href = R(prefix, f"work/{w['slug']}/")
        figs.append(
            f'    <figure>\n'
            f'      <a href="{href}">{picture(w, prefix, "(max-width:699px) 48vw, (max-width:1079px) 32vw, (max-width:1779px) 24vw, 19vw")}</a>\n'
            f'      <figcaption><a href="{href}">{caption_html(w)}</a></figcaption>\n'
            f'    </figure>')

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{S['name']} \u2014 Work",
        "url": f"{BASE}/",
        "about": {"@type": "Person", "name": S["name"], "jobTitle": "Painter"},
        "hasPart": [{
            "@type": "VisualArtwork", "name": w["title"], "artMedium": w["medium"],
            "dateCreated": str(w["year"]), "url": f"{BASE}/work/{w['slug']}/",
            "image": f"{BASE}/assets/art/{w['slug']}-1600.jpg",
        } for w in WORKS],
    }, ensure_ascii=False)

    body = f"""<main id="main">
  <div class="index">
{chr(10).join(figs)}
  </div>
  <p class="backtop"><a href="#top">Back to top &#8593;</a></p>
</main>
"""
    title = f"{S['name']} \u2014 Painting"
    desc = ("Paintings by Anna Hemmerich \u2014 acrylic, oil and collage on canvas, "
            "panel and cut wood. Twenty works, 2025\u20132026.")
    return (head(title, desc, "/", prefix,
                 f'<script type="application/ld+json">{ld}</script>\n')
            + top(prefix, "", as_h1=True, meta=True) + body + tail(prefix))


# ------------------------------------------------------------- work pages ---
def build_work(idx, prefix="../../"):
    w = WORKS[idx]
    prev = WORKS[idx - 1] if idx > 0 else WORKS[-1]
    nxt = WORKS[(idx + 1) % len(WORKS)]

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": w["title"],
        "creator": {"@type": "Person", "name": S["name"]},
        "artMedium": w["medium"],
        "artform": "Painting",
        "dateCreated": str(w["year"]),
        "image": f"{BASE}/assets/art/{w['slug']}-1600.jpg",
        "url": f"{BASE}/work/{w['slug']}/",
        "isPartOf": {"@type": "CollectionPage", "name": f"{S['name']} \u2014 Work", "url": f"{BASE}/"},
    }, ensure_ascii=False)

    links = [("Work", ""), ("List of works", "list-of-works/"), ("About", "about/")]
    body = f"""<main id="main" class="sheet">
  <div class="sheet__head">
    <p class="name"><a href="{prefix or "./"}">{esc(S['name'])}</a></p>
    <nav class="sheet__nav" aria-label="Sections">{navlinks(prefix, "", links)}</nav>
  </div>

  <div class="sheet__body">
    <a href="{R(prefix, f"assets/art/{w['slug']}-1600.jpg")}">{picture(w, prefix, '(max-width:1100px) 92vw, 78vw', loading='eager')}</a>
    <h1 class="sheet__cap">{caption_html(w)}</h1>
  </div>

  <div class="sheet__foot">
    <a href="{R(prefix, f"work/{prev['slug']}/")}">&#8592; {esc(prev['title'])}</a>
    <span>{w['n']} of {len(WORKS)}</span>
    <a href="{R(prefix, f"work/{nxt['slug']}/")}">{esc(nxt['title'])} &#8594;</a>
  </div>
</main>
"""
    return (head(f"{w['title']} \u2014 {S['name']}", f"{cap(w)}. Painting by Anna Hemmerich.",
                 f"/work/{w['slug']}/", prefix,
                 f'<script type="application/ld+json">{ld}</script>\n')
            + body + tail(prefix))


# --------------------------------------------------------- list of works ---
def build_list(prefix="../"):
    rows = []
    for w in WORKS:
        rows.append(f'    <li><a href="{R(prefix, f"work/{w["slug"]}/")}"><b>{esc(w["title"])}</b>, '
                    f'{esc(w["medium"])}, {esc(w["dims"])}, {w["year"]}</a></li>')
    body = f"""<main id="main" class="page">
  <h1>List of works</h1>
  <p class="sub">Twenty works, {esc(S['years'])}</p>
  <ol class="olist">
{chr(10).join(rows)}
  </ol>
  <p class="note">Dimensions are in inches, height &#215; width. The full list with prices is available on request.</p>
</main>
"""
    return (head(f"List of works \u2014 {S['name']}",
                 f"The full list of works by {S['name']}, 2025\u20132026.",
                 "/list-of-works/", prefix) + top(prefix, "list-of-works/") + body + tail(prefix))


# ---------------------------------------------------------------- about ---
def build_about(prefix="../"):
    bio = f'  <p>{esc(BIO)}</p>\n' if BIO else ""
    body = f"""<main id="main" class="page">
  <h1>About</h1>
  <p>{ABOUT[0]}</p>
  <p>{ABOUT[1]}</p>
  <p>{ABOUT[2]}</p>
  <p>{ABOUT[3]}</p>
{bio}  <ul class="tags">
{chr(10).join(f'    <li>{esc(m)}</li>' for m in MEDIA)}
  </ul>

  <h2>Contact</h2>
  <p>For enquiries about the work, exhibitions, or the full list of works with
  prices: <a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a></p>
</main>
"""
    return (head(f"About \u2014 {S['name']}",
                 f"About the work of {S['name']}, painting in acrylic, oil and collage.",
                 "/about/", prefix) + top(prefix, "about/") + body + tail(prefix))


# ------------------------------------------------------------------ 404 ---
def build_404():
    """A 404 can be served at any depth, so relative links are not safe here.
    This is the one page that uses paths absolute to the project root, and
    PROJECT_BASE is the single value that changes when the domain goes live."""
    b = PROJECT_BASE or ""
    proot = f"{PROJECT_BASE}/"
    links = (f'<a href="{b}/">Work</a> &nbsp; '
             f'<a href="{b}/list-of-works/">List of works</a> &nbsp; '
             f'<a href="{b}/about/">About</a>')
    body = f"""<main id="main" class="page">
  <h1>404</h1>
  <p class="sub">That page isn't here.</p>
  <p>{links}</p>
</main>
"""
    return (head("Not found", "Page not found.", "/404.html", proot)
            + f'<header class="top" id="top"><p class="name">'
              f'<a href="{b}/">{esc(S["name"])}</a></p></header>\n'
            + body + tail(proot))


# ----------------------------------------------------------------- write ---
def write(path, content):
    full = os.path.join(ROOT, path.lstrip("/").replace("/", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return full


n = 0
write("index.html", build_home("")); n += 1
for i in range(len(WORKS)):
    write(f"work/{WORKS[i]['slug']}/index.html", build_work(i, "../../")); n += 1
write("list-of-works/index.html", build_list("../")); n += 1
write("about/index.html", build_about("../")); n += 1
write("404.html", build_404()); n += 1

write(".nojekyll", "")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
urls = ["/"] + [f"/work/{w['slug']}/" for w in WORKS] + ["/list-of-works/", "/about/"]
write("sitemap.xml",
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f'  <url><loc>{BASE}{u}</loc><lastmod>{NOW}</lastmod></url>\n' for u in urls)
      + "</urlset>\n")

print(f"built {n} pages + .nojekyll/robots.txt/sitemap.xml  (page URLs relative,"
      f" 404 root = {PROJECT_BASE or '/'})")
