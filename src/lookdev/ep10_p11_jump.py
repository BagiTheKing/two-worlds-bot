"""Episode 10 (the finale), part 11: the jump.

The cell is close. The Noob lets go of the stub and leaps off the cliff for it,
one hand out, in slow motion. A close look at the cell, turning, coming; a
close look at his hand reaching it, and closing on the glass: he has it. And
Steve, hanging beside him, throws his free hand after him, and misses his
hand by a little: "NOOB!" (slowed). Next: the fall.

The leap is a real one: from where he hangs, a ballistic arc (gravity, no
cheating) chosen so that his reaching hand meets the falling cell at the grab;
after it he hangs from the cell and they fall together. The world runs slow
(about a seventh of real time) through all of it.

    python src/lookdev/ep10_p11_jump.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
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
import ep10_p10_player as P10                                        # noqa: E402
import ep10_p7_reveal as P7                                          # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

G = 9.81
T = {"jump": 0.0, "cell": 2.3, "hand": 3.3, "steve_noob": 4.4, "steve_noob_end": 5.6, "end": 5.8, "length": 6.4}
SLOW = 0.15                                                   # the world's speed in the slow motion
W = {}


def shots():
    return [("JUMP", T["cell"]), ("CELL", T["hand"]), ("HAND", T["steve_noob"]), ("MISS", 1e9)]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "MISS", t0, 1e9


# ------------------------------------------------------------------ time
def rate(t):
    return 1.0 - (1.0 - SLOW) * ss(0.22, 0.6, t)


def clock(t, n=80):
    if t <= 0:
        return t
    h = t / n
    return sum(rate((k + 0.5) * h) for k in range(n)) * h


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    E = P10.build(tl, tex_dir, assets, res, samples)
    # where he hangs at the start (part 10's end), measured
    P10.T.update({"sees": 3.6, "noob_player": 4.5, "steve_dont": 7.8, "steve_dont_end": 10.0})
    E.force_shot = "R1"
    E.lip_frame = 0
    P7.cast(E, P7.T["dive"] - 2.6)
    E.force_shot = None
    bpy.context.view_layer.update()
    N = E.N
    E.root0 = N.root.location.copy()
    E.yaw0 = math.degrees(N.root.rotation_euler.z)
    E.hn0 = P7.P6._head(N.face)
    fo = P7.noob_eye_normal(E)
    E.fo = Vector((fo.x, fo.y, 0)).normalized()
    # the moments (world time)
    W["push"] = 0.12                                          # the legs push off the wall
    W["grab"] = clock(T["hand"] + 0.55)                       # the hand closes on the glass
    W["miss"] = clock(T["steve_noob"] + 0.35)                 # Steve's hand closes on nothing
    # the reach (his pose at the grab) and where his hand is in it, relative to his root
    from noob import pose_noob
    pose_noob(N, dict(REACH, root_yaw=E.yaw0))
    N.root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    E.hand_off = P7.P6._noob_hand(N, "sl").copy()
    # the grab: the cell's near face, out and a little down from where he hangs
    E.grab_c = E.hn0 + E.fo * 2.3 + Vector((0, 0, -1.25))
    E.grab_hand = E.grab_c - E.fo * 0.5 + Vector((0, 0, 0.18))
    root_g = E.grab_hand - E.hand_off
    d = W["grab"] - W["push"]
    E.v0 = (root_g - E.root0 - Vector((0, 0, -0.5 * G * d * d))) / d
    E.Vc = Vector((0, 0, 0)) + (-E.fo) * 0.9 + Vector((0, 0, -1.4))      # the cell's drift: in toward him, falling
    print("JUMP grab", round(W["grab"], 3), "v0", tuple(round(v, 2) for v in E.v0), flush=True)
    return E


REACH = {"chest_lean": 26, "head_nod": -14, "arm_sl": {"fwd": 150, "out": 6}, "arm_sr": {"fwd": -40, "out": 18},
         "leg_sl": {"fwd": -38}, "leg_sr": {"fwd": -8}}


# ------------------------------------------------------------------ the bodies
def cell_at(E, tau):
    s = tau - W["grab"]
    c = E.grab_c + E.Vc * s
    if s > 0:
        c = c + Vector((0, 0, -0.5 * G * 0.55 * s * s))       # his weight on it: down
    axis = E.fo.cross(Vector((0, 0, 1))).normalized()
    q = Quaternion(axis, -0.9 * tau) @ Quaternion(E.fo, 0.3 * math.sin(tau * 0.8))
    return c, q


def noob(E, t, tau):
    from noob import pose_noob
    N = E.N
    push, grab = W["push"], W["grab"]
    if tau < push:                                            # the crouch against the wall, the grip about to go
        u = tau / push
        pz = {"chest_lean": lerp(-4, 14, u), "head_nod": -10, "arm_sl": {"fwd": lerp(12, 70, u), "out": 16},
              "arm_sr": {"fwd": 218, "out": 6}, "leg_sl": {"fwd": lerp(4, 40, u)}, "leg_sr": {"fwd": lerp(-4, 35, u)},
              "root_yaw": E.yaw0}
        pose_noob(N, pz)
        N.root.location = E.root0 + Vector((0, 0, -0.08 * u))
        return
    if tau < grab:                                            # the leap: off the wall, arcing out, the hand going for it
        s = tau - push
        u = s / (grab - push)
        pz = {"chest_lean": lerp(14, REACH["chest_lean"], ss(0, 0.5, u)), "head_nod": lerp(-10, -14, u),
              "arm_sl": {"fwd": lerp(70, 150, ss(0, 0.6, u)), "out": 6},
              "arm_sr": {"fwd": lerp(218, -40, ss(0, 0.5, u)), "out": lerp(6, 18, u)},
              "leg_sl": {"fwd": lerp(40, -38, ss(0, 0.6, u))}, "leg_sr": {"fwd": lerp(35, -8, ss(0, 0.6, u))},
              "root_yaw": E.yaw0}
        pose_noob(N, pz)
        N.root.location = E.root0 + E.v0 * s + Vector((0, 0, -0.5 * G * s * s))
        return
    # he has it: hanging from the cell, swinging under it as they drop
    s = tau - grab
    c, q = cell_at(E, tau)
    sw = 20 * math.exp(-s * 1.5) * math.sin(s * 5.0)
    pz = {"chest_lean": lerp(26, 4, ss(0, 0.4, s)) + sw * 0.3, "head_nod": -18, "arm_sl": {"fwd": lerp(150, 172, ss(0, 0.3, s)), "out": 4},
          "arm_sr": {"fwd": lerp(-40, 30, ss(0, 0.5, s)), "out": 22}, "leg_sl": {"fwd": lerp(-38, 10, ss(0, 0.5, s)) + sw},
          "leg_sr": {"fwd": lerp(-8, -14, ss(0, 0.5, s)) - sw}, "root_yaw": E.yaw0}
    pose_noob(N, pz)
    bpy.context.view_layer.update()
    hand = P7.P6._noob_hand(N, "sl")
    target = c - E.fo * 0.5 + Vector((0, 0, 0.18))
    N.root.location = N.root.location + (target - hand)


def faces(E, t, tau):
    """His set, determined face (then the shock of having it, over nothing); Steve's horror."""
    from faceplate import NOOB_EYES
    from ep09_new import NF, talk
    import ep10_p6_fall as P6
    grab = W["grab"]
    grin = {"both_h": 1.55, "both_ps": 1.0, "both_to": 0.28, "both_tm": 0.18, "both_ti": 0.05, "m_arch": -0.6,
            "m_w": 2.4, "m_o": 0.05, "m_tilt": 0.18}
    effort = {"both_h": 1.4, "both_ps": 0.9, "both_to": 0.35, "both_tm": 0.3, "both_ti": 0.25, "m_arch": -0.2,
              "m_w": 2.0, "m_o": 0.35}
    got = {"both_h": 1.9, "both_ps": 1.0, "both_to": 0.0, "m_arch": -0.5, "m_w": 2.2, "m_o": 0.55}
    face = P6._mixf(P6._mixf(grin, effort, ss(W["push"], W["push"] + 0.2, tau)), got, ss(grab, grab + 0.12, tau))

    def hook(fn):
        for k, v in face.items():
            if k.startswith("both_"):
                for e in NOOB_EYES:
                    fn[f"{e}_{k[5:]}"] = v
            else:
                fn[k] = v
        return fn
    E.noob_face_hook = hook
    E.noob_head = (-6, -2)
    panic = {"both_to": -0.35, "both_tm": -0.35, "both_ti": -0.3, "both_ps": 0.48, "both_py": 0.0,
             "bb_tilt": -0.85, "bb_raise": 1.0, "m_arch": 0.25, "m_w": 1.6}
    E.steve_face = panic
    E.steve_head = (-50, -10)

    # Steve throws his free hand after him (his right, screen-left), leaning out on his gripping arm
    lunge = ss(W["push"] + 0.05, W["miss"], tau)

    def steve_pose(p):
        p = dict(p)
        p["arm_sl"] = {"fwd": lerp(10, 70, lunge), "out": lerp(14, 70, lunge), "elbow": lerp(20, 2, lunge)}
        p["chest_lean"] = lerp(-6, 10, lunge)
        p["chest_twist"] = lerp(0, -18, lunge)
        p["arm_sr"] = {"fwd": lerp(172, 200, lunge), "out": 6, "elbow": 4}     # his grip: up and back (he stays off the wall)
        return p
    E.steve_pose_hook = steve_pose
    E.steve_yaw_add = 0.0


