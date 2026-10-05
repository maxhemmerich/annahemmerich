"""Crop each artwork photograph to the painting itself.

Why: her photographs are documentary — the painting sits on a wall with a wide
margin of wall around it. In the portfolio PDF that margin reads as a gallery
page. On the web it wastes the tile and makes every work small. The references
she sent all show the work filling the frame.

Method: sample the wall colour from the photograph's border, mask everything
that differs from it, then take the largest contiguous run of rows and of
columns that are mostly non-wall. Validated: reject any crop that is implausibly
small, implausibly large, or a silly aspect, and fall back to the whole photo.

Every result is written to a contact sheet so it can be checked by eye before
anything reaches the site.
"""
import os
from PIL import Image, ImageFilter, ImageDraw

SRC = r"C:/Users/maxhe/AppData/Local/hermes/cache/scratch/anna_art"
OUT = r"C:/Users/maxhe/AppData/Local/hermes/cache/scratch/anna_crop"
os.makedirs(OUT, exist_ok=True)

SLUGS = ["tennis", "since-daisies", "pear-juice", "sunset-florida-man", "personal-highway",
         "sounding-yellow-bell", "entry-line", "buster", "garbage-collector", "sesick",
         "wonder-bus", "jarvis-tea", "machine-for-wilting", "electric-fence", "hive-knot",
         "depot-drawers", "sweetie-snow-cap", "huckleberry-bush", "purple-propeller", "gosha"]

PAD = 0.012      # pad each side, as a fraction of the longer side of the crop
THRESH = 20      # per-channel difference from the wall that counts as "not wall"
ROW_FRAC = 0.30  # a row/column counts as content when this share of it differs
MIN_AREA = 0.30  # reject a crop smaller than this share of the photo
MAX_AREA = 0.985


def wall_colour(im):
    """Median colour of a 2.5%-wide frame around the photograph."""
    w, h = im.size
    b = max(3, int(min(w, h) * 0.025))
    small = im.resize((max(1, w // 4), max(1, h // 4)))
    sw, sh = small.size
    sb = max(1, b // 4)
    px = small.load()
    vals = []
    for y in range(sh):
        for x in range(sw):
            if x < sb or y < sb or x >= sw - sb or y >= sh - sb:
                vals.append(px[x, y])
    if not vals:
        return (255, 255, 255)
    vals.sort(key=lambda c: c[0] + c[1] + c[2])
    return vals[len(vals) // 2]


def largest_run(flags):
    """Longest contiguous run of True."""
    best = (0, -1)
    s = None
    for i, f in enumerate(flags + [False]):
        if f and s is None:
            s = i
        elif not f and s is not None:
            if i - s > best[1] - best[0] + 1:
                best = (s, i - 1)
            s = None
    return best


def detect_once(im, box_hint=None):
    """One pass: find the content box inside im (or inside box_hint)."""
    if box_hint:
        im = im.crop(box_hint)
    W, H = im.size
    wall = wall_colour(im)
    sc = 380 / max(W, H)
    if sc < 1:
        small = im.resize((max(1, round(W * sc)), max(1, round(H * sc))), Image.LANCZOS)
    else:
        small = im
        sc = 1
    sw, sh = small.size
    g = small.convert("L")
    wall_l = Image.new("L", small.size, int(0.299 * wall[0] + 0.587 * wall[1] + 0.114 * wall[2]))
    from PIL import ImageChops
    diff = ImageChops.difference(g, wall_l).filter(ImageFilter.GaussianBlur(1.2))
    px = diff.load()

    rows = [sum(1 for x in range(sw) if px[x, y] > THRESH) / sw > ROW_FRAC for y in range(sh)]
    cols = [sum(1 for y in range(sh) if px[x, y] > THRESH) / sh > ROW_FRAC for x in range(sw)]
    y0, y1 = largest_run(rows)
    x0, x1 = largest_run(cols)
    if y1 < y0 or x1 < x0:
        return None, wall, "no content run found"
    k = 1 / sc
    b = [x0 * k, y0 * k, (x1 + 1) * k, (y1 + 1) * k]
    if box_hint:
        b = [b[0] + box_hint[0], b[1] + box_hint[1], b[2] + box_hint[0], b[3] + box_hint[1]]
    return b, wall, "ok"


def detect(path):
    """Single pass, with the wall re-sampled from a 2% inset frame rather than
    the photograph's outer border. On these photographs the outer border often
    sits in shadow, so sampling it reads the wall as darker than it is and
    leaves a band behind. Sampling from just inside avoids that.

    A second re-entrant pass was tried and over-cropped badly (it cut
    Garbage Collector to a horizontal band and Wonder bus to a strip), so the
    detection stays single-pass and its results are checked on a contact sheet.
    """
    im = Image.open(path).convert("RGB")
    W, H = im.size
    ix, iy = W * 0.02, H * 0.02
    b1, wall, why = detect_once(im, [ix, iy, W - ix, H - iy])
    if not b1:
        return None, wall, why
    box = b1
    # pad outward
    bw, bh = box[2] - box[0], box[3] - box[1]
    p = PAD * max(bw, bh)
    box = [max(0, box[0] - p), max(0, box[1] - p), min(W, box[2] + p), min(H, box[3] + p)]

    area = (box[2] - box[0]) * (box[3] - box[1]) / (W * H)
    ar = (box[2] - box[0]) / (box[3] - box[1])
    if area < MIN_AREA:
        return None, wall, f"crop too small ({area:.2f})"
    if area > MAX_AREA:
        return None, wall, f"crop too large ({area:.2f})"
    if not (0.25 < ar < 4.0):
        return None, wall, f"silly aspect ({ar:.2f})"
    return [round(v) for v in box], wall, f"ok area={area:.2f} ar={ar:.2f}"


results = []
for slug, fn in zip(SLUGS, sorted(os.listdir(SRC))):
    path = os.path.join(SRC, fn)
    box, wall, why = detect(path)
    im = Image.open(path).convert("RGB")
    if box:
        out = im.crop(tuple(int(v) for v in box))
    else:
        out = im.copy()
    out.save(os.path.join(OUT, f"{slug}.jpg"), "JPEG", quality=95, subsampling=0)
    results.append((slug, im.size, box, out.size, why))
    print(f"{slug:22} {str(im.size):14} -> {str(out.size):14} wall={wall} {why}")

# contact sheet, for looking at
cols, tile = 5, 300
rows = (len(results) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tile, rows * (tile + 16)), (245, 245, 245))
d = ImageDraw.Draw(sheet)
for i, (slug, _, _, _, why) in enumerate(results):
    im = Image.open(os.path.join(OUT, f"{slug}.jpg"))
    im.thumbnail((tile - 8, tile - 8))
    x = (i % cols) * tile + (tile - im.width) // 2
    y = (i // cols) * (tile + 16) + 4
    sheet.paste(im, (x, y))
    d.text(((i % cols) * tile + 4, (i // cols) * (tile + 16) + tile - 8), slug[:30], fill=(0, 0, 0))
sheet.save(r"D:/Anna Website/.shots/crop-sheet.png")
print("\ncontact sheet -> D:/Anna Website/.shots/crop-sheet.png")
