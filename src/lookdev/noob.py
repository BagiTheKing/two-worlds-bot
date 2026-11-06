"""The Noob, built in code at the reference quality bar: the classic Roblox R6
body (a 2x2x1 torso, 1x2x1 arms and legs, all rigid, as Roblox has no elbows or
knees), smooth plastic in the classic colours, softly rounded edges, and a face
drawn by the same shader system as Steve's (faceplate.py, style "noob": glossy
black oval eyes with a shine, lids that can squint or slant, the mouth shapes).

Two heads: "classic" (the rounded Roblox head) and "box" (the series' block head).
Units are studs; build_noob(..., height=2.0) scales him to a height in scene units.
Posing: pose_noob(n, {...}) with the same names as Steve's pose.py
(root_yaw, chest_lean/side/twist, head_turn/tilt/nod, arm_sl/sr {out, fwd, twist},
leg_sl/sr {fwd, out}); "sl" = the screen's left when he faces the camera (his right).
"""
import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

from faceplate import NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH, MOUTH_DEFAULTS, face_material

YELLOW = (232, 192, 40)       # Bright yellow (a touch under, so the sun doesn't burn it white)
BLUE = (13, 105, 172)         # Bright blue
GREEN = (140, 168, 58)        # Br. yellowish green (likewise)
HEAD_W, HEAD_H = 1.2, 1.2


def _lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c)


def plastic(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*_lin(rgb), 1)
    b.inputs["Roughness"].default_value = 0.32                 # Roblox smooth plastic
    b.inputs["Specular IOR Level"].default_value = 0.5
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.15
        b.inputs["Coat Roughness"].default_value = 0.2
    return m


def _finish(me, sharp=40):
    for p in me.polygons:
        p.use_smooth = True
    if hasattr(me, "set_sharp_from_angle"):
        me.set_sharp_from_angle(angle=math.radians(sharp))


def rounded_box(name, size, r=0.07, seg=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=seg, profile=0.5, affect="EDGES")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    _finish(me)
    return me


def _classic_r(zl, R=HEAD_W / 2, H=HEAD_H, rc=0.3):
    """The classic head's radius at height zl (0..H): a cylinder with well rounded caps."""
    if zl < rc:
        return R - rc + math.sqrt(max(0.0, rc * rc - (rc - zl) ** 2))
    if zl > H - rc:
        return R - rc + math.sqrt(max(0.0, rc * rc - (zl - (H - rc)) ** 2))
    return R


