"""Episode 10 (the finale), part 6: Null deletes the bridge.

Steve is still lost in his deja vu on the old bridge when the Noob skids up and
shakes him ("STEVE, WAKE UP! THE BRIDGE IS FALLING!"). Out in the void Null
lifts a claw and clicks: the Noob's rainbow parts flash red and are deleted
one after another, the rest lose their supports and fall, then the old oak
planks give way in a wave that chases the two of them toward the island. They
sprint for the lip, the planks under them go, they leap and catch the bridge's
stub side by side, and hang there over nothing. Patch rises out of the void,
thrilled: "OMG, how did I miss this? Look!" (his beam on Null). Steve, hanging
by one hand, turns to him: "I've seen enough." ... "HE'S LITERALLY COMING TO
DELETE US."

The physics is worked out here, not keyframed: every falling piece (a rainbow
part, an oak plank block, a fence post, a splinter) hinges on the edge that
still holds it, under gravity (a rigid body turning about an edge), snaps at
its own angle, then flies free (its centre a ballistic arc from the velocity
it had when it snapped, its spin kept). The two of them fall the same way:
they leave the deck with the speed they ran at, hit the stub's face, slide,
and their hands land on its top when the fall brings them there; the jolt and
the swing after it are a damped spring and a pendulum. A little slow motion
round the leap (the world's clock runs slower; the sound does not).

    python src/lookdev/ep10_p6_fall.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
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

G = 9.81
T = {"a": 0.0, "noob_wake": 0.35, "run": 3.1, "drop": 3.85, "catch": 4.75, "hang": 5.3, "patch_omg": 6.3,
     "patch_omg_end": 9.23, "steve_seen": 9.73, "steve_delete": 11.06, "end": 13.59, "length": 14.5}
W = {}                                      # the world clock's marks (set in plan_time)


# ------------------------------------------------------------------ time
def _rate_shape(t, lo):
    a, b = T["drop"] + 0.05, T["catch"] + 0.08
    if t <= a or t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return 1.0 - (1.0 - lo) * math.sin(math.pi * u) ** 1.5


def _clock(t, lo, n=60):
    a = T["drop"] + 0.05
    if t <= a:
        return t
    h = (t - a) / n
    return a + sum(_rate_shape(a + (k + 0.5) * h, lo) for k in range(n)) * h


def clock(t):
    return _clock(t, W.get("lo", 1.0))


def plan_time(fall_tau):
    """Slow the world round the leap just enough that the fall (fall_tau of world
    time, from the leap to the hands landing) ends on the catch's thump."""
    t_leap, t_land = T["drop"] + 0.1, T["catch"] + 0.05
    lo_a, lo_b = 0.15, 1.0
    for _ in range(40):
        lo = 0.5 * (lo_a + lo_b)
        if _clock(t_land, lo) - _clock(t_leap, lo) > fall_tau:
            lo_b = lo
        else:
            lo_a = lo
    W["lo"] = 0.5 * (lo_a + lo_b)
    W["leap"] = clock(t_leap)
    W["land"] = W["leap"] + fall_tau


