"""The movie, chapter 3 ("The Dragon Entered an Obby") v2, in the new look and in 16:9.

The creator's notes (2026-11-25, story/movie/ep03_shots.md "v2"): it picks up Episode 2's dive into the portal.
Inside the swirl; then the Noob's world, an obby floating in a Roblox sky (stages towering off into the haze,
kill bricks, spinning beams, truss ladders, neon checkpoints, studded plastic, a warm sun). A portal tears open
over the spawn pad, they tumble out, the dragon blasts through after them. They hide at a ledge where four
players stand frozen in glitch crystal (the setup); the tutorial is a hologram in the sky; the Noob jumps and is
killed, respawns on the checkpoint; the dragon comes for Steve, his wall knocks it low, right under the Noob's
blind jump; it carries him into the crystals and the players are freed; it banks round over them mid-roar and
freezes in a stutter, wings locked, the wall's cobblestones hanging in the air round it; the glitch.
Sound and timing: episodes/movie_ep03_the_dragon.json (movie/ep03_v2).

    python src/lookdev/movie_ep03.py TIMELINE VOICE TEX_DIR ASSETS OUT_DIR [--times 1.0,5.0] [--res 720]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import movie_ep00 as M                                                # noqa: E402
import movie_ep02 as E2                                               # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402
from kit.timeref import spread                                        # noqa: E402

B = M.B
_yaw, _wrap, _clamp, _cr = E2._yaw, E2._wrap, E2._clamp, E2._cr
life = E2.life

# ------------------------------------------------------------------ the place (metres, z up; the camera mostly south, looking north)
SPAWN = (Vector((0, 0, 0)), (6.0, 5.0, 1.2))            # the spawn pad (top at z 0)
TERRACE = (Vector((-7.0, 0.5, 0)), (6.0, 6.0, 1.2))     # west of it, a 1 m gap
LEDGE = (Vector((-7.0, 2.9, 0.55)), (6.0, 1.2, 1.1))     # the raised ledge on the terrace's back edge
CRY_X = (-9.0, -7.7, -6.4, -5.1)                         # the four crystals on the ledge (west to east)
CRY_Y, CRY_Z = 2.9, 1.1
CP = (Vector((8.0, -1.0, 0.5)), (3.4, 3.4, 0.8))         # the checkpoint (top at z 0.5)
STONE = (Vector((4.6, -1.2, 0.2)), (1.4, 1.4, 0.6))      # a stepping stone to it
AHEAD = [Vector((10.0, -5.0, 5.5)), Vector((14.0, -7.5, 7.5)), Vector((18.0, -10.0, 9.5))]   # the course ahead (smashed)
PORTAL = Vector((0.0, 4.6, 1.0))                          # the portal's foot (6 x 8, facing -y), floating behind the pad
PW, PH = 6, 8
WALL_X = -1.6                                             # Steve's wall (3 wide along y, 2 high)
WALL_Y = (-1.3, -0.3, 0.7)
STEVE_LAND = Vector((-0.9, -0.5, 0))
NOOB_LAND = Vector((1.1, -1.0, 0))
HIDE_S = Vector((-5.0, 1.55, 0))
HIDE_N = Vector((-7.95, 1.55, 0))
EDGE_N = Vector((-6.8, -2.25, 0))                         # the terrace's front edge: the Noob's jump
STEVE_WALL = Vector((-0.45, -0.3, 0))
STEVE_FLAT = Vector((0.7, -2.0, 0))
STEVE_PLAN = Vector((0.8, -2.4, 0))
CP_SPOT = Vector((7.6, -1.0, 0.5))
CP_EDGE = Vector((6.75, -0.9, 0.5))
DRAGON_SCALE = 0.95
HEAD_AHEAD = 3.6                                          # its head is this far ahead of its root (measured)


def b(name, i=0):
    return B[name][i]


def gp(E, v):
    return Vector((v.x, v.y, E.ground(v.x, v.y)))


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    from world import sky, sun_object
    from stage import build_steve, build_noob_char, char_light
    from roblox import plastic_material
    E = M.Ep()
    E.tl, E.tex_dir, E.assets = tl, tex_dir, assets
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    E.sc = sc
    E.sun, E.to_sun = sun_object(sc, 150, 40, energy=4.4, color=(1.0, 0.9, 0.78))
    E.sky = sky(sc, E.to_sun, fill=1.05)
    E.plastic = plastic_material()
    E.tops = []                                           # (x0, x1, y0, y1, top z) for the ground under a spot
    _course(E)
    _far_world(E)
    _clouds(E)
    E.S = build_steve(sc)
    E.N = build_noob_char(sc)
    E.lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    from props import sprite_item, hold
    pk = sprite_item("iron_pickaxe", os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets",
                                                  "minecraft", "textures", "item"), px=0.072)
    hold(E.S.arm, pk, "sr", up=25, face=60, collection=[E.S.rig])
    E.P = type("P", (), {})()                            # (movie_ep02's helpers look for a hidden first portal)
    _players(E)
    _crystals(E)
    _portal(E, assets)
    _wall(E, assets)
    _burst(E)
    _respawn(E)
    _hologram(E)
    _dragon(E, assets)
    _checker(E)
    _shards(E)
    _tunnel(E, assets)
    _matte_noob(E)
    E.key = char_light(sc, "char_key", (0, -3, 3), 300, (1.0, 0.92, 0.82), cone=40, size=1.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.dof.use_dof = True
    cam.data.sensor_width = 36
    cam.data.clip_end = 3000
    E.cam = cam
    E2.lens_wash(E)
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = res * 16 // 9
    sc.render.resolution_y = res
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.28
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = -0.05
    sc.render.fps = FPS
    sc.render.compositor_device = "CPU"
    from ep09_new import _mist_output
    _mist_output(sc)
    sc.world.mist_settings.start = 30.0
    sc.world.mist_settings.depth = 400.0
    return E


def _top(E, ob, c, size):
    E.tops.append((c.x - size[0] / 2, c.x + size[0] / 2, c.y - size[1] / 2, c.y + size[1] / 2, c.z + size[2] / 2, ob))


def ground(E, x, y):
    best = -50.0
    for x0, x1, y0, y1, z, ob in E.tops:
        if ob is not None and (ob.hide_render or ob.location.z < -100):
            continue
        if x0 <= x <= x1 and y0 <= y <= y1:
            best = max(best, z)
    return best


def _neon_material():
    m = bpy.data.materials.get("rbx_neon")
    if m:
        return m
    m = bpy.data.materials.new("rbx_neon")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(oi.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(oi.outputs["Color"], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 5.0
    bs.inputs["Roughness"].default_value = 0.4
    return m


def part(E, name, c, size, colour, neon=False, shape="box", top=True, col=None):
    """A Roblox part: studded plastic in one of the classic colours (or neon). c is its centre."""
    from roblox import make_part, BRICK, lin
    col = col or E.sc.collection
    if isinstance(colour, tuple):
        BRICK[name] = colour
        colour = name
    ob = make_part(col, name, size, colour, _neon_material() if neon else E.plastic, shape=shape)
    ob.location = c
    if top:
        _top(E, ob, Vector(c), size)
    return ob


def _course(E):
    E.ground = lambda x, y: ground(E, x, y)
    s0 = part(E, "spawn", SPAWN[0] - Vector((0, 0, SPAWN[1][2] / 2)), SPAWN[1], "Medium stone grey")
    E.tops[-1] = E.tops[-1][:4] + (0.0, None)
    sp = part(E, "spawn_plate", Vector((0, -0.2, 0.02)), (2.4, 2.4, 0.04), "Institutional white", top=False)
    for k, (dx, dy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):              # the spawn's corner marks
        part(E, f"spawn_mark_{k}", Vector((dx * 1.05, -0.2 + dy * 1.05, 0.03)), (0.3, 0.3, 0.06), "Bright blue", top=False)
    t0 = part(E, "terrace", TERRACE[0] - Vector((0, 0, TERRACE[1][2] / 2)), TERRACE[1], "Bright blue")
    E.tops[-1] = E.tops[-1][:4] + (0.0, None)
    E.ledge = part(E, "ledge", LEDGE[0], LEDGE[1], "Bright violet")
    E.ledge_home = Vector(LEDGE[0])
    part(E, "cp", CP[0] - Vector((0, 0, CP[1][2] / 2)), CP[1], "Dark stone grey")
    E.tops[-1] = E.tops[-1][:4] + (CP[0].z, None)
    E.cp_pad = part(E, "cp_pad", CP[0] + Vector((0, 0, 0.03)), (2.6, 2.6, 0.06), (40, 255, 90), neon=True, top=False)
    part(E, "stone", STONE[0] - Vector((0, 0, STONE[1][2] / 2)), STONE[1], "Bright orange")
    E.tops[-1] = E.tops[-1][:4] + (STONE[0].z, None)
    # the checkpoint flag
    part(E, "flag_pole", Vector((9.3, 0.3, 0.5 + 1.4)), (0.12, 0.12, 2.8), "Institutional white", shape="cyl", top=False)
    E.flag = part(E, "flag", Vector((9.3, 0.3 + 0.0, 0.5 + 2.45)), (0.05, 1.1, 0.7), (40, 255, 90), neon=True, top=False)
    E.flag.location.x += 0.0
    E.flag.location.y += 0.55
    # the course ahead, smashed by the dragon on its way out
    E.ahead = []
    for k, (c, colr) in enumerate(zip(AHEAD, ("Bright yellow", "Bright orange", "Bright red"))):
        ob = part(E, f"ahead_{k}", c, (3.0, 3.0, 0.8), colr, top=False)
        E.ahead.append(ob)
    # near the course: a truss up to a high stage, a spinner, kill bricks, a neon stripe
    for i in range(14):
        z = 0.5 + i * 0.9
        part(E, f"truss_r_{i}", Vector((-11.4, 5.2, z)), (1.0, 0.12, 0.12), "Medium stone grey", top=False)
    for dx in (-0.45, 0.45):
        part(E, f"truss_s_{dx}", Vector((-11.4 + dx, 5.2, 6.6)), (0.12, 0.12, 13.0), "Medium stone grey", top=False)
    part(E, "high_stage", Vector((-11.4, 6.8, 13.0)), (4.0, 4.0, 0.8), "Bright green", top=False)
    for k, (x, z) in enumerate(((-11.8, 0.0), (-14.2, 0.5), (-16.6, 1.0), (-19.0, 1.5), (-22.0, 2.0))):   # the course west
        part(E, f"west_{k}", Vector((x, -0.6 + 0.4 * k, z - 0.3)), (1.6, 1.6, 0.6), ("Bright yellow", "Bright green", "Bright orange",
                                                                                     "Bright red", "Bright blue")[k], top=False)
    part(E, "high_stage2", Vector((-4.0, 12.0, 16.0)), (3.0, 3.0, 0.8), "Bright yellow", top=False)
    E.spinners = []
    hub = part(E, "spin_post", Vector((15.0, 7.0, 1.5)), (0.6, 0.6, 3.0), "Dark stone grey", shape="cyl", top=False)
    part(E, "spin_base", Vector((15.0, 7.0, -0.2)), (7.0, 7.0, 0.8), "Bright blue", top=False)
    bar = part(E, "spin_bar", Vector((15.0, 7.0, 2.4)), (6.0, 0.4, 0.4), (255, 40, 40), neon=True, top=False)
    E.spinners.append((bar, 1.4))
    for k in range(4):
        part(E, f"kill_{k}", Vector((12.5 + k * 1.6, -5.5, 0.1 + 0.3 * k)), (1.0, 1.0, 0.3), (255, 30, 30), neon=True, top=False)
        part(E, f"killstep_{k}", Vector((12.5 + k * 1.6, -5.5, -0.35 + 0.3 * k)), (1.4, 1.4, 0.6), "Medium stone grey", top=False)


def _far_world(E):
    """The obby goes on into the haze: towers of stages, truss ladders, spinners, kill paths, neon checkpoints."""
    rnd = random.Random(5)
    cols = ["Bright red", "Bright blue", "Bright yellow", "Bright green", "Bright orange", "Bright violet",
            "Lime green", "Pastel blue", "Medium stone grey", "Institutional white"]
    col = bpy.data.collections.new("far")
    E.sc.collection.children.link(col)
    k = 0
    for i in range(70):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(32, 240)
        x, y = math.sin(a) * d, math.cos(a) * d
        if y < -10 and d < 60:                            # keep the near south (the cameras' side) open
            continue
        z0 = rnd.uniform(-25, 30)
        kind = rnd.choice(("tower", "tower", "truss", "spinner", "kill", "checkpoint", "steps"))
        s = 1.0 + d / 120
        if kind == "tower":
            n = rnd.randint(3, 6)
            for j in range(n):
                w = rnd.uniform(3, 8) * s
                part(E, f"f{k}", Vector((x + rnd.uniform(-2, 2), y + rnd.uniform(-2, 2), z0 + j * rnd.uniform(5, 9) * s)),
                     (w, w * rnd.uniform(0.6, 1.4), 1.2 * s), rnd.choice(cols), top=False, col=col)
                k += 1
                part(E, f"f{k}", Vector((x, y, z0 + j * 7 * s - 3.5 * s)), (0.6 * s, 0.6 * s, 7 * s), "Medium stone grey",
                     top=False, col=col)
                k += 1
        elif kind == "truss":
            h = rnd.uniform(14, 40)
            for dx in (-0.6, 0.6):
                for dy in (-0.6, 0.6):
                    part(E, f"f{k}", Vector((x + dx * s, y + dy * s, z0 + h / 2)), (0.15 * s, 0.15 * s, h), "Medium stone grey",
                         top=False, col=col)
                    k += 1
            for j in range(int(h / 2)):
                part(E, f"f{k}", Vector((x, y, z0 + j * 2)), (1.3 * s, 1.3 * s, 0.12 * s), "Medium stone grey", top=False, col=col)
                k += 1
            part(E, f"f{k}", Vector((x, y, z0 + h)), (5 * s, 5 * s, 1 * s), rnd.choice(cols), top=False, col=col)
            k += 1
        elif kind == "spinner":
            part(E, f"f{k}", Vector((x, y, z0)), (8 * s, 8 * s, 1 * s), rnd.choice(cols), top=False, col=col)
            k += 1
            bar = part(E, f"f{k}", Vector((x, y, z0 + 1.2 * s)), (7 * s, 0.5 * s, 0.5 * s), (255, 40, 40), neon=True, top=False, col=col)
            k += 1
            E.spinners.append((bar, rnd.uniform(0.8, 2.0) * rnd.choice((-1, 1))))
        elif kind == "kill":
            for j in range(5):
                part(E, f"f{k}", Vector((x + j * 3 * s, y, z0 + j * 0.8 * s)), (2 * s, 2 * s, 0.6 * s), rnd.choice(cols), top=False, col=col)
                k += 1
                if j % 2:
                    part(E, f"f{k}", Vector((x + j * 3 * s - 1.5 * s, y, z0 + j * 0.8 * s)), (1 * s, 2 * s, 0.4 * s),
                         (255, 30, 30), neon=True, top=False, col=col)
                    k += 1
        elif kind == "checkpoint":
            part(E, f"f{k}", Vector((x, y, z0)), (6 * s, 6 * s, 1 * s), "Dark stone grey", top=False, col=col)
            k += 1
            part(E, f"f{k}", Vector((x, y, z0 + 0.55 * s)), (4 * s, 4 * s, 0.1 * s), (40, 255, 90), neon=True, top=False, col=col)
            k += 1
        else:
            for j in range(7):
                part(E, f"f{k}", Vector((x + j * 2.6 * s, y + rnd.uniform(-1, 1), z0 + j * 1.4 * s)), (1.8 * s, 1.8 * s, 0.5 * s),
                     cols[j % 6], top=False, col=col)
                k += 1


def _clouds(E):
    """Soft white clouds round the obby, and a sea of them far below (we are high up)."""
    m = bpy.data.materials.new("cloud")
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bs.inputs["Roughness"].default_value = 1.0
    bs.inputs["Emission Color"].default_value = (0.95, 0.97, 1.0, 1)
    bs.inputs["Emission Strength"].default_value = 0.35
    if "Subsurface Weight" in bs.inputs:
        bs.inputs["Subsurface Weight"].default_value = 0.2
    rnd = random.Random(9)
    col = bpy.data.collections.new("clouds")
    E.sc.collection.children.link(col)

    def puff(c, r, n, flat=0.55):
        for _ in range(n):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
            ob = bpy.context.active_object
            for cc in ob.users_collection:
                cc.objects.unlink(ob)
            col.objects.link(ob)
            rr = r * rnd.uniform(0.5, 1.0)
            ob.scale = (rr, rr, rr * flat)
            ob.location = c + Vector((rnd.uniform(-1.6, 1.6) * r, rnd.uniform(-0.8, 0.8) * r, rnd.uniform(-0.2, 0.3) * r))
            ob.data.materials.append(m)
            ob.visible_shadow = False
            for p in ob.data.polygons:
                p.use_smooth = True
    for i in range(26):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(70, 300)
        c = Vector((math.sin(a) * d, math.cos(a) * d, rnd.uniform(-15, 45)))
        if c.y < -20 and d < 110:
            continue
        puff(c, rnd.uniform(6, 16), rnd.randint(4, 7))
    for i in range(40):                                   # the sea below
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(40, 420)
        puff(Vector((math.sin(a) * d, math.cos(a) * d, -70 + rnd.uniform(-8, 4))), rnd.uniform(18, 40), 3, flat=0.35)


def _players(E):
    """The four players frozen in the crystals, in their own colours (Episode 0's obby players)."""
    import noob as NB
    from stage import build_noob_char
    keep = (NB.BLUE, NB.GREEN)
    E.players = []
    for k, (shirt, pants) in enumerate((((220, 60, 60), (40, 40, 50)), ((150, 80, 220), (230, 230, 235)),
                                        ((250, 140, 30), (50, 90, 160)), ((60, 190, 90), (60, 60, 70)))):
        NB.BLUE, NB.GREEN = shirt, pants
        E.players.append(build_noob_char(E.sc, name=f"player_{k}"))
    NB.BLUE, NB.GREEN = keep


def _crystals(E):
    m = bpy.data.materials.new("glitch_crystal")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.55, 0.92, 1.0, 1)
    bs.inputs["Transmission Weight"].default_value = 0.88
    bs.inputs["Roughness"].default_value = 0.12
    bs.inputs["IOR"].default_value = 1.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (1.0, 0.1, 0.7, 1)
    e = ramp.color_ramp.elements.new(0.7)
    e.color = (0.1, 0.9, 1.0, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 0.9
    E.cry_mat = m
    E.crystals = []
    for k, x in enumerate(CRY_X):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"crystal_{k}"
        ob.scale = (1.0, 1.0, 2.35)
        ob.location = (x, CRY_Y, CRY_Z + 1.175)
        ob.data.materials.append(m)
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = 0.04
        E.crystals.append(ob)


def _portal(E, assets):
    from portal import build_portal
    E.PP = build_portal(E.sc, assets, at=tuple(PORTAL), w=PW, h=PH, name="arrival")
    E.PP.home = {ob.name: Vector(ob.location) for ob in E.PP.blocks}
    m = E.PP.membrane.data.materials[0]
    E.portal_power = m.node_tree.nodes[m["power"]] if "power" in m else None
    E.portal_flow = m.node_tree.nodes[m["flow"]] if "flow" in m else None
    E.portal_power0 = 0.6
    E.portal_light0 = E.PP.light.data.energy


def _wall(E, assets):
    mat = E2._blockmat("w_cobble", assets, "cobblestone.png")
    E.wall = []
    for r in range(2):
        for c, y in enumerate(WALL_Y):
            ob = E2._cube(E, f"cobble_{r}_{c}", 1.0, mat)
            ob.location = (0, 0, -300)
            E.wall.append((ob, Vector((WALL_X, y, 0.5 + r))))
    rnd = random.Random(4)
    E.wall_v = [Vector((rnd.uniform(4.0, 7.0), rnd.uniform(-1.2, 1.2), rnd.uniform(1.5, 4.0))) for _ in E.wall]
    E.wall_spin = [Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-6, 6))) for _ in E.wall]
    E.kick_v = [Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-2.0, 0.5), rnd.uniform(5.0, 7.5))) for _ in E.wall]


