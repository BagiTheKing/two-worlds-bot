"""
Final pass: upscale the rendered frames to 1080x1920, draw the overlays (HUD,
achievement pop-up, title cards, fades), burn in captions (short word groups
in each speaker's colour, with a small pop-in), add a soft vignette, and
encode with the episode audio. Frames that were not rendered (under a
full-black card) are drawn black.

    python src/assemble.py build/timeline.json build/frames build/audio.wav out.mp4
"""

import json
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "InterDisplay-Black.otf")
MONO = os.path.join(HERE, "..", "fonts", "FreeMonoBold.ttf")
CAPTION_Y = 1180          # above the Shorts UI at the bottom of the screen
MAX_WORDS = 3


def chunks(line):
    """Split a line into groups of up to MAX_WORDS words, timed by length."""
    words = line["text"].split()
    wide = ImageFont.truetype(FONT, 92)
    groups, cur = [], []
    for w in words:
        if cur and wide.getlength(" ".join(cur + [w]).upper()) > W - 140:   # keep it on screen
            groups.append(cur)
            cur = []
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


def fitted(text, size, max_w=W - 100, path=None):
    """The font at `size`, or smaller if `text` would not fit max_w."""
    path = path or FONT
    f = ImageFont.truetype(path, size)
    w = f.getlength(text)
    return f if w <= max_w else ImageFont.truetype(path, max(20, int(size * max_w / w)))


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
    pct = o.get("value")
    if o.get("_steps"):
        k = sum(1 for x in o["_steps"] if x <= t)
        a, b = o["count_from"], o["count_to"]
        pct = round(a - (a - b) * k / len(o["_steps"]))
    text = o["text"].format(pct=pct)
    low = o.get("alert") or (pct is not None and pct < 30) or (pct is None and "{pct}" in o["text"])
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
    if o.get("over"):                    # over the last shot: darken it, keep it moving
        dim = min(0.62, (t - o["start"]) / 0.4 * 0.62)
        img.paste(Image.blend(img, Image.new("RGB", (W, H), (4, 3, 8)), dim))
    else:
        img.paste((4, 3, 8), (0, 0, W, H))
    d = ImageDraw.Draw(img)
    k = (t - o["start"]) / o.get("pace", 1.0)       # pace < 1: everything arrives sooner
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
        d.text((W // 2, 1340), o["question"], font=fitted(o["question"], 80), fill=(255, 59, 212), anchor="mm")
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


def hook(img, o, t, f, fonts):
    """The first-seconds hook: one big line that pops in."""
    a, b = o["start"], o["end"]
    k = min(1.0, (t - a) / 0.12, (b - t) / 0.15)
    if k <= 0:
        return
    size = int(104 * (0.85 + 0.15 * min(1.0, (t - a) / 0.12)))
    fnt = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(img)
    y = o.get("y", 560)
    for i, line in enumerate(o["text"].split("\n")):
        d.text((W // 2, y + i * int(size * 1.1)), line, font=fnt, fill=o.get("color", "#FFFFFF"),
               anchor="mm", stroke_width=12, stroke_fill=(0, 0, 0))


def prompt(img, o, t, f, fonts):
    """A small mid-video nudge to comment, in the series' glitch style."""
    a, b = o["start"], o["end"]
    k = min(1.0, (t - a) / 0.2, (b - t) / 0.2)
    if k <= 0:
        return
    fnt = ImageFont.truetype(FONT, 54)
    layer = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = d.textlength(o["text"], font=fnt) + 80
    x0 = (W - w) / 2
    d.rounded_rectangle((x0, 20, x0 + w, 130), radius=26, fill=(8, 6, 14, int(220 * k)),
                        outline=(255, 59, 212, int(255 * k)), width=4)
    d.text((W // 2, 75), o["text"], font=fnt, fill=(255, 255, 255, int(255 * k)), anchor="mm")
    img.paste(layer, (0, o.get("y", 1500)), layer)


def tutorial(img, o, t, f, fonts):
    """The obby's cheerful tutorial pop-up (the Noob's world talking): a white
    rounded panel with a bouncing arrow pointing down at what it means."""
    a, b = o["start"], o["end"]
    k = min(1.0, (t - a) / 0.15, (b - t) / 0.15)
    if k <= 0:
        return
    pop = 1.0 + 0.12 * max(0.0, 1 - (t - a) / 0.25)                 # a little overshoot on arrival
    layer = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    small = ImageFont.truetype(FONT, int(40 * pop))
    big = ImageFont.truetype(FONT, int(70 * pop))
    w = max(d.textlength(o["text"], font=big), 360) + 90
    x0 = (W - w) / 2
    alpha = int(255 * k)
    up = o.get("arrow", "down") == "up"             # pointing at something above the panel
    top = 300 if up else 20
    d.rounded_rectangle((x0 + 8, top + 8, x0 + w + 8, top + 208), radius=34, fill=(0, 0, 0, int(90 * k)))
    d.rounded_rectangle((x0, top, x0 + w, top + 200), radius=34, fill=(250, 250, 252, alpha),
                        outline=(40, 160, 255, alpha), width=6)
    d.text((W // 2, top + 52), o.get("title", "TUTORIAL"), font=small, fill=(40, 160, 255, alpha), anchor="mm")
    d.text((W // 2, top + 130), o["text"], font=big, fill=(30, 30, 40, alpha), anchor="mm")
    bob = 26 * abs(math.sin(2 * math.pi * 1.6 * (t - a)))
    ax = o.get("arrow_x", W // 2)
    sgn, ay = (-1, 270 - bob) if up else (1, 260 + bob)
    d.polygon([(ax - 26, ay), (ax + 26, ay), (ax + 26, ay + 90 * sgn), (ax + 62, ay + 90 * sgn),
               (ax, ay + 170 * sgn), (ax - 62, ay + 90 * sgn), (ax - 26, ay + 90 * sgn)],
              fill=(255, 210, 40, alpha), outline=(30, 30, 40, alpha))
    img.paste(layer, (0, o.get("y", 330)), layer)


def watermark(img, o, t, f, fonts):
    """The channel handle, small and quiet, top-right on every frame."""
    fnt = ImageFont.truetype(FONT, o.get("size", 40))
    layer = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((W - 48, 60), o["text"], font=fnt, fill=(255, 255, 255, int(255 * o.get("opacity", 0.55))),
           anchor="rm", stroke_width=3, stroke_fill=(0, 0, 0, int(160 * o.get("opacity", 0.55))))
    img.paste(layer, (0, o.get("y", 70)), layer)


def timer(img, o, t, f, fonts):
    """A stopwatch on someone's plan: counts up, then fails at `fail_after`
    seconds (shaking, in red)."""
    el = t - o["start"]
    fail = o.get("fail_after", 3.0)
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype(MONO, 66)
    if el < fail:
        text, col, dx = f"{o.get('label', 'PLAN')}: {el:4.2f}s", (245, 245, 245), 0
    else:
        k = el - fail
        text, col = f"{o.get('label', 'PLAN')} FAILED: {fail:4.2f}s", (255, 70, 90)
        dx = int(14 * math.sin(60 * k) * max(0.0, 1 - k / 0.35))
    x, y = W // 2 + dx, o.get("y", 430)
    for ox, c in ((-4, (255, 0, 200)), (4, (0, 230, 255))):
        d.text((x + ox, y), text, font=fnt, fill=c, anchor="mm")
    d.text((x, y), text, font=fnt, fill=col, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))


def flash(img, o, t, f, fonts):
    """An impact flash (white, or o["color"]), fading out."""
    k = 1 - (t - o["start"]) / max(1e-6, o["end"] - o["start"])
    col = tuple(o.get("color", (255, 255, 255)))
    img.paste(Image.blend(img, Image.new("RGB", img.size, col), max(0.0, min(1.0, k)) * o.get("strength", 0.85)))


def memory(img, o, t, f, fonts):
    """The past, as Patch remembers it: colours pulled toward cyan and lifted
    (never darker), faint scanlines, a colour fringe that grows toward the
    edges, and a slow, gentle flicker. Eases in and out over 0.3 s."""
    import numpy as np
    k = min(1.0, (t - o["start"]) / 0.3, (o["end"] - t) / 0.3)
    if k <= 0:
        return
    a = np.asarray(img, dtype=np.float32) / 255.0
    lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
    tint = np.stack([lum * 0.62, lum * 1.0, lum * 1.08], -1) * 1.15 + np.array([0.03, 0.07, 0.08], np.float32)
    # strong magenta (Null, Patch's glitching eye) keeps its colour
    keep = np.clip(((a[..., 0] + a[..., 2]) / 2 - a[..., 1]) * 3.0, 0, 1)[..., None]
    amt = 0.4 * k * (1 - keep)
    g = a * (1 - amt) + tint * amt
    sh = int(round(4 * k))                                     # colour fringe, strongest at the sides
    if sh:
        r = np.roll(g[..., 0], sh, axis=1)
        b = np.roll(g[..., 2], -sh, axis=1)
        w = (np.abs(np.linspace(-1, 1, g.shape[1], dtype=np.float32)) ** 1.5)[None, :]
        g[..., 0] = g[..., 0] * (1 - w) + r * w
        g[..., 2] = g[..., 2] * (1 - w) + b * w
    g[::4] *= 1 - 0.10 * k                                   # scanlines
    g *= 1 + 0.025 * k * math.sin(f * 0.9) + 0.015 * k * math.sin(f * 2.3)
    img.paste(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)))


def warp(img, o, t, f, fonts):
    """Patch takes them back: the beam from his eye, end-on, grows from a
    glowing point (colour cycling cyan, white, magenta) into a burst with
    rings and rushing streaks that swallows the whole screen, then white.
    o["at"]: [[time, x, y], ...] the eye on screen (fractions), o["grow"]:
    when the burst starts, o["full"]: when it covers everything."""
    from PIL import ImageFilter
    pts = o["at"]
    if t <= pts[0][0]:
        x, y = pts[0][1:]
    elif t >= pts[-1][0]:
        x, y = pts[-1][1:]
    else:
        for (t0, x0, y0), (t1, x1, y1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / max(1e-6, t1 - t0)
                x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                break
    cx, cy = x * W, y * H
    g0, g1 = o["grow"], o["full"]
    cols = [(0, 230, 255), (255, 255, 255), (255, 40, 210), (0, 230, 255)]
    ph = (t - o["start"]) * 3.2
    c0, c1 = cols[int(ph) % 4], cols[(int(ph) + 1) % 4]
    u = ph - int(ph)
    col = tuple(int(a + (b - a) * u) for a, b in zip(c0, c1))
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    if t < g0:                                       # the charge: a pulsing core and rings
        k = (t - o["start"]) / max(1e-6, g0 - o["start"])
        r = 18 + 50 * k + 8 * math.sin(t * 40)
        for i in range(3):
            rr = r * (1.6 + i * 0.9) + 30 * ((t * 3 + i * 0.33) % 1.0)
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=col, width=max(2, int(6 * k)))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
        layer = layer.filter(ImageFilter.GaussianBlur(10 + 10 * k))
        d = ImageDraw.Draw(layer)
        d.ellipse((cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45), fill=(255, 255, 255))
        img.paste(ImageChops.add(img, layer))
        return
    k = min(1.0, (t - g0) / max(1e-6, g1 - g0))         # the burst
    R = 60 + (math.hypot(W, H) * 1.05) * (k ** 1.6)
    rnd = random.Random(int(t * 1000))
    for i in range(48):                              # warp streaks rushing outward
        a = rnd.uniform(0, 2 * math.pi)
        r0 = R * rnd.uniform(0.3, 0.9)
        r1 = r0 + 200 + 900 * k
        d.line((cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * r1, cy + math.sin(a) * r1),
               fill=rnd.choice(((255, 255, 255), col, (120, 240, 255))), width=rnd.randint(3, 9))
    for i in range(4):                               # rings riding the front
        rr = R * (0.55 + 0.15 * i)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=cols[i % 3], width=int(10 + 30 * k))
    d.ellipse((cx - R * 0.5, cy - R * 0.5, cx + R * 0.5, cy + R * 0.5), fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(6 + 14 * k))
    img.paste(ImageChops.add(img, layer))
    if k > 0.6:                                      # into white
        img.paste(Image.blend(img, Image.new("RGB", (W, H), (235, 252, 255)), min(1.0, (k - 0.6) / 0.4)))


def grade(img, o, t, f, fonts):
    """The look of the reference animations: richer colour, a soft glow
    around everything bright, warm light, and (with o["sun"] = [x, y] on
    screen, fractions) rays streaming from the sun through the trees.
    Worked on a quarter-size copy, so it is quick."""
    import numpy as np
    from PIL import ImageFilter
    sat = o.get("saturation", 1.22)
    a = np.asarray(img, dtype=np.float32) / 255.0
    lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
    a = lum[..., None] + (a - lum[..., None]) * sat                       # richer colour
    a = a * np.array(o.get("tint", (1.03, 1.0, 0.95)), np.float32)        # warm light
    small = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    s_ = np.asarray(small, dtype=np.float32) / 255.0
    bright = np.clip((s_ - o.get("threshold", 0.72)) / 0.28, 0, 1) * s_
    glow = np.asarray(Image.fromarray((bright * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)),
                      dtype=np.float32) / 255.0
    add = glow * o.get("glow", 0.55)
    if o.get("sun"):                                                      # rays: the bright parts, smeared from the sun
        sx, sy = o["sun"][0] * (W // 4), o["sun"][1] * (H // 4)
        src = Image.fromarray((bright * 255).astype(np.uint8))
        acc = np.zeros_like(bright)
        steps = 14
        for k in range(1, steps + 1):
            z = 1 + 0.045 * k
            w2, h2 = int(src.width * z), int(src.height * z)
            big = src.resize((w2, h2), Image.BILINEAR)
            ox, oy = int(sx * z - sx), int(sy * z - sy)
            acc += np.asarray(big.crop((ox, oy, ox + src.width, oy + src.height)), dtype=np.float32) / 255.0 * (1 - k / (steps + 1))
        add = add + acc / steps * o.get("rays", 0.9) * np.array((1.0, 0.92, 0.75), np.float32)
    up = np.asarray(Image.fromarray((np.clip(add, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                    dtype=np.float32) / 255.0
    a = 1 - (1 - np.clip(a, 0, 1)) * (1 - up)                             # screen blend: light adds, never burns
    img.paste(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)))


def chat(img, o, t, f, fonts):
    """The game's chat, bottom left: messages pop in and fade after 4 s.
    o["lines"]: [{"at": seconds, "text": ..., "color": [r, g, b]}]."""
    d = ImageDraw.Draw(img, "RGBA")
    shown = [m for m in o["lines"] if m["at"] <= t < m["at"] + 4.0]
    y = o.get("y", 1430)
    for m in reversed(shown):
        age = t - m["at"]
        k = min(1.0, (4.0 - age) / 0.6)
        fnt = fonts["mono"]
        w = int(d.textlength(m["text"], font=fnt)) + 28
        d.rectangle((24, y - 34, 24 + w, y + 30), fill=(0, 0, 0, int(120 * k)))
        col = tuple(m.get("color", (255, 255, 255)))
        d.text((40 + 3, y + 3), m["text"], font=fnt, fill=(40, 40, 40, int(255 * k)), anchor="lm")
        d.text((40, y), m["text"], font=fnt, fill=(*col, int(255 * k)), anchor="lm")
        y -= 70


def endnote(img, o, t, f, fonts):
    """The ending without a card: the last shot keeps playing, a soft shade
    rises at the bottom with what's next and the question."""
    k = min(1.0, (t - o["start"]) / 0.3)
    shade = Image.new("L", (1, 560))
    for y in range(560):
        shade.putpixel((0, y), int(185 * k * (y / 560) ** 1.4))
    shade = shade.resize((W, 560))
    img.paste((4, 3, 8), (0, H - 560), shade)
    d = ImageDraw.Draw(img)
    y0 = H - 470
    d.text((W // 2, y0), o["next_label"], font=fonts["small"], fill=(255, 210, 63), anchor="mm")
    if o.get("highlight"):                       # the title big, in the series' cyan/magenta glitch
        fnt = fitted(o["next_title"], 120, W - 120)
        g = random.Random(f).choice((0, 0, 0, 5, -5))
        for dx, col in ((-6 + g, (0, 230, 255)), (6 + g, (255, 0, 200))):
            d.text((W // 2 + dx, y0 + 85), o["next_title"], font=fnt, fill=col, anchor="mm")
        d.text((W // 2 + g, y0 + 85), o["next_title"], font=fnt, fill=(255, 255, 255), anchor="mm")
    else:
        d.text((W // 2, y0 + 62), o["next_title"], font=fitted(o["next_title"], 54, W - 120),
               fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    dq = 40 if o.get("highlight") else 0
    d.text((W // 2, y0 + 170 + dq), o["question"], font=fitted(o["question"], 84, W - 120),
           fill=(255, 59, 212), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((W // 2, y0 + 250 + dq), o["question_sub"], font=fonts["small"], fill=(220, 220, 230), anchor="mm")


_HOLO_CACHE = {}


def holo(img, o, t, f, fonts):
    """Patch's projected screen: a piece of an earlier episode inside a glowing
    cyan frame, above the captions. It flickers on (a bright line opening
    out) and off; scanlines, a slight cyan cast and a label ("ARCHIVE · EP 3").
    The source is cropped to the middle of its picture (no HUD, no captions)."""
    import numpy as np
    from PIL import ImageFilter
    a, b = o["start"], o["end"]
    fps = o.get("fps", 24)
    bw, bh = o.get("w", 900), o.get("h", 750)
    cx, top = W // 2, o.get("y", 250)
    # one clip ("video"), or several in turn ("clips": [{"at", "video", "offset"}]):
    # the screen stays on and switches with a two-frame glitch
    clips = o.get("clips") or [{"at": a, "video": o["video"], "offset": o.get("offset", 0.0)}]
    cur = max((c for c in clips if c["at"] <= t + 1e-6), key=lambda c: c["at"], default=clips[0])
    for k in list(_HOLO_CACHE):                     # only this screen's clips stay in memory
        if k not in {c["video"] for c in clips}:
            del _HOLO_CACHE[k]
    if cur["video"] not in _HOLO_CACHE:
        _HOLO_CACHE[cur["video"]] = read_holo_clip(os.path.join(HERE, "..", cur["video"]), bw, bh,
                                                   crop=o.get("crop", False))
    frames = _HOLO_CACHE[cur["video"]]
    pic = frames[max(0, min(len(frames) - 1, int((t - cur["at"] + cur.get("offset", 0.0)) * fps)))]
    switch = cur is not clips[0] and t - cur["at"] < 2 / fps
    arr = np.asarray(pic, dtype=np.float32)
    arr = (arr - 128) * 1.12 + 128                                              # a touch more contrast
    arr = arr * 0.92 + np.array((40, 160, 200), np.float32) * 0.08              # a light cyan cast
    arr[::4] *= 0.9                                                             # scanlines
    if switch:                                                                  # a channel change
        rr = random.Random(f)
        for _ in range(6):
            y0_, h_ = rr.randrange(0, bh - 40), rr.randrange(10, 60)
            arr[y0_:y0_ + h_] = np.roll(arr[y0_:y0_ + h_], rr.randrange(-80, 80), axis=1)
        arr = arr * 0.8 + 255 * 0.2
    pic = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    k_on = min(1.0, (t - a) / 0.28)
    k_off = min(1.0, (b - t) / 0.2)
    k = max(0.0, min(k_on, k_off))
    open_y = max(0.02, k ** 0.6)                                                # opening from a line
    ph = max(2, int(bh * open_y))
    pic = pic.resize((bw, ph))
    x0, y0 = cx - bw // 2, top + (bh - ph) // 2
    glow = Image.new("RGBA", (bw + 120, ph + 120), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((60 - 8, 60 - 8, 60 + bw + 8, 60 + ph + 8), 18, outline=(60, 230, 255, 230), width=10)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img.paste(glow, (x0 - 60, y0 - 60), glow)
    alpha = int(255 * (0.93 if k >= 1 else 0.6 + 0.35 * k))
    if random.Random(f).random() < 0.05:
        alpha = int(alpha * 0.7)                                                # a flicker
    mask = Image.new("L", (bw, ph), alpha)
    img.paste(pic, (x0, y0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0 - 4, y0 - 4, x0 + bw + 4, y0 + ph + 4), 14, outline=(150, 245, 255), width=4)
    if k_on < 1:                                                                # the bright opening line
        d.rectangle((x0, top + bh // 2 - 3, x0 + bw, top + bh // 2 + 3), fill=(220, 255, 255))
    if k > 0.6 and o.get("label"):
        lab = o["label"]
        fnt = fonts["mono_small"]
        tw = fnt.getlength(lab)
        # a tab on top of the frame, outside the picture: the old clips have
        # their own banners (achievements) in their top corner
        d.rounded_rectangle((x0 + 10, y0 - 62, x0 + 34 + tw, y0 + 2), 10, fill=(4, 24, 32),
                            outline=(150, 245, 255), width=4)
        d.rectangle((x0 + 14, y0 - 4, x0 + 30 + tw, y0 + 2), fill=(4, 24, 32))
        d.text((x0 + 22, y0 - 56), lab, font=fnt, fill=(120, 240, 255))


def comment(img, o, t, f, fonts):
    """A YouTube comment, dark mode: round avatar with an initial, @handle,
    the comment text (one phrase highlighted as it is read), like/dislike/Reply."""
    a = o["start"]
    k = min(1.0, (t - a) / 0.22)
    s = 1.0 + 0.08 * math.sin(min(1.0, k) * math.pi)                          # a small overshoot
    if k <= 0:
        return
    cw = 940
    name_f = ImageFont.truetype(FONT, 40)
    text_f = ImageFont.truetype(FONT, 50)
    small_f = ImageFont.truetype(FONT, 34)
    words = o["text"].split()
    lines, cur = [], ""
    for w_ in words:                                                            # wrap to the card
        if text_f.getlength((cur + " " + w_).strip()) > cw - 190:
            lines.append(cur)
            cur = w_
        else:
            cur = (cur + " " + w_).strip()
    lines.append(cur)
    chh = 150 + 66 * len(lines) + 90
    card = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, chh - 1), 34, fill=(24, 24, 24, 245), outline=(70, 70, 70, 255), width=2)
    d.ellipse((36, 40, 136, 140), fill=tuple(o.get("avatar_color", (0, 137, 123))))
    d.text((86, 90), o.get("initial", "Y"), font=ImageFont.truetype(FONT, 56), fill=(255, 255, 255), anchor="mm")
    d.text((162, 46), o["handle"], font=name_f, fill=(241, 241, 241))
    hl = o.get("highlight", "")
    y = 108
    hk = max(0.0, min(1.0, (t - o.get("hl_start", a + 0.8)) / o.get("hl_dur", 1.6)))
    for ln in lines:
        x = 162
        if hl and hk > 0:
            lo = ln.lower()
            i = lo.find(hl.lower()[:12]) if hl.lower()[:12] in lo else -1
            if i >= 0 or any(w_.lower() in hl.lower() for w_ in ln.split()[:1]):
                pass
        d.text((x, y), ln, font=text_f, fill=(241, 241, 241))
        y += 66
    if hl and hk > 0:                                                           # the highlight sweep, under the phrase
        full = " ".join(lines)
        y = 108
        for ln in lines:
            for w_ in ln.split():
                pass
        # mark each word of the phrase where it sits
        pos = []
        y = 108
        for ln in lines:
            x = 162
            for w_ in ln.split(" "):
                ww = text_f.getlength(w_)
                pos.append((w_, x, y, ww))
                x += ww + text_f.getlength(" ")
            y += 66
        target = hl.lower().split()
        n_t = len(target)
        for i in range(len(pos) - n_t + 1):
            if [p[0].lower().strip(".,!?\"'…") for p in pos[i:i + n_t]] == [w_.strip(".,!?\"'…") for w_ in target]:
                upto = hk * n_t
                for j, (w_, x, yy, ww) in enumerate(pos[i:i + n_t]):
                    part = max(0.0, min(1.0, upto - j))
                    if part > 0:
                        ww = ww + (text_f.getlength(" ") if j < n_t - 1 and part >= 1 else 0)   # one continuous band
                        hb = Image.new("RGBA", (int(ww * part) + 8, 60), (255, 210, 63, 90))
                        card.alpha_composite(hb, (int(x) - 4, yy + 2))
                        d.line((x, yy + 60, x + ww * part, yy + 60), fill=(255, 210, 63), width=5)
                break
    y = 108 + 66 * len(lines) + 24
    gray = (170, 170, 170)

    def thumb(x, y, down=False):                                                # a simple outline thumb
        pts = [(x, y + 14), (x + 10, y + 14), (x + 10, y + 40), (x, y + 40)]
        d.polygon(pts, outline=gray, width=3)
        hand = [(x + 14, y + 16), (x + 22, y + 2), (x + 28, y + 4), (x + 26, y + 16), (x + 42, y + 16),
                (x + 40, y + 40), (x + 14, y + 40)]
        if down:
            pts = [(px, 2 * y + 42 - py) for px, py in pts]
            hand = [(px, 2 * y + 42 - py) for px, py in hand]
            d.polygon(pts, outline=gray, width=3)
        d.polygon(hand, outline=gray, width=3)

    thumb(162, y)
    thumb(262, y, down=True)
    d.text((352, y + 2), "Reply", font=small_f, fill=gray)
    if s != 1.0:
        card = card.resize((int(cw * s), int(chh * s)), Image.LANCZOS)
    al = card.split()[3].point(lambda v: int(v * k))
    card.putalpha(al)
    img.paste(card, (W // 2 - card.width // 2, o.get("y", 520) - card.height // 2), card)


def stack(img, o, t, f, fonts):
    """The loop: the picture steps back and shows the copies of itself behind
    it, one more every beat, like a deck of cards (we have been here before)."""
    u = t - o["start"]
    k_in = min(1.0, u / 0.25, max(0.0, (o["end"] - t) / 0.2))
    if k_in <= 0:
        return
    n = min(o.get("cards", 9), 1 + int(u / o.get("every", 0.16)))
    s0 = 1 - 0.2 * k_in
    base = img.copy()
    img.paste((150, 96, 200), (0, 0, W, H))
    rnd = random.Random(f // 2)
    for i in range(n, -1, -1):                       # the oldest first, the live one on top
        s = s0 * (0.93 ** i)
        w, h = int(W * s), int(H * s)
        card = base.resize((w, h), Image.BILINEAR)
        if i:
            tint = Image.new("RGB", (w, h), (255, 40, 220))
            card = Image.blend(card, tint, min(0.6, 0.1 + 0.07 * i))
        x = (W - w) // 2 + int((-34 * i + (rnd.choice((0, 0, 6, -6)) if i else 0)) * k_in)
        y = int(H * 0.58 - h * 0.5 - 46 * i * k_in)
        ImageDraw.Draw(img).rectangle((x - 5, y - 5, x + w + 4, y + h + 4), fill=(255, 255, 255) if i == 0 else (255, 120, 235))
        img.paste(card, (x, y))


def ffwd(img, o, t, f, fonts):
    """A tape running fast: torn scan lines and the >> mark."""
    import numpy as np
    rnd = random.Random(f)
    a = np.asarray(img).copy()
    for _ in range(5):
        y = rnd.randrange(0, H - 12)
        h = rnd.randrange(3, 12)
        a[y:y + h] = np.roll(a[y:y + h], rnd.randrange(-70, 70), axis=1)
        a[y:y + 2] = np.minimum(255, a[y:y + 2].astype(np.int16) + 70).astype(np.uint8)
    img.paste(Image.fromarray(a))
    d = ImageDraw.Draw(img)
    x, y = W - 250, 150
    for i in range(2):
        d.polygon([(x + i * 62, y), (x + i * 62 + 54, y + 34), (x + i * 62, y + 68)], fill=(255, 255, 255))
    d.text((x - 96, y + 6), "x4", font=fonts["mono"], fill=(255, 255, 255))


DRAW = {"stack": stack, "ffwd": ffwd, "holo": holo, "comment": comment, "grade": grade, "chat": chat, "warp": warp, "memory": memory, "endnote": endnote, "watermark": watermark, "timer": timer, "flash": flash, "hud": hud, "achievement": achievement, "card": card, "fade_in": fade_in,
        "label": label, "endcard": endcard, "hook": hook, "prompt": prompt, "tutorial": tutorial}
FULL = ("grade", "memory", "card", "fade_in", "endcard", "stack", "ffwd")


def read_holo_clip(path, bw, bh, crop=False):
    """A clip's frames as the holo screen shows them (bw x bh). The screen
    shows the episode as it was published, whole (a vertical screen for a
    vertical episode); crop=True keeps only the middle of a vertical picture."""
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", path],
                                   capture_output=True, text=True, check=True).stdout.strip().split(","))
    crop = f"scale={W}:{H},crop={W}:900:0:210," if crop and h > w else ""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vf", f"{crop}scale={bw}:{bh}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (bw * bh * 3)
    return [Image.frombytes("RGB", (bw, bh), raw[i * bw * bh * 3:(i + 1) * bw * bh * 3]) for i in range(n)]


def read_clip(path):
    """All frames of a short clip, as 1080x1920 images."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vf", f"scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (W * H * 3)
    return [Image.frombytes("RGB", (W, H), raw[i * W * H * 3:(i + 1) * W * H * 3]) for i in range(n)]


def retime_map(new_tl, old_tl):
    """Map a time in the new timeline to the same story moment in the old
    one (whose frames were rendered), so new voices can reuse old frames:
    every beat or line in both is an anchor; times between anchors are
    interpolated (moved beats shift, longer lines stretch slightly)."""
    anchors = [(0.0, 0.0)]
    lines = {ln["name"] for ln in new_tl.get("lines", [])}
    for name, (a, b) in new_tl["beats"].items():
        if name in old_tl["beats"]:
            oa, ob = old_tl["beats"][name]
            anchors.append((a, oa))
            if name not in lines:           # a line's end is set by its voice; what follows anchors it
                anchors.append((b, ob))
    anchors.sort()
    mono = [anchors[0]]
    for n, o in anchors[1:]:                     # keep it monotonic
        if n > mono[-1][0] and o >= mono[-1][1]:
            mono.append((n, o))
    nx = [a for a, _ in mono]
    ox = [b for _, b in mono]

    def to_old(t):
        if t <= nx[-1]:
            import bisect
            i = max(1, bisect.bisect_left(nx, t))
            a0, a1, b0, b1 = nx[i - 1], nx[i], ox[i - 1], ox[i]
            return b0 + (b1 - b0) * (t - a0) / max(1e-9, a1 - a0)
        return ox[-1] + (t - nx[-1])
    return to_old


def rewind_frame(o, t, f, frames_dir, fps):
    """A tape rewinding: earlier frames (o["src_from"]..o["src_to"]) played
    backwards, faster and faster, with VHS tracking bands, a colour split,
    noise lines and a rewind mark."""
    import numpy as np
    u = (t - o["start"]) / max(1e-6, o["end"] - o["start"])
    st = o["src_to"] - (o["src_to"] - o["src_from"]) * min(1.0, u ** 1.5)
    path = os.path.join(frames_dir, f"{int(round(st * fps)) + 1:04d}.png")
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGB")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    a = np.asarray(img, dtype=np.float32)
    rnd = random.Random(f)
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], 9, axis=1)                                 # colour split
    out[..., 2] = np.roll(a[..., 2], -9, axis=1)
    for _ in range(3):                                                          # tracking bands
        y0 = rnd.randrange(0, H - 120)
        hgt = rnd.randrange(30, 120)
        out[y0:y0 + hgt] = np.roll(out[y0:y0 + hgt], rnd.randrange(-80, 80), axis=1) * 0.8 + 50
    for _ in range(26):                                                         # noise lines
        y0 = rnd.randrange(0, H)
        out[y0:y0 + 3] = out[y0:y0 + 3] * 0.3 + 200
    lum = out @ np.array([0.3, 0.59, 0.11], np.float32)
    out = lum[..., None] + (out - lum[..., None]) * 0.75                        # tape colours
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    if (f // 6) % 2 == 0:                                                       # the blinking mark
        x, y = 90, 150
        for dx in (0, 70):
            d.polygon([(x + dx + 70, y), (x + dx + 70, y + 80), (x + dx, y + 40)], fill=(255, 255, 255))
        d.text((x + 170, y + 40), "REWIND", font=ImageFont.truetype(MONO, 60), fill=(255, 255, 255), anchor="lm")
    return img


def main(timeline, frames_dir, audio, out, source_timeline=None):
    """source_timeline: the timeline the frames were rendered for, when the
    audio has since been re-voiced (frames are retimed to match)."""
    tl = json.load(open(timeline))
    to_old = retime_map(tl, json.load(open(source_timeline))) if source_timeline else (lambda t: t)
    fps = tl["fps"]
    n_frames = int(round((tl["length"] + 0.4) * fps)) + 1
    caps = []
    for ln in tl["lines"]:
        if not ln.get("caption", True):
            continue
        color = tl["cast"][ln["who"]]["caption"]
        caps += [(a, b, txt, color) for a, b, txt in chunks(ln)]
    font = ImageFont.truetype(FONT, 92)
    fonts = {"mono": ImageFont.truetype(MONO, 54), "mono_small": ImageFont.truetype(MONO, 40),
             "big": ImageFont.truetype(FONT, 80), "mid": ImageFont.truetype(FONT, 50),
             "small": ImageFont.truetype(FONT, 38), "title": ImageFont.truetype(FONT, 130)}
    overlays = tl.get("overlays", [])
    clips = []                                    # ready-made footage replaces the render
    for o in [o for o in overlays if o["type"] == "clip"]:
        frames = read_clip(os.path.join(HERE, "..", o["video"]))
        need = o["end"] - o["start"]
        if len(frames) / fps < need - 0.05:      # would freeze on its last frame
            print(f"WARNING: {o['video']} is {len(frames) / fps:.2f}s but plays for {need:.2f}s; "
                  "its last frame will be held")
        clips.append((o["start"], o["end"], frames, o.get("graded", False)))
    overlays = [o for o in overlays if o["type"] != "clip"]
    for o in overlays:
        if o["type"] == "rewind":
            DRAW.setdefault("rewind", lambda *a_: None)       # drawn above, in place of the frame
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
        src = int(round(to_old(t) * fps)) + 1
        path = os.path.join(frames_dir, f"{src:04d}.png")
        img = Image.open(path).convert("RGB") if os.path.exists(path) else black.copy()
        graded = False
        for o in overlays:
            if o["type"] == "rewind" and o["start"] <= t < o["end"]:
                rw = rewind_frame(o, t, f, frames_dir, fps)
                if rw is not None:
                    img, graded = rw, True
        for c0, c1, frames, g in clips:
            if c0 <= t < c1 and frames:
                img = frames[min(len(frames) - 1, int(round((t - c0) * fps)))].copy()
                graded = g
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        if not graded:                          # a finished episode's frames already have it
            img = Image.composite(black, img, vig)
        for o in overlays:                        # full-frame ones first
            if o["type"] in FULL and o["start"] <= t < o["end"]:
                DRAW[o["type"]](img, o, t, f, fonts)
        row = 0
        for a, b, txt, color in caps:
            if a <= t < b:
                y = CAPTION_Y + 115 * row                  # lines said together stack
                row += 1
                pop = min(1.0, (t - a) / 0.08)
                size = int(92 * (0.82 + 0.18 * pop))
                fnt = fitted(txt, size, W - 140)
                ImageDraw.Draw(img).text((W // 2, y), txt, font=fnt, fill=color,
                                         anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0))
        for o in overlays:
            if o["type"] not in FULL and o["start"] <= t < o["end"]:
                DRAW[o["type"]](img, o, t, f, fonts)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out, n_frames, "frames")


if __name__ == "__main__":
    main(*sys.argv[1:6])
