"""The movie, chapter 0: Episode 0 "The End", remade in the new look, in 16:9.

Shot for shot on the published Short's own soundtrack and timing
(story/movie/ep00_shots.md). The place is the finale's: the egg of land in the
void, Minecraft's half on +x, the Noob's obby half on -x, the old oak bridge
across the chasm with his rainbow parts at its far end (ep10_p4_build / p6
build it; this chapter loads it finished). So when the finale comes back to
the bridge, the stub and the void, the viewer has been there.

  1 both worlds   2 mine   3 his   4 the seam   5 the sky, reality stops
  6 the erasure   7 the obby   8 "Noob! Run!"   9 "I am running!"
  10 the bridge, side on   11 the sign   12 the two-shot   13 the drop and grab
  14 from below   15 faces, the darkening   16 Null rises   17 "Reality has been
  corrected."   18 the ledge goes   19 the plunge   (black: 24 HOURS EARLIER)
  21 the forest: the first portal, the Noob drops out, "Whoa. Where am I?"

Everything is a function of time, so any frame renders on its own (shards).

    python src/lookdev/movie_ep00.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080]
        [--samples 32] [--times 0.5,3.6]

--res is the picture's height; the width is 16:9.
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_p6_fall as P6                                            # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402

B = {}                                    # the published timeline's beats: name -> (start, end)
G = 9.81

# Episode 0's light: a clear day going to dusk, a peach horizon, the void glowing below
DAY = {"glow": (255, 236, 214), "power": 40.0, "horizon": (255, 214, 188), "mid": (150, 186, 246), "zenith": (58, 118, 226),
       "fill": 1.0, "fill_col": (186, 204, 240)}
# after the darkening: Null's light
DARK = {"glow": (236, 170, 230), "power": 4.0, "horizon": (214, 80, 150), "mid": (110, 46, 120), "zenith": (34, 18, 60),
        "fill": 0.55, "fill_col": (176, 130, 220)}


def b(name, i=0):
    return B[name][i]


def mix_look(a, c, u):
    out = {}
    for k in a:
        if isinstance(a[k], tuple):
            out[k] = tuple(lerp(x, y, u) for x, y in zip(a[k], c[k]))
        else:
            out[k] = lerp(a[k], c[k], u)
    return out


class Ep:
    pass


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    """The finale's finished egg (part 6's build), then this chapter's own things."""
    E = P6.build({"length": 14.1, "beats": {}, "lines": []}, tex_dir, assets, res, samples)
    _recentre_blocks(E)
    sc = E.sc
    sc.render.resolution_x = res * 16 // 9
    sc.render.resolution_y = res
    E.tl = tl
    I = E.I
    from island import BRIDGE_Y
    # nobody here yet: Patch arrives in Episode 4; Null waits in the void
    E.Pt.root.location = (0, 0, -900)
    E.giz.draw([])
    P4._beams(E, [])
    # Steve's pickaxe (Episode 0's Steve carries it)
    from props import sprite_item, hold
    pk = sprite_item("iron_pickaxe", os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets",
                                                  "minecraft", "textures", "item"), px=0.072)
    hold(E.S.arm, pk, "sr", up=25, face=60, collection=[E.S.rig])
    E.pick = pk
    E.hidden0 = {ob.name for ob in E.objs if ob.hide_render}          # parts the finale's build leaves out
    # planks lying flush under the rainbow parts render as a black patch where their faces meet: leave them out
    E.under_rb = set()
    for pc in E.pieces:
        for rb in E.rainbow:
            if rb.kind != "reach" and abs(pc.c0.x - rb.c0.x) < 0.75 and abs(pc.c0.y - rb.c0.y) < 1.6:
                E.under_rb.add(pc.ob.name)
                for o, _ in pc.extra:
                    E.under_rb.add(o.name)
    for rb in E.rainbow:
        if rb.kind != "reach":
            rb.c0 = rb.c0 + Vector((0, 0, -0.015))
        else:                                              # his violet reach starts where the last blue part ends
            rb.c0 = rb.c0 + Vector((0.42, 0, 0.01))
    E.lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    from world import bake_textures
    E.textures = bake_textures(assets)
    _bridge_ends(E)
    _places(E)
    _sign(E, assets)
    _checker(E)
    _erase_plan(E)
    _birds(E)
    _sun(E)
    _cells(E)
    _avatars(E)
    dl = bpy.data.objects.new("dark_light", bpy.data.lights.new("dark_light", "AREA"))
    E.sc.collection.objects.link(dl)
    dl.data.size = 14.0
    dl.data.color = (1.0, 0.22, 0.72)
    dl.data.energy = 0.0
    dl.location = (E.XE - 6.0, E.Y0 - 4.0, E.deck - 12.0)
    dl.rotation_euler = (Vector((E.XE, E.Y0, E.deck)) - Vector(dl.location)).to_track_quat("-Z", "Y").to_euler()
    E.dark_light = dl
    return E


