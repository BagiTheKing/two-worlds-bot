"""Episode 10 (the finale), part 13: Patch.

The world is back, gold under a gold sky, and the Noob is still falling toward
it, glowing faintly, eyes closed. High above, Patch has watched it all: "I will
not allow this." He dives, faster than anything we have seen, and falling
alongside the Noob he transforms (his upgrade), a mechanical sequence in steps:
his fins unlock and split into two armour plates; a shoulder socket pushes out
of his side, its joint spinning up; the upper arm telescopes out, sleeve by
sleeve, each one locking with a clunk; the forearm swings out from where it lay
folded; the hand spins round into place and its three fingers flip out one by
one and test their grip; the plates lock on as a shoulder pad and a forearm
guard; the joints flash cyan. Then he swoops: one hand takes the Noob by the
scruff of his neck (who swings down from where he lay on his back). Up to the
island, where Steve still hangs from the stub; the other hand takes Steve by
the neck. And down, the two of them held well apart, turning slowly to face us,
until their feet touch the grass of the world that came back. He lets go and
his arms fold back in.

The set is part 12's (the island, the restored world of the upgrade episode),
the world now laid out below the island. Every turn here is smooth: Patch's
heading is planned, not read off his velocity, and whoever he holds hangs from
his hand by the neck.

    python src/lookdev/ep10_p13_patch.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_p12_normal as P12                                        # noqa: E402
import ep10_p7_reveal as P7                                          # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

T = {"watch": 0.0, "patch_allow": 0.7, "patch_allow_end": 2.3, "dive": 2.45, "upgrade": 4.05, "catch": 6.65,
     "climb": 7.85, "grab_steve": 10.05, "land": 10.95, "end": 13.95, "length": 14.9}
SEG = 0.62                                                    # each arm segment (m)
UP_PAD, UP_LEN = 0.1, 2.4                                     # the transformation: starts 0.1 s into its beat, takes 2.4 s
CLUNKS = (0.28, 0.36, 0.44, 0.52, 0.68, 0.97)                 # where it locks (camera bumps; the sound follows these)
SPARK_AT = (0.28, 0.52, 0.68, 0.97)
N_SPARK = 6
SHOULDER = {"r": Vector((0.24, 0.02, 0.0)), "l": Vector((-0.24, 0.02, 0.0))}
OUTV = {"r": Vector((1.0, 0.0, 0.4)).normalized(), "l": Vector((-1.0, 0.0, 0.4)).normalized()}
REST = {s: SHOULDER[s] + OUTV[s] * 0.3 + Vector((0.0, 0.0, -0.4)) for s in ("r", "l")}   # the arm at rest (his frame)
V_FALL = Vector((0.25, 0.1, -4.5))                            # the Noob's fall (m/s)
OFF0, OFF1 = Vector((1.0, -0.5, 5.0)), Vector((0.9, -0.4, 3.2))   # Patch above the Noob while he transforms
H_GRAB = 90 - 125 - 22                                        # Steve's heading as he hangs (part 7's)
H_LAND = math.degrees(math.atan2(-3.75, 11.5))                # facing the landing camera

FALL_N = {"chest_lean": 0, "head_nod": -10, "arm_sl": {"fwd": 40, "out": -12}, "arm_sr": {"fwd": 40, "out": -12},
          "leg_sl": {"fwd": 22, "out": 0}, "leg_sr": {"fwd": 8, "out": 0}, "root_yaw": 0}
LAND_N = {"chest_lean": 3, "head_nod": 18, "arm_sl": {"fwd": 4, "out": 6}, "arm_sr": {"fwd": 4, "out": 6},
          "leg_sl": {"fwd": 0, "out": 0}, "leg_sr": {"fwd": 0, "out": 0}, "root_yaw": 0}
CARRIED_S = {"chest_lean": 4, "arm_sl": {"fwd": 160, "out": 10, "elbow": 45}, "arm_sr": {"fwd": 160, "out": 10, "elbow": 45},
             "foot_sl": {"y": 0.0, "z": 0.05}, "foot_sr": {"y": -0.05, "z": 0.0}}
LAND_S = {"chest_lean": 0, "arm_sl": {"fwd": 6, "out": 12, "elbow": 14}, "arm_sr": {"fwd": 6, "out": 12, "elbow": 16},
          "foot_sl": {"y": 0.0, "z": 0.0}, "foot_sr": {"y": 0.0, "z": 0.0}}


def shots():
    return [("WATCH", T["dive"]), ("DIVE", T["upgrade"]), ("UPGRADE", T["catch"]), ("CATCH", T["climb"]),
            ("CLIMB", T["grab_steve"]), ("GRAB", T["land"]), ("LAND", 1e9)]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "LAND", t0, 1e9


# the beats inside the beats
def sw0():
    return T["upgrade"] + UP_PAD + UP_LEN - 0.15               # the swoop down to the Noob begins


def tc():
    return T["catch"] + 0.35                                  # his hand on the Noob's neck


def ts():
    return T["grab_steve"] + 0.3                              # ... on Steve's


def tl():
    return T["land"] + 2.3                                    # their feet on the grass


def tr():
    return tl() + 0.3                                         # he lets go


def kprog(t):
    """How far the transformation has gone (0 = fins, 1 = arms)."""
    return max(0.0, min(1.0, (t - T["upgrade"] - UP_PAD) / UP_LEN))


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def rz(deg):
    return Matrix.Rotation(math.radians(deg), 3, "Z")


# ------------------------------------------------------------------ build
def build(tl_, tex_dir, assets, res, samples):
    E = P12.build(tl_, tex_dir, assets, res, samples)
    sc = E.sc
    W = E.W
    # the restored world laid out below the island (the landing hill under the Noob's fall)
    h0 = W.H.get((0, -12), 2) if hasattr(W, "H") else 2
    E.land_local = Vector((0.0, -12.0, float(h0)))
    E.land_at = Vector((E.XE - 14.0, E.lane["N"] - 30.0, E.deck - 62.0))
    new_at = E.land_at - E.land_local
    for o in E.world_objs:
        o.location = o.location - P12.WORLD_AT + new_at
    E.new_at = new_at
    P12.void_fx_set(W, 1e5, 4.0, 0, 0)
    sc.world = E.respawn_world
    E.I.sun.hide_render = True
    W.sun.hide_render = False
    E.I.void.hide_render = True
    E.star.hide_render = True
    E.heart.data.energy = 0.0
    E.cell.hide_render = E.cell_head.hide_render = True
    E.cell_glow.data.energy = 0.0
    for ob, *_ in E.drifters:
        ob.hide_render = True
    E.wave_ring.hide_render = True
    _arms(E)
    # the Noob's faint glow (what is left of the light)
    L = bpy.data.lights.new("noob_glow", "POINT")
    L.color = (1.0, 0.86, 0.6)
    L.shadow_soft_size = 0.5
    E.nglow = bpy.data.objects.new("noob_glow", L)
    sc.collection.objects.link(E.nglow)
    # paths (world positions)
    E.steve_hang = None
    E.patch0 = Vector((E.XE - 4.5, E.lane["S"] - 3.5, E.deck + 9.0))
    E.noob0 = Vector((E.XE - 7.0, E.lane["N"] - 6.0, E.deck - 16.0))
    d = E.noob0 - E.patch0
    E.h_dive = math.degrees(math.atan2(d.x, -d.y))
    E._prep = False
    return E


def _mat(name, base, emit=None, strength=0.0, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def _arms(E):
    """Two arms in pieces, placed per frame by chain(): a shoulder socket, three telescoping
    upper-arm sleeves, two forearm sleeves, a hand with three fingers, cyan joints, the two
    halves of each fin (a shoulder pad and a forearm guard), and a few sparks."""
    Pt = E.Pt
    shell = None
    for o in Pt.col.objects:
        if o.type == "MESH" and o.data.materials:
            for m in o.data.materials:
                if m and "shell" in m.name:
                    shell = m
    E.joint_mat = jm = _mat("patch_joint", (0.05, 0.6, 0.9), (0.02, 0.75, 1.0), 4.0)
    frame = _mat("patch_frame", (0.09, 0.1, 0.12), rough=0.35, metal=0.6)          # the dark inner frame
    spark = _mat("patch_spark", (1.0, 0.7, 0.3), (1.0, 0.72, 0.35), 40.0)
    col = bpy.data.collections.new("patch_arms")
    E.sc.collection.children.link(col)

    def box(name, mat, bevel=0.01):
        me = bpy.data.meshes.new(name)
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        if bevel:
            mod = ob.modifiers.new("bevel", "BEVEL")
            mod.width = bevel
            mod.segments = 2
        ob.data.materials.append(mat)
        ob.rotation_mode = "QUATERNION"
        ob.location = (0, 0, -900)
        return ob
    E.arms = {}
    for side in ("l", "r"):
        A = {"socket": box(f"arm_{side}_socket", frame), "s0": box(f"arm_{side}_s0", shell),
             "s1": box(f"arm_{side}_s1", frame), "s2": box(f"arm_{side}_s2", shell),
             "f0": box(f"arm_{side}_f0", shell), "f1": box(f"arm_{side}_f1", frame),
             "hand": box(f"arm_{side}_hand", shell), "pad": box(f"arm_{side}_pad", shell, 0.006),
             "guard": box(f"arm_{side}_guard", shell, 0.006),
             "j": [box(f"arm_{side}_j{i}", jm) for i in range(3)],
             "fingers": [box(f"arm_{side}_finger{i}", frame) for i in range(3)],
             "sparks": [box(f"arm_{side}_spark{i}", spark, 0) for i in range(N_SPARK * len(SPARK_AT))]}
        E.arms[side] = A
    # the fins at rest, in Patch's frame: the two plates start as their halves
    for side in ("l", "r"):
        Pt.fins[side].rotation_euler = (0, 0, 0)
        Pt.fins[side].scale = (1, 1, 1)
    bpy.context.view_layer.update()
    E.fin_rest = {}
    inv = Pt.root.matrix_world.inverted()
    for side in ("l", "r"):
        mesh = [c for c in Pt.fins[side].children if c.type == "MESH"][0]
        rel = inv @ mesh.matrix_world
        E.fin_rest[side] = (rel.translation.copy(), mesh.dimensions.copy())


def arm_parts(A):
    return [A[k] for k in ("socket", "s0", "s1", "s2", "f0", "f1", "hand", "pad", "guard")] + A["j"] + A["fingers"]


def arm_hide(E, side, hidden=True):
    A = E.arms[side]
    for ob in arm_parts(A) + A["sparks"]:
        ob.hide_render = hidden


def _put(ob, m, q_m, loc, quat, scale):
    ob.location = m @ loc
    ob.rotation_quaternion = q_m @ quat
    ob.scale = scale


def _seg(ob, m, q_m, a, b, w):
    d = b - a
    L = max(d.length, 1e-4)
    q = Vector((0, 0, 1)).rotation_difference(d / L) if d.length > 1e-6 else Quaternion()
    _put(ob, m, q_m, (a + b) * 0.5, q, (w, w, L))


def ik(S, target, out, a=SEG, b=SEG):
    """A two-bone arm from S toward target, the elbow bent toward `out`: (elbow, hand)."""
    d = target - S
    dist = max(1e-4, min(d.length, (a + b) * 0.999))
    dn = d.normalized() if d.length > 1e-5 else Vector((0, 0, -1))
    cos_a = max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist)))
    ang = math.acos(cos_a)
    pole = out - dn * out.dot(dn)
    pole = pole.normalized() if pole.length > 1e-5 else Vector((0, 0, 1))
    return S + (dn * math.cos(ang) + pole * math.sin(ang)) * a, S + dn * dist


def rest_pose(side):
    return ik(SHOULDER[side], REST[side], OUTV[side])


def chain(E, side, m, El, H, k, grip=0.0, sparks=True):
    """Patch's arm on `side`, in his own frame (m = his world matrix): shoulder SHOULDER[side],
    elbow El, wrist H. k = how far the transformation has gone (0: still a fin, 1: the arm), in
    steps: unlock and split (0-0.1), the plates swing and the socket pushes out (0.04-0.3), the
    upper arm telescopes (0.28-0.52), the forearm unfolds (0.52-0.68) and extends (0.66-0.76),
    the hand spins in (0.72-0.84), the fingers flip out (0.78-0.92), a grip test (0.9-0.98),
    the plates lock on as pad and guard (0.84-0.97). Returns the wrist (world)."""
    A = E.arms[side]
    sx = 1.0 if side == "r" else -1.0
    q_m = m.to_quaternion()
    S = SHOULDER[side]
    fin = E.Pt.fins[side]
    if k <= 0.0:
        arm_hide(E, side, True)
        fin.scale = (1, 1, 1)
        return m @ H

    def st(a, b):
        return ss(a, b, k)
    arm_hide(E, side, False)
    fin.scale = (0.001,) * 3
    X = Vector((sx, 0, 0))
    # the socket pushes out of his side; the shoulder joint spins up in it
    so = st(0.04, 0.28)
    _put(A["socket"], m, q_m, S + X * lerp(-0.1, -0.035, so), Quaternion(), (0.11, 0.13, 0.13))
    _put(A["j"][0], m, q_m, S, Quaternion(X, math.radians(720) * st(0.18, 0.5)), (0.1 * so + 1e-3,) * 3)
    # the upper arm telescopes out: three sleeves, one after the other
    u = El - S
    Lu = max(u.length, 1e-4)
    u = u / Lu
    e0, e1, e2 = st(0.28, 0.36), st(0.36, 0.44), st(0.44, 0.52)
    ln = 0.4 * Lu
    s0 = (e0 - 1.0) * 0.36 * Lu
    s1 = s0 + e1 * 0.3 * Lu
    s2 = s1 + e2 * 0.3 * Lu
    for ob, a_, w in ((A["s0"], s0, 0.088), (A["s1"], s1, 0.074), (A["s2"], s2, 0.062)):
        _seg(ob, m, q_m, S + u * a_, S + u * (a_ + ln), w)
    elb = S + u * (s2 + ln)
    # the forearm swings out from where it lay folded along the upper arm, then extends
    fdf = H - El
    Lf = max(fdf.length, 1e-4)
    fdf = fdf / Lf
    g = st(0.52, 0.68)
    d0 = -u
    ax = d0.cross(fdf)
    ax = ax.normalized() if ax.length > 1e-4 else Vector((0, 1, 0))
    fd = Quaternion(ax, d0.angle(fdf) * g) @ d0
    base = elb + ax.cross(d0).normalized() * 0.075 * (1 - g)
    e3 = st(0.66, 0.76)
    lf = 0.55 * Lf
    _seg(A["f0"], m, q_m, base, base + fd * lf, 0.07)
    f1a = 0.45 * Lf * e3
    _seg(A["f1"], m, q_m, base + fd * f1a, base + fd * (f1a + lf), 0.058)
    W = base + fd * (f1a + lf)
    _put(A["j"][1], m, q_m, elb, Quaternion(u, math.radians(540) * st(0.5, 0.7)), (0.085,) * 3)
    # the hand spins round into place; the fingers flip out one by one; a grip test
    hv = st(0.72, 0.84)
    _put(A["j"][2], m, q_m, W, Quaternion(fd, math.radians(360) * hv), (0.065,) * 3)
    qh = Quaternion(fd, math.pi * (1 - hv)) @ Vector((0, 0, 1)).rotation_difference(fd)
    hs = lerp(0.55, 1.0, hv)
    _put(A["hand"], m, q_m, W + fd * 0.05, qh, (0.13 * hs, 0.13 * hs, 0.11 * hs))
    sv = fd.cross(Vector((0, 0, 1)))
    sv = sv.normalized() if sv.length > 1e-4 else Vector((1, 0, 0))
    test = math.sin(math.pi * st(0.9, 0.98))
    for i, f in enumerate(A["fingers"]):
        fi = st(0.78 + 0.03 * i, 0.86 + 0.03 * i)
        bend = (1 - fi) * 150 + 70 * max(grip, test)
        fdir = Quaternion(sv, math.radians(bend)) @ fd
        b0 = W + fd * 0.11 + sv * (i - 1) * 0.04
        _seg(f, m, q_m, b0, b0 + fdir * 0.09, 0.03)
    # the fin's halves: unlock and split, swing open; the top one becomes the shoulder pad,
    # the bottom one slides down the arm and locks on as the forearm guard
    fc, fdim = E.fin_rest[side]
    ph = fdim.z / 4
    p1, p2 = st(0.0, 0.1), st(0.08, 0.3)
    top0 = fc + Vector((0, 0, ph)) + X * 0.03 * p1 + Vector((0, 0, 0.02 * p1))
    pad_at = S + X * 0.03 + Vector((0, 0, 0.11))
    _put(A["pad"], m, q_m, top0.lerp(pad_at, p2), Quaternion((0, 1, 0), math.radians(-sx * 65) * p2),
         (fdim.x * lerp(1, 1.4, p2), fdim.y * lerp(1, 1.5, p2), fdim.z / 2 * lerp(1, 1.9, p2)))
    bot0 = fc - Vector((0, 0, ph)) + X * 0.03 * p1 - Vector((0, 0, 0.02 * p1))
    park = S + X * 0.03 + Vector((0, 0, -0.11))
    q_park = Quaternion((0, 1, 0), math.radians(sx * 65) * p2)
    g6 = st(0.84, 0.97)
    nrm = X - fd * fd.dot(X)
    nrm = nrm.normalized() if nrm.length > 1e-4 else Vector((0, 0, 1))
    q_fore = Matrix((nrm, fd, nrm.cross(fd))).transposed().to_quaternion()
    on_fore = base + fd * (0.5 * Lf) + nrm * 0.055
    _put(A["guard"], m, q_m, bot0.lerp(park, p2).lerp(on_fore, g6), q_park.slerp(q_fore, g6),
         (fdim.x * lerp(1, 1.3, p2), fdim.y * lerp(1, 2.0, g6), fdim.z / 2 * lerp(1, 1.5, p2)))
    # what is still inside him stays hidden
    inside = k < 0.27
    for ob in [A["s0"], A["s1"], A["s2"], A["f0"], A["f1"], A["hand"], A["j"][1], A["j"][2]] + A["fingers"]:
        ob.hide_render = inside
    # sparks where it locks
    at = {0.28: S + X * 0.06, 0.52: elb, 0.68: elb, 0.97: on_fore}
    for j, kc in enumerate(SPARK_AT):
        for i in range(N_SPARK):
            ob = A["sparks"][j * N_SPARK + i]
            tau = (k - kc) * UP_LEN
            if not sparks or tau < 0.0 or tau > 0.3:
                ob.hide_render = True
                continue
            rnd = random.Random(j * 31 + i * 7 + (0 if side == "l" else 500))
            v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 1))).normalized() * rnd.uniform(0.8, 1.6) + X * 0.6
            p = at[kc] + v * tau + Vector((0, 0, -3.0)) * tau * tau
            sc_ = 0.016 * (1 - tau / 0.3) + 1e-4
            _put(ob, m, q_m, p, Quaternion(), (sc_,) * 3)
    return m @ W


# ------------------------------------------------------------------ the story, in positions
def bez(p0, p1, p2, p3, u):
    v = 1 - u
    return p0 * v ** 3 + p1 * 3 * v * v * u + p2 * 3 * v * u * u + p3 * u ** 3


def noob_free(E, t):
    """The Noob before the catch: falling, slowly turning, on his back, glowing faintly."""
    s = max(0.0, t - T["watch"])
    return E.noob0 + V_FALL * s


def fall_rot(t):
    return Euler((math.radians(-78), math.radians(6 * math.sin(t * 0.5)), math.radians(20 + 5 * t)), "XYZ")


def limp_n(t):
    return {"chest_lean": 6, "head_nod": 22, "arm_sl": {"fwd": 8, "out": 8}, "arm_sr": {"fwd": 8, "out": -8},
            "leg_sl": {"fwd": 6 + 8 * math.sin(t * 2.1), "out": 0}, "leg_sr": {"fwd": -4 + 8 * math.sin(t * 2.1 + 1.2), "out": 0},
            "root_yaw": 0}


def steve_neck(E):
    S = E.S
    pb = S.arm.pose.bones["Head"]
    return S.holder.matrix_world @ S.arm.matrix_world @ pb.head


def noob_neck(E):
    return E.N.neck.matrix_world.translation


def heading(E, t):
    """Patch's heading (degrees; 0 faces -y): planned, so nothing ever snaps round."""
    if t < T["climb"]:
        return E.h_dive
    if t < ts():
        return E.h_dive + wrap(H_GRAB - E.h_dive) * ss(T["climb"], T["grab_steve"], t)
    return H_GRAB + wrap(H_LAND - H_GRAB) * ss(ts() + 0.2, tl() - 0.3, t)


