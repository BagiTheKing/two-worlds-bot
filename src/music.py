"""
The soundtrack, composed in code (so the channel owns every note).

A chiptune-meets-cinematic palette: square and pulse leads, triangle bass,
detuned-saw pads, synth drums, and a low "braam" for Null. Everything grows
out of one main motif (D F A G F E), so the series has a theme people learn:

    theme_soft   prologue: pad + plucked motif, gentle
    chase        erasure and running: driving bass, arpeggios, drums
    null         Null's theme: drone, braams, the motif slowed down and low
    theme_full   end card: drums + lead motif + pad, ends on a sting

    render(cue, seconds, seed) -> mono float array at SR
"""

import numpy as np

SR = 48000
BPM = 104
BEAT = 60 / BPM
D = 62                                     # D4 in MIDI
MOTIF = [0, 3, 7, 5, 3, 2]                 # D F A G F E, relative to D


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, a, d, sustain=0.0, release=0.05):
    a, r = int(a * SR), int(release * SR)
    e = np.full(n, 1.0)
    if a:
        e[:a] = np.linspace(0, 1, a)
    k = np.arange(n - a)
    e[a:] = sustain + (1 - sustain) * np.exp(-k / max(1, d * SR))
    if r and n > r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / cutoff) ** 4), len(x))


def square(f, sec, duty=0.5):
    ph = (_t(sec) * f) % 1.0
    return np.where(ph < duty, 1.0, -1.0)


def tri(f, sec):
    ph = (_t(sec) * f) % 1.0
    return 4 * np.abs(ph - 0.5) - 1


def saw(f, sec):
    return 2 * ((_t(sec) * f) % 1.0) - 1


def place(buf, clip, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(clip) <= 0:
        return
    n = min(len(clip), len(buf) - i)
    buf[i:i + n] += clip[:n] * gain


def reverb(x, size=1.6, mix=0.25, seed=0):
    r = np.random.default_rng(seed)
    n = int(size * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / (size * SR / 5))
    ir = lowpass(ir, 5000)
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[:len(x)]
    wet /= (np.max(np.abs(wet)) or 1)
    return x * (1 - mix) + wet * mix * (np.max(np.abs(x)) or 1)


# ------------------------------------------------------------- instruments

def pluck(m, sec=0.4, duty=0.25):
    return square(hz(m), sec, duty) * env(int(sec * SR), 0.003, 0.12, 0.0, 0.03) * 0.5


def lead(m, sec, duty=0.5):
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * _t(sec))
    ph = np.cumsum(hz(m) * vib) / SR % 1.0
    w = np.where(ph < duty, 1.0, -1.0)
    return lowpass(w, 3500) * env(len(w), 0.01, 0.6, 0.6, 0.08) * 0.45


def bass(m, sec):
    return tri(hz(m - 24), sec) * env(int(sec * SR), 0.004, 0.25, 0.5, 0.03) * 0.8


def pad(chord, sec):
    out = np.zeros(int(sec * SR))
    for m in chord:
        for det in (-0.08, 0.0, 0.07):
            out += saw(hz(m + det), sec)
    out = lowpass(out, 1400) / (len(chord) * 3)
    return out * env(len(out), min(0.8, sec / 3), 10, 1.0, min(0.8, sec / 3))


def kick():
    t = _t(0.35)
    f = 50 + 120 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.12) * 0.9


def snare(r):
    n = int(0.22 * SR)
    noise = lowpass(r.standard_normal(n), 7000) * env(n, 0.001, 0.06)
    body = np.sin(2 * np.pi * 190 * _t(0.22)) * env(n, 0.001, 0.04)
    return (0.6 * noise + 0.4 * body) * 0.6


def hat(r):
    n = int(0.05 * SR)
    x = r.standard_normal(n)
    x = x - lowpass(x, 6000)
    return x * env(n, 0.0005, 0.012) * 0.25


def braam(sec, root=D - 24):
    """The cinematic low brass hit for Null: detuned saws, filter opening."""
    t = _t(sec)
    out = np.zeros(len(t))
    for m in (root, root + 7, root + 12):
        for det in (-0.12, 0.0, 0.1):
            out += saw(hz(m + det), sec)
    cut = 180 + 900 * np.minimum(1, t / (sec * 0.35))
    # time-varying low-pass, approximated in blocks
    y = np.zeros_like(out)
    blk = int(0.05 * SR)
    for i in range(0, len(out), blk):
        seg = out[max(0, i - blk):i + 2 * blk]
        y[i:i + blk] = lowpass(seg, cut[min(i, len(cut) - 1)])[(i - max(0, i - blk)):(i - max(0, i - blk)) + len(y[i:i + blk])]
    sub = np.sin(2 * np.pi * hz(root - 12) * t)
    return (y / 9 + 0.5 * sub) * env(len(t), 0.06, sec * 0.5, 0.3, 0.6)


# ------------------------------------------------------------------- cues

