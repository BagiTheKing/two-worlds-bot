"""Null, rebuilt after the series thumbnail (Ep 0/6/8): an enormous wraith whose
head is the classic Roblox head covered in the magenta/black "missing texture"
checkerboard, glowing; whose body is made of near-black pixels coming apart:
broad hunched shoulders, long arms ending in claw hands with long dripping
fingers, no legs: the lower body dissolves into a trail of voxel debris. Glitch
pixels (magenta, cyan, green) and horizontal scanline streaks run over him, and
a ring of Minecraft and Roblox blocks orbits him with motion trails.

    from null import build_null
    N = build_null(collection, assets, height=10.0)
    N.root      empty at his base (move, turn, scale him)
    N.head, N.torso, N.arms["sl"/"sr"] (shoulder pivots), N.forearms[...] (elbow pivots)
    N.orbit     empty the orbiting blocks hang from (rotate it about z to orbit)

Built from signed-distance shapes sampled on a voxel grid (in units where he is
10 tall), so the silhouette and the dissolve follow the thumbnail's painting.
"""
import math
import os
import random

import bpy
import numpy as np
from mathutils import Matrix, Vector

V = 0.16                                   # one body pixel


def _lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c)


# ------------------------------------------------------------- shape (SDF)
def _seg(p, a, b, ra, rb):
    """Distance to a capsule from a (radius ra) to b (radius rb). p: (..., 3)."""
    a, b = np.array(a, np.float32), np.array(b, np.float32)
    ba = b - a
    t = np.clip(((p - a) @ ba) / (ba @ ba), 0, 1)[..., None]
    q = p - (a + t * ba)
    return np.linalg.norm(q, axis=-1) - (ra + (rb - ra) * t[..., 0])


def _ellip(p, c, r):
    q = (p - np.array(c, np.float32)) / np.array(r, np.float32)
    k = np.linalg.norm(q, axis=-1)
    return (k - 1) * min(r)


