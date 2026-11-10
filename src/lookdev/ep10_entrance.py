"""Episode 10, part 1: Null's entrance (about 6.5 s, three shots).

The small first portal stands in the forest under Null's storm. His claws are
already through its membrane (frame 1), feel for the frame and grip it. Close
from below, both claws strain on the obsidian while something presses at the
membrane from behind, then they RIP the frame open. Close from the front, the
membrane stretches over a face, tears, and his head bursts out at us: "HI!"

    python src/lookdev/ep10_entrance.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080]
        [--samples 32] [--times 0.4,2.6] [--list]

TIMELINE may be "-" (look-dev before the voice exists: the default timing).
Every moment is a function of time, applied in a frame handler, so any frame
renders on its own (CI shards, motion blur). Frames: OUT/NNNN.png, graded.
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))

FPS = 24
PORTAL_AT = Vector((0.0, 5.0, 0.0))        # the portal faces -y (the camera side); +y is "the other side"
NULL_K = 0.6                               # Null's scale here: his head is about 2.7 m wide, the opening 2 m
LENGTH = 6.6

# The moments (seconds). With a voice, they follow Null's line "HI!".
T = {"s2": 1.75, "s3": 3.45, "grip_r": 1.2, "grip_l": 2.0, "strain": 1.9, "rip": 2.62, "press": 3.45,
     "tear": 3.98, "burst": 4.02, "hi": 4.55, "tilt": 5.35}


def ss(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    u = min(1.0, max(0.0, (x - a) / (b - a)))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def back_out(u, s=1.7):
    """0 -> 1 overshooting past 1 and settling (a snap with weight)."""
    u = min(1.0, max(0.0, u)) - 1
    return 1 + u * u * ((s + 1) * u + s)


def lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c)


class Ep:
    pass


# ----------------------------------------------------------------- the claws
VC = 0.06                                  # one cell of a claw
FINGERS = [  # (knuckle x, knuckle z offset, segment lengths, base width) in the hand's frame (fingers along +z)
    (-0.19, 0.00, (0.30, 0.26, 0.34), 0.18),
    (-0.063, 0.02, (0.34, 0.29, 0.38), 0.18),
    (0.063, 0.02, (0.35, 0.30, 0.39), 0.18),
    (0.19, 0.00, (0.29, 0.25, 0.33), 0.17),
]
THUMB = (0.27, -0.26, (0.22, 0.2, 0.28), 0.17)


def _seg_items(length, w0, w1, rnd, tip=False):
    """A tapered segment along +z made of cells: solid (no gaps), dark, a knuckle
    cell at its base, the last one a hooked claw. Faces on a few cells only."""
    from null import CELL_VARIANTS, _CELL_ODDS, CELL_FACE_COLOURS
    dark = [lin(c) for c in ((8, 6, 11), (13, 9, 17), (5, 4, 7), (17, 11, 23), (10, 8, 14))]
    names, odds = [CELL_VARIANTS.index(k) for k, _ in _CELL_ODDS], [w for _, w in _CELL_ODDS]
    fcols = [lin(c) for c, _ in CELL_FACE_COLOURS]
    items = []
    nz = max(2, int(round(length / VC)))
    for k in range(nz):
        u = (k + 0.5) / nz
        z = u * length
        w = lerp(w0, w1, u)
        if tip:
            w = lerp(w0, VC * 0.9, min(1.0, u * 1.6))
        n = max(1, int(round(w / VC)))
        hook = (0.11 * u ** 2.0) if tip else 0.0          # the claw curls toward the palm (+y)
        knuckle = (k == 0 and not tip)
        for i in range(n):
            for j in range(n):
                x = (i - (n - 1) / 2) * VC
                y = (j - (n - 1) / 2) * VC + hook
                if n > 2 and 0 < i < n - 1 and 0 < j < n - 1:
                    continue                                # hollow inside (never seen)
                half = VC * 0.5 * (1.12 if knuckle else rnd.uniform(0.94, 1.02))
                if tip and u > 0.75:
                    half *= lerp(1.0, 0.55, (u - 0.75) / 0.25)
                cell = None
                glow = (0, 0, 0)
                rgb = rnd.choice(dark)
                if tip and u > 0.55:                        # the claw's point: a cold magenta edge
                    rgb = lin((30, 8, 34))
                    glow = tuple(v * 0.25 * (u - 0.55) / 0.45 for v in lin((255, 40, 230)))
                elif rnd.random() < 0.01:
                    rgb = glow = lin(rnd.choice(((255, 40, 255), (40, 255, 255))))
                elif rnd.random() < 0.16:                   # a few old faces, faint embers
                    sides = {2: -y, 3: x, 4: y, 5: -x}
                    side = max(sides, key=sides.get)
                    cell = (side, rnd.choices(names, odds)[0], tuple(v * (0.05 + 0.5 * rnd.random() ** 3) for v in fcols[0]),
                            1.0 if rnd.random() < 0.05 else rnd.uniform(0.0, 0.9))
                items.append(((x, y, z), half, rgb, glow, 0.0, cell))
    return items


def _empty(col, name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    e.rotation_mode = "XYZ"
    return e


class Claw:
    """An articulated claw hand of Null's cells. Wrist at .root; fingers along the
    root's +z, the palm facing +y. Pose with set(curl, spread, thumb)."""

    def __init__(self, col, name, mat, seed, mirror=False):
        from null import _cubes
        rnd = random.Random(seed)
        self.root = _empty(col, name)
        self.root.rotation_mode = "QUATERNION"
        self.mirror = mirror
        sx = -1 if mirror else 1
        palm = []
        for k in range(int(0.44 / VC)):                    # the palm: a flat slab of cells, the wrist below
            for i in range(int(0.52 / VC)):
                for j in range(3):
                    if j == 1 and 0 < i < int(0.52 / VC) - 1 and k > 0:
                        continue
                    x = -0.26 + (i + 0.5) * VC
                    palm.append(((x * sx, (j - 1) * VC, k * VC - 0.06), VC * 0.5 * rnd.uniform(0.9, 1.05), lin((10, 8, 14)),
                                 (0, 0, 0), rnd.uniform(-0.1, 0.1),
                                 (2 if j == 0 else 4, 1, tuple(v * (0.06 + 0.9 * rnd.random() ** 3.5) for v in lin((236, 190, 60))),
                                  rnd.uniform(0, 0.9)) if rnd.random() < 0.6 else None))
        for k in range(int(0.5 / VC)):                     # the wrist and forearm, running back (-z), thicker
            for i in range(4):
                for j in range(4):
                    if 0 < i < 3 and 0 < j < 3:
                        continue
                    palm.append((((i - 1.5) * VC * 1.6 * sx, (j - 1.5) * VC * 1.4, -0.08 - k * VC), VC * 0.55, lin((9, 7, 12)),
                                 (0, 0, 0), 0.0, None))
        ob = _cubes(name + "_palm", palm, mat, col)
        ob.parent = self.root
        self.parts = [ob]
        self.joints = []                                    # [(knuckle, mid, tip)] per finger, the thumb last
        for f, (kx, kz, lens, w) in enumerate(FINGERS + [THUMB]):
            thumb = f == len(FINGERS)
            j0 = _empty(col, f"{name}_f{f}_0", self.root, (kx * sx, 0.02 if not thumb else 0.06, 0.40 + kz if not thumb else 0.12))
            if thumb:
                j0.rotation_euler = (math.radians(-35), math.radians(-48 * sx), 0)
            chain = [j0]
            parent = j0
            for s_, L in enumerate(lens):
                tip = s_ == len(lens) - 1
                seg = _cubes(f"{name}_f{f}_s{s_}", _seg_items(L, w * (1 - 0.25 * s_), w * (1 - 0.25 * (s_ + 1)), rnd, tip), mat, col)
                seg.parent = parent
                self.parts.append(seg)
                if not tip:
                    nxt = _empty(col, f"{name}_f{f}_{s_ + 1}", parent, (0, 0, L))
                    chain.append(nxt)
                    parent = nxt
            for j_ in chain:
                j_["rest"] = tuple(j_.rotation_euler)
            self.joints.append(chain)

    def set(self, curl, spread=0.0, thumb=0.4, twitch=None):
        """curl: 0 straight .. 1 a fist (per finger: a number or a list of 4).
        spread: the fingers fanning (degrees). twitch: (t, amount) small life."""
        sx = -1 if self.mirror else 1
        for f, chain in enumerate(self.joints):
            thumb_ = f == len(FINGERS)
            c = thumb if thumb_ else (curl[f] if isinstance(curl, (list, tuple)) else curl)
            if twitch:
                t, a = twitch
                c += a * (math.sin(t * 23 + f * 1.9) * 0.6 + math.sin(t * 41 + f * 3.1) * 0.4)
            for k, j_ in enumerate(chain):
                rx, ry, rz = j_["rest"]
                bend = math.radians((70 if k == 0 else 80 if k == 1 else 62) * c)
                fan = 0.0
                if k == 0 and not thumb_:
                    fan = math.radians(spread * (f - 1.5) / 1.5) * sx
                j_.rotation_euler = (rx - bend, ry + fan, rz)

    def place(self, wrist, forward, palm):
        """Wrist position; the fingers' direction; the palm's normal (world)."""
        z = Vector(forward).normalized()
        y = (Vector(palm) - Vector(palm).dot(z) * z).normalized()
        x = y.cross(z)
        m = Matrix((x, y, z)).transposed()
        self.root.location = wrist
        self.root.rotation_quaternion = m.to_quaternion()
        self.root.scale = (1.3, 1.3, 1.3)

    def meshes(self):
        return self.parts

    def hide(self, h):
        for o in self.parts:
            o.hide_render = h


