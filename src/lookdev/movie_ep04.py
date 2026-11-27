"""The movie, chapter 4 ("This Block Shouldn't Exist"), in the new look and in 16:9.

The creator's notes (2026-11-26, story/movie/ep04_shots.md): it picks up Episode 3 v3's last frame (the frozen
dragon over the obby's spawn pad, the Noob on its neck, Steve below, the portal flickering, the kicked cobblestones
hanging, REALITY 92%). One last missing-texture shudder: a glitching cube rips out of the dragon's chest and drops
onto the blue terrace, the jolt flings the Noob down after it (a spawn ring lights under him: a new checkpoint);
the glitch crystal that held the frozen players seals the dragon where it hangs. The Noob touches the cube twice:
each time he bursts, respawns, and a tether from the spawn ring feeds the cube, which swells (0.45 -> 0.85 ->
1.45 m) while REALITY drops (92 -> 89 -> 85). Patch squeezes out of the portal, stops between the Noob's fist and
the cube, scans it from the front right; then turns to the Noob: "Wait. I know you." The twist in silence.
Sound and timing: episodes/movie_ep04_the_block.json (movie/ep04).

    python src/lookdev/movie_ep04.py TIMELINE VOICE TEX_DIR ASSETS OUT_DIR [--times 1.0,5.0] [--res 720]
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
import movie_ep00 as M                                                # noqa: E402
import movie_ep02 as E2                                               # noqa: E402
import movie_ep03 as E3                                               # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402

B = M.B
_yaw, _wrap, _clamp, _cr = E2._yaw, E2._wrap, E2._clamp, E2._cr
life = E2.life
gp = E3.gp
_face_to, _look, _run, _lie = E3._face_to, E3._look, E3._run, E3._lie
EP3_TL = os.path.join(HERE, "..", "..", "movie", "ep03_v3", "timeline.json")

# ------------------------------------------------------------------ the place (Ep3's obby; metres, z up)
RING = Vector((-6.9, 0.2, 0.0))          # the spawn ring on the blue terrace (centre back)
CUBE = Vector((-4.85, -1.55, 0.0))       # the cube, the terrace's front right corner
SIZES = (0.45, 0.85, 1.45)               # its size: dropped, after touch 1, after touch 2
HOVER = 0.15                             # its bottom above the terrace
N_LOOK = Vector((-5.75, -1.0, 0.0))      # the Noob crouching to it ("A secret block!")
POKE_N = Vector((-5.42, -1.2, 0.0))      # stepping in to poke
CHOP_N = Vector((-5.78, -1.32, 0.0))     # the karate chop (it is 0.85 m now)
WIND_N = Vector((-6.5, -1.15, 0.0))      # the third swing, wound up (1.45 m now)
REACT_N = Vector((-6.95, -0.8, 0.0))     # he hops back from Patch
STEVE_EDGE = Vector((-2.55, -1.0, 0.0))  # Steve at the grey pad's west edge, across the 1 m gap
STEVE_BACK = Vector((-2.1, -1.3, 0.0))   # his half step back when Patch appears
P_OUT = Vector((-1.6, 4.3, 3.3))         # Patch, just out of the portal's membrane (y 4.6, facing -y)
P_STOP = Vector((-5.98, -1.2, 1.55))     # between the fist and the cube
P_SCAN = Vector((-4.25, -3.3, 1.6))      # the front right of the cube: a clear line to it
P_TWIST = Vector((-5.45, -3.0, 1.85))     # drifting closer to the Noob


def b(name, i=0):
    return B[name][i]


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    E = E3.build(tl, tex_dir, assets, res, samples)
    E.B4 = {k: tuple(v) for k, v in tl["beats"].items()}
    E.B3 = {k: tuple(v) for k, v in json.load(open(EP3_TL))["beats"].items()}
    E.T3 = json.load(open(EP3_TL))["length"]
    _cube_block(E)
    _ring(E)
    _tether(E)
    _sparks(E)
    _shock(E)
    _patch(E)
    _warp(E)
    _bars(E)
    E.prepped = False
    return E


def _emission(name, rgb, strength, alpha=True):
    return E3._emit_mat(name, rgb, strength)


def _cube_block(E):
    """The glitch block: the missing texture (magenta and black checks, four a face whatever its size) glowing more as
    it grows, a magenta rim, the checks stepping now and then (live corrupted code); a pink light inside."""
    m = bpy.data.materials.new("glitch_block")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Color1"].default_value = (1.0, 0.0, 0.85, 1)
    ck.inputs["Color2"].default_value = (0.01, 0.0, 0.01, 1)
    ck.inputs["Scale"].default_value = 4.0
    nt.links.new(mp.outputs["Vector"], ck.inputs["Vector"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    rim = nt.nodes.new("ShaderNodeMix")
    rim.data_type = "RGBA"
    rim.blend_type = "ADD"
    nt.links.new(lw.outputs["Fresnel"], rim.inputs[0])
    nt.links.new(ck.outputs["Color"], rim.inputs[6])
    rim.inputs[7].default_value = (1.0, 0.25, 0.9, 1)
    nt.links.new(ck.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(rim.outputs[2], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 0.6
    bs.inputs["Roughness"].default_value = 0.55
    E.blk_emit = bs.inputs["Emission Strength"]
    E.blk_map = mp
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = "glitch_block"
    bv = ob.modifiers.new("bevel", "BEVEL")
    bv.width = 0.015
    bv.segments = 2
    ob.data.materials.append(m)
    ob.location = (0, 0, -300)
    E.blk = ob
    L = bpy.data.lights.new("blk_light", "POINT")
    L.color = (1.0, 0.2, 0.85)
    L.shadow_soft_size = 0.3
    lo = bpy.data.objects.new("blk_light", L)
    E.sc.collection.objects.link(lo)
    lo.location = (0, 0, -300)
    E.blk_light = lo


def _ring(E):
    """A round spawn pad (white, a cyan neon ring): it lights when the Noob lands on it, like a checkpoint."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.95, depth=0.06)
    pad = bpy.context.active_object
    pad.name = "spawn_ring_pad"
    pm = bpy.data.materials.new("ring_pad")
    pm.use_nodes = True
    pb = pm.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0.85, 0.87, 0.9, 1)
    pb.inputs["Roughness"].default_value = 0.5
    pad.data.materials.append(pm)
    pad.location = RING + Vector((0, 0, 0.03))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.82, minor_radius=0.045, major_segments=64, minor_segments=8)
    tor = bpy.context.active_object
    tor.name = "spawn_ring_neon"
    m = bpy.data.materials.new("ring_neon")
    m.use_nodes = True
    nb = m.node_tree.nodes["Principled BSDF"]
    nb.inputs["Base Color"].default_value = (0.1, 0.9, 1.0, 1)
    nb.inputs["Emission Color"].default_value = (0.1, 0.9, 1.0, 1)
    nb.inputs["Emission Strength"].default_value = 0.0
    tor.data.materials.append(m)
    tor.location = RING + Vector((0, 0, 0.07))
    E.ring_emit = nb.inputs["Emission Strength"]
    E.ring_pad, E.ring_neon = pad, tor


