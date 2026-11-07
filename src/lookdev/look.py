"""Look test: the BlendSwap Steve in a world built to match the reference frames
(Benly: forest hill filling the frame, deep blue sky with blocky clouds, warm sun
plus a golden rim, bright yellow-green leaves, blurred foreground logs and grass,
warm floating specks, a 3D hair fringe).
Usage: python look.py out_prefix [res_x] [samples] [shots: close,wide]"""
import math
import os
import random
import sys


import bpy
import bmesh
from mathutils import Vector

OUT = sys.argv[1]
RES = int(sys.argv[2]) if len(sys.argv) > 2 else 540
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 32
SHOTS = (sys.argv[4] if len(sys.argv) > 4 else "close,wide").split(",")
HERE_ = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE_, "..", ".."))
A = os.environ.get("TWB_ASSETS", "/home/user/assets")            # MCprep pack (not in the repo)
RIGS = os.path.join(REPO, "assets", "rigs")                       # the Steve rig and its skins
TX = A + "/mcprep/resourcepacks/mcprep_default/assets/minecraft/textures/block/"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.use_scripts_auto_execute = True
sc = bpy.context.scene


def srgb(c):
    return tuple((((v / 255) + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else (v / 255) / 12.92 for v in c)


def img(name):
    return bpy.data.images.load(TX + name + ".png", check_existing=True)


def mat(name, image, tint=None, holes=None, alpha=False, rough=0.85):
    """A block material, pixel-sharp. holes: the colour shown where the texture is
    see-through (leaves look full and dense, as in the reference, and render fast);
    alpha: really see-through (plants)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = image
    t.interpolation = "Closest"
    col = t.outputs["Color"]
    if tint:
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        mul.inputs["B"].default_value = (*tint, 1)
        nt.links.new(col, mul.inputs["A"])
        col = mul.outputs["Result"]
    if holes:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = (*holes, 1)
        nt.links.new(t.outputs["Alpha"], mix.inputs["Factor"])
        nt.links.new(col, mix.inputs["B"])
        col = mix.outputs["Result"]
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.15
    if alpha:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "DITHERED"
    return m


def camera_only(ob):
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission"):
        if hasattr(ob, attr):
            setattr(ob, attr, False)


# ---------------------------------------------------------------- voxel world
DIRS = [((0, 0, 1), "top"), ((0, 0, -1), "bottom"), ((1, 0, 0), "side"), ((-1, 0, 0), "side"),
        ((0, 1, 0), "side"), ((0, -1, 0), "side")]


def voxels(name, cells, kinds, scale=1.0):
    """One mesh for a dict {(x, y, z): kind}: only the faces nothing covers.
    kinds: {kind: {"top": mat, "side": mat, "bottom": mat}}."""
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    slots = {}
    for k in kinds.values():
        for m in k.values():
            if m.name not in slots:
                slots[m.name] = len(slots)
                me.materials.append(m)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vcache = {}

    def v(p):
        if p not in vcache:
            vcache[p] = bm.verts.new(p)
        return vcache[p]

    for (x, y, z), kind in cells.items():
        for (dx, dy, dz), face in DIRS:
            if (x + dx, y + dy, z + dz) in cells:
                continue
            if dz == 1:
                q = [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
            elif dz == -1:
                q = [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y, z), (x, y, z)]
            elif dx == 1:
                q = [(x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x + 1, y, z + 1)]
            elif dx == -1:
                q = [(x, y + 1, z), (x, y, z), (x, y, z + 1), (x, y + 1, z + 1)]
            elif dy == 1:
                q = [(x + 1, y + 1, z), (x, y + 1, z), (x, y + 1, z + 1), (x + 1, y + 1, z + 1)]
            else:
                q = [(x, y, z), (x + 1, y, z), (x + 1, y, z + 1), (x, y, z + 1)]
            try:
                f = bm.faces.new([v(p) for p in q])
            except ValueError:
                continue
            f.material_index = slots[kinds[kind][face].name]
            for loop, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                loop[uv].uv = c
    bm.to_mesh(me)
    bm.free()
    ob.scale = (scale, scale, scale)
    return ob


def crosses(name, items):
    """Plants as crossed quads, all in one mesh: items = [(x, y, z, h, mat)]."""
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    slots = {}
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    rnd = random.Random(11)
    for x, y, z, h, m in items:
        if m.name not in slots:
            slots[m.name] = len(slots)
            me.materials.append(m)
        a0 = rnd.uniform(0, math.pi)
        for a in (a0 + math.pi / 4, a0 - math.pi / 4):
            dx, dy = 0.5 * h * math.cos(a), 0.5 * h * math.sin(a)
            vs = [bm.verts.new(p) for p in ((x - dx, y - dy, z), (x + dx, y + dy, z),
                                            (x + dx, y + dy, z + h), (x - dx, y - dy, z + h))]
            f = bm.faces.new(vs)
            f.material_index = slots[m.name]
            f.smooth = False
            for loop, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                loop[uv].uv = c
    bm.to_mesh(me)
    bm.free()
    return ob


WORLD2 = os.environ.get("WORLD", "2") == "2"          # the rebuilt world (world.py); WORLD=1: the old meadow
if WORLD2:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from world import build_world, render_depth  # noqa: E402
    import json as _jw  # noqa: E402
    WCFG = _jw.loads(os.environ.get("WCFG", "{}"))
    WCFG.setdefault("clear_plants", [(0, 0, 1.2), (1.5, 0.3, 1.4),          # the characters' feet
                                     (0.6, -6.0, 2.2), (-1.0, -3.0, 2.4), (-4.0, 3.0, 2.6), (0.3, -2.05, 1.6)])  # cameras
    WCFG.setdefault("keep_clear", [(0, -14, 8), (0, 14, 7), (-14, 3, 7), (-22, 3, 9), (-34, 4, 10), (-46, 5, 10)])        # the view to the lake
    W = build_world(sc, A, WCFG)
    rnd = random.Random(7)
else:
    GRASS = (0.46, 0.90, 0.16)               # the reference's bright, slightly yellow green
    LEAF = (0.36, 0.84, 0.12)
    grass_top = mat("grass_top", img("grass_block_top"), GRASS)
    grass_side = mat("grass_side", img("grass_block_side"))
    dirt = mat("dirt", img("dirt"))
    log_side = mat("log_side", img("oak_log"))
    log_top = mat("log_top", img("oak_log_top"))
    leaves = mat("leaves", img("oak_leaves"), LEAF, holes=(0.03, 0.12, 0.015))
    leaves2 = mat("leaves2", img("oak_leaves"), (0.26, 0.70, 0.12), holes=(0.03, 0.10, 0.015))
    cherry = mat("cherry", img("cherry_leaves"), None, holes=(0.25, 0.08, 0.14))
    birch_side = mat("birch_side", img("birch_log"))
    birch_top = mat("birch_top", img("birch_log_top"))
    birch_lv = mat("birch_lv", img("birch_leaves"), (0.48, 0.80, 0.20), holes=(0.04, 0.12, 0.02))
    cloud = bpy.data.materials.new("cloud")
    cloud.use_nodes = True
    cb = cloud.node_tree.nodes["Principled BSDF"]
    cb.inputs["Base Color"].default_value = (1, 1, 1, 1)
    cb.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    cb.inputs["Emission Strength"].default_value = 0.9

    KINDS = {
        "grass": {"top": grass_top, "side": grass_side, "bottom": dirt},
        "dirt": {"top": dirt, "side": dirt, "bottom": dirt},
        "log": {"top": log_top, "side": log_side, "bottom": log_top},
        "leaves": {"top": leaves, "side": leaves, "bottom": leaves},
        "leaves2": {"top": leaves2, "side": leaves2, "bottom": leaves2},
        "cherry": {"top": cherry, "side": cherry, "bottom": cherry},
        "birch": {"top": birch_top, "side": birch_side, "bottom": birch_top},
        "birch_lv": {"top": birch_lv, "side": birch_lv, "bottom": birch_lv},
    }

    rnd = random.Random(7)


    def ground_h(x, y):
        """A meadow where the characters stand, then (from y=24) a forest hill rising
        gently, so the camera sees its sunlit treetops (the reference's backdrop)."""
        bump = 0.6 * math.sin(x * 0.3 + 0.5) * math.sin(y * 0.27 + 1.1)
        if y < 24:
            return max(0, int(round(bump + max(0, y - 14) * 0.12))) if abs(x) > 2 or y > 6 else 0
        rise = 1.2 + (y - 24) * 0.30 + 2.0 * math.sin(x * 0.09 + 1.3) * math.sin(y * 0.08 + 0.4) \
            + 1.2 * math.sin(x * 0.21 + y * 0.15)
        return max(0, int(round(rise)))


    cells = {}
    X0, X1, Y0, Y1 = -70, 70, -14, 84
    heights = {}
    for x in range(X0, X1):
        for y in range(Y0, Y1):
            h = ground_h(x, y)
            heights[(x, y)] = h
            for z in range(-2, h):
                cells[(x, y, z)] = "grass" if z == h - 1 else "dirt"


    def oak(x, y, base, h, r, lv="leaves"):
        for z in range(base, base + h):
            cells[(x, y, z)] = "log"
        top = base + h
        for z in range(top - 3, top + 2):
            rr = r if z < top else r - 1
            for dx in range(-rr, rr + 1):
                for dy in range(-rr, rr + 1):
                    if (dx, dy) == (0, 0) and z < top:
                        continue
                    corner = abs(dx) == rr and abs(dy) == rr
                    if corner and (z >= top or rnd.random() < 0.6):
                        continue
                    cells.setdefault((x + dx, y + dy, z), lv)


    def birch(x, y, base, h):
        for z in range(base, base + h):
            cells[(x, y, z)] = "birch"
        oak_top = base + h
        for z in range(oak_top - 2, oak_top + 2):
            rr = 2 if z < oak_top else 1
            for dx in range(-rr, rr + 1):
                for dy in range(-rr, rr + 1):
                    if abs(dx) == rr and abs(dy) == rr and rnd.random() < 0.7:
                        continue
                    cells.setdefault((x + dx, y + dy, z), "birch_lv")


    # trees: a dense forest on the slope, a few nearer ones to frame the shot
    for gx in range(X0 + 2, X1 - 2, 4):
        for gy in range(10, Y1 - 3, 4):
            x, y = gx + rnd.randint(-1, 1), gy + rnd.randint(-1, 1)
            if rnd.random() < (0.10 if y > 24 else 0.8):     # dense on the hill, a few in the meadow
                continue
            if y <= 24 and abs(x) < 7:
                continue
            b = heights[(x, y)]
            p = rnd.random()
            if abs(x) < 8 and p < 0.17:
                p = 0.5                                         # keep the backdrop behind him calm: oaks only
            if p < 0.07:
                oak(x, y, b, rnd.randint(4, 6), 2, "cherry")
            elif p < 0.17:
                birch(x, y, b, rnd.randint(5, 7))
            else:
                oak(x, y, b, rnd.randint(4, 7), rnd.choice((2, 2, 3)), rnd.choice(("leaves", "leaves", "leaves2")))
    for x, y, h, r in [(-7, 5, 6, 3), (8, 6, 5, 2), (-12, 3, 6, 3), (13, 4, 6, 3)]:
        oak(x, y, 0, h, r)
    world = voxels("world", cells, KINDS)

    # clouds: the game's flat blocky clouds, high and far
    cc = {}
    for cx in range(-60, 60):
        for cy in range(0, 60):
            n = math.sin(cx * 0.45) * math.sin(cy * 0.6 + 1) + math.sin(cx * 0.21 + cy * 0.33) * 0.8 + rnd.uniform(-0.35, 0.35)
            if n > 0.3:
                cc[(cx, cy, 0)] = "c"
    clouds = voxels("clouds", cc, {"c": {"top": cloud, "side": cloud, "bottom": cloud}}, scale=6.0)
    clouds.scale = (4.0, 4.0, 1.6)
    clouds.location = (0, 50, 40)
    camera_only(clouds)

    # plants: tall grass and flowers on the near ground
    tall_b = mat("tall_b", img("tall_grass_bottom"), GRASS, alpha=True)
    tall_t = mat("tall_t", img("tall_grass_top"), GRASS, alpha=True)
    short = mat("short", img("short_grass"), GRASS, alpha=True)
    fern = mat("fern", img("fern"), GRASS, alpha=True)
    flowers = [mat(n, img(n), alpha=True) for n in ("poppy", "dandelion", "oxeye_daisy", "cornflower")]
    items = []
    for i in range(900):
        x, y = rnd.uniform(-14, 14), rnd.uniform(-6, 9)
        if abs(x) < 1.2 and -1.0 < y < 1.2:
            continue                                        # keep his feet clear
        if abs(x) < 3.0 + (y + 7) * 0.15 and y < 1.5 and rnd.random() < 0.97:
            continue                                        # and the camera's view of him
        h = heights.get((math.floor(x), math.floor(y)), 0)
        p = rnd.random()
        if p < 0.25 and y > 2.5:
            s = rnd.uniform(0.9, 1.1)
            items += [(x, y, h, s, tall_b), (x, y, h + s * 0.98, s, tall_t)]
        elif p < 0.85:
            items.append((x, y, h, rnd.uniform(0.7, 1.0), rnd.choice((short, short, fern))))
        else:
            items.append((x, y, h, rnd.uniform(0.6, 0.8), rnd.choice(flowers)))
    for i in range(70):
        x, y = rnd.uniform(-3.5, 3.5), rnd.uniform(-5.8, -4.4)
        items.append((x, y, 0, rnd.uniform(0.3, 0.55), rnd.choice((short, short, fern, rnd.choice(flowers)))))
    crosses("plants", items)

    # foreground props: logs lying on their side, ring end to camera (blurred framing, as in the reference)
    logs = {}
    for (x, y, z) in [(-3, 0, 0), (-4, 0, 0), (-3, 0, 1), (2, 1, 0), (3, 1, 0), (3, 0, 0), (-4, 1, 0)]:
        logs[(x, y, z)] = "logy"
    voxels("logs", logs, {"logy": {"top": log_side, "side": log_top, "bottom": log_side}})

    # warm specks drifting in the light (camera only)
    spk = bpy.data.materials.new("speck")
    spk.use_nodes = True
    sb = spk.node_tree.nodes["Principled BSDF"]
    sb.inputs["Base Color"].default_value = (0, 0, 0, 1)
    sb.inputs["Emission Color"].default_value = (1.0, 0.55, 0.15, 1)
    sb.inputs["Emission Strength"].default_value = 5.0
    for i in range(28):
        bpy.ops.mesh.primitive_cube_add(size=rnd.uniform(0.012, 0.022),
                                        location=(rnd.uniform(-3, 3), rnd.uniform(-1.5, 6), rnd.uniform(0.3, 3.5)))
        ob = bpy.context.active_object
        ob.data.materials.append(spk)
        camera_only(ob)

    # ---------------------------------------------------------------- sky and light
    w = bpy.data.worlds.new("sky")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (*srgb((150, 200, 250)), 1)     # pale near the horizon
    el[1].position, el[1].color = 0.45, (*srgb((40, 115, 230)), 1)     # deep blue overhead
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.3                          # light the scene gets from the sky
    fill = nt.nodes.new("ShaderNodeMix")
    fill.data_type = "RGBA"
    fill.inputs["Factor"].default_value = 0.55
    nt.links.new(ramp.outputs["Color"], fill.inputs["A"])
    fill.inputs["B"].default_value = (0.85, 0.88, 0.9, 1)
    nt.links.new(fill.outputs["Result"], bg.inputs["Color"])
    lp = nt.nodes.new("ShaderNodeLightPath")
    seen = nt.nodes.new("ShaderNodeBackground")                        # what the camera sees
    nt.links.new(ramp.outputs["Color"], seen.inputs["Color"])
    seen.inputs["Strength"].default_value = 1.0
    mixw = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mixw.inputs["Fac"])
    nt.links.new(bg.outputs["Background"], mixw.inputs[1])
    nt.links.new(seen.outputs["Background"], mixw.inputs[2])
    nt.links.new(mixw.outputs["Shader"], nt.nodes["World Output"].inputs["Surface"])


    def sun_light(name, toward, energy, color, angle=2.0):
        s = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        sc.collection.objects.link(s)
        s.data.energy = energy
        s.data.color = color
        s.data.angle = math.radians(angle)
        s.rotation_euler = Vector(toward).normalized().to_track_quat("-Z", "Y").to_euler()
        return s


    sun_light("key", (-0.5, 0.7, -0.5), 5.5, (1.0, 0.9, 0.8))           # warm sun from the front, screen right, high
    sun_light("rim", (0.85, -0.45, -0.3), 3.0, (1.0, 0.78, 0.5), angle=4)   # golden edge from behind left (the world)

# ---------------------------------------------------------------- Steve (BlendSwap rig, CC-BY)
with bpy.data.libraries.load(RIGS + "/steve_blendswap.blend", link=False) as (src, dst):
    dst.collections = ["Rig"]
rig = dst.collections[0]
sc.collection.children.link(rig)
skin = bpy.data.images.load(RIGS + "/steve_skin_v2.png", check_existing=True)
for m in bpy.data.materials:
    if m.name.startswith("Skin") and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and n.image.name.startswith("Steve"):
                n.image = skin
for c in bpy.data.collections:
    if c.name.startswith("Head_Layers"):
        c.hide_render = True
for idb in list(bpy.data.objects) + list(bpy.data.armatures) + list(bpy.data.shape_keys):
    ad = getattr(idb, "animation_data", None)
    if ad:
        for d in ad.drivers:
            d.is_valid = True
            d.driver.is_valid = True

# 3D hair modelled on the reference's Steve (see hair.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hair import build_hair  # noqa: E402
from mathutils import Matrix  # noqa: E402
arm = bpy.data.objects["Thomas_rig"]
HAIR = os.environ.get("HAIR", "1") == "1"
if HAIR:
    build_hair(arm, lattice=bpy.data.objects["Head"])
# the new face: our own eyes, mouth, brows and painted skin replace the rig's (see faceplate.py)
import json as _json  # noqa: E402
from faceplate import build_faceplate, set_face, flatten_face  # noqa: E402
from brows import build_brows, set_brows  # noqa: E402
from skin_face import make_face_skin  # noqa: E402
_head = bpy.data.objects["Head_NoDeform"]
for _i, _m in enumerate(_head.data.materials):
    if _m and _m.name in ("Eyes.001", "Mouth"):
        _head.data.materials[_i] = _head.data.materials[0]
for _n in ("Eyes", "Eyebrows", "Eyebrows.001", "Top_teeth", "Bottom_teeth", "Tongue"):
    bpy.data.objects[_n].hide_render = True
flatten_face(_head, arm)
_lat = bpy.data.objects["Head"]
FACE = build_faceplate(arm, bpy.data.images.load(make_face_skin(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_faceskin.png"))), lattice=_lat)
BROWS = build_brows(arm, lattice=_lat)
_expr = _json.loads(os.environ.get("EXPR", "{}"))
if os.environ.get("NULL"):                           # Null: {"x", "y", "yaw", "height"}
    from null import build_null  # noqa: E402
    _nl = _json.loads(os.environ["NULL"])
    _lcol = bpy.data.collections.new("null")
    sc.collection.children.link(_lcol)
    NULL = build_null(_lcol, A, height=_nl.get("height", 11.0))
    NULL.root.location = (_nl.get("x", 0.0), _nl.get("y", 13.0), _nl.get("z", 0.0))     # he floats
    NULL.root.rotation_euler = (0, 0, math.radians(_nl.get("yaw", 0)))
    _hz = _nl.get("height", 11.0) / 10.0
    for _n, _loc, _c, _p in (("null_rim_pink", (-8, 6, 9), (1.0, 0.35, 0.85), 9000),
                             ("null_rim_cyan", (8, 6, 8), (0.45, 0.85, 1.0), 8000)):
        _L = bpy.data.lights.new(_n, "AREA")
        _L.energy, _L.color, _L.size = _p * _hz * _hz, _c, 5
        _o = bpy.data.objects.new(_n, _L)
        sc.collection.objects.link(_o)
        _rz = Matrix.Rotation(math.radians(_nl.get("yaw", 0)), 3, "Z")
        _o.location = Vector(NULL.root.location) + _rz @ (Vector(_loc) * _hz)
        _o.rotation_euler = (Vector(NULL.root.location) + Vector((0, 0, 5.5 * _hz)) - _o.location).to_track_quat("-Z", "Y").to_euler()
    # the cold glow behind him (the thumbnail's backlight), seen by the camera only
    _gm = bpy.data.materials.new("null_backglow")
    _gm.use_nodes = True
    _gt = _gm.node_tree
    for _n_ in list(_gt.nodes):
        _gt.nodes.remove(_n_)
    _go = _gt.nodes.new("ShaderNodeOutputMaterial")
    _gg = _gt.nodes.new("ShaderNodeTexGradient")
    _gg.gradient_type = "SPHERICAL"
    _gtc = _gt.nodes.new("ShaderNodeTexCoord")
    _gsc = _gt.nodes.new("ShaderNodeVectorMath")             # fade to nothing before the plane's edge
    _gsc.operation = "SCALE"
    _gsc.inputs["Scale"].default_value = 2.0
    _gt.links.new(_gtc.outputs["Object"], _gsc.inputs[0])
    _gt.links.new(_gsc.outputs[0], _gg.inputs["Vector"])
    _gp = _gt.nodes.new("ShaderNodeMath")
    _gp.operation = "POWER"
    _gp.inputs[1].default_value = 1.8
    _gt.links.new(_gg.outputs["Fac"], _gp.inputs[0])
    _gs = _gt.nodes.new("ShaderNodeMath")
    _gs.operation = "MULTIPLY"
    _gs.inputs[1].default_value = float(os.environ.get("NULL_GLOW", "3.0"))
    _gt.links.new(_gp.outputs[0], _gs.inputs[0])
    _ge = _gt.nodes.new("ShaderNodeEmission")
    _ge.inputs["Color"].default_value = (0.62, 0.74, 0.98, 1)
    _gt.links.new(_gs.outputs[0], _ge.inputs["Strength"])
    _gtr = _gt.nodes.new("ShaderNodeBsdfTransparent")
    _gad = _gt.nodes.new("ShaderNodeAddShader")
    _gt.links.new(_gtr.outputs["BSDF"], _gad.inputs[0])
    _gt.links.new(_ge.outputs["Emission"], _gad.inputs[1])
    _gt.links.new(_gad.outputs["Shader"], _go.inputs["Surface"])
    bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.radians(90), 0, 0))
    _gl = bpy.context.active_object
    _gl.name = "null_backglow"
    _rz = Matrix.Rotation(math.radians(_nl.get("yaw", 0)), 3, "Z")
    _gl.location = Vector(NULL.root.location) + _rz @ (Vector((0.4, 5.0, 6.4)) * _hz)
    _gl.rotation_euler = (math.radians(90), 0, math.radians(_nl.get("yaw", 0)))
    _gl.scale = (24 * _hz, 24 * _hz, 1)
    _gl.data.materials.append(_gm)
    for _a in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_shadow"):
        setattr(_gl, _a, False)
if os.environ.get("NOOB"):                           # the Noob beside him: {"x", "y", "yaw", "head", "pose", "face"}
    from noob import build_noob, pose_noob  # noqa: E402
    from faceplate import NOOB_EYES as _NE  # noqa: E402
    _nb = _json.loads(os.environ["NOOB"])
    _ncol = bpy.data.collections.new("noob")
    sc.collection.children.link(_ncol)
    NOOB = build_noob(_ncol, head=_nb.get("head", "classic"), height=_nb.get("height", 2.0), finish=_nb.get("finish", "pixel"))
    NOOB.root.location = (_nb.get("x", 1.6), _nb.get("y", 0.3), 0)
    pose_noob(NOOB, {**_nb.get("pose", {}), "root_yaw": _nb.get("pose", {}).get("root_yaw", 0) + _nb.get("yaw", 0)})
    set_face(NOOB.face, _nb.get("face", {}))
if os.environ.get("PROPS"):                          # held props, e.g. [{"item": "iron_pickaxe", "side": "sl"}]
    from props import sprite_item, block_item, hold  # noqa: E402
    for _pr in _json.loads(os.environ["PROPS"]):
        if "item" in _pr:
            _ob = sprite_item(_pr["item"], A + "/mcprep/resourcepacks/mcprep_default/assets/minecraft/textures/item",
                              px=_pr.get("px", 0.072))
            hold(arm, _ob, _pr.get("side", "sl"), up=_pr.get("up", 25), face=_pr.get("face", 50), reach=_pr.get("reach", 0))
        else:
            _m = mat("held_" + _pr["block"], img(_pr["block"]))
            hold(arm, block_item({"default": _m}, size=_pr.get("size", 0.32)), _pr.get("side", "sr"), kind="block")
if os.environ.get("POSE"):                           # a body pose (see pose.py), by name or as JSON
    from pose import pose as _pose  # noqa: E402
    _p = os.environ["POSE"]
    _lib = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "poses_lib.json")))
    _pose(arm, _lib[_p] if _p in _lib else _json.loads(_p))