# ------------------------------------------------------------------ rigid pieces
class Piece:
    """A rigid piece resting at (c0, q0); from t_rel it turns about a hinge (a point
    h on the edge that holds it, an axis a) under gravity, snaps at theta_b and flies:
    the centre on a ballistic arc, the spin kept. Or it is deleted at t_del."""

    def __init__(self, ob, c0, q0, size):
        self.ob, self.c0, self.q0, self.size = ob, Vector(c0), Quaternion(q0), Vector(size)
        self.t_rel = None
        self.t_del = None
        self.track = None
        self.extra = []                      # things riding on it (posts): (ob, offset matrix)

    def release(self, t_rel, hinge, axis, theta_b, spin=(0, 0, 0), shudder=0.25, push=(0, 0, 0)):
        self.t_rel = t_rel
        self.shudder = shudder
        h, a = Vector(hinge), Vector(axis).normalized()
        r0 = self.c0 - h
        r_perp = r0 - a * r0.dot(a)
        d = r_perp.length
        # inertia about the hinge (box about an axis through its edge): k2 = I/m
        sx, sy, sz = self.size
        ax = [abs(a.x), abs(a.y), abs(a.z)]
        i_c = (ax[0] * (sy * sy + sz * sz) + ax[1] * (sx * sx + sz * sz) + ax[2] * (sx * sx + sy * sy)) / 12.0
        k2 = i_c + d * d
        dt = 1.0 / 600
        th, om, tt = 0.0, 0.0, 0.0
        out = [(0.0, 0.0, 0.0)]
        while th < theta_b and tt < 3.0:
            r = Quaternion(a, th) @ r_perp
            torque = a.dot(r.cross(Vector((0, 0, -G))))         # per unit mass
            om += torque / k2 * dt
            th += om * dt
            tt += dt
            out.append((tt, th, om))
        self.hinge, self.axis, self.track = h, a, out
        self.t_snap = t_rel + tt
        self.th_b, self.om_b = th, om
        qb = Quaternion(a, th)
        self.c_b = h + qb @ r0
        self.v_b = (a * om).cross(self.c_b - h) + Vector(push)
        self.w_b = a * om + Vector(spin)
        self.q_b = qb @ self.q0

    def drop(self, t_rel, spin=(0, 0, 0), push=(0, 0, 0), shudder=0.15):
        """Nothing holds it: it simply falls (with a nudge and a turn)."""
        self.t_rel = t_rel
        self.shudder = shudder
        self.track = [(0.0, 0.0, 0.0)]
        self.hinge, self.axis = self.c0.copy(), Vector((0, 1, 0))
        self.t_snap = t_rel
        self.c_b, self.v_b, self.w_b, self.q_b = self.c0.copy(), Vector(push), Vector(spin), self.q0.copy()

    def at(self, tau):
        """(centre, rotation, visible)"""
        if self.t_del is not None and tau >= self.t_del:
            return self.c0, self.q0, False
        if self.t_rel is None or tau < self.t_rel:
            c, q = self.c0.copy(), self.q0.copy()
            if self.t_rel is not None and tau > self.t_rel - self.shudder:      # it creaks first
                k = (tau - (self.t_rel - self.shudder)) / self.shudder
                j = 0.012 * k * math.sin(tau * 97.0 + self.c0.x * 3.1) + 0.006 * k * math.sin(tau * 151.0)
                q = Quaternion(self.axis, j * 2.2) @ q
                c.z -= 0.01 * k * abs(math.sin(tau * 71.0))
            return c, q, True
        if tau < self.t_snap:
            s = tau - self.t_rel
            tr = self.track
            i = min(len(tr) - 1, max(0, int(s * 600)))
            th = tr[i][1]
            qh = Quaternion(self.axis, th)
            return self.hinge + qh @ (self.c0 - self.hinge), qh @ self.q0, True
        s = tau - self.t_snap
        c = self.c_b + self.v_b * s + Vector((0, 0, -0.5 * G * s * s))
        w = self.w_b
        wl = w.length
        q = (Quaternion(w / wl, wl * s) if wl > 1e-6 else Quaternion()) @ self.q_b
        return c, q, c.z > -240.0

    def place(self, tau, offset=None):
        c, q, vis = self.at(tau)
        ob = self.ob
        ob.rotation_mode = "QUATERNION"
        ob.rotation_quaternion = q
        ob.location = c if offset is None else c + q @ offset
        ob.hide_render = not vis
        for o, off in self.extra:
            m = Matrix.Translation(c) @ q.to_matrix().to_4x4() @ off
            o.matrix_world = m
            o.hide_render = not vis
        return c, q, vis


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    E = P4.build(tl, assets, res, samples)
    sc = E.sc
    plan = E.plan
    I = E.I
    for p, ob in zip(plan.parts, E.objs):                   # his world, finished
        ob.location = p["at"]
        ob.scale = (1, 1, 1)
        ob["flash"] = 0.0
        ob.hide_render = False
    E.giz.draw([])
    P4._beams(E, [])
    for o in E.tool.children_recursive + [E.tool]:
        o.hide_render = True
    from roblox import make_part, plastic_material
    col = bpy.data.collections.new("fall")
    sc.collection.children.link(col)
    E.col = col
    rng = random.Random(61)
    # ---------------------------------------------------- the old bridge, rebuilt as blocks
    from island import BRIDGE_Y
    from world import voxel_mesh
    l0, r0 = I.chasm(BRIDGE_Y)
    deck = I.bridge_z
    span = r0 - l0
    reach = r0 - 0.66 * span
    Y0 = int(BRIDGE_Y)
    XE = int(math.ceil(r0)) - 1                              # the stub: blocks from XE on stay (on the island)
    E.XE, E.deck, E.Y0 = XE, deck, Y0
    E.lip = Vector((XE, BRIDGE_Y, deck))
    old_mesh = I.bridge
    mats = list(old_mesh.data.materials)
    plank_m = next((m for m in mats if "plank" in m.name), mats[0])
    # the stub, alone (the cells over the chasm go, as blocks of their own)
    stub = {}

    def land(x, y, z):
        h = I.H.get((x, y))
        return h is not None and z < h

    for x in range(XE, int(math.ceil(r0)) + 3):
        for dy in (-1, 0, 1):
            if not land(x, Y0 + dy, deck - 1):
                stub[(x, Y0 + dy, deck - 1)] = "planks"
    for x in range(int(math.ceil(r0)) - 1, int(math.ceil(r0)) + 3):
        for dy in (-1, 0, 1):
            for z in range(deck - 4, deck - 1):
                if not land(x, Y0 + dy, z):
                    stub.setdefault((x, Y0 + dy, z), "planks" if z == deck - 2 else "post")
    print("STUB", sorted({k[0] for k in stub}), {(x, y): I.H.get((x, y)) for x in range(XE, XE + 4) for y in (Y0 - 1, Y0, Y0 + 1)},
          flush=True)
    post_m = next((m for m in mats if "log" in m.name), plank_m)
    KS = {"planks": {"top": plank_m, "side": plank_m, "bottom": plank_m},
          "post": {"top": post_m, "side": post_m, "bottom": post_m}}
    old_mesh.hide_render = True
    old_mesh.hide_viewport = True
    E.stub = voxel_mesh(sc, "old_bridge_stub", stub, KS)
    for f in I.fences:
        f.hide_render = True
    E.pieces = []
    E.blocks = {}

    def block(name, c, size, mat, bevel=0.012):
        bpy.ops.mesh.primitive_cube_add(size=1, location=c)
        ob = bpy.context.active_object
        ob.name = name
        ob.scale = size
        bpy.ops.object.transform_apply(scale=True)
        if bevel:
            mod = ob.modifiers.new("bevel", "BEVEL")
            mod.width = bevel
            mod.segments = 1
        ob.data.materials.append(mat)
        for c_ in ob.users_collection:
            c_.objects.unlink(ob)
        col.objects.link(ob)
        _uv_cube(ob, size)
        return ob
    E.block = block
    xs = list(range(int(math.floor(reach)), XE))
    for x in xs:
        for dy in (-1, 0, 1):
            if x < reach + 1.2 and (dy + x) % 2 == 0:
                continue
            c = Vector((x + 0.5, Y0 + dy + 0.5, deck - 0.5))
            ob = block(f"plank_{x}_{dy}", c, (1, 1, 1), plank_m, bevel=0.0)
            pc = Piece(ob, c, Quaternion(), (1, 1, 1))
            pc.kind, pc.x, pc.dy = "plank", x, dy
            E.pieces.append(pc)
            E.blocks[(x, dy)] = pc
    # the fences: posts every 2 blocks and rails between them, each riding on its block
    for side, dy in ((-1.62, -1), (1.62, 1)):
        ys = BRIDGE_Y + 0.5 + side
        for x in range(int(math.floor(reach)) + 2, XE + 3, 2):
            host = E.blocks.get((x, dy)) or E.blocks.get((x - 1, dy)) or E.blocks.get((x, 0))
            post = block(f"post_{x}_{dy}", (x + 0.5, ys, deck + 0.5), (0.25, 0.25, 1.0), plank_m, bevel=0.0)
            if x >= XE:
                continue
            if host:
                host.extra.append((post, Matrix.Translation(Vector((x + 0.5, ys, deck + 0.5)) - host.c0)))
            else:
                post.hide_render = True
            for zz in (deck + 0.38, deck + 0.8):
                rail = block(f"rail_{x}_{zz:.2f}_{dy}", (x - 0.5, ys, zz), (2.0, 0.12, 0.19), plank_m, bevel=0.0)
                if host:
                    host.extra.append((rail, Matrix.Translation(Vector((x - 0.5, ys, zz)) - host.c0)))
                else:
                    rail.hide_render = True
        # the stub's own fence: posts and rails over the island stay
        x0, x1 = XE + 1, int(math.ceil(r0)) + 2
        for zz in (deck + 0.38, deck + 0.8):
            block(f"rail_stub_{zz:.2f}_{dy}", ((x0 + x1) / 2 + 0.5, ys, zz), (x1 - x0, 0.12, 0.19), plank_m, bevel=0.0)
    # ---------------------------------------------------- the rainbow parts and his reach
    E.rainbow = []
    for p_, ob_ in zip(plan.parts, E.objs):
        if p_["kind"] != "bridge":
            continue
        if p_["colour"] == "Bright violet":
            ob_.hide_render = True
            continue
        pc = Piece(ob_, p_["at"], Quaternion(), p_["size"])
        pc.kind = "rainbow"
        E.rainbow.append(pc)
    pa = make_part(col, "rbx_bridge_reach", (3.3, 3.0, 0.5), "Bright violet", plastic_material())
    c = Vector((plan.bridge_end.x + 0.6, plan.bridge_end.y, plan.deck - 0.25 + 0.045))
    pa.location = c
    pr = Piece(pa, c, Quaternion(), (3.3, 3.0, 0.5))
    pr.kind = "reach"
    E.rainbow.append(pr)
    E.rainbow.sort(key=lambda p: p.c0.x)
    # ---------------------------------------------------- splinters and crumbs (a pool, placed per frame)
    E.bits = []
    dirt_m = next((m for m in bpy.data.materials if m.name.startswith("dirt") or "dirt" in m.name), plank_m)
    for k in range(70):
        s = rng.uniform(0.07, 0.16)
        m = plank_m if k < 46 else dirt_m
        ob = block(f"bit_{k}", (0, 0, -900), (s, s * rng.uniform(0.5, 1.6), s), m, bevel=0.0)
        ob.hide_render = True
        E.bits.append(ob)
    E.bit_specs = []                         # (ob, t0, c0, v0, w)
    # the deleted parts' glitch pixels
    E.px = []
    from roblox import lin as rl
    for k, rgb in enumerate([(255, 40, 60)] * 10 + [(255, 60, 220)] * 10 + [(60, 230, 255)] * 6):
        m = bpy.data.materials.new(f"delpx_{k}")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rl(rgb), 1)
        b.inputs["Emission Color"].default_value = (*rl(rgb), 1)
        b.inputs["Emission Strength"].default_value = 6.0
        ob = block(f"delpx_{k}", (0, 0, -900), (0.09, 0.09, 0.09), m, bevel=0.0)
        ob.hide_render = True
        ob.visible_shadow = False
        E.px.append(ob)
    E.px_specs = []
    E.Pt.root.location = (0, 0, -500)
    E.Pt.root.scale = (1.0, 1.0, 1.0)
    E.beam_pitch = float(os.environ.get("BEAM_PITCH", "-55"))
    E.cam_up = Vector((0, 0, 1))
    sc.render.motion_blur_shutter = 0.45
    _measure(E)
    _schedule(E, rng)
    return E


