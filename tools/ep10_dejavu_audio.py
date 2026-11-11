"""Episode 10, part 5: Episode 0's "I am running!", exactly as published, falling
into Steve's deja vu: "I am" plays as it was; through "running" time slows to a
quarter, the voice sinks and smears, and echoes of it (the other loops) pile up
underneath, then everything is sucked back into one.

    python tools/ep10_dejavu_audio.py EP0_MP4 OUT_DIR

Writes OUT_DIR/ep0_noob_running_dejavu.wav (24 kHz).

The take in the episode is the first one this tool made (commit 6533b14), chosen
by the creator over the slower ones: "running" sinks in pitch rather than really
slowing (its slices were too short to stretch), with the echoes and the suck at
the end. --first remakes it exactly that way. Times are in Episode 0's
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


def vstretch(x, rate_of, sr=SR):
    """WSOLA with a speed that changes over the sound: rate_of(u) (u = 0..1 through the
    input) is how fast the input is read (1 = as recorded, 0.25 = four times slower);
    the pitch stays (a slow-motion voice, not a tape running down)."""
    n = int(0.04 * sr)
    hop = n // 2
    tol = int(0.012 * sr)
    win = np.hanning(n)
    out = np.zeros(int(len(x) * 6) + n)
    weight = np.zeros_like(out)
    prev, pos, k = None, 0.0, 0
    while True:
        centre = int(pos)
        if centre + n + tol >= len(x):
            break
        best = centre
        if prev is not None and prev + hop + n <= len(x):
            target = x[prev + hop:prev + hop + n]
            lo, hi = max(0, centre - tol), min(len(x) - n, centre + tol)
            scores = [(np.dot(x[c:c + n], target), c) for c in range(lo, hi + 1, 4)]
            best = max(scores)[1] if scores else centre
        out[k * hop:k * hop + n] += x[best:best + n] * win
        weight[k * hop:k * hop + n] += win
        prev = best
        pos += hop * rate_of(pos / len(x))
        k += 1
    end = k * hop + n
    weight[weight < 1e-3] = 1.0
    return (out / weight)[:end]


def pitch(x, semis):
    """Shift pitch, keep the length (resample, then stretch back)."""
    p = 2 ** (semis / 12)
    y = np.interp(np.linspace(0, len(x) - 1, int(len(x) / p)), np.arange(len(x)), x)
    return A.stretch(y, len(y) / len(x)) if abs(p - 1) > 1e-3 else x


def main(mp4, out_dir, final=0.25, dry=False, name="ep0_noob_running_dejavu.wav", first=False, tail=False):
    x = read(mp4, 17.66, 0.86)                     # "I am running!" with a breath of room on each side
    split = int((18.08 - 17.66) * SR)              # "I am" | "running"
    head, word = x[:split], x[split:]
    # "running": time slows through the word, from as recorded down to `final`, and sinks a little
    if first:                                       # the chosen take: short slices, each lower
        sl = np.array_split(word, 10)
        slow = np.concatenate([pitch(A.stretch(seg, 1.0 - 0.75 * (k / 9) ** 1.3), -6.0 * (k / 9) ** 1.2)
                               for k, seg in enumerate(sl)])
        voice = np.concatenate([head, slow])
        return _finish(voice, split, out_dir, name, tail)
    slow = vstretch(word, lambda u: 1.0 - (1.0 - final) * min(1.0, u * 2.4) ** 0.9)
    k = 8                                           # the sinking: in a few overlapping pieces, deeper each time
    pieces = np.array_split(np.arange(len(slow)), k)
    sunk = np.zeros(len(slow))
    for i, idx in enumerate(pieces):
        seg = slow[max(0, idx[0] - 600):idx[-1] + 600]
        y = pitch(seg, -5.0 * (i / (k - 1)) ** 1.3)[:len(seg)]
        y = np.pad(y, (0, len(seg) - len(y)))
        a0 = max(0, idx[0] - 600)
        fade = np.ones(len(y))
        r = min(600, len(y) // 4)
        fade[:r] = np.linspace(0, 1, r)
        fade[-r:] = np.linspace(1, 0, r)
        sunk[a0:a0 + len(y)] += y[:len(sunk) - a0] * fade[:len(sunk) - a0]
    norm_w = np.zeros(len(slow))
    for i, idx in enumerate(pieces):
        a0 = max(0, idx[0] - 600)
        L = min(len(slow), idx[-1] + 600) - a0
        fade = np.ones(L)
        r = min(600, L // 4)
        fade[:r] = np.linspace(0, 1, r)
        fade[-r:] = np.linspace(1, 0, r)
        norm_w[a0:a0 + L] += fade
    slow = sunk / np.maximum(norm_w, 1e-3)
    voice = np.concatenate([head, slow])
    if dry:                                         # the slow-down alone (to judge its speed)
        p = os.path.join(out_dir, name)
        sf.write(p, A.norm(voice, 0.9), SR)
        print(p, round(len(voice) / SR, 2), "s")
        return
    _finish(voice, split, out_dir, name, tail)


def _finish(voice, split, out_dir, name, tail_out=False):
    """The other loops' echoes, the smear, and the suck back into one."""
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
    if tail_out:                                    # no suck: the echoes ring on and fade (under Steve's whisper)
        mix = mix[:len(voice) + int(1.6 * SR)]
        n_f = int(1.4 * SR)
        mix[-n_f:] *= np.linspace(1, 0, n_f) ** 1.5
        os.makedirs(out_dir, exist_ok=True)
        p = os.path.join(out_dir, name)
        sf.write(p, A.norm(mix, 0.9), SR)
        print(p, round(len(mix) / SR, 2), "s")
        return
    # then sucked back into one: a reversed swell, cut dead
    swell = A.sfx_suck(0.5) if hasattr(A, "sfx_suck") else np.zeros(int(0.5 * SR))
    end = len(voice) + int(0.25 * SR)
    mix = mix[:end + len(swell)]
    mix[end:end + len(swell)] += 0.5 * swell[:len(mix) - end]
    mix *= np.minimum(1, (len(mix) - np.arange(len(mix))) / (0.03 * SR))
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, name)
    sf.write(p, A.norm(mix, 0.9), SR)
    print(p, round(len(mix) / SR, 2), "s")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("out_dir")
    ap.add_argument("--final", type=float, default=0.25, help="the speed it slows to (0.25 = a quarter)")
    ap.add_argument("--dry", action="store_true", help="only the slow-down, no echoes or smear")
    ap.add_argument("--name", default="ep0_noob_running_dejavu.wav")
    ap.add_argument("--first", action="store_true", help="the chosen take (see the top of this file)")
    ap.add_argument("--tail", action="store_true", help="no suck at the end: the echoes ring on and fade")
    a = ap.parse_args()
    main(a.mp4, a.out_dir, a.final, a.dry, a.name, a.first, a.tail)
