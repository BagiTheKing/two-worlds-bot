"""The movie, chapter 2 ("The Plan"), in the new look and in 16:9.

It picks up on Episode 1's last shot (the eye in the sky's crack, the same model and the same angle),
then the same meadow, the same floating oak: Steve's plan (a portal home, built block by block on the
place sounds), the Noob and the button. v5 (the creator's corrections, story/movie/fixes_2026-11-23.md):
the zombies come through close and scary (a hand through the swirl, a head, red eyes; one locks on Steve
and lunges); the cube that kills the Noob seen leaving the portal, in slow motion, his parts flying clear
of the tree; the button seen driving the portal before Plan B; a slow-motion swing and the button
shattering close; the suck, the last zombie clinging to the frame; then the dragon: its shadow over the
meadow, the dive, the clinging zombie snatched, the circle, "Whoa! Is that a dragon?...", "Yes.", its
roar, "Into the portal. Now!", the run and the jump, the dragon diving in after them. Sound and timing:
episodes/movie_ep02_the_plan.json (the v5 sound preview passed review, movie/ep02_v5).

    python src/lookdev/movie_ep02.py TIMELINE VOICE TEX_DIR ASSETS OUT_DIR [--times 1.0,5.0] [--res 720]
"""
import argparse
import json
import math
import os
import random

import numpy as np
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import movie_ep00 as M                                                # noqa: E402
import movie_ep01 as E1                                               # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402
from kit.timeref import spread                                        # noqa: E402

B = M.B
STEVE0 = E1.STEVE2                         # where chapter 1 leaves Steve
NOOB0 = E1.NOOB_BACK                       # and the Noob
PORTAL = Vector((-3.8, 3.8, 0.0))          # the portal's foot (its frame 6 wide, 8 tall, facing -y)
PW, PH = 6, 8
BUILD_AT = Vector((-0.2, 2.2, 0.0))        # where Steve builds from: just right of the frame, placing to his left
STEVE_REST = Vector((1.75, -0.45, 0.0))    # afterwards he goes to lean by the oak
PILLAR = Vector((0.5, -0.5, 0.0))          # the button's stone (a block: x 0..1, y -1..0)
NOOB_BTN = Vector((1.75, -0.05, 0.0))      # the Noob at the button: just off the stone (x 0.5..1.5), his right hand over it
PAD = Vector((2.6, -3.0, 0.0))             # the respawn pad
STEVE_DONT = Vector((-0.6, 1.0, 0.0))      # Steve after his two steps back
STEVE_DODGE = Vector((-1.6, -1.6, 0.0))    # where the chaos pushes him
STEVE_SMASH = Vector((-0.05, -0.1, 0.0))  # Steve at the button (west of it, facing +x)
STEVE_TIRED = Vector((-0.9, -1.9, 0.0))    # after it, he staggers back a few steps (clear of the Noob's way to the portal)
NOOB_PORTAL = Vector((0.0, 2.6, 0.0))      # "Hi!": at the portal's right edge, so a camera sees his face and the portal
MIRROR_CAM = Vector((-3.0, 0.0, 0.0))      # "Hi!": front-left of him, seeing into the portal
WAVED_CAM = Vector((0.0, -2.2, 0.0))       # "It waved back": close on him, the portal (and the figure) behind
NOOB_WATCH = Vector((1.9, -0.6, 0.0))
BUILD_CAM = Vector((-0.6, -5.0, 0.0))      # the build's camera (the frame, Steve at its end, the button, the Noob)      # where the Noob watches the building from     # the Noob in front of the dark portal, at its right
ZOMBIES = [  # (out of the portal at x, where it goes after stepping out, where the chaos takes it)
    (-4.4, Vector((-4.7, 0.9, 0)), Vector((-4.2, -0.8, 0))),     # the first: the hand through the swirl
    (-3.0, Vector((-3.0, 1.7, 0)), Vector((-3.4, -3.4, 0))),     # the eager one: locks on Steve, lunges
    (-2.2, Vector((-2.0, -0.4, 0)), Vector((-4.0, -2.6, 0))),
    (-4.1, Vector((-4.4, 2.0, 0)), None),                        # pulled through on the button's flashes
    (-2.7, Vector((-2.6, 2.3, 0)), None),                        # ... the last one: it clings to the frame
]
ZH = 2.35                                  # tall (the creator: "tall, hunched, ragged skin, glowing red eyes")
STEVE_BACKED = Vector((0.45, 2.2, 0.0))   # where Steve backs off to from the lunge
NOOB_NEAR = Vector((-0.27, -0.64, 0.0))    # beside Steve as they face the dragon (north-east of him), not in his line    # the Noob comes over to Steve after the suck
DRAGON_SCALE = 0.95
STEVE_D = Vector((0.6, -3.2, 0.0))          # they back away from the dragon: real distance from the portal for the run
NOOB_D = Vector((1.45, -2.05, 0.0))


def b(name, i=0):
    return B[name][i]


def gp(E, v):
    return Vector((v.x, v.y, E.ground(v.x, v.y)))


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    # the clearings keep their first coordinates: the plants come from one random sequence, and moving one
    # clearing reshuffles the grass in every shot (already-rendered shots are reused)
    clear = [(STEVE0.x, STEVE0.y, 1.3), (NOOB0.x, NOOB0.y, 1.2), (BUILD_AT.x, BUILD_AT.y, 1.4),
             (PILLAR.x + 0.5, PILLAR.y + 0.5, 1.2), (1.2, -0.05, 1.0), (PAD.x, PAD.y, 1.6),
             (STEVE_DONT.x, STEVE_DONT.y, 1.2), (STEVE_DODGE.x, STEVE_DODGE.y, 1.4), (-1.9, 2.4, 1.4),
             (-3.8, 3.8, 3.6), (-3.8, 1.8, 2.6), (-5.0, 0.4, 1.2), (-2.8, -0.4, 1.2), (-0.2, 1.0, 1.2),
             (-3.6, -1.2, 1.2), (-1.0, -2.4, 1.2), (0.6, -2.0, 1.0), (1.0, 0.75, 1.2), (0.1, 0.05, 1.3),
             (2.0, -6.5, 2.4), (-1.0, -7.5, 2.4), (4.0, -4.5, 1.6), (-6.0, -2.0, 1.6), (3.0, 1.8, 1.4), (-0.6, -3.6, 1.6),
             (-6.8, -1.4, 1.8), (-5.6, -0.8, 1.6), (-7.2, -3.4, 2.0), (-4.6, -0.2, 1.6), (0.8, 1.2, 1.4),
             (NOOB_WATCH.x, NOOB_WATCH.y, 1.0), (-5.0, -2.6, 1.6), (-4.2, -5.2, 1.6), (-4.6, -2.0, 1.4), (-0.3, 2.9, 1.0), (-1.4, -4.4, 1.6), (-0.6, -5.0, 1.6), (-0.9, -4.6, 1.4), (STEVE_REST.x, STEVE_REST.y, 1.0), (STEVE_TIRED.x, STEVE_TIRED.y, 1.2), (0.2, 3.0, 1.2), (-0.3, -4.7, 1.6), (1.2, 5.2, 1.4), (-4.4, 1.8, 1.4), (-3.6, -5.4, 1.6), (3.4, -1.0, 1.2), (-0.8, -6.6, 1.6), (-3.2, 2.0, 1.2), (3.6, -1.4, 1.2), (0.2, -1.6, 1.2)]
    E = M.build_forest(tl, tex_dir, assets, res, samples, drop_trees=[(M.NEAR_OAK[0], M.NEAR_OAK[1])], clear=clear)
    E.tl = tl
    E.tex_dir = tex_dir
    E1._oak(E, assets)                      # the same oak; its lowest log is gone (the tree floats)
    E.log0.hide_render = True
    E1._decal(E, assets)
    E.shell.hide_render = True
    E1._crack(E)                            # the same crack and eye as chapter 1's last shot
    from props import sprite_item, hold
    pk = sprite_item("iron_pickaxe", os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets",
                                                  "minecraft", "textures", "item"), px=0.072)
    hold(E.S.arm, pk, "sr", up=25, face=60, collection=[E.S.rig])
    E.P.root.location = (0, 0, -500)
    _portal(E, assets)
    _button(E, assets)
    _pad(E, assets)
    _junk(E, assets)
    _zombies(E, assets)
    _burst(E)
    _dragon(E, assets)
    _finish_materials(E)
    _ripple(E)
    E.sc.render.motion_blur_shutter = 0.28                 # fast props stay readable
    E.mats_sky = {}
    return E


def _blockmat(name, assets, tex, rough=0.6, spec=0.3):
    from world import material
    B_ = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    return bpy.data.materials.get(name) or material(name, os.path.join(B_, tex), rough=rough, spec=spec)


def _cube(E, name, size, mat, col=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size, size, size) if not isinstance(size, tuple) else size
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.uv.cube_project(cube_size=1.0 / (size if not isinstance(size, tuple) else max(size)))
    bpy.ops.object.mode_set(mode="OBJECT")
    if mat is not None:
        ob.data.materials.append(mat)
    ob.location = (0, 0, -300)
    return ob


def _uv_full(ob):
    """Every face shows the whole texture (a block's face)."""
    me = ob.data
    uv = me.uv_layers[0]
    for p_ in me.polygons:
        for k, li in enumerate(p_.loop_indices):
            uv.data[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[k % 4]


def _portal(E, assets):
    """The portal Steve builds: the finale's portal (portal.py) as a 6x8 obsidian frame. Its blocks arrive
    one by one on the place sounds; its membrane flashes, swirls, goes dark, and lets the figure be seen."""
    from portal import build_portal
    E.PP = build_portal(E.sc, assets, at=tuple(gp(E, PORTAL)), w=PW, h=PH, name="plan_portal")
    # the order Steve places them: the bottom row, the left side up, the top, the right side down
    cells = [(i, 0) for i in range(PW)] + [(0, j) for j in range(1, PH)] + [(i, PH - 1) for i in range(1, PW)] + \
            [(PW - 1, j) for j in range(PH - 2, 0, -1)]
    home = {tuple(round(v, 3) for v in ob["home"]): ob for ob in E.PP.blocks}
    E.portal_order = [home[(round(i - PW / 2 + 0.5, 3), 0.0, round(j + 0.5, 3))] for i, j in cells]
    # the membrane: see-through when dark (the figure is behind it); a value node drives it
    m = E.PP.membrane.data.materials[0]
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    bsdf = nt.nodes["Principled BSDF"]
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    see = nt.nodes.new("ShaderNodeValue")
    see.name = "see"
    see.outputs[0].default_value = 0.0
    nt.links.new(see.outputs[0], mx.inputs[0])
    nt.links.new(bsdf.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    E.portal_see = see
    # its colour dims when it goes dark (the surface itself, not only its glow)
    src = bsdf.inputs["Base Color"].links[0].from_socket
    dim = nt.nodes.new("ShaderNodeMix")
    dim.data_type = "RGBA"
    dim.blend_type = "MULTIPLY"
    dim.inputs[0].default_value = 1.0
    nt.links.new(src, dim.inputs[6])
    dim.inputs[7].default_value = (1, 1, 1, 1)
    nt.links.new(dim.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(dim.outputs[2], bsdf.inputs["Emission Color"])
    E.portal_dim = dim
    E.portal_power = nt.nodes[m["power"]]
    E.portal_flow = nt.nodes[m["flow"]]
    # the flash: a white sheet in the opening
    bpy.ops.mesh.primitive_plane_add(size=1)
    fl = bpy.context.active_object
    fl.name = "portal_flash"
    fm = bpy.data.materials.new("portal_flash")
    fm.use_nodes = True
    fnt = fm.node_tree
    for n_ in list(fnt.nodes):
        fnt.nodes.remove(n_)
    em = fnt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 0.96, 1, 1)
    em.inputs["Strength"].default_value = 12.0
    fo = fnt.nodes.new("ShaderNodeOutputMaterial")
    fnt.links.new(em.outputs[0], fo.inputs["Surface"])
    fl.data.materials.append(fm)
    fl.parent = E.PP.root
    fl.location = (0, -0.05, PH / 2)
    fl.rotation_euler = (math.radians(90), 0, 0)
    fl.scale = (PW - 2, PH - 2, 1)
    fl.visible_shadow = False
    E.portal_flash = fl
    E.portal_flash_em = em
    # the room behind the dark surface: a deep purple tunnel, seen only through the opening
    # (its walls face inward; seen from outside they are see-through)
    import bmesh
    bm = bmesh.new()
    x0, x1, z0, z1, d = -PW / 2 + 1, PW / 2 - 1, 1.0, PH - 1.0, 6.0
    vs = [bm.verts.new(v) for v in [(x0, 0.6, z0), (x1, 0.6, z0), (x1, 0.6, z1), (x0, 0.6, z1),
                                    (x0, d, z0), (x1, d, z0), (x1, d, z1), (x0, d, z1)]]
    for f in ((0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0), (4, 7, 6, 5)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.normal_flip()                                        # inward
    me = bpy.data.meshes.new("portal_room")
    bm.to_mesh(me)
    room = bpy.data.objects.new("portal_room", me)
    E.sc.collection.objects.link(room)
    room.parent = E.PP.root
    rm = bpy.data.materials.new("portal_room")
    rm.use_nodes = True
    rnt = rm.node_tree
    for n_ in list(rnt.nodes):
        rnt.nodes.remove(n_)
    geo = rnt.nodes.new("ShaderNodeNewGeometry")
    emr = rnt.nodes.new("ShaderNodeEmission")
    emr.inputs["Color"].default_value = (0.16, 0.03, 0.26, 1)
    emr.inputs["Strength"].default_value = 1.4
    trr = rnt.nodes.new("ShaderNodeBsdfTransparent")
    mxr = rnt.nodes.new("ShaderNodeMixShader")
    ro = rnt.nodes.new("ShaderNodeOutputMaterial")
    rnt.links.new(geo.outputs["Backfacing"], mxr.inputs[0])
    rnt.links.new(emr.outputs[0], mxr.inputs[1])
    rnt.links.new(trr.outputs[0], mxr.inputs[2])
    rnt.links.new(mxr.outputs[0], ro.inputs["Surface"])
    room.data.materials.append(rm)
    room.visible_shadow = False
    room.visible_diffuse = False
    E.portal_room = room
    bl = bpy.data.objects.new("portal_room_light", bpy.data.lights.new("portal_room_light", "AREA"))
    E.sc.collection.objects.link(bl)
    bl.data.size = 3.0
    bl.data.color = (0.9, 0.35, 1.0)
    bl.data.energy = 0.0
    bl.parent = E.PP.root
    bl.location = (0, 5.5, PH / 2)
    bl.rotation_euler = (math.radians(90), 0, 0)                 # shining toward -y, at the figure's back
    bl.visible_camera = False
    bl.visible_glossy = False
    E.portal_room_light = bl


def _button(E, assets):
    st = _blockmat("w_stone_bricks", assets, "stone_bricks.png")
    E.pillar = _cube(E, "button_pillar", 1.0, st)
    _uv_full(E.pillar)
    red = bpy.data.materials.new("button_red")
    red.use_nodes = True
    bs = red.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.75, 0.03, 0.02, 1)
    bs.inputs["Roughness"].default_value = 0.25
    bs.inputs["Emission Color"].default_value = (1.0, 0.05, 0.03, 1)
    bs.inputs["Emission Strength"].default_value = 0.25
    E.button = _cube(E, "button", (0.42, 0.42, 0.16), red)
    E.button_shards = []
    rnd = random.Random(5)
    for k in range(9):
        s = rnd.uniform(0.07, 0.14)
        ob = _cube(E, f"button_shard_{k}", s, red)
        a = rnd.uniform(0, 2 * math.pi)
        v = Vector((math.cos(a) * rnd.uniform(1.2, 2.6), math.sin(a) * rnd.uniform(1.2, 2.6), rnd.uniform(2.0, 4.0)))
        E.button_shards.append((ob, v, Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9))), s))
    E.puffs = []                                   # a small dust puff where each block lands
    pm = bpy.data.materials.new("puff")
    pm.use_nodes = True
    pb = pm.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0.8, 0.8, 0.78, 1)
    pb.inputs["Roughness"].default_value = 1.0
    pb.inputs["Alpha"].default_value = 0.6
    for k in range(8):
        E.puffs.append(_cube(E, f"puff_{k}", 0.09, pm))
    bl = bpy.data.objects.new("button_light", bpy.data.lights.new("button_light", "POINT"))
    E.sc.collection.objects.link(bl)
    bl.data.color = (1.0, 0.08, 0.04)
    bl.data.energy = 0.0
    bl.data.shadow_soft_size = 0.2
    bl.location = (0, 0, -300)
    E.button_light = bl


