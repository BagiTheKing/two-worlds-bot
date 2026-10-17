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
    """A small readout that flickers like a failing display. With "steps" it
    counts down (e.g. REALITY 100% -> 3%) on the erasure pops."""
    rnd = random.Random(f)
    if rnd.random() < 0.08:                      # drop-out frames
        return
    pct = None
    if o.get("_steps"):
        k = sum(1 for x in o["_steps"] if x <= t)
        a, b = o["count_from"], o["count_to"]
        pct = round(a - (a - b) * k / len(o["_steps"]))
    text = o["text"].format(pct=pct)
    low = pct is not None and pct < 30 or pct is None
    d = ImageDraw.Draw(img)
    x, y = 70 + rnd.choice((0, 0, 0, 3, -3)), 150
    for dx, col in ((-4, (255, 0, 200)), (4, (0, 230, 255))):
        d.text((x + dx, y), text, font=fonts["mono"], fill=col)
    d.text((x, y), text, font=fonts["mono"], fill=(255, 120, 150) if low else (245, 245, 245))


def label(img, o, t, f, fonts):
    """Episode number and title, small, at the top."""
    a, b = o["start"], o["end"]
    k = min(1.0, (t - a) / 0.3, (b - t) / 0.3)
    if k <= 0:
        return
    layer = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((W // 2, 70), o["text"], font=fonts["small"], fill=(255, 255, 255, int(235 * k)),
           anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, int(200 * k)))
    if o.get("sub"):
        d.text((W // 2, 125), o["sub"], font=fonts["mid"], fill=(255, 210, 63, int(255 * k)),
               anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, int(200 * k)))
    img.paste(layer, (0, 210), layer)


def achievement(img, o, t, f, fonts):
    """The world's own system notification, in the series' glitch style."""
    a, b = o["start"], o["end"]
    slide = min(1.0, (t - a) / 0.25, (b - t) / 0.25)
    if slide <= 0:
        return
    w, h = 980, 250
    x = (W - w) // 2
    y = int(-h + (h + 330) * (1 - (1 - slide) ** 3))
    jitter = random.Random(f).choice((0, 0, 0, 0, 4, -4))
    panel = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    for dx, col in ((-6, (255, 0, 200, 255)), (6, (0, 230, 255, 255))):
        d.rectangle((10 + dx, 10, w + 10 + dx, h + 10), outline=col, width=4)
    d.rectangle((10, 10, w + 10, h + 10), fill=(8, 6, 14, 238), outline=(255, 255, 255, 255), width=3)
    cx, cy = 125, 10 + h // 2
    d.polygon([(cx, cy - 62), (cx + 62, cy), (cx, cy + 62), (cx - 62, cy)], fill=(255, 0, 200, 255))
    d.polygon([(cx, cy - 34), (cx + 34, cy), (cx, cy + 34), (cx - 34, cy)], fill=(8, 6, 14, 255))
    d.text((220, 75), o["title"], font=fonts["mono_small"], fill=(0, 230, 255, 255), anchor="lm")
    size = 62
    while size > 26:                              # shrink the text until it fits
        fnt = ImageFont.truetype(FONT, size)
        if d.textlength(o["text"], font=fnt) <= w - 230:
            break
        size -= 2
    d.text((220, 150), o["text"], font=fnt, fill=(255, 255, 255, 255), anchor="lm")
    if o.get("sub"):
        d.text((220, 212), o["sub"], font=fonts["small"], fill=(255, 120, 200, 255), anchor="lm")
    img.paste(panel, (x - 10 + jitter, y - 10), panel)