def _smin(a, b, k=0.5):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _noise3(p, scale, seed):
    """Smooth value noise 0..1 on a lattice (vectorised)."""
    rng = np.random.default_rng(seed)
    T = rng.random((32, 32, 32)).astype(np.float32)
    q = p * scale
    i = np.floor(q).astype(int)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * \
                    (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * T[(i[..., 0] + dx) % 32, (i[..., 1] + dy) % 32, (i[..., 2] + dz) % 32]
    return out


# body parts, in the 10-tall frame (x right on screen, y away from the camera, z up); he faces -y
SHOULDER = {"sl": (-2.35, 0.1, 7.3), "sr": (2.35, 0.1, 7.3)}
ELBOW = {"sl": (-4.0, -0.4, 5.25), "sr": (4.0, -0.4, 5.25)}
WRIST = {"sl": (-4.55, -0.9, 3.05), "sr": (4.55, -0.9, 3.05)}


def _torso(p):
    d = _ellip(p, (0, 0.15, 6.1), (2.15, 1.2, 2.15))                     # chest: tall
    d = _smin(d, _seg(p, (-2.15, 0.15, 7.25), (2.15, 0.15, 7.25), 1.0, 1.0), 0.6)   # shoulders: broad, hunched
    d = _smin(d, _ellip(p, (0, 0.2, 4.0), (1.6, 1.0, 1.8)), 0.8)        # belly, narrowing to the waist
    d = _smin(d, _seg(p, (0, 0.25, 3.0), (0.15, 0.4, 0.2), 1.55, 0.15), 1.0)    # the trailing tail
    d = _smin(d, _seg(p, (0, 0.0, 7.6), (0, -0.2, 8.7), 0.72, 0.5), 0.4)       # a short neck, bowed forward
    return d


def _upper(p, s):
    return _seg(p, SHOULDER[s], ELBOW[s], 0.88, 0.66)


def _fore(p, s):
    return _seg(p, ELBOW[s], WRIST[s], 0.66, 0.52)


def _fingers(s):
    """Five hooked claws hanging from the hand: each a long finger down, then a
    tip curling in toward the body (the thumbnail's dripping claws)."""
    wx, wy, wz = WRIST[s]
    out_x = 1 if s == "sr" else -1                       # away from the body
    segs = []
    for k, (dx, length) in enumerate(((-0.95, 2.1), (-0.42, 2.6), (0.1, 2.75), (0.62, 2.45), (1.1, 1.7))):
        x0 = wx + out_x * dx
        a = (wx + out_x * dx * 0.45, wy - 0.2, wz - 0.5)                  # the knuckle, on the palm
        b = (x0 + out_x * dx * 0.65, wy - 0.4 - 0.05 * k, wz - 0.5 - length)  # fanning out as it hangs
        c = (b[0] - out_x * 0.5, b[1] - 0.3, b[2] - 0.5)                 # the hook, curling inward
        segs.append((a, b, c))
    return segs


def _hand(p, s):
    wx, wy, wz = WRIST[s]
    d = _ellip(p, (wx, wy - 0.15, wz - 0.35), (0.85, 0.55, 0.7))
    for a, b, c in _fingers(s):
        d = _smin(d, _seg(p, a, b, 0.22, 0.15), 0.12)
        d = np.minimum(d, _seg(p, b, c, 0.15, 0.06))
    return d


# ------------------------------------------------------------- materials
def _mat_body():
    m = bpy.data.materials.new("null_body")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = "vox_col"
    nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
    e = nt.nodes.new("ShaderNodeAttribute")
    e.attribute_name = "vox_glow"
    nt.links.new(e.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 4.0
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Specular IOR Level"].default_value = 0.25
    return m


def _mat_head():
    """The missing-texture checker, glowing magenta, projected from the front."""
    m = bpy.data.materials.new("null_head")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    com = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], com.inputs["X"])
    nt.links.new(sep.outputs["Z"], com.inputs["Y"])
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 1.0
    sc_ = nt.nodes.new("ShaderNodeVectorMath")
    sc_.operation = "SCALE"
    sc_.inputs["Scale"].default_value = 2.1                # about seven squares across the face
    nt.links.new(com.outputs["Vector"], sc_.inputs[0])
    nt.links.new(sc_.outputs[0], ck.inputs["Vector"])
    ck.inputs["Color1"].default_value = (*_lin((236, 20, 236)), 1)
    ck.inputs["Color2"].default_value = (*_lin((14, 6, 16)), 1)
    nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(ck.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 2.4
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Specular IOR Level"].default_value = 0.15
    return m


def _mat_trail():
    m = bpy.data.materials.new("null_trail")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*_lin((214, 176, 255)), 1)
    em.inputs["Strength"].default_value = 1.2
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.22
    nt.links.new(tr.outputs["BSDF"], mx.inputs[1])
    nt.links.new(em.outputs["Emission"], mx.inputs[2])
    nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    return m


