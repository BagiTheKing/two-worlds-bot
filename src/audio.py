"""
Voices, sound effects and the episode timeline.

The audio decides the timing: every dialogue line is synthesised first
(Kokoro, local, Apache-2.0), and the beats between lines get the durations
the episode file asks for. The result is build/timeline.json, which the
Blender scene reads, so mouths (head bobs), punches and cuts land exactly on
the sound. All sound effects are synthesised here from noise and sine waves,
so there is nothing to license.

    python src/audio.py episodes/ep00_poc.json build/
"""

import json
import math
import os
import sys

import numpy as np
import soundfile as sf

SR = 48000
KOKORO_SR = 24000
MODEL = os.getenv("KOKORO_MODEL_PATH", "models/kokoro-v1.0.onnx")
VOICES = os.getenv("KOKORO_VOICES_PATH", "models/voices-v1.0.bin")

PUNCH_AT = 0.18          # seconds into a "punch" beat when the fist lands
FLURRY_GAP = 0.19        # seconds between hits in a "flurry" beat
rng = np.random.default_rng(7)


# ------------------------------------------------------------------ helpers

def t(sec):
    return np.arange(int(sec * SR)) / SR


def band(x, lo, hi):
    """Band-pass through the FFT with soft edges (no scipy needed)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * mask, len(x))


def env(n, attack, decay):
    a = int(attack * SR)
    e = np.exp(-np.arange(n) / max(1, decay * SR))
    if a:
        e[:a] *= np.linspace(0, 1, a)
    return e


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def place(mix, clip, at, gain=1.0):
    i = int(at * SR)
    if i >= len(mix):
        return
    n = min(len(clip), len(mix) - i)
    mix[i:i + n] += clip[:n] * gain


# --------------------------------------------------------------- the sounds

def sfx_portal(dur):
    x = t(dur + 0.6)
    sweep = np.sin(2 * np.pi * (80 * x + 260 * x ** 2))
    hiss = band(rng.standard_normal(len(x)), 600, 5000)
    s = 0.6 * sweep * np.sin(np.pi * x / x[-1]) + 0.5 * norm(hiss) * env(len(x), 0.3, 0.6)
    return norm(s, 0.8)


def sfx_fall(dur):
    x = t(dur)
    f = 1400 - 900 * x / dur
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0.1, 0.5, len(x)), 0.25)


def sfx_thump(freq=70, length=0.45, click=0.5):
    x = t(length)
    body = np.sin(2 * np.pi * freq * x * (1 - 0.4 * x)) * env(len(x), 0.002, 0.12)
    crack = band(rng.standard_normal(len(x)), 300, 4000) * env(len(x), 0.0005, 0.02)
    return norm(body + click * norm(crack), 0.9)


def sfx_land(dur):
    return sfx_thump(55, 0.6, 0.35)


def sfx_punch_wood():
    x = t(0.3)
    knock = np.sin(2 * np.pi * 180 * x) * env(len(x), 0.001, 0.05)
    tap = band(rng.standard_normal(len(x)), 800, 3500) * env(len(x), 0.0005, 0.015)
    return norm(knock + 0.7 * norm(tap), 0.9)


def sfx_step():
    x = t(0.12)
    return norm(band(rng.standard_normal(len(x)), 150, 1800) * env(len(x), 0.002, 0.03), 0.4)


def sfx_break():
    out = np.zeros(int(0.8 * SR))
    for i in range(7):
        place(out, norm(band(rng.standard_normal(int(0.08 * SR)), 400 + i * 200, 3000))
              * env(int(0.08 * SR), 0.001, 0.02), i * 0.035)
    place(out, sfx_thump(240, 0.3, 0.8), 0.0)
    pop = np.sin(2 * np.pi * 520 * t(0.12) * (1 + 2 * t(0.12))) * env(int(0.12 * SR), 0.001, 0.04)
    place(out, pop, 0.25, 0.6)
    return norm(out, 0.9)


def sfx_glitch(dur):
    """The Null's signature: digital stutter over a low drone."""
    n = int((dur + 1.5) * SR)
    out = np.zeros(n)
    x = t(dur + 1.5)
    drone = (np.sin(2 * np.pi * 41 * x) + 0.5 * np.sin(2 * np.pi * 61.5 * x)) * np.minimum(1, x / 0.4)
    out += 0.5 * drone
    pos = 0.0
    while pos < dur:
        seg = rng.uniform(0.03, 0.09)
        f = rng.choice([220, 330, 880, 1320, 95])
        burst = np.sign(np.sin(2 * np.pi * f * t(seg)))
        burst = np.round(burst * 4) / 4 * env(len(burst), 0.001, seg)
        place(out, burst, pos, 0.35)
        pos += seg + rng.uniform(0.0, 0.12)
    # three-note signal
    for i, f in enumerate((392, 311, 466)):
        tone = np.sin(2 * np.pi * f * t(0.35)) * env(int(0.35 * SR), 0.01, 0.25)
        place(out, tone, 0.25 + i * 0.38, 0.45)
    return norm(out, 0.8)


def ambience(length):
    """Wind plus a few birds."""
    n = int(length * SR)
    wind = band(rng.standard_normal(n), 80, 700)
    wind = norm(wind) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * np.arange(n) / SR))
    out = 0.5 * wind
    at = 0.8
    while at < length - 1:
        x = t(0.09)
        chirp = np.sin(2 * np.pi * (3200 * x + 9000 * x ** 2)) * env(len(x), 0.005, 0.03)
        place(out, chirp, at, 0.25)
        place(out, chirp, at + 0.13, 0.18)
        at += rng.uniform(1.6, 3.2)
    return out


# ------------------------------------------------------------------- voices

_kokoro = None
_chatterbox = None
ENGINE = os.getenv("VOICE_ENGINE", "kokoro")        # "chatterbox" for final renders
REF_LINES = {
    "am_puck": "Oh wow, this place is amazing! I have no idea where I am, but "
               "honestly, that has never stopped me before. Let's go!",
    "am_michael": "Every problem has a solution. You just need the right blocks, "
                  "the right tools, and enough time to build it properly.",
}


def _kokoro_say(text, voice, speed):
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(MODEL, VOICES)
    s, sr = _kokoro.create(text, voice=voice, speed=speed, lang="en-us")
    return np.asarray(s, dtype=np.float64), sr


def tts_text(text):
    """What the voice model reads. ALL-CAPS words get spelled out letter by
    letter ("RUN" -> "R... run"), so shout with "!" instead of capitals."""
    words = []
    for k, w in enumerate(text.split()):
        core = "".join(ch for ch in w if ch.isalpha())
        if len(core) > 1 and core.isupper():
            w = w.lower()
            if k == 0 or words[-1][-1:] in ".!?":
                w = w[0].upper() + w[1:]
        words.append(w)
    return " ".join(words)


def _norm_words(text):
    import unicodedata
    # diacritics (Arabic harakat, accents) are dropped, not taken for word breaks
    text = "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")
    keep = "".join(ch.lower() if (ch.isalnum() or ch in "' ") else " " for ch in text)
    return keep.split()


_whisper = None
WHISPER_LANG = "en"            # an episode's "language" (dubs) sets it
PIN_MODEL = None               # an episode's "tts_model" pins every take to one model


def transcribe(samples, sr):
    """Words with timings, from Whisper (faster-whisper, CPU)."""
    global _whisper
    from faster_whisper import WhisperModel
    if _whisper is None:
        _whisper = WhisperModel(os.getenv("WHISPER_MODEL", "base.en"), device="cpu", compute_type="int8")
    x = np.interp(np.linspace(0, len(samples) - 1, int(len(samples) * 16000 / sr)),
                  np.arange(len(samples)), samples).astype(np.float32)
    # temperature 0 only: Whisper's default retries at higher temperatures
    # sample at random, so the same audio could be cut differently each run
    segs, _ = _whisper.transcribe(x, language=WHISPER_LANG, word_timestamps=True, beam_size=5,
                                  condition_on_previous_text=False, temperature=0.0)
    return [(w.word, w.start, w.end) for seg in segs for w in (seg.words or [])]


