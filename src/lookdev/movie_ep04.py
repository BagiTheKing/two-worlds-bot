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
WIND_N = Vector((-6.75, -1.05, 0.0))     # the third swing, wound up (1.45 m now): an arm's length clear of it
REACT_N = Vector((-6.95, -0.8, 0.0))     # he hops back from Patch
STEVE_CLEAR = Vector((-2.5, -2.25, 0.0))  # Steve's step back out from under the shuddering dragon (clear of the stones)
STEVE_EDGE = Vector((-2.55, -1.0, 0.0))  # Steve at the grey pad's west edge, across the 1 m gap
STEVE_BACK = Vector((-2.1, -1.3, 0.0))   # his half step back when Patch appears
P_OUT = Vector((-1.6, 4.3, 3.3))         # Patch, just out of the portal's membrane (y 4.6, facing -y)
P_STOP = Vector((-5.98, -1.2, 1.55))     # between the fist and the cube
P_SCAN = Vector((-4.25, -3.3, 1.6))      # the front right of the cube: a clear line to it
P_TURN = Vector((-6.1, -2.4, 1.75))      # recognising him, it drifts close to the Noob
P_TWIST = Vector((-6.0, -2.6, 1.95))     # the two-shot: between the Noob and Steve, clear of Steve's silhouette
# the Noob's faces (the creator, 2026-11-27: happy lines need a happy face, an open smile; sad only for "You do?")
JOY = {"both_h": 1.95, "both_w": 1.05, "both_bm": 0.2, "both_py": 0.3, "m_arch": -1.2, "m_w": 2.6, "m_o": 0.55,
       "m_up": 0.6, "m_r": 0.4, "m_vee": 0.0, "_joy": 1}
GRIN = {"both_h": 1.8, "both_bm": 0.3, "m_arch": -0.9, "m_w": 2.3, "m_o": 0.3, "m_up": 0.7, "m_vee": 0.0, "_joy": 1}


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
    lo.rotation_euler = (math.radians(-90), 0, 0)                # emitting toward -y, away from the screen (it used to
                                                                  # face into the glossy screen and wash the eye out)
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
    cap = {}
    set0 = M.set_noob

    def keep(E_, loc, yaw, pz, face, t, **kw):                    # the Noob's pose on the neck (the slide starts there)
        if kw.get("N") is None:
            cap["pz"] = dict(pz)
        return set0(E_, loc, yaw, pz, face, t, **kw)
    M.set_noob = keep
    try:
        E3.noob(E, E.T3)
    finally:
        M.set_noob = set0
    E.e3_pz = {k: v for k, v in cap.get("pz", {}).items() if k != "root_yaw"}
    E.noob_scale0 = getattr(E, "noob_scale0", E.N.root.scale[0])
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
    # the shell's own crystal: the frozen players' material with about 70% fewer pink/cyan flecks and a softer glow
    # (the creator, 2026-11-27: the dense confetti behind every close-up competed with the faces)
    sm = E.cry_mat.copy()
    sm.name = "glitch_crystal_shell"
    for n_ in sm.node_tree.nodes:
        if n_.type == "VALTORGB":
            els = n_.color_ramp.elements
            els[2].position = 0.75                               # the cyan first (the ramp keeps its order)
            els[1].position = 0.71                               # then the pink
        if n_.type == "BSDF_PRINCIPLED":
            n_.inputs["Emission Strength"].default_value = 0.55
    E.shell_mat = sm
    E.burst_scale = {k: tuple(o.scale) for k, o in E.burst_parts.items()}
    for ob in D.meshes:
        c = ob.matrix_world @ (sum((Vector(v) for v in ob.bound_box), Vector()) / 8)
        far = max(far, (c - E.d_root).length)
        sh = bpy.data.objects.new(ob.name + "_crystal", ob.data)
        E.sc.collection.objects.link(sh)
        sh.material_slots[0].link = "OBJECT"
        sh.material_slots[0].material = E.shell_mat
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
    c = cube_centre(E, t)
    s = cube_size(t)
    d = Vector((c.x - RING.x, c.y - RING.y, 0)).normalized()
    a = RING + d * 0.82 + Vector((0, 0, 0.07))                   # out of the ring's neon edge, never out of the Noob
    sp = E.teth.data.splines[0]
    p0, p1 = sp.bezier_points
    reach = min(1.0, u / 0.35)                                   # it runs from the ring to the cube, then holds
    tip = c - d * (s / 2) + Vector((0, 0, -0.1 * s))             # into the cube's near face
    end = a.lerp(tip, reach)
    span = (end - a).length
    up = Vector((0, 0, 0.35 + 0.15 * big))                       # a low arc skimming the floor
    p0.co, p0.handle_left, p0.handle_right = a, a, a + d * span * 0.4 + up
    p1.co, p1.handle_right, p1.handle_left = end, end, end - d * span * 0.35 + up * 0.6
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
        (T("turn") + 0.45, P_SCAN),
        (T("turn") + 1.6, P_TURN),                                # recognising him: it drifts in close
        (T("drift"), P_TURN),
        (T("drift", 1), P_TWIST),
    ]


LINES_P = ("patch_stop", "patch_name", "patch_feed", "patch_grows", "patch_know", "patch_deleted")


def _speaking(t, who_lines, pre=0.15, post=0.25):
    return any(b(x) - pre <= t < b(x, 1) + post for x in who_lines)


