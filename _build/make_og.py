"""Build the social card on the site's own white ground, out of two of the works.
Same rule as the site: no chrome, no colour added — the paintings are the image."""
import os
from PIL import Image, ImageOps

ART = r"C:/Users/maxhe/AppData/Local/hermes/cache/scratch/anna_art"
DST = r"D:/Anna Website/assets"
files = sorted(os.listdir(ART))

W, H = 1200, 630
card = Image.new("RGB", (W, H), (255, 255, 255))
margin = 46
gap = 22
n = 3
colw = (W - margin * 2 - gap * (n - 1)) // n

slot = 0
for src in (files[0], files[1], files[2]):
    im = ImageOps.exif_transpose(Image.open(os.path.join(ART, src))).convert("RGB")
    r = min(colw / im.width, (H - margin * 2) / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x = margin + slot * (colw + gap) + (colw - im.width) // 2
    y = margin + (H - margin * 2 - im.height) // 2
    card.paste(im, (x, y))
    slot += 1

card.save(os.path.join(DST, "og.jpg"), "JPEG", quality=88, optimize=True, progressive=True)
card.save(os.path.join(DST, "og.webp"), "WEBP", quality=88, method=6)
print("og.jpg", os.path.getsize(os.path.join(DST, "og.jpg")) // 1024, "KB",
      "og.webp", os.path.getsize(os.path.join(DST, "og.webp")) // 1024, "KB")
