"""Join the finale's rendered parts into its five Shorts (FINALE 1/5 ... 5/5).

Each Short is a run of parts played straight through, hard cuts between them:
  - each part's silent tail (the 0.4 s pad every render ends on) is cut, so
    the joins have no dead air; where a part still has sound at its end, it
    gets a short fade so the next one does not start on a click;
  - a "FINALE n/5" badge, in the series' cyan/magenta glitch, in the first
    seconds (so whoever lands on part 3 knows it is part 3 of 5);
  - except on the last Short (which has its own Season 2 end card): the last
    frame held under a rising shade with TO BE CONTINUED / FINALE n+1/5 and a
    question for the comments, over a short glitch stinger.

    python tools/finale_join.py OUT.mp4 --n 1 --of 5 --question "WHY THE NOOB?" p1.mp4 p2.mp4 p3.mp4
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
W, H, FPS = 1080, 1920, 24
FONT = os.path.join(HERE, "..", "fonts", "InterDisplay-Black.otf")
TAIL_KEEP = 0.06          # what is kept of a part's silent tail
CARD = 1.9                # the to-be-continued card (s)
BADGE = 2.6               # the badge, from the start (s)
TARGET = -15.0            # every part brought to this loudness (LUFS), so the joins do not jump


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def silent_tail(path, dur):
    """Where the silence at the very end of a part starts (None if it ends on sound)."""
    err = subprocess.run(["ffmpeg", "-nostdin", "-i", path, "-af", "silencedetect=noise=-50dB:d=0.1", "-vn", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    if starts and (len(ends) < len(starts) or ends[-1] > dur - 0.05):
        return starts[-1]
    return None


def loudness(path):
    err = subprocess.run(["ffmpeg", "-nostdin", "-i", path, "-af", "ebur128", "-vn", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)[-1])


def fitted(text, size, max_w):
    f = ImageFont.truetype(FONT, size)
    w = f.getlength(text)
    return f if w <= max_w else ImageFont.truetype(FONT, max(20, int(size * max_w / w)))


def glitch_text(d, xy, text, fnt, f, spread=6, jitter=True):
    g = random.Random(f).choice((0, 0, 0, 4, -4)) if jitter else 0
    x, y = xy
    for dx, col in ((-spread + g, (0, 230, 255, 255)), (spread + g, (255, 0, 200, 255))):
        d.text((x + dx, y), text, font=fnt, fill=col, anchor="mm")
    d.text((x + g, y), text, font=fnt, fill=(255, 255, 255, 255), anchor="mm")


def badge_png(path, n, of):
    """FINALE n/5, in a dark pill under the watermark."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT, 76)
    small = ImageFont.truetype(FONT, 40)
    label, part = "THE FINALE", f"{n}/{of}"
    wl, wp = small.getlength(label), big.getlength(part)
    gap = 26
    tw = wl + gap + wp
    cx, cy = W // 2, 300
    x0 = cx - tw / 2
    pad = 44
    d.rounded_rectangle((x0 - pad, cy - 66, x0 + tw + pad, cy + 66), radius=66, fill=(6, 4, 12, 170),
                        outline=(0, 230, 255, 120), width=3)
    d.text((x0 + wl / 2, cy + 2), label, font=small, fill=(255, 210, 63, 255), anchor="mm")
    glitch_text(d, (x0 + wl + gap + wp / 2, cy), part, big, 0, spread=5, jitter=False)
    img.save(path)


