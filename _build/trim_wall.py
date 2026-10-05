"""Objective check on each crop: how much of the crop's border is still wall?

A tight crop has a border ring made of the painting's own edge — varied,
usually saturated. A loose crop has a border ring that matches the wall.
Measures all four sides separately, then trims any side that is still wall.
"""
import os, json
from PIL import Image, ImageChops
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SRC = r"C:/Users/maxhe/AppData/Local/hermes/cache/scratch/anna_art"
OUT = r"C:/Users/maxhe/AppData/Local/hermes/cache/scratch/anna_crop"
SLUGS = ["tennis", "since-daisies", "pear-juice", "sunset-florida-man", "personal-highway",
         "sounding-yellow-bell", "entry-line", "buster", "garbage-collector", "sesick",
         "wonder-bus", "jarvis-tea", "machine-for-wilting", "electric-fence", "hive-knot",
         "depot-drawers", "sweetie-snow-cap", "huckleberry-bush", "purple-propeller", "gosha"]

TOL = 26       # per-channel distance from the wall that still counts as wall
K = 3          # strip thickness examined per step
OCCUPY = 0.55  # strip counts as wall when this share of it is wall-like
MAXTRIM = 0.16 # never trim more than this share of a side


def wall_of(im):
    """Median colour of a frame 2% inside the edge."""
    w, h = im.size
    b = max(2, int(min(w, h) * 0.02))
    p = im.load()
    vals = []
    for y in range(b, h - b):
        vals.append(p[b, y]); vals.append(p[w - 1 - b, y])
    for x in range(b, w - b):
        vals.append(p[x, b]); vals.append(p[x, h - 1 - b])
    vals.sort(key=lambda c: c[0] + c[1] + c[2])
    return vals[len(vals) // 2]


def strip_is_wall(im, side, depth):
    w, h = im.size
    p = im.load()
    n = ok = 0
    if side in ('top', 'bottom'):
        y = depth if side == 'top' else h - 1 - depth
        if y < 0 or y >= h: return False
        for x in range(0, w, 2):
            c = p[x, y]; n += 1
            if max(abs(c[0]-W[0]), abs(c[1]-W[1]), abs(c[2]-W[2])) <= TOL: ok += 1
    else:
        x = depth if side == 'left' else w - 1 - depth
        if x < 0 or x >= w: return False
        for y in range(0, h, 2):
            c = p[x, y]; n += 1
            if max(abs(c[0]-W[0]), abs(c[1]-W[1]), abs(c[2]-W[2])) <= TOL: ok += 1
    return n and ok / n >= OCCUPY


def ring_wall_share(im, band):
    """Share of the border ring that is wall-like, per side."""
    w, h = im.size
    out = {}
    for side in ('top', 'bottom', 'left', 'right'):
        n = ok = 0
        for d in range(band):
            if side == 'top': ys, xs = [d], range(0, w, 3)
            elif side == 'bottom': ys, xs = [h - 1 - d], range(0, w, 3)
            elif side == 'left': ys, xs = range(0, h, 3), [d]
            else: ys, xs = range(0, h, 3), [w - 1 - d]
            p = im.load()
            for y in ys:
                for x in xs:
                    c = p[x, y]; n += 1
                    if max(abs(c[0]-W[0]), abs(c[1]-W[1]), abs(c[2]-W[2])) <= TOL: ok += 1
        out[side] = round(100 * ok / n) if n else 0
    return out


print(f"{'work':22} {'before (t/b/l/r %wall)':30} {'trimmed':22} after")
rows = []
for slug in SLUGS:
    im = Image.open(os.path.join(OUT, f"{slug}.jpg")).convert("RGB")
    W = wall_of(im)
    before = ring_wall_share(im, max(2, int(min(im.size) * 0.012)))
    t = dict(top=0, bottom=0, left=0, right=0)
    for side in t:
        limit = int((im.size[0] if side in ('left', 'right') else im.size[1]) * MAXTRIM)
        d = 0
        while d < limit and strip_is_wall(im, side, d):
            d += K
        t[side] = d
    if any(t.values()):
        x0 = t['left']; y0 = t['top']
        x1 = im.size[0] - t['right']; y1 = im.size[1] - t['bottom']
        if x1 - x0 > im.size[0] * 0.4 and y1 - y0 > im.size[1] * 0.4:
            im = im.crop((x0, y0, x1, y1))
    im.save(os.path.join(OUT, f"{slug}.jpg"), "JPEG", quality=95, subsampling=0)
    after = ring_wall_share(im, max(2, int(min(im.size) * 0.012)))
    fmt = lambda d: f"{d['top']}/{d['bottom']}/{d['left']}/{d['right']}"
    flag = '' if max(after.values()) <= 35 else '   <-- still wall-ish'
    print(f"{slug:22} {fmt(before):30} {fmt(t):22} {fmt(after)}{flag}")
    rows.append((slug, before, after))

bad = [r[0] for r in rows if max(r[2].values()) > 35]
print("\nstill showing a wall-ish border on: ", bad or "none")
