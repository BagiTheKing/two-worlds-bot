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
    keep = "".join(ch.lower() if (ch.isalnum() or ch in "' ") else " " for ch in text)
    return keep.split()


_whisper = None


def transcribe(samples, sr):
    """Words with timings, from Whisper (faster-whisper, CPU)."""
    global _whisper
    from faster_whisper import WhisperModel
    if _whisper is None:
        _whisper = WhisperModel(os.getenv("WHISPER_MODEL", "base.en"), device="cpu", compute_type="int8")
    x = np.interp(np.linspace(0, len(samples) - 1, int(len(samples) * 16000 / sr)),
                  np.arange(len(samples)), samples).astype(np.float32)
    segs, _ = _whisper.transcribe(x, language="en", word_timestamps=True, beam_size=5,
                                  condition_on_previous_text=False)
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


def _cache_path(cache_dir, *key):
    import hashlib
    h = hashlib.sha1(json.dumps(key).encode()).hexdigest()[:16]
    return os.path.join(cache_dir, h + ".wav")


def say(text, voice, speed, pitch, emotion=0.5, pace=0.5, ref_dir="build/voice_refs",
        cache_dir=None):
    cache = _cache_path(cache_dir, ENGINE, text, voice, speed, emotion, pace, "v2") if cache_dir else None
    if cache and os.path.exists(cache):
        s, sr = sf.read(cache)
    else:
        if ENGINE == "chatterbox":
            s, sr = _chatterbox_say(text, voice, speed, emotion, pace, ref_dir)
        else:
            s, sr = _kokoro_say(tts_text(text), voice, speed)
        if cache:
            os.makedirs(cache_dir, exist_ok=True)
            sf.write(cache, s, sr)
    s = np.asarray(s, dtype=np.float64)
    loud = np.where(np.abs(s) > 0.02)[0]
    if len(loud):
        s = s[max(0, loud[0] - 240): loud[-1] + 2400]
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
    old = json.load(open(keep)) if keep else None
    old_lines = {ln["name"]: ln for ln in old["lines"]} if old else {}
    starts = sorted(a for a, _ in old["beats"].values()) if old else []
    cache_dir = os.getenv("VOICE_CACHE", os.path.join(out_dir, "voice_cache"))
    os.makedirs(out_dir, exist_ok=True)
    cursor = 0.0
    beats, lines, clips, impacts = {}, [], [], []
    fx_times = {}
    counts = {}
    for ev in ep["events"]:
        if "pause" in ev:
            cursor += ev["pause"]
            continue
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
            if old and name in old["beats"]:
                beats[name] = list(old["beats"][name])
                cursor = beats[name][0]
                dur = beats[name][1] - cursor
            if old and name in old.get("fx_times", {}):
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
            if kind:
                clips.append((kind, cursor, dur))
            cursor += dur
        else:
            who = ev["line"]
            c = ep["cast"][who]
            audio = say(ev["text"], c["voice"], c["speed"], c["pitch"],
                        emotion=ev.get("emotion", c.get("emotion", 0.5)),
                        pace=ev.get("pace", c.get("pace", 0.5)),
                        ref_dir=os.path.join(out_dir, "voice_refs"), cache_dir=cache_dir)
            if c.get("fx") == "null":
                audio = null_voice(audio)
            counts[who] = counts.get(who, 0) + 1
            name = ev.get("name", f"{who}_{counts[who]}")
            if name in old_lines:
                cursor = old_lines[name]["start"]
                nxt = next((x for x in starts if x > cursor + 0.01), cursor + 99)
                room = nxt + 0.1 - cursor
                if len(audio) / SR > room:
                    ratio = min(1.10, len(audio) / SR / room)
                    audio = np.interp(np.linspace(0, len(audio) - 1, int(len(audio) / ratio)),
                                      np.arange(len(audio)), audio)
            dur = len(audio) / SR
            lines.append({"name": name, "who": who, "text": ev["text"], "vo": ev.get("vo", False),
                          "start": round(cursor, 3), "end": round(cursor + dur, 3)})
            beats[name] = [cursor, cursor + dur]
            clips.append(("voice", cursor, audio))
            cursor += dur + ev.get("pad", 0.2)
    length = old["length"] if old else cursor
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
            for i in range(int(arg / 0.25)):
                place(mix, sfx_step(), at + 0.1 + i * 0.25, 0.5)
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
        elif kind == "plunge":
            place(mix, sfx_plunge(arg), at, 0.6)
        elif kind == "ledge":
            place(mix, sfx_thump(160, 0.3, 1.0), at, 0.7)
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
        place(score, music.render(m["cue"], m1 - m0, seed=k), m0, m.get("gain", 0.2))
    duck = np.convolve(np.abs(voice) > 0.02, np.ones(SR // 10) / (SR // 10), "same")
    duck = np.clip(duck * 3, 0, 1)
    out = voice + mix * (1 - 0.45 * duck) + score * (1 - 0.75 * duck)
    out = norm(out, 0.89)
    sf.write(os.path.join(out_dir, "audio.wav"), np.stack([out, out], 1).astype(np.float32), SR)

    overlays = []
    for o in ep.get("overlays", []):
        o = dict(o)
        o["start"] = round(R(o.pop("from")), 3)
        o["end"] = round(R(o.pop("to")), 3)
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
