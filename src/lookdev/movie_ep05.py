"""The movie, chapter 5 ("Noob Found Creative Mode"), in the new look and in 16:9.

The creator's notes (2026-11-27, story/movie/ep05_shots.md): it picks up Episode 4's last instant (the twist: the
Noob stunned on the blue terrace, Patch facing him, the 1.45 m glitch cube humming at the terrace's corner, Steve
on the grey pad, the dragon sealed in crystal overhead, REALITY 85%). The Noob pokes the cube a third time: it
implodes into his hand as a BTools hammer ("Since the block!"). He builds: a giant duck on the white spawn plate,
a giant statue of himself on the checkpoint, a toy castle on the violet ledge, a door at the terrace's edge that
opens onto the sky ("Close enough!"). Then the world starts deleting what doesn't belong, one rule for every
erasure (checkerboard top to bottom, sliced into nothing): the duck, the castle, the statue; then the original
course itself. The dragon glitches but stays and the door stays (Episode 6 erases them).
Sound and timing: episodes/movie_ep05_creative_mode.json.

    python src/lookdev/movie_ep05.py TIMELINE VOICE TEX_DIR ASSETS OUT_DIR [--times 1.0,5.0] [--res 720]
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
import movie_ep04 as E4                                               # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402

B = M.B
_yaw, _wrap, _clamp, _cr = E2._yaw, E2._wrap, E2._clamp, E2._cr
life = E2.life
gp = E3.gp
_face_to, _look, _run = E3._face_to, E3._look, E3._run
EP4_TL = os.path.join(HERE, "..", "..", "movie", "ep04", "timeline.json")

# ------------------------------------------------------------------ the place (Ep3's obby; metres, z up)
REACT_N = E4.REACT_N                     # the Noob at Ep4's end (-6.95, -0.8)
STEVE0 = E4.STEVE_BACK                   # Steve at Ep4's end (-2.1, -1.3)
P_TWIST = E4.P_TWIST                     # Patch at Ep4's end (-5.45, -3.0, 1.85)
CUBE_C = E4.CUBE + Vector((0, 0, E4.HOVER + E4.SIZES[2] / 2))   # the cube's centre at Ep4's end
N_POKE = Vector((-5.95, -1.3, 0.0))      # the third poke (the cube is 1.45 m now)
N_BUILD = Vector((-5.35, -1.55, 0.0))    # where he builds from (where the cube was)
DUCK_AT = E4.RING + Vector((0.0, 0.15, 0.06))   # the duck: on the white spawn ring beside him (Ep4's checkpoint)
PLATE = DUCK_AT
CP_TOP = Vector((8.0, -1.0, 0.5))        # the checkpoint's top: the statue's place
LEDGE_TOP = Vector((-9.0, 2.9, 1.1))     # the violet ledge's top (its west end): the castle's place
DOOR_HINGE = Vector((-8.08, -2.2, 0.08)) # the door's hinge foot (the sill's top is 0.04, the leaf 4 cm above it)
DOOR_W, DOOR_H = 0.92, 2.0
N_DOOR = Vector((-6.75, -1.95, 0.0))     # the Noob beside the door, reaching its handle
STEVE_D = Vector((-2.35, -1.2, 0.0))     # Steve's half step back from the duck
P_WATCH = Vector((-4.7, -3.3, 2.05))     # Patch watching the builds (clear of the cameras)
P_PLATE = Vector((-6.2, -1.3, 2.4))      # Patch over the empty ring, scanning down
STATUE_K = 4.2                           # the statue: the Noob 4.2 times over


def b(name, i=0):
    return B[name][i]


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    t4 = json.load(open(EP4_TL))
    E = E4.build(t4, tex_dir, assets, res, samples)              # Episode 4's world, rigs and props
    E.B5 = {k: tuple(v) for k, v in tl["beats"].items()}
    E.T4 = t4["length"]
    from roblox import Gizmos
    E.giz = Gizmos(E.sc.collection)
    _erase_material(E)
    _hammer(E)
    _duck(E)
    _statue(E)
    _castle(E)
    _door(E)
    _scan_plane(E)
    _pixels(E)
    E.prepped5 = False
    return E


def _use(E, which):
    B.clear()
    B.update(E.B3 if which == 3 else E.B4 if which == 4 else E.B5)


def _erase_material(E):
    """The one erase rule, for every deleted thing: above a front sweeping down it turns pink-and-black checkerboard
    (glowing), and above a second front trailing it, it is gone (transparent); a ragged edge (noise). The same
    material builds things too: below a rising scan line, solid; above it, nothing yet; a cyan glow on the line.
    Per object: e_hi (the checker front), e_cut (the cut), e_line (the scan line), world z; the colour from the
    object's colour (Roblox parts are coloured that way)."""
    m = bpy.data.materials.new("erase")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    N, L = nt.nodes.new, nt.links.new
    geo = N("ShaderNodeNewGeometry")
    sep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0])
    nz = N("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    L(geo.outputs["Position"], nz.inputs["Vector"])
    rag = N("ShaderNodeMath")
    rag.operation = "MULTIPLY_ADD"                                # z + (noise - 0.5) * 0.25
    L(nz.outputs["Fac"], rag.inputs[0])
    rag.inputs[1].default_value = 0.25
    rag.inputs[2].default_value = -0.125
    z = N("ShaderNodeMath")
    z.operation = "ADD"
    L(sep.outputs["Z"], z.inputs[0])
    L(rag.outputs[0], z.inputs[1])

    def attr(name):
        a = N("ShaderNodeAttribute")
        a.attribute_type = "OBJECT"
        a.attribute_name = name
        return a.outputs["Fac"]

    def gt(a, b_):
        g = N("ShaderNodeMath")
        g.operation = "GREATER_THAN"
        L(a, g.inputs[0])
        L(b_, g.inputs[1])
        return g.outputs[0]

    ck_mask = gt(z.outputs[0], attr("e_hi"))
    cut_mask = gt(z.outputs[0], attr("e_cut"))
    oi = N("ShaderNodeObjectInfo")
    bs = N("ShaderNodeBsdfPrincipled")
    L(oi.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.4
    tc = N("ShaderNodeTexCoord")
    ck = N("ShaderNodeTexChecker")
    ck.inputs["Color1"].default_value = (1.0, 0.0, 0.85, 1)
    ck.inputs["Color2"].default_value = (0.01, 0.0, 0.01, 1)
    ck.inputs["Scale"].default_value = 4.0
    L(tc.outputs["Object"], ck.inputs["Vector"])
    em = N("ShaderNodeEmission")
    L(ck.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 2.2
    m1 = N("ShaderNodeMixShader")
    L(ck_mask, m1.inputs[0])
    L(bs.outputs[0], m1.inputs[1])
    L(em.outputs[0], m1.inputs[2])
    # the scan line (building): a thin cyan glow band at e_line
    d = N("ShaderNodeMath")
    d.operation = "SUBTRACT"
    L(sep.outputs["Z"], d.inputs[0])
    L(attr("e_line"), d.inputs[1])
    ab = N("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    L(d.outputs[0], ab.inputs[0])
    band = N("ShaderNodeMath")
    band.operation = "LESS_THAN"
    L(ab.outputs[0], band.inputs[0])
    band.inputs[1].default_value = 0.035
    em2 = N("ShaderNodeEmission")
    em2.inputs["Color"].default_value = (0.3, 0.9, 1.0, 1)
    em2.inputs["Strength"].default_value = 6.0
    m2 = N("ShaderNodeMixShader")
    L(band.outputs[0], m2.inputs[0])
    L(m1.outputs[0], m2.inputs[1])
    L(em2.outputs[0], m2.inputs[2])
    tr = N("ShaderNodeBsdfTransparent")
    m3 = N("ShaderNodeMixShader")
    L(cut_mask, m3.inputs[0])
    L(m2.outputs[0], m3.inputs[1])
    L(tr.outputs[0], m3.inputs[2])
    out = N("ShaderNodeOutputMaterial")
    L(m3.outputs[0], out.inputs["Surface"])
    E.erase_mat = m


# ------------------------------------------------------------------ the things he builds
def _plastic(E, name, c, size, colour, parent, shape="box", neon=False):
    ob = E3.part(E, name, c, size, colour, neon=neon, shape=shape, top=False)
    ob.parent = parent
    ob.location = c
    return ob


def _root(E, name, loc):
    r = bpy.data.objects.new(name, None)
    E.sc.collection.objects.link(r)
    r.location = loc
    return r


def _thing(E, name, root, meshes, top_z=None):
    """An object that is built and can be erased: its root, its meshes, and their own materials (kept)."""
    th = type("Thing", (), {})()
    th.name, th.root, th.meshes = name, root, list(meshes)
    th.mats = [[s.material for s in ob.material_slots] for ob in th.meshes]
    th.home = Matrix(root.matrix_world)
    for ob in th.meshes:
        ob["e_hi"], ob["e_cut"], ob["e_line"] = 999.0, 999.0, -999.0
    E.things[name] = th
    return th


def _hammer(E):
    """The BTools hammer, formed from the glitch cube: a dark handle gripped in the right fist (through it, the
    pommel just showing behind), a white head across the end with a cyan glowing rim (it is a glitch tool).
    Built in the arm's own space: the fist is at (0, -0.1, -1.38); the handle runs forward (-y) from it."""
    piv = E.N.arms["sr"]
    root = bpy.data.objects.new("hammer", None)
    E.sc.collection.objects.link(root)
    root.parent = piv
    root.location = (0, -0.05, -1.38)
    E.ham = root
    hm = bpy.data.materials.new("hammer_handle")
    hm.use_nodes = True
    hb = hm.node_tree.nodes["Principled BSDF"]
    hb.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
    hb.inputs["Roughness"].default_value = 0.5
    head = bpy.data.materials.new("hammer_head")
    head.use_nodes = True
    nt = head.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.92, 0.94, 0.96, 1)
    bs.inputs["Roughness"].default_value = 0.35
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.25
    ramp = nt.nodes.new("ShaderNodeMix")
    ramp.data_type = "RGBA"
    nt.links.new(lw.outputs["Fresnel"], ramp.inputs[0])
    ramp.inputs[6].default_value = (0.0, 0.0, 0.0, 1)
    ramp.inputs[7].default_value = (0.2, 0.95, 1.0, 1)
    nt.links.new(ramp.outputs[2], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 1.8
    E.ham_glow = bs.inputs["Emission Strength"]
    parts = []
    for nm, size, loc, mat in (("hammer_grip", (0.32, 2.3, 0.32), (0, -0.85, 0), hm),
                               ("hammer_head", (0.62, 0.72, 1.35), (0, -2.15, 0), head),
                               ("hammer_band", (0.36, 0.2, 0.36), (0, -1.72, 0), head)):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = nm
        ob.scale = size
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = 0.05
        bv.segments = 2
        ob.data.materials.append(mat)
        ob.parent = root
        ob.location = loc
        parts.append(ob)
    E.ham_parts = parts
    L = bpy.data.lights.new("hammer_light", "POINT")
    L.color = (0.3, 0.9, 1.0)
    L.shadow_soft_size = 0.2
    lo = bpy.data.objects.new("hammer_light", L)
    E.sc.collection.objects.link(lo)
    lo.parent = root
    lo.location = (0, -2.15, 0)
    E.ham_light = lo
    root.scale = (0, 0, 0)


def _duck(E):
    """A giant rubber duck, built from Roblox parts (yellow, an orange beak, black eyes), on the white plate."""
    E.things = {}
    r = _root(E, "duck", (0, 0, -300))
    Y, O, K = (255, 214, 40), (255, 140, 20), (20, 20, 24)
    ms = [
        _plastic(E, "duck_body", Vector((0, 0.1, 0.5)), (1.25, 1.7, 0.9), Y, r),
        _plastic(E, "duck_chest", Vector((0, -0.55, 0.62)), (1.05, 0.5, 0.75), Y, r),
        _plastic(E, "duck_tail", Vector((0, 0.95, 0.95)), (0.7, 0.45, 0.5), Y, r),
        _plastic(E, "duck_neck", Vector((0, -0.45, 1.12)), (0.7, 0.6, 0.35), Y, r),
        _plastic(E, "duck_head", Vector((0, -0.5, 1.55)), (0.9, 0.85, 0.8), Y, r),
        _plastic(E, "duck_beak", Vector((0, -1.05, 1.45)), (0.55, 0.45, 0.2), O, r),
        _plastic(E, "duck_beak2", Vector((0, -1.0, 1.32)), (0.45, 0.35, 0.1), O, r),
        _plastic(E, "duck_eye_l", Vector((-0.46, -0.65, 1.68)), (0.04, 0.18, 0.2), K, r),
        _plastic(E, "duck_eye_r", Vector((0.46, -0.65, 1.68)), (0.04, 0.18, 0.2), K, r),
        _plastic(E, "duck_wing_l", Vector((-0.66, 0.15, 0.62)), (0.12, 0.9, 0.5), (240, 190, 30), r),
        _plastic(E, "duck_wing_r", Vector((0.66, 0.15, 0.62)), (0.12, 0.9, 0.5), (240, 190, 30), r),
    ]
    th = _thing(E, "duck", r, ms)
    th.size = (1.45, 2.5, 2.0)
    th.lo = Vector((-0.72, -1.3, 0.0))


def _statue(E):
    """A giant statue of the Noob, in grey studded plastic (a Roblox build), arms up, on the checkpoint."""
    import noob as NB
    from stage import build_noob_char
    from noob import pose_noob
    keep = (NB.BLUE, NB.GREEN)
    NB.BLUE, NB.GREEN = (150, 152, 160), (128, 130, 138)
    SN = build_noob_char(E.sc, name="statue")
    NB.BLUE, NB.GREEN = keep
    pose_noob(SN, {"root_yaw": -62, "arm_sl": {"out": 150, "fwd": 18}, "arm_sr": {"out": 150, "fwd": 18},
                   "head_nod": -6, "chest_lean": -4, "leg_sl": {"out": 6}, "leg_sr": {"out": 6}})
    k = E.N.root.scale[0] * STATUE_K
    SN.root.scale = (k, k, k)
    SN.root.location = (0, 0, -300)
    meshes = [o for o in SN.root.children_recursive if o.type == "MESH"]
    grey = (0.46, 0.47, 0.5, 1)
    for ob in meshes:
        nm = " ".join(s.material.name.lower() for s in ob.material_slots if s.material)
        if "face" in nm:
            continue                                              # his face stays (a statue of HIM)
        ob.color = grey
        for s in ob.material_slots:
            s.link = "OBJECT"
            s.material = E.plastic
    E.SN = SN
    th = _thing(E, "statue", SN.root, meshes)
    th.lo = None                                                  # measured in prepare


def _castle(E):
    """A pastel toy castle (walls, four round towers, a gate, little flags) on the violet ledge."""
    r = _root(E, "castle", (0, 0, -300))
    PK, BL, CR, YL = (255, 170, 200), (150, 200, 255), (250, 240, 215), (255, 225, 110)
    ms = [_plastic(E, "castle_wall", Vector((0, 0, 0.35)), (1.9, 0.75, 0.7), CR, r),
          _plastic(E, "castle_gate", Vector((0, -0.38, 0.25)), (0.42, 0.04, 0.5), (110, 80, 60), r),
          _plastic(E, "castle_keep", Vector((0, 0.05, 0.95)), (0.8, 0.55, 0.55), PK, r)]
    for k, (x, y) in enumerate(((-0.95, -0.35), (0.95, -0.35), (-0.95, 0.35), (0.95, 0.35))):
        ms.append(_plastic(E, f"castle_tower_{k}", Vector((x, y, 0.55)), (0.44, 0.44, 1.1), BL if k % 2 else PK, r, shape="cyl"))
        ms.append(_plastic(E, f"castle_cap_{k}", Vector((x, y, 1.16)), (0.5, 0.5, 0.12), YL, r))
        ms.append(_plastic(E, f"castle_pole_{k}", Vector((x, y, 1.45)), (0.04, 0.04, 0.5), (240, 240, 240), r))
        ms.append(_plastic(E, f"castle_flag_{k}", Vector((x + 0.14, y, 1.6)), (0.26, 0.02, 0.16), PK if k % 2 else BL, r))
    for k in range(5):
        ms.append(_plastic(E, f"castle_cren_{k}", Vector((-0.6 + 0.3 * k, -0.33, 0.78)), (0.16, 0.12, 0.16), CR, r))
    E.castle_flags = [o for o in ms if "flag" in o.name]
    th = _thing(E, "castle", r, ms)
    th.size = (2.5, 1.3, 1.9)
    th.lo = Vector((-1.25, -0.65, 0.0))


def _door(E):
    """A single freestanding wooden door on a threshold sill, its own frame, facing the open sky (south). The
    leaf hangs from its hinge (origin on the hinge edge) 4 cm above the sill and swings out over the drop."""
    r = _root(E, "door", (0, 0, -300))
    W, H = DOOR_W, DOOR_H
    BR, DK, GD = (120, 72, 40), (90, 52, 30), (230, 190, 70)
    z0 = -DOOR_HINGE.z                                            # the terrace's top, in the door's space
    ms = [_plastic(E, "door_sill", Vector((W / 2, 0, z0 + 0.02)), (W + 0.3, 0.3, 0.04), DK, r),
          _plastic(E, "door_post_l", Vector((-0.06, 0, z0 + (H + 0.14) / 2)), (0.1, 0.16, H + 0.14), DK, r),
          _plastic(E, "door_post_r", Vector((W + 0.06, 0, z0 + (H + 0.14) / 2)), (0.1, 0.16, H + 0.14), DK, r),
          _plastic(E, "door_lintel", Vector((W / 2, 0, H + 0.06)), (W + 0.22, 0.16, 0.12), DK, r)]
    hinge = bpy.data.objects.new("door_hinge", None)
    E.sc.collection.objects.link(hinge)
    hinge.parent = r
    hinge.location = (0, 0, 0)
    leaf = [_plastic(E, "door_leaf", Vector((W / 2, 0, H / 2)), (W - 0.02, 0.07, H - 0.02), BR, hinge),
            _plastic(E, "door_panel_t", Vector((W / 2, -0.04, H * 0.72)), (W - 0.3, 0.02, H * 0.3), DK, hinge),
            _plastic(E, "door_panel_b", Vector((W / 2, -0.04, H * 0.27)), (W - 0.3, 0.02, H * 0.34), DK, hinge),
            _plastic(E, "door_knob", Vector((W - 0.12, -0.07, 1.0)), (0.07, 0.07, 0.07), GD, hinge),
            _plastic(E, "door_knob2", Vector((W - 0.12, 0.07, 1.0)), (0.07, 0.07, 0.07), GD, hinge)]
    E.door_hinge = hinge
    th = _thing(E, "door", r, ms + leaf)
    th.size = (W + 0.5, 0.5, H + 0.3)
    th.lo = Vector((-0.2, -0.25, -0.08))


def _scan_plane(E):
    """The BTools scan: a thin plane of cyan light rising through the selection box."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = "scan_plane"
    m, mx, em = E3._emit_mat("scan_plane", (0.3, 0.9, 1.0), 3.0)
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ob.location = (0, 0, -300)
    E.scanp, E.scanp_mix = ob, mx


def _pixels(E):
    """Small squares: magenta code (the cube pouring into his hand, erased things rising away as dead pixels) and
    grey-white dust puffs where a build lands."""
    m, mx, em = E3._emit_mat("pix_mag", (1.0, 0.12, 0.85), 9.0)
    m2, mx2, em2 = E3._emit_mat("pix_cyan", (0.2, 0.9, 1.0), 9.0)
    dm = bpy.data.materials.new("dust")
    dm.use_nodes = True
    db = dm.node_tree.nodes["Principled BSDF"]
    db.inputs["Base Color"].default_value = (0.85, 0.85, 0.82, 1)
    db.inputs["Roughness"].default_value = 1.0
    E.pix5, E.dust = [], []
    for k in range(64):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"code_pix_{k}"
        ob.data.materials.append(m if k % 3 else m2)
        ob.visible_shadow = False
        ob.location = (0, 0, -300)
        E.pix5.append(ob)
    for k in range(28):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"dust_{k}"
        ob.data.materials.append(dm)
        ob.visible_shadow = False
        ob.location = (0, 0, -300)
        E.dust.append(ob)


# ------------------------------------------------------------------ Episode 4's last instant
def ep4_world(E, t):
    """Everything as Episode 4 left it: Ep3's obby (the portal and spinners alive), the dragon sealed in crystal,
    the spawn ring lit; no tether, sparks, warp or read-out."""
    _use(E, 4)
    T4 = E.T4
    E4.ep3_world(E, T4 + t)            # (it swaps Ep3's beats in and Ep4's back)
    E4.dragon(E, T4)
    E4.ring(E, T4)
    E4.tether(E, T4)
    E4.shockwave(E, T4)
    E4.sparks(E, T4)
    E4.warp(E, T4)
    for ob in E.bars:
        ob.location = (0, 0, -300)
    _use(E, 5)


def prepare(E):
    """Measured once: Ep4's end (the poses, the camera), the sizes of the builds, the sun."""
    if E.prepped5:
        return
    E.prepped5 = True
    _use(E, 4)
    E4.prepare(E)
    _use(E, 5)
    ep4_world(E, 0.0)
    # the statue's box, posed, on the checkpoint
    SN = E.SN
    SN.root.location = CP_TOP
    bpy.context.view_layer.update()
    th = E.things["statue"]
    pts = [ob.matrix_world @ Vector(c) for ob in th.meshes for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    SN.root.location = CP_TOP + Vector((0, 0, CP_TOP.z - lo.z))   # feet on the checkpoint
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for ob in th.meshes for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    th.box = (lo, hi)
    th.home_loc = Vector(SN.root.location)
    SN.root.location = (0, 0, -300)
    for nm, at, yaw in (("duck", DUCK_AT, -35.0), ("castle", LEDGE_TOP, 0.0), ("door", DOOR_HINGE, 0.0)):
        th = E.things[nm]
        th.home_loc = Vector(at)
        th.yaw = yaw
        rot = Matrix.Rotation(math.radians(yaw), 3, "Z")
        cs = [rot @ Vector((th.lo.x + dx * th.size[0], th.lo.y + dy * th.size[1], th.lo.z + dz * th.size[2]))
              for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
        if nm == "door":
            cs = [Vector((th.lo.x + dx * th.size[0], th.lo.y + dy * th.size[1], th.lo.z + dz * th.size[2]))
                  for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
        lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))) + Vector(at)
        hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))) + Vector(at)
        th.box = (lo, hi)
    # the original course that goes at the end: the stones west, the stepping stone and checkpoint east, the truss tower
    by = {ob.name: ob for ob in bpy.data.objects}
    E.course = {
        "west": [by[f"west_{k}"] for k in range(5)],
        "east": [by[n] for n in ("stone", "cp", "cp_pad", "flag_pole", "flag")],
        "tower": [ob for ob in bpy.data.objects if ob.name.startswith(("truss_r_", "truss_s_", "high_stage"))],
    }
    for grp in E.course.values():
        for ob in grp:
            ob["e_hi"], ob["e_cut"], ob["e_line"] = 999.0, 999.0, -999.0
            ob["mat0"] = ob.material_slots[0].material.name if ob.material_slots else ""
    E.sun_energy0 = E.sun.data.energy
    E.sun_col0 = tuple(E.sun.data.color)
    E.bg0 = None
    w = bpy.context.scene.world
    if w and w.use_nodes:
        for n_ in w.node_tree.nodes:
            if n_.type == "BACKGROUND":
                E.bg0 = (n_, n_.inputs["Strength"].default_value)
                break


# ------------------------------------------------------------------ the shots
SHOTS = [("open", "still", 0), ("stunned", "still", 0.55), ("master", "reach", 0), ("hand", "implode", 0.55),
         ("hammer", "hammer", 0), ("duck", "hammer", 0.45), ("build", "noob_build", 0), ("since", "lower", 0),
         ("block", "noob_block", 0), ("statue", "statue", 0), ("me", "noob_statue", 0), ("crane", "crane", 0),
         ("see", "noob_see", 0), ("castle", "castle", 0), ("pinch", "pinch", 0), ("door", "salute", 0),
         ("open_door", "open", 0), ("stare", "stare", 0), ("chime", "chime", 0), ("where", "noob_duck", 0),
         ("scan", "scan", 0), ("patch", "patch_delete", 2.2), ("castle_gone", "castle_gone", 0),
         ("statue_gone", "statue_gone", 0), ("no", "noob_no", 0), ("dragon", "dragon", 0), ("west", "hush", 0),
         ("east", "stairs_gone", 2.3), ("void", "stairs_gone", 2.9), ("us", "steve_us", -0.15), ("hold", "hold", 0)]


def shot_bounds():
    return [(name, b(beat) + off) for name, beat, off in SHOTS]


def which(t):
    bs = shot_bounds()
    for i, (name, t0) in enumerate(bs):
        t1 = bs[i + 1][1] if i + 1 < len(bs) else 1e9
        if t < t1:
            return name, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


# ------------------------------------------------------------------ building and erasing
BUILDS = (("duck", "duck", 0.0), ("statue", "statue", 0.35), ("castle", "castle", 0.3), ("door", "door", 0.3))
ERASES = (("duck", "duck_gone", 0.05, 0.55), ("castle", "castle_gone", 0.25, 0.55), ("statue", "statue_gone", 0.2, 0.9))
COURSE = (("west0", "stairs_gone", 0.1), ("west1", "stairs_gone", 0.6), ("west2", "stairs_gone", 1.1),
          ("west3", "stairs_gone", 1.6), ("west4", "stairs_gone", 2.05), ("east", "stairs_gone", 2.5),
          ("tower", "stairs_gone", 2.95))
SNAP, SCAN, POP = 0.04, 0.22, 0.12        # the materialize: the box snaps, the scan rises, the pop settles


def build_time(name):
    for nm, beat, off in BUILDS:
        if nm == name:
            return b(beat) + off
    return None


def erase_window(name):
    for nm, beat, off, dur in ERASES:
        if nm == name:
            return b(beat) + off, dur
    return None


def _set_mats(obs, mats=None, erase=None):
    for k, ob in enumerate(obs):
        for i, s in enumerate(ob.material_slots):
            if erase is not None:
                s.link = "OBJECT"
                s.material = erase
            else:
                s.material = mats[k][i] if mats else s.material


def _restore(th):
    for ob, ms in zip(th.meshes, th.mats):
        for s, m0 in zip(ob.material_slots, ms):
            s.material = m0


def thing(E, name, t):
    """A build: hidden before it is made; the selection box snaps round where it goes, the scan rises through it
    (solid below the scan, nothing above), it pops in with a small overshoot; then, when its time comes, erased."""
    th = E.things[name]
    t0 = build_time(name)
    ew = erase_window(name)
    lo, hi = th.box
    h = hi.z - lo.z
    if t < t0 + SNAP or (ew and t >= ew[0] + ew[1]):
        th.root.location = (0, 0, -300)
        return None
    th.root.location = th.home_loc
    if name != "statue":
        th.root.rotation_euler = (0, 0, math.radians(getattr(th, "yaw", 0.0)))
    s_ = 1.0
    ts = t0 + SNAP
    if t < ts + SCAN:                                             # rising scan
        u = (t - ts) / SCAN
        line = lo.z + h * u
        _set_erase(th.meshes, 999.0, line, line)
    else:
        _restore(th)
        _set_props(th.meshes, 999.0, 999.0, -999.0)
        dt = t - ts - SCAN
        if dt < POP:
            s_ = 1.0 + 0.04 * math.sin(math.pi * dt / POP)
    if ew and t >= ew[0]:                                         # the erase rule
        u = (t - ew[0]) / ew[1]
        _set_erase(th.meshes, hi.z - (h + 0.3) * ss(0.0, 0.6, u), hi.z + 0.2 - (h + 0.5) * ss(0.25, 1.0, u), -999.0)
    base = Matrix.Translation(th.home_loc)
    sc = Vector((s_, s_, s_))
    k0 = E.N.root.scale[0] * STATUE_K if name == "statue" else 1.0
    th.root.scale = sc * k0
    return th


def _set_props(obs, hi, cut, line):
    for ob in obs:
        ob["e_hi"], ob["e_cut"], ob["e_line"] = hi, cut, line


def _set_erase(obs, hi, cut, line):
    for ob in obs:
        for s in ob.material_slots:
            s.link = "OBJECT"
            s.material = bpy.data.materials["erase"]
        ob["e_hi"], ob["e_cut"], ob["e_line"] = hi, cut, line


def course(E, t):
    """The original course: the stones west (nearest first), then the stepping stone and checkpoint east, then the
    truss tower: each by the same rule, then gone."""
    for key, beat, off in COURSE:
        t0 = b(beat) + off
        obs = E.course["west"][int(key[-1]):int(key[-1]) + 1] if key.startswith("west") else E.course[key]
        dur = 0.45 if key.startswith("west") else (0.55 if key == "east" else 0.6)
        for ob in obs:
            if not hasattr(ob, "_home5"):
                pass
            if t < t0:
                ob.hide_render = False
                if ob.material_slots and ob.material_slots[0].link == "OBJECT":
                    ob.material_slots[0].link = "DATA"
                ob["e_hi"], ob["e_cut"], ob["e_line"] = 999.0, 999.0, -999.0
                continue
            if t >= t0 + dur:
                ob.hide_render = True
                continue
            ob.hide_render = False
            pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            zl, zh = min(p.z for p in pts), max(p.z for p in pts)
            if key == "tower":
                zl, zh = -1.0, 14.0
            u = (t - t0) / dur
            hh = zh - zl
            for s in ob.material_slots:
                s.link = "OBJECT"
                s.material = E.erase_mat
            ob["e_hi"] = zh - (hh + 0.3) * ss(0.0, 0.6, u)
            ob["e_cut"] = zh + 0.2 - (hh + 0.5) * ss(0.25, 1.0, u)
            ob["e_line"] = -999.0


def gizmo(E, t):
    """The selection box: snaps round where a build goes (first frame white, then Studio blue); a pink flickering
    residue box over the empty plate after the duck is erased (while Patch scans it)."""
    specs = []
    for nm, _, _ in BUILDS:
        t0 = build_time(nm)
        if t0 <= t < t0 + SNAP + SCAN + POP + 0.25:
            lo, hi = E.things[nm].box
            c = (lo + hi) / 2
            pad = (hi - lo) * 0.04
            size = tuple((hi - lo) + 2 * pad)
            k = 1.0 if t < t0 + SNAP + 1.0 / FPS else 0.0
            specs.append({"m": Matrix.Translation(c), "size": size, "mode": "snap", "k": k, "w": 0.03 + 0.01 * (nm == "statue")})
    E.giz.draw(specs)


def scanplane(E, t):
    for nm, _, _ in BUILDS:
        t0 = build_time(nm) + SNAP
        if t0 <= t < t0 + SCAN:
            lo, hi = E.things[nm].box
            u = (t - t0) / SCAN
            c = (lo + hi) / 2
            E.scanp.location = (c.x, c.y, lo.z + (hi.z - lo.z) * u)
            E.scanp.scale = ((hi.x - lo.x) * 1.08, (hi.y - lo.y) * 1.08, 1)
            E.scanp.rotation_euler = (0, 0, 0)
            E.scanp_mix.inputs[0].default_value = 0.85
            return
    E.scanp.location = (0, 0, -300)


def _pix(ob, p, s, rot=0.0):
    ob.location = p
    ob.scale = (s, s, s)
    ob.rotation_euler = (rot, rot * 1.3, rot * 0.7)


def pixels(E, t):
    """The code pouring from the cube into his fist; dead pixels rising off erased things; dust where builds land;
    pink static hanging over the empty plate."""
    used = 0
    pool = E.pix5
    rnd = random.Random(7)
    # the implode: squares stream from the cube's surface to the fist
    t0 = b("implode")
    if t0 <= t < t0 + 1.35:
        fist = E.fist_now
        for k in range(36):
            st = t0 + 0.05 + 0.9 * k / 36 + rnd.uniform(0, 0.08)
            u = (t - st) / 0.42
            ob = pool[used]
            used += 1
            if not 0 <= u < 1:
                ob.location = (0, 0, -300)
                continue
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
            a = CUBE_C + d * 0.72 * E.cube_s_now
            mid = a.lerp(fist, 0.5) + Vector((0, 0, 0.35))
            p = (a.lerp(mid, u)).lerp(mid.lerp(fist, u), u)
            _pix(ob, p, 0.05 * (1 - 0.6 * u), t * 7 + k)
    # erased things: 12 squares rising from where it went
    for nm, beat, off, dur in ERASES:
        t1 = b(beat) + off
        if t1 <= t < t1 + dur + 0.9:
            lo, hi = E.things[nm].box
            for k in range(12):
                ob = pool[used]
                used += 1
                st = t1 + dur * rnd.uniform(0.0, 0.8)
                u = (t - st) / 0.9
                if not 0 <= u < 1:
                    ob.location = (0, 0, -300)
                    continue
                base = Vector((rnd.uniform(lo.x, hi.x), rnd.uniform(lo.y, hi.y), lerp(hi.z, lo.z, (st - t1) / dur)))
                _pix(ob, base + Vector((0, 0, 1.6 * u)), 0.07 * (1 - u) * (1.6 if nm == "statue" else 1.0), k + t)
    # static over the empty plate (while Patch scans it)
    s0, s1 = b("duck_gone", 1), b("castle_gone")
    if s0 <= t < s1:
        f = int(round(t * FPS))
        for k in range(8):
            ob = pool[used]
            used += 1
            if (f + k * 3) % 5 < 2:
                ob.location = (0, 0, -300)
                continue
            r2 = random.Random(f * 13 + k)
            _pix(ob, DUCK_AT + Vector((r2.uniform(-0.8, 0.8), r2.uniform(-0.8, 0.8), r2.uniform(0.1, 1.6))), 0.05, 0)
    for ob in pool[used:]:
        ob.location = (0, 0, -300)
    # dust puffs at the base of each build as it lands
    used = 0
    for nm, _, _ in BUILDS:
        t2 = build_time(nm) + SNAP + SCAN
        if t2 <= t < t2 + 0.7:
            lo, hi = E.things[nm].box
            n = 10 if nm == "statue" else 6
            for k in range(n):
                if used >= len(E.dust):
                    break
                ob = E.dust[used]
                used += 1
                a = 2 * math.pi * k / n + 0.3
                u = (t - t2) / 0.7
                c = (lo + hi) / 2
                r0 = max(hi.x - lo.x, hi.y - lo.y) / 2
                p = Vector((c.x + math.cos(a) * r0 * (1 + 0.6 * u), c.y + math.sin(a) * r0 * (1 + 0.6 * u), lo.z + 0.1 + 0.3 * u))
                _pix(ob, p, (0.18 if nm == "statue" else 0.1) * (1 - u) ** 0.7, a)
    for ob in E.dust[used:]:
        ob.location = (0, 0, -300)


# ------------------------------------------------------------------ the cube and the hammer
def cube(E, t):
    """Ep4's cube, humming; at the third poke a pink flash, then it implodes into his fist."""
    k = int(round(t * FPS))
    t0 = b("implode")
    s = E4.SIZES[2]
    c = Vector(CUBE_C) + Vector((0, 0, 0.03 * math.sin((E.T4 + t) * 2.1)))
    if t >= t0:
        u = (t - t0) / 1.25
        if u >= 1:
            E.blk.location = (0, 0, -300)
            E.blk_light.location = (0, 0, -300)
            E.cube_s_now = 0.0
            return
        s = s * (1 - ss(0.0, 1.0, u) ** 1.4)
        c = c.lerp(E.fist_now, ss(0.55, 1.0, u) * 0.6)
    glitchy = (k * 7919 % 29) < 3 or (t >= t0 and k % 2 == 0)
    jit = Vector((((k * 31) % 7 - 3) * 0.012, ((k * 17) % 5 - 2) * 0.012, 0)) if glitchy else Vector()
    E.blk.location = c + jit
    E.blk.scale = (s, s, s)
    E.blk.rotation_euler = (0, 0, math.radians(18) + 0.15 * math.sin((E.T4 + t) * 0.6) + (t - t0) * 6 * (t >= t0))
    E.blk_map.inputs["Location"].default_value = (0.25 * (k // 6 % 2) if glitchy else 0.0, 0, 0)
    flash = math.exp(-((t - b("poke3") - 0.08) / 0.08) ** 2)
    E.blk_emit.default_value = 2.5 * (1.6 if glitchy else 1.0) + 8.0 * flash
    E.blk_light.location = c
    E.blk_light.data.energy = 60.0 * s ** 2 * 2.2 + 400 * flash
    E.cube_s_now = s


def hammer(E, t):
    """Formed in the fist as the cube pours in (a pop, a flare), glowing; it dips when he throws his hands out."""
    t0 = b("implode") + 0.95
    if t < t0:
        E.ham.scale = (0, 0, 0)
        E.ham_light.data.energy = 0.0
        return
    u = (t - t0) / 0.3
    s = E4._back(u) if u < 1 else 1.0
    E.ham.scale = (s, s, s)
    flare = math.exp(-((t - t0 - 0.25) / 0.2) ** 2)
    E.ham_glow.default_value = 1.8 + 6.0 * flare
    E.ham_light.data.energy = 25.0 + 120.0 * flare


# ------------------------------------------------------------------ the dragon
def dragon(E, t):
    """Sealed in crystal as Ep4 left it; in the cascade it flickers violently into the missing texture and a
    scanline tears across it, then it snaps back (still there: the next chapter erases it)."""
    D = E.D
    t0, t1 = b("dragon") + 0.05, b("dragon") + 0.75
    k = int(round(t * FPS))
    on = t0 <= t < t1 and (k * 7919 % 7) < 4
    D.root.location = E.d_root
    D.root.rotation_euler = E.d_rot
    if t0 <= t < t1:
        r = random.Random(k)
        D.root.location = E.d_root + Vector((r.uniform(-1, 1), 0, r.uniform(-1, 1))) * 0.08
    for ob in D.meshes:
        ob.material_slots[0].material = E.checker if on else D.mat
    for sh, c, d, jit, mw in E.shell:
        sh.hide_render = on


# ------------------------------------------------------------------ the sky pales
def sun(E, t):
    u = ss(b("stairs_gone"), b("stairs_gone", 1) + 0.6, t)
    E.sun.data.energy = E.sun_energy0 * (1 - 0.25 * u)
    c0 = Vector(E.sun_col0)
    E.sun.data.color = tuple(c0.lerp(Vector((0.86, 0.9, 1.0)), 0.6 * u))
    if E.bg0:
        E.bg0[0].inputs["Strength"].default_value = E.bg0[1] * (1 - 0.15 * u)


# ------------------------------------------------------------------ Patch
def _patch_keys():
    T = b
    return [
        (0.0, P_TWIST),
        (T("reach") + 0.2, P_TWIST),
        (T("reach") + 0.6, P_TWIST + Vector((-0.25, 0.35, -0.1))),       # darting toward the Noob: "Wait-"
        (T("implode") + 0.1, P_TWIST + Vector((-0.25, 0.35, -0.1))),
        (T("implode") + 0.6, P_TWIST + Vector((0.4, -0.3, 0.2))),         # recoiling from the burst of code
        (T("duck") + 0.3, P_WATCH),
        (T("scan"), P_WATCH),
        (T("scan") + 0.65, P_PLATE),                                      # darts over the empty plate
        (T("castle_gone") + 0.3, P_PLATE),
        (T("castle_gone") + 1.2, P_PLATE + Vector((-0.9, -0.4, 0.2))),
    ]


def patch_pos(t):
    K = _patch_keys()
    if t <= K[0][0]:
        return K[0][1].copy()
    for i in range(len(K) - 1):
        if K[i][0] <= t < K[i + 1][0]:
            if (K[i + 1][1] - K[i][1]).length < 1e-3:
                return K[i][1].copy()
            u = ss(0, 1, (t - K[i][0]) / (K[i + 1][0] - K[i][0]))
            p0 = K[max(0, i - 1)][1]
            p3 = K[min(len(K) - 1, i + 2)][1]
            return _cr(p0, K[i][1], K[i + 1][1], p3, u)
    return K[-1][1].copy()


def scan_target(E, t):
    """Where the beam points: down onto the empty plate (sweeping slowly), whipping over to the castle just
    before it goes."""
    s0 = b("scan") + 0.55
    w = b("patch_delete", 1) - 0.1
    sweep = Vector((0.6 * math.sin((t - s0) * 1.6), 0.35 * math.sin((t - s0) * 1.1), 0))
    p = DUCK_AT + Vector((0, 0, 0.1)) + sweep
    if t >= w:
        p = p.lerp(LEDGE_TOP + Vector((0, 0, 0.8)), ss(w, w + 0.25, t))
    return p


def patch(E, t):
    from patch import set_patch
    P = E.PA
    p = patch_pos(t)
    dt = 0.04
    v = (patch_pos(t + dt) - patch_pos(t - dt)) / (2 * dt)
    a = (patch_pos(t + dt) - 2 * p + patch_pos(t - dt)) / (dt * dt)
    bob = 0.05 * math.sin((E.T4 + t) * 2.4) + 0.02 * math.sin((E.T4 + t) * 5.3 + 1)
    cam = Vector(E.cam_loc_now)
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.3))
    scanning = b("scan") + 0.55 <= t < b("castle_gone") + 0.3
    tgt = N_
    if b("hammer") <= t < b("scan"):                               # watching what he builds
        for nm, beat, off in BUILDS:
            if t >= b(beat) + off - 0.2:
                lo, hi = E.things[nm].box
                tgt = (lo + hi) / 2
    if scanning:
        tgt = scan_target(E, t)
    if b("castle_gone") <= t:
        tgt = LEDGE_TOP + Vector((0, 0, 0.6))
    if b("statue_gone") <= t:
        tgt = E.things["statue"].box[1] * 0.5 + E.things["statue"].box[0] * 0.5
    if b("dragon") <= t:
        tgt = Vector(E.D.root.location)
    if b("hush") <= t:
        tgt = Vector((-15.0, 0.5, 0.5))
    if b("stairs_gone") + 2.4 <= t < b("void"):
        tgt = Vector((6.0, -1.0, 0.6))
    if b("void") <= t:
        tgt = N_
    if v.length > 0.8:
        tgt = p + v * 2
    to = tgt - p
    yaw = _yaw(Vector((to.x, to.y, 0)))
    if not scanning and v.length <= 0.8:                         # cheated a little toward the camera so the eye reads
        tc = cam - p
        yaw = yaw + _wrap(_yaw(Vector((tc.x, tc.y, 0))) - yaw) * 0.3
    fw = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0))
    side = Vector((-fw.y, fw.x, 0))
    pitch = _clamp(-a.dot(fw) * 0.9 - v.dot(fw) * 4.0, -16, 16)
    roll = _clamp(a.dot(side) * 0.9, -16, 16)
    if scanning:                                                  # tipped down toward the plate
        pitch += 22.0
    P.root.location = p + Vector((0, 0, bob))
    P.root.rotation_euler = (math.radians(pitch), math.radians(roll), math.radians(yaw))
    P.root.scale = (1, 1, 1)
    for side_, sx in (("l", -1), ("r", 1)):
        P.fins[side_].rotation_euler = (math.radians(8 * math.sin(t * 9 + sx) + pitch * 0.6), 0, 0)
    talk = 0.0
    f = int(round(t * FPS))
    mo = E.mouth.get("patch", {})
    if mo.get(f):
        talk = mo[f].get("m_o", 0.0)
    per = 2.8
    ph = (E.T4 + t + 0.9) % per
    blink = math.exp(-((ph - 0.06) / 0.04) ** 2)
    vals = {"open": max(0.05, 1 - blink), "look_x": 0.0, "look_y": 0.0, "squint": 0.0, "wide": 0.6, "glitch": 0.0,
            "scan": 0.0, "smile": 0.0, "sad": 0.3}
    if t >= b("reach") + 0.15:                                    # alarmed: the eye snaps wide
        vals.update({"wide": 1.0, "sad": 0.0, "open": 1.0})
    if b("implode") <= t < b("implode") + 1.2:
        g = int(t * FPS) % 3 == 0
        vals["glitch"] = 0.7 if g else 0.0
    if b("hammer") <= t < b("duck_gone"):                         # curious, wary
        vals.update({"wide": 0.4, "squint": 0.25, "open": max(0.05, 1 - blink)})
    if b("duck_gone") <= t:
        vals.update({"wide": 0.9, "squint": 0.0, "open": max(0.05, 1 - blink) * (1 + 0.12 * talk)})
    if scanning:
        vals["scan"] = 1.0
    if b("dragon") <= t < b("dragon") + 0.8:
        vals["glitch"] = 0.8 if f % 2 else 0.3
    set_patch(P, vals)
    P.glow.data.energy = 12.0
    if scanning:                                                  # the beam aimed at what it scans
        bpy.context.view_layer.update()
        o = P.root.matrix_world @ Vector((0, -0.55 * 0.42, 0.02 * 0.42))
        d = scan_target(E, t) - o
        q = d.to_track_quat("-Y", "Z")
        L_ = 3.0 * 0.42 * 3
        k = d.length / L_
        P.beam.matrix_world = Matrix.Translation(o) @ q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(8), 4, "X") \
            @ Matrix.Diagonal((1.0, k, k, 1.0))