def _tether(E):
    """The respawn drawn into the cube: a glowing arc from the ring to it, magenta and cyan bands running along."""
    cu = bpy.data.curves.new("tether", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.04
    cu.bevel_resolution = 3
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(1)
    ob = bpy.data.objects.new("tether", cu)
    E.sc.collection.objects.link(ob)
    m = bpy.data.materials.new("tether")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 6.0
    wv.inputs["Distortion"].default_value = 3.0
    nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (1.0, 0.1, 0.85, 1)
    ramp.color_ramp.elements[1].color = (0.15, 0.95, 1.0, 1)
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 3.0
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    cu.materials.append(m)
    ob.visible_shadow = False
    ob.hide_render = True
    E.teth, E.teth_map, E.teth_em = ob, mp, em


def _sparks(E):
    m, mx, em = E3._emit_mat("spark", (1.0, 0.15, 0.85), 12.0)
    rnd = random.Random(21)
    E.sparks = []
    for k in range(22):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"spark_{k}"
        s = rnd.uniform(0.04, 0.09)
        ob.scale = (s, s, s)
        ob.data.materials.append(m)
        ob.visible_shadow = False
        ob.location = (0, 0, -300)
        v = Vector((rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(-1.0, 3.5)))
        E.sparks.append((ob, v, rnd.uniform(0.35, 0.8)))


def _shock(E):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=64, minor_segments=6)
    ob = bpy.context.active_object
    ob.name = "shockwave"
    m, mx, em = E3._emit_mat("shock", (1.0, 0.3, 0.9), 8.0)
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ob.location = (0, 0, -300)
    E.shock, E.shock_mix = ob, mx


def _patch(E):
    from patch import build_patch
    E.PA = build_patch(E.sc.collection, size=0.42, name="patch")
    E.PA.root.location = (0, 0, -300)
    L = bpy.data.lights.new("patch_screen", "AREA")              # the screen's glow on what it faces
    L.energy, L.color, L.size = 12.0, (0.1, 0.8, 1.0), 0.3
    lo = bpy.data.objects.new("patch_screen", L)
    E.sc.collection.objects.link(lo)
    lo.parent = E.PA.root
    lo.location = (0, -0.32, 0.0)
    lo.rotation_euler = (math.radians(90), 0, 0)                 # facing -y, with the screen
    E.PA.glow = lo


def _warp(E):
    """Where Patch squeezes out of the portal: a cyan disc of light on the membrane and pixels rushing in."""
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=1.0, fill_type="NGON")
    ob = bpy.context.active_object
    ob.name = "warp_disc"
    ob.rotation_euler = (math.radians(90), 0, 0)
    m, mx, em = E3._emit_mat("warp", (0.2, 0.85, 1.0), 10.0)
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ob.location = (0, 0, -300)
    E.warp, E.warp_mix = ob, mx
    rnd = random.Random(33)
    E.pix = []
    m2, _, _ = E3._emit_mat("warp_pix", (0.3, 0.95, 1.0), 10.0)
    for k in range(14):
        bpy.ops.mesh.primitive_cube_add(size=0.07)
        p = bpy.context.active_object
        p.name = f"warp_pix_{k}"
        p.data.materials.append(m2)
        p.visible_shadow = False
        p.location = (0, 0, -300)
        a = rnd.uniform(0, 2 * math.pi)
        E.pix.append((p, Vector((math.cos(a), 0, math.sin(a))) * rnd.uniform(0.7, 1.6)))


def _bars(E):
    """Patch's scan read-out beside the cube: three small bars of light, flickering."""
    m, mx, em = E3._emit_mat("scan_bars", (0.2, 0.9, 1.0), 6.0)
    E.bars = []
    for k in range(3):
        bpy.ops.mesh.primitive_plane_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"scan_bar_{k}"
        ob.data.materials.append(m)
        ob.visible_shadow = False
        ob.location = (0, 0, -300)
        E.bars.append(ob)


# ------------------------------------------------------------------ Episode 3's last instant
def _use(E, which):
    B.clear()
    B.update(E.B3 if which == 3 else E.B4)


def ep3_world(E, t):
    """Everything as Episode 3 left it (its last instant), the portal and spinners still alive."""
    _use(E, 3)
    T3 = E.T3
    E3.light(E, T3 + t)
    E3.tunnel(E, T3)
    E3.portal(E, T3 + t)
    E3.ahead(E, T3)
    E3.hologram(E, T3)
    E3.dragon(E, T3)
    E3.wall(E, T3)
    E3.crystals(E, T3)
    E3.ledge(E, T3)
    E3.respawn_fx(E, T3)
    E3.players(E, T3)
    _use(E, 4)


def prepare(E):
    """Measured once (every shard): the frozen dragon's pose, the Noob's place on its neck, Ep3's last camera;
    the crystal shell over the dragon."""
    if E.prepped:
        return
    E.prepped = True
    ep3_world(E, 0.0)
    _use(E, 3)
    E3.steve(E, E.T3)
    E3.noob(E, E.T3)
    bpy.context.view_layer.update()
    E.cam_open = E3._neck_side(E, 26, dist=8.5)
    _use(E, 4)
    D = E.D
    E.d_root = Vector(D.root.location)
    E.d_rot = tuple(D.root.rotation_euler)
    E.chest = D.root.matrix_world @ Vector((0, 0, -0.55))
    E.n0 = Vector(E.N.root.location)
    E.n0_rot = tuple(E.N.root.rotation_euler)
    rnd = random.Random(5)
    E.shell = []
    far = 0.0
    for ob in D.meshes:
        c = ob.matrix_world @ (sum((Vector(v) for v in ob.bound_box), Vector()) / 8)
        far = max(far, (c - E.d_root).length)
        sh = bpy.data.objects.new(ob.name + "_crystal", ob.data)
        E.sc.collection.objects.link(sh)
        sh.material_slots[0].link = "OBJECT"
        sh.material_slots[0].material = E.cry_mat
        sh.matrix_world = Matrix.Translation(c) @ Matrix.Scale(1.07, 4) @ Matrix.Translation(-c) @ ob.matrix_world
        sh.hide_render = True
        E.shell.append((sh, c, (c - E.d_root).length, rnd.uniform(-0.08, 0.08), Matrix(sh.matrix_world)))
    E.shell_far = far


# ------------------------------------------------------------------ the shots
SHOTS = [("open", "shudder", 0), ("drop", "tearoff", 0), ("seal", "crystal", 0), ("secret", "noob_secret", 0),
         ("warn", "lean", 0), ("master", "poke1", 0), ("grew", "stare", 0), ("master2", "noob_again", 0),
         ("arrive", "patch_in", 0), ("stop", "patch_stop", 0), ("react", "react", 0), ("cube", "noob_cube", 0),
         ("name", "patch_name", 0), ("scan", "scan", 0), ("feed", "patch_feed", 0), ("helping", "noob_helping", 0),
         ("no", "sigh", 0), ("turn", "turn", 0), ("doyou", "noob_doyou", 0), ("two", "drift", 0),
         ("stunned", "hold", 0), ("glance", "hold", 1.3)]


