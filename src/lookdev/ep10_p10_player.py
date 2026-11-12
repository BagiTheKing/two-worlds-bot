"""Episode 10 (the finale), part 10: "I am a Roblox player."

What is left of Null drifts in the void. One cell (a glass pixel, a freed Noob
inside it, at peace now) comes rolling through the sky toward the island,
tumbling end over end like a ball, slowing; the camera flies with it, the cell
sharp, everything else melted. It stops in the air in front of the Noob, a
jump away from the stub, the way an obby's next block waits. The Noob sees it:
his wet face lifts, and a grin grows. "Steve, remember... I am a Roblox
player." Steve: "Don't—" (cut).

The set is part 7's (ep10_p7_reveal): the island, the two of them hanging
one-handed from the stub, the cell heads (the soul's head collections).

    python src/lookdev/ep10_p10_player.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
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
import ep10_p7_reveal as P7                                          # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

T = {"roll": 0.0, "sees": 3.6, "noob_player": 4.5, "noob_player_end": 7.0, "steve_dont": 7.15, "end": 7.6,
     "length": 8.0}
P7_TL = {"beats": {"a": [0.0, 0.25], "patch_look": [0.25, 3.23], "see": [3.33, 4.73], "steve_you": [4.73, 8.75],
                   "dive": [8.75, 12.8], "end": [12.8, 13.0]}, "lines": [], "length": 13.0}
R_CELL = 0.5                                                  # half the cell's size (m): a 1 m cube


def shots():
    return [("ROLL", T["sees"]), ("SEES", T["noob_player"]), ("PLAYER", T["steve_dont"]), ("DONT", 1e9)]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "DONT", t0, 1e9


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    P7.align(P7_TL)
    E = P7.build(P7_TL, tex_dir, assets, res, samples)
    E.mouth = {}
    E.X.root.location = (0, 0, -3000.0)                      # Null is gone
    E.X.root.scale = (0.001,) * 3
    col = bpy.data.collections.new("freed")
    E.sc.collection.children.link(col)
    # the cell: the soul's glass, its edges a softer, paler glow now
    import bmesh
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    h = R_CELL
    vs = [bm.verts.new((dx * h, dy * h, dz * h)) for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                                                    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        fc = bm.faces.new([vs[i] for i in f])
        for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = uv
    me = bpy.data.meshes.new("freed_cell")
    bm.to_mesh(me)
    bm.free()
    m = P7._cell_material()
    m.name = "freed_cell"
    for n in m.node_tree.nodes:
        if n.type == "EMISSION":
            n.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
            n.inputs["Strength"].default_value = 2.4
    me.materials.append(m)
    E.cell = bpy.data.objects.new("freed_cell", me)
    col.objects.link(E.cell)
    E.cell.rotation_mode = "QUATERNION"
    E.cell_head = bpy.data.objects.new("freed_head", None)
    E.cell_head.instance_type = "COLLECTION"
    E.cell_head.instance_collection = E.styles[0]
    E.cell_head.rotation_mode = "QUATERNION"
    k = E.style_scale[0]
    E.cell_head.scale = (k, k, k)
    col.objects.link(E.cell_head)
    for f in E.style_faces:                                   # at peace: the Noob's own face, a small smile
        _peace(f)
    L = bpy.data.lights.new("freed_glow", "POINT")
    L.energy = 18.0
    L.color = (0.8, 0.9, 1.0)
    L.shadow_soft_size = 0.4
    E.cell_glow = bpy.data.objects.new("freed_glow", L)
    col.objects.link(E.cell_glow)
    # far off, a few more of them still drifting (soft points behind)
    rng = random.Random(10)
    E.drifters = []
    for k_ in range(26):
        ob = bpy.data.objects.new(f"drift_{k_}", me)
        col.objects.link(ob)
        s = rng.uniform(0.35, 0.9)
        ob.scale = (s, s, s)
        ob.rotation_mode = "XYZ"
        E.drifters.append((ob, Vector((E.XE - rng.uniform(12, 60), E.Y0 + rng.uniform(-30, 30), E.deck + rng.uniform(-14, 10))),
                           Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(-0.15, 0.1))),
                           Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))))
    # the cell's path: from out over the void, down and in, to just out of the Noob's reach
    # from where Null was (his chest, where it all flew apart), falling the whole way to just in front of the Noob
    E.cell_start = Vector((E.XE - 26.0, E.Y0 + 7.0, E.deck + 4.0))
    E.cell_end = Vector((E.XE - 1.7, E.lane["N"] - 0.2, E.deck - 1.7))
    return E


def _peace(f):
    from faceplate import NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    for e in NOOB_EYES:
        for k, v in NOOB_EYE_DEFAULTS.items():
            f[f"{e}_{k}"] = v
        f[f"{e}_h"] = 1.6
    for k, v in NOOB_MOUTH.items():
        f[k] = v
    f["m_o"] = 0.0
    f["m_w"] = 1.6


# ------------------------------------------------------------------ the cell
def cell_at(E, t):
    """(centre, rotation of the cube, how far along 0..1): one long fall from where Null was toward
    the Noob, never stopping: it drifts at first, then the fall takes it (faster, lower), tumbling."""
    t_arrive = T["steve_dont"] + 0.55                        # it would reach him just after the cut
    u = max(0.0, min(1.05, t / t_arrive))
    S_, A_ = E.cell_start, E.cell_end
    h = S_.lerp(A_, 0.25 * u + 0.75 * u ** 1.5)              # across: slow out there, quicker as it comes
    top = S_.z + 5.0                                          # up and clear of his builds, over them, then the fall
    if u < 0.4:
        z = lerp(S_.z, top, math.sin(0.5 * math.pi * u / 0.4))
    else:
        z = lerp(top, A_.z, ss(0.45, 1.0, u) ** 1.25)
    c = Vector((h.x, h.y, z))
    # tumbling end over end (a rolling ball's turn for the way it has come), a slow wobble across it
    path = A_ - S_
    d = path.normalized()
    axis = d.cross(Vector((0, 0, -1))).normalized()
    dist = (h - S_).length + abs(z - S_.z) * 0.3
    q = Quaternion(axis, 0.55 * dist / R_CELL) @ Quaternion(d, 0.35 * math.sin(t * 0.8))
    return c, q, u


def apply(E, t):
    shot = which(t)[0]
    P7.set_world(E, False)
    E.force_shot = "R1"
    # their faces and heads for this part
    noob_face(E, t)
    steve_face(E, t)
    E.lip_frame = int(round(t * FPS))
    P7.cast(E, P7.T["dive"] - 2.6)
    E.force_shot = None
    E.X.root.location = (0, 0, -3000.0)                      # Null is gone
    E.X.root.scale = (0.001,) * 3
    E.Pt.beam.hide_render = True
    E.Pt.root.location = (0, 0, -500)                        # Patch has gone up to look (out of this part)
    for o in E.Pt.col.objects:
        o.hide_render = True
    c, q, k = cell_at(E, t)
    E.cell.location = c
    E.cell.rotation_quaternion = q
    # the head inside stays upright (afloat), turning slowly; at the stop it looks at the Noob
    hn = P7.P6._head(E.N.face)
    look = (hn - c)
    yaw_to = math.atan2(look.y, look.x) + math.pi / 2       # the head faces -y
    yaw = yaw_to + 0.5 * math.sin(t * 0.7)                   # afloat, turning a little on its own
    E.cell_head.location = c
    E.cell_head.rotation_quaternion = Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), 0.08 * math.sin(t * 1.3))
    E.cell_glow.location = c + Vector((0, 0, 0.15))
    for ob, p0, v, w in E.drifters:
        ob.location = p0 + v * (t + 6.0)
        ob.rotation_euler = tuple(w * (t + 6.0) * 0.4)
    return camera_set(E, t, shot)


def noob_face(E, t):
    """Teary, then he sees it: eyes up and wide, the shine back; a grin grows, cocky."""
    from faceplate import NOOB_EYES
    import ep10_p6_fall as P6
    from ep09_new import NF, talk
    f_render = int(round(t * FPS))
    see = ss(T["sees"] - 0.1, T["sees"] + 0.5, t)
    grin = ss(T["sees"] + 0.35, T["noob_player"] + 0.2, t)
    teary = dict(NF.get("teary", NF["scared"]))
    teary.update({"m_arch": 0.38, "m_w": 1.35})
    wide = {"both_h": 1.9, "both_ps": 1.0, "both_open": 1.0, "m_arch": 0.15, "m_w": 1.4, "m_o": 0.15}
    cocky = {"both_h": 1.55, "both_ps": 1.0, "both_to": 0.28, "both_tm": 0.18, "both_ti": 0.05, "m_arch": -0.6,
             "m_w": 2.4, "m_o": 0.05, "m_tilt": 0.18}
    face = P6._mixf(P6._mixf(teary, wide, see), cocky, grin)

    def hook(fn):
        for k, v in face.items():
            if k.startswith("both_"):
                for e in NOOB_EYES:
                    fn[f"{e}_{k[5:]}"] = v
            else:
                fn[k] = v
        for e in NOOB_EYES:                                   # looking at the cell
            fn[f"{e}_py"] = lerp(-0.3, -0.05, see)
            fn[f"{e}_px"] = lerp(0.0, 0.2, see)
        talk(fn, E.mouth.get("noob", {}).get(f_render))
        return fn
    E.noob_face_hook = hook
    E.noob_head = (lerp(-20, -6, see), lerp(-6, -2, see) + 4 * grin * math.sin(t * 2.0))


def steve_face(E, t):
    """Watching the Noob; on "Don't—" he turns to him, panicking."""
    from ep09_new import SF
    import ep10_p6_fall as P6
    dont = ss(T["steve_dont"] - 0.35, T["steve_dont"] - 0.05, t)
    worried = {"both_to": 0.05, "both_tm": 0.0, "both_ti": -0.1, "both_ps": 0.62, "both_py": 0.0,
               "bb_tilt": -0.6, "bb_raise": 0.5, "m_arch": 0.25, "m_w": 1.5}
    panic = {"both_to": -0.3, "both_tm": -0.3, "both_ti": -0.25, "both_ps": 0.5, "both_py": 0.0,
             "bb_tilt": -0.8, "bb_raise": 0.95, "m_arch": 0.2, "m_w": 1.7}
    E.steve_face = P6._mixf(worried, panic, dont)
    E.steve_head = (lerp(-34, -52, ss(T["noob_player"] - 0.3, T["noob_player"] + 0.4, t)), lerp(-8, -4, dont))


# ------------------------------------------------------------------ cameras
def camera_set(E, t, shot):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    loc, look, lens, fstop, focus, amp, roll = camera(E, t, shot)
    y1, p1, r1 = handheld(t, amp)
    q = P7.P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1 + roll))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.key.location = loc + Vector((0.4, 0.0, 1.2))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    return {"shot": shot}


def camera(E, t, shot):
    c, q, k = cell_at(E, t)
    if os.environ.get("DBGCAM"):
        cc = Vector((E.XE - 1.5, E.Y0 + 0.5, E.deck - 0.8))
        return cc + Vector((-5.0, -4.0, 1.5)), cc, 24, 16.0, None, 0.0, 0.0
    hn = P7.P6._head(E.N.face)
    hs = P7.P6._head(E.S.face, E.S.holder)
    t0, t1 = which(t)[1:]
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, T["end"], t)
    if shot == "ROLL":
        # a chase from a distance: alongside and a little behind, the cell in the void, the island far ahead
        lag = cell_at(E, max(0.0, t - 0.35))[0]
        path = (E.cell_end - E.cell_start).normalized()
        side = path.cross(Vector((0, 0, 1))).normalized()
        loc = lag - path * lerp(6.5, 4.5, u) + side * lerp(3.4, 2.6, u) + Vector((0, 0, lerp(1.6, 0.6, u)))
        ahead = c + path * 1.2
        look = c.lerp(ahead, 0.25).lerp(hn, 0.18 * ss(0.55, 1.0, u))     # at the end, him far ahead of it
        return loc, look, lerp(42, 46, u), 4.0, (c - loc).length, 0.04, 0.0
    if shot == "SEES":
        # his face, from the front: he catches sight of it (it is in his eyes, mirrored, far off, coming)
        fw = P7.noob_eye_normal(E)
        fw = Vector((fw.x, fw.y, 0)).normalized()
        side = fw.cross(Vector((0, 0, 1))).normalized()
        loc = hn + fw * lerp(0.95, 0.75, u) + side * 0.18 + Vector((0, 0, 0.02))
        return loc, hn + Vector((0, 0, -0.02)), 50, 2.6, None, 0.04, 0.0
    if shot == "PLAYER":
        # his face three-quarters, the cell behind and beside him, coming, bigger and bigger (soft)
        fw = P7.noob_eye_normal(E)
        fw = Vector((fw.x, fw.y, 0)).normalized()
        to_c = Vector(((c - hn).x, (c - hn).y, 0)).normalized()
        sgn = 1 if fw.cross(to_c).z > 0 else -1
        a = math.radians(-58 * sgn)
        d = Vector((fw.x * math.cos(a) - fw.y * math.sin(a), fw.x * math.sin(a) + fw.y * math.cos(a), 0))
        loc = hn + d * lerp(1.15, 1.0, u) + Vector((0, 0, -0.02))
        look = hn.lerp(c, 0.06)
        return loc, look, 40, 2.4, (hn - loc).length, 0.08, 0.0
    # DONT: Steve, close, turning to him, panicking; we cut on his word
    d = (hn - hs).normalized()
    d = Vector((d.x, d.y, 0)).normalized()
    side = d.cross(Vector((0, 0, 1))).normalized()
    out = Vector((-1.0, 0.0, 0.0))                           # out from the wall
    v = (out * 0.8 + d * 0.45).normalized()
    loc = hs + v * 1.0 + Vector((0, 0, 0.02))
    return loc, hs + Vector((0, 0, -0.04)), 42, 2.0, None, 0.35, 0.0


# ------------------------------------------------------------------ main
def finish(path, mist_path):
    P4.finish(path, mist_path)


def align(tl):
    b = tl.get("beats", {})
    for k in ("roll", "sees", "end"):
        if k in b:
            T[k] = b[k][0]
    for k in ("noob_player", "steve_dont"):
        if k in b:
            T[k] = b[k][0]
            T[k + "_end"] = b[k][1]
    if b:
        T["length"] = tl["length"] + 0.05


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
    tl = {"length": T["length"] - 0.05, "beats": {}, "lines": []} if a.timeline == "-" else json.load(open(a.timeline))
    align(tl)
    n_frames = int(round(T["length"] * FPS)) + 1
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    E = build(tl, a.tex_dir, a.assets, a.res, a.samples)
    E.force_shot = None
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
        apply(E, (f - 1) / FPS)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        finish(dst, cand[-1] if cand else "")
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