# ------------------------------------------------------------------ the Noob
def _hand(E, side="sr"):
    return E.N.arms[side].matrix_world @ Vector((0, -0.1, -1.38))


def _swing(pz, t, t0, toward_up=True):
    """A BTools swing: the hammer up and back, then down at the target (contact at t0 + 0.3), a follow-through."""
    up_ = ss(t0 - 0.05, t0 + 0.2, t)
    dn = ss(t0 + 0.2, t0 + 0.32, t)
    back = 1 - ss(t0 + 0.5, t0 + 0.9, t)
    pz["arm_sr"] = {"fwd": (40 + 130 * up_ - 85 * dn) * back + 25 * (1 - back), "out": 15, "elbow": 40 * up_ * (1 - dn)}
    pz["chest_lean"] = pz.get("chest_lean", 0) - 8 * up_ * (1 - dn) + 10 * dn * back
    pz["chest_twist"] = -10 * up_ * (1 - dn)


def noob(E, t):
    from ep09_new import NF
    N = E.N
    HYPE = E3.HYPE
    face = dict(NF["happy"])
    pz = {"arm_sl": {"out": 8, "fwd": 4}, "arm_sr": {"out": 8, "fwd": 4}}
    stunned = {"both_h": 1.9, "both_w": 1.05, "m_arch": 0.15, "both_ps": 0.8}
    g0 = b("still") + 1.2
    if t < g0:                                                    # Ep4's last instant goes on: stunned, facing Patch
        _use(E, 4)
        keep, E.mouth = E.mouth, {}
        E4.noob(E, E.T4 + t)
        E.mouth = keep
        _use(E, 5)
        return
    P_ = Vector(E.PA.root.location)
    p, yaw = REACT_N.copy(), _face_to(REACT_N, P_)
    if t < b("reach"):                                            # a blink; his eyes slide to the cube
        face = dict(stunned)
        k = ss(g0, b("reach"), t)
        tl, nd = _look(yaw, p, CUBE_C, h=1.4)
        pz["head_turn"], pz["head_nod"] = tl * k, nd * k
    elif t < b("poke3") + 0.1:                                    # zero impulse control: to the cube, a finger out
        u = ss(b("reach"), b("poke3") - 0.05, t)
        p = REACT_N.lerp(N_POKE, u)
        yaw = lerp(_face_to(REACT_N, P_), _face_to(N_POKE, CUBE_C), ss(b("reach"), b("reach") + 0.35, t))
        if 0.05 < u < 0.95:
            _run(pz, t, b("reach"), 1.8, k=0.4, steve=False)
        r = ss(b("reach") + 0.3, b("poke3"), t)
        pz["arm_sr"] = {"fwd": 20 + 65 * r, "out": 8, "elbow": 10 * (1 - r)}
        pz["chest_lean"] = 8 * r
        face = dict(HYPE) if t < b("patch_wait") + 0.3 else dict(NF["happy"])
    elif t < b("hammer"):                                         # the poke lands: no zap; it pours into his fist
        p = N_POKE.copy()
        yaw = _face_to(N_POKE, CUBE_C)
        ti = b("implode")
        pz["arm_sr"] = {"fwd": 85, "out": 8}
        pz["chest_lean"] = 8
        face = dict(NF["shock"])
        if t >= ti:
            rec = ss(ti, ti + 0.3, t)
            pz["chest_lean"] = 8 - 14 * rec
            pz["head_nod"] = -10 * rec
            jit = math.sin(t * 70) * (1 - ss(ti + 0.6, ti + 1.2, t))
            pz["arm_sr"] = {"fwd": 85 + 6 * jit, "out": 8, "elbow": 5}
            face = dict(NF["shock"]) if t < ti + 1.0 else dict(NF["awe"])
            if t >= ti + 1.1:                                     # he draws the new thing up to his face
                k = ss(ti + 1.1, b("hammer"), t)
                pz["arm_sr"] = {"fwd": 85 + 25 * k, "out": 8 + 10 * k, "elbow": 70 * k}
                tl, nd = _look(yaw, p, _hand(E) + Vector((0, 0, 0.2)), h=1.4)
                pz["head_turn"], pz["head_nod"] = tl * k, nd * k
    else:
        p = N_POKE.lerp(N_BUILD, ss(b("hammer"), b("hammer") + 0.5, t))
        S_ = Vector(E.S.holder.location)
        yaw = _face_to(p, PLATE)
        face = dict(HYPE)
        if t < b("duck") + 0.4:                                   # looking at it; then he points it at the plate
            k = ss(b("hammer") + 0.35, b("hammer") + 0.55, t)
            pz["arm_sr"] = {"fwd": 110 - 20 * k, "out": 18 - 10 * k, "elbow": 70 * (1 - k)}
            face = dict(NF["awe"]) if t < b("hammer") + 0.4 else dict(HYPE)
            if t >= b("duck"):
                face = dict(HYPE)
        elif t < b("lower"):                                      # "I can BUILD stuff!": the hammer high, bouncing
            k = ss(b("duck") + 0.4, b("noob_build") + 0.2, t)
            yaw = lerp(_face_to(p, PLATE), _face_to(p, E.cam_loc_now), 0.55 * k)
            pz["arm_sr"] = {"fwd": 90 + 70 * k, "out": 15 + 15 * k, "elbow": 10}
            pz["arm_sl"] = {"fwd": 30 * k, "out": 40 * k}
            p = p + Vector((0, 0, 0.12 * abs(math.sin((t - b("noob_build")) * 7)) * k))
            face = dict(HYPE)
        elif t < b("statue"):                                     # "Since the block!": the hammer lifted, proud
            yaw = _face_to(p, S_)
            pz["arm_sr"] = {"fwd": 40, "out": 15, "elbow": 30}
            face = dict(NF["happy"])
            if t >= b("noob_block") - 0.15:
                k = ss(b("noob_block") - 0.15, b("noob_block") + 0.2, t)
                pz["arm_sr"] = {"fwd": 40 + 110 * k, "out": 15 + 10 * k, "elbow": 30 * (1 - k)}
                pz["chest_lean"] = -6 * k
                face = dict(HYPE)
        elif t < b("crane"):                                      # the statue: a swing east; delighted
            yaw = _face_to(p, CP_TOP)
            _swing(pz, t, b("statue"))
            face = dict(HYPE)
            if t >= b("noob_statue") - 0.2:                       # "A statue of me!": arms wide
                k = ss(b("noob_statue") - 0.2, b("noob_statue") + 0.15, t)
                yaw = lerp(_face_to(p, CP_TOP), _face_to(p, E.cam_loc_now), 0.6 * k)
                pz["arm_sr"] = {"fwd": 25 + 20 * k, "out": 15 + 95 * k, "elbow": 0}
                pz["arm_sl"] = {"fwd": 20 * k, "out": 8 + 102 * k}
                pz["chest_lean"] = -8 * k
            sl = b("statue") + 0.7                                # the slam shakes him
            pz["hips_drop"] = 0.06 * math.exp(-max(0.0, t - sl) * 8) * (t >= sl)
        elif t < b("castle"):                                     # watching Steve; "So everyone can see me!"
            yaw = _face_to(p, S_)
            face = dict(NF["happy"])
            pz["arm_sr"] = {"fwd": 25, "out": 15, "elbow": 20}
            if t >= b("noob_see") - 0.1:
                k = ss(b("noob_see") - 0.1, b("noob_see") + 0.2, t)
                pz["arm_sl"] = {"out": 45 * k + 8, "fwd": -15 * k, "elbow": 100 * k}
                pz["arm_sr"] = {"fwd": 25 + 120 * k, "out": 15, "elbow": 20 * (1 - k)}
                pz["chest_lean"] = -10 * k
                face = dict(HYPE)
        elif t < b("pinch"):                                      # a swing back over his shoulder: the castle
            yaw = lerp(_face_to(p, S_), _face_to(p, LEDGE_TOP), ss(b("castle") - 0.1, b("castle") + 0.25, t))
            _swing(pz, t, b("castle"))
            face = dict(HYPE)
            if t >= b("castle") + 0.9:
                yaw = lerp(_face_to(p, LEDGE_TOP), _face_to(p, S_), ss(b("castle") + 0.9, b("pinch"), t))
        elif t < b("salute") + 0.6:                               # listening to Steve; the salute
            yaw = _face_to(p, S_)
            face = dict(NF["happy"])
            pz["arm_sr"] = {"fwd": 20, "out": 12, "elbow": 15}
            if t >= b("salute"):
                k = ss(b("salute"), b("salute") + 0.15, t) * (1 - ss(b("salute") + 0.45, b("salute") + 0.6, t))
                pz["arm_sl"] = {"fwd": 130 * k, "out": 55 * k, "elbow": 125 * k}
                pz["chest_lean"] = -5 * k
                face = dict(HYPE)
        elif t < b("open"):                                       # the door: a swing at the terrace's edge
            yaw = _face_to(p, DOOR_HINGE + Vector((DOOR_W / 2, 0, 0)))
            _swing(pz, t, b("door"))
            face = dict(HYPE)
        else:                                                     # to the door; the handle; "Close enough!"
            u = ss(b("open"), b("open") + 0.45, t)
            p = N_BUILD.lerp(N_DOOR, u)
            knob = DOOR_HINGE + Vector((DOOR_W - 0.12, 0, 0))
            yaw = _face_to(p, knob)
            if 0.05 < u < 0.95:
                _run(pz, t, b("open"), 2.2, k=0.4, steve=False)
            pz["arm_sr"] = {"fwd": 15, "out": 10, "elbow": 15}
            push = ss(b("open") + 0.4, b("open") + 0.6, t) * (1 - ss(b("open") + 1.0, b("open") + 1.3, t))
            pz["arm_sl"] = {"fwd": 75 * push + 5, "out": 10 + 15 * push}
            face = dict(HYPE)
            if t >= b("open") + 1.2:                              # presenting it, proud
                k = ss(b("open") + 1.2, b("noob_close") + 0.1, t)
                yaw = lerp(_face_to(p, knob), _face_to(p, S_), k)
                pz["arm_sl"] = {"fwd": 20 * k, "out": 10 + 70 * k}
                pz["chest_lean"] = -8 * k
                face = dict(NF["happy"]) if t < b("noob_close") else dict(HYPE)
            if t >= b("stare"):                                   # waiting for applause; a glance at the door
                gl = ss(b("stare") + 0.6, b("stare") + 0.8, t) * (1 - ss(b("stare") + 1.2, b("stare") + 1.4, t))
                tl, nd = _look(yaw, p, knob + Vector((0, -1, 0)), h=1.4)
                pz["head_turn"], pz["head_nod"] = tl * gl, nd * gl
                face = dict(NF["happy"])
            if t >= b("chime"):
                p = N_DOOR.lerp(N_BUILD, ss(b("chime"), b("chime") + 0.6, t))
                yaw = _face_to(p, S_)
                if t < b("chime") + 0.6:
                    _run(pz, t, b("chime"), 2.0, k=0.35, steve=False)
            if t >= b("duck_gone"):                               # the duck goes: the smile drops at once
                p = N_BUILD.copy()
                yaw = _face_to(p, DUCK_AT)
                pz["arm_sl"] = {"fwd": 10, "out": 10}
                pz["chest_lean"] = 0
                face = dict(NF["shock"])
            if t >= b("noob_duck") - 0.1:                         # "Hey! Where's my duck?": worried, a step forward
                k = ss(b("noob_duck") - 0.1, b("noob_duck") + 0.3, t)
                p = N_BUILD + Vector((0.35, 0.0, 0)) * k
                face = dict(NF["worried"])
                pz["arm_sl"] = {"fwd": 30 * k, "out": 40 * k}
                pz["chest_lean"] = 10 * k
            if t >= b("scan"):                                    # leaning in, anxious; glances at his castle
                p = N_BUILD + Vector((0.35, 0.0, 0))
                face = dict(NF["worried"])
                pz["chest_lean"] = 12
                look_at = Vector(E.PA.root.location)
                if b("patch_delete") + 1.6 <= t < b("patch_delete") + 2.4:
                    look_at = LEDGE_TOP + Vector((0, 0, 0.8))
                if b("patch_delete") + 3.6 <= t:
                    look_at = LEDGE_TOP + Vector((0, 0, 0.8))
                tl, nd = _look(yaw, p, look_at, h=1.4, lim=75)
                pz["head_turn"], pz["head_nod"] = tl, nd
            if t >= b("castle_gone"):                             # he turns to the castle as it goes
                p = N_BUILD + Vector((0.35, 0.0, 0))
                yaw = lerp(_face_to(p, DUCK_AT), _face_to(p, LEDGE_TOP), ss(b("castle_gone"), b("castle_gone") + 0.4, t))
                face = dict(NF["shock"])
                pz["head_turn"], pz["head_nod"] = 0, -5
            if t >= b("statue_gone"):                             # then the statue: steps toward it, hands out
                k = ss(b("statue_gone") + 0.2, b("noob_no") + 0.1, t)
                p = N_BUILD + Vector((0.35, 0.0, 0)) + Vector((0.55, -0.1, 0)) * k
                yaw = _face_to(p, CP_TOP)
                pz["arm_sl"] = {"fwd": 70 * k, "out": 25 * k}
                pz["arm_sr"] = {"fwd": 55 * k, "out": 20 * k, "elbow": 0}
                pz["chest_lean"] = 14 * k
                face = dict(NF["scared"])
                if b("noob_no") <= t < b("noob_no", 1) + 0.1:
                    face = dict(NF["shout"])
                    pz["arm_sl"] = {"fwd": 85, "out": 30}
                    pz["arm_sr"] = {"fwd": 70, "out": 25}
            if t >= b("dragon"):                                  # looking up; recoiling
                p0 = N_BUILD + Vector((0.9, -0.1, 0))
                p = p0.copy()
                tl, nd = _look(yaw, p, Vector(E.D.root.location), h=1.4, lim=80)
                pz["head_turn"], pz["head_nod"] = tl, nd
                pz["arm_sl"] = {"fwd": 30, "out": 30}
                pz["arm_sr"] = {"fwd": 25, "out": 25}
                pz["chest_lean"] = -8
                face = dict(NF["scared"])
            if t >= b("hush"):                                    # the course west goes, stone by stone
                rc = ss(b("stairs_gone") + 0.2, b("stairs_gone") + 1.2, t)
                p = (N_BUILD + Vector((0.9, -0.1, 0))).lerp(N_BUILD + Vector((1.25, -0.35, 0)), rc)
                yaw = _face_to(p, Vector((-15.0, 0.5, 0)))
                pz["head_turn"], pz["head_nod"] = 0, 0
                pz["chest_lean"] = -10 * rc
                pz["arm_sl"] = {"fwd": 40 * rc, "out": 30}
                pz["arm_sr"] = {"fwd": 30 * rc, "out": 25}
                face = dict(NF["scared"])
            if t >= b("stairs_gone") + 2.4:                       # and east; then he looks to Steve
                yaw = _face_to(p, Vector(E.S.holder.location))
                face = dict(NF["scared"])
            if t >= b("void"):
                face = {"both_h": 1.9, "both_w": 1.05, "m_arch": 0.15, "both_ps": 0.8}
    pz = life(E, "noob", pz, face, t, 1.6)
    M.set_noob(E, p, yaw, pz, face, t)
    bpy.context.view_layer.update()
    E.fist_now = _hand(E)