def shot_bounds():
    return [(name, b(beat) + off) for name, beat, off in SHOTS]


def which(t):
    bs = shot_bounds()
    for i, (name, t0) in enumerate(bs):
        t1 = bs[i + 1][1] if i + 1 < len(bs) else 1e9
        if t < t1:
            return name, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


# ------------------------------------------------------------------ the cube
def _back(u):
    """Ease out with an overshoot (pops slightly past, settles)."""
    u = min(1.0, max(0.0, u))
    c = 2.2
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


def cube_size(t):
    s = SIZES[0]
    for k, rb in ((1, "respawn1"), (2, "respawn2")):
        g = b(rb) + 0.6
        s = lerp(s, SIZES[k], _back((t - g) / 0.3)) if t >= g else s
    return s


def cube_centre(E, t):
    """Ripped out of the chest at the tear-off, a throw down onto the terrace, a bounce, then hovering."""
    s = cube_size(t)
    t0, t1 = b("tearoff") + 0.05, b("fall") + 0.35
    land = CUBE + Vector((0, 0, s / 2))
    if t < t0:
        return None
    if t < t1:
        u = (t - t0) / (t1 - t0)
        a = E.chest
        T = t1 - t0
        vz = (land.z - a.z + 4.9 * T * T) / T
        tt = u * T
        p = a.lerp(land, u)
        p.z = a.z + vz * tt - 4.9 * tt * tt
        return p
    dt = t - t1
    bounce = 0.22 * abs(math.sin(min(dt, 0.45) / 0.45 * math.pi)) * (dt < 0.45)
    rise = HOVER * ss(0.45, 0.9, dt)
    bob = 0.03 * math.sin(t * 2.1) * ss(0.9, 1.4, dt)
    return land + Vector((0, 0, bounce + rise + bob))