def classic_head(name, segs=48, rings=40):
    bm = bmesh.new()
    rows = []
    for j in range(rings + 1):
        zl = HEAD_H * j / rings
        r = _classic_r(zl)
        rows.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), zl))
                     for i in range(segs)])
    for j in range(rings):
        for i in range(segs):
            a, b = rows[j][i], rows[j][(i + 1) % segs]
            c, d = rows[j + 1][(i + 1) % segs], rows[j + 1][i]
            bm.faces.new((a, b, c, d))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def _plate(name, head):
    """The face plate: a patch hugging the front of the head, UV 0..1 = the 8 x 8 face grid."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    n = 24
    vs = {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = i / n, j / n
            zl = v * HEAD_H
            if head == "classic":
                th = (u - 0.5) * math.radians(150)
                r = _classic_r(zl) + 0.004
                p = (r * math.sin(th), -r * math.cos(th), zl)
            else:                                      # only the flat part of the front (inside the rounded edges)
                fx = 0.13 / HEAD_W
                uu, vv = fx + u * (1 - 2 * fx), fx + v * (1 - 2 * fx)
                p = ((uu - 0.5) * HEAD_W, -HEAD_W / 2 - 0.004, vv * HEAD_H)
            vs[i, j] = bm.verts.new(p)
    for i in range(n):
        for j in range(n):
            f = bm.faces.new([vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]])
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                if head == "classic":
                    loop[uvl].uv = (a / n, b / n)
                else:
                    fx = 0.13 / HEAD_W
                    loop[uvl].uv = (fx + a / n * (1 - 2 * fx), fx + b / n * (1 - 2 * fx))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _empty(name, loc, parent, col):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    e.rotation_mode = "QUATERNION"
    return e


def _part(name, me, mat, loc, parent, col):
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    col.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    return ob


class Noob:
    pass


def build_noob(col, head="classic", height=2.0, name="noob"):
    """Build him in collection `col`, standing at the origin facing -y."""
    n = Noob()
    yel, blu, grn = plastic(name + "_yellow", YELLOW), plastic(name + "_blue", BLUE), plastic(name + "_green", GREEN)
    total = 4.0 + HEAD_H
    n.root = _empty(name + "_root", (0, 0, 0), None, col)
    n.root.scale = (height / total,) * 3
    n.pelvis = _empty(name + "_pelvis", (0, 0, 2.0), n.root, col)
    n.torso = _empty(name + "_torso", (0, 0, 0), n.pelvis, col)
    _part(name + "_torso_mesh", rounded_box(name + "_torso", (2, 1, 2)), blu, (0, 0, 1.0), n.torso, col)
    n.neck = _empty(name + "_neck", (0, 0, 2.0), n.torso, col)
    if head == "classic":
        hm = classic_head(name + "_head")
    else:
        hm = rounded_box(name + "_head", (HEAD_W, HEAD_W, HEAD_H), r=0.13, seg=4)
    hz = 0.0 if head == "classic" else HEAD_H / 2
    n.head_mesh = _part(name + "_head_mesh", hm, yel, (0, 0, hz), n.neck, col)
    img = bpy.data.images.new(name + "_skin", 8, 8)
    img.pixels = [*(c / 255 for c in YELLOW), 1.0] * 64     # a generated byte image holds sRGB values
    n.face = bpy.data.objects.new(name + "_face", _plate(name + "_face", head))
    n.face.data.materials.append(face_material(img, name + "_face_mat", style="noob"))
    col.objects.link(n.face)
    n.face.parent = n.neck
    for e in NOOB_EYES:
        for k, v in NOOB_EYE_DEFAULTS.items():
            n.face[f"{e}_{k}"] = v
    for k, v in MOUTH_DEFAULTS.items():
        n.face[k] = v
    for k, v in NOOB_MOUTH.items():
        n.face[k] = v
    n.arms, n.legs = {}, {}
    for side, x in (("sl", -1.5), ("sr", 1.5)):
        piv = _empty(f"{name}_arm_{side}", (x, 0, 1.55), n.torso, col)   # the shoulder joint, near the top
        _part(f"{name}_arm_{side}_mesh", rounded_box(f"{name}_arm_{side}", (1, 1, 2)), yel, (0, 0, -0.55), piv, col)
        n.arms[side] = piv
    for side, x in (("sl", -0.5), ("sr", 0.5)):
        piv = _empty(f"{name}_leg_{side}", (x, 0, 0.0), n.pelvis, col)  # the hip joint
        _part(f"{name}_leg_{side}_mesh", rounded_box(f"{name}_leg_{side}", (1, 1, 2)), grn, (0, 0, -1.0), piv, col)
        n.legs[side] = piv
    return n


def _q(axis, deg):
    return Quaternion(Vector(axis), math.radians(deg))


def pose_noob(n, P):
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    n.root.rotation_mode = "XYZ"
    n.root.rotation_euler = (0, 0, math.radians(P.get("root_yaw", 0)))
    n.torso.rotation_quaternion = _q(Z, P.get("chest_twist", 0)) @ _q(Y, -P.get("chest_side", 0)) @ _q(X, P.get("chest_lean", 0))
    n.neck.rotation_quaternion = _q(Z, P.get("head_turn", 0)) @ _q(Y, -P.get("head_tilt", 0)) @ _q(X, P.get("head_nod", 0))
    for side, piv in n.arms.items():
        a = P.get("arm_" + side, {})
        s = 1 if side == "sl" else -1
        piv.rotation_quaternion = _q(Z, a.get("twist", 0) * s) @ _q(X, -a.get("fwd", 0)) @ _q(Y, a.get("out", 0) * s)
    for side, piv in n.legs.items():
        a = P.get("leg_" + side, {})
        s = 1 if side == "sl" else -1
        piv.rotation_quaternion = _q(X, -a.get("fwd", 0)) @ _q(Y, a.get("out", 0) * s)
