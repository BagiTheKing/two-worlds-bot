"""Episode 10, part 5: deja vu (about 7.5 s).

The Noob's bridge has just met the old one. Steve stands on the Minecraft
planks; the Noob is at the far end of the rainbow bridge, Null behind him.

  A  Steve, close from the Noob's side: "Noob! Run!" (Episode 0's own recording).
  B  Through Steve's eyes: the Noob runs at us. "I am running!" (Episode 0's own
     recording). On "running" time slows to a quarter: the picture drains of
     colour, grain and a split of colours creep in, the image softens, and the
     Noob comes apart into the Noobs of other loops, each a different make of
     him (the old Episode 0 model, plain plastic, a box head, a fading ghost),
     running a little out of step. Then they are sucked back into one: a flash,
     colour, now.
  C  Steve, close, front: "I went through this... 412 times!"
  D  Steve, close, from the side, lower; his eyes drop: "I built a trap."

    python src/lookdev/ep10_p5_dejavu.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080]
        [--samples 32] [--times ...]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

T = {"a": 0.0, "steve_noob_run": 0.2, "noob_running": 1.57, "word": 1.99, "snap": 3.94, "steve_412": 4.14,
     "hush": 6.4, "steve_trap": 6.95, "end": 8.0, "length": 9.3}
SLOW = 0.25


# ------------------------------------------------------------------ time
def rate(t):
    """How fast the world runs: 1, then down to a quarter through "running", back to 1 at the snap."""
    if t >= T["snap"]:
        return 1.0
    return 1.0 - (1.0 - SLOW) * ss(T["word"], T["word"] + 0.35, t)


def clock(t):
    """The world's own time: the integral of rate (so the slow motion is smooth)."""
    if t <= T["word"]:
        return t
    n = 40
    t1 = min(t, T["snap"])
    h = (t1 - T["word"]) / n
    acc = sum(rate(T["word"] + (k + 0.5) * h) for k in range(n)) * h
    return T["word"] + acc + max(0.0, t - T["snap"])


def dv(t):
    """How deep in the deja vu the picture is: 0 now .. 1 the memory."""
    if t >= T["snap"] or t < T["word"] - 0.05:
        return 0.0
    return ss(T["word"] - 0.05, T["word"] + 0.55, t)


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    E = P4.build(tl, assets, res, samples)
    sc = E.sc
    plan = E.plan
    for p, ob in zip(plan.parts, E.objs):                   # his world, finished
        ob.hide_render = bool(ob.get("keep_hidden"))
        ob.location = p["at"]
        ob.scale = (1, 1, 1)
        ob["flash"] = 0.0
    E.giz.draw([])
    P4._beams(E, [])
    for o in E.tool.children_recursive + [E.tool]:          # he's running for his life, the tool put away
        o.hide_render = True
    E.Pt.root.location = (0, 0, -500)
    for o in E.Pt.col.objects:
        o.hide_render = True
    # the Noobs of other loops
    from noob import build_noob
    from kit.rigs import make_noob
    E.clones = []
    col = bpy.data.collections.new("loops")
    sc.collection.children.link(col)
    for k, (kind, kw) in enumerate((("plastic", {"finish": "plastic"}), ("box", {"head": "box"}),
                                    ("ghost", {}))):
        n = build_noob(col, height=2.0, name=f"loop_{kind}", **kw)
        n.kind = kind
        E.clones.append(n)
    tex = {os.path.splitext(f)[0]: os.path.join(tex_dir, f) for f in os.listdir(tex_dir)}
    old = make_noob(tex, name="loop_old", faces=False)       # Episode 0's own Noob
    old.kind = "old"
    E.old = old
    _ghostify([o for o in col.objects if o.name.startswith("loop_ghost") and o.type == "MESH"])
    E.Sp = Vector((1.7, plan.bridge_end.y, plan.deck))       # Steve, on the old planks, facing the Noob (-x)
    # his bridge reaches on over the old one's broken planks (no holes underfoot now)
    from roblox import make_part, plastic_material
    pa = make_part(col, "rbx_bridge_reach", (3.3, 3.0, 0.5), "Bright violet", plastic_material())
    for p_, ob_ in zip(plan.parts, E.objs):                  # (his last rainbow part lies under it)
        if p_["kind"] == "bridge" and p_["colour"] == "Bright violet":
            ob_.hide_render = True
            ob_["keep_hidden"] = 1
    pa.location = (plan.bridge_end.x + 0.6, plan.bridge_end.y, plan.deck - 0.25 + 0.045)   # over the planks and his last part
    E.Np0 = Vector((plan.lip.x - 0.4, plan.lip.y, plan.deck))
    sc.render.motion_blur_shutter = 0.5
    return E


