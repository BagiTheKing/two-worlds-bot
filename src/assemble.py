"""
Final pass: upscale the rendered frames to 1080x1920, burn in captions
(short word groups in each speaker's colour, with a small pop-in), add a soft
vignette, and encode with the episode audio.

    python src/assemble.py build/timeline.json build/frames build/audio.wav out.mp4
"""

import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT = os.path.join(os.path.dirname(__file__), "..", "fonts", "InterDisplay-Black.otf")
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


def main(timeline, frames_dir, audio, out):
    tl = json.load(open(timeline))
    fps = tl["fps"]
    caps = []
    for ln in tl["lines"]:
        color = tl["cast"][ln["who"]]["caption"]
        caps += [(a, b, txt, color) for a, b, txt in chunks(ln)]
    font = ImageFont.truetype(FONT, 92)
    vig = vignette()
    black = Image.new("RGB", (W, H), (0, 0, 0))
    frames = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", audio,
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for i, name in enumerate(frames):
        t = i / fps
        img = Image.open(os.path.join(frames_dir, name)).convert("RGB")
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        img = Image.composite(black, img, vig)
        for a, b, txt, color in caps:
            if a <= t < b:
                pop = min(1.0, (t - a) / 0.08)
                size = int(92 * (0.82 + 0.18 * pop))
                f = font if size == 92 else ImageFont.truetype(FONT, size)
                d = ImageDraw.Draw(img)
                d.text((W // 2, CAPTION_Y), txt, font=f, fill=color, anchor="mm",
                       stroke_width=10, stroke_fill=(0, 0, 0), align="center")
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out, len(frames), "frames")


if __name__ == "__main__":
    main(*sys.argv[1:5])
