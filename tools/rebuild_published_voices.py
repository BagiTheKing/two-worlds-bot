"""Rebuild a published episode's finished voice lines from its rescued prep (movie/epNN_published), as a
`voices_from` folder (voice.flac + timeline.json) for the movie.

    git worktree add <code_dir> <the published run's commit>
    python tools/rebuild_published_voices.py episodes/ep05_creative_mode.json movie/ep05_published <code_dir>

The published run's own sound code (`<code_dir>/src`) is run on the published episode file (placing every line
at its exact, unrounded time, as the published run did): the speech service is replaced by the rescued scene recordings (`scenes/<first line>.flac`, every
scene line cut at its pinned `cut_at`, so those lines come out exactly as published). The solo lines are not in
the scenes: the bed (effects, ambience, music, ducked as it was) is rebuilt by the same code and subtracted from
the published mix (`published_audio.flac`), after fitting the mix's normalising gain on voice-free stretches.
Each scene line is checked against the mix (the residual where only it and the bed sound).
"""
import json
import os
import sys
import types

import numpy as np
import soundfile as sf


def load_audio_module(code_dir, dump):
    src_dir = os.path.join(code_dir, "src")
    sys.path.insert(0, src_dir)
    path = os.path.join(src_dir, "audio.py")
    text = open(path).read()
    hook = "    duck = np.convolve(np.abs(voice) > 0.02"
    assert text.count(hook) == 1, "the mix line moved: adapt the hook"
    text = text.replace(hook, f"    np.savez({dump!r}, voice=voice, mix=mix, score=score)\n" + hook)
    mod = types.ModuleType("audio")
    mod.__file__ = path
    sys.modules["audio"] = mod
    exec(compile(text, path, "exec"), mod.__dict__)
    return mod


