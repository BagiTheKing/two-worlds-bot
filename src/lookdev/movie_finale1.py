"""The movie's FINALE 1/5 (16:9): the published finale parts 1-3 in one landscape chapter, on the chapter sound
(movie/finale1, made by tools/movie_finale1_join.py). Shot list: story/movie/finale1_shots.md.

  P1 (0 - 7.08 s)  ep10_entrance's choreography as published; the cameras reframed for 16:9; the storm rolls in
                   over the first second out of Ep8's indigo twilight (Ep8 hard-cuts into frame 1); Steve, the Noob
                   and Patch stand in front of the portal from frame 1 (seen in the wide shot).
  P2 (7.08 - 13.6) ep10_p2_omg's choreography as published, reframed; the Noob's head shader and rim fixed.
  P3 (13.6 - 27.1) re-staged on the creator's notes (2026-11-27): breathing in the frozen two-shot, the Noob's arm
                   down in a hunched guard, Patch bobbing and glancing up at Null; a close-up of the Noob on "What's
                   the signal?"; a 1.2 s slow-motion shock beat (Null's grin looming, debris hanging); Steve's "RUN!"
                   hard-cut into the sprint; no pickaxe; a fill that runs with them (no lighting cliff); no erased
                   ground (the pink slab); the Noob leaning into the run, arms pumping, a glance back; Patch dimmed
                   (his screen reads) and banking right with the Noob; the overhead split held longer; Null's head
                   flicks to Steve, snaps to the Noob; a wide shot of Null banking down the right path after him.

    python src/lookdev/movie_finale1.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--samples 32]
        [--times 0.4,2.6] [--list]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_entrance as EN                                         # noqa: E402
import ep10_p2_omg as P2                                           # noqa: E402
import ep10_p3_run as P3                                           # noqa: E402
from ep10_entrance import FPS, PORTAL_AT, lerp, ss                  # noqa: E402

STEVE_AT, NOOB_AT, FORK = P2.STEVE_AT, P2.NOOB_AT, P3.FORK
EN.EXTRA_KEEP.extend([(-3.0, -45.5, 4.0), (12.0, -17.5, 4.0)])      # the new cameras (the bank shot, P1's wide)
EN.EXTRA_CLEAR.extend([(12.0, -17.3, 3.0), (-7.0, -27.0, 3.5), (7.5, -27.0, 3.5), (-9.5, -32.0, 3.5), (10.0, -32.0, 3.5)])  # the two paths
SPEED = 3.6
OFF = {"p1": 0.0, "p2": 7.084, "p3": 13.601}
LENGTH = 27.519
T3 = {"freeze": 0.0, "steve_signal": 0.4, "noob_signal": 2.37, "shock": 3.644, "steve_run": 4.844, "run": 5.618,
      "fork": 7.718, "null_look": 9.818, "null_bank": 11.418, "end": 13.018}
TWILIGHT = {"glow": (150, 140, 220), "power": 2.2, "horizon": (96, 58, 138), "mid": (26, 26, 62), "zenith": (7, 11, 26),
            "fill": 0.2, "fill_col": (110, 100, 190)}             # Ep8's last look (#070B1A), violet at the horizon
STORM = {"glow": (214, 196, 255), "power": 6.0, "horizon": (176, 96, 180), "mid": (84, 52, 132), "zenith": (22, 14, 48),
         "fill": 0.32, "fill_col": (150, 120, 210)}


def go():
    """The hard cut into the sprint: 0.3 s into 'RUN!'."""
    return T3["steve_run"] + 0.3


# ------------------------------------------------------------------ build
def build(tl, assets, res, samples):
    p3 = next(p for p in tl["parts"] if p["id"] == "p3")["timeline"]
    E = P3.build(p3, assets, res, samples)
    sc = E.sc
    sc.render.resolution_x = res * 16 // 9                      # the movie: landscape
    sc.render.resolution_y = res
    # no pickaxe: it was erased in Ep6 (the creator: Steve runs empty-handed)
    for ob in bpy.data.objects:
        if ob.name.startswith("item_"):
            ob.hide_render = True
            ob.hide_viewport = True
        if ob.type == "LIGHT" and ob.data.type == "AREA":       # lights light, they are never seen
            ob.visible_camera = False
    # the Noob's skin: no blown-out, faceted highlights (rougher, less specular, smooth shading on the head)
    for m in bpy.data.materials:
        if m.name.startswith("noob_") and m.node_tree and "Principled BSDF" in m.node_tree.nodes:
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Roughness"].default_value = max(0.58, b.inputs["Roughness"].default_value)
            b.inputs["Specular IOR Level"].default_value = 0.25
            if "Coat Weight" in b.inputs:
                b.inputs["Coat Weight"].default_value = min(0.08, b.inputs["Coat Weight"].default_value)
    hm = E.N.head_mesh
    for p in hm.data.polygons:
        p.use_smooth = True
    try:
        bpy.ops.object.select_all(action="DESELECT")
        hm.select_set(True)
        bpy.context.view_layer.objects.active = hm
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception as e:                                       # older Blender: weighted normals do it
        print("smooth by angle:", e)
    if not any(md.type == "WEIGHTED_NORMAL" for md in hm.modifiers):
        wn = hm.modifiers.new("wnormal", "WEIGHTED_NORMAL")
        wn.keep_sharp = True
    # Patch's casing: a gain on its colour, so he can be dimmed (his cyan screen must read while he flies)
    sh = bpy.data.materials.get("patch_shell")
    if sh:
        nt = sh.node_tree
        b = nt.nodes["Principled BSDF"]
        src = b.inputs["Base Color"].links[0].from_socket
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs[0].default_value = 1.0
        nt.links.new(src, mx.inputs[6])
        mx.inputs[7].default_value = (1, 1, 1, 1)
        nt.links.new(mx.outputs[2], b.inputs["Base Color"])
        E.shell_gain = mx.inputs[7]
        print("patch shell gain node on", sh.name)
    else:
        E.shell_gain = None
    # a soft fill that runs with them (the creator: no lighting cliff on the sprint)
    L = bpy.data.lights.new("run_fill", "AREA")
    L.shape, L.size, L.size_y = "RECTANGLE", 9.0, 4.0
    L.color, L.energy = (0.78, 0.66, 1.0), 0.0
    E.run_fill = bpy.data.objects.new("run_fill", L)
    E.run_fill.visible_camera = False
    sc.collection.objects.link(E.run_fill)
    E.base = {"null_key": E.null_key.data.energy, "cold_rim": E.cold_rim.data.energy,
              "face_fill": E.face_fill.data.energy, "key": 900.0, "rim": E.rim.data.energy}
    return E


# ---------------------------------------------------------------- helpers
def centre(ob, m=None):
    c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
    return (m @ ob.matrix_world @ c) if m is not None else ob.matrix_world @ c


def set_cam(E, loc, look, lens, fstop, focus, roll=0.0, yaw=0.0, pitch=0.0):
    q = (look - loc).to_track_quat("-Z", "Y")
    q = q @ Quaternion((0, 1, 0), math.radians(yaw)) @ Quaternion((1, 0, 0), math.radians(pitch)) \
        @ Quaternion((0, 0, 1), math.radians(roll))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop


def lights(E, **k):
    """The part's light levels (fractions of the build's)."""
    for name in ("null_key", "cold_rim", "face_fill", "key", "rim"):
        ob = {"null_key": E.null_key, "cold_rim": E.cold_rim, "face_fill": E.face_fill, "key": E.key, "rim": E.rim}[name]
        ob.data.energy = E.base[name] * k.get(name, 1.0)


def patch_idle(E, t, look_up=0.0, look_x=0.0):
    """Patch hovering just behind them, between their heads: a subtle bob, his eye on Null now and then."""
    from patch import DEFAULTS as PD, set_patch
    Pt = E.Pt
    Pt.root.location = Vector((0.05 + 0.04 * math.sin(t * 1.7), STEVE_AT.y - 0.7, 2.35 + 0.06 * math.sin(t * 3.1)))
    Pt.root.rotation_euler = (math.radians(3 * math.sin(t * 2.3)), math.radians(2.5 * math.sin(t * 1.9)), math.radians(180))
    pf = dict(PD)
    pf.update({"wide": 1.0, "look_y": look_up, "look_x": look_x})
    set_patch(Pt, pf)
    for side, pv in Pt.fins.items():
        pv.rotation_euler = (math.radians(6 * math.sin(2 * math.pi * 5.0 * t)) * (1 if side == "l" else -1), 0, 0)
    if E.shell_gain is not None:
        E.shell_gain.default_value = (1, 1, 1, 1)


def breath(t, seed=0.0, rate=2.3):
    """Panic breathing: quick, shallow, a little irregular (degrees, about 1.4 at most)."""
    return 1.0 * math.sin(2 * math.pi * rate * t + seed) + 0.4 * math.sin(2 * math.pi * 3.7 * t + 1.3 * seed)


# ---------------------------------------------------------------- part 1
def apply_p1(E, u):
    # Steve and the Noob already stand in front of the portal (Ep8 ends on them), frozen as part 2 opens
    P2.apply(E, 0.0)
    EN.apply(E, u)
    # the storm arrives over the first second, out of Ep8's twilight (nothing appears from nowhere)
    from world import set_sky
    k = ss(0.0, 1.3, u)
    sky = {key: (tuple(lerp(a, b, k) for a, b in zip(TWILIGHT[key], STORM[key])) if isinstance(TWILIGHT[key], tuple)
                 else lerp(TWILIGHT[key], STORM[key], k)) for key in STORM}
    set_sky(E.W, sky)
    flash = math.exp(-max(0.0, u - EN.T["rip"]) / 0.12) if u >= EN.T["rip"] else 0.0
    flash = max(flash, 0.7 * math.exp(-max(0.0, u - EN.T["hi"]) / 0.1) if u >= EN.T["hi"] else 0.0)
    E.W.sky_pow.inputs[1].default_value = sky["power"] * (1 + 1.6 * flash)
    lights(E, null_key=0.0, cold_rim=0.0, face_fill=0.0)          # part 1's own light, as published
    E.key.data.energy = 900.0
    patch_idle(E, u + 13.0, look_up=0.4)
    # the cameras, reframed for 16:9
    T = EN.T
    loc, look, lens, fstop, focus = EN.camera(u)
    if u < T["s2"]:
        lens *= 0.62
    elif u < T["s3"]:
        lens *= 0.7
    elif u >= T["s4"]:                                       # the wide: further back, his whole height in frame
        w = ss(T["s4"], T["s4"] + 1.65, u)
        loc = PORTAL_AT + Vector((12.5 - 0.8 * w, -22.0 - 0.6 * w, 2.4))      # from the front-right, low: Steve
        look = (PORTAL_AT + Vector((-1.0, -4.0, 4.5))).lerp(PORTAL_AT + Vector((-1.0, -4.0, 9.5)), ss(0.0, 0.9, w))
        lens = 16.0                                             # and the Noob under him, the whole of him above
    else:
        lens *= 0.66
    off, roll_ = EN.shake(u, EN.trauma(u))
    set_cam(E, loc + off, look, lens, fstop, focus)
    E.cam.rotation_quaternion = E.cam.rotation_quaternion @ Quaternion((0, 0, 1), roll_)
    E.key.location = loc + Vector((-1.6, 0.4, 2.2))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------- part 2
def apply_p2(E, u):
    P2.apply(E, u)
    patch_idle(E, u + 20.0, look_up=0.5)
    noob_cu = u >= P2.T["noob"]
    lights(E, null_key=0.65 if noob_cu else 1.0, key=0.0)          # the rim down ~35% on the Noob's face
    hs = centre(E.S.face, E.S.holder.matrix_world)
    hn = centre(E.N.head_mesh)
    loc, look, lens, fstop, focus, hand, rum = P2.camera(u, hs, hn)
    if u < P2.T["legs"]:                                     # A: his face, the night and the rift beside him
        lens *= 0.7
    elif not noob_cu:                                        # B: his feet
        lens *= 0.66
    else:                                                    # C: the Noob's face
        lens *= 0.7
    y1, p1, r1 = P2.handheld(u, hand)
    y2, p2, r2 = P2.rumble(u, rum)
    set_cam(E, loc, look, lens, fstop, focus, roll=r1 + r2, yaw=y1 + y2, pitch=p1 + p2)


# ---------------------------------------------------------------- part 3
def run_y(t):
    """How far they have run (m, toward -y): the cut lands on them at full speed."""
    if t < go():
        return 0.0
    return -SPEED * (t - go() + 0.25)


def split(t):
    return ss(T3["fork"] + 0.35, T3["fork"] + 1.35, t)


def runner_x(t, side):
    """Across the path: they break apart round the boulder, then the two paths keep diverging."""
    sp = split(t)
    past = max(0.0, t - T3["fork"] - 1.35)
    return side * (5.5 * sp ** 1.3 + 1.1 * past)


def null_state(t):
    """-> neck position, scale, lean (deg), yaw (deg), head yaw (deg), head pitch (deg), grin"""
    k = 1.6
    base = PORTAL_AT + Vector((0.0, -2.4, 17.0))
    if t < go():
        return base, k, 8.0, 0.0, 0.0, 0.0, 0.0
    chase = min(t, T3["null_look"]) - go()
    y = -2.4 - 3.4 * chase
    look = t - T3["null_look"]
    if look >= 0:
        y -= 1.2 * ss(0, 0.4, look)                           # he pulls up at the fork
    n = PORTAL_AT + Vector((0.0, y, 17.0 - 2.0 * ss(go(), go() + 1.5, t)))
    lean = 8 + 22 * ss(go(), go() + 1.0, t)
    head, pitch, grin, yaw = 0.0, 0.0, 0.0, 0.0
    if look >= 0:
        pitch = 24 * ss(0.0, 0.25, look)                      # looking straight down at the fork

        def snap(at, a, b, dur=0.1):
            q = (look - at) / dur
            if q <= 0:
                return a
            if q >= 1:
                return b
            return a + (b - a) * (0.15 if q < 0.33 else 0.85 if q < 0.66 else 1.0)    # stepped: it skips frames
        head = snap(0.3, 0.0, -48.0, 0.12)                    # a flick left: where Steve went (-x)
        head = snap(0.72, head, 62.0, 0.08)                   # held 0.4 s, then snapped right: the Noob (+x)
        grin = ss(0.85, 1.1, look)
    bank = ss(T3["null_bank"] - 0.3, T3["null_bank"] + 1.4, t)
    if bank > 0:                                              # he banks down the right-hand path, after the Noob
        yaw = 38 * bank
        head = lerp(head, 22, bank)
        pitch = lerp(pitch, 14, bank)
        n = n + Vector((7.5 * bank ** 1.2, -7.0 * bank, -2.0 * bank))
        lean = lerp(lean, 38, bank)
    return n, k, lean, yaw, head, pitch, grin


def cam3(t, hs, hn, hx, mid):
    """-> loc, look, lens, fstop, focus, handheld, rumble"""
    if t < T3["noob_signal"] - 0.02:                         # a: the frozen two-shot, a slow creep in
        u = ss(0, T3["noob_signal"], t)
        loc = Vector((0.15 - 0.1 * u, -0.2 - 0.55 * u, 1.35 + 0.05 * u))
        look = Vector((0.05, -4.0, 1.85))
        return loc, look, 21 + 2 * u, 3.2, None, 0.45, 0.06
    if t < T3["shock"]:                                      # b: close on the Noob: "What's the signal?"
        u = ss(T3["noob_signal"], T3["shock"], t)
        loc = hn + Vector((0.95 - 0.1 * u, 1.25 - 0.12 * u, -0.22))
        look = hn + Vector((0.0, 0.0, 0.02))
        return loc, look, 34 + 4 * u + 8 * P2.crash(t, T3["noob_signal"] + 0.05, 0.18), 1.6, None, 0.6, 0.1
    if t < T3["steve_run"] - 0.25:                           # c: the shock: up at his grin, the world hanging still
        u = ss(T3["shock"], T3["steve_run"] - 0.25, t)
        loc = Vector((0.3, -3.2 + 0.25 * u, 1.2))
        n = null_state(t)[0]
        look = n + Vector((0.0, -1.2, 4.0 - 0.3 * u))
        return loc, look, 20 + 5 * u, 6.0, None, 0.25, 0.02
    if t < go():                                             # d: close on Steve: his eyes slide; RUN!
        loc = hs + Vector((-1.0, 1.0, -0.28))
        look = hs + Vector((0.0, 0.0, 0.05))
        lens = 30 + 16 * P2.crash(t, T3["steve_run"] + 0.04)
        rum = 0.06 + 0.7 * math.exp(-((t - T3["steve_run"] - 0.1) / 0.12) ** 2)
        return loc, look, lens, 1.6, None, 0.5, rum
    if t < T3["fork"]:                                       # e: full speed, running at us
        ry = run_y(t)
        loc = Vector((0.2, max(STEVE_AT.y + ry - 4.6, FORK.y + 3.8), 1.0))
        look = Vector((0.0, STEVE_AT.y + ry + 8.0, 3.2))
        return loc, look, 18, 5.0, (loc - mid).length, 0.8, 0.18
    if t < T3["null_look"]:                                  # f: high and steep, the split, held (nothing hides them)
        u = ss(T3["fork"], T3["null_look"], t)
        loc = Vector((0.0, -30.0 + 0.6 * u, 17.5 - 0.5 * u))
        look = Vector((0.0, -18.0 - 3.0 * u, 0.5))
        return loc, look, 20, 14.0, None, 0.3, 0.06
    if t < T3["null_bank"]:                                  # g: up at his face as he looks down: left, then right
        u = ss(T3["null_look"], T3["null_bank"], t)
        look = hx if hx is not None else null_state(t)[0] + Vector((0, -1.2, 4.6))
        loc = look + Vector((6.5 - 0.4 * u, -14.0 + 0.6 * u, -11.0))       # on the Noob's side: the grin snaps to us
        lt = t - T3["null_look"]
        lens = 22 + 5 * ss(0.72, 0.85, lt)
        rum = 0.12 + 0.45 * math.exp(-((lt - 0.32) / 0.06) ** 2) + 0.7 * math.exp(-((lt - 0.74) / 0.06) ** 2)
        return loc, look, lens, 8.0, None, 0.5, rum
    u = ss(T3["null_bank"], T3["end"] + 0.5, t)             # h: wide, low, from ahead: he banks after the Noob
    loc = Vector((-3.5 + 0.8 * u, -46.0 + 1.0 * u, 4.6))   # (right of frame); Steve, ignored, on the left path
    look = Vector((2.5, -27.0, 6.5 + 0.5 * u))
    return loc, look, 19, 16.0, None, 0.4, 0.15 + 0.1 * u


def apply_p3(E, t):
    from pose import pose
    from noob import pose_noob, NOOB_POSES
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from patch import DEFAULTS as PD, set_patch
    from world import fx_set
    from ep09_new import flat, unflat, talk, SF, NF
    slow = T3["shock"] <= t < T3["steve_run"] - 0.25
    tt = T3["shock"] + 0.2 * (t - T3["shock"]) if slow else t           # the world's own clock (slow motion)
    EN.apply(E, EN.T["s4"] + 2.0 + tt)
    S, N, Pt, G = E.S, E.N, E.Pt, E.G
    running = t >= go()
    ry = run_y(t)
    # ------------------------------------------------ Null
    n, k, lean, yaw, head, pitch, grin = null_state(t)
    from mathutils import Matrix
    rot = Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(lean), 3, "X")
    G.root.scale = (k, k, k)
    G.root.rotation_euler = rot.to_euler()
    G.root.location = n - rot @ (Vector((0, -0.35, 9.25)) * k)
    G.neck.rotation_euler = (math.radians(pitch), 0.0, math.radians(head))
    reach = ss(go(), go() + 0.8, t)
    drop = ss(T3["null_look"] - 0.2, T3["null_look"] + 0.25, t) * (1 - ss(T3["null_bank"] - 0.3, T3["null_bank"] + 0.3, t))
    for side, sgn in (("sl", 1), ("sr", -1)):
        fwd = lerp(lerp(-40, -78, reach), -18, drop)
        out = lerp(lerp(16, 8, reach), 38, drop)
        G.arms[side].rotation_euler = (math.radians(fwd), math.radians(sgn * out), 0)
    if slow:                                                 # the shock: the grin creeps wider
        grin = 0.35 * ss(T3["shock"], T3["steve_run"], t)
    EN.draw_face(E.face_im, smile=1.0, eyes=1.0, wide=grin, open_=0.35 * grin)
    fx_set(E.W, R=1e5, Wd=100.0, Cx=0.0, Cy=0.0, D=0.0, Nx=0.0, Ny=60.0, Dz=-1.0)   # no erased ground (the pink slab)
    # ------------------------------------------------ Steve
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    sp = flat(lib["idle (Benly 2.2)"])
    if not running:
        b = breath(t, 0.0)
        frozen = {"chest_lean": -5 + 1.4 * b, "head_nod": -20 + 0.9 * b, "hips_drop": 0.18 + 0.004 * b,
                  "chest_side": 1.2 * math.sin(t * 0.9),
                  "arm_sl": {"out": 18 + 1.5 * b, "fwd": 12, "elbow": 30}, "arm_sr": {"out": 16 + 1.5 * b, "fwd": 9, "elbow": 34},
                  "foot_sr": {"y": 0.7, "yaw": 10}, "foot_sl": {"y": 0.1}}
        if t >= T3["steve_run"] - 0.25:                     # RUN!: the shout throws him forward
            kk = ss(T3["steve_run"] - 0.05, T3["steve_run"] + 0.2, t)
            frozen.update({"chest_lean": lerp(frozen["chest_lean"], 10, kk), "head_nod": lerp(-20, -6, kk)})
        for kk_, v in flat(frozen).items():
            sp[kk_] = v
        sx, sy, syaw, bob = STEVE_AT.x, STEVE_AT.y, 180.0, 0.0
    else:
        ph = 2 * math.pi * 2.9 * (t - go()) + 0.6
        sw = math.sin(ph)
        sp = flat({"chest_lean": 18, "chest_twist": 10 * sw, "head_nod": -8, "hips_drop": 0.16 + 0.05 * abs(math.cos(ph)),
                   "arm_sl": {"fwd": -60 * sw, "elbow": 88, "out": 8}, "arm_sr": {"fwd": 60 * sw, "elbow": 88, "out": 8},
                   "foot_sl": {"y": -0.55 * sw, "z": max(0.0, 0.5 * math.sin(ph + 1.2))},
                   "foot_sr": {"y": 0.55 * sw, "z": max(0.0, 0.5 * math.sin(ph + 1.2 + math.pi))}})
        s_ = split(t)
        syaw = -28 * ss(0.0, 0.5, s_) * (1 - ss(0.6, 1.0, s_)) - 12 * ss(T3["fork"] + 1.35, T3["fork"] + 1.8, t)
        sx, sy, bob = STEVE_AT.x + runner_x(t, -1), STEVE_AT.y + ry, 0.07 * abs(math.sin(ph))
    pose(S.arm, unflat(sp))
    S.holder.hide_render = False
    S.holder.location = (sx, sy, bob)
    S.holder.rotation_euler = (0, 0, math.radians(syaw))
    fs = {f"{e}_{kk_}": v for e in EYES for kk_, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    sf = dict(SF["scared"]) if t >= T3["steve_run"] - 0.25 else {"both_to": 0.36, "both_tm": 0.4, "both_ti": 0.3, "both_ps": 0.62,
                                                                 "both_py": 0.45, "bb_raise": 0.6, "bb_tilt": -0.7}
    if T3["steve_run"] - 0.3 <= t < T3["steve_run"] + 0.1:   # his eyes slide to the Noob, then the shout
        sf["both_px"] = 0.55 * ss(T3["steve_run"] - 0.3, T3["steve_run"] - 0.1, t)
        sf["both_py"] = 0.15
    for kk_, v in sf.items():
        if kk_.startswith("both_"):
            for e in EYES:
                fs[f"{e}_{kk_[5:]}"] = v
        elif not kk_.startswith("bb_"):
            fs[kk_] = v
    mo = E.mouth.get("steve", {}).get(int(round(t * FPS)))
    if mo and t < T3["shock"]:                               # a whisper through his teeth
        mo = dict(mo, m_o=mo["m_o"] * 0.45)
    talk(fs, mo)
    set_face(S.face, fs)
    for ob_ in S.brows.values():
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(S.brows, {kk_: v for kk_, v in sf.items() if kk_.startswith("bb_")})
    # ------------------------------------------------ the Noob
    if not running:
        b = breath(t, 1.7, 2.6)
        npz = flat(NOOB_POSES["scared"])
        # a nervous hunched guard: both arms in, low in front of his chest (not one arm held straight out)
        npz.update({"head_nod": -24 + 1.2 * b, "head_tilt": 4, "chest_lean": 9 + 1.6 * b,
                    "arm_sl.fwd": 32 + 2.0 * b, "arm_sl.out": -16, "arm_sr.fwd": 26 + 2.0 * b, "arm_sr.out": -14,
                    "chest_side": 1.0 * math.sin(t * 1.1 + 0.5)})
        if T3["noob_signal"] - 0.1 <= t < T3["shock"]:       # he leans to Steve to whisper
            w = ss(T3["noob_signal"] - 0.1, T3["noob_signal"] + 0.3, t)
            npz["head_turn"] = -14 * w
            npz["arm_sl.fwd"] += 8 * w
        nyaw, nx, ny, nbob, npitch = 180.0, NOOB_AT.x, NOOB_AT.y, 0.0, 0.0
    else:
        ph = 2 * math.pi * 2.9 * (t - go()) + 0.9 + math.pi
        sw = math.sin(ph)
        # leaning into it like Steve: spine forward ~14 degrees, arms pumping from a forward bend (his arms are
        # rigid Roblox blocks: the bend is in the swing, short and forward), a panicked glance back at Null
        glance = ss(go() + 1.0, go() + 1.25, t) * (1 - ss(go() + 1.7, go() + 1.95, t))
        npz = {"chest_lean": 22, "head_nod": -12, "head_turn": 70 * glance, "chest_twist": 8 * sw + 18 * glance,
               "arm_sl.fwd": 38 - 42 * sw, "arm_sl.out": 6, "arm_sr.fwd": 38 + 42 * sw, "arm_sr.out": 6,
               "leg_sl.fwd": 50 * sw, "leg_sr.fwd": -50 * sw}
        s_ = split(t)
        nyaw = 26 * ss(0.0, 0.5, s_) * (1 - ss(0.6, 1.0, s_)) + 12 * ss(T3["fork"] + 1.35, T3["fork"] + 1.8, t)
        nx, ny, nbob, npitch = NOOB_AT.x + runner_x(t, 1), NOOB_AT.y + ry, 0.08 * abs(math.sin(ph)), 10.0
    npz["root_yaw"] = nyaw
    pose_noob(N, unflat(npz))
    N.root.location = (nx, ny, nbob)
    if npitch:                                               # the whole body tipped into the run (from the feet)
        N.root.rotation_euler = (math.radians(-npitch), 0, math.radians(nyaw))
    fn = {f"{e}_{kk_}": v for e in NOOB_EYES for kk_, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    nf = dict(NF["scared"])
    nf.update({"both_py": 0.42})
    if T3["noob_signal"] - 0.1 <= t < T3["shock"]:
        nf.update({"both_px": -0.5, "both_py": 0.1})
    if running:
        nf = dict(NF["shout"])
    for kk_, v in nf.items():
        if kk_.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{kk_[5:]}"] = v
        else:
            fn[kk_] = v
    mo = E.mouth.get("noob", {}).get(int(round(t * FPS)))
    if mo:
        mo = dict(mo, m_o=mo["m_o"] * 0.8)
    talk(fn, mo)
    set_face(N.face, fn)
    # ------------------------------------------------ Patch
    if not running:
        dart = ss(0.9, 1.1, t) * (1 - ss(1.6, 1.8, t)) + ss(3.0, 3.15, t)     # his eye darts up to Null
        patch_idle(E, t, look_up=lerp(0.1, 0.85, min(1.0, dart)), look_x=0.15 * math.sin(t * 2.0))
    else:
        s_ = split(t)
        mid_x = lerp(0.0, NOOB_AT.x + runner_x(t, 1) - 0.4, s_)            # torn between them, then with the Noob
        pp = Vector((mid_x + 0.3 * math.sin(t * 3), STEVE_AT.y + ry + 0.9, 2.3 + 0.1 * math.sin(t * 9) + 0.6 * s_))
        Pt.root.location = pp
        bankr = 28 * ss(T3["fork"] + 0.3, T3["fork"] + 0.8, t) * (1 - 0.5 * ss(T3["fork"] + 1.4, T3["fork"] + 1.9, t))
        Pt.root.rotation_euler = (math.radians(14), math.radians(-bankr), math.radians(-20 * s_))   # facing where he flies
        pf = dict(PD)
        pf.update({"wide": 0.8, "squint": 0.0, "look_y": -0.2, "look_x": -0.6 * s_})        # glancing back at Steve
        set_patch(Pt, pf)
        for side, pv in Pt.fins.items():
            pv.rotation_euler = (math.radians(30 * math.sin(2 * math.pi * 5.0 * t)) * (1 if side == "l" else -1), 0, 0)
        if E.shell_gain is not None:                         # his casing down, so his screen reads (no white blob)
            E.shell_gain.default_value = (0.4, 0.4, 0.45, 1)
    # ------------------------------------------------ light
    lights(E, key=0.0, null_key=0.65 if T3["noob_signal"] - 0.02 <= t < T3["shock"] else 1.0)
    mid = Vector(((sx + nx) / 2, (sy + ny) / 2, 1.2))
    if running:                                              # the fill runs with them, ahead and above
        E.run_fill.location = mid + Vector((0.0, -4.5, 4.2))
        E.run_fill.rotation_euler = (mid + Vector((0, 0, 0.4)) - E.run_fill.location).to_track_quat("-Z", "Y").to_euler()
        E.run_fill.data.energy = 2600.0 * (1 - ss(T3["fork"] - 0.05, T3["fork"], t))   # softer from above
        E.run_fill.data.size = 9.0 + 6.0 * split(t)
        E.cold_rim.location = mid + Vector((0.4, -4.5, 3.4))   # the cold rim keeps up with them too
    else:
        E.run_fill.data.energy = 0.0
        E.cold_rim.location = STEVE_AT + Vector((0.4, -4.5, 3.4))
    # ------------------------------------------------ the camera
    bpy.context.view_layer.update()
    hs = centre(S.face, S.holder.matrix_world)
    hn = centre(N.head_mesh)
    hx = centre(G.head)
    loc, look, lens, fstop, focus, hand, rum = cam3(t, hs, hn, hx, mid)
    y1, p1, r1 = P2.handheld(tt, hand)
    y2, p2, r2 = P2.rumble(tt, rum)
    set_cam(E, loc, look, lens, fstop, focus, roll=r1 + r2, yaw=y1 + y2, pitch=p1 + p2)
    E.face_fill.location = loc + Vector((0, 0, 0.9))
    aim = mid if running else look
    E.face_fill.rotation_euler = (aim - E.face_fill.location).to_track_quat("-Z", "Y").to_euler()
    E.sc.render.motion_blur_shutter = 0.15 if slow else 0.5
    # the specks hanging in the air around the lens, at a crawl, in the shock
    c_ = loc + (look - loc).normalized() * 2.6
    for ob in E.dust:
        ob.hide_render = not slow
        if ob.hide_render:
            continue
        el = 0.2 * (t - T3["shock"])
        o, v, w = Vector(ob["off"]), Vector(ob["vel"]), Vector(ob["spin"])
        ob.location = c_ + o * 1.4 + v * el * 4.0
        ob.rotation_euler = tuple(w * el * 3.0)
        z = ob["size"]
        ob.scale = (z, z, z)


# ------------------------------------------------------------ apply a frame
def apply(E, t):
    if E.shell_gain is not None:
        E.shell_gain.default_value = (1, 1, 1, 1)
    for ob in E.dust:
        ob.hide_render = True
    E.run_fill.data.energy = 0.0
    E.S.holder.hide_render = False
    E.sc.render.motion_blur_shutter = 0.5
    if t < OFF["p2"]:
        apply_p1(E, t - OFF["p1"])
    elif t < OFF["p3"]:
        apply_p2(E, t - OFF["p2"])
    else:
        apply_p3(E, t - OFF["p3"])


# ------------------------------------------------------------------ main
def align(tl, voice_path, tmp):
    """Each part's own clock from its own timeline (the chapter's "parts"); the voices cut per part for the
    lip sync and the word finding the parts do."""
    global LENGTH
    import soundfile as sf
    parts = {p["id"]: p for p in tl["parts"]}
    for k in OFF:
        OFF[k] = parts[k]["offset"]
    v, sr = (sf.read(voice_path) if voice_path and os.path.exists(voice_path) else (None, 48000))
    if v is not None and v.ndim > 1:
        v = v.mean(axis=1)
    paths = {}
    for k, p in parts.items():
        if v is None:
            paths[k] = None
            continue
        a = int(round(p["offset"] * sr))
        b = a + int(round((p["length"] + 0.4) * sr))
        paths[k] = os.path.join(tmp, f"_voice_{k}.wav")
        sf.write(paths[k], v[a:b], sr)
    EN.align(parts["p1"]["timeline"], paths["p1"])
    env = P2.align(parts["p2"]["timeline"], paths["p2"])
    b3 = parts["p3"]["timeline"]["beats"]
    for k in T3:
        if k in b3:
            T3[k] = b3[k][0]
    LENGTH = tl["length"] + 0.4
    return env, paths


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
    tl = json.load(open(a.timeline))
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    n_frames = int(round((tl["length"] + 0.4) * FPS)) + 1
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    import tempfile
    env, vp = align(tl, a.voice, tempfile.mkdtemp())
    E = build(tl, a.assets, a.res, a.samples)
    E.env = env or (lambda t: 0.7)
    E.mouth, E.noob_mouth = {}, {}
    from ep09_new import _lipsync
    if vp.get("p2"):
        t2 = next(p for p in tl["parts"] if p["id"] == "p2")["timeline"]
        E.noob_mouth = _lipsync({"length": t2["length"], "lines": [ln for ln in t2["lines"] if ln["who"] == "noob"]},
                                vp["p2"]).get("noob", {})
    if vp.get("p3"):
        E.mouth = _lipsync(next(p for p in tl["parts"] if p["id"] == "p3")["timeline"], vp["p3"])
    sc = E.sc
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
