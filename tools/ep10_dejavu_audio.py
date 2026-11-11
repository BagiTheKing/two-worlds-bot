"""Episode 10, part 5: Episode 0's "I am running!", exactly as published, falling
into Steve's deja vu: "I am" plays as it was; through "running" time slows to a
quarter, the voice sinks and smears, and echoes of it (the other loops) pile up
underneath, then everything is sucked back into one.

    python tools/ep10_dejavu_audio.py EP0_MP4 OUT_DIR

Writes OUT_DIR/ep0_noob_running_dejavu.wav (24 kHz). Times are in Episode 0's
published soundtrack: the line is at 17.73-18.46 s there ("running" from 18.13).
"""
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import audio as A                                                     # noqa: E402

SR = A.SR


def read(mp4, t0, dur):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", mp4,
                          "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def pitch(x, semis):
    """Shift pitch, keep the length (resample, then stretch back)."""
    p = 2 ** (semis / 12)
    y = np.interp(np.linspace(0, len(x) - 1, int(len(x) / p)), np.arange(len(x)), x)
    return A.stretch(y, len(y) / len(x)) if abs(p - 1) > 1e-3 else x


def main(mp4, out_dir):
    x = read(mp4, 17.66, 0.86)                     # "I am running!" with a breath of room on each side
    split = int((18.08 - 17.66) * SR)              # "I am" | "running"
    head, word = x[:split], x[split:]
    # "running": in slices, each slower and lower than the last (1x -> 0.25x, 0 -> -6 semitones)
    n = 10
    sl = np.array_split(word, n)
    out = []
    for k, s in enumerate(sl):
        u = k / (n - 1)
        rate = 1.0 - 0.75 * u ** 1.3
        y = A.stretch(s, rate)
        y = pitch(y, -6.0 * u ** 1.2)
        out.append(y)
    slow = np.concatenate(out)
    voice = np.concatenate([head, slow])
    # the other loops: echoes of the line, later and lower, piling up as it slows
    ghosts = np.zeros(len(voice) + int(1.2 * SR))
    for k, (d, g, st) in enumerate(((0.18, 0.35, -2), (0.33, 0.28, 3), (0.5, 0.24, -5), (0.7, 0.2, 2))):
        e = pitch(voice, st)
        i = int(d * SR)
        ghosts[i:i + len(e)] += g * e * np.linspace(0.2, 1.0, len(e))
    mix = np.zeros_like(ghosts)
    mix[:len(voice)] += voice
    mix += ghosts
    # a growing smear (a reverb tail that swells as time slows)
    tail = A.rng.standard_normal(int(0.9 * SR)) * np.exp(-np.arange(int(0.9 * SR)) / (0.3 * SR))
    wet = np.convolve(mix, tail * 0.015)[:len(mix)]
    ramp = np.clip((np.arange(len(mix)) - split) / (0.6 * SR), 0, 1)
    mix = mix + wet * ramp
    # then sucked back into one: a reversed swell, cut dead
    swell = A.sfx_suck(0.5) if hasattr(A, "sfx_suck") else np.zeros(int(0.5 * SR))
    end = len(voice) + int(0.25 * SR)
    mix = mix[:end + len(swell)]
    mix[end:end + len(swell)] += 0.5 * swell[:len(mix) - end]
    mix *= np.minimum(1, (len(mix) - np.arange(len(mix))) / (0.03 * SR))
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "ep0_noob_running_dejavu.wav")
    sf.write(p, A.norm(mix, 0.9), SR)
    print(p, round(len(mix) / SR, 2), "s")


if __name__ == "__main__":
    main(*sys.argv[1:3])
