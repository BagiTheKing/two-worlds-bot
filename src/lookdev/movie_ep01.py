"""The movie, chapter 1: Episode 1 "The Noob Who Punched a Tree", remade in the new look, in 16:9.

It picks up where chapter 0 leaves the Noob: in the restored meadow (movie_ep00.build_forest),
by the near oak, right after "Whoa. Where am I?" (story/movie/ep01_shots.md). The movie's own,
longer timing comes from its sound preview (episodes/movie_ep01_the_tree.json).

  1 looking round   2 the walk   3 "Okay. A tree. One punch. Watch this."   4 the punch
  5 Steve: "It's a tree. You need a tool."   6 the wide: "I'm a Roblox player."   7 the flurry
  8 the break   9 floating: "...Why is it floating?" / "That's normal."   10 the sky cracks
  11 the eye: "...That's not."

    python src/lookdev/movie_ep01.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080]
        [--samples 32] [--times 0.5,3.6]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import movie_ep00 as M                                                # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402

B = M.B                                    # the timeline's beats (shared with chapter 0's helpers)
TREE = (2.3, 0.9)                          # the oak he punches: chapter 0's near trunk (M.NEAR_OAK)
NOOB0 = Vector((0.1, -1.2, 0.0))           # where chapter 0 leaves him
PUNCH_AT = Vector((1.25, 0.5, 0.0))        # where he stands to punch (west of the trunk, facing +x): the fist lands
STAND_BACK = Vector((-0.75, 0.0, 0.0))     # a step back from it while talking, so his arms stay off the bark
STEVE_AT = Vector((-1.8, 3.6, 0.0))        # Steve, a few blocks from the tree, pickaxe in hand
STEVE2 = Vector((-0.8, 2.6, 0.0))          # after the break he comes a few steps closer to look at the tree
NOOB_BACK = Vector((-0.4, -0.6, 0.0))      # the Noob steps back from the log to look up at it
CRACK = Vector((-14.0, -28.0, 40.0))         # the crack in the sky (south-west, high, clear of the crowns), from the tree foot


TOOL_ARM = ((80, 70), 20, (0, 0))           # "You need a tool.": Steve's arm (fwd, out, elbow), the pick head held up clear


def b(name, i=0):
    return B[name][i]


def noob_stand(E, t):
    """Where the Noob stands from the walk to the flurry: a step back from the trunk while he talks, a step in to
    punch (with the turn before the punch and before the flurry), a step back after the one punch."""
    k = 1.0 - ss(b("punch") - 0.45, b("punch") - 0.05, t)                    # in for the punch
    if t >= b("punch") + 0.5:
        k = ss(b("punch") + 0.5, b("punch") + 1.0, t) * (1.0 - ss(b("flurry") - 0.4, b("flurry") - 0.05, t))
    p = E.punch_at + STAND_BACK * k
    p.z = E.ground(p.x, p.y)
    return p, k


def _step(pz, t, k0, k1):
    """Feet stepping while the stand point moves (k0..k1 the window), so he never slides."""
    if k0 < t < k1:
        ph = (t - k0) / (k1 - k0) * 2 * math.pi
        pz["leg_sl"] = {"fwd": 22 * math.sin(ph)}
        pz["leg_sr"] = {"fwd": -22 * math.sin(ph)}
    return pz


def steve_pos(E, t):
    u = ss(b("break") + 0.3, b("noob_float"), t)
    p = STEVE_AT.lerp(STEVE2, u)
    return Vector((p.x, p.y, E.ground(p.x, p.y)))


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    # grass cleared where they stand and where the low cameras look past (nothing in front of a face)
    clear = [(STEVE_AT.x, STEVE_AT.y, 1.3), (PUNCH_AT.x, PUNCH_AT.y, 1.2), (NOOB0.x, NOOB0.y, 1.2),
             (0.5, -5.6, 2.2), (-0.4, -4.8, 1.6), (0.8, -1.8, 1.4), (-4.7, 2.5, 1.8), (4.2, -3.7, 1.8), (2.0, -1.0, 1.6), (3.9, -4.7, 1.8),
             (0.3, 5.0, 1.6), (-3.3, 0.3, 1.8), (-0.5, 4.3, 1.4), (-4.4, 8.2, 2.0), (0.7, -4.3, 1.8), (0.1, 0.05, 1.3), (-0.4, -0.6, 1.3), (-0.8, 2.6, 1.3), (3.0, -4.4, 1.8),
             (1.6, -2.0, 1.6)]
    E = M.build_forest(tl, tex_dir, assets, res, samples, drop_trees=[(M.NEAR_OAK[0], M.NEAR_OAK[1])], clear=clear)
    E.tl = tl
    g = E.ground
    E.noob0 = NOOB0 + Vector((0, 0, g(NOOB0.x, NOOB0.y)))
    E.punch_at = PUNCH_AT + Vector((0, 0, g(PUNCH_AT.x, PUNCH_AT.y)))
    E.steve_at = STEVE_AT + Vector((0, 0, g(STEVE_AT.x, STEVE_AT.y)))
    _oak(E, assets)
    _decal(E, assets)
    _bits(E)
    _crack(E)
    from props import sprite_item, hold
    pk = sprite_item("iron_pickaxe", os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets",
                                                  "minecraft", "textures", "item"), px=0.072)
    hold(E.S.arm, pk, "sr", up=25, face=60, collection=[E.S.rig])
    E.P.root.location = (0, 0, -500)                   # the portal: closed since chapter 0
    return E


def _materials(E, assets):
    from world import material
    T = E.W.textures if hasattr(E.W, "textures") else None
    if T is None:
        from world import bake_textures
        T = bake_textures(assets)
    M_ = {k: bpy.data.materials.get("p_" + k) or material("p_" + k, T[k]) for k in ("oak_log", "oak_log_top")}
    M_["oak_leaves"] = bpy.data.materials.get("p_oak_leaves") or material("p_oak_leaves", T["oak_leaves"], alpha=True,
                                                                           rough=0.6, translucent=0.42)
    return M_


def _oak(E, assets):
    """The oak: its lowest log a block of its own (it breaks), everything above it one piece (it floats)."""
    from world import voxel_mesh, tree
    M_ = _materials(E, assets)
    K = {"oak_log": {"top": M_["oak_log_top"], "side": M_["oak_log"], "bottom": M_["oak_log_top"]},
         "oak_lv": {"top": M_["oak_leaves"], "side": M_["oak_leaves"], "bottom": M_["oak_leaves"]}}
    gx, gy = int(math.floor(TREE[0])), int(math.floor(TREE[1]))
    gz = int(round(E.ground(gx + 0.5, gy + 0.5)))
    cells = {}
    tree(cells, gx, gy, gz, "oak", random.Random(31))
    base = {(gx, gy, gz): "oak_log"}
    logs = {k: v for k, v in cells.items() if not v.endswith("_lv") and k not in base}
    leaves = {k: v for k, v in cells.items() if v.endswith("_lv")}
    E.log0 = voxel_mesh(E.sc, "punch_log", base, K)
    E.upper = [voxel_mesh(E.sc, "punch_oak_logs", logs, K),
               voxel_mesh(E.sc, "punch_oak_leaves", leaves, K, keep_leaf_faces=("oak_lv",))]
    E.tree_foot = Vector((gx + 0.5, gy + 0.5, gz))


def _decal(E, assets):
    """Minecraft's breaking stages on the lowest log: a shell a hair outside the block, one image per stage."""
    tex = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    E.stages = []
    for k in range(10):
        m = bpy.data.materials.new(f"destroy_{k}")
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(tex, f"destroy_stage_{k}.png"))
        t.interpolation = "Closest"
        bsdf.inputs["Base Color"].default_value = (0.02, 0.015, 0.01, 1)
        nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
        E.stages.append(m)
    bpy.ops.mesh.primitive_cube_add(size=1.006, location=E.tree_foot + Vector((0, 0, 0.5)))
    sh = bpy.context.active_object
    sh.name = "destroy_shell"
    sh.data.materials.append(E.stages[0])
    uv = sh.data.uv_layers.active.data
    for poly in sh.data.polygons:                     # each face: the whole 16x16 stage image
        for j, li in enumerate(poly.loop_indices):
            uv[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[j % 4]
    E.shell = sh


def _bits(E):
    """The log's bits when it breaks: small blocks in the log's own material, flung out, falling, bouncing."""
    rng = random.Random(5)
    E.bits = []
    mat = E.log0.data.materials[0] if E.log0.data.materials else None
    for k in range(14):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"log_bit_{k}"
        s = rng.uniform(0.14, 0.26)
        ob.scale = (s, s, s)
        if mat:
            ob.data.materials.append(mat)
        a = rng.uniform(0, 2 * math.pi)
        v = Vector((math.cos(a) * rng.uniform(1.2, 2.6), math.sin(a) * rng.uniform(1.2, 2.6), rng.uniform(2.0, 3.6)))
        o = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0.2, 0.8)))
        w = Vector((rng.uniform(-9, 9), rng.uniform(-9, 9), rng.uniform(-9, 9)))
        E.bits.append((ob, o, v, w, s))