def cube(E, t):
    c = cube_centre(E, t)
    if c is None:
        E.blk.location = (0, 0, -300)
        E.blk_light.location = (0, 0, -300)
        return
    s = cube_size(t)
    k = int(round(t * FPS))
    jit = Vector((0, 0, 0))
    glitchy = (k * 7919 % 29) < 3                                # now and then the code stutters
    if glitchy:
        jit = Vector((((k * 31) % 7 - 3) * 0.012, ((k * 17) % 5 - 2) * 0.012, 0))
    E.blk.location = c + jit
    E.blk.scale = (s, s, s)
    spin = 0.0
    if t < b("fall") + 0.35:
        spin = (t - b("tearoff")) * 7.0
    E.blk.rotation_euler = (spin * 0.7, spin, math.radians(18) + 0.15 * math.sin(t * 0.6) + spin * 0.4)
    E.blk_map.inputs["Location"].default_value = (0.25 * (k // 6 % 2) if glitchy else 0.0, 0, 0)
    stage = 0 if t < b("respawn1") + 0.6 else (1 if t < b("respawn2") + 0.6 else 2)
    E.blk_emit.default_value = (0.6, 1.4, 2.5)[stage] * (1.6 if glitchy else 1.0)
    E.blk_light.location = c + Vector((0, 0, 0))
    E.blk_light.data.energy = 60.0 * s ** 2 * (1, 1.5, 2.2)[stage]


def tether(E, t):
    on = None
    for rb, big in (("respawn1", False), ("respawn2", True)):
        if b(rb) + 0.1 <= t < b(rb) + 0.6:
            on = (rb, big)
    if on is None:
        E.teth.hide_render = True
        return
    rb, big = on
    u = (t - b(rb) - 0.1) / 0.5
    a = RING + Vector((0, 0, 0.25))
    c = cube_centre(E, t)
    sp = E.teth.data.splines[0]
    p0, p1 = sp.bezier_points
    reach = min(1.0, u / 0.35)                                   # it shoots from the ring to the cube, then holds
    end = a.lerp(c, reach)
    up = Vector((0, 0, 1.3 + 0.4 * big))
    p0.co, p0.handle_left, p0.handle_right = a, a, a + up
    p1.co, p1.handle_right, p1.handle_left = end, end, end + up * 0.7
    E.teth.data.bevel_depth = (0.05 if big else 0.035) * (1 + 0.3 * math.sin(t * 60))
    E.teth.hide_render = int(round(t * FPS)) % 5 == 4            # a flicker
    E.teth_map.inputs["Location"].default_value = (-3.0 * t, 0, 0)
    E.teth_em.inputs["Strength"].default_value = 3.0 + 1.5 * big


def shockwave(E, t):
    for rb in ("respawn1", "respawn2"):
        g = b(rb) + 0.6
        if g <= t < g + 0.4:
            u = (t - g) / 0.4
            E.shock.location = CUBE + Vector((0, 0, 0.1))
            r = 0.6 + 2.6 * u
            E.shock.scale = (r, r, 1)
            E.shock_mix.inputs[0].default_value = 1 - u
            return
    E.shock.location = (0, 0, -300)


def sparks(E, t):
    t0 = b("tearoff") + 0.03
    for ob, v, life_ in E.sparks:
        dt = t - t0
        if 0 <= dt < life_:
            ob.location = E.chest + v * dt + Vector((0, 0, -4.9 * dt * dt))
            ob.hide_render = False
        else:
            ob.location = (0, 0, -300)


def ring(E, t):
    land = b("fall") + 0.85
    flare = math.exp(-((t - land) / 0.15) ** 2) * 6.0
    pulse = sum(math.exp(-((t - (b(r) + 0.05)) / 0.2) ** 2) for r in ("respawn1", "respawn2")) * 5.0
    E.ring_emit.default_value = (2.5 * ss(land, land + 0.2, t) + flare + pulse)


def bars(E, t):
    on = ss(b("scan") + 0.8, b("scan") + 1.0, t) * (1 - ss(b("patch_grows", 1), b("patch_grows", 1) + 0.2, t))
    s = cube_size(t)
    c = cube_centre(E, t) or CUBE
    for k, ob in enumerate(E.bars):
        if on <= 0.01:
            ob.location = (0, 0, -300)
            continue
        h = 0.08 + 0.25 * abs(math.sin(t * (5 + 3 * k) + k)) if int(t * 12) % 4 else 0.05
        ob.location = c + Vector((s / 2 + 0.25, -0.2 + 0.0, -s / 2 + 0.2 + 0.15 * k + h / 2))
        ob.scale = (0.02, 0.32 * on, h)
        ob.rotation_euler = (0, 0, math.radians(90))


# ------------------------------------------------------------------ the dragon
def dragon(E, t):
    """Frozen as Episode 3 left it; one last violent shudder in the missing texture; the cube rips out and it snaps
    back to its dark scales; the glitch crystal grows over it, wingtips first, and seals it."""
    D = E.D
    k = int(round(t * FPS))
    t_snap = b("tearoff") + 0.05
    if t < t_snap:
        u = t / max(0.1, t_snap)
        amp = 0.03 + 0.12 * u ** 1.5
        r = random.Random(k)
        D.root.location = E.d_root + Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * amp
        D.root.rotation_euler = tuple(a + r.uniform(-1, 1) * math.radians(2.5) * u for a in E.d_rot)
        on = (k * 7919 % 11) / 11.0 < 0.45 + 0.5 * u or t < 2.0 / FPS
    else:
        D.root.location = E.d_root
        D.root.rotation_euler = E.d_rot
        on = False
    for ob in D.meshes:
        ob.material_slots[0].material = E.checker if on else D.mat
    # the shell
    c0 = b("crystal") + 0.05
    for sh, c, d, jit, mw in E.shell:
        at = c0 + 1.15 * (1 - d / max(0.1, E.shell_far)) + jit
        g = ss(at, at + 0.18, t)
        sh.hide_render = g <= 0.0
        if g > 0:
            s = 0.92 + 0.08 * g
            sh.matrix_world = Matrix.Translation(c) @ Matrix.Scale(s, 4) @ Matrix.Translation(-c) @ mw
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ Patch
def _patch_keys():
    T = b
    return [
        (T("patch_in") + 0.45, P_OUT),
        (T("patch_in") + 0.85, P_OUT + Vector((0, -0.15, 0.05))),
        (T("patch_in") + 1.3, Vector((-3.9, 1.3, 2.5))),
        (T("patch_in") + 1.75, P_STOP),
        (T("scan") + 0.05, P_STOP),
        (T("scan") + 0.85, P_SCAN),
        (T("drift"), P_SCAN),
        (T("drift", 1), P_TWIST),
    ]


def patch_pos(t):
    K = _patch_keys()
    if t <= K[0][0]:
        return K[0][1].copy()
    for i in range(len(K) - 1):
        if K[i][0] <= t < K[i + 1][0]:
            u = ss(0, 1, (t - K[i][0]) / (K[i + 1][0] - K[i][0]))
            p0 = K[max(0, i - 1)][1]
            p3 = K[min(len(K) - 1, i + 2)][1]
            if (K[i + 1][1] - K[i][1]).length < 1e-3:
                return K[i][1].copy()
            return _cr(p0, K[i][1], K[i + 1][1], p3, u)
    return K[-1][1].copy()


def patch(E, t):
    from patch import set_patch
    P = E.PA
    t_in = b("patch_in") + 0.45
    if t < t_in:
        P.root.location = (0, 0, -300)
        P.glow.data.energy = 0.0
        set_patch(P, {"scan": 0})
        return
    p = patch_pos(t)
    dt = 0.04
    v = (patch_pos(t + dt) - patch_pos(t - dt)) / (2 * dt)
    a = (patch_pos(t + dt) - 2 * p + patch_pos(t - dt)) / (dt * dt)
    bob = 0.05 * math.sin(t * 2.4) + 0.02 * math.sin(t * 5.3 + 1)
    N_ = (REACT_N if t >= b("react") else WIND_N) + Vector((0, 0, 1.3))
    cam = Vector(E.cam_loc_now)
    # where it looks: along its flight, then at the Noob (cheated a little toward the camera so the eye reads)
    tgt = N_
    if b("scan") + 0.3 <= t < b("patch_feed") + 0.2:
        tgt = cube_centre(E, t)
    if t < b("patch_in") + 1.75 and v.length > 0.6:
        tgt = p + v
    to = tgt - p
    yaw = _yaw(Vector((to.x, to.y, 0)))
    if b("patch_stop") <= t < b("turn") + 0.2 and not (b("scan") + 0.3 <= t < b("patch_feed") + 0.2):
        tc = cam - p
        yaw = yaw + _wrap(_yaw(Vector((tc.x, tc.y, 0))) - yaw) * 0.35
    if t >= b("turn") + 0.2:                                      # the sharp turn to the Noob
        tc = cam - p
        yaw = yaw + _wrap(_yaw(Vector((tc.x, tc.y, 0))) - yaw) * 0.3
    # a drone: leaning into its acceleration (pitch forward, bank into turns), settling with a counter-tilt
    fw = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0))
    side = Vector((-fw.y, fw.x, 0))
    pitch = _clamp(-a.dot(fw) * 0.9 - v.dot(fw) * 4.0, -16, 16)
    roll = _clamp(a.dot(side) * 0.9, -16, 16)
    pop = 1.0
    if t < t_in + 0.25:                                           # squeezing out: a pop with an overshoot
        pop = _back((t - t_in) / 0.25)
    P.root.location = p + Vector((0, 0, bob))
    P.root.rotation_euler = (math.radians(pitch), math.radians(roll), math.radians(yaw))
    P.root.scale = (pop, pop, pop)
    for side_, sx in (("l", -1), ("r", 1)):
        P.fins[side_].rotation_euler = (math.radians(8 * math.sin(t * 9 + sx) + pitch * 0.6), 0, 0)
    # the eye
    talk = 0.0
    mo = E.mouth.get("patch", {})
    f = int(round(t * FPS))
    if mo.get(f):
        talk = mo[f].get("m_o", 0.0)
    per = 2.8
    ph = (t + 0.9) % per
    blink = math.exp(-((ph - 0.06) / 0.04) ** 2)
    vals = {"open": max(0.05, 1 - blink) * (1 + 0.12 * talk), "look_x": 0.0, "look_y": 0.0, "squint": 0.0, "wide": 0.0,
            "glitch": 0.0, "scan": 0.0, "smile": 0.0, "sad": 0.0}
    if b("patch_stop") <= t < b("patch_stop", 1) + 0.2:          # annoyed
        vals["squint"] = 0.6
    if b("scan") + 0.7 <= t < b("scan") + 1.7:
        vals["scan"] = 1.0
    if b("turn") + 0.45 <= t:                                     # recognition: dilates, a scanline flicker, freezes
        u = ss(b("turn") + 0.45, b("turn") + 0.6, t)
        vals["wide"] = 1.0 * u
        vals["open"] = 1.0
        g = b("turn") + 0.55 <= t < b("turn") + 0.8
        vals["glitch"] = (0.8 if (f % 2) else 0.3) if g else 0.0
        vals["look_x"] = 0.0
    if b("drift") <= t:                                           # dim and soft
        vals["wide"] = 0.6
        vals["sad"] = 0.3
        vals["open"] = max(0.05, 1 - blink)
    set_patch(P, vals)
    P.glow.data.energy = 12.0 * (0.6 if b("drift") <= t else 1.0) * pop


def warp(E, t):
    t0 = b("patch_in") + 0.05
    u = (t - t0) / 0.6
    if not 0 <= u < 1:
        E.warp.location = (0, 0, -300)
        for p, _ in E.pix:
            p.location = (0, 0, -300)
        return
    E.warp.location = P_OUT + Vector((0, 0.28, 0))
    s = 0.25 + 0.6 * math.sin(math.pi * u)
    E.warp.scale = (s, s, s)
    E.warp_mix.inputs[0].default_value = math.sin(math.pi * u) * (0.6 if int(t * FPS) % 2 else 1.0)
    for p, d in E.pix:
        p.location = P_OUT + Vector((0, 0.2, 0)) + d * (1 - u) ** 1.5
        p.hide_render = u > 0.8


