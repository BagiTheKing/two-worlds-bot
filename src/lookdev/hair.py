"""Steve's 3D hair, modelled on the reference animation's Steve (studied from
front, three-quarter, side, back and top views):

  - a shell around the head, standing off it by about half a skin pixel,
    with a flat cap on top;
  - cut into strips one skin pixel wide, each made of pixel-sized pieces in
    varied browns (like a skin texture, so it reads as Minecraft);
  - front fringe short (about 2 px, uneven tips), the corners longer;
  - sides growing longer toward the back (3.5 px at the front, 6 px behind);
  - back hanging to just above the neck (about 6.5 px), jagged;
  - every strip flares out a little toward its tip, and strips sit at
    slightly different depths, so they catch light and cast thin shadows.

Built in the Head bone's space (the BlendSwap rig: bone x = back, y = up,
z = his left/our right; the head is a 0.8 cube, 1 px = 0.1) and deformed by
the rig's head lattice, so it squashes and stretches with the face.
"""
import math
import random

import bmesh
import bpy

P = 0.1                         # one skin pixel
HALF = 4                        # the head is 8 px: -4..4 across, 0..8 up

PALETTE = [(72, 42, 26), (62, 36, 22), (82, 48, 30), (56, 33, 20), (68, 40, 25), (77, 45, 28), (52, 31, 19)]
TIP = (42, 25, 15)


def _lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c) + (1.0,)


def hair_material(name="steve_hair"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = "hair_col"
    nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.72
    b.inputs["Specular IOR Level"].default_value = 0.25
    return m


class _Builder:
    def __init__(self, seed):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.float_color.new("hair_col")
        self.rnd = random.Random(seed)

    def box(self, corners, color):
        """corners: 8 points (bottom 4 then top 4, same winding) in head px coords
        (r = right, b = back, u = up); converted to bone space."""
        vs = [self.bm.verts.new((b * P, u * P, r * P)) for r, b, u in corners]
        faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        c = _lin(color)
        for f in faces:
            try:
                face = self.bm.faces.new([vs[i] for i in f])
            except ValueError:
                continue
            for loop in face.loops:
                loop[self.col] = c

    def strip_colour(self):
        return self.rnd.choice(PALETTE)

    def shade(self, base, tip=False):
        """A piece of a strip: the strip's own brown, varied a little (the
        reference's hair is smooth along a strip, the strips differ)."""
        k = self.rnd.uniform(0.93, 1.06) * (0.82 if tip else 1.0)
        return tuple(min(255, v * k) for v in base)


def _strip(B, side, a0, a1, length, base, thick, flare, top=8.0):
    """One strip hanging down a face of the head.
    side: 'front' | 'back' | 'left' | 'right'; a0..a1: its span along that face
    (px, in the face's own across-axis); base: how far it stands off the head at
    the top; flare: extra standoff per px of drop. Cut into 1 px pieces."""
    segs = max(1, math.ceil(length - 1e-6))
    base_col = B.strip_colour()
    for s in range(segs):
        u1 = top - s
        u0 = max(top - length, u1 - 1)
        d1 = base + flare * (top - u1)            # standoff at this piece's top
        d0 = base + flare * (top - u0)            # and at its bottom
        last = s == segs - 1
        col = B.shade(base_col, tip=last)
        pts = []
        for u, d in ((u0, d0), (u1, d1)):
            for (a, dd) in ((a0, d), (a1, d), (a1, d + thick), (a0, d + thick)):
                pts.append(_to_head(side, a, dd, u))
        B.box(pts, col)


def _to_head(side, a, d, u):
    """A point on a face of the head: a = across that face, d = out from it."""
    if side == "front":                           # the face side is at back = -4; across = right
        return (a, -HALF - d, u)
    if side == "back":
        return (a, HALF + d, u)
    if side == "right":                           # his left, our right when facing him: r = +4
        return (HALF + d, a, u)
    return (-HALF - d, a, u)


def build_hair(arm, lattice=None, bone="Head", seed=12, name="steve_hair"):
    B = _Builder(seed)
    rnd = B.rnd
    O = 0.26                                      # standoff of the sides and back
    OF = 0.2                                     # standoff of the fringe (closer to the face)
    T = 0.3                                      # strip thickness
    # front fringe: 8 strips; corners longer, joining the sides
    front = [4.2, 2.6, 2.3, 1.9, 2.2, 2.0, 2.7, 4.3]
    for i, L in enumerate(front):
        a0 = -HALF + i - (OF + T if i == 0 else 0)
        a1 = -HALF + i + 1 + (OF + T if i == 7 else 0)
        _strip(B, "front", a0, a1, L + rnd.uniform(-0.15, 0.15), OF + rnd.uniform(0, 0.08), T, 0.045)
    # sides: front to back, longer toward the back
    sides = [3.4, 4.0, 4.6, 5.1, 5.5, 5.9, 6.1, 6.3]
    for side in ("left", "right"):
        for j, L in enumerate(sides):
            a0 = -HALF - OF - T + j * (8 + OF + T + O) / 8
            a1 = a0 + (8 + OF + T + O) / 8
            _strip(B, side, a0, a1, L + rnd.uniform(-0.4, 0.4), O + rnd.uniform(0, 0.08), T, 0.045)
    # back: to just above the neck, jagged
    for j in range(8):
        a0 = -HALF - O - T + j * (8 + 2 * (O + T)) / 8
        a1 = a0 + (8 + 2 * (O + T)) / 8
        _strip(B, "back", a0, a1, 6.4 + rnd.uniform(-0.5, 0.4), O + rnd.uniform(0, 0.08), T, 0.05)
    # top cap: pixel tiles, rows running front to back (as the hair is combed)
    E = O + T
    n = 8
    step_r = (8 + 2 * E) / n
    step_b = (8 + OF + T + E) / n
    for i in range(n):
        base_col = rnd.choice(PALETTE)
        for j in range(n):
            r0 = -HALF - E + i * step_r
            b0 = -HALF - OF - T + j * step_b
            h = 8.0 + 0.3
            col = B.shade(base_col)
            pts = [(r0, b0, 7.9), (r0 + step_r, b0, 7.9), (r0 + step_r, b0 + step_b, 7.9), (r0, b0 + step_b, 7.9),
                   (r0, b0, h), (r0 + step_r, b0, h), (r0 + step_r, b0 + step_b, h), (r0, b0 + step_b, h)]
            B.box(pts, col)

    bmesh.ops.recalc_face_normals(B.bm, faces=B.bm.faces)
    me = bpy.data.meshes.new(name)
    B.bm.to_mesh(me)
    B.bm.free()
    me.materials.append(hair_material(name + "_mat"))
    ob = bpy.data.objects.new(name, me)
    for col in arm.users_collection:
        col.objects.link(ob)
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    from mathutils import Matrix
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.location = (0, -arm.data.bones[bone].length, 0)   # bone-parented objects sit at the bone's tail
    bv = ob.modifiers.new("soft_edges", "BEVEL")       # edges catch the light, as on the reference
    bv.width = 0.007
    bv.segments = 2
    bv.limit_method = "ANGLE"
    if lattice is not None:
        md = ob.modifiers.new("head_lattice", "LATTICE")
        md.object = lattice
    return ob
