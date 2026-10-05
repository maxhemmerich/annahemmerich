"""Read Anna's reference sites: their own stylesheets, their own tokens.
Writes a report to _build/refs/report.md and dumps CSS into _build/refs/.
"""
import os, re, json, subprocess, urllib.parse, collections

OUT = r"D:/Anna Website/_build/refs"
os.makedirs(OUT, exist_ok=True)

SITES = [
    ("flatfix",            "https://flatfix.biz/"),
    ("erlendpederkvam",    "https://erlendpederkvam.com/"),
    ("cameronplatter",     "https://cameronplatter.com/HOME-2"),
    ("tareklakhrissi",     "https://tareklakhrissi.com/"),
    ("hughfrost",          "https://hughfrost.net/"),
    ("zartnan",            "https://zartnan.com/menu"),
    ("ailsaogden",         "https://ailsaogden.studio/"),
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def curl(url, dest=None, timeout=40):
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-A", UA,
           "-H", "Accept: text/html,application/xhtml+xml,text/css,*/*",
           url]
    if dest:
        cmd += ["-o", dest]
        subprocess.run(cmd, capture_output=True)
        return dest
    return subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", "replace")


report = ["# Anna's reference sites — what they are actually made of", ""]

for name, url in SITES:
    report.append(f"\n## {name} — {url}\n")
    html = curl(url)
    if not html.strip():
        report.append("  FETCH FAILED\n")
        continue
    with open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8") as f:
        f.write(html)

    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    report.append(f"- title: {title.group(1).strip()[:120] if title else '(none)'}")
    report.append(f"- html bytes: {len(html)}")

    gen = re.search(r'name="generator"\s+content="([^"]+)"', html, re.I)
    report.append(f"- generator: {gen.group(1) if gen else '(none declared)'}")

    # linked stylesheets
    links = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', html, re.I)
    hrefs = []
    for l in links:
        m = re.search(r'href=["\']([^"\']+)["\']', l)
        if m:
            hrefs.append(urllib.parse.urljoin(url, m.group(1)))
    inline_css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    report.append(f"- stylesheets: {len(hrefs)}")
    for h in hrefs[:6]:
        report.append(f"    - {h}")

    css_all = inline_css
    for i, h in enumerate(hrefs[:6]):
        fn = os.path.join(OUT, f"{name}.{i}.css")
        css = curl(h, fn)
        if css and os.path.exists(fn):
            with open(fn, encoding="utf-8", errors="replace") as f:
                css_all += "\n" + f.read()

    # custom properties
    props = collections.Counter(re.findall(r"(--[A-Za-z0-9_-]{1,60})\s*:\s*([^;}\n]{1,90})", css_all))
    interesting = [(k, v) for (k, v), n in props.items()
                   if re.search(r"(hsl|rgb|#|font|color|size|space|radius|accent|primary|secondary)", k, re.I)]
    report.append(f"- CSS custom properties found: {len(props)}")
    for k, v in interesting[:34]:
        report.append(f"    {k}: {v.strip()}")

    # font families
    fams = collections.Counter(re.findall(r"font-family\s*:\s*([^;}\n]{1,110})", css_all))
    if fams:
        report.append("- font-family declarations (top 8):")
        for k, n in fams.most_common(8):
            report.append(f"    {k.strip()[:100]}   x{n}")

    # background colours
    bgs = collections.Counter(re.findall(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]{1,40}\)|hsla?\([^)]{1,50}\))", css_all))
    if bgs:
        report.append("- background colours (top 10):")
        for k, n in bgs.most_common(10):
            report.append(f"    {k}   x{n}")

    # type scale hints
    fs = collections.Counter(re.findall(r"font-size\s*:\s*([^;}\n]{1,40})", css_all))
    if fs:
        report.append("- font-size values (top 12):  " + ", ".join(f"{k.strip()}({n})" for k, n in fs.most_common(12)))

    # webfonts
    wf = re.findall(r"https://fonts\.googleapis\.com/css2?\?([^\"')]+)", css_all)
    wf2 = re.findall(r"@font-face\s*\{[^}]*?font-family\s*:\s*['\"]?([^;'\"]+)", css_all, re.S | re.I)
    if wf:
        report.append("- google fonts: " + "; ".join(sorted(set(urllib.parse.unquote(w)[:90] for w in wf))))
    if wf2:
        report.append("- @font-face families: " + ", ".join(sorted(set(f.strip() for f in wf2))[:12]))

    # structure hints from the live html
    imgs = len(re.findall(r"<img", html, re.I))
    report.append(f"- <img> tags: {imgs}")

report.append("\n")
with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(report))
print("\n".join(report))
