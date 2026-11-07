"""The world, rebuilt after the reference's environments (see ENV_STUDY.md).

    from world import build_world
    W = build_world(sc, assets_dir, cfg)          # cfg: {"seed", "sun": (azimuth, elevation), "stage": [(x, y), ...]}

What it builds:
- terrain: a meadow where the characters stand, a big terraced hill behind it, a
  second hill with a cherry grove, a lake, and a ring of far mountains with stone
  cliffs and snow. Steps are one block, so slopes show dirt-side stripes under
  the green fringe. The near world is at block scale; the far world uses blocks 3
  units wide, with textures tiled so the pixel size stays the same.
- trees: fancy round oaks, big oaks, birches and cherries, with see-through leaves
  (all faces drawn, as Minecraft's fancy leaves, so the inside of a canopy shows
  dark through the holes). Far forests are leaf bumps on the far terrain.
- ground cover: dense short and tall grass, ferns and flowers as crossed sprites.
- sky: a deep-blue-to-pale gradient with a warm glow around the sun, Minecraft's
  blocky cloud layer from clouds.png, and a warm sun with soft fill.
- depth: render_depth() renders a camera-distance pass; grade.py turns it into
  aerial haze (far things fade to pale blue).
Units: one block = 1. Ground level at the stage is z = 0 (top of the grass).
"""
import math
import os
import random

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.path.join(REPO, "build", "lookdev_tex")

GRASS = (150, 210, 70)          # the reference's yellow-green grass
FOLIAGE = (140, 205, 52)        # oak leaves
BIRCH_LV = (128, 167, 85)
SPRUCE_LV = (97, 153, 97)
WATER = (52, 104, 214)


# ------------------------------------------------------------------ textures
def _tex_root(assets):
    return os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures")


def bake_textures(assets):
    """Tint Minecraft's grey textures (as the game does with biome colours) and
    build the grass-side texture: dirt with the tinted green fringe."""
    os.makedirs(CACHE, exist_ok=True)
    B = os.path.join(_tex_root(assets), "block")

    def load(n):
        im = Image.open(os.path.join(B, n + ".png")).convert("RGBA")
        return im.crop((0, 0, 16, 16))

    def tint(im, c, gain=1.0):
        a = np.asarray(im).astype(np.float32)
        a[..., :3] = a[..., :3] * (np.array(c, np.float32) / 255.0) * gain
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    out = {}

    def save(name, im):
        p = os.path.join(CACHE, name + ".png")
        im.save(p)
        out[name] = p

    save("grass_top", tint(load("grass_block_top"), GRASS, 1.18))
    side = np.asarray(load("grass_block_side")).astype(np.float32)
    ov = np.asarray(load("grass_block_side_overlay")).astype(np.float32)
    m = ov[..., 3:4] / 255.0
    side[..., :3] = side[..., :3] * (1 - m) + ov[..., :3] * (np.array(GRASS, np.float32) / 255.0) * 1.18 * m
    save("grass_side", Image.fromarray(np.clip(side, 0, 255).astype(np.uint8)))
    for n in ("dirt", "stone", "andesite", "gravel", "sand", "snow", "grass_block_snow", "oak_log", "oak_log_top",
              "birch_log", "birch_log_top", "cherry_log", "cherry_log_top", "cherry_leaves", "coarse_dirt",
              "poppy", "dandelion", "oxeye_daisy", "cornflower", "azure_bluet", "pink_petals"):
        save(n, load(n))
    save("oak_leaves", tint(load("oak_leaves"), FOLIAGE, 1.55))
    save("birch_leaves", tint(load("birch_leaves"), BIRCH_LV, 1.3))
    for n in ("short_grass", "tall_grass_bottom", "tall_grass_top", "fern", "large_fern_bottom", "large_fern_top", "bush"):
        try:
            save(n, tint(load(n), GRASS, 1.3))
        except FileNotFoundError:
            pass
    save("water", tint(load("water_still"), WATER))
    return out