# ------------------------------------------------------------------ per frame
def apply(E, t):
    shot = which(t)[0]
    tau = clock(t)
    P7.set_world(E, False)
    faces(E, t, tau)
    E.force_shot = "R1"
    E.lip_frame = int(round(t * FPS))
    P7.cast(E, P7.T["dive"] - 2.6)
    E.force_shot = None
    E.X.root.location = (0, 0, -3000.0)
    E.X.root.scale = (0.001,) * 3
    E.Pt.root.location = (0, 0, -500)
    for o in E.Pt.col.objects:
        o.hide_render = True
    noob(E, t, tau)
    c, q = cell_at(E, tau)
    E.cell.location = c
    E.cell.rotation_quaternion = q
    E.cell_head.location = c
    tgt = getattr(E, "cell_head_look", None) if shot == "CELL" else None
    v_ = (tgt - c) if tgt is not None else -E.fo
    E.cell_head.rotation_quaternion = Quaternion((0, 0, 1), math.atan2(v_.y, v_.x) + math.pi / 2)
    E.cell_glow.location = c + Vector((0, 0, 0.15))
    for ob, p0, v, w in E.drifters:
        ob.location = p0 + v * (tau + 14.0)
        ob.rotation_euler = tuple(w * (tau + 14.0) * 0.4)
    return camera_set(E, t, tau, shot)


