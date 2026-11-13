"""Text on a finale thumbnail: one big word or two in the series' glitch (white,
a magenta and a cyan copy pulled apart, a thick black outline), and the
"THE FINALE n/5" pill from the Shorts themselves, so the five read as a set.

    python tools/thumb_finale.py base.png out.png "HI!" --n 1 [--of 5] [--y 0.035] [--size 0.30]
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FONT = os.path.join(HERE, "..", "fonts", "InterDisplay-Black.otf")
WHITE, MAGENTA, CYAN, GOLD = (255, 255, 255, 255), (255, 40, 210, 255), (0, 230, 255, 255), (255, 210, 63, 255)


def big_text(im, text, y, size_frac):
    W, H = im.size
    font = ImageFont.truetype(FONT, int(size_frac * H))
    l, t, r, b = font.getbbox(text)
    if r - l > 0.9 * W:                                     # never wider than the frame
        font = ImageFont.truetype(FONT, int(size_frac * H * 0.9 * W / (r - l)))
        l, t, r, b = font.getbbox(text)
    x = (W - (r - l)) // 2 - l
    yy = int(y * H) - t
    stroke = max(6, font.size // 11)
    spread = max(6, font.size // 28)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + stroke // 2, yy + stroke), text, font=font, fill=(0, 0, 0, 210),
                            stroke_width=stroke + spread, stroke_fill=(0, 0, 0, 210))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(stroke)))
    d = ImageDraw.Draw(im)
    d.text((x, yy), text, font=font, fill=(0, 0, 0, 255), stroke_width=stroke + spread, stroke_fill=(0, 0, 0, 255))
    d.text((x - spread, yy), text, font=font, fill=CYAN)
    d.text((x + spread, yy), text, font=font, fill=MAGENTA)
    d.text((x, yy), text, font=font, fill=WHITE)
    return im, yy + b


def pill(im, n, of, cy):
    W, H = im.size
    s = H / 1920
    big = ImageFont.truetype(FONT, int(84 * s))
    small = ImageFont.truetype(FONT, int(44 * s))
    label, part = "THE FINALE", f"{n}/{of}"
    wl, wp = small.getlength(label), big.getlength(part)
    gap, pad, hh = 28 * s, 48 * s, 72 * s
    tw = wl + gap + wp
    x0 = W / 2 - tw / 2
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0 - pad, cy - hh, x0 + tw + pad, cy + hh), radius=hh, fill=(6, 4, 12, 200),
                        outline=(0, 230, 255, 160), width=max(3, int(4 * s)))
    d.text((x0 + wl / 2, cy + 2 * s), label, font=small, fill=GOLD, anchor="mm")
    sp = int(5 * s)
    px = x0 + wl + gap + wp / 2
    d.text((px - sp, cy), part, font=big, fill=CYAN, anchor="mm")
    d.text((px + sp, cy), part, font=big, fill=MAGENTA, anchor="mm")
    d.text((px, cy), part, font=big, fill=WHITE, anchor="mm")
    return Image.alpha_composite(im, layer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("text")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--of", type=int, default=5)
    ap.add_argument("--y", type=float, default=0.035, help="top of the big text, as a fraction of the height")
    ap.add_argument("--size", type=float, default=0.13, help="big text size, as a fraction of the height")
    ap.add_argument("--pill-y", type=float, default=None, help="the pill's centre (default: under the big text)")
    a = ap.parse_args()
    im = Image.open(a.src).convert("RGBA")
    im, bottom = big_text(im, a.text, a.y, a.size)
    cy = a.pill_y * im.size[1] if a.pill_y is not None else bottom + 0.055 * im.size[1]
    im = pill(im, a.n, a.of, cy)
    im.convert("RGB").save(a.dst, quality=95)


if __name__ == "__main__":
    main()