def score_take(text, words):
    """How well a take says the line: similarity of the words, minus a
    penalty for extra words (stutters, invented sounds)."""
    import difflib
    ref, hyp = _norm_words(text), _norm_words(" ".join(w for w, _, _ in words))
    if not ref:
        return 0.0
    sim = difflib.SequenceMatcher(None, " ".join(ref), " ".join(hyp)).ratio()
    return sim - 0.15 * max(0, len(hyp) - len(ref))


def _chatterbox_take(text, voice, speed, emotion, pace, ref_dir, seed):
    global _chatterbox
    import torch
    if _chatterbox is None:
        from chatterbox.tts import ChatterboxTTS
        _chatterbox = ChatterboxTTS.from_pretrained(device="cpu")
    ref = os.path.join(ref_dir, f"ref_{voice}.wav")
    if not os.path.exists(ref):
        s, sr = _kokoro_say(REF_LINES.get(voice, REF_LINES["am_puck"]), voice, speed)
        os.makedirs(ref_dir, exist_ok=True)
        sf.write(ref, s, sr)
    torch.manual_seed(seed)
    wav = _chatterbox.generate(tts_text(text), audio_prompt_path=ref,
                               exaggeration=emotion, cfg_weight=pace)
    return wav.squeeze(0).numpy().astype(np.float64), _chatterbox.sr


def _chatterbox_say(text, voice, speed, emotion, pace, ref_dir, takes=3, max_takes=6):
    """Chatterbox performs the line in the timbre of a Kokoro reference clip,
    so every character keeps one voice but gets real delivery. Several takes
    are generated; Whisper transcribes each and the take that says the line
    best wins, trimmed to where its first word starts and last word ends."""
    best = None
    base = sum(map(ord, text))
    k = 0
    while k < max_takes and (k < takes or best[0] < 0.85):
        e = emotion if k < takes else max(0.25, emotion - 0.15)
        s, sr = _chatterbox_take(text, voice, speed, e, pace, ref_dir, base + 7919 * k)
        try:
            words = transcribe(s, sr)
            sc = score_take(text, words)
        except Exception as ex:                    # no Whisper: keep the first take
            print("whisper unavailable:", ex)
            return s, sr
        print(f"  take {k}: {sc:.2f} {' '.join(w for w, _, _ in words)!r}")
        if best is None or sc > best[0]:
            best = (sc, s, sr, words)
        k += 1
    sc, s, sr, words = best
    if words and sc >= 0.5:                        # trim stray sounds around the words
        a = max(0, int((words[0][1] - 0.06) * sr))
        b = min(len(s), int((words[-1][2] + 0.15) * sr))
        s = s[a:b]
    print(f"line {text!r}: best {sc:.2f}")
    return s, sr


# --------------------------------------------------------------- ElevenLabs
# Eleven v3 acts: inline audio tags such as [excited], [whispers], [sighs]
# shape the delivery. Each cast member names a voice id ("eleven_voice");
# the key comes from the ELEVENLABS_API_KEY secret and is never printed.

ELEVEN = "https://api.elevenlabs.io/v1"


def _eleven_post(path, payload, timeout=120):
    import requests
    key = os.environ["ELEVENLABS_API_KEY"]
    for attempt in range(4):
        r = requests.post(ELEVEN + path, json=payload, timeout=timeout,
                          headers={"xi-api-key": key, "Content-Type": "application/json"})
        if r.status_code == 429 or r.status_code >= 500:
            import time
            time.sleep(2 ** attempt * 3)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs {path.split('?')[0]}: HTTP {r.status_code} {r.text[:300]}")
        return r.content
    raise RuntimeError(f"ElevenLabs {path.split('?')[0]}: still failing after retries")


def _eleven_take(text, voice_id, stability, seed):
    pcm = _eleven_post(f"/text-to-speech/{voice_id}?output_format=pcm_24000", {
        "text": text, "model_id": os.getenv("ELEVEN_MODEL", "eleven_v3"), "seed": seed,
        "voice_settings": {"stability": stability, "similarity_boost": 0.8}})
    return np.frombuffer(pcm, dtype="<i2").astype(np.float64) / 32768.0, 24000


def eleven_sfx(prompt, seconds):
    """A sound effect from a description (screams, gasps, crowd noise...)."""
    mp3 = _eleven_post("/sound-generation", {"text": prompt, "duration_seconds": seconds,
                                             "prompt_influence": 0.6})
    import io
    import subprocess
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "-", "-f", "s16le", "-ac", "1",
                          "-ar", "24000", "-"], input=mp3, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0, 24000


def _eleven_say(text, voice_id, stability, takes=2, max_takes=4):
    """Best of a few takes, checked by Whisper like Chatterbox's. The audio
    tags in brackets are direction, not words, so they are not scored."""
    import re
    spoken = re.sub(r"\[[^\]]*\]", " ", text)
    best = None
    k = 0
    while k < max_takes and (k < takes or best[0] < 0.85):
        s, sr = _eleven_take(text, voice_id, stability, 1000 + k)
        try:
            words = transcribe(s, sr)
            sc = score_take(spoken, words)
        except ImportError:
            return s, sr
        print(f"  take {k}: {sc:.2f} {' '.join(w for w, _, _ in words)!r}")
        if best is None or sc > best[0]:
            best = (sc, s, sr, words)
        k += 1
    sc, s, sr, words = best
    if words and sc >= 0.5:
        a = max(0, int((words[0][1] - 0.08) * sr))
        b = min(len(s), int((words[-1][2] + 0.2) * sr))
        s = s[a:b]
    print(f"line {spoken.strip()!r}: best {sc:.2f}")
    return s, sr


# ------------------------------------------------------------------- Gemini
# Gemini's speech models voice up to two speakers in one request, so a whole
# scene's dialogue costs one request of the small free daily quota. Whisper
# then finds where each line starts and ends in the scene's audio. Direction
# goes in [brackets] at the start of a line; the key comes from the
# GEMINI_API_KEY secret and is never printed.

GEMINI = "https://generativelanguage.googleapis.com/v1beta"
SCENE_NOTES = ("Perform this scene from an animated comedy-adventure series like "
               "professional voice actors: natural, expressive, with real comic timing. "
               "Words in [brackets] are acting directions: follow them, never say them.")
_gemini_models = None
_spent = set()                       # (key, model) pairs whose daily free quota is used up


def gemini_keys():
    """GEMINI_API_KEY, GEMINI_API_KEY_2, ... Quota is per Google Cloud
    project, so keys from different projects each add a daily allowance."""
    keys = [os.environ.get("GEMINI_API_KEY")] + [os.environ.get(f"GEMINI_API_KEY_{i}") for i in range(2, 10)]
    return [k for k in keys if k]


def gemini_models():
    """Speech models to use, best first: GEMINI_TTS_MODEL, then every speech
    model the key can see (asked from the API, so renames do not break runs).
    Free quotas are per model, so later ones are fallbacks for the day."""
    global _gemini_models
    if _gemini_models is None:
        import requests
        r = requests.get(f"{GEMINI}/models", params={"pageSize": 200},
                         headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=60)
        r.raise_for_status()
        names = [m["name"].split("/")[-1] for m in r.json().get("models", []) if "tts" in m["name"]]

        def rank(n):
            return ("lite" in n, "pro" in n,
                    [-int(x) for x in "".join(c if c.isdigit() else " " for c in n).split()])
        names.sort(key=rank)
        if os.getenv("GEMINI_TTS_MODEL"):
            names.insert(0, os.environ["GEMINI_TTS_MODEL"])
        if PIN_MODEL:                # one model for the whole job: no voice changes mid-dub
            names = [PIN_MODEL]
        if not names:
            raise RuntimeError("no Gemini speech (TTS) model is available to this key")
        _gemini_models = names
        print("Gemini speech models, in order:", ", ".join(names))
    return list(_gemini_models)