def _pad(E, assets):
    """The respawn pad: a ring of stone with a glowing cyan rim, flat on the grass."""
    st = _blockmat("w_smooth_stone", assets, "smooth_stone.png")
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.85, depth=0.12)
    pad = bpy.context.active_object
    pad.name = "respawn_pad"
    pad.data.materials.append(st)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.82, minor_radius=0.045, major_segments=32, minor_segments=8)
    rim = bpy.context.active_object
    rim.name = "respawn_rim"
    rmat = bpy.data.materials.new("pad_rim")
    rmat.use_nodes = True
    nt = rmat.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.1, 0.9, 1.0, 1)
    bs.inputs["Emission Color"].default_value = (0.1, 0.9, 1.0, 1)
    bs.inputs["Emission Strength"].default_value = 4.0
    rim.data.materials.append(rmat)
    rim.parent = pad
    rim.location = (0, 0, 0.065)
    E.pad = pad
    E.pad_glow = bs
    E.pad_at = gp(E, PAD) + Vector((0, 0, 0.06))
    pad.location = (0, 0, -300)
    lt = bpy.data.objects.new("pad_light", bpy.data.lights.new("pad_light", "POINT"))
    E.sc.collection.objects.link(lt)
    lt.data.color = (0.2, 0.9, 1.0)
    lt.data.energy = 0.0
    lt.data.shadow_soft_size = 0.5
    lt.parent = pad
    lt.location = (0, 0, 0.4)
    E.pad_light = lt
    # where it comes from: a cyan spark shot out of the portal as it opens, and the beam it lands in
    sm = bpy.data.materials.new("pad_spark")
    sm.use_nodes = True
    snt = sm.node_tree
    for n_ in list(snt.nodes):
        snt.nodes.remove(n_)
    se = snt.nodes.new("ShaderNodeEmission")
    se.inputs["Color"].default_value = (0.3, 0.95, 1.0, 1)
    se.inputs["Strength"].default_value = 30.0
    so = snt.nodes.new("ShaderNodeOutputMaterial")
    snt.links.new(se.outputs[0], so.inputs["Surface"])
    E.spark = _cube(E, "pad_spark", 0.16, sm)
    E.spark.visible_shadow = False
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.8, depth=1.0)
    beam = bpy.context.active_object
    beam.name = "pad_beam"
    bm_ = bpy.data.materials.new("pad_beam")
    bm_.use_nodes = True
    bnt = bm_.node_tree
    for n_ in list(bnt.nodes):
        bnt.nodes.remove(n_)
    be = bnt.nodes.new("ShaderNodeEmission")
    be.inputs["Color"].default_value = (0.3, 0.95, 1.0, 1)
    bt = bnt.nodes.new("ShaderNodeBsdfTransparent")
    bmx = bnt.nodes.new("ShaderNodeMixShader")
    bo = bnt.nodes.new("ShaderNodeOutputMaterial")
    bnt.links.new(bt.outputs[0], bmx.inputs[1])
    bnt.links.new(be.outputs[0], bmx.inputs[2])
    bnt.links.new(bmx.outputs[0], bo.inputs["Surface"])
    beam.data.materials.append(bm_)
    beam.visible_shadow = False
    beam.location = (0, 0, -300)
    E.beam, E.beam_mix, E.beam_em = beam, bmx, be


def _junk(E, assets):
    """What the portal pours out: pink blocks (smaller than the world's), and a red-and-white barrier pole."""
    pink = _blockmat("w_pink_wool", assets, "pink_wool.png", rough=0.9, spec=0.1)
    rnd = random.Random(12)
    E.cubes = []
    n = 12
    launch = spread(b("pour_out") + 1.1, b("hit_see") + 0.4, n)
    for k in range(n):
        s = rnd.uniform(0.32, 0.5)
        ob = _cube(E, f"junk_{k}", s, pink)
        _uv_full(ob)
        land = Vector((rnd.uniform(-6.0, 3.2), rnd.uniform(-4.5, 2.2), 0))
        if (land - Vector((1.2, -0.05, 0.0))).length < 1.0 or (land - PAD).length < 1.2 or (land - PILLAR).length < 1.0:
            land += Vector((0.0, -1.3, 0))
        E.cubes.append({"ob": ob, "s": s, "t0": launch[k], "land": land, "spin": Vector((rnd.uniform(-7, 7), rnd.uniform(-7, 7), rnd.uniform(-4, 4))),
                        "sx": rnd.uniform(-1.6, 1.6), "sz": rnd.uniform(2.0, 5.5), "T": rnd.uniform(0.7, 1.0)})
    # the cube that hits the Noob
    hit = _cube(E, "junk_hit", 0.42, pink)
    _uv_full(hit)
    E.hit_cube = hit
    # the barrier pole: red and white bands
    bpy.ops.mesh.primitive_cube_add(size=1)
    pole = bpy.context.active_object
    pole.name = "barrier_pole"
    pole.scale = (0.14, 0.14, 2.2)
    bpy.ops.object.transform_apply(scale=True)
    pm = bpy.data.materials.new("barrier")
    pm.use_nodes = True
    nt = pm.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2.5
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.85, 0.04, 0.03, 1)
    mix.inputs[7].default_value = (0.92, 0.92, 0.9, 1)
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mul.inputs[0])
    nt.links.new(mul.outputs[0], fr.inputs[0])
    nt.links.new(fr.outputs[0], gt.inputs[0])
    nt.links.new(gt.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.4
    pole.data.materials.append(pm)
    pole.location = (0, 0, -300)
    E.pole = pole


def _zombies(E, assets):
    from mob import build_mob, skin_path, scary_skin
    sk, gl = scary_skin(skin_path(assets), os.path.join(E.tex_dir, "zombie_scary"))
    E.Z = [build_mob(E.sc, f"zombie_{k}", sk, height=ZH, glow_png=gl, glow=8.0) for k in range(len(ZOMBIES))]
    for Z in E.Z:
        Z.root.location = (0, 0, -300)


def _finish_materials(E):
    """Matching the world (the creator, 2026-11-25): the pedestal's stone crisp (pixel sampling, a bump), the button
    matte with a fine bump (not plastic), the Noob matte like Steve (no glossy patches), the dragon darker and scalier."""
    def bump(m, strength, src=None):
        nt = m.node_tree
        bs = nt.nodes.get("Principled BSDF")
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = strength
        if src is None:
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 60.0
            src = nz.outputs["Fac"]
        nt.links.new(src, bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    for m in E.pillar.data.materials:
        for nd in m.node_tree.nodes:
            if nd.type == "TEX_IMAGE":
                nd.interpolation = "Closest"
                bump(m, 0.2, nd.outputs["Color"])
                break
        bs = m.node_tree.nodes.get("Principled BSDF")
        if bs:
            bs.inputs["Roughness"].default_value = 0.85
    m = E.button.data.materials[0]
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.5
    if "Specular IOR Level" in bs.inputs:
        bs.inputs["Specular IOR Level"].default_value = 0.25
    bump(m, 0.15)
    seen = set()
    for ob in E.N.root.children_recursive:
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
    dm = bpy.data.materials.get("dragon_skin")
    if dm:
        for nd in dm.node_tree.nodes:
            if nd.type == "MIX" and nd.blend_type == "SCREEN":
                nd.inputs[0].default_value = 0.05            # its own dark charcoal scales
        bs = dm.node_tree.nodes["Principled BSDF"]
        bs.inputs["Roughness"].default_value = 0.55


def _ripple(E):
    """A bright violet ring spreading on the portal's surface where the dragon's snout goes in."""
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.06, major_segments=48, minor_segments=8)
    ob = bpy.context.active_object
    ob.name = "portal_ripple"
    m = bpy.data.materials.new("portal_ripple")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.85, 0.45, 1.0, 1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ob.location = (0, 0, -300)
    E.ripple, E.ripple_em = ob, em


def _dragon(E, assets):
    from dragon import build_dragon
    E.D = build_dragon(E.sc, assets, scale=DRAGON_SCALE)
    E.D.root.location = (0, 0, -400)


def _burst(E):
    """The Noob bursting: his own parts fly; a small dark cube hangs a moment in the middle (Null's cell)."""
    N = E.N
    E.burst_parts = {"torso": N.torso, "neck": N.neck, "arm_sl": N.arms["sl"], "arm_sr": N.arms["sr"],
                     "leg_sl": N.legs["sl"], "leg_sr": N.legs["sr"]}
    E.burst_home = {k: (Vector(o.location), o.rotation_mode, tuple(o.rotation_quaternion)) for k, o in E.burst_parts.items()}
    rnd = random.Random(3)
    # world velocities (m/s): away from the portal, the way the cube was going, and away from the oak (its trunk
    # is at the Noob's back right): nothing flies into the tree
    d = (NOOB_BTN - PORTAL)
    a0 = math.atan2(d.y, d.x)
    E.burst_v = {}
    for k_, name in enumerate(E.burst_parts):
        a = a0 + math.radians(rnd.uniform(-50, 12))
        sp = rnd.uniform(2.2, 3.4)
        E.burst_v[name] = Vector((math.cos(a) * sp, math.sin(a) * sp, rnd.uniform(1.6, 2.8)))
    E.burst_v["neck"] = Vector((math.cos(a0) * 1.6, math.sin(a0) * 1.6, 3.2))
    dm = bpy.data.materials.new("dark_cell")
    dm.use_nodes = True
    bs = dm.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.01, 0.005, 0.015, 1)
    bs.inputs["Roughness"].default_value = 0.3
    bs.inputs["Emission Color"].default_value = (0.6, 0.0, 0.5, 1)
    bs.inputs["Emission Strength"].default_value = 0.35
    bs.inputs["Emission Strength"].default_value = 1.4
    E.dark_cube = _cube(E, "dark_cell", 0.22, dm)


# ------------------------------------------------------------------ the shots
SHOTS = [("eye", "eye"), ("lookup", "look_up"), ("rule", "steve_rule"), ("build", "steve_plan"),
         ("this", "noob_this"), ("dont", "steve_dont"), ("press", "press"), ("open", "portal_open"),
         ("hand", "pour_hand"),                    # close on the swirl: a hand, a head, red eyes
         ("rise", "pour_out"),                     # low: it steps out, towering
         ("cheer", ("pour_out", 1.3)),             # the Noob cheering, two more stepping out behind him
         ("lock", "lunge"),                        # close: the eager one turns its head to Steve, its eyes flare
         ("lunge", ("lunge", 0.6)),                # side on, low: the lunge, Steve recoiling
         ("fear", "steve_back"),                   # over its shoulder: Steve backing off, terrified
         ("hit_see", "hit_see"),                   # the cube leaving the portal at the Noob, who doesn't see it
         ("hit_slow", "hit_slow"),                 # slow motion, close on the Noob: the cube coming
         ("hit", "hit"),                           # the impact; his parts fly clear of the tree
         ("respawn", "respawn"), ("chaos", "chaos"),
         ("cause", "notice"),                      # the button flashes, the portal pulses, one more stumbles out
         ("realize", ("notice", 1.0)),             # Steve's face, lit red by the next flash: he gets it
         ("planb", ("notice", 1.9)), ("dash", "dash"),
         ("windup", "windup"), ("swing", "swing"), ("shatter", ("smash", -0.08)),
         ("suck", "suck"), ("cling", ("suck", 1.8)), ("quiet", "quiet"), ("never", "steve_never"),
         ("shadow", "sky_roar"), ("dive", "dive"), ("catch", "catch"), ("circle", "circle"),
         ("whoa", "noob_dragon"), ("toss", ("noob_dragon", 2.45)), ("dragons_too", ("noob_dragon", 3.0)),
         ("yes", "steve_yes"), ("roar", "dragon_turn"), ("go", "steve_go"), ("run", "run"), ("jump", "jump"),
         ("dive_after", "dive_after"), ("swirl", ("dive_after", 0.8))]


def shot_bounds():
    out = []
    for name, ref in SHOTS:
        out.append((name, b(ref) if isinstance(ref, str) else b(ref[0]) + ref[1]))
    return out


def which(t):
    bs = shot_bounds()
    for k, (name, t0) in enumerate(bs):
        t1 = bs[k + 1][1] if k + 1 < len(bs) else 1e9
        if t < t1:
            return name, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


def _build_spot(E, t):
    """Where Steve stands as he builds: by the button for its stone and the button, then along the frame's foot,
    just right of the block he is placing (he walks with the work)."""
    pt = place_times()
    xs = [BUILD_AT.x, BUILD_AT.x] + [_clamp(Vector(ob["home"]).x + Vector(E.PP.root.location).x + 1.4, -5.6, BUILD_AT.x)
                                      for ob in E.portal_order]
    xs = xs[:len(pt)]
    x = float(np.interp(t, pt, xs))
    x = 0.5 * x + 0.5 * float(np.interp(t + 0.25, pt, xs))          # he moves on a little ahead of the next block
    return Vector((x, BUILD_AT.y, 0.0))


def place_times():
    return spread(b("steve_plan"), b("build") + 2.3, 26)


def z_out(k):
    """When zombie k comes through (its front at the surface)."""
    return [b("pour_hand") + 0.15, b("pour_out") + 0.2, b("pour_out") + 1.05, b("notice") + 0.3, b("notice") + 1.4][k]


def button_flashes():
    """The button is stuck: it blinks, and every blink the portal pulses and pulls something through."""
    return [z_out(k) - 0.1 for k in range(len(ZOMBIES))] + [b("hit_see") + 0.05]


def smash_at():
    return b("smash") + 0.1


def cube_hit_at():
    return b("hit") + 0.04


# ------------------------------------------------------------------ per frame
DAY = {"glow": (255, 240, 220), "power": 30.0, "horizon": (220, 232, 250), "mid": (140, 186, 250), "zenith": (52, 120, 236),
       "fill": 1.1, "fill_col": (186, 206, 240)}
DUSK = {"glow": (236, 190, 230), "power": 8.0, "horizon": (200, 150, 200), "mid": (110, 90, 170), "zenith": (44, 34, 96),
        "fill": 0.8, "fill_col": (176, 150, 220)}


def light(E, t):
    from world import set_sky
    snap = b("eye") + 2.1
    dk = 1.0 - ss(snap, b("steve_rule"), t)                      # chapter 1's dusk lifts as the crack shuts
    look = M.mix_look(DAY, DUSK, dk)
    set_sky(E.W, look)
    if not hasattr(E, "sun0"):
        E.sun0 = E.W.sun.data.energy
        E.key0 = (E.key.data.energy, tuple(E.key.data.color))
    # the dragon's shadow passing over them dims the sun a moment (it is between them and the sun)
    sh = math.exp(-((t - (b("sky_roar") + 0.55)) / 0.16) ** 2)
    E.W.sun.data.energy = E.sun0 * (1 - 0.6 * dk) * (1 - 0.25 * sh)
    _shadow_caster(E, t)
    E.sc.view_settings.exposure = -0.05 - 0.3 * dk
    E.key.data.energy = E.key0[0] * (1 - 0.35 * dk) * (1 - 0.3 * sh)
    E.key.data.color = tuple(lerp(c0, c1, dk) for c0, c1 in zip(E.key0[1], (0.72, 0.74, 1.0)))
    for nm, e0 in (("cloud", 0.85), ("cloud_under", 0.6)):
        mt = bpy.data.materials.get(nm)
        if mt is None:
            continue
        bs = mt.node_tree.nodes.get("Principled BSDF")
        if nm not in E.mats_sky:
            E.mats_sky[nm] = tuple(bs.inputs["Base Color"].default_value)[:3]
        col = tuple(lerp(c0, c1, dk) for c0, c1 in zip(E.mats_sky[nm], (0.42, 0.34, 0.72)))
        bs.inputs["Base Color"].default_value = (*col, 1)
        bs.inputs["Emission Color"].default_value = (*col, 1)
        bs.inputs["Emission Strength"].default_value = e0 * (1 - 0.45 * dk)
    E.crack_light.data.energy = 1.0 * (1 - ss(snap, snap + 0.25, t))
    E.crack.hide_render = t > snap + 0.9
    if not E.crack.hide_render:
        to_cam = (E.cam.location - E.crack_at)
        to_cam.z *= 0.3
        E.crack.location = E.crack_at
        E.crack.rotation_mode = "QUATERNION"
        E.crack.rotation_quaternion = to_cam.to_track_quat("Z", "Y") @ Quaternion((0, 0, 1), math.radians(-14))
        u = ss(snap - 0.05, snap + 0.12, t)
        fade = 1 - ss(snap + 0.15, snap + 0.9, t)
        E.crack.scale = (52.0 * (1 - 0.35 * u) * max(0.02, fade ** 0.3), 52.0 * 640 / 2048 * max(0.015, 1 - u), 1)
        E.crack.data.materials[0] = E.crack_mats["eye" if t < snap else "crack"]
    E1.eye_look(E, t + 3.2, (not E.crack.hide_render) and t < snap, 0.0)


def _pulse(t, times, w=0.12):
    return sum(math.exp(-((t - x) / w) ** 2) for x in times)


