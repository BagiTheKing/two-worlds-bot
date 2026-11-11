"""Episode 10, part 7: the voices inside Null. As the camera dives through the
Noob's eye into Null's body, his own old lines from the published episodes rise
out of the dark, the Noobs of every loop he left behind: a few alone and clear
at first ("Steve... can you respawn if there's no world?", "I don't want to be
deleted."), then more and more over each other, until a crowd of them; at the
cells, every head says "Hi!" at once, and it stops dead.

The voices are his real ones (cut from the published soundtracks); they are only
made to sound far away and inside something: band-limited, a little detuned
each, a long dark room, never a whisper effect.

    python tools/ep10_cells_chorus.py MP4_DIR TIMELINE_DIR OUT_WAV [--dur 5.0]

MP4_DIR holds <episode id>.mp4 (each preview branch's episode.mp4), TIMELINE_DIR
<episode id>.json (each preview branch's timeline.json).
"""
import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import audio as A                                                     # noqa: E402
from ep10_dejavu_audio import read, pitch                             # noqa: E402

SR = A.SR
# (episode, the line as in its timeline, role): "solo" ones are heard alone, early
LINES = [
    ("ep00_the_end", "Steve... can you respawn if there's no world?", "solo"),
    ("ep07_another_world", "I don't want to be deleted.", "solo"),
    ("ep01_the_tree", "Whoa. Where am I?", "crowd"),
    ("ep00_the_end", "I am running!", "crowd"),
    ("ep07_another_world", "That's... us?", "crowd"),
    ("ep04_the_block", "Again!", "crowd"),
    ("ep02_the_plan", "I'm fine! New record!", "crowd"),
    ("ep07_another_world", "Hey, that's me!", "crowd"),
    ("ep03_the_dragon", "Checkpoint!", "crowd"),
    ("ep01_the_tree", "I don't need tools. I'm a Roblox player.", "crowd"),
    ("ep06_deleting_itself", "...Hi?", "crowd"),
    ("ep02_the_plan", "Hi!", "hi"),
]


def bandpass(x, lo=260.0, hi=4200.0):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.clip((f - lo * 0.6) / (lo * 0.4), 0, 1) * np.clip((hi * 1.4 - f) / (hi * 0.4), 0, 1)
    return np.fft.irfft(X * g, n=len(x))


def room(x, secs=1.6, wet=0.5, seed=3):
    r = np.random.default_rng(seed)
    n = int(secs * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / (0.42 * SR))
    ir = bandpass(ir, 180, 2600)
    ir /= np.abs(ir).max() + 1e-9
    y = np.convolve(x, ir * 0.06)[:len(x) + n]
    out = np.zeros(len(x) + n)
    out[:len(x)] += x * (1 - wet)
    out[:len(y)] += y * wet
    return out


def cut(mp4s, tls, ep, text):
    tl = tls[ep]
    ln = next(l for l in tl["lines"] if l.get("text", "").strip() == text)
    x = read(mp4s[ep], max(0.0, ln["start"] - 0.03), ln["end"] - ln["start"] + 0.12)
    n = int(0.02 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def main(mp4_dir, tl_dir, out, dur=5.0):
    mp4s = {os.path.splitext(f)[0]: os.path.join(mp4_dir, f) for f in os.listdir(mp4_dir) if f.endswith(".mp4")}
    tls = {os.path.splitext(f)[0]: json.load(open(os.path.join(tl_dir, f))) for f in os.listdir(tl_dir)
           if f.endswith(".json")}
    clips = {(ep, t): A.norm(cut(mp4s, tls, ep, t), 0.9) for ep, t, _ in LINES}
    r = np.random.default_rng(412)
    mix = np.zeros(int((dur + 2.5) * SR))

    def put(x, at, gain):
        i = int(at * SR)
        j = min(len(mix), i + len(x))
        if j > i:
            mix[i:j] += gain * x[:j - i]

    # alone and clear-ish first, far inside
    solos = [(ep, t) for ep, t, role in LINES if role == "solo"]
    put(room(bandpass(clips[solos[0]]), 1.4, 0.45, 1), 0.0, 0.55)
    put(room(bandpass(pitch(clips[solos[1]], -1.0)), 1.6, 0.5, 2), 1.55, 0.6)
    # then the crowd: more and more of them, each a little detuned, on top of each other
    crowd = [(ep, t) for ep, t, role in LINES if role == "crowd"]
    n = 34
    for k in range(n):
        u = (k / (n - 1)) ** 0.55                                   # denser toward the end
        at = 1.1 + u * (dur - 1.75) + r.uniform(-0.12, 0.12)
        ep, t = crowd[r.integers(len(crowd))]
        x = pitch(clips[(ep, t)], r.uniform(-2.2, 1.8))
        x = room(bandpass(x, r.uniform(220, 380), r.uniform(3000, 5200)), r.uniform(1.0, 1.8), r.uniform(0.45, 0.7),
                 int(r.integers(1000)))
        put(x, at, 0.16 + 0.22 * u)
    # every head at once: "Hi!"
    hi = clips[("ep02_the_plan", "Hi!")]
    t_hi = dur - 0.55
    for k in range(18):
        x = pitch(hi, r.uniform(-1.6, 1.2))
        put(bandpass(x, 240, 5200), t_hi + r.uniform(0.0, 0.035), 0.11)
    hi_end = t_hi + len(hi) / SR + 0.04
    # it stops dead after the "Hi!" (the room's tail cut too)
    mix = mix[:int(hi_end * SR)]
    k = int(0.012 * SR)
    mix[-k:] *= np.linspace(1, 0, k)
    mix = A.norm(mix, 0.9)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    sf.write(out, mix, SR)
    print(out, round(len(mix) / SR, 2), "s; Hi! at", round(t_hi, 2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4_dir")
    ap.add_argument("tl_dir")
    ap.add_argument("out")
    ap.add_argument("--dur", type=float, default=5.0)
    a = ap.parse_args()
    main(a.mp4_dir, a.tl_dir, a.out, a.dur)
