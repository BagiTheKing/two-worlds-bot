"""Episode 10, part 9: the cells' crying and Null's broken sob, from the Noob's
own crying takes (the sound bank ep10_p9_sobs: a voices-only run).

  - cells_crying.wav: the takes layered many times, each a little detuned and
    delayed, far inside something (a choir of the Noobs of every loop, crying);
  - null_sob.wav: one take through Null's voice (as everything he says), then
    broken like a program crashing: grains stutter and repeat, drop out, jump in
    pitch, and the last of it is cut dead.

    python tools/ep10_p9_sounds.py VOICE_WAV TIMELINE_JSON OUT_DIR
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import audio as A                                                     # noqa: E402
from ep10_dejavu_audio import pitch                                   # noqa: E402
from ep10_cells_chorus import bandpass, room                          # noqa: E402

SR = A.SR


def takes(voice, tl):
    x, sr = sf.read(voice)
    x = x.mean(axis=1) if x.ndim > 1 else x
    if sr != SR:
        x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / sr)), np.arange(len(x)), x)
    out = {}
    for ln in json.load(open(tl))["lines"]:
        a, b = int(ln["start"] * SR), int(ln["end"] * SR)
        y = x[a:b].copy()
        n = int(0.015 * SR)
        y[:n] *= np.linspace(0, 1, n)
        y[-n:] *= np.linspace(1, 0, n)
        out[ln["name"]] = A.norm(y, 0.9)
    return out


def cells_crying(S, dur=3.0, seed=7):
    r = np.random.default_rng(seed)
    mix = np.zeros(int((dur + 2.0) * SR))
    names = ["sob1", "sob2", "sob3"]
    for k in range(26):
        x = S[names[k % 3]]
        x = pitch(x, r.uniform(-2.5, 2.5))
        x = room(bandpass(x, r.uniform(220, 360), r.uniform(2600, 4600)), r.uniform(1.2, 2.0), r.uniform(0.5, 0.75),
                 int(r.integers(1000)))
        at = r.uniform(-0.6, dur - 0.8)
        i = max(0, int(at * SR))
        j0 = max(0, -int(at * SR))
        seg = x[j0:j0 + len(mix) - i]
        mix[i:i + len(seg)] += r.uniform(0.15, 0.32) * seg
    mix = mix[:int(dur * SR)]
    n = int(0.4 * SR)
    mix[:n] *= np.linspace(0, 1, n)
    mix[-n:] *= np.linspace(1, 0, n)
    return A.norm(mix, 0.85)


def null_sob(S, seed=11):
    r = np.random.default_rng(seed)
    x = np.concatenate([S["sob4"], S["sob2"][: int(0.9 * SR)]])
    v = A.null_voice(x)
    # broken: grains of it stutter, repeat, drop out, jump in pitch, the colour of a crash
    out = []
    i = 0
    g = int(0.07 * SR)
    while i < len(v):
        L = int(r.uniform(0.045, 0.14) * SR)
        grain = v[i:i + L].copy()
        if len(grain) < 32:
            break
        roll = r.random()
        if roll < 0.18:                                   # a stutter: the same few hundredths, again and again
            rep = int(r.integers(2, 5))
            gg = grain[: max(32, len(grain) // 2)]
            out.extend([gg] * rep)
        elif roll < 0.26:                                 # a dropout
            out.append(np.zeros(int(r.uniform(0.03, 0.09) * SR)))
        elif roll < 0.34:                                 # a jump in pitch
            out.append(pitch(grain, r.choice([-7.0, 5.0, 12.0])))
        elif roll < 0.38:
            out.append(grain[::-1])
        else:
            out.append(grain)
        i += L
    y = np.concatenate(out)
    y = np.round(y * 24) / 24                             # bit-crushed
    k = int(0.012 * SR)
    y[-k:] *= np.linspace(1, 0, k)                        # cut dead
    return A.norm(y, 0.9)


def main(voice, tl, out_dir):
    S = takes(voice, tl)
    os.makedirs(out_dir, exist_ok=True)
    a = cells_crying(S)
    sf.write(os.path.join(out_dir, "cells_crying.wav"), a, SR)
    b = null_sob(S)
    sf.write(os.path.join(out_dir, "null_sob.wav"), b, SR)
    print("cells_crying", round(len(a) / SR, 2), "s; null_sob", round(len(b) / SR, 2), "s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
