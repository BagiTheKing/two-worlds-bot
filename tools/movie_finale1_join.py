"""The movie's FINALE 1/5 sound: the three published parts joined on their own timing into one chapter folder
(`movie/finale1`: audio.flac, voice.flac, timeline.json), for `prep_dir`.

  P1 (ep10_p1_entrance) and P2 (ep10_p2_omg): their published mixes as they are (stereo, decoded from the published
      episode.mp4, `movie/finale1_published/p1|p2/published_audio.flac`), cut at their timeline lengths, as the
      published Short joined them. Their voices (for the lip sync only) lifted from those mixes (voice.flac).
  P3: the movie's re-paced part (episodes/movie_finale1_p3.json, built with VOICES_FROM=movie/finale1_published/p3:
      the published takes), brought to the published part's level (the published mix = 0.646 x its raw build).

The timeline keeps every part's own beats, prefixed (p1_claws, p2_legs, p3_run, ...), the lines at their chapter
times, and a "parts" list (id, offset, the part's own timeline) that src/lookdev/movie_finale1.py reads.

    python tools/movie_finale1_join.py <p3 build dir> movie/finale1
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

SR = 48000
PUB = "movie/finale1_published"
P3_LEVEL = 0.79             # the published P3 dialogue (0.4-3.4 s) is -16.2 LUFS; the movie build is -14.3


def main(p3_dir, out):
    os.makedirs(out, exist_ok=True)
    parts = []
    for key in ("p1", "p2"):
        tl = json.load(open(os.path.join(PUB, key, "timeline.json")))
        mix, sr = sf.read(os.path.join(PUB, key, "published_audio.flac"))
        voice, sr2 = sf.read(os.path.join(PUB, key, "voice.flac"))
        mix = mix if mix.ndim > 1 else np.stack([mix, mix], 1)          # the published mixes are stereo
        assert sr == sr2 == SR
        parts.append((key, tl, mix, voice))
    tl3 = json.load(open(os.path.join(p3_dir, "timeline.json")))
    mix3, sr = sf.read(os.path.join(p3_dir, "audio.wav"))
    v3, _ = sf.read(os.path.join(p3_dir, "voice.wav"))
    mix3 = (mix3 if mix3.ndim > 1 else np.stack([mix3, mix3], 1)) * P3_LEVEL
    v3 = v3.mean(axis=1) if v3.ndim > 1 else v3
    parts.append(("p3", tl3, mix3, v3))

    audio, voice = [], []
    beats, lines, info = {}, [], []
    off = 0.0
    for i, (key, tl, mix, v) in enumerate(parts):
        last = i == len(parts) - 1
        n = len(mix) if last else int(round(tl["length"] * SR))
        a = np.zeros((n, 2))
        a[:min(n, len(mix))] = mix[:n]
        vv = np.zeros(n)
        vv[:min(n, len(v))] = v[:n]
        f = int(0.004 * SR)                        # no click at the seams (the parts were cut hard in the Short too)
        if i:
            a[:f] *= np.linspace(0, 1, f)[:, None]
        if not last:
            a[-f:] *= np.linspace(1, 0, f)[:, None]
        audio.append(a)
        voice.append(vv)
        for name, (s, e) in tl["beats"].items():
            beats[f"{key}_{name}"] = [round(s + off, 3), round(e + off, 3)]
        for ln in tl["lines"]:
            ln = dict(ln, start=round(ln["start"] + off, 3), end=round(ln["end"] + off, 3))
            ln.pop("caption_y", None)               # the movie's own caption layout
            lines.append(ln)
        info.append({"id": key, "offset": round(off, 3), "length": tl["length"], "timeline": tl})
        off += tl["length"]
    length = round(off, 3)
    A = np.concatenate(audio)
    V = np.concatenate(voice)
    pk = np.max(np.abs(A))
    if pk > 0.99:
        A *= 0.99 / pk
    sf.write(os.path.join(out, "audio.flac"), A.astype(np.float32), SR)
    sf.write(os.path.join(out, "voice.flac"), V.astype(np.float32), SR)
    tl = {"id": "movie_finale1", "fps": 24, "length": length, "beats": beats, "impacts": [], "fx_times": {},
          "lines": lines, "cast": {**parts[0][1].get("cast", {}), **parts[1][1].get("cast", {}), **tl3.get("cast", {})},
          "overlays": [{"type": "watermark", "text": "@GLITCHBOUND2469", "start": 0.0, "end": round(length + 0.4, 3)},
                       {"type": "hud", "text": "REALITY: 12%", "alert": True, "start": 0.0, "end": round(length + 0.4, 3)}],
          "parts": info}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), indent=1)
    print(f"wrote {out}: {length:.3f} s (audio {len(A) / SR:.2f} s); parts at", [p["offset"] for p in info])


if __name__ == "__main__":
    main(*sys.argv[1:3])
