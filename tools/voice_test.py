"""
Compare Kokoro (flat, local) with Chatterbox (expressive, local) on the same
lines. Chatterbox clones the timbre of a short Kokoro reference clip per
character, so each character keeps one consistent voice while the delivery
gets emotion. Writes WAVs and one comparison reel to out_dir.

    python tools/voice_test.py out_dir
"""

import os
import sys

import numpy as np
import soundfile as sf

OUT = sys.argv[1] if len(sys.argv) > 1 else "build/voicetest"
os.makedirs(OUT, exist_ok=True)

REFS = {
    "noob": ("am_puck", 1.1, "Oh wow, this place is amazing! I have no idea where I am, "
             "but honestly, that has never stopped me before. Let's go!"),
    "steve": ("am_michael", 0.95, "Every problem has a solution. You just need the right "
              "blocks, the right tools, and enough time to build it properly."),
}
# (who, text, exaggeration, cfg_weight): higher exaggeration = more emotion,
# lower cfg = slower, more deliberate pacing
LINES = [
    ("noob", "Okay. A tree. One punch. Watch this!", 0.8, 0.4),
    ("steve", "It's a tree. You need a tool.", 0.35, 0.5),
    ("noob", "The bridge is under maintenance.", 0.55, 0.5),
    ("noob", "Can you respawn if there's no world?", 0.6, 0.45),
    ("steve", "No.", 0.3, 0.5),
    ("noob", "...Oh.", 0.4, 0.5),
]


def main():
    from kokoro_onnx import Kokoro
    k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
    for who, (v, sp, text) in REFS.items():
        s, sr = k.create(text, voice=v, speed=sp, lang="en-us")
        sf.write(f"{OUT}/ref_{who}.wav", s, sr)
    kok = []
    for i, (who, text, _, _) in enumerate(LINES):
        v, sp, _ = REFS[who]
        s, sr = k.create(text, voice=v, speed=sp, lang="en-us")
        sf.write(f"{OUT}/kokoro_{i}_{who}.wav", s, sr)
        kok.append((s, sr))

    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="cpu")
    cb = []
    for i, (who, text, exag, cfg) in enumerate(LINES):
        torch.manual_seed(i)
        wav = m.generate(text, audio_prompt_path=f"{OUT}/ref_{who}.wav",
                         exaggeration=exag, cfg_weight=cfg)
        ta.save(f"{OUT}/chatterbox_{i}_{who}.wav", wav, m.sr)
        cb.append((wav.squeeze(0).numpy(), m.sr))

    # one reel: each line Kokoro then Chatterbox, with short gaps
    sr = 24000
    reel = []
    for (a, ra), (b, rb) in zip(kok, cb):
        for s, r in ((a, ra), (b, rb)):
            s = np.interp(np.linspace(0, len(s) - 1, int(len(s) * sr / r)), np.arange(len(s)), s)
            reel += [s / (np.abs(s).max() or 1) * 0.9, np.zeros(int(0.5 * sr))]
        reel.append(np.zeros(int(0.6 * sr)))
    sf.write(f"{OUT}/compare_kokoro_then_chatterbox.wav", np.concatenate(reel), sr)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
