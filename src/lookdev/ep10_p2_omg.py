"""Episode 10, part 2: "Oh... My... God..." (about 5.5 s, three shots).

The same place and moment as part 1's end: the torn portal, the rift, and
Null towering over the forest in his storm. Steve and the Noob stand in front
of it, lit magenta from above.

  A  An anime side view of Steve's face, close. He raises his head to the sky
     as he says "Oh... My... God...": the mouth is keyed by hand, word by word,
     on the words found in his voice. The camera trembles; now and then the
     focus slips (the reference's blur).
  B  Low at his feet, the camera pushing in as one foot slides back and his
     knees bend: ready to run.
  C  The Noob's face from the side, afraid: trembling eyes, "...Steve?"

    python src/lookdev/ep10_p2_omg.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080]
        [--samples 32] [--times 0.4,2.6] [--list]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_entrance as EN                                   # noqa: E402
EN.EXTRA_CLEAR.append((0.0, -3.9, 3.4))                     # where they stand
from ep10_entrance import FPS, PORTAL_AT, lerp, ss, shake   # noqa: E402

STEVE_AT = PORTAL_AT + Vector((-0.95, -9.0, 0.0))
NOOB_AT = PORTAL_AT + Vector((1.05, -8.8, 0.0))
LENGTH = 5.6
# moments; with a voice they come from the timeline
T = {"breath": 0.0, "line": 0.45, "line_end": 3.4, "legs": 3.6, "noob": 4.95, "noob_line": 5.15, "noob_end": 5.9,
     "end": 6.4}
WORDS = [(0.5, 0.95), (1.4, 1.85), (2.4, 3.15)]               # Oh / My / God (start, end), from the voice


# ----------------------------------------------------------------- the mouth
def _shape(name):
    from mouths import VISEME, MOUTHS
    return dict(VISEME.get(name) or MOUTHS[name])


# per word: (fraction of the word, mouth shape). The shapes are the 2D lip-sync set:
# A closed (M B P), B teeth (K S T EE), C open (EH), D wide (AA), E round (AO), F pucker (OO W)
WORD_SHAPES = [
    [(0.0, "E"), (0.55, "E"), (0.85, "F")],                          # "Oh..."  round, closing to a small O
    [(0.0, "A"), (0.14, "A"), (0.26, "D"), (0.62, "D"), (0.86, "B")],  # "My..."  lips, wide "ah", into "ee"
    [(0.0, "B"), (0.14, "C"), (0.3, "E"), (0.72, "E"), (0.9, "C")],    # "God..." "g", round "o", "d"
]
SHOCK_MOUTH = {"m_o": 0.36, "m_w": 1.45, "m_up": 0.9, "m_r": 1.0, "m_vee": 0.3, "m_arch": 0.0, "m_tu": 0.5}


def mix(a, b, k):
    from faceplate import MOUTH_DEFAULTS
    out = {}
    for key in set(a) | set(b):
        va = a.get(key, MOUTH_DEFAULTS.get(key, 0.0))
        vb = b.get(key, MOUTH_DEFAULTS.get(key, 0.0))
        out[key] = lerp(va, vb, k)
    return out


def steve_mouth(t, env):
    """The keyed mouth: each word's shapes at their places in the word, eased
    over two frames, opened by the voice's own loudness; between the words his
    jaw hangs open in shock (the lower lip trembling)."""
    rest = dict(SHOCK_MOUTH)
    if t < WORDS[0][0] - 0.25:                                   # the gasp before: the mouth falls open
        g = ss(T["line"] - 0.4, WORDS[0][0] - 0.1, t)
        return mix({}, rest, g)
    for w, (a, b) in enumerate(WORDS):
        if a - 0.06 <= t <= b + 0.08:
            u = (t - a) / max(0.05, b - a)
            keys = WORD_SHAPES[w]
            cur = keys[0]
            nxt = keys[-1]
            for i in range(len(keys) - 1):
                if keys[i][0] <= u < keys[i + 1][0]:
                    cur, nxt = keys[i], keys[i + 1]
                    break
            else:
                cur = nxt = keys[-1] if u >= keys[-1][0] else keys[0]
            span = max(1e-3, nxt[0] - cur[0])
            k = ss(0, 1, (u - cur[0]) / span) if nxt is not cur else 0.0
            m = mix(_shape(cur[1]), _shape(nxt[1]), k)
            loud = min(1.0, env(t) / 0.8)
            if "m_o" in m:                                       # big enough to read at this framing
                m["m_o"] = m["m_o"] * (0.8 + 0.6 * loud)
            m["m_w"] = m.get("m_w", 1.9) * 1.12
            # ease in and out of the word from the hanging-open rest
            e_in, e_out = ss(a - 0.06, a + 0.04, t), 1 - ss(b - 0.02, b + 0.08, t)
            return mix(rest, m, min(e_in, e_out))
    # between words and after: open, trembling
    rest["m_tl"] = 0.3
    return rest


def find_words(voice, start, end):
    """The three words: loud stretches of the line, split at its two longest pauses."""
    try:
        import soundfile as sf
        x, sr = sf.read(voice)
    except Exception:
        return None, None
    x = x.mean(1) if x.ndim > 1 else x
    seg = x[int(start * sr):int(end * sr)]
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(seg[i:i + hop] ** 2)) for i in range(0, len(seg) - hop, hop)])
    if not len(rms):
        return None, None
    thr = 0.12 * rms.max()
    on = rms > thr
    runs, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    runs = [r for r in runs if r[1] - r[0] > 6]                 # a breath or a click is not a word
    while len(runs) > 3:                                        # join across the shortest gaps
        g = [runs[k + 1][0] - runs[k][1] for k in range(len(runs) - 1)]
        k = int(np.argmin(g))
        runs[k] = [runs[k][0], runs[k + 1][1]]
        del runs[k + 1]
    words = [(start + a * 0.01, start + b * 0.01) for a, b in runs if b - a > 4]

    def env(t):
        k = int((t - start) / 0.01)
        return float(rms[k] / rms.max()) if 0 <= k < len(rms) else 0.0
    return (words if len(words) == 3 else None), env


# ----------------------------------------------------------------- the build
def build(tl, assets, res, samples):
    E = EN.build(tl, assets, res, samples)
    sc = E.sc
    from stage import build_steve, build_noob_char, char_light
    from props import sprite_item, hold
    E.S = build_steve(sc)
    pk = sprite_item("iron_pickaxe", os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets",
                                                  "minecraft", "textures", "item"), px=0.072)
    hold(E.S.arm, pk, "sr", up=25, face=60, collection=[E.S.rig])
    E.N = build_noob_char(sc)
    # light: Null's magenta from above in front of them, a cold rim behind, the storm's fill
    def area(name, power, color, size):
        L = bpy.data.lights.new(name, "AREA")
        L.energy, L.color, L.size = power, color, size
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        return o
    E.null_key = area("null_key", 5200, (1.0, 0.36, 0.9), 6.0)
    E.null_key.location = PORTAL_AT + Vector((0.0, -3.0, 12.0))
    E.cold_rim = area("cold_rim", 1600, (0.55, 0.62, 1.0), 3.0)
    E.cold_rim.location = STEVE_AT + Vector((0.4, -4.5, 3.4))
    for o in (E.null_key, E.cold_rim):
        o.rotation_euler = ((STEVE_AT + Vector((1.0, 0.2, 1.4))) - o.location).to_track_quat("-Z", "Y").to_euler()
    E.face_fill = char_light(sc, "face_fill", (0, 0, 0), 260, (0.95, 0.7, 1.0), cone=30, size=0.6)
    E.lines = tl.get("lines", [])
    return E


# ---------------------------------------------------------- the choreography
def steve_pose(t):
    """Frozen by what he sees: nothing shakes. His head rises slowly, all through
    the line; his hands lift a little, held still. Then the step back, slow and
    careful, a gazelle ready to bolt: the heel lifts, the foot slides back and is
    set down without a sound, the knees sink into a crouch."""
    lift = ss(T["line"] - 0.25, WORDS[2][1] + 0.35, t)          # one slow rise, no jerks
    nod = lerp(4, -24, lift)
    L0 = T["legs"]
    heel = ss(L0 + 0.05, L0 + 0.45, t) * (1 - ss(L0 + 0.85, L0 + 1.15, t))     # the foot leaves the ground, barely
    back = ss(L0 + 0.15, L0 + 1.05, t)                                         # and travels back, slowly
    crouch = ss(L0 + 0.1, L0 + 1.3, t)
    P = {"chest_lean": lerp(-2, -6, lift) + 6 * crouch, "head_nod": nod - 3 * crouch, "head_tilt": 1.5 * lift,
         "head_turn": -2 * lift,
         "arm_sl": {"out": lerp(8, 15, lift) + 4 * crouch, "fwd": lerp(6, 12, lift), "elbow": lerp(10, 24, lift) + 10 * crouch},
         "arm_sr": {"out": lerp(8, 13, lift) + 4 * crouch, "fwd": lerp(4, 9, lift), "elbow": lerp(12, 28, lift) + 10 * crouch},
         "hips_drop": 0.22 * crouch,
         "foot_sr": {"y": 0.7 * back, "z": 0.1 * heel, "yaw": 10 * back},
         "foot_sl": {"y": 0.1 * crouch, "yaw": -5 * crouch}}
    return P


def steve_face(t):
    """Wide, still eyes that roll up slowly; brows rising; nothing twitches."""
    lift = ss(T["line"] - 0.35, WORDS[2][1] + 0.2, t)
    f = {"both_to": lerp(0.05, 0.38, ss(T["line"] - 0.4, WORDS[0][0] + 0.2, t)), "both_tm": lerp(0.05, 0.42, lift),
         "both_ti": lerp(0.0, 0.32, lift), "both_ps": lerp(0.95, 0.58, lift),
         "both_py": lerp(0.0, 0.6, lift), "both_px": 0.0,
         "bb_raise": lerp(0.1, 0.65, ss(T["line"] - 0.35, WORDS[1][1], t)),
         "bb_tilt": lerp(0.0, -0.75, lift), "bb_arch": 0.3 * lift}
    return f


def noob_face(t):
    """Frozen; on "Steve?" his eyes slide slowly to his friend."""
    from ep09_new import NF
    f = dict(NF["scared"])
    look = ss(T["noob_line"] - 0.3, T["noob_line"] + 0.45, t)
    f.update({"both_py": lerp(0.45, 0.22, look), "both_px": lerp(0.0, -0.5, look), "both_ps": 0.66})
    return f


# --------------------------------------------------------------- the camera
def crash(t, at, dur=0.14):
    """A crash zoom: 0 -> 1, fast in, settling."""
    return ss(at - 0.02, at + dur, t)


def camera(t, hs, hn):
    """All the fear is in the camera. -> loc, look, lens, fstop, focus distance (None = on the look
    point), handheld amount (degrees), rumble amount (degrees)"""
    O, M, G = (w[0] for w in WORDS)
    if t < T["legs"]:                                            # A: Steve's face, a side view from below
        u = ss(0, T["legs"], t)
        loc = hs + Vector((-1.15 + 0.12 * u, 1.05 - 0.08 * u, -0.42))
        look = hs + Vector((0.0, 0.0, 0.08))
        lens = 44 + 13 * crash(t, O) + 5 * ss(O + 0.2, M + 0.4, t) + 16 * crash(t, G)   # crash in on Oh, creep, crash on God
        d = (look - loc).length
        focus = d
        focus = lerp(7.0, d, ss(0.15, O - 0.1, t))               # it opens out of focus and finds his face
        focus *= 1 + 0.45 * math.exp(-((t - (O + M) / 2) / 0.16) ** 2)       # breathes out between the words
        focus *= 1 + 0.3 * math.exp(-((t - (M + G) / 2 - 0.05) / 0.14) ** 2)
        rumble = 0.08 + sum(0.55 * math.exp(-((t - w) / 0.1) ** 2) for w in (O, M, G))
        return loc, look, lens, 1.4, focus, 0.7, rumble
    if t < T["noob"]:                                            # B: low at his feet; slow push, then a crash in as the foot lands
        L0 = T["legs"]
        u = ss(L0, T["noob"], t)
        feet = STEVE_AT + Vector((-0.05, 0.05 - 0.32 * ss(L0 + 0.15, L0 + 1.05, t), 0.17))
        loc = feet + Vector((-1.1 + 0.25 * u, 1.25 - 0.3 * u, 0.02))
        lens = 36 + 8 * u + 20 * crash(t, L0 + 1.0, 0.16)
        d = (feet - loc).length
        focus = lerp(d * 0.55, d, ss(L0, L0 + 0.35, t))          # racks from the grass to his foot
        rumble = 0.2 + 0.6 * math.exp(-((t - L0) / 0.12) ** 2) + 0.5 * math.exp(-((t - L0 - 1.0) / 0.1) ** 2)
        return loc, feet, lens, 2.2, focus, 0.9, rumble
    u = ss(T["noob"], T["end"] + 0.4, t)                         # C: the Noob's face
    loc = hn + Vector((1.15 - 0.2 * u, 1.1 - 0.2 * u, -0.28))
    look = hn + Vector((0.0, 0.0, 0.05))
    lens = 48 + 7 * u + 14 * crash(t, T["noob_line"] + 0.05, 0.18)
    d = (look - loc).length
    focus = d * (1 + 0.4 * (1 - ss(T["noob"], T["noob"] + 0.3, t)))          # finds him as we cut in
    rumble = 0.1 + 0.4 * math.exp(-((t - T["noob_line"]) / 0.12) ** 2)
    return loc, look, lens, 1.4, focus, 0.65, rumble


def handheld(t, amp):
    """A frightened operator: slow drift (yaw, pitch, roll in degrees)."""
    y = amp * (0.6 * math.sin(1.3 * t + 0.4) + 0.4 * math.sin(2.9 * t + 1.7) + 0.2 * math.sin(5.3 * t + 0.9))
    p = amp * (0.5 * math.sin(1.1 * t + 2.1) + 0.35 * math.sin(3.4 * t + 0.2) + 0.15 * math.sin(6.7 * t + 1.0))
    r = amp * 0.7 * (0.6 * math.sin(0.9 * t + 1.0) + 0.4 * math.sin(2.3 * t + 2.0))
    return y, p, r


def rumble(t, amp):
    """The ground shaking under the camera (fast)."""
    y = amp * (0.5 * math.sin(23.1 * t) + 0.3 * math.sin(37.7 * t + 1.1) + 0.2 * math.sin(53.3 * t + 2.3))
    p = amp * (0.5 * math.sin(19.7 * t + 0.6) + 0.3 * math.sin(41.9 * t + 1.9) + 0.2 * math.sin(61.1 * t + 0.4))
    return y, p, 0.4 * y


def apply(E, t):
    from pose import pose
    from noob import pose_noob, NOOB_POSES
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from ep09_new import flat, unflat, talk
    # the place and Null: as part 1 left them (he idles; his rings turn)
    EN.apply(E, EN.T["s4"] + 2.0 + t)
    S, N = E.S, E.N
    # ------------------------------------------------ Steve
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    sp = flat(lib["idle (Benly 2.2)"])
    for k, v in flat(steve_pose(t)).items():
        sp[k] = v
    pose(S.arm, unflat(sp))
    S.holder.location = STEVE_AT
    S.holder.rotation_euler = (0, 0, math.radians(180))
    fs = {f"{e}_{k}": v for e in EYES for k, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    sf = steve_face(t)
    for k, v in sf.items():
        if k.startswith("both_"):
            for e in EYES:
                fs[f"{e}_{k[5:]}"] = v
        elif not k.startswith("bb_"):
            fs[k] = v
    fs.update(steve_mouth(t, E.env))
    set_face(S.face, fs)
    for ob_ in S.brows.values():
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(S.brows, {k: v for k, v in sf.items() if k.startswith("bb_")})
    # ------------------------------------------------ the Noob
    npz = flat(NOOB_POSES["scared"])
    turn = ss(T["noob_line"] - 0.2, T["noob_line"] + 0.7, t)            # a slow, small turn toward Steve
    npz.update({"head_nod": -26 + 4 * turn, "head_turn": -9 * turn, "head_tilt": 4, "chest_lean": -4, "root_yaw": 180,
                "arm_sl.fwd": 55, "arm_sr.fwd": 55})
    pose_noob(N, unflat(npz))
    N.root.location = NOOB_AT
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    for k, v in noob_face(t).items():
        if k.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{k[5:]}"] = v
        else:
            fn[k] = v
    mo = E.noob_mouth.get(int(round(t * FPS)))
    if mo:
        mo = dict(mo, m_o=min(1.1, mo["m_o"] * 1.5))
    talk(fn, mo)
    set_face(N.face, fn)
    # ------------------------------------------------ camera
    bpy.context.view_layer.update()
    def centre(ob, m=None):
        c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
        return (m @ ob.matrix_world @ c) if m is not None else ob.matrix_world @ c
    hs = centre(S.face, S.holder.matrix_world)            # the middle of his face plate
    hn = centre(N.head_mesh)
    loc, look, lens, fstop, focus, hand, rum = camera(t, hs, hn)
    y1, p1, r1 = handheld(t, hand)
    y2, p2, r2 = rumble(t, rum)
    q = (look - loc).to_track_quat("-Z", "Y")
    q = q @ Quaternion((0, 1, 0), math.radians(y1 + y2)) @ Quaternion((1, 0, 0), math.radians(p1 + p2)) \
        @ Quaternion((0, 0, 1), math.radians(r1 + r2))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = focus
    E.cam.data.dof.aperture_fstop = fstop
    who = look
    E.face_fill.location = loc + (who - loc).normalized().cross(Vector((0, 0, 1))) * 0.8 + Vector((0, 0, 0.9))
    E.face_fill.rotation_euler = (who - E.face_fill.location).to_track_quat("-Z", "Y").to_euler()
    E.key.data.energy = 0.0
    return {"g": 0.0, "s": 1.0}


# ------------------------------------------------------------------ main
def align(tl, voice):
    global LENGTH
    b = tl.get("beats", {})
    lines = {ln["name"]: ln for ln in tl.get("lines", [])}
    if "steve_omg" in lines:
        s = lines["steve_omg"]
        T.update(line=s["start"], line_end=s["end"], legs=b["legs"][0], noob=b["noob"][0])
        n = lines.get("noob_steve")
        if n:
            T.update(noob_line=n["start"], noob_end=n["end"])
        T["end"] = tl["length"]
        w, env = find_words(voice, s["start"], s["end"])
        if w:
            WORDS[:] = w
        LENGTH = tl["length"] + 0.4
        return env
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("voice")
    ap.add_argument("tex_dir")
    ap.add_argument("assets")
    ap.add_argument("out_dir")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--res", type=int, default=1080)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--times")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    tl = {"length": LENGTH, "fps": FPS, "beats": {}, "lines": []} if a.timeline == "-" else json.load(open(a.timeline))
    env = align(tl, a.voice)
    n_frames = int(round(LENGTH * FPS)) + (1 if a.timeline != "-" else 0)
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    E = build(tl, a.assets, a.res, a.samples)
    E.env = env or (lambda t: 0.7)
    E.noob_mouth = {}
    if a.timeline != "-" and os.path.exists(a.voice):
        from ep09_new import _lipsync
        m = _lipsync({"length": tl["length"], "lines": [ln for ln in tl["lines"] if ln["who"] == "noob"]}, a.voice)
        E.noob_mouth = m.get("noob", {})
    sc = E.sc
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    mist_dir = os.path.join(out, "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"

    def handler(scene, depsgraph=None):
        apply(E, (scene.frame_current + scene.frame_subframe - 1) / FPS)

    bpy.app.handlers.frame_change_pre.append(handler)
    if a.times:
        frames = [int(round(float(x) * FPS)) + 1 for x in a.times.split(",")]
    else:
        frames = list(range(1, n_frames + 1))
        k, n = (int(x) for x in a.shard.split("/"))
        per = (len(frames) + n - 1) // n
        frames = frames[k * per:(k + 1) * per]
    print("rendering", len(frames), "frames")
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not a.times:
            continue
        sc.frame_set(f)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        EN.finish(dst, cand[-1] if cand else "")
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