# ------------------------------------------------------------------ Steve
def steve(E, t):
    from ep09_new import SF
    S = E.S
    if t < b("still") + 1.2:                                      # Ep4's last instant goes on: his alarmed glance
        _use(E, 4)
        keep, E.mouth = E.mouth, {}
        E4.steve(E, E.T4 + t)
        E.mouth = keep
        _use(E, 5)
        return
    face = dict(SF["stunned"])
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.0))
    P_ = Vector(E.PA.root.location)
    p = STEVE0.copy()
    yaw = _face_to(p, N_)
    pz = {"arm_sr": {"fwd": 20, "out": 25, "elbow": 15}, "arm_sl": {"fwd": 20, "out": 30, "elbow": 40}}
    look_at = N_
    lim = 70
    if t < b("implode"):                                          # the reach: a hand up, too late again
        k = ss(b("reach") + 0.1, b("poke3"), t)
        pz["arm_sl"] = {"fwd": 20 + 55 * k, "out": 20, "elbow": 40 * (1 - k)}
        pz["chest_lean"] = 10 * k
        face = dict(SF["scared"]) if t >= b("reach") + 0.1 else dict(SF["stunned"])
    elif t < b("hammer") + 0.4:                                   # it pours into him: a flinch, staring
        fl = math.exp(-((t - b("implode") - 0.1) / 0.15) ** 2)
        pz["chest_lean"] = -10 * fl
        face = dict(SF["stunned"])
    elif t < b("lower"):                                          # the box round the plate; the duck: a half step back
        dk = b("duck") + 0.35
        look_at = DUCK_AT + Vector((0, 0, 1.0))
        jb = ss(dk - 0.05, dk + 0.2, t)
        p = STEVE0.lerp(STEVE_D, jb) + Vector((0, 0, 0.1 * math.sin(math.pi * jb)))
        yaw = lerp(_face_to(STEVE0, N_), _face_to(p, DUCK_AT), ss(b("hammer") + 0.4, b("duck"), t) * 0.6)
        pz["arm_sr"] = {"fwd": 30, "out": 40, "elbow": 35}
        pz["hips_drop"] = 0.08 * jb
        face = dict(SF["stunned"]) if t < dk else dict(SF["amazed"])
        if t >= b("noob_build") + 0.6:
            look_at = N_
    else:
        p = STEVE_D.copy()
        yaw = _face_to(p, N_)
        if t < b("statue"):                                       # the pickaxe down, slowly; "Since when?"
            d = ss(b("lower"), b("lower") + 0.5, t)
            pz["arm_sr"] = {"fwd": 30 - 25 * d, "out": 40 - 30 * d, "elbow": 35 - 25 * d}
            pz["arm_sl"] = {"fwd": 8, "out": 8, "elbow": 10}
            face = dict(SF["flat"]) if t >= b("steve_since") else dict(SF["stunned"])
        elif t < b("castle"):
            pz["arm_sr"] = {"fwd": 5, "out": 10, "elbow": 10}
            pz["arm_sl"] = {"fwd": 8, "out": 8, "elbow": 10}
            sl = b("statue") + 0.7
            top = E.things["statue"].box[1]
            if t < b("crane"):                                    # the slam: a flinch; he turns to it
                look_at = (E.things["statue"].box[0] + top) / 2
                yaw = lerp(_face_to(p, N_), _face_to(p, CP_TOP), ss(b("statue") + 0.1, b("statue") + 0.6, t) * 0.7)
                fl = math.exp(-((t - sl - 0.05) / 0.12) ** 2)
                pz["chest_lean"] = -10 * fl
                face = dict(SF["stunned"])
                lim = 85
            elif t < b("steve_big"):                              # the crane: the head right up to its top; a blink down
                yaw = _face_to(p, CP_TOP) * 0.7 + _face_to(p, N_) * 0.3
                look_at = Vector((top.x * 0.5 + CP_TOP.x * 0.5, CP_TOP.y, top.z))
                lim = 85
                face = dict(SF["flat"])
                if t >= b("crane") + 0.5:
                    look_at = N_
                    face = dict(SF["flat"])
            else:                                                 # "Why is it so big?" deadpan
                face = dict(SF["flat"])
        elif t < b("open"):                                       # the castle; the pinch; "Build us a way home."
            pz["arm_sr"] = {"fwd": 5, "out": 10, "elbow": 10}
            if t < b("pinch"):
                look_at = LEDGE_TOP + Vector((0, 0, 0.8))
                face = dict(SF["flat"])
            else:
                pn = ss(b("pinch"), b("pinch") + 0.25, t) * (1 - ss(b("pinch") + 0.55, b("pinch") + 0.7, t))
                pt = ss(b("pinch") + 0.6, b("pinch") + 0.8, t) * (1 - ss(b("steve_home", 1), b("steve_home", 1) + 0.3, t))
                pz["arm_sl"] = {"fwd": 150 * pn + 80 * pt, "out": 10 + 25 * pt, "elbow": 125 * pn}
                pz["head_nod"] = 10 * pn
                face = dict(SF["flat"])
                if pt > 0.3:
                    yaw = _face_to(p, Vector((-6.5, -6.0, 0)))
                    look_at = N_
        else:                                                     # the door gag: the deadpan stare, then the rest
            door_c = DOOR_HINGE + Vector((DOOR_W / 2, -0.4, 1.0))
            pz["arm_sr"] = {"fwd": 5, "out": 10, "elbow": 10}
            look_at = door_c
            face = dict(SF["flat"])
            if b("noob_close") <= t < b("stare"):
                look_at = N_
            if b("chime") <= t:
                look_at = N_
                if t >= b("chime") + 0.6:                         # the chime behind him: a look over his shoulder
                    look_at = DUCK_AT + Vector((0, 0, 1.0))
                    yaw = lerp(_face_to(p, N_), _face_to(p, DUCK_AT), ss(b("chime") + 0.6, b("chime") + 0.95, t) * 0.75)
                    face = dict(SF["stunned"])
                    lim = 85
            if b("noob_duck") <= t:
                yaw = _face_to(p, N_)
                look_at = N_
                face = dict(SF["worried"])
            if b("scan") <= t:
                look_at = P_
                if b("patch_delete") + 1.0 <= t:
                    look_at = DUCK_AT + Vector((0, 0, 0.6))
                face = dict(SF["worried"])
            if b("castle_gone") <= t:
                look_at = LEDGE_TOP + Vector((0, 0, 0.8))
                face = dict(SF["scared"])
            if b("statue_gone") <= t:                             # the statue over his shoulder
                yaw = _face_to(p, CP_TOP) * 0.8 + _face_to(p, N_) * 0.2
                look_at = (E.things["statue"].box[0] + E.things["statue"].box[1]) / 2
                lim = 85
            if b("noob_no") <= t:
                yaw = _face_to(p, N_)
                look_at = N_
            if b("dragon") <= t:
                look_at = Vector(E.D.root.location)
                lim = 85
            if b("hush") <= t:                                    # the course west; then east, behind him
                yaw = _face_to(p, Vector((-15.0, 0.5, 0)))
                look_at = Vector((-15.0, 0.5, 0.5))
                face = dict(SF["scared"])
                pz["arm_sr"] = {"fwd": 25, "out": 25, "elbow": 20}
            if b("stairs_gone") + 2.4 <= t:
                look_at = Vector((6.0, -1.0, 0.5))
                yaw = _face_to(p, Vector((-15.0, 0.5, 0))) + 40
                lim = 85
            if b("void") <= t:                                    # staring where the stones were; slowly to them
                look_at = Vector((-15.0, 0.5, 0.5))
                yaw = _face_to(p, Vector((-15.0, 0.5, 0)))
                face = dict(SF["stunned"])
                sh = ss(b("steve_us") - 0.3, b("steve_us") + 0.6, t)
                pz["arm_sr"] = {"fwd": 10, "out": 10, "elbow": 10}
                pz["chest_lean"] = 6 * sh
                if t >= b("steve_us") - 0.3:
                    turn = ss(b("steve_us") - 0.3, b("steve_us") + 0.9, t)
                    yaw = lerp(_face_to(p, Vector((-15.0, 0.5, 0))), _face_to(p, N_), turn)
                    look_at = Vector((-15.0, 0.5, 0.5)).lerp(N_, turn)
                    face = dict(SF["flat"])
    tl, nd = _look(yaw, p, look_at, lim=lim)
    pz["head_turn"], pz["head_nod"] = tl, nd + pz.get("head_nod", 0)
    pz = life(E, "steve", pz, face, t, 2.7)
    M.set_steve(E, p, yaw, pz, face, t)


