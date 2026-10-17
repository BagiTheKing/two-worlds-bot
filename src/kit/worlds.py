"""
Locations. Each builder is deterministic for a given seed and returns
handles the effects need (chunks that can be erased, the bridge blocks, the
obstacle-course platforms...).

  seam          Steve's voxel land (west, x < 0) and a plastic obby land
                (east, x > 14) facing each other across a void chasm, joined
                by a bridge that is half wooden planks, half plastic bricks.
                Both lands float over the void, so erased chunks show nothing
                beneath.
  forest_valley the forest clearing of episode 2, built by the same code, so
                episode 1 can end on exactly episode 2's first shot.
"""

import math
import random

import bpy

from kit.blocks import box, empty, material, voxels
from kit.rigs import srgb

PLASTIC = dict(rough=0.32, spec=0.5, coat=0.3)
RAINBOW = [(232, 64, 64), (245, 150, 40), (245, 210, 50), (90, 200, 80),
           (60, 150, 240), (150, 90, 230), (240, 100, 190)]


def block_mats(tex):
    names = ("grass_top", "grass_side", "dirt", "stone", "log_side", "log_top",
             "leaves", "null", "planks")
    m = {k: material(k, tex=tex[k]) for k in names}
    m["missing"] = material("missing_flash", tex=tex["missing"], emit_tex=True, strength=4.0)
    return m


def palette(m):
    log = {"top": m["log_top"], "side": m["log_side"], "bottom": m["log_top"]}
    return {
        "grass": {"top": m["grass_top"], "side": m["grass_side"], "bottom": m["dirt"]},
        "dirt": {"side": m["dirt"]}, "stone": {"side": m["stone"]},
        "log": log, "leaves": {"side": m["leaves"]}, "planks": {"side": m["planks"]},
    }


def flash_copy(ob, mat):
    """A twin of `ob` sharing its mesh but drawn in `mat` (the missing-texture
    flash an erased chunk shows for two frames)."""
    twin = ob.copy()
    bpy.context.scene.collection.objects.link(twin)
    for slot in twin.material_slots:
        slot.link = "OBJECT"
        slot.material = mat
    twin.hide_render = True
    twin["is_flash"] = 1
    return twin


# ---------------------------------------------------------------------- seam

def _tree(cells, x, y, base, height, rnd):
    for z in range(height):
        cells[(x, y, base + z)] = "log"
    top = base + height
    for z in range(top - 3, top + 1):
        r = 2 if z < top - 1 else 1
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                corner = abs(dx) == r and abs(dy) == r
                if (x + dx, y + dy, z) in cells or (corner and (z == top or rnd.random() < 0.6)):
                    continue
                cells[(x + dx, y + dy, z)] = "leaves"
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        cells[(x + dx, y + dy, top + 1)] = "leaves"