def _burst(E):
    N = E.N
    E.burst_parts = {"torso": N.torso, "neck": N.neck, "arm_sl": N.arms["sl"], "arm_sr": N.arms["sr"],
                     "leg_sl": N.legs["sl"], "leg_sr": N.legs["sr"]}
    E.burst_home = {k: (Vector(o.location), o.rotation_mode, tuple(o.rotation_quaternion)) for k, o in E.burst_parts.items()}
    rnd = random.Random(3)
    E.burst_v = {}
    for name in E.burst_parts:                                    # flung west with the dragon's sweep
        a = math.radians(180 + rnd.uniform(-35, 35))
        sp = rnd.uniform(2.6, 4.0)
        E.burst_v[name] = Vector((math.cos(a) * sp, math.sin(a) * sp, rnd.uniform(1.2, 2.6)))
    dm = bpy.data.materials.new("dark_cell")
    dm.use_nodes = True
    bs = dm.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.01, 0.005, 0.015, 1)
    bs.inputs["Emission Color"].default_value = (0.6, 0.0, 0.5, 1)
    bs.inputs["Emission Strength"].default_value = 1.4
    E.dark_cube = E2._cube(E, "dark_cell", 0.22, dm)


def _emit_mat(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    mx.inputs[0].default_value = 1.0
    return m, mx, em


def _respawn(E):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.9, depth=1.0)
    beam = bpy.context.active_object
    beam.name = "respawn_beam"
    m, mx, em = _emit_mat("respawn_beam", (0.3, 1.0, 0.55), 6.0)
    beam.data.materials.append(m)
    beam.visible_shadow = False
    beam.location = (0, 0, -300)
    E.beam, E.beam_mix = beam, mx


def _hologram(E):
    """The tutorial, as the obby's own hologram in the sky: a panel of light, TUTORIAL / JUMP ON THE BOSS!, an arrow."""
    from PIL import Image, ImageDraw, ImageFont
    W_, H_ = 1400, 600
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, W_ - 10, H_ - 10), 40, fill=(10, 40, 70, 170), outline=(120, 240, 255, 255), width=10)
    for yy in range(20, H_ - 20, 9):
        d.line((30, yy, W_ - 30, yy), fill=(120, 240, 255, 26), width=2)
    f1 = ImageFont.truetype(os.path.join(HERE, "..", "..", "fonts", "InterDisplay-Black.otf"), 96)
    f2 = ImageFont.truetype(os.path.join(HERE, "..", "..", "fonts", "InterDisplay-Black.otf"), 130)
    d.text((W_ / 2, 150), "TUTORIAL", font=f1, fill=(255, 225, 60, 255), anchor="mm")
    d.text((W_ / 2 - 60, 360), "JUMP ON THE BOSS!", font=f2, fill=(255, 255, 255, 255), anchor="mm")
    d.polygon([(W_ - 150, 300), (W_ - 40, 230), (W_ - 70, 290), (W_ - 30, 420), (W_ - 110, 430), (W_ - 140, 330)],
              fill=(255, 225, 60, 255))
    path = os.path.join(bpy.app.tempdir or "/tmp", "holo_tutorial.png")
    im.save(path)
    img = bpy.data.images.load(path)
    img.pack()
    m = bpy.data.materials.new("hologram")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 3.0
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(tx.outputs["Alpha"], mul.inputs[0])
    mul.inputs[1].default_value = 0.0
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = "hologram"
    ob.scale = (7.0, 3.0, 1)
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ob.location = (0, 0, -300)
    E.holo, E.holo_vis = ob, mul.inputs[1]


def _dragon(E, assets):
    from dragon import build_dragon, upgrade_skin
    E.D = build_dragon(E.sc, assets, scale=DRAGON_SCALE)
    upgrade_skin(E.D.mat)
    E.D.root.location = (0, 0, -400)
    E.D.meshes = [ob for ob in E.D.root.children_recursive if ob.type == "MESH"]


