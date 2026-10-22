#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build annahemmerich.com — landing (one painting), work (grid + overlay), cv.

    python _build/build.py

Max's redesign (2026-10-22):
  * landing  = ONE painting, static, height < screen
  * work     = a GRID of all paintings (4 across, thumbnails), scrollable;
               click one -> the grid disappears and the picture opens big, with
               an X to close and left/right arrows to move through them
  * nav      = "anna hemmerich" top-left, "work" below it, "cv" below that,
               left aligned. No About.
  * no red / no underline on hover
  * footer   = copyright only — "All works remain the property of the artist"
               and "Back to top" are gone

Content source of truth: _build/works.json
"""
import json, os, datetime, html, shutil, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "_build", "works.json"), encoding="utf-8") as f:
    DATA = json.load(f)

S = DATA["site"]
WORKS = DATA["works"]
DOMAIN = S["domain"]
BASE = f"https://{DOMAIN}"
PROJECT_BASE = S.get("base", "")
NOW = datetime.date.today().isoformat()
YEAR = datetime.date.today().year


def esc(s):
    return html.escape(str(s), quote=True)


def cap(w):
    return f"{w['title']} {w['medium']} {w['dims']}, {w['year']}"


def caption_html(w):
    return (f'<b>{esc(w["title"])}</b> {esc(w["medium"])} '
            f'{esc(w["dims"])}, {w["year"]}')


def R(prefix, path):
    return prefix + path.lstrip("/")


def css_href(prefix):
    try:
        with open(os.path.join(ROOT, "assets", "css", "site.css"), "rb") as f:
            v = hashlib.sha256(f.read()).hexdigest()[:8]
    except OSError:
        v = ""
    return R(prefix, "assets/css/site.css") + (f"?v={v}" if v else "")


# ---------------------------------------------------------------- nav ---
# Two sections: Work and CV. About is gone (Max, 2026-10-22).
NAV = [("work", "work/"), ("cv", "cv/")]


def navlinks(prefix, current):
    out = []
    for label, href in NAV:
        cur = ' aria-current="page"' if (href == current and "#" not in href) else ""
        target = R(prefix, href) if href else (prefix or "./")
        out.append(f'<a href="{target}"{cur}>{esc(label)}</a>')
    return "".join(out)


def top(prefix, current, as_h1=False):
    """The name top-left, then the two links stacked under it, left aligned."""
    name = f'<a href="{prefix or "./"}">{esc(S["name"])}</a>'
    tag = "h1" if as_h1 else "p"
    return f"""<header class="top" id="top">
  <{tag} class="name">{name}</{tag}>
  <nav class="top__nav" aria-label="Sections">{navlinks(prefix, current)}</nav>
</header>
"""


def tail(prefix):
    """Copyright only — the property line and Back to top are gone."""
    return f'<footer class="tail"><span>&copy; {YEAR} {esc(S["name"])}</span></footer>\n'


def head(title, desc, path, prefix, extra="", body_class=""):
    bc = f' class="{body_class}"' if body_class else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta name="theme-color" content="#ffffff">
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
<link rel="stylesheet" href="{css_href(prefix)}">
{extra}</head>
<body{bc}>
<a class="skip" href="#main">Skip to content</a>
"""


def picture(w, prefix, sizes, loading="lazy"):
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


# ------------------------------------------------------------- landing ---
def build_home(prefix=""):
    """One painting, static, height less than the screen."""
    w = WORKS[0]  # the landing painting is the first work
    body = f"""<main id="main" class="landing">
  <div class="landing__img">
    {picture(w, prefix, "100vw", loading="eager")}
  </div>
  <p class="landing__cap">{caption_html(w)}</p>
</main>
"""
    return (head(f"{S['name']} — Painting", "Paintings by Anna Hemmerich.", "/", prefix,
                 body_class="home")
            + top(prefix, "", as_h1=True) + body + tail(prefix))


