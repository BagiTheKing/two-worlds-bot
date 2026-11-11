"""Episode 10, part 4: the Noob builds his world (about 8.6 s).

What is left of Minecraft is half an egg of land in the void. The Noob, running
from Null, builds the other half out of Roblox parts with his BTool, over the
void, as he runs: the ground appears under his feet, the island spreads out
from his path in a wave, obby pieces rise on it, and at its near end he sends
a rainbow bridge across the chasm onto the old Minecraft bridge.

  A  Low, ahead of him: he runs at us; the first parts slam down under his feet.
  B  Beside him, tracking: the ground races out, obby pieces rise, every part in
     Roblox Studio's tool (selection outline, move arrows, resize, snap).
  C  Patch's view, high above, in the wind: the egg, Minecraft on the right, the
     Noob's half still growing on the left, Null behind him, Steve on his side.
     PATCH: "This is bad."
  D  Over his shoulder at the chasm: the rainbow bridge slides out, part by part,
     and the last part snaps onto the old bridge.
  E  Patch, close: his eye goes wide.

    python src/lookdev/ep10_p4_build.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080]
        [--samples 32] [--times ...] [--sfx]
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
from ep10_entrance import FPS, lerp, ss, back_out, lin               # noqa: E402

T = {"a": 0.0, "b": 1.4, "b2": 2.3, "c": 3.2, "patch_bad": 3.55, "c2": 4.5, "d": 5.0, "e": 7.2, "length": 8.6}
TILE = 3.0
RIM = 1.5


# ------------------------------------------------------------------ the plan
class Plan:
    """Everything the Noob builds, and when: deterministic, from the island's outline."""

    def __init__(self, I):
        self.I = I
        l0, r0 = I.chasm(I.bridge_end.y)
        self.deck = I.bridge_z                               # the old bridge's deck top: his deck's top too
        self.lip = Vector((l0 - 0.4, I.bridge_end.y, self.deck))
        self.bridge_end = Vector((I.bridge_end.x - 0.6, I.bridge_end.y, self.deck))
        # the runway: from the middle of his half to the lip at the near end
        self.P = [Vector((-24.0, -2.0)), Vector((-21.0, -17.0)), Vector((-14.0, -27.0)), Vector((self.lip.x - 1.0, self.lip.y))]
        self.samples = [self.bez(k / 400) for k in range(401)]
        self.cum = [0.0]
        for k in range(400):
            self.cum.append(self.cum[-1] + (self.samples[k + 1] - self.samples[k]).length)
        self.length = self.cum[-1]
        self.parts = []                                      # dicts: kind, size, colour, shape, at (Vector), t0, mode
        self._make()

    def bez(self, u):
        a, b, c, d = self.P
        return (1 - u) ** 3 * a + 3 * (1 - u) ** 2 * u * b + 3 * (1 - u) * u * u * c + u ** 3 * d

    def run_s(self, t):
        """How far along the runway he is (m) at t: off at a sprint, easing in at the lip."""
        t0, t1 = T["a"], T["d"] - 0.05
        u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
        return self.length * (u * (1.15 - 0.15 * u * u)) / 1.0 if u < 1 else self.length

    def at_s(self, s):
        s = min(max(s, 0.0), self.length)
        k = 0
        lo, hi = 0, 400
        while lo < hi:
            mid = (lo + hi) // 2
            if self.cum[mid] < s:
                lo = mid + 1
            else:
                hi = mid
        k = max(1, lo)
        f = (s - self.cum[k - 1]) / max(1e-6, self.cum[k] - self.cum[k - 1])
        p = self.samples[k - 1].lerp(self.samples[k], f)
        d = (self.samples[k] - self.samples[k - 1]).normalized()
        return p, d

    def nearest(self, x, y):
        q = Vector((x, y))
        best = min(range(0, 401, 4), key=lambda k: (self.samples[k] - q).length)
        return self.cum[best], (self.samples[best] - q).length

    def t_reach(self, s):
        """When he reaches s along the runway."""
        lo, hi = T["a"], T["d"]
        for _ in range(30):
            mid = (lo + hi) / 2
            if self.run_s(mid) < s:
                lo = mid
            else:
                hi = mid
        return hi

    def inside(self, x, y):
        I = self.I
        l, _r = I.chasm(y)
        return I.egg(x, y) < 1.0 and x < l - 0.15

    def _make(self):
        rnd = random.Random(4)
        I, deck = self.I, self.deck
        t_end = T["d"] + 1.0
        # the deck: big tiles, half tiles at the rim; a grey path along the runway
        covered = set()
        for gx in range(-20, 2):
            for gy in range(-14, 14):
                x0, y0 = gx * TILE, gy * TILE
                subs = [(x0 + (i + 0.5) * RIM, y0 + (j + 0.5) * RIM) for i in range(2) for j in range(2)]
                ins = [self.inside(*p) for p in subs]
                if not any(ins):
                    continue
                if all(ins):
                    tiles = [((x0 + TILE / 2, y0 + TILE / 2), TILE)]
                else:
                    tiles = [(p, RIM) for p, k in zip(subs, ins) if k]
                for (cx, cy), sz in tiles:
                    s, d = self.nearest(cx, cy)
                    path = d < 2.4
                    col = "Dark stone grey" if path else ("Bright green" if (gx + gy) % 2 else "Dark green")
                    t0 = self.t_reach(max(0.0, s - 1.0)) - 0.45 + d / 11.0 + rnd.uniform(0, 0.08)
                    self.parts.append({"kind": "tile", "size": (sz - 0.04, sz - 0.04, 1.2), "colour": col, "shape": "box",
                                       "at": Vector((cx, cy, deck - 0.6)), "t0": min(t0, t_end), "path": path})
                    covered.add((round(cx, 2), round(cy, 2)))
        # the underside: stepped blocks, narrowing downward (earth-brown, then grey)
        for gx in range(-10, 1):
            for gy in range(-7, 7):
                cx, cy = gx * 6 + 3, gy * 6 + 3
                if not self.inside(cx, cy):
                    continue
                r = I.egg(cx, cy)
                depth = 2.0 + 22.0 * (1 - r) ** 0.85
                s, d = self.nearest(cx, cy)
                tt = min(self.t_reach(max(0.0, s - 1.0)) + d / 11.0, t_end)
                z = deck - 1.2
                k = 0
                while depth > 0.5 and k < 6:
                    hgt = min(3.4, depth)
                    w = 5.6 - 0.75 * k
                    col = "Brown" if k == 0 else ("Reddish brown" if k < 3 else "Dark stone grey")
                    self.parts.append({"kind": "under", "size": (w, w, hgt), "colour": col, "shape": "box",
                                       "at": Vector((cx, cy, z - hgt / 2)), "t0": tt + 0.2 + 0.07 * k, "path": False})
                    z -= hgt
                    depth -= hgt
                    k += 1
        # obby: pillars, jump pads, arches, a tower of stairs; never on the runway
        bright = ["Bright red", "Bright blue", "Bright yellow", "Bright orange", "Lime green", "Bright violet", "Teal",
                  "Hot pink"]
        placed = []
        tries = 0
        while len(placed) < 58 and tries < 6000:
            tries += 1
            x, y = rnd.uniform(-50, -3), rnd.uniform(-40, 38)
            if not self.inside(x, y) or I.egg(x, y) > 0.9:
                continue
            s, d = self.nearest(x, y)
            if d < 4.5 or any((Vector((x, y)) - p).length < 4.2 for p in placed):
                continue
            placed.append(Vector((x, y)))
            t0 = min(self.t_reach(max(0.0, s - 1.0)) + d / 11.0 + 0.35, t_end)
            kind = rnd.choice(["pillar", "pillar", "pad", "arch", "stairs", "tower", "slab", "slab"])
            c = rnd.choice(bright)
            if kind == "pillar":
                h = rnd.uniform(2.5, 6.5)
                self.parts.append({"kind": "obby", "size": (1.2, 1.2, h), "colour": c, "shape": "cyl",
                                   "at": Vector((x, y, deck + h / 2)), "t0": t0, "path": False})
            elif kind == "pad":
                for k in range(3):
                    z = deck + 1.2 + 1.1 * k
                    self.parts.append({"kind": "obby", "size": (1.8, 1.8, 0.4), "colour": bright[(k + len(placed)) % 8],
                                       "shape": "box", "at": Vector((x + 1.6 * k, y + 0.6 * k, z)), "t0": t0 + 0.1 * k,
                                       "path": False})
            elif kind == "arch":
                for dx in (-1.6, 1.6):
                    self.parts.append({"kind": "obby", "size": (0.8, 0.8, 3.6), "colour": c, "shape": "box",
                                       "at": Vector((x + dx, y, deck + 1.8)), "t0": t0, "path": False})
                self.parts.append({"kind": "obby", "size": (4.2, 0.8, 0.8), "colour": bright[(bright.index(c) + 3) % 8],
                                   "shape": "box", "at": Vector((x, y, deck + 4.0)), "t0": t0 + 0.12, "path": False})
            elif kind == "stairs":
                for k in range(5):
                    self.parts.append({"kind": "obby", "size": (2.4, 0.9, 0.5 * (k + 1)), "colour": bright[k % 8],
                                       "shape": "box", "at": Vector((x, y + 0.9 * k, deck + 0.25 * (k + 1))),
                                       "t0": t0 + 0.06 * k, "path": False})
            elif kind == "slab":                              # a big bright platform (colour, seen from above)
                w = rnd.uniform(4.0, 7.0)
                self.parts.append({"kind": "obby", "size": (w, w * rnd.uniform(0.6, 1.0), 0.6), "colour": c,
                                   "shape": "box", "at": Vector((x, y, deck + 0.3)), "t0": t0, "path": False})
            else:
                for k in range(4):
                    w = 3.0 - 0.5 * k
                    self.parts.append({"kind": "obby", "size": (w, w, 1.6), "colour": bright[(k * 3 + len(placed)) % 8],
                                       "shape": "box", "at": Vector((x, y, deck + 0.8 + 1.6 * k)), "t0": t0 + 0.09 * k,
                                       "path": False})
        # his moment: pillars shooting up beside his path and an arch he runs under
        hero = ["Bright red", "Bright blue", "Bright yellow", "Lime green", "Bright orange", "Bright violet", "Teal"]
        for k, (s_at, side_, h) in enumerate(((7.0, 1, 4.5), (8.5, -1, 5.5), (10.0, 1, 6.5), (11.5, -1, 5.0),
                                              (13.0, 1, 7.0), (14.5, 1, 6.0), (16.0, 1, 5.0), (17.5, 1, 6.5))):
            pt, dr = self.at_s(s_at)
            sv = Vector((-dr.y, dr.x)) * side_ * 3.6
            self.parts.append({"kind": "riser", "size": (1.1, 1.1, h), "colour": hero[k % 7], "shape": "cyl",
                               "at": Vector((pt.x + sv.x, pt.y + sv.y, deck + h / 2)),
                               "t0": self.t_reach(s_at) - 0.55, "path": False})
        s_arch = self.run_s(T["b2"] + 0.45)
        pt, dr = self.at_s(s_arch)
        sv = Vector((-dr.y, dr.x))
        ta = self.t_reach(s_arch) - 0.6
        for sg in (-1, 1):
            c = pt + sv * 2.4 * sg
            self.parts.append({"kind": "riser", "size": (0.9, 0.9, 4.4), "colour": "Bright red", "shape": "box",
                               "at": Vector((c.x, c.y, deck + 2.2)), "t0": ta, "path": False})
        ang = math.atan2(sv.y, sv.x)
        self.parts.append({"kind": "obby", "size": (5.7, 0.9, 0.9), "colour": "Bright yellow", "shape": "box",
                           "at": Vector((pt.x, pt.y, deck + 4.85)), "t0": ta + 0.18, "path": False, "rot": ang})
        # the rainbow bridge: from his lip onto the old bridge's broken end
        from roblox import RAINBOW
        a, b = self.lip, self.bridge_end
        n = 6
        for k in range(n):
            u0, u1 = k / n, (k + 1) / n
            c = a.lerp(b, (u0 + u1) / 2)
            self.parts.append({"kind": "bridge", "size": ((b.x - a.x) / n + 0.06, 3.0, 0.5), "colour": RAINBOW[k],
                               "shape": "box", "at": Vector((c.x, c.y, self.deck - 0.25)),
                               "t0": T["d"] + 0.55 + 0.27 * k, "path": True})
        for p in self.parts:
            p["t0"] = max(T["a"] - 0.6, p["t0"])


