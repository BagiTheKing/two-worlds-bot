"""Episode 10 (the finale), part 14: the end.

Patch sets them down on a meadow of the world that came back (gold light, the
floating island still up in the sky) and folds his arms away. Steve and the
Noob look at each other. Nobody knows what to say. "...So. I'm back?" "You
jumped off a cliff." "...Technically, a bridge." Quack: the Noob's duck from
Episode 5 (RIP duck), respawned with the world, waddles out of the grass. "MY
DUCK!" Steve smiles despite himself; Patch's eye curls into a ^. "We did it,
guys." The three of them on the hill, the sun going down. "What do you think
happens to Null... in the void?" The camera drifts away from them, up, and down
into the void: "What do you think happens to anyone in the void?" Swimming
through the dark, past dying cells, to what is left of Null: his head, pulling
its pixels back together, the upset face lit. "All I wanted... was to fix this
world. I'll be back. And next time... I'll finish it." SEASON 2.

The set is part 13's (the restored world under the island); the void is its own
place, far under everything.

    python src/lookdev/ep10_p14_end.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
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
import ep10_p13_patch as P13                                         # noqa: E402
import ep10_p7_reveal as P7                                          # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

T = {"land": 0.0, "noob_back": 1.4, "steve_jumped": 3.0, "noob_bridge": 4.6, "duck": 6.2, "noob_duck": 7.2,
     "patch_did": 8.4, "sunset": 10.2, "steve_null": 11.0, "noob_void": 14.0, "swim": 16.6, "null_end": 18.2,
     "null_end_end": 23.0, "end": 23.3, "length": 27.0}
VOID_AT = Vector((0.0, 0.0, -2600.0))


def shots():
    return [("LAND", T["noob_back"]), ("NOOB1", T["steve_jumped"]), ("STEVE1", T["noob_bridge"]),
            ("NOOB2", T["duck"]), ("DUCK", T["noob_duck"]), ("HUG", T["patch_did"]), ("PATCH", T["sunset"]),
            ("SUNSET", T["noob_void"]), ("DRIFT", T["swim"]), ("VOID", 1e9)]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "VOID", t0, 1e9


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    import ep10_p9_death as P9
    E = P13.build(tl, tex_dir, assets, res, samples)
    sc = E.sc
    rng = random.Random(14)
    g = E.land_at.copy()
    E.ground = g
    E.spot = {"S": g + Vector((-0.7, 0.0, 0.0)), "N": g + Vector((0.7, 0.15, 0.0))}
    E.patch_spot = g + Vector((0.05, 0.85, 2.2))
    # the duck (Episode 5's, from the obby kit's drawing), small, in Roblox plastic
    from kit.obby import DUCK
    from roblox import make_part, plastic_material
    col = bpy.data.collections.new("duck")
    sc.collection.children.link(col)
    mat = plastic_material()
    names = {"yellow": "Bright yellow", "orange": "Bright orange", "black": "Really black"}
    E.duck = bpy.data.objects.new("duck_root", None)
    col.objects.link(E.duck)
    k = 0.2
    for i, (size, at, c) in enumerate(DUCK):
        ob = make_part(col, f"duck_{i}", tuple(v * k for v in size), names.get(c, "Bright yellow"), mat)
        ob.location = tuple(v * k for v in at)
        ob.parent = E.duck
    E.duck.rotation_mode = "XYZ"
    # the void: Null's head, the pixels coming back to it, debris drifting, a cold dark
    P9._upset_face(E)
    E.void_bits = []
    bm = bpy.data.materials.new("void_bit")
    bm.use_nodes = True
    b = bm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.02, 0.01, 0.03, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.85, 1)
    b.inputs["Emission Strength"].default_value = 0.0
    pm = bpy.data.materials.new("void_pink")
    pm.use_nodes = True
    b2 = pm.node_tree.nodes["Principled BSDF"]
    b2.inputs["Base Color"].default_value = (0.9, 0.05, 0.85, 1)
    b2.inputs["Emission Color"].default_value = (1.0, 0.1, 0.9, 1)
    b2.inputs["Emission Strength"].default_value = 3.0
    for i in range(180):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -900))
        ob = bpy.context.active_object
        ob.name = f"void_bit_{i}"
        ob.data.materials.append(pm if i % 3 == 0 else bm)
        s = rng.uniform(0.12, 0.45)
        far = rng.random() < 0.45                                 # some drift far around; the rest come home to him
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        r0 = rng.uniform(9, 40) if far else rng.uniform(4, 16)
        E.void_bits.append((ob, s, far, d, r0, rng.uniform(0, 6.28), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                                                              rng.uniform(-1, 1)))))
    L = bpy.data.lights.new("void_rim", "POINT")
    L.energy = 6000.0
    L.color = (1.0, 0.2, 0.85)
    L.shadow_soft_size = 2.0
    E.void_rim = bpy.data.objects.new("void_rim", L)
    sc.collection.objects.link(E.void_rim)
    L2 = bpy.data.lights.new("void_fill", "POINT")
    L2.energy = 2500.0
    L2.color = (0.3, 0.7, 1.0)
    L2.shadow_soft_size = 2.0
    E.void_fill = bpy.data.objects.new("void_fill", L2)
    sc.collection.objects.link(E.void_fill)
    w = bpy.data.worlds.new("void_world")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.012, 0.004, 0.022, 1)
    bg.inputs["Strength"].default_value = 1.0
    w.mist_settings.start = 4.0
    w.mist_settings.depth = 60.0
    E.void_world = w
    return E


# ------------------------------------------------------------------ the meadow
# the Noob bending down for the duck (rigid legs: a staggered stance, the hips a little down)
PICKUP = {"chest_lean": 72, "head_nod": -38, "hips_drop": 0.12, "arm_sl": {"fwd": 88, "out": -6},
          "arm_sr": {"fwd": 88, "out": -6}, "leg_sl": {"fwd": 20}, "leg_sr": {"fwd": -20}}


def pickup_spot(E):
    """Where his hands come down in front of him when he bends (the duck walks to there), and how high."""
    if getattr(E, "_pick", None) is None:
        from noob import pose_noob
        N = E.N
        pose_noob(N, dict(PICKUP, root_yaw=-90))
        N.root.location = E.spot["N"]
        N.root.rotation_euler = (0, 0, math.radians(-90))
        bpy.context.view_layer.update()
        m = 0.5 * (P7.P6._noob_hand(N, "sl") + P7.P6._noob_hand(N, "sr"))
        E._pick = Vector((m.x, m.y, E.ground.z))
        E._pick_dz = m.z - E.ground.z
    return E._pick


def cast(E, t):
    pickup_spot(E)
    from pose import pose
    from noob import pose_noob
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from ep09_new import SF, NF, talk, flat, unflat
    from patch import DEFAULTS as PD, set_patch
    import ep10_p6_fall as P6
    S, N, Pt = E.S, E.N, E.Pt
    f_render = int(round(t * FPS))
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    sit = 1.0 if t >= T["sunset"] else 0.0                   # sitting already when the sunset shot opens (a time cut)
    # the duck: he bends down, scoops it up, hugs it
    nd = T["noob_duck"]
    bend = ss(nd - 0.4, nd + 0.05, t) * (1 - ss(nd + 0.2, nd + 0.65, t))
    hug = ss(nd + 0.2, nd + 0.65, t)
    # ---- where they stand (facing each other), then sit side by side facing the sun (+x -y)
    sun_dir = Vector((0.55, -0.83, 0)).normalized()
    # Steve
    sp = flat(lib["idle (Benly 2.2)"])
    stand_pose = {"head_nod": -2 + 4 * ss(T["steve_jumped"] + 1.2, T["noob_bridge"], t),
                  "arm_sl": {"fwd": 6, "out": 12, "elbow": 14}, "arm_sr": {"fwd": 6, "out": 12, "elbow": 16}}
    # on the grass, legs out in front, leaning back on his hands
    sit_pose = {"hips_drop": 0.93, "chest_lean": -6, "head_nod": -2, "arm_sl": {"fwd": -22, "out": 14, "elbow": 4},
                "arm_sr": {"fwd": -22, "out": 14, "elbow": 4},
                "foot_sl": {"x": -0.06, "y": -0.97, "z": 0.08, "pitch": 70},
                "foot_sr": {"x": 0.1, "y": -0.8, "z": 0.06, "pitch": 55, "yaw": 8}}
    for k_, v in flat(P13.P12.P10.P7.P6._mix(stand_pose, sit_pose, sit)).items():
        sp[k_] = v
    pose(S.arm, unflat(sp))
    yaw_face = 90                                              # toward the Noob (+x)
    yaw_sun = math.degrees(math.atan2(sun_dir.y, sun_dir.x)) + 90
    S.holder.rotation_euler = (0, 0, math.radians(lerp(yaw_face, yaw_sun, sit)))
    S.holder.location = E.spot["S"] + Vector((0, 0, 0.02))
    # his face
    flat_ = {"both_to": 0.42, "both_tm": 0.45, "both_ti": 0.4, "both_ps": 0.8, "bb_tilt": -0.2, "bb_raise": -0.1,
             "m_arch": 0.12, "m_w": 1.6}
    smile = {"both_to": 0.18, "both_tm": 0.15, "both_ti": 0.1, "both_ps": 0.85, "bb_tilt": -0.35, "bb_raise": 0.25,
             "m_arch": -0.45, "m_w": 1.9}
    calm = {"both_to": 0.25, "both_tm": 0.22, "both_ti": 0.15, "both_ps": 0.8, "bb_tilt": -0.45, "bb_raise": 0.3,
            "m_arch": 0.05, "m_w": 1.7}
    face = P6._mixf(P6._mixf(flat_, smile, ss(T["noob_duck"] + 0.2, T["noob_duck"] + 0.8, t)), calm, sit)
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
    # the Noob
    hold = {"arm_sl": {"fwd": lerp(6, 62, hug), "out": lerp(8, -14, hug)},
            "arm_sr": {"fwd": lerp(6, 62, hug), "out": lerp(8, -14, hug)}}
    stand_n = {"chest_lean": 4, "head_nod": 6 * (1 - hug) - 4 * hug, **hold}
    sit_n = {"hips_drop": 1.0, "chest_lean": 8, "head_nod": -2, "leg_sl": {"fwd": 80}, "leg_sr": {"fwd": 80}, **hold}
    npz = P13.P12.P10.P7.P6._mix(P13.P12.P10.P7.P6._mix(stand_n, PICKUP, bend), sit_n, sit)
    npz["root_yaw"] = lerp(-90, yaw_sun, sit)
    pose_noob(N, npz)
    N.root.location = E.spot["N"] + (Vector((0, 0, 0.0)))
    N.root.rotation_euler = (0, 0, math.radians(npz["root_yaw"]))
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    sheep = {"both_h": 1.5, "both_ps": 1.0, "both_to": 0.2, "both_tm": 0.1, "both_py": -0.2, "m_arch": 0.15, "m_w": 1.4}
    joy = dict(NF["happy"])
    joy.update({"both_ps": 1.0})
    quiet = {"both_h": 1.55, "both_ps": 1.0, "both_to": 0.2, "m_arch": -0.2, "m_w": 1.6}
    nf = P6._mixf(P6._mixf(sheep, joy, ss(T["noob_duck"] - 0.1, T["noob_duck"] + 0.2, t)), quiet, ss(T["steve_null"], T["noob_void"], t))
    for k, v in nf.items():
        if k.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{k[5:]}"] = v
        else:
            fn[k] = v
    talk(fn, E.mouth.get("noob", {}).get(f_render))
    set_face(N.face, fn)
    # ---- the duck: out of the grass, up to him; he bends down and scoops it up into his arms
    bpy.context.view_layer.update()
    d1 = E._pick
    d0 = E.ground + Vector((2.4, -2.2, 0.0))
    u = ss(T["duck"], nd - 0.45, t)
    waddle = math.sin(t * 14.0) * (1 - ss(0.95, 1.0, u)) * (u > 0)
    dv = (d1 - d0).normalized()
    yaw_walk = math.atan2(-dv.x, dv.y) + math.pi
    grab = nd + 0.08                                           # his hands close on it
    if t < grab:
        E.duck.location = d0.lerp(d1, u) + Vector((0, 0, 0.03 * abs(waddle)))
        E.duck.rotation_euler = (0, math.radians(6 * waddle), yaw_walk)
    else:
        hl, hr = P7.P6._noob_hand(N, "sl"), P7.P6._noob_hand(N, "sr")
        lift = ss(grab, nd + 0.65, t)
        E.duck.location = 0.5 * (hl + hr) + Vector((0, 0, -lerp(E._pick_dz, 0.15, lift)))
        fwd = N.root.matrix_world.to_3x3() @ Vector((0, -1, 0))
        yaw_hug = math.atan2(-fwd.x, fwd.y) + math.pi
        dy = (yaw_hug - yaw_walk + math.pi) % (2 * math.pi) - math.pi     # turned round in his hands, the short way
        E.duck.rotation_euler = (math.radians(-10 * math.sin(math.pi * lift)), 0, yaw_walk + dy * lift)
    E.duck.hide_render = t < T["duck"] - 0.05
    for ch in E.duck.children:
        ch.hide_render = E.duck.hide_render
    # ---- Patch: hovering by them, arms folding away, his eye
    pc = E.patch_spot + Vector((0, 0, 0.08 * math.sin(t * 2.6)))
    Pt.root.location = pc
    look_at = lerp(0, 1, ss(T["patch_did"] - 0.2, T["patch_did"] + 0.2, t))
    fwd = Vector((0, -1, 0)).lerp(sun_dir, sit)
    Pt.root.rotation_euler = (0, 0, math.atan2(-fwd.x, fwd.y) + math.pi)
    for o in Pt.col.objects:
        o.hide_render = False
    Pt.beam.hide_render = True
    # his arms go back in: the transformation of part 13, in reverse (pads and guards off, the fingers
    # fold, the forearm folds back, the sleeves slide home, the plates close up into fins again)
    fold = ss(0.2, 2.0, t)
    for side in ("l", "r"):
        Pt.fins[side].rotation_euler = (math.radians(20 * math.sin(t * 12.0) * ss(1.9, 2.3, t)), 0, 0)
    bpy.context.view_layer.update()
    m = Pt.root.matrix_world.copy()
    for side in ("l", "r"):
        P13.chain(E, side, m, *P13.rest_pose(side), 1.0 - fold, sparks=False)
    vals = dict(PD)
    vals.update({"open": 1.0, "smile": ss(T["noob_duck"] + 0.3, T["noob_duck"] + 0.8, t), "wide": 0.0})
    set_patch(Pt, vals)
    E.nglow.data.energy = 0.0


# ------------------------------------------------------------------ the void
def void(E, t):
    from null import null_smile
    import ep10_p9_death as P9
    X = E.X
    X.root.location = VOID_AT
    X.root.scale = (1.6,) * 3
    X.root.rotation_euler = (math.radians(8), 0, math.radians(0.6 * math.sin(t * 0.3)))
    for ob in X.root.children_recursive:
        if ob.type == "MESH" and ob is not X.head:
            ob.hide_render = True
    X.head.hide_render = False
    for o in (getattr(X, "orbit", None), getattr(X, "orbit2", None)):
        if o is not None:
            for ch in o.children_recursive:
                ch.hide_render = True
    # his face: the upset one, lit, flickering as he speaks
    on = ss(T["swim"] + 0.4, T["null_end"] - 0.2, t)
    talking = T["null_end"] <= t < T["null_end_end"]
    fl = 1.0 if not talking else (0.75 + 0.25 * (1 if (t * 21.0) % 1.0 > 0.35 else 0))
    null_smile(on * fl * (1 - 0.7 * ss(T["end"] + 1.2, T["end"] + 2.6, t)))
    P9.null_upset(1.0)
    hc = X.head.matrix_world @ (sum((Vector(v) for v in X.head.bound_box), Vector()) / 8)
    E.null_head_c = hc
    # the pixels: some drift far off; the rest come home to him, slowly, turning
    come = ss(T["swim"] - 1.0, T["end"] + 2.0, t)
    for ob, s, far, d, r0, ph, w in E.void_bits:
        if far:
            p = hc + d * r0 + Vector((math.sin(t * 0.2 + ph), math.cos(t * 0.17 + ph), 0.5 * math.sin(t * 0.13 + ph))) * 2.0
        else:
            r = lerp(r0, 2.6 + 0.4 * math.sin(ph), come ** 0.7)
            a = ph + 0.25 * t
            q = Quaternion(Vector((0, 0, 1)), a)
            p = hc + q @ (d * r)
        ob.location = p
        ob.rotation_euler = tuple(w * (t + ph))
        ob.scale = (s, s, s)
        ob.hide_render = False
    E.void_rim.location = hc + Vector((-9.0, 6.0, 7.0))
    E.void_fill.location = hc + Vector((8.0, -10.0, -3.0))


def hide_void(E):
    for ob, *_ in E.void_bits:
        ob.hide_render = True
    E.void_rim.data.energy = 0.0
    E.void_fill.data.energy = 0.0
    E.X.root.location = (0, 0, -3000.0)
    E.X.root.scale = (0.001,) * 3


# ------------------------------------------------------------------ per frame
def apply(E, t):
    shot = which(t)[0]
    inside = shot == "VOID"
    cast(E, t)
    if inside:
        E.sc.world = E.void_world
        E.W.sun.hide_render = True
        E.void_rim.data.energy = 6000.0
        E.void_fill.data.energy = 2500.0
        void(E, t)
    else:
        E.sc.world = E.respawn_world
        E.W.sun.hide_render = False
        hide_void(E)
    return camera_set(E, t, shot)


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
    E.cam.data.clip_end = 5000
    E.key.location = loc + Vector((0.4, 0.0, 1.2))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    return {"shot": shot}


def camera(E, t, shot):
    hs = P7.P6._head(E.S.face, E.S.holder)
    hn = P7.P6._head(E.N.face)
    pc = E.Pt.root.location.copy()
    mid = 0.5 * (hs + hn)
    t0, t1 = which(t)[1:]
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, T["end"] + 3.0, t)
    if shot == "LAND":
        # wide, gold: down onto the meadow, the island up in the sky behind
        loc = E.ground + Vector((-1.5, -7.5, 1.6))
        return loc, mid + Vector((0, 0, 0.3)), 28, 8.0, None, 0.03, 0.0
    if shot in ("NOOB1", "NOOB2"):
        # the Noob, from past Steve's shoulder side (Steve at the frame's edge)
        loc = hn + Vector((-1.3, -1.0, -0.05))
        return loc, hn + Vector((0.0, 0, -0.05)), 50, 2.4, None, 0.04, 0.0
    if shot == "STEVE1":
        # Steve, deadpan
        loc = hs + Vector((1.3, -1.0, -0.05))
        return loc, hs + Vector((0, 0, -0.05)), 52, 2.4, None, 0.03, 0.0
    if shot == "DUCK":
        # low in the grass: the duck waddling in, the two of them above
        dk = E.duck.location
        loc = dk + Vector((0.3, -1.6, 0.25))
        return loc, dk.lerp(mid, 0.25), 28, 3.0, (dk - loc).length, 0.03, 0.0
    if shot == "HUG":
        # "MY DUCK!": the Noob squeezing it; Steve beside him, smiling despite himself
        m0 = 0.5 * (E.spot["S"] + E.spot["N"]) + Vector((0, 0, 1.25))
        loc = m0 + Vector((0.15, -4.1 + 0.5 * u, -0.25))
        return loc, m0 + Vector((0.0, 0, -0.35 + 0.15 * u)), 30, 4.0, None, 0.04, 0.0
    if shot == "PATCH":
        # Patch, the two of them below him
        loc = pc + Vector((0.4, -1.8, -0.4))
        return loc, pc.lerp(mid, 0.3), 34, 4.0, (pc - loc).length, 0.03, 0.0
    if shot == "SUNSET":
        # sitting on the hill, the sun going down: from the front-side, the gold on them
        loc = mid + Vector((2.6, -2.4, 0.2))
        return loc, mid + Vector((-0.2, 0, -0.35)), 35, 5.0, None, 0.02, 0.0
    if shot == "DRIFT":
        # away from them: up and out, over the world, toward the sky's edge
        a = mid + Vector((2.6, -2.4, 0.2))
        b = mid + Vector((30.0, -60.0, 34.0))
        loc = a.lerp(b, u ** 1.6) + Vector((0, 0, 9.0 * math.sin(0.5 * math.pi * u)))
        return loc, mid.lerp(mid + Vector((40, -120, -20)), u), lerp(35, 24, u), 8.0, None, 0.0, 6.0 * u
    # VOID: swimming through the dark, past drifting pixels, to his head
    hc = getattr(E, "null_head_c", VOID_AT + Vector((0, 0, 14)))
    path0 = hc + Vector((-14.0, -26.0, 5.0))
    path1 = hc + Vector((-2.0, -17.0, 1.0))
    k = ss(0.0, 1.0, u) ** 0.8
    loc = path0.lerp(path1, k) + Vector((0.6 * math.sin(t * 0.7), 0.0, 0.4 * math.sin(t * 0.55)))
    return loc, hc + Vector((0, 0, -0.3)), lerp(28, 36, k), 4.0, (hc - loc).length, 0.0, 3.0 * math.sin(t * 0.4)


# ------------------------------------------------------------------ the look
def finish(path, mist_path, shot, t):
    import numpy as np
    from PIL import Image
    P4.finish(path, mist_path)
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, np.float32) / 255.0
    if shot == "DRIFT":                                         # into the void: the gold goes dark
        k = ss(T["swim"] - 0.9, T["swim"], t)
        a = a * (1 - k) + np.array([0.012, 0.004, 0.022], np.float32) * k
    if shot == "VOID":
        k = 1 - ss(T["swim"], T["swim"] + 0.8, t)               # out of the dark
        k2 = ss(T["end"] + 1.0, T["end"] + 2.8, t)             # and back into it, under the card
        a = a * (1 - max(k, 0.8 * k2))
        if T["null_end"] - 0.3 <= t < T["null_end"] - 0.05 or T["null_end_end"] <= t < T["null_end_end"] + 0.3:
            sh = 6
            a[:, :, 0] = np.roll(a[:, :, 0], sh, 1)
            a[:, :, 2] = np.roll(a[:, :, 2], -sh, 1)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    for k in ("land", "noob_back", "steve_jumped", "noob_bridge", "duck", "noob_duck", "patch_did", "sunset",
              "steve_null", "noob_void", "swim", "end"):
        if k in b:
            T[k] = b[k][0]
    if "null_end" in b:
        T["null_end"], T["null_end_end"] = b["null_end"]
    if b:
        T["length"] = tl["length"] + 0.2


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
    tl = {"length": T["length"] - 0.2, "beats": {}, "lines": []} if a.timeline == "-" else json.load(open(a.timeline))
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
        t = (f - 1) / FPS
        sc.frame_set(f)
        look = apply(E, t)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        finish(dst, cand[-1] if cand else "", look["shot"], t)
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
