"""
Gemini voice audition: a short Noob/Steve exchange read by a few voice
pairings, one request per pairing (the free tier allows 10 a minute).
Writes pair_<n>.wav and pairs.txt.

    GEMINI_API_KEY=... python tools/gemini_audition.py out_dir
"""

import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import audio  # noqa: E402

PAIRS = [("Puck", "Charon"), ("Fenrir", "Orus"), ("Sadachbia", "Algenib"), ("Puck", "Iapetus")]
NOTES = ("Noob: bright, fast, cheerful cartoon character, impulsive and oblivious. "
         "Steve: calm, low, dry and deadpan.")
TURNS = [("Noob", "[cheerfully, oblivious] Oh! The bridge is under maintenance!"),
         ("Steve", "[shouting] Noob! Run!"),
         ("Noob", "[curious, innocent] Can you respawn if there's no world?"),
         ("Steve", "[flatly] No."),
         ("Noob", "[quietly, realizing] ...Oh.")]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "build/gemini_audition"
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "pairs.txt"), "w") as f:
        for i, (noob, steve) in enumerate(PAIRS, 1):
            f.write(f"Pair {i}: Noob = {noob}, Steve = {steve}\n")
            s, sr = audio.gemini_speak(TURNS, {"Noob": noob, "Steve": steve}, NOTES)
            sf.write(os.path.join(out, f"pair_{i}.wav"), s, sr)
            print("pair", i, noob, steve, round(len(s) / sr, 1), "s")


if __name__ == "__main__":
    main()