# ------------------------------------------------------------------ the door
def door(E, t):
    k = ss(b("open") + 0.3, b("open") + 1.35, t)
    E.door_hinge.rotation_euler = (0, 0, math.radians(-95.0 * (k ** 1.3)))


def castle_flags(E, t):
    for k, ob in enumerate(E.castle_flags):
        ob.rotation_euler = (0, 0, 0.25 * math.sin(t * 4 + k))


# ------------------------------------------------------------------ one frame
def apply(E, t):
    prepare(E)
    _use(E, 5)
    E._t_now = t
    name, t0, t1 = which(t)
    E.cam_loc_now = _cam(E, t, name, t0, t1)[0]
    if not hasattr(E, "fist_now"):
        E.fist_now = REACT_N + Vector((0.5, 0, 1.0))
    if not hasattr(E, "cube_s_now"):
        E.cube_s_now = E4.SIZES[2]
    ep4_world(E, t)
    dragon(E, t)
    sun(E, t)
    for nm in ("duck", "statue", "castle", "door"):
        thing(E, nm, t)
    door(E, t)
    castle_flags(E, t)
    course(E, t)
    patch(E, t)
    steve(E, t)
    noob(E, t)
    cube(E, t)
    hammer(E, t)
    bpy.context.view_layer.update()
    pixels(E, t)
    gizmo(E, t)
    scanplane(E, t)
    camera(E, t, name, t0, t1)
    E2.set_wash(E, 0.0)