def theme_soft(sec, seed=0):
    out = np.zeros(int((sec + 2) * SR))
    chords = [[D - 12, D - 5, D + 3], [D - 14, D - 7, D + 0], [D - 9, D - 2, D + 5], [D - 7, D + 0, D + 4]]
    bar = BEAT * 4
    k = 0
    while k * bar < sec:
        place(out, pad(chords[k % 4], bar + 0.6), k * bar, 0.5)
        k += 1
    notes = MOTIF + [0, -2]
    for i, n in enumerate(notes * 4):
        at = BEAT * 0.5 + i * BEAT * (1 if i % 8 < 6 else 1.5)
        if at < sec - 0.3:
            place(out, pluck(D + 12 + n, 0.5), at, 0.35)
    return reverb(out, 2.2, 0.35, seed)[:int(sec * SR)]


def chase(sec, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros(int((sec + 1) * SR))
    eighth = BEAT / 2 * 0.72                 # faster: the world is ending
    roots = [0, 0, -4, -2]                   # Dm  Dm  Bb  C
    i = 0
    while i * eighth < sec:
        bar_pos = i % 8
        root = D + roots[(i // 8) % 4]
        at = i * eighth
        place(out, bass(root + (12 if bar_pos % 2 else 0), eighth * 0.95), at, 0.7)
        arp = [0, 3, 7, 12][i % 4]
        place(out, pluck(root + 12 + arp, eighth * 0.9, 0.125), at, 0.22)
        if bar_pos in (0, 4):
            place(out, kick(), at, 0.9)
        if bar_pos in (2, 6):
            place(out, snare(r), at, 0.7)
        place(out, hat(r), at, 0.6)
        i += 1
    for j, n in enumerate(MOTIF):            # the theme, urgent, on top
        place(out, lead(D + 12 + n, eighth * 1.8), 8 * eighth + j * eighth * 2, 0.3)
    return reverb(out, 1.2, 0.18, seed)[:int(sec * SR)]


def null_theme(sec, seed=0):
    out = np.zeros(int((sec + 3) * SR))
    t = _t(sec + 3)
    drone = (np.sin(2 * np.pi * hz(D - 36) * t) + 0.4 * np.sin(2 * np.pi * hz(D - 29) * t * 1.002))
    out += 0.35 * drone * np.minimum(1, t / 1.5)
    place(out, braam(3.5), 0.0, 0.9)
    if sec > 5:
        place(out, braam(3.5, D - 26), 4.0, 0.8)
    for j, n in enumerate(MOTIF[:4]):        # the theme, slowed down and low
        at = 1.2 + j * BEAT * 2
        if at < sec:
            place(out, lead(D - 12 + n, BEAT * 1.9, 0.3), at, 0.25)
    return reverb(out, 3.0, 0.4, seed)[:int(sec * SR)]


def theme_full(sec, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros(int((sec + 2) * SR))
    chords = [[D - 12, D - 5, D + 3], [D - 14, D - 7, D + 0], [D - 9, D - 2, D + 5], [D - 7, D + 0, D + 4]]
    bar = BEAT * 4
    for k in range(int(sec / bar) + 1):
        place(out, pad(chords[k % 4], bar + 0.4), k * bar, 0.45)
        for b in range(8):
            at = k * bar + b * BEAT / 2
            place(out, bass(D + [0, -2, -7, -5][k % 4] + (12 if b % 2 else 0), BEAT / 2 * 0.9), at, 0.6)
            if b in (0, 4):
                place(out, kick(), at, 0.9)
            if b in (2, 6):
                place(out, snare(r), at, 0.6)
            place(out, hat(r), at, 0.5)
    for j, n in enumerate(MOTIF + [0]):
        place(out, lead(D + 12 + n, BEAT * (0.95 if j < 6 else 2.5)), j * BEAT, 0.4)
    sting_at = max(0.0, sec - 1.2)
    place(out, braam(1.6, D - 24), sting_at, 0.6)
    return reverb(out, 1.8, 0.25, seed)[:int(sec * SR)]


CUES = {"theme_soft": theme_soft, "chase": chase, "null": null_theme, "theme_full": theme_full}


def render(cue, sec, seed=0):
    x = CUES[cue](sec, seed)
    fade = int(min(0.4, sec / 4) * SR)
    x[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    if fade:
        x[-fade:] *= np.linspace(1, 0, fade)
    m = np.max(np.abs(x)) or 1
    return x / m * 0.9


if __name__ == "__main__":
    import sys
    import soundfile as sf
    out = sys.argv[1] if len(sys.argv) > 1 else "build/music_demo.wav"
    parts = [render(c, s) for c, s in (("theme_soft", 9), ("chase", 8), ("null", 7), ("theme_full", 5))]
    gap = np.zeros(int(0.5 * SR))
    demo = np.concatenate(sum(([p, gap] for p in parts), []))
    sf.write(out, np.stack([demo, demo], 1).astype(np.float32), SR)
    print("wrote", out, round(len(demo) / SR, 1), "s")
