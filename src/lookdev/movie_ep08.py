"""The movie, chapter 8: "Steve Was Hiding Something", in the new look, in 16:9 (story/movie/ep08_shots.md).

Built in the finale's own forest clearing (ep10_entrance's world: the same seed, trees, plants and portal place), so
the last shot (5B) ends on the finale's first camera and light and cuts into ep10_part1_null_entrance with no seam.
The light moves with the story: golden sunset (sun 12 degrees) at the landing, deep twilight blue by the
forgiveness, and on the ignition the finale's storm light and the portal's violet spill.

  1  wide: out of Ep7's warp flash; the tumble; Steve pulls the vines off his old portal; "You had a PORTAL?!"
  2  the memory (cool, desaturated): past-Steve sets the last block, flint and steel, the first flare
  3A the Noob, hurt   3B Steve's confession   4A the Noob forgives   4B the two-shot, the shoulder pat
  5A the violet glow on their faces, they turn   5B the creeping push-in on the blazing portal, the magenta crack

Every frame is a function of time alone (shards start anywhere); the dissolves into and out of the memory render
both sides and blend them.

    python src/lookdev/movie_ep08.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--samples 32]
        [--times 0.5,3.6] [--list]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_entrance as EN                                           # noqa: E402
import ep10_p6_fall as P6                                            # noqa: E402
import movie_ep00 as M                                               # noqa: E402
from ep10_entrance import FPS, PORTAL_AT, lerp, ss                   # noqa: E402

B = M.B                                    # the timeline's beats: name -> (start, end)


def b(name, i=0):
    return B[name][i]


# ------------------------------------------------------------------ the light
SUNSET = {"glow": (255, 196, 140), "power": 7.0, "horizon": (255, 176, 118), "mid": (214, 150, 150), "zenith": (70, 78, 140),
          "fill": 1.05, "fill_col": (255, 206, 170)}
TWILIGHT = {"glow": (130, 120, 180), "power": 6.0, "horizon": (66, 70, 122), "mid": (28, 34, 78), "zenith": (7, 11, 26),
            "fill": 0.34, "fill_col": (112, 132, 206)}
STORM = {"glow": (214, 196, 255), "power": 6.0, "horizon": (176, 96, 180), "mid": (84, 52, 132), "zenith": (22, 14, 48),
         "fill": 0.32, "fill_col": (150, 120, 210)}          # ep10_entrance's sky on its frame 1
MEMORY = {"glow": (190, 205, 235), "power": 8.0, "horizon": (150, 168, 205), "mid": (86, 108, 160), "zenith": (30, 42, 84),
          "fill": 0.7, "fill_col": (160, 180, 230)}
SUN_COL = (1.0, 0.745, 0.52)              # #FFBE85
SUN_KEYS = [(0.0, 12.0), (24.3, 7.0), (38.0, 2.0), (43.0, -1.0), (51.9, -4.0)]


def key_interp(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(v0, v1, ss(t0, t1, t))
    return keys[-1][1]


# ------------------------------------------------------------------ places (metres; the portal at (0, 5), facing -y)
LAND_S = (-1.5, 2.15)
LAND_N = (1.4, 2.35)
VINE_A = (-0.5, 3.72)                     # Steve pulling the left curtain
VINE_B = (0.45, 3.72)                     # ... the right one
NOOB_SEE = (2.6, 2.3)                   # the Noob, scrambled up behind him: "You had a PORTAL?!"
STEVE_T = (-0.8, 2.3)                   # the talk, ~3.8 m in front of the frame
NOOB_T = (0.7, 2.1)
NOOB_PAT = (0.1, 2.15)                   # beside Steve for the pat
PATCH_T = Vector((-1.9, 2.9, 1.9))
PATCH_BACK = Vector((-2.6, 0.7, 2.4))     # startled back by the ignition
PAST_S = (0.55, 3.8)                      # past-Steve setting the last block (the right column's middle)
PAST_FLINT = (-0.35, 3.8)
PAST_BACK = (0.4, 2.4)
LAST_BLOCK = 2                            # P.blocks index: the sill, x 0.5 (the last one he set)
CURTAIN_X = (-0.5, 0.5)
PILE = ((-2.95, 3.55), (2.95, 3.45))


def yaw_to(a, c):
    """The facing (degrees) of someone at a looking at c (0 = facing -y, the rigs' convention)."""
    return math.degrees(math.atan2(c[0] - a[0], -(c[1] - a[1])))


class Ep:
    pass


# ------------------------------------------------------------------ the build
def _cubes(name, centers, size, mat, col):
    """One mesh of axis-aligned cubes (each face mapped to the whole texture)."""
    verts, faces, uvs = [], [], []
    h = size / 2
    corners = [(-h, -h, -h), (h, -h, -h), (h, h, -h), (-h, h, -h), (-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for c in centers:
        s = c[3] if len(c) > 3 else 1.0
        base = len(verts)
        verts += [(c[0] + x * s, c[1] + y * s, c[2] + z * s) for x, y, z in corners]
        for q in quads:
            faces.append(tuple(base + i for i in q))
            uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="uv")
    uv.data.foreach_set("uv", [v for p in uvs for v in p])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def _emit(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    lin = tuple(((v / 255 + 0.055) / 1.055) ** 2.4 for v in rgb)
    bs.inputs["Base Color"].default_value = (*lin, 1)
    bs.inputs["Emission Color"].default_value = (*lin, 1)
    bs.inputs["Emission Strength"].default_value = strength
    return m


def _vines(E, assets):
    """Steve's old portal, overgrown: two hanging vine curtains over the opening (pulled off by hand), and
    fixed moss/leaf clusters and vine strands draped over the frame (they stay)."""
    from world import material
    col = bpy.data.collections.new("overgrowth")
    E.sc.collection.children.link(col)
    leaves = bpy.data.materials["w_oak_leaves"]
    BK = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    moss = material("e8_moss", os.path.join(BK, "moss_block.png"), rough=0.9)
    rnd = random.Random(8)
    P0 = PORTAL_AT
    E.curtains = []
    for k, cx in enumerate(CURTAIN_X):
        cells = []
        for i in range(6):
            x = -0.42 + 0.17 * i + rnd.uniform(-0.03, 0.03)
            n = rnd.randint(15, 21)
            for j in range(n):
                cells.append((x + rnd.uniform(-0.025, 0.025), rnd.uniform(-0.03, 0.03), -0.07 - 0.14 * j, rnd.uniform(0.8, 1.15)))
        root = bpy.data.objects.new(f"curtain_{k}", None)
        col.objects.link(root)
        ob = _cubes(f"curtain_{k}_mesh", cells, 0.15, leaves, col)
        ob.parent = root
        root["home"] = (P0.x + cx, P0.y - 0.6, 4.0)
        root.location = root["home"]
        E.curtains.append(root)
    # fixed clusters: lumps of moss and leaves on the frame (7), and strands down its outer columns
    lumps = [(-1.6, 4.85, 0.9), (-0.6, 4.95, 0.7), (0.5, 4.9, 0.8), (1.55, 4.8, 0.95), (-1.85, 3.2, 0.6), (1.85, 2.4, 0.65),
             (1.85, 0.7, 0.55)]
    E.moss = []
    for n_, (x, z, r) in enumerate(lumps):
        mc, lc = [], []
        for _ in range(int(40 * r)):
            v = Vector((rnd.gauss(0, r * 0.45), rnd.gauss(0, 0.22), rnd.gauss(0, r * 0.3)))
            if v.length > r:
                continue
            (mc if rnd.random() < 0.45 else lc).append((v.x, v.y, v.z, rnd.uniform(0.8, 1.2)))
        for nm, cells, sz, mt in (("moss", mc, 0.24, moss), ("leaves", lc, 0.17, leaves)):
            if cells:
                ob = _cubes(f"frame_{nm}_{n_}", cells, sz, mt, col)
                ob.location = (P0.x + x, P0.y - 0.45, z)
                E.moss.append(ob)
    for n_, x in enumerate((-1.75, -1.35, 1.3, 1.7)):
        n = rnd.randint(10, 22)
        cells = [(rnd.uniform(-0.03, 0.03), 0, -0.14 * j, rnd.uniform(0.8, 1.1)) for j in range(n)]
        ob = _cubes(f"frame_strand_{n_}", cells, 0.17, leaves, col)
        ob.location = (P0.x + x, P0.y - 0.56, 4.9)
        E.moss.append(ob)


def _glimpse(E):
    """A split-second picture of the obby through the first portal's haze (the flashback)."""
    from PIL import Image
    rnd = random.Random(3)
    w, h = 40, 60
    im = Image.new("RGB", (w, h), (120, 190, 255))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (int(lerp(90, 170, y / h)), int(lerp(170, 220, y / h)), 255)
    cols = [(255, 70, 70), (255, 210, 40), (60, 220, 90), (60, 140, 255), (255, 120, 220), (255, 150, 40)]
    for _ in range(9):
        cx, cy, bw = rnd.randint(2, w - 8), rnd.randint(8, h - 6), rnd.randint(4, 8)
        c = rnd.choice(cols)
        for y in range(cy, min(h, cy + 3)):
            for x in range(cx, min(w, cx + bw)):
                px[x, y] = c
    path = os.path.join(bpy.app.tempdir or "/tmp", "e8_obby.png")
    im.save(path)
    m = bpy.data.materials.new("e8_glimpse")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.interpolation = "Closest"
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.2
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.0
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m["fac"] = mx.name
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = "glimpse"
    ob.scale = (2.0, 3.0, 1)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = PORTAL_AT + Vector((0, -0.04, 2.5))
    ob.data.materials.append(m)
    ob.visible_shadow = False
    E.glimpse, E.glimpse_mat = ob, m


def build(tl, tex_dir, assets, res, samples):
    from world import build_world, add_world_fx, fx_set
    from portal import build_portal
    from stage import build_steve, build_noob_char, char_light
    import movie_ep04 as E4
    E = Ep()
    E.tl = tl
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    E.sc = sc
    # exactly ep10_entrance.build's world (the finale's clearing): the same random sequence, the same trees
    cfg = {"seed": 7, "sun": (71, 12), "flat_box": [-22, 22, -40, 8], "plant_clear_box": [-3.4, 3.4, 2.0, 6.5],
           "keep_clear": [(0, -14, 8), (0, 16, 5), (0, 24, 5), (15, -0.5, 8), (8, 1, 6)] + EN.EXTRA_KEEP,
           "feature_trees": [(-6, 13, "big_oak"), (5, 17, "oak"), (-9, 19, "oak"), (9, 18, "big_oak"), (-4, 22, "birch"),
                             (4, 23, "oak"), (-11, 9, "oak"), (-7, 27, "oak"), (8, 28, "oak")] + EN.EXTRA_FEATURES,
           "clear_plants": [(0.0, 3.6, 2.4), (16.5, 0.6, 4.0), (10.0, 1.5, 3.0)] + EN.EXTRA_CLEAR,
           "particle_box": (-9, 9, 9.0, 24, 0.3, 7.0)}
    E.W = W = build_world(sc, assets, cfg)
    add_world_fx(W)
    fx_set(W, R=1e5, Wd=100.0, Cx=0.0, Cy=0.0, D=0.0, Nx=0.0, Ny=60.0, Dz=-1.0)
    E.ground = lambda x, y: W.layout.height(x, y)
    E.P = P = build_portal(sc, assets, at=PORTAL_AT)
    P.light.data.energy = 0.0
    m = P.membrane.data.materials[0]
    E.flow = m.node_tree.nodes[m["flow"]]
    E.power = m.node_tree.nodes[m["power"]]
    E.S = build_steve(sc)
    E.N = build_noob_char(sc)
    E.lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    E4._patch(E)
    _vines(E, assets)
    _glimpse(E)
    col = bpy.data.collections.new("e8_fx")
    sc.collection.children.link(col)
    spark = _emit("e8_spark", (255, 200, 120), 40.0)
    E.sparks = [_cubes(f"spark_{i}", [(0, 0, 0)], 0.025, spark, col) for i in range(16)]
    static = _emit("e8_static", (90, 20, 140), 6.0)
    rnd = random.Random(5)
    ring = []
    for i in range(34):                                    # round the inner edge of the opening (x -1..1, z 1..4)
        u = i / 34 * 10.0
        x, z = (-1 + u, 1.0) if u < 2 else (1.0, 1 + (u - 2)) if u < 5 else (1 - (u - 5), 4.0) if u < 7 else (-1.0, 4 - (u - 7))
        ring.append((x, z, rnd.uniform(0, 6.28)))
    E.ring = [(_cubes(f"static_{i}", [(0, 0, 0)], 0.09, static, col), x, z, ph) for i, (x, z, ph) in enumerate(ring)]
    crack = _emit("e8_crack", (255, 60, 220), 30.0)
    pts, p = [], Vector((-0.95, 0, 3.1))
    while p.x < 0.95:
        pts.append(p.copy())
        p += Vector((0.05, 0, rnd.uniform(-0.07, 0.07)))
        p.z = min(3.9, max(1.2, p.z - 0.012))
    E.crack = [_cubes(f"crack_{i}", [(0, 0, 0)], 0.045, crack, col) for i in range(len(pts))]
    E.crack_pts = pts
    E.flint = _cubes("flint_steel", [(0, 0, 0)], 0.09, bpy.data.materials["w_stone"], col)
    E.key = char_light(sc, "char_key", (2, -3, 3), 260, (1.0, 0.82, 0.62), cone=50, size=1.2)
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
    sc.view_settings.exposure = -0.1
    sc.render.fps = FPS
    sc.render.compositor_device = "CPU"
    from ep09_new import _mist_output
    _mist_output(sc)
    return E


def G(E, x, y):
    return Vector((x, y, E.ground(x, y)))


def prepare(E):
    """Measured once per shard (time-independent): the pat's arm pose, so the Noob's hand lands on Steve's left
    sleeve."""
    piv = E.N.arms["sl"]                                  # the Noob's arm length (as ep10_p6_fall._measure)
    zs = []
    for ch in piv.children_recursive:
        if ch.type == "MESH":
            mm = piv.matrix_world.inverted() @ ch.matrix_world
            zs += [(mm @ Vector(c)).z for c in ch.bound_box]
    E.N.arm_len = -min(zs) * 0.93 if zs else 1.6
    s_loc = G(E, *STEVE_T)
    s_yaw, n_yaw = PAT_STEVE_YAW, PAT_NOOB_YAW
    M.set_steve(E, s_loc, s_yaw, {}, {}, 0.0)
    bpy.context.view_layer.update()
    head = P6._head(E.S.face, E.S.holder)
    f = Vector((math.sin(math.radians(s_yaw)), -math.cos(math.radians(s_yaw)), 0))
    left = Vector((-f.y, f.x, 0))                          # his left (his right is (f.y, -f.x))
    target = head + left * 0.5 + Vector((0, 0, -0.95))     # the upper sleeve
    E.pat_target = target
    best = None
    for gap in (1.35, 1.2, 1.05, 0.95):                    # the Noob as far off as still lets his hand land
        n_loc = G(E, STEVE_T[0] + gap, NOOB_PAT[1])
        for side in ("sr", "sl"):
            for fwd in range(20, 161, 8):
                for out in range(-80, 81, 8):
                    M.set_noob(E, n_loc, n_yaw, {"arm_" + side: {"fwd": fwd, "out": out}}, {}, 0.0)
                    bpy.context.view_layer.update()
                    d = (P6._noob_hand(E.N, side) - target).length
                    if best is None or d < best[0]:
                        best = (d, side, fwd, out, gap)
        if best[0] < 0.1:
            break
    E.pat_x = STEVE_T[0] + best[4]
    E.pat = best[:4]
    E.pat_target = target
    print("pat:", best, flush=True)


PAT_STEVE_YAW = 18.0
PAT_NOOB_YAW = -38.0


# ------------------------------------------------------------------ shots
def shots():
    return [("land", 0.0), ("past", b("dissolve")), ("noob_hurt", b("back", 1)), ("steve", b("guilt")),
            ("noob_smile", b("think")), ("two", b("step")), ("turn", b("ignite")), ("portal", b("reveal"))]


def which(t):
    cur = shots()[0]
    for s in shots():
        if t >= s[1]:
            cur = s
    return cur[0]


def layer_at(t):
    return "past" if b("dissolve") <= t < b("back", 1) else "present"


# ------------------------------------------------------------------ helpers
def walk(ph, k=1.0, steve=True):
    sw = math.sin(ph)
    if steve:
        return {"arm_sl": {"fwd": -26 * sw * k, "out": 6}, "arm_sr": {"fwd": 26 * sw * k, "out": 6},
                "foot_sl": {"y": -0.3 * sw * k, "z": max(0.0, 0.18 * math.sin(ph + 1.2)) * k},
                "foot_sr": {"y": 0.3 * sw * k, "z": max(0.0, 0.18 * math.sin(ph + 1.2 + math.pi)) * k}, "chest_lean": 4 * k}
    return {"arm_sl": {"fwd": -30 * sw * k, "out": 8}, "arm_sr": {"fwd": 30 * sw * k, "out": 8},
            "leg_sl": {"fwd": 32 * sw * k}, "leg_sr": {"fwd": -32 * sw * k}}


def move(E, a, c, t0, t1, t, speed=2.6):
    """Along a -> c between t0 and t1 (eased): position, facing, walk phase weight."""
    u = ss(t0, t1, t)
    p = (lerp(a[0], c[0], u), lerp(a[1], c[1], u))
    k = 1.0 if t0 < t < t1 else 0.0
    k *= min(1.0, (t - t0) / 0.2, (t1 - t) / 0.2) if t0 < t < t1 else 0.0
    return G(E, *p), yaw_to(a, c), (t - t0) * speed * 2 * math.pi, k


def mixf(a, c, u):
    keys = set(a) | set(c)
    return {k: lerp(a.get(k, 0.0), c.get(k, 0.0), u) for k in keys}


def blink(t, period=3.3, phase=0.0):
    ph = (t + phase) % period
    return math.exp(-((ph - 0.08) / 0.045) ** 2)


NOOB_WORRIED = {"both_to": -0.4, "both_ti": 0.15, "both_h": 1.75, "m_arch": 0.2}
NOOB_HURT = {"both_to": -0.5, "both_ti": 0.3, "both_tm": -0.15, "both_h": 1.7, "m_arch": 0.26, "both_py": -0.05}
NOOB_CROOKED = {"both_bm": 0.22, "both_h": 1.8, "m_arch": -0.3, "m_tilt": 0.12}
NOOB_GRIN = {"both_bm": 0.3, "m_arch": -0.45}
NOOB_SHOCK = {"both_w": 1.12, "both_h": 1.95, "both_ps": 0.8, "m_o": 0.6, "m_w": 1.2, "m_up": 0.92, "m_r": 0.9,
              "m_vee": 0.3, "m_arch": 0.1}
STEVE_FLAT = {"both_to": -0.25, "both_tm": -0.3, "both_ti": -0.2, "m_arch": 0.06}
STEVE_GUILT = {"both_to": -0.3, "both_ti": 0.12, "bb_tilt": -0.55, "bb_raise": 0.12, "m_arch": 0.16, "both_py": -0.35}
STEVE_HALF = {"both_bm": 0.18, "m_arch": -0.08, "m_tilt": 0.1, "bb_raise": 0.05}
STEVE_DREAD = {"both_to": 0.25, "both_tm": 0.3, "both_ti": 0.25, "both_ps": 0.8, "bb_tilt": -0.5, "bb_raise": 0.3,
               "m_arch": 0.1}
STEVE_AWE = {"both_to": 0.15, "both_tm": 0.2, "both_ti": 0.15, "both_py": 0.2, "bb_raise": 0.25, "m_arch": 0.02}


# ------------------------------------------------------------------ the present
def steve_now(E, t):
    lib_face = dict(STEVE_FLAT)
    if t < b("tumble") + 0.35:                                    # falling out of the warp
        u = ss(0.0, b("tumble") + 0.35, t)
        p = G(E, *LAND_S) + Vector((0.25 * (1 - u), -0.4 * (1 - u), 2.3 * (1 - u * u)))
        pz = {"chest_lean": 18, "arm_sl": {"out": 70, "fwd": 30}, "arm_sr": {"out": 60, "fwd": 40}, "foot_sl": {"y": -0.2},
              "foot_sr": {"y": 0.25, "z": 0.2}}
        return M.set_steve(E, p, 10, pz, {"both_to": 0.2, "both_tm": 0.25, "bb_raise": 0.3}, t)
    if t < b("rise", 1):                                          # one knee down, then up
        k = ss(b("rise"), b("rise") + 0.8, t)
        kneel = 1 - k
        look = 22 * math.sin((t - b("rise")) * 2.2) * ss(b("rise") + 0.5, b("rise") + 1.0, t)
        pz = {"hips_drop": 0.55 * kneel, "chest_lean": 22 * kneel, "head_nod": -4 + 6 * kneel, "head_turn": look,
              "foot_sl": {"y": -0.35 * kneel}, "foot_sr": {"y": 0.45 * kneel, "z": 0.0},
              "arm_sr": {"fwd": 30 * kneel, "out": 18 * kneel}}
        return M.set_steve(E, G(E, *LAND_S), 10 - 8 * k, pz, lib_face, t)
    if t < b("vines"):                                            # straight to the archway
        p, y, ph, k = move(E, LAND_S, VINE_A, b("walk"), b("vines") - 0.05, t, speed=1.9)
        return M.set_steve(E, p, y, walk(ph, k), lib_face, t)
    if t < b("dissolve", 1):                                      # the two curtains, then he stands there
        v0 = b("vines")
        pa = (v0 + 0.1, v0 + 1.15)
        pb = (v0 + 1.35, v0 + 2.35)
        x = lerp(VINE_A[0], VINE_B[0], ss(pa[1], pb[0] + 0.05, t))
        pz = {}
        if t < pa[1] + 0.1:
            u = ss(*pa, t)
            pz = {"arm_sl": {"fwd": lerp(150, 60, u) * ss(v0, pa[0] + 0.1, t) + 4, "out": lerp(10, 85, u)},
                  "arm_sr": {"fwd": 70 * ss(v0, pa[0], t) * (1 - u)}, "chest_twist": -18 * u, "chest_lean": 6}
        elif t < pb[1] + 0.25:
            u = ss(*pb, t)
            pz = {"arm_sr": {"fwd": lerp(150, 60, u) * ss(pa[1] + 0.1, pb[0] + 0.1, t) + 4, "out": lerp(10, 85, u)},
                  "chest_twist": 18 * u, "chest_lean": 6}
        else:                                                     # hand on the frame; he glances back at the Noob
            g = ss(b("noob_portal") + 0.2, b("noob_portal") + 0.8, t)
            pz = {"arm_sr": {"fwd": 70 * (1 - ss(pb[1] + 0.25, pb[1] + 0.7, t)), "out": 10}, "head_turn": -55 * g,
                  "chest_twist": -12 * g}
            lib_face = mixf(STEVE_FLAT, STEVE_GUILT, g)
        return M.set_steve(E, G(E, x, VINE_A[1]), 180, pz, lib_face, t)
    return steve_talk(E, t)


def steve_talk(E, t):
    """After the memory: Steve facing the Noob; the confession; the half-smile; the turn to the portal."""
    br = 1.2 * math.sin(2 * math.pi * t / 3.1) + 0.5 * math.sin(2 * math.pi * t / 1.37 + 1)   # breathing on the chest
    yaw = yaw_to(STEVE_T, NOOB_T)
    face = dict(STEVE_GUILT)
    pz = {"chest_lean": br}
    sc0 = b("steve_cost")
    your_side = sc0 + 2.62
    if t < b("guilt"):                                            # hearing it
        face["both_py"] = -0.1
        pz["head_nod"] = 4
    elif t < b("think"):
        nod = 12.0                                                # guilt: head down
        py = -0.35
        nod = lerp(12, 1, ss(your_side - 0.05, your_side + 0.35, t))             # eyes up to the Noob on "Your side"
        py = lerp(-0.35, 0.05, ss(your_side - 0.05, your_side + 0.35, t))
        dip = ss(sc0 + 4.0, sc0 + 4.5, t)                                         # dipping on "...what it would cost"
        nod, py = lerp(nod, 7, dip), lerp(py, -0.2, dip)
        ex = ss(b("guilt") + 0.6, b("guilt") + 1.0, t) * (1 - ss(b("guilt") + 1.2, b("guilt") + 1.8, t))   # an exhale
        pz.update({"head_nod": nod, "chest_lean": br + 4 * ex, "arm_sl": {"out": 4 - 2 * ex}, "arm_sr": {"out": 4 - 2 * ex}})
        face["both_py"] = py
        if your_side - 0.2 <= t < your_side - 0.075:            # the 3-frame blink before "Your side"
            face["both_open"] = 0.05
        elif t > b("guilt") + 0.4 and blink(t, 4.1) > 0.5 and abs(t - your_side) > 0.4:
            face["both_open"] = max(0.05, 1 - blink(t, 4.1))
        # the slow blink at the start
        sb = math.exp(-((t - (b("guilt") + 0.9)) / 0.12) ** 2)
        face["both_open"] = min(face.get("both_open", 1.0), max(0.05, 1 - sb))
    else:
        u = ss(b("think"), b("noob_blocks", 1), t)
        face = mixf(STEVE_GUILT, STEVE_FLAT, u)
        face["both_py"] = -0.05
        pz["head_nod"] = 4 * (1 - u)
        if t >= b("steve_same") - 0.3:
            face = mixf(STEVE_FLAT, STEVE_HALF, ss(b("steve_same") - 0.3, b("steve_same") + 0.4, t))
        if t >= b("step"):
            yaw = lerp(yaw, PAT_STEVE_YAW, ss(b("step"), b("step") + 1.2, t))
        if t >= b("pat") and t < b("ignite"):
            pz["head_turn"] = 14 * ss(b("pat"), b("pat") + 0.4, t)                # he glances down at the hand
            pz["head_nod"] = 6 * ss(b("pat"), b("pat") + 0.4, t) * (1 - ss(b("pat", 1) - 0.4, b("pat", 1), t))
        if t >= b("ignite"):                                      # freeze, then head, shoulders, hips to the portal
            k1 = ss(b("ignite") + 0.45, b("ignite") + 1.2, t)
            k2 = ss(b("ignite") + 0.8, b("ignite") + 1.8, t)
            k3 = ss(b("ignite") + 1.2, b("ignite") + 2.4, t)
            yaw = lerp(PAT_STEVE_YAW, 130, k3)
            pz.update({"head_turn": 45 * k1 * (1 - 0.5 * k3), "chest_twist": 25 * k2 * (1 - 0.6 * k3), "head_nod": -4 * k1})
            face = mixf(STEVE_HALF, STEVE_DREAD, ss(b("ignite") + 0.1, b("ignite") + 0.5, t))
            face["both_open"] = 1.0
        elif blink(t, 3.6, 1.1) > 0.3:
            face["both_open"] = max(0.05, 1 - blink(t, 3.6, 1.1))
    M.set_steve(E, G(E, *STEVE_T), yaw, pz, face, t)


def noob_now(E, t):
    if t < b("tumble") + 0.6:                                     # falling, arms flung
        u = ss(0.0, b("tumble") + 0.6, t)
        p = G(E, *LAND_N) + Vector((-0.3 * (1 - u), -0.3 * (1 - u), 2.6 * (1 - u * u)))
        pz = {"arm_sl": {"out": 150, "fwd": 20}, "arm_sr": {"out": 140, "fwd": 30}, "leg_sl": {"fwd": 30}, "leg_sr": {"fwd": -15}}
        M.set_noob(E, p, -30 + 120 * u, pz, NOOB_SHOCK, t)
        return
    sit_up = (b("rise") + 0.6, b("rise") + 1.1)
    stand = (b("vines") + 1.0, b("vines") + 1.55)
    if t < sit_up[1]:                                            # flat on his back, then sitting up
        u = ss(*sit_up, t)
        rx = lerp(-88, 0, u)
        pz = {"hips_drop": 0.95 * u, "leg_sl": {"fwd": 88 * u}, "leg_sr": {"fwd": 85 * u},
              "arm_sl": {"out": lerp(60, 20, u), "fwd": 30 * u}, "arm_sr": {"out": lerp(50, 20, u), "fwd": 30 * u}}
        land = ss(b("tumble") + 0.6, b("tumble") + 0.75, t)
        M.set_noob(E, G(E, *LAND_N) + Vector((0, 0, 0.32 * (1 - u) + 0.08 * (1 - land))), 160, pz, NOOB_WORRIED, t)
        E.N.root.rotation_euler = Euler((math.radians(rx), 0, math.radians(160)), "ZXY")
        return
    if t < stand[1]:                                             # sitting, staring at Steve and the vines; getting up
        u = ss(*stand, t)
        look = yaw_to(LAND_N, VINE_A)
        pz = {"hips_drop": 0.95 * (1 - u), "leg_sl": {"fwd": 88 * (1 - u)}, "leg_sr": {"fwd": 85 * (1 - u)},
              "arm_sl": {"out": 20, "fwd": 30 * (1 - u)}, "arm_sr": {"out": 20, "fwd": 30 * (1 - u)},
              "head_turn": max(-40, min(40, look - 160)) * (1 - u)}
        M.set_noob(E, G(E, *LAND_N), lerp(160, look, u), pz, NOOB_WORRIED, t)
        return
    if t < b("dissolve", 1):                                     # scrambling up behind him, shocked
        p, y, ph, k = move(E, LAND_N, NOOB_SEE, b("scramble") - 0.25, b("scramble", 1), t, speed=3.4)
        pz = walk(ph, k * 1.4, steve=False)
        face = NOOB_SHOCK
        if t >= b("noob_portal") - 0.1:
            y = yaw_to(NOOB_SEE, (lerp(VINE_A[0], VINE_B[0], 1), VINE_A[1]))
            pz = {"arm_sl": {"out": 35, "fwd": 40}, "arm_sr": {"out": 35, "fwd": 40}, "head_nod": -6, "chest_lean": -4}
        M.set_noob(E, p, y, pz, face, t)
        return
    # the talk
    yaw = yaw_to(NOOB_T, STEVE_T)
    pz, face = {}, dict(NOOB_HURT)
    loc = G(E, *NOOB_T)
    if t < b("think"):                                           # hurt: shoulders dropping
        d = ss(b("hurt"), b("hurt") + 0.6, t)
        pz = {"chest_lean": 5 * d, "head_nod": 7 * d, "arm_sl": {"out": 4 - 3 * d}, "arm_sr": {"out": 4 - 3 * d}}
        face = mixf(NOOB_WORRIED, NOOB_HURT, d)
    elif t < b("step"):                                          # the worry relaxing into a crooked smile, a tilt
        u = ss(b("think") + 0.3, b("noob_blocks") + 0.3, t)
        face = mixf(NOOB_HURT, NOOB_CROOKED, u)
        pz = {"chest_lean": 5 * (1 - u), "head_nod": 7 * (1 - u), "head_tilt": 9 * ss(b("noob_blocks"), b("noob_blocks") + 0.5, t)}
    else:                                                       # stepping beside him; the pat; the grin
        p, _, ph, k = move(E, NOOB_T, (getattr(E, "pat_x", NOOB_PAT[0]), NOOB_PAT[1]), b("step") + 0.2, b("step", 1) - 0.1, t,
                           speed=2.0)
        loc = p
        yaw = lerp(yaw, PAT_NOOB_YAW, ss(b("step") + 0.2, b("step", 1), t))
        pz = walk(ph, k * 0.7, steve=False)
        face = NOOB_CROOKED
        if E.pat is not None and b("pat") <= t < b("pat", 1):
            _, side, fwd, out = E.pat
            up = ss(b("pat") + 0.05, b("pat") + 0.4, t)
            down = ss(b("pat") + 0.82, b("pat") + 1.25, t)                       # 10 frames of contact between
            tap = 3.0 * math.sin((t - b("pat") - 0.4) * 2 * math.pi * 2.4) * (1 - down) * up
            a = up * (1 - down)
            pz["arm_" + side] = {"fwd": fwd * a + tap * a, "out": out * a}
        if t >= b("noob_kinda") - 0.2:
            face = mixf(NOOB_CROOKED, NOOB_GRIN, ss(b("noob_kinda") - 0.2, b("noob_kinda") + 0.2, t))
        if t >= b("ignite"):                                     # frozen, then turning to the light
            k1 = ss(b("ignite") + 0.5, b("ignite") + 1.25, t)
            k3 = ss(b("ignite") + 1.3, b("ignite") + 2.4, t)
            yaw = lerp(PAT_NOOB_YAW, -140, k3)
            pz = {"head_turn": -40 * k1 * (1 - 0.5 * k3), "chest_twist": -20 * k1 * (1 - 0.6 * k3)}
            face = mixf(NOOB_GRIN, NOOB_SHOCK, ss(b("ignite") + 0.1, b("ignite") + 0.45, t))
    if t < b("ignite") and blink(t, 3.0, 0.4) > 0.3:
        face = dict(face)
        face["both_open"] = max(0.05, 1 - blink(t, 3.0, 0.4))
    M.set_noob(E, loc, yaw, pz, face, t)


def patch_now(E, t, hidden=False):
    from patch import set_patch
    PA = E.PA
    if hidden:
        PA.root.location = (0, 0, -300)
        PA.glow.data.energy = 0.0
        return
    land = G(E, 0.0, 1.6) + Vector((0, 0, 2.2))
    side = G(E, 2.4, 1.2) + Vector((0, 0, 2.2))
    if t < b("tumble") + 1.0:                                     # wobbling out of the warp, steadying
        u = ss(0.0, b("tumble") + 1.0, t)
        p = land + Vector((0, 0, 1.4 * (1 - u)))
        wob = 22 * math.exp(-u * 3) * math.sin(t * 14)
        PA.root.location = p
        PA.root.rotation_euler = (math.radians(wob), math.radians(-wob * 0.7), math.radians(20 + 200 * (1 - u)))
    else:
        if t < b("back", 1):
            p = land.lerp(side, ss(b("walk"), b("walk") + 2.5, t))
            tgt = G(E, *VINE_A) + Vector((0, 0, 1.5)) if t > b("vines") else G(E, *LAND_N)
        else:
            p = PATCH_T.lerp(PATCH_BACK, ss(b("ignite") + 0.1, b("ignite") + 0.9, t))
            p = p + Vector((0, 0, E.ground(p.x, p.y)))
            who = "steve" if (b("steve_cost") <= t < b("think")) or b("steve_same") <= t < b("steve_same", 1) else "noob"
            tgt = G(E, *(STEVE_T if who == "steve" else NOOB_T)) + Vector((0, 0, 1.5))
            if t >= b("ignite") + 0.3:
                tgt = PORTAL_AT + Vector((0, 0, 2.5))
        p = p + Vector((0, 0, 0.05 * math.sin(t * 2.3) + 0.02 * math.sin(t * 5.1 + 1)))
        to = tgt - p
        PA.root.location = p
        PA.root.rotation_euler = (math.radians(-6), 0, math.radians(yaw_to((p.x, p.y), (tgt.x, tgt.y))))
    vals = {"open": max(0.05, 1 - blink(t, 2.8, 0.9)), "look_x": 0.0, "look_y": 0.0, "squint": 0.0, "wide": 0.0,
            "glitch": 0.0, "scan": 0.0, "smile": 0.0, "sad": 0.0}
    if t >= b("ignite") + 0.2:
        vals["wide"] = ss(b("ignite") + 0.2, b("ignite") + 0.5, t)
        vals["open"] = 1.0
    elif b("back", 1) <= t:
        vals["sad"] = 0.25
    set_patch(PA, vals)
    PA.glow.data.energy = 10.0


def overgrowth(E, t, past):
    ig = b("ignite")
    burn = 0.0 if past else ss(ig + 0.05, ig + 0.9, t)          # the plasma burns the overgrowth off the frame
    for i, o in enumerate(E.moss):
        o.hide_render = past or burn >= 0.999
        k = max(1e-3, 1 - ss(0.1 * (i % 4) / 4, 0.75 + 0.25 * (i % 3) / 3, burn))
        o.scale = (k, k, k)
    for k, root in enumerate(E.curtains):
        for c in root.children:
            c.hide_render = past
        home = Vector(root["home"])
        v0 = b("vines")
        pull = (v0 + 0.1, v0 + 1.15) if k == 0 else (v0 + 1.35, v0 + 2.35)
        u = ss(pull[0] + 0.15, pull[1], t)
        sx = -1 if k == 0 else 1
        pile = G(E, *PILE[k]) + Vector((0, 0, 0.12))
        if burn >= 0.999:
            for c in root.children:
                c.hide_render = True
        root.scale = (max(1e-3, 1 - burn),) * 3
        if u <= 0:
            root.location = home
            root.rotation_euler = (math.radians(1.5 * math.sin(t * 1.3 + k)), 0, 0)      # a breath of wind
            continue
        arc = Vector((sx * 0.6 * math.sin(math.pi * min(1, u * 1.4)), -0.5 * math.sin(math.pi * u), 0))
        root.location = home.lerp(pile + Vector((0, 0, 2.6 * (1 - u) ** 2)), u ** 1.3) + arc
        root.rotation_euler = (math.radians(-86 * u ** 1.6), math.radians(sx * 25 * u), math.radians(sx * 30 * u))


def portal(E, t, past):
    P = E.P
    for k, ob in enumerate(P.blocks):
        ob.location = Vector(ob["home"])
        ob.hide_render = False
    mem = P.membrane
    E.flow.inputs[1].default_value = (0.05 * t, 0.03 * t, 0.0)
    E.glimpse.hide_render = True
    E.glimpse_mat.node_tree.nodes[E.glimpse_mat["fac"]].inputs["Fac"].default_value = 0.0
    for ob, *_ in E.ring:
        ob.location = (0, 0, -400)
    for ob in E.crack:
        ob.location = (0, 0, -400)
    if past:
        blk = P.blocks[LAST_BLOCK]
        p0 = b("place")
        hand = getattr(E, "hand_now", None)
        u = ss(p0 + 0.5, p0 + 0.9, t)
        if t < p0 + 0.5 and hand is not None:
            blk.location = P.root.matrix_world.inverted() @ (hand + Vector((0, 0, 0.1)))
        elif hand is not None and u < 1:
            start = P.root.matrix_world.inverted() @ (getattr(E, "hand_place", hand))
            blk.location = start.lerp(Vector(blk["home"]), u)
        fl = b("flare")
        k = ss(fl, fl + 0.25, t)
        mem.hide_render = k <= 0
        surge = math.exp(-max(0.0, t - fl - 0.15) / 0.5) if t >= fl else 0.0
        E.power.inputs[2].default_value = 0.42 + 2.2 * surge
        P.light.data.energy = 600 * k * (1 + 0.6 * surge)
        g = math.exp(-((t - (fl + 0.3)) / 0.13) ** 2)                      # the split-second glimpse of the obby
        E.glimpse.hide_render = g < 0.02
        E.glimpse_mat.node_tree.nodes[E.glimpse_mat["fac"]].inputs["Fac"].default_value = 0.75 * g
        st = ss(fl + 0.5, fl + 1.0, t)                                       # dark purple static round the edges
        if st > 0:
            for i, (ob, x, z, ph) in enumerate(E.ring):
                j = 0.04 * math.sin(t * 23 + ph * 7)
                fl_ = (math.sin(t * 17 + ph * 5) > -0.2)
                ob.location = PORTAL_AT + Vector((x + j, -0.06, z + 0.04 * math.sin(t * 19 + ph)))
                ob.scale = (st * (1.4 if fl_ else 0.5),) * 3
        return
    ig = b("ignite")
    k = ss(ig, ig + 0.4, t)
    mem.hide_render = k <= 0
    E.power.inputs[2].default_value = 0.42 + 0.9 * math.exp(-max(0.0, t - ig) / 0.6) * (t >= ig)
    full = ss(b("reveal") - 0.1, b("reveal") + 0.8, t)
    soft = lerp(0.18, 1.0, full)                                             # gentler on their faces in 5A
    P.light.data.energy = 900 * k * soft                                     # ep10_entrance's portal light by 5B
    P.light.data.color = tuple(lerp(x, y, full) for x, y in zip((0.42, 0.3, 1.0), (0.62, 0.25, 1.0)))   # bluer, not pink
    c0 = b("crack") + 0.15
    if t >= c0:                                                              # the magenta crack ripples across
        n = len(E.crack)
        u = ss(c0, c0 + 0.3, t)
        for i, ob in enumerate(E.crack):
            if i / n <= u:
                ob.location = PORTAL_AT + Vector((E.crack_pts[i].x, -0.03, E.crack_pts[i].z))
                ob.scale = (1.0 + 0.4 * math.exp(-(t - c0) / 0.2),) * 3


def light(E, t, past):
    from world import set_sky, set_sun
    W = E.W
    W.clouds.hide_render = True
    if past:
        set_sky(W, MEMORY)
        set_sun(W, 71, 9, 2.2, (0.72, 0.8, 1.0))
        E.key.data.energy = 160
        E.key.data.color = (0.75, 0.85, 1.0)
        return
    tw = ss(0.0, b("step"), t)
    look = M.mix_look(SUNSET, TWILIGHT, tw)
    ig = b("ignite")
    sk = ss(ig, b("reveal", 1), t)
    if sk > 0:
        look = M.mix_look(look, STORM, sk)
    set_sky(W, look)
    el = key_interp(SUN_KEYS, t)
    en = 5.6 * max(0.0, min(1.0, el / 6.0)) + 0.15
    col = tuple(lerp(c, w, ss(0, b("step"), t)) for c, w in zip(SUN_COL, (0.62, 0.7, 1.0)))
    if sk > 0:                                                    # ending on ep10_entrance's sun (71, 16, 1.5 violet)
        el, en = lerp(el, 16, sk), lerp(en, 1.5, sk)
        col = tuple(lerp(c, w, sk) for c, w in zip(col, (0.8, 0.66, 1.0)))
    set_sun(W, 71, el, en, col)
    # the character key: warm sun-side fill fading into the dusk; off on the ignition (no front light)
    E.key.data.energy = lerp(320, 80, tw) * (1 - ss(ig - 0.1, ig + 0.15, t))
    E.key.data.color = tuple(lerp(c, w, tw) for c, w in zip((1.0, 0.82, 0.62), (0.62, 0.7, 1.0)))


def past_steve(E, t):
    """Before he met them: setting the last block, the flint, the flare, stepping back in awe."""
    p0, fl0, fa = b("place"), b("flint"), b("flare")
    blk_home = E.P.root.matrix_world @ Vector(E.P.blocks[LAST_BLOCK]["home"])
    if t < fl0:
        y = yaw_to(PAST_S, (blk_home.x, blk_home.y))
        u = ss(p0 + 0.3, p0 + 0.9, t)
        pz = {"arm_sr": {"fwd": lerp(30, 72, u), "out": 6}, "hips_drop": 0.45 * u, "chest_lean": 30 * u, "head_nod": 5 * u,
              "foot_sr": {"y": 0.3 * u}}
        M.set_steve(E, G(E, *PAST_S), y, pz, STEVE_FLAT, t)
        bpy.context.view_layer.update()
        E.hand_now = P6._steve_hand(E.S, "sr")
        E.hand_place = E.hand_now
        if t >= p0 + 0.5:                                         # where the hand was when the block left it
            u5 = ss(p0 + 0.3, p0 + 0.9, p0 + 0.5)
            M.set_steve(E, G(E, *PAST_S), y, {"arm_sr": {"fwd": lerp(30, 72, u5), "out": 6}, "hips_drop": 0.45 * u5,
                                              "chest_lean": 30 * u5, "head_nod": 5 * u5, "foot_sr": {"y": 0.3 * u5}},
                        STEVE_FLAT, t)
            bpy.context.view_layer.update()
            E.hand_place = P6._steve_hand(E.S, "sr")
            M.set_steve(E, G(E, *PAST_S), y, pz, STEVE_FLAT, t)
        E.flint.location = (0, 0, -400)
        return
    if t < fa:                                                    # walking round to the opening's foot, crouching, striking
        p, y, ph, k = move(E, PAST_S, PAST_FLINT, fl0 - 0.05, fl0 + 0.45, t, speed=2.2)
        cr = ss(fl0 + 0.35, fl0 + 0.6, t)
        strike = sum(math.exp(-((t - (fl0 + 0.4 + 0.32 * i)) / 0.06) ** 2) for i in range(2))
        pz = walk(ph, k)
        pz.update({"hips_drop": 0.42 * cr, "chest_lean": 24 * cr, "head_nod": 14 * cr,
                   "arm_sr": {"fwd": 70 * cr + 18 * strike, "out": 6}, "arm_sl": {"fwd": 55 * cr, "out": -6}})
        y = lerp(y, 180, cr)
        M.set_steve(E, p, y, pz, STEVE_FLAT, t)
        bpy.context.view_layer.update()
        E.flint.location = P6._steve_hand(E.S, "sr")
        E.hand_now = E.flint.location.copy()
        return
    E.flint.location = (0, 0, -400)
    u = ss(fa + 0.25, fa + 1.2, t)                                # stepping back in quiet awe
    p = G(E, lerp(PAST_FLINT[0], PAST_BACK[0], u), lerp(PAST_FLINT[1], PAST_BACK[1], u))
    ph = (t - fa) * 2.0 * 2 * math.pi
    k = 1.0 if fa + 0.25 < t < fa + 1.2 else 0.0
    cr = 1 - ss(fa, fa + 0.35, t)
    pz = walk(-ph, 0.6 * k)
    pz.update({"hips_drop": 0.42 * cr, "chest_lean": 24 * cr + 1.0 * math.sin(t * 2), "head_nod": lerp(-10, 14, cr),
               "head_tilt": 5 * ss(fa + 1.5, fa + 2.5, t)})
    M.set_steve(E, p, 180, pz, mixf(STEVE_FLAT, STEVE_AWE, ss(fa, fa + 0.4, t)), t)


def sparks(E, t):
    rnd = random.Random(9)
    s0s = [b("flint") + 0.4 + 0.32 * i for i in range(2)]
    origin = PORTAL_AT + Vector((0.0, -0.45, 1.05))
    for i, ob in enumerate(E.sparks):
        s0 = s0s[i % 2]
        v = Vector((rnd.uniform(-1.6, 1.6), rnd.uniform(-1.2, 0.4), rnd.uniform(0.5, 2.2)))
        dt = t - s0
        if 0 <= dt < 0.45:
            ob.location = origin + v * dt + Vector((0, 0, -4.9 * dt * dt))
            ob.scale = ((1 - dt / 0.45) + 0.2,) * 3
        else:
            ob.location = (0, 0, -400)


# ------------------------------------------------------------------ cameras
def _head(E, who):
    bpy.context.view_layer.update()
    return P6._head(E.S.face, E.S.holder) if who == "steve" else P6._head(E.N.face)


def _over(E, who, other, dist, side_deg, lens, fstop, dz=-0.05):
    """A close shot on `who`, from the front (the side away from the portal), `side_deg` off his line to `other`."""
    h, o = _head(E, who), _head(E, other)
    d = Vector((o.x - h.x, o.y - h.y, 0)).normalized()
    best = None
    for s in (1, -1):
        r = d.copy()
        r.rotate(Euler((0, 0, math.radians(s * side_deg))))
        loc = h + r * dist + Vector((0, 0, dz))
        if best is None or loc.y < best.y:
            best = loc
    return best, h + Vector((0, 0, -0.12)), lens, fstop, (h - best).length


def camera(E, t, shot, layer):
    from ep10_p2_omg import handheld
    if layer == "past":
        if t < b("flare"):                                       # through the empty frame, from behind: his face
            u = ss(b("dissolve"), b("flare"), t)
            loc = G(E, 0.35, 8.3) + Vector((0, -0.4 * u, 2.15))
            look = G(E, 0.1, 3.8) + Vector((0, 0, 1.9))
            lens, fs, fd, sh = 30, 6.0, 4.6, 0.04
        else:                                                    # beside the frame: his face in the violet light
            u = ss(b("flare"), b("back", 1), t)
            loc = G(E, 3.6, 2.5) + Vector((-0.2 * u, 0.05 * u, 2.2))         # his profile, the portal at the right
            look = G(E, -0.2, 3.7) + Vector((0, 0, 2.4))
            lens, fs, fd, sh = 26, 5.0, 3.3, 0.04
    elif shot in ("land", "past"):
        u = ss(0.0, b("dissolve", 1), t)
        loc = G(E, 3.2, -6.2) + Vector((-0.5 * u, 1.1 * u, 1.75))
        look = G(E, -0.1, 3.4) + Vector((0, 0, 2.7 - 0.3 * u))
        lens, fs, fd, sh = 26, 9.0, 9.0, 0.06
    elif shot in ("noob_hurt", "noob_smile"):
        loc, look, lens, fs, fd = _over(E, "noob", "steve", 2.3, 40, 50, 2.8)
        sh = 0.05
    elif shot == "steve":
        loc, look, lens, fs, fd = _over(E, "steve", "noob", 2.0, 40, 65, 2.2)
        u = ss(b("guilt"), b("think"), t)
        loc = loc + (look - loc).normalized() * 0.25 * u                 # a slow creep in
        sh = 0.04
    elif shot == "two":
        u = ss(b("step"), b("ignite"), t)
        loc = G(E, -0.3, -2.2) + Vector((0.1 * u, 0.25 * u, 1.7))
        look = G(E, -0.2, 2.3) + Vector((0, 0, 1.7))
        lens, fs, fd, sh = 35, 4.0, (look - loc).length, 0.04
    elif shot == "turn":
        loc = G(E, -0.2, 4.25) + Vector((0, 0, 1.8))
        look = G(E, -0.3, 2.2) + Vector((0, 0, 1.75))
        lens, fs, fd, sh = 32, 3.2, (look - loc).length, 0.05 + 0.4 * math.exp(-((t - b("ignite")) / 0.12) ** 2)
    else:                                                         # 5B: onto ep10_entrance's first camera
        u = ss(b("reveal"), b("crack", 1), t)
        u = u * (2 - u) if u < 1 else 1.0
        loc = PORTAL_AT + Vector((lerp(-5.4, -3.5, u), lerp(-3.6, -2.0, u), lerp(1.8, 1.9, u)))
        look = PORTAL_AT + Vector((lerp(0.4, 0.0, u), -0.5, 2.4))
        lens, fs, fd, sh = 32, 2.8, (look - loc).length, 0.03
    y1, p1, r1 = handheld(t, sh)
    from mathutils import Quaternion
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.data.lens = lens
    E.cam.data.dof.use_dof = True
    E.cam.data.dof.focus_distance = fd
    E.cam.data.dof.aperture_fstop = fs
    if not (layer == "past"):
        E.key.location = loc + Vector((1.2, -0.4, 1.8)) if shot not in ("turn", "portal") else Vector((0, 0, -50))
    else:
        E.key.location = loc + Vector((-1.0, 0.0, 2.0))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()


# ------------------------------------------------------------------ a frame
def apply(E, t, layer=None):
    layer = layer or layer_at(t)
    shot = which(t)
    past = layer == "past"
    light(E, t, past)
    portal(E, t, past)
    overgrowth(E, t, past)
    if past:
        M.set_noob(E, Vector((0, 0, -500)), 0, {}, {}, t)
        patch_now(E, t, hidden=True)
        past_steve(E, t)
        sparks(E, t)
        portal(E, t, past)                                        # the block follows this frame's hand
    else:
        E.flint.location = (0, 0, -400)
        for ob in E.sparks:
            ob.location = (0, 0, -400)
        steve_now(E, t)
        noob_now(E, t)
        patch_now(E, t)
    camera(E, t, "past" if past else shot, layer)
    E.grade = ("past", 0, 0) if past else (("end", 0, 1) if shot == "portal" else
                                           ("now", 1 - ss(0.0, b("step"), t), ss(b("ignite"), b("reveal", 1), t)))


def finish(path, mist_path, grade):
    from PIL import Image, ImageEnhance
    from ep09_new import finish as f9
    kind, g, s = grade
    if kind == "end":
        EN.finish(path, mist_path)
        return
    f9(path, mist_path, {"g": g, "s": s})
    if kind == "past":                                            # the memory: cool, hazy, desaturated
        im = Image.open(path).convert("RGB")
        im = ImageEnhance.Color(im).enhance(0.45)
        a = np.asarray(im, np.float32) / 255.0
        a = a * np.array([0.86, 0.95, 1.1]) * 0.9 + np.array([0.05, 0.07, 0.11])
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ render
def _render_one(E, f, t, layer, dst, mist_dir):
    sc = E.sc
    E.frame_t = t
    E.layer = layer
    sc.frame_set(f)
    apply(E, t, layer)
    sc.render.filepath = dst
    bpy.ops.render.render(write_still=True)
    cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
    finish(dst, cand[-1] if cand else "", E.grade)
    for x in cand:
        os.remove(x)


def _render(E, frames, out):
    from PIL import Image
    sc = E.sc
    mist_dir = os.path.join(out, "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"
    bpy.app.handlers.frame_change_pre.clear()

    def handler(scene, depsgraph=None):
        apply(E, M._no_cross(E, (scene.frame_current + scene.frame_subframe - 1) / FPS), getattr(E, "layer", None))

    bpy.app.handlers.frame_change_pre.append(handler)
    d0, d1 = b("dissolve"), b("dissolve", 1)
    r0, r1 = b("back"), b("back", 1)
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not E.force:
            continue
        t = (f - 1) / FPS
        if d0 <= t < d1 or r0 <= t < r1:                          # a dissolve: both sides, blended
            a = ss(d0, d1, t) if t < d1 else 1 - ss(r0, r1, t)
            tmp = os.path.join(out, f"_now_{f:04d}.png")
            _render_one(E, f, t, "present", tmp, mist_dir)
            _render_one(E, f, t, "past", dst, mist_dir)
            im = Image.blend(Image.open(tmp).convert("RGB"), Image.open(dst).convert("RGB"), a)
            im.save(dst)
            os.remove(tmp)
        else:
            _render_one(E, f, t, None, dst, mist_dir)
        E.layer = None
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
    n_frames = int(round(tl["length"] * FPS))
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
    E = build(tl, a.tex_dir, a.assets, a.res, a.samples)
    E.force = bool(a.times)
    E.mouth = {}
    E.pat = None
    if not os.path.exists(a.voice):
        alt = os.path.join(os.path.dirname(a.voice), "audio.wav")
        a.voice = alt if os.path.exists(alt) else a.voice
    if os.path.exists(a.voice):
        from ep09_new import _lipsync
        mouth_tl = dict(tl, lines=[ln for ln in tl["lines"] if not ln.get("vo") and ln["name"] != "steve_didnt"])
        E.mouth = _lipsync(mouth_tl, a.voice)
    prepare(E)
    E.cuts = sorted(t0 for _, t0 in shots() if t0 > 0 and _ not in ("past",))
    _render(E, frames, out)


if __name__ == "__main__":
    main()