def pitch(t):
    p = -40.0 * ss(T["dive"], T["dive"] + 0.4, t)
    p = lerp(p, -12.0, ss(T["upgrade"], T["upgrade"] + 0.5, t))
    p = lerp(p, -35.0, ss(sw0() - 0.1, sw0() + 0.2, t))
    return lerp(p, 0.0, ss(tc(), tc() + 0.5, t))


def carry_point(E, side, t):
    """Where the hand holding `side`'s one is (world), from Patch's centre and heading."""
    return patch_at(E, t) + rz(heading(E, t)) @ E.carry[side]


def catch_pos(E):
    return E.neck_tc + Vector((0, 0, 0.08)) - rz(heading(E, tc())) @ E.carry["r"]


def steve_pos(E):
    return E.steve_neck0 + Vector((0, 0, 0.06)) - rz(H_GRAB) @ E.carry["l"]


def patch_at(E, t):
    """Patch's centre: high up; the dive; falling with the Noob while he transforms; the swoop
    and the catch; up to Steve; the carry down; feet on the grass; up a little once he lets go."""
    up0, s0, tc_, ts_, tl_ = T["upgrade"], sw0(), tc(), ts(), tl()
    if t < T["dive"]:
        return E.patch0 + Vector((0, 0, 0.08 * math.sin(t * 3.0)))
    A = noob_free(E, up0) + OFF0
    if t < up0:
        d = up0 - T["dive"]
        return bez(E.patch0, E.patch0 + Vector((-0.4, -0.3, -0.6)), A - V_FALL * (d / 3), A, (t - T["dive"]) / d)
    if t < s0:
        wob = ss(up0, up0 + 0.5, t) * (1 - ss(s0 - 0.4, s0, t))
        return noob_free(E, t) + OFF0.lerp(OFF1, ss(up0, s0, t)) + \
            Vector((0.06 * math.sin(t * 2.3), 0.05 * math.sin(t * 1.7), 0.0)) * wob
    B = noob_free(E, s0) + OFF1
    C = catch_pos(E)
    v_end = V_FALL + Vector((0, 0, -3.0))
    if t < tc_:
        d = tc_ - s0
        return bez(B, B + V_FALL * (d / 3), C - v_end * (d / 3), C, (t - s0) / d)
    Sp = steve_pos(E)
    if t < ts_:
        d = ts_ - tc_
        x = (t - tc_) / d
        return bez(C, C + v_end * (d / 6) * 0.6, Sp + rz(H_GRAB) @ Vector((0.6, -0.6, -1.2)), Sp, x * (2 - x))
    L = E.land_pos
    if t < tl_:
        return bez(Sp, Sp + Vector((-6.0, -4.0, 1.0)), L + Vector((4.0, 6.0, 14.0)), L, ss(ts_ + 0.15, tl_, t))
    return L + Vector((0, 0, 0.5 * ss(tr(), tr() + 1.0, t)))