def _patch_yaw(E, t, p, v, cam):
    """Where Patch faces: along its flight; the Noob (or the cube while scanning, Steve on his "No."), always cheated
    toward the camera, most while it talks, so its screen reads three-quarter front (never its blank side)."""
    N_ = (REACT_N if t >= b("react") else WIND_N) + Vector((0, 0, 1.3))
    if t < b("patch_in") + 1.75 and v.length > 0.6:
        tgt = p + v
    elif b("scan") + 0.3 <= t < b("patch_feed") - 0.1:
        tgt = cube_centre(E, t)
    elif b("sigh") <= t < b("turn"):
        tgt = gp(E, STEVE_BACK) + Vector((0, 0, 1.5))
    else:
        tgt = N_
    to = tgt - p
    yaw = _yaw(Vector((to.x, to.y, 0)))
    if t >= b("patch_stop") and not (b("scan") + 0.3 <= t < b("patch_feed") - 0.1):
        tc = cam - p
        k = 0.6 if _speaking(t, LINES_P) else 0.3
        yaw = yaw + _wrap(_yaw(Vector((tc.x, tc.y, 0))) - yaw) * k
    return yaw


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
    cam = Vector(E.cam_loc_now)
    yaw = _patch_yaw(E, t, p, v, cam)
    T0 = b("turn")
    if T0 - 0.05 <= t < T0 + 0.6:                                 # the sharp turn: whip round, overshoot, settle
        y0 = _patch_yaw(E, T0 - 0.06, patch_pos(T0 - 0.06), Vector(), cam)
        y1 = _patch_yaw(E, T0 + 0.6, patch_pos(T0 + 0.6), Vector(), cam)
        yaw = y0 + _wrap(y1 - y0) * _back((t - T0) / 0.3)
    # a drone: nose down as it speeds forward, nose up to brake, banking into turns
    fw = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0))
    side = Vector((-fw.y, fw.x, 0))
    pitch = _clamp(a.dot(fw) * 0.6 + v.dot(fw) * 3.0, -16, 16)
    roll = _clamp(a.dot(side) * 0.9, -16, 16)
    if b("scan") + 0.6 <= t < b("patch_feed") - 0.1:              # aiming down into the cube's centre
        c = cube_centre(E, t)
        d = c - p
        aim = math.degrees(math.atan2(-d.z, Vector((d.x, d.y, 0)).length))
        pitch += aim * ss(b("scan") + 0.6, b("scan") + 0.85, t) * (1 - ss(b("patch_feed") - 0.35, b("patch_feed") - 0.1, t))
    if T0 <= t < T0 + 0.5:                                        # recoil: a small tip back as it recognises him
        pitch -= 9 * math.sin(math.pi * (t - T0) / 0.5)
    pop = 1.0
    if t < t_in + 0.25:                                           # squeezing out: a pop with an overshoot
        pop = _back((t - t_in) / 0.25)
    P.root.location = p + Vector((0, 0, bob))
    P.root.rotation_euler = (math.radians(pitch), math.radians(roll), math.radians(yaw))
    P.root.scale = (pop, pop, pop)
    flare = 25 * math.exp(-((t - T0 - 0.15) / 0.2) ** 2)           # the fins flare on the recognition
    for side_, sx in (("l", -1), ("r", 1)):
        P.fins[side_].rotation_euler = (math.radians(8 * math.sin(t * 9 + sx) + pitch * 0.6 - flare), 0, 0)
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
    if b("scan") + 0.95 <= t < b("scan") + 1.75:                  # the beam only once parked and aimed
        vals["scan"] = 1.0
    if b("scan") + 0.6 <= t < b("scan") + 0.95:
        vals["squint"] = 0.35                                     # focusing
    if b("turn") + 0.2 <= t:                                      # recognition: the eye widens (not blown out), a
        u = ss(b("turn") + 0.2, b("turn") + 0.4, t)               # short scanline stutter, then a slow look
        vals["wide"] = 0.55 * u
        vals["open"] = max(0.05, 1 - blink) if t > b("turn") + 1.2 else 1.0
        g = b("turn") + 0.3 <= t < b("turn") + 0.5
        vals["glitch"] = (0.6 if (f % 2) else 0.2) if g else 0.0
        vals["look_y"] = -0.15 * math.sin(t * 0.9)
        vals["look_x"] = 0.12 * math.sin(t * 0.7)
    if b("drift") <= t:                                           # dim and soft
        vals["wide"] = 0.3
        vals["sad"] = 0.35
        vals["open"] = max(0.05, 0.85 - blink)
    set_patch(P, vals)
    if vals["scan"] > 0.5:                                        # the beam ends in the cube (not through it)
        dist = (cube_centre(E, t) - p).length
        P.beam.scale = (1.0, dist / (3.0 * 0.42 * 3), 1.0)
    P.glow.data.energy = 8.0 * (0.6 if b("drift") <= t else 1.0) * pop


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


# ------------------------------------------------------------------ the cast: shared helpers
HC = 1.0                                  # the Noob's body centre above his feet (m): he turns about it bouncing up
SLIDE_D = Vector((-0.738, -0.674, 0.0))   # off the neck's west side, toward the terrace (across the neck's line)


def _blend(a, c, k):
    out = {}
    for key in set(a) | set(c):
        va, vc = a.get(key), c.get(key)
        if isinstance(va, dict) or isinstance(vc, dict):
            out[key] = _blend(va or {}, vc or {}, k)
        else:
            out[key] = lerp(va or 0.0, vc or 0.0, k)
    return out


def _stride(pz, t, t0, t1, a, c, amp=24.0, stride=0.5, steve=False):
    """Walk from a to c, eased in and out. The legs swing with the speed (still at the start and the end, never
    held apart); the Noob Roblox style (stiff legs, the arms swinging against them), Steve his own cycle."""
    x = _clamp((t - t0) / max(1e-3, t1 - t0), 0.0, 1.0)
    u = x * x * (3 - 2 * x)
    p = a.lerp(c, u)
    dist = (c - a).length
    k = min(1.0, 6 * x * (1 - x) / 1.5) * min(1.0, dist / 0.6)
    ph = math.pi * dist * u / stride
    if steve:
        pz.update(M.run_cycle(ph, 0.4 * k, True))
        return p
    sw = math.sin(ph)
    pz["leg_sl"] = {"fwd": amp * k * sw}
    pz["leg_sr"] = {"fwd": -amp * k * sw}
    pz["arm_sl"] = {"fwd": -0.9 * amp * k * sw, "out": 8}
    pz["arm_sr"] = {"fwd": 0.9 * amp * k * sw, "out": 8}
    pz["chest_lean"] = pz.get("chest_lean", 0) + 5 * k
    return p + Vector((0, 0, 0.04 * k * abs(sw)))


def _look_mix(yaw, p, a, c, k, h=1.6, lim=70.0):
    t1, n1 = _look(yaw, p, a, h=h, lim=lim)
    t2, n2 = _look(yaw, p, c, h=h, lim=lim)
    return lerp(t1, t2, k), lerp(n1, n2, k)


def _turn_to(y0, y1, k):
    return y0 + _wrap(y1 - y0) * k


def _set_noob(E, loc, yaw, pz, face, t):
    """M.set_noob, keeping a happy face happy while he talks (the voice opens the mouth; the smile stays)."""
    from noob import pose_noob
    from faceplate import set_face, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from ep09_new import talk
    face = dict(face)
    joy = face.pop("_joy", 0)
    N = E.N
    pz = dict(pz)
    pz["root_yaw"] = yaw
    pose_noob(N, pz)
    N.root.location = loc
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    fn.update(M._face(NOOB_EYES, NOOB_EYE_DEFAULTS, face))
    talk(fn, E.mouth.get("noob", {}).get(int(round(t * FPS))))
    if joy:
        fn["m_arch"] = min(fn["m_arch"], -0.85)
        fn["m_vee"] = 0.0
    set_face(N.face, fn)


