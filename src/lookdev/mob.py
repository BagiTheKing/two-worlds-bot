"""Minecraft mobs in the new look: a jointed block body skinned from the game's own 64x64 entity texture.

The boxes and their UVs follow the game's player-style layout (head 8x8x8, body 8x12x4, arms and legs
4x12x4), so the skin reads exactly as in the game; pixel-sharp sampling, the same soft world light as
the rest of the set. Used for the zombies of Episode 2 (and any player-shaped mob later).

    Z = build_mob(sc, "zombie_1", skin_png, height=2.0)
    pose_mob(Z, {"root_yaw": 0, "head_turn": 10, "arm_r": {"fwd": 90}, "arm_l": {"fwd": 85}, "leg_r": {"fwd": 20}})
    Z.root.location = (x, y, z)

The mob faces -y at yaw 0 (as the Noob and Steve). Its right side is -x.
"""
import math

import bpy
from mathutils import Quaternion, Vector

PX = 1.0 / 16.0           # one skin pixel, in blocks, at a 2-block-tall mob (scaled by `height`)

# texture origin (u, v) and box size (w, h, d) in pixels, the player-style 64x64 layout
PARTS = {
    "head":  ((0, 0), (8, 8, 8)),
    "body":  ((16, 16), (8, 12, 4)),
    "arm_r": ((40, 16), (4, 12, 4)),
    "arm_l": ((32, 48), (4, 12, 4)),
    "leg_r": ((0, 16), (4, 12, 4)),
    "leg_l": ((16, 48), (4, 12, 4)),
}
# where each part hangs from (its pivot, in pixels from the feet) and where its box sits from the pivot
PIVOT = {"head": (0, 0, 24), "body": (0, 0, 12), "arm_r": (-6, 0, 22), "arm_l": (6, 0, 22),
         "leg_r": (-2, 0, 12), "leg_l": (2, 0, 12)}
BOX_FROM_PIVOT = {"head": (0, 0, 4), "body": (0, 0, 6), "arm_r": (0, 0, -4), "arm_l": (0, 0, -4),
                  "leg_r": (0, 0, -6), "leg_l": (0, 0, -6)}


class Mob:
    pass


def _regions(u, v, w, h, d):
    """The six face rectangles (x0, y0, w, h) in skin pixels."""
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
            "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
            "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}


def _box_mesh(name, origin, size, tex_w=64, tex_h=64, inflate=0.0, mirror=False):
    (u, v), (w, h, d) = origin, size
    hx, hy, hz = w / 2 + inflate, d / 2 + inflate, h / 2 + inflate
    X0, X1, Y0, Y1, Z0, Z1 = -hx, hx, -hy, hy, -hz, hz
    # corners as seen from outside: bottom-left, bottom-right, top-right, top-left
    quads = {
        "front": [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y0, Z1), (X0, Y0, Z1)],
        "back": [(X1, Y1, Z0), (X0, Y1, Z0), (X0, Y1, Z1), (X1, Y1, Z1)],
        "right": [(X0, Y1, Z0), (X0, Y0, Z0), (X0, Y0, Z1), (X0, Y1, Z1)],      # the mob's right is -x
        "left": [(X1, Y0, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X1, Y0, Z1)],
        "top": [(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)],
        "bottom": [(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y0, Z0), (X0, Y0, Z0)],
    }
    reg = _regions(u, v, w, h, d)
    if mirror:                         # the game's old layout: a left limb is the right one mirrored
        reg["left"], reg["right"] = reg["right"], reg["left"]
    verts, faces, uvs = [], [], []
    for k, q in quads.items():
        i = len(verts)
        verts += [Vector(p) * PX for p in q]
        faces.append((i, i + 1, i + 2, i + 3))
        x0, y0, rw, rh = reg[k]
        # bottom-left, bottom-right, top-right, top-left in UV (V up, the image's y down)
        xa, xb = (x0 + rw, x0) if mirror else (x0, x0 + rw)
        uvs += [(xa / tex_w, 1 - (y0 + rh) / tex_h), (xb / tex_w, 1 - (y0 + rh) / tex_h),
                (xb / tex_w, 1 - y0 / tex_h), (xa / tex_w, 1 - y0 / tex_h)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], faces)
    uv = me.uv_layers.new()
    for li, loop in enumerate(me.loops):
        uv.data[li].uv = uvs[loop.vertex_index]
    me.update()
    return me


def _skin_material(name, skin_png):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(skin_png, check_existing=True)
    t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.78
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.25
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    return m


def build_mob(sc, name, skin_png, height=2.0, collection=None):
    """A player-shaped mob, 32 skin pixels tall scaled to `height` blocks."""
    col = collection or sc.collection
    mat = _skin_material(f"{name}_skin", skin_png)
    M = Mob()
    M.name = name
    M.root = bpy.data.objects.new(name, None)
    col.objects.link(M.root)
    M.root.scale = (height / 2.0,) * 3
    M.pivots, M.boxes = {}, {}
    from PIL import Image
    skin = Image.open(skin_png).convert("RGBA")
    tw, th = skin.size
    for part, (origin, size) in PARTS.items():
        mirror = False
        if part in ("arm_l", "leg_l"):
            u, v = origin
            w, h, d = size
            if th < 64 or skin.crop((u, v, u + 2 * (w + d), v + h + d)).getextrema()[3][1] == 0:
                origin, mirror = PARTS[part.replace("_l", "_r")][0], True
        pv = bpy.data.objects.new(f"{name}_{part}_pivot", None)
        col.objects.link(pv)
        pv.parent = M.root
        pv.location = Vector(PIVOT[part]) * PX
        pv.rotation_mode = "QUATERNION"
        me = _box_mesh(f"{name}_{part}", origin, size, tw, th, mirror=mirror)
        me.materials.append(mat)
        ob = bpy.data.objects.new(f"{name}_{part}", me)
        col.objects.link(ob)
        ob.parent = pv
        ob.location = Vector(BOX_FROM_PIVOT[part]) * PX
        bev = ob.modifiers.new("bevel", "BEVEL")                  # the soft block edge of the new look
        bev.width = 0.012
        bev.segments = 2
        bev.harden_normals = False
        M.pivots[part], M.boxes[part] = pv, ob
    M.root.rotation_mode = "XYZ"
    return M


def _q(axis, deg):
    return Quaternion(Vector(axis), math.radians(deg))


def pose_mob(M, P):
    """root_yaw, chest_twist, head_turn/nod/tilt, arm_r/l and leg_r/l {fwd, out} in degrees."""
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    M.root.rotation_euler = (0, 0, math.radians(P.get("root_yaw", 0)))
    M.pivots["body"].rotation_quaternion = _q(Z, P.get("chest_twist", 0)) @ _q(X, P.get("chest_lean", 0))
    M.pivots["head"].rotation_quaternion = _q(Z, P.get("head_turn", 0)) @ _q(Y, -P.get("head_tilt", 0)) \
        @ _q(X, P.get("head_nod", 0))
    for part in ("arm_r", "arm_l", "leg_r", "leg_l"):
        a = P.get(part, {})
        s = -1 if part.endswith("_r") else 1
        # fwd lifts the limb toward -y (the front); out swings it away from the body
        M.pivots[part].rotation_quaternion = _q(X, -a.get("fwd", 0)) @ _q(Y, -a.get("out", 0) * s)


def skin_path(assets, mob="zombie", kind="zombie"):
    import os
    return os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures",
                        "entity", mob, f"{kind}.png")