# ---------------------------------------------------------------- work ---
def build_work(prefix=""):
    """The grid of all works, and the overlay that opens a picture big."""
    tiles = []
    for i, w in enumerate(WORKS):
        tiles.append(
            f'    <button class="tile" type="button" data-i="{i}" '
            f'aria-label="{esc(cap(w))}">{picture(w, prefix, "300px")}</button>')

    works_js = json.dumps([{
        "src": R(prefix, f"assets/art/{w['slug']}-1600.jpg"),
        "webp": R(prefix, f"assets/art/{w['slug']}-1600.webp"),
        "cap": cap(w),
    } for w in WORKS], ensure_ascii=False)

    body = f"""<main id="main" class="work">
  <div class="grid" id="grid">
{chr(10).join(tiles)}
  </div>
</main>

<div class="overlay" id="overlay" hidden>
  <button class="overlay__x" type="button" aria-label="Close">×</button>
  <button class="overlay__prev" type="button" aria-label="Previous">←</button>
  <figure class="overlay__fig">
    <picture>
      <source id="ov-src" type="image/webp">
      <img id="ov-img" src="" alt="">
    </picture>
    <figcaption id="ov-cap"></figcaption>
  </figure>
  <button class="overlay__next" type="button" aria-label="Next">→</button>
</div>

<script>
(() => {{
  const W = {works_js};
  const ov = document.getElementById("overlay");
  const img = document.getElementById("ov-img");
  const src = document.getElementById("ov-src");
  const cap = document.getElementById("ov-cap");
  let cur = -1;
  function show(i) {{
    cur = (i + W.length) % W.length;
    img.src = W[cur].src;
    src.srcset = W[cur].webp;
    img.alt = W[cur].cap;
    cap.textContent = W[cur].cap;
    ov.hidden = false;
    document.body.classList.add("locked");
  }}
  function hide() {{
    ov.hidden = true;
    document.body.classList.remove("locked");
  }}
  document.querySelectorAll(".tile").forEach((b, i) =>
    b.addEventListener("click", () => show(i)));
  document.querySelector(".overlay__x").addEventListener("click", hide);
  document.querySelector(".overlay__prev").addEventListener("click", () => show(cur - 1));
  document.querySelector(".overlay__next").addEventListener("click", () => show(cur + 1));
  document.addEventListener("keydown", (e) => {{
    if (ov.hidden) return;
    if (e.key === "Escape") hide();
    else if (e.key === "ArrowLeft") show(cur - 1);
    else if (e.key === "ArrowRight") show(cur + 1);
  }});
}})();
</script>
"""
    return (head(f"{S['name']} — Work", "All paintings by Anna Hemmerich.", "/work/", prefix)
            + top(prefix, "work/") + body + tail(prefix))


# ------------------------------------------------------------------ cv ---
def build_cv(prefix="../"):
    CV = S.get("cv", {})

    def rows(items, key):
        out = []
        for it in items:
            out.append(f'    <li><span class="yr">{esc(it[key])}</span>'
                       f'<span>{esc(it["what"])}</span></li>')
        return chr(10).join(out)

    edu = rows(CV.get("education", []), "years")
    shows = rows(CV.get("exhibitions", []), "year")
    ig = S.get("instagram", "").strip()
    city = S.get("city", "").strip()
    contact = f'{esc(city)} \u00b7 ' if city else ""
    contact += f'<a href="mailto:{esc(S.get("email", ""))}">{esc(S.get("email", ""))}</a>'
    if ig:
        contact += (f' \u00b7 <a href="https://www.instagram.com/{esc(ig)}/">'
                    f'@{esc(ig)}</a>')
    body = f"""<main id="main" class="page">
  <h1>CV</h1>
  <p class="sub">{esc(S['name'])} \u2014 {contact}</p>

  <h2>Education</h2>
  <ul class="cvlist">
{edu}
  </ul>

  <h2>Selected exhibitions</h2>
  <ul class="cvlist">
{shows}
  </ul>
</main>
"""
    return (head(f"CV — {S['name']}",
                 f"Education and selected exhibitions — {S['name']}.",
                 "/cv/", prefix) + top(prefix, "cv/") + body + tail(prefix))


# ----------------------------------------------------------------- 404 ---
def build_404():
    b = PROJECT_BASE or ""
    proot = f"{PROJECT_BASE}/"
    body = f"""<main id="main" class="page">
  <h1>404</h1>
  <p class="sub">That page isn't here.</p>
  <p><a href="{b}/work/">Work</a></p>
</main>
"""
    return (head("Not found", "Page not found.", "/404.html", proot)
            + f'<header class="top" id="top"><p class="name">'
              f'<a href="{b}/">{esc(S["name"])}</a></p></header>\n'
            + body + tail(proot))


# ---------------------------------------------------------------- write ---
def write(path, content):
    full = os.path.join(ROOT, path.lstrip("/").replace("/", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return full


n = 0
write("index.html", build_home("")); n += 1
write("work/index.html", build_work("../")); n += 1
write("cv/index.html", build_cv("../")); n += 1
write("404.html", build_404()); n += 1

# The old pages are gone: about, the per-year streams, and the one-page-per-work
# sheets (the overlay replaces them). Remove their directories so a rebuild
# cannot leave them answering at their own URLs.
for stale in ("about", "2025", "2026"):
    d = os.path.join(ROOT, stale)
    if os.path.isdir(d):
        shutil.rmtree(d)
        print(f"removed stale {stale}/")
stale_work = os.path.join(ROOT, "work")
if os.path.isdir(stale_work):
    for child in os.listdir(stale_work):
        p = os.path.join(stale_work, child)
        if os.path.isdir(p):
            shutil.rmtree(p)
    print("removed stale work/<slug>/ pages")

write(".nojekyll", "")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
urls = ["/", "/work/", "/cv/"]
write("sitemap.xml",
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f'  <url><loc>{BASE}{u}</loc><lastmod>{NOW}</lastmod></url>\n' for u in urls)
      + "</urlset>\n")

print(f"built {n} pages + .nojekyll/robots.txt/sitemap.xml  (404 root = {PROJECT_BASE or '/'})")