def card_frames(folder, nxt, of, question, sub):
    """The to-be-continued card, frame by frame (the shade rises; the title glitches)."""
    os.makedirs(folder, exist_ok=True)
    small = ImageFont.truetype(FONT, 42)
    sub_f = ImageFont.truetype(FONT, 38)
    n = int(round(CARD * FPS)) + 4                       # a few spare, so the card holds to the last frame
    for f in range(n):
        t = f / FPS
        k = min(1.0, t / 0.3)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shade = Image.new("L", (1, 760))
        for y in range(760):
            shade.putpixel((0, y), int(215 * k * (y / 760) ** 1.2))
        shade = shade.resize((W, 760))
        img.paste((4, 3, 8, 255), (0, H - 760), shade)
        top = Image.new("L", (1, 1))
        top.putpixel((0, 0), int(70 * k))
        img.paste((4, 3, 8, 255), (0, 0, W, H - 760), top.resize((W, H - 760)))
        if t > 0.12:
            d = ImageDraw.Draw(img)
            y0 = H - 560
            d.text((W // 2, y0), "TO BE CONTINUED", font=small, fill=(255, 210, 63, 255), anchor="mm")
            glitch_text(d, (W // 2, y0 + 100), f"FINALE {nxt}/{of}", fitted(f"FINALE {nxt}/{of}", 124, W - 120), f)
            d.text((W // 2, y0 + 245), question, font=fitted(question, 84, W - 120), fill=(255, 59, 212, 255),
                   anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, 255))
            d.text((W // 2, y0 + 330), sub, font=sub_f, fill=(220, 220, 230, 255), anchor="mm")
        img.save(os.path.join(folder, f"c{f:04d}.png"))


def stinger(path):
    """A glitch and a low drop under the card."""
    import audio
    sr = audio.SR
    out = np.zeros(int(CARD * sr) + sr)
    audio.place(out, audio.sfx_glitch(0.35), 0.0, 0.5)
    audio.place(out, audio.sfx_sub_drop(1.2), 0.05, 0.55)
    audio.place(out, audio.sfx_whoosh(0.6), 0.0, 0.25)
    out = out[:int(CARD * sr)]
    out *= np.minimum(1.0, (CARD - np.arange(len(out)) / sr) / 0.4)
    sf.write(path, np.stack([out, out], 1), sr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("parts", nargs="+")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--of", type=int, default=5)
    ap.add_argument("--question", default="WHAT HAPPENS NEXT?")
    ap.add_argument("--sub", default="Comment your theory")
    ap.add_argument("--no-card", action="store_true")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="finale_")
    card = not a.no_card and a.n < a.of
    inputs, filt, cuts = [], [], []
    for i, p in enumerate(a.parts):
        dur = probe_duration(p)
        s = silent_tail(p, dur)
        end = min(dur, s + TAIL_KEEP) if s is not None and dur - s > 0.2 else dur
        end = round(end * FPS) / FPS                       # on a frame
        fade = s is None or dur - s <= 0.2                  # it ends on sound: a short fade
        gain = TARGET - loudness(p)
        cuts.append({"part": os.path.basename(p), "dur": round(dur, 3), "kept": round(end, 3), "faded": fade,
                     "gain_db": round(gain, 2)})
        inputs += ["-i", p]
        filt.append(f"[{i}:v]trim=0:{end:.4f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[v{i}]")
        af = f"[{i}:a]atrim=0:{end:.4f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume={gain:.2f}dB"
        if fade:
            af += f",afade=t=out:st={max(0.0, end - 0.12):.4f}:d=0.12"
        if i > 0:
            af += ",afade=t=in:st=0:d=0.02"
        filt.append(af + f"[a{i}]")
    k = len(a.parts)
    filt.append("".join(f"[v{i}][a{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=1[vc][ac]")
    total = sum(c["kept"] for c in cuts)
    nin = k
    badge = os.path.join(tmp, "badge.png")
    badge_png(badge, a.n, a.of)
    inputs += ["-loop", "1", "-t", f"{BADGE:.2f}", "-framerate", str(FPS), "-i", badge]
    filt.append(f"[{nin}:v]format=rgba,fade=t=in:st=0.15:d=0.25:alpha=1,fade=t=out:st={BADGE - 0.35:.2f}:d=0.35:alpha=1[bd]")
    nin += 1
    if card:
        cdir = os.path.join(tmp, "card")
        card_frames(cdir, a.n + 1, a.of, a.question, a.sub)
        sting = os.path.join(tmp, "sting.wav")
        stinger(sting)
        inputs += ["-framerate", str(FPS), "-i", os.path.join(cdir, "c%04d.png"), "-i", sting]
        filt.append(f"[vc]tpad=stop_mode=clone:stop_duration={CARD:.3f}[vp]")
        filt.append("[vp][bd]overlay=0:0:eof_action=pass[vb]")
        filt.append(f"[{nin}:v]format=rgba,setpts=PTS-STARTPTS+{total:.4f}/TB[cd]")
        filt.append("[vb][cd]overlay=0:0:eof_action=pass[vout]")
        filt.append(f"[{nin + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(total * 1000)}|{int(total * 1000)}[st]")
        filt.append(f"[ac]apad=pad_dur={CARD:.3f}[ap]")
        filt.append("[ap][st]amix=inputs=2:duration=first:normalize=0[am]")
    else:
        filt.append("[vc][bd]overlay=0:0:eof_action=pass[vout]")
        filt.append("[ac]anull[am]")
    filt.append("[am]alimiter=limit=0.89:attack=2:release=60:level=disabled[aout]")
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt),
           "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(json.dumps({"out": a.out, "duration": round(probe_duration(a.out), 3), "parts": cuts}, indent=1))


if __name__ == "__main__":
    main()