def _recentre_blocks(E):
    """Part 6's bridge blocks are made with transform_apply(scale=True), which on newer Blender also
    bakes the location into the mesh, so every block would sit twice as far out. Put each block's
    mesh back round its origin (no change on the Blender the finale was made with)."""
    from mathutils import Matrix as Mx
    for ob in E.col.objects:
        if ob.type != "MESH" or not len(ob.data.vertices):
            continue
        c = sum((Vector(v.co) for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
        if c.length > 1e-4:
            ob.data.transform(Mx.Translation(-c))
            ob.location = Vector(ob.location) + c


def _places(E):
    """Where everyone stands: Steve under a tree on his half near the bridge, the Noob on a
    plate of his obby near the chasm, where they meet (by the sign, at the stub)."""
    I, XE, deck, Y0 = E.I, E.XE, E.deck, E.Y0
    import numpy as np
    # the trunks: log cells on the Minecraft half near the bridge's end
    v = I.logs.data.vertices
    co = np.empty(len(v) * 3, np.float32)
    v.foreach_get("co", co)
    co = co.reshape(-1, 3) @ np.array(I.logs.matrix_world)[:3, :3].T + np.array(I.logs.matrix_world)[:3, 3]
    best, bd = None, 1e9
    for x, y in {(int(math.floor(p[0])), int(math.floor(p[1]))) for p in co}:
        if x < XE + 4 or abs(y - Y0) > 14:
            continue
        h = I.height(x + 0.5, y - 2.5)
        if h is None:
            continue
        d = math.hypot(x - (XE + 7), y - (Y0 + 4))
        if d < bd:
            best, bd = (x, y), d
    tx, ty = best if best else (XE + 7, Y0 + 4)
    E.tree = Vector((tx + 0.5, ty + 0.5, I.height(tx + 0.5, ty + 0.5) or deck))
    # Steve's spot: in the open on his grass near the bridge's end, an oak of his own just behind him (north),
    # so his close-ups have it over his shoulder and the sky shot sees the sun over the obby clear of it
    sx, sy = XE + STEVE_SPOT[0], Y0 + STEVE_SPOT[1]
    E.steve_home = Vector((sx, sy, I.height(sx, sy) or deck))
    trunks = {(int(math.floor(q[0])), int(math.floor(q[1]))) for q in co}
    best, bd = (sx + 0.5, sy + 5.0), -1.0
    for dx in (-1.5, -0.5, 0.5, 1.5, -2.5, 2.5):
        for dy in (4.5, 5.5, 6.5):
            x, y = sx + dx, sy + dy
            if I.height(x, y) is None:
                continue
            d = min((math.hypot(x - (a + 0.5), y - (c + 0.5)) for a, c in trunks), default=99.0)
            if d > bd:
                best, bd = (x, y), d
    E.tree = _plant_oak(E, *best)
    # the obby plate he dances on: a wide part near the chasm, the bridge's end
    best, bd = None, 1e9
    for p in E.plan.parts:
        if p["kind"] == "bridge" or p.get("shape", "box") != "box":
            continue
        sz, at = p["size"], Vector(p["at"])
        if sz[0] < 2.0 or sz[1] < 2.0 or sz[2] > 3.0:
            continue
        d = (Vector((at.x, at.y)) - Vector((E.rb_far - 11.0, Y0 + 4.0))).length
        if d < bd:
            best, bd = p, d
    if best:
        at, sz = Vector(best["at"]), best["size"]
        E.noob_home = Vector((at.x, at.y, at.z + sz[2] / 2))
    else:
        E.noob_home = Vector((E.rb_far - 3.0, Y0 + 6.0, deck))
    # the bridge: their lanes, where the Noob starts running (the rainbow's far end) and where they meet
    E.null_base = Vector((XE - 12.0, Y0 - 21.0, deck - 12.0))
    E.sky_cam = E.steve_home + Vector(SKY_CAM)
    E.sky_cam.z = (I.height(E.sky_cam.x, E.sky_cam.y) or deck) + SKY_CAM[2]
    _clear_plants(E, [E.sky_cam], 1.5)
    E.y_s, E.y_n = Y0 + 0.5 - 0.5, Y0 + 0.5 + 0.45
    E.x_meet_s, E.x_meet_n = XE - 0.55, XE - 2.0
    _clear_plants(E, [E.steve_home, E.tree, Vector((XE + 1.5, Y0 + 0.5, deck)), Vector((XE + 5.0, Y0 + 1.0, deck)),
                      Vector((XE + 4.0, Y0 - 4.0, deck))], 1.9)


def _plant_oak(E, x, y):
    """One oak on the island (Minecraft blocks, the world's own textures)."""
    from world import bake_textures, material, voxel_mesh, tree
    T = E.textures
    M = {k: bpy.data.materials.get("s_" + k) or material("s_" + k, T[k]) for k in ("oak_log", "oak_log_top")}
    M["oak_leaves"] = bpy.data.materials.get("s_oak_leaves") or material("s_oak_leaves", T["oak_leaves"], alpha=True, rough=0.6,
                                                                          translucent=0.42)
    K = {"oak_log": {"top": M["oak_log_top"], "side": M["oak_log"], "bottom": M["oak_log_top"]},
         "oak_lv": {"top": M["oak_leaves"], "side": M["oak_leaves"], "bottom": M["oak_leaves"]}}
    gx, gy = int(math.floor(x)), int(math.floor(y))
    gz = int(round(E.I.height(gx + 0.5, gy + 0.5) or E.deck))
    cells = {}
    tree(cells, gx, gy, gz, "oak", random.Random(21))
    logs = {k: v for k, v in cells.items() if not v.endswith("_lv")}
    leaves = {k: v for k, v in cells.items() if v.endswith("_lv")}
    voxel_mesh(E.sc, "steve_oak_logs", logs, K)
    voxel_mesh(E.sc, "steve_oak_leaves", leaves, K, keep_leaf_faces=("oak_lv",))
    return Vector((gx + 0.5, gy + 0.5, gz))


def _clear_plants(E, spots, r):
    """Take the grass and flowers out where someone stands or the camera looks past (nothing in front of a face)."""
    import bmesh
    ob = E.I.plants
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = ob.matrix_world
    kill = [f for f in bm.faces if any((Vector(((mw @ f.calc_center_median()).x, (mw @ f.calc_center_median()).y)) -
                                        Vector((c.x, c.y))).length < r for c in spots)]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()


def _sign(E, assets):
    """BRIDGE UNDER MAINTENANCE: an oak sign at the bridge's Minecraft end, facing whoever comes across."""
    from PIL import Image, ImageDraw, ImageFont
    tex = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    oak = Image.open(os.path.join(tex, "oak_planks.png")).convert("RGB").resize((16, 16), Image.NEAREST)
    W_, H_ = 192, 96                                        # board pixels
    im = Image.new("RGB", (W_, H_))
    for x in range(0, W_, 32):
        for y in range(0, H_, 32):
            im.paste(oak.resize((32, 32), Image.NEAREST), (x, y))
    # the letters: bold, a clear gap between the words, blown up with nearest-neighbour so they stay crisp
    txt = Image.new("L", (W_, H_), 0)
    d = ImageDraw.Draw(txt)
    try:
        f = ImageFont.load_default(size=19)
    except TypeError:
        f = ImageFont.load_default()
    for k, line in enumerate(("BRIDGE  UNDER", "MAINTENANCE")):
        w = d.textlength(line, font=f)
        d.text(((W_ - w) / 2, 16 + 36 * k), line, fill=255, font=f, stroke_width=1, stroke_fill=255)
    ink = Image.new("RGB", (W_, H_), (30, 18, 8))
    im.paste(ink, (0, 0), txt)
    im = im.resize((W_ * 4, H_ * 4), Image.NEAREST)
    path = os.path.join(bpy.app.tempdir or "/tmp", "ep00_sign.png")
    im.save(path)
    m = bpy.data.materials.new("sign_board")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path)
    t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    XE, deck = E.XE, E.deck
    # on the stub, beside the lane, the board turned to face the bridge (-x)
    base = Vector((XE + 0.55, E.Y0 + 0.5 + 1.3, deck))
    E.sign_at = base
    bpy.ops.mesh.primitive_cube_add(size=1, location=base + Vector((0, 0, 0.55)))
    post = bpy.context.active_object
    post.name = "sign_post"
    post.scale = (0.12, 0.12, 1.1)
    post.data.materials.append(next((mm for mm in bpy.data.materials if "oak_log" in mm.name),
                                   next((mm for mm in bpy.data.materials if "plank" in mm.name), m)))
    bpy.ops.mesh.primitive_cube_add(size=1, location=base + Vector((0, 0, 1.38)))
    board = bpy.context.active_object
    board.name = "sign_board"
    board.scale = (0.08, 1.5, 0.75)
    # UVs: the -x face carries the text, the rest plain oak (the same image, a corner of it)
    board.data.materials.append(m)
    uv = board.data.uv_layers.active.data
    for poly in board.data.polygons:
        n = poly.normal
        for li in poly.loop_indices:
            vco = board.data.vertices[board.data.loops[li].vertex_index].co
            if n.x < -0.5:
                uv[li].uv = (0.5 - vco.y, vco.z + 0.5)        # seen from -x: +y is to the left
            else:
                uv[li].uv = (0.02 + 0.1 * (vco.y + 0.5), 0.02 + 0.1 * (vco.z + 0.5))
    E.sign = [post, board]


def _checker(E):
    """The missing texture: what the erasure turns things into for an instant before they go."""
    m = bpy.data.materials.new("erase_checker")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ch = nt.nodes.new("ShaderNodeTexChecker")
    ch.inputs["Scale"].default_value = 4.0
    ch.inputs["Color1"].default_value = (1.0, 0.05, 0.9, 1)
    ch.inputs["Color2"].default_value = (0.004, 0.0, 0.006, 1)
    nt.links.new(tc.outputs["Object"], ch.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ch.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 2.5
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    E.checker = m


def _erase_plan(E):
    """Who goes when. The obby's parts on the two erasure beats' ticks (fx_times), far from
    the bridge first; the rainbow behind the running Noob; the oak planks far to near on
    the bridge's own beat; the stub on the ledge's."""
    fx = E.tl.get("fx_times", {})
    XE = E.XE
    rng = random.Random(4)
    E.erase = {}                                           # object name -> time it goes
    obby = [(ob, p) for ob, p in zip(E.objs, E.plan.parts) if p["kind"] != "bridge"]
    # the first wave eats the obby's far side, the second its near side (toward the chasm)
    obby.sort(key=lambda op: op[1]["at"][0])
    n = len(obby)
    far, near = obby[: n // 2], obby[n // 2:]
    E.hold = {}                                            # how long each shows the missing texture before it goes
    ticks = fx.get("erasure", [])
    for k, (ob, p) in enumerate(far):
        if ticks:
            E.erase[ob.name] = ticks[min(len(ticks) - 1, int(k * len(ticks) / max(1, len(far))))] + rng.uniform(0, 0.05)
    # the second wave chases him: what he has just run past goes, a moment after he passes it
    keys = noob_keys(E)
    samples = [(keys[0][0] + 0.02 * i, _track(keys, keys[0][0] + 0.02 * i)[0]) for i in range(int((keys[2][0] - keys[0][0]) / 0.02) + 1)]
    ticks_b = fx.get("erasure_b", [])
    for k, (ob, p) in enumerate(near):
        at = Vector(p["at"])
        passed = next((tt for tt, q in samples if q.x >= at.x - 0.5), None)
        if passed is not None and abs(at.y - E.y_n) < 9.0:
            # spreading out from his path, a beat behind him, so the shot watches it go
            E.erase[ob.name] = max(b("erasure_b") - 0.2, passed + 0.55 + 0.22 * abs(at.y - E.y_n) + rng.uniform(0, 0.45))
        elif ticks_b and rng.random() > 0.3:
            E.erase[ob.name] = ticks_b[min(len(ticks_b) - 1, int(k * len(ticks_b) / max(1, len(near))))] + rng.uniform(0, 0.05)
    # the rainbow: behind him once he's across it; his violet reach (where Steve turns back) last
    for p in E.rainbow:
        passed = next((tt for tt, q in samples if q.x >= p.c0.x), keys[2][0])
        E.erase[p.ob.name] = passed + 0.45 if p.kind != "reach" else 20.8
    # the oak planks: far to near across the bridge's beat; the last ones under their feet as the fall begins
    xs = sorted({p.x for p in E.pieces if p.kind == "plank"})
    a, c = b("bridge_delete"), b("fall") - 0.02
    for p in E.pieces:
        u = (p.x - xs[0]) / max(1, xs[-1] - xs[0])
        tt = lerp(a, c, u ** 0.8) + rng.uniform(-0.03, 0.03)
        E.erase[p.ob.name] = tt
        E.hold[p.ob.name] = 0.1
        for o, _ in p.extra:
            E.erase[o.name] = tt
            E.hold[o.name] = 0.1
    E.stub_gone = b("ledge_gone") + 0.11


def _birds(E):
    """A few birds wheeling over the bridge (they stop dead when reality stops)."""
    m = bpy.data.materials.new("bird")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.03, 1)
    E.birds = []
    rng = random.Random(8)
    for k in range(7):
        bpy.ops.object.empty_add(location=(0, 0, 0))
        root = bpy.context.active_object
        root.name = f"bird_{k}"
        for s in (-1, 1):
            bpy.ops.mesh.primitive_cube_add(size=1)
            w = bpy.context.active_object
            w.scale = (0.5, 0.12, 0.03)
            w.location = (0.22 * s, 0, 0)
            w.data.materials.append(m)
            w.parent = root
            w["side"] = s
        E.birds.append((root, rng.uniform(5, 9), rng.uniform(0, 6.28), rng.uniform(0.25, 0.4), rng.uniform(-1.5, 1.5)))
    E.bird_c = Vector((E.XE - 6.0, E.Y0 + 6.0, E.deck + 16.0))


def _sun(E):
    """Minecraft's square sun, high over the obby, with its square halo."""
    from world import set_sun
    I = E.I
    I.W.sun = I.sun
    # to the south-west of the bridge, high: seen from below the towers in shot 5
    set_sun(I.W, -118, 46, energy=4.2, color=(1.0, 0.94, 0.86))
    I.sun = I.W.sun
    E.to_sun = Vector(I.W.to_sun)
    E.sunq = []
    for name, size, power, col in (("sun_disc", 110.0, 30.0, (1.0, 0.98, 0.9)), ("sun_halo", 190.0, 2.5, (1.0, 0.96, 0.86))):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n_ in list(nt.nodes):
            nt.nodes.remove(n_)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*col, 1)
        em.inputs["Strength"].default_value = power
        if name == "sun_halo":
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx = nt.nodes.new("ShaderNodeMixShader")
            mx.inputs["Fac"].default_value = 0.45
            nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(em.outputs[0], mx.inputs[2])
            nt.links.new(mx.outputs[0], out.inputs["Surface"])
        else:
            nt.links.new(em.outputs[0], out.inputs["Surface"])
        bpy.ops.mesh.primitive_plane_add(size=size)
        ob = bpy.context.active_object
        ob.name = name
        ob.data.materials.append(m)
        ob.visible_shadow = False
        ob.visible_diffuse = False
        ob.visible_glossy = False
        d = 1500.0 if name == "sun_disc" else 1520.0
        ob.location = E.to_sun * d
        ob.rotation_mode = "QUATERNION"
        ob.rotation_quaternion = (-E.to_sun).to_track_quat("Z", "Y")
        E.sunq.append(ob)


def _cells(E):
    """The small dark cubes in the void (the planting rule): Null's cells, faces too small to read."""
    from ep10_new import _cube
    rng = random.Random(12)
    E.cells = []
    variants = ["smile", "scared", "smile", "smile"]
    for k in range(10):
        ob = _cube(E.X.col, variants[k % len(variants)], (60, 48, 40), f"void_cell_{k}")
        s = rng.uniform(0.25, 0.45)
        ob.scale = (s, s, s)
        c = Vector((E.XE - rng.uniform(3, 18), E.Y0 + rng.uniform(-4, 14), E.deck - rng.uniform(9, 30)))
        E.cells.append((ob, c, Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.1, 0.1), rng.uniform(-0.25, -0.05))),
                        Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)))))
    # the void's debris under the hang: dark blocks and a few torn-off pieces of both worlds, drifting,
    # that the plunge falls past (Episode 0's falling shot)
    dark = bpy.data.materials.new("void_block")
    dark.use_nodes = True
    bd = dark.node_tree.nodes["Principled BSDF"]
    bd.inputs["Base Color"].default_value = (0.012, 0.006, 0.02, 1)
    bd.inputs["Roughness"].default_value = 0.5
    worldish = [m for m in bpy.data.materials if any(k in m.name for k in ("dirt", "plank", "grass", "stone"))][:4]
    for k in range(30):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"void_block_{k}"
        sz = rng.uniform(0.35, 1.4) if k % 5 else rng.uniform(1.6, 2.2)
        ob.scale = (sz, sz, sz)
        ob.data.materials.append(worldish[k % len(worldish)] if (worldish and k % 4 == 1) else dark)
        c = Vector((E.XE - 1.2 + rng.uniform(-6, 6), E.Y0 + 0.5 + rng.uniform(-6, 6), E.deck - rng.uniform(9, 48)))
        if abs(c.x - (E.XE - 2.2)) < 4.5 and abs(c.y - (E.Y0 + 1.5)) < 4.5:
            c.x -= 6.5                                     # never through or against the two of them
        E.cells.append((ob, c, Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), rng.uniform(0.05, 0.3))),
                        Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4)))))


