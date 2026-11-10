"""Episode 10 (the finale), all in the new look, rendered from the episode's
timeline and voices. Everything that moves is a function of time, applied in a
frame handler, so any frame renders on its own (shards), with motion blur.

    python src/lookdev/ep10_new.py build/timeline.json build/voice.wav build/tex ASSETS out_dir \
        [--shard 3/40] [--res 1080] [--samples 32] [--times 0.0,12.5] [--list]

Three places, one build:
  the forest   the first portal; Null comes through it (after the creator's reference)
  the ledge    what is left over the void: the bridge, the ledge they hang from, Null rising
  the island   the three percent that survives
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from ep09_new import FPS, NF, SF, Keys, _lipsync, _mist_output, flat, lerp, ss, talk, unflat  # noqa: E402

PORTAL_AT = Vector((0.0, 5.0, 0.0))
NULL_H = 15.0
S_X, N_X = -0.62, 0.62                     # Steve screen-left, the Noob screen-right (camera looking +y)
S_HANG, N_HANG = -2.12, -2.2               # their feet below the ledge's top when they hang by both hands
DROP = 1.22                                # how far the Noob falls before Steve has his wrist

DUSK = {"glow": (255, 232, 190), "power": 26.0, "horizon": (255, 206, 176), "mid": (170, 168, 240), "zenith": (60, 96, 214),
        "fill": 1.0, "fill_col": (186, 196, 240)}
STORM = {"glow": (214, 226, 255), "power": 9.0, "horizon": (226, 150, 214), "mid": (128, 92, 170), "zenith": (44, 34, 84),
         "fill": 0.6, "fill_col": (180, 150, 220)}
VOID = {"glow": (236, 214, 255), "power": 5.0, "horizon": (244, 170, 226), "mid": (160, 112, 200), "zenith": (70, 52, 128),
        "fill": 0.85, "fill_col": (196, 166, 232)}                      # bright: the void glows, it isn't black
CLEAR = {"glow": (255, 236, 220), "power": 6.0, "horizon": (255, 214, 226), "mid": (150, 190, 255), "zenith": (60, 130, 240),
         "fill": 1.1, "fill_col": (186, 206, 240)}


class Ep:
    pass


def mixlook(a, b, k):
    out = {}
    for key in a:
        va, vb = a[key], b[key]
        out[key] = tuple(lerp(x, y, k) for x, y in zip(va, vb)) if isinstance(va, tuple) else lerp(va, vb, k)
    return out


# ------------------------------------------------------------------ the build
def _block_kinds(assets):
    """Block materials of our own (the world's carry its effects)."""
    from world import bake_textures, material
    T = bake_textures(assets)
    M = {k: material("v_" + k, T[k]) for k in ("grass_top", "grass_side", "dirt", "stone", "cherry_log", "cherry_log_top")}
    M["cherry_leaves"] = material("v_cherry_leaves", T["cherry_leaves"], alpha=True, rough=0.6, translucent=0.42)
    B = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    M["planks"] = material("v_planks", os.path.join(B, "oak_planks.png"))
    M["cobble"] = material("v_cobble", os.path.join(B, "cobblestone.png"))
    return M, {
        "grass": {"top": M["grass_top"], "side": M["grass_side"], "bottom": M["dirt"]},
        "dirt": {"top": M["dirt"], "side": M["dirt"], "bottom": M["dirt"]},
        "stone": {"top": M["stone"], "side": M["stone"], "bottom": M["stone"]},
        "cobble": {"top": M["cobble"], "side": M["cobble"], "bottom": M["cobble"]},
        "cherry_log": {"top": M["cherry_log_top"], "side": M["cherry_log"], "bottom": M["cherry_log_top"]},
        "cherry_lv": {"top": M["cherry_leaves"], "side": M["cherry_leaves"], "bottom": M["cherry_leaves"]},
    }


def _void_stage(sc, assets, E):
    """The ledge (y <= 0, its top at z = 0, its lip at y = 0), the bridge beyond it
    (planks, each row its own object so they can blink out), the island, the void's eye."""
    from world import voxel_mesh, tree
    M, K = _block_kinds(assets)
    rnd = random.Random(10)
    # the ledge: the last thin shelf of the far side (nothing under it, so a camera in the
    # void sees their faces below its edge and Null above it)
    cells = {(x, y, -1): "cobble" for x in range(-3, 3) for y in (-2, -1) if not (y == -2 and rnd.random() < 0.3)}
    E.ledge = voxel_mesh(sc, "ledge", cells, K, scale=(1, 0.8, 0.25))
    E.planks = []
    for j in range(1, 34):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"plank_{j}"
        ob.scale = (3.0, 0.94, 0.22)
        ob.location = (0, j + 0.5, -0.11)
        ob.data.materials.append(M["planks"])
        ob["y"] = j + 0.5
        E.planks.append(ob)
    # the island: a rough disc of grass, dirt under it, stone tapering away, one cherry tree
    ic = {}
    for x in range(-5, 5):
        for y in range(-4, 6):
            r = math.hypot(x + 0.5, y - 0.5) + rnd.uniform(-0.5, 0.5)
            if r > 4.6:
                continue
            ic[(x, y, -1)] = "grass"
            depth = int(max(0, (4.6 - r) * 1.5 + rnd.uniform(-0.6, 0.6)))
            for k in range(depth):
                ic[(x, y, -2 - k)] = "dirt" if k < 1 else "stone"
    tc = {}
    tree(tc, 2, 3, 0, "cherry", random.Random(3))
    for k in list(tc):
        if k in ic:
            del tc[k]
    E.island = [voxel_mesh(sc, "island", ic, K),
                voxel_mesh(sc, "island_logs", {k: v for k, v in tc.items() if not v.endswith("_lv")}, K),
                voxel_mesh(sc, "island_leaves", {k: v for k, v in tc.items() if v.endswith("_lv")}, K,
                           keep_leaf_faces=("cherry_lv",))]
    # the void's eye: a ring of light far below, closing like a lid
    m = bpy.data.materials.new("void_eye")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc_ = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    nt.links.new(tc_.outputs["Object"], gr.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, (0.5, 0.12, 0.6, 1)
    cr.elements[1].position, cr.elements[1].color = 1.0, (0.01, 0.0, 0.03, 1)
    e2 = cr.elements.new(0.45)
    e2.color = (1.0, 0.25, 1.0, 1)
    e3 = cr.elements.new(0.7)
    e3.color = (0.08, 0.01, 0.16, 1)
    nt.links.new(gr.outputs["Fac"], ramp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 2.2
    E.eye_power = em.inputs["Strength"]
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type="NGON")
    E.eye = bpy.context.active_object
    E.eye.name = "void_eye"
    E.eye.data.materials.append(m)
    E.eye.visible_shadow = False
    E.void_objs = [E.ledge] + E.planks + E.island + [E.eye]


def _cube(col, variant, colour, name):
    """The loose cell: one of Null's cubes with its face on (it never fades)."""
    from null import _cubes, _lin, V, CELL_VARIANTS
    c = _lin(colour)
    items = [((0, 0, 0), V * 0.5, _lin((14, 10, 18)), (0, 0, 0), 0.0, (2, CELL_VARIANTS.index(variant), tuple(v * 2.2 for v in c), 1.0))]
    ob = _cubes(name, items, bpy.data.materials["null_body"], col)
    ob.scale = (1.9, 1.9, 1.9)
    return ob


def build(tl, voice_path, tex_dir, assets, res, samples):
    from kit.timeref import resolve
    from world import build_world, add_world_fx
    from stage import build_steve, build_noob_char, build_patch_char, build_null_char, null_lights, char_light
    from portal import build_portal
    from null import build_hand
    E = Ep()
    E.tl = tl
    E.T = lambda ref: resolve(tl["beats"], ref, tl["length"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.use_scripts_auto_execute = True
    sc = bpy.context.scene
    E.sc = sc
    cfg = {"seed": 7, "sun": (71, 12), "flat_box": [-7, 7, -40, 8], "plant_clear_box": [-2.2, 2.2, 2.5, 6.0],
           "keep_clear": [(0, -14, 8), (0, -26, 8), (0, 16, 5), (0, 24, 5), (15, 5, 7), (27, 7, 9), (41, 9, 11), (56, 11, 12)],
           "feature_trees": [(-6, 15, "big_oak"), (6, 15, "oak"), (-9, 21, "oak"), (9, 20, "big_oak"), (-4, 24, "birch"),
                             (4, 25, "oak"), (-12, 16, "cherry"), (12, 15, "cherry"), (-7, 29, "oak"), (8, 30, "cherry")],
           "clear_plants": [(S_X, -2.6, 0.9), (N_X, -2.3, 0.9)],
           "particle_box": (-6, 6, -6, 9, 0.3, 6.0)}
    E.W = W = build_world(sc, assets, cfg)
    add_world_fx(W)
    E.null_ground = W.layout.height(-2, 34)
    E.world_objs = [W.terrain, W.logs, W.leaves, W.far, W.plants, W.water, W.clouds] + list(getattr(W, "particles", []))
    E.P0 = build_portal(sc, assets, at=PORTAL_AT)
    E.X = build_null_char(sc, assets, height=10.0)
    null_lights(sc, E.X)
    E.hands = (build_hand(E.X.col), build_hand(E.X.col, side="sl", seed=9))
    for h in E.hands:
        h.rotation_mode = "QUATERNION"
    E.S = build_steve(sc)
    E.N = build_noob_char(sc)
    E.Pt = build_patch_char(sc, size=0.4)
    _void_stage(sc, assets, E)
    E.cubes = {"scared": _cube(E.X.col, "scared", (244, 222, 150), "cube_scared"),
               "smile": _cube(E.X.col, "smile", (244, 222, 150), "cube_smile"),
               "wrong": _cube(E.X.col, "smile", (255, 40, 255), "cube_wrong")}
    E.edges = []
    for nm in ("steve", "noob"):
        for k, (dx, dy, dz, p, c, az) in enumerate(((-1.6, 2.6, 2.3, 700, (0.72, 0.92, 1.0), 1.55),
                                                    (1.2, 2.4, 3.4, 550, (1.0, 0.8, 0.55), 1.8))):
            E.edges.append((nm, char_light(sc, f"{nm}_edge{k}", (0, 0, 0), p, c), Vector((dx, dy, dz)), az))
    E.key = char_light(sc, "char_key", (0, -3, 3), 650, (1.0, 0.88, 0.76), cone=38, size=0.9)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.dof.use_dof = True
    cam.data.sensor_width = 36
    E.cam = cam
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
    E.mouth = _lipsync(tl, voice_path)
    E.lines = tl["lines"]
    E.lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    _solve_reach(E)
    E.C = Choreo(E)
    return E


REACH = (-74, 6, -26)                      # his left arm (screen-left, Steve's side) stretched at the ledge


def _solve_reach(E):
    """Where Null must float so that his reaching claw stops at Steve's fingers."""
    X = E.X
    k = NULL_H / 10.0
    X.root.scale = (k, k, k)
    X.root.location = (0, 0, 0)
    X.root.rotation_euler = (0, 0, 0)
    X.arms["sl"].rotation_euler = tuple(math.radians(a) for a in REACH)
    bpy.context.view_layer.update()
    fore = next(o for o in X.col.objects if o.name.endswith("_fore_sl"))
    n = len(fore.data.vertices)
    co = np.empty(n * 3, np.float32)
    fore.data.vertices.foreach_get("co", co)
    co = np.c_[co.reshape(-1, 3), np.ones(n, np.float32)] @ np.array(fore.matrix_world).T
    tips = co[co[:, 1] < np.percentile(co[:, 1], 1.5)][:, :3].mean(0)
    E.null_ledge = Vector((S_X - 0.05, 0.42, 0.3)) - Vector(tips.tolist())
    X.arms["sl"].rotation_euler = (0, 0, 0)


# --------------------------------------------------------------- choreography
class Choreo:
    def __init__(self, E):
        self.E = E
        T = E.T
        names = ["open", "noob_hi", "crawl", "react", "reveal", "null_hi", "unfold", "ff", "hang", "patch_412", "steve_trap",
                 "patch_bodies", "noob_smile", "steve_new", "noob_guys", "noob_sorry", "null_im", "glitch", "cube",
                 "steve_noob", "catch", "noob_tool", "steve_roblox", "sink", "noob_real", "cube_look", "silence",
                 "null_survive", "end"]
        self.t = {n: T(n) for n in names}
        self.e = {n: T(n + ".end") for n in names}
        t = self.t
        t["bird"] = t["glitch"] + 0.7                           # the silence breaks inside the glitch beat
        self.t_chase, self.t_bridge, self.t_grab = t["ff"], t["ff"] + 1.0, t["ff"] + 1.95
        self.t_island = t["sink"] + 0.8
        self.t_slip = t["steve_noob"] - 0.12
        self.t_caught = t["catch"] + 0.18
        self.t_took = t["cube"] + 0.95                         # the cube lands in the Noob's hand
        self.end = E.tl["length"] + 0.5
        sh = [
            (0.0, t["crawl"], self.cam_fingers), (t["crawl"], t["react"], self.cam_arms), (t["react"], t["reveal"], self.cam_react),
            (t["reveal"], t["unfold"], self.cam_reveal), (t["unfold"], t["ff"], self.cam_unfold),
            (self.t_chase, self.t_bridge, self.cam_chase), (self.t_bridge, self.t_grab, self.cam_bridge),
            (self.t_grab, t["hang"], self.cam_grab),
            (t["hang"], t["steve_trap"], self.cam_hang_wide), (t["steve_trap"], t["patch_bodies"], self.cam_face("steve", (0.5, -2.0, 0.1), 46)),
            (t["patch_bodies"], t["noob_smile"], self.cam_cells), (t["noob_smile"], t["steve_new"], self.cam_face("noob", (-0.45, -1.9, 0.05), 46)),
            (t["steve_new"], t["noob_guys"], self.cam_two), (t["noob_guys"], t["null_im"], self.cam_face("noob", (-0.9, -1.9, -0.35), 42)),
            (t["null_im"], t["bird"], self.cam_null_head), (t["bird"], t["cube"], self.cam_fingers_stop),
            (t["cube"], t["noob_tool"], self.cam_catch), (t["noob_tool"], t["steve_roblox"], self.cam_face("noob", (-0.35, -2.0, 0.5), 44)),
            (t["steve_roblox"], t["sink"], self.cam_face("steve", (0.55, -1.9, -0.25), 46)),
            (t["sink"], self.t_island, self.cam_sink), (self.t_island, t["cube_look"], self.cam_island),
            (t["cube_look"], t["silence"], self.cam_cube), (t["silence"], self.end + 1, self.cam_last),
        ]
        self.shots = sh

    # ---- which place we are in
    def place(self, t):
        if t < self.t_bridge:
            return "forest"
        return "ledge" if t < self.t_island else "island"

    def line_at(self, t):
        for ln in self.E.lines:
            if ln["start"] <= t < ln["end"]:
                return ln["name"]
        return None

    # ---- the characters: (location, yaw) and how far the Noob has dropped
    def run_y(self, t):
        if t < self.t_bridge:
            return -2.5 - 7.0 * (t - self.t_chase)                      # the chase, fast-forwarded
        u = (t - self.t_bridge) / (self.t_grab - self.t_bridge)
        return lerp(13.0, 1.6, u)                                       # the bridge

    def drop(self, t):
        return DROP * ss(self.t_slip, self.t_caught, t) ** 0.7 if t >= self.t_slip else 0.0

    def chars(self, t):
        """-> steve (loc, yaw), noob (loc, yaw), mode"""
        tt = self.t
        if t < tt["ff"]:                                                # facing the portal; they turn to run as he unfolds
            turn = ss(tt["unfold"] + 0.1, tt["unfold"] + 0.5, t)
            return (Vector((-S_X, -2.6, 0)), lerp(176, 20, turn)), (Vector((-N_X, -2.3, 0)), lerp(184, 340, turn)), "stand"
        if t < self.t_grab:
            y = self.run_y(t)
            return (Vector((S_X - 0.2, y, 0)), 0), (Vector((N_X + 0.2, y + 0.2, 0)), 0), "run"
        if t < tt["hang"]:                                              # the jump onto the ledge
            u = ss(self.t_grab, tt["hang"] - 0.12, t)
            y = lerp(1.6, 0.3, u)
            arc = 0.55 * math.sin(math.pi * u)
            return (Vector((S_X, y, lerp(0.0, S_HANG, u) + arc)), 0), (Vector((N_X, y + 0.02, lerp(0.0, N_HANG, u) + arc)), 0), "jump"
        if t < self.t_island:
            d = self.drop(t)
            pull = ss(tt["sink"] + 0.25, self.t_island, t) * 0.5
            return (Vector((S_X, 0.3, S_HANG + pull)), 0), (Vector((N_X - 0.1 * d / DROP, 0.3, N_HANG - d + pull)), 0), "hang"
        return (Vector((S_X - 0.2, 0.3, 0)), 0), (Vector((N_X + 0.15, 0.1, 0)), 0), "island"

    def head(self, who, t):
        (sl, _), (nl, _), _ = self.chars(t)
        return (sl + Vector((0, 0, 1.68))) if who == "steve" else (nl + Vector((0, 0, 1.77)))

    def patch_pos(self, t):
        bob = 0.05 * math.sin(2 * math.pi * 0.7 * t)
        p = self.place(t)
        if p == "forest":
            if t >= self.t_chase:
                return Vector((0.1, self.run_y(t) + 0.3, 2.1 + bob))
            return Vector((0.0, -1.9, 2.25 + bob))
        if p == "ledge":
            if t < self.t["hang"]:
                return Vector((0.0, self.run_y(min(t, self.t_grab)) + 0.3, 1.9 + bob))
            return Vector((1.75, 0.15, -0.35 + bob))
        return Vector((0.2, 0.9, 2.2 + bob))

    # ---- Null: where, how big, what he does
    def null(self, t):
        """-> dict(H, loc, yaw, lights, smile, awake, reach, jitter, show)"""
        tt, E = self.t, self.E
        d = {"H": NULL_H, "yaw": 0.0, "lights": 1.0, "smile": 1.0, "awake": 0.0, "reach": 0.0, "jitter": 0.0, "show": True,
             "arms": 0.0}
        if t < tt["reveal"]:                                            # only his hands are through
            d.update(show=False, loc=PORTAL_AT + Vector((0, 30, -60)), lights=0.0)
        elif t < tt["unfold"]:                                          # the head rises, the face turns to us last
            u = ss(tt["reveal"], tt["null_hi"] + 0.1, t)
            d.update(H=7.5, loc=PORTAL_AT + Vector((1.2, -3.4, lerp(-7.6, -3.1, u ** 0.7))),
                     yaw=lerp(-118, -40, ss(tt["reveal"] + 0.35, tt["null_hi"] + 0.25, t)), lights=0.55,
                     smile=self.flicker(t, tt["null_hi"] - 0.12), arms=18)
        elif t < tt["ff"]:                                              # too big for the frame he came through
            u = ss(tt["unfold"], tt["ff"] - 0.1, t)
            d.update(H=lerp(7.5, NULL_H, u), loc=PORTAL_AT + Vector((lerp(1.2, 0.0, u), lerp(-3.4, 1.0, u), lerp(-3.1, 1.5, u))),
                     yaw=lerp(-40, 0, u), lights=lerp(0.55, 1.0, u), arms=lerp(18, 0, u))
        elif t < self.t_bridge:                                         # the chase
            d.update(loc=Vector((-2.0, 34.0 - 2.2 * (t - self.t_chase) * 2, self.E.null_ground + 2.0)), reach=0.35)
        elif t < tt["hang"]:
            d.update(loc=Vector((0.0, 60.0, -6.0)), lights=1.0)
        else:                                                           # out of the void, at the ledge
            base = Vector(E.null_ledge)
            rise = ss(tt["hang"] - 0.2, tt["patch_412"] + 2.6, t) ** 0.8
            z = lerp(-34.0, 0.0, rise)
            sink = ss(tt["sink"], tt["sink"] + 1.3, t)
            z -= 44.0 * sink ** 1.6
            d.update(loc=base + Vector((0, 0, z)),
                     awake=ss(tt["patch_bodies"] - 0.1, tt["patch_bodies"] + 1.7, t),
                     reach=ss(tt["noob_smile"] + 0.4, self.e["noob_sorry"], t) ** 0.9)
            if t >= tt["null_im"]:                                      # nothing to copy: he breaks
                g = 1 - ss(self.e["null_im"] + 0.5, tt["bird"] + 0.3, t)
                d["jitter"] = g
                d["smile"] = self.flicker(t, tt["null_im"] + 0.05, 2.4) if t < tt["bird"] else 1.0
                d["awake"] = 1 - 0.85 * ss(tt["null_im"], tt["null_im"] + 0.5, t)
                d["reach"] = 1.0 - 0.35 * ss(tt["cube"] + 0.2, tt["steve_noob"], t)
            if t >= tt["sink"]:
                d["lights"] = 1 - sink
        return d

    @staticmethod
    def flicker(t, t0, dur=0.34):
        """Off, then on in a stutter."""
        u = t - t0
        if u < 0:
            return 0.0
        if u > dur:
            return 1.0
        return 1.0 if int(u / 0.055) % 2 == 0 else 0.0

    # ---- the cube
    def cube(self, t):
        """-> (which, location, spin) or None"""
        tt = self.t
        if t < tt["cube"]:
            return None
        (_, _), (nl, _), mode = self.chars(t)
        hand = nl + Vector((0.5, -0.42, 1.18))                          # held against his chest
        if mode == "island":
            hand = nl + Vector((0.0, -0.5, 1.2))
        if t < self.t_took:
            u = ss(tt["cube"], self.t_took, t)
            src = Vector(self.E.null_ledge) + Vector((1.5, -9.0, 10.0))
            p = src.lerp(nl + Vector((0.95, -0.25, 1.75)), u ** 0.8) + Vector((0, 0, 0.5 * math.sin(math.pi * u)))
            return "scared", p, 2.5 * u
        if t < tt["noob_tool"]:
            u = ss(self.t_took, self.t_took + 0.3, t)
            return "scared", (nl + Vector((0.95, -0.25, 1.75))).lerp(hand, u), 0.0
        if t < tt["cube_look"] + 0.15:
            return ("scared" if t < self.t_island else "smile"), hand, 0.0
        u = t - (tt["cube_look"] + 0.62)
        return ("wrong" if 0 <= u < 0.09 or 0.16 <= u < 0.2 else "smile"), hand, 0.0

    # ---- cameras: -> (loc, look, lens, fstop, shake, focus point or None)
    def cam_fingers(self, t, u):
        loc = PORTAL_AT + Vector((-3.5, -2.0, 1.9)) + Vector((0.25 * u, 0.1 * u, 0))
        return loc, PORTAL_AT + Vector((0.0, -0.5, 2.35)), 42, 2.8, 0.0, None

    def cam_arms(self, t, u):
        """Low, against the sky: both arms out of the portal (the reference's hand shot)."""
        loc = PORTAL_AT + Vector((2.3, -2.9, 0.3)) + Vector((-0.2 * u, 0.15 * u, 0))
        return loc, PORTAL_AT + Vector((-0.1, -0.5, 2.5)), 28, 2.8, 0.004, None

    def cam_react(self, t, u):
        loc = Vector((0.25, 1.35 - 0.2 * u, 1.45))
        return loc, Vector((0.0, -2.45, 1.42)), 40, 2.8, 0.0, None

    def cam_reveal(self, t, u):
        n = self.null(self.t["null_hi"] + 0.5)
        head = n["loc"] + Vector((0, -0.35 * 0.75, (9.25 + 1.9) * 0.75))
        loc = head + Vector((-9.0, -4.6, -2.2)) + Vector((0.5 * u, 0.25 * u, 0))
        return loc, head + Vector((0.2, 0.6, -0.9)), 32, 4.0, 0.003 + 0.01 * ss(0.5, 0.7, u), None

    def cam_unfold(self, t, u):
        loc = Vector((2.4, -7.5, 0.7)) + Vector((0, -1.5 * u, 0.1 * u))
        look = Vector((0.2, 5.0, 4.5)).lerp(Vector((0.0, 6.0, 11.0)), ss(0, 1, u))
        return loc, look, 22, 4.0, 0.012 + 0.012 * u, Vector((0, 4, 5))

    def cam_chase(self, t, u):
        y = self.run_y(t)
        return Vector((0.05, y - 4.3, 0.95)), Vector((0.0, y + 10.0, 4.4)), 21, 4.0, 0.016, Vector((0, y, 1.4))

    def cam_bridge(self, t, u):
        y = self.run_y(t)
        return Vector((2.3, y - 4.6, 1.5)), Vector((0.0, y + 3.0, 1.6)), 22, 4.0, 0.014, Vector((0, y, 1.4))

    def cam_grab(self, t, u):
        """On the ledge, at the lip: two hands slap onto the edge."""
        return Vector((1.5, -2.3, 0.75)), Vector((0.0, 0.2, -0.15)), 34, 2.8, 0.02 * ss(0.6, 0.8, u), None

    def cam_hang_wide(self, t, u):
        loc = Vector((0.5, -5.8, -1.15)) + Vector((0.0, 0.5 * u, 0.0))
        return loc, Vector((0.1, 0.4, -0.5)).lerp(Vector((0.1, 0.4, 0.9)), ss(0, 1, u)), 23, 4.0, 0.004, Vector((0, 0.3, -1))

    def cam_face(self, who, off, lens):
        def f(t, u):
            h = self.head(who, t)
            loc = h + Vector(off) + Vector((0.0, 0.1 * u, 0))
            return loc, h + Vector((0, 0, -0.12)), lens, 1.4, 0.0, None
        return f

    def cam_cells(self, t, u):
        """Into him: the cells light up."""
        base = Vector(self.E.null_ledge)
        k = NULL_H / 10.0
        a = base + Vector((1.2, -9.5, 6.4)) * k
        b = base + Vector((0.9, -3.3, 6.75)) * k
        loc = a.lerp(b, ss(0, 1, u) ** 0.85)
        look = base + Vector((0.5, 0, 6.5)) * k
        return loc, look, 34, 4.0, 0.0, base + Vector((0.6, -1.2, 6.5)) * k

    def cam_two(self, t, u):
        loc = Vector((0.15, -3.6, -0.95)) + Vector((0, 0.3 * u, 0))
        return loc, Vector((0.0, 0.3, -0.5)), 30, 2.8, 0.0, None

    def cam_null_head(self, t, u):
        n = self.null(t)
        k = NULL_H / 10.0
        head = n["loc"] + Vector((0, -0.35, 9.25 + 1.9)) * k
        loc = head + Vector((-2.5, -15.0, -6.0))
        return loc, head + Vector((0, 0, -0.6)), 34, 4.0, 0.02 * n["jitter"], None

    def cam_fingers_stop(self, t, u):
        """The claw, stopped a pixel from Steve's fingers. A bird sings."""
        return Vector((-2.2, -1.5, 0.55)) + Vector((0.1 * u, 0, 0)), Vector((S_X + 0.1, 0.35, 0.12)), 50, 2.8, 0.0, None

    def cam_catch(self, t, u):
        d = self.drop(t)
        loc = Vector((0.35, -4.3, -1.1 - 0.3 * d))
        return loc, Vector((0.05, 0.3, -0.75 - 0.5 * d)), 30, 2.8, 0.03 * ss(self.t_slip, self.t_slip + 0.1, t) * (1 - ss(self.t_caught, self.t_caught + 0.4, t)), None

    def cam_sink(self, t, u):
        loc = Vector((1.2, -6.5, 1.6)) + Vector((0, 0, 0.6 * u))
        return loc, Vector((0.0, 3.0, -3.0)), 22, 4.0, 0.006, Vector((0, 0.3, -1))

    def cam_island(self, t, u):
        loc = Vector((0.3, -6.4, 1.25)) + Vector((0.0, 0.5 * u, 0))
        return loc, Vector((0.0, 0.3, 1.35)), 28, 2.8, 0.0, None

    def cam_cube(self, t, u):
        c = self.cube(t)[1]
        loc = c + Vector((0.25, -1.25, 0.28)) + Vector((0, 0.08 * u, 0))
        return loc, c + Vector((0, 0, 0.16)), 50, 1.8, 0.0, c

    def cam_last(self, t, u):
        """Up and away: the island, alone, and something rising under it."""
        k = ss(0, 1, min(1.0, (t - self.t["silence"]) / 3.2))
        loc = Vector((0.6, -7.0, 2.2)).lerp(Vector((1.5, -12.5, 9.5)), k)
        return loc, Vector((0.0, 0.4, 1.0)).lerp(Vector((0, 0.5, -1.5)), k), lerp(28, 24, k), 4.0, 0.0, Vector((0, 0, 1))

    def camera(self, t):
        for a, b, f in self.shots:
            if a <= t < b:
                return f(t, (t - a) / max(1e-6, b - a))
        a, b, f = self.shots[-1]
        return f(t, 1.0)

    # ---- the sky and the grade
    def look(self, t):
        tt = self.t
        if t < tt["unfold"]:
            sky, tag = DUSK, "dusk"
        elif t < self.t_bridge:
            sky, tag = mixlook(DUSK, STORM, ss(tt["unfold"], tt["ff"], t)), "storm"
        elif t < tt["bird"]:
            sky, tag = VOID, "void"
        elif t < self.t_island:
            sky, tag = mixlook(VOID, CLEAR, 0.35 * ss(tt["bird"], tt["cube"], t)), "void"
        else:
            sky, tag = CLEAR, "clear"
        return sky, tag


# ------------------------------------------------------------ apply a frame
def _faces(E, t, f_render, sf, nf, pf):
    from faceplate import EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH, set_face
    from brows import set_brows
    from patch import DEFAULTS as PD, set_patch

    def blink(t, phase):
        u = (t + phase) % 3.7
        return 0.0 if u < 0.09 else (0.5 if u < 0.14 else 1.0)
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
    set_face(E.S.face, fs)
    for ob_ in E.S.brows.values():
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(E.S.brows, {k: v for k, v in sf.items() if k.startswith("bb_")})
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
    set_face(E.N.face, fn)
    p = dict(PD)
    p.update(pf)
    p["open"] = p.get("open", 1.0) * blink(t, 2.4)
    set_patch(E.Pt, p)


def _hands(E, spec):
    """spec: [(index, scale, wrist (world), tilt, roll, yaw)]"""
    from portal import drape
    used = []
    for i, k, at, tilt, roll, yaw in spec:
        h = E.hands[i]
        h.scale = (k, k, k)
        h.location = at
        h.rotation_quaternion = (Quaternion((0, 0, 1), math.radians(yaw)) @ Quaternion((1, 0, 0), math.radians(tilt))
                                 @ Quaternion((0, 0, 1), math.radians(roll)))
        used.append(h)
    for h in E.hands:
        for o in [h] + list(h.children):
            o.hide_render = h not in used
    return used


def apply(E, t):
    from pose import pose
    from noob import pose_noob, NOOB_POSES
    from world import fx_set, set_sky, set_sun
    from stage import place_null_lights
    from null import cells_look, null_smile
    from portal import drape
    C = E.C
    tt = C.t
    f_render = int(round(t * FPS))
    place = C.place(t)
    # ------------------------------------------------ what exists
    forest = place == "forest"
    for o in E.world_objs:
        o.hide_render = not forest
    ledge_on = place == "ledge"
    E.ledge.hide_render = not ledge_on
    front = C.run_y(t) + 2.2 if t < C.t_grab else -1.0                  # planks blink out behind them
    for pl in E.planks:
        pl.hide_render = not ledge_on or pl["y"] > front or t >= tt["hang"] - 0.2
    for o in E.island:
        o.hide_render = place != "island"
    # the void's eye, far below
    E.eye.hide_render = forest
    lid = 1 - ss(tt["sink"] + 0.2, tt["sink"] + 1.25, t)
    rise = ss(tt["silence"], C.end, t)
    E.eye.location = (0, 6, -70 + 30 * rise)
    E.eye.scale = (95, max(0.02, 95 * lid) if t < C.t_island else 26 * (0.15 + rise), 1)
    if t >= C.t_island:
        E.eye.scale = (26 * (0.15 + rise), 26 * (0.15 + rise), 1)
    E.eye_power.default_value = 2.2 if t < C.t_island else 5.0 * rise
    # ------------------------------------------------ the world's own effects (the chase erases it)
    D, Dz = 0.0, -1.0
    n = C.null(t)
    if forest and t >= C.t_chase:
        D = min(6.0 + 26.0 * (t - C.t_chase), n["loc"].y - C.run_y(t) - 9.0)
        Dz = 1.0
    if forest:
        fx_set(E.W, R=1e5, Wd=100.0, Cx=0.0, Cy=0.0, D=D, Nx=n["loc"].x, Ny=n["loc"].y, Dz=Dz)
    sky, tag = C.look(t)
    set_sky(E.W, sky)
    if tag == "dusk":
        set_sun(E.W, 71, 12, 7.0, (1.0, 0.72, 0.44))
    elif tag == "storm":
        set_sun(E.W, 71, 20, 3.0, (0.9, 0.78, 1.0))
    elif tag == "void":
        set_sun(E.W, 150, 38, 3.4, (0.95, 0.82, 1.0))
    else:
        set_sun(E.W, 140, 30, 5.6, (1.0, 0.88, 0.76))
    E.W.sky_pow.inputs[1].default_value = sky["power"]
    E.W.clouds.hide_render = not forest or tag == "storm"
    # ------------------------------------------------ the portal and his hands
    P0 = E.P0
    portal_on = t < tt["ff"]
    burst = ss(tt["unfold"] + 0.25, tt["unfold"] + 1.1, t)
    rnd = random.Random(2)
    for b in P0.blocks:
        b.hide_render = not portal_on
        home = Vector(b["home"])
        d = Vector((home.x * 1.6 + rnd.uniform(-1, 1), -rnd.uniform(1.5, 5.0), (home.z - 2.5) * 1.3 + rnd.uniform(1.0, 4.0)))
        b.location = home + d * burst ** 0.7 * 2.2 + Vector((0, 0, -4.0 * burst * burst))
        b.rotation_euler = (burst * rnd.uniform(-4, 4), burst * rnd.uniform(-4, 4), burst * rnd.uniform(-4, 4))
    P0.membrane.hide_render = not portal_on or burst > 0.05
    P0.light.hide_render = not portal_on or burst > 0.6
    flow = P0.membrane.data.materials[0]
    flow.node_tree.nodes[flow["flow"]].inputs[1].default_value = (0.05 * t, 0.11 * t, 0.0)
    spec = []
    if t < tt["react"]:
        jerk = 0.05 * math.sin(31 * t) * (1 if int(t * 9) % 3 else 0)
        out1 = ss(-0.4, tt["noob_hi"] + 0.5, t)                         # already through at frame 1, still coming
        spec.append((0, 0.46, PORTAL_AT + Vector((0.0, lerp(0.75, 0.22, out1) + jerk, 2.7)), -66 + 6 * math.sin(7 * t), 78, 0))
        if t >= tt["crawl"]:
            u = ss(tt["crawl"], tt["crawl"] + 0.5, t)
            u2 = ss(tt["crawl"] + 0.6, tt["react"], t)
            spec[0] = (0, 0.5, PORTAL_AT + Vector((0.35, lerp(0.22, -0.25, u2) + jerk, 2.75)), lerp(-66, -52, u2), lerp(78, 20, u2), -6)
            spec.append((1, 0.5, PORTAL_AT + Vector((-0.45, lerp(1.6, 0.05, u) - 0.3 * u2 + jerk, 1.75)), lerp(-80, -58, u2), -15, 8))
    used = _hands(E, spec)
    # ------------------------------------------------ Null
    X = E.X
    k = n["H"] / 10.0
    jit = Vector((0, 0, 0))
    if n["jitter"]:
        r2 = random.Random(int(t * 24))
        jit = Vector((r2.uniform(-1, 1), 0, r2.uniform(-0.4, 0.4))) * 0.5 * n["jitter"] * (1 if r2.random() < 0.6 else 0)
    X.root.scale = (k, k, k)
    X.root.location = n["loc"] + jit
    X.root.rotation_euler = (0, 0, math.radians(n["yaw"]))
    orbit_on = n["show"] and t >= tt["unfold"] + 0.5
    for o in X.col.objects:
        if o.name.startswith(("null_hand", "cube_")):
            continue
        is_orbit = "_orbit" in o.name or "_trail_" in o.name
        o.hide_render = not n["show"] or (is_orbit and not orbit_on)
    X.glow.hide_render = not n["show"] or t < tt["unfold"] or place == "island"
    if getattr(X, "orbit", None):
        X.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0.9 * t)
        X.orbit2.rotation_euler = (math.radians(-12), math.radians(14), -0.6 * t)
    r = n["reach"]
    X.arms["sl"].rotation_euler = tuple(math.radians(a * r) for a in REACH) if not n["arms"] else (math.radians(-n["arms"]), 0, 0)
    X.arms["sr"].rotation_euler = (math.radians(-n["arms"] - 20 * r), math.radians(-8 * r), 0)
    place_null_lights(X, fade=n["lights"] if n["show"] else 0.0)
    null_smile(n["smile"])
    cells_look(near=0.9 * n["H"], far=2.4 * n["H"], awake=n["awake"], power=1.0 + 0.6 * n["awake"])
    bpy.context.view_layer.update()
    if portal_on and burst < 0.05:
        drape(P0, [c for h in used for c in h.children])
    # ------------------------------------------------ the cube
    cb = C.cube(t)
    for nm, ob in E.cubes.items():
        ob.hide_render = not (cb and cb[0] == nm)
        if cb and cb[0] == nm:
            ob.location = cb[1]
            ob.rotation_euler = (0.4 * cb[2], 0.3 * cb[2], cb[2])
    # ------------------------------------------------ bodies
    (sl, syaw), (nl, nyaw), mode = C.chars(t)
    S, N, Pt = E.S, E.N, E.Pt
    idle = flat(E.lib["idle (Benly 2.2)"])
    breathe = math.sin(2 * math.pi * 0.25 * t)
    act = C.act(t)
    if mode == "run":
        ph = 2 * math.pi * 3.6 * t
        sw = math.sin(ph)
        sp = {"chest_lean": 16, "chest_twist": 10 * sw, "head_nod": -12, "hips_drop": 0.16 + 0.05 * abs(math.cos(ph)),
              "arm_sl": {"fwd": -55 * sw, "elbow": 85, "out": 8}, "arm_sr": {"fwd": 55 * sw, "elbow": 85, "out": 8},
              "foot_sl": {"y": -0.5 * sw, "z": max(0.0, 0.45 * math.sin(ph + 1.2))},
              "foot_sr": {"y": 0.5 * sw, "z": max(0.0, 0.45 * math.sin(ph + 1.2 + math.pi))}}
        sw2 = math.sin(ph + 0.8)
        npz = {"chest_lean": 10, "arm_sl": {"fwd": -60 * sw2, "out": 12}, "arm_sr": {"fwd": 60 * sw2, "out": 12},
               "leg_sl": {"fwd": 45 * sw2}, "leg_sr": {"fwd": -45 * sw2}}
        sl = sl + Vector((0, 0, 0.06 * abs(math.sin(ph))))
        nl = nl + Vector((0, 0, 0.07 * abs(math.sin(ph + 0.8))))
    else:
        sp = dict(idle)
        npz = flat(NOOB_POSES["idle"])
        if mode in ("jump", "hang"):
            sway = math.sin(2 * math.pi * 0.45 * t)
            up = ss(C.t_grab, tt["hang"] - 0.15, t) if mode == "jump" else 1.0
            sp.update(flat({"arm_sl": {"fwd": 155 * up, "out": 4, "elbow": 4}, "arm_sr": {"fwd": 155 * up, "out": 4, "elbow": 4},
                            "head_nod": -6, "chest_lean": 2 + 1.5 * sway,
                            "foot_sl": {"y": 0.06 * sway, "z": 0.0}, "foot_sr": {"y": -0.05 * sway, "z": 0.03}}))
            npz.update(flat({"arm_sl": {"fwd": 155 * up, "out": 3}, "arm_sr": {"fwd": 155 * up, "out": 3},
                             "leg_sl": {"fwd": 6 * sway, "out": 3}, "leg_sr": {"fwd": -7 * sway, "out": 3}, "head_nod": -4}))
        sp["chest_lean"] = sp.get("chest_lean", 0) + 1.2 * breathe
        npz["head_tilt"] = npz.get("head_tilt", 0) + 2 * breathe
        sp.update(flat(act["steve"]))
        npz.update(flat(act["noob"]))
        sp, npz = unflat(sp), unflat(npz)
    pose(S.arm, sp)
    S.holder.location = sl
    S.holder.rotation_euler = (0, 0, math.radians(syaw))
    pose_noob(N, {**npz, "root_yaw": nyaw + npz.get("root_yaw", 0)})
    N.root.location = nl
    pp = C.patch_pos(t)
    Pt.root.location = pp
    Pt.root.rotation_euler = (0, 0, math.radians(act["patch_yaw"]))
    for side, pv in Pt.fins.items():
        pv.rotation_euler = (0, 0, 0)
    for o in Pt.col.objects:
        if o.name.endswith("_beam"):
            o.hide_render = True
    _faces(E, t, f_render, act["sf"], act["nf"], act["pf"])
    # ------------------------------------------------ lights and the camera
    loc, lookat, lens, fstop, shake, focus = C.camera(t)
    if shake:
        loc = loc + Vector((shake * math.sin(t * 37.0), 0, shake * math.cos(t * 29.0)))
    cam = E.cam
    cam.location = loc
    cam.rotation_euler = (lookat - loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.focus_distance = max(0.2, ((focus if focus is not None else lookat) - loc).length)
    cam.data.dof.aperture_fstop = fstop
    back = syaw > 90                                                   # they face +y in the forest: light from that side
    for nm, ob, off, az in E.edges:
        at = Vector(S.holder.location) if nm == "steve" else Vector(N.root.location)
        o2 = Vector((off.x, -off.y if back else off.y, off.z))
        ob.location = at + o2
        ob.rotation_euler = (at + Vector((0, 0, az)) - ob.location).to_track_quat("-Z", "Y").to_euler()
        ob.data.energy = (700 if ob.name.endswith("0") else 550) * (0.0 if mode == "run" and place == "ledge" and False else 1.0)
    key = E.key
    d = (lookat - loc).normalized()
    right = d.cross(Vector((0, 0, 1))).normalized()
    key.location = loc + right * 1.6 + Vector((0, 0, 1.4))
    mid = (Vector(S.holder.location) + Vector(N.root.location)) / 2 + Vector((0, 0, 1.5))
    key.rotation_euler = (mid - key.location).to_track_quat("-Z", "Y").to_euler()
    key.data.energy = 650 if (mid - loc).length < 9 else 0
    key.data.color = (1.0, 0.88, 0.76) if tag in ("dusk", "clear") else (0.9, 0.86, 1.0)
    return {"tag": tag, "place": place}


# ------------------------------------------------------------- acting
def _acting(C):
    """Who does what, line by line."""
    from faceplate import EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from patch import DEFAULTS as PD
    tt, e = C.t, C.e

    def base(eyes, mouth):
        def b(k):
            if k.startswith(("both_", "eR_", "eL_")):
                return eyes.get(k.split("_", 1)[1], 0.0)
            return mouth.get(k, 0.0)
        return b
    hangS = {"arm_sl.fwd": 155, "arm_sr.fwd": 155, "arm_sl.out": 4, "arm_sr.out": 4, "arm_sl.elbow": 4, "arm_sr.elbow": 4}
    hangN = {"arm_sl.fwd": 155, "arm_sr.fwd": 155, "arm_sl.out": 3, "arm_sr.out": 3}
    from noob import NOOB_POSES
    idle_s, idle_n = flat(C.E.lib["idle (Benly 2.2)"]), flat(NOOB_POSES["idle"])
    # Steve's body, on top of the mode's pose (only the keys named here)
    C.kS = Keys([
        (0.0, {"chest_lean": -5, "head_nod": -5, "head_turn": 6, "arm_sl": {"out": 16, "fwd": 10, "elbow": 30}, "arm_sr": {"out": 16, "fwd": 10, "elbow": 30}}, 0.1),
        (tt["null_hi"], {"chest_lean": -9, "head_nod": -16, "head_turn": 4, "arm_sl": {"out": 24, "fwd": 20, "elbow": 45}, "arm_sr": {"out": 24, "fwd": 20, "elbow": 45}}, 0.3),
        (tt["hang"], {"head_nod": -4, "head_turn": 0}, 0.05),
        (tt["hang"] + 0.5, {"head_turn": 34, "head_nod": 14}, 0.4),                     # down, over his shoulder: the void
        (tt["patch_412"] + 0.8, {"head_turn": -24, "head_nod": -4}, 0.4),               # at Patch
        (tt["steve_trap"], {"head_turn": 0, "head_nod": 12}, 0.4),
        (tt["noob_smile"], {"head_turn": -26, "head_nod": 0}, 0.4),
        (tt["steve_new"], {"head_turn": -30, "head_nod": -6}, 0.2),
        (tt["noob_guys"], {"head_turn": -22, "head_nod": -4}, 0.4),
        (tt["null_im"], {"head_turn": 30, "head_nod": -20}, 0.3),
        (tt["cube"], {"head_turn": -20, "head_nod": -10}, 0.4),
        (C.t_slip, {"head_turn": -34, "head_nod": 20, "chest_twist": -14, "chest_side": -10,
                    "arm_sr": {"fwd": 4, "out": 34, "elbow": 6}}, 0.16),               # no tool: his bare hand
        (tt["steve_roblox"], {"head_turn": -30, "head_nod": 24, "chest_twist": -14, "chest_side": -10,
                              "arm_sr": {"fwd": 4, "out": 34, "elbow": 6}}, 0.3),
        (C.t_island, {"head_turn": -14, "head_nod": 0, "chest_twist": 0, "chest_side": 0, "chest_lean": 6,
                      "arm_sl": {"fwd": 10, "out": 10, "elbow": 20}, "arm_sr": {"fwd": 10, "out": 10, "elbow": 20}}, 0.01),
        (tt["cube_look"], {"head_turn": -30, "head_nod": 10, "chest_lean": 2, "arm_sl": {"fwd": 0, "out": 8, "elbow": 10},
                           "arm_sr": {"fwd": 0, "out": 8, "elbow": 10}}, 0.4),
        (tt["null_survive"], {"head_turn": 0, "head_nod": 16}, 0.5),
    ], base=lambda k: idle_s.get(k, 0.0))
    C.kN = Keys([
        (0.0, {"head_nod": -6, "chest_lean": -4, "arm_sr": {"out": 70, "fwd": 20}}, 0.1),          # the wave, half raised
        (tt["crawl"] + 0.5, {"head_nod": -6, "chest_lean": -6, "arm_sr": {"out": 30, "fwd": 10}}, 0.6),
        (tt["null_hi"], {"head_nod": -18, "chest_lean": -8, "arm_sl": {"fwd": 40, "out": 8}, "arm_sr": {"fwd": 40, "out": 8}}, 0.3),
        (tt["hang"], {"head_nod": -4}, 0.05),
        (tt["hang"] + 0.6, {"head_turn": -30, "head_nod": 16}, 0.4),
        (tt["patch_412"] + 0.8, {"head_turn": -30, "head_nod": -4}, 0.4),
        (tt["patch_bodies"], {"head_turn": -34, "head_nod": -22}, 0.4),                   # up, over his shoulder, at him
        (tt["noob_smile"], {"head_turn": -20, "head_nod": -14}, 0.3),
        (tt["noob_smile"] + 1.0, {"head_turn": 0, "head_nod": 12}, 0.5),
        (tt["steve_new"], {"head_turn": 24, "head_nod": 0}, 0.3),
        (tt["noob_guys"], {"head_turn": -38, "head_nod": -26, "head_tilt": 6}, 0.4),               # to the cells
        (tt["null_im"], {"head_turn": -38, "head_nod": -26}, 0.2),
        (tt["cube"], {"head_turn": -24, "head_nod": -20}, 0.3),
        (tt["cube"] + 0.45, {"head_turn": -30, "head_nod": -18, "arm_sr": {"fwd": 60, "out": 70}}, 0.3),   # he lets go to catch it
        (C.t_took + 0.3, {"head_turn": -10, "head_nod": 8, "arm_sr": {"fwd": 55, "out": -14}}, 0.25),
        (C.t_slip + 0.05, {"head_turn": 20, "head_nod": -24, "arm_sr": {"fwd": 55, "out": -14}, "arm_sl": {"fwd": 168, "out": 22},
                           "leg_sl": {"fwd": 14, "out": 8}, "leg_sr": {"fwd": -10, "out": 10}}, 0.12),
        (tt["steve_roblox"], {"head_turn": 24, "head_nod": -26, "arm_sr": {"fwd": 55, "out": -14}, "arm_sl": {"fwd": 168, "out": 22}}, 0.3),
        (C.t_island, {"head_turn": 0, "head_nod": -10, "chest_lean": -6, "arm_sl": {"fwd": 0, "out": 160}, "arm_sr": {"fwd": 0, "out": 160},
                      "leg_sl": {"out": 8}, "leg_sr": {"out": 8}}, 0.01),                          # fists up
        (tt["cube_look"], {"head_turn": 0, "head_nod": 20, "chest_lean": 4, "arm_sl": {"fwd": 62, "out": -18}, "arm_sr": {"fwd": 62, "out": -18},
                           "leg_sl": {"out": 4}, "leg_sr": {"out": 4}}, 0.35),
        (tt["null_survive"] + 0.4, {"head_nod": 6}, 0.4),
    ], base=lambda k: idle_n.get(k, 0.0))
    C.fS = Keys([
        (0.0, SF["stunned"], 0.1), (tt["null_hi"], SF["scared"], 0.3), (tt["ff"], SF["scared"], 0.1),
        (tt["hang"] + 0.4, SF["worried"], 0.4), (tt["steve_trap"], dict(SF["worried"], both_to=-0.45, m_arch=0.22), 0.4),
        (tt["noob_smile"], SF["worried"], 0.4), (tt["steve_new"], dict(SF["worried"], bb_tilt=0.5, bb_raise=-0.1), 0.2),
        (tt["null_im"], SF["stunned"], 0.3), (tt["cube"], SF["worried"], 0.4), (C.t_slip, SF["scared"], 0.12),
        (tt["noob_tool"], SF["flat"], 0.5), (tt["steve_roblox"], SF["flat"], 0.2), (C.t_island, SF["smile"], 0.01),
        (tt["cube_look"], SF["smile"], 0.3), (tt["null_survive"], SF["stunned"], 0.25),
    ], base=base(EYE_DEFAULTS, MOUTH_DEFAULTS))
    C.fN = Keys([
        (0.0, NF["worried"], 0.1), (tt["null_hi"], NF["scared"], 0.25), (tt["ff"], NF["shout"], 0.1),
        (tt["hang"] + 0.3, NF["scared"], 0.3), (tt["patch_412"] + 0.6, NF["worried"], 0.5), (tt["patch_bodies"], NF["awe"], 0.5),
        (tt["noob_smile"], NF["teary"], 0.4), (tt["steve_new"], NF["worried"], 0.3), (tt["noob_guys"], NF["teary"], 0.4),
        (tt["null_im"], NF["awe"], 0.3), (tt["cube"] + 0.4, NF["happy"], 0.3), (C.t_slip, NF["shock"], 0.1),
        (tt["noob_tool"], NF["confused"], 0.4), (tt["steve_roblox"], NF["awe"], 0.4), (C.t_island, NF["shout"], 0.01),
        (tt["cube_look"], NF["happy"], 0.3), (tt["cube_look"] + 0.7, NF["confused"], 0.12), (tt["null_survive"], NF["worried"], 0.3),
    ], base=base(NOOB_EYE_DEFAULTS, {**MOUTH_DEFAULTS, **NOOB_MOUTH}))
    C.fP = Keys([
        (0.0, {"wide": 0.6, "look_y": 0.2}, 0.1), (tt["null_hi"], {"wide": 1.0, "look_y": 0.5}, 0.2),
        (tt["hang"], {"look_x": -0.5, "squint": 0.2}, 0.2), (tt["patch_412"], {"look_x": -0.6, "sad": 0.6}, 0.3),
        (tt["patch_bodies"], {"look_x": -0.3, "look_y": 0.4, "sad": 0.8}, 0.4), (tt["null_im"], {"wide": 1.0, "look_y": 0.4}, 0.2),
        (tt["cube"], {"look_x": -0.5, "wide": 0.5}, 0.3), (C.t_island, {"smile": 1.0}, 0.01), (tt["cube_look"] + 0.65, {"glitch": 1.0, "wide": 0.7}, 0.06),
        (tt["cube_look"] + 0.85, {"wide": 0.8, "look_y": -0.5}, 0.1),
    ], base=lambda k: PD.get(k, 0.0))

    def act(t):
        s, n_ = C.kS.at(t), C.kN.at(t)
        mode = C.chars(t)[2]
        if mode in ("jump", "hang"):                                    # hanging: the hands stay on the ledge unless a key moves them
            for k, v in hangS.items():
                if t < C.t_slip or not k.startswith("arm_sr"):
                    s[k] = v
            for k, v in hangN.items():
                if k.startswith("arm_sl") and t >= C.t_slip:
                    continue
                if k.startswith("arm_sr") and t >= tt["cube"] + 0.3:
                    continue
                n_[k] = v
        yaw = {"forest": 180.0, "ledge": 35.0, "island": 0.0}[C.place(t)] if t < C.t_chase or t >= tt["hang"] else 0.0
        return {"steve": unflat(s), "noob": unflat(n_), "sf": C.fS.at(t), "nf": C.fN.at(t), "pf": C.fP.at(t), "patch_yaw": yaw}
    C.act = act


# ------------------------------------------------------------- post (haze + grade)
LOOKS = {
    "dusk": ({"L": 240, "start": 22, "max": 0.72, "haze_warm": True}, {"tint": [1.05, 0.98, 0.98], "glow": 0.55}),
    "storm": ({"L": 150, "start": 14, "max": 0.78, "haze_storm": True}, {"tint": [1.02, 0.92, 1.08], "glow": 0.65}),
    "void": ({"L": 120, "start": 10, "max": 0.7, "haze_storm": True}, {"tint": [1.03, 0.95, 1.06], "glow": 0.6}),
    "clear": ({"L": 200, "start": 14, "max": 0.6, "haze_warm": True}, {"tint": [1.07, 1.0, 0.92], "glow": 0.6}),
}


def finish(path, mist_path, look):
    from PIL import Image
    import grade as G
    import assemble
    im = Image.open(path).convert("RGB")
    hz, gr = LOOKS[look["tag"]]
    if os.path.exists(mist_path):
        im = G.haze(im, mist_path, None, hz)
    assemble.W, assemble.H = im.size
    assemble.grade(im, dict({"saturation": 1.28, "threshold": 0.7}, **gr), 0, 0, None)
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
    ap.add_argument("--times", help="render these times only (previews)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    n_frames = int(round((tl["length"] + 0.4) * FPS)) + 1
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    E = build(tl, a.voice, a.tex_dir, a.assets, a.res, a.samples)
    _acting(E.C)
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
        frames = list(range(1, n_frames + 1))
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
        finish(dst, cand[-1] if cand else "", state.get("look", {"tag": "dusk"}))
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
