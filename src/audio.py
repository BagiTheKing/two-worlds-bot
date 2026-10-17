"""
Voices, sound effects and the episode timeline.

The audio decides the timing: every dialogue line is synthesised first
(Kokoro, local, Apache-2.0), and the beats between lines get the durations
the episode file asks for. The result is build/timeline.json, which the
Blender scene reads, so mouths (head bobs), punches and cuts land exactly on
the sound. All sound effects are synthesised here from noise and sine waves,
so there is nothing to license.

    python src/audio.py episodes/ep00_poc.json build/
"""

import json
import math
import os
import sys

import numpy as np
import soundfile as sf

SR = 48000
KOKORO_SR = 24000
MODEL = os.getenv("KOKORO_MODEL_PATH", "models/kokoro-v1.0.onnx")
VOICES = os.getenv("KOKORO_VOICES_PATH", "models/voices-v1.0.bin")

PUNCH_AT = 0.18          # seconds into a "punch" beat when the fist lands
FLURRY_GAP = 0.19        # seconds between hits in a "flurry" beat
rng = np.random.default_rng(7)


# ------------------------------------------------------------------ helpers

def t(sec):
    return np.arange(int(sec * SR)) / SR


def band(x, lo, hi):
    """Band-pass through the FFT with soft edges (no scipy needed)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * mask, len(x))


def env(n, attack, decay):
    a = int(attack * SR)
    e = np.exp(-np.arange(n) / max(1, decay * SR))
    if a:
        e[:a] *= np.linspace(0, 1, a)
    return e


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def place(mix, clip, at, gain=1.0):
    i = int(at * SR)
    if i >= len(mix):
        return
    n = min(len(clip), len(mix) - i)
    mix[i:i + n] += clip[:n] * gain


# --------------------------------------------------------------- the sounds

def sfx_portal(dur):
    x = t(dur + 0.6)
    sweep = np.sin(2 * np.pi * (80 * x + 260 * x ** 2))
    hiss = band(rng.standard_normal(len(x)), 600, 5000)
    s = 0.6 * sweep * np.sin(np.pi * x / x[-1]) + 0.5 * norm(hiss) * env(len(x), 0.3, 0.6)
    return norm(s, 0.8)


def sfx_fall(dur):
    x = t(dur)
    f = 1400 - 900 * x / dur
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0.1, 0.5, len(x)), 0.25)


def sfx_thump(freq=70, length=0.45, click=0.5):
    x = t(length)
    body = np.sin(2 * np.pi * freq * x * (1 - 0.4 * x)) * env(len(x), 0.002, 0.12)
    crack = band(rng.standard_normal(len(x)), 300, 4000) * env(len(x), 0.0005, 0.02)
    return norm(body + click * norm(crack), 0.9)


def sfx_land(dur):
    return sfx_thump(55, 0.6, 0.35)


def sfx_punch_wood():
    x = t(0.3)
    knock = np.sin(2 * np.pi * 180 * x) * env(len(x), 0.001, 0.05)
    tap = band(rng.standard_normal(len(x)), 800, 3500) * env(len(x), 0.0005, 0.015)
    return norm(knock + 0.7 * norm(tap), 0.9)


def sfx_step():
    x = t(0.12)
    return norm(band(rng.standard_normal(len(x)), 150, 1800) * env(len(x), 0.002, 0.03), 0.4)


def sfx_break():
    out = np.zeros(int(0.8 * SR))
    for i in range(7):
        place(out, norm(band(rng.standard_normal(int(0.08 * SR)), 400 + i * 200, 3000))
              * env(int(0.08 * SR), 0.001, 0.02), i * 0.035)
    place(out, sfx_thump(240, 0.3, 0.8), 0.0)
    pop = np.sin(2 * np.pi * 520 * t(0.12) * (1 + 2 * t(0.12))) * env(int(0.12 * SR), 0.001, 0.04)
    place(out, pop, 0.25, 0.6)
    return norm(out, 0.9)


def sfx_glitch(dur):
    """The Null's signature: digital stutter over a low drone."""
    n = int((dur + 1.5) * SR)
    out = np.zeros(n)
    x = t(dur + 1.5)
    drone = (np.sin(2 * np.pi * 41 * x) + 0.5 * np.sin(2 * np.pi * 61.5 * x)) * np.minimum(1, x / 0.4)
    out += 0.5 * drone
    pos = 0.0
    while pos < dur:
        seg = rng.uniform(0.03, 0.09)
        f = rng.choice([220, 330, 880, 1320, 95])
        burst = np.sign(np.sin(2 * np.pi * f * t(seg)))
        burst = np.round(burst * 4) / 4 * env(len(burst), 0.001, seg)
        place(out, burst, pos, 0.35)
        pos += seg + rng.uniform(0.0, 0.12)
    # three-note signal
    for i, f in enumerate((392, 311, 466)):
        tone = np.sin(2 * np.pi * f * t(0.35)) * env(int(0.35 * SR), 0.01, 0.25)
        place(out, tone, 0.25 + i * 0.38, 0.45)
    return norm(out, 0.8)