def seam(tex, mats, seed=3):
    rnd = random.Random(seed)
    pal = palette(mats)
    out = {"erasable": [], "protected": [], "bridge": [], "obby": []}

    # --- west: Steve's land, an island of 8x8-column chunks
    cells_by_chunk = {}
    for x in range(-40, 0):
        for y in range(-24, 24):
            h = 0 if x >= -14 else max(0, int(round((-14 - x) * 0.22 + 1.4 * math.sin(y / 5.0))))
            depth = 6 + int(14 * math.exp(-((x + 14) ** 2 / 180 + y ** 2 / 260)))
            if x >= -4 and abs(y) <= 8:
                depth = 30 + int(4 * math.sin(y * 1.7))      # the cliff they hang from
            key = (x // 8, y // 8)
            ch = cells_by_chunk.setdefault(key, {})
            for z in range(-depth, h):
                ch[(x, y, z)] = "grass" if z == h - 1 else ("dirt" if z >= h - 4 else "stone")
    for _ in range(9):
        x, y = rnd.randint(-36, -7), rnd.randint(-21, 20)
        if abs(y) < 4:
            continue
        ch = cells_by_chunk[(x // 8, y // 8)]
        top = max(z for (cx, cy, z) in ch if (cx, cy) == (x, y)) + 1
        _tree(ch, x, y, top, rnd.randint(4, 6), rnd)
    for key, cells in cells_by_chunk.items():
        ob = voxels(f"west_{key[0]}_{key[1]}", cells, pal)
        cx, cy = key[0] * 8 + 4, key[1] * 8 + 4
        protected = key[0] >= -2 and -1 <= key[1] <= 0
        item = {"ob": ob, "flash": flash_copy(ob, mats["missing"]), "center": (cx, cy, 0)}
        (out["protected"] if protected else out["erasable"]).append(item)

    # --- east: the plastic obby land
    greens = [srgb(c) for c in ((108, 186, 78), (98, 176, 70), (163, 162, 165))]
    for i, x0 in enumerate(range(14, 62, 8)):
        for j, y0 in enumerate(range(-24, 24, 8)):
            g = empty(f"east_{i}_{j}", (x0 + 4, y0 + 4, 0))
            slab = box(f"east_slab_{i}_{j}", (8, 8, 4), (0, 0, -2),
                       {"default": material(f"east_mat_{i}_{j}", greens[(i + j) % 3], **PLASTIC)},
                       g, bevel=0.15)
            for k in range(rnd.randint(0, 2)):
                col = srgb(rnd.choice(RAINBOW))
                m = material(f"east_prop_{i}_{j}_{k}", col, **PLASTIC)
                px, py = rnd.uniform(-2.5, 2.5), rnd.uniform(-2.5, 2.5)
                if rnd.random() < 0.5:
                    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=rnd.uniform(1, 2),
                                                        depth=rnd.uniform(4, 12))
                    cyl = bpy.context.object
                    cyl.location = (px, py, cyl.dimensions.z / 2)
                    cyl.data.materials.append(m)
                    bpy.ops.object.shade_smooth()
                    cyl.parent = g
                else:
                    hgt = rnd.uniform(2, 5)
                    box(f"east_house_{i}_{j}_{k}", (rnd.uniform(2, 3.5), rnd.uniform(2, 3.5), hgt),
                        (px, py, hgt / 2), {"default": m}, g, bevel=0.08)
            flash = flash_copy(slab, mats["missing"])
            flash.parent = g
            out["erasable"].append({"ob": g, "flash": flash, "center": (x0 + 4, y0 + 4, 0)})

    # sky stairs: a decorative obby climbing into the sky, erased in groups
    for gi in range(4):
        g = empty(f"stairs_{gi}", (0, 0, 0))
        for k in range(6):
            n = gi * 6 + k
            col = srgb(RAINBOW[n % len(RAINBOW)])
            box(f"stair_{n}", (2.4, 1.2, 0.35), (30 + n * 1.3, 8 + n * 0.6, 14 + n * 0.75),
                {"default": material(f"stair_m_{n}", col, **PLASTIC)}, g, bevel=0.06)
        out["erasable"].append({"ob": g, "flash": None, "center": (38 + gi * 8, 12, 20)})

    # the obby path the fleeing avatars run along (high and far -> near the chasm)
    a, b = (52.0, -12.0, 12.0), (20.0, 3.0, 5.0)
    for k in range(12):
        u = k / 11
        c = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u)
        col = srgb(RAINBOW[k % len(RAINBOW)])
        p = box(f"obby_{k}", (2.2, 2.2, 0.4), (0, 0, -0.2),
                {"default": material(f"obby_m_{k}", col, **PLASTIC)}, bevel=0.06)
        p.location = c
        out["obby"].append({"ob": p, "top": c})

    # --- the bridge: x 0..13, three blocks wide, planks then plastic bricks
    for x in range(0, 14):
        if x < 7:
            ob = voxels(f"bridge_{x}", {(0, yy, -1): "planks" for yy in (-1, 0, 1)}, pal,
                        location=(x, 0, 0))
        else:
            col = srgb(RAINBOW[x % len(RAINBOW)])
            m = material(f"brick_{x}", col, **PLASTIC)
            ob = box(f"bridge_{x}", (1, 3, 1), (0.5, 0.5, -0.5), {"default": m}, bevel=0.04)
            ob.location = (x, 0, 0)
            for yy in (-0.75, 0.0, 0.75, 1.5):
                bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.16, depth=0.12,
                                                    location=(0.5, yy + 0.25, 0.06))
                stud = bpy.context.object
                stud.data.materials.append(m)
                stud.parent = ob
        out["bridge"].append(ob)

    # --- the sign, on the bridge's south edge, facing the way they come
    wood = material("sign_wood", tex=tex["planks"])
    sign = empty("sign", (3.2, -1.05, 0))
    box("sign_post", (0.12, 0.12, 1.3), (0, 0, 0.65), {"default": wood}, sign)
    box("sign_board", (0.08, 1.5, 0.75), (0, 0, 1.55), {"default": wood}, sign)
    cu = bpy.data.curves.new("sign_text", "FONT")
    cu.body = "BRIDGE UNDER\nMAINTENANCE"
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.size = 0.2
    txt = bpy.data.objects.new("sign_text", cu)
    bpy.context.scene.collection.objects.link(txt)
    txt.data.materials.append(material("sign_ink", (0.02, 0.02, 0.02), rough=0.8))
    txt.parent = sign
    txt.location = (-0.05, 0, 1.55)
    txt.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
    out["sign"] = sign
    return out


def void_debris(tex, mats, n=40, seed=5, frames=1000):
    """Slowly tumbling blocks below the islands, for depth in the void."""
    rnd = random.Random(seed)
    choices = [mats["grass_side"], mats["dirt"], mats["stone"], mats["null"],
               material("debris_plastic", srgb((60, 150, 240)), **PLASTIC)]
    for i in range(n):
        s = rnd.uniform(0.6, 2.2)
        ob = box(f"debris_{i}", (s, s, s), (0, 0, 0), {"default": rnd.choice(choices)})
        ob.location = (rnd.uniform(-30, 70), rnd.uniform(-30, 30), rnd.uniform(-70, -12))
        spin = [rnd.uniform(-0.6, 0.6) for _ in range(3)]
        for f in (1, frames):
            ob.rotation_euler = tuple(w * f / 24 for w in spin)
            ob.location.z += 0.0 if f == 1 else rnd.uniform(-1.5, 1.5)
            ob.keyframe_insert("rotation_euler", frame=f)
            ob.keyframe_insert("location", frame=f)


# -------------------------------------------------------------- forest valley

def forest_valley(tex_dir, origin):
    """Episode 2's clearing, built by episode 2's own code and moved to
    `origin`, so the two episodes share an identical shot."""
    import scene_poc as poc
    before = set(bpy.data.objects)
    import os
    tex_dir = os.path.abspath(tex_dir)
    tex = {os.path.splitext(n)[0]: os.path.join(tex_dir, n) for n in os.listdir(tex_dir)}
    mats = {k: material("fv_" + k, tex=v) for k, v in tex.items()
            if k in ("grass_top", "grass_side", "dirt", "stone", "log_side",
                     "log_top", "leaves", "null")}
    rnd = random.Random(11)
    heights = poc.terrain(mats, rnd)
    poc.forest(mats, heights, rnd)
    poc.hero_tree(mats, rnd)
    poc.clouds(rnd)
    root = empty("forest_valley", origin)
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None and ob is not root:
            ob.parent = root
    return root