def main(episode, pub, code_dir):
    ep = json.load(open(episode))
    tl_pub = json.load(open(os.path.join(pub, "timeline.json")))
    work = os.path.join(pub, "_work")
    os.makedirs(work, exist_ok=True)
    dump = os.path.join(work, "parts.npz")
    os.environ["VOICE_ENGINE"] = "gemini"
    os.environ["VOICE_STEM"] = "1"
    os.environ["VOICE_CACHE"] = os.path.join(work, "cache")
    A = load_audio_module(code_dir, dump)

    lines = [ev for ev in ep["events"] if "line" in ev]
    by_text = {ev.get("direction_text") or ev["text"]: ev["name"] for ev in lines}
    # solo takes are not in the scenes: solo_only lines, lines with their own solo_text (the scene take is
    # replaced by a solo recording) and own_scene lines (a recording of their own): all lifted from the mix
    solos = [ev["name"] for ev in lines if ev.get("solo_only") or ev.get("solo_text") or ev.get("own_scene")]
    own = {ev["direction_text"] if ev.get("direction_text") else ev["text"]: ev["name"] for ev in lines if ev.get("own_scene")}
    pub_lines = {ln["name"]: ln for ln in tl_pub["lines"]}

    def speak(turns, voices, notes=""):
        if len(turns) == 1 and turns[0][1] in own:     # an own_scene line: a placeholder of its published length
            n = own[turns[0][1]]
            return np.random.default_rng(1).standard_normal(solo_len[n]) * 0.1, 48000
        first = by_text[turns[0][1]]
        x, sr = sf.read(os.path.join(pub, "scenes", first + ".flac"))
        print(f"  scene {first}: from the rescued recording ({len(x) / sr:.2f}s)")
        return x, sr

    def split(samples, sr, ls):         # every scene line is pinned; any span will do
        return {n: (0.0, 0.1, 0.0, 0.1) for n, _ in ls}

    solo_len = {n: int(round((pub_lines[n]["end"] - pub_lines[n]["start"]) * 48000)) for n in solos}

    def solo(cast, who, text, nonverbal, cache_dir, **kw):
        n = next(ev["name"] for ev in lines if ev["name"] in solos
                 and (ev.get("solo_text") or A._spoken(ev.get("direction_text") or ev["text"])) == text)
        r = np.random.default_rng(0)       # at the mix rate, so its length in samples is exact
        return r.standard_normal(solo_len[n]) * 0.1, 48000

    A.gemini_speak, A.split_scene, A.gemini_solo = speak, split, solo
    A.transcribe = lambda s, sr: []         # own_scene takes: Whisper is not reachable here; any take will do
    P, psr = sf.read(os.path.join(pub, "published_audio.flac"))
    P = P.mean(axis=1) if P.ndim > 1 else P
    from scipy.signal import correlate
    order = [ln["name"] for ln in tl_pub["lines"]]
    # the published run placed lines at exact (unrounded) times: rebuild without a kept timeline, the solo
    # placeholders' lengths (in samples) corrected until every scene line sits at lag 0 in the published mix
    for attempt in range(4):
        A.rng = np.random.default_rng(7)      # the module's effects generator, fresh as in a new process
        A.build(episode, work)
        Vt = np.load(dump)["voice"]
        tl = json.load(open(os.path.join(work, "timeline.json")))
        lag = {}
        Pp = np.pad(P, (400, 400 + len(Vt)))
        for ln in tl["lines"]:
            if ln["name"] in solos:
                continue
            a, b = int(ln["start"] * A.SR), int(ln["end"] * A.SR)
            c = correlate(Pp[a:b + 800], Vt[a:b], "valid", method="fft")
            lag[ln["name"]] = int(np.argmax(c)) - 400
        print("lags (samples):", lag)
        if not any(lag.values()):
            break
        for s_ in solos:                    # the line after a solo tells how long the solo really was
            nxt = order[order.index(s_) + 1] if order.index(s_) + 1 < len(order) else None
            before = [lag[x] for x in order[:order.index(s_)] if x in lag]
            if nxt in lag:
                solo_len[s_] += lag[nxt] - (before[-1] if before else 0)
        print("solo lengths:", solo_len)

    tl = json.load(open(os.path.join(work, "timeline.json")))
    SR = A.SR
    parts = np.load(dump)
    V, M, S = parts["voice"], parts["mix"], parts["score"]
    assert psr == SR
    n = min(len(P), len(V))
    P, V, M, S = P[:n], V[:n], M[:n], S[:n]
    span = {ln["name"]: (int(ln["start"] * SR), int(ln["end"] * SR)) for ln in tl["lines"]}
    # a solo take can ring on past its timeline span (or start a little before it): lift it over the gap to the
    # neighbouring lines too (at most 0.25 s each side); where nothing sounds, the lift is ~0 there anyway
    ordered = sorted(span.items(), key=lambda kv: kv[1][0])
    for i, (nm, (a, b)) in enumerate(ordered):
        if nm in solos:
            lo = ordered[i - 1][1][1] if i else 0
            hi = ordered[i + 1][1][0] if i + 1 < len(ordered) else n
            span[nm] = (max(lo, a - SR // 4), min(hi, b + SR // 4))
    for ln in tl["lines"]:
        p = pub_lines[ln["name"]]
        if abs(p["start"] - ln["start"]) > 0.002 or abs(p["end"] - ln["end"]) > 0.02:
            print(f"  WARNING {ln['name']}: placed {ln['start']:.3f}-{ln['end']:.3f}, published {p['start']:.3f}-{p['end']:.3f}")
    Vs = V.copy()
    for s in solos:                     # the placeholders out
        a, b = span[s]
        Vs[a:b] = 0.0

    def bed(voice):
        d = np.convolve(np.abs(voice) > 0.02, np.ones(SR // 10) / (SR // 10), "same")
        d = np.clip(d * 3, 0, 1)
        return M * (1 - 0.45 * d) + S * (1 - 0.75 * d)

    # the gain: published = k * (voice + bed); fitted where nobody speaks
    free = np.ones(n, bool)
    for a, b in span.values():
        free[max(0, a - SR // 5):b + SR // 5] = False
    B0 = bed(Vs)
    k = float(np.dot(P[free], B0[free]) / np.dot(B0[free], B0[free]))
    res = P[free] / k - B0[free]
    print(f"gain k={k:.5f}; voice-free residual {20 * np.log10(np.std(res) / np.std(B0[free]) + 1e-12):.1f} dB under the bed")

    # the solos: the published mix minus the rebuilt bed (the duck follows the solo itself, so iterate)
    Vfull = Vs.copy()
    for it in range(60):
        Bn = bed(Vfull)
        est = P / k - Bn
        moved = 0.0
        for s in solos:
            a, b = span[s]
            moved = max(moved, float(np.max(np.abs(Vfull[a:b] - est[a:b]))))
            Vfull[a:b] = est[a:b]
        if moved < 1e-9:
            break
    print(f"solos settled after {it + 1} passes (last change {moved:.2e})")
    Bn = bed(Vfull)
    for s in solos:
        a, b = span[s]
        f = int(0.004 * SR)
        Vfull[a:a + f] *= np.linspace(0, 1, f)
        Vfull[b - f:b] *= np.linspace(1, 0, f)
        r = P[a:b] / k - Bn[a:b] - Vfull[a:b]
        print(f"  {s}: lifted; bed {20 * np.log10(np.std(Bn[a:b]) / np.std(Vfull[a:b])):.1f} dB under the voice")
    for ln in tl["lines"]:              # every line: how well the published mix is explained
        a, b = span[ln["name"]]
        r = P[a:b] / k - Bn[a:b] - Vfull[a:b]
        c = np.corrcoef(P[a:b] / k - Bn[a:b], Vfull[a:b])[0, 1]
        print(f"  {ln['name']:14s} residual {20 * np.log10(np.std(r) / np.std(Vfull[a:b]) + 1e-12):6.1f} dB, corr {c:.3f}")
    sf.write(os.path.join(pub, "voice.flac"), Vfull.astype(np.float32), SR)
    json.dump(tl, open(os.path.join(pub, "timeline.json.rebuilt"), "w"), indent=1)
    print("wrote", os.path.join(pub, "voice.flac"))


if __name__ == "__main__":
    main(*sys.argv[1:4])
