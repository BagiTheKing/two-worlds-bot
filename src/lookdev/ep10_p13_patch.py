"""Episode 10 (the finale), part 13: Patch.

The world is back, gold under a gold sky, and the Noob is still falling toward
it, glowing faintly, eyes closed. High above, Patch has watched it all: "I will
not allow this." He dives, faster than anything we have seen; on the way down
his fins snap open and unfold into arms (his upgrade): segmented, his own pale
shell, cyan joints, blocky hands. One hand takes the Noob by the scruff of his
neck. Back up to the island, where Steve still hangs from the stub; the other
hand takes Steve by the neck. And down, both of them dangling, onto the grass of
the world that came back.

The set is part 12's (the island, the restored world of the upgrade episode),
the world now laid out below the island. Patch's arms reach for what they hold
(two-bone IK), and whoever he holds hangs from his hand by the neck.

    python src/lookdev/ep10_p13_patch.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
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
import ep10_p12_normal as P12                                        # noqa: E402
import ep10_p7_reveal as P7                                          # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

T = {"watch": 0.0, "patch_allow": 0.7, "patch_allow_end": 2.3, "dive": 2.45, "upgrade": 4.05, "catch": 5.05,
     "climb": 6.25, "grab_steve": 8.45, "land": 9.35, "end": 12.35, "length": 13.3}
SEG = 0.62                                                    # each arm segment (m)
CARRY_OUT, CARRY_DOWN = 0.82, 0.75                            # where each hand holds its one: out to the side, down (apart)


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


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    E = P12.build(tl, tex_dir, assets, res, samples)
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
    return E


def _arms(E):
    """Two arms in pieces (placed per frame): upper, fore, hand with three fingers; cyan joints."""
    Pt = E.Pt
    shell = None
    for o in Pt.col.objects:
        if o.type == "MESH" and o.data.materials:
            for m in o.data.materials:
                if m and "shell" in m.name:
                    shell = m
    jm = bpy.data.materials.new("patch_joint")
    jm.use_nodes = True
    b = jm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.05, 0.6, 0.9, 1)
    b.inputs["Emission Color"].default_value = (0.02, 0.75, 1.0, 1)
    b.inputs["Emission Strength"].default_value = 4.0

    def box(name, mat):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -900))
        ob = bpy.context.active_object
        ob.name = name
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = 0.01
        mod.segments = 2
        ob.data.materials.append(mat)
        ob.rotation_mode = "QUATERNION"
        return ob
    E.arms = {}
    for side in ("l", "r"):
        E.arms[side] = {"upper": box(f"arm_{side}_upper", shell), "fore": box(f"arm_{side}_fore", shell),
                        "hand": box(f"arm_{side}_hand", shell), "j0": box(f"arm_{side}_j0", jm),
                        "j1": box(f"arm_{side}_j1", jm),
                        "fingers": [box(f"arm_{side}_finger{k}", shell) for k in range(3)]}


def place_seg(ob, a, b, w):
    d = b - a
    L = max(d.length, 1e-4)
    ob.location = (a + b) * 0.5
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    ob.scale = (w, w, L)


def arm(E, side, shoulder, target, out, ext):
    """A two-bone arm from shoulder toward target (ext 0..1: how far out it has unfolded)."""
    A = E.arms[side]
    a = b = SEG * ext
    d = target - shoulder
    dist = min(d.length, (a + b) * 0.999)
    dn = d.normalized() if d.length > 1e-5 else Vector((0, 0, -1))
    # the elbow: bent outward and up
    cos_a = max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist + 1e-6)))
    ang = math.acos(cos_a)
    pole = (out - dn * out.dot(dn)).normalized()
    elbow = shoulder + (dn * math.cos(ang) + pole * math.sin(ang)) * a
    hand = shoulder + dn * dist
    vis = ext > 0.02
    for k in ("upper", "fore", "hand", "j0", "j1"):
        A[k].hide_render = not vis
    for f in A["fingers"]:
        f.hide_render = not vis
    if not vis:
        return hand
    place_seg(A["upper"], shoulder, elbow, 0.075)
    place_seg(A["fore"], elbow, hand, 0.065)
    for j, p in (("j0", shoulder), ("j1", elbow)):
        A[j].location = p
        A[j].scale = (0.1, 0.1, 0.1)
        A[j].rotation_quaternion = Quaternion()
    fd = (hand - elbow).normalized()
    A["hand"].location = hand + fd * 0.05
    A["hand"].rotation_quaternion = Vector((0, 0, 1)).rotation_difference(fd)
    A["hand"].scale = (0.13, 0.13, 0.11)
    side_v = fd.cross(Vector((0, 0, 1)))
    side_v = side_v.normalized() if side_v.length > 1e-4 else Vector((1, 0, 0))
    for k, f in enumerate(A["fingers"]):
        base = hand + fd * 0.11 + side_v * (k - 1) * 0.04
        place_seg(f, base, base + fd * 0.09, 0.03)
    return hand


# ------------------------------------------------------------------ the story, in positions
def bez(p0, p1, p2, p3, u):
    v = 1 - u
    return p0 * v ** 3 + p1 * 3 * v * v * u + p2 * 3 * v * u * u + p3 * u ** 3


def noob_free(E, t):
    """The Noob before the catch: falling, slowly turning, on his back, glowing faintly."""
    s = max(0.0, t - T["watch"])
    return E.noob0 + Vector((0.25 * s, 0.1 * s, -4.5 * s))


def steve_neck(E):
    S = E.S
    pb = S.arm.pose.bones["Head"]
    return S.holder.matrix_world @ S.arm.matrix_world @ pb.head


def noob_neck(E):
    return E.N.neck.matrix_world.translation


def patch_at(E, t):
    """Patch's centre: high up; the dive; the catch; up to Steve; the carry down; the landing."""
    tc = T["catch"] + 0.35
    if t < T["dive"]:
        return E.patch0 + Vector((0, 0, 0.08 * math.sin(t * 3.0)))
    neck_c = noob_free(E, tc) + Vector((0, 0, 1.9))           # about where the Noob's neck is at the catch
    catch_pos = neck_c + Vector((0, 0, 0.95))
    if t < tc:
        u = ss(T["dive"], tc, t) ** 1.25
        return bez(E.patch0, E.patch0 + Vector((-2.0, -1.0, -6.0)), catch_pos + Vector((0.5, 0.3, 6.0)), catch_pos, u)
    ts = T["grab_steve"] + 0.3
    steve_pos = E.steve_neck0 + Vector((0.15, 0.0, 0.85))
    if t < ts:
        u = ss(tc, ts, t)
        return bez(catch_pos, catch_pos + Vector((-1.0, 0, 8.0)), steve_pos + Vector((-2.5, -1.0, -4.0)), steve_pos, u)
    tl = T["end"] - 0.5
    land_pos = E.land_at + Vector((0.6, 0.0, 2.9))
    if t < tl:
        u = ss(ts + 0.15, tl, t)
        return bez(steve_pos, steve_pos + Vector((-6.0, -4.0, 1.0)), land_pos + Vector((4.0, 6.0, 14.0)), land_pos, u)
    return land_pos + Vector((0, 0, 0.6 * ss(tl, T["end"] + 0.6, t)))


