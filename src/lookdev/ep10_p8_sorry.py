"""Episode 10 (the finale), part 8: sorry.

Part 7's dive, run backwards: from the dome of heads (their smiles shutting) the
camera is drawn back out, faster and faster, down the tunnel of cells into the
dark of Null's body, out of his chest, back over the Noob's arch, and into the
mirror of the Noob's eye; out of the eye, slowing, to his face. A tear wells
in it and runs down. "I never came back for you guys... sorry."

The set, the cameras and the mirror trick are part 7's own (ep10_p7_reveal):
this file only drives part 7's clock backwards through them, then holds on him.

    python src/lookdev/ep10_p8_sorry.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_p7_reveal as P7                                          # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402

T = {"pull": 0.0, "tear": 3.0, "noob_sorry": 3.9, "noob_sorry_end": 6.4, "end": 6.4, "length": 7.6}
# part 7's approved timeline (voices run 43125649566), so its clock means what it meant there
P7_TL = {"beats": {"a": [0.0, 0.25], "patch_look": [0.25, 3.23], "see": [3.33, 4.73], "steve_you": [4.73, 8.75],
                   "dive": [8.75, 12.8], "end": [12.8, 13.0]}, "lines": [], "length": 13.0}


# ------------------------------------------------------------------ the clock, backwards
def phases():
    P = T["tear"]
    return {"A": (0.0, 0.38 * P), "B": (0.36 * P, 0.75 * P), "C": (0.74 * P, P), "CU": (P, 1e9)}


def t7_of(shot, t):
    """Part 7's time for this shot at part 8's time t."""
    a, b = phases()[shot]
    u = max(0.0, min(1.0, (t - a) / max(1e-6, b - a)))
    if shot == "A":                                         # out of the dome: slow, then faster and faster
        return lerp(P7.T["end"] - 0.3, P7.t_f() - 0.14, u ** 1.8)
    if shot == "B":                                         # out of his chest, back to the mirror (fast, slowing)
        return lerp(P7.t_f(), P7.t_m(), u)
    if shot == "C":                                         # out of the eye, slowing to his face
        return P7.t_m() - 2.6 * (1 - (1 - u) ** 2)
    return P7.t_m() - 2.6


SHOT7 = {"A": "S1", "B": "F", "C": "R5", "CU": "R5"}


def layers(t):
    ph = phases()
    if ph["B"][0] <= t < ph["A"][1]:
        u = ss(ph["B"][0], ph["A"][1], t)
        return [("A", 1 - u), ("B", u)]
    if ph["C"][0] <= t < ph["B"][1]:
        u = ss(ph["C"][0], ph["B"][1], t)
        return [("B", 1 - u), ("C", u)]
    for k in ("A", "B", "C"):
        if t < ph[k][1]:
            return [(k, 1.0)]
    return [("CU", 1.0)]


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    P7.align(P7_TL)
    E = P7.build(P7_TL, tex_dir, assets, res, samples)
    # the tear: a drop of water on his face
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12, location=(0, 0, -900))
    tr = bpy.context.active_object
    tr.name = "tear"
    m = bpy.data.materials.new("tear")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.85, 0.93, 1.0, 1)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.33
    tr.data.materials.append(m)
    for p in tr.data.polygons:
        p.use_smooth = True
    E.tear = tr
    return E


# ------------------------------------------------------------------ per frame
def apply(E, t, shot=None):
    shot = shot or E.force_shot or layers(t)[0][0]
    t7 = t7_of(shot, t)
    E.force_shot_7 = SHOT7[shot]
    prev = E.force_shot
    E.force_shot = SHOT7[shot]
    look = P7.apply(E, t7, SHOT7[shot])
    E.force_shot = prev
    if shot in ("C", "CU"):
        noob_after(E, t, t7, shot)
    else:
        E.tear.hide_render = True
    return look


def noob_after(E, t, t7, shot):
    """His face, out of the eye: the dread going to shame; a tear; the line."""
    from faceplate import set_face, NOOB_EYES, NOOB_EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_MOUTH
    from ep09_new import NF, talk
    import ep10_p6_fall as P6
    N = E.N
    f_render = int(round(t * FPS))
    sad = ss(T["tear"] - 0.6, T["tear"] + 0.6, t)
    base = {"both_h": 1.9, "both_ps": 0.35, "both_open": 1.0, "m_arch": 0.25, "m_w": 1.4, "m_o": 0.1}
    teary = dict(NF.get("teary", NF["scared"]))
    face = P6._mixf(base, teary, sad)
    face.update({"m_arch": 0.38 + 0.03 * math.sin(t * 23.0) * sad, "m_w": 1.35})   # the mouth turned down, trembling
    down = ss(T["noob_sorry"] + 0.4, T["noob_sorry"] + 1.4, t)          # he can't look at them
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    for k, v in face.items():
        if k.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{k[5:]}"] = v
        else:
            fn[k] = v
    for e in NOOB_EYES:
        fn[f"{e}_py"] = lerp(0.25, -0.35, down)
        fn[f"{e}_px"] = lerp(0.15, 0.0, down)
        fn[f"{e}_ps"] = lerp(0.06, 0.4, ss(T["tear"] - 0.8, T["tear"], t))   # the shine back: wet
    talk(fn, E.mouth.get("noob", {}).get(f_render))
    set_face(N.face, fn)
    # the tear: wells at the lower lid of his near eye, swells, runs down his cheek
    eye = P7.noob_eye(E)
    nrm = P7.noob_eye_normal(E)
    dn = (N.neck.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    dn = (dn - nrm * dn.dot(nrm)).normalized()
    t0 = T["tear"] + 0.05
    grow = ss(t0, t0 + 0.55, t)
    run = ss(t0 + 0.55, t0 + 2.4, t) ** 1.3
    if grow <= 0:
        E.tear.hide_render = True
        return
    r = 0.017 * grow * (1 - 0.2 * run) * (1 - ss(0.8, 1.0, run))
    E.tear.hide_render = False
    E.tear.scale = (r, r * 0.6, r * (1 + 0.5 * run))
    E.tear.rotation_mode = "QUATERNION"
    E.tear.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(dn)
    E.tear.location = eye + dn * (0.055 + 0.115 * run) + nrm * (0.004 + 0.5 * r)
    if r < 1e-4:
        E.tear.hide_render = True


def camera_cu(E, t):
    """Held on his face out of the eye, drifting in a touch as he speaks."""
    pass


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    for k in ("pull", "tear", "end"):
        if k in b:
            T[k] = b[k][0]
    if "noob_sorry" in b:
        T["noob_sorry"], T["noob_sorry_end"] = b["noob_sorry"]
    for ln in tl.get("lines", []):
        if ln.get("name") == "noob_sorry":
            T["noob_sorry"], T["noob_sorry_end"] = ln["start"], ln["end"]
    if b:
        T["length"] = tl["length"] + 0.4


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
    tl = {"length": T["length"] - 0.4, "beats": {}, "lines": []} if a.timeline == "-" else json.load(open(a.timeline))
    align(tl)
    n_frames = int(round(T["length"] * FPS)) + 1
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    E = build(tl, a.tex_dir, a.assets, a.res, a.samples)
    E.force_shot = None
    E.mouth = {}
    if a.timeline != "-" and os.path.exists(a.voice):
        from ep09_new import _lipsync
        E.mouth = _lipsync(tl, a.voice)
    sc = E.sc
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    mist_dir = os.path.join(out, "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"
    state = {"shot": None}

    def handler(scene, depsgraph=None):
        apply(E, (scene.frame_current + scene.frame_subframe - 1) / FPS, state["shot"])

    bpy.app.handlers.frame_change_pre.append(handler)
    if a.times:
        frames = [int(round(float(x) * FPS)) + 1 for x in a.times.split(",")]
    else:
        frames = list(range(1, n_frames + 1))
        k, n = (int(x) for x in a.shard.split("/"))
        per = (len(frames) + n - 1) // n
        frames = frames[k * per:(k + 1) * per]
    print("rendering", len(frames), "frames")
    import numpy as np
    from PIL import Image
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not a.times:
            continue
        t = (f - 1) / FPS
        ls = [(s_, w_) for s_, w_ in layers(t) if w_ >= 0.003]
        parts = []
        for shot, wgt in ls:
            state["shot"] = shot
            sc.frame_set(f)
            apply(E, t, shot)
            p = dst if len(ls) == 1 else dst[:-4] + f"_{shot}.png"
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
            P7.finish(p, cand[-1] if cand else "", SHOT7[shot], t7_of(shot, t))
            for x in cand:
                os.remove(x)
            parts.append((p, wgt))
        state["shot"] = None
        if len(parts) > 1:
            acc = None
            for p, wgt in parts:
                a_ = np.asarray(Image.open(p).convert("RGB"), np.float32)
                acc = a_ * wgt if acc is None else acc + a_ * wgt
                os.remove(p)
            Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).save(dst)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