# ----------------------------------------------------------------- the build
class Ep:
    pass


def build(tl, assets, res, samples):
    from island import build_island
    from stage import build_steve, build_noob_char, build_patch_char, build_null_char, null_lights, char_light
    from roblox import plastic_material, make_part, Gizmos, BRICK
    BRICK.update({"Brown": (124, 92, 70), "Reddish brown": (105, 64, 40)})
    E = Ep()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    E.sc = sc
    E.I = I = build_island(sc, assets)
    E.plan = plan = Plan(I)
    col = bpy.data.collections.new("roblox")
    sc.collection.children.link(col)
    mat = plastic_material()
    E.objs = []
    for k, p in enumerate(plan.parts):
        ob = make_part(col, f"rbx_{p['kind']}_{k}", p["size"], p["colour"], mat, shape=p["shape"])
        ob.location = p["at"]
        ob.rotation_mode = "QUATERNION"
        if p.get("rot"):
            ob.rotation_quaternion = Quaternion((0, 0, 1), p["rot"])
        E.objs.append(ob)
    E.giz = Gizmos(col)
    # the cast
    E.N = build_noob_char(sc)
    E.S = build_steve(sc)
    E.Pt = build_patch_char(sc, size=0.4)
    E.X = build_null_char(sc, assets, height=10.0)
    null_lights(sc, E.X)
    E.tool = _btool(col)
    hold_tool(E.N, E.tool, "sl")
    # lights: a warm key from the camera side, the void's cool fill comes from the sky
    E.key = char_light(sc, "key", (0, -3, 3), 260, (1.0, 0.9, 0.8), cone=40, size=1.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.dof.use_dof = True
    cam.data.sensor_width = 36
    cam.data.clip_end = 5000
    E.cam = cam
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = res * 9 // 16
    sc.render.resolution_y = res
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = -0.05
    sc.render.fps = FPS
    sc.render.compositor_device = "CPU"
    from ep09_new import _mist_output
    _mist_output(sc)
    return E


def _btool(col):
    """His building tool, designed in metres along +z (the grip at 0, the head at the top):
    a rubber grip with a white band, a white collar, a steel neck, and a glass cube head
    glowing selection blue inside a white edge frame (Studio's part icon), with its own light."""
    import bmesh
    from roblox import lin as rl, SELECT
    root = bpy.data.objects.new("btool", None)
    col.objects.link(root)

    def mat(name, rgb, glow=0.0, rough=0.4, metal=0.0, glass=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rl(rgb), 1)
        b.inputs["Emission Color"].default_value = (*rl(rgb), 1)
        b.inputs["Emission Strength"].default_value = glow
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        b.inputs["Transmission Weight"].default_value = glass
        return m

    def cyl(name, r, z0, z1, m, seg=20):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for p_ in me.polygons:
            p_.use_smooth = True
        me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        ob.parent = root
        ob.location = (0, 0, (z0 + z1) / 2)
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width, bv.segments = min(0.01, r * 0.3), 2
        return ob

    def box(name, size, loc, m):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        ob.parent = root
        ob.location = loc
        return ob
    grip = mat("btool_grip_m", (38, 40, 46), rough=0.75)
    white = mat("btool_white_m", (236, 238, 244), rough=0.35)
    steel = mat("btool_steel_m", (170, 176, 186), rough=0.25, metal=1.0)
    glass = mat("btool_glass_m", SELECT, glow=2.2, rough=0.08, glass=0.6)
    edge = mat("btool_edge_m", (255, 255, 255), glow=3.0)
    cyl("btool_grip", 0.042, -0.13, 0.17, grip)
    cyl("btool_band", 0.047, 0.03, 0.06, white)
    cyl("btool_cap", 0.05, -0.15, -0.12, white)
    cyl("btool_collar", 0.058, 0.17, 0.21, white)
    cyl("btool_neck", 0.022, 0.21, 0.31, steel, seg=12)
    hz, hs = 0.42, 0.2
    box("btool_head", (hs, hs, hs), (0, 0, hz), glass)
    e, h = 0.014, hs / 2 + 0.007
    for a in (-h, h):
        for b in (-h, h):
            box(f"btool_edge_x{a}{b}", (hs + 2 * e, e, e), (0, a, hz + b), edge)
            box(f"btool_edge_y{a}{b}", (e, hs + 2 * e, e), (a, 0, hz + b), edge)
            box(f"btool_edge_z{a}{b}", (e, e, hs + 2 * e), (a, b, hz), edge)
    L = bpy.data.lights.new("btool_light", "POINT")
    L.color, L.energy, L.shadow_soft_size = (0.35, 0.72, 1.0), 18.0, 0.08
    lo = bpy.data.objects.new("btool_light", L)
    col.objects.link(lo)
    lo.parent = root
    lo.location = (0, 0, hz)
    root["head_z"] = hz
    return root


def hold_tool(n, tool, side="sl", tilt=55.0):
    """Grip the tool in the Noob's fist: its grip runs through the hand, across the arm,
    so with the arm raised forward the tool stands up out of the fist, tipped forward
    by `tilt` degrees toward where he aims."""
    piv = n.arms[side]
    tool.parent = piv
    k = 1.0 / n.root.scale.x                                   # metres -> the arm's units
    d = Vector((0, -math.cos(math.radians(tilt)), -math.sin(math.radians(tilt))))
    q = Vector((0, 0, 1)).rotation_difference(d)
    fist = Vector((0, 0, -1.28))                               # inside the end of the arm
    tool.matrix_basis = Matrix.Translation(fist) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((k, k, k, 1))


# ------------------------------------------------------------ the cast's paths
def noob_at(E, t):
    """-> position (feet), heading (unit 2D), speed (m/s)."""
    plan = E.plan
    s = plan.run_s(t)
    p, d = plan.at_s(s)
    v = (plan.run_s(t + 0.02) - plan.run_s(t - 0.02)) / 0.04
    return Vector((p.x, p.y, plan.deck)), d, v


def steve_at(E, t):
    """On the Minecraft half, running for the old bridge."""
    I = E.I
    a = Vector((26.0, -12.0))
    b = Vector((I.bridge_end.x + 7.0, I.bridge_end.y + 0.2))
    u = ss(T["a"], T["e"] + 1.0, t)
    p = a.lerp(b, u)
    h = I.height(p.x, p.y) or I.bridge_z
    return Vector((p.x, p.y, h)), (b - a).normalized()


def null_at(E, t):
    """Behind the Noob, out in the void past his half's edge, gaining."""
    plan = E.plan
    s = plan.run_s(t)
    back = 19.0 - 3.0 * ss(T["a"], T["e"], t)
    p, d = plan.at_s(max(0.0, s - back))
    side = Vector((-d.y, d.x))
    q = p + side * 6.0 - d * max(0.0, back - s) * 0.8
    return Vector((q.x - 10.0, q.y + 4.0, plan.deck - 7.5)), d


PATCH_AT = Vector((-2.0, -66.0, 60.0))


# --------------------------------------------------------------- the camera
def camera(E, t):
    """-> loc, look, lens, fstop, focus (None = look point), shake (deg), roll"""
    nb, nd, nv = noob_at(E, t)
    if os.environ.get("TOOLCAM") and getattr(E, "tool_head", None) is not None:     # look-dev: the tool, close
        h = E.tool_head
        side = Vector((-nd.y, nd.x, 0))
        return h + side * 0.9 + Vector((nd.x, nd.y, 0)) * 0.7 + Vector((0, 0, -0.2)), h - Vector((0, 0, 0.25)), 45, 4.0, None, 0.0, 0.0
    if t < T["b"]:                                           # A: low and ahead, he runs at us
        u = ss(T["a"], T["b"], t)
        side = Vector((-nd.y, nd.x, 0))
        loc = nb + Vector((nd.x, nd.y, 0)) * lerp(5.2, 4.2, u) + side * 0.9 + Vector((0, 0, 0.55))
        look = nb + Vector((0, 0, 1.25))
        return loc, look, 22, 3.5, None, 0.35, 0.0
    if t < T["b2"]:                                          # B1: his moment: low, in front, the tool raised
        u = ss(T["b"], T["b2"], t)
        side = Vector((-nd.y, nd.x, 0))
        loc = nb + Vector((nd.x, nd.y, 0)) * lerp(2.9, 2.4, u) + side * lerp(1.5, 1.2, u) + Vector((0, 0, 0.75))
        look = nb + Vector((0, 0, 1.55)) + Vector((nd.x, nd.y, 0)) * 0.3
        return loc, look, 24, 2.6, (nb + Vector((0, 0, 1.5)) - loc).length, 0.35, 0.0
    if t < T["c"]:                                           # B2: beside him, tracking; he runs under the arch
        u = ss(T["b2"], T["c"], t)
        side = Vector((-nd.y, nd.x, 0))                      # his left: the island spreading out behind him
        fwd = Vector((nd.x, nd.y, 0))                         # ahead of him: he runs at us, under the arch
        loc = nb + fwd * lerp(7.0, 6.0, u) + side * 2.6 + Vector((0, 0, 1.8))
        look = nb + Vector((0, 0, 1.9)) + fwd * 1.0
        return loc, look, 24, 4.0, (nb + Vector((0, 0, 1.2)) - loc).length, 0.3, 0.0
    if t < T["d"]:                                           # C: Patch's eyes, high in the wind, searching
        u = (t - T["c"]) / (T["d"] - T["c"])
        loc = PATCH_AT + Vector((1.5 * math.sin(t * 1.3), 1.0 * math.sin(t * 0.9 + 1), 0.8 * math.sin(t * 1.7)))
        # the search: on the Noob's half, a whip across to the Minecraft half, back, and it settles on the chasm
        x = -18.0
        x = lerp(x, 16.0, ss(0.12, 0.3, u))
        x = lerp(x, -10.0, ss(0.42, 0.6, u))
        x = lerp(x, -3.0, ss(0.68, 0.9, u))
        look = Vector((x, -10.0 + 4.0 * math.sin(u * 5.0), 2.0))
        d = (look - loc).length
        # the focus hunts (soft, sharp, soft) and finds it as the view settles
        hunt = (0.65 * math.exp(-((u - 0.08) / 0.08) ** 2) + 0.55 * math.exp(-((u - 0.36) / 0.07) ** 2)
                + 0.5 * math.exp(-((u - 0.64) / 0.07) ** 2))
        return loc, look, 24, 0.8, d * (1 - hunt), 0.8, 0.0
    if t < T["e"]:                                           # D: over his shoulder, at the chasm, the bridge going out
        u = ss(T["d"], T["e"], t)
        lip, end = E.plan.lip, E.plan.bridge_end
        loc = lip + Vector((-3.6 + 0.8 * u, -2.6 + 0.5 * u, 1.9 - 0.2 * u))
        look = lip.lerp(end, 0.4 + 0.5 * ss(0.15, 0.85, u)) + Vector((0, 0, 0.3))
        return loc, look, 26, 5.0, None, 0.35, 0.0
    # E: Patch, close, from below his eye line: he sees it, and his eye goes wide
    fwd = (E.plan.bridge_end - PATCH_AT).normalized()
    u = ss(T["e"], T["e"] + 1.2, t)
    jolt = 0.12 * math.exp(-((t - T["e"] - 0.22) / 0.06) ** 2)
    fh = Vector((fwd.x, fwd.y, 0)).normalized()                  # level with his screen
    loc = PATCH_AT + fh * lerp(1.6, 1.35, u) + Vector((0.3, 0, 0.12)) - fh * jolt
    return loc, PATCH_AT + Vector((0, 0, 0.02)), 40, 2.0, None, 0.25, 0.0


# ------------------------------------------------------------ apply a frame
def apply(E, t):
    from noob import pose_noob
    from pose import pose
    from faceplate import set_face, NOOB_EYES, NOOB_EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_MOUTH, EYES, EYE_DEFAULTS
    from patch import DEFAULTS as PD, set_patch
    from stage import place_null_lights
    from ep09_new import NF, SF
    plan = E.plan
    nb, nd, nv = noob_at(E, t)
    tool_tip = None
    # ------------------------------------------------ the parts
    specs = []
    beams = []
    for p, ob in zip(plan.parts, E.objs):
        u = t - p["t0"]
        rel = p["at"].xy - nb.xy
        near = p["kind"] != "under" and (rel.length < 7.5 and rel.dot(nd) > -1.0 or p["kind"] == "obby" and rel.length < 14)
        dur = 0.42 if (near or p["kind"] == "bridge") else 0.26
        if u < 0:
            ob.hide_render = True
            continue
        ob.hide_render = False
        ob["flash"] = 0.0
        if p["kind"] == "riser":                         # shoots up out of the deck, overshoots, settles
            k = back_out(u / 0.32, 1.6)
            h = p["size"][2]
            ob.scale = (1.0, 1.0, max(0.02, k))
            ob.location = p["at"] - Vector((0, 0, h / 2 * (1 - k)))
            ob["flash"] = 1.0 * max(0.0, 1 - u / 0.2)
            continue
        if p["kind"] == "under":                         # rises out of the void into place
            k = ss(0, 0.3, u)
            ob.location = p["at"] - Vector((0, 0, 2.5 * (1 - k)))
            ob.scale = (0.6 + 0.4 * k,) * 3
            continue
        if not (near or p["kind"] == "bridge"):          # far: a pop, a blink of light
            k = back_out(u / dur, 2.2)
            ob.location = p["at"]
            ob.scale = (max(0.01, k),) * 3
            ob["flash"] = 0.6 * max(0.0, 1 - u / 0.25)
            continue
        f = u / dur
        if f < 1.0:                                      # move, resize, snap: Roblox Studio
            spawn = E.tool_head if E.tool_head is not None else p["at"] + Vector((0, 0, 3))
            if f < 0.5:
                g = ss(0, 0.5, f)
                ob.location = spawn.lerp(p["at"], 1 - (1 - g) ** 3)
                sz = 0.35
                mode = "move"
                beams.append((spawn, ob.location.copy()))
            elif f < 0.85:
                ob.location = p["at"]
                sz = lerp(0.35, 1.0, back_out((f - 0.5) / 0.35, 1.3))
                mode = "resize"
            else:
                ob.location = p["at"]
                sz = 1.0
                mode = "snap"
            ob.scale = (sz, sz, max(sz, 0.7)) if p["kind"] != "obby" else (sz, sz, sz)
            mw = Matrix.Translation(ob.location) @ ob.rotation_quaternion.to_matrix().to_4x4()
            tool = p["kind"] in ("obby", "bridge")             # the full Studio tool on the pieces that matter;
            if tool or mode == "move":                          # the ground tiles just get the outline as they slide
                specs.append({"m": mw, "size": tuple(v * s_ for v, s_ in zip(p["size"], ob.scale)),
                              "mode": mode if tool else "outline", "k": 0.0, "w": 0.035 if tool else 0.02})
        else:
            ob.location = p["at"]
            ob.scale = (1, 1, 1)
            ob["flash"] = 1.2 * max(0.0, 1 - (u - dur) / 0.1)
            if u - dur < 0.06 and p["kind"] in ("obby", "bridge"):
                specs.append({"m": Matrix.Translation(ob.location) @ ob.rotation_quaternion.to_matrix().to_4x4(),
                              "size": p["size"], "mode": "snap", "k": 1.0})
    # ------------------------------------------------ the Noob: running, the tool out ahead
    N = E.N
    running = t < T["d"] + 0.1
    if running:
        ph = 2 * math.pi * 2.9 * (t - T["a"])
        sw = math.sin(ph)
        aim = 120 if T["b"] <= t < T["b2"] else 92                 # his moment: the tool held high
        npz = {"chest_lean": 14, "head_nod": -4 if aim < 100 else -10, "arm_sl": {"fwd": aim + 6 * math.sin(ph * 0.5), "out": 6},
               "arm_sr": {"fwd": 62 * sw, "out": 12}, "leg_sl": {"fwd": 46 * sw}, "leg_sr": {"fwd": -46 * sw}}
        bob = 0.08 * abs(math.sin(ph))
    else:                                                   # at the lip: plants his feet, the tool aimed across
        u = ss(T["d"] + 0.1, T["d"] + 0.4, t)
        npz = {"chest_lean": lerp(14, 4, u), "head_nod": 2, "arm_sl": {"fwd": 95, "out": 2},
               "arm_sr": {"fwd": 10, "out": 20}, "leg_sl": {"fwd": 18}, "leg_sr": {"fwd": -14}}
        bob = 0.0
        if t > plan.parts[-1]["t0"] + 0.45:                 # the last part snaps: a fist in the air
            v = ss(plan.parts[-1]["t0"] + 0.45, plan.parts[-1]["t0"] + 0.7, t)
            npz["arm_sr"] = {"out": lerp(20, 165, v), "fwd": 10}
    yaw = math.degrees(math.atan2(-nd.x, nd.y)) + 180         # facing along the runway (he faces -y at 0)
    bd = plan.bridge_end - plan.lip
    npz["root_yaw"] = yaw if running else math.degrees(math.atan2(-bd.x, bd.y)) + 180
    pose_noob(N, npz)
    N.root.location = (nb.x, nb.y, nb.z + bob)
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    face = dict(NF["shout"] if t < T["c"] else NF["happy"] if t > plan.parts[-1]["t0"] + 0.45 else NF["confused"])
    for k, v in face.items():
        if k.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{k[5:]}"] = v
        else:
            fn[k] = v
    set_face(N.face, fn)
    bpy.context.view_layer.update()
    head = [o for o in E.tool.children if o.name == "btool_head"][0]
    E.tool_head = head.matrix_world.translation.copy()
    # beams: from the tool to what is being moved (only while it moves)
    for a, b in beams:
        d = b - E.tool_head
        if d.length < 0.3:
            continue
        mid = (E.tool_head + b) / 2
        q = d.to_track_quat("Z", "Y")
        specs.append({"m": Matrix.Translation(mid) @ q.to_matrix().to_4x4(), "size": (0.03, 0.03, d.length),
                      "mode": "beam", "k": 0.0})
    E.giz.draw([s_ for s_ in specs if s_["mode"] != "beam"])
    _beams(E, [s_ for s_ in specs if s_["mode"] == "beam"])
    # ------------------------------------------------ Steve, far, running for the bridge
    S = E.S
    sb, sd = steve_at(E, t)
    ph = 2 * math.pi * 2.6 * t
    sw = math.sin(ph)
    pose(S.arm, {"chest_lean": 16, "chest_twist": 10 * sw, "head_nod": -8, "hips_drop": 0.16,
                 "arm_sl": {"fwd": -55 * sw, "elbow": 85, "out": 8}, "arm_sr": {"fwd": 55 * sw, "elbow": 85, "out": 8},
                 "foot_sl": {"y": -0.5 * sw, "z": max(0.0, 0.45 * math.sin(ph + 1.2))},
                 "foot_sr": {"y": 0.5 * sw, "z": max(0.0, 0.45 * math.sin(ph + 1.2 + math.pi))}})
    S.holder.location = (sb.x, sb.y, sb.z + 0.06 * abs(math.sin(ph)))
    S.holder.rotation_euler = (0, 0, math.atan2(-sd.x, sd.y) + math.pi)
    # ------------------------------------------------ Null, behind him in the void
    X = E.X
    xb, xd = null_at(E, t)
    X.root.scale = (1.6,) * 3
    X.root.location = xb
    X.root.rotation_euler = (math.radians(14), 0, math.atan2(-xd.x, xd.y) + math.pi)
    for side, sgn in (("sl", 1), ("sr", -1)):
        X.arms[side].rotation_euler = (math.radians(-70), math.radians(sgn * 10), 0)
    X.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0.9 * t)
    X.orbit2.rotation_euler = (math.radians(-12), math.radians(14), -0.6 * t)
    place_null_lights(X, fade=1.0)
    # ------------------------------------------------ Patch, high above
    Pt = E.Pt
    Pt.root.location = PATCH_AT + Vector((0, 0, 0.1 * math.sin(t * 3)))
    fwd = (plan.bridge_end - PATCH_AT)
    Pt.root.rotation_euler = (0, 0, math.atan2(-fwd.x, fwd.y) + math.pi)
    pf = dict(PD)
    pf.update({"look_y": 0.6})
    if t >= T["e"]:
        pf["wide"] = ss(T["e"] + 0.15, T["e"] + 0.3, t)
        pf["look_y"] = lerp(0.6, 0.85, ss(T["e"] + 0.15, T["e"] + 0.3, t))
        g = t - T["e"] - 0.18
        pf["glitch"] = 1.0 if (0 <= g < 0.08 or 0.16 <= g < 0.22) else 0.0
        Pt.root.location = Pt.root.location - fwd.normalized() * 0.18 * ss(T["e"] + 0.15, T["e"] + 0.28, t)
    set_patch(Pt, pf)
    for o in Pt.col.objects:                                 # his own view: he is not in it
        o.hide_render = (T["c"] <= t < T["d"]) or o.name.endswith("_beam")
    # ------------------------------------------------ the camera
    loc, look, lens, fstop, focus, shake, roll = camera(E, t)
    from ep10_p2_omg import handheld, rumble
    y1, p1, r1 = handheld(t, shake)
    y2, p2, r2 = rumble(t, 0.05 if t < T["c"] else 0.0)
    q = (look - loc).to_track_quat("-Z", "Y") @ Quaternion((0, 1, 0), math.radians(y1 + y2)) \
        @ Quaternion((1, 0, 0), math.radians(p1 + p2)) @ Quaternion((0, 0, 1), math.radians(r1 + r2 + roll))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.key.location = loc + Vector((1.2, 0, 1.6))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    return {}