set_face(FACE, _expr.get("face", {}))
set_brows(BROWS, _expr.get("brows", {}))

# a relaxed stance: arms hanging, a slight bend at the elbows, head turned just a touch
from mathutils import Quaternion  # noqa: E402
POSE = {"R.arm": Quaternion((0, 1, 0), math.radians(-4)), "L.arm": Quaternion((0, 1, 0), math.radians(4)),
        "R.arm_elbow": Quaternion((1, 0, 0), math.radians(-12)), "L.arm_elbow": Quaternion((1, 0, 0), math.radians(-12)),
        "Head": Quaternion((0, 1, 0), math.radians(-4)) @ Quaternion((1, 0, 0), math.radians(3))}
for bn, q in ({} if os.environ.get("POSE") else POSE).items():   # (a POSE given replaces this)
    arm.pose.bones[bn].rotation_mode = "QUATERNION"
    arm.pose.bones[bn].rotation_quaternion = q

# the reference's face: eyes and brows sit lower on the head, brows thicker
EYES_DY = float(os.environ.get("EYES_DY", "-0.1"))
arm.pose.bones["Eyes_UP_DOWN"].location = (0, EYES_DY, 0)
if os.environ.get("BROW_THICK", "1"):
    for key in bpy.data.shape_keys:
        kb = key.key_blocks.get("EyebrowThikness")
        if kb is None:
            continue
        if key.animation_data:
            for d in list(key.animation_data.drivers):
                if "EyebrowThikness" in d.data_path:
                    key.animation_data.drivers.remove(d)
        kb.value = float(os.environ.get("BROW_THICK", "1"))

