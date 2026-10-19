"""
Change the episode number on the series thumbnail, keeping the image's own
neon glitch lettering: the old number is painted out of the background and
the new one is drawn in the same style (black face, cyan/yellow split rim,
magenta glow, torn scanlines).

    python tools/thumb_number.py assets/thumbnails/series_ep00.jpg out.jpg 1 [--test 0]

--test 0 redraws the existing 0 beside the original, to check the style.
"""

import argparse
import random

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

# where the number sits on the 2160x3840 thumbnail (the original "0")
FACE = (1786, 3195, 1986, 3535)            # the black face of the glyph
ERASE = (1738, 3160, 2050, 3572)           # the glyph with its glow
STROKE = 54
RADIUS = 30
GLOW, CYAN, YELLOW = (150, 30, 175), (160, 236, 245), (248, 196, 80)


def glyph(digit, h):
    """The digit's face as a mask, in the lettering's squared, rounded style."""
    s = STROKE
    if digit == "0":
        w = FACE[2] - FACE[0]
        m = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(m)
        d.rounded_rectangle((0, 0, w - 1, h - 1), RADIUS * 2, fill=255)
        d.rounded_rectangle((s, s + 10, w - 1 - s, h - 1 - s - 10), RADIUS, fill=0)
        return m
    if digit == "1":
        flag = 62                                  # how far the flag reaches left
        w = flag + s + 4
        m = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(m)
        d.rounded_rectangle((flag, 0, w - 1, h - 1), 12, fill=255)
        # the flag: a slanted block from the top of the stem down to the left
        d.polygon([(flag + 6, 0), (flag + 6, s + 18), (4, s + 62), (0, s + 40), (0, s + 8)],
                  fill=255)
        d.rounded_rectangle((0, s + 4, s - 8, s + 62), 8, fill=255)
        return m.filter(ImageFilter.MaxFilter(3))
    raise SystemExit(f"no glyph for {digit!r} yet")


def tear(m, seed, n=2):
    """The lettering's glitch: the lower part of the glyph slid sideways, and
    a few thin torn scanlines."""
    rnd = random.Random(seed)
    out = Image.new("L", (m.width + 24, m.height), 0)
    out.paste(m, (0, 0))
    cut = int(m.height * 0.72)
    low = m.crop((0, cut, m.width, m.height))
    out.paste(0, (0, cut, out.width, out.height))
    out.paste(low, (10, cut))
    for _ in range(n):
        y = rnd.randrange(int(m.height * 0.2), int(m.height * 0.65))
        h = rnd.randrange(6, 12)
        band = out.crop((0, y, out.width, y + h))
        out.paste(0, (0, y, out.width, y + h))
        out.paste(band, (rnd.choice((-1, 1)) * rnd.randrange(6, 12), y))
    return out


def draw(canvas, digit, cx, top, h, seed=5):
    """Draw the digit centred on cx, its face from top to top+h."""
    face = tear(glyph(digit, h), seed)
    pad = 60
    W, H = face.width + 2 * pad, face.height + 2 * pad
    m = Image.new("L", (W, H), 0)
    m.paste(face, (pad, pad))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = m.filter(ImageFilter.MaxFilter(17)).filter(ImageFilter.GaussianBlur(14))
    layer.paste((*GLOW, 255), (0, 0), glow.point(lambda v: min(255, int(v * 1.2))))
    layer.paste((*YELLOW, 255), (0, 0), ImageChops.offset(m, 5, 4))     # split rim
    layer.paste((*CYAN, 255), (0, 0), ImageChops.offset(m, -5, -4))
    layer.paste((4, 4, 6, 255), (0, 0), m)                               # the black face
    layer = layer.filter(ImageFilter.GaussianBlur(1.2))       # as soft as the image's own letters
    canvas.alpha_composite(layer, (cx - W // 2, top - pad))


def erase(img):
    """Paint the old number out of the background."""
    a = np.asarray(img.convert("RGB"))
    mask = np.zeros(a.shape[:2], np.uint8)
    x0, y0, x1, y1 = ERASE
    mask[y0:y1, x0:x1] = 255
    out = cv2.inpaint(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), mask, 21, cv2.INPAINT_TELEA)
    out = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
    # inpainting smears: give the patch back some of the scene's grain and sparks' darkness
    patch = out.crop(ERASE).filter(ImageFilter.GaussianBlur(3))
    noise = Image.effect_noise(patch.size, 14).convert("RGB")
    patch = ImageChops.add(patch, noise, scale=1.0, offset=-128)    # noise is centred on grey
    out.paste(patch, ERASE[:2])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("thumb")
    ap.add_argument("out")
    ap.add_argument("number")
    ap.add_argument("--test", help="redraw this digit in place of the original, for comparison")
    a = ap.parse_args()
    img = Image.open(a.thumb).convert("RGB").resize((2160, 3840), Image.LANCZOS)
    digit = a.test or a.number
    out = erase(img).convert("RGBA")
    h = FACE[3] - FACE[1]
    gw = glyph(digit, h).width
    # the number starts where the 0 started, so the word gap stays the same
    cx = FACE[0] + gw // 2
    draw(out, digit, cx, FACE[1], h)
    out.convert("RGB").save(a.out, quality=95)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