def _uv_cube(ob, size):
    """Block UVs: every face shows one texture tile per metre (planks read as Minecraft blocks)."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new()
    uv = me.uv_layers.active.data
    for p in me.polygons:
        n = p.normal
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > 0.5:
                u_, v_ = v.x, v.y
            elif abs(n.x) > 0.5:
                u_, v_ = v.y, v.z
            else:
                u_, v_ = v.x, v.z
            uv[li].uv = (u_ + 0.5, v_ + 0.5)


# ------------------------------------------------------------------ the characters' numbers
def _steve_hand(S, side):
    from pose import ARM
    pb = S.arm.pose.bones[ARM[side][1]]
    m = S.holder.matrix_world @ S.arm.matrix_world
    return m @ (pb.tail + (pb.tail - pb.head) * 0.6)


def _noob_hand(N, side):
    return N.arms[side].matrix_world @ Vector((0, 0, -N.arm_len))


def _measure(E):
    """How far up their hands reach in the poses they leap and hang in."""
    from pose import pose
    from noob import pose_noob
    S, N = E.S, E.N
    # the Noob's arm length (pivot to the end of the arm mesh, in the pivot's own units)
    piv = E.N.arms["sl"]
    zs = []
    for ch in piv.children_recursive:
        if ch.type == "MESH":
            m = piv.matrix_world.inverted() @ ch.matrix_world
            zs += [(m @ Vector(c)).z for c in ch.bound_box]
    N.arm_len = -min(zs) * 0.93 if zs else 1.6
    S.holder.location = (0, 0, 0)
    S.holder.rotation_euler = (0, 0, math.radians(90))
    N.root.location = (0, 0, 0)
    for name, sp, npz in (("hang", HANG_S, HANG_N), ("reach", REACH_S, REACH_N)):
        pose(S.arm, sp)
        pz = dict(npz)
        pz["root_yaw"] = 90
        pose_noob(N, pz)
        bpy.context.view_layer.update()
        hs = 0.5 * (_steve_hand(S, "sl") + _steve_hand(S, "sr"))
        hn = 0.5 * (_noob_hand(N, "sl") + _noob_hand(N, "sr"))
        setattr(E, "hs_" + name, hs.copy())
        setattr(E, "hn_" + name, hn.copy())
    print("MEASURE steve hang", tuple(round(v, 2) for v in E.hs_hang), "reach", tuple(round(v, 2) for v in E.hs_reach),
          "noob hang", tuple(round(v, 2) for v in E.hn_hang), "reach", tuple(round(v, 2) for v in E.hn_reach),
          "arm", round(N.arm_len, 2), flush=True)


# poses (Steve: rig terms, facing +x via the holder; the Noob: noob terms)
HANG_S = {"chest_lean": -9, "head_nod": -22, "hips_drop": 0.0,
          "arm_sl": {"fwd": 171, "out": 5, "elbow": 2}, "arm_sr": {"fwd": 171, "out": 5, "elbow": 2},
          "foot_sl": {"y": 0.05, "z": 0.0}, "foot_sr": {"y": -0.05, "z": 0.0}}
REACH_S = {"chest_lean": 14, "head_nod": -20, "arm_sl": {"fwd": 150, "out": 10, "elbow": 10},
           "arm_sr": {"fwd": 150, "out": 10, "elbow": 10}, "foot_sl": {"y": 0.5, "z": 0.45}, "foot_sr": {"y": 0.3, "z": 0.2}}
HANG_N = {"chest_lean": -8, "head_nod": -20, "arm_sl": {"fwd": 172, "out": 4}, "arm_sr": {"fwd": 172, "out": 4},
          "leg_sl": {"fwd": 4}, "leg_sr": {"fwd": -4}}
REACH_N = {"chest_lean": 14, "head_nod": -20, "arm_sl": {"fwd": 150, "out": 8}, "arm_sr": {"fwd": 150, "out": 8},
           "leg_sl": {"fwd": -30}, "leg_sr": {"fwd": -12}}


# ------------------------------------------------------------------ the choreography (world clock)
def _schedule(E, rng):
    """When everything goes. The rainbow first (Null's clicks), then the planks in a
    wave from the broken end that catches up with the two of them at the lip."""
    deck, XE = E.deck, E.XE
    # where they stand and run (lanes on the bridge)
    E.lane = {"S": E.Y0 - 0.75 + 0.5, "N": E.Y0 + 0.75 + 0.5}       # y of Steve and the Noob, side by side
    E.grip_x = XE - 0.03                                                 # their hands: hooked over the stub's edge
    E.x_hit = {"S": E.grip_x - E.hs_hang.x, "N": E.grip_x - E.hn_hang.x}  # their roots, hanging (fronts on the stub)
    # their leap: from the deck, at their running speed, a little hop
    E.v_run = {"S": 4.2, "N": 4.5}
    E.hop = 0.9
    # the fall, from the leap to the hands landing on the stub's top
    rise = {"S": E.hs_hang.z, "N": E.hn_hang.z}
    fall = {}
    for k in ("S", "N"):
        # hands land when root.z + rise = deck: hop*t - g t^2 / 2 = -rise
        a_, b_, c_ = 0.5 * G, -E.hop, -rise[k]
        fall[k] = (-b_ + math.sqrt(b_ * b_ - 4 * a_ * c_)) / (2 * a_)
    E.fall = fall
    plan_time(max(fall.values()))
    W["leap_S"] = W["leap"] + (fall["N"] - fall["S"]) if fall["N"] > fall["S"] else W["leap"]
    W["leap_N"] = W["leap"] + (fall["S"] - fall["N"]) if fall["S"] > fall["N"] else W["leap"]
    # where they leap from (both reach the stub's face at the same moment as they run)
    E.x_leap = {k: E.x_hit[k] - E.v_run[k] * 0.24 for k in ("S", "N")}
    # runs: from their spots at "run" to the leap, constant acceleration then flat out
    E.x0 = {"S": XE - 2.55, "N": XE - 3.25}
    print("FALL", {k: round(v, 3) for k, v in fall.items()}, "slow", round(W["lo"], 3), "leap", round(W["leap"], 3),
          "land", round(W["land"], 3), "XE", XE, "deck", deck, flush=True)
    # ------------------------------------------------ Null's clicks: the rainbow
    rb = E.rainbow
    E.clicks = []
    t0 = T["noob_wake"] + 0.15
    order = [0, 2, 4, 1, 3, 5]                               # far to near, every other one deleted, the rest fall
    deleted = {0, 2, 4}
    for i, k in enumerate(order):
        if k >= len(rb):
            continue
        p = rb[k]
        tk = t0 + 0.33 * i
        if k in deleted:
            p.t_del = tk + 0.14
            E.clicks.append((tk, p))
        else:
            # the neighbours gone, it drops: a turn about its long axis, a nudge outward
            p.drop(tk + 0.05, spin=(rng.uniform(-0.6, 0.6), rng.uniform(-1.2, 1.2), rng.uniform(-0.4, 0.4)),
                   push=(rng.uniform(-0.3, 0.3), rng.uniform(-0.4, 0.4), 0.0))
    t_rb = t0 + 0.33 * len(order)
    # his violet reach part, last: it hinges off the oak's broken end and goes
    # ------------------------------------------------ the planks: a wave, tied to the runners
    xs = sorted({p.x for p in E.pieces if p.kind == "plank"})
    # when each column goes: the far ones as the rainbow finishes, then faster, the last two under them at the leap
    near = XE - 1
    t_last = W["leap"] - 0.06
    for x in xs:
        if x >= near:
            tx = t_last
        elif x == near - 1:
            tx = W["leap"] - 0.32
        else:
            k = (near - 1 - x)                                # 1, 2, ... back toward the broken end
            tx = W["leap"] - 0.32 - 0.24 * k ** 0.85
            tx = max(tx, t_rb - 0.25 + 0.05 * (xs[-1] - x) * 0)
        for dy in (-1, 0, 1):
            p = E.blocks.get((x, dy))
            if not p:
                continue
            tt = tx + rng.uniform(-0.05, 0.05) + 0.03 * abs(dy)
            # each block hinges on its edge toward the island (the side still holding it) and snaps
            h = Vector((x + 1.0, p.c0.y, E.deck))
            p.release(tt, h, (0, -1, 0), math.radians(rng.uniform(18, 48)),
                      spin=(rng.uniform(-1.5, 1.5), rng.uniform(-0.8, 0.8), rng.uniform(-1.2, 1.2)),
                      shudder=0.3 if x < near else 0.45)
            # splinters where it tears
            for _ in range(2):
                E.bit_specs.append(("plank", p.t_snap, Vector((x + 1.0, p.c0.y + rng.uniform(-0.45, 0.45), E.deck - rng.uniform(0, 0.3))),
                                    Vector((rng.uniform(-1.2, 0.6), rng.uniform(-1.0, 1.0), rng.uniform(0.5, 2.2))),
                                    Vector((rng.uniform(-9, 9), rng.uniform(-9, 9), rng.uniform(-9, 9)))))
    # the reach part: it rests on the first oak columns; it goes with them, tipping off their end
    rp = next(p for p in E.rainbow if p.kind == "reach")
    first = min(xs)
    t_first = min(p.t_rel for p in E.pieces if p.kind == "plank" and p.x == first)
    rp.release(t_first + 0.05, Vector((rp.c0.x + 1.65, rp.c0.y, rp.c0.z - 0.25)), (0, -1, 0), math.radians(35),
               spin=(0.4, 0.3, -0.3))
    # crumbs off the stub when their hands slam on it (and when their feet scrabble)
    for k in ("S", "N"):
        y = E.lane[k]
        for _ in range(7):
            E.bit_specs.append(("dirt", W["land"] + rng.uniform(0.0, 0.06),
                                Vector((XE + rng.uniform(-0.05, 0.2), y + rng.uniform(-0.4, 0.4), E.deck - rng.uniform(0.0, 0.2))),
                                Vector((rng.uniform(-1.4, -0.2), rng.uniform(-0.8, 0.8), rng.uniform(0.2, 1.6))),
                                Vector((rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(-8, 8)))))
        for j in range(4):
            E.bit_specs.append(("dirt", W["land"] + 0.5 + 0.55 * j + rng.uniform(0, 0.2),
                                Vector((XE - 0.05, y + rng.uniform(-0.3, 0.3), E.deck - 1.4 - rng.uniform(0, 0.5))),
                                Vector((rng.uniform(-0.5, -0.1), rng.uniform(-0.3, 0.3), rng.uniform(0.0, 0.5))),
                                Vector((rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(-6, 6)))))
    E.bit_specs = E.bit_specs[:len(E.bits)]


# ------------------------------------------------------------------ per frame
def apply(E, t):
    tau = clock(t)
    for p in E.pieces + E.rainbow:
        p.place(tau)
    # splinters and crumbs
    for ob, spec in zip(E.bits, E.bit_specs):
        kind, t0, c0, v0, w = spec
        s = tau - t0
        if s < 0 or s > 6.0:
            ob.hide_render = True
            continue
        c = c0 + v0 * s + Vector((0, 0, -0.5 * G * s * s))
        ob.location = c
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = tuple(w * s)
        ob.hide_render = c.z < -200
    for ob in E.bits[len(E.bit_specs):]:
        ob.hide_render = True
    # Null's clicks: a red selection box, then gone in a spray of pixels
    specs = []
    pxi = 0
    for tk, p in E.clicks:
        if tk <= tau < p.t_del:
            m = Matrix.Translation(p.c0)
            specs.append({"m": m, "size": tuple(p.size), "mode": "outline", "mat": "red", "w": 0.05})
        s = tau - p.t_del
        if 0 <= s < 0.7:
            r = random.Random(int(p.c0.x * 100))
            for j in range(8):
                if pxi >= len(E.px):
                    break
                ob = E.px[pxi]
                pxi += 1
                d = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-0.2, 1)))
                st = Vector((r.uniform(-0.5, 0.5) * p.size[0], r.uniform(-0.5, 0.5) * p.size[1], 0))
                ob.location = p.c0 + st + d * (2.2 * s) + Vector((0, 0, -2.0 * s * s))
                k = max(0.0, 1 - s / 0.7)
                ob.scale = (k, k, k)
                ob.hide_render = False
    for ob in E.px[pxi:]:
        ob.hide_render = True
    E.giz.draw(specs)
    look = cast(E, t, tau)
    return look


def cast(E, t, tau):
    """Steve, the Noob, Patch, Null and the camera."""
    from pose import pose
    from noob import pose_noob
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from ep09_new import SF, NF, talk, flat, unflat
    from patch import DEFAULTS as PD, set_patch
    from stage import place_null_lights
    from null import null_smile
    S, N, X, Pt = E.S, E.N, E.X, E.Pt
    deck, XE = E.deck, E.XE
    f_render = int(round(t * FPS))
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    st_s, st_n = body(E, "S", t, tau), body(E, "N", t, tau)
    # ------------------------------------------------ Steve
    sp = flat(lib["idle (Benly 2.2)"])
    sp.update(flat(st_s["pose"]))
    pose(S.arm, unflat(sp))
    S.holder.rotation_euler = (0, 0, math.radians(st_s["yaw"]))
    S.holder.location = st_s["loc"]
    if st_s.get("grip"):
        bpy.context.view_layer.update()
        hands = [_steve_hand(S, sd) for sd in st_s["grip_sides"]]
        hc = sum(hands, Vector()) / len(hands)
        S.holder.location = Vector(st_s["loc"]) + (st_s["grip"] - hc)
    fs = {f"{e}_{k}": v for e in EYES for k, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    face = st_s["face"]
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
    # ------------------------------------------------ the Noob
    npz = dict(st_n["pose"])
    npz["root_yaw"] = st_n["yaw"]
    pose_noob(N, npz)
    N.root.location = st_n["loc"]
    if st_n.get("grip"):
        bpy.context.view_layer.update()
        hands = [_noob_hand(N, sd) for sd in st_n["grip_sides"]]
        hc = sum(hands, Vector()) / len(hands)
        N.root.location = Vector(st_n["loc"]) + (st_n["grip"] - hc)
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    for k, v in st_n["face"].items():
        if k.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{k[5:]}"] = v
        else:
            fn[k] = v
    talk(fn, E.mouth.get("noob", {}).get(f_render))
    set_face(N.face, fn)
    # ------------------------------------------------ Patch
    patch(E, t, tau)
    # ------------------------------------------------ Null, out in the void, clicking
    X.root.scale = (1.6,) * 3
    X.root.location = (XE - 26.0, E.Y0 + 7.0, deck - 8.0)
    X.root.rotation_euler = (math.radians(12), 0, math.radians(-90 + 180 + 15))
    click = 0.0
    for tk, p in E.clicks:
        click = max(click, math.exp(-((tau - tk) / 0.06) ** 2))
    lift = ss(T["noob_wake"] - 0.2, T["noob_wake"] + 0.3, tau)
    X.arms["sl"].rotation_euler = (math.radians(-70 - 40 * lift - 8 * click), math.radians(10), 0)
    X.forearms["sl"].rotation_euler = (math.radians(-20 * lift + 14 * click), 0, 0)
    X.arms["sr"].rotation_euler = (math.radians(-70), math.radians(-10), 0)
    X.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0.9 * tau)
    X.orbit2.rotation_euler = (math.radians(-12), math.radians(14), -0.6 * tau)
    place_null_lights(X, fade=1.0)
    null_smile(1.0)
    return camera_set(E, t, tau)


# ------------------------------------------------------------------ bodies
def run_x(E, k, tau):
    """Along the bridge (+x) from their spot at "run" to the leap; flat out."""
    t0 = T["run"] + (0.22 if k == "S" else 0.16)
    x0, x1 = E.x0[k], E.x_leap[k]
    v = E.v_run[k]
    tl = W["leap_" + k]
    # accelerate at a constant rate from t0, then run at v, arriving at x1 exactly at tl
    dur = tl - t0
    d = x1 - x0
    # time to reach v at rate a: v/a; distance: v*dur - v^2/(2a) = d  ->  a = v^2 / (2 (v*dur - d))
    if v * dur - d > 0 and v * v / (2 * (v * dur - d)) * dur > v:
        a = v * v / (2 * (v * dur - d))
    else:
        a = 2 * d / (dur * dur)
        v = a * dur
    ta = v / a
    s = max(0.0, tau - t0)
    if s < ta:
        return x0 + 0.5 * a * s * s, a * s
    return x0 + 0.5 * a * ta * ta + v * (s - ta), v


def body(E, k, t, tau):
    """Where he is, which way he faces, his pose and face."""
    from ep09_new import SF, NF
    deck, XE = E.deck, E.XE
    steve = k == "S"
    y_l = E.lane[k]
    y_0 = E.Y0 + 0.5 - 0.5 if steve else E.Y0 + 0.5 - 0.5
    t_turn = T["run"] + (0.0 if steve else 0.04)
    leap = W["leap_" + k]
    out = {}
    if tau < t_turn:
        # ---- before: Steve frozen in his memory, head down; the Noob skids up and shakes him
        if steve:
            x = E.x0["S"]
            sh = shake(tau)
            wake = ss(T["run"] - 0.55, T["run"] - 0.05, tau)           # he comes to
            out["loc"] = Vector((x, E.Y0 + 0.5 - 0.0, deck))
            out["yaw"] = -90
            out["pose"] = {"chest_lean": lerp(6, -2, wake) + 3 * sh[0], "chest_side": 4 * sh[1],
                           "head_nod": lerp(14, -6, wake) + 6 * sh[1], "head_tilt": lerp(4, 0, wake) + 3 * sh[0],
                           "arm_sl": {"fwd": 6, "out": 10, "elbow": 14}, "arm_sr": {"fwd": 6, "out": 10, "elbow": 16}}
            u = wake
            out["face"] = {"both_to": lerp(-0.2, 0.36, u), "both_tm": lerp(-0.15, 0.42, u), "both_ti": lerp(0.25, 0.34, u),
                           "both_ps": lerp(0.85, 0.6, u), "both_py": lerp(-0.5, 0.15, u), "bb_tilt": lerp(-0.9, -0.6, u),
                           "bb_raise": lerp(0.35, 0.7, u), "m_arch": lerp(0.2, -0.1, u)}
        else:
            # skids in from the broken end, stops in front of him, hands on his shoulders
            t_stop = T["noob_wake"] + 0.05
            xs = E.x0["N"]
            if tau < t_stop:
                u = (tau + 0.6) / (t_stop + 0.6)
                x = xs - 2.6 * (1 - u) ** 2
            else:
                x = xs
            ph = 2 * math.pi * 2.6 * tau
            runw = 1 - ss(t_stop - 0.15, t_stop + 0.1, tau)
            sh = shake(tau)
            grab = ss(t_stop - 0.1, t_stop + 0.15, tau)
            out["loc"] = Vector((x, E.Y0 + 0.5 - 0.35, deck + 0.06 * abs(math.sin(ph)) * runw))
            out["yaw"] = 90 + 18 * grab
            sw = math.sin(ph) * runw
            out["pose"] = {"chest_lean": 10 * runw + 8 * grab, "head_nod": -4,
                           "arm_sl": {"fwd": lerp(-55 * sw, 80 + 10 * sh[0], grab), "out": lerp(10, -6, grab)},
                           "arm_sr": {"fwd": lerp(55 * sw, 80 - 10 * sh[0], grab), "out": lerp(10, -6, grab)},
                           "leg_sl": {"fwd": 40 * sw - 14 * (1 - runw)}, "leg_sr": {"fwd": -40 * sw + 10 * (1 - runw)}}
            out["face"] = dict(NF["shout"])
        return out
    # ---- the turn and the run (side by side, into their lanes)
    if tau < leap:
        x, v = run_x(E, k, tau)
        tu = ss(t_turn, t_turn + 0.26, tau)
        yaw0, yaw1 = (-90, 90) if steve else (90, 90)
        yaw = lerp(yaw0, yaw1 + (180 if steve else 0) * 0, tu) if steve else 90
        if steve:
            yaw = -90 + 180 * tu                                     # he spins round (toward screen-left... via -y)
        y = lerp(E.Y0 + 0.5 - (0.0 if steve else 0.35), y_l, ss(t_turn, t_turn + 0.45, tau))
        ph = 2 * math.pi * 2.9 * max(0.0, tau - t_turn - 0.12)
        sw = math.sin(ph)
        runw = ss(t_turn + 0.08, t_turn + 0.3, tau)
        # reaching forward in the last strides (the planks go behind them)
        lunge = ss(leap - 0.22, leap, tau)
        out["loc"] = Vector((x, y, deck + 0.07 * abs(math.sin(ph)) * runw))
        out["yaw"] = yaw
        if steve:
            run = {"chest_lean": 18 * runw, "chest_twist": 10 * sw * runw, "head_nod": -8, "hips_drop": 0.16 * runw,
                   "arm_sl": {"fwd": -60 * sw * runw, "elbow": 88 * runw, "out": 8},
                   "arm_sr": {"fwd": 60 * sw * runw, "elbow": 88 * runw, "out": 8},
                   "foot_sl": {"y": -0.55 * sw * runw, "z": max(0.0, 0.5 * math.sin(ph + 1.2)) * runw},
                   "foot_sr": {"y": 0.55 * sw * runw, "z": max(0.0, 0.5 * math.sin(ph + 1.2 + math.pi)) * runw}}
            out["pose"] = _mix(run, REACH_S, lunge)
            out["face"] = dict(SF["scared"])
        else:
            run = {"chest_lean": 12 * runw, "head_nod": -2, "arm_sl": {"fwd": -62 * sw * runw, "out": 10},
                   "arm_sr": {"fwd": 62 * sw * runw, "out": 10}, "leg_sl": {"fwd": 46 * sw * runw},
                   "leg_sr": {"fwd": -46 * sw * runw}}
            out["pose"] = _mix(run, REACH_N, lunge)
            out["face"] = dict(NF["scared"])
        return out
    # ---- the fall: off the deck at their speed, into the stub's face, hands onto its top
    land = W["land"]
    if tau < land:
        s = tau - leap
        x, v = run_x(E, k, leap)
        xr = min(x + v * s, E.x_hit[k])
        z = deck + E.hop * s - 0.5 * G * s * s
        hit = x + v * s >= E.x_hit[k]
        out["loc"] = Vector((xr - (0.04 * math.exp(-(s - (E.x_hit[k] - x) / v) * 14) if hit else 0.0), y_l, z))
        out["yaw"] = 90
        u = ss(0.0, 0.25, s)
        if steve:
            p = _mix(REACH_S, HANG_S, ss(0.25, 1.0, s / (land - leap)))
            p["foot_sl"] = {"y": lerp(0.5, -0.1, u), "z": lerp(0.45, 0.2, u)}
            p["foot_sr"] = {"y": lerp(0.3, 0.2, u), "z": lerp(0.2, 0.5, u)}
            out["pose"] = p
            out["face"] = dict(SF["scared"])
        else:
            out["pose"] = _mix(REACH_N, HANG_N, ss(0.25, 1.0, s / (land - leap)))
            out["face"] = dict(NF["scared"])
        return out
    # ---- hanging: hands fixed on the stub's top, the jolt, the swing, feet scrabbling
    s = tau - land
    grip_x = E.grip_x
    jolt = -0.11 * math.exp(-6.0 * s) * math.cos(17.0 * s) + 0.11 * math.exp(-60 * s) * 0.0
    sway = 0.07 * math.exp(-1.2 * s) * math.sin(3.2 * s + (0.0 if steve else 1.1))
    out["yaw"] = 90
    out["grip"] = Vector((grip_x, y_l + sway * 0.2, deck + 0.07))
    out["grip_sides"] = ("sl", "sr")
    scr = math.exp(-0.8 * s) * (1.0 if s < 2.2 else 0.0)
    if steve:
        p = dict(HANG_S)
        ph = s * 9.0
        p = json.loads(json.dumps(p))
        p["foot_sl"] = {"y": -0.25 * scr * math.sin(ph) + 0.05, "z": 0.35 * scr * max(0.0, math.sin(ph))}
        p["foot_sr"] = {"y": 0.25 * scr * math.sin(ph + 2.0) - 0.05, "z": 0.35 * scr * max(0.0, math.sin(ph + 2.0))}
        el = 6 + 26 * math.exp(-6.0 * s) * abs(math.cos(8.5 * s))
        p["arm_sl"] = dict(p["arm_sl"], elbow=el)
        p["arm_sr"] = dict(p["arm_sr"], elbow=el)
        p["chest_lean"] = -9 - 8 * math.exp(-6.0 * s) * math.cos(8.5 * s)
        out["face"] = dict(SF["scared"])
        # Patch arrives: he looks up and round at him, then turns on one hand to face him (the punchline)
        st = steve_turn(tau)
        if st > 0:
            p, face_s, yaw_add = steve_one_hand(E, tau, st, p)
            out["face"] = face_s
            out["grip_sides"] = ("sr",)
            out["yaw"] = 90 + yaw_add
        else:
            look = ss(T["patch_omg"] - 0.4, T["patch_omg"] + 0.3, tau)
            up = ss(0.0, 0.25, s) * (1 - ss(1.2, 1.8, s))
            p["head_turn"] = 38 * look
            p["head_nod"] = lerp(-22 - 24 * up, -12, look)
            out["face"] = _mixf(SF["scared"], SF.get("stunned", SF["scared"]), look)
        out["pose"] = p
        out["loc"] = Vector((XE - 0.3, y_l, deck - 2.0))
    else:
        p = json.loads(json.dumps(HANG_N))
        ph = s * 10.0
        p["leg_sl"] = {"fwd": 4 + 30 * scr * math.sin(ph)}
        p["leg_sr"] = {"fwd": -4 - 30 * scr * math.sin(ph + 1.7)}
        up = ss(0.0, 0.25, s) * (1 - ss(1.2, 1.8, s))
        p["head_nod"] = -20 - 24 * up
        # Patch drops in: he swings round on one hand to see him, the same way Steve does
        # (hanging straight down from the raised arm; turning this way keeps him clear of the wall)
        nt = ss(T["hang"] + 0.55, T["hang"] + 1.15, tau)
        if nt > 0:
            qn = back_out(nt) if nt < 1 else 1.0
            p["arm_sl"] = {"fwd": lerp(172, 10, qn), "out": lerp(4, 16, qn)}
            p["arm_sr"] = {"fwd": 172, "out": 4}
            p["head_nod"] = lerp(p["head_nod"], -8, qn)
            p["chest_lean"] = lerp(-8, -3, qn)
            p["leg_sl"] = {"fwd": lerp(p["leg_sl"]["fwd"], 3, qn)}
            p["leg_sr"] = {"fwd": lerp(p["leg_sr"]["fwd"], -3, qn)}
            out["grip_sides"] = ("sr",)
            out["yaw"] = 90 - 125 * qn
        out["pose"] = p
        out["face"] = dict(NF["scared"]) if tau < T["steve_delete"] + 0.3 else dict(NF["shock"])
        out["loc"] = Vector((XE - 0.3, y_l, deck - 2.0))
    return out


def shake(tau):
    """The Noob shaking him by the shoulders: (front-back, side), 0 when not."""
    a = ss(T["noob_wake"] + 0.1, T["noob_wake"] + 0.3, tau) * (1 - ss(T["run"] - 0.25, T["run"] - 0.05, tau))
    return (a * math.sin(2 * math.pi * 5.0 * tau), a * math.sin(2 * math.pi * 5.0 * tau + 1.3))


def steve_turn(tau):
    t0 = T["hang"] + 0.45                                     # Patch drops in: they swing round to see him
    return ss(t0, t0 + 0.6, tau)


def steve_one_hand(E, tau, u, p):
    """Hanging by his right hand (screen left), he swings round to face Patch:
    deadpan, then losing it; on DELETE his free arm flings at Null."""
    from ep09_new import SF
    q = back_out(u) if u < 1 else 1.0
    p = dict(p)
    p["arm_sr"] = {"fwd": 172, "out": 4, "elbow": 4}
    flat_ = {"both_to": 0.42, "both_tm": 0.45, "both_ti": 0.4, "both_bo": 0.12, "both_ps": 0.8, "both_py": 0.0,
             "bb_tilt": -0.2, "bb_raise": -0.1, "bb_squeeze": 0.0, "m_arch": 0.12, "m_w": 1.6}
    seen = T["steve_seen"]
    dl = T["steve_delete"]
    build = ss(dl - 0.1, dl + 1.4, tau)
    fling = ss(dl + 0.9, dl + 1.25, tau)
    p["arm_sl"] = {"fwd": lerp(10, 80, fling), "out": lerp(18, 45, fling), "elbow": lerp(30, 6, fling), "twist": 0}
    p["head_turn"] = lerp(30, 0, q)
    p["head_nod"] = lerp(-12, 2, q) - 6 * build
    p["chest_lean"] = lerp(-4, -2, q) + 6 * build
    p["foot_sl"] = {"y": 0.0, "z": 0.0}
    p["foot_sr"] = {"y": -0.1, "z": 0.05}
    face = dict(flat_)
    if tau >= dl - 0.1:
        mad = {"both_to": 0.0, "both_tm": 0.0, "both_ti": 0.1, "both_ps": 0.55, "both_py": 0.0,
               "bb_tilt": 0.95, "bb_raise": -0.3, "bb_squeeze": 1.5, "m_arch": -0.1, "m_w": 2.1}   # brows knit together
        face = _mixf(flat_, mad, build)
    return p, face, -125 * q


def _mix(a, b, u):
    from ep09_new import flat, unflat
    fa, fb = flat(a), flat(b)
    keys = set(fa) | set(fb)
    return unflat({k: lerp(fa.get(k, 0.0), fb.get(k, 0.0), u) for k in keys})


def _mixf(a, b, u):
    keys = set(a) | set(b)
    return {k: lerp(a.get(k, b.get(k)), b.get(k, a.get(k)), u) for k in keys}


# ------------------------------------------------------------------ Patch
def patch(E, t, tau):
    """Patch drops in from above, already scanning Null with his beam (the beam sweeping
    him); it clicks (his eye goes wide), and still scanning he says it."""
    from patch import DEFAULTS as PD, set_patch
    Pt = E.Pt
    XE, deck = E.XE, E.deck
    t_in = T["hang"] - 0.15
    if tau < t_in:
        Pt.root.location = (0, 0, -500)
        for o in Pt.col.objects:
            o.hide_render = True
        return
    for o in Pt.col.objects:
        o.hide_render = False
    Pt.beam.hide_render = True
    u = ss(t_in, T["hang"] + 0.7, tau)
    home = Vector((XE - 1.75, E.Y0 + 0.5 - 0.2, deck - 0.75))
    drop = 1 - back_out(u) if u < 1 else 0.0
    loc = home + Vector((0.25 * drop, -0.2 * drop, 5.5 * drop))
    loc.z += 0.05 * math.sin(tau * 4.0)
    null_at = Vector((XE - 26.0, E.Y0 + 7.0, deck + 4.0))
    f = (null_at - loc)
    f = Vector((f.x, f.y, 0)).normalized()
    realize = ss(T["patch_omg"] - 0.4, T["patch_omg"] - 0.1, tau)
    Pt.root.location = loc
    Pt.root.rotation_euler = (math.radians(-6 - 6 * realize), 0, math.atan2(-f.x, f.y) + math.pi)
    vals = dict(PD)
    scanning = T["hang"] + 0.25 <= tau < T["steve_seen"] + 0.1
    vals.update({"open": 1.0, "smile": 0.0, "wide": 0.0, "squint": 0.45 * (1 - realize)})
    if realize > 0.5:
        vals.update({"wide": 1.0, "squint": 0.0})
    if T["patch_omg"] <= tau < T["patch_omg_end"]:
        vals.update({"smile": 0.7, "wide": 0.8})
    if scanning:
        vals["scan"] = 1.0
    if tau >= T["steve_seen"] + 0.3:                           # Steve's answer: he blinks at him
        vals.update({"smile": 0.0, "wide": 0.4, "scan": 0.0,
                     "open": 1.0 - 0.9 * math.exp(-((tau - T["steve_delete"] - 1.6) / 0.05) ** 2)})
    for side in ("l", "r"):
        Pt.fins[side].rotation_euler = (math.radians(25 * math.sin(tau * 18.0)), 0, 0)
    set_patch(Pt, vals)
    if scanning:
        Pt.beam.hide_render = False
        sweep = 1 - realize
        Pt.beam.rotation_euler = (math.radians(E.beam_pitch + 12 * math.sin(tau * 3.1) * sweep), 0,
                                  math.radians(14 * math.sin(tau * 2.3) * sweep))
    E.patch_at = loc


# ------------------------------------------------------------------ cameras
def camera_set(E, t, tau):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    E.cam_up = Vector((0, 0, 1))
    loc, look, lens, fstop, focus, shake_amp, roll = camera(E, t, tau)
    y1, p1, r1 = handheld(t, shake_amp)
    q = look_quat(look - loc, E.cam_up) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1 + roll))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.key.location = loc + Vector((0.6, 0.0, 1.6))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    return {}


def look_quat(d, up=Vector((0, 0, 1))):
    """A camera looking along d, its top toward `up` (or, looking straight down, toward the void: -x)."""
    f = d.normalized()
    u = up if abs(f.dot(up)) < 0.97 else Vector((-1, 0, 0))
    r = f.cross(u).normalized()
    u2 = r.cross(f)
    m = Matrix((r, u2, -f)).transposed()
    return m.to_quaternion()


def _head(ob_face, holder=None):
    c = sum((Vector(v) for v in ob_face.bound_box), Vector()) / 8
    m = (holder.matrix_world @ ob_face.matrix_world) if holder is not None else ob_face.matrix_world
    return m @ c


def shots():
    return [("S1", T["run"] - 1.5), ("S2", T["run"] - 0.45), ("S3", T["run"] + 0.12), ("S4", T["drop"] + 0.25),
            ("S4b", T["catch"] + 0.18),
            ("S5", T["hang"]), ("S5b", T["hang"] + 0.6), ("S6", T["steve_seen"]), ("S7", 1e9)]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "S7", t0, 1e9


def camera(E, t, tau):
    XE, deck, Y0 = E.XE, E.deck, E.Y0
    yc = Y0 + 0.5
    hs = _head(E.S.face, E.S.holder)
    hn = _head(E.N.face)
    name, t0, t1 = which(t)
    u = ss(t0, min(t1, t0 + 6), t) if t1 < 1e8 else ss(t0, T["end"] + 0.5, t)
    if os.environ.get("TOPCAM"):
        c = Vector((XE - 1.0, yc, deck - 1.0))
        return c + Vector((-4.5, -9.0, 2.0)), c, 30, 16.0, None, 0.0, 0.0
    if name == "S1":
        # the Noob, close, from Steve's side (Steve just off the right edge); the rainbow going behind him, Null out there
        foc = hn + Vector((0, 0, -0.05))
        loc = hn + Vector((1.15 - 0.1 * u, -1.25 + 0.1 * u, -0.25))
        return loc, foc + Vector((0.0, 0.0, -0.1)), 40, 2.4, (hn - loc).length, 0.35, 0.0
    if name == "S2":
        # wide, low, from the side: both on the bridge, the planks going toward them from the left
        mid = Vector((XE - 4.2, yc, deck + 0.4))
        loc = mid + Vector((0.9 - 0.4 * u, -7.6 + 0.8 * u, -1.1))
        return loc, mid + Vector((-0.2, 0, 0.3)), 24, 8.0, (hs - loc).length, 0.4, 0.0
    if name == "S3":
        # Steve snaps out of it: close from in front (the -x side), he sees it
        loc = hs + Vector((-0.6, 1.1, 0.0))
        return loc, hs + Vector((0, 0, -0.03)), 40, 2.0, None, 0.15, 0.0
    if name == "S4b":
        # at the very edge: they come down at it, and their hands slam on it in front of us
        land = W["land"]
        jolt = math.exp(-((tau - land) / 0.05) ** 2) if tau > land - 0.1 else 0.0
        loc = Vector((XE + 0.85, yc - 0.1, deck + 0.42))
        look = Vector((XE - 0.9, yc, deck - 0.35))
        return loc, look, 22, 6.0, (Vector((XE, yc, deck)) - loc).length, 0.3 + 2.4 * jolt, 0.0
    if name == "S4":
        # low on the island behind the stub, looking back along the bridge: they run at us, the deck goes, they leap,
        # their hands slam down in front of the lens
        land = W["land"]
        jolt = math.exp(-((tau - land) / 0.05) ** 2) if tau > land - 0.1 else 0.0
        dolly = 0.0
        loc = Vector((XE + 2.6, yc - 0.1, deck + 0.55))
        look = Vector((XE - 2.5, yc, deck + 0.35 - 1.5 * dolly))
        return loc, look, 20, 5.0, (Vector((XE, yc, deck)) - loc).length, 0.35 + 2.0 * jolt, 0.0
    if name == "S5":
        # the vertigo: from above the lip, straight down past their faces into the void, the bridge still falling
        E.cam_up = Vector((1, 0, 0))                       # the island at the top of the frame, the void below
        loc = Vector((XE + 0.25, yc - 0.2, deck + 2.7 + 0.35 * u))
        look = Vector((XE - 1.35, yc, deck - 7.0))
        return loc, look, 24, 7.0, (Vector((XE - 0.2, yc, deck - 0.4)) - loc).length, 0.3, 0.0
    if name == "S5b":
        # the hang, from the side: both of them on the stub's face, the drop under them
        ym = 0.5 * (E.lane["S"] + E.lane["N"])
        loc = Vector((XE - 0.55 - 0.1 * u, E.lane["S"] - 2.1 + 0.15 * u, deck - 3.3 + 0.1 * u))
        look = Vector((XE - 0.15, ym, deck - 0.5))
        return loc, look, 28, 5.6, (look - loc).length, 0.25, 0.0
    if name == "S6":
        # beside them against the stub, looking out: Patch rises into view, Null far behind him
        pa = getattr(E, "patch_at", Vector((XE - 1.75, yc - 0.2, deck - 0.75)))
        f = Vector((XE - 26.0, Y0 + 7.0, 0)) - Vector((pa.x, pa.y, 0))
        f.normalize()
        a = math.radians(66)
        c = Vector((f.x * math.cos(a) - f.y * math.sin(a), f.x * math.sin(a) + f.y * math.cos(a), 0))
        loc = pa + c * lerp(2.3, 2.0, u) + Vector((0, 0, 0.25))
        hm = 0.5 * (hs + hn)
        look = pa.lerp(hm, 0.55) + Vector((0, 0, -0.1))
        return loc, look, 30, 4.0, (pa - loc).length, 0.22, 0.0
    # S7: from Patch's side: Steve, one hand, turned to us; deadpan, then the build, the push-in on DELETE
    dl = T["steve_delete"]
    push = ss(dl + 0.6, dl + 1.4, t)
    pa = Vector((XE - 1.75, yc - 0.2, deck - 0.75))
    d = Vector((-0.86, -0.5, 0.0))
    loc = hs + d * lerp(2.1, 1.45, push) + Vector((0, 0, 0.15))
    shake_ = 0.2 + 1.4 * math.exp(-((t - (dl + 1.3)) / 0.2) ** 2)
    look = hs + Vector((0.0, 0.35 * (1 - push), -0.3 * (1 - push) - 0.05))
    return loc, look, lerp(32, 40, push), 2.4, (hs - loc).length, shake_, 0.0


# ------------------------------------------------------------------ the look
def finish(path, mist_path):
    P4.finish(path, mist_path)


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    for k in ("a", "noob_wake", "run", "drop", "catch", "hang", "patch_omg", "steve_seen", "steve_delete", "end"):
        if k in b:
            T[k] = b[k][0]
    if "patch_omg" in b:
        T["patch_omg_end"] = b["patch_omg"][1]
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
