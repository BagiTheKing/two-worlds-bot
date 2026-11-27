"""
Can every line be heard? Whisper listens to the finished soundtrack (voices,
music and effects together), one line at a time, and lists the scripted words
it could not hear.

    python tools/hearing_check.py build/audio.wav build/timeline.json

Never fails the build: it prints a report for the voice log. A line flagged
here is buried (the mix), clipped (its cut) or mumbled (the take).
"""

import json
import re
import sys

import numpy as np
import soundfile as sf


def words(s):
    return re.findall(r"[a-z0-9']+", s.lower().replace("—", " "))


def main(audio_path, timeline_path):
    from faster_whisper import WhisperModel
    a, sr = sf.read(audio_path)
    a = a.mean(axis=1) if a.ndim > 1 else a
    tl = json.load(open(timeline_path))
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    flagged = 0
    print("hearing check (Whisper on the final mix, line by line):")
    for ln in tl["lines"]:
        i0, i1 = int(max(0.0, ln["start"] - 0.15) * sr), int((ln["end"] + 0.25) * sr)
        x = a[i0:i1].astype(np.float32)
        x16 = np.interp(np.arange(0, len(x), sr / 16000), np.arange(len(x)), x).astype(np.float32)
        # no prompt with the script: it would make Whisper "hear" buried words
        segs, _ = model.transcribe(x16, language="en", beam_size=5, vad_filter=False)
        heard = " ".join(s.text for s in segs).strip()
        got = set(words(heard))
        want = [w for w in words(ln["text"]) if len(w) > 1]
        miss = [w for w in want if w not in got]
        bad = len(miss) > max(0, len(want) // 4)                # a quarter of its words or more
        flagged += bad
        extra = [w for w in words(heard) if w not in set(words(ln["text"])) and not w.isdigit()]
        bad = bad or len(extra) > 1
        flagged += bad and not (len(miss) > max(0, len(want) // 4))
        print(f"  {'!!' if bad else 'ok'} {ln['start']:6.1f}s {ln['name']:<18} heard {heard!r}"
              + (f"  missing: {' '.join(miss)}" if miss else "")
              + (f"  extra: {' '.join(extra)}" if extra else ""))
    print(f"hearing check: {flagged} of {len(tl['lines'])} lines flagged")


if __name__ == "__main__":
    try:
        main(*sys.argv[1:3])
    except Exception as e:                                        # a report, never a failed build
        print("hearing check skipped:", e)
