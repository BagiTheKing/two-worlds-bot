"""The world as it is in the finale's second half: what Null has left of
Minecraft is half an imperfect egg of land floating in the purple void (the
right, +x). The left half of the egg is the Noob's: he builds it out of Roblox
parts with his BTool, over the void (see roblox.py, ep10_p4_build.py), so this
module only makes the right half and leaves the outline for him. One old
Minecraft bridge reaches out from the right half's lip, part of the way across,
at the egg's near end (-y), where the chasm runs out to the rim.

    I = build_island(sc, assets)
    I.terrain, I.logs, I.leaves, I.plants, I.bridge (objects)
    I.height(x, y) -> the ground's top (or None in the void / the chasm)
    I.chasm(y) -> (left edge x, right edge x) of the chasm at y
    I.bridge_end -> where the old bridge stops (its broken end, on the deck)
"""
import math
import os
import random

import bpy
from mathutils import Vector

A = 58.0                    # the egg's half length (x)
B = 38.0                    # its half width (y), at the middle
BRIDGE_Y = -27.0             # at the egg's near end, where the chasm meets the rim


class Island:
    pass


def _noise():
    from world import Layout
    return Layout(11, {}).n


def build_island(sc, assets, seed=11):
    from world import bake_textures, material, voxel_mesh, crosses, tree, sun_object, sky, _DIRS
    rnd = random.Random(seed)
    N = _noise()
    T = bake_textures(assets)
    B_ = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    M = {k: bpy.data.materials.get("w_" + k) or material("w_" + k, p) for k, p in T.items() if k in (
        "grass_top", "grass_side", "dirt", "stone", "andesite", "coarse_dirt", "oak_log", "oak_log_top", "birch_log",
        "birch_log_top", "cherry_log", "cherry_log_top")}
    for k in ("tuff", "oak_planks", "stripped_oak_log", "deepslate"):
        M[k] = bpy.data.materials.get("w_" + k) or material("w_" + k, os.path.join(B_, k + ".png"))
    for k in ("oak_leaves", "birch_leaves", "cherry_leaves"):
        M[k] = bpy.data.materials.get("w_" + k) or material("w_" + k, T[k], alpha=True, rough=0.6, translucent=0.42)
    K = lambda t, s=None, b=None: {"top": M[t], "side": M[s or t], "bottom": M[b or s or t]}   # noqa: E731
    KINDS = {"grass": K("grass_top", "grass_side", "dirt"), "dirt": K("dirt"), "stone": K("stone"),
             "andesite": K("andesite"), "tuff": K("tuff"), "deep": K("deepslate"), "coarse": K("coarse_dirt"),
             "oak_log": K("oak_log_top", "oak_log"), "birch_log": K("birch_log_top", "birch_log"),
             "cherry_log": K("cherry_log_top", "cherry_log"), "oak_lv": K("oak_leaves"),
             "birch_lv": K("birch_leaves"), "cherry_lv": K("cherry_leaves"),
             "planks": K("oak_planks"), "post": K("oak_log_top", "stripped_oak_log")}
    I = Island()
    I.N = N

    def chasm(y):
        c = 1.6 * math.sin(y * 0.07) + 0.8 * math.sin(y * 0.19 + 1.0)
        w = 9.0 + 1.6 * N.fbm(y * 0.08 + 4.0, 2.0)
        return c - w / 2, c + w / 2

    def egg(x, y):
        """< 1 inside the egg's outline."""
        b = B * (1.0 + 0.16 * x / A)                         # wider on the Minecraft side: an egg, not an oval
        r = math.sqrt((x / A) ** 2 + (y / b) ** 2)
        return r + 0.07 * (N.fbm(x * 0.06 + 9.0, y * 0.06 + 3.0) - 0.5) + 0.03 * math.sin(math.atan2(y, x) * 7)

    def top(x, y):
        r = egg(x, y)
        h = 9.0 + 3.2 * N.fbm(x * 0.035 + 1.0, y * 0.035 + 7.0) + 1.4 * N.fbm(x * 0.11, y * 0.11)
        h -= 2.5 * max(0.0, r - 0.82) / 0.18                 # it slopes down at the rim
        return int(round(h))

    I.chasm = chasm
    I.egg = egg
    I.top = top
    cells = {}
    H = {}
    for x in range(int(-A) - 2, int(A) + 3):
        for y in range(int(-B * 1.25) - 2, int(B * 1.25) + 3):
            cx, cy = x + 0.5, y + 0.5
            r = egg(cx, cy)
            if r >= 1.0:
                continue
            l, rr = chasm(cy)
            if cx <= rr:                                      # the chasm, and the Noob's half: void for now
                continue
            h = top(cx, cy)
            H[(x, y)] = h
            d_ch = min(abs(cx - l), abs(cx - rr))             # how far from the chasm's cliff
            depth = 3 + 28 * (1 - r) ** 0.85 * (0.75 + 0.5 * N.fbm(cx * 0.09 + 5, cy * 0.09))
            depth = min(depth, 4 + 2.6 * d_ch)                # the cliffs fall away under the chasm's lips
            bot = h - int(depth)
            for z in range(bot, h):
                k = h - 1 - z
                if k == 0:
                    kind = "grass"
                elif k <= 3:
                    kind = "dirt"
                elif z - bot <= 1:
                    kind = "coarse" if rnd.random() < 0.5 else "deep"
                else:
                    v = N.fbm(cx * 0.2, z * 0.2 + cy * 0.1)
                    kind = "andesite" if v > 0.62 else "tuff" if v < 0.33 else "stone"
                cells[(x, y, z)] = kind
    I.H = H
    I.height = lambda x, y: H.get((int(math.floor(x)), int(math.floor(y))))
    # trees: groves on the Minecraft half, a few on the left (the Noob's build goes round them)
    tcells = {}
    for gx in range(int(-A) + 4, int(A) - 3, 5):
        for gy in range(int(-B * 1.2) + 3, int(B * 1.2) - 3, 5):
            x, y = gx + rnd.randint(-2, 2), gy + rnd.randint(-2, 2)
            h = H.get((x, y))
            if h is None or cells.get((x, y, h - 1)) != "grass" or egg(x, y) > 0.86:
                continue
            l, rr = chasm(y)
            if abs(x - l) < 4 or abs(x - rr) < 4 or abs(y - BRIDGE_Y) < 6 and x > rr - 2 and x < rr + 12:
                continue
            right = x > rr
            if not right:
                continue
            g = N.fbm(x * 0.07 + 40, y * 0.07 + 2)
            p = (0.75 if g > 0.5 else 0.15) if right else (0.22 if g > 0.55 else 0.03)
            if (not right) and -40 < x < -6 and abs(y + 2) < 9:      # the Noob's runway stays clear
                continue
            if rnd.random() > p:
                continue
            r_ = rnd.random()
            kind = "cherry" if (right and N.fbm(x * 0.05, y * 0.05 + 30) > 0.62) else (
                "big_oak" if r_ < 0.12 else "birch" if r_ < 0.32 else "oak")
            tree(tcells, x, y, h, kind, rnd)
    for k in list(tcells):
        if k in cells:
            del tcells[k]
    logs = {k: v for k, v in tcells.items() if not v.endswith("_lv")}
    leaves = {k: v for k, v in tcells.items() if v.endswith("_lv")}
    # the old bridge: oak planks from the right lip, two thirds of the way across, its end broken
    l0, r0 = chasm(BRIDGE_Y)
    deck_z = max(H.get((int(math.floor(r0)) + k, int(BRIDGE_Y)), 0) for k in (1, 2, 3)) or 9
    bridge = {}
    span = r0 - l0
    reach = r0 - 0.66 * span
    I.bridge_z = deck_z
    Y0 = int(BRIDGE_Y)
    for x in range(int(math.floor(reach)), int(math.ceil(r0)) + 3):
        for dy in (-1, 0, 1):
            broken = x < reach + 1.2 and (dy + x) % 2 == 0     # ragged where it stops
            if broken:
                continue
            bridge[(x, Y0 + dy, deck_z - 1)] = "planks"
    for x in range(int(math.ceil(r0)) - 1, int(math.ceil(r0)) + 3):
        for dy in (-1, 0, 1):
            for z in range(deck_z - 4, deck_z - 1):            # the abutment, down into the cliff
                bridge.setdefault((x, Y0 + dy, z), "planks" if z == deck_z - 2 else "post")
    I.bridge_end = Vector((reach + 1.0, BRIDGE_Y, deck_z))
    I.bridge_lip = Vector((l0, BRIDGE_Y, H.get((int(math.floor(l0)) - 1, int(BRIDGE_Y)), 9)))
    occ = dict(cells)
    col_top = lambda c: ((c[0], c[1]), float(H.get((c[0], c[1]), 0)))                    # noqa: E731
    I.terrain = voxel_mesh(sc, "island", cells, KINDS, group_of=col_top)
    I.logs = voxel_mesh(sc, "island_logs", logs, KINDS, occluders={**occ, **leaves},
                        group_of=lambda c: ((c[0], c[1]), float(H.get((c[0], c[1]), 0))))
    I.leaves = voxel_mesh(sc, "island_leaves", leaves, KINDS, occluders={**occ, **logs},
                          keep_leaf_faces=("oak_lv", "birch_lv", "cherry_lv"),
                          group_of=lambda c: ((c[0], c[1]), float(H.get((c[0], c[1]), 0))))
    I.bridge = voxel_mesh(sc, "old_bridge", bridge, KINDS, occluders=occ)
    # fences along both sides: thin oak posts and two rails (Minecraft's fence), broken off near the end
    I.fences = []

    def plank(name, c, size):
        bpy.ops.mesh.primitive_cube_add(size=1, location=c)
        ob = bpy.context.active_object
        ob.name = name
        ob.scale = size
        ob.data.materials.append(M["oak_planks"])
        I.fences.append(ob)
    x0, x1 = int(math.floor(reach)) + 2, int(math.ceil(r0)) + 2
    for side in (-1.62, 1.62):
        ys = BRIDGE_Y + 0.5 + side
        for x in range(x0, x1 + 1, 2):
            plank(f"fence_post_{x}_{side}", (x + 0.5, ys, deck_z + 0.5), (0.25, 0.25, 1.0))
        for zz in (deck_z + 0.38, deck_z + 0.8):
            plank(f"fence_rail_{zz}_{side}", ((x0 + x1) / 2 + 0.5, ys, zz), (x1 - x0, 0.12, 0.19))
    # plants: on the grass, thicker near the shots
    P = {k: bpy.data.materials.get("p_" + k) or material("p_" + k, T[k], alpha=True, rough=0.7, translucent=0.35)
         for k in ("short_grass", "fern", "poppy", "dandelion", "oxeye_daisy", "cornflower", "tall_grass_bottom",
                   "tall_grass_top")}
    items = []
    for (x, y), h in H.items():
        if cells.get((x, y, h - 1)) != "grass" or (x, y, h) in tcells or bridge.get((x, y, h - 1)):
            continue
        dens = 0.55 if (abs(y - BRIDGE_Y) < 14 or (-40 < x < -4 and abs(y) < 14)) else 0.22
        for _ in range(2):
            if rnd.random() > dens:
                continue
            px, py = x + rnd.random(), y + rnd.random()
            r_ = rnd.random()
            if r_ < 0.06:
                s = rnd.uniform(0.85, 1.05)
                items += [(px, py, h, s, P["tall_grass_bottom"]), (px, py, h + s * 0.98, s, P["tall_grass_top"])]
            elif r_ < 0.9:
                items.append((px, py, h, rnd.uniform(0.45, 0.75), P["fern"] if r_ < 0.14 else P["short_grass"]))
            else:
                items.append((px, py, h, rnd.uniform(0.5, 0.7), P[rnd.choice(("poppy", "dandelion", "oxeye_daisy",
                                                                               "cornflower"))]))
    I.plants = crosses(sc, "island_plants", items)
    # the void: a glowing purple depth far below (seen past the island's edges)
    bpy.ops.mesh.primitive_plane_add(size=40000, location=(0, 0, -260))
    v = bpy.context.active_object
    v.name = "void_floor"
    vm = bpy.data.materials.new("void_floor")
    vm.use_nodes = True
    nt = vm.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.0011, 0.0011, 1.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], gr.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    lin = lambda c: (*(((u / 255 + 0.055) / 1.055) ** 2.4 for u in c), 1)                  # noqa: E731
    ramp.color_ramp.elements[0].color = lin((26, 10, 52))
    ramp.color_ramp.elements[1].color = lin((150, 60, 190))
    nt.links.new(gr.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.4
    v.data.materials.append(vm)
    v.visible_shadow = False
    I.void = v
    # light and sky: the void's glow
    I.sun, I.to_sun = sun_object(sc, 120, 34, energy=3.6, color=(1.0, 0.86, 0.95))
    I.world = sky(sc, I.to_sun, fill=0.9)
    from world import World, set_sky
    W = World()
    W.world = I.world
    W.sky_dot = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "VECT_MATH" and n_.operation == "DOT_PRODUCT")
    W.sky_pow = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "MATH" and n_.operation == "POWER")
    W.sky_glow = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "MIX")
    W.sky_ramp = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "VALTORGB")
    W.sky_lit = next(n_ for n_ in W.world.node_tree.nodes if n_.type == "BACKGROUND" and not n_.inputs["Color"].is_linked)
    set_sky(W, {"glow": (236, 214, 255), "power": 5.0, "horizon": (244, 170, 226), "mid": (160, 112, 200),
                "zenith": (70, 52, 128), "fill": 0.6, "fill_col": (196, 176, 232)})
    I.W = W
    return I
