"""Patch, the glitch detector, at the new quality bar. What viewers know stays:
a small pale floating cube, a dark screen for a face, one cyan eye, two side
fins. What is new:
  - the shell is pixel-textured like a Minecraft block (soft greys, darker
    edge pixels, panel seams and rivets), with softly bevelled edges;
  - the face is a glossy dark screen with a bezel; the eye is drawn on it as
    glowing pixel art (a round iris, a darker pupil, a white catch pixel, faint
    scanlines), and it acts: it blinks, looks around, squints, smiles (^),
    looks sad, widens, and glitches to magenta with a colour split;
  - a cyan hover light under him and a soft glow; the scan beam is a fan of
    light with moving scanlines.

    from patch import build_patch, set_patch
    P = build_patch(collection, size=0.42)         # size = the cube's width (Steve's head is 0.8 rig = 0.5 scene)
    set_patch(P, {"open": 1, "look_x": 0.3, "smile": 0, "sad": 0, "squint": 0, "wide": 0, "glitch": 0, "scan": 0})
    P.root (move / turn / bob), P.fins["l"/"r"] (flap about x)
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector
from PIL import Image

from faceplate import N, ab, clamp01, gt, lt, mix, mn, mx, prop

HERE = os.path.dirname(os.path.abspath(__file__))
CYAN = (0.02, 0.75, 1.0)
MAGENTA = (1.0, 0.12, 0.85)
DEFAULTS = {"open": 1.0, "look_x": 0.0, "look_y": 0.0, "smile": 0.0, "sad": 0.0, "squint": 0.0,
            "wide": 0.0, "glitch": 0.0, "scan": 0.0}


def _lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c)


def shell_texture(path, seed=4):
    """16 x 16: a pale block with soft per-pixel shading, darker rim pixels,
    a panel seam across the middle and four rivets."""
    rnd = random.Random(seed)
    im = Image.new("RGB", (16, 16))
    for x in range(16):
        for y in range(16):
            base = 226 + rnd.randint(-7, 6)
            if x in (0, 15) or y in (0, 15):
                base -= 34                                  # the rim
            elif x in (1, 14) or y in (1, 14):
                base -= 12
            if y == 8 and 2 <= x <= 13:
                base -= 22                                  # the seam
            if (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
                base -= 46                                  # rivets
            if (x, y) in ((4, 4), (13, 4), (4, 13), (13, 13)):
                base += 10                                  # their highlight
            im.putpixel((x, y), (base - 4, base, base + 8))  # a cool, slightly blue white
    im.save(path)
    return path


def _shell_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(shell_texture(os.path.join(HERE, "_patch_shell.png")), check_existing=True)
    t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Specular IOR Level"].default_value = 0.5
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.25
    return m


def _screen_mat(name):
    """The face screen: glossy dark glass, the pixel eye glowing on it."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N.nt = nt
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*_lin((16, 20, 30)), 1)
    b.inputs["Roughness"].default_value = 0.12
    b.inputs["Specular IOR Level"].default_value = 0.7
    uv = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    G = 13.0                                               # the screen's pixel grid
    X = N.math("FLOOR", N(sep.outputs["X"]) * G) / G + 0.5 / G
    Y = N.math("FLOOR", N(sep.outputs["Y"]) * G) / G + 0.5 / G
    P = {k: prop(k) for k in DEFAULTS}
    r = 0.31 * (1 + 0.2 * P["wide"])
    cx = 0.5 + 0.12 * P["look_x"]
    cy = 0.5 + 0.1 * P["look_y"]
    dx = X - cx
    dy = Y - cy
    d2 = dx * dx + dy * dy
    iris = lt(d2, r * r)
    # lids: the top comes down (blink, squint, sad slants it), the bottom rises (squint)
    top = cy + r * (2 * P["open"] - 1) - 0.18 * P["squint"] - P["sad"] * 0.2 * (0.6 + dx * 4)
    bot = cy - r + 0.16 * P["squint"]
    shown = iris * gt(top, Y) * gt(Y, bot)
    # smile: the eye becomes an arch (^): a ring, the lower half cut
    ring = lt(d2, r * r) * gt(d2, r * r * 0.384) * gt(Y, cy - 0.02)
    shown = mix(P["smile"], shown, ring)
    pupil = lt(d2, r * r * 0.14 * (1 - 0.45 * P["wide"])) * (1.0 - P["smile"])
    rim = gt(d2, r * r * 0.7) * (1.0 - P["smile"])
    catch = lt(ab(X - (cx + r * 0.2)), 0.5 / G) * lt(ab(Y - (cy + r * 0.2)), 0.5 / G) * (1.0 - P["smile"])
    # colour: cyan, magenta when glitching; a colour split (one side cyan, one magenta)
    split = P["glitch"] * gt(ab(dx), r * 0.55)
    col = mix(P["glitch"], CYAN, MAGENTA)
    col = mix(split * lt(dx, 0.0), col, CYAN)
    col = mix(rim, col, mix(P["glitch"], (0.02, 0.45, 0.62), (0.5, 0.02, 0.4)))     # a darker ring at the iris edge
    col = mix(pupil, col, mix(P["glitch"], (0.0, 0.05, 0.08), (0.08, 0.0, 0.06)))
    col = mix(catch, col, (1.0, 1.0, 1.0))
    scan = 0.82 + 0.18 * N.math("MODULO", N.math("FLOOR", N(sep.outputs["Y"]) * G * 2), 2.0)
    glow = shown * scan * (1.0 - pupil * 0.92)
    nt.links.new(mix(glow, (0, 0, 0), col).s, b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 2.2
    return m


def _beam_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    wave = nt.nodes.new("ShaderNodeTexWave")                 # scanlines along the beam
    wave.inputs["Scale"].default_value = 18.0
    nt.links.new(tc.outputs["Generated"], wave.inputs["Vector"])
    fade = nt.nodes.new("ShaderNodeMath")
    fade.operation = "SUBTRACT"
    fade.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["Y"], fade.inputs[1])
    k = nt.nodes.new("ShaderNodeMath")                      # bright at the eye (generated y = 1 there), fading out
    k.operation = "MULTIPLY"
    nt.links.new(sep.outputs["Y"], k.inputs[0])
    nt.links.new(wave.outputs["Fac"], k.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*CYAN, 1)
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = 3.0
    nt.links.new(k.outputs[0], st.inputs[0])
    nt.links.new(st.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs["BSDF"], add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    return m


def _box(name, size, loc, mat, parent, col, bevel=0.0, uv_face=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    uvl = bm.loops.layers.uv.new()
    for f in bm.faces:
        n = f.normal
        for loop in f.loops:
            co = loop.vert.co
            if abs(n.z) > 0.5:
                u, v = co.x / size[0] + 0.5, co.y / size[1] + 0.5
            elif abs(n.x) > 0.5:
                u, v = co.y / size[1] + 0.5, co.z / size[2] + 0.5
            else:
                u, v = co.x / size[0] + 0.5, co.z / size[2] + 0.5
            loop[uvl].uv = (u, v)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    if bevel:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 3
        md.harden_normals = True
        for p in me.polygons:
            p.use_smooth = True
    return ob


class Patch:
    pass


def build_patch(col, size=0.42, name="patch"):
    s = size
    P = Patch()
    P.root = bpy.data.objects.new(name, None)
    col.objects.link(P.root)
    shell = _shell_mat(name + "_shell")
    _box(name + "_cube", (s, s, s), (0, 0, 0), shell, P.root, col, bevel=0.07 * s)
    bezel = bpy.data.materials.new(name + "_bezel")
    bezel.use_nodes = True
    bb = bezel.node_tree.nodes["Principled BSDF"]
    bb.inputs["Base Color"].default_value = (*_lin((52, 58, 70)), 1)
    bb.inputs["Roughness"].default_value = 0.35
    _box(name + "_bezel", (0.84 * s, 0.03 * s, 0.76 * s), (0, -0.5 * s - 0.005 * s, 0.02 * s), bezel, P.root, col,
         bevel=0.012 * s)
    P.screen = _box(name + "_screen", (0.74 * s, 0.03 * s, 0.66 * s), (0, -0.5 * s - 0.02 * s, 0.02 * s),
                    _screen_mat(name + "_screen"), P.root, col)
    for k, v in DEFAULTS.items():
        P.screen[k] = v
    P.fins = {}
    for side, sx in (("l", -1), ("r", 1)):
        pv = bpy.data.objects.new(f"{name}_fin_{side}", None)
        col.objects.link(pv)
        pv.parent = P.root
        pv.location = (sx * 0.5 * s, 0.05 * s, 0.05 * s)
        _box(f"{name}_fin_{side}_mesh", (0.09 * s, 0.42 * s, 0.26 * s), (sx * 0.06 * s, 0, 0), shell, pv, col,
             bevel=0.02 * s)
        P.fins[side] = pv
    # the hover light: a small cyan glow under him
    L = bpy.data.lights.new(name + "_hover", "POINT")
    L.energy, L.color, L.shadow_soft_size = 6.0 * (s / 0.42) ** 2, CYAN, 0.1
    lo = bpy.data.objects.new(name + "_hover", L)
    col.objects.link(lo)
    lo.parent = P.root
    lo.location = (0, 0, -0.75 * s)
    em = bpy.data.materials.new(name + "_underglow")
    em.use_nodes = True
    eb = em.node_tree.nodes["Principled BSDF"]
    eb.inputs["Base Color"].default_value = (0, 0, 0, 1)
    eb.inputs["Emission Color"].default_value = (*CYAN, 1)
    eb.inputs["Emission Strength"].default_value = 6.0
    _box(name + "_vent", (0.5 * s, 0.5 * s, 0.02 * s), (0, 0, -0.505 * s), em, P.root, col)
    # the scan beam: a flat fan of light from the eye, forward and down
    bm = bmesh.new()                                        # an open cone of light (four sides)
    uvl = bm.loops.layers.uv.new()
    a = bm.verts.new((0, 0, 0))
    L_, W_, H_ = 3.0 * s * 3, 0.9 * s * 3, 0.6 * s * 3
    ring = [bm.verts.new(p) for p in ((-W_, -L_, -H_), (W_, -L_, -H_), (W_, -L_, H_ - 2 * H_ * 0.9), (-W_, -L_, H_ - 2 * H_ * 0.9))]
    ring = [bm.verts.new((-W_, -L_, -1.5 * H_)), bm.verts.new((W_, -L_, -1.5 * H_)),
            bm.verts.new((W_, -L_, 0.2 * H_)), bm.verts.new((-W_, -L_, 0.2 * H_))]
    for i in range(4):
        f = bm.faces.new((a, ring[i], ring[(i + 1) % 4]))
        for loop, uvc in zip(f.loops, ((0.5, 0), (0, 1), (1, 1))):
            loop[uvl].uv = uvc
    me = bpy.data.meshes.new(name + "_beam")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(_beam_mat(name + "_beam"))
    P.beam = bpy.data.objects.new(name + "_beam", me)
    col.objects.link(P.beam)
    P.beam.parent = P.root
    P.beam.location = (0, -0.55 * s, 0.02 * s)
    P.beam.hide_render = True
    for attr in ("visible_diffuse", "visible_glossy", "visible_shadow"):
        setattr(P.beam, attr, False)
    return P


def set_patch(P, values):
    for k, v in values.items():
        if k in DEFAULTS:
            P.screen[k] = v
    P.beam.hide_render = values.get("scan", P.screen["scan"]) < 0.5
    P.screen.update_tag()