# ------------------------------------------------------------- voxel meshes
_CUBE = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _cubes(name, items, mat, col):
    """items: [(centre, half_size, colour, glow, rotation_z)]; one mesh, colours per face."""
    verts, faces, cols, glows = [], [], [], []
    for c, h, rgb, glow, rz in items:
        cz, sz = math.cos(rz), math.sin(rz)
        i = len(verts)
        for dx, dy, dz in _CUBE:
            x, y = dx * h, dy * h
            verts.append((c[0] + x * cz - y * sz, c[1] + x * sz + y * cz, c[2] + dz * h))
        for f in _FACES:
            faces.append([i + k for k in f])
            cols.append(rgb)
            glows.append(glow)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    ca = me.color_attributes.new("vox_col", "FLOAT_COLOR", "FACE")
    ga = me.color_attributes.new("vox_glow", "FLOAT_COLOR", "FACE")
    for k, (c_, g_) in enumerate(zip(cols, glows)):
        ca.data[k].color = (*c_, 1)
        ga.data[k].color = (*g_, 1)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def _voxelize(sdf, lo, hi, rnd, seed, dissolve, rel=(0, 0, 0)):
    """Sample a shape on the grid: the solid shell, the voxels coming loose at its
    edge (pushed outward, shrinking), as (centre, half, colour, glow, rot) items,
    relative to `rel` (the part's pivot)."""
    xs = np.arange(lo[0], hi[0], V)
    ys = np.arange(lo[1], hi[1], V)
    zs = np.arange(lo[2], hi[2], V)
    P = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1).reshape(-1, 3).astype(np.float32)
    d = sdf(P)
    n = _noise3(P, 1.3, seed)
    n2 = _noise3(P, 4.0, seed + 1)
    items = []
    inner = (d < -V) & (d > -3.2 * V)                       # the body's skin: solid where it isn't dissolving
    outer = (d >= -V) & (d < 0)                             # its outermost pixels: ragged
    loose_zone = (d >= 0) & (d < 0.9)                       # where loose pixels can hang
    rel = np.array(rel, np.float32)
    dark = [_lin(c) for c in ((8, 6, 11), (13, 9, 17), (5, 4, 7), (20, 13, 27), (10, 8, 14))]
    for k in np.nonzero(inner | outer | loose_zone)[0]:
        p = P[k]
        z = p[2]
        dz = dissolve(z)
        solid = (inner[k] and n[k] > dz * 1.15 - 0.08 + 0.2 * (n2[k] - 0.5)) or \
                (outer[k] and n2[k] > 0.3 + 0.8 * dz)
        if solid:
            c = p - rel
            half = V * 0.5 * rnd.uniform(0.92, 1.04)
        elif rnd.random() < (0.02 if loose_zone[k] else 0.12) + 0.45 * dz:   # a piece coming off: outward, smaller
            out_dir = p - np.array((0, 0.2, min(max(z, 1.0), 8.0)), np.float32)
            out_dir = out_dir / (np.linalg.norm(out_dir) + 1e-6)
            dist = rnd.uniform(0.05, 0.6) * (1 + 2.2 * dz)
            c = p + out_dir * dist + np.array((0, 0, -rnd.uniform(0, 0.8) * dz), np.float32) - rel
            half = V * 0.5 * rnd.uniform(0.35, 0.9)
        else:
            continue
        r_ = rnd.random()
        if r_ < 0.008:
            glow = _lin(rnd.choice(((255, 40, 255), (40, 255, 255), (80, 255, 120))))
            rgb = glow
        else:
            rgb = rnd.choice(dark)
            glow = (0, 0, 0)
        items.append((tuple(c), half, rgb, glow, rnd.uniform(-0.15, 0.15)))
    return items


# ----------------------------------------------------------------- build
class Null:
    pass