# ------------------------------------------------------------------ cameras
def camera_set(E, t, tau, shot):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    loc, look, lens, fstop, focus, amp, roll = camera(E, t, tau, shot)
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


def camera(E, t, tau, shot):
    N = E.N
    chest = N.torso.matrix_world.translation if hasattr(N, "torso") else N.root.location
    hn = P7.P6._head(N.face)
    hs = P7.P6._head(E.S.face, E.S.holder)
    c, q = cell_at(E, tau)
    side = E.fo.cross(Vector((0, 0, 1))).normalized()
    if side.x > 0:                                           # the open side (away from the island)
        side = -side
    t0, t1 = which(t)[1:]
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, T["end"], t)
    if shot == "JUMP":
        # from the side, a little below: off the wall and out over nothing, his hand going for it; we drift with him
        mid = chest + Vector((0, 0, 0.2))
        loc = mid + side * 3.0 + E.fo * 1.6 + Vector((0, 0, -0.45))
        return loc, mid.lerp(c, 0.25 * u), 30, 4.0, (mid - loc).length, 0.03, 0.0
    if shot == "CELL":
        # close on the cell: turning, coming; his hand, soft, behind it
        loc = c + side * 1.15 - E.fo * 0.35 + Vector((0, 0, 0.12))
        E.cell_head_look = loc
        return loc, c, 55, 2.0, (c - loc).length, 0.02, 0.0
    if shot == "HAND":
        # his hand closing on the glass
        hand = P7.P6._noob_hand(N, "sl")
        mid = hand.lerp(c, 0.3)
        loc = mid - side * 0.95 + Vector((0, 0, 0.55)) + E.fo * 0.25
        return loc, mid, 42, 4.0, (mid - loc).length, 0.02, 0.0
    # MISS: Steve's hand thrown after him, closing on nothing; the Noob falling away beyond it
    hs_hand = P7.P6._steve_hand(E.S, "sl")
    tr = P7.P6._noob_hand(N, "sr")
    # out in the void beyond the Noob, looking back up at Steve: his hand thrown at us, closing on nothing
    loc = hs_hand + Vector((-1.0, 0.45, -0.5))
    look = hs_hand.lerp(hs, 0.35)
    return loc, look, 32, 3.5, (hs_hand - loc).length, 0.08, 0.0


# ------------------------------------------------------------------ main
def finish(path, mist_path):
    P4.finish(path, mist_path)


def align(tl):
    b = tl.get("beats", {})
    for k in ("jump", "cell", "hand", "end"):
        if k in b:
            T[k] = b[k][0]
    if "steve_noob" in b:
        T["steve_noob"], T["steve_noob_end"] = b["steve_noob"]
    if b:
        T["length"] = tl["length"] + 0.3


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
    tl = {"length": T["length"] - 0.3, "beats": {}, "lines": []} if a.timeline == "-" else json.load(open(a.timeline))
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
