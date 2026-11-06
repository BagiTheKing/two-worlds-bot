"""Props as the reference shows them: Minecraft item sprites (16 x 16) made
into thin 3D pixel slabs, each opaque pixel a little block of its own colour,
the slab one sprite-pixel thick with slightly darker side edges (as the game's
item models look); held in the fist, handle in the hand, the tool pointing
forward from the hand (so when the arm comes up, the tool rises with it);
and blocks held small in front of the hand.

    item = sprite_item("iron_pickaxe", TEXDIR)            # an object, origin at the grip
    hold(arm, item, "sl")                                 # in the screen-left hand (his right)
    blk = block_item({"default": tex}, size=0.32); hold(arm, blk, "sr", kind="block")
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

WRIST = {"sl": "R.wrist", "sr": "L.wrist"}
GRIP_PX = {"default": (3.0, 3.0), "bow": (7.5, 7.5), "torch": (8.0, 2.0)}   # where the hand holds the sprite


def _lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c)


def item_material(name="item_mat"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = "item_col"
    nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Specular IOR Level"].default_value = 0.35
    return m


def sprite_item(name, texdir, px=0.072, depth=1.0, grip=None):
    """A 3D item from textures/item/<name>.png. px = size of one sprite pixel
    (rig units; Steve's skin pixel is 0.1). The object's origin is the grip."""
    from PIL import Image
    im = Image.open(os.path.join(texdir, name + ".png")).convert("RGBA")
    w, h = im.size
    gx, gy = grip or GRIP_PX.get(name.split("_")[-1], GRIP_PX["default"])
    on = {(x, y): im.getpixel((x, h - 1 - y)) for x in range(w) for y in range(h) if im.getpixel((x, h - 1 - y))[3] > 128}
    bm = bmesh.new()
    col = bm.loops.layers.float_color.new("item_col")
    d = depth * px

    def quad(pts, c):
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        for loop in f.loops:
            loop[col] = (*c, 1.0)

    for (x, y), rgba in on.items():
        c = _lin(rgba[:3])
        side = tuple(v * 0.72 for v in c)                  # the slab's edges a touch darker
        x0, x1, y0, y1 = (x - gx) * px, (x + 1 - gx) * px, (y - gy) * px, (y + 1 - gy) * px
        # the sprite lies in the item's X (right) / Z (up) plane, thickness along Y
        quad([(x0, -d / 2, y0), (x1, -d / 2, y0), (x1, -d / 2, y1), (x0, -d / 2, y1)], c)
        quad([(x0, d / 2, y1), (x1, d / 2, y1), (x1, d / 2, y0), (x0, d / 2, y0)], c)
        if (x - 1, y) not in on:
            quad([(x0, d / 2, y0), (x0, -d / 2, y0), (x0, -d / 2, y1), (x0, d / 2, y1)], side)
        if (x + 1, y) not in on:
            quad([(x1, -d / 2, y0), (x1, d / 2, y0), (x1, d / 2, y1), (x1, -d / 2, y1)], side)
        if (x, y - 1) not in on:
            quad([(x0, -d / 2, y0), (x0, d / 2, y0), (x1, d / 2, y0), (x1, -d / 2, y0)], side)
        if (x, y + 1) not in on:
            quad([(x0, d / 2, y1), (x0, -d / 2, y1), (x1, -d / 2, y1), (x1, d / 2, y1)], side)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me = bpy.data.meshes.new("item_" + name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(item_material())
    ob = bpy.data.objects.new("item_" + name, me)
    return ob


def block_item(mats, size=0.32, name="held_block"):
    """A small block (mats: {"top": m, "bottom": m, "default": m}), origin at its centre."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    uv = bm.loops.layers.uv.new()
    me = bpy.data.meshes.new(name)
    order = ["top", "bottom", "default"]
    for m in order:
        me.materials.append(mats.get(m, mats["default"]))
    for f in bm.faces:
        n = f.normal
        f.material_index = 0 if n.z > 0.5 else (1 if n.z < -0.5 else 2)
        for loop, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uv].uv = c
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


def hold(arm, ob, side, kind="tool", up=25.0, roll=0.0, reach=0.0, face=50.0, collection=None):
    """Put `ob` in a hand. At the rig's rest (arm hanging, facing -y) a tool
    sticks out forward from the fist, tilted `up` degrees, its flat side facing
    sideways (as items are held in the game); a block sits just in front of the fist.
    `reach` moves it further along the hand; `face` turns its flat side toward
    the front (degrees about the handle-to-head line). Then it follows the wrist bone."""
    bone = arm.data.bones[WRIST[side]]
    head, tail = arm.matrix_world @ bone.head_local, arm.matrix_world @ bone.tail_local
    down = (tail - head).normalized()
    fist = tail + down * (0.04 + reach)                    # the fist, near the end of the hand
    if kind == "block":
        rot = Matrix.Rotation(math.radians(18), 4, "Z")
        world = Matrix.Translation(fist + Vector((0, -0.2, 0.02))) @ rot
    else:
        # item axes: X (sprite right), Z (sprite up), Y (thickness). The sprite's diagonal
        # (handle -> head) is X+Z; point it forward (-y) and up.
        a = math.radians(up)
        diag = Vector((0, -math.cos(a), math.sin(a)))
        nrm = Vector((1, 0, 0)) if side == "sr" else Vector((-1, 0, 0))
        r45 = Matrix.Rotation(math.radians(45), 3, nrm)
        xa = (r45.inverted() @ diag).normalized()
        za = (r45 @ diag).normalized()
        ya = za.cross(xa).normalized()
        m3 = Matrix((xa, ya, za)).transposed()
        # turn the flat side partly toward the front, so the item reads from the camera
        m3 = Matrix.Rotation(math.radians(face if side == "sl" else -face), 3, diag) @ m3
        world = Matrix.Translation(fist) @ (m3.to_4x4() @ Matrix.Rotation(math.radians(roll), 4, "Z"))
    for col in (collection or list(arm.users_collection)):
        if ob.name not in col.objects:
            col.objects.link(ob)
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = WRIST[side]
    ob.matrix_parent_inverse = (arm.matrix_world @ bone.matrix_local @ Matrix.Translation((0, bone.length, 0))).inverted()
    ob.matrix_basis = world
    return ob


GRIPS = {                       # hold(..., **GRIPS[name]): how the hand holds the tool
    "hanging": {"up": 25, "face": 60},      # arm at the side: the tool points forward from the fist
    "raised": {"up": -55, "face": 80},      # forearm raised: the tool stands upright beside the head
    "swing": {"up": 30, "face": 50},        # arm up over the head, about to strike
}


def dropped_item(ob, loc, f0, f1, fps=24, scale=0.45, ground=0.0):
    """A dropped item as in the game and the reference: small, floating a little
    above the ground, bobbing gently and turning slowly, from frame f0 to f1."""
    ob.parent = None
    ob.scale = (scale, scale, scale)
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / fps
        ob.location = (loc[0], loc[1], ground + 0.25 + 0.06 * math.sin(t * 3.2))
        ob.rotation_euler = (0, 0, t * 1.6)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
    return ob