def _avatars(E):
    """Three of the obby's other players (shot 7), in their own colours."""
    import noob as NB
    from stage import build_noob_char
    keep = (NB.BLUE, NB.GREEN)
    E.avatars = []
    for k, (shirt, pants) in enumerate((((220, 60, 60), (40, 40, 50)), ((150, 80, 220), (230, 230, 235)),
                                        ((250, 140, 30), (50, 90, 160)))):
        NB.BLUE, NB.GREEN = shirt, pants
        E.avatars.append(build_noob_char(E.sc, name=f"avatar_{k}"))
    NB.BLUE, NB.GREEN = keep
    # their course: plates of the obby's far side, hopped in turn
    plates = []
    for p in E.plan.parts:
        if p["kind"] == "bridge" or p.get("shape", "box") != "box":
            continue
        sz, at = p["size"], Vector(p["at"])
        if 1.2 <= sz[0] <= 4.0 and 1.2 <= sz[1] <= 4.0:
            plates.append(at + Vector((0, 0, sz[2] / 2)))
    plates.sort(key=lambda v: (v.y, v.x))
    E.course = plates[:6] if len(plates) >= 6 else plates


# ------------------------------------------------------------------ the shots
SHOTS = [("both", "open"), ("mine", "vo_2"), ("his", "vo_3"), ("seam", "vo_4"), ("sky", "vo_5"),
         ("erase_wide", "erasure"), ("obby", ("erasure", 1.3)), ("shout", "steve_run"), ("runs", "noob_running"),
         ("side", ("erasure_b", 1.6)), ("sign", ("erasure_b", 2.7)), ("two", ("noob_bridge", 1.0)),
         ("drop", ("bridge_delete", 0.3)), ("below", ("grab", 0.6)), ("faces", "steve_no"),
         ("reveal", ("steve_what", 1.442)), ("null", "null_1"), ("ledge", "ledge_gone"),
         ("plunge", ("noob_scream", 0.5)), ("black", "black"), ("forest", "forest")]


def shot_bounds():
    out = []
    for name, ref in SHOTS:
        t = b(ref) if isinstance(ref, str) else b(ref[0]) + ref[1]
        out.append((name, t))
    return out


def which(t):
    bs = shot_bounds()
    for k, (name, t0) in enumerate(bs):
        t1 = bs[k + 1][1] if k + 1 < len(bs) else 1e9
        if t < t1:
            return name, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


# ------------------------------------------------------------------ per frame
def apply(E, t):
    from world import set_sky
    from stage import place_null_lights
    I = E.I
    # the light: day, then Null's dusk from the darkening
    dk = ss(b("darken"), b("darken", 1), t)
    set_sky(I.W, mix_look(DAY, DARK, dk))
    I.W.sun.data.energy = lerp(4.2, 0.6, dk)
    E.sc.view_settings.exposure = lerp(-0.05, -0.9, dk)
    E.dark_light.data.energy = 9000.0 * dk
    for ob in E.sunq:
        ob.hide_render = dk > 0.6
    # the world's pieces: the erasure
    frozen = b("freeze") <= t < b("erasure")
    for ob in E.objs:
        ob.hide_render = ob.name in E.hidden0
        if ob.name not in E.hidden0:
            _erase_state(E, ob, t)
    for p in E.pieces + E.rainbow:
        p.place(-100.0)
        _erase_state(E, p.ob, t)
        for o, _ in p.extra:
            _erase_state(E, o, t)
        if p.ob.name in E.under_rb:
            p.ob.hide_render = True
    gone = t >= E.stub_gone
    flash = E.stub_gone - 0.11 <= t < E.stub_gone
    E.stub.hide_render = gone
    _swap(E.stub, E.checker if flash else None)
    for o in E.sign:
        o.hide_render = gone
    # birds (they stop when reality does), the void's cells
    tb = min(t, b("freeze")) if t < b("erasure") else t - (b("erasure") - b("freeze"))
    for root, r, ph, w, dz in E.birds:
        a = ph + w * tb
        root.location = E.bird_c + Vector((r * math.cos(a), r * math.sin(a), dz + 0.4 * math.sin(2 * a)))
        root.rotation_euler = (0, 0, a + math.pi / 2)
        flap = 0.0 if frozen else math.sin(tb * 11.0 + ph * 3)
        for w_ in root.children:
            w_.rotation_euler = (0.5 * flap * w_["side"], 0, 0)
        root.hide_render = dk > 0.5
    for ob, c, v, wv in E.cells:
        ob.location = c + v * t
        ob.rotation_euler = tuple(wv * t)
        if ob.name.startswith("void_block"):              # the void's debris: torn off as the world goes (from the bridge on)
            ob.hide_render = t < b("bridge_delete")
    # the cast and the camera
    name, t0, t1 = which(t)
    cast(E, t, name)
    if t >= E.stub_gone:
        _clear_fall(E, t)
    _null(E, t, name)
    place_null_lights(E.X, fade=ss(b("null_rise") - 0.4, b("null_rise") + 1.0, t) if name not in ("forest",) else 0.0)
    E.X.glow_strength.default_value *= 0.35                 # his halo: a glow behind him, not a wall of light
    _avatars_at(E, t, name)
    camera(E, t, name, t0, t1)