# ------------------------------------------------------------------ the Noob
def _noob_fall(E, t):
    """Flung off the neck at the shudder: up a little, a tumble, a belly-flop onto the spawn ring."""
    t0, t1 = b("tearoff") + 0.25, b("fall") + 0.85
    T = t1 - t0
    u = (t - t0) / T
    a = E.n0
    vz = (0.0 - a.z + 4.9 * T * T) / T
    tt = u * T
    p = a.lerp(RING, u)
    p.z = a.z + vz * tt - 4.9 * tt * tt
    return p, u


def noob(E, t):
    from ep09_new import NF
    N = E.N
    HYPE = E3.HYPE
    E3._burst_reset(E)
    face = dict(NF["happy"])
    pz = {"arm_sl": {"out": 8, "fwd": 4}, "arm_sr": {"out": 8, "fwd": 4}}
    t_fly = b("tearoff") + 0.25
    land = b("fall") + 0.85
    cube_c = cube_centre(E, t) or CUBE
    if t < t_fly:                                                 # on the neck, jolted by the shudder
        _use(E, 3)
        E3.noob(E, E.T3)
        _use(E, 4)
        if t > b("tearoff"):
            N.root.location = Vector(N.root.location) + Vector((0, 0, 0.12 * math.sin((t - b("tearoff")) * 40)))
        return
    if t < land:                                                  # flung, tumbling
        p, u = _noob_fall(E, t)
        pz = {"arm_sl": {"fwd": 150, "out": 70}, "arm_sr": {"fwd": 150, "out": 70}, "leg_sl": {"fwd": 30, "out": 20},
              "leg_sr": {"fwd": -20, "out": 20}}
        yaw = _face_to(E.n0, RING)
        M.set_noob(E, p, yaw, pz, dict(NF["shock"]), t)
        pitch = 90 + 360 * (1 - u) * 1.0
        N.root.rotation_euler = (math.radians(pitch), 0, math.radians(yaw))
        return
    dt = t - land
    yaw_cube = _face_to(RING, cube_c)
    if dt < 0.5:                                                  # belly-flop: flat on the ring, a bounce
        pz = {"arm_sl": {"fwd": 170, "out": 40}, "arm_sr": {"fwd": 170, "out": 40}}
        M.set_noob(E, RING + Vector((0, 0, 0.12 * math.sin(min(dt, 0.25) / 0.25 * math.pi))), yaw_cube, pz,
                   dict(NF["shock"]), t)
        _lie(N.root, 90.0)
        sq = 1 - 0.12 * math.exp(-dt * 10)
        s0 = getattr(E, "noob_scale0", N.root.scale[0])
        N.root.scale = (s0 / sq ** 0.5, s0 / sq ** 0.5, s0 * sq)
        return
    if dt < 0.85:                                                 # pops up onto his feet
        u = ss(0.5, 0.8, dt)
        p = RING + Vector((0, 0, 0.25 * math.sin(u * math.pi)))
        M.set_noob(E, p, yaw_cube, {"arm_sl": {"out": 60 * (1 - u)}, "arm_sr": {"out": 60 * (1 - u)}}, dict(NF["happy"]), t)
        N.root.rotation_euler = (math.radians(90 * (1 - u)), 0, N.root.rotation_euler[2])
        return
    # standing from here: where he is, where he faces
    p, yaw = RING.copy(), yaw_cube
    up = Vector(E.D.root.location) + Vector((0, 0, 1))
    if t < b("crystal") + 1.05:                                   # he looks up at the dragon being sealed
        tl, nd = _look(yaw, p, up, h=1.4)
        k = ss(land + 0.85, land + 1.1, t)
        pz["head_turn"], pz["head_nod"] = tl * k, nd * k
        face = dict(NF["awe"])
    elif t < b("noob_secret"):                                    # spots the cube; hurries over
        u = ss(b("crystal") + 1.1, b("noob_secret") - 0.05, t)
        p = RING.lerp(N_LOOK, u)
        yaw = _face_to(RING, N_LOOK)
        if 0.02 < u < 0.98:
            _run(pz, t, b("crystal") + 1.1, 2.6, k=0.7, steve=False)
        face = dict(HYPE)
    elif t < b("poke1"):                                          # crouched to it: "A secret block!", reaching
        p = N_LOOK.copy()
        yaw = _face_to(p, cube_c)
        cr = ss(b("noob_secret"), b("noob_secret") + 0.3, t)
        pz.update({"hips_drop": 0.28 * cr, "chest_lean": 28 * cr, "head_nod": 12 * cr,
                   "arm_sl": {"fwd": 25, "out": 20}, "arm_sr": {"fwd": 25, "out": 20}})
        face = dict(NF["awe"])
        if t >= b("lean"):
            r = ss(b("lean"), b("lean") + 0.35, t)
            pz["arm_sr"] = {"fwd": 25 + 50 * r, "out": 12}
            face = dict(HYPE)
        if b("steve_touch") <= t:                                 # he glances back at Steve, hand hovering
            g = ss(b("steve_touch") + 0.4, b("steve_touch") + 0.8, t) * (1 - ss(b("steve_touch", 1) - 0.2, b("poke1"), t))
            tl, nd = _look(yaw, p, gp(E, STEVE_EDGE) + Vector((0, 0, 1.6)), h=1.2)
            pz["head_turn"] = tl * g
            face = dict(NF["happy"])
    elif t < b("die1"):                                           # the poke: a wind back, the touch, zapped
        p = N_LOOK.lerp(POKE_N, ss(b("poke1"), b("poke1") + 0.25, t))
        yaw = _face_to(p, cube_c)
        back = ss(b("poke1"), b("poke1") + 0.15, t) * (1 - ss(b("poke1") + 0.18, b("poke1") + 0.3, t))
        hit = ss(b("poke1") + 0.18, b("poke1") + 0.3, t)
        pz.update({"chest_lean": 18 + 8 * hit, "arm_sr": {"fwd": 75 - 30 * back + 15 * hit, "out": 8, "elbow": 10}})
        face = dict(HYPE)
        if t >= b("poke1") + 0.3:                                 # zapped: twitching
            z = math.sin(t * 90)
            pz["chest_lean"] += 6 * z
            pz["arm_sl"] = {"fwd": 40 + 30 * z, "out": 60}
            face = dict(NF["shock"])
    elif t < b("respawn1") + 0.1:                                 # bursts
        p = POKE_N.copy()
        yaw = _face_to(p, cube_c)
        M.set_noob(E, p, yaw, {"arm_sr": {"fwd": 90}}, dict(NF["shock"]), t)
        E3._burst_apply(E, t - b("die1"))
        _dark_cube(E, t - b("die1"), p)
        return
    elif t < b("chop") + 0.7:
        r1 = b("respawn1") + 0.1
        p = RING.copy()
        yaw = _face_to(RING, cube_c)
        face = dict(HYPE)
        _squash(E, t - r1)
        if t < b("noob_touched2"):                                # a fist pump
            k = ss(r1 + 0.35, r1 + 0.55, t)
            pz["arm_sr"] = {"fwd": 20, "out": 40 + 120 * k, "elbow": 60 + 30 * math.sin(t * 18) * k}
        elif t < b("noob_again"):                                 # "I touched it!" proud, hands on hips; looks at it
            pz["arm_sl"] = {"out": 45, "fwd": -15, "elbow": 100}
            pz["arm_sr"] = {"out": 45, "fwd": -15, "elbow": 100}
            pz["chest_lean"] = -8
            if t >= b("stare"):
                tl, nd = _look(yaw, p, cube_c, h=1.4)
                pz["head_turn"], pz["head_nod"] = tl, nd
        else:                                                     # "Again!" and off he goes: the karate chop
            r0 = b("noob_again") + 0.55
            u = ss(r0, b("chop") + 0.25, t)
            p = RING.lerp(CHOP_N, u)
            yaw = _face_to(p, cube_c)
            if 0.02 < u < 0.98:
                _run(pz, t, r0, 2.8, k=0.9, steve=False)
            if t >= b("chop") + 0.2:
                up_ = ss(b("chop") + 0.2, b("chop") + 0.33, t)
                dn = ss(b("chop") + 0.33, b("chop") + 0.4, t)
                pz["arm_sr"] = {"fwd": 40 + 120 * up_ - 70 * dn, "out": 30 - 20 * dn, "elbow": 10}
                pz["chest_lean"] = 10 + 15 * dn
            if t >= b("chop") + 0.4:
                z = math.sin(t * 90)
                pz["chest_lean"] += 6 * z
                pz["arm_sl"] = {"fwd": 40 + 30 * z, "out": 60}
                face = dict(NF["shock"])
            else:
                face = dict(NF["shout"]) if t < b("noob_again", 1) else dict(HYPE)
        if t < b("chop"):
            pz["_skip"] = 0
    elif t < b("respawn2") + 0.1:                                 # bursts again
        p = CHOP_N.copy()
        yaw = _face_to(p, cube_c)
        M.set_noob(E, p, yaw, {"arm_sr": {"fwd": 30}}, dict(NF["shock"]), t)
        E3._burst_apply(E, t - b("die2"))
        _dark_cube(E, t - b("die2"), p)
        return
    elif t < b("react"):                                          # back; a look up at the huge cube; the third swing
        r2 = b("respawn2") + 0.1
        _squash(E, t - r2)
        u = ss(r2 + 0.75, r2 + 1.4, t)
        p = RING.lerp(WIND_N, u)
        yaw = _face_to(p, cube_c)
        face = dict(NF["awe"]) if t < r2 + 0.75 else dict(HYPE)
        if t < r2 + 0.75:
            tl, nd = _look(yaw, p, cube_c + Vector((0, 0, 0.5)), h=1.4)
            pz["head_turn"], pz["head_nod"] = tl, nd
        elif u < 0.98:
            _run(pz, t, r2 + 0.75, 2.4, k=0.6, steve=False)
        wind = ss(r2 + 1.4, r2 + 1.75, t)
        pz["arm_sr"] = {"fwd": 30 + 100 * wind, "out": 40, "elbow": 80 * wind}
        pz["chest_lean"] = pz.get("chest_lean", 0) - 10 * wind
        if t >= b("patch_in") + 1.65:                             # Patch is there: frozen mid-swing, blinking
            face = dict(NF["shock"])
        if t >= b("patch_stop"):
            lw = ss(b("patch_stop") + 0.6, b("patch_stop", 1), t)
            pz["arm_sr"] = {"fwd": 130 - 90 * lw, "out": 40, "elbow": 80 - 60 * lw}
            face = dict(NF["confused"])
    else:                                                         # the hop back, pointing; then watching Patch
        hop = ss(b("react"), b("react") + 0.3, t)
        p = WIND_N.lerp(REACT_N, hop) + Vector((0, 0, 0.25 * math.sin(math.pi * hop)))
        P_ = Vector(E.PA.root.location)
        yaw = _face_to(p, P_)
        point = ss(b("react") + 0.2, b("react") + 0.4, t) * (1 - ss(b("noob_cube", 1), b("noob_cube", 1) + 0.4, t))
        pz["arm_sl"] = {"fwd": 85 * point + 4, "out": 20 - 10 * point}
        pz["arm_sr"] = {"fwd": 85 * point + 4, "out": 20 - 10 * point}
        tl, nd = _look(yaw, p, P_, h=1.4)
        pz["head_turn"], pz["head_nod"] = tl, nd
        pz["head_tilt"] = 12 * point
        face = dict(NF["shock"]) if t < b("patch_name") else dict(HYPE)
        if b("scan") + 0.3 <= t < b("patch_feed"):
            tl, nd = _look(yaw, p, cube_centre(E, t), h=1.4)
            pz["head_turn"], pz["head_nod"] = tl, nd
            face = dict(NF["awe"])
        if b("noob_helping") - 0.1 <= t < b("turn"):              # "So I'm helping!": fists on hips, chest out
            k = ss(b("noob_helping") - 0.1, b("noob_helping") + 0.15, t)
            pz["arm_sl"] = {"out": 45 * k + 8, "fwd": -15 * k, "elbow": 100 * k}
            pz["arm_sr"] = {"out": 45 * k + 8, "fwd": -15 * k, "elbow": 100 * k}
            pz["chest_lean"] = -10 * k
            face = dict(HYPE)
            if t >= b("steve_no"):
                tl, nd = _look(yaw, p, gp(E, STEVE_EDGE) + Vector((0, 0, 1.6)), h=1.4)
                pz["head_turn"], pz["head_nod"] = tl, nd
        if t >= b("turn") + 0.3:                                  # the smile goes
            face = dict(NF["confused"]) if t < b("noob_doyou") else dict(NF["worried"])
            if t >= b("patch_deleted"):
                face = {"both_h": 1.9, "both_w": 1.05, "m_arch": 0.15, "both_ps": 0.8}
    pz.pop("_skip", None)
    pz = life(E, "noob", pz, face, t, 1.6)
    M.set_noob(E, p, yaw, pz, face, t)


