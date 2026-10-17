"""
Final pass: upscale the rendered frames to 1080x1920, draw the overlays (HUD,
achievement pop-up, title cards, fades), burn in captions (short word groups
in each speaker's colour, with a small pop-in), add a soft vignette, and
encode with the episode audio. Frames that were not rendered (under a
full-black card) are drawn black.

    python src/assemble.py build/timeline.json build/frames build/audio.wav out.mp4
"""

import json
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "InterDisplay-Black.otf")
MONO = os.path.join(HERE, "..", "fonts", "FreeMonoBold.ttf")
CAPTION_Y = 1180          # above the Shorts UI at the bottom of the screen
MAX_WORDS = 3


def chunks(line):
    """Split a line into groups of up to MAX_WORDS words, timed by length."""
    words = line["text"].split()
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == MAX_WORDS or w[-1] in ".?!,":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    total = sum(len(" ".join(g)) + 2 for g in groups)
    t = line["start"]
    span = line["end"] - line["start"]
    out = []
    for g in groups:
        d = span * (len(" ".join(g)) + 2) / total
        out.append((t, t + d, " ".join(g).upper()))
        t += d
    return out


def vignette():
    v = Image.new("L", (W // 8, H // 8), 0)
    px = v.load()
    for y in range(H // 8):
        for x in range(W // 8):
            dx = (x - W / 16) / (W / 16)
            dy = (y - H / 16) / (H / 16)
            px[x, y] = int(255 * min(1, 0.32 * (dx * dx + dy * dy) ** 1.4))
    return v.resize((W, H), Image.BILINEAR)


# ---------------------------------------------------------------- overlays

def hud(img, o, t, f, fonts):
    """A small readout that flickers like a failing display."""
    rnd = random.Random(f)
    if rnd.random() < 0.08:                      # drop-out frames
        return
    d = ImageDraw.Draw(img)
    x, y = 70 + rnd.choice((0, 0, 0, 3, -3)), 150
    for dx, col in ((-4, (255, 0, 200)), (4, (0, 230, 255))):
        d.text((x + dx, y), o["text"], font=fonts["mono"], fill=col)
    d.text((x, y), o["text"], font=fonts["mono"], fill=(245, 245, 245))


def achievement(img, o, t, f, fonts):
    a, b = o["start"], o["end"]
    slide = min(1.0, (t - a) / 0.25, (b - t) / 0.25)
    if slide <= 0:
        return
    w, h = 900, 190
    x = (W - w) // 2
    y = int(-h + (h + 270) * (1 - (1 - slide) ** 3))
    panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=28, fill=(22, 22, 26, 235),
                        outline=(255, 210, 63, 255), width=5)
    d.rounded_rectangle((28, 35, 148, 155), radius=14, fill=(255, 210, 63, 255))
    d.text((88, 95), "★", font=fonts["big"], fill=(22, 22, 26, 255), anchor="mm")
    d.text((180, 60), o["title"], font=fonts["small"], fill=(255, 210, 63, 255), anchor="lm")
    size = 50
    while size > 24:                              # shrink the text until it fits
        fnt = ImageFont.truetype(FONT, size)
        if d.textlength(o["text"], font=fnt) <= w - 210:
            break
        size -= 2
    d.text((180, 125), o["text"], font=fnt, fill=(255, 255, 255, 255), anchor="lm")
    img.paste(panel, (x, y), panel)


def card(img, o, t, f, fonts):
    img.paste((0, 0, 0), (0, 0, W, H))
    shown = o["text"][:max(0, int((t - o["start"] - 0.25) / 0.05))]
    ImageDraw.Draw(img).text((W // 2, H // 2), shown, font=fonts["mid"],
                             fill=(235, 235, 235), anchor="mm")


def fade_in(img, o, t, f, fonts):
    k = 1 - (t - o["start"]) / max(1e-6, o["end"] - o["start"])
    if k > 0:
        black = Image.new("RGB", (W, H), (0, 0, 0))
        img.paste(Image.blend(img, black, k))


DRAW = {"hud": hud, "achievement": achievement, "card": card, "fade_in": fade_in}


def main(timeline, frames_dir, audio, out):
    tl = json.load(open(timeline))
    fps = tl["fps"]
    n_frames = int(round((tl["length"] + 0.4) * fps)) + 1
    caps = []
    for ln in tl["lines"]:
        color = tl["cast"][ln["who"]]["caption"]
        caps += [(a, b, txt, color) for a, b, txt in chunks(ln)]
    font = ImageFont.truetype(FONT, 92)
    fonts = {"mono": ImageFont.truetype(MONO, 54), "big": ImageFont.truetype(FONT, 80),
             "mid": ImageFont.truetype(FONT, 50), "small": ImageFont.truetype(FONT, 34)}
    overlays = tl.get("overlays", [])
    vig = vignette()
    black = Image.new("RGB", (W, H), (0, 0, 0))

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", audio,
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for f in range(1, n_frames + 1):
        t = (f - 1) / fps
        path = os.path.join(frames_dir, f"{f:04d}.png")
        img = Image.open(path).convert("RGB") if os.path.exists(path) else black.copy()
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        img = Image.composite(black, img, vig)
        for o in overlays:                        # full-frame ones first
            if o["type"] in ("card", "fade_in") and o["start"] <= t < o["end"]:
                DRAW[o["type"]](img, o, t, f, fonts)
        for a, b, txt, color in caps:
            if a <= t < b:
                pop = min(1.0, (t - a) / 0.08)
                size = int(92 * (0.82 + 0.18 * pop))
                fnt = font if size == 92 else ImageFont.truetype(FONT, size)
                ImageDraw.Draw(img).text((W // 2, CAPTION_Y), txt, font=fnt, fill=color,
                                         anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0))
        for o in overlays:
            if o["type"] not in ("card", "fade_in") and o["start"] <= t < o["end"]:
                DRAW[o["type"]](img, o, t, f, fonts)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out, n_frames, "frames")


if __name__ == "__main__":
    main(*sys.argv[1:5])