# place: one container, scaled so he stands 2 blocks tall
bpy.context.view_layer.update()
H_FILE = 3.215 + 0.0
k = 2.0 / H_FILE
sc.collection.children.unlink(rig)
steve = bpy.data.objects.new("steve", None)
steve.instance_type = "COLLECTION"
steve.instance_collection = rig
sc.collection.objects.link(steve)
steve.scale = (k, k, k)
steve.rotation_euler = (0, 0, math.radians(-4))
if os.environ.get("NO_STEVE") == "1":                # a shot without him (e.g. the Noob alone)
    steve.hide_render = True

# character light, as the reference lights its close-ups: edge lights from behind, narrow
# spots aimed at his head and shoulders (so the world around stays as the sun lights it)
def char_light(name, loc, power, color, aim=(0, 0, 1.55), cone=26, size=0.25):
    L = bpy.data.lights.new(name, "SPOT")
    L.energy, L.color = power, color
    L.spot_size = math.radians(cone)
    L.spot_blend = 0.35
    L.shadow_soft_size = size
    ob = bpy.data.objects.new(name, L)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


if os.environ.get("CHAR_LIGHT", "1") == "1":
    char_light("edge_cool", (-1.6, 2.6, 2.3), float(os.environ.get("EDGE_W", "900")), (0.72, 0.92, 1.0))
    char_light("edge_warm", (1.2, 2.4, 3.4), float(os.environ.get("EDGE_W2", "700")), (1.0, 0.8, 0.55), aim=(0, 0, 1.8))
    if WORLD2:                                         # a warm key from the camera side, on the faces
        char_light("char_key", (1.8, -3.2, 2.9), float(os.environ.get("KEY_W", "650")), (1.0, 0.88, 0.76),
                   aim=(0.6, 0.3, 1.7), cone=34, size=0.9)
    if os.environ.get("NOOB"):                         # the same edge light on the Noob
        _nx, _ny = NOOB.root.location.x, NOOB.root.location.y
        char_light("noob_edge_cool", (_nx - 1.6, _ny + 2.6, 2.3), 700, (0.72, 0.92, 1.0), aim=(_nx, _ny, 1.4))
        char_light("noob_edge_warm", (_nx + 1.2, _ny + 2.4, 3.4), 550, (1.0, 0.8, 0.55), aim=(_nx, _ny, 1.7))
    for m in bpy.data.materials:                     # skin: a little soft warmth where light enters
        if (m.name.startswith("Skin") or m.name.startswith("steve_face")) and m.node_tree:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b and "Subsurface Weight" in b.inputs:
                b.inputs["Subsurface Weight"].default_value = 0.12
                b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
                b.inputs["Subsurface Scale"].default_value = 0.03