def _checker(E):
    m = bpy.data.materials.new("missing_texture")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Color1"].default_value = (1.0, 0.0, 0.85, 1)
    ck.inputs["Color2"].default_value = (0.0, 0.0, 0.0, 1)
    ck.inputs["Scale"].default_value = 3.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], ck.inputs["Vector"])
    nt.links.new(ck.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(ck.outputs["Color"], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 0.6
    bs.inputs["Roughness"].default_value = 0.6
    E.checker = m


def _shards(E):
    """The crystals' shards (and the players' release)."""
    rnd = random.Random(8)
    E.shards = []
    for k, x in enumerate(CRY_X):
        for j in range(14):
            bpy.ops.mesh.primitive_cube_add(size=1)
            ob = bpy.context.active_object
            ob.name = f"shard_{k}_{j}"
            s = rnd.uniform(0.12, 0.32)
            ob.scale = (s, s * rnd.uniform(0.6, 1.6), s * rnd.uniform(0.8, 2.2))
            ob.data.materials.append(E.cry_mat)
            ob.visible_shadow = False
            ob.location = (0, 0, -300)
            home = Vector((x + rnd.uniform(-0.45, 0.45), CRY_Y + rnd.uniform(-0.45, 0.45), CRY_Z + rnd.uniform(0.1, 2.2)))
            v = Vector((rnd.uniform(-1.0, 3.0), rnd.uniform(-4.0, -0.5), rnd.uniform(1.0, 4.5)))
            spin = Vector((rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(-12, 12)))
            E.shards.append((ob, k, home, v, spin))


def _tunnel(E, assets):
    """Inside the swirl (the first second: Episode 2's dive goes on): a tube of the portal's swirl, the two of them
    tumbling ahead toward the light at its end."""
    from portal import _mat_membrane
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=3.0, depth=60, end_fill_type="NOTHING")
    ob = bpy.context.active_object
    ob.name = "tunnel"
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = (0, 300, 300)
    m = _mat_membrane(assets).copy()
    m.name = "tunnel_swirl"
    m.use_backface_culling = False
    ob.data.materials.append(m)
    E.tunnel = ob
    E.tunnel_mat = m
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=3.0, fill_type="NGON")
    end = bpy.context.active_object
    end.name = "tunnel_end"
    em, _, emn = _emit_mat("tunnel_end", (1.0, 0.92, 1.0), 5.0)
    end.data.materials.append(em)
    end.rotation_euler = (math.radians(90), 0, 0)
    end.location = (0, 300 + 30, 300)
    E.tunnel_end = end
    lt = bpy.data.objects.new("tunnel_light", bpy.data.lights.new("tunnel_light", "POINT"))
    E.sc.collection.objects.link(lt)
    lt.data.color = (0.8, 0.45, 1.0)
    lt.data.energy = 0.0
    lt.data.shadow_soft_size = 2.0
    E.tunnel_light = lt


def _matte_noob(E):
    seen = set()
    for N in [E.N] + E.players:
        for ob in N.root.children_recursive:
            for m in (getattr(ob.data, "materials", None) or []) if ob.type == "MESH" else []:
                if m is None or m.name in seen or not m.use_nodes:
                    continue
                seen.add(m.name)
                bs = m.node_tree.nodes.get("Principled BSDF")
                if bs is None:
                    continue
                bs.inputs["Roughness"].default_value = max(0.6, bs.inputs["Roughness"].default_value)
                if "Coat Weight" in bs.inputs:
                    bs.inputs["Coat Weight"].default_value = 0.0
                if "Specular IOR Level" in bs.inputs:
                    bs.inputs["Specular IOR Level"].default_value = 0.28


# ------------------------------------------------------------------ the shots
SHOTS = [("tunnel", "tumble"), ("arrive", "tear"), ("burst", "burst"), ("boss", "noob_boss"), ("hide_line", "steve_hide"),
         ("hide", "hide"), ("hi", "noob_hi"), ("tap", "tap"), ("frozen", "noob_frozen"), ("here", "steve_here"),
         ("panel", "panel"), ("tut", "noob_tut"), ("dont", "steve_dont"), ("jump", "jump"), ("respawn", "respawn"),
         ("wheel", "wheel"), ("wall_line", "steve_wall"), ("build", "build"), ("crash", "crash"), ("again", "noob_again"),
         ("done", "noob_done"), ("ride", "ride"), ("free", "free"), ("thanks", "thanks"), ("myplan", "steve_myplan"),
         ("planwall", "noob_planwall"), ("bank", "bank"), ("freeze", "freeze"), ("wave", "wave"), ("lag", "noob_lag"),
         ("look", "look"), ("lagline", "steve_lag"), ("glitch", "glitch")]


def shot_bounds():
    out = []
    for name, beat in SHOTS:
        t0 = b(beat)
        if name == "dont":
            t0 = b("steve_dont") - 0.05
        out.append((name, t0))
    return out


def which(t):
    bs = shot_bounds()
    for i, (name, t0) in enumerate(bs):
        t1 = bs[i + 1][1] if i + 1 < len(bs) else 1e9
        if t < t1:
            return name, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


# ------------------------------------------------------------------ the dragon
def _dragon_keys():
    """(time, root position) for its flight. The head is about 5 m ahead of the root."""
    T = b
    W = WALL_X - HEAD_AHEAD                              # its root when the snout meets the wall (heading +x)
    seat_x = CP_EDGE.x - 1.6                              # where the Noob comes down on it
    return [
        (T("burst") - 0.3, Vector((0, 9.0, 5.0))),
        (T("burst"), Vector((0, 7.4, 4.8))),               # its head at the membrane
        (T("burst") + 0.35, Vector((0, 4.2, 4.6))),
        (T("burst") + 0.75, Vector((0.6, -1.4, 4.4))),     # right over them (they duck)
        (T("burst") + 1.1, Vector((5.5, -3.3, 4.6))),     # its snout through the course ahead, climbing east
        (T("burst") + 1.45, Vector((9.5, -5.8, 6.5))),
        (T("burst") + 1.8, Vector((13.5, -8.3, 8.5))),
        (T("burst", 1), Vector((17.0, -11.5, 11.0))),
        (T("noob_boss") + 0.6, Vector((14, -20, 12))),
        (T("steve_hide") + 0.8, Vector((12, -25, 15))),
        (T("hide"), Vector((4, -18, 12))),
        (T("hide") + 0.9, Vector((-7, -2, 10.5))),         # over the terrace: its shadow passes over them
        (T("hide", 1), Vector((-18, 12, 13))),
        (T("noob_hi") + 0.7, Vector((-20, 26, 16))),
        (T("tap") + 0.4, Vector((-6, 34, 18))),
        (T("noob_frozen") + 1.0, Vector((12, 30, 17))),
        (T("steve_here") + 0.6, Vector((22, 14, 16))),
        (T("panel") + 0.4, Vector((20, -6, 12))),
        (T("noob_tut") + 0.8, Vector((10, -14, 8))),
        (T("steve_dont") + 0.3, Vector((5, -11, 5.2))),
        (T("jump") + 0.6, Vector((0, -7.5, 3.8))),
        (T("kill"), Vector((-6.6 + HEAD_AHEAD * 0.3, -5.6, 3.0))),     # the sweep: its head and neck through him
        (T("kill") + 0.4, Vector((-10.5, -6.4, 3.4))),
        (T("kill", 1), Vector((-15, -4, 5))),
        (T("respawn") + 0.4, Vector((-19, 3, 7.5))),
        (T("noob_cp") + 0.5, Vector((-20, 9, 8.5))),
        (T("wheel"), Vector((-21, 7, 7.5))),
        (T("wheel") + 0.8, Vector((-24, 2, 5.5))),
        (T("wheel", 1), Vector((-24, -0.8, 4.6))),
        (T("steve_wall", 1), Vector((-19, -0.5, 3.6))),
        (T("build") + 0.8, Vector((-13.5, -0.35, 3.0))),
        (T("crash") + 0.1, Vector((W, -0.3, 2.75))),      # the snout meets the wall
        (T("crash") + 0.45, Vector((W + 1.6, -0.35, 2.45))),   # knocked low, slowed
        (T("crash") + 1.0, Vector((W + 3.6, -0.5, 2.3))),
        (T("crash", 1), Vector((W + 5.6, -0.6, 2.25))),
        (T("noob_again", 1), Vector((seat_x - 2.5, -0.8, 2.25))),
        (T("leap") + 0.75, Vector((seat_x - 0.3, -0.9, 2.3))),   # he lands on it (the seat is a little ahead of the root)
        (T("leap", 1), Vector((seat_x + 2.3, -0.9, 3.3))),
        (T("noob_done") + 0.7, Vector((11, -1.0, 4.5))),
        (T("ride"), Vector((14, 1, 5.5))),
        (T("ride") + 0.6, Vector((14, 7.5, 6.0))),
        (T("ride") + 1.25, Vector((3, 13, 6.0))),
        (T("ride") + 1.9, Vector((-14, 9, 4.6))),
        (T("ride", 1), Vector((-20, 4.4, 3.6))),
        (T("free") + 0.05, Vector((CRY_X[0] - HEAD_AHEAD, CRY_Y + 0.1, 3.2))),     # its snout into the first crystal
        (T("free") + 0.5, Vector((CRY_X[1] - HEAD_AHEAD, CRY_Y + 0.1, 3.2))),
        (T("free") + 0.95, Vector((CRY_X[2] - HEAD_AHEAD, CRY_Y + 0.1, 3.25))),
        (T("free") + 1.4, Vector((CRY_X[3] - HEAD_AHEAD, CRY_Y + 0.1, 3.35))),
        (T("free") + 1.9, Vector((-7.0, 5.5, 5.2))),       # up and away north of the ledge, clear of the portal
        (T("free", 1), Vector((-2, 11, 7.5))),
        (T("thanks") + 0.8, Vector((9, 8, 8.0))),
        (T("steve_myplan") + 0.4, Vector((12, -3, 7.0))),
        (T("steve_myplan", 1), Vector((9.2, -9.6, 6.0))),
        (T("noob_planwall"), Vector((8.6, -9.3, 5.7))),    # hovering, turned to Steve
        (T("noob_planwall", 1), Vector((8.3, -9.0, 5.7))),
        (T("bank"), Vector((7.8, -8.6, 5.6))),
        (T("bank") + 0.8, Vector((3.0, -3.0, 4.3))),       # the bank: low over the pad, its wings kick up the cobblestones
        (T("freeze"), Vector((-1.0, 0.8, 5.2))),           # locked: over the pad, north-west of Steve
    ]


def _dragon_pos(E, t):
    K = _dragon_keys()
    if t <= K[0][0]:
        return K[0][1].copy()
    for i in range(len(K) - 1):
        if K[i][0] <= t < K[i + 1][0]:
            u = (t - K[i][0]) / (K[i + 1][0] - K[i][0])
            p0 = K[max(0, i - 1)][1]
            p3 = K[min(len(K) - 1, i + 2)][1]
            return _cr(p0, K[i][1], K[i + 1][1], p3, u)
    return K[-1][1].copy()


def freeze_time(t):
    """The world time the dragon (and what it kicked up) is shown at: it stutters back twice, then locks."""
    f = b("freeze")
    if t < f:
        return t
    dt = t - f
    if dt < 0.12:
        return f - 0.06 + 0.06 * (dt / 0.12)
    if dt < 0.2:
        return f - 0.13
    if dt < 0.3:
        return f
    if dt < 0.36:
        return f - 0.09
    return f


def dragon_head(E):
    return E.D.head.matrix_world.translation


def dragon_seat(E):
    """Where the Noob sits: on its shoulders, just behind the neck."""
    return E.D.root.matrix_world @ Vector((0, -0.25 * 16 * 0.0625, -0.18))