def portal(E, t):
    pt = place_times()
    P = E.PP
    for k, ob in enumerate(E.portal_order):
        h = Vector(ob["home"])
        if t < pt[k + 2]:
            ob.location = h + Vector((0, 0, -200))
            ob.scale = (1, 1, 1)
            continue
        u = ss(pt[k + 2], pt[k + 2] + 0.12, t)
        ob.location = h + Vector((0, 0, 0.12 * (1 - u)))
        s = 0.7 + 0.3 * u + 0.06 * math.sin(math.pi * u)
        ob.scale = (s, s, s)
    # the membrane: off until the press; the flash, the swirl; a pulse on every blink of the button; white and
    # pulling in the suck; it stays open after (calmer), flaring as they jump through and as the dragon dives in
    on = b("portal_open")
    vis = on <= t
    P.membrane.hide_render = not vis
    pulses = _pulse(t, [x + 0.1 for x in button_flashes()], 0.14)
    flash = math.exp(-((t - on - 0.08) / 0.12) ** 2) + 0.8 * math.exp(-((t - b("suck") - 0.05) / 0.15) ** 2) \
        + 0.0
    E.portal_flash.hide_render = flash < 0.02
    E.portal_flash_em.inputs["Strength"].default_value = 14.0 * min(1.0, flash)
    swirl = ss(on, on + 0.3, t)
    calm = ss(b("suck") + 1.6, b("suck", 1), t)
    E.portal_power.inputs[2].default_value = (0.42 + 0.6 * math.exp(-((t - on - 0.3) / 0.4) ** 2) + 1.4 * pulses) * swirl * (1 - 0.35 * calm) \
        + 1.5 * ss(b("suck"), b("suck") + 0.2, t) * (1 - ss(b("suck") + 1.2, b("suck") + 1.8, t)) \
        + 0.6 * _pulse(t, [b("jump") + 0.35, b("jump") + 0.5], 0.1) + 1.2 * ss(b("dive_after", 1) - 0.35, b("dive_after", 1), t)
    E.portal_flow.inputs[1].default_value = (0.13 * t, 0.37 * t * (1 + 2 * (1 - calm)) * (1 + 3 * ss(b("suck"), b("suck") + 0.3, t) * (1 - calm)), 0)
    E.portal_dim.inputs[7].default_value = (1, 1, 1, 1)
    see = 0.55 * ss(b("pour_hand") - 0.1, b("pour_hand") + 0.4, t) * (1 - ss(b("pour_out") + 1.8, b("pour_out") + 2.3, t)) \
        + 0.45 * ss(z_out(3) - 0.7, z_out(3) - 0.4, t) * (1 - ss(z_out(4) + 0.6, z_out(4) + 1.0, t))
    E.portal_see.outputs[0].default_value = see
    P.light.data.energy = 600 * swirl * (1 + 1.2 * pulses) * (1 if vis else 0) + 3000 * min(1.0, flash)
    E.portal_room.hide_render = see < 0.01
    E.portal_room_light.data.energy = 140.0 * min(1.0, see * 2)
    # the button, its stone, and the smash
    pt_pillar, pt_button = pt[0], pt[1]
    pg = gp(E, PILLAR + Vector((0.5, 0.5, 0)))
    if t < pt_pillar:
        E.pillar.location = (0, 0, -300)
    else:
        u = ss(pt_pillar, pt_pillar + 0.12, t)
        E.pillar.location = pg + Vector((0, 0, 0.5 + 0.12 * (1 - u)))
    top = pg + Vector((0, 0, 1.0))
    sm = smash_at()
    press = ss(b("press") - 0.03, b("press") + 0.03, t) * (1 - ss(b("press") + 0.3, b("press") + 0.45, t))
    bsb = E.button.data.materials[0].node_tree.nodes["Principled BSDF"]
    blink = _pulse(t, button_flashes(), 0.08) * (1 if t < sm else 0)
    bsb.inputs["Emission Strength"].default_value = 0.25 + 4.0 * math.exp(-((t - b("press") - 0.05) / 0.12) ** 2) + 18.0 * blink
    E.button_light.data.energy = 220.0 * blink
    E.button_light.location = top + Vector((0, 0, 0.35))
    if t < pt_button or t >= sm:
        E.button.location = (0, 0, -300)
    else:
        u = ss(pt_button, pt_button + 0.12, t)
        E.button.location = top + Vector((0, 0, 0.08 - 0.1 * press + 0.1 * (1 - u)))
    for ob, v, w, s in E.button_shards:
        if t < sm:
            ob.location = (0, 0, -300)
            continue
        dt = t - sm
        dt = 0.45 * dt if dt < 0.6 else 0.27 + (dt - 0.6)                # the shatter in slow motion, then real time
        p = top + Vector((0, 0, 0.1)) + v * dt + Vector((0, 0, -4.9 * dt * dt))
        p.z = max(p.z, E.ground(p.x, p.y) + s / 2)
        ob.location = p
        ob.rotation_euler = tuple(w * min(dt, 0.8))
    for k, ob in enumerate(E.puffs):
        ob.location = (0, 0, -300)
    alive_ = [(k, x) for k, x in enumerate(pt) if 0 <= t - x < 0.35]
    for slot, (k, x) in enumerate(alive_[:4]):
        dt = t - x
        if k >= 2:
            h = E.portal_order[k - 2].matrix_world.translation
        elif k == 0:
            h = pg + Vector((0, 0, 0.5))
        else:
            h = top
        for j in range(2):
            ob = E.puffs[(slot * 2 + j) % len(E.puffs)]
            a = 2.4 * j + k
            ob.location = h + Vector((math.cos(a) * (0.45 + 0.8 * dt), -0.55 - 0.3 * dt, -0.35 + 0.9 * dt))
            s = 1.2 * (1 - dt / 0.35) + 0.2
            ob.scale = (s, s, s)


def pad(E, t):
    a = b("portal_open") + 0.7
    s0 = a - 0.38
    if s0 <= t < a + 0.02:
        u = (t - s0) / 0.38
        m_ = portal_mouth(E)
        E.spark.location = m_.lerp(E.pad_at, u) + Vector((0, 0, 2.2 * math.sin(math.pi * u)))
        E.spark.rotation_euler = (u * 9, u * 6, 0)
    else:
        E.spark.location = (0, 0, -300)
    bk = ss(a - 0.02, a + 0.05, t) * (1 - ss(a + 0.15, a + 0.6, t))
    if bk > 0.01:
        E.beam.location = E.pad_at + Vector((0, 0, 1.6))
        E.beam.scale = (0.3 + 0.2 * ss(a, a + 0.3, t), 0.3 + 0.2 * ss(a, a + 0.3, t), 2.2)
        E.beam_mix.inputs[0].default_value = 0.12 * bk          # a soft glow, not a solid white cylinder
        E.beam_em.inputs["Strength"].default_value = 3.0
    else:
        E.beam.location = (0, 0, -300)
    if t < a:
        E.pad.location = (0, 0, -300)
        E.pad_light.data.energy = 0
        return
    u = ss(a, a + 0.25, t)
    E.pad.location = E.pad_at
    s = 0.2 + 0.8 * u + 0.12 * math.sin(math.pi * u)
    E.pad.scale = (s, s, 1)
    glow = 1.0 + 3.0 * math.exp(-((t - b("respawn") - 0.05) / 0.25) ** 2)
    E.pad_glow.inputs["Emission Strength"].default_value = 4.0 * glow
    E.pad_light.data.energy = 30 * glow * u


def ripple(E, t):
    """The ring spreading where the dragon's snout goes into the swirl."""
    r0 = b("dive_after") + 0.85
    if r0 <= t:
        u_ = min(1.0, (t - r0) / 0.6)
        hd = dragon_head(E) if E.D.root.location.z > -100 else gp(E, PORTAL) + Vector((0, 0, 4))
        E.ripple.location = Vector((hd.x, PORTAL.y - 0.42, hd.z))
        E.ripple.rotation_euler = (math.radians(90), 0, 0)
        E.ripple.scale = (0.4 + 2.4 * u_,) * 3
        E.ripple_em.inputs["Strength"].default_value = 18.0 * (1 - u_) ** 1.5
    else:
        E.ripple.location = (0, 0, -300)


def portal_mouth(E):
    return gp(E, PORTAL) + Vector((0, -0.4, PH / 2))


def junk(E, t):
    mouth = portal_mouth(E)
    g = 9.81
    sk0, sk1 = b("suck") + 0.4, b("suck") + 2.0
    for k, c in enumerate(E.cubes):
        ob = c["ob"]
        if True:                                     # gone (the creator, 2026-11-25: unclear props)
            ob.location = (0, 0, -300)
            continue
        if t < c["t0"]:
            ob.location = (0, 0, -300)
            continue
        p0 = mouth + Vector((c["sx"] * 0.6, 0, (c["sz"] - 3.5) * 0.4))
        land = gp(E, c["land"]) + Vector((0, 0, c["s"] / 2))
        T = c["T"]
        v = (land - p0) / T + Vector((0, 0, 0.5 * g * T))
        dt = t - c["t0"]
        if dt < T:
            p = p0 + v * dt + Vector((0, 0, -0.5 * g * dt * dt))
            rot = c["spin"] * dt
        else:
            u = dt - T
            hop = max(0.0, 1.6 * u - 0.5 * g * u * u)
            p = land + Vector((0, 0, hop))
            rot = c["spin"] * T
        ts = lerp(sk0, sk1, k / len(E.cubes))
        if t >= ts:
            u = min(1.0, (t - ts) / 0.55)
            p = p.lerp(mouth + Vector((0, 0.6, 0)), u ** 2.2)
            rot = rot + c["spin"] * 2 * u
            s = max(0.0, 1 - ss(0.75, 1.0, u))
            ob.scale = (s, s, s)
        else:
            ob.scale = (1, 1, 1)
        ob.location = p
        ob.rotation_euler = tuple(rot)
    pole = E.pole
    t0 = b("pour_out") + 1.9
    if True:
        pole.location = (0, 0, -300)
        return
    if t < t0:
        pole.location = (0, 0, -300)
    else:
        land = gp(E, Vector((-1.8, -2.4, 0))) + Vector((0, 0, 0.08))
        T = 0.9
        dt = t - t0
        if dt < T:
            v = (land - mouth) / T + Vector((0, 0, 0.5 * g * T))
            p = mouth + v * dt + Vector((0, 0, -0.5 * g * dt * dt))
            rot = (math.radians(90) + 7.0 * dt, 0.0, 0.6 + 2.0 * dt)
        else:
            roll = min(0.6, dt - T)
            p = land + Vector((0.5 * roll - 0.4 * roll * roll, 0, 0))
            rot = (math.radians(90), 2.2 * roll, 0.6 + 2.0 * T)
        ts = b("suck") + 0.3
        if t >= ts:
            u = min(1.0, (t - ts) / 0.6)
            p = p.lerp(mouth + Vector((0, 0.6, 0)), u ** 2)
            rot = (rot[0] + 8 * u, rot[1], rot[2] + 5 * u)
            s = max(0.0, 1 - ss(0.75, 1.0, u))
            pole.scale = (s, s, s)
        else:
            pole.scale = (1, 1, 1)
        pole.location = p
        pole.rotation_euler = rot


def _yaw(d):
    return math.degrees(math.atan2(d.x, -d.y))


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _clamp(x, a, b_):
    return max(a, min(b_, x))


# ------------------------------------------------------------------ Steve's path (for whoever looks at him)
def lunge_dir():
    d = STEVE_DONT - ZOMBIES[1][1]
    return Vector((d.x, d.y, 0)).normalized()


def lunge_end():
    return STEVE_DONT - lunge_dir() * 1.8


def steve_spot(E, t):
    if t < b("lunge") + 0.65:
        return gp(E, STEVE_DONT)
    if t < b("chaos"):
        # he throws himself back as it leaps (most of the way at once), then keeps backing off, slowly
        u = 0.7 * ss(b("lunge") + 0.65, b("lunge") + 1.15, t) + 0.3 * ss(b("lunge") + 1.6, b("steve_back", 1), t)
        return gp(E, STEVE_DONT.lerp(STEVE_BACKED, u))
    if t < b("dash"):
        return gp(E, STEVE_BACKED.lerp(STEVE_DODGE, ss(b("chaos"), b("chaos") + 1.8, t)))
    if t < b("smash") + 0.6:
        return gp(E, STEVE_DODGE.lerp(STEVE_SMASH, ss(b("dash"), b("dash", 1), t)))
    if t < b("run"):
        return gp(E, STEVE_SMASH.lerp(STEVE_TIRED, ss(b("quiet") - 0.1, b("quiet") + 0.9, t)))
    return Vector(E.S.holder.location)


# ------------------------------------------------------------------ the zombies
def _personas():
    from mob import Persona
    return [Persona(1.3, speed=0.85, limp=0.6, tilt=8, reach=84, droop=0.35),     # the slow one, dragging a leg
            Persona(4.1, speed=1.15, limp=0.0, tilt=-5, reach=94, droop=0.0),     # the eager one (goes for Steve)
            Persona(7.7, speed=0.8, limp=0.3, tilt=13, reach=78, droop=0.7),      # head lolling, one arm low
            Persona(2.6, speed=0.95, limp=0.4, tilt=-10, reach=88, droop=0.2),
            Persona(5.9, speed=1.0, limp=0.2, tilt=6, reach=90, droop=0.4)]


STRIDE = 1.7 * ZH / 2.0                     # one cycle covers what the legs reach (feet planted, no sliding)
HUNCH = 16                                   # the movie's zombies stoop: hunched, heads thrust forward


def zombie_state(E, k, t):
    """Where zombie k is and what it is doing: p, yaw, phase (None standing), arms_up, lean, look, lunge, lift
    (the suck), flail, glow, and 'cling' (the last one, held on the frame)."""
    per = _personas()[k]
    x_out, after, chaos_to = ZOMBIES[k]
    t0 = z_out(k)
    slow = 2.6 if k == 0 else 1.0                 # the first creeps through: the hand, then the head
    if t < t0 - 0.6:
        return None
    door = gp(E, Vector((x_out, PORTAL.y + (2.0 if k == 0 else 1.3), 0)))
    front = gp(E, Vector((x_out, PORTAL.y - 0.8, 0)))
    a = gp(E, after)
    steve_p = steve_spot(E, t)
    v = 0.95 * per.speed
    st = {"arms_up": 1.0, "lean": HUNCH, "lunge": 0.0, "lift": 0.0, "flail": 0.0, "look": steve_p + Vector((0, 0, 1.6)),
          "glow": 3.0 + 0.8 * math.sin(t * 3.1 + k)}
    # 1. through the surface: slow, its arms out ahead of it
    t_front = t0 + slow
    if t < t_front:
        u = _clamp((t - t0 + 0.6) / (t_front - t0 + 0.6), 0.0, 1.0)
        u = u ** 1.7 if k == 0 else ss(0.0, 1.0, u)
        st["p"] = door.lerp(front, u)
        st["phase"] = max(0.0, t - t0) * 0.55 * v / STRIDE
        st["yaw"] = _yaw(front - door)
        st["look"] = st["p"] + Vector((0, -3.0, 1.2))
        if k == 0:                                  # the head comes up as it comes through; its eyes find us
            st["glow"] = 4.0 + 3.0 * ss(t0 + 1.4, t0 + 1.8, t)        # its eyes first, glowing in the swirl
        return st
    # 2. out: to its place
    d1 = (a - front).length
    t_arr = t_front + d1 / v
    sk = b("suck") + 0.45 + 0.35 * min(k, 3)
    if k == 1 and t >= b("lunge") + 0.6 and t < b("chaos"):
        return _lunge_state(E, st, a, t)
    if t < t_arr:
        u = (t - t_front) / (t_arr - t_front)
        st["p"] = front.lerp(a, u)
        st["phase"] = (t - t0) * v / STRIDE
        st["yaw"] = _yaw(a - front)
        return st
    if k == 1 and b("lunge") <= t < b("lunge") + 0.6:
        # the lock: its head turns to Steve, then its shoulders; its eyes flare
        st["p"] = a
        st["phase"] = None
        y_path, y_st = _yaw(a - front), _yaw(steve_p - a)
        st["yaw"] = y_path + _wrap(y_st - y_path) * ss(b("lunge") + 0.1, b("lunge") + 0.55, t)
        st["glow"] = 3.5 + 7.0 * ss(b("lunge") + 0.2, b("lunge") + 0.4, t)
        st["lean"] = HUNCH + 4 * ss(b("lunge") + 0.3, b("lunge") + 0.6, t)
        return st
    # 3. arrived
    if k == 1 and t >= b("chaos"):
        a = gp(E, lunge_end())
    if chaos_to is None:
        if k == 4 and t >= b("suck") + 0.2:
            return _cling_state(E, st, a, t)
        if t >= sk - 0.5:
            return _suck_state(E, st, a, t, sk)
        st["p"] = a
        st["phase"] = None
        y_path, y_st = _yaw(a - front), _yaw(steve_p - a)
        st["yaw"] = y_path + _wrap(y_st - y_path) * ss(t_arr, t_arr + 0.9, t)
        return st
    c0 = b("chaos") + 0.25 * k
    if t < c0:
        st["p"] = a
        st["phase"] = None
        y_path, y_st = _yaw(a - front), _yaw(steve_p - a)
        st["yaw"] = y_path + _wrap(y_st - y_path) * ss(t_arr, t_arr + 0.9, t)
        return st
    c = gp(E, chaos_to)
    d2 = (c - a).length
    t2 = c0 + d2 / v
    if t < sk - 0.5:
        if t < t2:
            st["p"] = a.lerp(c, (t - c0) / (t2 - c0))
            st["phase"] = (d1 + (t - c0) * v) / STRIDE
            st["yaw"] = _yaw(c - a)
        else:
            st["p"] = c
            st["phase"] = None
            st["yaw"] = _yaw(c - a) + _wrap(_yaw(steve_p - c) - _yaw(c - a)) * ss(t2, t2 + 0.7, t)
        if k == 1:
            l0 = b("chaos") + 1.3
            wind = math.exp(-((t - l0) / 0.12) ** 2)
            st["lean"] -= 8 * wind
            st["lunge"] = ss(l0 + 0.08, l0 + 0.28, t) * (1 - ss(l0 + 0.55, l0 + 1.0, t))
        return st
    p_stop = c if t >= t2 else a.lerp(c, min(1.0, (sk - 0.5 - c0) / max(1e-3, t2 - c0)))
    return _suck_state(E, st, p_stop, t, sk)