def gemini_speak(turns, voices, notes=""):
    """turns: [(speaker, text)] (one or two speakers). voices: {speaker:
    voice name}. notes: acting notes for the whole scene. Returns
    (samples, 24000). Newer speech models take one part per line tagged with
    its speaker; older ones a "Name: line" script. Both are tried."""
    import base64
    import requests
    import time
    multi = len(voices) > 1
    if multi:
        speech = {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": sp, "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": v}}}
            for sp, v in voices.items()]}}
    else:
        speech = {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": next(iter(voices.values()))}}}
    script = "\n".join(f"{sp}: {t}" for sp, t in turns) if multi else " ".join(t for _, t in turns)
    if multi:   # one part per line, tagged with its speaker (newer models)
        parts = [{"text": t, "speech_metadata": {"speaker": sp}} for sp, t in turns]
        variants = [("per-line parts", {"contents": [{"role": "user", "parts": parts}]}),
                    ("script", {"contents": [{"parts": [{"text": script}]}]})]
    else:
        variants = [("script", {"contents": [{"parts": [{"text": script}]}]})]
    # acting notes are never put in the text, where they would be read aloud;
    # the [bracket] directions on each line carry the acting
    errors = []
    for model, (ki, key) in ((m, k) for m in gemini_models() for k in enumerate(gemini_keys(), 1)):
        if (ki, model) in _spent:
            continue
        for label, body in variants:
            body["generationConfig"] = {"responseModalities": ["AUDIO"], "speechConfig": speech}
            for attempt in range(4):
                r = requests.post(f"{GEMINI}/models/{model}:generateContent", json=body, timeout=300,
                                  headers={"x-goog-api-key": key})
                if r.status_code == 429 and "PerDay" in r.text:
                    break                                   # this model is done for today
                if r.status_code in (429, 500, 503):
                    wait = 30 * (attempt + 1)
                    print(f"{model}: busy or per-minute limit (HTTP {r.status_code}); retrying in {wait}s")
                    time.sleep(wait)
                    continue
                break
            if r.status_code == 429 and "PerDay" in r.text:
                print(f"{model} with key {ki}: daily free quota used up, trying the next key or model")
                _spent.add((ki, model))
                errors.append(f"{model} key {ki}: daily quota used up")
                break
            if r.status_code == 200:
                try:
                    part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
                except (KeyError, IndexError):
                    errors.append(f"{model} {label}: no audio in reply {r.text[:200]}")
                    continue
                print(f"Gemini speech ok ({model}, key {ki}, {label})")
                pcm = base64.b64decode(part["data"])
                return np.frombuffer(pcm, dtype="<i2").astype(np.float64) / 32768.0, 24000
            errors.append(f"{model} {label}: HTTP {r.status_code} {r.text[:240]}")
            if r.status_code != 400:
                break
    raise RuntimeError("Gemini speech failed:\n" + "\n".join(errors))


def _spoken(text):
    import re
    return re.sub(r"\[[^\]]*\]", " ", text).strip()


def split_scene(samples, sr, lines):
    """Find each line in a scene's audio. lines: [(name, text)]. Returns
    {name: (start, end)} for the lines Whisper could place."""
    import difflib
    words = transcribe(samples, sr)
    hyp = [(_norm_words(w) or [""])[0] for w, _, _ in words]
    ref, owner = [], []
    for k, (_, text) in enumerate(lines):
        for w in _norm_words(_spoken(text)):
            ref.append(w)
            owner.append(k)
    match = {}
    for a, b, n in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_matching_blocks():
        for i in range(n):
            match[a + i] = b + i
    spans = {}
    total = len(samples) / sr
    for k, (name, text) in enumerate(lines):
        idx = [match[i] for i in range(len(ref)) if owner[i] == k and i in match]
        n_words = sum(1 for o in owner if o == k)
        if n_words and len(idx) >= max(1, round(0.6 * n_words)):
            i0, i1 = min(idx), max(idx)
            # the line's last words misheard ("wall" heard as "well"): take as
            # many unmatched words right after it as there are scripted words missing
            last = max(i for i in range(len(ref)) if owner[i] == k)
            missing = sum(1 for i in range(len(ref)) if owner[i] == k and i not in match and i > max(
                j for j in range(len(ref)) if owner[j] == k and j in match))
            taken = set(match.values())
            while missing and i1 + 1 < len(words) and i1 + 1 not in taken and last not in match:
                i1 += 1
                missing -= 1
            prev_end = words[i0 - 1][2] if i0 > 0 else 0.0          # any word, scripted or not
            next_start = words[i1 + 1][1] if i1 + 1 < len(words) else total
            spans[name] = (words[i0][1], words[i1][2], prev_end, next_start)
    return spans


def cut_lines(samples, sr, spans, order, loose=False):
    """Cut each line at the middle of the silence between it and the lines
    around it, so drawn-out words are never clipped and pauses are not
    swallowed. (Cutting at any unrecognised word instead dropped scripted
    words Whisper misheard, like "Noob" heard as "new".)"""
    placed = [n for n in order if n in spans]
    total = len(samples) / sr
    cuts = {}
    for i, n in enumerate(placed):
        a, b = spans[n][:2]
        prev_end = spans[placed[i - 1]][1] if i else 0.0
        next_start = spans[placed[i + 1]][0] if i + 1 < len(placed) else total
        # loose (dubs): halfway into the gaps, without the 0.3 s / 0.6 s limits,
        # where Whisper's word timings are late and would chop a line's start
        start = (prev_end + a) / 2 if loose else max((prev_end + a) / 2, a - 0.3)
        end = (b + next_start) / 2 if loose else min((b + next_start) / 2, b + 0.6)
        cuts[n] = samples[int(start * sr):int(end * sr)]
    return cuts


def stretch(x, ratio, sr=SR):
    """Play x `ratio` times faster without changing its pitch (WSOLA: overlap
    windows of the original, each shifted a little to line up its waveform
    with the last one, so nothing clicks or turns into a chipmunk)."""
    if abs(ratio - 1) < 1e-3 or len(x) < sr // 10:
        return x
    n = int(0.04 * sr)
    hop = n // 2
    tol = int(0.012 * sr)
    win = np.hanning(n)
    n_out = int(len(x) / ratio)
    out = np.zeros(n_out + n)
    weight = np.zeros(n_out + n)
    prev = None
    k = 0
    while k * hop + n <= len(out):
        centre = int(k * hop * ratio)
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
        k += 1
    weight[weight < 1e-3] = 1.0
    return (out / weight)[:n_out]


def gate(x, thr_db=-32.0, cut_db=-20.0, min_gap=0.06, sr=SR):
    """Turn down breaths and mouth noise between words: wherever the voice
    stays more than thr_db below its peak for min_gap or longer, it drops by
    cut_db, with smooth ramps so nothing pumps. Words, soft consonants
    included, sit well above the threshold. The line's edges get a short fade."""
    win = int(0.01 * sr)
    if len(x) < 3 * win:
        return x
    size = len(x)
    x = np.concatenate([x, np.zeros(-size % win)])      # the last few ms count too (a take can end on a pop)
    n = len(x) // win
    rms = np.sqrt(np.mean(x.reshape(n, win) ** 2, axis=1))
    quiet = 20 * np.log10(rms / (rms.max() + 1e-12) + 1e-12) < thr_db
    g = np.ones(n)
    i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * 0.01 >= min_gap:
                g[i:j] = 10 ** (cut_db / 20)
            i = j
        else:
            i += 1
    # stray noise bursts: short, mostly hiss, after a silence (the "tch" a
    # speech model can leave at the end of a take). A word's own final "s"
    # is attached to the word, with no silence before it, and stays.
    loud = ~(20 * np.log10(rms / (rms.max() + 1e-12) + 1e-12) < -40)
    bursts = []
    i = 0
    while i < n:
        if loud[i]:
            j = i
            while j < n and loud[j]:
                j += 1
            calm_before = i == 0 or not loud[max(0, i - 10):i].any()
            calm_after = j >= n or not loud[j:min(n, j + 5)].any()
            # and the tick some takes end on: a few ms alone after the last word
            end_tick = j - i <= 3 and not loud[j:].any()
            # and its mirror: a click or smack alone before the first word,
            # with a clear pause (0.15 s) between it and the speech
            start_tick = (not loud[:i].any() and j - i <= 8 and not loud[j:min(n, j + 15)].any()
                          and loud[j:].any())
            if start_tick:
                bursts.append((0, min(n, j + 1) * win))
            elif j - i <= 20 and calm_before and calm_after and i > 0:
                y = x[i * win:j * win]
                S = np.abs(np.fft.rfft(y * np.hanning(len(y))))
                f = np.fft.rfftfreq(len(y), 1 / sr)
                if end_tick or S[f > 3000].sum() / (S.sum() + 1e-12) > 0.45:
                    bursts.append((max(0, i - 1) * win, min(n, j + 1) * win))
            i = j
        else:
            i += 1
    k = np.ones(5) / 5                                   # 50 ms ramps
    g = np.convolve(np.concatenate([[g[0]] * 2, g, [g[-1]] * 2]), k, "valid")
    gain = np.interp(np.arange(len(x)), np.arange(n) * win + win / 2, g)
    # bursts go after the smoothing, which would blur a cut this short away
    r = int(0.003 * sr)
    for a, b in bursts:
        cut = np.full(b - a + 2 * r, 10 ** (-60 / 20))
        cut[:r], cut[-r:] = np.linspace(1, cut[r], r), np.linspace(cut[r], 1, r)
        a0 = a - r
        lo, hi = max(0, a0), min(len(x), b + r)
        gain[lo:hi] *= cut[lo - a0:hi - a0]
    y = (x * gain)[:size]
    f = int(0.006 * sr)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    return y


def tighten(x, max_gap=0.22, sr=SR, floor=0.03):
    """Shorten every pause inside a line to at most max_gap seconds: the same
    take and delivery, less dead air between sentences."""
    win = int(0.01 * sr)
    n = len(x) // win
    if n < 3:
        return x
    rms = np.sqrt(np.mean(x[:n * win].reshape(n, win) ** 2, axis=1))
    quiet = rms < floor * rms.max()
    keep = np.ones(len(x), bool)
    fade = int(0.008 * sr)
    i = 0
    loud = np.nonzero(~quiet)[0]
    first, last = (loud[0], loud[-1]) if len(loud) else (0, n - 1)
    i = first
    while i <= last:
        if quiet[i]:
            j = i
            while j <= last and quiet[j]:
                j += 1
            gap = (j - i) * win
            if gap > max_gap * sr:                 # cut the middle of the pause
                cut = gap - int(max_gap * sr)
                a0 = i * win + (gap - cut) // 2
                keep[a0:a0 + cut] = False
            i = j
        else:
            i += 1
    out = x[keep].copy()
    # soften each splice
    for k in np.nonzero(np.diff(keep.astype(int)) == 1)[0]:
        pos = int(np.sum(keep[:k + 1]))
        lo, hi = max(0, pos - fade), min(len(out), pos + fade)
        out[lo:hi] *= np.concatenate([np.linspace(1, 0.3, pos - lo), np.linspace(0.3, 1, hi - pos)])
    return out


def falling(x, sr=SR):
    """A voice falling away: fades and drops in pitch as it goes."""
    n = len(x)
    rate = np.linspace(1.0, 0.82, n)                       # playback speed, slowing
    pos = np.cumsum(rate)
    pos = pos[pos < n - 1]
    y = np.interp(pos, np.arange(n), x)
    return y * np.linspace(1.0, 0.12, len(y)) ** 1.5


def gemini_lines(ep, cache_dir):
    """Voice every line of an episode with Gemini, a scene at a time.
    Returns {line name: (samples, sr)}. Each scene's full recording is cached,
    so changing how lines are cut never costs another request."""
    cast = ep["cast"]
    todo, counts = [], {}
    solos = {}          # lines re-done on their own; the scene recording stays as it was
    cut_style = {}      # lines that ask for their own cut
    pick = {}           # lines that use a chosen take of their solo recording
    borrowed = {}       # lines whose recording comes from another (cached) scene
    files = {}          # lines taken as they are from a recording in the repo
    own = set()         # lines recorded as a scene of their own, direction kept, used whole
    for ev in ep["events"]:
        if "line" not in ev:
            continue
        who = ev["line"]
        counts[who] = counts.get(who, 0) + 1
        name = ev.get("name", f"{who}_{counts[who]}")
        if ev.get("voice_file"):
            files[name] = ev["voice_file"]
            continue
        text = ev.get("direction_text") or ev.get("eleven_text") or ev["text"]
        todo.append((name, who, text, ev.get("nonverbal", False)))
        if ev.get("own_scene"):
            own.add(name)
        if ev.get("solo_text"):
            solos[name] = (who, ev["solo_text"], ev.get("nonverbal", False))
        if ev.get("solo_take") is not None:         # this take by number, not Whisper's pick
            pick[name] = ev["solo_take"]
        if ev.get("cut"):
            cut_style[name] = ev["cut"]
        if ev.get("cut_at"):               # pinned: [start, end] seconds in its scene's recording
            cut_style[name] = ("at", ev["cut_at"])
        if ev.get("solo_only"):            # recorded on its own: the scenes stay as they were
            todo.pop()
            if not ev.get("solo_text"):
                solos[name] = (who, _spoken(text), ev.get("nonverbal", False))
        if ev.get("voice_from"):
            borrowed[name] = ev["voice_from"]
    # scenes: consecutive lines with at most two voices (Null speaks alone)
    scenes, cur = [], []
    for item in todo:
        speakers = {w for _, w, _, _ in cur} | {item[1]}
        if cur and (item[3] or cur[-1][3] or len(speakers) > 2 or "null" in speakers and len(speakers) > 1
                    or item[0] in own or cur[-1][0] in own):
            scenes.append(cur)              # screams and Null are voiced on their own
            cur = []
        cur.append(item)
    if cur:
        scenes.append(cur)
    scenes = [[it[:3] for it in sc] for sc in scenes]
    nonverbal = {it[0] for it in todo if it[3]}

    out = {}
    for scene in scenes:
        if len(scene) == 1 and scene[0][0] in nonverbal and scene[0][0] in solos:
            continue                                            # voiced below, on its own
        whos = []
        for _, w, _ in scene:
            if w not in whos:
                whos.append(w)
        label = {w: w.capitalize() for w in whos}
        voices = {label[w]: cast[w]["gemini_voice"] for w in whos}
        notes = " ".join(f"{label[w]}: {cast[w].get('acting', '')}" for w in whos if cast[w].get("acting"))
        turns = [(label[w], t) for _, w, t in scene]
        raw = _cache_path(cache_dir, "gemini-scene-raw", turns, voices) if cache_dir else None
        if raw and os.path.exists(raw):
            s, sr = sf.read(raw)
        else:
            s, sr = gemini_speak(turns, voices, notes)
            if raw:
                os.makedirs(cache_dir, exist_ok=True)
                sf.write(raw, s, sr)
        names = [n for n, _, _ in scene]
        if len(scene) == 1 and names[0] in own:     # the whole take, acting and all (silence trimmed later)
            # a few takes (the first is the one above); Whisper keeps the one
            # that says the words best, so a take that adds speech or reads
            # its direction aloud loses. "solo_take" picks one by hand.
            n0, best = names[0], None
            for k in range(ep.get("own_takes", 1)):
                if k:
                    key = _cache_path(cache_dir, "gemini-scene-raw", turns, voices, k) if cache_dir else None
                    if key and os.path.exists(key):
                        s, sr = sf.read(key)
                    else:
                        s, sr = gemini_speak(turns, voices, notes)
                        if key:
                            sf.write(key, s, sr)
                words = transcribe(s, sr)
                sc = score_take(_spoken(scene[0][2]), words)
                print(f"  {n0} take {k} ({len(s) / sr:.2f}s): {sc:.2f} {' '.join(w for w, _, _ in words)[:80]!r}")
                if best is None or sc > best[0] or k == pick.get(n0):
                    best = (99 if k == pick.get(n0) else sc, s, sr)
            out[n0] = (best[1], best[2])
            continue
        if len(scene) == 1 and names[0] in nonverbal:          # a scream: no words to find
            out[names[0]] = (s, sr)
            continue
        spans = split_scene(s, sr, [(n, t) for n, _, t in scene])
        print("scene", names, "placed", [n for n in names if n in spans])
        for n in names:
            if n in spans:
                print(f"  {n}: words at {spans[n][0]:.2f}-{spans[n][1]:.2f}s of the scene")
        if os.getenv("SCENES_OUT"):         # the recording itself, to check or pin cuts by hand
            os.makedirs(os.environ["SCENES_OUT"], exist_ok=True)
            sf.write(os.path.join(os.environ["SCENES_OUT"], names[0] + ".wav"), s, sr)
        # each line's cut: the episode's choice, or the line's own ("cut": tight/loose)
        loose = {n: cut_style.get(n, "loose" if ep.get("cut_loose") else "tight") == "loose" for n in names}
        pinned = {n: cut_style[n][1] for n in names if isinstance(cut_style.get(n), tuple)}
        both = {k: cut_lines(s, sr, spans, names, loose=k) for k in (False, True)}
        cuts = {n: both[loose[n]][n] for n in names if n in both[loose[n]]}
        for n, (a, b) in pinned.items():
            seg = s[int(a * sr):int(b * sr)].copy()
            f = int(0.006 * sr)
            seg[:f] *= np.linspace(0, 1, f)
            seg[-f:] *= np.linspace(1, 0, f)
            cuts[n] = seg
            print(f"  {n}: pinned cut {a:.2f}-{b:.2f}s")
        for n, w, t in scene:
            if n in cuts:
                out[n] = (cuts[n], sr)
                continue
            # Whisper could not place it: re-take it alone, without the
            # [direction] (on their own the models tend to read it aloud), best
            # of three by how well each says the words
            print("  re-taking", n, "alone")
            clip, _ = gemini_solo(cast, w, _spoken(t), False, cache_dir)
            out[n] = (clip, sr)
    for n, (w, text, nonverbal) in solos.items():
        out[n] = gemini_solo(cast, w, text, nonverbal, cache_dir, takes=ep.get("solo_takes", 3),
                             whole=ep.get("solo_whole", False), pick=pick.get(n))
    for n, path in files.items():                    # a recording kept as it is
        clip, sr = sf.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", path))
        out[n] = (clip.mean(1) if clip.ndim > 1 else clip, sr)
        print(f"  {n}: from {path}")
    for n, src in borrowed.items():                  # an earlier episode's exact take
        turns = [tuple(t) for t in src["turns"]]
        raw = _cache_path(cache_dir, "gemini-scene-raw", turns, src["voices"])
        if not os.path.exists(raw):
            raise SystemExit(f"{n}: the recording it reuses is not in the voice cache")
        s, sr = sf.read(raw)
        spans = split_scene(s, sr, [(n, turns[0][1])])
        out[n] = (cut_lines(s, sr, spans, [n]).get(n, s), sr)
        print(f"  {n}: reused an earlier recording")
    return out


def gemini_solo(cast, who, text, nonverbal, cache_dir, takes=3, whole=False, pick=None):
    """One line on its own, without touching the scene it belongs to. Speech
    gets a few takes and Whisper keeps the one that says the words best;
    non-words (screams) get one take. No [directions]: on their own, the
    speech models tend to read them aloud. whole: keep each take whole (only
    its silence trimmed) instead of cutting it at the words Whisper found,
    for languages where Whisper's word timings are too loose to cut by."""
    label = who.capitalize()
    voice = {label: cast[who]["gemini_voice"]}
    best = None
    for k in range(1 if nonverbal else takes):
        key = _cache_path(cache_dir, "gemini-solo-raw", label, text, voice, k) if cache_dir else None
        if key and os.path.exists(key):
            clip, sr = sf.read(key)
            print(f"  solo {label} {text!r} take {k}: from the cache")
        else:
            clip, sr = gemini_speak([(label, text)], voice)
            print(f"  solo {label} {text!r} take {k}: NEW recording")
            if key:
                os.makedirs(cache_dir, exist_ok=True)
                sf.write(key, clip, sr)
        if nonverbal:
            return clip, sr
        span = split_scene(clip, sr, [("x", text)])
        words = transcribe(clip, sr)
        sc = score_take(text, words)
        print(f"  solo take {k} for {text!r}: {sc:.2f} {' '.join(w for w, _, _ in words)!r}")
        cut = clip if whole else cut_lines(clip, sr, span, ["x"]).get("x", clip)
        if best is None or sc > best[0] or k == pick:
            best = (sc if k != pick else 99, cut, sr)        # a picked take always wins
    return best[1], best[2]


def _cache_path(cache_dir, *key):
    import hashlib
    h = hashlib.sha1(json.dumps(key).encode()).hexdigest()[:16]
    return os.path.join(cache_dir, h + ".wav")


def say(text, voice, speed, pitch, emotion=0.5, pace=0.5, ref_dir="build/voice_refs",
        cache_dir=None, eleven_voice=None, stability=0.5, sfx=None):
    """sfx: {"prompt": ..., "seconds": ...} makes the line a generated sound
    effect instead of speech (screams and other non-words)."""
    engine = ENGINE if not (ENGINE == "elevenlabs" and not eleven_voice and not sfx) else "kokoro"
    key = (engine, text, voice, speed, emotion, pace, eleven_voice, stability, sfx, "v3")
    cache = _cache_path(cache_dir, *key) if cache_dir else None
    if cache and os.path.exists(cache):
        s, sr = sf.read(cache)
    else:
        if engine == "elevenlabs" and sfx:
            s, sr = eleven_sfx(sfx["prompt"], sfx.get("seconds", 2.0))
        elif engine == "elevenlabs":
            s, sr = _eleven_say(text, eleven_voice, stability)
        elif engine == "chatterbox":
            s, sr = _chatterbox_say(text, voice, speed, emotion, pace, ref_dir)
        else:
            s, sr = _kokoro_say(tts_text(text), voice, speed)
        if cache:
            os.makedirs(cache_dir, exist_ok=True)
            sf.write(cache, s, sr)
    return finish(np.asarray(s, dtype=np.float64), sr, pitch)


def finish(s, sr, pitch):
    """Trim silence, resample to the mix rate with the character's pitch."""
    peak = np.max(np.abs(s)) or 1.0
    loud = np.where(np.abs(s) > 0.03 * peak)[0]
    if len(loud):                        # generous tail: soft word endings stay
        s = s[max(0, loud[0] - int(0.03 * sr)): loud[-1] + int(0.25 * sr)]
    # a small pitch lift/drop by resampling gives each character a register
    n_out = int(len(s) * (SR / sr) / pitch)
    s = np.interp(np.linspace(0, len(s) - 1, n_out), np.arange(len(s)), s)
    return norm(s, 0.95)


# ------------------------------------------------------- episode-1 sounds

def sfx_pop():
    """A digital blip: what erasing a chunk of reality sounds like."""
    n = int(0.09 * SR)
    x = np.arange(n) / SR
    f = 1500 * np.exp(-x * 30) + 180
    blip = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.03)
    click = band(rng.standard_normal(n), 2000, 9000) * env(n, 0.0002, 0.004)
    return norm(blip + 0.4 * norm(click), 0.8)