def dragon(E, t):
    from dragon import pose_dragon
    D = E.D
    if t < b("burst") - 0.3:
        D.root.location = (0, 0, -400)
        bpy.context.view_layer.update()
        return
    te = freeze_time(t)
    frozen = t >= b("freeze")
    p = _dragon_pos(E, te)
    dtv = 0.04
    v = (_dragon_pos(E, te + dtv) - _dragon_pos(E, te - dtv)) / (2 * dtv)
    if frozen:                                          # its motion at the moment it locked
        v = (_dragon_pos(E, b("freeze") - 0.02) - _dragon_pos(E, b("freeze") - 0.1)) / 0.08
    hv = Vector((v.x, v.y, 0))
    yaw = _yaw(hv) if hv.length > 0.5 else 0.0
    # hovering at Steve for "Your plan was a wall": turned to him
    face = ss(b("steve_myplan", 1) - 0.4, b("noob_planwall"), te) * (1 - ss(b("bank"), b("bank") + 0.5, te))
    to = gp(E, STEVE_PLAN) + Vector((0, 0, 1.5)) - p
    yaw = yaw + _wrap(_yaw(Vector((to.x, to.y, 0))) - yaw) * face
    # the ledge: it ploughs along it heading east (held: no flip as it slows)
    plough = ss(b("free") - 0.3, b("free"), te) * (1 - ss(b("free") + 1.4, b("free") + 1.8, te))
    yaw = yaw + _wrap(_yaw(Vector((1, 0, 0))) - yaw) * plough
    pn = _dragon_pos(E, te + 0.1)
    yaw_rate = _wrap(_yaw(Vector(((pn - p).x, (pn - p).y, 0))) - _yaw(hv)) / 0.1 if hv.length > 0.5 else 0.0
    if frozen:
        yaw_rate = E._dragon_last_rate if hasattr(E, "_dragon_last_rate") else yaw_rate
    pitch = _clamp(math.degrees(math.atan2(-v.z, max(0.5, hv.length))), -35, 35) * (1 - face)
    bank = _clamp(-yaw_rate * 0.3, -45, 45) * (1 - face) * (1 - plough)
    # the wall: its snout knocked down, the body pitched nose-down, dazed
    knock = ss(b("crash") + 0.08, b("crash") + 0.2, te) * (1 - ss(b("crash") + 0.9, b("noob_again", 1), te))
    pitch += 12 * knock
    # wings: folded through the portal, then spread; a glide when it skims after the wall; full beats in the bank
    fold = 1 - ss(b("burst") + 0.45, b("burst") + 0.9, te)
    fold = max(fold, 0.55 * plough)
    glide = max(0.8 * knock, 0.3 * ss(b("leap"), b("leap") + 0.3, te) * (1 - ss(b("noob_done"), b("noob_done") + 0.5, te)))
    flap = 1.15 * te + 0.5 * max(0.0, min(te, b("freeze")) - b("bank"))
    amp = 1.0 + 0.35 * ss(b("bank"), b("bank") + 0.4, te)
    jaw = 0.9 * ss(b("burst"), b("burst") + 0.15, te) * (1 - ss(b("burst") + 1.2, b("burst") + 1.5, te)) \
        + 0.8 * ss(b("wheel") + 0.1, b("wheel") + 0.3, te) * (1 - ss(b("wheel") + 1.2, b("wheel") + 1.4, te)) \
        + 0.7 * ss(b("build") + 1.0, b("build") + 1.2, te) * (1 - ss(b("crash") + 0.05, b("crash") + 0.15, te)) \
        + 0.6 * ss(b("leap") + 0.8, b("leap") + 0.95, te) * (1 - ss(b("leap") + 1.3, b("leap") + 1.5, te)) \
        + 0.9 * ss(b("bank") + 0.2, b("bank") + 0.45, te)
    neck_pitch = 22 * knock - 15 * plough
    head_pitch = 12 * knock
    # watching Steve while hovering
    neck_yaw = 0.0
    head_yaw = 0.0
    if face > 0:
        rel = _wrap(_yaw(Vector((to.x, to.y, 0))) - yaw)
        neck_yaw = _clamp(rel, -50, 50) * 0.6 * face
        el = math.degrees(math.atan2(-to.z, max(1.0, Vector((to.x, to.y, 0)).length)))
        neck_pitch += _clamp(el, -10, 40) * 0.6 * face
    heave = pose_dragon(D, te, flap=flap, amp=amp, glide=glide, neck_pitch=neck_pitch, neck_yaw=neck_yaw,
                        head_pitch=head_pitch, head_yaw=head_yaw, jaw=min(1.0, jaw), legs=1.0, turn=_clamp(yaw_rate, -120, 120),
                        frozen=None)
    if fold > 0:
        for side, sx in (("l", 1), ("r", -1)):
            D.wing[side].rotation_euler.z += math.radians(-sx * 70 * fold)
            D.tip[side].rotation_euler.z += math.radians(-sx * 75 * fold)
    D.root.location = p + Vector((0, 0, heave))
    D.root.rotation_euler = (math.radians(pitch), math.radians(bank), math.radians(yaw))
    if not frozen:
        E._dragon_last_rate = yaw_rate
    # the glitch: the missing texture, flickering in, on more and more
    on = False
    if t >= b("glitch"):
        k = int(round(t * FPS))
        u = (t - b("glitch")) / max(0.1, b("glitch", 1) - b("glitch"))
        on = (k * 7919 % 13) / 13.0 < 0.25 + 0.5 * u
        if t < b("glitch") + 0.12:
            on = True
    for ob in D.meshes:
        ob.material_slots[0].material = E.checker if on else D.mat
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ the world's moving things
def light(E, t):
    for bar, w in E.spinners:
        bar.rotation_euler = (0, 0, w * t)
    E.flag.rotation_euler = (0, 0, 0.12 * math.sin(t * 3.1))


def portal(E, t):
    """It tears open over the pad: its blocks glitch in from scattered places, the membrane flares; it stays,
    flickering, for the whole chapter (where they came from)."""
    PP = E.PP
    t0 = b("tear")
    rnd = random.Random(12)
    for ob in PP.blocks:
        home = E.PP.home[ob.name]
        d = Vector((rnd.uniform(-3, 3), rnd.uniform(-2, 2), rnd.uniform(-3, 3)))
        delay = rnd.uniform(0.0, 0.35)
        u = ss(t0 + delay, t0 + delay + 0.35, t)
        jit = 0.0 if u >= 1 or u <= 0 else (0.08 if int(t * FPS) % 2 else -0.08)
        ob.location = home + d * (1 - u) + Vector((jit, 0, 0))
        ob.hide_render = t < t0 + delay
    on = ss(t0 + 0.35, t0 + 0.65, t)
    flick = 1.0 if t < b("drop") + 1.0 else 0.85 + 0.15 * math.sin(t * 23.0) * math.sin(t * 7.1)
    surge = math.exp(-((t - (b("burst") + 0.2)) / 0.25) ** 2) + math.exp(-((t - (b("drop") + 0.1)) / 0.2) ** 2)
    E.portal_power.inputs[2].default_value = E.portal_power0 * on * flick * (1 + 1.5 * surge)
    E.portal_flow.inputs[1].default_value = (0.13 * t, 0.37 * t * (1 + 2 * surge), 0)
    PP.membrane.hide_render = on <= 0.01
    PP.light.data.energy = E.portal_light0 * on * flick * (1 + 2 * surge) * 0.6


def tunnel(E, t):
    if t >= b("tear"):
        E.tunnel.location = (0, 300, 300)
        E.tunnel_end.location = (0, 330, 300)
        E.tunnel_light.data.energy = 0.0
        return
    base = Vector((0, -2000, 500))
    E.tunnel.location = base + Vector((0, 30, 0))
    E.tunnel.rotation_euler = (math.radians(90), t * 2.2, 0)        # spun about its own axis
    E.tunnel_end.location = base + Vector((0, 58 - 34 * ss(0, b("tear"), t), 0))
    E.tunnel_light.location = base + Vector((0, 14, 0))
    E.tunnel_light.data.energy = 350.0
    m = E.tunnel_mat
    m.node_tree.nodes[m["flow"]].inputs[1].default_value = (0.4 * t, 2.2 * t, 0)
    m.node_tree.nodes[m["power"]].inputs[2].default_value = 0.9


def ahead(E, t):
    """The three stages ahead, smashed as its snout goes through them: pieces flung on, tumbling down."""
    smash = [b("burst") + 1.1, b("burst") + 1.45, b("burst") + 1.8]
    for k, ob in enumerate(E.ahead):
        dt = t - smash[k]
        if dt < 0:
            ob.location = AHEAD[k]
            ob.rotation_euler = (0, 0, 0)
            ob.scale = (1, 1, 1)
            continue
        v = Vector((3.0, -6.0, 3.0))
        ob.location = AHEAD[k] + v * dt + Vector((0, 0, -4.9 * dt * dt))
        ob.rotation_euler = (dt * 3.0, dt * 1.7, dt * 2.2)
        s = max(0.0, 1 - dt / 3.0)
        ob.scale = (s, s, s)


def wall(E, t):
    """Steve's cobblestones: placed one by one (the place sounds), burst by the snout, tumbling down on the pad;
    four of them kicked up by its wings in the bank, hanging in the air when it freezes."""
    pts = spread(b("build"), b("build", 1) - 0.1, 6)
    hit = b("crash") + 0.1
    kick = b("bank") + 0.8
    te = freeze_time(t)
    for i, (ob, home) in enumerate(E.wall):
        if t < pts[i] - 0.05:
            ob.location = (0, 0, -300)
            continue
        if t < hit:
            u = ss(pts[i] - 0.05, pts[i] + 0.02, t)
            ob.location = home + Vector((0.35, 0, 0.25)) * (1 - u)
            ob.rotation_euler = (0, 0, 0)
            continue
        dt = te - hit
        v, w = E.wall_v[i], E.wall_spin[i]
        land_t = (v.z + math.sqrt(v.z * v.z + 2 * 9.81 * (home.z - 0.5))) / 9.81
        if dt < land_t:
            p = home + Vector((v.x * dt, v.y * dt, v.z * dt - 4.9 * dt * dt))
            r = w * dt
        else:
            p = home + Vector((v.x * land_t, v.y * land_t, 0))
            p.z = 0.5
            r = w * land_t
            r = Vector((round(r.x / (math.pi / 2)) * math.pi / 2, round(r.y / (math.pi / 2)) * math.pi / 2, r.z))
        if i < 4 and te >= kick:                         # kicked up by its wings
            dk = te - kick
            kv = E.kick_v[i]
            p = p + Vector((kv.x * dk, kv.y * dk, kv.z * dk - 4.9 * dk * dk))
            r = r + E.wall_spin[i] * dk * 0.6
            p.z = max(p.z, 0.5)
        ob.location = p
        ob.rotation_euler = tuple(r)


def crystals(E, t):
    hits = [b("free") + 0.05 + 0.45 * k for k in range(4)]
    # the dragon ploughs east along the ledge: the first it hits is the west one
    for k, ob in enumerate(E.crystals):
        ob.hide_render = t >= hits[k]
    for ob, k, home, v, spin in E.shards:
        dt = t - hits[k]
        if dt < 0 or dt > 2.2:
            ob.location = (0, 0, -300)
            continue
        p = home + Vector((v.x * dt, v.y * dt, v.z * dt - 4.9 * dt * dt))
        if p.z < 0.1:
            p.z = 0.1
        ob.location = p
        ob.rotation_euler = tuple(spin * dt)


def ledge(E, t):
    """The ledge shakes as it is hit."""
    hit = b("free") + 0.05
    if hit <= t < hit + 1.8:
        dt = t - hit
        E.ledge.location = E.ledge_home + Vector((0.05 * math.sin(dt * 60) * math.exp(-dt * 2), 0, 0))
    else:
        E.ledge.location = E.ledge_home


def hologram(E, t):
    a, z = b("panel"), b("jump") + 0.4
    if not (a <= t < z + 0.3):
        E.holo.location = (0, 0, -300)
        return
    u = ss(a, a + 0.35, t) * (1 - ss(z, z + 0.3, t))
    k = int(t * FPS)
    flick = 1.0 if u >= 1 else (1.0 if k % 3 else 0.35)
    E.holo.location = Vector((-3.6, -9.5, 7.8))
    E.holo.rotation_euler = (math.radians(100), 0, math.radians(195))      # facing them (north), tipped down
    E.holo.scale = (7.0, 3.0 * (0.15 + 0.85 * ss(a, a + 0.3, t)), 1)
    E.holo_vis.default_value = 0.95 * u * flick


# ------------------------------------------------------------------ the cast
def _lie(S_or_root, pitch, z=0.22):
    """Turn a placed character's holder to lie (pitch -90: on the back, +90: face down)."""
    ob = S_or_root
    e = ob.rotation_euler
    ob.rotation_euler = (math.radians(pitch), e[1], e[2])
    ob.location = Vector(ob.location) + Vector((0, 0, z * abs(math.sin(math.radians(pitch)))))


def _arc(a, c, h, u):
    """A jump from a to c with a peak h above the straight line."""
    p = a.lerp(c, u)
    return p + Vector((0, 0, 4 * h * u * (1 - u)))


def _run(pz, t, t0, rate, k=1.0, steve=True):
    pz.update(M.run_cycle((t - t0) * rate * 2 * math.pi, k, steve))


def _face_to(p, tgt):
    d = tgt - p
    return _yaw(Vector((d.x, d.y, 0)))


def _look(yaw, p, tgt, h=1.6, lim=60.0):
    d = tgt - (p + Vector((0, 0, h)))
    turn = _clamp(_wrap(_yaw(Vector((d.x, d.y, 0))) - yaw), -lim, lim)
    nod = -math.degrees(math.atan2(d.z, max(0.3, Vector((d.x, d.y, 0)).length)))
    return turn, _clamp(nod, -55, 40)