def _squash(E, dt):
    """Popping back onto the ring: a stretch, a squash, settled in 8 frames."""
    N = E.N
    if not hasattr(E, "noob_scale0"):
        E.noob_scale0 = N.root.scale[0]
    s0 = E.noob_scale0
    if dt < 0:
        return
    keys = [(0.0, 1.15), (0.12, 0.9), (0.33, 1.0)]
    z = 1.0
    for (a, za), (c, zc) in zip(keys, keys[1:]):
        if a <= dt < c:
            z = lerp(za, zc, ss(a, c, dt))
    N.root.scale = (s0 / z ** 0.5, s0 / z ** 0.5, s0 * z)


def _dark_cube(E, dt, p):
    """The planted clue: one small dark cube drifts away from where he died, slowly, up and to the side."""
    if dt < 0.05 or dt > 1.6:
        return
    c = p + Vector((0, 0, 1.1)) + Vector((-0.35, 0.55, 0.45)) * (dt - 0.05)
    E.dark_cube.location = c
    E.dark_cube.rotation_euler = (dt * 1.2, dt * 2.0, dt * 0.8)
    s = min(1.0, (dt - 0.05) / 0.1) * (1 - ss(1.2, 1.6, dt))
    E.dark_cube.scale = (s, s, s)


# ------------------------------------------------------------------ Steve
def steve(E, t):
    from ep09_new import SF
    S = E.S
    if t < b("tearoff"):
        _use(E, 3)
        E3.steve(E, E.T3)
        _use(E, 4)
        return
    face = dict(SF["flat"])
    pz = {"arm_sr": {"fwd": 25, "out": 12, "elbow": 35}, "arm_sl": {"fwd": 10, "out": 8, "elbow": 20}}
    p0 = gp(E, E3.STEVE_PLAN)
    p, yaw = p0.copy(), 35.0
    up = Vector(E.D.root.location) + Vector((0, 0, 1))
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.0))
    cube_c = cube_centre(E, t) or CUBE
    w0, w1 = b("crystal") + 1.0, b("lean") + 0.3
    if t < w0:                                                    # watching the Noob fall, then the dragon sealed
        yaw = lerp(35.0, _face_to(p0, RING), ss(b("tearoff"), b("fall") + 0.6, t))
        tgt = N_ if t < b("crystal") else up
        tl, nd = _look(yaw, p, tgt)
        pz["head_turn"], pz["head_nod"] = tl, nd
        flinch = math.exp(-((t - (b("fall") + 0.85)) / 0.12) ** 2)
        pz["chest_lean"] = -10 * flinch
        face = dict(SF["stunned"]) if t < b("crystal") + 0.4 else dict(SF["worried"])
    elif t < w1:                                                  # walks to the pad's west edge
        u = ss(w0, w1, t)
        p = p0.lerp(STEVE_EDGE, (t - w0) / (w1 - w0))
        yaw = _face_to(p0, STEVE_EDGE)
        if t < w1 - 0.1:
            _run(pz, t, w0, 1.55, k=0.45, steve=True)
        tl, nd = _look(yaw, p, N_)
        pz["head_turn"], pz["head_nod"] = tl * 0.6, nd * 0.4
        face = dict(SF["worried"])
        if t >= b("lean"):
            r = ss(b("lean"), w1, t)
            pz["arm_sr"] = {"fwd": 25 + 15 * r, "out": 15 + 7 * r, "elbow": 35 + 15 * r}
    else:
        p = STEVE_EDGE.copy()
        yaw = _face_to(p, N_)
        guard = {"fwd": 35, "out": 25, "elbow": 20}                # the pickaxe up
        pz["arm_sr"] = dict(guard)
        tl, nd = _look(yaw, p, N_)
        pz["head_turn"], pz["head_nod"] = tl, nd
        if t < b("poke1"):                                        # "It fell off the dragon. Don't touch it." leaning, waving
            k = ss(b("steve_touch"), b("steve_touch") + 0.3, t) * (1 - ss(b("steve_touch", 1), b("poke1"), t))
            pz["chest_lean"] = 14 * ss(b("lean"), b("lean") + 0.4, t)
            pz["arm_sl"] = {"fwd": 70 * k + 10, "out": 25 + 25 * math.sin(t * 9) * k, "elbow": 40}
            face = dict(SF["worried"])
        elif t < b("stare"):                                      # the poke: a reach, too late; the flinch
            k = ss(b("poke1"), b("poke1") + 0.25, t)
            pz["arm_sl"] = {"fwd": 80 * k, "out": 15}
            fl = math.exp(-((t - b("die1") - 0.05) / 0.1) ** 2)
            pz["chest_lean"] = 10 * k - 12 * fl
            face = dict(SF["scared"]) if t < b("respawn1") + 0.5 else dict(SF["stunned"])
            if t >= b("respawn1") + 0.5:
                tl, nd = _look(yaw, p, cube_c)
                pz["head_turn"], pz["head_nod"] = tl, nd
        elif t < b("noob_again"):                                 # he stares at the bigger cube: "...It grew."
            tl, nd = _look(yaw, p, cube_c)
            pz["head_turn"], pz["head_nod"] = tl, nd
            pz["arm_sr"] = {"fwd": 15, "out": 14, "elbow": 15}
            face = dict(SF["stunned"]) if t < b("steve_grew") else dict(SF["flat"])
        elif t < b("respawn2") + 0.4:                             # the lunge: a step, an arm out, too late
            lu = ss(b("chop") - 0.1, b("chop") + 0.25, t) * (1 - ss(b("die2") + 0.2, b("respawn2") + 0.4, t))
            p = STEVE_EDGE + Vector((-0.35, -0.05, 0)) * lu
            pz["arm_sl"] = {"fwd": 85 * lu, "out": 10}
            pz["chest_lean"] = 18 * lu
            face = dict(SF["scared"])
        elif t < b("react"):                                      # the portal flickers: he looks; then Patch
            P_ = Vector(E.PA.root.location)
            tgt = cube_c if t < b("patch_in") else (Vector((-1.6, 4.4, 3.3)) if P_.z < -100 else P_)
            tl, nd = _look(yaw, p, tgt, lim=80)
            pz["head_turn"], pz["head_nod"] = tl, nd
            face = dict(SF["stunned"]) if t >= b("patch_in") + 0.4 else dict(SF["worried"])
        else:                                                     # the jump back into a guard; wary
            P_ = Vector(E.PA.root.location)
            jb = ss(b("react"), b("react") + 0.25, t)
            p = STEVE_EDGE.lerp(STEVE_BACK, jb) + Vector((0, 0, 0.12 * math.sin(math.pi * jb)))
            yaw = _face_to(p, P_)
            low = ss(b("patch_name"), b("patch_feed"), t)
            pz["arm_sr"] = {"fwd": 30 - 10 * low, "out": 50 - 25 * low, "elbow": 35 - 20 * low}
            pz["arm_sl"] = {"fwd": 40 - 20 * low, "out": 30, "elbow": 40}
            pz["hips_drop"] = 0.15 * (1 - low)
            pz["chest_lean"] = -6 * (1 - low)
            look_at = P_
            if b("scan") + 0.3 <= t < b("patch_feed"):
                look_at = cube_c
            if b("sigh") <= t < b("turn"):                        # down goes the pickaxe; a look Noob, Patch, Noob
                d = ss(b("sigh"), b("sigh") + 0.4, t)
                pz["arm_sr"] = {"fwd": 30 - 20 * d, "out": 10, "elbow": 40 - 20 * d}
                pz["arm_sl"] = {"fwd": 5, "out": 6}
                pz["chest_lean"] = 6 * d
                seq = (t - b("sigh")) / 0.7
                look_at = N_ if seq < 0.35 or seq > 0.7 else P_
            tl, nd = _look(yaw, p, look_at, lim=70)
            pz["head_turn"], pz["head_nod"] = tl, nd
            face = dict(SF["scared"]) if t < b("noob_cube") else dict(SF["worried"])
            if b("sigh") <= t < b("turn"):
                face = dict(SF["flat"])
            if t >= b("turn"):
                face = dict(SF["worried"])
            if t >= b("hold") + 1.3:
                face = dict(SF["stunned"])
    pz = life(E, "steve", pz, face, t, 2.7)
    M.set_steve(E, p, yaw, pz, face, t)


