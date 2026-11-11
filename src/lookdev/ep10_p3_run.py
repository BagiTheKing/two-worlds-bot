"""Episode 10, part 3: "RUN!" (about 13 s): from reaction to action.

  a  Frozen, from the side, Null towering over them, Patch hovering behind:
     STEVE (a whisper through his teeth): "On my signal... we split."
     NOOB (whispering back): "What's the signal?"
  b  Close on Steve: his eyes slide to the Noob. "RUN!" (a crash zoom).
  c  Slow motion, total silence, a heartbeat: Steve turns away from Null; the
     Noob turns; then through Steve's eyes, the view swings from Null's face
     to the path out of the forest.
  d  Full speed: running at the camera, the world erasing behind them, Null
     following, Patch flying with them.
  e  High and wide: the path forks around a big oak. Steve breaks left, the
     Noob right, Patch shoots up.
  f  Null reaches the fork. His head snaps left, glitching, then right. His
     grin widens, and he goes after the Noob, the one he is made of.

    python src/lookdev/ep10_p3_run.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080]
        [--samples 32] [--times 0.4,2.6]
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_entrance as EN                                         # noqa: E402
import ep10_p2_omg as P2                                           # noqa: E402
from ep10_entrance import FPS, PORTAL_AT, lerp, ss                  # noqa: E402

STEVE_AT, NOOB_AT = P2.STEVE_AT, P2.NOOB_AT
FORK = Vector((0.0, -19.0, 0.0))                                   # the boulder the path splits around
EN.EXTRA_KEEP.extend([(0.0, -31.5, 6.0), (-12.0, -24.0, 5.0), (0.0, -19.0, 4.0), (6.2, -3.1, 3.0)])   # the cameras, the boulder
EN.EXTRA_CLEAR.extend([(4.8, -3.2, 2.2), (0.0, -9.0, 3.0), (0.0, -14.0, 3.0), (0.0, -18.0, 3.0), (-5.0, -24.0, 3.0), (5.0, -24.0, 3.0)])
SPEED = 3.6                                                        # running (m/s)
LENGTH = 13.5
T = {"freeze": 0.0, "steve_signal": 0.4, "noob_signal": 2.35, "beat": 3.4, "steve_run": 3.7, "turn_s": 4.25,
     "turn_n": 5.25, "pov": 6.25, "run": 7.55, "fork": 9.85, "null_look": 11.45, "end": 14.05, "length": 14.55}


# ------------------------------------------------------------------ build
def build(tl, assets, res, samples):
    E = P2.build(tl, assets, res, samples)
    from stage import build_patch_char
    E.Pt = build_patch_char(E.sc, size=0.4)
    _boulder(E, assets)
    return E


def _boulder(E, assets):
    """A mossy boulder of stone blocks at the fork: the path splits around it,
    and from above nothing hides who goes where."""
    import random
    from world import material
    B = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    mats = {n: bpy.data.materials.get("w_" + n) or material("w_" + n, os.path.join(B, n + ".png"), rough=0.9)
            for n in ("stone", "andesite", "cobblestone", "mossy_cobblestone", "moss_block", "tuff")}
    rnd = random.Random(19)
    ground = E.W.layout.height(FORK.x, FORK.y)
    cells = set()
    for z, (rx, ry) in enumerate(((2.6, 1.8), (2.1, 1.5), (1.5, 1.1), (0.9, 0.7))):
        for x in range(-3, 4):
            for y in range(-2, 3):
                if (x / rx) ** 2 + (y / ry) ** 2 <= 1.0 + 0.35 * rnd.random():
                    cells.add((x, y, z))
    for (x, y, z) in sorted(cells):
        if (x, y, z + 1) in cells and rnd.random() < 0.7:
            kind = rnd.choice(("stone", "andesite", "tuff", "cobblestone"))
        else:
            kind = "moss_block" if z >= 2 and rnd.random() < 0.6 else rnd.choice(("mossy_cobblestone", "stone", "andesite"))
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"boulder_{x}_{y}_{z}"
        ob.location = (FORK.x + x, FORK.y + y, ground + z + 0.5)
        ob.data.materials.append(mats[kind])


# ------------------------------------------------------------ where they are
def run_y(t):
    """How far they have run (m, toward -y): they burst off, already fast."""
    if t < T["run"]:
        return 0.0
    u = t - T["run"]
    return -SPEED * (u - 0.18 * (1 - math.exp(-u / 0.18)))


def split(t):
    """0 -> 1 as they break apart around the oak."""
    return ss(T["fork"] + 0.35, T["fork"] + 1.35, t)


def facing(t, turn_at, to=0.0):
    """Yaw (degrees): 180 = toward Null (+y); 0 or 360 = away (-y). The turn, in slow motion
    (to: which way round, so the face passes the camera)."""
    return lerp(180, to, ss(turn_at + 0.05, turn_at + 0.95, t) ** 1.1)


def null_state(t):
    """-> neck position, scale k, lean (degrees forward), yaw (degrees), head yaw (degrees), grin."""
    k = 1.6
    base = PORTAL_AT + Vector((0.0, -2.4, 17.0))
    if t < T["run"]:
        return base, k, 8.0, 0.0, 0.0, 0.0
    chase = t - T["run"]
    y = -2.4 - 3.4 * chase                                            # following, gaining a little
    look = t - T["null_look"]
    if look >= 0:
        y = -2.4 - 3.4 * (T["null_look"] - T["run"]) - 1.2 * ss(0, 0.4, look)   # he stops at the fork
    n = PORTAL_AT + Vector((0.0, y, 17.0 - 2.0 * ss(T["run"], T["run"] + 1.5, t)))
    lean = 8 + 22 * ss(T["run"], T["run"] + 1.0, t)
    head, grin, yaw = 0.0, 0.0, 0.0
    if look >= 0:
        # the head snaps left, holds, snaps right, holds; between, two glitch frames each
        def snap(at, a, b):
            u = (look - at) / 0.12
            if u <= 0:
                return a
            if u >= 1:
                return b
            return a + (b - a) * (0.15 if u < 0.33 else 0.85 if u < 0.66 else 1.0)    # stepped: it skips frames
        head = snap(0.25, 0.0, -62.0)                                   # left: where Steve went (-x)
        head = snap(0.95, head, 66.0)                                   # right: the Noob (+x)
        grin = ss(1.45, 1.75, look)
        lunge = ss(1.75, 2.3, look)
        yaw = 55 * lunge                                               # he turns his whole body after the Noob
        head = lerp(head, 15, lunge)
        n = n + Vector((5.0 * lunge, -1.0 * lunge, -1.5 * lunge))
        lean = lerp(lean, 35, lunge)
    return n, k, lean, yaw, head, grin


# --------------------------------------------------------------- the camera
def camera(t, hs, hn, hx=None):
    """-> loc, look, lens, fstop, focus distance (None: on the look point), handheld (deg), rumble (deg)"""
    ry = run_y(t)
    if t < T["beat"]:                                       # a: the frozen two-shot, Null over them
        u = ss(0, T["beat"], t)                              # low, from their side and a little ahead: both faces, Null over them
        loc = Vector((0.1, -0.5 - 0.25 * u, 1.45))                      # from where Null stands: both faces, lit by him
        look = Vector((0.05, -4.0, 1.9))
        return loc, look, 27, 3.2, None, 0.45, 0.06
    if t < T["turn_s"]:                                     # b: close on Steve; RUN!
        loc = hs + Vector((-1.1, 1.0, -0.3))
        look = hs + Vector((0.0, 0.0, 0.05))
        lens = 48 + 22 * P2.crash(t, T["steve_run"] + 0.05)
        rum = 0.06 + 0.7 * math.exp(-((t - T["steve_run"] - 0.1) / 0.12) ** 2)
        return loc, look, lens, 1.6, None, 0.5, rum
    if t < T["turn_n"]:                                     # c1: Steve turns in slow motion, through facing us
        u = ss(T["turn_s"], T["turn_n"], t)
        loc = hs + Vector((-2.0 + 0.2 * u, -0.25, -0.2))
        return loc, hs + Vector((0, 0, -0.05)), 52 + 6 * u, 1.6, None, 0.3, 0.02
    if t < T["pov"]:                                        # c2: the Noob turns
        u = ss(T["turn_n"], T["pov"], t)
        loc = hn + Vector((1.35 - 0.15 * u, -0.1, -0.15))
        return loc, hn, 50 + 6 * u, 1.4, None, 0.3, 0.02
    if t < T["run"]:                                        # c3: through Steve's eyes: Null, then the way out
        u = ss(T["pov"] + 0.15, T["run"] - 0.05, t)
        eye = STEVE_AT + Vector((0.0, -0.05, 1.78))
        a = math.radians(lerp(0, 180, u))                   # swings round, away from him
        up = lerp(66, 2, ss(0.1, 0.8, u))                   # from his face down to the path
        d = Vector((math.sin(a) * 0.25, math.cos(a), 0.0)).normalized()
        look = eye + Vector((d.x, d.y, math.tan(math.radians(up))))
        bob = Vector((0, 0, 0.02 * math.sin(t * 9)))
        return eye + bob, look, 22, 4.0, 30.0 if u < 0.5 else 6.0, 0.6, 0.02
    if t < T["fork"]:                                       # d: running at us, the world erased behind them
        u = t - T["run"]
        loc = Vector((0.15, max(STEVE_AT.y + ry - 4.4 - 0.5 * ss(0, 1.2, u), FORK.y + 3.8), 0.95))   # stops short of the oak
        look = Vector((0.0, STEVE_AT.y + ry + 9.0, 4.6))
        return loc, look, 21, 5.0, 4.6, 0.8, 0.18
    if t < T["null_look"]:                                  # e: high and wide: the fork
        u = ss(T["fork"], T["null_look"], t)            # high, from ahead: the oak in the middle, they split around it
        loc = Vector((0.0, -31.5 + 0.8 * u, 10.5 - 0.4 * u))             # high, from ahead: over the boulder as they split
        look = Vector((0.0, -14.5, 1.2))
        return loc, look, 26, 14.0, None, 0.35, 0.06
    u = ss(T["null_look"], T["end"] + 0.5, t)               # f: up at Null, at the fork
    n, k, lean, yaw, head, grin = null_state(t)
    loc = Vector((-12.0 + 0.6 * u, -24.0 + 0.4 * u, 2.0))                # in front of him, to the side
    look = hx if hx is not None else n + Vector((0.6, -1.2, 4.6))       # his head
    lens = 30 + 12 * ss(T["null_look"] + 1.45, T["null_look"] + 1.7, t)
    look_t = t - T["null_look"]
    rum = 0.12 + sum(0.6 * math.exp(-((look_t - c) / 0.07) ** 2) for c in (0.27, 0.97)) + 0.5 * ss(1.75, 2.0, look_t)
    return loc, look, lens, 8.0, None, 0.5, rum


# ------------------------------------------------------------ apply a frame
def apply(E, t):
    from pose import pose
    from noob import pose_noob, NOOB_POSES
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from patch import DEFAULTS as PD, set_patch
    from world import fx_set
    from ep09_new import flat, unflat, talk, SF, NF
    slow = T["turn_s"] <= t < T["run"]
    EN.apply(E, EN.T["s4"] + 2.0 + (t if not slow else T["turn_s"] + 0.25 * (t - T["turn_s"])))
    S, N, Pt, G = E.S, E.N, E.Pt, E.G
    ry = run_y(t)
    sp_ = split(t)
    running = t >= T["run"]
    # ------------------------------------------------ Null
    n, k, lean, yaw, head, grin = null_state(t)
    rot = Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(lean), 3, "X")
    G.root.scale = (k, k, k)
    G.root.rotation_euler = rot.to_euler()
    G.root.location = n - rot @ (Vector((0, -0.35, 9.25)) * k)
    G.neck.rotation_euler = (0.0, 0.0, math.radians(head))
    reach = ss(T["run"], T["run"] + 0.8, t)
    drop = ss(T["null_look"] - 0.2, T["null_look"] + 0.25, t) * (1 - ss(T["null_look"] + 1.75, T["null_look"] + 2.1, t))
    for side, sgn in (("sl", 1), ("sr", -1)):                   # reaching; low and wide while he looks around
        fwd = lerp(lerp(-40, -78, reach), -18, drop)
        out = lerp(lerp(16, 8, reach), 38, drop)
        G.arms[side].rotation_euler = (math.radians(fwd), math.radians(sgn * out), 0)
    from ep10_entrance import draw_face
    draw_face(E.face_im, smile=1.0, eyes=1.0, wide=grin, open_=0.35 * grin)
    # the world erases behind them, from where he is
    if running:
        D = min(5.0 + 16.0 * (t - T["run"]), max(2.0, (n.y - (STEVE_AT.y + ry)) - 7.0))
        if t >= T["fork"]:                                 # at the fork it stays under him
            D = min(D, 3.0)
        fx_set(E.W, R=1e5, Wd=100.0, Cx=0.0, Cy=0.0, D=D, Nx=n.x, Ny=n.y, Dz=1.0)
    # ------------------------------------------------ Steve
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    sp = flat(lib["idle (Benly 2.2)"])
    if not running:
        frozen = {"chest_lean": -5, "head_nod": -20, "hips_drop": 0.18, "arm_sl": {"out": 18, "fwd": 12, "elbow": 30},
                  "arm_sr": {"out": 16, "fwd": 9, "elbow": 34}, "foot_sr": {"y": 0.7, "yaw": 10}, "foot_sl": {"y": 0.1}}
        if t >= T["turn_s"]:                               # the turn: head first, then the body, slowly
            u = ss(T["turn_s"] + 0.05, T["turn_s"] + 0.95, t)
            frozen.update(head_nod=lerp(-20, 4, u), chest_lean=lerp(-5, 12, u), hips_drop=lerp(0.18, 0.22, u))
        for kk, v in flat(frozen).items():
            sp[kk] = v
        syaw = facing(t, T["turn_s"], 360.0)
        sx, sy, bob = STEVE_AT.x, STEVE_AT.y, 0.0
    else:
        ph = 2 * math.pi * 2.9 * (t - T["run"])
        sw = math.sin(ph)
        sp = {"chest_lean": 18, "chest_twist": 10 * sw, "head_nod": -8, "hips_drop": 0.16 + 0.05 * abs(math.cos(ph)),
              "arm_sl": {"fwd": -60 * sw, "elbow": 88, "out": 8}, "arm_sr": {"fwd": 60 * sw, "elbow": 88, "out": 8},
              "foot_sl": {"y": -0.55 * sw, "z": max(0.0, 0.5 * math.sin(ph + 1.2))},
              "foot_sr": {"y": 0.55 * sw, "z": max(0.0, 0.5 * math.sin(ph + 1.2 + math.pi))}}
        sp = flat(sp)
        syaw = -28 * ss(0.0, 0.5, sp_) * (1 - ss(0.6, 1.0, sp_))      # banks off to the left (-x)
        sx = STEVE_AT.x - 5.5 * sp_ ** 1.3
        sy, bob = STEVE_AT.y + ry, 0.07 * abs(math.sin(ph))
    pose(S.arm, unflat(sp))
    S.holder.hide_render = T["pov"] <= t < T["run"]          # through his eyes: not inside his head
    S.holder.location = (sx, sy, bob)
    S.holder.rotation_euler = (0, 0, math.radians(syaw))
    fs = {f"{e}_{kk}": v for e in EYES for kk, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    sf = dict(SF["scared"]) if t >= T["steve_run"] else {"both_to": 0.36, "both_tm": 0.4, "both_ti": 0.3, "both_ps": 0.62,
                                                         "both_py": 0.45, "bb_raise": 0.6, "bb_tilt": -0.7}
    if T["beat"] - 0.1 <= t < T["steve_run"] + 0.1:          # his eyes slide to the Noob
        sf["both_px"] = 0.55 * ss(T["beat"] - 0.1, T["beat"] + 0.15, t)
        sf["both_py"] = 0.15
    for kk, v in sf.items():
        if kk.startswith("both_"):
            for e in EYES:
                fs[f"{e}_{kk[5:]}"] = v
        elif not kk.startswith("bb_"):
            fs[kk] = v
    mo = E.mouth.get("steve", {}).get(int(round(t * FPS)))
    if mo and t < T["beat"]:                                 # a whisper through his teeth: the mouth barely opens
        mo = dict(mo, m_o=mo["m_o"] * 0.45)
    talk(fs, mo)
    set_face(S.face, fs)
    for ob_ in S.brows.values():
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(S.brows, {kk: v for kk, v in sf.items() if kk.startswith("bb_")})
    # ------------------------------------------------ the Noob
    if not running:
        npz = flat(NOOB_POSES["scared"])
        npz.update({"head_nod": -24, "head_tilt": 4, "chest_lean": -4, "arm_sl.fwd": 55, "arm_sr.fwd": 55})
        if T["noob_signal"] - 0.1 <= t < T["beat"] + 0.3:     # he leans to Steve to whisper
            npz["head_turn"] = -14 * ss(T["noob_signal"] - 0.1, T["noob_signal"] + 0.3, t)
        if t >= T["turn_n"]:
            u = ss(T["turn_n"] + 0.05, T["turn_n"] + 0.95, t)
            npz.update({"head_nod": lerp(-24, 2, u), "chest_lean": lerp(-4, 10, u)})
        nyaw = facing(t, T["turn_n"])
        nx, ny, nbob = NOOB_AT.x, NOOB_AT.y, 0.0
    else:
        ph = 2 * math.pi * 2.9 * (t - T["run"]) + 0.9
        sw = math.sin(ph)
        npz = {"chest_lean": 12, "head_turn": 0, "arm_sl.fwd": -65 * sw, "arm_sl.out": 12, "arm_sr.fwd": 65 * sw,
               "arm_sr.out": 12, "leg_sl.fwd": 48 * sw, "leg_sr.fwd": -48 * sw}
        nyaw = 26 * ss(0.0, 0.5, sp_) * (1 - ss(0.6, 1.0, sp_))
        nx = NOOB_AT.x + 5.5 * sp_ ** 1.3
        ny, nbob = NOOB_AT.y + ry, 0.08 * abs(math.sin(ph))
    npz["root_yaw"] = nyaw
    pose_noob(N, unflat(npz))
    N.root.location = (nx, ny, nbob)
    fn = {f"{e}_{kk}": v for e in NOOB_EYES for kk, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    nf = dict(NF["scared"])
    nf.update({"both_py": 0.42})
    if T["noob_signal"] - 0.1 <= t < T["beat"] + 0.3:
        nf.update({"both_px": -0.5, "both_py": 0.1})
    if running:
        nf = dict(NF["shout"])
    for kk, v in nf.items():
        if kk.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{kk[5:]}"] = v
        else:
            fn[kk] = v
    mo = E.mouth.get("noob", {}).get(int(round(t * FPS)))
    if mo:
        mo = dict(mo, m_o=mo["m_o"] * 0.8)
    talk(fn, mo)
    set_face(N.face, fn)
    # ------------------------------------------------ Patch: behind them; with them; then straight up
    pz = 2.35 + 0.05 * math.sin(t * 4.4)
    pp = Vector((0.05, STEVE_AT.y - 0.7, pz))
    if running:
        pp = Vector((0.05 + 0.4 * math.sin(t * 3), STEVE_AT.y + ry + 0.6, 2.2 + 0.1 * math.sin(t * 9)))
        pp.z += 9.0 * ss(T["fork"] + 0.35, T["fork"] + 1.0, t) ** 1.5
    Pt.root.location = pp
    Pt.root.rotation_euler = (0, 0, math.radians(180 if t < T["turn_n"] else lerp(180, 0, ss(T["turn_n"], T["turn_n"] + 0.6, t))))
    pf = dict(PD)
    pf.update({"wide": 1.0, "look_y": 0.5} if not running else {"wide": 0.8, "squint": 0.0, "look_y": -0.2})
    set_patch(Pt, pf)
    for side, pv in Pt.fins.items():
        fl = 30 * math.sin(2 * math.pi * 5.0 * t) * (1 if running else 0.2)
        pv.rotation_euler = (math.radians(fl) * (1 if side == "l" else -1), 0, 0)
    # ------------------------------------------------ the camera
    bpy.context.view_layer.update()

    def centre(ob, m=None):
        c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
        return (m @ ob.matrix_world @ c) if m is not None else ob.matrix_world @ c
    hs = centre(S.face, S.holder.matrix_world)
    hn = centre(N.head_mesh)
    hx = centre(G.head)
    loc, look, lens, fstop, focus, hand, rum = camera(t, hs, hn, hx)
    tt = T["turn_s"] + 0.25 * (t - T["turn_s"]) if slow else t           # the shake slows down too
    y1, p1, r1 = P2.handheld(tt, hand)
    y2, p2, r2 = P2.rumble(tt, rum)
    q = (look - loc).to_track_quat("-Z", "Y")
    q = q @ Quaternion((0, 1, 0), math.radians(y1 + y2)) @ Quaternion((1, 0, 0), math.radians(p1 + p2)) \
        @ Quaternion((0, 0, 1), math.radians(r1 + r2))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.face_fill.location = loc + Vector((0, 0, 0.9))
    E.face_fill.rotation_euler = (look - E.face_fill.location).to_track_quat("-Z", "Y").to_euler()
    E.key.data.energy = 0.0
    E.sc.render.motion_blur_shutter = 0.15 if slow else 0.5             # slow motion: crisp
    return {"g": 0.0, "s": 1.0}


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    if "turn_s" in b:
        for k in ("freeze", "steve_signal", "noob_signal", "beat", "steve_run", "turn_s", "turn_n", "pov", "run", "fork",
                  "null_look", "end"):
            if k in b:
                T[k] = b[k][0]
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
    tl = {"length": T["length"] - 0.4, "fps": FPS, "beats": {}, "lines": []} if a.timeline == "-" else json.load(open(a.timeline))
    align(tl)
    n_frames = int(round(T["length"] * FPS)) + 1
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    E = build(tl, a.assets, a.res, a.samples)
    E.env = lambda t: 0.7
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
