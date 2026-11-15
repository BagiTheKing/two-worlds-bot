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
PUNCH_AT = Vector((1.42, 0.5, 0.0))        # where he stands to punch (west of the trunk, facing +x): the fist lands
STAND_BACK = Vector((-0.75, 0.0, 0.0))     # a step back from it while talking, so his arms stay off the bark
STEVE_AT = Vector((-1.8, 3.6, 0.0))        # Steve, a few blocks from the tree, pickaxe in hand
STEVE2 = Vector((-0.8, 2.6, 0.0))          # after the break he comes a few steps closer to look at the tree
NOOB_BACK = Vector((1.9, -1.5, 0.0))       # the Noob steps back from the log to look up at it (clear of Steve)
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


STEVE_FROM = M.STEVE_FAR                   # where chapter 0 leaves Steve: far off at the left, among the trees
WALK_FROM = 0.9                            # he has seen the Noob land; he sets off toward him


def steve_walk(t):
    """Steve's walk across the meadow to the tree: (0..1 along the way, distance walked)."""
    u = ss(WALK_FROM, b("steve_arrives", 1) - 0.1, t)
    return u, u * (STEVE_AT - STEVE_FROM).length


def steve_pos(E, t):
    if t < b("steve_tool"):
        p = STEVE_FROM.lerp(STEVE_AT, steve_walk(t)[0])
        return Vector((p.x, p.y, E.ground(p.x, p.y)))
    u = ss(b("break") + 0.3, b("noob_float"), t)
    p = STEVE_AT.lerp(STEVE2, u)
    return Vector((p.x, p.y, E.ground(p.x, p.y)))


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    # grass cleared where they stand and where the low cameras look past (nothing in front of a face)
    clear = [(STEVE_AT.x, STEVE_AT.y, 1.3), (PUNCH_AT.x, PUNCH_AT.y, 1.2), (NOOB0.x, NOOB0.y, 1.2),
             (0.5, -5.6, 2.2), (-0.4, -4.8, 1.6), (0.8, -1.8, 1.4), (-4.7, 2.5, 1.8), (4.2, -3.7, 1.8), (2.0, -1.0, 1.6), (3.9, -4.7, 1.8),
             (0.3, 5.0, 1.6), (-3.3, 0.3, 1.8), (-0.5, 4.3, 1.4), (-4.4, 8.2, 2.0), (0.7, -4.3, 1.8), (0.1, 0.05, 1.3), (-0.4, -0.6, 1.3), (-0.8, 2.6, 1.3), (3.0, -4.4, 1.8),
             (1.6, -2.0, 1.6), (-1.2, -4.6, 1.6), (-0.8, -4.1, 1.4), (4.8, -3.0, 1.6), (-2.1, 0.4, 1.4), (-3.6, 9.8, 1.2), (-2.7, 6.6, 1.2), (5.6, -3.8, 1.6), (1.9, -1.5, 1.2), (3.2, 3.9, 1.6)]
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
    # the eye is its own piece over the crack (eye_look opens it, moves its pupil, blinks, narrows it)
    eye = base.copy()
    ew = Image.new("RGBA", (420, 240), (0, 0, 0, 0))
    ImageDraw.Draw(ew).ellipse((4, 4, 415, 235), fill=(196, 196, 204, 255), outline=(255, 255, 255, 255), width=8)
    epath = os.path.join(bpy.app.tempdir or "/tmp", "ep01_eyewhite.png")
    ew.save(epath)
    # the pupil is its own piece (eye_look moves it: the eye looks round, and blinks)
    pup = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    dp = ImageDraw.Draw(pup)
    dp.ellipse((1, 1, 190, 190), fill=(60, 58, 70, 255))
    dp.rectangle((76, 4, 116, 188), fill=(255, 20, 220, 255))
    ppath = os.path.join(bpy.app.tempdir or "/tmp", "ep01_pupil.png")
    pup.save(ppath)
    path = os.path.join(bpy.app.tempdir or "/tmp", "ep01_crack_eye.png")
    eye.save(path)
    paths["eye"] = path
    E.crack_mats = {}
    paths["pupil"] = ppath
    paths["eyewhite"] = epath
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
    bpy.ops.mesh.primitive_plane_add(size=1)
    ey = bpy.context.active_object
    ey.name = "sky_eye"
    ey.data.materials.append(E.crack_mats["eyewhite"])
    ey.parent = ob
    ey.scale = (420 / W_, 240 / H_, 1)
    ey.location = (0, 0, 0.002)
    bpy.ops.mesh.primitive_plane_add(size=1)
    pu = bpy.context.active_object
    pu.name = "sky_pupil"
    pu.data.materials.append(E.crack_mats["pupil"])
    pu.parent = ey
    pu.scale = (192 / 420, 192 / 240, 1)
    pu.location = (0, 0, 0.002)
    for o_ in (ey, pu):
        for a_ in ("visible_shadow", "visible_diffuse", "visible_glossy"):
            setattr(o_, a_, False)
    E.eye, E.pupil = ey, pu
    E.eye_room = (210 - 96) / 420                 # how far the pupil can travel inside the white (eye units)
    E.crack_at = E.tree_foot + CRACK
    lt = bpy.data.objects.new("crack_light", bpy.data.lights.new("crack_light", "SUN"))
    E.sc.collection.objects.link(lt)
    lt.data.color = (0.6, 0.25, 1.0)                  # the tear's magenta
    lt.data.energy = 0.0
    lt.rotation_euler = (-CRACK).to_track_quat("-Z", "Y").to_euler()
    E.crack_light = lt


