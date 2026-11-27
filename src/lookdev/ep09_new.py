"""Episode 9's new-look shots (the hook, the upgrade, the new world, Null, the
chase), rendered from the episode's timeline and voices. Everything that moves
is a function of time, applied in a frame handler, so any frame can be rendered
on its own (shards), with motion blur.

    python src/lookdev/ep09_new.py build/timeline.json build/voice.wav build/tex ASSETS out_dir \
        [--shard 3/40] [--res 1080] [--samples 32] [--times 110.2,141.0] [--list]

Frames written: out_dir/NNNN.png (the same numbering as the episode render),
already hazed and graded. --list prints the frames this renderer owns.
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))

FPS = 24
STEVE_AT = Vector((-1.25, 0.0, 0.0))
NOOB_AT = Vector((1.3, 0.15, 0.0))
PATCH_AT = Vector((0.05, 0.35, 2.3))
NULL_AT = Vector((-2.0, 34.0, 0.0))          # behind the hill top; z set from the ground
RUN_SPEED = 3.2


# ------------------------------------------------------------------ helpers
def ss(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    u = min(1.0, max(0.0, (x - a) / (b - a)))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, pre + k + "."))
        else:
            out[pre + k] = v
    return out


def unflat(d):
    out = {}
    for k, v in d.items():
        cur = out
        ks = k.split(".")
        for p in ks[:-1]:
            cur = cur.setdefault(p, {})
        cur[ks[-1]] = v
    return out


class Keys:
    """Values (numbers or dicts of numbers) at times; eased in between, held outside.
    keys: [(t, value, blend)] - blend = seconds of the transition INTO that key."""

    def __init__(self, keys, base=None):
        self.k = sorted(keys, key=lambda k: k[0])
        self.base = base or (lambda k: 0.0)          # the value of a key a pose leaves out

    def at(self, t):
        prev = {}
        out = {}
        for i, (tk, v, bl) in enumerate(self.k):
            fv = flat(v) if isinstance(v, dict) else {"_": v}
            if t >= tk:
                u = 1.0
            elif t >= tk - bl:
                u = ss(tk - bl, tk, t)
            else:
                break
            keys = set(out) | set(fv)
            out = {k: lerp(out.get(k, self.base(k)), fv.get(k, self.base(k)), u) for k in keys}
        return out


# --------------------------------------------------------------- the scene
class Ep:
    pass


def build(tl, voice_path, tex_dir, assets, res, samples):
    from kit.timeref import resolve
    from world import build_world, add_world_fx
    from stage import build_steve, build_noob_char, build_patch_char, build_null_char, null_lights, char_light
    E = Ep()
    E.tl = tl
    E.T = lambda ref: resolve(tl["beats"], ref, tl["length"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.use_scripts_auto_execute = True
    sc = bpy.context.scene
    E.sc = sc
    # the world: the stage flat, a flat corridor for the chase (toward -y)
    path = [(0, -14, 8), (0, -26, 8), (-11, 0, 10)]
    cfg = {"seed": 7, "sun": (140, 34), "flat_box": [-7, 7, -40, 6], "plant_clear_box": [-4.5, 4.5, -42, 4],
           "keep_clear": [(0, -14, 8), (-14, 3, 7), (-22, 3, 9)] + path,
           "clear_plants": [(STEVE_AT.x, STEVE_AT.y, 1.0), (NOOB_AT.x, NOOB_AT.y, 1.0)],
           "particle_box": (-7, 9, -6, 16, 0.4, 6.5)}
    E.W = W = build_world(sc, assets, cfg)
    add_world_fx(W)
    nx, ny = NULL_AT.x, NULL_AT.y
    E.null_ground = W.layout.height(nx, ny)
    # characters, new and old
    E.S = build_steve(sc)
    from props import sprite_item, hold                    # his pickaxe, new with his new arms
    pk = sprite_item("iron_pickaxe", os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets",
                                                  "minecraft", "textures", "item"), px=0.072)
    hold(E.S.arm, pk, "sr", up=25, face=60, collection=[E.S.rig])
    E.S.parts["arms"].append(pk)
    E.N = build_noob_char(sc)
    E.P = build_patch_char(sc, size=0.4)
    E.X = build_null_char(sc, assets, height=15.0)
    null_lights(sc, E.X)
    tex = {os.path.splitext(n)[0]: os.path.join(tex_dir, n) for n in os.listdir(tex_dir)}
    from kit.rigs import make_steve, make_noob, make_patch
    E.oS = make_steve(tex, name="old_steve", faces=True)
    E.oN = make_noob(tex, name="old_noob", faces=True)
    E.oP = make_patch(tex, name="old_patch", s=0.95)
    E.old_parts = {
        "steve": {"legs": ["leg_r", "leg_l"], "body": ["torso"], "arms": ["arm_r", "arm_l"], "head": ["head"]},
        "noob": {"legs": ["leg_r", "leg_l"], "body": ["torso"], "arms": ["arm_r", "arm_l"], "head": ["head"]},
    }
    # character light (edge spots follow each one; a key from the camera side)
    E.edges = []
    for nm in ("steve", "noob"):
        for k, (dx, dy, dz, p, c, az) in enumerate(((-1.6, 2.6, 2.3, 700, (0.72, 0.92, 1.0), 1.55),
                                                    (1.2, 2.4, 3.4, 550, (1.0, 0.8, 0.55), 1.8))):
            ob = char_light(sc, f"{nm}_edge{k}", (0, 0, 0), p, c)
            E.edges.append((nm, ob, Vector((dx, dy, dz)), az))
    E.key = char_light(sc, "char_key", (0, -3, 3), 650, (1.0, 0.88, 0.76), cone=34, size=0.9)
    # the upgrade's scan ring and pixel bursts
    E.ring = _ring(sc)
    E.wave_ring = _ring(sc, "wave_ring", r=1.0, h=0.16, strength=5.0)
    E.bursts = _bursts(sc, E)
    E.debris = _debris(sc, W)
    # the camera
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.dof.use_dof = True
    cam.data.sensor_width = 36
    E.cam = cam
    # render settings
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = res * 9 // 16
    sc.render.resolution_y = res
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = -0.1
    sc.render.fps = FPS
    sc.render.compositor_device = "CPU"
    _mist_output(sc)
    # voices -> mouth shapes per frame, per speaker
    E.mouth = _lipsync(tl, voice_path)
    E.lines = tl["lines"]
    chor = Choreo(E)
    E.chor = chor
    return E


def _ring(sc, name="scan_ring", r=0.62, h=0.035, strength=2.6):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=r, radius2=r, depth=h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Color"].default_value = (0.25, 0.95, 1.0, 1)
    b.inputs["Emission Strength"].default_value = strength
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.visible_shadow = False
    ob.hide_render = True
    return ob


def _bursts(sc, E):
    """Pools of little glowing cubes for the part swaps."""
    m = bpy.data.materials.new("burst")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Color"].default_value = (0.4, 0.95, 1.0, 1)
    b.inputs["Emission Strength"].default_value = 3.5
    me = bpy.data.meshes.new("burst_cube")
    s = 0.5
    me.from_pydata([(x, y, z) for x in (-s, s) for y in (-s, s) for z in (-s, s)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(m)
    pool = []
    for i in range(40):
        ob = bpy.data.objects.new(f"burst_{i}", me)
        sc.collection.objects.link(ob)
        ob.visible_shadow = False
        ob.hide_render = True
        pool.append(ob)
    return pool


def _debris(sc, W):
    """Chunks of the world pulled up into Null's storm while he erases it."""
    mats = [m for m in bpy.data.materials if m.name in ("w_grass_side", "w_dirt", "w_stone", "w_oak_leaves")]
    pool = []
    for i in range(60):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"debris_{i}"
        ob.data.materials.append(mats[i % len(mats)])
        ob.hide_render = True
        pool.append(ob)
    return pool