def sfx_crackle(dur):
    n = int(dur * SR)
    out = np.zeros(n)
    k = (rng.random(n) < 0.0012) * rng.uniform(-1, 1, n)
    out += band(k, 1500, 9000)
    return norm(out, 0.35)


def sfx_whistle(dur):
    x = t(dur)
    f = 900 - 500 * x / dur
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0.6, 0.0, len(x)), 0.3)


def sfx_sub_drop(dur):
    x = t(dur)
    f = 70 * np.exp(-x * 1.2) + 28
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.02, dur * 0.6), 0.9)


def sfx_rumble_rise(dur):
    """Null rising: a slow cinematic braam over a sub swell (no noise)."""
    import music
    x = t(dur + 1.5)
    sub = np.sin(2 * np.pi * 36 * x) * np.minimum(1, x / dur) ** 2
    b = np.zeros(len(x))
    place(b, music.braam(min(3.5, dur + 1.2)), max(0.0, dur - 1.0))
    return norm(0.6 * sub + b, 0.9)


def sfx_plunge(dur):
    """Falling into the void: rushing air that rises in pitch."""
    x = t(dur)
    air = band(rng.standard_normal(len(x)), 200, 2500) * np.linspace(0.3, 1, len(x))
    return norm(air, 0.6) + sfx_whistle(dur) * 0.5