def _keys(u, ks):
    """Eased steps through keys [(time, value), ...] (holds before the first and after the last)."""
    if u <= ks[0][0]:
        return ks[0][1]
    for (a, va), (c, vc) in zip(ks, ks[1:]):
        if u < c:
            return va + (vc - va) * ss(a, c, u)
    return ks[-1][1]


def _snap(u, ks, dur=0.07):
    """Like _keys, but each change is a quick dart (a saccade) at its time."""
    v = ks[0][1]
    for (a, va), (c, vc) in zip(ks, ks[1:]):
        if u >= c:
            v = vc
        elif u > c - dur:
            v = va + (vc - va) * ss(c - dur, c, u)
            break
        else:
            break
    return v


# the eye's life, in seconds from when it appears: it opens, darts left and right, blinks, then fixes on
# them and narrows; it goes on watching (a slow drift) into chapter 2
EYE_X = [(0.0, 0.0), (0.45, -0.85), (1.05, 0.8), (1.7, 0.05), (2.6, -0.25), (3.4, 0.1), (3.95, 0.7), (4.4, -0.15),
         (4.75, 0.55), (5.05, -0.6), (5.35, 0.2)]
EYE_Y = [(0.0, 0.0), (1.7, -0.6)]


def eye_look(E, t, show, t0=0.0):
    E.eye.hide_render = E.pupil.hide_render = not show
    if not show:
        return
    u = t - t0
    opn = ss(0.0, 0.22, u)
    blink = math.exp(-((u - 1.42) / 0.05) ** 2) + math.exp(-((u - 4.0) / 0.05) ** 2)
    narrow = 0.32 * ss(1.75, 2.1, u)
    E.eye.scale = (420 / 2048, 240 / 640 * max(0.03, opn * (1 - narrow) * (1 - 0.95 * blink)), 1)
    x = _snap(u, EYE_X) + 0.04 * math.sin(u * 7.3)
    y = _snap(u, EYE_Y, 0.1)
    E.pupil.location = (E.eye_room * max(-1.0, min(1.0, x)), 0.1 * y, 0.002)
    dil = 1.0 - 0.18 * ss(1.75, 2.0, u)                      # the slit narrows as it fixes on them
    E.pupil.scale = (192 / 420 * dil, 192 / 240, 1)


# ------------------------------------------------------------------ the shots
SHOTS = [("look", "look_around"), ("walk", "walk_to_tree"), ("tree", "noob_tree"), ("punch", "punch"),
         ("arrive", "steve_arrives"), ("steve", "steve_tool"), ("wide", "noob_roblox"), ("flurry", "flurry"), ("break", "break"),
         ("float", "noob_float"), ("normal", "steve_normal"), ("crack", "crack"), ("crackwide", ("crack", 0.9)),
         ("eye", "steve_not")]


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
    TEAR = b("crack") + 0.95                                     # the sky tears (seen, in his point of view)
    dk = ss(TEAR, TEAR + 0.6, t)
    look = M.mix_look({"glow": (255, 240, 220), "power": 30.0, "horizon": (220, 232, 250), "mid": (140, 186, 250),
                       "zenith": (52, 120, 236), "fill": 1.1, "fill_col": (186, 206, 240)},
                      {"glow": (236, 190, 230), "power": 8.0, "horizon": (200, 150, 200), "mid": (110, 90, 170),
                       "zenith": (44, 34, 96), "fill": 0.8, "fill_col": (176, 150, 220)}, dk)
    set_sky(E.W, look)
    E.sc.view_settings.exposure = lerp(-0.05, -0.35, dk)
    if not hasattr(E, "sun0"):
        E.sun0 = E.W.sun.data.energy
    E.W.sun.data.energy = lerp(E.sun0, 0.4 * E.sun0, dk)
    # the clouds (self-lit) take the dusk too, so the sky darkens as one
    for nm, e0 in (("cloud", 0.85), ("cloud_under", 0.6)):
        mt = bpy.data.materials.get(nm)
        if mt is None:
            continue
        bs = mt.node_tree.nodes.get("Principled BSDF")
        if not hasattr(E, "cloud0"):
            E.cloud0 = {}
        if nm not in E.cloud0:
            E.cloud0[nm] = tuple(bs.inputs["Base Color"].default_value)[:3]
        col = tuple(lerp(c0, c1, dk) for c0, c1 in zip(E.cloud0[nm], (0.42, 0.34, 0.72)))
        bs.inputs["Base Color"].default_value = (*col, 1)
        bs.inputs["Emission Color"].default_value = (*col, 1)
        bs.inputs["Emission Strength"].default_value = e0 * (1 - 0.45 * dk)
    if not hasattr(E, "key0"):
        E.key0 = (E.key.data.energy, tuple(E.key.data.color))
    E.key.data.energy = E.key0[0] * (1 - 0.35 * dk)                  # the faces' key dims and cools with the day
    E.key.data.color = tuple(lerp(c0, c1, dk) for c0, c1 in zip(E.key0[1], (0.72, 0.74, 1.0)))
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
    E.crack_light.data.energy = 1.0 * ss(TEAR, TEAR + 0.35, t) * (1 + 0.25 * math.sin(t * 23))
    E.crack.hide_render = t < TEAR
    if not E.crack.hide_render:
        # it rips from a point outward, fast, with a stutter (a glitch, not a smooth growth)
        u = ss(TEAR, TEAR + 0.5, t)
        u = min(1.0, u + 0.08 * math.sin(u * 40) * (1 - u))
        to_cam = (E.cam.location - E.crack_at)
        to_cam.z *= 0.3
        E.crack.location = E.crack_at
        E.crack.rotation_mode = "QUATERNION"
        E.crack.rotation_quaternion = to_cam.to_track_quat("Z", "Y") @ Quaternion((0, 0, 1), math.radians(-14))
        E.crack.scale = (52.0 * max(u, 0.02), 52.0 * 640 / 2048 * (0.25 + 0.75 * u), 1)
        E.crack.data.materials[0] = E.crack_mats["eye" if t >= b("steve_not") else "crack"]
    eye_look(E, t, (not E.crack.hide_render) and t >= b("steve_not"), b("steve_not"))
    cast(E, t, name, NF, SF)
    camera(E, t, name, t0, t1)