def _over(base, over):
    out = json.loads(json.dumps(base))
    for k, v in over.items():
        if isinstance(v, dict):
            out[k] = dict(out.get(k, {}) if isinstance(out.get(k), dict) else {}, **v)
        else:
            out[k] = v
    return out


def steve_hook(t):
    """Steve's own pose once Patch has him: hands up on the robot wrist, legs dangling; then
    standing as his feet come down."""
    mix = P7.P6._mix

    def hook(p):
        c = json.loads(json.dumps(CARRIED_S))
        c["foot_sl"]["y"] = 0.06 * math.sin(t * 2.0)
        c["foot_sr"]["y"] = -0.05 + 0.06 * math.sin(t * 2.0 + 1.3)
        q = mix(p, _over(p, c), ss(ts(), ts() + 0.45, t))
        return mix(q, _over(p, LAND_S), ss(tl() - 0.8, tl(), t))
    return hook


def prepare(E):
    """Once: where Steve's neck is as he hangs, where the Noob's is at the catch, and how high
    Patch must be at the landing for both their feet to touch the grass."""
    if E._prep:
        return
    from noob import pose_noob
    E._prep = True
    S, N = E.S, E.N
    faces(E, 0.0)
    E.steve_pose_hook = None
    E.steve_yaw_add = 0.0
    E.force_shot = "R1"
    P7.cast(E, P7.T["dive"] - 2.6)
    bpy.context.view_layer.update()
    E.steve_neck0 = steve_neck(E).copy()
    E.steve_pose_hook = lambda p: _over(p, LAND_S)
    P7.cast(E, P7.T["dive"] - 2.6)
    E.steve_pose_hook = None
    E.force_shot = None
    S.holder.location = (0, 0, 0)
    bpy.context.view_layer.update()
    nh_s = steve_neck(E).z
    pose_noob(N, LAND_N)
    N.root.location = (0, 0, 0)
    N.root.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    nh_n = noob_neck(E).z - N.root.matrix_world.translation.z
    g = E.land_at.z
    land_z = g + nh_n + 0.08 + 0.75
    E.carry = {"r": Vector((1.06, 0.02, -0.75)), "l": Vector((-1.06, 0.02, -(land_z - g - nh_s - 0.06)))}
    E.land_pos = Vector((E.land_at.x + 0.6, E.land_at.y, land_z))
    pose_noob(N, FALL_N)
    N.root.rotation_euler = fall_rot(tc())
    N.root.location = noob_free(E, tc())
    bpy.context.view_layer.update()
    E.neck_tc = noob_neck(E).copy()
    print("P13 prepare: neck heights", round(nh_n, 3), round(nh_s, 3), "carry", tuple(E.carry["l"]), flush=True)