def _ghostify(obs):
    """A loop almost gone: pale, see-through, glowing at the edges."""
    m = bpy.data.materials.new("loop_ghost")
    m.use_nodes = True
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.75, 0.85, 1.0, 1)
    b.inputs["Emission Color"].default_value = (0.55, 0.75, 1.0, 1)
    b.inputs["Emission Strength"].default_value = 0.6
    fr = nt.nodes.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.35
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "MULTIPLY_ADD"
    inv.inputs[1].default_value = 0.7
    inv.inputs[2].default_value = 0.25
    nt.links.new(fr.outputs["Facing"], inv.inputs[0])
    nt.links.new(inv.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    for o in obs:
        o.data.materials.clear()
        o.data.materials.append(m)


# ------------------------------------------------------------- the cast
def noob_x(tc):
    """The Noob's x along the bridges (world clock tc): from the far lip toward Steve."""
    t0 = T["noob_running"] - 0.3
    u = max(0.0, tc - t0)
    return min(-1.0, -6.5 + 3.0 * (u - 0.2 * (1 - math.exp(-u / 0.2))))


def run_pose(ph, kind="new"):
    sw = math.sin(ph)
    return {"chest_lean": 12, "head_turn": 0, "head_nod": -2, "arm_sl": {"fwd": -62 * sw, "out": 10},
            "arm_sr": {"fwd": 62 * sw, "out": 10}, "leg_sl": {"fwd": 46 * sw}, "leg_sr": {"fwd": -46 * sw}}


CLONES = [  # (lateral m, back m, phase offset, delay s) for plastic, box, ghost, old
    (-1.15, 0.7, 1.4, 0.10), (1.25, 1.0, 2.6, 0.22), (-0.55, 1.7, 3.7, 0.34), (0.7, 0.35, 0.7, 0.0)]


def apply(E, t):
    from pose import pose
    from noob import pose_noob
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from ep09_new import NF, SF, talk
    from stage import place_null_lights
    plan = E.plan
    tc = clock(t)
    d = dv(t)
    S, N, X = E.S, E.N, E.X
    f_render = int(round(t * FPS))
    # ------------------------------------------------ the Noob, running at Steve
    nx = noob_x(tc)
    ph = 2 * math.pi * 2.6 * tc
    npz = run_pose(ph)
    npz["root_yaw"] = 90                                       # facing +x
    pose_noob(N, npz)
    N.root.location = (nx, plan.lip.y, plan.deck + 0.07 * abs(math.sin(ph)))
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    for k, v in NF["shout"].items():
        if k.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{k[5:]}"] = v
        else:
            fn[k] = v
    mo = E.mouth.get("noob", {}).get(f_render)
    talk(fn, mo)
    set_face(N.face, fn)
    # ------------------------------------------------ the other loops: they come apart from him, then back in
    back = 0.0 if t < T["snap"] - 0.18 else ss(T["snap"] - 0.18, T["snap"], t)      # sucked back in
    for k, c in enumerate(E.clones + [E.old]):
        lat, bk, po, dl = CLONES[k]
        out = ss(T["word"] + dl, T["word"] + dl + 0.45, t) * (1 - back)
        show = out > 0.02 and t < T["snap"]
        cph = 2 * math.pi * 2.6 * (tc - 0.08 * (k + 1)) + po
        pos = Vector((nx - bk * out, plan.lip.y + lat * out, plan.deck + 0.07 * abs(math.sin(cph))))
        if c is E.old:
            E.old.root.location = pos
            E.old.root.rotation_euler = (0, 0, math.radians(90))
            sw = math.sin(cph)
            for nm, a in (("arm_r", -62 * sw), ("arm_l", 62 * sw), ("leg_r", 46 * sw), ("leg_l", -46 * sw)):
                E.old.parts[nm].rotation_euler = (math.radians(a), 0, 0)
            for o in E.old.root.children_recursive:
                o.hide_render = not show
        else:
            pz = run_pose(cph)
            pz["root_yaw"] = 90
            pose_noob(c, pz)
            c.root.location = pos
            for o in [c.root] + list(c.root.children_recursive):
                o.hide_render = not show
    # ------------------------------------------------ Steve, on the old bridge
    Sp = E.Sp
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    from ep09_new import flat, unflat
    sp = flat(lib["idle (Benly 2.2)"])
    if t < T["noob_running"]:                                  # "Noob! Run!": he leans in, an arm sweeps him on
        u = ss(T["steve_noob_run"], T["steve_noob_run"] + 0.3, t)
        w = math.sin(2 * math.pi * 1.8 * max(0.0, t - T["steve_noob_run"]))
        pz = {"chest_lean": 10 * u, "head_nod": -4, "arm_sl": {"fwd": 70 * u + 25 * w * u, "elbow": 50, "out": 10},
              "arm_sr": {"fwd": 10, "out": 14, "elbow": 20}}
        face = SF["scared"]
    elif t < T["hush"]:                                        # stunned
        u = ss(T["snap"], T["snap"] + 0.3, t)
        pz = {"chest_lean": lerp(4, -3, u), "head_nod": lerp(-4, -8, u),
              "arm_sl": {"fwd": 12, "out": 16, "elbow": 26}, "arm_sr": {"fwd": 10, "out": 16, "elbow": 28}}
        face = {"both_to": 0.36, "both_tm": 0.42, "both_ti": 0.34, "both_ps": 0.58, "both_py": 0.05,
                "bb_raise": 0.65, "bb_tilt": -0.6, "bb_arch": 0.3}
    else:                                                       # "I built a trap.": the head drops, eyes down
        u = ss(T["hush"], T["steve_trap"] + 0.3, t)
        pz = {"chest_lean": lerp(-3, 6, u), "head_nod": lerp(-8, 14, u), "head_tilt": 4 * u,
              "arm_sl": {"fwd": 6, "out": 10, "elbow": 14}, "arm_sr": {"fwd": 6, "out": 10, "elbow": 16}}
        face = {"both_to": lerp(0.36, -0.25, u), "both_tm": lerp(0.42, -0.2, u), "both_ti": lerp(0.34, 0.25, u),
                "both_ps": 0.85, "both_py": lerp(0.05, -0.5, u), "bb_tilt": lerp(-0.6, -0.95, u),
                "bb_raise": lerp(0.65, 0.35, u), "m_arch": 0.22 * u}
    for k, v in flat(pz).items():
        sp[k] = v
    pose(S.arm, unflat(sp))
    S.holder.location = Sp
    S.holder.rotation_euler = (0, 0, math.radians(-90))
    S.holder.hide_render = T["noob_running"] <= t < T["snap"]          # his own eyes
    fs = {f"{e}_{k}": v for e in EYES for k, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    for k, v in face.items():
        if k.startswith("both_"):
            for e in EYES:
                fs[f"{e}_{k[5:]}"] = v
        elif not k.startswith("bb_"):
            fs[k] = v
    talk(fs, E.mouth.get("steve", {}).get(f_render))
    set_face(S.face, fs)
    for ob_ in S.brows.values():
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(S.brows, {k: v for k, v in face.items() if k.startswith("bb_")})
    # ------------------------------------------------ Null, behind the Noob, out in the void
    X.root.scale = (1.6,) * 3
    X.root.location = (nx - 20.0, plan.lip.y + 6.0, plan.deck - 7.5)
    X.root.rotation_euler = (math.radians(14), 0, math.radians(-90 + 180))
    for side, sgn in (("sl", 1), ("sr", -1)):
        X.arms[side].rotation_euler = (math.radians(-70), math.radians(sgn * 10), 0)
    X.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0.9 * tc)
    X.orbit2.rotation_euler = (math.radians(-12), math.radians(14), -0.6 * tc)
    place_null_lights(X, fade=1.0)
    from null import null_smile
    null_smile(1.0)
    # ------------------------------------------------ the camera
    bpy.context.view_layer.update()

    def centre(ob, m=None):
        c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
        return (m @ ob.matrix_world @ c) if m is not None else ob.matrix_world @ c
    hs = centre(S.face, S.holder.matrix_world)
    loc, look, lens, fstop, focus, shake = camera(E, t, tc, hs)
    from ep10_p2_omg import handheld, rumble
    y1, p1, r1 = handheld(tc, shake)
    q = (look - loc).to_track_quat("-Z", "Y") @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.key.location = loc + Vector((0.8, 0.6, 1.4))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    E.sc.render.motion_blur_shutter = 0.5 if d < 0.5 else 0.9                   # the memory smears
    return {"dv": d, "flash": max(0.0, 1 - abs(t - T["snap"]) / 0.09) if t >= T["snap"] - 0.02 else 0.0}


def camera(E, t, tc, hs):
    Sp = E.Sp
    if os.environ.get("TOPCAM"):                             # look-dev: the bridge joint from above
        c = Vector((E.plan.bridge_end.x + 0.5, E.plan.bridge_end.y, E.plan.deck))
        return c + Vector((0.01, -0.5, 7.0)), c, 24, 8.0, None, 0.0
    if t < T["noob_running"]:                                # A: Steve, close, from the Noob's side
        u = ss(T["a"], T["noob_running"], t)
        loc = hs + Vector((-1.6 + 0.2 * u, -0.9 + 0.1 * u, -0.15))
        return loc, hs + Vector((0, 0, -0.05)), 36, 2.2, None, 0.4
    if t < T["snap"]:                                        # B: through Steve's eyes
        eye = Sp + Vector((-0.2, 0.0, 1.72))
        nx = noob_x(tc)
        look = Vector((nx, E.plan.lip.y, E.plan.deck + 1.3))
        d = (look - eye).length
        soft = dv(t)
        return eye, look, 30 + 6 * soft, 2.0, d * (1 + 0.35 * soft * (0.5 + 0.5 * math.sin(t * 5))), 0.35
    if t < T["hush"]:                                        # C: Steve, front, a slow push
        u = ss(T["snap"], T["hush"], t)
        loc = hs + Vector((-1.45 + 0.3 * u, 0.15, -0.08))
        return loc, hs + Vector((0, 0, -0.04)), lerp(40, 46, u), 2.0, None, 0.25
    u = ss(T["hush"], T["end"] + 0.5, t)                     # D: from his left, lower, as his head drops
    loc = hs + Vector((-0.55, -1.25 + 0.15 * u, -0.35))
    return loc, hs + Vector((0, 0, -0.12)), lerp(42, 48, u), 1.8, None, 0.2


# ----------------------------------------------------------- the deja vu look
def finish(path, mist_path, d, flash):
    import numpy as np
    from PIL import Image, ImageFilter
    P4.finish(path, mist_path)
    if d <= 0.001 and flash <= 0.001:
        return
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, np.float32) / 255.0
    h, w = a.shape[:2]
    if d > 0:
        rnd = np.random.default_rng(int(d * 1000) + int(os.path.basename(path)[:-4]))
        # the memory's softness: a glow of itself, blurred
        soft = np.asarray(im.filter(ImageFilter.GaussianBlur(3 + 4 * d)), np.float32) / 255.0
        a = a * (1 - 0.35 * d) + soft * 0.35 * d
        # colour drains toward an old print's warmth
        lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
        sep = np.stack([lum * 1.08 + 0.04, lum * 0.95 + 0.02, lum * 0.78], -1)
        a = a * (1 - 0.8 * d) + sep * 0.8 * d
        # a split of colours: red one way, blue the other
        sh = int(round(6 * d))
        if sh:
            a[:, :, 0] = np.roll(a[:, :, 0], sh, 1)
            a[:, :, 2] = np.roll(a[:, :, 2], -sh, 1)
        # grain
        a += rnd.normal(0, 0.04 * d, (h, w, 1)).astype(np.float32)
        # a few torn lines, more as it deepens
        for _ in range(int(6 * d)):
            y0 = int(rnd.integers(0, h - 8))
            hh = int(rnd.integers(2, 10))
            a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], int(rnd.integers(-30, 30)), 1)
        # a darker edge
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        a *= (1 - 0.45 * d * np.clip((r - 0.45) / 0.7, 0, 1) ** 1.3)[..., None]
    if flash > 0:
        a = a + (1 - a) * 0.85 * flash
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    for k in ("a", "steve_noob_run", "noob_running", "snap", "steve_412", "hush", "steve_trap", "end"):
        if k in b:
            T[k] = b[k][0]
    if "noob_running" in b:
        T["word"] = b["noob_running"][0] + 0.42               # "running" starts here in the recording
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
    state = {}

    def handler(scene, depsgraph=None):
        state["look"] = apply(E, (scene.frame_current + scene.frame_subframe - 1) / FPS)

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
        look = apply(E, (f - 1) / FPS)                         # the look of the frame itself (not a sub-frame)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        finish(dst, cand[-1] if cand else "", look["dv"], look["flash"])
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