def sfx_jingle():
    """Cheerful achievement jingle, completely wrong for the moment."""
    out = np.zeros(int(1.3 * SR))
    for i, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        x = t(0.5)
        tone = sum(np.sin(2 * np.pi * f * h * x) / h ** 1.5 for h in (1, 2, 3, 4))
        place(out, tone * env(len(x), 0.003, 0.18), i * 0.09, 0.5)
    x = t(1.0)
    ding = sum(np.sin(2 * np.pi * 1568 * r * x) / (k + 1) for k, r in enumerate((1, 2.76, 5.4)))
    place(out, ding * env(len(x), 0.002, 0.35), 0.38, 0.6)
    return norm(out, 0.85)


def sfx_whoosh(dur=0.7):
    x = t(dur)
    return norm(band(rng.standard_normal(len(x)), 300, 3000) * np.sin(np.pi * x / dur) ** 2, 0.5)


def sfx_run(dur, step=0.16):
    out = np.zeros(int(dur * SR) + SR)
    k = 0.0
    while k < dur:
        place(out, sfx_step(), k, 0.7)
        k += step
    return out


def sfx_place():
    """A block snapping into place: a dense knock with a click on top."""
    x = t(0.22)
    knock = np.sin(2 * np.pi * 150 * x * (1 - 0.3 * x)) * env(len(x), 0.001, 0.05)
    click = band(rng.standard_normal(len(x)), 1500, 6000) * env(len(x), 0.0003, 0.008)
    return norm(knock + 0.5 * norm(click), 0.9)


