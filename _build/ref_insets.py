"""Measure the page inset of each reference site, off the stored screenshots.

`_build/refs/shots/*-desk-top.png` are 1440px-wide captures of the seven sites
`shot_refs.js` took. The inset is where the first ink starts: scan columns from
the left, and take the first one that isn't the page ground. Rows are sampled
every third pixel; a column counts as inked if it carries more than H/300
sampled non-ground pixels, which ignores stray antialiasing.

Gives the number the README quotes for the references' own inset range.

    python _build/ref_insets.py
"""
import glob
import os

from PIL import Image

SHOTS = os.path.join(os.path.dirname(__file__), 'refs', 'shots')
TOL = 24          # sum of |r-255|+|g-255|+|b-255| before a pixel counts as ink
ROW_STEP = 3


def left_inset(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    px = im.load()
    threshold = max(3, h // 300)

    def inked(x):
        n = 0
        for y in range(0, h, ROW_STEP):
            r, g, b = px[x, y]
            if abs(r - 255) + abs(g - 255) + abs(b - 255) > TOL:
                n += 1
                if n > threshold:
                    return True
        return False

    for x in range(w):
        if inked(x):
            return x, w
    return None, w


def main():
    files = sorted(glob.glob(os.path.join(SHOTS, '*-desk-top.png')))
    if not files:
        raise SystemExit('no desk-top screenshots in %s' % SHOTS)
    print('%-16s %8s  %s' % ('site', 'inset', '(at 1440)'))
    for f in files:
        name = os.path.basename(f).split('-')[0]
        value, _ = left_inset(f)
        print('%-16s %8s' % (name, value if value is not None else 'none'))


if __name__ == '__main__':
    main()