def _mist_output(sc):
    sc.view_layers[0].use_pass_mist = True
    w = sc.world
    w.mist_settings.start = 0
    w.mist_settings.depth = 600
    w.mist_settings.falloff = "LINEAR"
    t = bpy.data.node_groups.new("comp", "CompositorNodeTree")
    sc.compositing_node_group = t
    rl = t.nodes.new("CompositorNodeRLayers")
    t.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    go = t.nodes.new("NodeGroupOutput")
    t.links.new(rl.outputs["Image"], go.inputs[0])
    of = t.nodes.new("CompositorNodeOutputFile")
    of.format.media_type = "IMAGE"
    of.format.file_format = "PNG"
    of.format.color_depth = "16"
    of.format.color_mode = "BW"
    of.file_output_items.new("FLOAT", "mist")
    t.links.new(rl.outputs["Mist"], of.inputs["mist"])
    sc["mist_node"] = of.name


def _lipsync(tl, voice_path):
    """Per speaker, per frame: the mouth (m_* values), smoothed like hand lip-sync."""
    import soundfile as sf
    from lips import shapes_from
    from mouths import VISEME
    from faceplate import MOUTH_DEFAULTS
    x, sr = sf.read(voice_path)
    x = x.mean(1) if x.ndim > 1 else x
    n = int((tl["length"] + 1) * FPS) + 2
    keys = ["m_w", "m_o", "m_arch", "m_up", "m_r", "m_vee", "m_tilt", "m_tu", "m_tl", "m_tg"]
    out = {}
    for ln in tl["lines"]:
        who = ln["who"]
        seg = x[int(ln["start"] * sr):int(ln["end"] * sr)]
        if len(seg) < sr // 20:
            continue
        seq = shapes_from(seg, sr, FPS)
        f0 = int(round(ln["start"] * FPS))
        arr = out.setdefault(who, {})
        cur = {k: MOUTH_DEFAULTS[k] for k in keys}
        for i, s_, loud in seq:
            tgt = {k: MOUTH_DEFAULTS[k] for k in keys}
            tgt.update({k: v for k, v in VISEME[s_].items() if k in keys})
            if s_ in "CDEH":
                tgt["m_o"] *= max(0.45, min(1.2, 0.35 + loud))
            cur = {k: 0.35 * cur[k] + 0.65 * tgt[k] for k in keys}
            arr[f0 + i] = dict(cur)
    return out


# ----------------------------------------------------------- expressions
SF = {   # Steve: eyes (both_*), mouth (m_*), brows (bb_*)
    "neutral": {},
    "stunned": {"both_to": 0.25, "both_tm": 0.3, "both_ti": 0.25, "both_ps": 0.85, "bb_raise": 0.35, "bb_arch": 0.4},
    "amazed": {"both_to": 0.2, "both_tm": 0.25, "both_ti": 0.2, "both_py": 0.35, "bb_raise": 0.3, "m_o": 0.3,
               "m_w": 1.2, "m_up": 0.9, "m_r": 0.9, "m_vee": 0.3},
    "flat": {"both_to": -0.35, "both_tm": -0.4, "both_ti": -0.3, "bb_raise": -0.1, "m_arch": 0.05},
    "smile": {"both_bo": 0.2, "both_bm": 0.35, "both_bi": 0.2, "m_arch": -0.22, "m_w": 2.0, "bb_raise": 0.1},
    "smug": {"both_to": -0.1, "both_tm": -0.14, "both_ti": -0.2, "both_bm": 0.25, "m_arch": -0.08, "m_tilt": 0.12,
             "bb_tilt": 0.2},
    "worried": {"both_to": -0.3, "both_ti": 0.15, "m_arch": 0.18, "bb_tilt": -0.8, "bb_raise": 0.2},
    "scared": {"both_to": 0.3, "both_tm": 0.35, "both_ti": 0.3, "both_ps": 0.7, "bb_tilt": -0.7, "bb_raise": 0.35,
               "m_o": 0.5, "m_w": 2.0, "m_up": 0.88, "m_r": 0.5, "m_vee": 0.2, "m_arch": 0.12, "m_tu": 1, "m_tl": 0.6},
}
NF = {   # the Noob
    "neutral": {},
    "happy": {"both_bm": 0.25, "m_arch": -0.4},
    "teary": {"both_bm": 0.45, "both_bo": 0.3, "both_bi": 0.3, "both_ps": 1.2, "m_arch": -0.3},
    "confused": {"eR_to": 0.1, "eL_to": -0.35, "eL_tm": -0.4, "eL_ti": -0.45, "m_tilt": -0.12, "m_arch": 0.0},
    "shock": {"both_w": 1.12, "both_h": 1.95, "both_ps": 0.8, "m_o": 0.85, "m_w": 1.2, "m_up": 0.92, "m_r": 0.9,
              "m_vee": 0.38, "m_tu": 0.6, "m_arch": 0.0},
    "awe": {"both_py": 0.45, "both_h": 1.8, "m_o": 0.45, "m_w": 1.1, "m_up": 0.9, "m_r": 0.9, "m_vee": 0.3, "m_arch": 0.0},
    "worried": {"both_to": -0.4, "both_ti": 0.15, "both_h": 1.75, "m_arch": 0.2},
    "scared": {"both_w": 0.85, "both_h": 1.8, "both_ps": 0.7, "both_bm": 0.15, "m_o": 0.6, "m_w": 2.0, "m_up": 0.85,
               "m_r": 0.5, "m_vee": 0.1, "m_arch": 0.15, "m_tu": 1, "m_tl": 0.7},
    "shout": {"both_ti": -0.4, "both_tm": -0.1, "both_h": 1.9, "m_o": 0.9, "m_w": 1.8, "m_up": 0.92, "m_r": 0.6,
              "m_vee": 0.15, "m_arch": 0.05, "m_tu": 0.8},
}