def _up(theta, yaw):
    """The body's long axis for a root turned (theta about x, then yaw): pitch 90 lies him face down, head forward."""
    th, y = math.radians(theta), math.radians(yaw)
    v = Vector((0, -math.sin(th), math.cos(th)))
    return Vector((v.x * math.cos(y) - v.y * math.sin(y), v.x * math.sin(y) + v.y * math.cos(y), v.z))


# ------------------------------------------------------------------ the Noob
def _fall_times():
    t_slide = b("tearoff") + 0.25
    land = b("fall") + 0.85
    return t_slide, land


def _land_yaw():
    return _yaw(SLIDE_D)                                          # head first, the way he was flung


def _slide_end(E):
    return E.n0 + SLIDE_D * 0.55 + Vector((0, 0, -0.35))


def _fall_split(E):
    """When the slide ends and the drop starts: the drop is a plain fall (no throw upward), timed to land on the beat."""
    t_slide, land = _fall_times()
    p1 = _slide_end(E)
    vd = 1.2
    dz = p1.z - 0.22
    T = (-vd + math.sqrt(vd * vd + 2 * 9.81 * dz)) / 9.81
    return max(t_slide + 0.25, land - T), vd


def _feet_land():
    y = _land_yaw()
    return RING - Vector((math.sin(math.radians(y)), -math.cos(math.radians(y)), 0)) * HC


def _noob_fall(E, t):
    """Off the neck: he slides down its side clawing at it, slips off and drops (arms windmilling, legs kicking),
    turning only as far as a belly-flop needs; head first, the way he was flung."""
    from mathutils import Euler
    N = E.N
    t_slide, land = _fall_times()
    t_drop, vd = _fall_split(E)
    q0 = Euler(E.n0_rot, "XYZ").to_quaternion()
    q1 = Euler((math.radians(90), 0, math.radians(_land_yaw())), "XYZ").to_quaternion()
    flail = {"arm_sl": {"fwd": 150 + 35 * math.sin(t * 13), "out": 45}, "arm_sr": {"fwd": 130 + 35 * math.sin(t * 13 + 2.2), "out": 55},
             "leg_sl": {"fwd": 25 * math.sin(t * 11)}, "leg_sr": {"fwd": -25 * math.sin(t * 11)}, "head_nod": -15}
    if t < t_drop:                                                 # the slide down the neck's side
        x = (t - t_slide) / (t_drop - t_slide)
        e = x * x
        p = E.n0 + SLIDE_D * 0.55 * e + Vector((0, 0, -0.35 * e))
        pz = _blend(E.e3_pz, flail, ss(0.0, 0.6, x))
        q = q0.slerp(q1, 0.2 * e)
    else:                                                          # the drop
        tau = t - t_drop
        T = land - t_drop
        p1 = _slide_end(E)
        L = _feet_land() + Vector((0, 0, 0.22))
        v1 = SLIDE_D * (2 * 0.55 / (t_drop - t_slide))
        acc = 2 * (Vector((L.x - p1.x, L.y - p1.y, 0)) - v1 * T) / (T * T)
        p = p1 + v1 * tau + acc * (0.5 * tau * tau)
        p.z = p1.z - vd * tau - 4.905 * tau * tau
        pz = flail
        u = tau / T
        q = q0.slerp(q1, 0.2 + 0.8 * (u * u * (3 - 2 * u)))
        if u > 0.75:                                               # bracing for the flop: arms forward
            pz = _blend(flail, {"arm_sl": {"fwd": 170, "out": 30}, "arm_sr": {"fwd": 170, "out": 30}}, ss(0.75, 1.0, u))
    M.set_noob(E, p, 0.0, pz, dict(_nf("shock")), t)
    N.root.rotation_mode = "QUATERNION"
    N.root.rotation_quaternion = q


def _nf(name):
    from ep09_new import NF
    return NF[name]


def _get_up(E, t):
    """Belly-flop on the ring (a squash, a bounce), then up in eight frames: a push off the floor, a hop about his
    middle onto his feet, a squash on landing. Returns True while it is running."""
    N = E.N
    _, land = _fall_times()
    dt = t - land
    y = _land_yaw()
    F = _feet_land()
    s0 = E.noob_scale0
    N.root.rotation_mode = "XYZ"
    if dt < 0.4:                                                   # flat on the ring
        pz = {"arm_sl": {"fwd": 170, "out": 30}, "arm_sr": {"fwd": 170, "out": 30}, "head_nod": -20}
        M.set_noob(E, F + Vector((0, 0, 0.1 * math.sin(min(dt, 0.22) / 0.22 * math.pi))), y, pz, dict(_nf("shock")), t)
        _lie(N.root, 90.0)
        sq = 1 - 0.14 * math.exp(-dt * 12)
        N.root.scale = (s0 / sq ** 0.5, s0 / sq ** 0.5, s0 * sq)
        return True
    if dt < 0.52:                                                  # the push: arms press down, the chest comes up
        u = ss(0.4, 0.52, dt)
        th = 90 - 18 * u
        pz = {"arm_sl": {"fwd": 170 - 80 * u, "out": 30 - 15 * u}, "arm_sr": {"fwd": 170 - 80 * u, "out": 30 - 15 * u},
              "head_nod": -20 - 10 * u}
        M.set_noob(E, F + Vector((0, 0, 0.22 * math.sin(math.radians(th)))), y, pz, dict(_nf("confused")), t)
        N.root.rotation_euler = (math.radians(th), 0, math.radians(y))
        return True
    if dt < 0.85:                                                  # the hop about his middle onto his feet
        u = ss(0.52, 0.85, dt)
        th = 72 * (1 - u)
        c0 = F + _up(72, y) * HC + Vector((0, 0, 0.22 * math.sin(math.radians(72))))
        c1 = RING + Vector((0, 0, HC))
        c = c0.lerp(c1, u) + Vector((0, 0, 0.3 * math.sin(math.pi * u)))
        feet = c - _up(th, y) * HC
        pz = {"arm_sl": {"fwd": 90 * (1 - u), "out": 15 + 55 * math.sin(math.pi * u)},
              "arm_sr": {"fwd": 90 * (1 - u), "out": 15 + 55 * math.sin(math.pi * u)},
              "leg_sl": {"fwd": 10 * math.sin(math.pi * u)}, "leg_sr": {"fwd": -6 * math.sin(math.pi * u)}}
        M.set_noob(E, feet, y, pz, dict(_nf("shock")), t)
        N.root.rotation_euler = (math.radians(th), 0, math.radians(y))
        return True
    return False