def _clear_fall(E, t):
    """In the plunge, keep the void's debris off the two of them on screen (the camera looks down past them):
    a block under either one is pushed out sideways until it clears them."""
    s = t - E.stub_gone
    z = E.deck - 2.0 - 0.5 * 7.0 * s * s
    bpy.context.view_layer.update()
    # both ends of each body (they lie flat on the air): feet and head
    pts = [Vector(E.S.holder.matrix_world.translation), P6._head(E.S.face, E.S.holder),
           Vector(E.N.root.matrix_world.translation), P6._head(E.N.face)]
    pts += [a.lerp(c, 0.5) for a, c in ((pts[0], pts[1]), (pts[2], pts[3]))]
    bodies = [Vector((q.x, q.y)) for q in pts]
    for ob, c, v, wv in E.cells:
        if not ob.name.startswith("void_block"):
            continue
        p = Vector(ob.location)
        if p.z > z + 1.5:
            continue
        for q in bodies:
            d = Vector((p.x, p.y)) - q
            r = 1.3 + 0.9 * ob.scale.x
            if d.length < r:
                d = d.normalized() if d.length > 1e-3 else Vector((-1.0, 0.0))
                p.x, p.y = q.x + d.x * r, q.y + d.y * r
        ob.location = p


def _swap(ob, mat):
    """Show an object in the missing texture (mat) or its own material (None)."""
    if not ob.material_slots:
        return
    if "own_mats" not in ob:
        ob["own_mats"] = [s.material.name if s.material else "" for s in ob.material_slots]
    for k, s in enumerate(ob.material_slots):
        own = ob["own_mats"][k]
        s.material = mat if mat is not None else (bpy.data.materials.get(own) if own else None)


def _erase_state(E, ob, t):
    te = E.erase.get(ob.name)
    if te is None:
        _swap(ob, None)
        return
    if t >= te + E.hold.get(ob.name, 0.3):
        ob.hide_render = True
        _swap(ob, None)
    elif t >= te:
        ob.hide_render = False
        _swap(ob, E.checker)
    else:
        _swap(ob, None)


# ------------------------------------------------------------------ the cast
def _face(prefix_keys, defaults, face):
    out = {}
    for k, v in face.items():
        if k.startswith("both_"):
            for e in prefix_keys:
                out[f"{e}_{k[5:]}"] = v
        elif not k.startswith("bb_"):
            out[k] = v
    return out


