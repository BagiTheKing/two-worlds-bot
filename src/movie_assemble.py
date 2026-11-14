"""The movie's assembly: a chapter's 16:9 frames with its overlays, in landscape.

The Shorts' assembly (assemble.py) is built for 1080x1920. This one reuses its
overlay drawing at 1920x1080 and changes what the movie changes
(story/creator_notes.md, "The movie"):
  - the Shorts packaging is dropped: episode labels, comment prompts, hooks,
    tutorials, end cards;
  - captions sit in the lower third, sized for landscape;
  - the REALITY readout is the movie's meter (movie_hud.Meter, approved
    version 6): hidden while still, glitching in for each wave of drops;
  - the watermark is on every frame.
The chapter ends at `--end` (seconds on the timeline); the sound is cut there
with a short fade (the join pass smooths it into the next chapter).

    python src/movie_assemble.py TIMELINE FRAMES AUDIO OUT.mp4 [--end 55.96] [--start 0]
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble as A                                                   # noqa: E402
from movie_hud import Meter                                            # noqa: E402

W, H = 1920, 1080
A.W, A.H = W, H                      # the Shorts' overlay drawers read these at call time
CAPTION_Y = 948                      # the lower third, clear of the frame's edge
CAPTION_SIZE = 66
DROP = {"label", "prompt", "hook", "tutorial", "endcard", "comment", "endnote", "hud"}
WATERMARK = "@GLITCHBOUND2469"


def meter_for(tl):
    """The REALITY meter from the timeline's hud overlays: a counting one (steps from fx_times), or a
    run of fixed readouts (REALITY: 99% then 97%), whose changes become the drops."""
    huds = [o for o in tl.get("overlays", []) if o["type"] == "hud" and "REALITY" in o.get("text", "")]
    if not huds:
        return None
    count = [o for o in huds if o.get("steps")]
    if count:
        o = count[0]
        names = o["steps"] if isinstance(o["steps"], list) else [o["steps"]]
        steps = sorted(sum((tl.get("fx_times", {}).get(s, []) for s in names), []))
        return Meter(steps, start=o["start"], end=o["end"], count_from=o["count_from"], count_to=o["count_to"])
    huds.sort(key=lambda o: o["start"])
    vals = [int(re.search(r"(\d+)\s*%", o["text"]).group(1)) for o in huds]
    steps, prev = [], vals[0]
    for o, v in zip(huds[1:], vals[1:]):
        steps += [o["start"] + 0.14 * i for i in range(max(0, prev - v))]   # one drop per percent lost
        prev = v
    if not steps:
        return None
    return Meter(steps, start=huds[0]["start"], end=huds[-1]["end"], count_from=vals[0], count_to=vals[-1])


def captions(tl):
    caps = []
    for ln in tl["lines"]:
        if not ln.get("caption", True):
            continue
        colour = tl["cast"][ln["who"]]["caption"]
        size = int(ln.get("caption_size", 92) * CAPTION_SIZE / 92)
        for a, b, txt in A.chunks(ln):
            caps.append((a, b, txt, colour, size))
    return caps


def draw_captions(img, caps, t):
    row = 0
    for a, b, txt, colour, base in caps:
        if not (a <= t < b):
            continue
        y = CAPTION_Y + 84 * row
        row += 1
        pop = min(1.0, (t - a) / 0.08)
        shout = base > CAPTION_SIZE * 1.3
        size = int(base * ((1.35 - 0.35 * pop) if shout else (0.82 + 0.18 * pop)))
        fnt = A.fitted(txt, size, W - 400)
        x = W // 2
        if shout:
            k = max(0.0, 1 - (t - a) / 0.6)
            x += int(10 * k * math.sin(t * 61))
            y += int(7 * k * math.sin(t * 47 + 1))
        ImageDraw.Draw(img).text((x, y), txt, font=fnt, fill=colour, anchor="mm",
                                 stroke_width=max(7, base // 9), stroke_fill=(0, 0, 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("frames")
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--start", type=float, default=0.0, help="the chapter's first second on the timeline")
    ap.add_argument("--end", type=float, default=None, help="the chapter's last second on the timeline")
    ap.add_argument("--fade", type=float, default=0.4, help="sound fade at the chapter's end (seconds)")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    fps = tl["fps"]
    end = a.end if a.end is not None else tl["length"]
    f0, f1 = int(round(a.start * fps)) + 1, int(round(end * fps))
    overlays = [o for o in tl.get("overlays", []) if o["type"] not in DROP and o["type"] != "clip"]
    if not any(o["type"] == "watermark" for o in overlays):
        overlays.append({"type": "watermark", "text": WATERMARK, "start": 0.0, "end": 1e9})
    for o in overlays:
        if o["type"] == "watermark":
            o["end"] = 1e9
    meter = meter_for(tl)
    caps = captions(tl)
    fonts = {"mono": ImageFont.truetype(A.MONO, 54), "mono_small": ImageFont.truetype(A.MONO, 40),
             "big": ImageFont.truetype(A.FONT, 80), "mid": ImageFont.truetype(A.FONT, 50),
             "small": ImageFont.truetype(A.FONT, 38), "title": ImageFont.truetype(A.FONT, 130)}
    vig = A.vignette()
    black = Image.new("RGB", (W, H), (0, 0, 0))
    dur = (f1 - f0 + 1) / fps
    af = f"afade=t=out:st={max(0.0, dur - a.fade):.3f}:d={a.fade:.3f}"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(fps), "-i", "-", "-ss", f"{a.start:.3f}", "-t", f"{dur:.3f}", "-i", a.audio,
         "-af", af, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out],
        stdin=subprocess.PIPE)
    missing = 0
    for f in range(f0, f1 + 1):
        t = (f - 1) / fps
        path = os.path.join(a.frames, f"{f:04d}.png")
        if os.path.exists(path):
            img = Image.open(path).convert("RGB")
        else:
            img, missing = black.copy(), missing + 1
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        img = Image.composite(black, img, vig)
        for o in overlays:                                   # full-frame ones first
            if o["type"] in A.FULL and o["start"] <= t < o["end"]:
                A.DRAW[o["type"]](img, o, t, f, fonts)
        draw_captions(img, caps, t)
        if meter is not None:
            meter.draw(img, t)
        for o in overlays:
            if o["type"] not in A.FULL and o["start"] <= t < o["end"]:
                A.DRAW[o["type"]](img, o, t, f, fonts)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", a.out, f1 - f0 + 1, "frames", f"({missing} missing, drawn black)" if missing else "")


if __name__ == "__main__":
    main()