def _n(t, f, seed):
    """Smooth noise, -1..1."""
    return math.sin(t * f + seed) * 0.6 + math.sin(t * f * 2.31 + seed * 1.7) * 0.3 + math.sin(t * f * 4.07 + seed * 2.9) * 0.1


def _yawto(a, c):
    d = c - a
    return math.degrees(math.atan2(d.x, -d.y))


def _turn(t, y0, y1, a, c, lead=0.14):
    """A human turn from y0 to y1 between a and c: the head first, then the chest, then the hips (the root).
    Returns (root yaw, chest twist, head turn) - the chest and head are relative to the root."""
    h = lerp(y0, y1, ss(a - lead, c - lead, t))
    ch = lerp(y0, y1, ss(a - lead * 0.5, c - lead * 0.4, t))
    r = lerp(y0, y1, ss(a, c, t))
    return r, ch - r, h - ch


def _walkcycle(t, rate=1.3, amp=1.0):
    ph = t * rate * 2 * math.pi
    sw = math.sin(ph) * amp
    return {"arm_sl": {"fwd": -26 * sw, "out": 6}, "arm_sr": {"fwd": 26 * sw, "out": 6},
            "leg_sl": {"fwd": 30 * sw}, "leg_sr": {"fwd": -30 * sw},
            "chest_twist": -6 * sw, "chest_side": 2.5 * math.sin(ph + 0.5) * amp,
            "head_tilt": 3 * math.sin(ph + 0.9) * amp}, 0.05 * abs(math.sin(ph)) * amp