def _lunge_state(E, st, a, t):
    """The eager one goes for Steve: two lurching steps, the leap with its arms up and out, the miss (he has
    backed off), the stumble, the recovery where he was."""
    l0 = b("lunge") + 0.6
    leap = l0 + 0.5
    land = leap + 0.32
    e = gp(E, lunge_end())
    mid = a.lerp(e, 0.45)
    if t < leap:
        u = ss(l0, leap, t)
        st["p"] = a.lerp(mid, u)
        st["phase"] = (t - l0) * 2.4
        st["lean"] = HUNCH + 6 - 10 * math.exp(-((t - leap + 0.06) / 0.08) ** 2)      # it gathers itself
    elif t < land:
        u = (t - leap) / (land - leap)
        st["p"] = mid.lerp(e, u) + Vector((0, 0, 0.45 * math.sin(math.pi * u)))
        st["phase"] = None
        st["lunge"] = 1.0
        st["lean"] = HUNCH + 22
    else:
        st["p"] = e
        st["phase"] = (t - land) * 1.2 if t < land + 0.5 else None
        st["lunge"] = 1.0 - ss(land, land + 0.7, t)
        st["lean"] = HUNCH + 22 * (1 - ss(land, land + 0.6, t)) + 6 * math.exp(-((t - land - 0.1) / 0.1) ** 2)
    st["yaw"] = _yaw(e - a) + _wrap(_yaw(steve_spot(E, t) - st["p"]) - _yaw(e - a)) * ss(land + 0.2, land + 1.0, t)
    st["glow"] = 9.0
    return st


def _suck_state(E, st, p_stop, t, sk):
    away = p_stop - gp(E, PORTAL)
    away = Vector((away.x, away.y, 0)).normalized()
    drag = ss(sk - 0.5, sk, t)
    st["p"] = p_stop - away * 0.5 * drag ** 2
    st["phase"] = (t - sk) * 2.2 if t < sk else None
    turn = ss(sk - 0.5, sk - 0.15, t)                       # it turns to fight the pull (not a snap)
    y0 = st.get("yaw", _yaw(steve_spot(E, t) - p_stop))
    st["yaw"] = y0 + _wrap(_yaw(away) - y0) * turn
    st["lean"] = 16 * drag
    st["flail"] = ss(sk - 0.4, sk, t)
    st["lift"] = ss(sk, sk + 0.9, t) if t >= sk else 0.0
    st["arms_up"] = 1.0
    return st


def cling_grip(E):
    """Where the last zombie's hands hold: the front edge of the frame's bottom row, right of the middle."""
    g = gp(E, Vector((-2.6, PORTAL.y - 0.5, 0)))
    return g + Vector((0, -0.02, 1.0))


def _cling_state(E, st, p0, t):
    """The last one: dragged back over the grass, digging in; torn off its feet, it catches the frame's bottom row
    with both hands and hangs on, its legs pulled into the swirl, its head up and its eyes on us."""
    s0 = b("suck") + 0.2
    if t < b("catch") + 0.1:
        if t < s0 + 1.0:
            drag = ss(s0, s0 + 1.0, t)
            st["p"] = p0.lerp(gp(E, Vector((p0.x, PORTAL.y - 1.0, 0))), drag ** 1.6)
            st["phase"] = (t - s0) * 2.6
            st["yaw"] = _yaw(Vector((0, -1, 0)))
            st["lean"] = 18
            st["flail"] = 0.5
            return st
        st["cling"] = ss(s0 + 1.0, s0 + 1.35, t)
        st["glow"] = 5.0 + 2 * math.sin(t * 9)
        st["p"] = p0
        st["phase"] = None
        st["yaw"] = 0.0
        return st
    st["held"] = True                              # in the dragon's jaws
    st["glow"] = 5.0
    return st


def zombies(E, t):
    from mob import pose_mob, zombie_pose
    pers = _personas()
    mouth = portal_mouth(E)
    for k, Z in enumerate(E.Z):
        st = zombie_state(E, k, t)
        if st is None:
            Z.root.location = (0, 0, -300)
            if Z.eye_light:
                Z.eye_light.data.energy = 0.0
            continue
        Z.glow.outputs[0].default_value = st["glow"]
        if Z.eye_light:
            Z.eye_light.data.energy = 0.5 * st["glow"] / 3.0
        if st.get("held"):
            _held_zombie(E, Z, pers[k], t)
            continue
        if st.get("cling", 0) > 0:
            _cling_pose(E, Z, pers[k], t, st)
            continue
        p, yaw = st["p"], st["yaw"]
        lk = st["look"] - (p + Vector((0, 0, 1.6)))
        look = max(-55.0, min(55.0, _wrap(_yaw(lk) - yaw)))
        pz, bob = zombie_pose(pers[k], t, st["phase"], st["arms_up"], st["lean"], look, st["lunge"], st["flail"])
        pz["root_yaw"] = yaw
        pz["head_nod"] = pz.get("head_nod", 0) - 0.8 * st["lean"]          # hunched, but its face up: it looks at you
        s = 1.0
        if st["lift"] > 0:
            u = st["lift"]
            p = p.lerp(mouth + Vector((0, 0.6, -1.0)), u ** 1.8) + Vector((0, 0, 1.3 * math.sin(math.pi * min(1.0, u * 1.15)) * (1 - u)))
            pz["root_yaw"] = yaw + 400 * u ** 1.6
            pz["root_pitch"] = -30 - 140 * u ** 1.4
            s = max(0.0, 1 - ss(0.82, 1.0, u))
        pose_mob(Z, pz)
        Z.root.location = p + Vector((0, 0, bob))
        Z.root.scale = (s * ZH / 2.0,) * 3


def _cling_pose(E, Z, per, t, st):
    """Lying across the opening, its hands on the frame, legs in the swirl, kicking; head up, growling."""
    from mob import pose_mob
    g = cling_grip(E)
    u = st["cling"]
    pz = {"root_yaw": 0.0, "root_pitch": 84 * u + 18 * (1 - u), "root_roll": 4 * math.sin(t * 7),
          "chest_lean": -8, "head_nod": -62 + 8 * math.sin(t * 5.3), "head_turn": 12 * math.sin(t * 2.1),
          "head_tilt": per.tilt,
          "arm_r": {"fwd": 72 + 6 * math.sin(t * 11), "out": 8}, "arm_l": {"fwd": 72 + 6 * math.sin(t * 9 + 1), "out": 8},
          "leg_r": {"fwd": 30 * math.sin(t * 12), "out": 6}, "leg_l": {"fwd": -30 * math.sin(t * 12 + 0.7), "out": 6}}
    pose_mob(Z, pz)
    Z.root.scale = (ZH / 2.0,) * 3
    Z.root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    # place it so its hands are on the grip, its body trailing back into the portal
    hr = Z.boxes["arm_r"].matrix_world @ Vector((0, 0, -6 * (1.0 / 16.0)))
    hl = Z.boxes["arm_l"].matrix_world @ Vector((0, 0, -6 * (1.0 / 16.0)))
    hc = (hr + hl) / 2
    Z.root.location = g - hc + Vector((0, 0, 0.04 * math.sin(t * 13)))
    E.cling_root = Vector(Z.root.location)


def _cling_root_at_grab(E, Z, per):
    """Where the clinging one's root was the moment before the jaws closed (computed once, from time alone)."""
    if getattr(E, "cling_root_grab", None) is None:
        tg = b("catch") + 0.09
        _cling_pose(E, Z, per, tg, {"cling": 1.0})
        E.cling_root_grab = Vector(Z.root.location)
    return E.cling_root_grab


def _toss_from(E, toss, t):
    """Where the jaws were when it let go (the dragon posed at that moment once, then put back)."""
    if getattr(E, "toss_tip", None) is None:
        dragon(E, toss)
        bpy.context.view_layer.update()
        E.toss_tip = E.D.head.matrix_world @ Vector((0, -1.25, -0.1))
        dragon(E, t)
        bpy.context.view_layer.update()
    return E.toss_tip


def _held_zombie(E, Z, per, t):
    """In the dragon's jaws: hanging by its middle from the jaw, flailing; flung away as the Noob speaks."""
    from mob import pose_mob
    g_grab = _cling_root_at_grab(E, Z, per)          # first: it poses the zombie itself
    D = E.D
    toss = b("noob_dragon") + 2.6
    tip = (D.head.matrix_world @ Vector((0, -1.25, -0.1)))                 # between the jaws, near the front
    fl = 1.0
    pz = {"root_yaw": math.degrees(D.root.rotation_euler.z), "root_pitch": 12, "root_roll": 10 * math.sin(t * 6),
          "chest_lean": 25, "head_nod": -30 + 20 * math.sin(t * 8), "head_turn": 25 * math.sin(t * 5),
          "arm_r": {"fwd": 120 + 50 * fl * math.sin(t * 13), "out": 40}, "arm_l": {"fwd": 120 + 50 * math.sin(t * 11 + 1), "out": 40},
          "leg_r": {"fwd": 40 * math.sin(t * 12), "out": 12}, "leg_l": {"fwd": -40 * math.sin(t * 12 + 0.7), "out": 12}}
    pose_mob(Z, pz)
    Z.root.scale = (ZH / 2.0,) * 3
    Z.root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    mid = Z.pivots["body"].matrix_world.translation
    held = tip - mid
    # the grab: from where it clung into the jaws in a quarter second
    g0 = g_grab
    k = ss(b("catch") + 0.1, b("catch") + 0.3, t)
    loc = held if g0 is None else g0.lerp(held, k)
    if t >= toss:
        dt = t - toss
        if dt > 2.2:
            Z.root.location = (0, 0, -300)
            return
        if not hasattr(E, "toss_v"):
            E.toss_v = {}
        key = round(toss, 3)
        # its path from the moment it is let go (worked out from the dragon's motion, so any frame can compute it)
        h0 = _dragon_pos(E, toss)
        v = (_dragon_pos(E, toss + 0.05) - h0) / 0.05 + Vector((0, 0, 7.0))
        side = Vector((-v.y, v.x, 0)).normalized() * 6.0
        tip0 = tip if dt == 0 else None
        base = _toss_from(E, toss, t)
        p = base + (v * 0.6 + side) * dt + Vector((0, 0, -4.9 * dt * dt)) - mid
        Z.root.location = p
        Z.root.rotation_euler = (dt * 9, dt * 4, math.radians(pz["root_yaw"]) + dt * 6)
        return
    Z.root.location = loc


# ------------------------------------------------------------------ the dragon
def _dragon_keys():
    """(time, position) for its flight: the pass over them (its shadow), up and round into the sky, the dive at the
    portal, the snatch at the frame, up over the portal, a wide circle round the meadow to the far side, the turn
    to them (hovering), and the dive after them into the portal."""
    T = b
    return [
        (T("sky_roar") - 0.6, Vector((20, -22, 10))),
        (T("sky_roar") + 0.55, Vector((-0.4, -1.2, 9.0))),      # right over them: its shadow crosses them
        (T("sky_roar") + 1.6, Vector((-22, 12, 30))),
        (T("dive"), Vector((-20, 24, 40))),
        (T("dive") + 0.7, Vector((-11, 12, 22))),
        (T("dive") + 1.35, Vector((-4.4, -2.4, 7.5))),
        (T("catch"), Vector((-2.6, -1.4, 5.0))),
        (T("catch") + 0.1, Vector((-2.6, 0.5, 4.3))),         # the clamp: straight in, its neck reaching down to the frame
        (T("catch") + 0.65, Vector((-2.6, 0.4, 4.5))),        # held: it worries it on the frame
        (T("catch") + 1.0, Vector((-2.6, -0.6, 5.8))),        # the yank: torn off the frame
        (T("catch") + 1.4, Vector((-3.1, -1.1, 10.5))),       # straight up in front of the portal, clear of its top
        (T("catch", 1), Vector((-8.5, 3.5, 16.0))),
        (T("circle") + 0.9, Vector((-12, 3, 17))),
        (T("circle") + 1.8, Vector((-13, -10, 16))),
        (T("noob_dragon"), Vector((4, -17, 15))),
        (T("noob_dragon") + 1.6, Vector((3, -19, 14))),
        (T("noob_dragon") + 2.6, Vector((10, -15, 13))),       # the toss
        (T("noob_dragon") + 4.0, Vector((14, -8, 12))),
        (T("steve_yes"), Vector((12, -3.5, 11))),
        (T("steve_yes", 1), Vector((9.5, -6.5, 8.5))),
        (T("dragon_turn") + 0.3, Vector((8.5, -8.0, 7.2))),    # hovering, turned to them, the roar
        (T("steve_go") + 0.6, Vector((8.4, -8.2, 7.6))),
        (T("run"), Vector((7.0, -7.4, 8.8))),
        (T("run") + 0.8, Vector((2.0, -6.0, 8.5))),
        (T("jump") + 0.2, Vector((-1.2, -4.2, 7.5))),
        (T("dive_after"), Vector((-2.9, -2.4, 5.6))),
        (T("dive_after") + 0.8, Vector((-3.5, 0.4, 5.2))),
        (T("dive_after", 1), Vector((-3.8, 1.9, 5.0))),
        (T("dive_after", 1) + 1.0, Vector((-3.8, 4.5, 4.8))),
    ]