def _crack(E):
    """The crack across the sky: a jagged tear showing the missing-texture checker behind, glowing white edges,
    and (from "...That's not.") the eye looking out of it."""
    from PIL import Image, ImageDraw, ImageFilter
    W_, H_ = 2048, 640
    rng = random.Random(9)
    pts_top, pts_bot = [], []
    n = 22
    for i in range(n + 1):
        x = 40 + (W_ - 80) * i / n
        mid = H_ / 2 + rng.uniform(-70, 70)
        half = 18 + 170 * math.sin(math.pi * i / n) ** 1.5 * rng.uniform(0.55, 1.0)
        pts_top.append((x, mid - half))
        pts_bot.append((x, mid + half))
    poly = pts_top + pts_bot[::-1]
    mask = Image.new("L", (W_, H_), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    chk = Image.new("RGBA", (W_, H_))
    d = ImageDraw.Draw(chk)
    c = 48
    for y in range(0, H_, c):
        for x in range(0, W_, c):
            d.rectangle((x, y, x + c, y + c), fill=(255, 20, 220, 255) if (x // c + y // c) % 2 else (8, 0, 12, 255))
    glow = mask.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(10))
    edge = Image.new("RGBA", (W_, H_), (255, 255, 255, 0))
    edge.putalpha(glow)
    base = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    base = Image.alpha_composite(base, edge)
    inside = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    inside.paste(chk, (0, 0), mask)
    base = Image.alpha_composite(base, inside)
    paths = {}
    path = os.path.join(bpy.app.tempdir or "/tmp", "ep01_crack.png")
    base.save(path)
    paths["crack"] = path
    eye = base.copy()
    de = ImageDraw.Draw(eye)
    cx, cy = W_ // 2, H_ // 2
    de.ellipse((cx - 210, cy - 120, cx + 210, cy + 120), fill=(196, 196, 204, 255), outline=(255, 255, 255, 255), width=8)
    de.ellipse((cx - 95, cy - 95, cx + 95, cy + 95), fill=(60, 58, 70, 255))
    de.rectangle((cx - 20, cy - 92, cx + 20, cy + 92), fill=(255, 20, 220, 255))
    path = os.path.join(bpy.app.tempdir or "/tmp", "ep01_crack_eye.png")
    eye.save(path)
    paths["eye"] = path
    E.crack_mats = {}
    for k, pth in paths.items():
        m = bpy.data.materials.new(f"crack_{k}")
        m.use_nodes = True
        nt = m.node_tree
        for n_ in list(nt.nodes):
            nt.nodes.remove(n_)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(pth)
        t.interpolation = "Closest"
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 2.2
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(t.outputs["Color"], em.inputs["Color"])
        nt.links.new(t.outputs["Alpha"], mx.inputs["Fac"])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        E.crack_mats[k] = m
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = "sky_crack"
    ob.data.materials.append(E.crack_mats["crack"])
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    E.crack = ob
    E.crack_at = E.tree_foot + CRACK
    lt = bpy.data.objects.new("crack_light", bpy.data.lights.new("crack_light", "SUN"))
    E.sc.collection.objects.link(lt)
    lt.data.color = (0.75, 0.2, 1.0)                  # the tear's magenta
    lt.data.energy = 0.0
    lt.rotation_euler = (-CRACK).to_track_quat("-Z", "Y").to_euler()
    E.crack_light = lt


# ------------------------------------------------------------------ the shots
SHOTS = [("look", "look_around"), ("walk", "walk_to_tree"), ("tree", "noob_tree"), ("punch", "punch"),
         ("steve", "steve_tool"), ("wide", "noob_roblox"), ("flurry", "flurry"), ("break", "break"),
         ("float", "noob_float"), ("crack", "crack"), ("crackwide", ("crack", 1.2)), ("eye", "steve_not")]


def shot_bounds():
    return [(n, b(r) if isinstance(r, str) else b(r[0]) + r[1]) for n, r in SHOTS]


def which(t):
    bs = shot_bounds()
    for k, (n, t0) in enumerate(bs):
        t1 = bs[k + 1][1] if k + 1 < len(bs) else 1e9
        if t < t1:
            return n, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


def _flurry_hits():
    a, c = b("flurry"), b("flurry", 1) - 0.05
    out, h = [], a + 0.12
    while h < c:
        out.append(h)
        h += 0.19
    return out


# ------------------------------------------------------------------ per frame
def apply(E, t):
    from ep09_new import NF, SF
    from world import set_sky
    name, t0, t1 = which(t)
    # the sky: day, darkening a little as the crack opens
    dk = ss(b("crack"), b("crack") + 0.6, t)
    look = M.mix_look({"glow": (255, 240, 220), "power": 30.0, "horizon": (220, 232, 250), "mid": (140, 186, 250),
                       "zenith": (52, 120, 236), "fill": 1.1, "fill_col": (186, 206, 240)},
                      {"glow": (236, 190, 230), "power": 8.0, "horizon": (200, 150, 200), "mid": (110, 90, 170),
                       "zenith": (44, 34, 96), "fill": 0.8, "fill_col": (176, 150, 220)}, dk)
    set_sky(E.W, look)
    E.sc.view_settings.exposure = lerp(-0.05, -0.55, dk)
    if not hasattr(E, "sun0"):
        E.sun0 = E.W.sun.data.energy
    E.W.sun.data.energy = lerp(E.sun0, 0.25 * E.sun0, dk)
    # the oak, the break, the bits
    broken = t >= b("break") + 0.05
    E.log0.hide_render = broken
    hits = _flurry_hits()
    if b("flurry") <= t < b("break") + 0.05:
        k = sum(1 for h in hits if h <= t)
        stage = min(9, int(round(9 * k / max(1, len(hits)))))
        E.shell.hide_render = broken or k == 0
        E.shell.data.materials[0] = E.stages[stage]
    elif b("punch") + 0.18 <= t < b("punch") + 0.9:
        E.shell.hide_render = False                      # one punch: the first crack, then it heals
        E.shell.data.materials[0] = E.stages[0]
    else:
        E.shell.hide_render = True
    tb = b("break") + 0.05
    for ob, o, v, w, s in E.bits:
        if t < tb:
            ob.location = (0, 0, -300)
            continue
        dt = t - tb
        p = E.tree_foot + Vector((0, 0, 0.5)) + o + v * dt + Vector((0, 0, -0.5 * 9.81 * dt * dt))
        floor = E.ground(p.x, p.y) + s / 2
        if p.z < floor:                                   # landed: a small bounce, then still
            tl_ = (v.z + math.sqrt(v.z ** 2 + 2 * 9.81 * max(0.0, (E.tree_foot.z + 0.5 + o.z) - floor))) / 9.81
            land = E.tree_foot + Vector((0, 0, 0.5)) + o + v * tl_
            u = dt - tl_
            hop = max(0.0, 0.8 * u - 0.5 * 9.81 * u * u)
            p = Vector((land.x + v.x * 0.15 * min(u, 0.3), land.y + v.y * 0.15 * min(u, 0.3), floor + hop))
            ob.rotation_euler = tuple(w * tl_)
        else:
            ob.rotation_euler = tuple(w * dt)
        ob.location = p
    # the crack: opens across the sky; the eye from "...That's not."
    E.crack_light.data.energy = 1.7 * ss(b("crack") + 0.15, b("crack") + 0.5, t) * (1 + 0.25 * math.sin(t * 23))
    E.crack.hide_render = t < b("crack") + 0.15
    if not E.crack.hide_render:
        u = ss(b("crack") + 0.15, b("crack") + 0.55, t)
        to_cam = (E.cam.location - E.crack_at)
        to_cam.z *= 0.3
        E.crack.location = E.crack_at
        E.crack.rotation_mode = "QUATERNION"
        E.crack.rotation_quaternion = to_cam.to_track_quat("Z", "Y") @ Quaternion((0, 0, 1), math.radians(-14))
        E.crack.scale = (52.0 * max(u, 0.02), 52.0 * 640 / 2048 * (0.25 + 0.75 * u), 1)
        E.crack.data.materials[0] = E.crack_mats["eye" if t >= b("steve_not") else "crack"]
    cast(E, t, name, NF, SF)
    camera(E, t, name, t0, t1)


def cast(E, t, shot, NF, SF):
    g = E.ground
    # ------------------------------------------------ the Noob
    if t < b("walk_to_tree"):
        # looking round where chapter 0 left him: right, left, then up; delighted
        u = t - b("look_around")
        turn = 34 * math.sin(u * 1.6) * (1 - ss(1.9, 2.6, u))
        nod = -16 * ss(1.9, 2.5, u)
        pz = {"head_turn": turn, "head_nod": nod, "arm_sl": {"out": 8}, "arm_sr": {"out": 8}}
        yaw = 8 * math.sin(u * 0.8) + 20 * ss(2.4, 3.0, u)
        M.set_noob(E, E.noob0, yaw, pz, NF["happy"], t)
    elif t < b("noob_tree"):
        # the walk to the tree
        s = ss(b("walk_to_tree"), b("walk_to_tree", 1), t)
        stand = E.punch_at + STAND_BACK
        p = E.noob0.lerp(stand, s)
        p.z = g(p.x, p.y)
        d = stand - E.noob0
        ph = (t - b("walk_to_tree")) * 1.25 * 2 * math.pi
        sw = math.sin(ph) * (1 - ss(b("walk_to_tree", 1) - 0.25, b("walk_to_tree", 1), t))
        pz = {"head_turn": 6, "head_nod": -4, "arm_sl": {"fwd": -26 * sw}, "arm_sr": {"fwd": 26 * sw},
              "leg_sl": {"fwd": 28 * sw}, "leg_sr": {"fwd": -28 * sw}}
        yaw = lerp(math.degrees(math.atan2(d.x, -d.y)), 20.0, ss(b("walk_to_tree", 1) - 0.3, b("walk_to_tree", 1), t))
        M.set_noob(E, p + Vector((0, 0, 0.03 * abs(sw))), yaw, pz, NF["happy"], t)
    elif t < b("punch"):
        # at the tree, showing off to us; he turns to the trunk at the end
        turn_t = b("punch") - 0.45
        yaw = lerp(20.0, 90.0, ss(turn_t, b("punch"), t))
        pz = {"head_turn": -10 * (1 - ss(turn_t, b("punch"), t)), "chest_lean": -3, "arm_sr": {"fwd": 30, "out": 10},
              "arm_sl": {"out": 14}}
        face = dict(NF["happy"])
        face.update({"eL_to": -0.3, "eL_tm": -0.3})                 # cocky: one eye squinting
        _step(pz, t, b("punch") - 0.45, b("punch") - 0.05)
        M.set_noob(E, noob_stand(E, t)[0], yaw, pz, face, t)
    elif t < b("steve_tool"):
        # one punch: wind up, hit (punch+0.18), pull back, the arm hangs
        u = t - b("punch")
        jab = math.exp(-((u - 0.18) / 0.07) ** 2)
        wind = math.exp(-((u - 0.06) / 0.06) ** 2)
        pz = {"chest_twist": -12 * wind + 10 * jab, "arm_sr": {"fwd": 90 * jab + 40 * (1 - ss(0.2, 0.8, u)), "out": 4},
              "arm_sl": {"fwd": 20, "out": 10}, "chest_lean": 6 * jab}
        _step(pz, t, b("punch") + 0.5, b("punch") + 1.0)
        M.set_noob(E, noob_stand(E, t)[0], 90.0, pz, NF["happy"] if u < 0.6 else NF["confused"], t)
    elif t < b("noob_roblox"):
        # Steve speaks; the Noob looks to him, unimpressed by the tool talk
        d = E.steve_at - E.punch_at
        yaw = math.degrees(math.atan2(d.x, -d.y)) * ss(b("steve_tool"), b("steve_tool") + 0.5, t) + \
            90 * (1 - ss(b("steve_tool"), b("steve_tool") + 0.5, t))
        pz = _step({"head_turn": 0, "arm_sl": {"out": 10}, "arm_sr": {"out": 10}}, t, b("punch") + 0.5, b("punch") + 1.0)
        M.set_noob(E, noob_stand(E, t)[0], yaw, pz, NF["neutral"], t)
    elif t < b("flurry"):
        # "I don't need tools. I'm a Roblox player." — he turns to Steve and spreads his arms
        d = E.steve_at - E.punch_at
        k = ss(b("noob_roblox") + 1.2, b("noob_roblox") + 1.6, t)
        pz = {"arm_sl": {"out": 20 + 70 * k, "fwd": 10}, "arm_sr": {"out": 20 + 70 * k, "fwd": 10}, "chest_lean": -6 * k,
              "head_nod": -4 * k}
        yaw = lerp(math.degrees(math.atan2(d.x, -d.y)) * 0.45, 90.0, ss(b("flurry") - 0.35, b("flurry"), t))
        _step(pz, t, b("flurry") - 0.4, b("flurry") - 0.05)
        M.set_noob(E, noob_stand(E, t)[0], yaw, pz, NF["happy"], t)
    elif t < b("break") + 0.1:
        # the flurry: alternating fists, about five a second
        hits = _flurry_hits()
        k = max([i for i, h in enumerate(hits) if h <= t + 0.05] or [0])
        side = "arm_sr" if k % 2 == 0 else "arm_sl"
        other = "arm_sl" if side == "arm_sr" else "arm_sr"
        ph = min(1.0, max(0.0, (t - (hits[k] - 0.05)) / 0.19)) if hits else 0
        pz = {side: {"fwd": 92 * math.sin(math.pi * ph) + 20, "out": 4}, other: {"fwd": 22, "out": 12},
              "chest_twist": 9 if side == "arm_sr" else -9, "chest_lean": 6}
        face = dict(NF["shout"])
        M.set_noob(E, E.punch_at, 90.0, pz, face, t)
    elif t < b("noob_float"):
        # the block bursts: he cheers, arms up
        k = ss(b("break") + 0.1, b("break") + 0.35, t)
        pz = {"arm_sl": {"out": 40 + 120 * k, "fwd": 10}, "arm_sr": {"out": 40 + 120 * k, "fwd": 10},
              "chest_lean": -6 * k, "head_nod": -6}
        back = ss(b("break") + 0.6, b("break") + 1.4, t)
        p = E.punch_at.lerp(NOOB_BACK, back)
        p.z = E.ground(p.x, p.y) + 0.12 * math.sin(math.pi * k)
        M.set_noob(E, p, lerp(40.0, 70.0, back), pz, NF["happy"], t)
    else:
        # looking up at the floating tree; puzzled, then (the crack) scared
        up = ss(b("noob_float") - 0.3, b("noob_float") + 0.3, t)
        face = dict(NF["confused"]) if t < b("crack") + 0.3 else dict(NF["worried"])
        pz = {"head_nod": -40 * up, "chest_lean": -6 * up, "arm_sl": {"out": 12}, "arm_sr": {"out": 12}}
        p = Vector((NOOB_BACK.x, NOOB_BACK.y, E.ground(NOOB_BACK.x, NOOB_BACK.y)))
        c = E.crack_at - p
        yc = math.degrees(math.atan2(c.x, -c.y))
        M.set_noob(E, p, lerp(70.0, yc - 40, ss(b("crack"), b("crack") + 0.8, t)), pz, face, t)
    # ------------------------------------------------ Steve (on screen from shot 5)
    if t < b("steve_tool"):
        E.S.holder.location = (0, 0, -300)
    else:
        d = E.tree_foot - steve_pos(E, t)
        yaw_tree = math.degrees(math.atan2(d.x, -d.y))
        face = dict(SF["flat"])
        pz = {"arm_sr": {"fwd": 40, "out": 10, "elbow": 60}, "arm_sl": {"fwd": 10, "out": 8, "elbow": 20}}
        yaw = yaw_tree
        if b("steve_tool") <= t < b("noob_roblox"):
            # "It's a tree. You need a tool." — the pickaxe up as the proof, lowered on "tool"
            low = ss(b("steve_tool", 1) - 0.5, b("steve_tool", 1), t)
            pz["arm_sr"] = {"fwd": lerp(*TOOL_ARM[0], low), "out": TOOL_ARM[1], "elbow": lerp(*TOOL_ARM[2], low)}
            yaw = yaw_tree - 25
        if t >= b("noob_float") - 0.3:
            up = ss(b("noob_float") - 0.3, b("noob_float") + 0.4, t)
            pz["head_nod"] = -38 * up
            pz["arm_sr"] = {"fwd": 25, "out": 14, "elbow": 35}
        if t >= b("crack"):
            # he turns to the crack in the sky, looking up: worried
            c = E.crack_at - steve_pos(E, t)
            yc = math.degrees(math.atan2(c.x, -c.y))
            yaw = lerp(yaw_tree, yc, ss(b("crack") - 0.1, b("crack") + 0.45, t))
            pz["head_nod"] = -30
            pz["arm_sr"] = {"fwd": 12, "out": 14, "elbow": 25}         # the pickaxe down at his side, clear of his face
            face = dict(SF["worried"])
        sp = steve_pos(E, t)
        if b("break") + 0.3 < t < b("noob_float"):                # the few steps
            ph = (t - b("break")) * 1.6 * 2 * math.pi
            sw = math.sin(ph)
            pz.update({"foot_sl": {"y": -0.3 * sw, "z": max(0.0, 0.25 * math.sin(ph + 1.2))},
                       "foot_sr": {"y": 0.3 * sw, "z": max(0.0, 0.25 * math.sin(ph + 1.2 + math.pi))}})
        M.set_steve(E, sp, yaw, pz, face, t)


# ------------------------------------------------------------------ the camera
def camera(E, t, shot, t0, t1):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    loc, look, lens, fstop, focus, shake = _cam(E, t, shot, t0, t1)
    y1, p1, r1 = handheld(t, shake)
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = M.P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.data.lens = lens
    E.cam.data.dof.use_dof = fstop < 30
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.key.location = loc + Vector((0.6, 0.0, 1.6))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus or None, handheld)"""
    u = ss(t0, t1, t) if t1 < 1e8 else 0.0
    hn = M.P6._head(E.N.face)
    tf = E.tree_foot
    mid = 0.5 * (E.punch_at + tf)
    if shot == "look":
        # medium-wide, low: the Noob centre, the oak at the right, the meadow and cherries behind
        c = E.noob0 + Vector((0.55, 0, 1.15))
        loc = c + Vector((0.4, -4.4, -0.35)) + Vector((0.0, 0.25, 0.0)) * u
        return loc, c, 24, 4.0, None, 0.05
    if shot == "walk":
        # tracking beside him as he walks to the tree, room ahead of him
        n = Vector(E.N.root.location)
        loc = n + Vector((-1.9, -3.7, 1.15))
        return loc, n + Vector((0.8, 0.7, 1.0)), 28, 4.0, None, 0.1
    if shot == "tree":
        # the Noob on the left third, the trunk on the right third, showing off to us
        c = E.punch_at.lerp(tf, 0.42) + Vector((0, 0, 1.15))
        loc = c + Vector((-0.4, -4.6, 0.1)) + Vector((0.0, 0.2, 0.0)) * u
        return loc, c, 26, 4.0, None, 0.05
    if shot == "punch":
        c = mid + Vector((0, 0, 0.95))
        loc = c + Vector((0.9, -3.8, 0.3))          # side on, a little in front: the Noob left, the trunk right
        sh = 0.08 + 0.9 * math.exp(-((t - b("punch") - 0.18) / 0.06) ** 2)
        return loc, c, 26, 4.5, None, sh
    if shot == "steve":
        # Steve close, deadpan, the pickaxe up; the tree soft behind him
        hs = M.P6._head(E.S.face, E.S.holder)
        c = hs + Vector((0, 0, -0.3))
        d = (E.punch_at - E.steve_at)
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        loc = c + d * 2.3 - side * 0.5 + Vector((0, 0, 0.05))
        return loc, c - side * 0.25, 34, 2.8, None, 0.05
    if shot == "break":
        c = mid + Vector((-0.6, 0, 1.25))
        loc = c + Vector((-0.4, -5.0, -0.55))
        return loc, c, 22, 64.0, None, 0.06 + 0.4 * math.exp(-((t - b("break") - 0.06) / 0.12) ** 2)
    if shot in ("wide", "break"):
        # the wide of the three: Steve left, the Noob centre, the oak right, the meadow behind
        c = Vector((0.4, 2.2, E.ground(0.4, 2.2) + 1.6))
        loc = c + Vector((0.1, -7.8, -0.9)) + Vector((0.0, 0.25, 0.0)) * u
        return loc, c, 22, 64.0, None, 0.05 if shot == "wide" else 0.3 * math.exp(-((t - b("break") - 0.06) / 0.12) ** 2)
    if shot == "flurry":
        c = mid + Vector((0, 0, 0.8))
        loc = c + Vector((0.3, -3.1, 0.1))
        sh = 0.18 + 0.2 * (1 - ss(b("flurry"), b("flurry") + 0.3, t))
        return loc, c, 22, 4.5, None, sh
    if shot == "float":
        # low from the grass up past the stump to the floating tree; the two looking up below
        # from the south-east, low: the stump's gap under the floating trunk, the two at the left looking up
        c = Vector((0.6, 1.0, E.ground(0.6, 1.0) + 1.8))
        loc = Vector((3.0, -4.4, E.ground(3.0, -4.4) + 0.4))
        return loc, c, 20, 64.0, None, 0.04
    if shot == "crack":
        # close, low, in front of him: his face turning up, the tear's pink light on it
        hs = M.P6._head(E.S.face, E.S.holder)
        d = (E.crack_at - steve_pos(E, t))
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        loc = hs + d * 1.7 + side * 0.6 + Vector((0, 0, -0.85))
        return loc, hs + Vector((0, 0, 0.05)), 30, 2.8, None, 0.06 + 0.35 * math.exp(-((t - b("crack") - 0.3) / 0.15) ** 2)
    if shot == "crackwide":
        # what he sees (the reverse of his close shot): the sky tearing open over the floating tree's crown
        hs = M.P6._head(E.S.face, E.S.holder)
        up_dir = (E.crack_at - hs).normalized()
        loc = hs + Vector((0, 0, 0.05))
        look = hs + up_dir * 10.0 + Vector((0, 0, 0.6 + 0.5 * ss(t0, t0 + 1.4, t)))
        return loc, look, 18, 64.0, None, 0.05
    if shot == "eye":
        # the crack framed wide, the eye in it looking down at them
        sp = steve_pos(E, t)
        d = (E.crack_at - sp)
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        loc = sp + d * 1.6 - side * 1.8 + Vector((0, 0, 1.8))
        return loc, E.crack_at, 28, 64.0, None, 0.04
    return Vector((0, -8, 3)), Vector((0, 0, 1)), 30, 64.0, None, 0.0


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("voice")
    ap.add_argument("tex_dir")
    ap.add_argument("assets")
    ap.add_argument("out_dir")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--res", type=int, default=1080)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--times")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    B.update({k: tuple(v) for k, v in tl["beats"].items()})
    n_frames = int(round(tl["length"] * FPS)) + 1
    if a.times:
        frames = [int(round(float(x) * FPS)) + 1 for x in a.times.split(",")]
    else:
        frames = list(range(1, n_frames + 1))
        k, n = (int(x) for x in a.shard.split("/"))
        per = (len(frames) + n - 1) // n
        frames = frames[k * per:(k + 1) * per]
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    E = build(tl, a.tex_dir, a.assets, a.res, a.samples)
    E.force = bool(a.times)
    E.mouth = {}
    voice = a.voice if os.path.exists(a.voice) else os.path.join(os.path.dirname(a.voice), "audio.wav")
    if os.path.exists(voice):
        from ep09_new import _lipsync
        E.mouth = _lipsync(tl, voice)
    E.cuts = sorted(t0 for _, t0 in shot_bounds())
    M._render(E, frames, out, apply, M.finish_forest)


if __name__ == "__main__":
    main()