def set_steve(E, loc, yaw, pose_d, face, t, grip=None, grip_sides=("sr",)):
    from pose import pose
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS
    from brows import set_brows
    from ep09_new import flat, unflat, talk
    S = E.S
    sp = flat(E.lib["idle (Benly 2.2)"])
    sp.update(flat(pose_d))
    pose(S.arm, unflat(sp))
    S.holder.rotation_euler = (0, 0, math.radians(yaw))
    S.holder.location = loc
    if grip is not None:
        bpy.context.view_layer.update()
        hands = [P6._steve_hand(S, sd) for sd in grip_sides]
        hc = sum(hands, Vector()) / len(hands)
        S.holder.location = Vector(loc) + (grip - hc)
    fs = {f"{e}_{k}": v for e in EYES for k, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    fs.update(_face(EYES, EYE_DEFAULTS, face))
    talk(fs, E.mouth.get("steve", {}).get(int(round(t * FPS))))
    set_face(S.face, fs)
    for ob_ in S.brows.values():
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(S.brows, {k: v for k, v in face.items() if k.startswith("bb_")})


def set_noob(E, loc, yaw, pose_d, face, t, grip=None, grip_sides=("sl", "sr"), N=None):
    from noob import pose_noob
    from faceplate import set_face, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from ep09_new import talk
    N = N or E.N
    pz = dict(pose_d)
    pz["root_yaw"] = yaw
    pose_noob(N, pz)
    N.root.location = loc
    if grip is not None:
        bpy.context.view_layer.update()
        hands = [P6._noob_hand(N, sd) for sd in grip_sides]
        hc = sum(hands, Vector()) / len(hands)
        N.root.location = Vector(loc) + (grip - hc)
    if N is not E.N:
        return
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    fn.update(_face(NOOB_EYES, NOOB_EYE_DEFAULTS, face))
    talk(fn, E.mouth.get("noob", {}).get(int(round(t * FPS))))
    set_face(N.face, fn)


def _steve_foot(E, side="sl"):
    from pose import FOOT
    S = E.S
    pb = S.arm.pose.bones[FOOT[side]]
    return S.holder.matrix_world @ S.arm.matrix_world @ pb.head


def run_cycle(ph, k=1.0, steve=True):
    sw = math.sin(ph)
    if steve:
        return {"chest_lean": 16 * k, "chest_twist": 10 * sw * k, "head_nod": -6, "hips_drop": 0.14 * k,
                "arm_sl": {"fwd": -60 * sw * k, "elbow": 85 * k, "out": 8}, "arm_sr": {"fwd": 60 * sw * k, "elbow": 85 * k, "out": 8},
                "foot_sl": {"y": -0.5 * sw * k, "z": max(0.0, 0.45 * math.sin(ph + 1.2)) * k},
                "foot_sr": {"y": 0.5 * sw * k, "z": max(0.0, 0.45 * math.sin(ph + 1.2 + math.pi)) * k}}
    # the Noob runs Roblox style: arms flung, legs stiff
    return {"chest_lean": 10 * k, "head_nod": -2, "arm_sl": {"fwd": -70 * sw * k, "out": 12}, "arm_sr": {"fwd": 70 * sw * k, "out": 12},
            "leg_sl": {"fwd": 48 * sw * k}, "leg_sr": {"fwd": -48 * sw * k}}


STEVE_SPOT = (3.5, 3.5)                   # Steve's spot, from the stub (x) and the bridge's line (y)
SKY_FACE = -35.0                          # shot 5: Steve's facing, degrees off straight at the camera
SKY_CAM = (5.0, 2.0, 0.5)                 # shot 5's camera, from Steve's spot: he is small at the bottom left
NOOB_GLANCE = -45.0                       # shot 10: the Noob turned this far toward the side camera (we see his face)
STEVE_GLANCE = -40.0                      # shot 10: Steve, running back, turned toward the side camera too
X_M = -1.0                                # where Steve meets the Noob on the bridge (x), before they run back


def _track(keys, t):
    """Piecewise-linear path through (time, point) keys; returns (point, moving)."""
    if t <= keys[0][0]:
        return keys[0][1].copy(), False
    for (t0, a), (t1, c) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            return a.lerp(c, u), (c - a).length > 0.05
    return keys[-1][1].copy(), False


def noob_keys(E):
    """Off his plate, across his obby (passing the camera of shot 9), onto the bridge, on to the
    Minecraft end where Steve meets him, and with Steve to the sign."""
    a = E.noob_home
    off = Vector((a.x + 1.2, E.y_n, E.deck))
    end = Vector((E.rb_far - 0.3, E.y_n, E.deck))
    meet = Vector((X_M - 2.0, E.y_n, E.deck))           # a step behind Steve (the Short's order: Steve leads to the Minecraft end)
    stop = Vector((E.x_meet_n, E.y_n, E.deck))
    return [(b("noob_running") - 0.2, a), (b("noob_running") + 0.15, off), (19.0, end), (20.5, meet),
            (b("noob_bridge") - 0.05, stop)]


def steve_keys(E):
    """From under his tree to the bridge's Minecraft end, out along the planks to the Noob, then back."""
    a = E.steve_home
    lip = Vector((E.XE + 1.2, E.y_s, E.deck))
    meet = Vector((X_M - 0.2, E.y_s, E.deck))
    stop = Vector((E.x_meet_s, E.y_s, E.deck))
    return [(18.3, a), (19.05, lip), (20.2, meet), (20.5, meet), (b("noob_bridge") - 0.1, stop)]


def noob_track(E, t):
    p, moving = _track(noob_keys(E), t)
    hop_a, hop_b = b("noob_running") - 0.2, b("noob_running") + 0.15
    if hop_a < t < hop_b:                                # off his plate: a hop down
        u = (t - hop_a) / (hop_b - hop_a)
        p.z = lerp(E.noob_home.z, E.deck, u) + 0.5 * math.sin(math.pi * u)
    return p, (t - hop_a) * 2.9 * 2 * math.pi, moving


def steve_track(E, t):
    p, moving = _track(steve_keys(E), t)
    if p.x > E.XE + 0.2:                                 # on his grass
        p.z = E.I.height(p.x, p.y) or E.deck
    return p, (t - b("steve_run", 1)) * 2.7 * 2 * math.pi, moving


# the hang: Steve by his right hand on the stub's edge, turned out to the void (we see the faces);
# the Noob below him, both hands round Steve's ankle, turned out too
YAW_HANG = -55.0
HANG_S1 = {"chest_lean": -6, "head_nod": -14, "arm_sr": {"fwd": 196, "out": 6, "elbow": 3},
           "arm_sl": {"fwd": 22, "out": 24, "elbow": 28}, "foot_sl": {"y": 0.05, "z": 0.0}, "foot_sr": {"y": -0.12, "z": 0.06}}
HANG_N1 = {"chest_lean": -6, "head_nod": -24, "head_tilt": -10, "arm_sr": {"fwd": 176, "out": 6},
           "arm_sl": {"fwd": 120, "out": 35}, "leg_sl": {"fwd": 4}, "leg_sr": {"fwd": -4}}
HANG_N_ROLL = 16.0                         # degrees: hanging from his right hand, his body swings under it


def _noob_arm_top(N, sides=("sr",)):
    """The top of his raised arm(s) (his hand, when the arm is up), in the world."""
    tops = []
    for side in sides:
        pts = []
        for ch in N.arms[side].children_recursive:
            if ch.type == "MESH":
                pts += [ch.matrix_world @ Vector(c) for c in ch.bound_box]
        if pts:
            zmax = max(q.z for q in pts)
            top = [q for q in pts if q.z > zmax - 0.05]
            tops.append(sum(top, Vector()) / len(top))
    return sum(tops, Vector()) / len(tops)


def hang_noob(E, t, pose_d, face, yaw, wrap=0.12):
    """Place the Noob so his raised hands close round Steve's left ankle."""
    bpy.context.view_layer.update()
    foot = _steve_foot(E, "sl")
    set_noob(E, Vector((foot.x, foot.y, foot.z - 2.4)), yaw, pose_d, face, t)
    E.N.root.rotation_mode = "XYZ"
    E.N.root.rotation_euler = (0.0, math.radians(HANG_N_ROLL), E.N.root.rotation_euler[2])
    bpy.context.view_layer.update()
    top = _noob_arm_top(E.N)
    target = foot + Vector((-0.12, 0.0, wrap))
    E.N.root.location = Vector(E.N.root.location) + (target - top)
    return foot


def cast(E, t, shot):
    from ep09_new import SF, NF
    deck, XE = E.deck, E.XE
    t_f, t_g = b("fall"), b("grab")
    # ---------------------------------------------------------------- Steve
    yaw_home = math.degrees(math.atan2(-(E.noob_home.x - E.steve_home.x), (E.noob_home.y - E.steve_home.y))) - 180
    if t < t_f:
        loc, ph, running = steve_track(E, t)
        keys = steve_keys(E)
        if running:
            p = run_cycle(ph)
            yaw = -90.0 if t < keys[2][0] else 90.0 + (STEVE_GLANCE if shot == "side" else 0.0)
            if keys[1][0] > t:                               # across his grass to the lip
                d = keys[1][1] - keys[0][1]
                yaw = math.degrees(math.atan2(d.x, -d.y))
            face = dict(SF["scared"])
        elif keys[2][0] <= t < keys[3][0] + 0.05:
            # he reaches the Noob and turns back: head, shoulders, hips, a step
            u = ss(keys[2][0], keys[3][0], t)
            yaw = lerp(-90.0, 90.0, u)
            p = {"head_turn": 40 * (1 - ss(keys[2][0], keys[2][0] + 0.15, t)), "chest_lean": 10,
                 "arm_sl": {"fwd": 60, "out": 10, "elbow": 30}, "foot_sl": {"y": 0.3 * math.sin(math.pi * u), "z": 0.15 * math.sin(math.pi * u)}}
            face = dict(SF["scared"])
        elif t < keys[0][0] + 0.01:
            # under his tree: calm for the narration, alarmed from the erasure, shouting "Noob! Run!"
            p = {"head_turn": -14, "arm_sr": {"fwd": 8, "out": 6, "elbow": 20}}
            yaw = yaw_home * 0.35
            alarm = ss(b("erasure") + 0.2, b("erasure") + 0.8, t)
            face = dict(SF["neutral"]) if alarm < 0.5 else dict(SF["scared"])
            if b("vo_5") <= t < b("erasure"):
                # shot 5: three-quarter to the camera, face up to the sky (we see his face from below)
                c = E.sky_cam - E.steve_home
                c = Vector((c.x, c.y, 0)).normalized()
                a_ = math.radians(SKY_FACE)
                f = Vector((c.x * math.cos(a_) - c.y * math.sin(a_), c.x * math.sin(a_) + c.y * math.cos(a_), 0))
                yaw = math.degrees(math.atan2(f.x, -f.y))
                p = {"head_nod": -26, "chest_lean": -5, "arm_sr": {"fwd": 8, "out": 6, "elbow": 20}, "arm_sl": {"fwd": 6, "out": 10, "elbow": 15}}
                face = dict(SF["amazed"]) if t < b("freeze") else dict(SF["stunned"])
            if b("steve_run") - 0.1 <= t < b("steve_run", 1) + 0.2:
                p = {"chest_lean": 6, "head_nod": -6, "head_turn": -20, "arm_sl": {"fwd": 40, "out": 30, "elbow": 30},
                     "arm_sr": {"fwd": 10, "out": 8, "elbow": 20}}
                face = dict(SF["scared"])
        else:
            # at the sign: deadpan, eyes sliding to the Noob
            p = {"head_turn": 24, "head_nod": 4, "arm_sl": {"fwd": 22, "out": 16, "elbow": 40}, "arm_sr": {"fwd": 14, "out": 10, "elbow": 30}}
            yaw = lerp(90.0, 0.0, ss(b("noob_bridge") - 0.1, b("noob_bridge") + 0.35, t))
            face = dict(SF["flat"])
            face.update({"both_ps": 0.7, "both_px": 0.45})
            if t >= b("bridge_delete"):
                face = dict(SF["scared"])
        set_steve(E, loc, yaw, p, face, t)
    elif t < E.stub_gone:
        grip = Vector((E.grip_x, E.y_s, deck + 0.07))
        p = json.loads(json.dumps(HANG_S1))
        face = dict(SF["scared"])
        if t < t_g:
            # the planks are gone under him: he drops, turning, his right arm going up for the edge
            u = ss(t_f, t_g, t)
            s0 = t - t_f
            p["arm_sr"] = {"fwd": lerp(60, 196, u), "out": 6, "elbow": lerp(30, 3, u)}
            p["arm_sl"] = {"fwd": lerp(60, 22, u), "out": 30, "elbow": 20}
            start = Vector((E.x_meet_s, E.y_s, deck - 0.5 * G * s0 * s0))
            set_steve(E, start, lerp(0.0, YAW_HANG, u), p, face, t)
            if u > 0.6:                                    # his hand finds the edge
                bpy.context.view_layer.update()
                h = P6._steve_hand(E.S, "sr")
                k = ss(0.6, 1.0, u)
                E.S.holder.location = Vector(E.S.holder.location) + (grip - h) * k
        else:
            s = t - t_g
            p["chest_lean"] = -6 - 10 * math.exp(-6.0 * s) * math.cos(8.5 * s)
            sway = 0.06 * math.exp(-1.0 * s) * math.sin(3.0 * s)
            if t >= b("steve_no") - 0.2:
                face = dict(SF["flat"])
            if t >= b("look_down"):
                face = dict(SF["scared"])
                p["head_nod"] = lerp(-14, 26, ss(b("look_down"), b("look_down", 1), t))
            set_steve(E, Vector((E.grip_x - 0.5, E.y_s + sway, deck - 2.0)), YAW_HANG, p, face, t, grip=grip, grip_sides=("sr",))
    else:
        _falling(E, t, "S")
    # ---------------------------------------------------------------- the Noob
    if t < t_f:
        loc, ph, running = noob_track(E, t)
        if running:
            p = run_cycle(ph, steve=False)
            keys = noob_keys(E)
            d = keys[2][1] - keys[1][1]
            yaw = 90.0 if t > keys[2][0] - 0.3 else math.degrees(math.atan2(d.x, -d.y))
            if shot == "side":
                yaw += NOOB_GLANCE                          # turned a little toward the side camera (we see his face)
            face = dict(NF["shout"]) if t < b("noob_running", 1) + 0.1 else dict(NF["scared"])
        elif t < b("noob_running"):
            # dancing on his plate (Episode 0's bounce); he stops dead when reality does
            tf = min(t, b("freeze")) if t < b("erasure") else t - (b("erasure") - b("freeze"))
            u = tf * 1.5 * 2 * math.pi
            bounce = 0.55 * 0.5 * abs(math.sin(u))
            loc = loc + Vector((0, 0, 0.18 * bounce))
            p = {"chest_lean": -4, "head_tilt": 8 * math.sin(u), "arm_sl": {"out": 120 + 40 * math.sin(u), "fwd": 20},
                 "arm_sr": {"out": 120 - 40 * math.sin(u), "fwd": 20}, "leg_sl": {"fwd": 14 * math.sin(u)}, "leg_sr": {"fwd": -14 * math.sin(u)}}
            yaw = 20.0
            face = dict(NF["happy"])
            if t >= b("erasure") + 0.3:
                p = {"chest_lean": -6, "head_nod": -14, "head_turn": 20, "arm_sl": {"out": 20}, "arm_sr": {"out": 20}}
                face = dict(NF["confused"])
        else:
            # at the sign, reading it, delighted
            p = {"head_turn": -10, "head_nod": -8, "arm_sl": {"fwd": 30, "out": 6}, "arm_sr": {"fwd": 20, "out": 6}}
            yaw = 90.0
            face = dict(NF["happy"]) if t < b("bridge_delete") else dict(NF["shock"])
        set_noob(E, loc, yaw, p, face, t)
    elif t < E.stub_gone:
        p = json.loads(json.dumps(HANG_N1))
        face = dict(NF["scared"])
        if t < t_g + 0.12:
            # he drops a little faster (heavier, no hold), arms up, and catches Steve's ankle
            u = ss(t_f, t_g + 0.12, t)
            s0 = t - t_f
            p["arm_sl"] = {"fwd": lerp(70, 120, u), "out": 35}
            p["arm_sr"] = {"fwd": lerp(70, 176, u), "out": 6}
            free = Vector((E.x_meet_n + 0.4 * u, E.y_n, deck - 0.5 * G * 1.15 * s0 * s0))
            set_noob(E, free, lerp(90.0, YAW_HANG, u), p, face, t)
            if u > 0.55:
                bpy.context.view_layer.update()
                at_free = Vector(E.N.root.location)
                hang_noob(E, t, p, face, lerp(90.0, YAW_HANG, u))
                E.N.root.location = at_free.lerp(Vector(E.N.root.location), ss(0.55, 1.0, u))
        else:
            s = t - t_g
            if t >= b("noob_respawn") - 0.1:
                face = dict(NF["confused"])
            if t >= b("noob_oh") - 0.15:
                face = dict(NF["worried"])
            if t >= b("look_down"):
                face = dict(NF["scared"])
                p["head_nod"] = lerp(-24, 26, ss(b("look_down"), b("look_down", 1), t))
            p["leg_sl"] = {"fwd": 4 + 8 * math.exp(-0.8 * s) * math.sin(2.6 * s)}
            p["leg_sr"] = {"fwd": -4 - 8 * math.exp(-0.8 * s) * math.sin(2.6 * s + 1.0)}
            hang_noob(E, t, p, face, YAW_HANG)
    else:
        _falling(E, t, "N")


def _falling(E, t, k):
    """Off the erased ledge: falling away into the void on their backs, faces up, arms flailing, screaming."""
    from ep09_new import SF, NF
    s = t - E.stub_gone
    z0 = E.deck - 2.0
    z = z0 - 0.5 * 7.0 * s * s
    tip = ss(0.0, 0.5, s)                                    # from hanging upright to lying on the air
    wob = 0.18 * math.sin(s * 3.1 + (0.0 if k == "S" else 1.3))
    fl = math.sin(s * 9.0)
    if k == "S":
        p = {"chest_lean": -10, "head_nod": -20, "arm_sl": {"fwd": 150 + 20 * fl, "out": 40}, "arm_sr": {"fwd": 160 - 20 * fl, "out": 30},
             "foot_sl": {"y": 0.2, "z": 0.0}, "foot_sr": {"y": -0.15, "z": 0.0}}        # legs straight (no bent knee)
        set_steve(E, Vector((E.grip_x - 0.6 - 0.6 * s, E.y_s, z)), YAW_HANG, p, dict(SF["scared"]), t)
        E.S.holder.rotation_euler = (math.radians(-80) * tip + wob, 0.0, math.radians(YAW_HANG))
    else:
        p = {"chest_lean": -10, "head_nod": -20, "arm_sl": {"fwd": 160 + 15 * fl, "out": 50}, "arm_sr": {"fwd": 140 - 15 * fl, "out": 60},
             "leg_sl": {"fwd": 30}, "leg_sr": {"fwd": -20}}
        set_noob(E, Vector((E.grip_x - 2.4 - 0.9 * s, E.y_s + 2.1, z - 2.2)), YAW_HANG, p, dict(NF["shout"]), t)
        E.N.root.rotation_euler = (math.radians(-80) * tip - wob, 0.0, E.N.root.rotation_euler[2])


def _avatars_at(E, t, shot):
    """Three players hopping across the obby's plates (shot 7), until the plates go."""
    far = Vector((0, 0, -900))
    course = E.course
    for k, A in enumerate(E.avatars):
        if shot not in ("obby", "erase_wide", "both") or len(course) < 2:
            A.root.location = far
            continue
        ph = (t - b("erasure")) * 1.6 + k * 0.7
        i = int(math.floor(ph)) % (len(course) - 1)
        u = ph - math.floor(ph)
        a, c = course[i], course[i + 1]
        p = a.lerp(c, u)
        p.z = lerp(a.z, c.z, u) + 1.6 * math.sin(math.pi * u)
        d = c - a
        yaw = math.degrees(math.atan2(d.x, -d.y))
        pz = {"arm_sl": {"out": 120, "fwd": 30}, "arm_sr": {"out": 120, "fwd": 30}, "leg_sl": {"fwd": 25}, "leg_sr": {"fwd": -15}} \
            if 0.1 < u < 0.9 else {"arm_sl": {"fwd": 20}, "arm_sr": {"fwd": -20}}
        set_noob(E, p, yaw, pz, {}, t, N=A)


# ------------------------------------------------------------------ Null
def _null(E, t, shot):
    from null import null_smile, cells_look
    X = E.X
    deck, XE = E.deck, E.XE
    if t < b("null_rise") - 0.2 or shot in ("forest", "black"):
        X.root.location = (0, 0, -2000)
        return
    u = ss(b("null_rise"), b("null_rise", 1) + 0.4, t)
    k = 1.6
    X.root.scale = (k, k, k)
    base = E.null_base
    X.root.location = base + Vector((0, 0, lerp(-34.0, 0.0, u) + 0.25 * math.sin(t * 1.3)))
    d = Vector((XE - 0.3, E.y_s, 0)) - Vector((base.x, base.y, 0))
    yaw = math.degrees(math.atan2(d.x, -d.y))                 # facing the two of them on the stub (he faces -y)
    X.root.rotation_euler = (math.radians(6), 0, math.radians(yaw))
    reach = ss(b("null_hand"), b("null_hand", 1), t)
    # arms hanging at his sides (long, the claws dripping), the left one lifting toward the ledge on null_hand
    X.arms["sl"].rotation_euler = (math.radians(-8 - 70 * reach), math.radians(10 - 4 * reach), 0)
    X.forearms["sl"].rotation_euler = (math.radians(-10 * (1 - reach)), 0, 0)
    X.arms["sr"].rotation_euler = (math.radians(-8), math.radians(-10), 0)
    X.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0.9 * t)
    X.orbit2.rotation_euler = (math.radians(-12), math.radians(14), -0.6 * t)
    null_smile(1.0)
    # his cells keep their faces dark: in Episode 0 nobody knows what he is made of (the finale shows it)
    cells_look(awake=0.0)