def _classic_head_mesh(name, W=3.1, H=3.85, segs=48, rings=40, rc=1.15):
    import bmesh
    bm = bmesh.new()
    R = W / 2
    rows = []
    for j in range(rings + 1):
        zl = H * j / rings
        if zl < rc:
            r = R - rc + math.sqrt(max(0.0, rc * rc - (rc - zl) ** 2))
        elif zl > H - rc:
            r = R - rc + math.sqrt(max(0.0, rc * rc - (zl - (H - rc)) ** 2))
        else:
            r = R
        taper = 0.86 + 0.14 * min(1.0, zl / (0.55 * H))           # narrower at the jaw, broad dome above
        rows.append([bm.verts.new((taper * r * math.cos(2 * math.pi * i / segs), 0.82 * taper * r * math.sin(2 * math.pi * i / segs), zl))
                     for i in range(segs)])
    for j in range(rings):
        for i in range(segs):
            bm.faces.new((rows[j][i], rows[j][(i + 1) % segs], rows[j + 1][(i + 1) % segs], rows[j + 1][i]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    return me


def _empty(name, loc, parent, col):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    return e


def build_null(col, assets, height=10.0, seed=6, name="null", orbit=True):
    rnd = random.Random(seed)
    N = Null()
    k = height / 10.0
    N.root = _empty(name + "_root", (0, 0, 0), None, col)
    N.root.scale = (k, k, k)
    body_mat = _mat_body()

    def dissolve(z):                                        # 0 solid .. 1 all debris
        return min(1.0, max(0.0, (2.3 - z) / 2.3)) ** 1.6 * 0.95 + 0.06

    # torso (with the trailing tail)
    N.torso = _empty(name + "_torso", (0, 0, 0), N.root, col)
    items_torso = _voxelize(_torso, (-3.6, -1.6, 0.0), (3.6, 1.8, 8.9), rnd, seed, dissolve)
    _cubes(name + "_torso_vox", items_torso, body_mat, col).parent = N.torso
    # arms: upper arm (pivot at the shoulder), forearm and claw hand (pivot at the elbow)
    N.arms, N.forearms = {}, {}
    for s in ("sl", "sr"):
        sh = _empty(f"{name}_shoulder_{s}", SHOULDER[s], N.torso, col)
        items = _voxelize(lambda p, s=s: _upper(p, s), (-5.8, -1.6, 4.0), (5.8, 1.5, 8.4), rnd, seed + 2,
                          lambda z: 0.04, rel=SHOULDER[s])
        _cubes(f"{name}_upper_{s}", items, body_mat, col).parent = sh
        el = _empty(f"{name}_elbow_{s}", tuple(np.subtract(ELBOW[s], SHOULDER[s])), sh, col)
        items = _voxelize(lambda p, s=s: _smin(_fore(p, s), _hand(p, s), 0.35), (-6.6, -2.8, -1.6), (6.6, 1.2, 6.0),
                          rnd, seed + 3, lambda z: 0.03, rel=ELBOW[s])     # claws stay whole
        _cubes(f"{name}_fore_{s}", items, body_mat, col).parent = el
        N.arms[s], N.forearms[s] = sh, el
    # head: the checkered classic head, bowed forward, its edge breaking into pixels
    N.neck = _empty(name + "_neck", (0, -0.35, 9.25), N.torso, col)
    N.neck.scale = (1.45, 1.45, 1.45)                       # the thumbnail's head is big
    N.head = bpy.data.objects.new(name + "_head", _classic_head_mesh(name + "_head"))
    N.head.data.materials.append(_mat_head())
    col.objects.link(N.head)
    N.head.parent = N.neck
    N.head.location = (0, -0.1, 0.0)
    N.head.rotation_euler = (math.radians(-3), 0, 0)
    ring = []
    for _ in range(240):                                   # pixels breaking off the head's outline
        a = rnd.uniform(0, 2 * math.pi)
        zl = rnd.uniform(0.05, 3.75)
        r_ = 1.6 + abs(rnd.gauss(0, 0.3))
        c = (r_ * math.cos(a), 0.82 * r_ * math.sin(a) - 0.1, zl)
        pink = rnd.random() < 0.45
        rgb = _lin((230, 24, 230)) if pink else _lin((16, 10, 20))
        ring.append((c, V * 0.5 * rnd.uniform(0.3, 0.8), rgb, rgb if pink else (0, 0, 0), rnd.uniform(0, 1)))
    _cubes(name + "_head_noise", ring, body_mat, col).parent = N.neck
    # glitch streaks: a few thin horizontal lines lying on his front (the thumbnail's scanlines)
    front = [it[0] for it in items_torso if it[0][1] < -0.5 and it[0][2] > 3.8 and it[1] > V * 0.45]
    streaks = []
    for _ in range(16):
        x, y, z = front[rnd.randrange(len(front))]
        L = rnd.uniform(0.3, 1.1)
        c = rnd.choice(((180, 200, 255), (255, 60, 255), (60, 230, 255), (110, 255, 140)))
        g = tuple(v * 0.45 for v in _lin(c))
        for t in range(int(L / 0.07)):
            streaks.append(((x + t * 0.07, y - V * 0.62, z), 0.025, _lin(c), g, 0.0))
    _cubes(name + "_streaks", streaks, body_mat, col).parent = N.torso
    # the orbit: blocks of both worlds circling him, with trails
    if orbit:                                              # two rings: one round the chest, one higher and wider
        N.orbit = _empty(name + "_orbit", (0, 0.2, 6.0), N.root, col)
        N.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0)     # dips in front of him
        _orbit(N, col, assets, rnd, name, N.orbit, (5.6, 6.6, 7.6), 20, "a")
        N.orbit2 = _empty(name + "_orbit2", (0, 0.6, 14.6), N.root, col)      # above the head, never across the face
        N.orbit2.rotation_euler = (math.radians(-12), math.radians(14), 0)
        _orbit(N, col, assets, rnd, name, N.orbit2, (6.8, 8.2), 14, "b")
    return N


def _orbit(N, col, assets, rnd, name, holder, radii, count, tag):
    B = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")

    def tex_mat(n, path=None, rgb=None, glow=0.0):
        m = bpy.data.materials.new(name + "_blk_" + n)
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        if path:
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(path, check_existing=True)
            t.interpolation = "Closest"
            nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
            if glow:
                nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
                b.inputs["Emission Strength"].default_value = glow
        else:
            b.inputs["Base Color"].default_value = (*_lin(rgb), 1)
        b.inputs["Roughness"].default_value = 0.6
        return m

    # the missing-texture cube, as a little image
    from PIL import Image
    mt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_missing.png")
    im = Image.new("RGB", (2, 2))
    im.putdata([(248, 0, 248), (0, 0, 0), (0, 0, 0), (248, 0, 248)])
    im.save(mt)
    kinds = [("grass", [os.path.join(B, "grass_block_side.png")]), ("stone", [os.path.join(B, "stone.png")]),
             ("bricks", [os.path.join(B, "bricks.png")]), ("dirt", [os.path.join(B, "dirt.png")]),
             ("cobble", [os.path.join(B, "cobblestone.png")]), ("planks", [os.path.join(B, "oak_planks.png")]),
             ("missing", [mt])]
    mats = {k: (bpy.data.materials.get(name + "_blk_" + k) or tex_mat(k, p[0], glow=2.0 if k == "missing" else 0.0))
            for k, p in kinds if os.path.exists(p[0])}
    mats["roblox"] = bpy.data.materials.get(name + "_blk_roblox") or tex_mat("roblox", rgb=(232, 192, 40))
    trail = _mat_trail()
    names = list(mats)
    for i in range(count):
        ring_r = rnd.choice(radii)
        a = 2 * math.pi * i / count + rnd.uniform(-0.15, 0.15)
        size = rnd.uniform(0.38, 0.8)
        kind = names[i % len(names)] if i < len(names) else rnd.choice(names)
        bpy.ops.mesh.primitive_cube_add(size=size, location=(ring_r * math.cos(a), ring_r * math.sin(a),
                                                              rnd.uniform(-0.6, 0.6)))
        ob = bpy.context.active_object
        for c_ in list(ob.users_collection):
            c_.objects.unlink(ob)
        col.objects.link(ob)
        ob.name = f"{name}_orbit_{tag}{i}"
        ob.data.materials.append(mats[kind])
        ob.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))
        ob.parent = holder
        # its trail: an arc behind it along the ring
        span = rnd.uniform(0.35, 0.8)
        pts = []
        for t in range(13):
            aa = a - span * t / 12
            pts.append((ring_r * math.cos(aa), ring_r * math.sin(aa), ob.location.z))
        cu = bpy.data.curves.new(f"{name}_trail_{tag}{i}", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p_, q in zip(sp.points, pts):
            p_.co = (*q, 1)
        cu.bevel_depth = size * 0.05
        cu.materials.append(trail)
        tob = bpy.data.objects.new(f"{name}_trail_{tag}{i}", cu)
        col.objects.link(tob)
        tob.parent = holder
        tob.visible_shadow = False