def _burst4(E, dt, span, seed):
    """He comes apart Roblox style: head, torso, both arms, both legs, each flung on its own (in world space, so no
    part drags another), tumbling, shrinking away to nothing exactly as he respawns (`span` after the death)."""
    if dt < 0:
        return
    bpy.context.view_layer.update()
    order = ["torso", "neck", "arm_sl", "arm_sr", "leg_sl", "leg_sr"]
    home = {k: E.burst_parts[k].matrix_world.copy() for k in order}
    rnd = random.Random(seed)
    away = Vector((E.N.root.location.x - CUBE.x, E.N.root.location.y - CUBE.y, 0)).normalized()
    a0 = math.atan2(away.y, away.x)
    s = 1.0 - ss(span - 0.28, span, dt)
    mid = Vector(E.N.root.location) + Vector((0, 0, 1.0))
    drag = 3.5                                                     # a pop: fast out of his middle, then slowing
    reach = (1 - math.exp(-drag * dt)) / drag
    for i, k in enumerate(order):
        loc, rot, sc = home[k].decompose()
        out = loc - mid
        out.z = 0
        out = out.normalized() if out.length > 1e-3 else away
        a = math.atan2(out.y, out.x) * 0.6 + a0 * 0.4 + math.radians(rnd.uniform(-35, 35))
        dev = _wrap(math.degrees(a - a0))                         # never back over the cube
        if abs(dev) > 75:
            a = a0 + math.radians(75 if dev > 0 else -75)
        sp = rnd.uniform(3.0, 4.2)
        v = Vector((math.cos(a) * sp, math.sin(a) * sp, rnd.uniform(2.4, 3.4) + (1.2 if k == "neck" else 0.0)))
        if k.startswith("leg"):
            v.z *= 0.6
        ax = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        w = rnd.uniform(7.0, 12.0) * (1 if rnd.random() < 0.5 else -1)
        pos = loc + v * reach + Vector((0, 0, -3.5 * dt * dt))
        pos.z = max(pos.z, 0.05)                                   # they hit the floor, they do not sink
        q = Quaternion(ax, w * dt) @ rot
        E.burst_parts[k].matrix_world = Matrix.LocRotScale(pos, q, sc * max(0.001, s))
        if i == 0:
            bpy.context.view_layer.update()
    for ob in E.N.root.children_recursive:
        ob.hide_render = s < 0.02
    _dark_cube(E, dt, Vector(E.N.root.location))


def _burst_reset4(E):
    E3._burst_reset(E)
    for k, o in E.burst_parts.items():
        o.scale = E.burst_scale[k]