def endcard(img, o, t, f, fonts):
    """Series title, to be continued, what's next, and a question for the
    audience. Elements arrive one after another."""
    img.paste((4, 3, 8), (0, 0, W, H))
    d = ImageDraw.Draw(img)
    k = t - o["start"]
    rnd = random.Random(f)

    def at(sec):
        return k >= sec

    big = fonts["title"]
    if at(0.0):
        d.text((W // 2, 600), "TWO WORLDS", font=big, fill=(255, 255, 255), anchor="mm")
    if at(0.25):
        g = rnd.choice((0, 0, 0, 6, -6))
        for dx, col in ((-6 + g, (0, 230, 255)), (6 + g, (255, 0, 200))):
            d.text((W // 2 + dx, 740), "ONE GLITCH", font=big, fill=col, anchor="mm")
        d.text((W // 2 + g, 740), "ONE GLITCH", font=big, fill=(255, 255, 255), anchor="mm")
    if at(0.7):
        shown = o.get("tbc", "TO BE CONTINUED...")[:int((k - 0.7) / 0.04)]
        d.text((W // 2, 930), shown, font=fonts["mono"], fill=(220, 220, 220), anchor="mm")
    if at(1.5):
        d.text((W // 2, 1090), o["next_label"], font=fonts["small"], fill=(255, 210, 63), anchor="mm")
        d.text((W // 2, 1150), o["next_title"], font=fonts["mid"], fill=(255, 255, 255), anchor="mm")
    if at(2.2):
        d.text((W // 2, 1340), o["question"], font=fonts["big"], fill=(255, 59, 212), anchor="mm")
        d.text((W // 2, 1420), o["question_sub"], font=fonts["small"], fill=(200, 200, 210), anchor="mm")


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


DRAW = {"hud": hud, "achievement": achievement, "card": card, "fade_in": fade_in,
        "label": label, "endcard": endcard}
FULL = ("card", "fade_in", "endcard")


def read_clip(path):
    """All frames of a short clip, as 1080x1920 images."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vf", f"scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (W * H * 3)
    return [Image.frombytes("RGB", (W, H), raw[i * W * H * 3:(i + 1) * W * H * 3]) for i in range(n)]


def main(timeline, frames_dir, audio, out):
    tl = json.load(open(timeline))
    fps = tl["fps"]
    n_frames = int(round((tl["length"] + 0.4) * fps)) + 1
    caps = []
    for ln in tl["lines"]:
        color = tl["cast"][ln["who"]]["caption"]
        caps += [(a, b, txt, color) for a, b, txt in chunks(ln)]
    font = ImageFont.truetype(FONT, 92)
    fonts = {"mono": ImageFont.truetype(MONO, 54), "mono_small": ImageFont.truetype(MONO, 40),
             "big": ImageFont.truetype(FONT, 80), "mid": ImageFont.truetype(FONT, 50),
             "small": ImageFont.truetype(FONT, 38), "title": ImageFont.truetype(FONT, 130)}
    overlays = tl.get("overlays", [])
    clips = []                                    # ready-made footage replaces the render
    for o in [o for o in overlays if o["type"] == "clip"]:
        clips.append((o["start"], o["end"], read_clip(os.path.join(HERE, "..", o["video"]))))
    overlays = [o for o in overlays if o["type"] != "clip"]
    for o in overlays:
        if o.get("steps"):
            steps = o["steps"] if isinstance(o["steps"], list) else [o["steps"]]
            o["_steps"] = sorted(sum((tl.get("fx_times", {}).get(s, []) for s in steps), []))
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
        for c0, c1, frames in clips:
            if c0 <= t < c1 and frames:
                img = frames[min(len(frames) - 1, int(round((t - c0) * fps)))].copy()
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        img = Image.composite(black, img, vig)
        for o in overlays:                        # full-frame ones first
            if o["type"] in FULL and o["start"] <= t < o["end"]:
                DRAW[o["type"]](img, o, t, f, fonts)
        for a, b, txt, color in caps:
            if a <= t < b:
                pop = min(1.0, (t - a) / 0.08)
                size = int(92 * (0.82 + 0.18 * pop))
                fnt = font if size == 92 else ImageFont.truetype(FONT, size)
                ImageDraw.Draw(img).text((W // 2, CAPTION_Y), txt, font=fnt, fill=color,
                                         anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0))
        for o in overlays:
            if o["type"] not in FULL and o["start"] <= t < o["end"]:
                DRAW[o["type"]](img, o, t, f, fonts)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out, n_frames, "frames")


if __name__ == "__main__":
    main(*sys.argv[1:5])