# ------------------------------------------------------------------ per frame
def apply(E, t):
    from noob import pose_noob
    from patch import DEFAULTS as PD, set_patch
    shot = which(t)[0]
    # Steve: hanging from the stub as part 12 left him (until Patch has him)
    faces(E, t)
    ts_ = T["grab_steve"] + 0.3
    if t >= ts_ and E.steve_hang is None:
        apply(E, 0.0)          # a shard that starts late: find Steve's hanging neck first
    if t >= ts_:
        a_, b_ = patch_at(E, t), patch_at(E, t + 0.08)
        hv = Vector(((b_ - a_).x, (b_ - a_).y, 0))
        head = math.degrees(math.atan2(-hv.x, hv.y) + math.pi) if hv.length > 1e-3 else getattr(E, "_last_head", 0.0)
        E._last_head = head
        # Steve's rig faces -y at yaw 0 (as the Noob's): the same heading; part 7's base yaw is -57
        E.steve_yaw_add = (head - (90 - 125 - 22)) * ss(ts_, ts_ + 0.5, t)
    else:
        E.steve_yaw_add = 0.0
    E.force_shot = "R1"
    E.lip_frame = int(round(t * FPS))
    P7.cast(E, P7.T["dive"] - 2.6)
    E.force_shot = None
    E.X.root.location = (0, 0, -3000.0)
    E.X.root.scale = (0.001,) * 3
    E.sc.world = E.respawn_world
    if E.steve_hang is None:
        bpy.context.view_layer.update()
        E.steve_neck0 = steve_neck(E)
        E.steve_hang = True
    Pt = E.Pt
    pc = patch_at(E, t)
    # facing: where he flies (and, still, at the start, down at the Noob)
    nxt = patch_at(E, t + 0.08)
    vel = nxt - pc
    fwd = Vector((vel.x, vel.y, 0))
    if t < T["dive"] or fwd.length < 1e-3:
        fwd = Vector(((noob_free(E, t) - pc).x, (noob_free(E, t) - pc).y, 0))
    fwd.normalize()
    pitch = -math.radians(40) * ss(T["dive"], T["dive"] + 0.4, t) * (1 - ss(T["catch"], T["climb"], t))
    Pt.root.location = pc
    Pt.root.rotation_euler = (pitch, 0, math.atan2(-fwd.x, fwd.y) + math.pi)
    for o in Pt.col.objects:
        o.hide_render = False
    Pt.beam.hide_render = True
    vals = dict(PD)
    vals.update({"open": 1.0, "squint": 0.6 if t < T["climb"] else 0.0, "wide": 0.0,
                 "smile": 0.6 * ss(T["land"] + 1.6, T["end"], t)})
    if T["upgrade"] <= t < T["upgrade"] + 0.6:
        vals["glitch"] = 0.4 * math.sin(math.pi * (t - T["upgrade"]) / 0.6)
    set_patch(Pt, vals)
    # the upgrade: the fins open and become arms
    ext = ss(T["upgrade"] + 0.15, T["upgrade"] + 0.75, t)
    for side, sx in (("l", -1), ("r", 1)):
        Pt.fins[side].scale = (1, 1, 1) if ext < 0.05 else (1 - ext + 0.001,) * 3
        Pt.fins[side].rotation_euler = (math.radians(25 * math.sin(t * 18.0)), 0, math.radians(sx * 70 * ext))
    bpy.context.view_layer.update()
    m = Pt.root.matrix_world
    shoulder = {"r": m @ Vector((0.24, 0.02, 0.0)), "l": m @ Vector((-0.24, 0.02, 0.0))}
    outv = {"r": (m.to_3x3() @ Vector((1, 0, 0.4))).normalized(), "l": (m.to_3x3() @ Vector((-1, 0, 0.4))).normalized()}
    # ---- the Noob
    N = E.N
    tc = T["catch"] + 0.35
    held_n = t >= tc
    limp = {"chest_lean": 6, "head_nod": 22, "arm_sl": {"fwd": 8, "out": 8}, "arm_sr": {"fwd": 8, "out": -8},
            "leg_sl": {"fwd": 6 + 8 * math.sin(t * 2.1)}, "leg_sr": {"fwd": -4 + 8 * math.sin(t * 2.1 + 1.2)}}
    if not held_n:
        pose_noob(N, {"chest_lean": 0, "head_nod": -10, "arm_sl": {"fwd": 40, "out": -12}, "arm_sr": {"fwd": 40, "out": -12},
                      "leg_sl": {"fwd": 22}, "leg_sr": {"fwd": 8}, "root_yaw": 0})
        N.root.rotation_euler = (math.radians(-78), math.radians(6 * math.sin(t * 0.5)), math.radians(20 + 5 * t))
        N.root.location = noob_free(E, t)
        hand_r = arm(E, "r", shoulder["r"], shoulder["r"] + outv["r"] * 0.3 + Vector((0, 0, -0.4)) * ext, outv["r"], ext)
        if T["catch"] <= t:                                   # reaching for him
            bpy.context.view_layer.update()
            tgt = noob_neck(E) + Vector((0, 0, 0.06))
            hand_r = arm(E, "r", shoulder["r"], shoulder["r"].lerp(tgt, ss(T["catch"], tc, t)), outv["r"], ext)
    else:
        pose_noob(N, dict(limp, root_yaw=0))
        sw = 7 * math.exp(-(t - tc) * 1.4) * math.sin((t - tc) * 4.5)
        N.root.rotation_euler = (math.radians(sw), math.radians(sw * 0.5), math.atan2(-fwd.x, fwd.y) + math.pi)
        side_r = Vector((outv["r"].x, outv["r"].y, 0)).normalized()
        hand_r = arm(E, "r", shoulder["r"], shoulder["r"] + side_r * CARRY_OUT + Vector((0, 0, -CARRY_DOWN)), outv["r"], ext)
        bpy.context.view_layer.update()
        N.root.location = N.root.location + (hand_r - noob_neck(E)) + Vector((0, 0, -0.08))
    # his faint glow
    E.nglow.location = N.root.location + Vector((0, 0, 1.0))
    E.nglow.data.energy = 120.0 * (1 - ss(T["land"], T["end"], t))
    # ---- Steve
    ts = T["grab_steve"] + 0.3
    if t >= ts:
        S = E.S
        side_l = Vector((outv["l"].x, outv["l"].y, 0)).normalized()
        hand_l = arm(E, "l", shoulder["l"], shoulder["l"] + side_l * CARRY_OUT + Vector((0, 0, -CARRY_DOWN)), outv["l"], ext)
        bpy.context.view_layer.update()
        S.holder.location = S.holder.location + (hand_l - steve_neck(E)) + Vector((0, 0, -0.06))
    else:
        tgt = E.steve_neck0 + Vector((0, 0, 0.04))
        reach = ss(T["grab_steve"] - 0.2, ts, t)
        rest = shoulder["l"] + outv["l"] * 0.3 + Vector((0, 0, -0.4)) * ext
        arm(E, "l", shoulder["l"], rest.lerp(tgt, reach), outv["l"], ext)
    # ---- landing: their feet down on the grass at the end
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
        # close on him as his fins open into arms
        loc = pc + Vector((0.9, -1.1, 0.35))
        return loc, pc + Vector((0, 0, -0.1)), 40, 3.2, (pc - loc).length, 0.1, 0.0
    if shot == "CATCH":
        # his hand on the Noob's neck: the catch
        mid = pc.lerp(nn, 0.55)
        loc = mid + Vector((1.6, -1.8, 0.2))
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
    # LAND: wide and gold: down onto the grass, both of them hanging from him
    land = E.land_at + Vector((0, 0, 1.0))
    loc = land + Vector((-4.5 + 1.5 * u, -13.0 + 3 * u, 4.0 - 1.5 * u))
    return loc, pc.lerp(land, 0.5), 32, 10.0, None, 0.04, 0.0


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
