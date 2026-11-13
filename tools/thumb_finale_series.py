"""The series thumbnail (Null over Steve and the Noob on the bridge) for the
finale's five Shorts: "EPISODE N" painted out and "FINALE n/5" drawn in its
place, in the image's own neon glitch lettering (black face, cyan/yellow
split rim, glow, torn scanlines), with the glow turned hot for the finale.

    python tools/thumb_finale_series.py assets/thumbnails/ep08.jpg out.jpg --n 1 [--of 5] [--style neon|hot]
"""
import argparse
import random

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import os
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "InterDisplay-Black.otf")
ERASE = (110, 3140, 2050, 3585)            # "EPISODE N" with its glow, on the 2160x3840 thumbnail
TOP, HEIGHT = 3195, 330                    # where the old letters' faces sat
CYAN, YELLOW = (160, 236, 245), (248, 196, 80)
STYLES = {"neon": {"glow": (150, 30, 175), "face": (4, 4, 6), "slash": (255, 40, 210)},
          "hot": {"glow": (255, 30, 150), "face": (4, 4, 6), "slash": (255, 210, 63)}}


def erase(img):
    a = np.asarray(img.convert("RGB"))
    mask = np.zeros(a.shape[:2], np.uint8)
    x0, y0, x1, y1 = ERASE
    mask[y0:y1, x0:x1] = 255
    out = cv2.inpaint(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), mask, 25, cv2.INPAINT_TELEA)
    out = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
    patch = out.crop(ERASE).filter(ImageFilter.GaussianBlur(4))
    patch = Image.blend(patch, Image.new("RGB", patch.size, (14, 8, 20)), 0.35)     # a darker bed for the letters
    noise = Image.effect_noise(patch.size, 12).convert("RGB")
    patch = ImageChops.add(patch, noise, scale=1.0, offset=-128)
    fade = Image.new("L", patch.size, 255).filter(ImageFilter.GaussianBlur(0))
    d = ImageDraw.Draw(fade)
    for i in range(40):                                     # feathered edges
        v = int(255 * i / 40)
        d.rectangle((i, i, patch.width - 1 - i, patch.height - 1 - i), outline=v)
    fade = fade.filter(ImageFilter.GaussianBlur(10))
    out.paste(patch, ERASE[:2], fade)
    return out


def mask_text(text, h):
    """The words as a hard mask whose capital height is h."""
    f = ImageFont.truetype(FONT, 400)
    l, t, r, b = f.getbbox("FINALE")
    f = ImageFont.truetype(FONT, int(400 * h / (b - t)))
    l, t, r, b = f.getbbox(text)
    m = Image.new("L", (r - l + 4, b - t + 4), 0)
    ImageDraw.Draw(m).text((2 - l, 2 - t), text, font=f, fill=255)
    return m


def tear(m, seed, n=5):
    rnd = random.Random(seed)
    out = Image.new("L", (m.width + 40, m.height), 0)
    out.paste(m, (20, 0))
    for _ in range(n):
        y = rnd.randrange(int(m.height * 0.15), int(m.height * 0.85))
        h = rnd.randrange(8, 16)
        band = out.crop((0, y, out.width, y + h))
        out.paste(0, (0, y, out.width, y + h))
        out.paste(band, (rnd.choice((-1, 1)) * rnd.randrange(10, 22), y))
    return out


def neon(canvas, m, x, y, st):
    pad = 70
    W, H = m.width + 2 * pad, m.height + 2 * pad
    mm = Image.new("L", (W, H), 0)
    mm.paste(m, (pad, pad))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = mm.filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(18))
    layer.paste((*st["glow"], 255), (0, 0), glow.point(lambda v: min(255, int(v * 1.35))))
    layer.paste((*YELLOW, 255), (0, 0), ImageChops.offset(mm, 7, 5))
    layer.paste((*CYAN, 255), (0, 0), ImageChops.offset(mm, -7, -5))
    layer.paste((*st["face"], 255), (0, 0), mm)
    layer = layer.filter(ImageFilter.GaussianBlur(1.3))
    canvas.alpha_composite(layer, (x - pad, y - pad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("thumb")
    ap.add_argument("out")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--of", type=int, default=5)
    ap.add_argument("--style", default="hot", choices=sorted(STYLES))
    a = ap.parse_args()
    st = STYLES[a.style]
    img = erase(Image.open(a.thumb).convert("RGB").resize((2160, 3840), Image.LANCZOS)).convert("RGBA")
    word = tear(mask_text("FINALE", HEIGHT), 7)
    num = tear(mask_text(f"{a.n}/{a.of}", HEIGHT), 11, n=3)
    gap = 70
    total = word.width + gap + num.width
    k = min(1.0, (2160 - 260) / total)
    if k < 1.0:
        word = word.resize((int(word.width * k), int(word.height * k)), Image.LANCZOS)
        num = num.resize((int(num.width * k), int(num.height * k)), Image.LANCZOS)
        total = word.width + gap + num.width
    x = (2160 - total) // 2
    y = TOP + (HEIGHT - word.height) // 2
    neon(img, word, x, y, st)
    # n/5 in its own colour: the series' magenta (neon) or gold (hot), still black-rimmed glitch
    pad = 70
    W, H = num.width + 2 * pad, num.height + 2 * pad
    mm = Image.new("L", (W, H), 0)
    mm.paste(num, (pad, pad))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = mm.filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(18))
    layer.paste((*st["glow"], 255), (0, 0), glow.point(lambda v: min(255, int(v * 1.35))))
    layer.paste((0, 0, 0, 255), (0, 0), mm.filter(ImageFilter.MaxFilter(19)))
    layer.paste((*CYAN, 255), (0, 0), ImageChops.offset(mm, -8, -5))
    layer.paste((255, 40, 210, 255), (0, 0), ImageChops.offset(mm, 8, 5))
    layer.paste((*st["slash"], 255), (0, 0), mm)
    layer = layer.filter(ImageFilter.GaussianBlur(1.2))
    img.alpha_composite(layer, (x + word.width + gap - pad, y + (word.height - num.height) // 2 - pad))
    img.convert("RGB").save(a.out, quality=95)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