def noob_anim(E, t, NF):
    """The Noob, every beat acted (story/creator_notes.md: movement is human, no dead holds)."""
    g = E.ground
    face = dict(NF["happy"])
    lift = 0.0
    if t < b("walk_to_tree"):
        # where chapter 0 left him ("Whoa. Where am I?"): still a little scared, then wonder, then delight.
        # The head turns first, the chest after it, the hips last; a step as he turns the other way.
        u = t - b("look_around")
        ht = _keys(u, [(0.0, -7.4), (0.2, 0), (0.75, 38), (1.15, 38), (1.75, -36), (2.0, -30), (2.35, 0)])
        nod = _keys(u, [(1.85, 0), (2.25, -20), (2.55, -20), (2.85, -4)])
        ch = _keys(u, [(0.3, 0), (0.95, 15), (1.3, 15), (1.95, -14), (2.5, 0)])
        root = _keys(u, [(0.45, 0), (1.1, 9), (1.45, 9), (2.1, -10), (2.7, 8)])
        wonder = ss(0.6, 1.3, u)
        pump = math.exp(-((u - 2.65) / 0.09) ** 2) + math.exp(-((u - 2.9) / 0.09) ** 2)
        pz = {"head_turn": ht - ch, "head_nod": nod + 3 * _n(t, 1.1, 1), "head_tilt": 6 * _n(t, 0.8, 2) - 6 * wonder * (u < 2.3),
              "chest_twist": ch - root * 0.3, "chest_lean": -4 * ss(1.85, 2.3, u) + 1.5 * math.sin(t * 2.4),
              "arm_sl": {"out": 10 + 14 * wonder + 30 * pump - 0.25 * ch, "fwd": 12 + 10 * wonder + 0.3 * ch},
              "arm_sr": {"out": 10 + 14 * wonder + 30 * pump + 0.25 * ch, "fwd": 12 + 10 * wonder - 0.3 * ch}}
        step = math.sin(math.pi * ss(1.25, 1.65, u))
        # chapter 0 ends with him mid-stride, walking toward us: his last steps die out here
        dec = 1 - ss(0.0, 0.45, u)
        sw0 = math.sin(2 * math.pi * (0.77 + 1.8 * u)) * dec
        pz["leg_sl"] = {"fwd": 18 * step + 30 * sw0}
        pz["leg_sr"] = {"fwd": -30 * sw0}
        pz["arm_sl"]["fwd"] += -28 * sw0
        pz["arm_sr"]["fwd"] += 28 * sw0
        lift = 0.03 * step + 0.07 * pump + 0.04 * abs(sw0)
        face = dict(NF["awe"]) if u < 2.35 else dict(NF["happy"])
        if u >= 2.35:
            face.update({"both_bm": 0.4, "m_arch": -0.55})
        M.set_noob(E, E.noob0 + Vector((0, 0, lift)), root, pz, face, t)
        return
    if t < b("noob_tree") + 0.25:
        # the walk to the tree: a bouncy, happy walk, looking up at it; slowing as he arrives, he turns to it
        a, c = b("walk_to_tree"), b("walk_to_tree", 1)
        stand = E.punch_at + STAND_BACK
        s_ = ss(a, c + 0.1, t)
        p = E.noob0.lerp(stand, s_)
        p.z = g(p.x, p.y)
        walk_yaw = _yawto(E.noob0, stand)
        tree_yaw = _yawto(stand, E.tree_foot)
        amp = 1.0 - ss(c - 0.35, c + 0.15, t)
        pz, bob = _walkcycle(t - a, 1.35, amp)
        r, ch, hd = _turn(t, walk_yaw, tree_yaw, c - 0.35, c + 0.2)
        pz["chest_twist"] += ch
        pz["head_turn"] = hd + 10 * (1 - ss(c - 0.5, c, t))
        pz["head_nod"] = -10 - 8 * ss(c - 0.4, c + 0.2, t)                   # looking up the trunk
        face = dict(NF["happy"])
        face.update({"both_bm": 0.35})
        M.set_noob(E, p + Vector((0, 0, bob)), r, pz, face, t)
        return
    if t < b("punch"):
        # "Okay. A tree. One punch. Watch this." - sizing the tree up, then to us, a gesture for each part
        stand = noob_stand(E, t)[0]
        tree_yaw = _yawto(E.punch_at + STAND_BACK, E.tree_foot)
        us = 20.0
        r1, ch1, hd1 = _turn(t, tree_yaw, us, 5.3, 5.65)                     # to us after "Okay."
        r2, ch2, hd2 = _turn(t, us, 90.0, b("punch") - 0.5, b("punch") - 0.08)   # to the trunk, to punch
        if t < b("punch") - 0.62:
            r, ch, hd = r1, ch1, hd1
        else:
            r, ch, hd = r2, ch2, hd2
        okay = math.exp(-((t - 5.12) / 0.1) ** 2)
        present = ss(5.55, 5.75, t) * (1 - ss(6.05, 6.3, t))                 # "A tree." - his hand shows it
        fist = ss(6.4, 6.6, t) * (1 - ss(7.25, 7.45, t))                      # "One punch." - the fist up
        pump = math.exp(-((t - 6.95) / 0.07) ** 2)
        cocky = ss(7.4, 7.6, t)                                               # "Watch this." - chest out, a shoulder roll
        roll = ss(7.5, 7.6, t) * (1 - ss(7.95, 8.1, t))
        rph = (t - 7.5) * 2 * math.pi * 1.6
        pz = {"head_turn": hd + 22 * present - 8 * okay + 6 * _n(t, 1.3, 3),
              "head_nod": -14 * (1 - ss(5.15, 5.4, t)) + 9 * okay - 4 * fist + 3 * pump,
              "head_tilt": 10 * cocky + 4 * _n(t, 0.9, 4),
              "chest_twist": ch + 6 * present - 4 * fist,
              "chest_lean": -7 * cocky + 3 * okay + 2 * math.sin(t * 2.2),
              "arm_sr": {"out": 12 + 55 * present, "fwd": 10 + 35 * present},
              "arm_sl": {"out": 10 + 8 * fist + 25 * roll * (0.5 + 0.5 * math.cos(rph)),
                         "fwd": 8 + 105 * fist + 12 * pump + roll * (55 + 45 * math.sin(rph))}}
        _step(pz, t, b("punch") - 0.45, b("punch") - 0.05)
        _step(pz, t, 5.35, 5.6)
        face = dict(NF["happy"])
        face.update({"both_bm": 0.3 + 0.15 * cocky, "m_arch": -0.45 - 0.15 * cocky,
                     "eL_to": -0.55 * cocky - 0.15, "eL_tm": -0.55 * cocky - 0.15, "eL_ti": -0.4 * cocky,
                     "m_tilt": 0.12 * cocky})
        M.set_noob(E, stand + Vector((0, 0, 0.03 * okay)), r, pz, face, t)
        return
    if t < b("steve_tool"):
        # one punch: the wind-up, the hit (punch+0.18), the follow-through; nothing happens: he looks at his fist
        u = t - b("punch")
        wind = ss(0.0, 0.1, u) * (1 - ss(0.1, 0.16, u))
        jab = math.exp(-((u - 0.18) / 0.06) ** 2)
        thru = ss(0.16, 0.3, u) * (1 - ss(0.4, 0.75, u))
        look = ss(0.55, 0.75, u) * (1 - ss(1.05, 1.2, u))
        pz = {"chest_twist": 16 * wind - 12 * jab - 8 * thru, "chest_lean": -5 * wind + 7 * jab + 4 * thru,
              "arm_sl": {"fwd": -25 * wind + 90 * jab + 70 * thru * (1 - jab) + 38 * look, "out": 4 + 26 * look},
              "arm_sr": {"fwd": 15 + 20 * wind, "out": 12},
              "head_nod": 4 * jab - 12 * look, "head_turn": -14 * look, "head_tilt": 14 * ss(0.6, 0.9, u)}
        _step(pz, t, b("punch") + 0.5, b("punch") + 1.0)
        face = NF["happy"] if u < 0.45 else NF["confused"]
        M.set_noob(E, noob_stand(E, t)[0], 90.0 - 10 * look, pz, dict(face), t)
        return
    if t < b("noob_roblox"):
        # Steve speaks; the Noob turns to him, unimpressed: a tilt, a small shrug at "tool"
        sy = _yawto(E.punch_at, E.steve_at)
        r, ch, hd = _turn(t, 90.0, sy, b("steve_tool") + 0.05, b("steve_tool") + 0.55)
        shrug = math.exp(-((t - 11.3) / 0.18) ** 2)
        pz = {"head_turn": hd + 4 * _n(t, 0.9, 5), "head_tilt": 9 * ss(10.2, 10.6, t) + 4 * _n(t, 0.7, 6),
              "chest_twist": ch, "chest_lean": 2 * math.sin(t * 2.0),
              "arm_sl": {"out": 12 + 22 * shrug, "fwd": 8 + 10 * shrug}, "arm_sr": {"out": 12 + 22 * shrug, "fwd": 8 + 10 * shrug}}
        _step(pz, t, b("punch") + 0.5, b("punch") + 1.0)
        face = dict(NF["neutral"])
        face.update({"eL_to": -0.2, "eR_to": -0.2, "m_tilt": 0.1})
        M.set_noob(E, noob_stand(E, t)[0] + Vector((0, 0, 0.04 * shrug)), r, pz, face, t)
        return
    if t < b("flurry"):
        # "I don't need tools." (shaking his head, a dismissive wave) "I'm a Roblox player." (chest out, arms
        # spread, a bounce on "Roblox"); then he turns to the trunk, shaking his arms out, steps in
        sy = _yawto(E.punch_at, E.steve_at)
        sy = lerp(sy, 10.0, 0.55)                     # he plays it to us as much as to Steve (the wide is in front)
        no = ss(12.1, 12.25, t) * (1 - ss(12.85, 13.05, t))
        wave = ss(12.35, 12.5, t) * (1 - ss(12.85, 13.0, t))
        k = ss(13.1, 13.5, t) * (1 - ss(15.0, 15.25, t))
        bounce = math.exp(-((t - 13.85) / 0.1) ** 2)
        shake = ss(15.05, 15.15, t) * (1 - ss(15.45, 15.58, t))
        r, ch, hd = _turn(t, sy, 90.0, b("flurry") - 0.5, b("flurry") - 0.05)
        pz = {"head_turn": hd + 16 * no * math.sin((t - 12.1) * 2 * math.pi * 2.6), "head_nod": -5 * k + 4 * bounce,
              "head_tilt": 6 * k * math.sin(t * 1.4),
              "chest_twist": ch, "chest_lean": -8 * k - 3 * bounce,
              "arm_sr": {"out": 20 + 70 * k + 25 * wave, "fwd": 10 + 45 * wave * (0.5 + 0.5 * math.sin((t - 12.35) * 2 * math.pi * 3)) + 20 * shake * math.sin(t * 40)},
              "arm_sl": {"out": 20 + 70 * k, "fwd": 10 + 20 * shake * math.sin(t * 40 + 1.3)}}
        _step(pz, t, b("flurry") - 0.4, b("flurry") - 0.05)
        face = dict(NF["happy"])
        face.update({"both_bm": 0.3 + 0.2 * k, "eL_to": -0.3 * k, "eR_to": -0.3 * k})
        M.set_noob(E, noob_stand(E, t)[0] + Vector((0, 0, 0.06 * bounce)), r, pz, face, t)
        return
    if t < b("break") + 0.1:
        # the flurry: every punch its own (reach, height, timing); the body rocks into each one, the head
        # bobs, the other fist cocked back ready; the feet shuffle; he leans in more as it goes
        import random as _r
        hits = _flurry_hits()
        k = max([i for i, h in enumerate(hits) if h <= t + 0.07] or [0])
        rr = _r.Random(100 + k)
        reach = rr.uniform(84, 96)
        outv = rr.uniform(-4, 8)
        side = "arm_sr" if k % 2 == 0 else "arm_sl"
        other = "arm_sl" if side == "arm_sr" else "arm_sr"
        hk = hits[k] if hits else t
        uu = t - hk
        ext = math.exp(-((uu) / 0.055) ** 2)                                # out to the bark at the hit
        back = ss(0.02, 0.14, uu) * (1 - ss(0.14, 0.2, uu))
        prog = ss(b("flurry"), b("break"), t)
        sgn = 1 if side == "arm_sr" else -1
        pz = {side: {"fwd": 25 + (reach - 25) * ext - 10 * back, "out": outv},
              other: {"fwd": 20 + 18 * math.exp(-((uu - 0.12) / 0.06) ** 2) + rr.uniform(-6, 6), "out": 10},
              "chest_twist": sgn * (11 * ext + 5 * back) + 2 * _n(t, 3, 7),
              "chest_lean": 5 + 7 * prog + 4 * ext, "head_nod": 4 * ext + 3 * prog, "head_tilt": 5 * _n(t, 2.1, 8),
              "head_turn": 4 * _n(t, 1.7, 9)}
        if k % 3 == 2:
            sh = math.sin(math.pi * ss(hk - 0.05, hk + 0.15, t))
            pz["leg_sl" if k % 2 else "leg_sr"] = {"fwd": 14 * sh}
        face = dict(NF["shout"])
        face["m_o"] = 0.6 + 0.35 * abs(math.sin(t * 9))
        M.set_noob(E, E.punch_at + Vector((0.03 * ext, 0, 0.015 * ext)), 90.0 + 4 * _n(t, 1.1, 10), pz, face, t)
        return
    if t < b("noob_float"):
        # the block bursts: a startle (he jerks back), then he cheers, arms up, hopping back as the bits land
        u = t - b("break")
        jerk = ss(0.0, 0.08, u) * (1 - ss(0.12, 0.3, u))
        k = ss(0.15, 0.4, u)
        hop = max(0.0, math.sin((u - 0.35) * 2 * math.pi * 1.6)) * ss(0.3, 0.4, u) * (1 - ss(1.2, 1.5, u))
        pump = math.sin((u - 0.35) * 2 * math.pi * 1.6)
        back = ss(0.6, 1.4, u)
        p = E.punch_at.lerp(NOOB_BACK, back)
        p.z = E.ground(p.x, p.y) + 0.16 * hop
        pz = {"arm_sl": {"out": 40 + 120 * k + 15 * pump * k, "fwd": 10 + 40 * jerk}, "arm_sr": {"out": 40 + 120 * k - 15 * pump * k, "fwd": 10 + 40 * jerk},
              "chest_lean": -8 * jerk - 6 * k, "head_nod": -6 * k - 6 * jerk, "head_tilt": 8 * pump * k}
        if back > 0 and back < 1:
            w_, _ = _walkcycle(u, 1.6, 0.6)
            pz["leg_sl"], pz["leg_sr"] = w_["leg_sl"], w_["leg_sr"]
        face = dict(NF["shock"]) if u < 0.2 else dict(NF["happy"])
        if u >= 0.2:
            face.update({"both_bm": 0.45, "m_arch": -0.6, "m_o": 0.4})
        M.set_noob(E, p, lerp(90.0, 115.0, ss(0.3, 1.2, u)), pz, face, t)
        return
    # looking up at the floating tree: puzzled, scratching his head; to Steve on "That's normal."; back up;
    # a shrug; the glitch makes him jump
    p = Vector((NOOB_BACK.x, NOOB_BACK.y, E.ground(NOOB_BACK.x, NOOB_BACK.y)))
    sy = _yawto(p, steve_pos(E, t))
    up = ss(b("noob_float") - 0.2, b("noob_float") + 0.3, t) * (1 - ss(21.3, 21.6, t)) + ss(22.5, 22.9, t)
    scratch = ss(19.95, 20.2, t) * (1 - ss(20.9, 21.15, t))
    to_steve = ss(21.35, 21.65, t) * (1 - ss(22.45, 22.8, t))
    shrug = math.exp(-((t - 22.95) / 0.16) ** 2)
    jolt = ss(b("crack"), b("crack") + 0.06, t) * (1 - ss(b("crack") + 0.15, b("crack") + 0.5, t))
    c = E.crack_at - p
    yc = math.degrees(math.atan2(c.x, -c.y))
    base = lerp(115.0, yc - 30, ss(b("crack") + 0.9, b("crack") + 1.5, t))
    pz = {"head_nod": -22 * up - 6 * jolt, "head_tilt": 12 * scratch + 4 * _n(t, 0.8, 11),
          "head_turn": 0.8 * _wrap(sy - base) * to_steve + 4 * _n(t, 0.6, 12),
          "chest_lean": -5 * up + 4 * jolt, "chest_twist": 0.25 * _wrap(sy - base) * to_steve,
          # the far arm scratches (the near one would cover his face from this side)
          "arm_sr": {"out": 12 - 22 * scratch + 20 * shrug + 30 * jolt, "fwd": 10 + 160 * scratch + 6 * math.sin(t * 18) * scratch + 30 * jolt},
          "arm_sl": {"out": 12 + 20 * shrug + 30 * jolt, "fwd": 10 + 30 * jolt}}
    face = dict(NF["confused"])
    face["both_py"] = 0.3 * up
    if t >= b("crack"):
        face = dict(NF["shock"]) if t < b("crack") + 0.6 else dict(NF["worried"])
        face["both_py"] = 0.35
    M.set_noob(E, p + Vector((0, 0, 0.05 * jolt)), base, pz, face, t)


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


