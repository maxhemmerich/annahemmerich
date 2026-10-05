"""Bake one accent colour per work, sampled from that painting's own pixels.
The site uses each work's accent for its collage plate and its hover ink, so no
colour on the site is invented — every one comes out of the work it belongs to."""
import os, json, colorsys
from PIL import Image, ImageOps
from collections import Counter

ART = r"C:/Users/maxhe/AppData/Local/hermes/cache/scratch/anna_art"
WJ  = r"D:/Anna Website/_build/works.json"

with open(WJ, encoding="utf-8") as f:
    data = json.load(f)

SLUGS = [w["slug"] for w in data["works"]]
files = sorted(os.listdir(ART))
assert len(files) == len(SLUGS)

def accent_for(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((240, 240))
    px = list(im.getdata())
    c = Counter()
    for r, g, b in px:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        h *= 360; s *= 100; l *= 100
        if s >= 42 and 26 <= l <= 62:
            c[(r // 10 * 10 + 5, g // 10 * 10 + 5, b // 10 * 10 + 5)] += 1
    if not c:
        return "#12121a"
    # average the top few bins in the winning hue family so the accent is not a speck
    top = c.most_common(1)[0][0]
    h0, l0, s0 = colorsys.rgb_to_hls(top[0] / 255, top[1] / 255, top[2] / 255)
    h0 *= 360
    fam = []
    for t, n in c.items():
        h, l, s = colorsys.rgb_to_hls(t[0] / 255, t[1] / 255, t[2] / 255)
        h *= 360
        d = abs(h - h0); d = min(d, 360 - d)
        if d < 22:
            fam.extend([t] * min(n, 4000))
    r = sum(t[0] for t in fam) // len(fam)
    g = sum(t[1] for t in fam) // len(fam)
    b = sum(t[2] for t in fam) // len(fam)
    # step down to a weight that reads as ink on bone paper
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = min(l, 0.42)
    s = min(1.0, s * 1.05)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))

for w, fn in zip(data["works"], files):
    a = accent_for(os.path.join(ART, fn))
    w["accent"] = a
    im = Image.open(os.path.join(ART, fn))
    im = ImageOps.exif_transpose(im)
    W, H = im.size
    w["ar"] = round(W / H, 3)
    # intrinsic pixel dimensions of the two generated sizes, for width/height attrs
    for size, key in ((1600, "px1600"), (900, "px900")):
        big = max(W, H)
        if big > size:
            r = size / big
            w[key] = [max(1, round(W * r)), max(1, round(H * r))]
        else:
            w[key] = [W, H]
    print(f"  {w['n']:2} {w['slug']:22} {W}x{H} ar={w['ar']:.2f} acc={a} "
          f"1600={w['px1600']} 900={w['px900']}")

# span pattern: portrait -> narrower, landscape/square -> wider. Disciplined, repeats.
def span(ar):
    if ar < 0.86:  return 4, 6     # tall
    if ar < 1.06:  return 6, 6     # square-ish
    return 8, 6                    # wide

for w in data["works"]:
    s, sm = span(w["ar"])
    w["span"], w["span_m"] = s, sm

with open(WJ, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1, ensure_ascii=False)
print("baked ->", WJ)