# ------------------------------------------------------------------ the camera
def camera(E, t, shot, t0, t1):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    loc, look, lens, fstop, focus, shake, up = _cam(E, t, shot, t0, t1)
    y1, p1, r1 = handheld(t, shake)
    q = P6.look_quat(look - loc, up) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.use_dof = fstop < 30
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.key.location = loc + Vector((0.6, 0.0, 1.6))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus distance or None, handheld amount, up)"""
    XE, deck, Y0 = E.XE, E.deck, E.Y0
    up = Vector((0, 0, 1))
    u = ss(t0, t1, t) if t1 < 1e8 else 0.0
    hs = P6._head(E.S.face, E.S.holder)
    hn = P6._head(E.N.face)
    if shot in ("both", "erase_wide"):
        # high and wide over the egg: the Noob's obby left, Minecraft right, the bridge across the chasm, the void
        loc = Vector((XE - 24.0, Y0 - 44.0, deck + 20.0)).lerp(Vector((XE - 22.0, Y0 - 40.0, deck + 18.5)), u)
        return loc, Vector((XE - 6.0, Y0 + 12.0, deck + 1.0)), 22, 64.0, None, 0.0, up
    if shot in ("mine", "shout"):
        # Steve from the waist up under his tree, three-quarter front
        f = hs + Vector((0, 0, -0.35))
        d = Vector((-0.55, -1.0, 0.05)).normalized()
        dist = lerp(2.9, 2.75, u) if shot == "mine" else 2.6
        return f + d * dist, f + Vector((0.25, 0, 0.05)), 40, 2.8, None, 0.06 if shot == "mine" else 0.25, up
    if shot == "his":
        c = E.noob_home + Vector((0, 0, 1.2))
        loc = c + Vector((2.2, -4.6, 0.6)) + Vector((-0.2, 0.3, 0)) * u
        return loc, c + Vector((0.5, 0, 0)), 32, 4.0, None, 0.06, up
    if shot == "seam":
        # low, from under the bridge's level, across the chasm: the bridge from one world to the other
        mid = Vector((0.5 * (XE + E.rb_far), Y0 + 0.5, deck))
        loc = mid + Vector((-0.5, -24.0, -3.0)) + Vector((0, 0.6, 0.15)) * u
        return loc, mid + Vector((0, 0, 0.6)), 40, 64.0, None, 0.0, up
    if shot == "sky":
        # worm's-eye from the obby, up past its towers to the square sun
        # from the Minecraft side of the chasm, low: the obby's towers below, the sun above them, Steve small
        foot = E.sky_cam + Vector((-0.5, -0.2, 0.25)) * u
        d = Vector((E.to_sun.x, E.to_sun.y, 0)).normalized()
        look = foot + d * 10.0 + Vector((0, 0, 10.0 * math.tan(math.radians(20))))
        return foot, look, 17, 64.0, None, 0.0, up
    if shot == "obby":
        if E.course:
            c = sum(E.course, Vector()) / len(E.course)
        else:
            c = E.noob_home
        loc = c + Vector((4.0, -9.5, 1.0)) + Vector((-1.0, 0.0, 0.0)) * u
        return loc, c + Vector((0, 0, 1.4)), 26, 64.0, None, 0.12, up
    if shot == "runs":
        # on the bridge ahead of him: he runs at us on the rainbow, the bridge erasing behind him; he passes us
        pass_at, _, _ = noob_track(E, b("noob_running", 1) + 0.15)
        cam = Vector((pass_at.x, E.y_n - 1.1, deck + 1.25))
        start, _, _ = noob_track(E, b("noob_running") + 0.3)
        look = Vector((start.x, E.y_n, deck + 1.1))
        return cam, look, 30, 4.5, max(1.2, (hn - cam).length), 0.25, up
    if shot == "side":
        # wide, side on, from below the deck's level: both running to the bridge's Minecraft end, the void below
        mid = Vector((XE - 2.5, Y0 + 0.5, deck))
        loc = mid + Vector((-1.0, -10.5, 0.4)) + Vector((-0.3, 0.3, 0)) * u
        return loc, mid + Vector((0.6, 0, 0.9)), 28, 64.0, None, 0.1, up
    if shot == "sign":
        c = E.sign_at + Vector((0, 0, 1.38))
        loc = c + Vector((-1.45, 1.35, -0.1)) + Vector((0, -0.06, 0)) * u
        return loc, c + Vector((0, -0.1, -0.08)), 32, 3.2, None, 0.08, up
    if shot == "two":
        # the two of them on the planks by the sign: the Noob in profile, Steve facing us, side-eye
        m = 0.5 * (hs + hn) + Vector((0, 0, -0.45))
        loc = m + Vector((0.3, -2.9, 0.55)) + Vector((0, 0.12, 0)) * u
        return loc, m, 24, 5.6, None, 0.1, up
    if shot == "drop":
        # side on to the stub: the planks blink out, they drop, a hand on the edge
        c = Vector((XE - 0.8, E.y_s, deck - 1.1))
        loc = c + Vector((-5.0, -6.0, -0.4))
        sh = 0.15 + 2.2 * math.exp(-((t - b("grab")) / 0.07) ** 2)
        return loc, c, 26, 8.0, None, sh, up
    if shot == "below":
        # from below the hang, up the stub's face to the sky
        c = Vector((XE - 0.6, E.y_s, deck - 2.4))
        loc = c + Vector((-4.6, -3.0, -3.0)) + Vector((0.2, 0.2, 0.3)) * u
        return loc, c + Vector((0.2, 0, 0.6)), 22, 8.0, None, 0.12, up
    if shot == "faces":
        # closer: the Noob's face, Steve above him
        c = hn.lerp(hs, 0.4)
        loc = c + Vector((-3.4, -2.3, -1.3)) + Vector((0.15, 0.15, 0.05)) * u
        return loc, c, 26, 5.0, (hn - loc).length, 0.12, up
    if shot == "reveal":
        # very wide over the void: the stub and the two tiny on the right, Null rising out of the chasm
        c = Vector((E.null_base.x, E.null_base.y, deck - 3.0)).lerp(Vector((XE, E.y_s, deck)), 0.45)
        loc = Vector((XE + 16.0, Y0 - 30.0, deck + 1.5))
        top = Vector(E.X.root.location) + Vector((0, 0, 14.0))
        look = c.lerp(top, 0.35 * ss(b("null_rise"), b("null_rise", 1), t))
        return loc, look, 16, 64.0, None, 0.08, up
    if shot == "null":
        # low on Null from the hang: the checker head, the copied smile, the blocks orbiting past the lens
        head = E.X.head.matrix_world.translation.copy()
        loc = Vector((XE - 2.2, E.y_s - 3.6, deck - 0.6)) + Vector((-0.3, 0.2, 0.1)) * u
        reach = ss(b("null_hand"), b("null_hand", 1), t)
        sh = 0.15 + 0.6 * reach
        return loc, head + Vector((0, 0, 2.0 - 4.0 * reach)) + Vector((4.0, 3.0, 0)) * reach, lerp(26, 29, u) - 8 * reach, 64.0, None, sh, up
    if shot == "ledge":
        c = Vector((XE - 0.4, E.y_s, deck - 2.2))
        loc = c + Vector((-2.6, -2.2, -5.2))
        return loc, c + Vector((-0.3 * ss(t0, t1, t), 0, -1.0 * ss(t0, t1, t))), 22, 8.0, None, 0.6, up
    if shot == "plunge":
        # falling with them, looking down past them into the void
        s = t - E.stub_gone
        z = deck - 2.0 - 0.5 * 7.0 * s * s
        c = Vector((XE - 1.2, E.y_s + 0.4, z))
        loc = c + Vector((0.4, -0.6, 4.0 + 1.5 * s))
        up = Vector((1, 0, 0))
        return loc, c + Vector((-0.3, 0.2, -6.0)), 24, 64.0, None, 0.5, up
    # black and the forest are handled elsewhere
    return Vector((0, -10, deck + 5)), Vector((0, 0, deck)), 30, 64.0, None, 0.0, up


# ------------------------------------------------------------------ the look
def finish(path, mist_path):
    P4.finish(path, mist_path)


# ------------------------------------------------------------------ main
def _bridge_ends(E):
    xs = [p.c0.x for p in E.rainbow] or [E.I.bridge_end.x]
    E.rb_far, E.rb_near = min(xs), max(xs)


# ------------------------------------------------------------------ the forest (shot 21)
SPOT = Vector((0.4, 4.6, 0.0))            # where the Noob lands (the ground's height is added at build)
OAK = (2.6, 7.4)                          # the oak he falls past
NEAR_OAK = (2.3, 0.9)                     # the trunk at the right of the last shot
STEVE_FAR = Vector((-5.5, 16.0, 0.0))    # Steve, far off at the left edge


def build_forest(tl, tex_dir, assets, res, samples):
    """The meadow the finale ends in (the restored world, world.build_world), the first portal
    (portal.py) tumbling in the sky above an oak, the Noob, and Steve far off."""
    from world import build_world, set_sky, set_sun
    from stage import build_steve, build_noob_char, char_light
    from portal import build_portal
    E = Ep()
    E.tl = tl
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    E.sc = sc
    cfg = {"seed": 7, "sun": (140, 40), "flat_box": [-7, 7, -40, 6], "plant_clear_box": [-2.5, 2.5, -4, 6],
           "feature_trees": [(OAK[0], OAK[1], "oak"), (NEAR_OAK[0], NEAR_OAK[1], "oak"), (-9, 16, "cherry"), (9, 15, "big_oak")],
           "clear_plants": [(SPOT.x, SPOT.y, 1.4), (0.3, 1.0, 1.4)],
           "particle_box": (-5, 7, 6, 14, 2.0, 9.0)}             # leaves drift round the oak, never across the lens
    E.W = W = build_world(sc, assets, cfg)
    set_sky(W, {"glow": (255, 240, 220), "power": 30.0, "horizon": (220, 232, 250), "mid": (140, 186, 250),
                "zenith": (52, 120, 236), "fill": 1.1, "fill_col": (186, 206, 240)})
    E.ground = lambda x, y: W.layout.height(x, y)
    E.spot = Vector((SPOT.x, SPOT.y, E.ground(SPOT.x, SPOT.y)))
    E.oak = Vector((OAK[0], OAK[1], E.ground(*OAK)))
    E.P = build_portal(sc, assets, at=(0, 0, -500), w=4, h=5)
    E.S = build_steve(sc)
    E.N = build_noob_char(sc)
    E.lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    E.key = char_light(sc, "char_key", (0, -3, 3), 300, (1.0, 0.9, 0.8), cone=40, size=1.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.dof.use_dof = True
    cam.data.sensor_width = 36
    cam.data.clip_end = 3000
    E.cam = cam
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = res * 16 // 9
    sc.render.resolution_y = res
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.45
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = -0.05
    sc.render.fps = FPS
    sc.render.compositor_device = "CPU"
    from ep09_new import _mist_output
    _mist_output(sc)
    return E


def apply_forest(E, t):
    """a: the portal tumbles in over the oak, he drops out of it and lands;
    b: "Whoa." close on him, looking round; c: "Where am I?" he walks past us."""
    from ep09_new import NF, SF
    t0 = b("forest")
    ta, tb = t0 + 2.0, b("noob_where") + 0.95
    P = E.P
    # the portal: small and far, tumbling closer over the oak; gone (closed) once he's out
    u = ss(t0, t0 + 1.6, t)
    P.root.location = E.oak + Vector((lerp(-7.0, -5.0, u), lerp(6.0, 2.5, u), lerp(17.0, 12.0, u)))
    s_ = lerp(0.45, 0.95, u) * (1.0 - ss(t0 + 1.75, t0 + 2.1, t))
    P.root.scale = (max(s_, 1e-3),) * 3
    P.root.rotation_euler = (math.radians(70 + 40 * t), math.radians(25 * math.sin(t * 1.7)), math.radians(30 + 60 * t))
    if s_ < 0.01:
        P.root.location = (0, 0, -500)                          # closed: gone
    # the Noob: out of the portal, past the oak, onto the grass
    t_out, t_land = t0 + 0.75, t0 + 1.55
    bpy.context.view_layer.update()
    mem = E.P.membrane
    out_at = sum((mem.matrix_world @ Vector(c) for c in mem.bound_box), Vector()) / 8 + Vector((0, 0, -0.6))
    if t < t_out:
        set_noob(E, Vector((0, 0, -500)), 0, {}, NF["shout"], t)
    elif t < t_land:
        s = (t - t_out) / (t_land - t_out)
        p = out_at.lerp(E.spot, s)
        p.z = lerp(out_at.z, E.spot.z, s * s)
        pose_d = {"chest_lean": -10, "head_nod": -10, "arm_sl": {"out": 150, "fwd": 20}, "arm_sr": {"out": 140, "fwd": 30},
                  "leg_sl": {"fwd": 30}, "leg_sr": {"fwd": -15}}
        set_noob(E, p, 20 + 200 * s, pose_d, NF["shout"], t)
    elif t < tb:
        # landed: a squash, he straightens, looks round, delighted
        k = ss(t_land, t_land + 0.45, t)
        look = math.sin((t - t_land) * 2.4) * 28 * ss(t_land + 0.5, t_land + 1.0, t)
        pose_d = {"hips_drop": 0.35 * (1 - k), "chest_lean": 18 * (1 - k), "head_turn": look, "head_nod": -6,
                  "arm_sl": {"out": lerp(40, 8, k)}, "arm_sr": {"out": lerp(40, 8, k)}}
        face = dict(NF["awe"]) if t >= b("noob_where") - 0.2 else dict(NF["happy"])
        set_noob(E, E.spot, 0, pose_d, face, t)
    else:
        # he walks toward us and past, the near trunk at the right
        s = (t - tb) / (b("forest_end", 1) - tb)
        end = Vector((0.1, -1.2, 0))
        p = E.spot.lerp(end, s)
        p.z = E.ground(p.x, p.y)
        ph = (t - tb) * 1.8 * 2 * math.pi
        sw = math.sin(ph)
        pose_d = {"head_turn": 18 * math.sin((t - tb) * 1.7), "head_nod": -4, "arm_sl": {"fwd": -28 * sw}, "arm_sr": {"fwd": 28 * sw},
                  "leg_sl": {"fwd": 30 * sw}, "leg_sr": {"fwd": -30 * sw}}
        set_noob(E, p + Vector((0, 0, 0.04 * abs(sw))), 0, pose_d, NF["awe"], t)
    # Steve, far off at the left, among the trees
    sp = STEVE_FAR + Vector((0, 0, E.ground(STEVE_FAR.x, STEVE_FAR.y)))
    set_steve(E, sp, -40, {"head_turn": 10}, SF["neutral"], t)
    # the camera
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    hn = P6._head(E.N.face)
    if t < ta:
        loc = E.oak + Vector((-1.5, -7.5, 0.6))
        look = E.oak + Vector((-1.0, 2.0, 9.0)) if t < t_land - 0.3 else E.oak.lerp(E.spot, 0.6) + Vector((0, 0, 3.0))
        look = (E.oak + Vector((-3.0, 2.0, 9.5))).lerp(E.spot + Vector((0, 0, 3.0)), ss(t_out + 0.2, t_land + 0.2, t))
        lens, fs, sh = 22, 64.0, 0.08 + 0.6 * math.exp(-((t - t_land) / 0.08) ** 2)
    elif t < tb:
        loc = E.spot + Vector((0.3, -3.0, 1.35))
        look = hn + Vector((0, 0, -0.35))
        lens, fs, sh = 36, 3.2, 0.1
    else:
        loc = Vector((0.9, -2.6, E.ground(0.9, -2.6) + 1.2))
        look = hn + Vector((0, 0, -0.2))
        lens, fs, sh = 28, 3.5, 0.12
    y1, p1, r1 = handheld(t, sh)
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.data.lens = lens
    E.cam.data.dof.use_dof = fs < 30
    E.cam.data.dof.focus_distance = (hn - loc).length
    E.cam.data.dof.aperture_fstop = fs
    E.key.location = loc + Vector((0.6, 0.0, 1.6))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()


def finish_forest(path, mist_path):
    from ep09_new import finish as f9
    f9(path, mist_path, {"g": 0.0, "s": 0.0})


# ------------------------------------------------------------------ main
def _render(E, frames, out, apply_fn, finish_fn):
    sc = E.sc
    mist_dir = os.path.join(out, "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"
    bpy.app.handlers.frame_change_pre.clear()

    def handler(scene, depsgraph=None):
        apply_fn(E, (scene.frame_current + scene.frame_subframe - 1) / FPS)

    bpy.app.handlers.frame_change_pre.append(handler)
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not E.force:
            continue
        sc.frame_set(f)
        apply_fn(E, (f - 1) / FPS)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        finish_fn(dst, cand[-1] if cand else "")
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


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
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    B.update({k: tuple(v) for k, v in tl["beats"].items()})
    n_frames = int(round(b("forest_end", 1) * FPS)) + 1      # the chapter ends with the forest (the end card is dropped)
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    if a.times:
        frames = [int(round(float(x) * FPS)) + 1 for x in a.times.split(",")]
    else:
        frames = list(range(1, n_frames + 1))
        k, n = (int(x) for x in a.shard.split("/"))
        per = (len(frames) + n - 1) // n
        frames = frames[k * per:(k + 1) * per]
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    tt = lambda f: (f - 1) / FPS                                                  # noqa: E731
    island = [f for f in frames if tt(f) < b("black")]
    black = [f for f in frames if b("black") <= tt(f) < b("forest")]
    forest = [f for f in frames if tt(f) >= b("forest")]
    print("rendering", len(island), "island,", len(black), "black,", len(forest), "forest frames", flush=True)
    mouth_tl = dict(tl, lines=[ln for ln in tl["lines"] if not ln.get("vo")])     # narration moves no mouth
    if black:
        from PIL import Image
        for f in black:
            Image.new("RGB", (a.res * 16 // 9, a.res), (0, 0, 0)).save(os.path.join(out, f"{f:04d}.png"))
    for part, fr in (("island", island), ("forest", forest)):
        if not fr:
            continue
        E = (build if part == "island" else build_forest)(tl, a.tex_dir, a.assets, a.res, a.samples)
        E.force = bool(a.times)
        E.mouth = {}
        if os.path.exists(a.voice):
            from ep09_new import _lipsync
            E.mouth = _lipsync(mouth_tl, a.voice)
        if part == "island":
            _render(E, fr, out, apply, finish)
        else:
            _render(E, fr, out, apply_forest, finish_forest)


if __name__ == "__main__":
    main()
