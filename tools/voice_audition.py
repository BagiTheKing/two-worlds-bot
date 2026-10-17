"""
Voice auditions: every voice on the ElevenLabs account reads the same test
lines for each character, as one reel per character. A number is announced
before each candidate; candidates.txt maps the numbers to voice names and
ids, which go into the episode's cast as "eleven_voice".

    ELEVENLABS_API_KEY=... python tools/voice_audition.py out_dir [--max 14]
"""

import argparse
import json
import os
import sys

import numpy as np
import requests
import soundfile as sf

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import audio  # noqa: E402

LINES = {
    "noob": "[excited] Oh! The bridge is under maintenance! [laughs] Okay, okay... "
            "can you respawn if there's no world?",
    "steve": "[flatly] No. [pause] [sighs] It's a tree. You need a tool.",
}


def voices(key, limit):
    r = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": key}, timeout=60)
    r.raise_for_status()
    out = []
    for v in r.json().get("voices", []):
        labels = v.get("labels") or {}
        if labels.get("gender", "male") != "male":
            continue
        out.append({"name": v["name"], "id": v["voice_id"],
                    "labels": {k: labels.get(k) for k in ("age", "accent", "description", "use_case")}})
    return out[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--max", type=int, default=14)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    cands = voices(os.environ["ELEVENLABS_API_KEY"], a.max)
    gap = np.zeros(int(0.7 * 24000))
    with open(os.path.join(a.out_dir, "candidates.txt"), "w") as f:
        for i, v in enumerate(cands, 1):
            f.write(f"{i:2d}. {v['name']:<22} {v['id']}  {json.dumps(v['labels'])}\n")
    for who, line in LINES.items():
        reel = []
        for i, v in enumerate(cands, 1):
            num, sr = audio._kokoro_say(f"Number {i}.", "bf_emma", 1.0)
            try:
                s, sr2 = audio._eleven_take(line, v["id"], 0.5, 1000)
            except Exception as ex:                      # skip voices v3 cannot use
                print("skip", v["name"], ex)
                continue
            reel += [num / (np.abs(num).max() or 1) * 0.6, gap[:len(gap) // 2],
                     s / (np.abs(s).max() or 1) * 0.9, gap]
            print(who, i, v["name"])
        sf.write(os.path.join(a.out_dir, f"{who}_candidates.wav"), np.concatenate(reel), 24000)


if __name__ == "__main__":
    main()