def steve(E, t):
    from ep09_new import SF
    S = E.S
    face = dict(SF["flat"])
    pz = {"arm_sr": {"fwd": 25, "out": 12, "elbow": 35}, "arm_sl": {"fwd": 10, "out": 8, "elbow": 20}}
    lie = 0.0
    dragon_at = dragon_head(E) if E.D.root.location.z > -100 else Vector((5, -15, 12))
    if t < b("tear"):
        return _tumble(E, t, "steve")
    if t < b("drop") + 0.3:
        S.holder.location = (0, 0, -500)
        return
    if t < b("drop") + 0.75:                                    # out of the membrane, falling onto the pad
        u = ss(b("drop") + 0.3, b("drop") + 0.75, t)
        a = PORTAL + Vector((-0.7, -0.3, 2.2))
        p = _arc(a, gp(E, STEVE_LAND), 0.4, u)
        yaw = 180.0
        pz.update({"arm_sl": {"fwd": 120, "out": 40}, "arm_sr": {"fwd": 110, "out": 40}, "chest_lean": -20})
        face = dict(SF["scared"])
        M.set_steve(E, p, yaw, pz, face, t)
        _lie(S.holder, -70 * u)
        return
    if t < b("noob_boss") + 0.4:                               # on his back; up on his elbows as it bursts over them
        p = gp(E, STEVE_LAND)
        yaw = 180.0 - 20
        up = ss(b("drop") + 1.0, b("drop") + 1.4, t)
        tilt = -90 + 35 * up
        pz.update({"head_nod": -20 * up, "arm_sl": {"fwd": -30, "out": 30, "elbow": 60}, "arm_sr": {"fwd": -30, "out": 30, "elbow": 60}})
        face = dict(SF["stunned"])
        if t > b("burst"):
            face = dict(SF["scared"])
            pz["head_turn"] = _clamp(30 * math.sin(min(1.0, (t - b("burst")) / 1.4) * math.pi), -40, 40)
        M.set_steve(E, p, yaw, pz, face, t)
        _lie(S.holder, tilt)
        return
    if t < b("hide"):                                           # up; "It used our portal. HIDE!"
        p = gp(E, STEVE_LAND)
        up = ss(b("noob_boss") + 0.4, b("steve_hide") - 0.1, t)
        yaw = lerp(160.0, _face_to(p, gp(E, NOOB_LAND) + Vector((0, -3, 0))), up)
        tl, nd = _look(yaw, p, E.PP.root.location + Vector((0, 0, 4)))
        back = ss(b("steve_hide") + 0.1, b("steve_hide") + 0.4, t) * (1 - ss(b("steve_hide") + 1.0, b("steve_hide") + 1.3, t))
        pz["head_turn"] = tl * back
        pz["head_nod"] = nd * back * 0.5
        face = dict(SF["flat"])
        hide_ = ss(b("steve_hide") + 1.2, b("steve_hide") + 1.4, t)
        if hide_ > 0:
            face = dict(SF["scared"])
            pz["arm_sl"] = {"fwd": 85 * hide_, "out": 10 + 40 * hide_, "elbow": 10}
        pz = life(E, "steve", pz, face, t, 1.0)
        M.set_steve(E, p, yaw, pz, face, t)
        if up < 1:
            _lie(S.holder, -55 * (1 - up))
        return
    if t < b("hide") + 1.25:                                   # the run to the ledge (a hop over the gap)
        u = (t - b("hide")) / 1.25
        a, c = gp(E, STEVE_LAND), gp(E, HIDE_S)
        p = a.lerp(c, u * u * (3 - 2 * u))
        gx = -3.5
        if abs(p.x - gx) < 0.9:
            p.z += 0.45 * math.cos((p.x - gx) / 0.9 * math.pi / 2)
        p.z = max(p.z, 0.0)
        yaw = _face_to(a, c)
        _run(pz, t, b("hide"), 2.4)
        face = dict(SF["scared"])
        M.set_steve(E, p, yaw, pz, face, t)
        return
    if t < b("noob_frozen") + 0.4:                             # crouched against the ledge, peeking at the sky
        p = gp(E, HIDE_S)
        yaw = 180.0 + 10
        pz.update({"hips_drop": 0.55, "chest_lean": 20, "foot_sl": {"y": -0.25}, "foot_sr": {"y": 0.2}})
        tl, nd = _look(yaw, p, dragon_at, h=1.1)
        pz["head_turn"], pz["head_nod"] = tl * 0.7, nd * 0.7
        face = dict(SF["worried"])
        pz = life(E, "steve", pz, face, t, 1.3)
        M.set_steve(E, p, yaw, pz, face, t)
        return
    if t < b("panel"):                                          # up: "The glitch is here too."
        p = gp(E, HIDE_S)
        u = ss(b("noob_frozen") + 0.4, b("noob_frozen") + 1.0, t)
        cry = Vector((CRY_X[3], CRY_Y, 2.6))
        yaw = lerp(190.0, _face_to(p, cry) + 35, u)
        pz["hips_drop"] = 0.55 * (1 - u)
        tl, nd = _look(yaw, p, cry)
        away = ss(b("steve_here") + 0.3, b("steve_here") + 0.8, t)
        yaw = lerp(yaw, 25.0, away)
        pz["head_turn"] = lerp(tl, -10, away)
        pz["head_nod"] = lerp(nd, 4, away)
        face = dict(SF["worried"])
        face.update({"bb_raise": 0.05, "m_arch": 0.12})
        pz = life(E, "steve", pz, face, t, 1.5)
        M.set_steve(E, p, yaw, pz, face, t)
        return
    if t < b("jump") + 1.6:                                     # the panel; DON'T!; the Noob's jump and his end
        p = gp(E, HIDE_S)
        yaw = _face_to(p, gp(E, EDGE_N) + Vector((0, -4, 0)))
        tgt = E.holo.location if t < b("steve_dont") else (E.N.root.location + Vector((0, 0, 1.2)))
        if t >= b("kill"):
            tgt = Vector((-6.6, -5.6, 3.0))
        tl, nd = _look(yaw, p, Vector(tgt))
        pz["head_turn"], pz["head_nod"] = tl, nd
        face = dict(SF["worried"])
        dont = ss(b("steve_dont") - 0.1, b("steve_dont") + 0.1, t)
        if dont > 0:
            face = dict(SF["scared"])
            pz["arm_sl"] = {"fwd": 90 * dont, "out": 5, "elbow": 5}
            pz["chest_lean"] = 10 * dont
            p = p + (gp(E, EDGE_N) - p).normalized() * 0.5 * dont
        if t >= b("kill"):
            k = ss(b("kill"), b("kill") + 0.15, t)
            pz["chest_lean"] = -10 * k
            pz["arm_sl"] = {"fwd": 40, "out": 20, "elbow": 40}
            face = dict(SF["stunned"])
        pz = life(E, "steve", pz, face, t, 1.7)
        M.set_steve(E, p, yaw, pz, face, t)
        return
    if t < b("wheel") + 0.2:                                    # looks east at the checkpoint
        p = gp(E, HIDE_S) + (gp(E, EDGE_N) - gp(E, HIDE_S)).normalized() * 0.5
        yaw = _face_to(p, gp(E, CP_SPOT)) + 20
        tl, nd = _look(yaw, p, gp(E, CP_SPOT) + Vector((0, 0, 1.4)))
        pz["head_turn"], pz["head_nod"] = tl, nd
        face = dict(SF["flat"])
        face.update({"bb_raise": 0.1})
        pz = life(E, "steve", pz, face, t, 1.9)
        M.set_steve(E, p, yaw, pz, face, t)
        return
    if t < b("steve_wall") + 0.2:                               # he heads for the checkpoint; it comes from behind
        a = gp(E, HIDE_S) + (gp(E, EDGE_N) - gp(E, HIDE_S)).normalized() * 0.5
        c = gp(E, STEVE_WALL)
        u = ss(b("wheel") + 0.2, b("wheel", 1) - 0.1, t)
        p = a.lerp(c, u)
        gx = -3.5
        if abs(p.x - gx) < 0.9:
            p.z += 0.45 * math.cos((p.x - gx) / 0.9 * math.pi / 2)
        p.z = max(p.z, 0.0)
        if u < 1:
            yaw = _face_to(a, c)
            _run(pz, t, b("wheel"), 2.2)
        else:                                                   # he turns to it: head, shoulders, then a step
            yaw = lerp(_face_to(a, c), -90.0, ss(b("wheel", 1) - 0.1, b("steve_wall") + 0.1, t))
            pz["head_turn"] = -30 * (1 - ss(b("wheel", 1), b("steve_wall") + 0.1, t)) * ss(b("wheel", 1) - 0.3, b("wheel", 1), t)
        face = dict(SF["worried"])
        M.set_steve(E, p, yaw, pz, face, t)
        return
    if t < b("crash") + 0.1:                                     # "Plan: wall." and the wall
        p = gp(E, STEVE_WALL)
        yaw = -90.0
        face = dict(SF["flat"])
        if t >= b("build"):
            pts = spread(b("build"), b("build", 1) - 0.1, 6)
            k = max([i for i, x in enumerate(pts) if x <= t + 0.08] or [0])
            jab = math.exp(-((t - pts[k] + 0.03) / 0.07) ** 2)
            hz = E.wall[k][1].z - 1.3
            pz["arm_sr"] = {"fwd": 70 + 25 * hz + 30 * jab, "out": 12, "elbow": 35 - 30 * jab}
            pz["head_nod"] = -8 * hz
            ty = E.wall[k][1].y
            pz["head_turn"] = _clamp((ty + 0.3) * -25, -30, 30)
            face = dict(SF["worried"]) if t > b("build", 1) - 0.4 else dict(SF["flat"])
        pz = life(E, "steve", pz, face, t, 2.1)
        M.set_steve(E, p, yaw, pz, face, t)
        return
    if t < b("ride") + 0.3:                                       # he dives flat; stays down while it passes
        a, c = gp(E, STEVE_WALL), gp(E, STEVE_FLAT)
        u = ss(b("crash") + 0.1, b("crash") + 0.5, t)
        p = a.lerp(c, u) + Vector((0, 0, 0.35 * math.sin(math.pi * u)))
        yaw = _face_to(a, c)
        face = dict(SF["scared"])
        pz.update({"arm_sl": {"fwd": 170 * u, "out": 15}, "arm_sr": {"fwd": 170 * u, "out": 15}, "head_nod": -25 * u})
        M.set_steve(E, p, yaw, pz, face, t)
        _lie(S.holder, 85 * u, z=0.2)
        if t > b("noob_done"):
            face = dict(SF["stunned"])
        return
    if t < b("steve_myplan"):                                    # up; he walks over, watching the ride and the crash
        a, c = gp(E, STEVE_FLAT), gp(E, STEVE_PLAN)
        up = ss(b("ride") + 0.3, b("ride") + 1.0, t)
        u = ss(b("ride") + 1.0, b("free") + 0.8, t)
        p = a.lerp(c, u)
        yaw = _face_to(p, Vector((CRY_X[1], CRY_Y, 2)))
        if 0 < u < 1:
            E2._walk(pz, t, b("ride"), 1.6)
        tgt = dragon_head(E)
        tl, nd = _look(yaw, p, tgt)
        pz["head_turn"], pz["head_nod"] = tl * up, nd * up
        face = dict(SF["stunned"])
        M.set_steve(E, p, yaw, pz, face, t)
        if up < 1:
            _lie(S.holder, 85 * (1 - up), z=0.2)
        return
    # "That was my plan." onward: at his spot
    p = gp(E, STEVE_PLAN)
    yaw = 35.0                                                    # turned to the camera's side (south-east)
    face = dict(SF["flat"])
    if t < b("bank"):
        tgt = dragon_head(E)
        tl, nd = _look(yaw, p, tgt)
        side = ss(b("noob_planwall") - 0.2, b("noob_planwall") + 0.3, t)
        pz["head_turn"], pz["head_nod"] = tl * side, nd * side
        if t < b("steve_myplan", 1):
            face = dict(SF["flat"])
            face.update({"bb_raise": -0.12, "both_to": -0.45, "both_tm": -0.5})
    elif t < b("look"):                                           # it banks over him; he ducks; then he dusts himself off
        k = ss(b("bank") + 0.5, b("bank") + 0.8, t) * (1 - ss(b("bank") + 1.3, b("freeze"), t))
        pz["hips_drop"] = 0.35 * k
        pz["chest_lean"] = 25 * k
        pz["arm_sl"] = {"fwd": 120 * k, "out": 30, "elbow": 90}
        dust = ss(b("freeze") + 0.2, b("freeze") + 0.5, t)
        pz["arm_sr"] = {"fwd": 40 * dust, "out": 10, "elbow": 70 + 20 * math.sin(t * 14) * dust}
        pz["head_nod"] = 14 * dust
        face = dict(SF["flat"])
        if t >= b("noob_lag"):
            face.update({"bb_raise": 0.1})
    else:                                                         # the turn: head, then shoulders, then a step
        tgt = dragon_head(E)
        u1 = ss(b("look"), b("look") + 0.35, t)
        u2 = ss(b("look") + 0.25, b("look", 1), t)
        want = _face_to(p, tgt)
        yaw = lerp(35.0, lerp(35.0, want, 0.55), u2)
        tl, nd = _look(yaw, p, tgt)
        pz["head_turn"], pz["head_nod"] = tl * u1, nd * u1
        face = dict(SF["flat"])
        face.update({"both_to": -0.2, "bb_raise": 0.0, "bb_tilt": 0.25})
    pz = life(E, "steve", pz, face, t, 2.7)
    M.set_steve(E, p, yaw, pz, face, t)