def noob(E, t):
    N = E.N
    _burst_reset4(E)
    E.N.root.rotation_mode = "XYZ"
    face = dict(_nf("happy"))
    pz = {"arm_sl": {"out": 8, "fwd": 4}, "arm_sr": {"out": 8, "fwd": 4}}
    t_slide, land = _fall_times()
    cube_c = cube_centre(E, t) or CUBE
    if t < t_slide:                                               # on the neck, jolted by the shudder
        _use(E, 3)
        E3.noob(E, E.T3)
        _use(E, 4)
        if t > b("tearoff"):
            N.root.location = Vector(N.root.location) + Vector((0, 0, 0.12 * math.sin((t - b("tearoff")) * 40)))
        return
    if t < land:
        _noob_fall(E, t)
        return
    if _get_up(E, t):
        return
    up_t = land + 0.85                                            # on his feet
    _squash(E, t - up_t, grow=False)
    p, yaw = RING.copy(), _land_yaw()
    if t < b("crystal") + 1.05:                                   # looks up at the dragon being sealed
        dragon_up = Vector(E.D.root.location) + Vector((0, 0, 0.5))
        yaw = _turn_to(_land_yaw(), _face_to(RING, dragon_up), 0.45 * ss(up_t + 0.1, up_t + 0.5, t))
        tl, nd = _look(yaw, p, dragon_up, h=1.4)
        k = ss(up_t + 0.05, up_t + 0.35, t)
        pz["head_turn"], pz["head_nod"] = tl * k, nd * k
        pz["chest_lean"] = -6 * k
        face = dict(_nf("awe"))
    elif t < b("noob_secret"):                                    # spots the cube; hurries over
        t0 = b("crystal") + 1.05
        y0 = _turn_to(_land_yaw(), _face_to(RING, Vector(E.D.root.location)), 0.45)
        yaw = _turn_to(y0, _face_to(RING, N_LOOK), ss(t0, t0 + 0.2, t))
        p = _stride(pz, t, t0 + 0.05, b("noob_secret") - 0.02, RING, N_LOOK, amp=26, stride=0.45)
        face = dict(GRIN)
    elif t < b("poke1"):                                          # "A secret block!": bent over it, bouncing, delighted
        p = N_LOOK.copy()
        yaw = _face_to(p, cube_c)
        cr = ss(b("noob_secret"), b("noob_secret") + 0.3, t)
        tl, nd = _look(yaw, p, cube_c, h=1.4)
        pz.update({"chest_lean": 14 * cr, "head_nod": nd * 0.5 * cr, "head_turn": tl,
                   "arm_sl": {"fwd": 35 * cr, "out": 22}, "arm_sr": {"fwd": 35 * cr, "out": 22}})
        if t < b("noob_secret", 1):
            p = p + Vector((0, 0, 0.04 * abs(math.sin((t - b("noob_secret")) * 9))))
        face = dict(JOY)
        if t >= b("lean"):                                        # a hand hovers toward it
            r = ss(b("lean"), b("lean") + 0.35, t)
            pz["arm_sr"] = {"fwd": 35 + 20 * r, "out": 14}
            face = dict(GRIN)
        if b("steve_touch") <= t:                                 # a glance back at Steve, the hand still hovering
            g = ss(b("steve_touch") + 0.4, b("steve_touch") + 0.8, t) * (1 - ss(b("steve_touch", 1) - 0.2, b("poke1"), t))
            tl2, nd2 = _look(yaw, p, gp(E, STEVE_EDGE) + Vector((0, 0, 1.6)), h=1.2)
            pz["head_turn"] = lerp(tl, tl2, g)
            pz["head_nod"] = lerp(pz["head_nod"], nd2, g)
            face = dict(GRIN)
    elif t < b("die1"):                                           # one step in and a poke with one hand; zapped
        p = _stride(pz, t, b("poke1"), b("poke1") + 0.25, N_LOOK, POKE_N, amp=18, stride=0.4)
        yaw = _face_to(p, cube_c)
        poke = ss(b("poke1") + 0.18, b("poke1") + 0.28, t)
        pz["chest_lean"] = 14 + 10 * poke
        pz["arm_sr"] = {"fwd": 55 - 15 * ss(b("poke1"), b("poke1") + 0.15, t) + 25 * poke, "out": 6}
        tl, nd = _look(yaw, p, cube_c, h=1.4)
        pz["head_nod"] = nd * 0.5
        face = dict(GRIN)
        if t >= b("poke1") + 0.3:                                 # zapped: a jolt through him
            z = math.sin(t * 90)
            pz["chest_lean"] = 14 + 4 * z
            pz["arm_sl"] = {"fwd": 30 + 15 * z, "out": 50 + 10 * z}
            pz["arm_sr"] = {"fwd": 80 + 8 * z, "out": 6}
            face = dict(_nf("shock"))
    elif t < b("respawn1") - 0.06:                                # bursts (the parts last up to the respawn's flash)
        p = POKE_N.copy()
        yaw = _face_to(p, cube_c)
        M.set_noob(E, p, yaw, {"arm_sr": {"fwd": 80}, "arm_sl": {"fwd": 30, "out": 55}, "chest_lean": 14}, dict(_nf("shock")), t)
        _burst4(E, t - b("die1"), b("respawn1") - b("die1"), 11)
        return
    elif t < b("chop") + 0.7:
        r1 = b("respawn1") - 0.06
        p = RING.copy()
        yaw = _face_to(RING, cube_c)
        face = dict(GRIN)
        _squash(E, t - r1)
        if t < b("noob_again"):
            if t < b("noob_touched2", 1) + 0.3:                   # "I touched it!": a fist pump, bouncing
                k = ss(r1 + 0.35, r1 + 0.55, t) * (1 - ss(b("noob_touched2", 1), b("noob_touched2", 1) + 0.3, t))
                pump = math.sin((t - r1) * 14)
                pz["arm_sr"] = {"fwd": 10, "out": 8 + (130 + 15 * pump) * k}
                pz["chest_lean"] = -4 * k
                p = p + Vector((0, 0, 0.05 * k * abs(pump)))
                face = dict(JOY)
            else:                                                 # pleased with himself, looking at it
                tl, nd = _look(yaw, p, cube_c, h=1.4)
                k = ss(b("noob_touched2", 1) + 0.2, b("stare"), t)
                pz["head_turn"], pz["head_nod"] = tl * k, nd * k
                pz["arm_sl"] = {"fwd": 6, "out": 10}
                pz["arm_sr"] = {"fwd": 6, "out": 10}
                pz["head_tilt"] = 8 * math.sin(t * 1.3)
        else:                                                     # "Again!": arms up, then off he goes: the karate chop
            r0 = b("noob_again") + 0.55
            face = dict(JOY)
            if t < r0:
                k = ss(b("noob_again"), b("noob_again") + 0.15, t)
                pz["arm_sl"] = {"fwd": 20, "out": 8 + 130 * k}
                pz["arm_sr"] = {"fwd": 20, "out": 8 + 130 * k}
                p = p + Vector((0, 0, 0.15 * math.sin(math.pi * ss(b("noob_again") + 0.05, b("noob_again") + 0.4, t))))
            else:
                p = _stride(pz, t, r0, b("chop") + 0.2, RING, CHOP_N, amp=30, stride=0.55)
                yaw = _face_to(RING, CHOP_N) if t < b("chop") + 0.1 else _face_to(p, cube_c)
                if t >= b("chop") + 0.12:
                    up_ = ss(b("chop") + 0.12, b("chop") + 0.3, t)
                    dn = ss(b("chop") + 0.3, b("chop") + 0.38, t)
                    pz["arm_sr"] = {"fwd": 40 + 125 * up_ - 95 * dn, "out": 6}
                    pz["arm_sl"] = {"fwd": 10, "out": 12}
                    pz["chest_lean"] = 4 + 14 * dn
                if t >= b("chop") + 0.4:
                    z = math.sin(t * 90)
                    pz["chest_lean"] = 18 + 4 * z
                    pz["arm_sl"] = {"fwd": 30 + 15 * z, "out": 50 + 10 * z}
                    face = dict(_nf("shock"))
    elif t < b("respawn2") - 0.06:                                # bursts again
        p = CHOP_N.copy()
        yaw = _face_to(p, cube_c)
        M.set_noob(E, p, yaw, {"arm_sr": {"fwd": 70}, "arm_sl": {"fwd": 30, "out": 55}, "chest_lean": 18}, dict(_nf("shock")), t)
        _burst4(E, t - b("die2"), b("respawn2") - b("die2"), 12)
        return
    elif t < b("react"):                                          # back; looks up at the huge cube; winds up again
        r2 = b("respawn2") - 0.06
        _squash(E, t - r2)
        p = _stride(pz, t, r2 + 0.75, r2 + 1.4, RING, WIND_N, amp=22, stride=0.45)
        yaw = _face_to(RING, cube_c) if t < r2 + 0.75 else _face_to(p, cube_c)
        face = dict(_nf("awe")) if t < r2 + 0.75 else dict(GRIN)
        if t < r2 + 0.75:
            tl, nd = _look(yaw, p, cube_c + Vector((0, 0, 0.5)), h=1.4)
            pz["head_turn"], pz["head_nod"] = tl, nd
            pz["chest_lean"] = -5
        wind = ss(r2 + 1.4, r2 + 1.75, t)
        arm = {"fwd": 8 + 150 * wind, "out": 10}
        lean = -6 * wind
        P_ = Vector(E.PA.root.location)
        portal = Vector((-1.6, 4.4, 3.0))
        if t >= b("patch_in"):                                    # the portal flickers: he turns his head to it,
            k = ss(b("patch_in"), b("patch_in") + 0.35, t)        # the raised arm sagging, wobbling
            tgt = portal if P_.z < -100 else P_
            tl, nd = _look(yaw, p, tgt, h=1.4, lim=75)
            pz["head_turn"], pz["head_nod"] = tl * k, nd * k
            arm = {"fwd": 158 - 30 * k + 6 * math.sin(t * 5), "out": 10}
            face = dict(_nf("confused"))
        fl = ss(b("patch_in") + 1.5, b("patch_in") + 1.7, t)      # Patch stops in his face: a flinch, hands up
        if fl > 0:
            arm = _blend(arm, {"fwd": 75, "out": -4}, fl)
            pz["arm_sl"] = _blend(pz.get("arm_sl", {}), {"fwd": 65, "out": -4}, fl)
            lean = lean * (1 - fl) - 12 * fl
            face = dict(_nf("shock"))
        if t >= b("patch_stop"):                                  # "Please stop doing that.": hands down, head tilted,
            k = ss(b("patch_stop") + 0.3, b("patch_stop") + 1.0, t)   # leaning in to look at the talking thing
            arm = _blend(arm, {"fwd": 6, "out": 8}, k)
            pz["arm_sl"] = _blend(pz.get("arm_sl", {}), {"fwd": 6, "out": 8}, k)
            lean = lerp(lean, 7, k)
            pz["head_tilt"] = 14 * k
            face = dict(_nf("confused"))
        pz["arm_sr"] = arm
        pz["chest_lean"] = pz.get("chest_lean", 0) + lean
    else:                                                         # the hop back; then with Patch
        hop = ss(b("react"), b("react") + 0.3, t)
        p = WIND_N.lerp(REACT_N, hop) + Vector((0, 0, 0.22 * math.sin(math.pi * hop)))
        P_ = Vector(E.PA.root.location)
        yaw = _face_to(p, P_)
        tl, nd = _look(yaw, p, P_, h=1.4)
        pz["head_turn"], pz["head_nod"] = tl, nd
        pz["arm_sl"] = {"fwd": 20 * (1 - hop) + 6, "out": 8 + 40 * math.sin(math.pi * hop)}
        pz["arm_sr"] = {"fwd": 20 * (1 - hop) + 6, "out": 8 + 40 * math.sin(math.pi * hop)}
        face = dict(_nf("shock")) if t < b("noob_cube") - 0.1 else dict(GRIN)
        if b("noob_cube") - 0.15 <= t < b("patch_name"):          # "A talking cube!": one hand pointing at it, the other
            k = ss(b("noob_cube") - 0.15, b("noob_cube") + 0.1, t) * (1 - ss(b("noob_cube", 1), b("patch_name"), t))
            d = P_ - (p + Vector((0, 0, 1.45)))                   # up waving, bouncing on his toes
            elev = math.degrees(math.atan2(d.z, Vector((d.x, d.y, 0)).length))
            pz["arm_sr"] = _blend(pz["arm_sr"], {"fwd": 90 + elev, "out": 4}, k)
            pz["arm_sl"] = _blend(pz["arm_sl"], {"fwd": 15, "out": 140 + 18 * math.sin(t * 11)}, k)
            p = p + Vector((0, 0, 0.05 * k * abs(math.sin(t * 8))))
            face = dict(JOY)
        if b("patch_name") <= t < b("scan") + 0.3:                # listening, delighted
            face = dict(GRIN)
            pz["head_tilt"] = 10
        if b("scan") + 0.3 <= t < b("patch_feed"):                # watching the scan
            tl2, nd2 = _look(yaw, p, cube_centre(E, t), h=1.4)
            k = ss(b("scan") + 0.3, b("scan") + 0.6, t) * (1 - ss(b("patch_feed") - 0.3, b("patch_feed"), t))
            pz["head_turn"], pz["head_nod"] = lerp(tl, tl2, k), lerp(nd, nd2, k)
            face = dict(_nf("awe"))
        if b("patch_feed") <= t < b("noob_helping") - 0.1:        # listening: it is his doing; a grin grows
            face = dict(_nf("awe")) if t < b("patch_grows") + 0.6 else dict(GRIN)
            pz["head_tilt"] = 6 * math.sin(t * 0.8)
        if b("noob_helping") - 0.1 <= t < b("turn"):              # "So I'm helping!": chest out, a fist up, a hop
            k = ss(b("noob_helping") - 0.1, b("noob_helping") + 0.12, t)
            pz["arm_sr"] = {"fwd": 10 + 100 * k, "out": 12}
            pz["arm_sl"] = {"fwd": 6, "out": 10}
            pz["chest_lean"] = -8 * k
            p = p + Vector((0, 0, 0.14 * math.sin(math.pi * ss(b("noob_helping") - 0.1, b("noob_helping") + 0.25, t))))
            face = dict(JOY)
            if t >= b("sigh"):                                    # Steve: "No." He looks at him, still grinning
                k2 = ss(b("sigh"), b("sigh") + 0.4, t)
                pz["arm_sr"] = _blend(pz["arm_sr"], {"fwd": 6, "out": 10}, k2)
                tl2, nd2 = _look(yaw, p, gp(E, STEVE_BACK) + Vector((0, 0, 1.6)), h=1.4, lim=75)
                pz["head_turn"], pz["head_nod"] = lerp(tl, tl2, k2), lerp(nd, nd2, k2)
                face = dict(GRIN)
        if t >= b("turn") + 0.3:                                  # the smile goes
            face = dict(_nf("confused")) if t < b("noob_doyou") else dict(_nf("worried"))
            pz["chest_lean"] = 3
            if t >= b("patch_deleted"):
                face = {"both_h": 1.9, "both_w": 1.05, "m_arch": 0.15, "both_ps": 0.8}
            if t >= b("hold"):                                    # stunned: a slow blink, a breath
                bl = math.exp(-((t - b("hold") - 0.75) / 0.06) ** 2)
                face["both_h"] = lerp(face["both_h"], 0.15, bl)
                pz["chest_lean"] = 3 + 1.5 * math.sin((t - b("hold")) * 2.2)
    pz = life(E, "noob", pz, face, t, 1.6)
    if face.get("_joy"):
        _set_noob(E, p, yaw, pz, face, t)
    else:
        M.set_noob(E, p, yaw, pz, face, t)


