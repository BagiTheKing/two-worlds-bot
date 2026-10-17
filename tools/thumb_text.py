"""
Thumbnail text on top of the base image from tools/thumbnail.py. Only this
changes per episode:

    python tools/thumb_text.py build/thumb/base_ep00.png out.png --episode 0
        [--subtitle "TWO WORLDS · ONE GLITCH"]

Big words are drawn small and enlarged without smoothing, so their edges are
chunky pixels like the block world, with a block extrusion and the series'
magenta/cyan glitch. No game logos or logo lettering: the game names are
plain words.
"""

import argparse
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "InterDisplay-Black.otf")
MAGENTA, CYAN = (255, 40, 210), (0, 230, 255)


def pixel_mask(text, height, base=34):
    """Text as a hard-edged pixel mask about `height` px tall."""
    f = ImageFont.truetype(FONT, base)
    l, t, r, b = f.getbbox(text)
    m = Image.new("L", (r - l + 8, b - t + 8), 0)
    ImageDraw.Draw(m).text((4 - l, 4 - t), text, font=f, fill=255)
    m = m.point(lambda v: 255 if v > 110 else 0)
    k = height / m.height
    return m.resize((int(m.width * k), int(m.height * k)), Image.NEAREST), k


def blocky(canvas, text, cx, top, height, face, extrude, depth=5, glitch=0, seed=0):
    """Pixel letters with a block extrusion and a black outline."""
    m, k = pixel_mask(text, height)
    px = max(1, int(k))                                   # one "pixel" of the letters
    x0 = cx - m.width // 2
    pad = px * (depth + 3)
    layer = Image.new("RGBA", (m.width + 2 * pad, m.height + 2 * pad), (0, 0, 0, 0))
    outline = Image.new("L", layer.size, 0)
    for d in range(depth, -1, -1):                        # extrusion, back to front
        outline.paste(m, (pad + d * px // 2, pad + d * px), m)
    outline = outline.filter(ImageFilter.MaxFilter(px * 2 + 1 if px % 2 == 0 else px * 2 + 1))
    layer.paste((0, 0, 0, 255), (0, 0), outline)
    for d in range(depth, 0, -1):
        layer.paste((*extrude, 255), (pad + d * px // 2, pad + d * px), m)
    if glitch:
        for dx, col in ((-glitch, MAGENTA), (glitch, CYAN)):
            layer.paste((*col, 255), (pad + dx, pad), m)
    layer.paste((*face, 255), (pad, pad), m)
    if glitch:                                            # a few torn scanlines
        rnd = random.Random(seed)
        for _ in range(6):
            y = rnd.randrange(pad, pad + m.height - px)
            h = rnd.randrange(px, px * 3)
            band = layer.crop((0, y, layer.width, y + h))
            layer.paste((0, 0, 0, 0), (0, y, layer.width, y + h))
            layer.paste(band, (rnd.choice((-1, 1)) * rnd.randrange(px, px * 4), y), band)
    canvas.alpha_composite(layer, (x0 - pad, top - pad))
    return top + m.height


def smooth(canvas, text, cx, y, size, fill, stroke=14):
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(canvas)
    d.text((cx + 8, y + 10), text, font=f, fill=(0, 0, 0, 200), anchor="mt")
    d.text((cx, y), text, font=f, fill=fill, anchor="mt", stroke_width=stroke, stroke_fill=(0, 0, 0))


def shade(canvas, top, bottom):
    """Darken the top and bottom bands so the words read on any image."""
    w, h = canvas.size
    g = Image.new("L", (1, h), 0)
    for y in range(h):
        a = max(0.0, 1 - y / top) if y < top else (max(0.0, (y - (h - bottom)) / bottom) if bottom else 0.0)
        g.putpixel((0, y), int(200 * min(1.0, a) ** 1.4))
    g = g.resize((w, h))
    canvas.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (w, h), 0)] * 3, g)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--episode", required=True)
    ap.add_argument("--subtitle", default="TWO WORLDS · ONE GLITCH")
    ap.add_argument("--erase-top", type=int, default=0,
                    help="blur away this many px at the top first (old title lettering)")
    ap.add_argument("--top-only", action="store_true", help="leave the bottom of the image as it is")
    a = ap.parse_args()

    img = Image.open(a.base).convert("RGBA").resize((2160, 3840), Image.LANCZOS)
    W, H = img.size
    if a.erase_top:                                 # wipe old lettering, feathered into the image
        band = img.crop((0, 0, W, a.erase_top + 200)).filter(ImageFilter.GaussianBlur(70))
        band = Image.blend(band, Image.new("RGBA", band.size, (8, 6, 14, 255)), 0.45)
        fade = Image.new("L", band.size, 255)
        for y in range(a.erase_top, band.height):
            ImageDraw.Draw(fade).line((0, y, W, y), fill=int(255 * (1 - (y - a.erase_top) / 200)))
        img.paste(band, (0, 0), fade)
    shade(img, 1250, 0 if a.top_only else 1300)
    cx = W // 2

    margin = 150                                    # keep clear of the edges

    def fit(widths_at, height):
        """Largest height (up to `height`) whose total width fits the frame."""
        w = widths_at(height)
        return int(height * min(1.0, (W - 2 * margin) / w))

    # top: the two game names, then ANIMATION
    y = 230
    left, right, gap = "MINECRAFT", "ROBLOX", 50

    def row_width(h):
        return (pixel_mask(left, h)[0].width + pixel_mask(right, h)[0].width
                + pixel_mask("x", int(h * 0.7))[0].width + 2 * gap)
    h = fit(row_width, 210)
    lm, rm, xm = pixel_mask(left, h)[0], pixel_mask(right, h)[0], pixel_mask("x", int(h * 0.7))[0]
    x = cx - row_width(h) // 2
    blocky(img, left, x + lm.width // 2, y, h, (236, 236, 236), (70, 150, 60), depth=5)
    blocky(img, "x", x + lm.width + gap + xm.width // 2, y + int(h * 0.22), int(h * 0.7),
           (255, 210, 63), (150, 110, 20), depth=4)
    blocky(img, right, x + lm.width + 2 * gap + xm.width + rm.width // 2, y, h,
           (236, 236, 236), (40, 100, 220), depth=5)
    blocky(img, "ANIMATION", cx, y + h + 90, fit(lambda k: pixel_mask("ANIMATION", k)[0].width, 170),
           (255, 255, 255), (60, 20, 90), depth=4, glitch=10, seed=3)

    if a.top_only:
        img.convert("RGB").save(a.out, quality=95)
        print("wrote", a.out, img.size)
        return

    # bottom: the episode, big, then the series name
    ep = f"EPISODE {a.episode}"
    blocky(img, ep, cx, H - 960, fit(lambda k: pixel_mask(ep, k)[0].width, 380),
           (255, 255, 255), (70, 10, 110), depth=6, glitch=18, seed=7)
    sub_size = 150
    while ImageFont.truetype(FONT, sub_size).getlength(a.subtitle) > W - 2 * margin:
        sub_size -= 4
    smooth(img, a.subtitle, cx, H - 520, sub_size, (255, 255, 255))

    img.convert("RGB").save(a.out, quality=95)
    print("wrote", a.out, img.size)


if __name__ == "__main__":
    main()