# ------------------------------------------------------------------ per frame
def apply(E, t):
    from noob import pose_noob
    from patch import DEFAULTS as PD, set_patch
    prepare(E)
    shot = which(t)[0]
    faces(E, t)
    H = heading(E, t)
    tc_, ts_, tl_, tr_ = tc(), ts(), tl(), tr()
    mix = P7.P6._mix
    # Steve: hanging from the stub as part 12 left him, until Patch has him
    if t >= ts_:
        E.steve_yaw_add = wrap(H - H_GRAB)
        E.steve_pose_hook = steve_hook(t)
    else:
        E.steve_yaw_add = 0.0
        E.steve_pose_hook = None
    E.force_shot = "R1"
    E.lip_frame = int(round(t * FPS))
    P7.cast(E, P7.T["dive"] - 2.6)
    E.force_shot = None
    E.steve_pose_hook = None
    E.X.root.location = (0, 0, -3000.0)
    E.X.root.scale = (0.001,) * 3
    E.sc.world = E.respawn_world
    # ---- Patch
    Pt = E.Pt
    pc = patch_at(E, t)
    Pt.root.location = pc
    Pt.root.rotation_euler = (math.radians(pitch(t)), 0, math.radians(H))
    for o in Pt.col.objects:
        o.hide_render = False
    Pt.beam.hide_render = True
    k = kprog(t)
    flash = math.sin(math.pi * ss(0.9, 0.99, k))
    vals = dict(PD)
    vals.update({"open": 1.0, "squint": 0.6 * (1 - flash) if t < T["climb"] else 0.0, "wide": 0.6 * flash,
                 "smile": 0.6 * ss(T["land"] + 1.6, tl_ + 0.6, t)})
    if T["upgrade"] <= t < T["upgrade"] + 0.6:
        vals["glitch"] = 0.4 * math.sin(math.pi * (t - T["upgrade"]) / 0.6)
    set_patch(Pt, vals)
    E.joint_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0 + 26.0 * flash
    damp = 1 - ss(T["upgrade"] - 0.3, T["upgrade"] + UP_PAD, t)
    for side in ("l", "r"):
        Pt.fins[side].rotation_euler = (math.radians(25 * math.sin(t * 18.0) * damp), 0, 0)
    bpy.context.view_layer.update()
    m = Pt.root.matrix_world.copy()
    mi = m.inverted()
    # ---- the Noob
    N = E.N
    if t < tc_:
        pose_noob(N, FALL_N)
        N.root.rotation_euler = fall_rot(t)
        N.root.location = noob_free(E, t)
        bpy.context.view_layer.update()
        tgt = REST["r"]
        if t >= T["catch"]:                                  # reaching for him
            tgt = REST["r"].lerp(mi @ (noob_neck(E) + Vector((0, 0, 0.08))), ss(T["catch"], tc_, t))
        chain(E, "r", m, *ik(SHOULDER["r"], tgt, OUTV["r"]), k, grip=ss(tc_ - 0.12, tc_, t))
    else:
        te = min(t, tr_)
        pose_noob(N, mix(mix(FALL_N, limp_n(t), ss(tc_, tc_ + 0.6, t)), LAND_N, ss(tl_ - 0.8, tl_, t)))
        sw = 7 * math.exp(-(t - tc_) * 1.4) * math.sin((t - tc_) * 4.5) * (1 - ss(tl_ - 0.8, tl_, t))
        qh = Euler((math.radians(sw), math.radians(sw * 0.5), math.radians(heading(E, te))), "XYZ").to_quaternion()
        N.root.rotation_euler = fall_rot(tc_).to_quaternion().slerp(qh, ss(tc_, tc_ + 0.7, t)).to_euler("XYZ")
        hand = carry_point(E, "r", te)
        bpy.context.view_layer.update()
        N.root.location = N.root.location + (hand - Vector((0, 0, 0.08)) - noob_neck(E))
        tgt = mi @ carry_point(E, "r", t) if t < tr_ else (mi @ carry_point(E, "r", tr_)).lerp(REST["r"], ss(tr_, tr_ + 0.8, t))
        chain(E, "r", m, *ik(SHOULDER["r"], tgt, OUTV["r"]), k, grip=1 - ss(tr_ - 0.05, tr_ + 0.25, t))
    # his faint glow
    E.nglow.location = N.root.location + Vector((0, 0, 1.0))
    E.nglow.data.energy = 120.0 * (1 - ss(T["land"], tl_ + 0.6, t))
    # ---- Steve
    S = E.S
    if t >= ts_:
        te = min(t, tr_)
        hand = carry_point(E, "l", te)
        bpy.context.view_layer.update()
        S.holder.location = S.holder.location + (hand - Vector((0, 0, 0.06)) - steve_neck(E))
        tgt = mi @ carry_point(E, "l", t) if t < tr_ else (mi @ carry_point(E, "l", tr_)).lerp(REST["l"], ss(tr_, tr_ + 0.8, t))
        chain(E, "l", m, *ik(SHOULDER["l"], tgt, OUTV["l"]), k, grip=1 - ss(tr_ - 0.05, tr_ + 0.25, t))
    else:
        tgt = REST["l"].lerp(mi @ (E.steve_neck0 + Vector((0, 0, 0.06))), ss(T["grab_steve"] - 0.2, ts_, t))
        chain(E, "l", m, *ik(SHOULDER["l"], tgt, OUTV["l"]), k, grip=ss(ts_ - 0.12, ts_, t))
    return camera_set(E, t, shot)