def sfx_click():
    """A big plastic button going down."""
    out = np.zeros(int(0.3 * SR))
    for at, f in ((0.0, 2400), (0.06, 1600)):
        n = int(0.03 * SR)
        place(out, band(rng.standard_normal(n), f * 0.6, f * 1.6) * env(n, 0.0002, 0.006), at)
    place(out, sfx_thump(110, 0.2, 0.3), 0.0, 0.6)
    return norm(out, 0.8)


def sfx_respawn():
    """Popping back into existence: three quick rising blips and a sparkle."""
    out = np.zeros(int(0.6 * SR))
    for i, f in enumerate((660, 880, 1320)):
        x = t(0.12)
        place(out, np.sin(2 * np.pi * f * x) * env(len(x), 0.002, 0.05), i * 0.06, 0.6)
    x = t(0.35)
    place(out, band(rng.standard_normal(len(x)), 4000, 11000) * env(len(x), 0.005, 0.12), 0.15, 0.25)
    return norm(out, 0.8)


def sfx_groan(dur=0.9):
    """A blocky zombie: a low, wobbling, throaty moan."""
    x = t(dur)
    f = 95 + 18 * np.sin(2 * np.pi * 3.2 * x) - 25 * x / dur
    saw = 2 * ((np.cumsum(f) / SR) % 1.0) - 1
    voice = band(saw, 150, 900) + 0.4 * band(rng.standard_normal(len(x)), 200, 700)
    return norm(voice * env(len(x), 0.08, dur * 0.4), 0.6)


def sfx_burst():
    """The Noob breaking apart: a pop, a plastic clatter."""
    out = np.zeros(int(0.9 * SR))
    place(out, sfx_pop(), 0.0, 1.0)
    place(out, sfx_thump(300, 0.15, 1.0), 0.0, 0.7)
    for i in range(6):
        n = int(0.05 * SR)
        place(out, band(rng.standard_normal(n), 1200, 5000) * env(n, 0.0005, 0.012),
              0.2 + i * 0.07 + 0.03 * rng.random(), 0.5)
    return norm(out, 0.9)


def sfx_whir(dur):
    """The spinning bar: air cut twice a turn."""
    x = t(dur)
    air = band(rng.standard_normal(len(x)), 250, 2200)
    return norm(air * (0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 0.8 * x))) * np.minimum(1, x / 0.3), 0.4)


def sfx_snap():
    """A portal slamming shut: a hard hit, a sub drop, a burst of glitch."""
    out = np.zeros(int(1.6 * SR))
    place(out, sfx_thump(48, 0.7, 1.0), 0.0, 1.0)
    place(out, sfx_sub_drop(1.2), 0.0, 0.8)
    place(out, sfx_glitch(0.15)[:int(0.5 * SR)], 0.02, 0.5)
    return norm(out, 0.95)


def sfx_suck(dur=1.2):
    """A portal swallowing everything back: rushing air that rises and is
    cut off, over a falling sub."""
    x = t(dur)
    air = band(rng.standard_normal(len(x)), 300, 4000) * np.linspace(0.2, 1.0, len(x)) ** 2
    air[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    f = 220 - 160 * x / dur
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0.6, 0.0, len(x))
    return norm(norm(air) + 0.5 * tone + 0.6 * sfx_sub_drop(dur)[:len(x)], 0.9)


def sfx_crunch():
    """The pickaxe through the button: a heavy hit, plastic shattering."""
    out = np.zeros(int(1.0 * SR))
    place(out, sfx_thump(60, 0.6, 1.0), 0.0, 1.0)
    place(out, sfx_break(), 0.0, 0.9)
    for i in range(5):
        n = int(0.06 * SR)
        place(out, band(rng.standard_normal(n), 2500, 9000) * env(n, 0.0005, 0.015), 0.05 + i * 0.05, 0.5)
    return norm(out, 0.95)


def sfx_roar(dur=1.2):
    """The dragon's roar: a growling low buzz that rises and falls, with
    breath noise and a rough, rattling edge."""
    x = t(dur)
    f0 = 62 + 38 * np.sin(np.pi * x / dur) ** 1.5                  # pitch swells, then sinks
    ph = 2 * np.pi * np.cumsum(f0) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 14))             # a buzzy, throaty tone
    rattle = 1 + 0.45 * np.sin(2 * np.pi * 27 * x)                  # the growl's flutter
    breath = band(rng.standard_normal(len(x)), 250, 3200)
    shape = np.minimum(1, x / 0.08) * np.sin(np.pi * np.minimum(x / dur, 1)) ** 0.6
    return norm((norm(saw) * rattle + 0.55 * norm(breath)) * shape, 0.95)


def sfx_flaps(dur=2.0, rate=1.3):
    """Big wingbeats: a low whump on every downstroke."""
    out = np.zeros(int((dur + 0.5) * SR))
    k = 0.0
    while k < dur:
        n = int(0.32 * SR)
        y = band(rng.standard_normal(n), 60, 900) * np.sin(np.pi * np.arange(n) / n) ** 2
        place(out, norm(y, 0.8), k, 1.0)
        k += 1 / rate
    return out


