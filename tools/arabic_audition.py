"""
Arabic voice audition for the dubs: the same short exchange in three styles
(classic cartoon-dub Standard Arabic, Egyptian, Gulf), each read with three
candidate voices for Steve (the Noob stays Puck). Each Steve voice says the
Noob's name with a different spelling, to hear which one sounds like "Noob".
One scene per request, with acting directions, on one pinned model.
Writes <style>.wav (the three voices one after another, 1 s apart) and
index.txt.

    GEMINI_API_KEY=... python tools/arabic_audition.py out_dir
"""

import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import audio  # noqa: E402

audio.PIN_MODEL = "gemini-3.8-flash-tts"
STEVES = [("Charon", "نوب"), ("Orus", "نُوب"), ("Algenib", "Noob")]

STYLES = {
    # classic Arabic cartoon dubbing: Standard Arabic, lively, with only the
    # vowel marks that prevent a misreading, and natural pausal line endings
    "msa_spacetoon": {
        "tone": "in the lively, expressive style of a classic Arabic cartoon dub",
        "vo": "كان هناك عالَمان.", "run": "{noob}! اهرب!",
        "running": "أنا أهرب فعلاً!", "respawn": "ستيف... هل نعود للحياة إذا اختفى العالَم؟"},
    "egyptian": {
        "tone": "in casual Egyptian Arabic",
        "vo": "زمان كان فيه دُنيتين.", "run": "{noob}! اجري!",
        "running": "ما أنا بجري!", "respawn": "ستيف... هو ينفع نعمل ريسبون لو الدنيا اختفت؟"},
    "gulf": {
        "tone": "in casual Gulf Arabic",
        "vo": "زمان كان فيه عالَمين.", "run": "{noob}! اشرد!",
        "running": "والله إني أشرد!", "respawn": "ستيف... نقدر نسوي ريسبون لو العالم اختفى؟"},
}


def turns(st, noob):
    t = st["tone"]
    return [("Steve", f"[softly, like a storyteller, {t}] {st['vo']}"),
            ("Steve", f"[shouting, alarmed, {t}] {st['run'].format(noob=noob)}"),
            ("Noob", f"[panicked, shouting, {t}] {st['running']}"),
            ("Noob", f"[curious, innocent, {t}] {st['respawn']}")]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "build/arabic_audition"
    os.makedirs(out, exist_ok=True)
    index = open(os.path.join(out, "index.txt"), "w")
    for name, st in STYLES.items():
        clips = []
        for k, (steve, noob) in enumerate(STEVES, 1):
            s, sr = audio.gemini_speak(turns(st, noob), {"Noob": "Puck", "Steve": steve})
            s = np.asarray(s, dtype=np.float64)
            clips += [s / (np.abs(s).max() or 1) * 0.9, np.zeros(sr)]
            index.write(f"{name} #{k}: Steve = {steve}, Noob spelled {noob}\n")
            print(name, k, steve, noob, round(len(s) / sr, 1), "s")
        sf.write(os.path.join(out, f"{name}.wav"), np.concatenate(clips), sr)
    index.close()


if __name__ == "__main__":
    main()