# ------------------------------------------------------------------ the camera
def camera(E, t, shot, t0, t1):
    from ep10_p2_omg import handheld
    loc, look, lens, fstop, focus, shake = _cam(E, t, shot, t0, t1)
    sl = build_time("statue") + SNAP + SCAN
    shake += 1.6 * math.exp(-max(0.0, t - sl) * 5) * (t >= sl)                       # the statue lands
    shake += 0.8 * math.exp(-max(0.0, t - b("implode")) * 4) * (b("implode") <= t < b("hammer"))
    shake += 0.6 * math.exp(-max(0.0, t - b("dragon")) * 5) * (t >= b("dragon"))
    for nm, beat, off, dur in ERASES:
        te = b(beat) + off + dur
        shake += 0.35 * math.exp(-max(0.0, t - te) * 8) * (t >= te)
    if shot == "open":
        shake = 0.05
    y1, p1, r1 = handheld(E.T4 + t, shake)
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
    if shot == "open":                                            # Ep4's last camera: Steve's alarmed glance
        return STEVE0 + _c(-2.6, -1.8, 1.5), STEVE0 + _c(0, 0, 1.5), 42, 2.8, None, 0.05
    if shot == "stunned":                                         # the Noob's stunned face (Ep4's shot); his eyes slide
        return REACT_N + _c(0.6, -3.1, 1.55), REACT_N + _c(0, 0, 1.6), 42, 2.6, None, 0.05
    if shot == "master":                                          # Ep4's locked master (the ruler): the third poke
        return _c(-5.4, -8.6, 1.5), _c(-5.8, -0.4, 0.95), 30, 30, None, 0.15
    if shot == "hand":                                            # close: the code pours into his fist
        f = Vector(E.fist_now)
        return f + _c(1.3, -2.4, 0.35), f + _c(-0.2, 0.2, 0.05), 40, 3.2, None, 0.25
    if shot == "hammer":                                          # the Noob and his new hammer
        return N_BUILD + _c(1.4, -3.0, 1.5), N_BUILD + _c(0.2, 0, 1.45), 34, 2.8, None, 0.2
    if shot == "duck":                                            # wide: the box round the ring, the duck, Steve across the gap
        return _c(-2.9, -7.4, 1.7), _c(-5.6, -0.2, 1.0), 26, 30, None, 0.2
    if shot == "build":                                           # "I can BUILD stuff!"
        return N_BUILD + _c(1.6, -3.1, 1.3), N_BUILD + _c(0.15, 0, 1.55), 32, 2.8, None, 0.25
    if shot == "since":                                           # Steve: "Since when?"
        return STEVE_D + _c(-2.4, -1.5, 1.45), STEVE_D + _c(0, 0, 1.5), 38, 2.8, None, 0.15
    if shot == "block":                                           # "Since the block!" the hammer up (a little low)
        return N_BUILD + _c(1.2, -2.8, 1.05), N_BUILD + _c(0.1, 0, 1.6), 34, 2.8, None, 0.2
    if shot == "statue":                                          # wide: the swing, the box, the statue slams down
        return _c(-9.5, -11.5, 2.2), _c(1.5, 0.0, 3.0), 18, 30, None, 0.2
    if shot == "me":                                              # the Noob, arms wide, the statue far behind him
        return N_BUILD + _c(-1.6, -3.4, 1.0), N_BUILD + _c(1.2, 0.4, 1.9), 26, 4.0, None, 0.2
    if shot == "crane":                                           # low on Steve, the statue towering behind
        return STEVE_D + _c(-2.2, -3.0, 0.75), STEVE_D + _c(1.6, 0.5, 2.3), 24, 4.0, (STEVE_D - _c(-4.55, -4.2, 0)).length, 0.15
    if shot == "see":                                             # "So everyone can see me!"
        return N_BUILD + _c(1.4, -2.9, 1.4), N_BUILD + _c(0.15, 0, 1.55), 34, 2.8, None, 0.2
    if shot == "castle":                                          # behind him the castle snaps onto the ledge
        return N_BUILD + _c(0.9, -4.6, 1.5), _c(-7.1, 1.2, 1.3), 26, 30, None, 0.2
    if shot == "pinch":                                           # Steve: the pinch, the point
        return STEVE_D + _c(-2.4, -1.6, 1.45), STEVE_D + _c(0, 0, 1.5), 36, 2.8, None, 0.15
    if shot == "door":                                            # the salute, the swing, the door at the edge
        return _c(-10.2, -7.6, 1.5), _c(-7.2, -1.9, 1.1), 26, 30, None, 0.2
    if shot == "open_door":                                       # from behind the door: it swings open onto the sky
        return _c(-7.55, 0.9, 1.35), _c(-7.45, -6.0, 0.8), 26, 30, None, 0.15
    if shot == "stare":                                           # Steve's deadpan stare
        return STEVE_D + _c(-2.0, -1.0, 1.5), STEVE_D + _c(0, 0, 1.55), 46, 2.6, None, 0.05
    if shot == "chime":                                           # the two of them; between them the duck, then the erase
        return _c(-4.4, -8.6, 1.6), _c(-4.9, -0.2, 1.1), 24, 30, None, 0.12
    if shot == "where":                                           # "Hey! Where's my duck?"
        return N_ + _c(1.5, -2.9, 1.45), N_ + _c(0.1, 0, 1.5), 36, 2.8, None, 0.15
    if shot == "scan":                                            # Patch over the empty ring, the beam down on it
        return _c(-3.2, -7.0, 2.1), _c(-6.3, -0.2, 1.2), 26, 30, None, 0.12
    if shot == "patch":                                           # Patch, three-quarter; the beam whips to the castle
        p = Vector(E.PA.root.location)
        return p + _c(-1.9, -2.4, -0.25), p + _c(0, 0, 0), 38, 3.0, None, 0.12
    if shot == "castle_gone":                                     # behind the Noob: the castle erased
        return N_ + _c(0.8, -4.4, 1.5), LEDGE_TOP + _c(0.3, -0.5, 0.4), 28, 30, None, 0.15
    if shot == "statue_gone":                                     # over Steve's shoulder: the statue erased
        return STEVE_D + _c(-1.6, -1.9, 1.95), _c(7.5, -0.6, 4.0), 30, 30, None, 0.2
    if shot == "no":                                              # "NO!"
        return N_ + _c(2.0, -2.6, 1.3), N_ + _c(0, 0, 1.5), 32, 2.8, None, 0.35
    if shot == "dragon":                                          # up at the sealed dragon: it flickers
        return _c(-4.6, -6.5, 1.2), Vector(E.D.root.location) + _c(0, 0, 0.5), 22, 30, None, 0.25
    if shot == "west":                                            # locked on the course west: the stones go one by one
        return _c(-6.2, -3.6, 2.3), _c(-15.5, 0.4, 0.6), 26, 30, None, 0.0
    if shot == "east":                                            # east: the stepping stone, the checkpoint; Steve
        return _c(-4.4, -3.9, 1.8), _c(5.0, -0.9, 0.6), 24, 30, None, 0.05
    if shot == "void":                                            # the lonely wide: two pads in the sky
        return _c(-4.0, -13.5, 4.2).lerp(_c(-4.0, -12.7, 4.0), u), _c(-4.2, 0.0, 1.6), 22, 30, None, 0.05
    if shot == "us":                                              # Steve, close: "...That wasn't us."
        return STEVE_D + _c(-1.9, -1.4, 1.5), STEVE_D + _c(0, 0, 1.55), 46, 2.6, None, 0.04
    if shot == "hold":                                            # hold: the three of them, the door, the dragon
        return _c(-3.0, -12.0, 3.4).lerp(_c(-3.2, -13.2, 3.6), u), _c(-4.0, 0.5, 2.6), 22, 30, None, 0.04
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
    E.tl = tl
    B.clear()
    B.update(E.B5)
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