# --------------------------------------------------------------- choreography
class Choreo:
    """Ep 9's new-look part: where everyone is, how they move and look, shot by shot."""

    def __init__(self, E):
        self.E = E
        T = E.T
        self.t_up = {"steve": T("up_steve"), "noob": T("up_noob"), "patch": T("up_patch")}
        self.swap = {k: [v + 0.75, v + 1.5, v + 2.25, v + 3.0] for k, v in self.t_up.items()}
        self.t_world = T("up_world")
        self.t_quiet = T("quiet")
        self.t_rise = T("rise")
        self.t_del = T("delete")
        self.t_run = T("run")
        self.t_end = tl_end = E.tl["length"] + 0.4
        self.hook_end = T("rewind") + 1.0 / FPS         # (one frame of overlap with the old look)
        self.new_from = T("patch_upgrade.end")
        # shots: (from, to, camera function)
        L = lambda name: (T(name), T(name + ".end"))   # noqa: E731
        sh = []
        A = lambda r: T(r)                              # noqa: E731
        sh.append((self.new_from, A("steve_hair"), self.cam_full("steve", (0.25, -4.7, 1.05), (0.15, -4.0, 1.1), 32)))
        sh.append((A("steve_hair"), A("noob_beautiful"), self.cam_close("steve", (0.35, -2.05, 0.0), 42)))
        sh.append((A("noob_beautiful"), A("steve_dont"), self.cam_close("noob", (-0.3, -2.1, 0.0), 42)))
        sh.append((A("steve_dont"), A("up_noob"), self.cam_close("steve", (0.3, -1.85, 0.0), 44)))
        sh.append((A("up_noob"), A("noob_textured"), self.cam_full("noob", (-0.2, -4.6, 1.05), (-0.15, -3.9, 1.1), 32)))
        sh.append((A("noob_textured"), A("steve_welcome"), self.cam_close("noob", (-0.45, -2.7, -0.3), 36)))
        sh.append((A("steve_welcome"), A("up_patch"), self.cam_close("steve", (0.45, -2.6, -0.2), 38)))
        sh.append((A("up_patch"), A("noob_smile"), self.cam_patch((0.05, -1.45, 0.0), 45)))
        sh.append((A("noob_smile"), A("patch_always"), self.cam_close("noob", (-0.25, -1.8, 0.0), 44)))
        sh.append((A("patch_always"), A("up_world"), self.cam_patch((0.25, -1.4, -0.05), 45)))
        sh.append((A("up_world"), A("steve_nice"), self.cam_crane))
        sh.append((A("steve_nice"), A("noob_him"), self.cam_two))
        sh.append((A("noob_him"), A("quiet"), self.cam_close("noob", (-0.3, -2.0, 0.0), 42)))
        sh.append((A("quiet"), A("steve_quiet"), self.cam_wide_quiet))
        sh.append((A("steve_quiet"), A("rise"), self.cam_close("steve", (0.3, -2.0, 0.0), 42)))
        sh.append((A("rise"), A("delete"), self.cam_rise))
        sh.append((A("delete"), A("noob_run"), self.cam_delete))           # straight into "RUUUN!"
        sh.append((A("noob_run"), A("run"), self.cam_close("noob", (-0.15, -1.9, 0.0), 36, shake=0.02)))
        sh.append((A("run"), tl_end + 0.1, self.cam_chase))
        self.shots = sh

    def line_at(self, t):
        for ln in self.E.lines:
            if ln["start"] <= t < ln["end"]:
                return ln["name"]
        return None

    # ---- spans this renderer owns
    def owns(self, t):
        return t < self.hook_end or t >= self.new_from - 1.0 / FPS     # a frame of overlap: no gaps

    def story_t(self, t):
        """The hook is a moment of the chase."""
        if t < self.hook_end:
            return self.t_run + 0.9 + t
        if t < self.new_from:
            return self.new_from
        return t

    # ---- character positions over time
    def run_offset(self, t):
        if t < self.t_run:
            return 0.0
        u = t - self.t_run
        return -RUN_SPEED * (u - 0.35 * (1 - math.exp(-u / 0.35)))      # accelerates into the run

    def facing(self, t):
        """0 = toward the camera side (-y); turns toward Null during the rise and delete."""
        a = ss(self.t_del - 0.2, self.t_del + 0.6, t) * (1 - ss(self.E.T("noob_run"), self.E.T("noob_run") + 0.4, t))
        return a * 40.0

    # ---- cameras
    def head(self, who, t):
        E = self.E
        old = t < self.swap.get(who, [0, 0, 0, 0])[3] and t >= self.new_from     # still the old head
        if who == "steve":
            return Vector((STEVE_AT.x, STEVE_AT.y + self.run_offset(t), 1.75 if old else 1.68))
        if who == "noob":
            return Vector((NOOB_AT.x, NOOB_AT.y + self.run_offset(t), 1.92 if old else 1.77))
        return self.patch_pos(t)

    def cam_full(self, who, p0, p1, lens):
        at = STEVE_AT if who == "steve" else NOOB_AT

        def f(t, u):
            loc = Vector(at) + Vector(p0).lerp(Vector(p1), ss(0, 1, u))
            return loc, Vector((at.x, at.y, 1.0)), lens, (loc - Vector((at.x, at.y, 1.0))).length, 3.2, 0.0
        return f

    def cam_close(self, who, off, lens, shake=0.0):
        def f(t, u):
            h = self.head(who, t)
            loc = h + Vector((off[0], off[1], -0.04 + off[2])) + Vector((0.0, 0.1 * u, 0))
            look = h + Vector((0, 0, -0.2))
            return loc, look, lens, (loc - look).length, 1.2, shake
        return f

    def cam_patch(self, off, lens):
        def f(t, u):
            p = self.patch_pos(t)
            loc = p + Vector(off) + Vector((0.0, 0.08 * u, 0.0))
            return loc, p, lens, (loc - p).length, 1.4, 0.0
        return f

    def cam_crane(self, t, u):
        k = ss(0.05, 1.0, u)
        loc = Vector((0.1, -4.6, 1.2)).lerp(Vector((0.4, -15.0, 7.5)), k)
        look = Vector((0.0, 0.0, 1.3)).lerp(Vector((-2.0, 30.0, 7.0)), ss(0.1, 1.0, u))
        return loc, look, lerp(30, 21, k), (loc - Vector((0, 0, 1.3))).length, lerp(2.8, 8.0, k), 0.0

    def cam_two(self, t, u):
        loc = Vector((0.0, -6.0, 1.35)) + Vector((0.12 * u, 0.25 * u, 0))
        look = Vector((0.0, 0.0, 1.3))
        return loc, look, 28, 5.6, 2.4, 0.0

    def cam_wide_quiet(self, t, u):
        loc = Vector((0.3, -8.0, 0.9)).lerp(Vector((0.25, -6.8, 0.95)), u)
        look = Vector((0.0, 8.0, 3.2))
        return loc, look, 26, 8.0, 3.5, 0.0

    def cam_rise(self, t, u):
        loc = Vector((0.9, -6.4, 0.75)) + Vector((0.0, -0.35 * u, 0.1 * u))
        look = Vector((-0.6, 30.0, 8.0)).lerp(Vector((-0.8, 30.0, 10.5)), ss(0, 1, u))
        return loc, look, 22, 6.4, 4.0, 0.004 + 0.012 * ss(0.3, 0.8, u)

    def cam_delete(self, t, u):
        loc = Vector((6.5, -11.5, 3.6)).lerp(Vector((6.0, -10.6, 3.3)), u)
        look = Vector((-1.2, 14.0, 5.2))
        return loc, look, 20, 13.0, 6.0, 0.006

    def cam_chase(self, t, u):
        ts = self.story_t(t)
        y = self.run_offset(ts)
        loc = Vector((0.05, y - 4.1 - 0.5 * ss(0, 2.5, ts - self.t_run), 0.95))
        look = Vector((0.0, y + 10.0, 4.4))
        return loc, look, 21, 4.2, 4.0, 0.012

    def camera(self, t):
        ts = self.story_t(t)
        for a, b, f in self.shots:
            if a <= ts < b:
                return f(ts, (ts - a) / max(1e-6, b - a))
        a, b, f = self.shots[-1]
        return f(ts, 1.0)

    # ---- Patch
    def patch_pos(self, t):
        bob = 0.05 * math.sin(2 * math.pi * 0.7 * t)
        p = Vector(PATCH_AT) + Vector((0, self.run_offset(t), bob))
        if t >= self.t_run:
            p.z = 2.0 + bob
        return p

    # ---- the sky over time: day, then golden after the wave, then Null's storm
    def looks(self, t):
        g = ss(self.t_world + 1.0, self.t_world + 4.0, t)
        s = ss(self.t_quiet + 0.3, self.t_rise + 1.4, t)
        return g, s