REST_ARM = {"fwd": 12, "out": 14, "elbow": 25}            # the pickaxe held low at his side


def steve_anim(E, t, SF):
    """Steve: never a statue - he breathes, shifts his weight, watches, reacts."""
    if t < b("steve_tool"):
        # where chapter 0 left him (standing among the trees, looking on); he sets off across the meadow,
        # the pickaxe in his hand, watching the Noob; his last steps slow as he arrives
        sp = steve_pos(E, t)
        u, dist = steve_walk(t)
        walk_yaw = _yawto(STEVE_FROM, STEVE_AT)
        yaw_noob = _yawto(sp, Vector(E.N.root.location))
        yaw = lerp(-40.0, walk_yaw, ss(WALK_FROM - 0.3, WALK_FROM + 0.3, t))
        ph = dist / 0.8 * 2 * math.pi                            # one cycle per 0.8 m: the feet don't slide
        mv = ss(WALK_FROM - 0.1, WALK_FROM + 0.3, t) * (1 - ss(b("steve_arrives", 1) - 0.35, b("steve_arrives", 1) - 0.05, t))
        sw = math.sin(ph) * mv
        look = max(-50.0, min(50.0, ((yaw_noob - yaw + 180) % 360) - 180))
        pz = {"foot_sl": {"y": -0.32 * sw, "z": max(0.0, 0.22 * math.sin(ph + 1.2)) * mv},
              "foot_sr": {"y": 0.32 * sw, "z": max(0.0, 0.22 * math.sin(ph + 1.2 + math.pi)) * mv},
              "arm_sl": {"fwd": 18 * sw + 6, "out": 9, "elbow": 22},
              "arm_sr": {"fwd": REST_ARM["fwd"] - 8 * sw, "out": REST_ARM["out"], "elbow": REST_ARM["elbow"]},
              "chest_lean": 3 * mv, "chest_twist": -5 * sw,
              "head_turn": lerp(10.0, look * 0.7, ss(0.3, 0.8, t)) + 3 * _n(t, 0.6, 31), "head_nod": 3 * abs(sw)}
        face = dict(SF["neutral"]) if t < 1.0 else dict(SF["flat"])
        if t >= b("punch") + 0.6:
            face["bL_raise"] = 0.3 * ss(b("punch") + 0.6, b("punch") + 0.9, t)   # the tree didn't break: a brow
        M.set_steve(E, sp + Vector((0, 0, 0.025 * abs(sw))), yaw, pz, face, t)
        return
    sp = steve_pos(E, t)
    yaw_tree = _yawto(sp, E.tree_foot)
    noob_p = Vector(E.N.root.location)
    yaw_noob = _yawto(sp, noob_p)
    breath = math.sin(t * 2 * math.pi / 3.2)
    face = dict(SF["flat"])
    pz = {"arm_sr": dict(REST_ARM), "arm_sl": {"fwd": 8, "out": 10, "elbow": 18}, "chest_lean": 2 * breath,
          "head_tilt": 3 * _n(t, 0.5, 21), "head_turn": 3 * _n(t, 0.6, 22)}
    yaw = yaw_tree
    if t < b("noob_roblox"):
        # "It's a tree. You need a tool." - the pickaxe up as the proof, a small nod on each phrase, a brow on "tool"
        low = ss(b("steve_tool", 1) - 0.5, b("steve_tool", 1), t)
        pz["arm_sr"] = {"fwd": lerp(*TOOL_ARM[0], low), "out": TOOL_ARM[1], "elbow": lerp(*TOOL_ARM[2], low)}
        yaw = yaw_tree - 25
        pz["head_nod"] = 5 * math.exp(-((t - 10.3) / 0.12) ** 2) + 5 * math.exp(-((t - 11.35) / 0.12) ** 2)
        face["bL_raise"] = 0.3 * ss(10.8, 11.0, t)
    elif t < b("flurry"):
        # he lowers the pickaxe and watches the Noob; on "Roblox player" one brow goes up, a slow head shake
        low = ss(b("noob_roblox"), b("noob_roblox") + 0.5, t)
        pz["arm_sr"] = {"fwd": lerp(TOOL_ARM[0][1], REST_ARM["fwd"], low), "out": lerp(TOOL_ARM[1], REST_ARM["out"], low),
                        "elbow": lerp(TOOL_ARM[2][1], REST_ARM["elbow"], low)}
        yaw = lerp(yaw_tree - 25, yaw_noob, ss(b("noob_roblox"), b("noob_roblox") + 0.6, t))
        pz["head_turn"] += 7 * math.sin((t - 14.1) * 2 * math.pi * 1.1) * ss(14.0, 14.2, t) * (1 - ss(14.9, 15.1, t))
        pz["arm_sl"] = {"fwd": 5, "out": 30, "elbow": 80}                              # a hand on his hip
        face["bL_raise"] = 0.35 * ss(13.3, 13.6, t)
        face.update({"both_to": -0.45, "both_tm": -0.5})
    elif t < b("break"):
        # the flurry: unimpressed, a hand on his hip, a little flinch at each hit; his eyes widen as it cracks
        yaw = yaw_noob + 10
        hits = _flurry_hits()
        fl = sum(math.exp(-((t - h) / 0.05) ** 2) for h in hits)
        pz["arm_sl"] = {"fwd": 5, "out": 30, "elbow": 80}
        pz["head_nod"] = 5 * fl
        pz["chest_lean"] += -2.5 * fl
        pz["arm_sr"] = {"fwd": REST_ARM["fwd"] + 6 * fl, "out": REST_ARM["out"], "elbow": REST_ARM["elbow"] + 10 * fl}
        widen = ss(17.2, 17.8, t)
        face.update({"both_to": -0.45 * (1 - widen), "both_tm": -0.5 * (1 - widen)})
        face["bb_raise"] = 0.2 * widen
    else:
        # the burst: he jerks back, stunned; then he walks over for a closer look
        u = t - b("break")
        jerk = ss(0.02, 0.1, u) * (1 - ss(0.25, 0.6, u))
        pz["chest_lean"] += -10 * jerk
        pz["head_nod"] = -6 * jerk
        pz["arm_sl"] = {"fwd": 25 * jerk + 8, "out": 14, "elbow": 30 + 30 * jerk}
        face = dict(SF["stunned"]) if u < 0.9 else dict(SF["flat"])
        yaw = yaw_tree
        if b("break") + 0.3 < t < b("noob_float"):                # the few steps
            ph = (t - b("break")) * 1.6 * 2 * math.pi
            sw = math.sin(ph)
            pz.update({"foot_sl": {"y": -0.3 * sw, "z": max(0.0, 0.25 * math.sin(ph + 1.2))},
                       "foot_sr": {"y": 0.3 * sw, "z": max(0.0, 0.25 * math.sin(ph + 1.2 + math.pi))}})
        if t >= b("noob_float") - 0.3:
            # up at the floating tree; on "That's normal." to the Noob (deadpan, a small shrug); back up at it
            up = ss(b("noob_float") - 0.3, b("noob_float") + 0.4, t) * (1 - ss(21.4, 21.7, t)) + ss(22.5, 22.9, t) * 0.8
            pz["head_nod"] = -26 * up
            to_n = ss(21.35, 21.6, t) * (1 - ss(22.5, 22.9, t))
            pz["head_turn"] = 0.75 * _wrap(yaw_noob - yaw_tree) * to_n
            pz["chest_twist"] = 0.25 * _wrap(yaw_noob - yaw_tree) * to_n
            shrug = math.exp(-((t - 21.95) / 0.15) ** 2)
            pz["arm_sl"] = {"fwd": 10 + 15 * shrug, "out": 12 + 20 * shrug, "elbow": 25 + 30 * shrug}
            face = dict(SF["flat"])
    if t >= b("crack"):
        # the glitch: his head snaps up to the sky; he turns to it: worried
        c = E.crack_at - sp
        yc = math.degrees(math.atan2(c.x, -c.y))
        yaw = lerp(yaw_tree, yc, ss(b("crack") + 0.05, b("crack") + 0.6, t))
        pz["head_nod"] = -30 * ss(b("crack"), b("crack") + 0.2, t)
        pz["head_turn"] = 0
        pz["chest_twist"] = 0
        pz["arm_sr"] = dict(REST_ARM)
        pz["arm_sl"] = {"fwd": 10, "out": 10, "elbow": 20}
        pz["chest_lean"] = -4 + 2 * breath
        face = dict(SF["worried"])
    M.set_steve(E, sp, yaw, pz, face, t)


