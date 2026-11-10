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
# The cells. Every pixel of Null's body is one of the Noob's old bodies, pressed
# into a cube: near-black, with a worn rim, and on its outward side what is left
# of his face (the two tall eyes and the smile), glowing faintly like an ember.
# The faces fade out with distance, so from afar he is the dark wraith he always
# was; a few cells ("glints") keep their smile at any distance.
CELL_PX = 16
_E, _S = "#", "~"
_CELL_FACES = {          # 12 x 9 drawings, placed at (2, 4) of the 16 x 16 cell
    "smile":  ["..##....##..", "..##....##..", "..##....##..", "..##....##..", "............", ".#........#.",
               ".##......##.", "..########..", "...######..."],
    "left":   [".##....##...", ".##....##...", ".##....##...", ".##....##...", "............", ".#........#.",
               ".##......##.", "..########..", "...######..."],
    "right":  ["...##....##.", "...##....##.", "...##....##.", "...##....##.", "............", ".#........#.",
               ".##......##.", "..########..", "...######..."],
    "asleep": ["............", "............", ".####..####.", "............", "............", ".#........#.",
               ".##......##.", "..########..", "...######..."],
    "wide":   ["..##....##..", "..##....##..", "..##....##..", "............", ".##########.", ".#~~~~~~~~#.",
               ".##~~~~~~##.", "..########..", "...######..."],
    "one":    ["..##........", "..##....~...", "..##........", "..##........", "............", ".#........#.",
               ".##......##.", "..########..", "...######..."],
    "worn":   ["..#~....##..", "..~#....#~..", "..##....~#..", "..~.....##..", "............", ".#........~.",
               ".~#......##.", "..##~##~#~..", "...#~.##~..."],
}
CELL_VARIANTS = ["blank"] + list(_CELL_FACES)
_CELL_ODDS = [("smile", 0.5), ("left", 0.1), ("right", 0.1), ("asleep", 0.1), ("wide", 0.07), ("one", 0.06), ("worn", 0.07)]
CELL_FACE_COLOURS = [((236, 190, 60), 0.5), ((244, 222, 150), 0.26), ((214, 140, 40), 0.2),    # his yellow: fresh, bleached, amber
                     ((236, 40, 236), 0.04)]                 # and a few gone wrong (the missing texture's magenta)
CELL_TINTS = [(26, 20, 8), (8, 13, 26), (13, 20, 8)]        # the same three, almost gone to black


