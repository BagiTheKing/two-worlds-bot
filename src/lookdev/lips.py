"""A simple lip-sync: pick a mouth shape for every video frame from the voice
itself (loudness, hiss, brightness), using the standard 2D-animation shapes:
  X rest   A M/B/P closed   B teeth (S T K EE)   C open (EH)   D wide (AA)
  E round (AO ER)   F pucker (OO W)
Rules of thumb from hand lip-sync: shapes hold at least 2 frames, the mouth
closes briefly at dips in loudness (consonants), hissy sounds show teeth,
loud low sounds open round, loud bright sounds open wide.
Usage (as a module): shapes(wav_path, fps) -> [(frame, shape, loudness), ...]"""
import wave

import numpy as np


def _read(path):
    with wave.open(path, "rb") as w:
        n, ch, sr, sw = w.getnframes(), w.getnchannels(), w.getframerate(), w.getsampwidth()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return a / (np.abs(a).max() + 1e-9), sr


def shapes(path, fps=24):
    a, sr = _read(path)
    return shapes_from(a, sr, fps)


def shapes_from(a, sr, fps=24):
    """The same, from samples (e.g. one line's slice of the voice track)."""
    a = a / (np.abs(a).max() + 1e-9)
    hop = sr // fps
    frames = len(a) // hop
    rms, zcr, cen = [], [], []
    freqs = np.fft.rfftfreq(hop * 2, 1 / sr)
    for i in range(frames):
        seg = a[max(0, i * hop - hop // 2): i * hop + hop + hop // 2]
        rms.append(float(np.sqrt(np.mean(seg ** 2))))
        zcr.append(float(np.mean(np.abs(np.diff(np.sign(seg)))) / 2))
        spec = np.abs(np.fft.rfft(seg[: hop * 2], n=hop * 2))
        cen.append(float((spec * freqs).sum() / (spec.sum() + 1e-9)))
    rms, zcr, cen = np.array(rms), np.array(zcr), np.array(cen)
    loud = rms / (np.percentile(rms, 95) + 1e-9)
    out = []
    for i in range(frames):
        l = loud[i]
        if l < 0.08:
            s = "X"
        elif zcr[i] > 0.22 and l < 0.7:
            s = "B"                                   # hiss: teeth
        elif 0 < i < frames - 1 and l < 0.35 and loud[i - 1] > l and loud[i + 1] > l:
            s = "A"                                   # a dip between sounds: lips meet
        elif l > 0.8:
            s = "D" if cen[i] > 1100 else "E"
        elif l > 0.45:
            s = "C" if cen[i] > 900 else "E"
        elif l > 0.2:
            s = "B" if cen[i] > 1600 else ("F" if cen[i] < 600 else "C")
        else:
            s = "A"
        out.append(s)
    # hold each shape at least 2 frames
    for i in range(1, frames - 1):
        if out[i] != out[i - 1] and out[i] != out[i + 1]:
            out[i] = out[i - 1]
    return [(i, out[i], float(loud[i])) for i in range(frames)]