def _tumble(E, t, who):
    """In the swirl: tumbling slowly ahead of the camera toward the light."""
    base = Vector((0, -2000, 500))
    rot = t * (1.6 if who == "steve" else -2.1)
    off = Vector((-0.9, 11 + 2.0 * t, 0.3)) if who == "steve" else Vector((0.9, 12.5 + 2.4 * t, -0.4))
    if who == "steve":
        from ep09_new import SF
        pz = {"arm_sl": {"fwd": 140, "out": 50}, "arm_sr": {"fwd": 120, "out": 60}, "chest_lean": -15}
        M.set_steve(E, base + off, 180.0, pz, dict(SF["scared"]), t)
        E.S.holder.rotation_euler = (rot, 0.4 * rot, math.radians(180))
    else:
        from ep09_new import NF
        pz = {"arm_sl": {"fwd": 160, "out": 40}, "arm_sr": {"fwd": 150, "out": 50}, "leg_sl": {"fwd": 30}, "leg_sr": {"fwd": -20}}
        M.set_noob(E, base + off, 180.0, pz, dict(NF["shock"]), t)
        E.N.root.rotation_euler = (rot, -0.3 * rot, math.radians(180))


HYPE = {"both_h": 1.95, "both_w": 1.06, "m_o": 0.8, "m_w": 1.8, "m_up": 0.9, "m_r": 0.85, "m_vee": 0.3, "m_arch": -0.45}


def _seat_noob(E, pz, t, yaw_off=0.0):
    """The Noob astride the dragon: his hips on its shoulders, turned with it."""
    N = E.N
    D = E.D
    pz = dict(pz)
    pz.update({"hips_drop": 1.0})
    pz.setdefault("leg_sl", {"fwd": 70, "out": 28})
    pz.setdefault("leg_sr", {"fwd": 70, "out": 28})
    dyaw = math.degrees(D.root.rotation_euler.z)
    from ep09_new import NF
    s = N.root.scale.z
    seat = dragon_seat(E)
    M.set_noob(E, seat - Vector((0, 0, 1.0 * s)), dyaw + yaw_off, pz, pz.pop("_face", dict(NF["happy"])), t)
    rx, ry = D.root.rotation_euler.x, D.root.rotation_euler.y
    e = N.root.rotation_euler
    N.root.rotation_euler = (rx, ry, e[2])


def noob(E, t):
    from ep09_new import NF
    N = E.N
    face = dict(NF["happy"])
    pz = {"arm_sl": {"out": 8, "fwd": 4}, "arm_sr": {"out": 8, "fwd": 4}}
    _burst_reset(E)
    hidden = False
    if t < b("tear"):
        return _tumble(E, t, "noob")
    if t < b("drop") + 0.15:
        N.root.location = (0, 0, -500)
        return
    if t < b("drop") + 0.65:                                     # out first, landing on his feet
        u = ss(b("drop") + 0.15, b("drop") + 0.65, t)
        a = PORTAL + Vector((0.8, -0.3, 2.4))
        p = _arc(a, gp(E, NOOB_LAND), 0.6, u)
        pz.update({"arm_sl": {"fwd": 150, "out": 30}, "arm_sr": {"fwd": 150, "out": 30}, "leg_sl": {"fwd": 25}, "leg_sr": {"fwd": -15}})
        face = dict(NF["shock"])
        M.set_noob(E, p, 180.0 - 180 * u, pz, face, t)
        return
    p = gp(E, NOOB_LAND)
    if t < b("hide"):
        yaw = 15.0
        dt = t - (b("drop") + 0.65)
        bounce = abs(math.sin(dt * 6.0)) * 0.25 * math.exp(-dt * 1.5)
        face = dict(NF["awe"])
        pz.update({"arm_sl": {"fwd": 20, "out": 60}, "arm_sr": {"fwd": 20, "out": 60}})
        if b("burst") <= t < b("burst") + 1.0:                   # it bursts over them: he ducks
            k = ss(b("burst") + 0.2, b("burst") + 0.4, t) * (1 - ss(b("burst") + 0.8, b("burst") + 1.0, t))
            pz.update({"chest_lean": 35 * k, "arm_sl": {"fwd": 150 * k, "out": 20}, "arm_sr": {"fwd": 150 * k, "out": 20}})
            face = dict(NF["shock"])
        if t >= b("burst") + 1.0:
            tl, nd = _look(yaw, p, dragon_head(E), h=1.7)
            pz["head_turn"], pz["head_nod"] = tl, nd
            yaw = lerp(yaw, _face_to(p, dragon_head(E)), 0.5)
        if b("noob_boss") - 0.1 <= t < b("steve_hide"):            # BOSS FIGHT!
            k = ss(b("noob_boss") - 0.1, b("noob_boss") + 0.1, t)
            pz.update({"arm_sl": {"fwd": 10, "out": 160 * k}, "arm_sr": {"fwd": 10, "out": 160 * k}})
            bounce = abs(math.sin((t - b("noob_boss")) * 8.0)) * 0.3
            face = dict(HYPE)
        if t >= b("steve_hide"):
            tl, nd = _look(yaw, p, E.S.holder.location + Vector((0, 0, 1.4)), h=1.7)
            pz["head_turn"], pz["head_nod"] = tl, nd
            face = dict(NF["happy"]) if t < b("steve_hide") + 1.3 else dict(NF["confused"])
        pz = life(E, "noob", pz, face, t, 0.5)
        M.set_noob(E, p + Vector((0, 0, bounce)), yaw, pz, face, t)
        return
    if t < b("hide") + 1.25:
        u = (t - b("hide") - 0.05) / 1.2
        u = _clamp(u, 0, 1)
        a, c = gp(E, NOOB_LAND), gp(E, HIDE_N)
        p = a.lerp(c, u * u * (3 - 2 * u))
        for gx in (-3.5,):
            if abs(p.x - gx) < 0.9:
                p.z += 0.5 * math.cos((p.x - gx) / 0.9 * math.pi / 2)
        p.z = max(p.z, 0.0)
        _run(pz, t, b("hide"), 2.6, steve=False)
        M.set_noob(E, p, _face_to(a, c), pz, dict(NF["happy"]), t)
        return
    cry = Vector((CRY_X[1], CRY_Y, CRY_Z + 2.0))
    if t < b("noob_hi"):                                         # ducked, giggling
        p = gp(E, HIDE_N)
        pz.update({"chest_lean": 30, "head_nod": 10, "hips_drop": 0.25})
        M.set_noob(E, p, 190.0, life(E, "noob", pz, face, t, 0.7), face, t)
        return
    if t < b("panel"):                                            # "Hi! ...Hello?", the tap, "They're... frozen."
        p = gp(E, HIDE_N)
        up = ss(b("noob_hi") - 0.3, b("noob_hi") + 0.1, t)
        yaw = lerp(190.0, _face_to(p, cry) - 25, up)
        tl, nd = _look(yaw, p, cry, h=1.7)
        pz["head_turn"], pz["head_nod"] = tl * up, nd * up
        pz["chest_lean"] = 30 * (1 - up)
        wave = ss(b("noob_hi"), b("noob_hi") + 0.15, t) * (1 - ss(b("noob_hi") + 0.7, b("noob_hi") + 0.9, t))
        if wave > 0:
            pz["arm_sl"] = {"out": 150 * wave, "fwd": 10 + 15 * math.sin((t - b("noob_hi")) * 14)}
            face = dict(NF["happy"])
        if t >= b("noob_hi") + 0.8:
            face = dict(NF["confused"])
        tap = ss(b("tap") - 0.1, b("tap") + 0.15, t) * (1 - ss(b("tap", 1) - 0.1, b("noob_frozen") + 0.2, t))
        if tap > 0:
            k = math.exp(-((t - (b("tap") + 0.2)) / 0.06) ** 2) + math.exp(-((t - (b("tap") + 0.45)) / 0.06) ** 2)
            pz["arm_sr"] = {"fwd": (100 + 8 * k) * tap, "out": 8}
            face = dict(NF["confused"])
        if t >= b("noob_frozen") - 0.2:
            face = dict(NF["worried"])
            pz["head_turn"] = lerp(pz["head_turn"], _clamp(_wrap(_face_to(p, Vector(E.S.holder.location)) - yaw), -60, 60),
                                   ss(b("noob_frozen") + 0.9, b("steve_here"), t))
        pz = life(E, "noob", pz, face, t, 0.9)
        M.set_noob(E, p, yaw, pz, face, t)
        return
    if t < b("jump"):                                             # the hologram: "Tutorial says JUMP!", and off he goes
        p = gp(E, HIDE_N)
        yaw = _face_to(p, E.holo.location)
        tl, nd = _look(yaw, p, E.holo.location, h=1.7)
        pz["head_turn"], pz["head_nod"] = tl, nd
        face = dict(NF["awe"])
        if t >= b("noob_tut"):
            face = dict(HYPE)
            k = ss(b("noob_tut"), b("noob_tut") + 0.2, t)
            pz["arm_sl"] = {"fwd": 150 * k, "out": 10}
            p = p + Vector((0, 0, abs(math.sin((t - b("noob_tut")) * 7)) * 0.2))
        if t >= b("steve_dont") - 0.15:                            # he runs for the edge
            u = ss(b("steve_dont") - 0.15, b("jump") + 0.02, t)
            p = gp(E, HIDE_N).lerp(gp(E, EDGE_N), u)
            yaw = _face_to(gp(E, HIDE_N), gp(E, EDGE_N))
            _run(pz, t, b("steve_dont"), 2.8, steve=False)
        pz = life(E, "noob", pz, face, t, 1.1)
        M.set_noob(E, p, yaw, pz, face, t)
        return
    if t < b("kill"):                                              # the leap at the boss
        u = (t - b("jump")) / (b("kill") - b("jump"))
        a = gp(E, EDGE_N)
        c = Vector((-6.6, -5.6, 1.6))
        p = _arc(a, c, 2.2, u * 0.9)
        pz.update({"arm_sl": {"fwd": 160, "out": 20}, "arm_sr": {"fwd": 150, "out": 30}, "leg_sl": {"fwd": 30}, "leg_sr": {"fwd": -25}})
        M.set_noob(E, p, _face_to(a, c), pz, dict(HYPE), t)
        return
    if t < b("respawn"):                                           # swept through: he bursts
        a = gp(E, EDGE_N)
        c = Vector((-6.6, -5.6, 1.6))
        p = _arc(a, c, 2.2, 0.9)
        M.set_noob(E, p, _face_to(a, c), {"arm_sl": {"fwd": 160}, "arm_sr": {"fwd": 150}}, dict(NF["shock"]), t)
        _burst_apply(E, t - b("kill"))
        return
    if t < b("noob_again") + 0.6:                                   # the checkpoint
        p = gp(E, CP_SPOT)
        pop = ss(b("respawn") + 0.1, b("respawn") + 0.3, t)
        yaw = -60.0
        face = dict(NF["happy"])
        if t < b("respawn") + 0.1:
            N.root.location = (0, 0, -500)
            return
        if t >= b("noob_cp") - 0.1 and t < b("wheel"):             # "Checkpoint!!"
            k = ss(b("noob_cp") - 0.1, b("noob_cp") + 0.1, t)
            pz.update({"arm_sl": {"fwd": 10, "out": 160 * k}, "arm_sr": {"fwd": 10, "out": 160 * k}})
            p = p + Vector((0, 0, abs(math.sin((t - b("noob_cp")) * 7.5)) * 0.3))
            face = dict(HYPE)
        if t >= b("wheel"):
            tgt = E.S.holder.location + Vector((0, 0, 1.5))
            yaw = _face_to(p, tgt)
            tl, nd = _look(yaw, p, dragon_head(E), h=1.7)
            k = ss(b("build"), b("build") + 0.6, t)
            pz["head_turn"], pz["head_nod"] = tl * k, nd * k
            face = dict(NF["awe"]) if t < b("crash") else dict(NF["shock"])
        if t >= b("noob_again") - 0.1:                              # "ROUND TWO!": he crouches to spring
            k = ss(b("noob_again") - 0.1, b("noob_again") + 0.3, t)
            yaw = -80.0
            pz.update({"chest_lean": 25 * k, "arm_sl": {"fwd": -40 * k, "out": 10}, "arm_sr": {"fwd": -40 * k, "out": 10}, "hips_drop": 0.2 * k})
            p = p.lerp(gp(E, CP_EDGE), ss(b("noob_again") - 0.1, b("noob_again") + 0.5, t))
            face = dict(HYPE)
        s0 = getattr(E, "noob_scale0", N.root.scale[0])
        pz = life(E, "noob", pz, face, t, 1.4)
        M.set_noob(E, p, yaw, pz, face, t)
        N.root.scale = (s0 * (0.2 + 0.8 * pop),) * 3
        return
    land = b("leap") + 0.75
    if t < land:                                                   # the blind jump: up, and down onto its back
        t0 = b("noob_again") + 0.6
        u = (t - t0) / (land - t0)
        a = gp(E, CP_EDGE)
        bpy.context.view_layer.update()
        s = N.root.scale.z
        c = _seat_at(E, land) - Vector((0, 0, 1.0 * s))
        p = _arc(a, c, 2.0, u)
        pz.update({"arm_sl": {"fwd": 170, "out": 25}, "arm_sr": {"fwd": 165, "out": 30}, "leg_sl": {"fwd": 35}, "leg_sr": {"fwd": -20},
                   "hips_drop": 1.0 * ss(0.75, 1.0, u)})
        M.set_noob(E, p, -95.0, pz, dict(HYPE), t)
        return
    # on its back from here
    dt = t - land
    face = dict(NF["shock"]) if dt < 0.4 else dict(NF["happy"])
    pz["chest_lean"] = 20 * math.exp(-dt * 4)
    pz["arm_sl"] = {"fwd": 60, "out": 30}
    pz["arm_sr"] = {"fwd": 60, "out": 30}
    if b("noob_done") - 0.1 <= t < b("ride"):                       # "Tutorial complete!"
        k = ss(b("noob_done") - 0.1, b("noob_done") + 0.1, t) * (1 - ss(b("noob_done", 1), b("ride"), t))
        pz["arm_sl"] = {"fwd": 10, "out": 60 + 100 * k}
        pz["arm_sr"] = {"fwd": 10, "out": 60 + 100 * k}
        face = dict(HYPE)
    if b("ride") <= t < b("free", 1):                              # clinging on
        pz.update({"chest_lean": 40, "arm_sl": {"fwd": 75, "out": 12}, "arm_sr": {"fwd": 75, "out": 12}, "head_nod": -10})
        face = dict(NF["shock"]) if t < b("free") + 1.5 else dict(NF["awe"])
    if b("free", 1) <= t < b("noob_planwall"):                      # he waves to the freed players
        k = ss(b("thanks") + 0.2, b("thanks") + 0.4, t) * (1 - ss(b("thanks", 1), b("thanks", 1) + 0.3, t))
        pz["arm_sl"] = {"out": 60 + 90 * k, "fwd": 10 + 12 * math.sin(t * 12) * k}
        face = dict(NF["happy"])
    if b("noob_planwall") <= t < b("bank"):                         # "Your plan was a wall." to Steve below, a point
        k = ss(b("noob_planwall") + 0.1, b("noob_planwall") + 0.3, t) * (1 - ss(b("noob_planwall") + 0.9, b("noob_planwall", 1), t))
        pz["arm_sr"] = {"fwd": 70 + 20 * k, "out": 10}
        pz["arm_sl"] = {"fwd": 50, "out": 20}
        pz["head_nod"] = 18
        pz["head_turn"] = -25
        face = dict(NF["happy"])
    if b("bank") <= t < b("freeze"):                                # holding on through the bank, laughing
        pz.update({"chest_lean": 30, "arm_sl": {"fwd": 75, "out": 15}, "arm_sr": {"fwd": 30, "out": 120}})
        face = dict(NF["happy"])
    if t >= b("freeze"):
        jolt = math.exp(-((t - (b("freeze") + 0.15)) / 0.08) ** 2) + math.exp(-((t - (b("freeze") + 0.32)) / 0.06) ** 2)
        pz.update({"chest_lean": 30 + 12 * jolt, "arm_sl": {"fwd": 75, "out": 15}, "arm_sr": {"fwd": 75, "out": 15}})
        look = ss(b("freeze") + 0.6, b("freeze") + 1.0, t)
        pz["head_turn"] = 35 * math.sin((t - b("freeze")) * 2.0) * look * (1 - ss(b("freeze") + 1.5, b("freeze", 1), t))
        face = dict(NF["confused"])
        if t >= b("freeze") + 1.4:
            return _crawl(E, t, pz)
    pz["_face"] = face
    pz = life(E, "noob", pz, face, t, 1.6)
    pz["_face"] = face
    _seat_noob(E, pz, t)