# ------------------------------------------------------------- Null's face
FW, FH = 31, 38                                      # the face image (the head's front, pixel art)


def _face_material():
    """The missing-texture checker, glowing, with a face image on the front whose
    pixels are: white (lines), dark (an open mouth), or clear (the checker)."""
    m = bpy.data.materials.new("null_head_live")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes.new, nt.links.new
    b = nt.nodes["Principled BSDF"]
    tc = N("ShaderNodeTexCoord")
    sep = N("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])
    com = N("ShaderNodeCombineXYZ")
    L(sep.outputs["X"], com.inputs["X"])
    L(sep.outputs["Z"], com.inputs["Y"])
    ck = N("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 1.0
    sc_ = N("ShaderNodeVectorMath")
    sc_.operation = "SCALE"
    sc_.inputs["Scale"].default_value = 2.1
    L(com.outputs["Vector"], sc_.inputs[0])
    L(sc_.outputs[0], ck.inputs["Vector"])
    ck.inputs["Color1"].default_value = (*lin((236, 20, 236)), 1)
    ck.inputs["Color2"].default_value = (*lin((14, 6, 16)), 1)
    im = bpy.data.images.new("null_face_live", FW, FH, alpha=True, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    mp = N("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.0, 0.0)
    mp.inputs["Scale"].default_value = (1 / 3.1, 1 / 3.85, 1.0)
    L(com.outputs["Vector"], mp.inputs["Vector"])
    st = N("ShaderNodeTexImage")
    st.image, st.interpolation, st.extension = im, "Closest", "CLIP"
    L(mp.outputs["Vector"], st.inputs["Vector"])
    front = N("ShaderNodeMath")
    front.operation = "LESS_THAN"
    front.inputs[1].default_value = -0.35
    L(sep.outputs["Y"], front.inputs[0])
    sp = N("ShaderNodeSeparateColor")
    L(st.outputs["Color"], sp.inputs[0])
    white = N("ShaderNodeMath")                            # R: the lines
    white.operation = "MULTIPLY"
    L(sp.outputs["Red"], white.inputs[0])
    L(front.outputs[0], white.inputs[1])
    hole = N("ShaderNodeMath")                             # G: the mouth's inside
    hole.operation = "MULTIPLY"
    L(sp.outputs["Green"], hole.inputs[0])
    L(front.outputs[0], hole.inputs[1])
    c1 = N("ShaderNodeMix")
    c1.data_type = "RGBA"
    L(hole.outputs[0], c1.inputs[0])
    L(ck.outputs["Color"], c1.inputs[6])
    c1.inputs[7].default_value = (*lin((40, 0, 34)), 1)     # the mouth: a deep magenta dark
    c2 = N("ShaderNodeMix")
    c2.data_type = "RGBA"
    L(white.outputs[0], c2.inputs[0])
    L(c1.outputs[2], c2.inputs[6])
    c2.inputs[7].default_value = (1.0, 0.94, 1.0, 1)
    es = N("ShaderNodeMath")                               # the checker glows; the lines burn; the mouth is dark
    es.operation = "MULTIPLY_ADD"
    L(white.outputs[0], es.inputs[0])
    es.inputs[1].default_value = 4.5
    es.inputs[2].default_value = 2.4
    dim = N("ShaderNodeMath")
    dim.operation = "MULTIPLY_ADD"
    L(hole.outputs[0], dim.inputs[0])
    dim.inputs[1].default_value = -0.85
    dim.inputs[2].default_value = 1.0
    es2 = N("ShaderNodeMath")
    es2.operation = "MULTIPLY"
    L(es.outputs[0], es2.inputs[0])
    L(dim.outputs[0], es2.inputs[1])
    pw = N("ShaderNodeMath")
    pw.operation = "MULTIPLY"
    L(es2.outputs[0], pw.inputs[0])
    pw.inputs[1].default_value = 1.0
    m["power"] = pw.name
    L(c2.outputs[2], b.inputs["Base Color"])
    L(c2.outputs[2], b.inputs["Emission Color"])
    L(pw.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Roughness"].default_value = 0.8
    b.inputs["Specular IOR Level"].default_value = 0.15
    return m, im


def draw_face(im, smile=1.0, open_=0.0, wide=0.0, eyes=1.0, eye_y=0.0):
    """The Noob's face, copied: two tall eyes and the smile. open_: the mouth
    opens (dark inside, a white rim); wide: stretched into a grin."""
    R = np.zeros((FH, FW), np.float32)                     # lines
    G = np.zeros((FH, FW), np.float32)                     # mouth inside
    cx = FW // 2
    if eyes > 0:
        eh = int(round(8 * eyes))
        for ex in (cx - 6, cx + 5):                         # two tall eyes, 2 px wide
            y0 = 9 + int(eye_y) + (8 - eh) // 2
            R[y0:y0 + eh, ex - 1:ex + 1] = 1
    if smile > 0:
        mw = int(round(lerp(9, 12, wide)))                  # half width of the mouth
        top = 21
        h = int(round(lerp(1, 9, open_)))                   # how far it opens
        for x in range(-mw, mw + 1):
            u = abs(x) / mw
            yb = top + int(round(h * math.sqrt(max(0.0, 1 - u ** 2.4)) + (1 - u ** 2) * 2 * (1 - open_)))
            yt = top + int(round(-2 * u ** 2 * (1 - open_) + (open_ * (u ** 3) * 1.5)))
            if open_ < 0.15:                                # closed: the smile line (the copied drawing)
                y = top + int(round(4 * (1 - u ** 2)))
                R[y:y + 2, cx + x] = 1
                continue
            R[yb:yb + 2, cx + x] = 1
            R[yt:yt + 1, cx + x] = 1
            if yb > yt + 1:
                G[yt + 1:yb, cx + x] = 1
            if wide > 0.3 and yb > yt + 3 and x % 3 != 0:   # teeth, a row of them
                R[yt + 1:yt + 2, cx + x] = 1
        for s_ in (-1, 1):                                  # the corners turn up
            R[top - 2:top + 1, cx + s_ * mw] = 1
    px = np.zeros((FH, FW, 4), np.float32)
    px[..., 0] = R
    px[..., 1] = G * (1 - R)
    px[..., 3] = 1
    im.pixels.foreach_set(px[::-1].ravel())
    im.update()


# ----------------------------------------------------------------- the build
def _membrane_tear(P):
    """The membrane can tear: where the attribute 'hole' passes 0.5 it is gone,
    with a burning pink edge."""
    me = P.membrane.data
    me.attributes.new("hole", "FLOAT", "POINT")
    m = me.materials[0]
    nt = m.node_tree
    N, L = nt.nodes.new, nt.links.new
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bsdf = nt.nodes["Principled BSDF"]
    h = N("ShaderNodeAttribute")
    h.attribute_name = "hole"
    cut = N("ShaderNodeMath")
    cut.operation = "GREATER_THAN"
    cut.inputs[1].default_value = 0.5
    L(h.outputs["Fac"], cut.inputs[0])
    rim = N("ShaderNodeMapRange")                           # the edge: bright where 'hole' nears 0.5
    rim.interpolation_type = "SMOOTHSTEP"
    rim.inputs["From Min"].default_value = 0.18
    rim.inputs["From Max"].default_value = 0.5
    L(h.outputs["Fac"], rim.inputs["Value"])
    em = N("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*lin((255, 120, 240)), 1)
    st = N("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = 14.0
    L(rim.outputs["Result"], st.inputs[0])
    L(st.outputs[0], em.inputs["Strength"])
    add = N("ShaderNodeAddShader")
    L(bsdf.outputs[0], add.inputs[0])
    L(em.outputs[0], add.inputs[1])
    tr = N("ShaderNodeBsdfTransparent")
    mix = N("ShaderNodeMixShader")
    L(cut.outputs[0], mix.inputs[0])
    L(add.outputs[0], mix.inputs[1])
    L(tr.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    P.base_co = co.reshape(-1, 3).copy()


def _debris(col, assets, n=46):
    from world import material
    B = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    obs = bpy.data.materials.get("w_obsidian") or material("w_obsidian", os.path.join(B, "obsidian.png"), rough=0.35, spec=0.6)
    spark = bpy.data.materials.new("rip_spark")
    spark.use_nodes = True
    bs = spark.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*lin((255, 110, 255)), 1)
    bs.inputs["Emission Color"].default_value = (*lin((255, 110, 255)), 1)
    bs.inputs["Emission Strength"].default_value = 12.0
    out = []
    for i in range(n):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        for c_ in list(ob.users_collection):
            c_.objects.unlink(ob)
        col.objects.link(ob)
        ob.name = f"rip_bit_{i}"
        is_spark = i % 3 == 0
        ob.data.materials.append(spark if is_spark else obs)
        ob["spark"] = is_spark
        ob.hide_render = True
        out.append(ob)
    return out


def build(tl, assets, res, samples):
    from world import build_world, add_world_fx
    from portal import build_portal
    from stage import build_null_char, null_lights
    from null import _mat_body
    E = Ep()
    E.tl = tl
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    E.sc = sc
    cfg = {"seed": 7, "sun": (71, 12), "flat_box": [-7, 7, -40, 8], "plant_clear_box": [-3.4, 3.4, 2.0, 6.5],
           "keep_clear": [(0, -14, 8), (0, 16, 5), (0, 24, 5)],
           "feature_trees": [(-6, 13, "big_oak"), (6, 13, "oak"), (-9, 19, "oak"), (9, 18, "big_oak"), (-4, 22, "birch"),
                             (4, 23, "oak"), (-11, 9, "oak"), (11, 10, "big_oak"), (-7, 27, "oak"), (8, 28, "oak")],
           "clear_plants": [(0.0, 3.6, 2.4)], "particle_box": (-9, 9, 9.0, 24, 0.3, 7.0)}
    E.W = W = build_world(sc, assets, cfg)
    add_world_fx(W)
    from world import fx_set
    fx_set(W, R=1e5, Wd=100.0, Cx=0.0, Cy=0.0, D=0.0, Nx=0.0, Ny=60.0, Dz=-1.0)
    E.P = P = build_portal(sc, assets, at=PORTAL_AT)
    _membrane_tear(P)
    P.light.data.energy = 900
    # Null: only his head comes through here (the rest stays on the other side, in the dark)
    E.X = X = build_null_char(sc, assets, height=10.0)
    null_lights(sc, X)
    keep = (X.head.name, X.neck.name)
    for o in X.col.objects:
        if o.name not in keep and not o.name.startswith(X.neck.name) and "head_noise" not in o.name:
            o.hide_render = True
    X.neck.parent = None
    X.neck.scale = (1.45 * NULL_K,) * 3
    X.neck.rotation_mode = "XYZ"
    m, E.face_im = _face_material()
    X.head.data.materials.clear()
    X.head.data.materials.append(m)
    E.face_mat = m
    X.glow.hide_render = True
    # the claws
    body = bpy.data.materials.get("null_body") or _mat_body()
    E.R = Claw(X.col, "claw_r", body, 11, mirror=False)    # his right: screen-right as he faces us
    E.L = Claw(X.col, "claw_l", body, 23, mirror=True)
    # the other side: a deep dark beyond the opening (seen only through it)
    bpy.ops.mesh.primitive_plane_add(size=1)
    vd = bpy.context.active_object
    vd.name = "beyond"
    vd.scale = (9, 9, 1)
    vd.rotation_euler = (math.radians(90), 0, 0)
    vd.location = PORTAL_AT + Vector((0, 4.5, 2.6))
    vm = bpy.data.materials.new("beyond")
    vm.use_nodes = True
    vb = vm.node_tree.nodes["Principled BSDF"]
    vb.inputs["Base Color"].default_value = (*lin((12, 2, 20)), 1)
    vb.inputs["Emission Color"].default_value = (*lin((70, 10, 90)), 1)
    vb.inputs["Emission Strength"].default_value = 0.6
    vd.data.materials.append(vm)
    vd.visible_shadow = False
    E.beyond = vd
    E.bits = _debris(P.col, assets)
    # light: Null's storm. A cold top light, magenta from his head, purple from the portal
    from stage import char_light
    E.key = char_light(sc, "key", (-3, -4, 6), 900, (0.72, 0.62, 1.0), cone=40, size=1.4)
    E.rim = char_light(sc, "rim", (2.5, 8.5, 5.0), 1400, (1.0, 0.35, 0.85), aim=tuple(PORTAL_AT + Vector((0, 0, 2.5))),
                       cone=50, size=1.0)
    hl = bpy.data.lights.new("head_glow", "POINT")
    hl.color, hl.energy, hl.shadow_soft_size = (1.0, 0.3, 0.95), 0.0, 1.2
    E.head_light = bpy.data.objects.new("head_glow", hl)
    sc.collection.objects.link(E.head_light)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.dof.use_dof = True
    cam.data.sensor_width = 36
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
    sc.view_settings.exposure = -0.1
    sc.render.fps = FPS
    sc.render.compositor_device = "CPU"
    from ep09_new import _mist_output
    _mist_output(sc)
    return E


# ----------------------------------------------------------- the choreography
def opening(t):
    """How far the frame's sides have been torn apart (m): 0, the strain, the rip."""
    strain = 0.04 * ss(T["strain"], T["rip"], t) * (0.5 + 0.5 * math.sin(t * 47))
    return strain + 1.35 * back_out((t - T["rip"]) / 0.34, 1.4) if t >= T["rip"] else strain


def column(side, t):
    """The torn column's offset (x) and lean (radians) for side -1 (left) / +1 (right)."""
    d = opening(t)
    lean = math.radians(9) * ss(T["rip"], T["rip"] + 0.5, t)
    return side * d, side * lean


def claw_pose(E, t):
    """-> for each claw: (show, wrist, forward, palm, curl, spread, thumb, twitch)"""
    P0 = PORTAL_AT
    out = {}
    # the right claw (screen right): already through at frame 1, feeling, then gripping the right column
    d, lean = column(1, t)
    grip_r = ss(T["grip_r"] - 0.22, T["grip_r"], t)
    jerk = 0.03 * math.sin(t * 29) * (1 - grip_r)
    feel = Vector((0.1 + 0.06 * math.sin(t * 3.3), 0.3 + jerk - 0.25 * ss(0, 0.9, t), 2.65 + 0.08 * math.sin(t * 2.1)))
    hold = Vector((0.7 + d, -0.42, 2.45))
    w = feel.lerp(hold, grip_r)
    fwd = Vector((0.1, -1, 0.15)).normalized().lerp(Vector((1, -0.28, 0.0)).normalized(), grip_r)
    palm = Vector((-1, 0, -0.3)).lerp(Vector((0, 1, 0)), grip_r)
    curl = lerp(0.15 + 0.12 * math.sin(t * 5), 0.5, back_out(grip_r, 2.2))
    tw = (t, 0.05 * (1 - grip_r) + 0.03 * ss(T["strain"], T["rip"], t) * (t < T["rip"] + 0.2))
    out["R"] = (True, P0 + w, fwd, palm, curl, lerp(26, 8, grip_r), lerp(0.2, 0.8, grip_r), tw)
    # the left claw: through at grip_l - 0.45, gripping the left column
    d, lean = column(-1, t)
    a = ss(T["grip_l"] - 0.3, T["grip_l"] - 0.12, t)
    grip_l = ss(T["grip_l"] - 0.2, T["grip_l"], t)
    feel = Vector((-0.42, lerp(0.9, 0.25, a), 2.15))
    hold = Vector((-0.7 + d, -0.42, 2.2))
    w = feel.lerp(hold, grip_l)
    fwd = Vector((-0.15, -1, 0.2)).normalized().lerp(Vector((-1, -0.28, 0.0)).normalized(), grip_l)
    palm = Vector((0.2, 0, -1)).lerp(Vector((0, 1, 0)), grip_l)
    curl = lerp(0.2, 0.5, back_out(grip_l, 2.2))
    out["L"] = (t >= T["grip_l"] - 0.3, P0 + w, fwd, palm, curl, lerp(26, 8, grip_l), lerp(0.2, 0.8, grip_l),
                (t + 1.3, 0.05 * (1 - grip_l) + 0.03 * ss(T["strain"], T["rip"], t) * (t < T["rip"] + 0.2)))
    return out


def head_state(t):
    """-> (show, position (world, the head's base), yaw, roll, pitch, face kwargs, press)"""
    P0 = PORTAL_AT
    if t < T["press"] - 0.3:
        return False, P0 + Vector((0, 4, 0.4)), 0, 0, 0, {}, 0.0
    # behind the membrane: leaning on it (a face against glass), then through
    push = ss(T["press"] - 0.3, T["tear"], t)
    burst = back_out((t - T["burst"]) / 0.32, 1.5) if t >= T["burst"] else 0.0
    hi = t - T["hi"]
    y = lerp(0.95, 0.12, push) - 1.75 * burst
    if hi > 0:
        y -= 0.42 * math.exp(-((hi - 0.12) / 0.16) ** 2)          # the shout pushes it at us
    z = 0.95 + 0.12 * math.sin(t * 2.4) * (t > T["burst"])
    roll = math.radians(14) * ss(T["tilt"], T["tilt"] + 0.45, t) - math.radians(5) * ss(T["burst"], T["burst"] + 0.3, t)
    pitch = math.radians(-8) * (1 - ss(T["burst"], T["burst"] + 0.5, t)) + math.radians(6) * ss(T["hi"] - 0.08, T["hi"] + 0.1, t) \
        * (1 - ss(T["hi"] + 0.5, T["hi"] + 1.0, t))
    # the face: no smile until he is through; the smile switches on in a stutter; "HI!"
    sm = 1.0
    if T["burst"] <= t < T["burst"] + 0.5:                 # the smile stutters as he comes through
        u = t - T["burst"]
        sm = 1.0 if int(u / 0.06) % 2 == 0 else 0.0
    face = {"smile": sm, "open_": 0.0, "wide": 0.0, "eyes": 1.0}
    if hi > -0.06:
        o = ss(-0.06, 0.05, hi) * (1 - ss(0.55, 0.8, hi))
        face.update(open_=o * (1.0 if hi < 0.28 else 0.75), wide=ss(0.18, 0.32, hi), eyes=1.0 + 0.25 * o)
        if hi > 0.6:
            face.update(open_=0.0, wide=0.0)
    return True, P0 + Vector((0, y, z)), 0.0, roll, pitch, face, push


def shake(t, trauma):
    """A camera shake from layered sines (location m, roll rad)."""
    if trauma <= 0:
        return Vector((0, 0, 0)), 0.0
    a = trauma ** 2
    x = math.sin(t * 37.1) * 0.6 + math.sin(t * 71.3 + 1.2) * 0.4
    z = math.sin(t * 43.7 + 0.5) * 0.6 + math.sin(t * 83.9 + 2.1) * 0.4
    r = math.sin(t * 29.3 + 2.4) * 0.7 + math.sin(t * 61.1) * 0.3
    return Vector((x, 0, z)) * 0.07 * a, math.radians(3.2) * a * r


def trauma(t):
    k = 0.0
    k = max(k, 0.25 * ss(T["grip_r"] - 0.05, T["grip_r"], t) * (1 - ss(T["grip_r"], T["grip_r"] + 0.25, t)))
    k = max(k, 0.3 * ss(T["strain"], T["rip"], t))
    if t >= T["rip"]:
        k = max(k, 1.0 * math.exp(-(t - T["rip"]) / 0.45) + 0.25)
    if T["s3"] <= t:
        k = max(k, 0.18 + 0.2 * ss(T["press"], T["tear"], t))
    if t >= T["burst"]:
        k = max(k, 0.7 * math.exp(-(t - T["burst"]) / 0.3))
    if t >= T["hi"] - 0.04:
        k = max(k, 1.0 * math.exp(-(t - T["hi"]) / 0.55) + 0.12)
    return min(1.0, k)


def camera(t):
    """-> loc, look, lens, fstop, focus distance (None = to the look point)"""
    P0 = PORTAL_AT
    if t < T["s2"]:                                       # 1: close, beside the membrane: the claws through it
        u = t / T["s2"]
        loc = P0 + Vector((-3.5 + 0.3 * u, -2.0 + 0.12 * u, 1.9))
        look = P0 + Vector((0.25 * ss(T["grip_r"] - 0.4, T["grip_r"] + 0.2, t), -0.5, 2.4))
        return loc, look, 42, 2.8, None
    if t < T["s3"]:                                       # 2: low, from the front: both claws, the rip
        u = (t - T["s2"]) / (T["s3"] - T["s2"])
        loc = P0 + Vector((0.3, -4.9 + 0.5 * u - 0.6 * ss(T["rip"], T["rip"] + 0.3, t), 1.25))
        look = P0 + Vector((0.0, 0.0, 2.55 + 0.25 * ss(T["rip"], T["rip"] + 0.4, t)))
        return loc, look, 25, 4.5, None
    # 3: close, at the opening: the membrane, the face behind it, the burst, HI!
    u = (t - T["s3"]) / (LENGTH - T["s3"])
    back = 0.8 * ss(T["burst"] - 0.05, T["burst"] + 0.25, t)                      # it comes at us: we flinch back
    push = 1.0 * ss(T["hi"] - 0.05, T["hi"] + 0.16, t) * (1 - 0.35 * ss(T["hi"] + 0.4, LENGTH, t))   # the punch-in on HI!
    loc = P0 + Vector((0.1, -8.4 + 0.5 * u - back + push, 2.35))
    look = P0 + Vector((0.0, -0.4 - 1.5 * ss(T["burst"], T["burst"] + 0.3, t), 2.6))
    lens = 32 + 5 * ss(T["hi"] - 0.04, T["hi"] + 0.12, t) * (1 - 0.4 * ss(T["hi"] + 0.3, LENGTH, t))
    return loc, look, lens, 4.0, None


# ---------------------------------------------------------- apply a frame
def drape(P, objs, holes_r=0.05, tear=None):
    """Stretch the membrane over what pushes through it (in the membrane's own
    space, so it follows the frame as it is torn wider); tear holes where things
    have passed through; tear: (centre (x, z), radius) a growing rip."""
    from portal import RES, LIMIT, CONE
    xs, zs, nx, nz = P.grid
    me = P.membrane.data
    dg = bpy.context.evaluated_depsgraph_get()
    inv = np.array(P.membrane.matrix_world.inverted())
    sx = P.membrane.scale.x
    big = 9.0
    H = np.full((nx, nz), big, np.float32)
    N0 = np.full((nx, nz), big, np.float32)
    thru = np.zeros((nx, nz), np.float32)
    for ob in objs:
        if ob.type != "MESH" or ob.hide_render:
            continue
        m_ = ob.data
        co = np.empty(len(m_.vertices) * 3, np.float32)
        m_.vertices.foreach_get("co", co)
        co = np.c_[co.reshape(-1, 3), np.ones(len(m_.vertices), np.float32)]
        loc = co @ (inv @ np.array(ob.evaluated_get(dg).matrix_world)).T
        keep = (loc[:, 1] < 0.9) & (loc[:, 0] > xs[0]) & (loc[:, 0] < xs[-1]) & (loc[:, 2] > zs[0]) & (loc[:, 2] < zs[-1])
        loc = loc[keep]
        if not len(loc):
            continue
        i = np.clip(np.round((loc[:, 0] - xs[0]) / RES).astype(int), 0, nx - 1)
        j = np.clip(np.round((loc[:, 2] - zs[0]) / RES).astype(int), 0, nz - 1)
        np.minimum.at(N0, (i, j), loc[:, 1])
        ok = loc[:, 1] < 0.1
        np.minimum.at(H, (i[ok], j[ok]), loc[ok, 1] - 0.035)
        cross = np.abs(loc[:, 1]) < 0.12                    # where it pierces the skin
        thru[i[cross], j[cross]] = 1.0
    K = int(0.2 / RES)
    for axis in (0, 1):
        out = H.copy()
        for d in range(1, K + 1):
            pen = CONE * (d * RES) ** 2
            for sgn in (1, -1):
                sh = np.roll(H, sgn * d, axis)
                if axis == 0:
                    (sh[:d] if sgn > 0 else sh[-d:])[...] = big
                else:
                    (sh[:, :d] if sgn > 0 else sh[:, -d:])[...] = big
                out = np.minimum(out, sh + pen)
        H = out
    ex = np.minimum(np.arange(nx), np.arange(nx)[::-1])[:, None] * RES * sx
    ez = np.minimum(np.arange(nz), np.arange(nz)[::-1])[None, :] * RES
    hold = np.minimum(ex, ez)
    y = np.clip(np.minimum(H, 0.0), -LIMIT, 0.0)
    y = np.maximum(y, -hold * 1.6)
    # holes: grown out of the pierced cells, ragged
    hole = thru
    r = max(1, int(holes_r / RES))
    for _ in range(r):
        hole = np.maximum.reduce([hole, np.roll(hole, 1, 0), np.roll(hole, -1, 0), np.roll(hole, 1, 1), np.roll(hole, -1, 1)])
    X, Z = np.meshgrid(xs * sx, zs, indexing="ij")
    if tear is not None:
        (cx, cz), R = tear
        ang = np.arctan2(Z - cz, X - cx)
        rag = R * (1 + 0.22 * np.sin(ang * 5 + 1.3) + 0.12 * np.sin(ang * 11 + 0.4))
        dist = np.hypot((X - cx) * 0.85, Z - cz)
        hole = np.maximum(hole, np.clip((rag - dist) / 0.12 + 0.5, 0, 1))
    soft = hole
    for _ in range(2):
        soft = (soft + np.roll(soft, 1, 0) + np.roll(soft, -1, 0) + np.roll(soft, 1, 1) + np.roll(soft, -1, 1)) / 5
    co = P.base_co.copy()
    co[:, 1] = y.ravel()
    # the torn skin curls back from the hole's edge (away from us)
    co[:, 1] += 0.25 * soft.ravel() ** 2
    me.vertices.foreach_set("co", co.ravel())
    me.attributes["stretch"].data.foreach_set("value", np.clip(-y.ravel() / LIMIT, 0, 1) ** 1.6)
    press = np.clip((0.75 - N0) / 0.75, 0, 1)
    for _ in range(2):
        press = (press + np.roll(press, 1, 0) + np.roll(press, -1, 0) + np.roll(press, 1, 1) + np.roll(press, -1, 1)) / 5
    me.attributes["press"].data.foreach_set("value", press.ravel().astype(np.float32))
    me.attributes["hole"].data.foreach_set("value", np.clip(soft.ravel(), 0, 1).astype(np.float32))
    me.update()


def apply(E, t):
    from world import set_sky, set_sun
    from stage import place_null_lights
    from null import cells_look
    P, X = E.P, E.X
    # ------------------------------------------------ Null's storm (his theme, from frame 1)
    STORM = {"glow": (214, 196, 255), "power": 6.0, "horizon": (176, 96, 180), "mid": (84, 52, 132), "zenith": (22, 14, 48),
             "fill": 0.32, "fill_col": (150, 120, 210)}
    set_sky(E.W, STORM)
    set_sun(E.W, 71, 16, 1.5, (0.8, 0.66, 1.0))
    flash = math.exp(-max(0.0, t - T["rip"]) / 0.12) if t >= T["rip"] else 0.0
    flash = max(flash, 0.7 * math.exp(-max(0.0, t - T["hi"]) / 0.1) if t >= T["hi"] else 0.0)
    E.W.sky_pow.inputs[1].default_value = STORM["power"] * (1 + 1.6 * flash)
    E.W.clouds.hide_render = True
    # ------------------------------------------------ the portal: torn open
    rnd = random.Random(4)
    w, h = P.w, P.h
    for k, b in enumerate(P.blocks):
        home = Vector(b["home"])
        i, j = int(round(home.x + w / 2 - 0.5)), int(round(home.z - 0.5))
        side = -1 if i == 0 else 1 if i == w - 1 else 0
        loc, rot = home.copy(), [0.0, 0.0, 0.0]
        if side:
            d, lean = column(side, t)
            pivot = Vector((home.x, 0, 0))
            rel = home - pivot
            rel = Matrix.Rotation(-lean, 3, "Y") @ rel
            loc = pivot + rel + Vector((d, 0, 0))
            rot[1] = -lean
            if t >= T["rip"]:                                 # cracking: a block jolts loose
                kick = rnd.uniform(-1, 1)
                loc += Vector((0.06 * kick, 0.05 * rnd.uniform(-1, 1), 0)) * ss(T["rip"], T["rip"] + 0.2, t)
                rot[0] += 0.08 * kick * ss(T["rip"], T["rip"] + 0.3, t)
        elif j == 0:                                          # the sill tips over toward us
            if t >= T["rip"]:
                u = ss(T["rip"] + 0.04, T["rip"] + 0.42, t)
                ang = math.radians(92) * u ** 1.6
                piv = Vector((home.x, -0.5, 0.0))
                rel = Matrix.Rotation(ang, 3, "X") @ (home - piv)
                loc = piv + rel + Vector((0.15 * (1 if i >= w / 2 else -1) * u, -0.1 * u, 0))
                rot = [ang, 0.0, 0.08 * (1 if i >= w / 2 else -1) * u]
                b.hide_render = t >= T["rip"] + 0.3              # and shatters (the chips fly from it)
        elif j == h - 1:                                      # the lintel breaks in the middle and flies
            if t >= T["rip"]:
                u = t - T["rip"]
                s_ = -1 if i < w / 2 else 1
                v = Vector((s_ * rnd.uniform(1.4, 2.4), -rnd.uniform(1.0, 2.5), rnd.uniform(3.0, 4.5)))
                loc = home + v * u + Vector((0, 0, -9.8 * u * u / 2))
                rot = [u * rnd.uniform(-9, 9), u * rnd.uniform(-9, 9), u * rnd.uniform(-9, 9)]
        if not (j == 0 and side == 0):
            b.hide_render = False
        b.location = loc
        b.rotation_euler = rot
    # the membrane spans the torn opening
    half = 1.0 + opening(t)
    P.membrane.scale = (half / 1.0, 1, 1)
    P.light.data.size = 2 * half
    P.light.data.energy = 900 * (1 + 2.5 * flash) * (1 + 0.6 * ss(T["press"], T["tear"], t))
    flow = P.membrane.data.materials[0]
    flow.node_tree.nodes[flow["flow"]].inputs[1].default_value = (0.05 * t, 0.11 * t, 0.0)
    E.beyond.scale = (2 * half + 0.6, 4.4, 1)
    E.beyond.location = PORTAL_AT + Vector((0, 1.3, 2.5))
    # debris at the rip: obsidian chips and pink sparks
    rnd = random.Random(9)
    for k, ob in enumerate(E.bits):
        t0 = T["rip"] + rnd.uniform(-0.02, 0.18)
        u = t - t0
        life = 1.3 if not ob["spark"] else 0.7
        if not (0 <= u < life):
            ob.hide_render = True
            continue
        ob.hide_render = False
        side = -1 if k % 2 else 1
        o = PORTAL_AT + Vector((side * (1.0 + opening(t0)), -0.3, rnd.uniform(1.0, 4.4)))
        if k % 5 == 4:                                     # from the sill, shattering at our feet
            o = PORTAL_AT + Vector((rnd.uniform(-0.9, 0.9), -0.9, 0.4))
        v = Vector((side * rnd.uniform(0.8, 3.0), -rnd.uniform(0.5, 3.0), rnd.uniform(0.5, 3.5)))
        p = o + v * u + Vector((0, 0, -9.8 * u * u / 2 * (0.3 if ob["spark"] else 1)))
        ob.location = p
        s_ = (0.05 if ob["spark"] else rnd.uniform(0.08, 0.22)) * (1 - u / life * (0.8 if ob["spark"] else 0.2))
        ob.scale = (s_, s_, s_)
        ob.rotation_euler = (u * 7 + k, u * 5, u * 3)
    # ------------------------------------------------ the claws
    pose = claw_pose(E, t)
    for key, cl in (("R", E.R), ("L", E.L)):
        show, wrist, fwd, palm, curl, spread, thumb, tw = pose[key]
        cl.hide(not show)
        cl.place(wrist, fwd, palm)
        cl.set(curl, spread, thumb, tw)
    # ------------------------------------------------ the head
    show, base, yaw, roll, pitch, face, press = head_state(t)
    X.neck.location = base
    X.neck.rotation_euler = (pitch, roll, yaw)
    for o in [X.head] + [c for c in X.neck.children if "head_noise" in c.name]:
        o.hide_render = not show
    if face:
        draw_face(E.face_im, **face)
    else:
        draw_face(E.face_im, smile=0.0, eyes=0.0)
    E.face_mat.node_tree.nodes[E.face_mat["power"]].inputs[1].default_value = 1.0 if t >= T["burst"] else 0.55
    E.head_light.location = base + Vector((0, -1.6, 1.6))
    E.head_light.data.energy = 900 * ss(T["burst"] - 0.1, T["burst"] + 0.2, t) * (1 + 0.8 * flash)
    cells_look(near=0.6, far=1.6, awake=1.0, power=0.8)
    X.root.location = PORTAL_AT + Vector((0, 40, -30))
    place_null_lights(X, fade=0.0)
    bpy.context.view_layer.update()
    tear = None
    if t >= T["tear"]:
        R_ = 0.15 + 2.2 * ss(T["tear"], T["burst"] + 0.3, t) ** 0.7
        tear = ((0.0, 2.6), R_)
    pierce = [o for cl in (E.R, E.L) for o in cl.meshes() if not o.hide_render]
    drape(P, pierce + ([X.head] if show else []), tear=tear)
    # ------------------------------------------------ the camera
    loc, look, lens, fstop, focus = camera(t)
    off, roll_ = shake(t, trauma(t))
    loc = loc + off
    q = (look - loc).to_track_quat("-Z", "Y")
    q = q @ Quaternion((0, 0, 1), roll_)
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.key.location = loc + Vector((-1.6, 0.4, 2.2))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    return {"g": 0.0, "s": 1.0}


def finish(path, mist_path):
    """Haze (thin), the episode grade, and a vignette: Null's moment is dark at the edges."""
    from PIL import Image
    import grade as G
    import assemble
    im = Image.open(path).convert("RGB")
    if os.path.exists(mist_path):
        im = G.haze(im, mist_path, None, {"L": 140, "start": 14, "max": 0.45, "haze_storm": True})
    assemble.W, assemble.H = im.size
    assemble.grade(im, {"saturation": 1.12, "glow": 0.7, "threshold": 0.68, "tint": [1.0, 0.9, 1.06]}, 0, 0, None)
    a = np.asarray(im, np.float32) / 255.0
    h_, w_ = a.shape[:2]
    yy, xx = np.mgrid[0:h_, 0:w_]
    r = np.hypot((xx - w_ / 2) / (w_ / 2), (yy - h_ / 2) / (h_ / 2))
    a *= (1 - 0.38 * np.clip((r - 0.55) / 0.75, 0, 1) ** 1.5)[..., None]
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ main
def default_timeline():
    return {"length": LENGTH, "fps": FPS, "beats": {}, "lines": []}


def align(tl, voice_path=None):
    """Follow the episode file: the beats set the moments, and the mouth opens
    on the first sound of Null's "HI!" (his voice swells in before the word)."""
    global LENGTH
    b = tl.get("beats", {})
    if "claws" in b:
        T["grip_r"] = b["grip"][0]
        T["s2"] = b["grip"][0] + 0.55
        T["grip_l"] = b["grip_l"][0]
        T["strain"] = b["grip_l"][0] - 0.1
        T["rip"] = b["rip"][0]
        T["s3"] = T["press"] = b["press"][0]
        T["tear"] = b["tear"][0]
        T["burst"] = b["tear"][0] + 0.04
        hi = next((ln for ln in tl.get("lines", []) if ln.get("who") == "null"), None)
        T["hi"] = hi["start"] + 0.12 if hi else T["burst"] + 0.53
        if hi and voice_path and os.path.exists(voice_path):
            import soundfile as sf
            x, sr = sf.read(voice_path)
            x = x.mean(1) if x.ndim > 1 else x
            seg = np.abs(x[int(hi["start"] * sr):int(hi["end"] * sr)])
            if len(seg):
                env = np.convolve(seg, np.ones(int(0.01 * sr)) / int(0.01 * sr), "same")
                on = np.nonzero(env > 0.25 * env.max())[0]
                if len(on):
                    T["hi"] = hi["start"] + on[0] / sr
        T["tilt"] = T["hi"] + 0.8
    LENGTH = tl.get("length", LENGTH) + 0.4


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
    tl = default_timeline() if a.timeline == "-" else json.load(open(a.timeline))
    align(tl, a.voice)
    n_frames = int(round((tl["length"] + 0.4) * FPS)) + 1 if a.timeline != "-" else int(round(LENGTH * FPS))
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    E = build(tl, a.assets, a.res, a.samples)
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
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        finish(dst, cand[-1] if cand else "")
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