def _beams(E, specs):
    """The tool's beams: thin glowing lines (part of the gizmo look), one mesh."""
    me = bpy.data.meshes.get("beams")
    if me is None:
        me = bpy.data.meshes.new("beams")
        ob = bpy.data.objects.new("beams", me)
        E.sc.collection.objects.link(ob)
        me.materials.append(bpy.data.materials["gz_sel"])
        ob.visible_shadow = False
        try:
            ob.cycles.use_motion_blur = False
        except Exception:
            pass
    verts, faces = [], []
    for s in specs:
        m = s["m"]
        w, _, L = s["size"]
        i = len(verts)
        for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            verts.append(tuple(m @ Vector((dx * w, dy * w, dz * L / 2))))
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            faces.append([i + k for k in f])
    me.clear_geometry()
    if verts:
        me.from_pydata(verts, [], faces)
    me.update()


def finish(path, mist_path):
    """A light haze toward the void (the void glows; it shouldn't wash out the near build), the grade."""
    import numpy as np
    from PIL import Image
    import grade as G
    import assemble
    im = Image.open(path).convert("RGB")
    if os.path.exists(mist_path):
        im = G.haze(im, mist_path, None, {"L": 260, "start": 30, "max": 0.35})
    assemble.W, assemble.H = im.size
    assemble.grade(im, {"saturation": 1.18, "glow": 0.5, "threshold": 0.74, "tint": [1.02, 0.98, 1.02]}, 0, 0, None)
    a = np.asarray(im, np.float32) / 255.0
    h_, w_ = a.shape[:2]
    yy, xx = np.mgrid[0:h_, 0:w_]
    r = np.hypot((xx - w_ / 2) / (w_ / 2), (yy - h_ / 2) / (h_ / 2))
    a *= (1 - 0.25 * np.clip((r - 0.6) / 0.7, 0, 1) ** 1.5)[..., None]
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    for k in ("a", "b", "b2", "c", "c2", "d", "e"):
        if k in b:
            T[k] = b[k][0]
    for ln in tl.get("lines", []):
        if ln["name"] == "patch_bad":
            T["patch_bad"] = ln["start"]
    if "e" in b:
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
    E = build(tl, a.assets, a.res, a.samples)
    E.tool_head = None
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
    import ep10_entrance as EN
    print("rendering", len(frames), "frames;", len(E.plan.parts), "parts")
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not a.times:
            continue
        sc.frame_set(f)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        finish(dst, cand[-1] if cand else "")
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