# ---------------------------------------------------------------- camera, render, grade
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.dof.use_dof = True
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = RES
sc.render.resolution_y = RES * 16 // 9               # a Short: vertical
VT = os.environ.get("VIEW", "standard")
if VT == "standard":
    sc.view_settings.view_transform = "Standard"
elif VT == "filmic":
    sc.view_settings.view_transform = "Filmic"
    for look in ("Filmic - High Contrast", "High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
else:
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Punchy", "Punchy"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
sc.view_settings.exposure = float(os.environ.get("EXPOSURE", "-0.1" if WORLD2 else "-0.25"))

SHOT = {
    "close": dict(loc=(0.45, -2.05, 1.38), at=(0.05, 0.0, 1.62), lens=42, focus=None, fstop=0.9),
    "two": dict(loc=(0.55, -6.4, 1.35), at=(0.65, 0.1, 1.35), lens=34, focus=None, fstop=2.4),
    "medium": dict(loc=(0.55, -3.1, 1.55), at=(-0.15, 0.0, 1.62), lens=40, focus=None, fstop=1.4),
    "full": dict(loc=(-0.3, -4.3, 0.8), at=(0.0, 0.0, 1.25), lens=32, focus=None, fstop=2.4),
    "wide": dict(loc=(0.4, -7.0, 1.1), at=(0.0, 0.0, 1.5), lens=28, focus=None, fstop=2.0),
}
HEAD = Vector((0, 0, 2.8 * k))                      # head centre, world
def around(az, el, dist=2.9, lens=60):
    """A camera orbiting the head: az 0 = in front of him, 90 = his left."""
    a, e = math.radians(az), math.radians(el)
    loc = HEAD + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    return dict(loc=tuple(loc), at=tuple(HEAD), lens=lens, focus=None, fstop=4.0)
SHOT.update({"h_front": around(0, 2), "h_q": around(-35, 18), "h_side": around(-70, 8),
             "h_backq": around(-150, 10), "h_top": around(160, 50)})
if os.environ.get("NOOB"):                           # a close-up of the Noob, wherever he stands
    _nx, _ny = NOOB.root.location.x, NOOB.root.location.y
    SHOT["noob_close"] = dict(loc=(_nx - 0.55, _ny - 2.0, 1.62), at=(_nx, _ny, 1.72), lens=42, focus=None, fstop=0.9)
SHOT.update({
    "meadow": dict(loc=(0.25, -3.1, 0.65), at=(0.75, 4.0, 2.6), lens=28, focus=3.2, fstop=2.2,        # Benly 2.0
                   sun=(140, 17, 6.4, (1.0, 0.76, 0.5)), glow_dir=(22, 14), golden=True, sun_xy=(0.92, 0.08), haze=(240, 25),
                   noob_at=(1.75, 1.5, -28)),
    "close": dict(loc=(2.05, 0.4, 1.42), at="steve_head", lens=42, focus=2.05, fstop=0.9,               # movie 46.5
                  steve_yaw=90, noob_at=(-3.0, 5.0, 60), sun=(60, 30, 5.6, (1.0, 0.86, 0.7)), haze=(380, 40)),
    "hill": dict(loc=(-1.0, -3.0, 1.0), at=(-6.0, 40.0, 11.0), lens=24, focus=4.5, fstop=4.0,          # Benly 7.0
                 sun=(140, 16, 6.6, (1.0, 0.74, 0.48)), glow_dir=(22, 13), golden=True, sun_xy=(0.95, 0.1), haze=(240, 25),
                 steve_at=(-2.0, 2.4, 0), steve_yaw=172, noob_at=(1.4, 7.5, 175)),
    "storm": dict(loc=(5.2, 0.15, 1.35), at=(-6.0, 0.1, 8.6), lens=17, focus=5.2, fstop=4.0,           # the thumbnail
                  sun=(180, 30, 1.6, (0.85, 0.75, 1.0)), sky="storm", haze=(120, 12), storm=True, glow_dir=(-90, 14),
                  hide=("clouds", "falling_leaf_green", "falling_leaf_petal"),
                  steve_at=(0.0, -0.95, 0), steve_yaw=82, noob_at=(0.4, 1.0, 98)),
    "vista": dict(loc=(-3.0, 3.0, 3.0), at=(-300.0, 0.0, 44.0), lens=26, focus=5.5, fstop=6.0,         # movie 10.0
                  sun=(163, 34, 5.6, (1.0, 0.92, 0.82)), haze=(380, 50),
                  steve_at=(-7.3, 2.25, 0), steve_yaw=-90, noob_at=(-9.2, 3.9, -96)),
})
from world import set_sun as _set_sun, set_sky as _set_sky, SKY_DAY, SKY_GOLDEN, SKY_STORM  # noqa: E402
for name in SHOTS:
    s = SHOT[name]
    if WORLD2:
        _set_sun(W, *(s.get("sun") or WCFG.get("sun", (105, 34)))[:2],
                 *(list(s["sun"][2:]) if s.get("sun") else [5.4, (1.0, 0.87, 0.7)]))
        _set_sky(W, SKY_STORM if s.get("sky") == "storm" else SKY_GOLDEN if s.get("golden") else SKY_DAY)
        if s.get("glow_dir"):                          # the sky's glow placed for the frame, apart from the light
            ga, ge = (math.radians(v) for v in s["glow_dir"])
            W.sky_dot.inputs[1].default_value = (math.sin(ga) * math.cos(ge), math.cos(ga) * math.cos(ge), math.sin(ge))
    for _hn in ("clouds", "speck", "falling_leaf_green", "falling_leaf_petal"):   # things a shot can leave out
        _ho = bpy.data.objects.get(_hn)
        if _ho is not None:
            _ho.hide_render = _hn in s.get("hide", ())
    # staging for this shot: where the characters stand and face
    steve.rotation_euler = (0, 0, math.radians(s.get("steve_yaw", -4)))
    steve.location = s.get("steve_at", (0, 0, 0))
    for ln_ in ("edge_cool", "edge_warm"):             # Steve's edge lights travel with him
        lo_ = bpy.data.objects.get(ln_)
        if lo_ is not None:
            if "home" not in lo_:
                lo_["home"] = tuple(lo_.location)
            lo_.location = Vector(lo_["home"]) + Vector(steve.location)
    if os.environ.get("NOOB") and s.get("noob_at"):
        NOOB.root.location = s["noob_at"][:2] + (0,)
        NOOB.root.rotation_euler = (0, 0, math.radians(s["noob_at"][2]))
    cam.location = s["loc"]
    at = s["at"]
    if at == "steve_head":                             # aim at where his head really is in this pose
        bpy.context.view_layer.update()
        hb = arm.pose.bones["Head"]
        at = tuple(steve.matrix_world @ arm.matrix_world @ ((hb.head + hb.tail) / 2)) 
        at = (at[0], at[1], at[2] - 0.05)
    d = Vector(at) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    key = bpy.data.objects.get("char_key")
    if key is not None:                                # the key light follows the camera: up and to its right
        subj = Vector(s.get("key_at", tuple(Vector(steve.location) + Vector((0, 0, 1.7)))))
        right = d.normalized().cross(Vector((0, 0, 1))).normalized()
        key.location = Vector(s["loc"]) + right * 1.6 + Vector((0, 0, 1.4))
        key.rotation_euler = (subj - key.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = s["lens"]
    cam.data.dof.focus_distance = s["focus"] or d.length
    cam.data.dof.aperture_fstop = s["fstop"]
    sc.render.filepath = f"{OUT}_{name}_raw.png"
    bpy.ops.render.render(write_still=True)
    print("SAVED", sc.render.filepath)
    if WORLD2 and os.environ.get("HAZE", "1") == "1":
        render_depth(sc, f"{OUT}_{name}_depth.png")
        shot_look = {}                                   # this shot's haze and grade, for grade.py
        if s.get("haze"):
            shot_look.update({"L": s["haze"][0], "start": s["haze"][1]})
        if s.get("golden"):
            shot_look.update({"tint": [1.1, 1.0, 0.86], "haze_warm": True})
        if s.get("storm"):
            shot_look.update({"tint": [1.02, 0.9, 1.08], "haze_storm": True})
        if s.get("sun_xy"):
            shot_look["sun"] = s["sun_xy"]
        open(f"{OUT}_{name}_haze.json", "w").write(_jw.dumps(shot_look))