# ------------------------------------------------------------ apply a frame
def apply(E, t_render):
    C = E.chor
    t = C.story_t(t_render)
    from faceplate import EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH, set_face
    from brows import set_brows
    from patch import DEFAULTS as PD, set_patch
    from pose import pose
    from noob import pose_noob
    from world import fx_set, set_sky, set_sun, SKY_DAY, SKY_GOLDEN, SKY_STORM
    from stage import place_null_lights
    T = E.T
    f_render = int(round(t_render * FPS))          # voices follow the real clock (the hook's VO is off screen)
    if t_render < C.hook_end:
        f_render = -1
    ro = C.run_offset(t)
    face_dir = C.facing(t)
    running = t >= C.t_run - 0.1
    # ------------------------------------------------ world: reveal wave, sky, erase
    tw = C.t_world
    if t < tw:
        R = 0.0
    else:
        u = max(0.0, (t - tw - 0.2) / 4.0)
        R = 2.0 + 720.0 * u ** 2.3 if u < 1 else 1e5
    g, s = C.looks(t)
    D = 0.0
    Dz = -1.0
    nxy = (NULL_AT.x, NULL_AT.y - (2.2 * max(0.0, t - C.t_run) if t >= C.t_run else 0.0))
    if t >= C.t_del:
        D = min(4.0 + 11.0 * (t - C.t_del), nxy[1] - ro - 9.0)    # the void stays behind them
        Dz = 1.0
    fx_set(E.W, R=R, Wd=5.0 + 0.12 * min(R, 1e3), Cx=0.0, Cy=0.0, D=D, Nx=nxy[0], Ny=nxy[1], Dz=Dz)
    E.W.water.hide_render = R < 60
    for ob in getattr(E.W, "particles", []):
        ob.hide_render = R < 30 or s > 0.5 and ob.name.startswith("falling_leaf")
    wr = E.wave_ring
    wr.hide_render = not (tw <= t < tw + 4.2)
    if not wr.hide_render:
        wr.scale = (R, R, 1.0)
        wr.location = (0, 0, 0.3)
    def mixlook(a, b, k):
        out = {}
        for key in a:
            va, vb = a[key], b[key]
            out[key] = tuple(lerp(x, y, k) for x, y in zip(va, vb)) if isinstance(va, tuple) else lerp(va, vb, k)
        return out
    day = dict(SKY_DAY, fill=1.1, fill_col=(176, 204, 240))
    gold = dict(SKY_GOLDEN, fill=1.1, fill_col=(176, 204, 240))
    storm = dict(SKY_STORM)
    look = mixlook(mixlook(day, gold, g), storm, s)
    set_sky(E.W, look)
    sun_day, sun_gold, sun_storm = (140, 34, 5.4, (1.0, 0.9, 0.8)), (140, 16, 6.2, (1.0, 0.76, 0.5)), (140, 30, 1.4, (0.85, 0.75, 1.0))
    a_ = lerp(lerp(sun_day[1], sun_gold[1], g), sun_storm[1], s)
    en = lerp(lerp(sun_day[2], sun_gold[2], g), sun_storm[2], s)
    col = tuple(lerp(lerp(x, y, g), z, s) for x, y, z in zip(sun_day[3], sun_gold[3], sun_storm[3]))
    set_sun(E.W, 140, a_, en, col)
    if g > 0 and s < 1:                                        # the golden glow placed in frame
        ga, ge = math.radians(22), math.radians(14)
        E.W.sky_dot.inputs[1].default_value = (math.sin(ga) * math.cos(ge), math.cos(ga) * math.cos(ge), math.sin(ge))
    E.W.clouds.hide_render = s > 0.5
    # ------------------------------------------------ Null
    X = E.X
    vis_null = t >= C.t_rise or t_render < C.hook_end
    ground = E.null_ground
    if t < C.t_rise:
        zn = ground - 26
    else:
        zn = lerp(ground - 26, ground + 2.0, ss(0, 2.8, t - C.t_rise) ** 0.8)
    X.root.location = (nxy[0], nxy[1], zn)
    X.root.rotation_euler = (0, 0, 0)
    for o in X.col.objects:
        o.hide_render = not vis_null
    X.glow.hide_render = not vis_null
    if getattr(X, "orbit", None):
        X.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0.9 * t)
    if getattr(X, "orbit2", None):
        X.orbit2.rotation_euler = (math.radians(-12), math.radians(14), -0.6 * t)
    reach = ss(C.t_del - 0.3, C.t_del + 0.6, t)
    for side, sgn in (("sl", 1), ("sr", -1)):
        X.arms[side].rotation_euler = (math.radians(-35 * reach), math.radians(sgn * 12 * reach), 0)
    place_null_lights(X, fade=ss(C.t_rise, C.t_rise + 1.5, t) if vis_null else 0.0)
    # debris: chunks lifted from the erasing front up into the storm
    rnd = random.Random(5)
    for i, ob in enumerate(E.debris):
        t0 = C.t_del + rnd.uniform(0, 9.0)
        life = 1.8
        u = (t - t0) / life
        a0 = math.radians(rnd.uniform(-60, 60))
        ob.hide_render = not (0 <= u < 1) or Dz < 0
        if ob.hide_render:
            continue
        r0 = 4.0 + 7.5 * (t0 - C.t_del)
        start = Vector((nxy[0] + r0 * math.sin(a0), nxy[1] - r0 * math.cos(a0), 0.5))
        end = Vector((nxy[0] + rnd.uniform(-6, 6), nxy[1], zn + 6 + rnd.uniform(0, 8)))
        p = start.lerp(end, u ** 1.6)
        p.z += 3.0 * math.sin(math.pi * u)
        ob.location = p
        ob.rotation_euler = (3 * u + i, 2 * u, u * 4)
        sc_ = 0.6 * (1 - 0.7 * u)
        ob.scale = (sc_, sc_, sc_)
    # ------------------------------------------------ the upgrades: which parts are new
    def new_parts(who):
        if t_render < C.hook_end or t >= C.t_world:
            return {"legs", "body", "arms", "head"}
        sw = C.swap[who]
        return {p for p, ts in zip(("legs", "body", "arms", "head"), sw) if t >= ts}
    S, N, P = E.S, E.N, E.P
    ns = new_parts("steve")
    for part, obs in S.parts.items():
        for o in obs:
            o.hide_render = part not in ns
    if "head" in ns and t < C.swap["steve"][3] + 0.7 and t_render >= C.hook_end:      # the hair pops in last
        for o in S.parts["head"]:
            if o.name.startswith("steve_hair"):
                o.hide_render = True
    nn = new_parts("noob")
    for part, obs in N.parts.items():
        for o in obs:
            o.hide_render = part not in nn

    def old_body(rig, who, new, plate):
        for part, names in E.old_parts[who].items():
            for nm in names:
                for o in [rig.parts[nm]] + list(rig.parts[nm].children_recursive):
                    o.hide_render = part in new
        for expr, o in rig.faces.items():               # one face plate shows (talking or not)
            o.hide_render = "head" in new or expr != plate
    ms = E.mouth.get("steve", {}).get(f_render)
    mn = E.mouth.get("noob", {}).get(f_render)
    old_s = "surprised" if t < T("steve_hair") else "neutral"
    old_n = {"noob_beautiful": "happy"}.get(C.line_at(t), "neutral")
    old_body(E.oS, "steve", ns, old_s + ("_talk" if ms and ms["m_o"] > 0.25 else ""))
    old_body(E.oN, "noob", nn, old_n + ("_talk" if mn and mn["m_o"] > 0.25 else ""))
    pnew = t_render < C.hook_end or t >= C.swap["patch"][0] + 0.05
    for o in P.col.objects:
        if o.name.endswith("_beam"):
            continue
        o.hide_render = not pnew
    for o in [E.oP.root] + list(E.oP.root.children_recursive):
        o.hide_render = pnew or "beam" in o.name
    # the scan ring sweeping up whoever is upgrading
    ring = E.ring
    ring.hide_render = True
    for who, at, h1 in (("steve", STEVE_AT, 2.12), ("noob", NOOB_AT, 2.1)):
        t0 = C.t_up[who]
        if t0 <= t < t0 + 3.4:
            u = t - t0
            z = float(np.interp(u, (0, 0.75, 1.5, 2.25, 3.0, 3.4), (0.0, 0.75, 1.5, 1.62, h1, h1 + 0.15)))
            ring.hide_render = False
            ring.location = (at.x, at.y, z)
            ring.scale = (1.0, 1.0, 1.0)
    t0 = C.t_up["patch"]
    if t0 <= t < t0 + 1.2:
        u = (t - t0) / 1.0
        pp = C.patch_pos(t)
        ring.hide_render = False
        ring.location = (pp.x, pp.y, pp.z - 0.32 + 0.64 * min(1.0, u))
        ring.scale = (0.55, 0.55, 1.0)
    # pixel bursts at each swap
    k = 0
    pool = E.bursts
    for ob in pool:
        ob.hide_render = True
    for who, at in (("steve", STEVE_AT), ("noob", NOOB_AT), ("patch", None)):
        times = C.swap[who] if who != "patch" else [C.swap["patch"][0]]
        zc = (0.4, 1.1, 1.1, 1.75)
        for j, ts in enumerate(times):
            u = t - ts
            if not (0 <= u < 0.7):
                continue
            c = C.patch_pos(t) if who == "patch" else Vector((at.x, at.y, zc[j]))
            rnd = random.Random(hash((who, j)) & 0xffff)
            for i in range(10):
                if k >= len(pool):
                    break
                ob = pool[k]
                k += 1
                d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.4, 1))).normalized()
                ob.hide_render = False
                ob.location = c + d * (0.25 + 1.6 * u) + Vector((0, 0, -1.2 * u * u))
                s_ = 0.07 * (1 - u / 0.7)
                ob.scale = (s_, s_, s_)
                ob.rotation_euler = (u * 8 + i, u * 5, 0)
    # ------------------------------------------------ bodies
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    idle = lib["idle (Benly 2.2)"]
    breathe = math.sin(2 * math.pi * 0.25 * t)
    # Steve
    sp = flat(idle)
    sp.update(flat(C.steve_act(t)))
    sp["root_yaw"] = 0
    sp["chest_lean"] = sp.get("chest_lean", 0) + 1.2 * breathe
    sp["head_nod"] = sp.get("head_nod", 0) - 0.8 * breathe
    sp = unflat(sp)
    if running:
        ph = 2 * math.pi * 2.6 * (t - C.t_run)
        sw = math.sin(ph)
        sp = {"chest_lean": 16, "chest_twist": 10 * sw, "head_nod": -12, "hips_drop": 0.16 + 0.05 * abs(math.cos(ph)),
              "arm_sl": {"fwd": -55 * sw, "elbow": 85, "out": 8}, "arm_sr": {"fwd": 55 * sw, "elbow": 85, "out": 8},
              "foot_sl": {"y": -0.5 * sw, "z": max(0.0, 0.45 * math.sin(ph + 1.2))},
              "foot_sr": {"y": 0.5 * sw, "z": max(0.0, 0.45 * math.sin(ph + 1.2 + math.pi))}}
    pose(S.arm, sp)
    S.holder.location = (STEVE_AT.x, STEVE_AT.y + ro, 0.0 if not running else 0.06 * abs(math.sin(2 * math.pi * 2.6 * (t - C.t_run))))
    S.holder.rotation_euler = (0, 0, math.radians(face_dir - 4))          # he turns over his left shoulder
    # Noob
    from noob import NOOB_POSES
    npz = dict(NOOB_POSES["idle"])
    npz = flat(npz)
    npz["head_tilt"] = npz.get("head_tilt", 0) + 2 * breathe
    for kk, vv in flat(C.noob_act(t) if hasattr(C, "noob_act") else {}).items():
        npz[kk] = vv
    npz = unflat(npz)
    if running:
        ph = 2 * math.pi * 2.6 * (t - C.t_run) + 0.8
        sw = math.sin(ph)
        npz = {"chest_lean": 10, "head_turn": 0, "arm_sl": {"fwd": -60 * sw, "out": 12}, "arm_sr": {"fwd": 60 * sw, "out": 12},
               "leg_sl": {"fwd": 45 * sw}, "leg_sr": {"fwd": -45 * sw}}
    pose_noob(N, {**npz, "root_yaw": npz.get("root_yaw", 0) - face_dir})  # the Noob over his right
    N.root.location = (NOOB_AT.x, NOOB_AT.y + ro, 0.0 if not running else 0.07 * abs(math.sin(2 * math.pi * 2.6 * (t - C.t_run) + 0.8)))
    # old ones stand where the new ones stand
    E.oS.root.location = (STEVE_AT.x, STEVE_AT.y, 0)
    E.oS.root.rotation_euler = (0, 0, math.radians(-4))
    E.oN.root.location = (NOOB_AT.x, NOOB_AT.y, 0)
    pp = C.patch_pos(t)
    E.oP.root.location = pp
    P.root.location = pp
    P.root.rotation_euler = (0, 0, math.radians(0.5 * face_dir))
    fl = 25 * math.sin(2 * math.pi * 2.0 * t) * (C.patch_flap(t) if hasattr(C, "patch_flap") else 0)
    for side, pv in P.fins.items():
        pv.rotation_euler = (math.radians(fl) * (1 if side == "l" else -1), 0, 0)
    # ------------------------------------------------ faces
    def blink(t, phase):
        u = (t + phase) % 3.7
        return 0.0 if u < 0.09 else (0.5 if u < 0.14 else 1.0)
    sf = C.steve_face(t) if hasattr(C, "steve_face") else {}
    fs = {f"{e}_{k}": v for e in EYES for k, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    for kk, vv in sf.items():
        if kk.startswith("both_"):
            for e in EYES:
                fs[f"{e}_{kk[5:]}"] = vv
        elif not kk.startswith("bb_"):
            fs[kk] = vv
    talk(fs, E.mouth.get("steve", {}).get(f_render))
    bl = blink(t, 0.3)
    for e in EYES:
        fs[f"{e}_open"] = fs.get(f"{e}_open", 1.0) * bl
    set_face(S.face, fs)
    for ob_ in S.brows.values():                       # brows: the expression's keys, the rest at rest
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(S.brows, {k: v for k, v in sf.items() if k.startswith("bb_")})
    nf = C.noob_face(t) if hasattr(C, "noob_face") else {}
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    for kk, vv in nf.items():
        if kk.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{kk[5:]}"] = vv
        else:
            fn[kk] = vv
    talk(fn, E.mouth.get("noob", {}).get(f_render))
    bl = blink(t, 1.7)
    for e in NOOB_EYES:
        fn[f"{e}_open"] = fn.get(f"{e}_open", 1.0) * bl
    set_face(N.face, fn)
    pf = dict(PD)
    pf.update(C.patch_face(t) if hasattr(C, "patch_face") else {})
    pf["open"] = pf.get("open", 1.0) * blink(t, 2.4)
    set_patch(P, pf)
    # ------------------------------------------------ lights follow
    for nm, ob, off, az in E.edges:
        at = Vector(S.holder.location) if nm == "steve" else Vector(N.root.location)
        ob.location = at + off
        ob.rotation_euler = (at + Vector((0, 0, az)) - ob.location).to_track_quat("-Z", "Y").to_euler()
        ob.data.energy = ob.get("p0", ob.data.energy)
        ob["p0"] = ob.data.energy
    # ------------------------------------------------ camera
    loc, lookat, lens, focus, fstop, shake = C.camera(t_render)
    if shake:
        loc = loc + Vector((shake * math.sin(t * 37.0), 0, shake * math.cos(t * 29.0)))
    cam = E.cam
    cam.location = loc
    cam.rotation_euler = (lookat - loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.focus_distance = max(0.2, focus)
    cam.data.dof.aperture_fstop = fstop
    key = E.key
    d = (lookat - loc).normalized()
    right = d.cross(Vector((0, 0, 1))).normalized()
    key.location = loc + right * 1.6 + Vector((0, 0, 1.4))
    key.rotation_euler = (lookat - key.location).to_track_quat("-Z", "Y").to_euler()
    key.data.energy = 650 * (1 - 0.35 * s)
    key.data.color = tuple(lerp(a_, b_, s) for a_, b_ in zip((1.0, 0.88, 0.76), (0.86, 0.84, 1.0)))
    return {"g": g, "s": s}


def talk(face, mo):
    """Layer the voice's mouth over the expression's: the opening comes from the
    voice, the width and the smile or frown stay the expression's."""
    if not mo:
        return
    for k in ("m_o", "m_up", "m_r", "m_vee", "m_tu", "m_tl", "m_tg"):
        face[k] = max(face.get(k, 0.0), mo[k]) if k == "m_o" and face.get("m_o", 0) > 0.3 else mo[k]
    face["m_w"] = face["m_w"] + (mo["m_w"] - 1.9) * 0.8
    face["m_arch"] = face["m_arch"] * (1 - 0.6 * min(1.0, mo["m_o"] * 2))


# ------------------------------------------------------------- acting
def _acting(C):
    """Who does what, line by line (keys of poses and faces)."""
    E = C.E
    T = E.T
    from faceplate import EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from patch import DEFAULTS as PD
    from noob import NOOB_POSES
    idle_s = flat(json.load(open(os.path.join(HERE, "poses_lib.json")))["idle (Benly 2.2)"])
    idle_n = flat(NOOB_POSES["idle"])

    def face_base(eyes, mouth):
        def b(k):
            if k.startswith(("both_", "eR_", "eL_")):
                return eyes.get(k.split("_", 1)[1], 0.0)
            return mouth.get(k, 0.0)
        return b
    sbase = face_base(EYE_DEFAULTS, MOUTH_DEFAULTS)
    nbase = face_base(NOOB_EYE_DEFAULTS, {**MOUTH_DEFAULTS, **NOOB_MOUTH})
    look_noob = {"head_turn": -22}
    look_steve = {"head_turn": 22}
    C.steve_keys = Keys([
        (C.new_from, {"head_nod": 14}, 0.1),
        (T("up_steve") + 3.2, {"head_nod": 0}, 0.4),
        (T("steve_hair"), {"arm_sl": {"fwd": 150, "elbow": 115, "out": 25, "twist": -10}, "head_nod": -6}, 0.5),
        (T("steve_hair.end") - 0.3, {"arm_sl": {"fwd": 150, "elbow": 115, "out": 25, "twist": -10}, "head_nod": -6}, 0.2),
        (T("noob_beautiful"), look_noob, 0.3),
        (T("steve_dont"), {"head_turn": -30, "head_nod": 6}, 0.25),
        (T("up_noob"), look_noob, 0.4),
        (T("steve_welcome"), {"head_turn": -26, "arm_sr": {"fwd": 30, "elbow": 60, "out": 12}}, 0.4),
        (T("up_patch"), {"head_turn": -12, "head_nod": -14}, 0.4),
        (T("up_world"), {"head_nod": -12, "head_turn": 8}, 0.6),
        (T("up_world") + 2.5, {"head_nod": -18, "head_turn": -14}, 1.4),
        (T("steve_nice"), {"head_nod": -4, "head_turn": 10}, 0.5),
        (T("noob_him"), look_noob, 0.4),
        (T("quiet"), {"head_turn": 18, "head_nod": -4}, 0.6),
        (T("steve_quiet"), {"head_turn": -20, "head_nod": -6}, 0.5),
        (T("steve_quiet") + 0.6, {"head_turn": 16, "head_nod": -6}, 0.4),
        (T("rise"), {"head_nod": -24, "arm_sl": {"out": 22, "fwd": 18, "elbow": 40}, "arm_sr": {"out": 22, "fwd": 18, "elbow": 40}, "chest_lean": -6}, 0.6),
        (T("noob_run"), {"head_nod": -10}, 0.3),
        *([(T("steve_stop"), {"head_nod": -6, "head_turn": 24}, 0.2),        # snaps at the Noob
           (T("steve_stop.end") + 0.2, {"head_nod": -10}, 0.4)] if "steve_stop" in E.tl["beats"] else []),
    ], base=lambda k: idle_s.get(k, 0.0))
    C.steve_faces = Keys([
        (C.new_from, SF["stunned"], 0.2), (T("steve_hair"), SF["stunned"], 0.2), (T("steve_hair.end") - 0.6, SF["smile"], 0.4),
        (T("steve_dont"), SF["flat"], 0.2), (T("up_noob"), SF["neutral"], 0.4), (T("steve_welcome"), SF["smug"], 0.3),
        (T("up_patch"), SF["neutral"], 0.4), (T("up_world"), SF["amazed"], 0.6), (T("steve_nice"), SF["smile"], 0.5),
        (T("noob_him"), SF["neutral"], 0.3), (T("quiet"), SF["worried"], 0.6), (T("rise"), SF["scared"], 0.5),
    ], base=sbase)
    C.noob_keys = Keys([
        (C.new_from, {"head_turn": -20}, 0.2),
        (T("noob_beautiful"), {"head_tilt": 14, "arm_sl": {"fwd": 60, "out": -20}, "arm_sr": {"fwd": 60, "out": -20}}, 0.4),
        (T("steve_dont"), {"head_tilt": 6, "head_turn": -20}, 0.4),
        (T("up_noob"), {"head_nod": 16}, 0.3),
        (T("noob_textured"), {"head_nod": 22, "arm_sl": {"fwd": 70, "out": 6}, "arm_sr": {"fwd": 55, "out": 6}}, 0.4),
        (T("steve_welcome"), {"head_turn": -24}, 0.4),
        (T("up_patch"), {"head_turn": -18, "head_nod": -14}, 0.4),
        (T("noob_smile"), {"head_turn": -18, "head_nod": -14, "arm_sl": {"out": 55, "fwd": 25}, "arm_sr": {"out": 55, "fwd": 25}}, 0.25),
        (T("patch_always"), {"head_turn": -18, "head_nod": -14}, 0.5),
        (T("up_world"), {"head_nod": -18, "head_turn": 10}, 0.6),
        (T("noob_woah"), {"head_nod": -24, "head_turn": -8, "arm_sl": {"out": 20}, "arm_sr": {"out": 20}}, 0.6),
        (T("steve_nice"), {"head_turn": -20}, 0.5),
        (T("noob_him"), {"head_turn": -24, "head_tilt": 6}, 0.4),
        (T("quiet"), {"head_turn": 10, "head_nod": -6}, 0.6),
        (T("rise"), {"head_nod": -28, "arm_sl": {"fwd": 75, "out": -8}, "arm_sr": {"fwd": 75, "out": -8}}, 0.6),
        (T("noob_run"), {"head_nod": -6, "arm_sl": {"out": 150, "fwd": 20}, "arm_sr": {"out": 150, "fwd": 20}}, 0.2),
        *([(T("noob_finale"), {"head_nod": 4, "head_tilt": 10}, 0.2),          # to the camera, mid-run
           (T("steve_stop"), {"head_nod": -4, "head_turn": -20}, 0.25)] if "noob_finale" in E.tl["beats"] else []),
    ], base=lambda k: idle_n.get(k, 0.0))
    C.noob_faces = Keys([
        (C.new_from, NF["neutral"], 0.2), (T("noob_beautiful"), NF["teary"], 0.3), (T("up_noob"), NF["neutral"], 0.4),
        (T("noob_textured"), NF["confused"], 0.3), (T("up_patch"), NF["neutral"], 0.4), (T("noob_smile"), NF["shock"], 0.15),
        (T("patch_always"), NF["happy"], 0.4), (T("up_world"), NF["awe"], 0.6), (T("steve_nice"), NF["happy"], 0.5),
        (T("noob_him") + 1.2, NF["worried"], 0.5), (T("quiet"), NF["worried"], 0.4), (T("rise"), NF["scared"], 0.4),
        (T("noob_run"), NF["shout"], 0.15),
        *([(T("noob_finale"), NF["happy"], 0.15), (T("steve_stop"), NF["shout"], 0.2)]
          if "noob_finale" in E.tl["beats"] else []),
    ], base=nbase)
    C.patch_faces = Keys([
        (C.new_from, {"look_x": -0.6}, 0.2), (T("up_noob"), {"look_x": 0.6}, 0.3), (T("up_patch"), {"look_y": -0.4}, 0.3),
        (T("up_patch") + 1.7, {"smile": 1.0}, 0.12), (T("patch_always.end"), {"smile": 1.0}, 0.1),
        (T("up_world"), {"wide": 0.6, "look_y": 0.3}, 0.4), (T("noob_him"), {"look_x": 0.5}, 0.3),
        (T("quiet"), {"squint": 0.4}, 0.4), (T("rise"), {"wide": 1.0, "look_y": 0.5}, 0.3),
        (T("delete"), {"glitch": 1.0, "wide": 0.6}, 0.1),
    ], base=lambda k: PD.get(k, 0.0))
    C.steve_act = lambda t: unflat(C.steve_keys.at(t))
    C.noob_act = lambda t: unflat(C.noob_keys.at(t))
    C.steve_face = lambda t: C.steve_faces.at(t)
    C.noob_face = lambda t: C.noob_faces.at(t)
    C.patch_face = lambda t: C.patch_faces.at(t)
    C.patch_flap = lambda t: ss(T("up_patch") + 1.6, T("up_patch") + 1.9, t) * (1 - ss(T("patch_always.end"), T("patch_always.end") + 0.4, t))


# ------------------------------------------------------------- post (haze + grade)
def finish(path, mist_path, look, sun=None):
    from PIL import Image
    import grade as G
    import assemble
    im = Image.open(path).convert("RGB")
    g, s = look["g"], look["s"]
    if os.path.exists(mist_path):
        params = {"L": lerp(lerp(380, 260, g), 140, s), "start": lerp(lerp(40, 25, g), 12, s),
                  "max": lerp(0.7, 0.8, s)}
        if g > 0.5 and s < 0.5:
            params["haze_warm"] = True
        if s >= 0.5:
            params["haze_storm"] = True
        im = G.haze(im, mist_path, None, params)
    assemble.W, assemble.H = im.size
    o = {"saturation": 1.28, "glow": lerp(0.5, 0.65, max(g, s)), "threshold": 0.7}
    if g > 0.5 and s < 0.5:
        o["tint"] = [1.1, 1.0, 0.86]
    if s >= 0.5:
        o["tint"] = [1.02, 0.9, 1.08]
    assemble.grade(im, o, 0, 0, None)
    im.save(path)


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
    ap.add_argument("--times", help="render these story times only (previews)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    n_frames = int(round((tl["length"] + 0.4) * FPS)) + 1
    if a.list:
        from kit.timeref import resolve
        hook_end, new_from = resolve(tl["beats"], "rewind", tl["length"]), resolve(tl["beats"], "patch_upgrade.end", tl["length"])
        owned = [f for f in range(1, n_frames + 1) if (f - 1) / FPS < hook_end + 1 / FPS or (f - 1) / FPS >= new_from - 1 / FPS]
        print(json.dumps({"frames": owned, "count": len(owned)}))
        return
    E = build(tl, a.voice, a.tex_dir, a.assets, a.res, a.samples)
    _acting(E.chor)
    C = E.chor
    sc = E.sc
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    mist_dir = os.path.join(out, "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"
    state = {}

    def handler(scene, depsgraph=None):
        t = (scene.frame_current + scene.frame_subframe - 1) / FPS
        state["look"] = apply(E, t)

    bpy.app.handlers.frame_change_pre.append(handler)
    if a.times:
        frames = [int(round(float(x) * FPS)) + 1 for x in a.times.split(",")]
    else:
        frames = [f for f in range(1, n_frames + 1) if C.owns((f - 1) / FPS)]
        k, n = (int(x) for x in a.shard.split("/"))
        per = (len(frames) + n - 1) // n
        frames = frames[k * per:(k + 1) * per]
    print("rendering", len(frames), "frames", frames[:1], "...", frames[-1:])
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not a.times:
            continue
        sc.frame_set(f)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        mist = cand[-1] if cand else ""
        finish(dst, mist, state.get("look", {"g": 0, "s": 0}))
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