# ------------------------------------------------------------------ one frame
def apply(E, t):
    prepare(E)
    E._t_now = t
    name, t0, t1 = which(t)
    E.cam_loc_now = _cam(E, t, name, t0, t1)[0]
    ep3_world(E, t)
    dragon(E, t)
    cube(E, t)
    tether(E, t)
    shockwave(E, t)
    sparks(E, t)
    ring(E, t)
    warp(E, t)
    patch(E, t)
    steve(E, t)
    noob(E, t)
    bpy.context.view_layer.update()
    camera(E, t, name, t0, t1)
    bars(E, t)
    E2.set_wash(E, 0.0)


# ------------------------------------------------------------------ the camera
def camera(E, t, shot, t0, t1):
    from ep10_p2_omg import handheld
    loc, look, lens, fstop, focus, shake = _cam(E, t, shot, t0, t1)
    hit = 0.0
    for rb in ("respawn1", "respawn2"):
        g = b(rb) + 0.6
        hit += 1.2 * math.exp(-max(0.0, t - g) * 6) * (t >= g)
    shake += hit + 0.8 * math.exp(-max(0.0, t - b("fall") - 0.35) * 6) * (t >= b("fall") + 0.35) * (t < b("crystal"))
    if t < b("tearoff"):
        shake = 0.0                                               # still Episode 3's frozen camera
    y1, p1, r1 = handheld(t, shake)
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = M.P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.data.lens = lens
    E.cam.data.dof.use_dof = fstop < 30
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    S_ = Vector(E.S.holder.location)
    N_ = Vector(E.N.root.location)
    near = [v for v in (S_, N_) if v.z > -100 and (v - loc).length < 25]
    tgt = (sum(near, Vector()) / len(near) + Vector((0, 0, 1.3))) if near else look
    E.key.location = loc + (tgt - loc) * 0.3 + Vector((0.5, 0, 1.4))
    E.key.rotation_euler = (tgt - E.key.location).to_track_quat("-Z", "Y").to_euler()
    E.key.data.energy = 260.0