def _seat_at(E, t):
    """The seat's position at a time (the dragon posed at that time, then put back)."""
    keep = getattr(E, "_t_now", t)
    dragon(E, t)
    s = dragon_seat(E)
    dragon(E, keep)
    return s


def _crawl(E, t, pz):
    """After the freeze he crawls up its neck and waves a hand in front of its eye."""
    from ep09_new import NF
    N, D = E.N, E.D
    u = ss(b("freeze") + 1.4, b("wave") + 0.1, t)
    seat = dragon_seat(E)
    neck_top = D.neck[2].matrix_world @ Vector((0, 0, 0.36))
    p = seat.lerp(neck_top, u)
    dyaw = math.degrees(D.root.rotation_euler.z)
    lie = 70 * u
    ph = (t - b("freeze")) * 5.0
    pz = {"arm_sl": {"fwd": 150 + 25 * math.sin(ph) * (u < 1), "out": 15}, "arm_sr": {"fwd": 150 - 25 * math.sin(ph) * (u < 1), "out": 15},
          "leg_sl": {"fwd": 20}, "leg_sr": {"fwd": 20}, "head_nod": -60 * u}
    face = dict(NF["confused"])
    if t >= b("wave"):                                               # the wave in front of its eye
        k = ss(b("wave"), b("wave") + 0.15, t)
        pz["arm_sr"] = {"fwd": 120, "out": 50 + 25 * math.sin((t - b("wave")) * 16) * (t < b("noob_lag")), "twist": 20}
        pz["head_nod"] = -60 + 20 * k
        pz["head_turn"] = 30 * k
        face = dict(NF["confused"])
    if t >= b("noob_lag"):                                           # "...Is it lagging?" down to Steve
        pz["head_turn"] = 55
        pz["head_nod"] = -25
        face = dict(NF["worried"])
    s = N.root.scale.z
    M.set_noob(E, p - Vector((0, 0, 0.35 * s)), dyaw, pz, face, t)
    N.root.rotation_euler = (math.radians(lie) + D.root.rotation_euler.x, D.root.rotation_euler.y, N.root.rotation_euler[2])


def _burst_reset(E):
    if not hasattr(E, "noob_scale0"):
        E.noob_scale0 = E.N.root.scale[0]
    E.N.root.scale = (E.noob_scale0,) * 3
    for k, o in E.burst_parts.items():
        loc, mode, q = E.burst_home[k]
        o.location = loc
        o.rotation_quaternion = Quaternion(q)
    E.dark_cube.location = (0, 0, -300)
    for ob in E.N.root.children_recursive:
        ob.hide_render = False


def _burst_apply(E, dt):
    if dt < 0:
        return
    bpy.context.view_layer.update()
    for name, o in E.burst_parts.items():
        loc, mode, q = E.burst_home[name]
        par = o.parent.matrix_world if o.parent else Matrix()
        inv = par.inverted().to_3x3()
        w = E.burst_v[name]
        dw = Vector((w.x * dt, w.y * dt, w.z * dt - 0.5 * 9.81 * dt * dt))
        o.location = loc + inv @ dw
        o.rotation_quaternion = Quaternion(q) @ Quaternion(Vector((1, 0.4, 0.2)).normalized(), 9.0 * dt * (1 if name < "n" else -1))
    hide = dt > 0.6
    for ob in E.N.root.children_recursive:
        ob.hide_render = hide
    c = Vector(E.N.root.location) + Vector((0, 0, 1.2))
    if dt < 0.75:
        E.dark_cube.location = c + Vector((-0.3, 0, 0.1 * dt - 0.4 * dt * dt))
        E.dark_cube.rotation_euler = (dt * 2, dt * 3.5, dt * 1.5)
        s = min(1.0, dt / 0.06) * (1 - ss(0.55, 0.75, dt))
        E.dark_cube.scale = (s, s, s)


WEST = [(-10.0, 0.0), (-11.8, 0.0), (-14.2, 0.5), (-16.6, 1.0), (-19.0, 1.5), (-22.0, 2.0)]   # the stones west of the terrace


def _west_z(x):
    """The freed players' way west: the terrace, then a hop to each stepping stone."""
    if x >= WEST[0][0]:
        return 0.0
    for (x0, z0), (x1, z1) in zip(WEST, WEST[1:]):
        if x1 <= x <= x0:
            u = (x0 - x) / (x0 - x1)
            return lerp(z0, z1, u) + 0.7 * math.sin(math.pi * u)
    return WEST[-1][1]


def respawn_fx(E, t):
    a = b("respawn")
    if not (a <= t < a + 0.7):
        E.beam.location = (0, 0, -300)
        return
    u = (t - a) / 0.7
    E.beam.location = gp(E, CP_SPOT) + Vector((0, 0, 1.4))
    E.beam.scale = (0.9 * (1 - 0.6 * u), 0.9 * (1 - 0.6 * u), 3.0)
    E.beam_mix.inputs[0].default_value = 0.7 * math.sin(math.pi * u)


def players(E, t):
    """Frozen mid-run in the crystals; freed (tumbling out, up, looking round), they wave and run off west."""
    hits = [b("free") + 0.05 + 0.45 * k for k in range(4)]
    from ep09_new import NF
    for k, P in enumerate(E.players):
        home = Vector((CRY_X[k], CRY_Y, CRY_Z))
        frozen = {"arm_sl": {"fwd": 70 + 15 * k, "out": 10}, "arm_sr": {"fwd": -40, "out": 10}, "leg_sl": {"fwd": 30}, "leg_sr": {"fwd": -25},
                  "chest_lean": 8, "head_turn": 10 * (k - 1.5)}
        if t < hits[k]:
            M.set_noob(E, home, 180.0 + 12 * (k - 1.5), frozen, {}, t, N=P)
            continue
        dt = t - hits[k]
        floor = Vector((CRY_X[k] + 0.2, 1.3, 0.0))
        if dt < 0.55:                                              # tumbling off the ledge
            u = dt / 0.55
            p = _arc(home, floor, 0.5, u)
            pz = {"arm_sl": {"fwd": 150, "out": 40}, "arm_sr": {"fwd": 140, "out": 40}, "chest_lean": 40 * u}
            M.set_noob(E, p, 180.0, pz, {}, t, N=P)
            P.root.rotation_euler = (math.radians(-50 * math.sin(math.pi * u)), 0, P.root.rotation_euler[2])
            continue
        wave_t = b("thanks") + 0.1 * k
        run_t = b("thanks") + 0.8 + 0.12 * k
        if t < run_t:
            look = ss(hits[k] + 0.6, hits[k] + 1.2, t)
            yaw = 180.0 + 50 * math.sin((t - hits[k]) * 1.5 + k) * look * (1 - ss(wave_t - 0.3, wave_t, t))
            yaw = lerp(yaw, _face_to(floor, gp(E, STEVE_PLAN)), ss(wave_t - 0.3, wave_t, t))
            w = ss(wave_t, wave_t + 0.15, t)
            pz = {"arm_sl": {"out": 150 * w, "fwd": 10 + 15 * math.sin(t * 13 + k) * w}, "arm_sr": {"out": 8}}
            M.set_noob(E, floor, yaw, pz, {}, t, N=P)
            continue
        u = (t - run_t)
        a = floor
        c = Vector((-22.0, -1.0 + 0.8 * k, 0.0))
        p = a + (c - a).normalized() * min((c - a).length, 4.5 * u)
        p.z = _west_z(p.x)
        pz = {}
        _run(pz, t, run_t, 2.8, steve=False)
        M.set_noob(E, p, _face_to(a, c), pz, {}, t, N=P)