def cast(E, t, shot, NF, SF):
    noob_anim(E, t, NF)
    steve_anim(E, t, SF)


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
    gain = {"look": 1.6, "walk": 2.6, "tree": 2.6, "punch": 1.3, "float": 1.5, "normal": 1.3}.get(shot, 1.0)
    E.key.data.energy *= gain                                   # faces lit (apply set the base this frame)
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
        wide = c + Vector((0.4, -4.4, -0.35)) + Vector((0.0, 0.25, 0.0)) * u
        ep0 = Vector((0.9, -2.6, E.ground(0.9, -2.6) + 1.2))      # chapter 0's last camera: the same shot goes on
        k = ss(0.8, 2.4, t)
        loc = ep0.lerp(wide, k)
        look = (hn + Vector((0, 0, -0.2))).lerp(c, k)
        return loc, look, lerp(28, 24, k), lerp(3.5, 4.0, k), None, lerp(0.12, 0.05, k)
    if shot == "arrive":
        # Steve's last steps up to the tree, seen from ahead of him: the meadow he crossed behind him
        hs = M.P6._head(E.S.face, E.S.holder)
        d = STEVE_AT - STEVE_FROM
        d = Vector((d.x, d.y, 0)).normalized()
        left = Vector((-d.y, d.x, 0))
        base = STEVE_AT + d * 3.2 - left * 1.2
        loc = Vector((base.x, base.y, E.ground(base.x, base.y) + 1.25))
        return loc, hs + Vector((0, 0, -0.4)), 30, 3.5, None, 0.05
    if shot == "walk":
        # tracking ahead of him, a little to his left: his face as he walks to the tree, the trunk at the right
        n = Vector(E.N.root.location)
        d = (E.punch_at + STAND_BACK) - E.noob0
        d = Vector((d.x, d.y, 0)).normalized()
        left = Vector((-d.y, d.x, 0))
        loc = n + d * 3.2 + left * 1.3 + Vector((0, 0, 1.05))
        return loc, n + Vector((0, 0, 1.05)) + d * 0.3, 28, 4.0, None, 0.09
    if shot == "tree":
        # the Noob on the left third, the trunk on the right third, showing off to us
        c = E.punch_at.lerp(tf, 0.42) + Vector((0, 0, 1.15))
        loc = c + Vector((-0.4, -4.6, 0.1)) + Vector((0.0, 0.2, 0.0)) * u
        return loc, c, 26, 4.0, None, 0.05
    if shot == "punch":
        c = mid + Vector((0, 0, 0.95))
        loc = c + Vector((0.6, -3.6, 0.3))          # side on from the south, a little in front: the Noob left, the fist on the bark at the right
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
        # from the south-east, low, beside the tree: the Noob and Steve facing us as they look up at it, the
        # floating trunk (its gap) between them
        c = Vector((1.0, 0.4, E.ground(1.0, 0.4) + 1.8))
        loc = Vector((5.6, -3.8, E.ground(5.6, -3.8) + 0.6))
        return loc, c, 20, 64.0, None, 0.04
    if shot == "normal":
        # "That's normal." - Steve chest-up, turned to the Noob; the floating tree soft behind
        hs = M.P6._head(E.S.face, E.S.holder)
        sp = steve_pos(E, t)
        d = Vector(E.N.root.location) - sp
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        loc = hs + d * 2.1 - side * 0.45 + Vector((0, 0, -0.1))
        return loc, hs + Vector((0, 0, -0.22)) - side * 0.2, 36, 2.8, None, 0.04
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
        look = E.crack_at + Vector((0, 0, -6.0 + 4.0 * ss(t0, t0 + 1.4, t)))     # the tear in the middle, tilting up to it
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
