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


DRAW = {"watermark": watermark, "timer": timer, "hud": hud, "achievement": achievement, "card": card, "fade_in": fade_in,
        "label": label, "endcard": endcard, "hook": hook, "prompt": prompt}
FULL = ("card", "fade_in", "endcard")


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