# ------------------------------------------------------------------ one frame
def apply(E, t):
    E._t_now = t
    name, t0, t1 = which(t)
    tc = t
    hs = b("crash") + 0.1                                     # the impact's hit-stop: two frames held
    if hs <= t < hs + 2.0 / FPS:
        t = hs
    E._t_now = t
    light(E, t)
    tunnel(E, t)
    portal(E, t)
    ahead(E, t)
    hologram(E, t)
    dragon(E, t)
    wall(E, t)
    crystals(E, t)
    ledge(E, t)
    respawn_fx(E, t)
    players(E, t)
    steve(E, t)
    noob(E, t)
    camera(E, tc, name, t0, t1)
    E2.set_wash(E, 0.9 * (1 - ss(0.0, 0.45, tc)))      # Episode 2 cut on the flare: it clears into the swirl


# ------------------------------------------------------------------ the camera
def camera(E, t, shot, t0, t1):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    loc, look, lens, fstop, focus, shake = _cam(E, t, shot, t0, t1)
    hs = b("crash") + 0.1
    shake += 1.6 * math.exp(-max(0.0, t - hs) * 6) * (t >= hs) + 1.0 * math.exp(-max(0.0, t - (b("burst") + 0.6)) * 4) * (b("burst") + 0.4 <= t < b("noob_boss"))
    if b("freeze") <= t < b("glitch"):
        shake = 0.0                                          # nothing moves in the freeze: not even the camera
    y1, p1, r1 = handheld(t if t < b("freeze") else b("freeze"), shake)
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = M.P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.data.lens = lens
    E.cam.data.dof.use_dof = fstop < 30
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    # the key from the camera's side, a little above, aimed at the characters (never at the sky)
    tgt = look
    if shot not in ("tunnel",):
        S_ = Vector(E.S.holder.location)
        N_ = Vector(E.N.root.location)
        near = [v for v in (S_, N_) if v.z > -100 and (v - loc).length < 25]
        if near:
            tgt = sum(near, Vector()) / len(near) + Vector((0, 0, 1.3))
    E.key.location = loc + (tgt - loc) * 0.3 + Vector((0.5, 0, 1.4))
    E.key.rotation_euler = (tgt - E.key.location).to_track_quat("-Z", "Y").to_euler()
    E.key.data.energy = 0.0 if shot == "tunnel" else 260.0


def _neck_side(E, lens, toward_noob=False, dist=4.6):
    """From the dragon's side (the side toward the cameras' south): its head and the Noob on its neck together."""
    D = E.D
    hd = dragon_head(E)
    nk = D.neck[2].matrix_world.translation
    mid = hd.lerp(nk, 0.45)
    yw = D.root.rotation_euler.z
    fw = Vector((math.sin(yw), -math.cos(yw), 0))
    side = Vector((fw.y, -fw.x, 0))
    if side.y > 0:
        side = -side
    loc = mid + side * dist + fw * 0.8 + Vector((0, 0, 0.7))
    look = mid + Vector((0, 0, 0.35))
    if toward_noob:
        look = look.lerp(Vector(E.N.root.location) + Vector((0, 0, 0.5)), 0.5)
    return loc, look, lens, 4.0, None, 0.0


def _c(x, y, z):
    return Vector((x, y, z))


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus or None, handheld)"""
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, t0 + 3, t)
    S_ = Vector(E.S.holder.location)
    N_ = Vector(E.N.root.location)
    if shot == "tunnel":
        base = Vector((0, -2000, 500))
        return base + _c(0, 4.0 + 0.5 * t, 0), base + _c(0, 30, 0), 22, 30, None, 0.6
    if shot == "arrive":                                     # wide: the pad, the sky, the portal tearing open over it
        loc = _c(6.5, -13.5, 3.2) + _c(-0.4, 0.6, 0) * u
        return loc, _c(-0.5, 2.0, 4.0), 20, 30, None, 0.3
    if shot == "burst":                                      # low behind the pad's front: they land, it blasts out over them
        loc = _c(-4.6, -8.2, 1.2)
        look = _c(0.0, 0.8, 3.2).lerp(_c(5.0, -3.0, 5.0), ss(b("burst") + 0.6, b("burst") + 1.5, t))
        return loc, look, 18, 30, None, 0.4
    if shot == "boss":                                       # the Noob, thrilled, the dragon off in the sky behind the camera
        loc = gp(E, NOOB_LAND) + _c(1.2, -2.6, 1.3)
        return loc, gp(E, NOOB_LAND) + _c(0, 0, 1.55), 38, 2.8, None, 0.35
    if shot == "hide_line":                                  # Steve getting up, the portal behind him
        loc = gp(E, STEVE_LAND) + _c(-1.7, -3.0, 1.3)
        return loc, gp(E, STEVE_LAND) + _c(0, 0.3, 1.35), 36, 2.8, None, 0.35
    if shot == "hide":                                       # wide from the south-west: the run, the ledge, the crystals
        loc = _c(-3.0, -9.5, 2.6)
        return loc, _c(-4.5, 1.0, 1.8) + _c(0, 0, 1.5) * ss(b("hide") + 0.7, b("hide") + 1.3, t), 22, 30, None, 0.35
    if shot == "hi":                                         # the Noob, the frozen player above him
        loc = _c(-7.05, 2.32, 3.0)                         # from the ledge, beside the frozen player he greets
        return loc, gp(E, HIDE_N) + _c(0, 0, 1.6), 30, 3.2, None, 0.2
    if shot == "tap":                                        # close: his hand on the crystal, the face inside
        loc = _c(-5.75, 1.55, 2.45)
        return loc, _c(CRY_X[1] + 0.1, CRY_Y - 0.45, 2.35), 40, 2.4, None, 0.2
    if shot == "frozen":                                     # his uneasy face
        loc = _c(-7.25, 2.3, 2.55)
        return loc, gp(E, HIDE_N) + _c(0, 0, 1.65), 45, 2.4, None, 0.2
    if shot == "here":                                       # Steve, grim, the crystals behind him
        loc = gp(E, HIDE_S) + _c(1.4, -2.3, 1.55)
        return loc, gp(E, HIDE_S) + _c(-0.2, 0.2, 1.55), 42, 2.6, None, 0.25
    if shot == "panel":                                      # low behind them: the hologram over the course, the dragon
        loc = _c(-9.3, 2.05, 2.2)                          # over his shoulder: he looks up at the panel over the course
        return loc, _c(-5.4, -6.0, 5.6), 18, 30, None, 0.3
    if shot == "tut":                                        # the Noob, pointing up at it
        loc = gp(E, HIDE_N) + _c(1.2, -2.4, 1.0)
        return loc, gp(E, HIDE_N) + _c(0, 0, 1.75), 32, 3.0, None, 0.3
    if shot == "dont":                                       # Steve: DON'T!, the Noob already running at the edge
        loc = gp(E, HIDE_S) + _c(2.2, -2.8, 1.5)
        return loc, gp(E, HIDE_S) + _c(-1.2, -0.6, 1.4), 26, 4.0, None, 0.35
    if shot == "jump":                                       # side on, wide: the leap, the sweep, the burst
        loc = _c(-9.5, -17.5, 2.5)
        return loc, _c(-6.5, -5.0, 2.8), 24, 30, None, 0.35
    if shot == "respawn":                                    # the checkpoint: the pop, "Checkpoint!!"
        loc = gp(E, CP_SPOT) + _c(-1.2, -3.6, 1.1)
        return loc, gp(E, CP_SPOT) + _c(0.1, 0, 1.3), 30, 3.2, None, 0.25
    if shot == "wheel":                                      # wide from the south: Steve running east, the dragon coming round behind
        loc = _c(-2.5, -15.0, 3.0)
        return loc, _c(-6.0, -0.5, 3.0).lerp(_c(-3.0, -0.5, 2.5), u), 20, 30, None, 0.35
    if shot == "wall_line":                                  # Steve: "Plan: wall."
        loc = gp(E, STEVE_WALL) + _c(-1.15, -2.6, 1.45)
        return loc, gp(E, STEVE_WALL) + _c(-0.4, 0, 1.45), 36, 2.8, None, 0.3
    if shot == "build":                                      # from the south, the wall in profile, the dragon closing in from the left
        loc = _c(0.8, -9.0, 1.6)
        return loc, _c(-3.0, -0.3, 1.8), 22, 30, None, 0.3
    if shot == "crash":                                      # low, close: the snout through the wall, Steve flat
        loc = _c(2.6, -6.4, 0.7)
        return loc, _c(-1.0, -0.6, 1.4).lerp(_c(1.5, -0.6, 1.8), ss(b("crash") + 0.3, b("crash", 1), t)), 20, 30, None, 0.3
    if shot == "again":                                      # the checkpoint from the south-west: his blind jump, it coming in low
        loc = _c(7.5, -10.5, 1.8)
        return loc, _c(5.0, -0.8, 2.4), 26, 30, None, 0.3
    if shot == "done":                                       # riding: alongside, a little ahead
        hd = dragon_seat(E)
        return hd + _c(0.5, -5.5, 0.8), hd + _c(0, 0, 0.6), 30, 4.0, None, 0.5
    if shot == "ride":                                       # the chase camera behind and above
        sd = dragon_seat(E)
        v = _dragon_pos(E, t + 0.1) - _dragon_pos(E, t - 0.1)
        v = Vector((v.x, v.y, 0)).normalized() if v.length > 0.01 else Vector((1, 0, 0))
        return sd - v * 6.5 + _c(0, 0, 2.5), sd + v * 4.0, 24, 30, None, 0.6
    if shot == "free":                                       # the ledge from the south: the crystals bursting one by one
        loc = _c(-6.0, -6.8, 2.3)
        return loc, _c(-7.0, 2.4, 2.4), 22, 30, None, 0.4
    if shot == "thanks":                                     # the freed players waving, running off
        loc = _c(-5.0, -4.2, 1.5)
        return loc, _c(-8.0, 1.2, 1.3), 26, 30, None, 0.3
    if shot == "myplan":                                     # Steve, deadpan; the broken ledge behind him
        loc = gp(E, STEVE_PLAN) + _c(1.9, -2.6, 1.5)
        return loc, gp(E, STEVE_PLAN) + _c(-0.2, 0.2, 1.5), 38, 2.8, None, 0.25
    if shot == "planwall":                                   # the Noob on the hovering dragon, from below
        sd = dragon_seat(E)
        yw = E.D.root.rotation_euler.z
        fw = Vector((math.sin(yw), -math.cos(yw), 0))         # its heading (yaw 0 faces -y)
        left = Vector((fw.y, -fw.x, 0))
        if left.y > 0:
            left = -left
        return sd + left * 4.6 + fw * 4.6 + _c(0, 0, 0.9), sd + _c(0, 0, 1.0), 30, 4.0, None, 0.3
    if shot == "bank":                                       # wide and low: it banks round over them, mid-roar
        loc = _c(-1.0, -13.0, 1.4)
        return loc, _c(-0.5, -3.0, 3.5), 20, 30, None, 0.4
    if shot in ("freeze", "wave"):                           # the same wide: it locks mid-flap, the cobblestones hanging
        loc = _c(1.5, -17.5, 2.0)
        look = _c(-1.5, 0.5, 4.2)
        if shot == "wave":
            return _neck_side(E, 32)
        return loc, look, 28, 30, None, 0.0
    if shot == "lag":                                        # the Noob on its neck: "...Is it lagging?"
        return _neck_side(E, 36, toward_noob=True)
    if shot in ("look", "lagline"):                          # Steve turns and looks up at it; it hangs over him
        p = gp(E, STEVE_PLAN)
        c = p + _c(-2.6, -2.7, 0.85)
        return c, p + _c(-0.9, 1.0, 2.4), 24, 4.0, (p + _c(0, 0, 1.6) - c).length, 0.0
    if shot == "glitch":                                     # the frozen dragon, flickering, the Noob on its neck
        loc, look, lens, f, fo, sh = _neck_side(E, 26, dist=8.5)
        return loc, look, lens, 30, None, 0.0
    return _c(0, -12, 3), _c(0, 0, 2), 24, 30, None, 0.3


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
    E.cuts = sorted(t0 for _, t0 in shot_bounds()) + [b("crash") + 0.1]
    M._render(E, frames, out, apply, M.finish_forest)


if __name__ == "__main__":
    main()