# ----------------------------------------------------------------- materials
def material(name, path, alpha=False, rough=0.8, translucent=0.0, spec=0.25, tile=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    t.interpolation = "Closest"
    if tile != 1.0:
        uv = nt.nodes.new("ShaderNodeUVMap")
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        sc.inputs["Scale"].default_value = tile
        nt.links.new(uv.outputs["UV"], sc.inputs[0])
        nt.links.new(sc.outputs[0], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    out = nt.nodes["Material Output"]
    if translucent > 0:                      # light through leaves and grass blades
        tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
        nt.links.new(t.outputs["Color"], tr.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.inputs["Fac"].default_value = translucent
        nt.links.new(b.outputs["BSDF"], mx.inputs[1])
        nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
        surf = mx.outputs["Shader"]
    else:
        surf = b.outputs["BSDF"]
    if alpha:
        tp = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx2 = nt.nodes.new("ShaderNodeMixShader")
        gt = nt.nodes.new("ShaderNodeMath")              # a hard cutout, as the game
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.5
        nt.links.new(t.outputs["Alpha"], gt.inputs[0])
        nt.links.new(gt.outputs[0], mx2.inputs["Fac"])
        nt.links.new(tp.outputs["BSDF"], mx2.inputs[1])
        nt.links.new(surf, mx2.inputs[2])
        surf = mx2.outputs["Shader"]
    nt.links.new(surf, out.inputs["Surface"])
    return m


def flat(name, rgb, rough=0.5, emission=0.0, spec=0.3):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    lin = tuple(((v / 255 + 0.055) / 1.055) ** 2.4 for v in rgb)
    b.inputs["Base Color"].default_value = (*lin, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    if emission:
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = emission
    return m


# ------------------------------------------------------------------- meshes
_DIRS = [((0, 0, 1), "top"), ((0, 0, -1), "bottom"), ((1, 0, 0), "side"), ((-1, 0, 0), "side"),
         ((0, 1, 0), "side"), ((0, -1, 0), "side")]


def _quad(x, y, z, d):
    dx, dy, dz = d
    if dz == 1:
        return [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
    if dz == -1:
        return [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y, z), (x, y, z)]
    if dx == 1:
        return [(x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x + 1, y, z + 1)]
    if dx == -1:
        return [(x, y + 1, z), (x, y, z), (x, y, z + 1), (x, y + 1, z + 1)]
    if dy == 1:
        return [(x + 1, y + 1, z), (x, y + 1, z), (x, y + 1, z + 1), (x + 1, y + 1, z + 1)]
    return [(x, y, z), (x + 1, y, z), (x + 1, y, z + 1), (x, y, z + 1)]


def voxel_mesh(sc, name, cells, kinds, occluders=None, keep_leaf_faces=(), scale=(1, 1, 1), offset=(0, 0, 0)):
    """One object for {(x, y, z): kind}. A face is drawn unless its neighbour
    (in `cells` or `occluders`) hides it; kinds in keep_leaf_faces keep their faces
    toward each other (fancy leaves). kinds: {kind: {"top", "side", "bottom": material}}."""
    me = bpy.data.meshes.new(name)
    slots = {}
    for k in kinds.values():
        for m in k.values():
            if m.name not in slots:
                slots[m.name] = len(slots)
                me.materials.append(m)
    verts, faces, mats = {}, [], []
    vlist = []

    def vi(p):
        i = verts.get(p)
        if i is None:
            i = verts[p] = len(vlist)
            vlist.append(p)
        return i

    occ = occluders or {}
    for (x, y, z), kind in cells.items():
        for d, face in _DIRS:
            nb = (x + d[0], y + d[1], z + d[2])
            nk = cells.get(nb) or occ.get(nb)
            if nk is not None:
                if not (kind in keep_leaf_faces and nk in keep_leaf_faces):
                    continue
            faces.append([vi(p) for p in _quad(x, y, z, d)])
            mats.append(slots[kinds[kind][face].name])
    sx, sy, sz = scale
    ox, oy, oz = offset
    me.from_pydata([(p[0] * sx + ox, p[1] * sy + oy, p[2] * sz + oz) for p in vlist], [], faces)
    uv = me.uv_layers.new()
    for poly, mi in zip(me.polygons, mats):
        poly.material_index = mi
        for li, c in zip(poly.loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
            uv.data[li].uv = c
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    return ob


def crosses(sc, name, items, seed=11):
    """Plants as two crossed quads each, one mesh: items = [(x, y, z, size, material)]."""
    me = bpy.data.meshes.new(name)
    slots = {}
    rnd = random.Random(seed)
    verts, faces, mats, uvs = [], [], [], []
    for x, y, z, s, m in items:
        if m.name not in slots:
            slots[m.name] = len(slots)
            me.materials.append(m)
        a0 = rnd.uniform(0, math.pi)
        for a in (a0 + math.pi / 4, a0 - math.pi / 4):
            dx, dy = 0.5 * s * math.cos(a), 0.5 * s * math.sin(a)
            i = len(verts)
            verts += [(x - dx, y - dy, z), (x + dx, y + dy, z), (x + dx, y + dy, z + s), (x - dx, y - dy, z + s)]
            faces.append([i, i + 1, i + 2, i + 3])
            mats.append(slots[m.name])
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new()
    for poly, mi in zip(me.polygons, mats):
        poly.material_index = mi
        for li, c in zip(poly.loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
            uv.data[li].uv = c
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    return ob


def only_camera(ob, shadow=False):
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission"):
        setattr(ob, attr, False)
    ob.visible_shadow = shadow


# -------------------------------------------------------------------- noise
class Noise:
    def __init__(self, seed):
        self.r = np.random.default_rng(seed).random((256, 256))

    def value(self, x, y):
        xi, yi = math.floor(x), math.floor(y)
        fx, fy = x - xi, y - yi
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        r = self.r
        a, b = r[xi % 256, yi % 256], r[(xi + 1) % 256, yi % 256]
        c, d = r[xi % 256, (yi + 1) % 256], r[(xi + 1) % 256, (yi + 1) % 256]
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

    def fbm(self, x, y, octaves=4):
        v, amp, f, tot = 0.0, 1.0, 1.0, 0.0
        for _ in range(octaves):
            v += amp * self.value(x * f, y * f)
            tot += amp
            amp *= 0.5
            f *= 2.03
        return v / tot


# ------------------------------------------------------------------ terrain
def _dome(x, y, cx, cy, r, h):
    d = math.hypot(x - cx, y - cy) / r
    return h * max(0.0, 1 - d * d) ** 1.4


PEAKS = [(-330, -55, 150, 70), (-300, 12, 112, 52), (-372, 70, 178, 80), (-285, 108, 92, 48),
         (-390, -150, 140, 76), (-292, -118, 84, 46), (-420, 0, 128, 74), (-318, 46, 96, 40),
         (-350, -10, 132, 44), (-265, -40, 70, 36), (-268, 60, 66, 34), (-400, 120, 150, 70)]   # x, y, height, radius


class Layout:
    """The landscape as height fields. Stage = flat ground at the origin."""

    def __init__(self, seed=7, cfg=None):
        self.n = Noise(seed)
        self.cfg = cfg or {}
        self.lake = self.cfg.get("lake", (-58.0, 7.0, 19.0))         # x, y, radius

    def height(self, x, y):
        """North (+y): the big terraced hill behind the stage. West (-x): the
        valley vista, falling to a lake ringed by stone cliffs, with high jagged
        snowy mountains beyond. Elsewhere a lower ring of far mountains."""
        n = self.n
        h = 1.6 * (n.fbm(x * 0.045, y * 0.045) - 0.5)
        h += _dome(x, y, -6, 50, 44, 26)                 # the big hill (gentle: wide steps)
        h += _dome(x, y, 30, 62, 30, 17)                  # the cherry hill
        h += _dome(x, y, 66, 26, 30, 13)
        h += _dome(x, y, 20, -40, 28, 10)
        h += 4.0 * (n.fbm(x * 0.03 + 50, y * 0.03 + 9) - 0.5) * min(1.0, max(0.0, (y - 14) / 30))
        # the west valley: the ground steps down toward the lake
        wv = min(1.0, max(0.0, (-x - 16) / 26))
        h -= 3.5 * wv * max(0.0, 1 - abs(y - 6) / 45)
        h += _dome(x, y, -60, 40, 18, 16) + _dome(x, y, -62, -26, 16, 14)    # cliffs on both banks
        # mountains
        dist = math.hypot(x, y - 20)
        ridge = 1 - abs(2 * n.fbm(x * 0.016 + 11, y * 0.016 + 5, 5) - 1)        # sharp crests
        west = min(1.0, max(0.0, (-x - 40) / 40)) * max(0.0, 1 - abs(y - 5) / (0.9 * max(1.0, -x)))  # the vista's sector
        if dist > 105:
            k = min(1.0, (dist - 105) / 60) * (1 - 0.85 * west * min(1.0, max(0.0, (250 + x) / 40)))
            h += k * (18 + 45 * n.fbm(x * 0.012 + 3, y * 0.012 + 7, 5) ** 1.5 + 30 * ridge ** 3)
        if x < -220:                                      # the great range of the vista: separate peaks
            pk = 0.0
            for px, py, ph, pr in PEAKS:
                d = math.hypot(x - px, y - py) / pr
                if d < 1:
                    pk = max(pk, ph * (1 - d) ** 1.25)
            if pk > 0:
                pk *= 0.62 + 0.75 * ridge                  # crests and gullies on the faces
            h += max(pk, 14 * min(1.0, (-x - 220) / 40))
        # the stage: flat around the origin
        sx, sy = self.cfg.get("stage_center", (0.0, 0.0))
        ds = math.hypot(x - sx, y - sy)
        if ds < 13:
            h = h * max(0.0, (ds - 8) / 5)
        # the lake
        lx, ly, lr = self.lake
        dl = math.hypot((x - lx) * 0.8, y - ly) / lr
        if dl < 1.0:
            h = min(h, -2.5 * (1 - dl))
        elif dl < 1.3:
            h = min(h, (dl - 1) / 0.3 * 1.5)
        return h


def _columns(layout, x0, x1, y0, y1, step, skip=None):
    H = {}
    for gx in range(x0, x1):
        for gy in range(y0, y1):
            wx, wy = (gx + 0.5) * step, (gy + 0.5) * step
            if skip and skip(wx, wy):
                continue
            H[(gx, gy)] = int(math.floor(layout.height(wx, wy) / step + 0.5))
    return H


def _terrain_cells(H, step, snowline, lake, scale_far=False, noise=None):
    """Fill each column from just under its lowest neighbour up to its top."""
    cells = {}
    self_noise = noise or Noise(99)
    lx, ly, lr = lake
    for (gx, gy), h in H.items():
        nbs = [H.get((gx + 1, gy), h), H.get((gx - 1, gy), h), H.get((gx, gy + 1), h), H.get((gx, gy - 1), h)]
        low = min(nbs + [h]) - 1
        steep = h - min(nbs) >= 2
        wz = h * step
        wx, wy = (gx + 0.5) * step, (gy + 0.5) * step
        near_water = math.hypot(wx - lx, wy - ly) < lr * 1.15 and wz <= 1
        for z in range(low, h):
            depth = h - 1 - z
            sl = snowline + 8 * (math.sin(wx * 0.11) + math.cos(wy * 0.13))
            if wz > sl:
                if scale_far:                                  # far peaks: snow, with rock breaking through
                    rock = steep and self_noise.value(gx * 0.45 + z * 0.3, gy * 0.45) > 0.5   # rock bands through the snow
                    k = "snowblock" if (z + 1) * step > sl - 6 and not rock else ("andesite" if z % 4 == 0 else "stone")
                else:
                    k = "snow" if depth == 0 else ("snowblock" if wz - (h - z) * step > sl - 10 else "stone")
            elif steep and wz > 8:
                k = "andesite" if (int(wx * 0.3) + int(wy * 0.21) + z) % 3 == 0 else "stone"
            elif near_water:
                k = "sand" if depth < 2 else "stone"
            elif depth == 0:
                k = "grass"
            elif depth < 3:
                k = "dirt"
            else:
                k = "stone"
            cells[(gx, gy, z)] = k
    return cells


# -------------------------------------------------------------------- trees
def _blob(cells, cx, cy, cz, rx, rz, kind, rnd, rough=0.38):
    R = int(math.ceil(rx)) + 1
    Z = int(math.ceil(rz)) + 1
    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            for dz in range(-Z, Z + 1):
                d = (dx / rx) ** 2 + (dy / rx) ** 2 + (dz / rz) ** 2
                if d + rnd.uniform(-rough, rough) * (0.4 + d) < 1.0:
                    cells.setdefault((cx + dx, cy + dy, cz + dz), kind)


def tree(cells, x, y, z, kind, rnd):
    """Adds one tree's blocks (logs: 'oak_log' etc., leaves: 'oak_lv' etc.) to cells."""
    if kind == "oak":
        h = rnd.randint(6, 8)
        for k in range(h):
            cells[(x, y, z + k)] = "oak_log"
        _blob(cells, x, y, z + h - 1, rnd.uniform(3.0, 3.9), rnd.uniform(2.5, 3.1), "oak_lv", rnd, rough=0.26)
    elif kind == "big_oak":
        h = rnd.randint(8, 11)
        for k in range(h):
            cells[(x, y, z + k)] = "oak_log"
        _blob(cells, x, y, z + h, rnd.uniform(4.2, 5.2), rnd.uniform(3.2, 3.8), "oak_lv", rnd, rough=0.24)
        for _ in range(rnd.randint(2, 3)):                  # branches with their own leaf clumps
            a = rnd.uniform(0, 2 * math.pi)
            bz = z + rnd.randint(h - 5, h - 2)
            ex, ey = x + round(3 * math.cos(a)), y + round(3 * math.sin(a))
            for t in range(1, 4):
                cells[(x + round(t * math.cos(a)), y + round(t * math.sin(a)), bz + t // 2)] = "oak_log"
            _blob(cells, ex, ey, bz + 2, rnd.uniform(2.8, 3.4), 2.3, "oak_lv", rnd, rough=0.26)
    elif kind == "birch":
        h = rnd.randint(6, 8)
        for k in range(h):
            cells[(x, y, z + k)] = "birch_log"
        _blob(cells, x, y, z + h - 1, rnd.uniform(2.4, 2.9), rnd.uniform(2.4, 3.0), "birch_lv", rnd, rough=0.28)
    elif kind == "cherry":
        h = rnd.randint(5, 7)
        a = rnd.uniform(0, 2 * math.pi)
        tx, ty = x, y
        for k in range(h):
            if k >= h - 3:                                 # the trunk leans out near the top
                tx, ty = x + round((k - h + 4) * math.cos(a)), y + round((k - h + 4) * math.sin(a))
            cells[(tx, ty, z + k)] = "cherry_log"
        _blob(cells, tx, ty, z + h, rnd.uniform(4.4, 5.4), rnd.uniform(2.0, 2.5), "cherry_lv", rnd, rough=0.26)
        for _ in range(rnd.randint(4, 8)):                 # pink hanging bits under the canopy
            hx, hy = tx + rnd.randint(-3, 3), ty + rnd.randint(-3, 3)
            cells.setdefault((hx, hy, z + h - 2), "cherry_lv")


# ------------------------------------------------------------------- clouds
def cloud_cells(assets, center, radius_px):
    im = Image.open(os.path.join(_tex_root(assets), "environment", "clouds.png")).convert("L")
    a = np.asarray(im)
    cx, cy = center
    cells = {}
    for i in range(-radius_px, radius_px):
        for j in range(-radius_px, radius_px):
            if a[(cy + j) % 256, (cx + i) % 256] > 128:
                cells[(i, j, 0)] = "c"
    return cells


# --------------------------------------------------------------------- sky
def sky(sc, sun_dir, fill=1.0):
    """The camera sees the sky gradient and the sun's glow; the scene gets a soft fill."""
    w = bpy.data.worlds.new("sky_v2")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    lin = lambda c: (*(((v / 255 + 0.055) / 1.055) ** 2.4 for v in c), 1)   # noqa: E731
    cr.elements[0].position, cr.elements[0].color = 0.0, lin((200, 224, 250))
    cr.elements[1].position, cr.elements[1].color = 0.55, lin((40, 128, 245))
    e = cr.elements.new(0.16)
    e.color = lin((118, 182, 255))
    # the glow around the sun: (dir . sun)^k
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(tc.outputs["Generated"], dot.inputs[0])
    dot.inputs[1].default_value = tuple(Vector(sun_dir).normalized())
    cl = nt.nodes.new("ShaderNodeMath")
    cl.operation = "MAXIMUM"
    cl.inputs[1].default_value = 0.0
    nt.links.new(dot.outputs["Value"], cl.inputs[0])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 6.0
    nt.links.new(cl.outputs[0], pw.inputs[0])
    glow = nt.nodes.new("ShaderNodeMix")
    glow.data_type = "RGBA"
    glow.blend_type = "SCREEN"
    nt.links.new(pw.outputs[0], glow.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], glow.inputs["A"])
    glow.inputs["B"].default_value = lin((255, 236, 236))
    seen = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(glow.outputs["Result"], seen.inputs["Color"])
    seen.inputs["Strength"].default_value = 1.0
    lit = nt.nodes.new("ShaderNodeBackground")            # the light the world gets: a soft cool fill
    lit.inputs["Color"].default_value = lin((176, 204, 240))
    lit.inputs["Strength"].default_value = fill
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"])
    nt.links.new(lit.outputs["Background"], mx.inputs[1])
    nt.links.new(seen.outputs["Background"], mx.inputs[2])
    nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    return w


def sun_object(sc, azimuth, elevation, energy=5.4, color=(1.0, 0.87, 0.7)):
    """azimuth 0 = the sun is straight ahead of a camera looking +y (behind the hill);
    90 = to the right (+x). Returns the object and the direction toward the sun."""
    a, e = math.radians(azimuth), math.radians(elevation)
    to_sun = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    s = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sc.collection.objects.link(s)
    s.data.energy, s.data.color, s.data.angle = energy, color, math.radians(1.2)
    s.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
    return s, to_sun


# -------------------------------------------------------------------- world
class World:
    pass


def build_world(sc, assets, cfg=None):
    cfg = cfg or {}
    rnd = random.Random(cfg.get("seed", 7))
    T = bake_textures(assets)
    sc.cycles.transparent_max_bounces = 48                # many leaf and grass layers in a row
    W = World()
    W.layout = L = Layout(cfg.get("seed", 7), cfg)
    M = {k: material("w_" + k, p) for k, p in T.items() if k in (
        "grass_top", "grass_side", "dirt", "stone", "andesite", "gravel", "sand", "snow", "grass_block_snow",
        "oak_log", "oak_log_top", "birch_log", "birch_log_top", "cherry_log", "cherry_log_top")}
    for k in ("oak_leaves", "birch_leaves", "cherry_leaves"):
        M[k] = material("w_" + k, T[k], alpha=True, rough=0.6, translucent=0.42)
    KINDS = {
        "grass": {"top": M["grass_top"], "side": M["grass_side"], "bottom": M["dirt"]},
        "dirt": {"top": M["dirt"], "side": M["dirt"], "bottom": M["dirt"]},
        "stone": {"top": M["stone"], "side": M["stone"], "bottom": M["stone"]},
        "sand": {"top": M["sand"], "side": M["sand"], "bottom": M["sand"]},
        "snow": {"top": M["snow"], "side": M["grass_block_snow"], "bottom": M["stone"]},
        "snowblock": {"top": M["snow"], "side": M["snow"], "bottom": M["snow"]},
        "andesite": {"top": M["andesite"], "side": M["andesite"], "bottom": M["andesite"]},
        "oak_log": {"top": M["oak_log_top"], "side": M["oak_log"], "bottom": M["oak_log_top"]},
        "birch_log": {"top": M["birch_log_top"], "side": M["birch_log"], "bottom": M["birch_log_top"]},
        "cherry_log": {"top": M["cherry_log_top"], "side": M["cherry_log"], "bottom": M["cherry_log_top"]},
        "oak_lv": {"top": M["oak_leaves"], "side": M["oak_leaves"], "bottom": M["oak_leaves"]},
        "birch_lv": {"top": M["birch_leaves"], "side": M["birch_leaves"], "bottom": M["birch_leaves"]},
        "cherry_lv": {"top": M["cherry_leaves"], "side": M["cherry_leaves"], "bottom": M["cherry_leaves"]},
    }
    LEAVES = ("oak_lv", "birch_lv", "cherry_lv")
    # --- near terrain, block scale
    NX0, NX1, NY0, NY1 = cfg.get("near", (-70, 70, -40, 105))
    Hn = _columns(L, NX0, NX1, NY0, NY1, 1)
    W.H = Hn
    near = _terrain_cells(Hn, 1, 70, L.lake)
    # --- trees
    tcells = {}
    stage = cfg.get("stage", [(0, 0)])
    keep = cfg.get("keep_clear", [])                       # [(x, y, r)]: e.g. the camera's view to the stage
    for gx in range(NX0 + 3, NX1 - 3, 5):
        for gy in range(NY0 + 3, NY1 - 3, 5):
            x, y = gx + rnd.randint(-2, 2), gy + rnd.randint(-2, 2)
            h = Hn.get((x, y))
            if h is None or near.get((x, y, h - 1)) != "grass":
                continue
            dst = min(math.hypot(x - sx, y - sy) for sx, sy in stage)
            if dst < 9 or any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep):
                continue
            g = L.n.fbm(x * 0.05 + 70, y * 0.05 + 13)                 # trees in groves, open slopes between
            front = 14 < y < 40 and -30 < x < 20                      # the open face of the big hill
            p_tree = 0.1 if dst < 20 else (0.75 if g > (0.62 if front else 0.54) else (0.02 if front else 0.07))
            if rnd.random() > p_tree:
                continue
            on_cherry_hill = math.hypot(x - 30, y - 62) < 24
            r_ = rnd.random()
            kind = ("cherry" if r_ < 0.7 else "oak") if on_cherry_hill else \
                ("big_oak" if r_ < 0.12 else "birch" if r_ < 0.27 else "cherry" if r_ < 0.31 else "oak")
            tree(tcells, x, y, h, kind, rnd)
    # trees placed for the cameras: cherries where the shots look (meadow and hill frames)
    for fx, fy, fk in cfg.get("feature_trees", [(9, 15, "cherry"), (14, 23, "cherry"), (5, 27, "cherry"),
                                                (-12, 21, "cherry"), (19, 31, "cherry"), (-5, 33, "oak"),
                                                (-18, 30, "big_oak"), (11, 38, "cherry"), (2, 41, "oak")]):
        h = Hn.get((fx, fy))
        if h is not None and near.get((fx, fy, h - 1)) == "grass":
            tree(tcells, fx, fy, h, fk, rnd)
    # bushes: low leaf mounds on the slopes and the meadow's edge (the reference's dense near background)
    for gx in range(NX0 + 2, NX1 - 2, 3):
        for gy in range(NY0 + 2, NY1 - 2, 3):
            x, y = gx + rnd.randint(-1, 1), gy + rnd.randint(-1, 1)
            h = Hn.get((x, y))
            if h is None or near.get((x, y, h - 1)) != "grass" or (x, y, h) in tcells:
                continue
            dst = min(math.hypot(x - sx, y - sy) for sx, sy in stage)
            if dst < 8 or any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep):
                continue
            p = 0.42 if (8 < y < 45 and -32 < x < 26) else (0.22 if dst < 60 else 0.0)
            if rnd.random() < p:
                kind = "cherry_lv" if rnd.random() < 0.12 else "oak_lv"
                _blob(tcells, x, y, h, rnd.uniform(1.1, 1.9), rnd.uniform(0.8, 1.3), kind, rnd, rough=0.3)
    for k in list(tcells):                                 # never inside the ground
        if k in near:
            del tcells[k]
    logs = {k: v for k, v in tcells.items() if not v.endswith("_lv")}
    leaves = {k: v for k, v in tcells.items() if v.endswith("_lv")}
    for k in list(leaves):                                 # drop leaves no one can see (fully inside)
        x, y, z = k
        if all((x + dx, y + dy, z + dz) in leaves for (dx, dy, dz), _ in _DIRS):
            del leaves[k]
    W.terrain = voxel_mesh(sc, "terrain", near, KINDS, occluders={**logs, **leaves})
    W.logs = voxel_mesh(sc, "logs", logs, KINDS, occluders={**near, **leaves})
    W.leaves = voxel_mesh(sc, "leaves", leaves, KINDS, occluders={**near, **logs}, keep_leaf_faces=LEAVES)
    # --- far terrain: 3-unit blocks, with forest bumps
    S = 3
    Mf = {k: material("wf_" + k, T[k], tile=S) for k in ("grass_top", "grass_side", "dirt", "stone", "snow",
                                                           "grass_block_snow", "sand", "andesite")}
    Mf["oak_leaves"] = material("wf_leaves", T["oak_leaves"], tile=S, rough=0.7)
    Mf["cherry_leaves"] = material("wf_cherry", T["cherry_leaves"], tile=S, rough=0.7)
    KF = {
        "grass": {"top": Mf["grass_top"], "side": Mf["grass_side"], "bottom": Mf["dirt"]},
        "dirt": {"top": Mf["dirt"], "side": Mf["dirt"], "bottom": Mf["dirt"]},
        "stone": {"top": Mf["stone"], "side": Mf["stone"], "bottom": Mf["stone"]},
        "sand": {"top": Mf["sand"], "side": Mf["sand"], "bottom": Mf["sand"]},
        "snow": {"top": Mf["snow"], "side": Mf["grass_block_snow"], "bottom": Mf["stone"]},
        "snowblock": {"top": Mf["snow"], "side": Mf["snow"], "bottom": Mf["snow"]},
        "andesite": {"top": Mf["andesite"], "side": Mf["andesite"], "bottom": Mf["andesite"]},
        "forest": {"top": Mf["oak_leaves"], "side": Mf["oak_leaves"], "bottom": Mf["oak_leaves"]},
        "pink": {"top": Mf["cherry_leaves"], "side": Mf["cherry_leaves"], "bottom": Mf["cherry_leaves"]},
    }
    R = cfg.get("far_radius", 430)

    def inside_near(wx, wy):
        return NX0 + 1 <= wx < NX1 - 1 and NY0 + 1 <= wy < NY1 - 1

    Hf = _columns(L, -R // S, R // S, (NY0 - 60) // S, (R + 60) // S, S, skip=inside_near)
    far = _terrain_cells(Hf, S, 88, L.lake, scale_far=True)
    for (gx, gy), h in Hf.items():                         # forests on the far hills
        if far.get((gx, gy, h - 1)) == "grass" and h * S < 55:
            n = L.n.fbm(gx * 0.25 + 31, gy * 0.25 + 17)
            if n > 0.47:
                far[(gx, gy, h)] = "pink" if L.n.fbm(gx * 0.1 + 3, gy * 0.1) > 0.72 else "forest"
                if n > 0.6:
                    far[(gx, gy, h + 1)] = far[(gx, gy, h)]
    W.far = voxel_mesh(sc, "far_terrain", far, KF, scale=(S, S, S))
    # --- water
    lx, ly, lr = L.lake
    bpy.ops.mesh.primitive_plane_add(size=lr * 3.2, location=(lx, ly, -0.15))
    W.water = bpy.context.active_object
    W.water.name = "water"
    wm = bpy.data.materials.new("water")
    wm.use_nodes = True
    wb = wm.node_tree.nodes["Principled BSDF"]
    wb.inputs["Base Color"].default_value = (0.02, 0.07, 0.2, 1)
    wb.inputs["Roughness"].default_value = 0.03
    wb.inputs["Specular IOR Level"].default_value = 0.6
    W.water.data.materials.append(wm)
    # --- ground cover
    P = {k: material("p_" + k, T[k], alpha=True, rough=0.7, translucent=0.35) for k in (
        "short_grass", "tall_grass_bottom", "tall_grass_top", "fern", "poppy", "dandelion", "oxeye_daisy",
        "cornflower", "azure_bluet")}
    items = []
    clear = cfg.get("clear_plants", [])                    # [(x, y, r)]: feet, faces
    pr = cfg.get("plant_radius", 48)
    for (gx, gy), h in Hn.items():
        if near.get((gx, gy, h - 1)) != "grass" or (gx, gy, h) in tcells:
            continue
        dst = math.hypot(gx, gy - 6)
        if dst > pr:
            continue
        patch = 0.35 + 0.9 * L.n.fbm(gx * 0.12 + 5, gy * 0.12 + 9)    # thick patches and thinner lawn
        dens = min(1.0, patch) * (1.0 if dst < 26 else max(0.25, 1 - (dst - 26) / 30))
        for _ in range(2):
            if rnd.random() > 0.62 * dens:
                continue
            x, y = gx + rnd.random(), gy + rnd.random()
            if any(math.hypot(x - cx, y - cy) < cr for cx, cy, cr in clear):
                continue
            r_ = rnd.random()
            if r_ < 0.07:
                s = rnd.uniform(0.85, 1.05)
                items += [(x, y, h, s, P["tall_grass_bottom"]), (x, y, h + s * 0.98, s, P["tall_grass_top"])]
            elif r_ < 0.9:
                items.append((x, y, h, rnd.uniform(0.5, 0.8), P["fern"] if r_ < 0.14 else P["short_grass"]))
            elif r_ < 0.97:
                items.append((x, y, h, rnd.uniform(0.55, 0.75), P[rnd.choice(("poppy", "dandelion", "oxeye_daisy",
                                                                               "cornflower", "azure_bluet"))]))
    W.plants = crosses(sc, "plants", items)
    # --- sky, sun, clouds
    az, el = cfg.get("sun", (105, 34))
    W.sun, W.to_sun = sun_object(sc, az, el, energy=cfg.get("sun_energy", 5.4))
    W.world = sky(sc, W.to_sun, fill=cfg.get("fill", 1.1))
    W.sky_dot = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "VECT_MATH" and n_.operation == "DOT_PRODUCT")
    W.sky_pow = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "MATH" and n_.operation == "POWER")
    W.sky_glow = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "MIX")
    W.sky_ramp = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "VALTORGB")
    W.sky_lit = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "BACKGROUND" and not n_.inputs["Color"].is_linked)
    cm_top = flat("cloud", (255, 255, 255), rough=1.0, emission=0.85)
    cm_bot = flat("cloud_under", (226, 232, 244), rough=1.0, emission=0.6)
    cc = cloud_cells(assets, cfg.get("cloud_offset", (40, 90)), cfg.get("cloud_radius", 110))
    W.clouds = voxel_mesh(sc, "clouds", cc, {"c": {"top": cm_top, "side": cm_bot, "bottom": cm_bot}},
                          scale=(6, 6, 2.5), offset=(0, 0, cfg.get("cloud_height", 130)))
    only_camera(W.clouds)
    if cfg.get("particles", True):
        W.particles = add_particles(sc, T, cfg.get("particle_box", (-7, 9, -4, 16, 0.4, 6.5)), rnd)
    return W


def add_particles(sc, T, box, rnd, leaves=170, petals=50, specks=70):
    """What floats in the reference's air: drifting leaves (small green squares,
    two-sided, light through them), cherry petals and warm glowing specks.
    One mesh each; names start with falling_leaf / speck so the depth pass skips them."""
    x0, x1, y0, y1, z0, z1 = box
    out = []

    def flakes(name, n, cols, size):
        verts, faces, col = [], [], []
        for _ in range(n):
            c = (rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(z0, z1))
            s = rnd.uniform(*size)
            a = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
            b = a.orthogonal().normalized()
            e = a.cross(b).normalized()
            i = len(verts)
            for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                verts.append(tuple(Vector(c) + (b * u + e * v) * s / 2))
            faces.append([i, i + 1, i + 2, i + 3])
            col.append(rnd.choice(cols))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        ca = me.color_attributes.new("flake_col", "FLOAT_COLOR", "FACE")
        for k, c_ in enumerate(col):
            ca.data[k].color = (*(((v / 255 + 0.055) / 1.055) ** 2.4 for v in c_), 1)
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        b_ = nt.nodes["Principled BSDF"]
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "flake_col"
        nt.links.new(at.outputs["Color"], b_.inputs["Base Color"])
        b_.inputs["Roughness"].default_value = 0.6
        tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
        nt.links.new(at.outputs["Color"], tr.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.inputs["Fac"].default_value = 0.45
        nt.links.new(b_.outputs["BSDF"], mx.inputs[1])
        nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
        nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
        me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        ob.visible_shadow = False
        out.append(ob)

    flakes("falling_leaf_green", leaves, [(96, 168, 36), (124, 196, 48), (78, 140, 30), (150, 210, 70)], (0.1, 0.18))
    flakes("falling_leaf_petal", petals, [(250, 182, 214), (240, 160, 200), (255, 210, 228)], (0.07, 0.12))
    me = bpy.data.meshes.new("speck")
    verts, faces = [], []
    for _ in range(specks):
        c = Vector((rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(z0, z1)))
        s = rnd.uniform(0.012, 0.026)
        i = len(verts)
        for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            verts.append(tuple(c + Vector((dx, dy, dz)) * s))
        faces += [[i, i + 1, i + 2, i + 3], [i + 4, i + 7, i + 6, i + 5], [i, i + 4, i + 5, i + 1],
                  [i + 1, i + 5, i + 6, i + 2], [i + 2, i + 6, i + 7, i + 3], [i + 3, i + 7, i + 4, i]]
    me.from_pydata(verts, [], faces)
    me.materials.append(flat("speck", (255, 196, 120), emission=6.0))
    ob = bpy.data.objects.new("speck", me)
    sc.collection.objects.link(ob)
    only_camera(ob)
    out.append(ob)
    return out


SKY_DAY = {"glow": (255, 236, 236), "power": 6.0, "horizon": (200, 224, 250)}
SKY_GOLDEN = {"glow": (255, 222, 200), "power": 8.0, "horizon": (214, 222, 248)}     # golden hour: a warm glow by the sun


SKY_DAY.update({"mid": (118, 182, 255), "zenith": (40, 128, 245)})
SKY_GOLDEN.update({"mid": (118, 182, 255), "zenith": (40, 128, 245)})
SKY_STORM = {"glow": (200, 222, 252), "power": 9.0, "horizon": (196, 128, 192),        # Null's storm (the thumbnail)
             "mid": (92, 66, 128), "zenith": (22, 18, 40), "fill": 0.45, "fill_col": (170, 140, 210)}


def set_sky(W, look):
    lin = lambda c: (*(((v / 255 + 0.055) / 1.055) ** 2.4 for v in c), 1)   # noqa: E731
    W.sky_glow.inputs["B"].default_value = lin(look["glow"])
    W.sky_pow.inputs[1].default_value = look["power"]
    el = sorted(W.sky_ramp.color_ramp.elements, key=lambda e: e.position)
    el[0].color = lin(look["horizon"])
    el[1].color = lin(look["mid"])
    el[2].color = lin(look["zenith"])
    W.sky_lit.inputs["Strength"].default_value = look.get("fill", 1.1)
    W.sky_lit.inputs["Color"].default_value = lin(look.get("fill_col", (176, 204, 240)))


def set_sun(W, azimuth, elevation, energy=None, color=None):
    """Move the sun (and its glow in the sky) for a shot."""
    a, e = math.radians(azimuth), math.radians(elevation)
    W.to_sun = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    W.sun.rotation_euler = (-W.to_sun).to_track_quat("-Z", "Y").to_euler()
    W.sky_dot.inputs[1].default_value = tuple(W.to_sun)
    if energy is not None:
        W.sun.data.energy = energy
    if color is not None:
        W.sun.data.color = color


# ------------------------------------------------------------- depth pass
def render_depth(sc, path, far=600.0):
    """A pass with each pixel's distance from the camera / far (1 = sky), for the haze."""
    m = None
    # each material shows its depth instead of its colour, keeping its alpha cutout
    # (so grass blades and leaf holes are as thin in the depth as in the picture)
    swapped = []
    for mat_ in bpy.data.materials:
        if not mat_.use_nodes or mat_ is m:
            continue
        mt = mat_.node_tree
        outs = [n_ for n_ in mt.nodes if n_.type == "OUTPUT_MATERIAL"]
        if not outs:
            continue
        o_ = outs[0]
        lk = o_.inputs["Surface"].links
        src = lk[0].from_socket if lk else None
        em_ = mt.nodes.new("ShaderNodeEmission")
        cd_ = mt.nodes.new("ShaderNodeCameraData")
        dv_ = mt.nodes.new("ShaderNodeMath")
        dv_.operation = "DIVIDE"
        dv_.inputs[1].default_value = far
        mt.links.new(cd_.outputs["View Distance"], dv_.inputs[0])
        mt.links.new(dv_.outputs[0], em_.inputs["Color"])
        tgt = em_.outputs["Emission"]
        cut = None
        if src is not None and src.node.type == "MIX_SHADER" and src.node.inputs[1].links and \
                src.node.inputs[1].links[0].from_node.type == "BSDF_TRANSPARENT":
            cut = src.node
            prev = cut.inputs[2].links[0].from_socket
            mt.links.new(tgt, cut.inputs[2])
            swapped.append((mat_, o_, src, (em_, cd_, dv_), (cut, prev)))
        else:
            mt.links.new(tgt, o_.inputs["Surface"])
            swapped.append((mat_, o_, src, (em_, cd_, dv_), None))
    old = (sc.world, sc.cycles.samples, sc.cycles.use_denoising, sc.view_settings.view_transform,
           sc.view_settings.exposure, sc.view_settings.look, sc.render.image_settings.color_depth,
           sc.render.image_settings.color_mode, sc.cycles.max_bounces, sc.render.filepath, sc.render.filter_size,
           sc.camera.data.dof.use_dof)
    w = bpy.data.worlds.new("depth_sky")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    sc.world = w
    sc.cycles.samples = 8
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 0
    sc.view_settings.view_transform = "Raw"                # linear values: distance / far
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.color_mode = "BW"
    sc.render.image_settings.color_depth = "16"
    sc.render.filter_size = 0.01
    sc.camera.data.dof.use_dof = False                   # the haze follows sharp depth
    hidden = []
    for ob in sc.objects:                                 # particles and motes don't belong in the depth
        if ob.name.startswith(("mote", "speck", "falling_leaf", "null_backglow")):
            hidden.append((ob, ob.hide_render))
            ob.hide_render = True
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for ob, h in hidden:
        ob.hide_render = h
    for mat_, o_, src, nodes, cut in swapped:
        mt = mat_.node_tree
        if cut is not None:
            mt.links.new(cut[1], cut[0].inputs[2])
        elif src is not None:
            mt.links.new(src, o_.inputs["Surface"])
        for n_ in nodes:
            mt.nodes.remove(n_)
    (sc.world, sc.cycles.samples, sc.cycles.use_denoising, sc.view_settings.view_transform,
     sc.view_settings.exposure, look, depth_, mode_, sc.cycles.max_bounces, sc.render.filepath, sc.render.filter_size,
     sc.camera.data.dof.use_dof) = old
    sc.view_settings.look = look
    sc.render.image_settings.color_mode = mode_
    sc.render.image_settings.color_depth = depth_