def _cr(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


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


def _sky_look(E, p, t):
    """Where they look up to: the sound in the sky first, then the dragon itself, blended (no snap)."""
    ph = p + Vector((-1.5, 5, 10)).lerp(Vector((-2, 2, 11)), ss(b("sky_roar") + 0.3, b("sky_roar") + 1.0, t))
    if E.D.root.location.z < -100:
        return ph                                    # they follow the roar and the shadow across the sky
    dh = dragon_head(E)
    hd = Vector(((dh - p).x, (dh - p).y, 0)).length
    if t < b("dive"):
        # as it goes right over them they follow where it is going (heads tilt back and turn), never a flip
        ahead = _dragon_pos(E, t + 0.7) + Vector((0, 0, 0.5))
        dh = ahead.lerp(dh, ss(3.0, 8.0, hd))
    return ph.lerp(dh, ss(b("sky_roar") + 0.05, b("sky_roar") + 0.6, t))


def _shadow_caster(E, t):
    """The dragon's shadow sweeping over the meadow as it passes over them: a dark shape seen by nothing but the
    sun, carried across the ground along its flight, high between them and the sun."""
    if not hasattr(E, "shade"):
        bpy.ops.mesh.primitive_plane_add(size=1)
        ob = bpy.context.active_object
        ob.name = "dragon_shadow"
        ob.scale = (7.0, 12.0, 1)
        for k in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
            if hasattr(ob, k):
                setattr(ob, k, False)
        E.shade = ob
    ob = E.shade
    a, c = b("sky_roar") + 0.1, b("sky_roar") + 1.0
    if not (a <= t <= c):
        ob.location = (0, 0, -400)
        return
    to_sun = (E.W.sun.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    mid = (gp(E, STEVE_TIRED) + gp(E, NOOB_NEAR)) / 2
    fl = Vector((-0.7, 0.7, 0)).normalized()
    u = (t - a) / (c - a)
    ob.location = mid + to_sun * (8.0 / max(0.3, to_sun.z)) + fl * lerp(-14, 14, u)
    ob.rotation_euler = (0, 0, math.atan2(fl.y, fl.x) - math.pi / 2)


def dragon_head(E):
    return E.D.head.matrix_world.translation


def chars_mid(E):
    return (Vector(E.S.holder.location) + Vector(E.N.root.location)) / 2 + Vector((0, 0, 1.4))


def dragon(E, t):
    from dragon import pose_dragon
    D = E.D
    if t < b("dive") or t > b("dive_after", 1) + 0.1:      # unseen until it comes down out of the sky (no pop-in)
        D.root.location = (0, 0, -400)
        bpy.context.view_layer.update()
        return
    p = _dragon_pos(E, t)
    v = (_dragon_pos(E, t + 0.04) - _dragon_pos(E, t - 0.04)) / 0.08
    hv = Vector((v.x, v.y, 0))
    to0 = chars_mid(E) - p
    yaw = _yaw(hv) if hv.length > 0.5 else _yaw(Vector((to0.x, to0.y, 0)))
    # hovering and turned to them (the roar): it faces them whatever way it drifts
    face_them = ss(b("steve_yes", 1) - 0.4, b("dragon_turn") + 0.3, t) * (1 - ss(b("steve_go") + 0.8, b("run") + 0.2, t))
    to = chars_mid(E) - p
    yaw = yaw + _wrap(_yaw(Vector((to.x, to.y, 0))) - yaw) * face_them
    E._dyaw = yaw
    yaw_rate = _wrap(_yaw(Vector(((_dragon_pos(E, t + 0.1) - p).x, (_dragon_pos(E, t + 0.1) - p).y, 0))) - _yaw(hv)) / 0.1 if hv.length > 0.5 else 0.0
    pitch = _clamp(math.degrees(math.atan2(-v.z, max(0.5, hv.length))), -38, 38) * (1 - face_them)
    bank = _clamp(-yaw_rate * 0.25, -40, 40) * (1 - face_them)
    # the snatch: it comes straight in heading north and holds that heading (no flip), level, wings shallow
    face_n = ss(b("catch") - 0.7, b("catch") - 0.4, t) * (1 - ss(b("catch") + 1.2, b("catch") + 1.6, t))
    yaw = yaw + _wrap(180.0 - yaw) * face_n
    pitch *= 1 - face_n
    bank *= 1 - face_n
    yaw_rate *= 1 - face_n
    # wings: a glide in the dive (spread, still), big beats pulling up out of the snatch and hovering
    dive_glide = ss(b("dive") + 0.2, b("dive") + 0.5, t) * (1 - ss(b("dive") + 1.2, b("dive") + 1.5, t))
    after_glide = ss(b("dive_after") + 0.2, b("dive_after") + 0.6, t)
    glide = max(dive_glide, after_glide, 0.35 * ss(b("sky_roar") - 0.6, b("sky_roar"), t) * (1 - ss(b("sky_roar") + 1.0, b("sky_roar") + 1.4, t)))
    rate = 1.1 + 0.6 * (ss(b("catch") + 0.05, b("catch") + 0.2, t) * (1 - ss(b("circle"), b("circle") + 0.8, t))) \
        + 0.5 * face_them
    flap = 1.1 * t + 0.6 * max(0.0, min(t, b("circle") + 0.8) - (b("catch") + 0.1)) + 0.5 * max(0.0, t - b("steve_yes", 1)) * (t < b("run") + 0.5)
    # the jaw: roars (the dive, the turn, the dive after), the snatch, chewing on the zombie (held)
    jaw = 0.9 * ss(b("dive") + 0.5, b("dive") + 0.7, t) * (1 - ss(b("dive") + 1.4, b("dive") + 1.6, t)) \
        + 0.9 * ss(b("catch") - 0.35, b("catch") - 0.1, t) * (1 - ss(b("catch") + 0.05, b("catch") + 0.12, t)) \
        + 1.0 * ss(b("dragon_turn") + 0.05, b("dragon_turn") + 0.25, t) * (1 - ss(b("dragon_turn", 1) - 0.1, b("dragon_turn", 1) + 0.15, t)) \
        + 0.8 * ss(b("dive_after") - 0.1, b("dive_after") + 0.15, t) * (1 - ss(b("dive_after") + 0.9, b("dive_after") + 1.1, t)) \
        + 0.15 * ss(b("catch") + 0.12, b("catch") + 0.2, t) * (1 - ss(b("noob_dragon") + 2.5, b("noob_dragon") + 2.6, t))
    # the head: down at the frame for the snatch; on them from the circle on
    to_h = Vector((to.x, to.y, 0))
    rel = _wrap(_yaw(to_h) - yaw) if to_h.length > 0.1 else 0.0
    watch = ss(b("circle"), b("circle") + 0.8, t) * (1 - ss(b("run") + 0.5, b("jump"), t))
    neck_yaw = _clamp(rel, -70, 70) * watch * 0.7
    head_yaw = _clamp(rel, -70, 70) * watch * 0.3
    el = math.degrees(math.atan2(-to.z, max(1.0, to_h.length)))
    snatch = ss(b("catch") - 0.4, b("catch") + 0.02, t) * (1 - ss(b("catch") + 0.7, b("catch") + 1.0, t))
    neck_pitch = 65 * snatch + _clamp(el - pitch, -30, 40) * watch * 0.6 - 10 * ss(b("dragon_turn") + 0.05, b("dragon_turn") + 0.3, t) * (1 - ss(b("dragon_turn", 1), b("dragon_turn", 1) + 0.3, t))
    head_pitch = 30 * snatch + _clamp(el - pitch, -30, 40) * watch * 0.4
    legs = 1.0 - 0.6 * face_them
    heave = pose_dragon(D, t, flap=flap, amp=(1.0 + 0.3 * face_them) * (1 - 0.7 * snatch), glide=glide, neck_pitch=neck_pitch, neck_yaw=neck_yaw,
                        head_pitch=head_pitch, head_yaw=head_yaw, jaw=min(1.0, jaw), legs=legs, turn=yaw_rate)
    fold = max(0.95 * ss(b("catch") - 0.4, b("catch"), t) * (1 - ss(b("catch") + 1.35, b("catch") + 1.75, t)),
               ss(b("jump") - 0.2, b("dive_after") + 0.4, t))
    if fold > 0:
        for side, sx in (("l", 1), ("r", -1)):
            D.wing[side].rotation_euler.z += math.radians(-sx * 70 * fold)
            D.tip[side].rotation_euler.z += math.radians(-sx * 75 * fold)
    D.root.location = p + Vector((0, 0, heave))
    D.root.rotation_euler = (math.radians(pitch), math.radians(bank), math.radians(yaw))
    # the snatch: its jaws are where the clinging one is (the body follows the head in), whatever the flight path
    w = ss(b("catch") - 0.3, b("catch") + 0.08, t) * (1 - ss(b("catch") + 0.6, b("catch") + 0.85, t))
    if w > 0:
        bpy.context.view_layer.update()
        want = cling_grip(E) + Vector((0, -0.35, 0.55))
        tip = D.head.matrix_world @ Vector((0, -1.25, -0.1))
        D.root.location = D.root.location + (want - tip) * w
    bpy.context.view_layer.update()                  # everyone who looks at it, or hangs from its jaws, sees it as it is now


# ------------------------------------------------------------------ the cast
def alive(pz, t, seed):
    """Never a statue: breathing, and a head that drifts a little, added on top of every pose."""
    def n(f, sd):
        return math.sin(t * f + sd) * 0.6 + math.sin(t * f * 2.31 + sd * 1.7) * 0.3 + math.sin(t * f * 4.07 + sd * 2.9) * 0.1
    pz = dict(pz)
    pz["chest_lean"] = pz.get("chest_lean", 0) + 1.6 * math.sin(t * 2 * math.pi / 3.1 + seed)
    pz["head_tilt"] = pz.get("head_tilt", 0) + 3.0 * n(0.6, seed + 1)
    pz["head_turn"] = pz.get("head_turn", 0) + 3.0 * n(0.5, seed + 2)
    pz["head_nod"] = pz.get("head_nod", 0) + 1.5 * n(0.7, seed + 3)
    return pz


def life(E, who, pz, face, t, seed):
    """Bodies never frozen in dialogue (the creator, 2026-11-25): a slow drift in the chest and head, a head dip
    and a shoulder lift on each stressed syllable (two frames ahead of it, easing back), and blinks."""
    pz = dict(pz)
    def n(f, sd):
        return math.sin(t * f + sd) * 0.6 + math.sin(t * f * 2.31 + sd * 1.7) * 0.3 + math.sin(t * f * 4.07 + sd * 2.9) * 0.1
    pz["chest_lean"] = pz.get("chest_lean", 0) + 1.2 * n(0.9, seed + 11)
    pz["head_nod"] = pz.get("head_nod", 0) + 1.5 * n(1.1, seed + 12)
    pz["head_tilt"] = pz.get("head_tilt", 0) + 1.5 * n(0.8, seed + 13)
    mo = E.mouth.get(who, {})
    f = int(round(t * FPS)) + 2                                  # two frames ahead of the sound
    acc = 0.0
    for k in range(0, 7):
        a_ = mo.get(f - k, {}).get("m_o", 0.0) - mo.get(f - k - 3, {}).get("m_o", 0.0)
        acc = max(acc, max(0.0, a_) * (1 - k / 7.0))
    talking = 1.0 if any(mo.get(f - k) for k in range(-3, 4)) else 0.0
    acc = min(1.0, acc * 2.2)
    pz["head_nod"] += 4.0 * acc
    pz["head_tilt"] += 2.5 * talking * math.sin(t * 2.7 + seed)
    pz["chest_lean"] += 1.5 * acc
    if who == "steve":
        for arm in ("arm_sl", "arm_sr"):
            a = dict(pz.get(arm, {}))
            a["out"] = a.get("out", 10) + 3 * acc                   # the shoulders lift with it
            pz[arm] = a
    # blinks: every few seconds, never in a scream
    per = 3.1 + 0.6 * math.sin(seed)
    ph = (t + seed * 0.37) % per
    bl = math.exp(-((ph - 0.06) / 0.045) ** 2)
    if bl > 0.05 and face.get("m_o", 0) < 0.6:
        if who == "steve":
            for k in ("both_to", "both_tm", "both_ti"):
                face[k] = lerp(face.get(k, 0.0), -1.0, bl)
        else:
            face["both_h"] = lerp(face.get("both_h", 1.6), 0.15, bl)
    return pz


def steve_place_pose(E, t, pz):
    pt = place_times()
    k = max([i for i, x in enumerate(pt) if x <= t + 0.08] or [0])
    jab = math.exp(-((t - pt[k] + 0.03) / 0.07) ** 2) if b("steve_plan") - 0.1 <= t <= pt[-1] + 0.25 else 0.0
    pz["arm_sr"] = {"fwd": 55 + 35 * jab, "out": 12, "elbow": 40 - 30 * jab}
    return k


def _walk(pz, t, t0, rate, amp=0.3, lift=0.25):
    ph = (t - t0) * rate * 2 * math.pi
    pz.update({"foot_sl": {"y": -amp * math.sin(ph), "z": max(0.0, lift * math.sin(ph + 1.2))},
               "foot_sr": {"y": amp * math.sin(ph), "z": max(0.0, lift * math.sin(ph + 1.2 + math.pi))}})
    return ph


def _head_to(yaw, p, tgt, lim=60.0):
    d = tgt - p
    return _clamp(_wrap(_yaw(d) - yaw), -lim, lim)


def _nod_to(p, tgt, h=1.6):
    d = tgt - (p + Vector((0, 0, h)))
    return -math.degrees(math.atan2(d.z, max(0.3, Vector((d.x, d.y, 0)).length)))


def run_path(E, who):
    """Their run to the portal and the leap through it: (start, the take-off spot, the far side)."""
    if who == "steve":
        a, b_ = STEVE_D, Vector((-4.2, 2.0, 0))
    else:
        a, b_ = NOOB_D, Vector((-2.1, 2.2, 0))
    return gp(E, a), gp(E, b_), gp(E, Vector((b_.x, PORTAL.y + 1.6, 0)))


def _run_jump(E, t, who, pz):
    """Running to the portal and diving through: returns (position, yaw, hidden)."""
    a, tk, far = run_path(E, who)
    lag = 0.0 if who == "steve" else 0.12
    r0, r1 = b("run") + lag, b("jump") + 0.05 + lag
    if t < r1:
        u = ss(r0, r1, t) if who else 0
        u = (t - r0) / (r1 - r0) if t > r0 else 0.0
        u = u * u * (1.6 - 0.6 * u) if u < 1 else 1.0
        p = a.lerp(tk, min(1.0, u))
        return p, _yaw(tk - a), False, max(0.0, t - r0)
    dt = t - r1
    T = 0.55
    u = min(1.0, dt / T)
    p = tk.lerp(far, u) + Vector((0, 0, 1.5 * math.sin(math.pi * u * 0.85) + 0.3 * u))
    return p, _yaw(far - tk), p.y > PORTAL.y + 0.35, None


def steve(E, t):
    from ep09_new import SF
    face = dict(SF["flat"])
    pz = {"arm_sr": {"fwd": 25, "out": 12, "elbow": 35}, "arm_sl": {"fwd": 10, "out": 8, "elbow": 20}}
    pt = place_times()
    E.S.holder.hide_render = False
    for ob in E.S.holder.children_recursive:
        ob.hide_render = False
    if t < b("steve_plan"):
        p = gp(E, STEVE0)
        c = E.crack_at - p
        yc = math.degrees(math.atan2(c.x, -c.y))
        n = gp(E, NOOB0) - p
        yn = math.degrees(math.atan2(n.x, -n.y))
        yaw = lerp(yc, yn, ss(b("look_up") + 0.1, b("look_up") + 0.6, t))
        yaw = lerp(yaw, -25.0, ss(b("steve_rule") - 0.15, b("steve_rule") + 0.3, t))
        pz["head_nod"] = -30 * (1 - ss(b("look_up") + 0.1, b("look_up") + 0.6, t))
        pz["head_turn"] = 14 * (1 - ss(b("steve_rule") - 0.25, b("steve_rule") + 0.1, t)) * ss(b("steve_rule") - 0.4, b("steve_rule") - 0.15, t)
        face = dict(SF["worried"]) if t < b("look_up") + 0.5 else dict(SF["flat"])
    elif t < b("build") + 2.4:
        u = ss(b("steve_plan"), b("steve_plan") + 1.3, t)
        p = gp(E, STEVE0.lerp(_build_spot(E, t), u))
        k = steve_place_pose(E, t, pz)
        tgt = Vector(E.portal_order[k - 2]["home"]) + Vector(E.PP.root.location) if k >= 2 else gp(E, PILLAR + Vector((0.5, 0.5, 0)))
        el = math.degrees(math.atan2(tgt.z - (p.z + 1.6), max(0.5, Vector(((tgt - p).x, (tgt - p).y, 0)).length)))
        pt_all = place_times()
        jab = math.exp(-((t - pt_all[k] + 0.03) / 0.07) ** 2) if b("steve_plan") - 0.1 <= t <= pt_all[-1] + 0.25 else 0.0
        pz["arm_sr"] = {"fwd": 55 + 0.9 * max(0.0, el) + 30 * jab, "out": 12, "elbow": 35 - 30 * jab}
        hop = jab * ss(5.0, 6.0, tgt.z - p.z)                    # the top row: a little jump to place it
        p = p + Vector((0, 0, 0.28 * hop))
        sp = (_build_spot(E, t + 0.05) - _build_spot(E, t - 0.05)).length / 0.1
        if sp > 0.4 and u >= 1:
            _walk(pz, t, b("steve_plan"), 1.7, 0.28, 0.2)
        d = tgt - p
        ty = math.degrees(math.atan2(d.x, -d.y))
        cy = math.degrees(math.atan2(BUILD_CAM.x - p.x, -(BUILD_CAM.y - p.y)))
        yaw = ty + _wrap(cy - ty) * 0.35
        pz["head_turn"] = max(-50.0, min(50.0, _wrap(ty - yaw)))
        pt_ = ss(7.7, 7.9, t) * (1 - ss(8.95, 9.2, t))
        if pt_ > 0:
            bd = gp(E, PILLAR + Vector((0.5, 0.5, 0))) - p
            by = math.degrees(math.atan2(bd.x, -bd.y))
            pz["arm_sl"] = {"fwd": 80 * pt_, "out": 10 + 0.6 * max(-60.0, min(60.0, _wrap(by - yaw))) * pt_, "elbow": 8}
            ny = math.degrees(math.atan2(gp(E, NOOB_WATCH).x - p.x, -(gp(E, NOOB_WATCH).y - p.y)))
            pz["head_turn"] = lerp(pz["head_turn"], max(-60.0, min(60.0, _wrap(ny - yaw))), pt_)
            face = dict(SF["flat"])
            face.update({"bb_tilt": 0.3, "bb_raise": -0.05})
        if 0 < u < 1:
            _walk(pz, t, b("steve_plan"), 1.6)
        if pt_ <= 0:
            pz["head_nod"] = -0.9 * _clamp(el, -10, 50)          # he looks up at the block he places
            pz["chest_lean"] = -0.25 * _clamp(el, 0, 50)
            pz["chest_side"] = 4 * math.sin((t - b("steve_plan")) * 2.4)   # his weight shifts as he works
        else:
            pz["head_nod"] = -6
    elif t < b("steve_dont"):
        u = ss(b("build") + 2.4, b("build") + 2.9, t)
        p = gp(E, _build_spot(E, b("build") + 2.4).lerp(STEVE_DONT, u))
        d = gp(E, PORTAL) - p
        yaw = math.degrees(math.atan2(d.x, -d.y))
        pz["head_nod"] = -14 * u
        face = dict(SF["smug"])
        pz["arm_sl"] = {"fwd": 5, "out": 30, "elbow": 80}
    elif t < b("portal_open"):
        p = gp(E, STEVE_DONT)
        d = gp(E, NOOB_BTN) - p
        yn = math.degrees(math.atan2(d.x, -d.y))
        dpt = gp(E, PORTAL) - p
        yaw = lerp(math.degrees(math.atan2(dpt.x, -dpt.y)), yn, ss(b("steve_dont") - 0.05, b("steve_dont") + 0.2, t))
        k = ss(b("steve_dont") - 0.02, b("steve_dont") + 0.18, t)
        pz["arm_sl"] = {"fwd": 85 * k, "out": 10, "elbow": 10}
        pz["chest_lean"] = 8 * k
        face = dict(SF["scared"])
        if t >= b("press"):
            face = dict(SF["stunned"])
    elif t < b("pour_hand"):
        # the portal opens: shock, his arms come down slowly
        p = gp(E, STEVE_DONT)
        yaw = _yaw(gp(E, PORTAL) - p)
        pz["arm_sl"] = {"fwd": 30, "out": 25, "elbow": 40}
        pz["arm_sr"] = {"fwd": 30, "out": 25, "elbow": 40}
        pz["chest_lean"] = -6
        face = dict(SF["stunned"])
    elif t < b("chaos"):
        # frozen, afraid of a false move; the hand; the lock; the lunge: he throws himself back; terrified
        p = steve_spot(E, t)
        z1 = zombie_state(E, 1, t)
        z0 = zombie_state(E, 0, t)
        watch = (z1["p"] if (z1 and t >= b("pour_out") + 0.9) else (z0["p"] if z0 else gp(E, PORTAL))) + Vector((0, 0, 1.8))
        y_watch = _yaw(watch - p)
        lunge_t = b("lunge") + 1.0
        rec = ss(lunge_t - 0.25, lunge_t + 0.05, t)                   # the recoil: arms up, leaning away
        backing = ss(b("lunge") + 0.8, b("lunge") + 1.3, t) * (1 - ss(b("lunge") + 1.4, b("lunge") + 1.6, t)) \
            + ss(b("lunge") + 1.6, b("lunge") + 1.7, t) * (1 - ss(b("steve_back", 1) - 0.2, b("steve_back", 1), t))
        yaw = y_watch
        pz["head_turn"] = 0.0
        pz["head_nod"] = _nod_to(p, watch) * 0.5
        creep = ss(b("pour_hand"), b("pour_out"), t)
        pz["arm_sl"] = {"fwd": 30 + 50 * rec, "out": 25 + 15 * rec, "elbow": 40 + 40 * rec}
        pz["arm_sr"] = {"fwd": 30 + 35 * rec, "out": 25 + 10 * rec, "elbow": 40 + 30 * rec}
        pz["chest_lean"] = -6 - 3 * creep - 14 * rec * (1 - 0.5 * ss(lunge_t + 0.8, lunge_t + 1.6, t))
        pz["chest_twist"] = -10 * rec
        if backing > 0.05:
            _walk(pz, t, b("lunge") + 0.8, 2.4 if t < b("lunge") + 1.5 else 1.2, 0.32 * backing, 0.2 * backing)
        if b("hit") <= t:
            pz["arm_sl"]["fwd"] += 40 * (1 - ss(b("hit") + 0.4, b("hit") + 0.9, t))
        face = dict(SF["scared"])
        face.update({"both_ps": 0.6})
        if t < b("pour_out"):
            face = dict(SF["stunned"])
    elif t < b("notice"):
        # the chaos: pushed back, flinging his arms, dodging
        u = ss(b("chaos"), b("chaos") + 1.8, t)
        p = gp(E, STEVE_BACKED.lerp(STEVE_DODGE, u))
        zs = zombie_state(E, 1, t)
        dz = (zs["p"] if zs else gp(E, PORTAL)) - p
        yaw = _yaw(dz)
        fl = math.sin((t - b("chaos")) * 5.0)
        pz["arm_sl"] = {"fwd": 60 + 30 * fl, "out": 40, "elbow": 30}
        pz["arm_sr"] = {"fwd": 60 - 30 * fl, "out": 40, "elbow": 30}
        pz["chest_lean"] = -8
        if 0 < u < 1:
            _walk(pz, t, b("chaos"), 2.0)
        face = dict(SF["scared"])
    elif t < b("dash"):
        # he sees it: the button blinks, the portal pulses, one more comes through. Twice. His eyes go from one to
        # the other; his face hardens. "Plan B!": the pickaxe goes up on "B"
        p = gp(E, STEVE_DODGE)
        btn = gp(E, PILLAR + Vector((0.5, 0.5, 0))) + Vector((0, 0, 1.1))
        prt = gp(E, PORTAL) + Vector((0, 0, 3.0))
        y_b, y_p = _yaw(btn - p), _yaw(prt - p)
        yaw = y_b + _wrap(y_p - y_b) * 0.5
        f1, f2 = button_flashes()[3], button_flashes()[4]
        to_p = ss(f1 + 0.15, f1 + 0.4, t) - ss(f2 - 0.3, f2 - 0.05, t) + ss(f2 + 0.15, f2 + 0.4, t) - ss(f2 + 0.6, f2 + 0.85, t)
        tgt = btn.lerp(prt, _clamp(to_p, 0, 1))
        pz["head_turn"] = _head_to(yaw, p, tgt)
        pz["head_nod"] = _nod_to(p, tgt) * 0.6
        face = dict(SF["scared"]) if t < f2 + 0.6 else dict(SF["flat"])
        if t >= f2 + 0.6:
            hard = ss(f2 + 0.6, f2 + 1.0, t)
            face.update({"bb_tilt": 0.55 * hard, "bb_raise": -0.15 * hard, "both_to": -0.15, "both_tm": -0.15, "m_arch": 0.1})
            yaw = lerp(yaw, _yaw(btn - p) - 30, ss(f2 + 0.6, f2 + 1.1, t))
            pz["head_turn"] = lerp(pz["head_turn"], 0.0, ss(f2 + 0.6, f2 + 1.1, t))
        k = ss(b("steve_planb") + 0.45, b("steve_planb") + 0.75, t)
        pz["arm_sr"] = {"fwd": lerp(30, 85, k), "out": lerp(15, 20, k), "elbow": lerp(40, 0, k)}
        pz["arm_sl"] = {"fwd": 20, "out": 15, "elbow": 60}
    elif t < b("smash") + 0.6:
        # the dash; the wind-up (the pickaxe high, leaning back); the swing in slow motion; the hit
        u = ss(b("dash"), b("dash", 1), t)
        p = gp(E, STEVE_DODGE.lerp(STEVE_SMASH, u))
        d = gp(E, STEVE_SMASH) - gp(E, STEVE_DODGE)
        yaw = lerp(_yaw(d), 90.0, ss(b("dash", 1) - 0.3, b("dash", 1), t))
        H = smash_at()
        if t < b("dash", 1) - 0.1:
            ph = _walk(pz, t, b("dash"), 2.6, 0.45, 0.3)
            pz["chest_lean"] = 14
            pz["arm_sl"] = {"fwd": -40 * math.sin(ph), "out": 10, "elbow": 60}
            pz["arm_sr"] = {"fwd": 85, "out": 18, "elbow": 10}
        else:
            up = ss(b("windup") - 0.05, b("windup", 1) - 0.05, t)
            coil = ss(b("swing"), H - 0.15, t)                   # slow motion: coiling further back, the tension
            down = ss(H - 0.125, H, t)                           # the snap: three frames
            rec = ss(H + 0.09, H + 0.5, t)                       # after the hit-stop
            pz["arm_sr"] = {"fwd": lerp(lerp(85, 190, up) + 14 * coil, 72, down) + 10 * rec, "out": 8,
                            "elbow": lerp(lerp(0, 30, up), 0, down)}
            pz["arm_sl"] = {"fwd": lerp(20, 45, down), "out": 15, "elbow": 40}
            pz["chest_lean"] = lerp(lerp(-4, -16, up) - 4 * coil, 22, down) - 8 * rec
            pz["chest_twist"] = lerp(-22 * up - 6 * coil, 8, down) * (1 - rec)
            pz["head_nod"] = 12 * down * (1 - rec)
            pz["foot_sl"] = {"y": -0.18 * up * (1 - down), "z": 0.12 * up * (1 - down)}
        face = dict(SF["flat"])
        face.update({"bb_tilt": 0.6, "bb_raise": -0.18, "both_to": -0.1, "both_tm": -0.1, "m_arch": 0.15})
    elif t < b("sky_roar"):
        # the suck, the quiet: he staggers back, straightens, breathes out; "...Never again."
        st_ = ss(b("quiet") - 0.1, b("quiet") + 0.9, t)
        p = gp(E, STEVE_SMASH.lerp(STEVE_TIRED, st_))
        if 0 < st_ < 1:
            _walk(pz, t, b("quiet") - 0.1, 1.4, 0.22, 0.16)
        yp = _yaw(gp(E, PORTAL) - p)
        yaw = lerp(90.0, yp + 25, ss(b("suck") + 0.1, b("suck") + 0.8, t))
        yaw = lerp(yaw, 10.0, ss(b("quiet") + 0.2, b("quiet") + 1.0, t))
        breath = math.sin(max(0.0, t - b("quiet")) * 2 * math.pi / 2.2)
        pz["chest_lean"] = 6 + 3 * breath
        pz["arm_sr"] = {"fwd": 8, "out": 10, "elbow": 10}
        pz["arm_sl"] = {"fwd": 5, "out": 8, "elbow": 10}
        pz["head_nod"] = 8 * ss(b("quiet"), b("quiet") + 0.8, t)
        face = dict(SF["flat"])
        face.update({"both_to": -0.5, "both_tm": -0.55, "both_ti": -0.45})
        if b("steve_never", 1) + 0.15 <= t:
            k = ss(b("steve_never", 1) + 0.15, b("steve_never", 1) + 0.55, t)
            pz["head_turn"] = 18 * k
            pz["head_nod"] = 8 - 14 * k
            face = dict(SF["flat"])
        if b("suck") <= t < b("quiet"):
            face = dict(SF["stunned"])
    elif t < b("run"):
        # the dragon: the shadow, the dive, the snatch, the circle; the Noob's question; "Yes."; the roar;
        # "Into the portal. Now!"
        bk = ss(b("dive") + 0.1, b("catch") - 0.1, t)
        p = gp(E, STEVE_TIRED.lerp(STEVE_D, bk))
        if 0.02 < bk < 0.98:
            _walk(pz, t, b("dive"), 1.8, 0.25, 0.15)
        dh = _sky_look(E, p, t)
        y_d = _yaw(dh - p)
        # his body turns to it (head first, then shoulders and hips: the head leads by a few frames)
        yaw = _yaw(Vector((-0.6, 1.0, 0))) + _wrap(y_d - _yaw(Vector((-0.6, 1.0, 0)))) * (0.55 + 0.4 * ss(b("circle"), b("circle") + 1.2, t))
        pz["head_turn"] = _head_to(yaw, p, dh, 65)
        pz["head_nod"] = _nod_to(p, dh) * 0.7
        face = dict(SF["stunned"])
        if t >= b("dive") + 0.6:
            face = dict(SF["scared"])
        if b("circle") + 1.0 <= t < b("dragon_turn"):
            face = dict(SF["flat"])                              # deadpan, watching it
        if b("noob_dragon") + 3.2 <= t < b("dragon_turn"):       # "...dragons too?": he looks at the Noob; "Yes."
            n_ = Vector(E.N.root.location) + Vector((0, 0, 1.3))
            k = ss(b("noob_dragon") + 3.2, b("noob_dragon") + 3.7, t)
            pz["head_turn"] = lerp(pz["head_turn"], _head_to(yaw, p, n_, 25), k)
            pz["head_nod"] = lerp(pz["head_nod"], 4.0, k)
            face = dict(SF["flat"])
            face.update({"both_to": -0.45, "both_tm": -0.5, "both_ti": -0.4})
        if t >= b("dragon_turn"):
            face = dict(SF["scared"])
            pz["chest_lean"] = -8 * ss(b("dragon_turn") + 0.1, b("dragon_turn") + 0.3, t)
        if t >= b("steve_go") - 0.1:
            # urgent: he turns to the Noob (head, then body), his left arm flung out at the portal beside them
            # three-quarter to us (away from the portal, toward the Noob), his left arm flung back at the portal
            k = ss(b("steve_go") - 0.1, b("steve_go") + 0.3, t)
            n_ = Vector(E.N.root.location) + Vector((0, 0, 1.3))
            away = p - gp(E, PORTAL)
            y_go = _yaw(Vector((away.x, away.y, 0))) + 0.35 * _wrap(_yaw(n_ - p) - _yaw(Vector((away.x, away.y, 0))))
            yaw = yaw + _wrap(y_go - yaw) * ss(b("steve_go") - 0.05, b("steve_go") + 0.4, t)
            pz["head_turn"] = lerp(pz["head_turn"], _head_to(yaw, p, n_, 30), k)
            pz["head_nod"] = lerp(pz["head_nod"], 2.0, k)
            pz["head_tilt"] = 0.0
            pz["arm_sl"] = {"fwd": -40 * k, "out": 78 * k, "elbow": 5}
            face = dict(SF["scared"])
            face.update({"bb_tilt": 0.45, "bb_raise": -0.05, "m_o": 0.3})
        pz["arm_sr"] = {"fwd": 6, "out": 5, "elbow": 10}
    else:
        p, yaw, hidden, rt = _run_jump(E, t, "steve", pz)
        if hidden:
            E.S.holder.location = (0, 0, -300)
            return
        if rt is not None:
            ph = _walk(pz, t, b("run") - 0.1, 2.7, 0.5, 0.32)
            pz["chest_lean"] = 18
            pz["arm_sl"] = {"fwd": -45 * math.sin(ph), "out": 12, "elbow": 70}
            pz["arm_sr"] = {"fwd": 45 * math.sin(ph) + 20, "out": 15, "elbow": 70}
        else:
            pz["chest_lean"] = 35
            pz["arm_sl"] = {"fwd": 160, "out": 10, "elbow": 5}
            pz["arm_sr"] = {"fwd": 160, "out": 10, "elbow": 5}
            pz["foot_sl"] = {"y": 0.3, "z": 0.2}
            pz["foot_sr"] = {"y": 0.45, "z": 0.3}
        face = dict(SF["scared"])
    M.set_steve(E, p, yaw, life(E, "steve", alive(pz, t, 21), face, t, 21), face, t)


def noob(E, t):
    from ep09_new import NF
    _burst_reset(E)
    face = dict(NF["happy"])
    pz = {"arm_sl": {"out": 8}, "arm_sr": {"out": 8}}
    if t < b("steve_plan"):
        p = gp(E, NOOB0)
        c = E.crack_at - p
        yc = math.degrees(math.atan2(c.x, -c.y))
        s_ = gp(E, STEVE0) - p
        ys = math.degrees(math.atan2(s_.x, -s_.y))
        yaw = lerp(yc - 40, ys, ss(b("look_up") + 0.2, b("look_up") + 0.7, t))
        pz["head_nod"] = -26 * (1 - ss(b("look_up") + 0.2, b("look_up") + 0.7, t))
        w = ss(b("steve_rule") + 0.4, b("steve_rule", 1) + 0.4, t)
        if w > 0:
            p = gp(E, NOOB0.lerp(NOOB_WATCH, w))
            dd = NOOB_WATCH - NOOB0
            yaw = lerp(math.degrees(math.atan2(dd.x, -dd.y)), -25.0, ss(b("steve_rule", 1), b("steve_rule", 1) + 0.5, t))
        face = dict(NF["worried"]) if t < b("look_up") + 0.6 else dict(NF["neutral"])
    elif t < b("noob_this"):
        w0, w1 = b("build") + 0.6, b("build") + 2.6
        u = ss(w0, w1, t)
        p = gp(E, NOOB_WATCH.lerp(NOOB_BTN, u))
        d = gp(E, PORTAL) - p
        yaw = math.degrees(math.atan2(d.x, -d.y))
        if t >= w0:
            dd = NOOB_BTN - NOOB_WATCH
            yaw = lerp(math.degrees(math.atan2(dd.x, -dd.y)), -90.0, ss(w1 - 0.4, w1, t))
            if t < w1:
                ph = (t - w0) * 1.25 * 2 * math.pi
                sw = math.sin(ph)
                pz.update({"arm_sl": {"fwd": -24 * sw}, "arm_sr": {"fwd": 24 * sw}, "leg_sl": {"fwd": 26 * sw},
                           "leg_sr": {"fwd": -26 * sw}})
                p += Vector((0, 0, 0.03 * abs(sw)))
        pz["head_nod"] = -10
        face = dict(NF["awe"]) if t < w0 else dict(NF["happy"])
        look_btn = ss(7.9, 8.2, t) * (1 - ss(w0 - 0.2, w0, t))
        if look_btn > 0:
            bd = gp(E, PILLAR + Vector((0.5, 0.5, 0))) - p
            pz["head_turn"] = max(-60.0, min(60.0, _wrap(math.degrees(math.atan2(bd.x, -bd.y)) - yaw))) * look_btn
            pz["head_nod"] = -10 + 12 * look_btn
            face = dict(NF["happy"])
            face.update({"both_h": 1.5 + 0.3 * look_btn, "both_bm": 0.35})
    elif t < b("portal_open"):
        p = gp(E, NOOB_BTN)
        yaw = -90.0 + 25 * (1 - ss(b("steve_dont"), b("steve_dont") + 0.2, t))
        hover = ss(b("noob_this"), b("noob_this") + 0.3, t)
        up = ss(b("press") - 0.3, b("press") - 0.08, t)
        down = ss(b("press") - 0.06, b("press") + 0.02, t)
        bounce = math.exp(-((t - b("press") - 0.12) / 0.06) ** 2)
        pz["arm_sr"] = {"fwd": 75 * hover + 28 * up * (1 - down) - 14 * down + 6 * bounce, "out": -4}
        pz["chest_lean"] = 8 * down * (1 - ss(b("press") + 0.2, b("press") + 0.45, t))
        pz["head_turn"] = 28 * (1 - ss(b("steve_dont"), b("steve_dont") + 0.25, t))
        face = dict(NF["happy"])
        face.update({"both_h": 1.6})
    elif t < b("hit"):
        # the portal opens: he cheers; each zombie that steps out gets a delighted point and a hop; then the cube
        # he never sees (slow motion: his head comes round too late, his eyes going wide)
        p = gp(E, NOOB_BTN)
        d = gp(E, PORTAL) - p
        yp = _yaw(d)
        cy = _yaw(Vector((1.6, -8.6, 0)) - p)
        yaw = lerp(-90.0, yp + _wrap(cy - yp) * 0.45, ss(b("portal_open"), b("portal_open") + 0.4, t))
        k = ss(b("portal_open") + 0.25, b("portal_open") + 0.5, t)
        bounce = abs(math.sin((t - b("portal_open")) * 7.0)) * (1 - ss(b("portal_open") + 1.2, b("portal_open") + 1.6, t))
        pz = {"arm_sl": {"out": 40 + 120 * k, "fwd": 10}, "arm_sr": {"out": 40 + 120 * k, "fwd": 10}, "chest_lean": -6 * k}
        p = p + Vector((0, 0, 0.1 * bounce * k))
        face = dict(NF["happy"])
        if t >= b("pour_hand"):
            zs = [zombie_state(E, i, t) for i in range(3)]
            near = [z_ for z_ in zs if z_ is not None]
            hop = sum(math.exp(-((t - (z_out(i) + 0.9)) / 0.12) ** 2) for i in range(3))
            slow = ss(b("hit_slow"), b("hit_slow", 1), t)
            spd = 1.0 - 0.8 * ss(b("hit_slow"), b("hit_slow") + 0.1, t)            # slow motion
            tt = t if t < b("hit_slow") else b("hit_slow") + (t - b("hit_slow")) * 0.2
            pz = {"arm_sl": {"out": 60 + 25 * math.sin(tt * 5.0), "fwd": 25}, "arm_sr": {"out": 40, "fwd": 70 + 20 * hop},
                  "head_nod": -4, "chest_lean": -4 * hop}
            if near:
                zd = near[-1]["p"] - p
                pz["head_turn"] = _clamp(_wrap(_yaw(zd) - yaw), -60, 60)
            if t >= b("hit_slow"):
                cube = E.hit_cube.matrix_world.translation
                pz["head_turn"] = lerp(pz.get("head_turn", 0), _head_to(yaw, p, cube, 75), ss(b("hit_slow") + 0.4, b("hit_slow", 1), t) * 0.8)
            p = p + Vector((0, 0, 0.12 * hop))
            face = dict(NF["happy"])
            face.update({"both_h": 1.8, "m_o": 0.5, "both_bm": 0.3})
            if t >= b("hit_slow") + 0.5:
                sh = ss(b("hit_slow") + 0.5, b("hit_slow", 1), t)
                face = dict(NF["shock"]) if sh > 0.5 else dict(NF["awe"])
            _ = spd, slow
    elif t < b("respawn"):
        p = gp(E, NOOB_BTN)
        yaw = _yaw(gp(E, PORTAL) - p)
        face = dict(NF["shock"])
        pz = {"arm_sl": {"out": 70, "fwd": 20}, "arm_sr": {"out": 70, "fwd": 20}}
        M.set_noob(E, p, yaw, life(E, "noob", alive(pz, t, 7), face, t, 7), face, t)
        _burst_apply(E, 0.6 * (t - cube_hit_at()))
        return
    elif t < b("quiet") + 0.3:
        # the respawn on the pad: pops up, cheers; watches the chaos from there; ducks in the suck
        p = E.pad_at.copy()
        dt = t - b("respawn")
        pop = ss(0.0, 0.15, dt)
        s = 0.4 + 0.6 * pop + 0.12 * math.sin(math.pi * min(1.0, dt / 0.25))
        d = gp(E, PORTAL) - p
        yaw = lerp(-15.0, _yaw(d), ss(b("noob_fine", 1), b("noob_fine", 1) + 0.6, t))
        k = ss(b("noob_fine"), b("noob_fine") + 0.3, t) * (1 - ss(b("noob_fine", 1) + 0.2, b("noob_fine", 1) + 0.7, t))
        pz = {"arm_sl": {"out": 12 + 148 * k, "fwd": 14}, "arm_sr": {"out": 20 + 140 * k, "fwd": -4}, "chest_lean": -5 * k,
              "chest_side": 4, "head_turn": 18 * math.sin((dt - 0.3) * 14) * ss(0.3, 0.4, dt) * (1 - ss(0.7, 1.1, dt))}
        face = dict(NF["happy"])
        face.update({"both_ps": 1.1})
        if t >= b("noob_fine", 1) + 0.5:
            cy = _yaw(Vector((1.6, -8.6, 0)) - p)
            yaw = lerp(yaw, yaw + _wrap(cy - yaw) * 0.5, ss(b("noob_fine", 1), b("noob_fine", 1) + 0.6, t))
            zs = [zombie_state(E, i, t) for i in range(len(ZOMBIES))]
            near = [z_ for z_ in zs if z_ is not None and "p" in z_]
            hd = 0.0
            if near:
                zn = min(near, key=lambda z_: (z_["p"] - p).length)
                hd = _clamp(_wrap(_yaw(zn["p"] - p) - yaw), -65, 65)
            cheer = max(0.0, math.sin((t - b("chaos")) * 2.6)) * ss(b("chaos"), b("chaos") + 0.3, t) * (1 - ss(b("notice"), b("notice") + 0.3, t))
            flinch = math.exp(-((t - (b("chaos") + 1.45)) / 0.15) ** 2)
            duck = ss(b("suck") + 0.1, b("suck") + 0.5, t) * (1 - ss(b("suck", 1) - 0.4, b("suck", 1) + 0.3, t))
            pull = ss(b("suck"), b("suck") + 0.2, t) * (1 - duck)
            sway = math.sin(t * 1.7)
            pz = {"arm_sl": {"out": 12 + 4 * sway + 110 * cheer + 40 * pull * math.sin(t * 13), "fwd": 14 + 150 * duck},
                  "arm_sr": {"out": 20 - 4 * sway + 105 * cheer - 20 * flinch + 40 * pull * math.sin(t * 11 + 1), "fwd": -4 + 40 * flinch + 150 * duck},
                  "chest_side": 3 * sway,
                  "chest_lean": -6 * cheer + 10 * flinch + 25 * duck - 10 * pull, "head_turn": hd * (1 - duck),
                  "head_nod": 20 * duck}
            face = dict(NF["happy"]) if cheer > 0.3 else dict(NF["awe"])
            if flinch > 0.3:
                face = dict(NF["shock"])
            if duck > 0.2:
                face = dict(NF["scared"])
            if t >= b("suck", 1):
                face = dict(NF["neutral"])
        M.set_noob(E, p, yaw, life(E, "noob", alive(pz, t, 7), face, t, 7), face, t)
        sc = E.noob_scale0 * s
        uq = (dt - 0.12) / 0.33
        sq = 1 + 0.12 * math.cos(math.pi * 2.0 * uq) * (1 - uq) if 0 <= uq <= 1 else 1.0   # 1.12, 0.92, 1.0
        E.N.root.scale = (sc / math.sqrt(sq), sc / math.sqrt(sq), sc * sq)
        return
    elif t < b("sky_roar"):
        # he trots over to Steve, a little dazed
        u = ss(b("quiet") + 0.3, b("steve_never", 1) + 0.2, t)
        p = E.pad_at.lerp(gp(E, NOOB_NEAR), u)
        p.z = E.ground(p.x, p.y)
        d = gp(E, NOOB_NEAR) - E.pad_at
        s_ = gp(E, STEVE_TIRED) - p
        yaw = lerp(_yaw(d), _yaw(s_), ss(b("steve_never", 1) - 0.2, b("steve_never", 1) + 0.4, t))
        if 0 < u < 1:
            ph = (t - b("quiet") - 0.3) * 1.5 * 2 * math.pi
            sw = math.sin(ph)
            pz.update({"arm_sl": {"fwd": -22 * sw}, "arm_sr": {"fwd": 22 * sw}, "leg_sl": {"fwd": 24 * sw},
                       "leg_sr": {"fwd": -24 * sw}})
            p += Vector((0, 0, 0.03 * abs(sw)))
        face = dict(NF["neutral"])
    elif t < b("run") + 0.02:
        # the dragon: he looks up at the shadow; awe; delight; "Whoa! Is that a dragon? Does your world have dragons
        # too?" (pointing up at it, then turning to Steve); the roar: scared
        bk = ss(b("dive") + 0.2, b("catch"), t)
        p = gp(E, NOOB_NEAR.lerp(NOOB_D, bk))
        if 0.02 < bk < 0.98:
            sw_ = math.sin((t - b("dive")) * 1.9 * 2 * math.pi)
            pz.update({"leg_sl": {"fwd": 22 * sw_}, "leg_sr": {"fwd": -22 * sw_}})
        dh = _sky_look(E, p, t)
        st_ = Vector(E.S.holder.location) + Vector((0, 0, 1.6))
        yaw = _yaw(dh - p) * 1.0
        yaw = _yaw(Vector((-0.6, 1.0, 0))) + _wrap(_yaw(dh - p) - _yaw(Vector((-0.6, 1.0, 0)))) * (0.6 + 0.35 * ss(b("circle"), b("circle") + 1.2, t))
        pz["head_turn"] = _head_to(yaw, p, dh, 70)
        pz["head_nod"] = _nod_to(p, dh, 1.2) * 0.8
        face = dict(NF["confused"]) if t < b("dive") + 0.4 else dict(NF["awe"])
        if b("catch") + 0.3 <= t < b("dragon_turn"):
            face = dict(NF["happy"])
            face.update({"both_h": 1.9, "m_o": 0.4})
        point = ss(b("noob_dragon") + 0.3, b("noob_dragon") + 0.6, t) * (1 - ss(b("noob_dragon") + 2.8, b("noob_dragon") + 3.2, t))
        if point > 0:
            pz["arm_sr"] = {"out": 20 + 60 * point, "fwd": 10 + 120 * point}
            pz["chest_lean"] = -5 * point
            pz["root_pitch"] = 0
        hop = math.exp(-((t - (b("noob_dragon") + 0.6)) / 0.1) ** 2)
        p = p + Vector((0, 0, 0.12 * hop))
        to_s = ss(b("noob_dragon", 1) - 0.5, b("noob_dragon", 1), t) * (1 - ss(b("dragon_turn") - 0.1, b("dragon_turn") + 0.15, t))
        if to_s > 0:
            g_ = to_s * (1 - ss(b("noob_dragon", 1) - 0.3, b("noob_dragon", 1) + 0.2, t))
            pz["arm_sl"] = {"out": 25 + 15 * g_, "fwd": 20 + 55 * g_ + 15 * g_ * math.sin((t - b("noob_dragon")) * 5.0)}
            pz["arm_sr"] = {"out": 8, "fwd": 10}
            yaw = yaw + _wrap(_yaw(st_ - p) - yaw) * 0.12 * to_s       # his body stays to the dragon; his head turns
            pz["head_turn"] = lerp(pz["head_turn"], _head_to(yaw, p, st_, 25), to_s)
            pz["head_nod"] = lerp(pz["head_nod"], 0.0, to_s)
            pz["arm_sl"] = {"out": 10 + 20 * to_s, "fwd": 20 * to_s}
        if t >= b("dragon_turn"):
            face = dict(NF["scared"])
            pz["chest_lean"] = 12 * ss(b("dragon_turn") + 0.05, b("dragon_turn") + 0.25, t)
            pz["arm_sl"] = {"out": 20, "fwd": 70}
            pz["arm_sr"] = {"out": 20, "fwd": 70}
        if t >= b("steve_go") + 0.3:
            k = ss(b("steve_go") + 0.3, b("steve_go") + 0.7, t)
            pz["head_turn"] = lerp(pz["head_turn"], _head_to(yaw, p, st_, 70), k)
            face = dict(NF["scared"])
    else:
        p, yaw, hidden, rt = _run_jump(E, t, "noob", pz)
        if hidden:
            E.N.root.location = (0, 0, -300)
            return
        if rt is not None:
            ph = (t - b("run")) * 2.9 * 2 * math.pi
            sw = math.sin(ph)
            pz.update({"arm_sl": {"fwd": -50 * sw, "out": 15}, "arm_sr": {"fwd": 50 * sw, "out": 15}, "leg_sl": {"fwd": 40 * sw},
                       "leg_sr": {"fwd": -40 * sw}, "chest_lean": 12})
            p = p + Vector((0, 0, 0.06 * abs(sw)))
        else:
            pz.update({"arm_sl": {"fwd": 170, "out": 10}, "arm_sr": {"fwd": 170, "out": 10}, "chest_lean": 30,
                       "leg_sl": {"fwd": -30}, "leg_sr": {"fwd": -20}})
        face = dict(NF["scared"])
    M.set_noob(E, p, yaw, life(E, "noob", alive(pz, t, 7), face, t, 7), face, t)


def _burst_reset(E):
    if not hasattr(E, "noob_scale0"):
        E.noob_scale0 = E.N.root.scale[0]
    E.N.root.scale = (E.noob_scale0,) * 3
    for k, o in E.burst_parts.items():
        loc, mode, q = E.burst_home[k]
        o.location = loc
        o.rotation_quaternion = Quaternion(q)
    E.dark_cube.location = (0, 0, -300)
    E.N.root.hide_render = False
    for ob in E.N.root.children_recursive:
        ob.hide_render = False


def _burst_apply(E, dt):
    """His parts fly (world velocities, so they go where they are aimed: away from the oak), spinning; a puff of
    nothing: they are gone before they land (the respawn)."""
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
    hide = dt > 0.55
    for ob in E.N.root.children_recursive:
        ob.hide_render = hide
    c = Vector(E.N.root.location) + Vector((0, 0, 1.2))
    if dt < 0.75:
        toward = Vector((0.76, -0.64, 0)) * 0.35 * ss(0.0, 0.2, dt)
        E.dark_cube.location = c + toward + Vector((0, 0, 0.1 * dt - 0.4 * dt * dt))
        E.dark_cube.rotation_euler = (dt * 2, dt * 3.5, dt * 1.5)
        s = min(1.0, dt / 0.06) * (1 - ss(0.55, 0.75, dt))
        E.dark_cube.scale = (s, s, s)


def cube_u(t):
    """How far along its flight the killing cube is (0 at the portal's mouth, 1 at the Noob's head): real speed
    out of the portal, then the slow motion, then the hit."""
    a = b("hit_see") + 0.12
    if t < a:
        return None
    if t < b("hit_slow"):
        return 0.62 * (t - a) / (b("hit_slow") - a)
    if t < b("hit"):
        return 0.62 + 0.34 * (t - b("hit_slow")) / (b("hit") - b("hit_slow"))
    return min(1.0, 0.96 + (t - b("hit")) / 0.04 * 0.04)


def hit_cube(E, t):
    ob = E.hit_cube
    u = cube_u(t)
    t1 = cube_hit_at()
    if u is None or t >= t1 + 0.9:
        ob.location = (0, 0, -300)
        return
    mouth = portal_mouth(E)
    tgt = gp(E, NOOB_BTN) + Vector((0, 0, 1.3))
    tgt = tgt + (mouth - tgt).normalized() * 0.45            # it stops on his face, it doesn't go into it
    if t < t1:
        ob.location = mouth.lerp(tgt, u) + Vector((0, 0, 1.2 * math.sin(math.pi * u)))
        ob.rotation_euler = (u * 7, u * 4, 0)
    else:
        dt = 0.6 * (t - t1)
        land = tgt + Vector((1.0, -0.6, 0))
        land.z = E.ground(land.x, land.y) + 0.21
        p = tgt + Vector((-1.2 * dt, 0.9 * dt, 2.0 * dt - 4.9 * dt * dt))
        p.z = max(p.z, land.z)
        ob.location = p
        ob.rotation_euler = (7 + dt * 5, 4, 0)


def apply(E, t):
    from ep09_new import NF, SF  # noqa: F401
    name, t0, t1 = which(t)
    tc = t
    if smash_at() <= t < smash_at() + 0.084:
        t = smash_at()
    light(E, t)
    portal(E, t)
    pad(E, t)
    junk(E, t)
    hit_cube(E, t)
    dragon(E, t)
    ripple(E, t)
    zombies(E, t)
    steve(E, t)
    noob(E, t)
    camera(E, tc, name, t0, t1)


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
    if shot in ("hit_see", "hit_slow", "hit", "lock", "lunge", "fear", "cheer", "rise", "hand") or t >= b("suck", 1):
        # by the portal its violet would light their faces head-on: a violet rim, the faces in their own colours
        E.PP.light.data.energy *= 0.12 if t >= b("suck", 1) else 0.35
        E.key.data.energy *= 1.3
    if shot in ("shadow", "circle", "toss", "dive"):
        # the camera looks up at the sky: aim the key at the two of them, not at the sky
        tgt = chars_mid(E)
        E.key.location = loc + (tgt - loc) * 0.35 + Vector((0.4, 0, 1.2))
        E.key.rotation_euler = (tgt - E.key.location).to_track_quat("-Z", "Y").to_euler()
    if shot in ("windup", "swing", "dragons_too", "yes"):
        E.key.data.energy *= 1.6
    if not hasattr(E, "fill_cam"):
        fl = bpy.data.objects.new("fill_cam", bpy.data.lights.new("fill_cam", "AREA"))
        E.sc.collection.objects.link(fl)
        fl.data.size = 2.0
        fl.data.color = (1.0, 0.97, 0.94)
        fl.visible_camera = False
        fl.visible_glossy = False
        E.fill_cam = fl
    on = t >= b("suck", 1)
    E.fill_cam.data.energy = 90.0 if on else 0.0
    E.fill_cam.location = loc + (look - loc).normalized() * 0.5 + Vector((0, 0, 0.8))
    E.fill_cam.rotation_euler = (look - E.fill_cam.location).to_track_quat("-Z", "Y").to_euler()


def _wide(E, t, t0, t1, lens=20):
    c = Vector((-1.2, 0.6, E.ground(-1.2, 0.6) + 2.6))
    loc = Vector((1.6, -8.6, E.ground(1.6, -8.6) + 1.3))
    return loc, c, lens


def _g(E, x, y, h):
    return Vector((x, y, E.ground(x, y) + h))


def _fwd(ob):
    f = ob.matrix_world.to_3x3() @ Vector((0, -1, 0))
    f = Vector((f.x, f.y, 0))
    return f.normalized() if f.length > 1e-6 else Vector((0, -1, 0))


def _front_of(head, f, dist, side=0.0, up=0.0):
    sd = Vector((-f.y, f.x, 0))
    return head + f * dist + sd * side + Vector((0, 0, up))


def _zhead(E, k):
    Z = E.Z[k]
    return Z.boxes["head"].matrix_world.translation


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus or None, handheld)"""
    u = ss(t0, t1, t) if t1 < 1e8 else 0.0
    if shot == "eye":
        sp = gp(E, STEVE0)
        d = (E.crack_at - sp)
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        loc = sp + d * 1.6 - side * 1.8 + Vector((0, 0, 1.8))
        loc = loc.lerp(E.crack_at, 0.06 * ss(0.0, 2.1, t))
        snap = b("eye") + 2.1
        return loc, E.crack_at, 28, 64.0, None, 0.04 + 0.5 * math.exp(-((t - snap - 0.03) / 0.08) ** 2)
    if shot == "lookup":
        c = _g(E, -0.6, 1.0, 1.7)
        loc = _g(E, -4.6, -0.2, 0.6)
        return loc, c, 22, 64.0, None, 0.04
    if shot == "rule":
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE0) + Vector((-1.0, -2.6, 1.78))
        return loc, hs + Vector((-0.45, 0, -0.18)), 36, 2.8, None, 0.05
    if shot == "build":
        loc = gp(E, BUILD_CAM) + Vector((0, 0, 1.2)) + Vector((-0.3, 0.4, 0)) * u
        c = _g(E, -1.2, 2.2, 2.6)
        return loc, c, 20, 64.0, None, 0.04
    if shot == "this":
        hn = M.P6._head(E.N.face)
        c = hn.lerp(gp(E, PILLAR + Vector((0.5, 0.5, 0))) + Vector((0, 0, 1.0)), 0.45)
        loc = Vector((-0.2, -2.0, c.z - 0.35))
        return loc, c, 28, 3.2, None, 0.05
    if shot == "dont":
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE_DONT) + Vector((0.6, -2.8, 1.35))
        return loc, hs + Vector((0.3, -0.3, -0.45)), 30, 3.2, None, 0.08
    if shot == "press":
        top = gp(E, PILLAR + Vector((0.5, 0.5, 0))) + Vector((0, 0, 1.08))
        loc = top + Vector((-0.9, -1.7, 0.2))
        jolt = 0.1 + 0.9 * math.exp(-((t - b("press") - 0.03) / 0.05) ** 2)
        return loc, top + Vector((0.1, 0.0, 0.18)), 40, 5.0, None, jolt
    if shot == "open":
        loc, c, lens = _wide(E, t, t0, t1)
        loc = loc + Vector((0.0, 0.5, 0.0)) * u
        return loc, c, lens, 64.0, None, 0.06 + 0.6 * math.exp(-((t - b("portal_open") - 0.08) / 0.15) ** 2)
    if shot in ("chaos", "suck"):
        loc, c, lens = _wide(E, t, t0, t1)
        return loc, c, lens, 64.0, None, 0.25 if shot == "chaos" else 0.3
    # ---- the pour
    x0 = ZOMBIES[0][0]
    if shot == "hand":
        # low and close on the swirl where the first one comes through; a slow push in; its head rising into frame
        mem = _g(E, x0, PORTAL.y - 0.05, 0)
        loc = mem + Vector((0.9, -3.4 + 0.7 * u, 1.05))
        look = mem + Vector((0.05, 0, 1.75 + 0.25 * ss(t0 + 0.6, t0 + 1.4, t)))
        return loc, look, 32, 4.5, None, 0.05
    if shot == "rise":
        # from the grass, looking up: it steps out over us, the swirl behind it; its eyes
        z = E.Z[0].root.location
        loc = _g(E, -3.95, 1.15, 0.4)
        look = Vector((z.x, z.y, 0)) + Vector((0, 0, E.ground(z.x, z.y) + 1.9))
        return loc, look, 20, 64.0, None, 0.06
    if shot == "cheer":
        # the Noob in front, cheering at the right; two more coming out of the swirl behind him at the left
        # behind the zombies coming out: Steve facing them, frozen, and the Noob cheering beyond him
        loc = _g(E, -4.3, 0.2, 1.55)
        return loc, _g(E, 0.4, 0.5, 1.45), 24, 64.0, None, 0.05
    if shot == "lock":
        # close on the eager one's face: its head comes round to Steve (to us), its eyes flare
        h = _zhead(E, 1)
        f = _fwd(E.Z[1].boxes["head"])
        loc = _front_of(h, f, 1.15, -0.45, -0.1)
        return loc, h + Vector((0, 0, -0.05)), 40, 3.5, None, 0.05
    if shot == "lunge":
        # side on and low: it lunges in from the left, arms up; Steve throwing himself back at the right
        a = gp(E, lunge_end())
        e = gp(E, STEVE_DONT.lerp(STEVE_BACKED, 0.7))
        mid = a.lerp(e, 0.5)
        d = (e - a)
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((d.y, -d.x, 0))
        if side.y > 0:
            side = -side
        loc = mid + side * 4.6 + Vector((0, 0, 1.0)) - d * 0.25 * u
        return loc, mid + Vector((0, 0, 1.3)), 22, 64.0, None, 0.1 + 0.5 * math.exp(-((t - b("lunge") - 1.1) / 0.1) ** 2)
    if shot == "fear":
        # over the zombie's shoulder: Steve's face, terrified, backing off; its arms reaching into the frame
        # anchored where it landed (not on its moving head: the camera never passes through it)
        h = gp(E, lunge_end()) + Vector((0, 0, 2.1))
        s_ = M.P6._head(E.S.face, E.S.holder)
        d = (gp(E, STEVE_BACKED) - gp(E, lunge_end()))
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        loc = h - d * 1.2 + side * 1.9 + Vector((0, 0, -0.1))
        return loc, s_ + Vector((0, 0, -0.1)), 34, 2.8, (s_ - loc).length, 0.08
    # ---- the hit
    if shot == "hit_see":
        # side on: the swirl at the left spitting the cube; the Noob cheering at the right, turned away from it
        a, n = portal_mouth(E), gp(E, NOOB_BTN) + Vector((0, 0, 1.3))
        mid = a.lerp(n, 0.55)
        d = (n - a)
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((d.y, -d.x, 0))
        loc = mid + side * 7.5 + Vector((0, 0, -1.6))
        loc.z = max(loc.z, E.ground(loc.x, loc.y) + 1.2)
        return loc, mid + Vector((0, 0, 0.6)), 24, 64.0, None, 0.06
    if shot == "hit_slow":
        # slow motion, close on the Noob: the cube coming in at the top left; his head comes round too late
        hn = M.P6._head(E.N.face)
        f = _fwd(E.N.root)
        loc = _front_of(hn, f, 2.3, -1.1, -0.15)
        cube = E.hit_cube.matrix_world.translation
        look = hn.lerp(cube, 0.3 * ss(t0, t1, t)) if cube.z > -100 else hn
        return loc, look, 30, 3.0, (hn - loc).length, 0.03
    if shot == "hit":
        # the impact, a step wider: his parts flying toward us and to the right, the oak clear behind them
        n = gp(E, NOOB_BTN)
        loc = n + Vector((0.7, -3.9, 1.2))
        return loc, n + Vector((0.7, 0, 1.15)), 24, 64.0, None, 0.08 + 0.6 * math.exp(-((t - cube_hit_at() - 0.05) / 0.1) ** 2)
    if shot == "respawn":
        pd = E.pad_at
        loc = pd + Vector((-1.0, -3.6, 0.6))
        return loc, pd + Vector((0.1, 0, 1.1)), 26, 4.0, None, 0.05
    # ---- cause and effect
    if shot == "cause":
        # wide: the button at the right blinks red; the portal at the left pulses and one more stumbles out
        # the button close in front, the portal straight behind it: it blinks, the portal pulses, one more comes
        btn = gp(E, PILLAR + Vector((0.5, 0.5, 0))) + Vector((0, 0, 1.1))
        prt = gp(E, PORTAL) + Vector((0, 0, 2.6))
        loc = _g(E, 3.3, -2.0, 1.35) + Vector((-0.3, 0.25, 0)) * u
        return loc, btn.lerp(prt, 0.35), 30, 64.0, None, 0.03
    if shot == "realize":
        # Steve's face, close: the next blink lights it red; his eyes go to the button, to the portal
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = _front_of(hs, _fwd(E.S.holder), 1.5, 0.3, -0.05)
        return loc, hs + Vector((0.0, 0, -0.06)), 40, 2.8, None, 0.04
    if shot == "planb":
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE_DODGE) + Vector((2.0, -1.0, 1.45))
        return loc, hs + Vector((-0.3, 0.4, -0.25)), 30, 3.2, None, 0.12
    if shot == "dash":
        s_ = Vector(E.S.holder.location)
        loc = _g(E, 0.8, -4.6, 1.3)                          # the front-yard side, as the wind-up and the smash
        return loc, s_ + Vector((0.0, 0, 1.2)), 24, 64.0, None, 0.15
    # ---- the smash
    top = gp(E, PILLAR + Vector((0.5, 0.5, 0))) + Vector((0, 0, 1.05))
    if shot == "windup":
        loc = _g(E, 0.2, -3.6, 1.0)
        return loc, _g(E, 0.15, -0.55, 1.75), 24, 64.0, None, 0.06
    if shot == "swing":
        # slow motion, low by the button: the pickaxe coming down at us, his face behind it, set
        loc = top + Vector((0.55, -1.25, 0.05))
        hs = M.P6._head(E.S.face, E.S.holder)
        return loc, top.lerp(hs, 0.55), 26, 4.0, (top - loc).length + 0.3, 0.03
    if shot == "shatter":
        # the button, close: the hit, the shards, the portal behind turning inside out
        loc = top + Vector((0.45, -1.15, 0.22))
        return loc, top + Vector((-0.1, 0.1, 0.12)), 40, 4.0, None, 0.08 + 1.1 * math.exp(-((t - smash_at() - 0.04) / 0.12) ** 2)
    if shot == "cling":
        # close on the frame's bottom row: the last one hanging on, legs in the swirl, eyes on us, growling
        g = cling_grip(E)
        loc = g + Vector((1.5, -2.4, 0.55))
        return loc, g + Vector((-0.15, 0.1, 0.25)), 30, 3.5, None, 0.06
    if shot == "quiet":
        c = _g(E, -2.0, 1.8, 2.2)
        loc = _g(E, -0.8, -6.6, 1.0)
        return loc, c, 24, 64.0, None, 0.03
    if shot == "never":
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE_TIRED) + Vector((0.6, -2.8, 1.45))
        return loc, hs + Vector((-0.6, 0, -0.35)), 30, 3.2, None, 0.04
    # ---- the dragon
    mid = (gp(E, STEVE_TIRED) + gp(E, NOOB_NEAR)) / 2 if t < b("catch") else (gp(E, STEVE_D) + gp(E, NOOB_D)) / 2
    dp = Vector(E.D.root.location)
    if shot == "shadow":
        # low in front of them: the two of them, the sky above; something huge crosses it, its shadow over them
        # from by the portal, low, back at them: their faces; it comes over from behind us, its shadow on them
        s0, n0 = gp(E, STEVE_TIRED), gp(E, NOOB_NEAR)
        ln = Vector(((n0 - s0).x, (n0 - s0).y, 0)).normalized()
        sd = Vector((-ln.y, ln.x, 0))
        if sd.x > 0:
            sd = -sd
        loc = mid + sd * 4.2 + Vector((0, 0, 0.45))
        return loc, mid - sd * 2.0 + Vector((0, 0, 3.2)), 16, 64.0, None, 0.05 + 0.25 * math.exp(-((t - b("sky_roar") - 0.55) / 0.2) ** 2)
    if shot == "dive":
        # from the ground by the portal: it comes down out of the sky at us
        loc = _g(E, -0.6, -4.6, 1.0)
        return loc, loc.lerp(dp, 0.85) if dp.z > -100 else loc + Vector((0, 5, 6)), 20, 64.0, None, 0.08 + 0.2 * ss(t0 + 0.8, t1, t)
    if shot == "catch":
        # by the frame: it swoops in, snatches the clinging one off the frame, and hauls it up and away
        # from the side, close on the frame: it swoops in, its jaws close on the clinging one, it hauls it off
        g = cling_grip(E)
        loc = _g(E, -9.5, 0.8, 3.9)
        look = (g + Vector((0.0, -1.0, 1.0))).lerp(dragon_head(E) + Vector((0, 0, -1.0)), ss(t0 + 1.0, t0 + 1.35, t))
        return loc, look, 30, 64.0, None, 0.04 + 0.15 * math.exp(-((t - b("catch") - 0.12) / 0.08) ** 2)
    if shot == "circle":
        # low behind them, a little to the side: their faces turned up, the dragon wheeling over the meadow
        f = (_fwd(E.S.holder) + _fwd(E.N.root)).normalized()
        sd = Vector((-f.y, f.x, 0))
        loc = mid + sd * 3.4 + f * 1.6 + Vector((0, 0, 0.6))
        return loc, (mid + Vector((0, 0, 1.6))).lerp(dp, 0.3), 16, 64.0, None, 0.05
    if shot == "whoa":
        # the Noob, close, from in front of him: delighted, looking up at it
        # anchored to where the dragon is as the shot starts (not to his turning body: no jump when he points)
        hn = M.P6._head(E.N.face)
        h0 = gp(E, NOOB_D) + Vector((0, 0, hn.z - E.ground(NOOB_D.x, NOOB_D.y)))
        dd = _dragon_pos(E, t0) - h0
        f = Vector((dd.x, dd.y, 0)).normalized()
        sdn = Vector((-f.y, f.x, 0))
        if sdn.dot(gp(E, STEVE_D) - h0) > 0:
            sdn = -sdn
        loc = h0 + f * 1.5 + sdn * 0.45 + Vector((0, 0, -0.45))
        return loc, hn + Vector((0, 0, 0.05)), 35, 3.0, None, 0.03
    if shot == "toss":
        # the dragon over the meadow: it flings the zombie away over the trees
        loc = mid + Vector((0.6, 0.6, 1.4))
        return loc, dp, 32, 64.0, None, 0.05
    if shot == "dragons_too":
        # the two of them, from in front: the Noob turning to Steve; Steve deadpan
        s0, n0 = gp(E, STEVE_D), gp(E, NOOB_D)
        ln = Vector(((n0 - s0).x, (n0 - s0).y, 0)).normalized()
        dd = _dragon_pos(E, t0) - mid
        f = Vector((dd.x, dd.y, 0)).normalized()
        loc = mid + f * (3.9 - 0.6 * u) + Vector((0, 0, 1.2))
        return loc, mid + Vector((0, 0, 1.25)), 28, 4.0, None, 0.03
    if shot == "yes":
        hs = M.P6._head(E.S.face, E.S.holder)
        s0, n0 = gp(E, STEVE_D), gp(E, NOOB_D)
        to_n = Vector(((n0 - s0).x, (n0 - s0).y, 0)).normalized()
        dd = _dragon_pos(E, t0) - s0
        f = Vector((dd.x, dd.y, 0)).normalized()
        sd = Vector((-f.y, f.x, 0))
        if sd.dot(to_n) > 0:
            sd = -sd
        h0 = s0 + Vector((0, 0, hs.z - s0.z))
        loc = h0 + (f * 0.85 + sd * 0.35).normalized() * 1.6 + Vector((0, 0, -0.1))
        return loc, hs + Vector((0, 0, -0.08)), 36, 2.8, None, 0.03
    if shot == "roar":
        # the dragon turned to them, hovering, roaring at us
        dh = dragon_head(E)
        d = (mid + Vector((0, 0, 1.6))) - dh
        d = d.normalized()
        loc = dh + d * 6.5 + Vector((0, 0, -0.8))
        return loc, dh + Vector((0, 0, -0.6)), 30, 64.0, None, 0.12 + 0.5 * ss(b("dragon_turn") + 0.1, b("dragon_turn") + 0.3, t) * (1 - ss(b("dragon_turn", 1) - 0.2, b("dragon_turn", 1), t))
    if shot == "go":
        # Steve three-quarter to us, his arm flung back at the portal; its glow behind his hand; the Noob at the edge
        hs = M.P6._head(E.S.face, E.S.holder)
        s0 = gp(E, STEVE_D)
        away = Vector(((s0 - gp(E, PORTAL)).x, (s0 - gp(E, PORTAL)).y, 0)).normalized()
        sd = Vector((-away.y, away.x, 0))
        if sd.dot(gp(E, NOOB_D) - s0) < 0:
            sd = -sd
        h0 = s0 + Vector((0, 0, hs.z - s0.z))
        loc = h0 + away * 2.4 + sd * 0.9 + Vector((0, 0, -0.1))
        return loc, hs + Vector((0, 0, -0.15)) - away * 0.6, 30, 3.5, (hs - loc).length, 0.08
    if shot == "run":
        # side on: they sprint across to the portal (screen left, where he pointed), the dragon coming behind them
        s_ = Vector(E.S.holder.location)
        n_ = Vector(E.N.root.location)
        c = (s_ + n_) / 2 if n_.z > -100 and s_.z > -100 else s_
        a, tk, _ = run_path(E, "steve")
        mp = (a + tk) / 2
        loc = Vector((mp.x - 4.6, mp.y - 4.6, E.ground(mp.x - 4.6, mp.y - 4.6) + 1.4))
        return loc, c + Vector((0, 0, 1.2)) + (tk - a).normalized() * 0.8, 24, 64.0, None, 0.1
    if shot == "jump":
        # behind them, three-quarter: they dive into the swirl; the dragon comes down behind them
        _, tk1, _ = run_path(E, "steve")
        _, tk2, _ = run_path(E, "noob")
        tk = (tk1 + tk2) / 2
        away = Vector(((tk - gp(E, PORTAL)).x, (tk - gp(E, PORTAL)).y, 0)).normalized()
        sd = Vector((-away.y, away.x, 0))
        loc = tk + away * 3.6 + sd * 1.6 + Vector((0, 0, 1.6))
        return loc, gp(E, PORTAL) + Vector((0, 0, 2.2)), 24, 64.0, None, 0.12
    if shot == "dive_after":
        # from the frame's side, low: the dragon coming at the portal, at us
        loc = _g(E, -7.0, -0.6, 0.55)                        # low, close: it towers as it comes at the portal
        return loc, dp if dp.z > -100 else _g(E, 0, -2, 4), 18, 64.0, None, 0.12 + 0.3 * u
    if shot == "swirl":
        # close on the swirl: its snout plunges in; the flash
        c = gp(E, PORTAL) + Vector((0, 0, 4.2))
        loc = c + Vector((3.2, -3.4, -0.6))
        return loc, c + Vector((-0.2, 0, -0.1)), 30, 64.0, None, 0.15 + 0.4 * u
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
    E.cuts = sorted(t0 for _, t0 in shot_bounds()) + [cube_hit_at(), smash_at()]
    M._render(E, frames, out, apply, M.finish_forest)


if __name__ == "__main__":
    main()
