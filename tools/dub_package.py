"""
Check a dubbed soundtrack against the published episode and package it.

    python tools/dub_package.py published.mp4 published_timeline.json dub_dir out_prefix

dub_dir holds the "Dub audio" workflow's audio.flac and timeline.json.
Prints every line's start and length next to the published one, checks the
music and effects line up with the published audio where nobody speaks,
then writes out_prefix_track.m4a (trimmed to the published audio's exact
length, for the video's Languages > Audio) and out_prefix_preview.mp4.
"""

import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

SR = 48000


def mono(path, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), out],
                   check=True)
    return sf.read(out)[0]


def quiet_spans(tl, min_len=1.5):
    """Stretches with no line spoken, long enough to compare."""
    spoken = sorted((ln["start"], ln["end"]) for ln in tl["lines"])
    spans, t = [], 0.3
    for a, b in spoken + [(tl["length"] - 0.3, tl["length"])]:
        if a - t >= min_len:
            spans.append((t + 0.1, a - 0.1))
        t = max(t, b)
    return spans


def main(video, pub_tl, dub_dir, out):
    pub = json.load(open(pub_tl))
    dub = json.load(open(os.path.join(dub_dir, "timeline.json")))
    P = {ln["name"]: ln for ln in pub["lines"]}
    worst = 0.0
    print(f"length: dub {dub['length']}  published {pub['length']}")
    for ln in dub["lines"]:
        p = P[ln["name"]]
        worst = max(worst, abs(ln["start"] - p["start"]))
        print(f"  {ln['name']:14} start {ln['start']:6.2f} (published {p['start']:6.2f})  "
              f"{ln['end'] - ln['start']:4.2f}s (published {p['end'] - p['start']:4.2f}s)  {ln['text']}")
    print(f"largest line-start difference: {worst * 1000:.0f} ms")
    lines = sorted(dub["lines"], key=lambda ln: ln["start"])
    for x, y in zip(lines, lines[1:]):
        if x["end"] > y["start"] + 0.02 and y["start"] - x["start"] > 0.05:    # not lines said together
            print(f"  OVERLAP: {x['name']} runs {x['end'] - y['start']:.2f}s into {y['name']}")

    tmp = tempfile.mkdtemp()
    a = mono(video, os.path.join(tmp, "pub.wav"))
    b = mono(os.path.join(dub_dir, "audio.flac"), os.path.join(tmp, "dub.wav"))
    for t0, t1 in quiet_spans(pub):
        x = a[int(t0 * SR):int(t1 * SR)]
        best = max((np.corrcoef(x, b[int(t0 * SR) + lag:int(t1 * SR) + lag])[0, 1], lag)
                   for lag in range(-480, 481, 8))
        print(f"  no voice {t0:5.1f}-{t1:5.1f}s: music/effects line up at {best[1] / SR * 1000:+.1f} ms "
              f"(correlation {best[0]:.3f})")

    dur = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                "stream=duration", "-of", "csv=p=0", video],
                               capture_output=True, text=True, check=True).stdout.strip())
    track, preview = out + "_track.m4a", out + "_preview.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(dub_dir, "audio.flac"), "-t", str(dur),
                    "-af", f"afade=t=out:st={dur - 0.05}:d=0.05", "-c:a", "aac", "-b:a", "256k", "-ar", str(SR),
                    "-ac", "2", track], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", track, "-map", "0:v", "-map", "1:a",
                    "-c", "copy", "-shortest", "-movflags", "+faststart", preview], check=True)
    print(f"wrote {track} ({dur:.3f}s, the published audio's length) and {preview}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