SFX = {"place": lambda e: sfx_place(), "roar": lambda e: sfx_roar(e.get("dur", 1.2)),
       "flaps": lambda e: sfx_flaps(e.get("dur", 2.0), e.get("rate", 1.3)), "suck": lambda e: sfx_suck(e.get("dur", 1.2)),
       "crunch": lambda e: sfx_crunch(), "click": lambda e: sfx_click(), "respawn": lambda e: sfx_respawn(),
       "groan": lambda e: sfx_groan(e.get("dur", 0.9)), "burst": lambda e: sfx_burst(),
       "whir": lambda e: sfx_whir(e.get("dur", 2.0)), "snap": lambda e: sfx_snap(),
       "pop": lambda e: sfx_pop(), "thump": lambda e: sfx_thump(e.get("freq", 70), 0.45, 0.6),
       "glitch": lambda e: sfx_glitch(e.get("dur", 0.3)), "portal": lambda e: sfx_portal(e.get("dur", 0.9)),
       "whoosh": lambda e: sfx_whoosh(e.get("dur", 0.7)), "break": lambda e: sfx_break(),
       "jingle": lambda e: sfx_jingle(), "sub_drop": lambda e: sfx_sub_drop(e.get("dur", 1.0))}


def void_wind(length):
    n = int(length * SR)
    w = band(rng.standard_normal(n), 50, 320)
    return norm(w) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * np.arange(n) / SR))


def null_voice(s):
    """Null speaks with the Noob's voice: pitched down, doubled an octave
    lower, bit-crushed, with a reversed reverb swelling into each word."""
    def pitch(x, p):
        return np.interp(np.linspace(0, len(x) - 1, int(len(x) / p)), np.arange(len(x)), x)
    a = pitch(s, 0.62)
    b = pitch(s, 0.31)[:len(a)]
    b = np.pad(b, (0, len(a) - len(b)))
    v = a + 0.35 * b
    v = np.round(v * 48) / 48                          # a light bit crush
    tail = rng.standard_normal(int(0.9 * SR)) * np.exp(-np.arange(int(0.9 * SR)) / (0.25 * SR))
    rev = np.convolve(v[::-1], tail * 0.02)[:len(v)][::-1]
    v = np.concatenate([np.zeros(int(0.35 * SR)), v])
    rev = np.concatenate([rev, np.zeros(int(0.35 * SR))])
    return norm(v + 0.6 * rev, 0.95)


# ----------------------------------------------------------------- timeline

def resolve_ref(beats, ref, length):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from kit.timeref import resolve
    return resolve(beats, ref, length)