def ambience(length):
    """Wind plus a few birds."""
    n = int(length * SR)
    wind = band(rng.standard_normal(n), 80, 700)
    wind = norm(wind) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * np.arange(n) / SR))
    out = 0.5 * wind
    at = 0.8
    while at < length - 1:
        x = t(0.09)
        chirp = np.sin(2 * np.pi * (3200 * x + 9000 * x ** 2)) * env(len(x), 0.005, 0.03)
        place(out, chirp, at, 0.25)
        place(out, chirp, at + 0.13, 0.18)
        at += rng.uniform(1.6, 3.2)
    return out


# ------------------------------------------------------------------- voices

_kokoro = None


def say(text, voice, speed, pitch):
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(MODEL, VOICES)
    s, sr = _kokoro.create(text, voice=voice, speed=speed, lang="en-us")
    s = np.asarray(s, dtype=np.float64)
    loud = np.where(np.abs(s) > 0.02)[0]
    if len(loud):
        s = s[max(0, loud[0] - 240): loud[-1] + 2400]
    # a small pitch lift/drop by resampling gives each character a register
    n_out = int(len(s) * (SR / sr) / pitch)
    s = np.interp(np.linspace(0, len(s) - 1, n_out), np.arange(len(s)), s)
    return norm(s, 0.95)


# ----------------------------------------------------------------- timeline

def build(episode_path, out_dir):
    ep = json.load(open(episode_path))
    os.makedirs(out_dir, exist_ok=True)
    cursor = 0.0
    beats, lines, clips, impacts = {}, [], [], []
    counts = {}
    for ev in ep["events"]:
        if "beat" in ev:
            beats[ev["beat"]] = [cursor, cursor + ev["dur"]]
            if ev["beat"] == "punch":
                impacts.append(cursor + PUNCH_AT)
            if ev["beat"] == "flurry":
                h = cursor + 0.12
                while h < cursor + ev["dur"] - 0.05:
                    impacts.append(h)
                    h += FLURRY_GAP
            if ev.get("sfx"):
                clips.append((ev["sfx"], cursor, ev["dur"]))
            cursor += ev["dur"]
        else:
            who = ev["line"]
            c = ep["cast"][who]
            audio = say(ev["text"], c["voice"], c["speed"], c["pitch"])
            counts[who] = counts.get(who, 0) + 1
            name = f"{who}_{counts[who]}"
            dur = len(audio) / SR
            lines.append({"name": name, "who": who, "text": ev["text"],
                          "start": round(cursor, 3), "end": round(cursor + dur, 3)})
            beats[name] = [cursor, cursor + dur]
            clips.append(("voice", cursor, audio))
            cursor += dur + ev.get("pad", 0.2)
    length = cursor

    mix = np.zeros(int((length + 0.5) * SR))
    voice = np.zeros_like(mix)
    crack_at = beats.get("crack", [length])[0]
    amb = ambience(crack_at)
    amb[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))   # a hard cut: the Null's silence
    place(mix, amb, 0, 0.10)
    for kind, at, arg in clips:
        if kind == "voice":
            place(voice, arg, at, 1.0)
        elif kind == "portal":
            place(mix, sfx_portal(arg), at, 0.5)
        elif kind == "fall":
            place(mix, sfx_fall(arg), at, 0.5)
        elif kind == "land":
            place(mix, sfx_land(arg), at, 0.7)
        elif kind == "steps":
            for i in range(int(arg / 0.25)):
                place(mix, sfx_step(), at + 0.1 + i * 0.25, 0.5)
        elif kind == "glitch":
            place(mix, sfx_glitch(arg), at, 0.55)
        elif kind == "break":
            place(mix, sfx_break(), at, 0.75)
    for h in impacts:
        place(mix, sfx_punch_wood(), h, 0.6)
    # duck everything under dialogue
    duck = np.convolve(np.abs(voice) > 0.02, np.ones(SR // 10) / (SR // 10), "same")
    out = voice + mix * (1 - 0.45 * np.clip(duck * 3, 0, 1))
    out = norm(out, 0.89)
    sf.write(os.path.join(out_dir, "audio.wav"), np.stack([out, out], 1).astype(np.float32), SR)

    timeline = {"id": ep["id"], "fps": 24, "length": round(length, 3),
                "beats": {k: [round(a, 3), round(b, 3)] for k, (a, b) in beats.items()},
                "impacts": [round(h, 3) for h in impacts],
                "lines": lines, "cast": ep["cast"]}
    with open(os.path.join(out_dir, "timeline.json"), "w") as f:
        json.dump(timeline, f, indent=1)
    return timeline


if __name__ == "__main__":
    tl = build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "build")
    print(json.dumps({k: tl[k] for k in ("length", "beats")}, indent=1))