def _squash(E, dt, grow=True):
    """Popping back onto the ring: grown out of the ring's flash in 3 frames, a stretch, a squash, settled."""
    N = E.N
    s0 = E.noob_scale0
    if dt < 0:
        return
    keys = [(0.0, 1.15), (0.12, 0.9), (0.33, 1.0)]
    z = 1.0
    for (a, za), (c, zc) in zip(keys, keys[1:]):
        if a <= dt < c:
            z = lerp(za, zc, ss(a, c, dt))
    g = (0.3 + 0.7 * ss(0.0, 0.12, dt)) if grow else 1.0
    N.root.scale = (g * s0 / z ** 0.5, g * s0 / z ** 0.5, g * s0 * z)


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
RELAX_R = {"fwd": 16, "out": 9, "elbow": 28}                       # the pickaxe hanging at his side
RELAX_L = {"fwd": 6, "out": 7, "elbow": 14}


def _blink(face, t, at, steve=True):
    bl = math.exp(-((t - at) / 0.05) ** 2)
    if bl > 0.05:
        for k in ("both_to", "both_tm", "both_ti"):
            face[k] = lerp(face.get(k, 0.0), -1.0, bl)


def steve(E, t):
    from ep09_new import SF
    S = E.S
    if t < b("tearoff"):
        _use(E, 3)
        E3.steve(E, E.T3)
        _use(E, 4)
        return
    face = dict(SF["flat"])
    pz = {"arm_sr": dict(RELAX_R), "arm_sl": dict(RELAX_L)}
    p0 = gp(E, E3.STEVE_PLAN)
    clear = gp(E, STEVE_CLEAR)
    p, yaw = p0.copy(), 35.0
    up = Vector(E.D.root.location) + Vector((0, 0, 1))
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.5))           # his head, more or less
    if N_.z < -100 or N_.z > 4.0:
        N_ = RING + Vector((0, 0, 1.5))
    cube_c = cube_centre(E, t) or CUBE
    w0, w1 = b("crystal") + 1.0, b("crystal") + 2.6
    breath = math.sin(2 * math.pi * 0.27 * t)
    if t < w0:                                                    # backs out from under the shuddering dragon,
        p = _stride(pz, t, b("tearoff") + 0.15, b("fall") + 0.5, p0, clear, steve=True)   # watching the Noob fall
        yaw = _turn_to(35.0, _face_to(clear, RING), ss(b("tearoff") + 0.1, b("fall") + 0.6, t))
        tgt_k = ss(b("crystal") - 0.1, b("crystal") + 0.4, t)
        tl, nd = _look_mix(yaw, p, N_, up, tgt_k)
        pz["head_turn"], pz["head_nod"] = tl, nd
        flinch = math.exp(-((t - (b("fall") + 0.85)) / 0.12) ** 2)
        pz["chest_lean"] = pz.get("chest_lean", 0) - 10 * flinch
        face = dict(SF["stunned"]) if t < b("crystal") + 0.4 else dict(SF["worried"])
    elif t < w1:                                                  # to the pad's west edge
        yaw = _turn_to(_face_to(clear, RING), _face_to(clear, STEVE_EDGE), ss(w0, w0 + 0.25, t))
        p = _stride(pz, t, w0 + 0.1, w1, clear, STEVE_EDGE, steve=True)
        tl, nd = _look(yaw, p, N_)
        pz["head_turn"], pz["head_nod"] = tl * 0.6, nd * 0.4
        face = dict(SF["worried"])
    else:
        p = STEVE_EDGE.copy()
        yaw = _turn_to(_face_to(clear, STEVE_EDGE), _face_to(p, N_), ss(w1, w1 + 0.3, t))
        tl, nd = _look(yaw, p, N_)
        pz["head_turn"], pz["head_nod"] = tl, nd
        if t < b("poke1"):                                        # "It fell off the dragon. Don't touch it."
            k = ss(b("steve_touch"), b("steve_touch") + 0.3, t) * (1 - ss(b("steve_touch", 1), b("poke1"), t))
            pz["chest_lean"] = 10 * ss(b("lean"), b("lean") + 0.4, t)
            wag = math.sin(t * 9)                                  # the left hand out, palm up, wagging "no"
            pz["arm_sl"] = {"fwd": 8 + 55 * k, "out": 8 + 10 * k + 8 * wag * k, "elbow": 14 + 20 * k + 14 * wag * k}
            face = dict(SF["worried"])
        elif t < b("stare"):                                      # the poke: a reach, too late; the flinch
            k = ss(b("poke1"), b("poke1") + 0.25, t)
            pz["arm_sl"] = {"fwd": 75 * k + 6, "out": 10, "elbow": 14}
            fl = math.exp(-((t - b("die1") - 0.05) / 0.1) ** 2)
            pz["chest_lean"] = 10 * k - 12 * fl
            face = dict(SF["scared"]) if t < b("respawn1") + 0.5 else dict(SF["stunned"])
            if t >= b("respawn1") + 0.3:
                tl2, nd2 = _look(yaw, p, cube_c)
                k2 = ss(b("respawn1") + 0.3, b("respawn1") + 0.6, t)
                pz["head_turn"], pz["head_nod"] = lerp(tl, tl2, k2), lerp(nd, nd2, k2)
        elif t < b("noob_again"):                                 # he stares at the bigger cube: "...It grew."
            tl, nd = _look(yaw, p, cube_c)
            pz["head_turn"], pz["head_nod"] = tl, nd
            face = dict(SF["stunned"]) if t < b("steve_grew") else dict(SF["flat"])
        elif t < b("respawn2") + 0.4:                             # the lunge: a step, an arm out, too late
            lu = ss(b("chop") - 0.1, b("chop") + 0.25, t) * (1 - ss(b("die2") + 0.2, b("respawn2") + 0.4, t))
            p = STEVE_EDGE + Vector((-0.35, -0.05, 0)) * lu
            pz["arm_sl"] = {"fwd": 85 * lu + 6, "out": 10, "elbow": 14}
            pz["chest_lean"] = 18 * lu
            face = dict(SF["scared"])
        elif t < b("react"):                                      # the portal flickers: he looks; then Patch
            P_ = Vector(E.PA.root.location)
            tgt = Vector((-1.6, 4.4, 3.3)) if P_.z < -100 else P_
            k = ss(b("patch_in") - 0.05, b("patch_in") + 0.3, t)
            tl, nd = _look_mix(yaw, p, cube_c, tgt, k, lim=80)
            pz["head_turn"], pz["head_nod"] = tl, nd
            face = dict(SF["stunned"]) if t >= b("patch_in") + 0.4 else dict(SF["worried"])
        else:                                                     # the jump back into a guard; wary, then listening
            P_ = Vector(E.PA.root.location)
            jb = ss(b("react"), b("react") + 0.25, t)
            p = STEVE_EDGE.lerp(STEVE_BACK, jb) + Vector((0, 0, 0.12 * math.sin(math.pi * jb)))
            y_p = _face_to(p, P_)
            low = ss(b("patch_name") + 0.3, b("patch_name") + 1.3, t)
            guard_r = {"fwd": 30, "out": 20, "elbow": 14}
            pz["arm_sr"] = _blend(guard_r, RELAX_R, low)
            pz["arm_sl"] = _blend({"fwd": 40, "out": 26, "elbow": 40}, RELAX_L, low)
            pz["hips_drop"] = 0.15 * (1 - low)
            pz["chest_lean"] = -6 * (1 - low)
            # where he looks (eased, never snapped): Patch; the cube while it is scanned; the Noob on "No."
            k_cube = ss(b("scan") + 0.3, b("scan") + 0.6, t) * (1 - ss(b("patch_feed") - 0.3, b("patch_feed"), t))
            k_noob = ss(b("sigh"), b("sigh") + 0.45, t) * (1 - ss(b("turn") + 0.1, b("turn") + 0.5, t))
            yaw = _turn_to(y_p, _face_to(p, N_), 0.5 * k_noob)      # the torso turns with the look
            tl, nd = _look(yaw, p, P_, lim=70)
            tl2, nd2 = _look(yaw, p, cube_c, lim=70)
            tl3, nd3 = _look(yaw, p, N_, lim=70)
            tl, nd = lerp(tl, tl2, k_cube), lerp(nd, nd2, k_cube)
            tl, nd = lerp(tl, tl3, k_noob), lerp(nd, nd3, k_noob)
            pz["head_turn"], pz["head_nod"] = tl, nd
            face = dict(SF["scared"]) if t < b("noob_cube") else dict(SF["worried"])
            if b("patch_name") + 0.5 <= t < b("sigh"):
                face = dict(SF["flat"]) if t < b("scan") else dict(SF["worried"])
            if b("sigh") <= t < b("turn"):                        # the pickaxe sinks, a breath out: "No."
                d = ss(b("sigh"), b("sigh") + 0.4, t)
                pz["arm_sr"] = _blend(RELAX_R, {"fwd": 8, "out": 6, "elbow": 18}, d)
                drop = ss(b("steve_no"), b("steve_no") + 0.2, t)        # the shoulders drop on the word
                pz["chest_lean"] = 2 * d + 3 * drop
                pz["head_nod"] = pz["head_nod"] + 3 * drop
                for arm in ("arm_sl", "arm_sr"):
                    pz[arm] = dict(pz[arm])
                    pz[arm]["out"] = pz[arm].get("out", 8) - 3 * drop
                face = dict(SF["flat"])
                _blink(face, t, b("steve_no") + 0.08)
            if t >= b("turn"):                                    # tense, the pickaxe low, watching it
                face = dict(SF["worried"])
                pz["arm_sr"] = {"fwd": 14, "out": 8, "elbow": 30}
                pz["chest_lean"] = 2
            if t >= b("patch_deleted"):
                face = dict(SF["stunned"])
            if t >= b("hold") + 1.3:                              # the glance: alarmed, a look to the Noob, a blink
                g = ss(b("hold") + 1.3, b("hold") + 1.55, t)
                tl3, nd3 = _look(yaw, p, N_, lim=70)
                pz["head_turn"] = lerp(pz["head_turn"], tl3, g)
                pz["head_nod"] = lerp(pz["head_nod"], nd3, g)
                pz["chest_lean"] = 2 - 4 * g
                face = dict(SF["scared"])
                _blink(face, t, b("hold") + 1.9)
    pz["chest_lean"] = pz.get("chest_lean", 0) + 1.3 * breath     # breathing
    for arm in ("arm_sl", "arm_sr"):
        a_ = dict(pz.get(arm, {}))
        a_["out"] = a_.get("out", 8) + 1.2 * breath
        pz[arm] = a_
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
    if shot == "cube":                                            # the Noob, pointing at it: "A talking cube!"
        return REACT_N + _c(2.3, -2.7, 1.45), REACT_N + _c(0.35, -0.2, 1.45), 32, 2.8, None, 0.25
    if shot == "name":                                            # Patch, three-quarter: "I'm Patch."
        return _c(-6.9, -3.2, 1.5), P_STOP + _c(0, 0, 0.05), 42, 2.8, None, 0.2
    if shot == "scan":                                            # the scan: from the west, Patch clear of Steve, the cone
        return _c(-4.6, -7.5, 1.4), _c(-4.6, -2.2, 1.1), 28, 30, None, 0.2   # down into the huge cube (from the south:
                                                                  # the Noob left, the cube, Patch, Steve right)
    if shot == "feed":                                            # Patch talking to the Noob: from the Noob's side, so its
        c = P_SCAN + (REACT_N - P_SCAN) * 0.6 + _c(0, -0.6, 0)      # screen faces us (never its blank side); south of
        return _c(c.x, c.y, 1.72), P_SCAN + _c(0, 0, 0.05), 40, 2.8, None, 0.2   # the cube's corner, out of shot
    if shot == "helping":                                         # the Noob, proud
        return REACT_N + _c(0.8, -3.2, 1.5), REACT_N + _c(0, 0, 1.45), 34, 2.8, None, 0.2
    if shot == "no":                                              # Steve: "No."
        return _c(-4.0, -0.45, 1.5), STEVE_BACK + _c(0, 0, 1.45), 34, 2.8, None, 0.15   # from the Noob's side: his look
                                                                  # at the Noob comes toward us
    if shot == "turn":                                            # over the Noob's shoulder: Patch whips round, drifts in
        n = REACT_N + _c(0, 0, 1.75)
        d = (n - P_TURN)
        d.z = 0
        d.normalize()
        r = Vector((-d.y, d.x, 0))
        loc = n + d * 1.25 - r * 0.55 + _c(0, 0, 0.12)
        P_ = Vector(E.PA.root.location) if E.PA.root.location.z > -100 else P_TURN
        look = P_.lerp(n, 0.2) + _c(0, 0, -0.05)
        return loc, look, 50, 2.8, (P_ - loc).length, 0.1
    if shot == "doyou":                                           # the reverse: over Patch's shoulder, the Noob, the
        n = REACT_N + _c(0, 0, 1.7)                                # smile gone
        d = P_TURN - n
        d.z = 0
        d.normalize()
        r = Vector((-d.y, d.x, 0))
        loc = P_TURN + d * 1.8 + r * 1.3 + _c(0, 0, 0.05)
        return loc, n.lerp(P_TURN, 0.12), 45, 2.6, (n - loc).length, 0.1
    if shot == "two":                                             # a slow push in: the Noob left, Patch right, the sky between
        a = _c(-9.0, -6.0, 1.3)
        c = _c(-8.5, -5.3, 1.38)
        return a.lerp(c, u), _c(-3.5, 1.5, 3.0), 28, 30, None, 0.05
    if shot == "stunned":                                         # the Noob's stunned face: a slow push in
        a, look = REACT_N + _c(-0.5, -3.1, 1.55), REACT_N + _c(0, 0, 1.6)   # (from the west: Patch out of shot)
        return a.lerp(look, 0.12 * ss(t0, t1, t)), look, 42, 2.6, None, 0.12
    if shot == "glance":                                          # Steve's alarmed glance: a slow push in
        a, look = STEVE_BACK + _c(-2.6, -1.8, 1.5), STEVE_BACK + _c(0, 0, 1.5)
        return a.lerp(look, 0.12 * ss(t0, t1 if t1 < 1e8 else t0 + 1.2, t)), look, 42, 2.8, None, 0.12
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