def build(episode_path, out_dir, keep=None):
    """keep: an earlier timeline whose timing must not change (the frames are
    already rendered). New voices are placed at the old line starts; a take
    that runs long is sped up slightly (at most 10%) to fit."""
    ep = json.load(open(episode_path))
    global WHISPER_LANG, PIN_MODEL
    WHISPER_LANG = ep.get("language", "en")
    PIN_MODEL = ep.get("tts_model")
    old = json.load(open(keep)) if keep else None
    old_lines = {ln["name"]: ln for ln in old["lines"]} if old else {}
    starts = sorted(a for a, _ in old["beats"].values()) if old else []
    cache_dir = os.getenv("VOICE_CACHE", os.path.join(out_dir, "voice_cache"))
    keeping = old is not None        # until an event says "retime"
    pre = gemini_lines(ep, cache_dir) if ENGINE == "gemini" else {}
    os.makedirs(out_dir, exist_ok=True)
    cursor = 0.0
    beats, lines, clips, impacts = {}, [], [], []
    fx_times = {}
    counts = {}
    for ev in ep["events"]:
        if "pause" in ev:
            cursor += ev["pause"]
            continue
        if ev.get("retime"):
            keeping = False
        if "beat" in ev:
            name, dur = ev["beat"], ev["dur"]
            beats[name] = [cursor, cursor + dur]
            if name == "punch":
                impacts.append(cursor + PUNCH_AT)
            if name == "flurry":
                h = cursor + 0.12
                while h < cursor + dur - 0.05:
                    impacts.append(h)
                    h += FLURRY_GAP
            kind = ev.get("sfx")
            if keeping and name in old["beats"]:
                beats[name] = list(old["beats"][name])
                cursor = beats[name][0]
                dur = beats[name][1] - cursor
            if keeping and name in old.get("fx_times", {}):
                fx_times[name] = old["fx_times"][name]
            elif kind == "erasure":
                r = np.random.default_rng(ev.get("seed", 1))
                ts = np.sort(r.uniform(cursor + 0.2, cursor + dur - 0.2, ev.get("count", 40)))
                # the pops accelerate as the corruption closes in
                ts = cursor + 0.2 + (ts - cursor - 0.2) ** 0.8 * (dur - 0.4) ** 0.2
                fx_times[name] = [round(float(x), 3) for x in ts]
            elif kind == "bridge":
                n = ev.get("count", 14)
                fx_times[name] = [round(cursor + dur * 0.7 * i / (n - 1), 3) for i in range(n)]
            if kind == "steps" and "step_every" in ev:     # on the walk cycle's foot contacts
                clips.append((kind, cursor, (dur, ev["step_every"], ev.get("step_first", 0.1))))
            elif kind:
                clips.append((kind, cursor, dur))
            if ev.get("audio_clip"):                 # a ready-made clip's own sound
                clips.append(("file", cursor, ev["audio_clip"]))
            cursor += dur
        else:
            who = ev["line"]
            c = ep["cast"][who]
            pre_name = ev.get("name", f"{who}_{counts.get(who, 0) + 1}")
            if pre_name in pre:
                s_, sr_ = pre[pre_name]
                audio = finish(np.asarray(s_, dtype=np.float64), sr_, c["pitch"])
            else:
                audio = say(ev.get("eleven_text", ev["text"]) if ENGINE == "elevenlabs" else ev["text"],
                        c["voice"], c["speed"], c["pitch"],
                        emotion=ev.get("emotion", c.get("emotion", 0.5)),
                        pace=ev.get("pace", c.get("pace", 0.5)),
                        ref_dir=os.path.join(out_dir, "voice_refs"), cache_dir=cache_dir,
                        eleven_voice=c.get("eleven_voice"),
                        stability=ev.get("stability", c.get("stability", 0.5)),
                        sfx=ev.get("sfx_voice") if ENGINE == "elevenlabs" else None)
            if ep.get("gate") is not None:              # breaths and mouth noise down
                audio = gate(audio, ep["gate"])
            if c.get("fx") == "null":
                audio = null_voice(audio)
            if ev.get("fx") == "falling":
                audio = norm(falling(audio), 0.95)
            if ev.get("tighten"):                     # shorter pauses inside the line
                audio = tighten(audio, ev["tighten"], floor=ep.get("tighten_floor", 0.03))
            if ev.get("trim") and len(audio) > ev["trim"] * SR:   # cut short, fading out
                audio = audio[:int(ev["trim"] * SR)].copy()
                f = int(ev.get("trim_fade", 0.25) * SR)
                audio[-f:] *= np.linspace(1, 0, f)
            if ev.get("mute_start"):                       # a click before the first word: silenced in place
                m = int(ev["mute_start"] * SR)
                f = int(0.01 * SR)
                audio = audio.copy()
                audio[:m - f] = 0.0
                audio[m - f:m] *= np.linspace(0, 1, f)
            if ev.get("together") and lines:              # said at the same time as the last line
                cursor = lines[-1]["start"]
            counts[who] = counts.get(who, 0) + 1
            name = ev.get("name", f"{who}_{counts[who]}")
            if keeping and name in old_lines:
                cursor = old_lines[name]["start"]
                nxt = next((x for x in starts if x > cursor + 0.01), cursor + 99)
                room = nxt + 0.1 - cursor
                if ev.get("slot") is not None:          # plays over what follows, on purpose
                    room = len(audio) / SR
                if len(audio) / SR > room:              # faster, same pitch
                    ratio = min(ep.get("fit_max", 1.10), len(audio) / SR / room)
                    audio = stretch(audio, ratio)
                    print(f"  {name}: sped up x{ratio:.2f} to fit its {room:.2f}s")
            dur = len(audio) / SR
            lines.append({"name": name, "who": who, "text": ev["text"], "vo": ev.get("vo", False),
                          "caption": ev.get("caption", True),
                          "start": round(cursor, 3), "end": round(cursor + dur, 3)})
            beats[name] = [cursor, cursor + dur]
            clips.append(("voice", cursor, audio))
            end_here = cursor + dur + ev.get("pad", 0.2)
            if ev.get("slot") is not None:        # the story moves on; the line plays over it
                end_here = cursor + ev["slot"]
            if ev.get("together") and len(lines) > 1:
                prev = lines[-2]
                prev_end = prev["start"] + ev["slot"] if ev.get("slot") is not None else prev["end"] + ev.get("pad", 0.2)
                end_here = max(end_here, prev_end)
            cursor = end_here
    length = old["length"] if keeping else cursor
    R = lambda ref: resolve_ref(beats, ref, length)  # noqa: E731

    mix = np.zeros(int((length + 0.5) * SR))
    voice = np.zeros_like(mix)
    amb_spec = ep.get("ambience")
    if amb_spec is None:                     # episode 2's original behaviour
        crack_at = beats.get("crack", [length])[0]
        amb_spec = [{"kind": "meadow", "from": 0, "to": crack_at}]
    for a in amb_spec:
        a0, a1 = R(a["from"]), R(a["to"])
        seg = (ambience if a["kind"] == "meadow" else void_wind)(a1 - a0)
        if a.get("glitch_at") is not None:   # one bird call stutters
            g = int((R(a["glitch_at"]) - a0) * SR)
            if 0 < g < len(seg) - SR // 4:
                piece = seg[g:g + int(0.06 * SR)].copy()
                for k in range(4):
                    seg[g + k * len(piece):g + (k + 1) * len(piece)] = np.round(piece * 6) / 6
            place(mix, sfx_pop(), R(a["glitch_at"]) + 0.25, 0.25)
        cut = int(0.03 * SR)
        seg[-cut:] *= np.linspace(1, 0, cut)                   # hard cuts, on purpose
        if a.get("fade_in"):
            f = int(a["fade_in"] * SR)
            seg[:f] *= np.linspace(0, 1, f)
        place(mix, seg, a0, a.get("gain", 0.10))
    for kind, at, arg in clips:
        if kind == "voice":
            place(voice, arg, at, 1.0)
        elif kind == "portal":
            place(mix, sfx_portal(arg), at, 0.5)
        elif kind == "fall":
            place(mix, sfx_fall(arg), at, 0.5)
        elif kind == "land":
            place(mix, sfx_land(arg), at, 0.7)
        elif kind == "steps":
            dur, every, first = arg if isinstance(arg, tuple) else (arg, 0.25, 0.1)
            for i in range(int((dur - first) / every) + 1):
                place(mix, sfx_step(), at + first + i * every, 0.5)
        elif kind == "glitch":
            place(mix, sfx_glitch(arg), at, 0.55)
        elif kind == "break":
            place(mix, sfx_break(), at, 0.75)
        elif kind == "crackle":
            place(mix, sfx_crackle(arg), at, 0.5)
        elif kind == "run":
            place(mix, sfx_run(arg), at, 0.45)
        elif kind == "grab":
            place(mix, sfx_thump(90, 0.4, 0.6), at + 0.05, 0.8)
            place(mix, sfx_thump(70, 0.4, 0.5), at + 0.32, 0.6)
        elif kind == "sub_drop":
            place(mix, sfx_sub_drop(arg + 1.0), at, 0.8)
        elif kind == "rumble_rise":
            place(mix, sfx_rumble_rise(arg), at, 0.7)
        elif kind == "jingle":
            place(mix, sfx_jingle(), at + 0.1, 0.7)
        elif kind == "whoosh":
            place(mix, sfx_whoosh(), at, 0.6)
        elif kind == "file":
            x, r = sf.read(arg)
            x = x.mean(axis=1) if x.ndim > 1 else x
            if r != SR:
                x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / r)), np.arange(len(x)), x)
            place(mix, x, at, 1.0)
        elif kind == "plunge":
            place(mix, sfx_plunge(arg), at, 0.6)
        elif kind == "ledge":
            place(mix, sfx_thump(160, 0.3, 1.0), at, 0.7)
    from kit.timeref import spread
    for e in ep.get("sfx", []):                   # timed effects, not tied to a beat
        times = (spread(R(e["from"]), R(e["to"]), e["count"]) if "count" in e else [R(e["at"])])
        if "to" in e and "count" not in e:       # a sound that lasts until a moment
            e = dict(e, dur=R(e["to"]) - R(e["at"]))
        for h in times:
            place(mix, SFX[e["kind"]](e), h, e.get("gain", 0.6))
    for name, ts in fx_times.items():
        for k, h in enumerate(ts):
            place(mix, sfx_pop(), h, 0.35 + 0.25 * (k % 3 == 0))
        if name.startswith("bridge"):
            place(mix, sfx_thump(200, 0.35, 1.0), ts[0], 0.6)
            place(mix, sfx_whistle(1.4), ts[-1], 0.6)
    for h in impacts:
        place(mix, sfx_punch_wood(), h, 0.6)
    score = np.zeros_like(mix)
    import music
    for k, m in enumerate(ep.get("music", [])):
        m0, m1 = R(m["from"]), R(m["to"])
        kw = {"hit_at": R(m["hit_at"]) - m0} if m.get("hit_at") else {}
        if m.get("minimal"):
            kw["minimal"] = True
        x = music.render(m["cue"], m1 - m0, seed=k, **kw)
        for sw in m.get("swell", []):           # louder while nobody speaks, eased in and out
            s0, s1 = int((R(sw["from"]) - m0) * SR), int((R(sw["to"]) - m0) * SR)
            ramp = int(sw.get("ramp", 0.3) * SR)
            g = np.ones(len(x))
            g[max(0, s0):max(0, s1)] = sw["gain"]
            for i0, i1, up in ((s0 - ramp, s0, True), (s1, s1 + ramp, False)):
                a_, b_ = max(0, i0), min(len(x), i1)
                if b_ > a_:
                    r = np.linspace(0, 1, i1 - i0)[a_ - i0:b_ - i0]
                    g[a_:b_] = 1 + (sw["gain"] - 1) * (r if up else 1 - r)
            x = x * g
        place(score, x, m0, m.get("gain", 0.2))
    duck = np.convolve(np.abs(voice) > 0.02, np.ones(SR // 10) / (SR // 10), "same")
    duck = np.clip(duck * 3, 0, 1)
    out = voice + mix * (1 - 0.45 * duck) + score * (1 - 0.75 * duck)
    out = norm(out, 0.89)
    sf.write(os.path.join(out_dir, "audio.wav"), np.stack([out, out], 1).astype(np.float32), SR)
    if os.getenv("VOICE_STEM"):                    # the voices alone, for checking dubs
        sf.write(os.path.join(out_dir, "voice.wav"), voice.astype(np.float32), SR)

    overlays = []
    for o in ep.get("overlays", []):
        o = dict(o)
        o["start"] = round(R(o.pop("from")), 3)
        to = o.pop("to")
        # "end" means the last frame: the video runs 0.4 s past the last beat
        o["end"] = round(length + 0.4 if to == "end" else R(to), 3)
        overlays.append(o)
    timeline = {"id": ep["id"], "fps": 24, "length": round(length, 3),
                "beats": {k: [round(a, 3), round(b, 3)] for k, (a, b) in beats.items()},
                "impacts": [round(h, 3) for h in impacts], "fx_times": fx_times,
                "lines": lines, "cast": ep["cast"], "overlays": overlays}
    with open(os.path.join(out_dir, "timeline.json"), "w") as f:
        json.dump(timeline, f, indent=1)
    return timeline


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("out_dir", nargs="?", default="build")
    ap.add_argument("--keep-timeline", help="re-voice only: keep this timeline's timing")
    args = ap.parse_args()
    tl = build(args.episode, args.out_dir, args.keep_timeline)
    print(json.dumps({k: tl[k] for k in ("length", "beats")}, indent=1))