def _cell_atlas():
    """One strip of 16 x 16 cells: R = how light the surface is (the worn rim,
    scratches), G = the face. Not colour data."""
    im = bpy.data.images.get("null_cells")
    if im:
        return im
    n = len(CELL_VARIANTS)
    rng = np.random.default_rng(4)
    px = np.zeros((CELL_PX, CELL_PX * n, 4), np.float32)
    px[..., 3] = 1
    for k, name in enumerate(CELL_VARIANTS):
        t = np.full((CELL_PX, CELL_PX), 0.30, np.float32) + rng.uniform(-0.07, 0.07, (CELL_PX, CELL_PX)).astype(np.float32)
        t[0, :] = t[-1, :] = t[:, 0] = t[:, -1] = 0.07          # the seam between two cells
        t[1, 1:-1] = 0.78                                      # a lit top edge,
        t[1:-1, 1] = 0.55                                      # a softer left one,
        t[-2, 1:-1] = t[1:-1, -2] = 0.16                       # shade below and right
        t[2, 2] = t[2, -3] = 0.62                              # rivet-like corner pixels
        g = np.zeros((CELL_PX, CELL_PX), np.float32)
        for r, row in enumerate(_CELL_FACES.get(name, [])):
            for c, ch in enumerate(row):
                if ch != ".":
                    g[4 + r, 2 + c] = rng.uniform(0.72, 1.0) if ch == _E else 0.25
                    t[4 + r, 2 + c] = 0.12                     # the face is cut into the surface
        px[:, k * CELL_PX:(k + 1) * CELL_PX, 0] = t[::-1]      # (image rows run bottom-up)
        px[:, k * CELL_PX:(k + 1) * CELL_PX, 1] = g[::-1]
    im = bpy.data.images.new("null_cells", CELL_PX * n, CELL_PX, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(px.ravel())
    im.pack()
    return im


def _mat_body():
    m = bpy.data.materials.new("null_body")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes.new, nt.links.new
    b = nt.nodes["Principled BSDF"]
    a = N("ShaderNodeAttribute")
    a.attribute_name = "vox_col"
    e = N("ShaderNodeAttribute")
    e.attribute_name = "vox_glow"
    cell = N("ShaderNodeAttribute")
    cell.attribute_name = "vox_cell"                       # the face's colour; alpha = a glint
    tex = N("ShaderNodeTexImage")
    tex.image = _cell_atlas()
    tex.interpolation = "Closest"
    tex.extension = "EXTEND"
    sep = N("ShaderNodeSeparateColor")
    L(tex.outputs["Color"], sep.inputs["Color"])

    def math_(op, x=None, y=None, z=None, clamp=False):
        n = N("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((x, y, z)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n

    def vmix(fac, c1, c2, kind="MIX"):
        n = N("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = kind
        for sock, v in ((n.inputs[0], fac), (n.inputs[6], c1), (n.inputs[7], c2)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = v
            else:
                L(v, sock)
        return n.outputs[2]
    # how near the camera is: 1 close, 0 far (the faces and the surface detail fade with it)
    cd = N("ShaderNodeCameraData")
    near = N("ShaderNodeMapRange")
    near.interpolation_type = "SMOOTHSTEP"
    near.inputs["From Min"].default_value = 9.0
    near.inputs["From Max"].default_value = 24.0
    near.inputs["To Min"].default_value = 1.0
    near.inputs["To Max"].default_value = 0.0
    L(cd.outputs["View Distance"], near.inputs["Value"])
    m["near_node"] = near.name
    # the surface: the cell's own dark colour, lighter on its worn rim (up close)
    gain = math_("MULTIPLY_ADD", sep.outputs["Red"], 9.0, -1.7)           # 0.30 -> 1, the rim well above
    gain = math_("MULTIPLY_ADD", math_("SUBTRACT", gain.outputs[0], 1.0).outputs[0], near.outputs["Result"], 1.0)
    base = N("ShaderNodeVectorMath")
    base.operation = "SCALE"
    L(a.outputs["Color"], base.inputs[0])
    L(gain.outputs[0], base.inputs["Scale"])
    L(base.outputs[0], b.inputs["Base Color"])
    # the face: an ember in the cell's colour
    # (the attribute's alpha: over 0.95 a glint, else the cell's place in the order they wake up)
    glint = math_("GREATER_THAN", cell.outputs["Alpha"], 0.95)
    wake = math_("SUBTRACT", 1.0, math_("DIVIDE", cell.outputs["Alpha"], 0.9).outputs[0])
    m["wake"] = wake.name                                  # inputs[0]: 0 none awake .. 1 all (and beyond)
    on = math_("MULTIPLY", wake.outputs[0], 25.0, clamp=True)
    vis = math_("MAXIMUM", math_("MULTIPLY", near.outputs["Result"], on.outputs[0]).outputs[0], glint.outputs[0])
    amt = math_("MULTIPLY", sep.outputs["Green"], vis.outputs[0])
    power = math_("MULTIPLY", amt.outputs[0], 1.0)
    m["face_power"] = power.name                           # inputs[1]: how bright the faces are
    face = N("ShaderNodeVectorMath")
    face.operation = "SCALE"
    L(cell.outputs["Color"], face.inputs[0])
    L(power.outputs[0], face.inputs["Scale"])
    glow = N("ShaderNodeVectorMath")
    glow.operation = "SCALE"
    L(e.outputs["Color"], glow.inputs[0])
    glow.inputs["Scale"].default_value = 4.0
    add = N("ShaderNodeVectorMath")
    add.operation = "ADD"
    L(glow.outputs[0], add.inputs[0])
    L(face.outputs[0], add.inputs[1])
    L(add.outputs[0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Specular IOR Level"].default_value = 0.25
    return m


def null_smile(amount):
    """The copied smile on his face: 0 none (as in the thumbnail) .. 1 on."""
    m = bpy.data.materials["null_head"]
    m.node_tree.nodes[m["smile"]].inputs[1].default_value = amount


def cells_look(near=9.0, far=24.0, power=1.0, awake=1.0):
    """Where the faces fade out (metres from the camera), how bright they are, and
    how many are awake (0 none .. 1 all): they light up one by one, in an order of their own."""
    m = bpy.data.materials["null_body"]
    n = m.node_tree.nodes[m["near_node"]]
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = near, far
    m.node_tree.nodes[m["face_power"]].inputs[1].default_value = power
    m.node_tree.nodes[m["wake"]].inputs[0].default_value = awake * 1.05


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
    # the copied smile: the Noob's face (the same drawing as on every cell), white, on the front of the head
    px = np.zeros((38, 31, 4), np.float32)
    px[..., 3] = 1
    for r, row in enumerate(_CELL_FACES["smile"]):
        for c, ch in enumerate(row):
            if ch != ".":
                px[9 + 2 * r:11 + 2 * r, 3 + 2 * c:5 + 2 * c, 0] = 1.0
    im = bpy.data.images.new("null_smile", 31, 38, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(px[::-1].ravel())
    im.pack()
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.0, 0.0)
    mp.inputs["Scale"].default_value = (1 / 3.1, 1 / 3.85, 1.0)
    nt.links.new(com.outputs["Vector"], mp.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeTexImage")
    st.image, st.interpolation, st.extension = im, "Closest", "CLIP"
    nt.links.new(mp.outputs["Vector"], st.inputs["Vector"])
    front = nt.nodes.new("ShaderNodeMath")                 # only on the face's side (-y)
    front.operation = "LESS_THAN"
    front.inputs[1].default_value = -0.35
    nt.links.new(sep.outputs["Y"], front.inputs[0])
    on = nt.nodes.new("ShaderNodeMath")
    on.operation = "MULTIPLY"
    nt.links.new(st.outputs["Color"], on.inputs[0])
    nt.links.new(front.outputs[0], on.inputs[1])
    amt = nt.nodes.new("ShaderNodeMath")
    amt.operation = "MULTIPLY"
    amt.inputs[1].default_value = 0.0
    nt.links.new(on.outputs[0], amt.inputs[0])
    m["smile"] = amt.name                                  # inputs[1]: 0 no smile .. 1 the copied smile
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    nt.links.new(amt.outputs[0], mixc.inputs[0])
    nt.links.new(ck.outputs["Color"], mixc.inputs[6])
    mixc.inputs[7].default_value = (1.0, 0.94, 1.0, 1)
    es = nt.nodes.new("ShaderNodeMath")
    es.operation = "MULTIPLY_ADD"
    nt.links.new(amt.outputs[0], es.inputs[0])
    es.inputs[1].default_value = 3.6
    es.inputs[2].default_value = 2.4
    nt.links.new(mixc.outputs[2], b.inputs["Base Color"])
    nt.links.new(mixc.outputs[2], b.inputs["Emission Color"])
    nt.links.new(es.outputs[0], b.inputs["Emission Strength"])
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
    """items: [(centre, half_size, colour, glow, rotation_z[, cell])]; one mesh, colours
    per face. cell = (side 2..5, variant, face colour, glint): the face on that side."""
    verts, faces, cols, glows, cells, uvs = [], [], [], [], [], []
    nv = len(CELL_VARIANTS)
    for it in items:
        c, h, rgb, glow, rz = it[:5]
        cell = it[5] if len(it) > 5 else None
        cz, sz = math.cos(rz), math.sin(rz)
        i = len(verts)
        for dx, dy, dz in _CUBE:
            x, y = dx * h, dy * h
            verts.append((c[0] + x * cz - y * sz, c[1] + x * sz + y * cz, c[2] + dz * h))
        for fi, f in enumerate(_FACES):
            faces.append([i + k for k in f])
            cols.append(rgb)
            glows.append(glow)
            on = cell is not None and fi == cell[0]
            cells.append((*cell[2], cell[3]) if on else (0.0, 0.0, 0.0, 0.0))
            u0 = (cell[1] if on else 0) / nv
            uvs.extend((u0, 0.0, u0 + 1.0 / nv, 0.0, u0 + 1.0 / nv, 1.0, u0, 1.0))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.uv_layers.new(name="cell").data.foreach_set("uv", uvs)
    me.color_attributes.new("vox_cell", "FLOAT_COLOR", "FACE").data.foreach_set("color", [v for c_ in cells for v in c_])
    ca = me.color_attributes.new("vox_col", "FLOAT_COLOR", "FACE")
    ga = me.color_attributes.new("vox_glow", "FLOAT_COLOR", "FACE")
    for k, (c_, g_) in enumerate(zip(cols, glows)):
        ca.data[k].color = (*c_, 1)
        ga.data[k].color = (*g_, 1)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def _voxelize(sdf, lo, hi, rnd, seed, dissolve, rel=(0, 0, 0), loose=True):
    """Sample a shape on the grid: the solid shell, the voxels coming loose at its
    edge (pushed outward, shrinking), as (centre, half, colour, glow, rot) items,
    relative to `rel` (the part's pivot)."""
    xs = np.arange(lo[0], hi[0], V)
    ys = np.arange(lo[1], hi[1], V)
    zs = np.arange(lo[2], hi[2], V)
    P = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1).reshape(-1, 3).astype(np.float32)
    d = sdf(P)
    gx, gy, _gz = np.gradient(d.reshape(len(xs), len(ys), len(zs)), V)     # outward: where a cell's face looks
    gx, gy = gx.ravel(), gy.ravel()
    n = _noise3(P, 1.3, seed)
    n2 = _noise3(P, 4.0, seed + 1)
    items = []
    inner = (d < -V) & (d > -3.2 * V)                       # the body's skin: solid where it isn't dissolving
    outer = (d >= -V) & (d < 0)                             # its outermost pixels: ragged
    loose_zone = (d >= 0) & (d < 0.9)                       # where loose pixels can hang
    rel = np.array(rel, np.float32)
    dark = [_lin(c) for c in ((8, 6, 11), (13, 9, 17), (5, 4, 7), (20, 13, 27), (10, 8, 14))]
    tints = [_lin(c) for c in CELL_TINTS]
    names, odds = [CELL_VARIANTS.index(k) for k, _ in _CELL_ODDS], [w for _, w in _CELL_ODDS]
    fcols, fodds = [_lin(c) for c, _ in CELL_FACE_COLOURS], [w for _, w in CELL_FACE_COLOURS]
    for k in np.nonzero(inner | outer | loose_zone)[0]:
        p = P[k]
        z = p[2]
        dz = dissolve(z)
        solid = (inner[k] and n[k] > dz * 1.15 - 0.08 + 0.2 * (n2[k] - 0.5)) or \
                (outer[k] and n2[k] > 0.3 + 0.8 * dz)
        if not loose:
            solid = bool(inner[k] or outer[k])              # a clean part: nothing coming off it
        if solid:
            c = p - rel
            half = V * 0.5 * rnd.uniform(0.92, 1.04)
        elif loose and rnd.random() < (0.02 if loose_zone[k] else 0.12) + 0.45 * dz:   # a piece coming off: outward, smaller
            out_dir = p - np.array((0, 0.2, min(max(z, 1.0), 8.0)), np.float32)
            out_dir = out_dir / (np.linalg.norm(out_dir) + 1e-6)
            dist = rnd.uniform(0.05, 0.6) * (1 + 2.2 * dz)
            c = p + out_dir * dist + np.array((0, 0, -rnd.uniform(0, 0.8) * dz), np.float32) - rel
            half = V * 0.5 * rnd.uniform(0.35, 0.9)
        else:
            continue
        r_ = rnd.random()
        cell = None
        if r_ < 0.008:
            glow = _lin(rnd.choice(((255, 40, 255), (40, 255, 255), (80, 255, 120))))
            rgb = glow
        else:
            kc = rnd.choices(range(len(fcols)), fodds)[0]
            rgb = rnd.choice(tints) if rnd.random() < 0.3 else rnd.choice(dark)
            glow = (0, 0, 0)
            # the face looks outward, and a little more often at whoever he is facing (-y)
            sides = {2: -gy[k] * 1.5 + 0.25, 3: gx[k], 4: gy[k], 5: -gx[k]}
            side = max(sides, key=sides.get)
            if rnd.random() < 0.9:
                lum = 0.1 + 1.5 * rnd.random() ** 2.6          # most are faint embers, a few burn
                cell = (side, rnd.choices(names, odds)[0], tuple(v * lum for v in fcols[kc]),
                        1.0 if rnd.random() < 0.012 else rnd.uniform(0.0, 0.9))
        items.append((tuple(c), half, rgb, glow, rnd.uniform(-0.15, 0.15), cell))
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


def build_hand(col, side="sr", seed=6, name="null_hand"):
    """One forearm and claw hand on its own, whole (nothing coming loose), for close
    work such as reaching through the portal. Returns an empty at the wrist: the
    claws hang along its -z, the forearm runs up and back from it; scale it freely."""
    rnd = random.Random(seed)
    mat = bpy.data.materials.get("null_body") or _mat_body()
    piv = _empty(f"{name}_{side}", (0, 0, 0), None, col)
    items = _voxelize(lambda p: _smin(_fore(p, side), _hand(p, side), 0.35), (-6.6, -2.8, -1.6), (6.6, 1.2, 6.0),
                      rnd, seed + 3, lambda z: 0.0, rel=WRIST[side], loose=False)
    ob = _cubes(f"{name}_{side}_vox", items, mat, col)
    ob.parent = piv
    piv["mesh"] = ob.name
    return piv


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