def faces(E, t):
    from faceplate import NOOB_EYES
    asleep = {"both_open": 0.0, "both_h": 1.5, "m_arch": -0.4, "m_w": 1.6, "m_o": 0.0}

    def hook(fn):
        for k, v in asleep.items():
            if k.startswith("both_"):
                for e in NOOB_EYES:
                    fn[f"{e}_{k[5:]}"] = v
            else:
                fn[k] = v
        return fn
    E.noob_face_hook = hook
    E.noob_head = (0, 12)
    shock = {"both_to": -0.35, "both_tm": -0.35, "both_ti": -0.3, "both_ps": 0.45, "bb_tilt": -0.85, "bb_raise": 1.0,
             "m_arch": 0.25, "m_w": 1.6, "m_o": 0.3}
    relief = {"both_to": 0.15, "both_tm": 0.1, "both_ti": 0.1, "both_ps": 0.8, "bb_tilt": -0.4, "bb_raise": 0.4,
              "m_arch": -0.35, "m_w": 1.9, "m_o": 0.15}
    import ep10_p6_fall as P6
    E.steve_face = P6._mixf(shock, relief, ss(T["land"] + 1.0, T["end"], t))
    E.steve_head = (-30, lerp(30, 0, ss(T["grab_steve"], T["land"], t)))


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
    pc = E.Pt.root.location.copy()
    t0, t1 = which(t)[1:]
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, T["end"], t)
    nn = noob_neck(E)
    if shot == "WATCH":
        # Patch high in the gold sky, his eye on the fall below; the island under him, the world far below
        d = (E.noob0 - pc)
        d = Vector((d.x, d.y, 0)).normalized()
        loc = pc + d * 1.3 + Vector((0, 0, -0.35)) + d.cross(Vector((0, 0, 1))).normalized() * 0.35
        return loc, pc, 40, 3.0, (pc - loc).length, 0.06, 0.0
    if shot == "DIVE":
        # with him, beside and above, the island's cliff rushing past, the glowing Noob far below
        loc = pc + Vector((-2.6, -3.2, 1.2))
        return loc, pc.lerp(nn, 0.15), 30, 6.0, (pc - loc).length, 0.15, 0.0
    if shot == "UPGRADE":
        # around him as he transforms, falling with him (the Noob far below): from his front-left
        # round to his right side, closing in; a jolt at each lock
        uu = ss(T["upgrade"], T["catch"], t)
        a = math.radians(lerp(-50, 35, uu))
        r = lerp(2.0, 1.7, uu)
        loc = pc + rz(heading(E, t)) @ Vector((r * math.sin(a), -r * math.cos(a), lerp(0.35, -0.1, uu)))
        bump = sum(math.exp(-((t - (T["upgrade"] + UP_PAD + c * UP_LEN)) / 0.06) ** 2) for c in CLUNKS)
        return loc, pc + Vector((0, 0, -0.15)), 28, 5.6, (pc - loc).length, 0.06 + 0.45 * bump, 0.0
    if shot == "CATCH":
        # his hand on the Noob's neck: the catch
        mid = pc.lerp(nn, 0.5)
        loc = mid + rz(heading(E, t)) @ Vector((0.3, -3.2, 0.35))
        return loc, mid, 36, 4.0, (mid - loc).length, 0.12 + 0.8 * math.exp(-((t - T["catch"] - 0.35) / 0.08) ** 2), 0.0
    if shot == "CLIMB":
        # up the cliff to Steve, the Noob dangling
        loc = pc + Vector((-3.5, -5.0, -1.0))
        return loc, pc + Vector((0, 0, -0.8)), 30, 8.0, None, 0.1, 0.0
    if shot == "GRAB":
        # Patch's other hand on Steve's neck; Steve's face
        hs = P7.P6._head(E.S.face, E.S.holder)
        loc = hs + Vector((-1.4, -0.9, 0.35))
        return loc, hs.lerp(pc, 0.3), 36, 4.0, (hs - loc).length, 0.15, 0.0
    # LAND: with them on the way down (in front, a little to the side), pulling back as their
    # feet come down onto the grass, to a wide gold frame of the three of them
    te = min(t, tl())                                       # the camera stays put once they are down
    pcam = patch_at(E, te)
    w = ss(tl() - 1.3, tl(), t)
    loc = pcam + rz(heading(E, te)) @ Vector((0.7, -4.4, 0.5)).lerp(Vector((0.0, -6.8, -1.0)), w)
    look = pcam + Vector((0, 0, lerp(-0.8, -1.3, w)))
    return loc, look, 30, 8.0, None, 0.05, 0.0


# ------------------------------------------------------------------ main
def finish(path, mist_path):
    P4.finish(path, mist_path)


def align(tl):
    b = tl.get("beats", {})
    for k in ("watch", "dive", "upgrade", "catch", "climb", "grab_steve", "land", "end"):
        if k in b:
            T[k] = b[k][0]
    if "patch_allow" in b:
        T["patch_allow"], T["patch_allow_end"] = b["patch_allow"]
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