def _c(x, y, z):
    return Vector((x, y, z))


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus or None, handheld)"""
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, t0 + 3, t)
    N_ = Vector(E.N.root.location)
    S_ = Vector(E.S.holder.location)
    if shot == "open":                                            # Episode 3's last camera, unchanged
        loc, look, lens, f, fo, sh = E.cam_open
        return loc, look, lens, 30, None, 0.0
    if shot == "drop":                                            # wide and low from the south-west: the cube and the Noob fall
        return _c(-10.5, -10.5, 1.6), _c(-3.6, 0.4, 2.6), 20, 30, None, 0.4
    if shot == "seal":                                            # low behind Steve: the crystal grows over the dragon
        return _c(-7.6, -8.2, 1.2), _c(-1.8, 1.2, 4.0), 22, 30, None, 0.25
    if shot == "secret":                                          # close: the Noob crouched to the little cube
        return _c(-3.4, -4.9, 1.05), _c(-5.35, -1.2, 0.85), 30, 3.2, None, 0.25
    if shot == "warn":                                            # Steve at the pad's edge, the portal behind him
        return STEVE_EDGE + _c(-2.7, -1.3, 1.45), STEVE_EDGE + _c(0, 0, 1.45), 36, 2.8, None, 0.3
    if shot in ("master", "master2"):                             # locked: the ring, the cube, the Noob (a fixed ruler)
        return _c(-5.4, -8.6, 1.5), _c(-5.8, -0.4, 0.95), 30, 30, None, 0.15
    if shot == "grew":                                            # Steve stares at it
        return STEVE_EDGE + _c(-2.5, -1.6, 1.45), STEVE_EDGE + _c(0, 0, 1.5), 40, 2.8, None, 0.2
    if shot == "arrive":                                          # wide: the portal flickers, Patch squeezes out, zips over
        return _c(-8.0, -7.0, 1.9), _c(-3.4, 1.4, 2.6), 24, 30, None, 0.25
    if shot == "stop":                                            # Patch between the fist and the cube
        return _c(-6.0, -4.9, 1.5), _c(-6.0, -1.2, 1.4), 30, 3.2, None, 0.2
    if shot == "react":                                           # Steve jumps back into a guard
        return _c(-4.5, -2.45, 1.45), STEVE_BACK + _c(0, 0, 1.4), 30, 3.0, None, 0.35
    if shot == "cube":                                            # the Noob, pointing: "A talking cube!"
        return REACT_N + _c(1.0, -3.4, 1.5), REACT_N + _c(0.4, 0, 1.4), 32, 2.8, None, 0.25
    if shot == "name":                                            # Patch, three-quarter: "I'm Patch."
        return _c(-6.9, -3.2, 1.5), P_STOP + _c(0, 0, 0.05), 42, 2.8, None, 0.2
    if shot == "scan":                                            # the scan: from the side, the cone onto the huge cube
        return _c(-8.0, -6.0, 1.7), _c(-4.2, -2.7, 1.2), 28, 30, None, 0.2
    if shot == "feed":                                            # Patch, close, talking to the Noob
        return P_SCAN + _c(-0.5, -2.4, -0.05), P_SCAN + _c(0, 0, 0.05), 44, 2.8, None, 0.2
    if shot == "helping":                                         # the Noob, proud
        return REACT_N + _c(0.8, -3.2, 1.5), REACT_N + _c(0, 0, 1.45), 34, 2.8, None, 0.2
    if shot == "no":                                              # Steve: "No."
        return _c(-3.6, -2.95, 1.5), STEVE_BACK + _c(0, 0, 1.5), 34, 2.8, None, 0.15
    if shot == "turn":                                            # over the Noob's shoulder: Patch turns to him
        n = REACT_N + _c(0, 0, 1.55)
        d = (n - P_SCAN)
        d.z = 0
        d.normalize()
        r = Vector((-d.y, d.x, 0))
        return n + d * 3.4 + r * 1.25 + _c(0, 0, 0.75), P_SCAN + _c(0.0, 0, 0.25), 55, 2.6, (P_SCAN - n).length + 3.4, 0.1
    if shot == "doyou":                                           # the Noob, the smile gone
        return REACT_N + _c(0.9, -3.0, 1.55), REACT_N + _c(0, 0, 1.6), 40, 2.6, None, 0.1
    if shot == "two":                                             # a slow push in: the Noob left, Patch right, the sky between
        a = _c(-9.0, -6.0, 1.3)
        c = _c(-8.5, -5.3, 1.38)
        return a.lerp(c, u), _c(-3.5, 1.5, 3.0), 28, 30, None, 0.05
    if shot == "stunned":                                         # the Noob's stunned face
        return REACT_N + _c(0.6, -3.1, 1.55), REACT_N + _c(0, 0, 1.6), 42, 2.6, None, 0.05
    if shot == "glance":                                          # Steve's alarmed glance
        return STEVE_BACK + _c(-2.6, -1.8, 1.5), STEVE_BACK + _c(0, 0, 1.5), 42, 2.8, None, 0.05
    return _c(-5, -12, 3), _c(-5, 0, 2), 24, 30, None, 0.3


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
    B.clear()
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
