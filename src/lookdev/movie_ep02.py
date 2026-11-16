"""The movie, chapter 2 ("The Plan"), in the new look and in 16:9.

It picks up on Episode 1's last shot (the eye in the sky's crack, the same model and the same angle),
then the same meadow, the same floating oak: Steve's plan (a portal home, built block by block on the
place sounds), the Noob and the button, the junk and three zombies pouring out, the Noob's burst and
respawn, Plan B (the button smashed), the suck, the quiet, and the figure inside the dark portal that
waves back before the portal snaps empty. Shot list: story/movie/ep02_shots.md; sound and timing:
episodes/movie_ep02_the_plan.json (its sound preview passed review, v4).

    python src/lookdev/movie_ep02.py TIMELINE VOICE TEX_DIR ASSETS OUT_DIR [--times 1.0,5.0] [--res 720]
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
STEVE_SMASH = Vector((-0.45, -0.55, 0.0))  # Steve at the button (west of it, facing +x)
STEVE_TIRED = Vector((-0.9, -1.9, 0.0))    # after it, he staggers back a few steps (clear of the Noob's way to the portal)
NOOB_PORTAL = Vector((0.0, 2.6, 0.0))      # "Hi!": at the portal's right edge, so a camera sees his face and the portal
MIRROR_CAM = Vector((-3.0, 0.0, 0.0))      # "Hi!": front-left of him, seeing into the portal
WAVED_CAM = Vector((-1.8, 0.4, 0.0))       # "It waved back": close on him, the portal (and the figure) behind
NOOB_WATCH = Vector((1.9, -0.6, 0.0))
BUILD_CAM = Vector((-0.6, -5.0, 0.0))      # the build's camera (the frame, Steve at its end, the button, the Noob)      # where the Noob watches the building from     # the Noob in front of the dark portal, at its right
ZOMBIES = [  # (out of the portal at x, where it ends up after the pour, where the chaos takes it)
    (-4.6, Vector((-5.0, 0.4, 0)), Vector((-4.2, -0.8, 0))),
    (-3.2, Vector((-3.2, -0.8, 0)), Vector((-2.9, -2.6, 0))),
    (-2.2, Vector((-1.8, -0.2, 0)), Vector((3.4, -1.0, 0))),
]


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
    _figure(E, assets)
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
    launch = spread(b("pour"), b("pour") + 3.6, n)
    for k in range(n):
        s = rnd.uniform(0.32, 0.5)
        ob = _cube(E, f"junk_{k}", s, pink)
        _uv_full(ob)
        land = Vector((rnd.uniform(-6.0, 3.2), rnd.uniform(-4.5, 2.2), 0))
        if (land - NOOB_BTN).length < 1.0 or (land - PAD).length < 1.2 or (land - PILLAR).length < 1.0:
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
    from mob import build_mob, skin_path
    E.Z = [build_mob(E.sc, f"zombie_{k}", skin_path(assets)) for k in range(3)]
    for Z in E.Z:
        Z.root.location = (0, 0, -300)


def _burst(E):
    """The Noob bursting: his own parts fly; a small dark cube hangs a moment in the middle (Null's cell)."""
    N = E.N
    E.burst_parts = {"torso": N.torso, "neck": N.neck, "arm_sl": N.arms["sl"], "arm_sr": N.arms["sr"],
                     "leg_sl": N.legs["sl"], "leg_sr": N.legs["sr"]}
    E.burst_home = {k: (Vector(o.location), o.rotation_mode, tuple(o.rotation_quaternion)) for k, o in E.burst_parts.items()}
    rnd = random.Random(3)
    E.burst_v = {k: Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.6, 1.3))) for k in E.burst_parts}
    E.burst_v["neck"] = Vector((0.3, -0.4, 1.6))
    dm = bpy.data.materials.new("dark_cell")
    dm.use_nodes = True
    bs = dm.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.01, 0.005, 0.015, 1)
    bs.inputs["Roughness"].default_value = 0.3
    bs.inputs["Emission Color"].default_value = (0.6, 0.0, 0.5, 1)
    bs.inputs["Emission Strength"].default_value = 0.35
    bs.inputs["Emission Strength"].default_value = 1.4
    E.dark_cube = _cube(E, "dark_cell", 0.22, dm)


def _figure(E, assets):
    """The figure in the dark portal: the finale's Null, small and far, in the room behind the surface."""
    from null import build_null
    col = bpy.data.collections.new("figure")
    E.sc.collection.children.link(col)
    E.fig = build_null(col, assets, height=1.5, orbit=False)
    for ob in col.all_objects:
        ob.visible_shadow = False
    E.fig.root.location = (0, 0, -300)


# ------------------------------------------------------------------ the shots
SHOTS = [("eye", "eye"), ("lookup", "look_up"), ("rule", "steve_rule"), ("build", "steve_plan"),
         ("this", "noob_this"), ("dont", "steve_dont"), ("press", "press"), ("open", "portal_open"),
         ("react", ("pour", 1.6)), ("hit", ("hit", -0.45)), ("respawn", "respawn"), ("chaos", "chaos"), ("planb", "steve_planb"), ("dash", "dash"),
         ("smash", "smash"), ("suck", "suck"), ("quiet", "quiet"), ("never", "steve_never"), ("approach", "approach"),
         ("mirror", "noob_hi"), ("waved", "noob_waved"), ("snap", "snap")]


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


def place_times():
    return spread(b("steve_plan"), b("build") + 2.3, 26)


# ------------------------------------------------------------------ per frame
DAY = {"glow": (255, 240, 220), "power": 30.0, "horizon": (220, 232, 250), "mid": (140, 186, 250), "zenith": (52, 120, 236),
       "fill": 1.1, "fill_col": (186, 206, 240)}
DUSK = {"glow": (236, 190, 230), "power": 8.0, "horizon": (200, 150, 200), "mid": (110, 90, 170), "zenith": (44, 34, 96),
        "fill": 0.8, "fill_col": (176, 150, 220)}
# the dark portal's mood: a dimmer, cooler afternoon (readable: as bright as chapter 0's darkening at least)
GLOOM = {"glow": (230, 214, 236), "power": 16.0, "horizon": (196, 196, 226), "mid": (120, 140, 206), "zenith": (50, 70, 160),
         "fill": 0.9, "fill_col": (170, 176, 226)}


def light(E, t):
    from world import set_sky
    snap = b("eye") + 2.1
    dk = 1.0 - ss(snap, b("steve_rule"), t)                      # chapter 1's dusk lifts as the crack shuts
    gl = ss(b("approach"), b("noob_hi") + 0.6, t) * (1 - ss(b("snap") + 0.1, b("snap") + 1.6, t))
    look = M.mix_look(M.mix_look(DAY, GLOOM, gl), DUSK, dk)
    set_sky(E.W, look)
    if not hasattr(E, "sun0"):
        E.sun0 = E.W.sun.data.energy
        E.key0 = (E.key.data.energy, tuple(E.key.data.color))
    E.W.sun.data.energy = E.sun0 * (1 - 0.6 * dk) * (1 - 0.3 * gl)
    E.sc.view_settings.exposure = -0.05 - 0.3 * dk - 0.12 * gl
    E.key.data.energy = E.key0[0] * (1 - 0.35 * dk)
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
    # the crack: the eye looks round, then the crack snaps shut from its ends, a seam fading
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
    E1.eye_look(E, t + 3.2, (not E.crack.hide_render) and t < snap, 0.0)       # it goes on looking round from chapter 1


def portal(E, t):
    pt = place_times()
    P = E.PP
    # place 0 is the button's stone, 1 the button ("step one"); 2..25 the frame
    for k, ob in enumerate(E.portal_order):
        h = Vector(ob["home"])
        if t < pt[k + 2]:
            ob.location = h + Vector((0, 0, -200))
            ob.scale = (1, 1, 1)
            continue
        u = ss(pt[k + 2], pt[k + 2] + 0.12, t)                 # it pops in, settling to its size
        ob.location = h + Vector((0, 0, 0.12 * (1 - u)))
        s = 0.7 + 0.3 * u + 0.06 * math.sin(math.pi * u)
        ob.scale = (s, s, s)
    # the membrane: off until the press; the flash, the swirl; white and pulling in the suck; dark after; gone at the snap
    on = b("portal_open")
    vis = on <= t < b("snap") + 0.12
    P.membrane.hide_render = not vis
    flash = math.exp(-((t - on - 0.08) / 0.12) ** 2) + 0.8 * math.exp(-((t - b("suck") - 0.05) / 0.15) ** 2) \
        + 1.2 * math.exp(-((t - b("snap") - 0.04) / 0.08) ** 2)
    E.portal_flash.hide_render = flash < 0.02
    E.portal_flash_em.inputs["Strength"].default_value = 14.0 * min(1.0, flash)
    swirl = ss(on, on + 0.3, t)
    dark = ss(b("suck") + 1.4, b("suck", 1), t)
    E.portal_power.inputs[2].default_value = (0.42 + 0.6 * math.exp(-((t - on - 0.3) / 0.4) ** 2)) * swirl * (1 - 0.93 * dark) \
        + 1.5 * ss(b("suck"), b("suck") + 0.2, t) * (1 - ss(b("suck") + 1.2, b("suck") + 1.8, t))
    E.portal_flow.inputs[1].default_value = (0.13 * t, 0.37 * t * (1 + 2 * (1 - dark)) * (1 + 3 * ss(b("suck"), b("suck") + 0.3, t) * (1 - dark)), 0)
    dv = 1.0 - 0.72 * dark
    E.portal_dim.inputs[7].default_value = (dv, dv * 0.9, dv, 1)
    E.portal_see.outputs[0].default_value = 0.72 * ss(b("noob_hi") - 0.2, b("noob_hi") + 0.6, t)
    P.light.data.energy = 600 * swirl * (1 - 0.75 * dark) * (1 if vis else 0) + 3000 * min(1.0, flash)
    E.portal_room.hide_render = not (b("approach") <= t < b("snap") + 0.04)
    E.portal_room_light.data.energy = 140.0 * (0 if E.portal_room.hide_render else 1)
    # the button, its stone, and the smash
    pt_pillar, pt_button = pt[0], pt[1]
    pg = gp(E, PILLAR + Vector((0.5, 0.5, 0)))
    if t < pt_pillar:
        E.pillar.location = (0, 0, -300)
    else:
        u = ss(pt_pillar, pt_pillar + 0.12, t)
        E.pillar.location = pg + Vector((0, 0, 0.5 + 0.12 * (1 - u)))
    top = pg + Vector((0, 0, 1.0))
    smash = b("smash") + 0.35
    press = ss(b("press") - 0.03, b("press") + 0.03, t) * (1 - ss(b("press") + 0.3, b("press") + 0.45, t))
    bsb = E.button.data.materials[0].node_tree.nodes["Principled BSDF"]
    bsb.inputs["Emission Strength"].default_value = 0.25 + 4.0 * math.exp(-((t - b("press") - 0.05) / 0.12) ** 2)
    if t < pt_button or t >= smash:
        E.button.location = (0, 0, -300)
    else:
        u = ss(pt_button, pt_button + 0.12, t)
        E.button.location = top + Vector((0, 0, 0.08 - 0.1 * press + 0.1 * (1 - u)))
    for ob, v, w, s in E.button_shards:
        if t < smash:
            ob.location = (0, 0, -300)
            continue
        dt = t - smash
        p = top + Vector((0, 0, 0.1)) + v * dt + Vector((0, 0, -4.9 * dt * dt))
        p.z = max(p.z, E.ground(p.x, p.y) + s / 2)
        ob.location = p
        ob.rotation_euler = tuple(w * min(dt, 0.8))
    # the dust puffs where the blocks land
    for k, ob in enumerate(E.puffs):
        ob.location = (0, 0, -300)
    alive = [(k, x) for k, x in enumerate(pt) if 0 <= t - x < 0.35]
    for slot, (k, x) in enumerate(alive[:4]):
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
    a = b("portal_open") + 0.4
    # the spark: out of the portal's mouth in an arc to the pad's place, landing as the pad forms
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
        E.beam.scale = (0.6 + 0.4 * ss(a, a + 0.3, t), 0.6 + 0.4 * ss(a, a + 0.3, t), 3.2)
        E.beam_mix.inputs[0].default_value = 0.3 * bk
        E.beam_em.inputs["Strength"].default_value = 6.0
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


def portal_mouth(E):
    return gp(E, PORTAL) + Vector((0, -0.4, PH / 2))


def junk(E, t):
    mouth = portal_mouth(E)
    g = 9.81
    sk0, sk1 = b("suck") + 0.4, b("suck") + 2.0
    for k, c in enumerate(E.cubes):
        ob = c["ob"]
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
        # the suck: each cube pulled back into the mouth, spinning, shrinking as it goes in
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
    # the pole: tumbles out end over end, lands across the grass, rolls; sucked in first
    pole = E.pole
    t0 = b("pour") + 0.9
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


def steve_spot(E, t):
    """Where Steve stands (his path, not his pose): for whoever looks at him."""
    if t < b("chaos"):
        return gp(E, STEVE_DONT)
    if t < b("dash"):
        return gp(E, STEVE_DONT.lerp(STEVE_DODGE, ss(b("chaos"), b("chaos") + 1.6, t)))
    return gp(E, STEVE_DODGE.lerp(STEVE_SMASH, ss(b("dash"), b("dash", 1), t)))


def _yaw(d):
    return math.degrees(math.atan2(d.x, -d.y))


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _personas():
    from mob import Persona
    return [Persona(1.3, speed=0.85, limp=0.6, tilt=8, reach=84, droop=0.35),     # the slow one, dragging a leg
            Persona(4.1, speed=1.15, limp=0.0, tilt=-5, reach=94, droop=0.0),     # the eager one (goes for Steve)
            Persona(7.7, speed=0.8, limp=0.3, tilt=13, reach=78, droop=0.7)]      # head lolling, one arm low


STRIDE = 0.85                               # blocks per step cycle


def zombie_state(E, k, t):
    """Where zombie k is and what it is doing: a dict with p, yaw, phase (None standing), arms_up, lean,
    look (a target point), lunge, lift (0..1, the suck), flail."""
    per = _personas()[k]
    x_out, after, chaos_to = ZOMBIES[k]
    t_out = b("pour") + 0.4 + 1.0 * k
    if t < t_out - 0.35:
        return None
    door = gp(E, Vector((x_out, PORTAL.y + 0.9, 0)))
    a = gp(E, after)
    c = gp(E, chaos_to)
    steve_p = steve_spot(E, t)
    v = 0.95 * per.speed
    st = {"arms_up": 1.0, "lean": 0.0, "lunge": 0.0, "lift": 0.0, "flail": 0.0, "look": steve_p + Vector((0, 0, 1.6))}
    # out of the portal: the first step a lurch (it falls forward out of the surface, catches itself);
    # the arms come up from hanging as its head finds Steve
    d1 = (a - door).length
    t_arr = t_out + d1 / v
    if t < t_arr:
        u = max(0.0, (t - t_out) / (t_arr - t_out))
        p = door.lerp(a, u)
        st["phase"] = max(0.0, (t - t_out)) * v / STRIDE
        st["yaw"] = _yaw(a - door)
        st["arms_up"] = ss(t_out + 0.15, t_out + 0.9, t)
        st["lean"] = 14 * math.exp(-((t - t_out - 0.15) / 0.2) ** 2)          # the lurch
        st["p"] = p
        return st
    c0 = b("chaos") + 0.25 * k
    d2 = (c - a).length
    t2 = c0 + d2 / v
    sk = b("suck") + 0.45 + 0.35 * k
    if t < c0:
        # arrived: swaying where it stopped, turning to Steve
        st["p"] = a
        st["phase"] = None
        y_path, y_st = _yaw(a - door), _yaw(steve_p - a)
        st["yaw"] = y_path + _wrap(y_st - y_path) * ss(t_arr, t_arr + 0.9, t)
        return st
    if t < sk:
        if t < t2:
            st["p"] = a.lerp(c, (t - c0) / (t2 - c0))
            st["phase"] = (d1 + (t - c0) * v) / STRIDE
            st["yaw"] = _yaw(c - a)
        else:
            st["p"] = c
            st["phase"] = None
            st["yaw"] = _yaw(c - a) + _wrap(_yaw(steve_p - c) - _yaw(c - a)) * ss(t2, t2 + 0.7, t)
        if k == 1:
            # the eager one goes for Steve: a wind-up (leaning back), the lunge, the miss, the recovery
            l0 = b("chaos") + 1.3
            wind = math.exp(-((t - l0) / 0.12) ** 2)
            lunge = ss(l0 + 0.08, l0 + 0.28, t) * (1 - ss(l0 + 0.55, l0 + 1.0, t))
            st["lean"] -= 8 * wind
            st["lunge"] = lunge
        return st
    # the suck: it digs in, leaning away, dragged backward over the grass; then torn off its feet, flailing
    p_stop = c if t >= t2 else a.lerp(c, min(1.0, (sk - c0) / max(1e-3, t2 - c0)))
    mouth = portal_mouth(E)
    away = p_stop - gp(E, PORTAL)
    away = Vector((away.x, away.y, 0)).normalized()
    drag = ss(sk - 0.5, sk, t)
    st["p"] = p_stop - away * 0.5 * drag ** 2
    st["phase"] = (t - sk) * 2.2 if t < sk else None
    st["yaw"] = _yaw(away)                                        # it faces away from the pull, fighting it
    st["lean"] = 16 * drag
    st["flail"] = ss(sk - 0.4, sk, t)
    st["lift"] = ss(sk, sk + 0.9, t) if t >= sk else 0.0
    st["arms_up"] = 1.0
    return st


def zombies(E, t):
    from mob import pose_mob, zombie_pose
    mouth = portal_mouth(E)
    pers = _personas()
    for k, Z in enumerate(E.Z):
        st = zombie_state(E, k, t)
        if st is None:
            Z.root.location = (0, 0, -300)
            continue
        p, yaw = st["p"], st["yaw"]
        # the head: toward what it looks at, a little behind the body's turn (overlap)
        lk = st["look"] - (p + Vector((0, 0, 1.6)))
        look = max(-55.0, min(55.0, _wrap(_yaw(lk) - yaw)))
        pz, bob = zombie_pose(pers[k], t, st["phase"], st["arms_up"], st["lean"], look, st["lunge"], st["flail"])
        pz["root_yaw"] = yaw
        s = 1.0
        if st["lift"] > 0:
            u = st["lift"]
            # off its feet: pulled up and back into the mouth, tumbling, stretched as it goes in
            p = p.lerp(mouth + Vector((0, 0.6, -1.0)), u ** 1.8) + Vector((0, 0, 1.3 * math.sin(math.pi * min(1.0, u * 1.15)) * (1 - u)))
            pz["root_yaw"] = yaw + 400 * u ** 1.6
            pz["root_pitch"] = -30 - 140 * u ** 1.4
            s = max(0.0, 1 - ss(0.82, 1.0, u))
        pose_mob(Z, pz)
        Z.root.location = p + Vector((0, 0, bob))
        Z.root.scale = (s, s, s)
        # the step into the world: its rear half still behind the surface (the membrane hides it)


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


def steve_place_pose(E, t, pz):
    """His right arm reaching to place the block being placed (a quick jab on each place sound)."""
    pt = place_times()
    k = max([i for i, x in enumerate(pt) if x <= t + 0.08] or [0])
    jab = math.exp(-((t - pt[k] + 0.03) / 0.07) ** 2) if b("steve_plan") - 0.1 <= t <= pt[-1] + 0.25 else 0.0
    pz["arm_sr"] = {"fwd": 55 + 35 * jab, "out": 12, "elbow": 40 - 30 * jab}
    return k


def steve(E, t):
    from ep09_new import SF
    g = E.ground
    face = dict(SF["flat"])
    pz = {"arm_sr": {"fwd": 25, "out": 12, "elbow": 35}, "arm_sl": {"fwd": 10, "out": 8, "elbow": 20}}
    pt = place_times()
    if t < b("steve_plan"):
        p = gp(E, STEVE0)
        c = E.crack_at - p
        yc = math.degrees(math.atan2(c.x, -c.y))
        # still looking up at where the crack was; then at the Noob; then (the rule) to us
        n = gp(E, NOOB0) - p
        yn = math.degrees(math.atan2(n.x, -n.y))
        yaw = lerp(yc, yn, ss(b("look_up") + 0.1, b("look_up") + 0.6, t))
        yaw = lerp(yaw, -25.0, ss(b("steve_rule") - 0.15, b("steve_rule") + 0.3, t))
        pz["head_nod"] = -30 * (1 - ss(b("look_up") + 0.1, b("look_up") + 0.6, t))
        pz["head_turn"] = 14 * (1 - ss(b("steve_rule") - 0.25, b("steve_rule") + 0.1, t)) * ss(b("steve_rule") - 0.4, b("steve_rule") - 0.15, t)
        face = dict(SF["worried"]) if t < b("look_up") + 0.5 else dict(SF["flat"])
    elif t < b("build") + 2.4:
        # he walks over to build, placing as he goes; then he turns right for the stone and the button
        u = ss(b("steve_plan"), b("steve_plan") + 1.3, t)
        p = gp(E, STEVE0.lerp(BUILD_AT, u))
        k = steve_place_pose(E, t, pz)
        if k >= 2:
            tgt = E.portal_order[k - 2].matrix_world.translation
        else:
            tgt = gp(E, PILLAR + Vector((0.5, 0.5, 0)))
        d = tgt - p
        ty = math.degrees(math.atan2(d.x, -d.y))
        # played to the camera: his body turned a third of the way to us, his head on the block he places
        cy = math.degrees(math.atan2(BUILD_CAM.x - p.x, -(BUILD_CAM.y - p.y)))
        yaw = ty + _wrap(cy - ty) * 0.35
        pz["head_turn"] = max(-50.0, min(50.0, _wrap(ty - yaw)))
        # "Nobody touches anything." - his free hand points at the button, his eyes on the Noob
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
            ph = (t - b("steve_plan")) * 1.6 * 2 * math.pi
            pz.update({"foot_sl": {"y": -0.3 * math.sin(ph), "z": max(0.0, 0.25 * math.sin(ph + 1.2))},
                       "foot_sr": {"y": 0.3 * math.sin(ph), "z": max(0.0, 0.25 * math.sin(ph + 1.2 + math.pi))}})
        pz["head_nod"] = -6
    elif t < b("steve_dont"):
        # two steps back, satisfied, looking up at his portal
        u = ss(b("build") + 2.4, b("build") + 2.9, t)
        p = gp(E, BUILD_AT.lerp(STEVE_DONT, u))
        d = gp(E, PORTAL) - p
        yaw = math.degrees(math.atan2(d.x, -d.y))
        pz["head_nod"] = -14 * u
        face = dict(SF["smug"])
        pz["arm_sl"] = {"fwd": 5, "out": 30, "elbow": 80}                    # a hand on his hip
    elif t < b("portal_open"):
        # "Don't!": he turns to the Noob, his arm shooting out
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
    elif t < b("steve_planb"):
        # the portal opens: shock; the chaos pushes him back, flinging his arms, dodging a zombie
        u = ss(b("chaos"), b("chaos") + 1.6, t)
        p = gp(E, STEVE_DONT.lerp(STEVE_DODGE, u))
        d = gp(E, PORTAL) - p
        yaw = math.degrees(math.atan2(d.x, -d.y))
        # played to the wide (his face, not his back); his head on the portal
        cy = math.degrees(math.atan2(1.6 - p.x, -(-8.6 - p.y)))
        body = yaw + _wrap(cy - yaw) * 0.45
        pz["head_turn"] = max(-55.0, min(55.0, _wrap(yaw - body)))
        yaw = body
        # the third zombie steps out right beside him: he jerks away from it
        jump = ss(b("pour") + 2.45, b("pour") + 2.6, t) * (1 - ss(b("pour") + 3.2, b("pour") + 3.8, t))
        # the Noob bursts (the hit): he flinches, an arm up against the bits
        fl_hit = ss(b("hit") + 0.0, b("hit") + 0.08, t) * (1 - ss(b("hit") + 0.4, b("hit") + 0.9, t))
        if b("pour") <= t < b("chaos"):
            pz["arm_sl"] = {"fwd": 30 + 45 * jump + 60 * fl_hit, "out": 25 + 15 * jump, "elbow": 15 + 25 * fl_hit}
            pz["arm_sr"] = {"fwd": 30 + 35 * jump, "out": 25 + 15 * jump, "elbow": 15}
            pz["chest_lean"] = -4 + 6 * jump - 8 * fl_hit
            pz["head_nod"] = 8 * jump
            pz["chest_twist"] = 18 * jump
            pz["head_turn"] = pz["head_turn"] + 35 * jump
            p = p + Vector((0.25 * jump, -0.25 * jump, 0))
        if b("chaos") <= t:
            zs = zombie_state(E, 1, t)
            dz = (zs["p"] if zs else gp(E, PORTAL)) - p
            yaw = math.degrees(math.atan2(dz.x, -dz.y))
            fl = math.sin((t - b("chaos")) * 5.0)
            pz["arm_sl"] = {"fwd": 60 + 30 * fl, "out": 40, "elbow": 30}
            pz["arm_sr"] = {"fwd": 60 - 30 * fl, "out": 40, "elbow": 30}
            pz["chest_lean"] = -8
            if 0 < u < 1:
                ph = (t - b("chaos")) * 2.0 * 2 * math.pi
                pz.update({"foot_sl": {"y": -0.3 * math.sin(ph), "z": max(0.0, 0.25 * math.sin(ph + 1.2))},
                           "foot_sr": {"y": 0.3 * math.sin(ph), "z": max(0.0, 0.25 * math.sin(ph + 1.2 + math.pi))}})
        elif t < b("pour"):
            pz["arm_sl"] = {"fwd": 30, "out": 25, "elbow": 40}
            pz["arm_sr"] = {"fwd": 30, "out": 25, "elbow": 40}
            pz["chest_lean"] = -6
        face = dict(SF["scared"]) if t >= b("pour") else dict(SF["stunned"])
    elif t < b("dash"):
        # "Plan B!": the pickaxe goes up on "B"
        p = gp(E, STEVE_DODGE)
        d = gp(E, PILLAR + Vector((0.5, 0.5, 0))) - p
        yaw = math.degrees(math.atan2(d.x, -d.y)) - 30
        k = ss(b("steve_planb") + 0.45, b("steve_planb") + 0.75, t)
        pz["arm_sr"] = {"fwd": lerp(30, 85, k), "out": lerp(15, 20, k), "elbow": lerp(40, 0, k)}
        pz["arm_sl"] = {"fwd": 20, "out": 15, "elbow": 60}
        face = dict(SF["flat"])
        face.update({"bb_tilt": 0.55, "bb_raise": -0.15, "both_to": -0.15, "both_tm": -0.15, "m_arch": 0.1})
    elif t < b("smash") + 0.6:
        # the dash to the button, then the swing down
        u = ss(b("dash"), b("dash", 1), t)
        p = gp(E, STEVE_DODGE.lerp(STEVE_SMASH, u))
        d = gp(E, STEVE_SMASH) - gp(E, STEVE_DODGE)
        yaw = lerp(math.degrees(math.atan2(d.x, -d.y)), 90.0, ss(b("dash", 1) - 0.25, b("dash", 1), t))
        if t < b("dash", 1):
            ph = (t - b("dash")) * 3.0 * 2 * math.pi
            pz.update({"foot_sl": {"y": -0.45 * math.sin(ph), "z": max(0.0, 0.3 * math.sin(ph + 1.2))},
                       "foot_sr": {"y": 0.45 * math.sin(ph), "z": max(0.0, 0.3 * math.sin(ph + 1.2 + math.pi))},
                       "chest_lean": 14, "arm_sl": {"fwd": -40 * math.sin(ph), "out": 10, "elbow": 60}})
            pz["arm_sr"] = {"fwd": 85, "out": 18, "elbow": 10}
        else:
            hit = b("smash") + 0.35
            up = ss(b("smash") - 0.05, hit - 0.12, t)
            down = ss(hit - 0.1, hit, t)
            rec = ss(hit + 0.05, hit + 0.5, t)
            pz["arm_sr"] = {"fwd": lerp(lerp(85, 175, up), 55, down) + 15 * rec, "out": 10, "elbow": lerp(lerp(0, 20, up), 5, down)}
            pz["arm_sl"] = {"fwd": lerp(20, 45, down), "out": 15, "elbow": 40}
            pz["chest_lean"] = lerp(lerp(-4, -12, up), 18, down) - 8 * rec
            pz["head_nod"] = 10 * down * (1 - rec)
        face = dict(SF["flat"])
        face.update({"bb_tilt": 0.55, "bb_raise": -0.15, "both_to": -0.1, "both_tm": -0.1, "m_arch": 0.15})
    elif t < b("noob_hi"):
        # the suck, the quiet: he staggers back a few steps, straightens up, breathes out; "...Never again.";
        # a glance up and left after
        st = ss(b("quiet") - 0.1, b("quiet") + 0.9, t)
        p = gp(E, STEVE_SMASH.lerp(STEVE_TIRED, st))
        if 0 < st < 1:
            ph = (t - b("quiet") + 0.1) * 1.4 * 2 * math.pi
            pz.update({"foot_sl": {"y": -0.22 * math.sin(ph), "z": max(0.0, 0.16 * math.sin(ph + 1.2))},
                       "foot_sr": {"y": 0.22 * math.sin(ph), "z": max(0.0, 0.16 * math.sin(ph + 1.2 + math.pi))}})
        d = gp(E, PORTAL) - p
        yp = math.degrees(math.atan2(d.x, -d.y))
        yaw = lerp(90.0, yp + 25, ss(b("suck") + 0.1, b("suck") + 0.8, t))
        yaw = lerp(yaw, 10.0, ss(b("quiet") + 0.2, b("quiet") + 1.0, t))      # he turns away from it, to us
        breath = math.sin(max(0.0, t - b("quiet")) * 2 * math.pi / 2.2)
        pz["chest_lean"] = 6 + 3 * breath
        pz["arm_sr"] = {"fwd": 8, "out": 10, "elbow": 10}
        pz["arm_sl"] = {"fwd": 5, "out": 8, "elbow": 10}
        pz["head_nod"] = 8 * ss(b("quiet"), b("quiet") + 0.8, t)
        face = dict(SF["flat"])
        face.update({"both_to": -0.5, "both_tm": -0.55, "both_ti": -0.45})
        if t >= b("steve_never", 1) + 0.9:
            nn = Vector(E.N.root.location) - p
            yn = math.degrees(math.atan2(nn.x, -nn.y))
            cc = Vector((-4.4, 1.8, 0)) - Vector((p.x, p.y, 0))
            yc = math.degrees(math.atan2(cc.x, -cc.y))
            # the Noob goes off behind him; he doesn't watch: worn out, he turns a little away and shuts his
            # eyes a moment, breathing
            k = ss(b("steve_never", 1) + 0.9, b("steve_never", 1) + 1.6, t)
            yaw = lerp(yaw, yc - 20, k)
            pz["head_nod"] = pz.get("head_nod", 0) + 6 * k
            face = dict(SF["flat"])
            face.update({"both_to": -0.9 * k, "both_tm": -0.95 * k, "both_ti": -0.9 * k})
        if b("steve_never", 1) + 0.15 <= t < b("steve_never", 1) + 0.9:
            k = ss(b("steve_never", 1) + 0.15, b("steve_never", 1) + 0.55, t)
            pz["head_turn"] = 18 * k
            pz["head_nod"] = 8 - 14 * k
            face = dict(SF["flat"])
        if b("suck") <= t < b("quiet"):
            face = dict(SF["stunned"])
    else:
        # worn out, he trudges over to lean by the oak, then watches the Noob wander off to the portal
        w0, w1 = b("noob_hi"), b("noob_hi") + 1.4
        u = ss(w0, w1, t)
        p = gp(E, STEVE_TIRED.lerp(STEVE_REST, u))
        dd = STEVE_REST - STEVE_TIRED
        n = Vector(E.N.root.location) - p
        yaw = lerp(math.degrees(math.atan2(dd.x, -dd.y)), math.degrees(math.atan2(n.x, -n.y)), ss(w1 - 0.3, w1 + 0.4, t))
        if 0 < u < 1:
            ph = (t - w0) * 1.3 * 2 * math.pi
            pz.update({"foot_sl": {"y": -0.25 * math.sin(ph), "z": max(0.0, 0.2 * math.sin(ph + 1.2))},
                       "foot_sr": {"y": 0.25 * math.sin(ph), "z": max(0.0, 0.2 * math.sin(ph + 1.2 + math.pi))}})
        pz["arm_sr"] = {"fwd": 8, "out": 10, "elbow": 10}
        pz["chest_lean"] = 6 + 2 * math.sin(t * 2.0)
        pz["head_nod"] = 6
        face = dict(SF["flat"])
        face.update({"both_to": -0.45, "both_tm": -0.5})
    M.set_steve(E, p, yaw, alive(pz, t, 21), face, t)


def noob(E, t):
    from ep09_new import NF
    _burst_reset(E)
    face = dict(NF["happy"])
    pz = {"arm_sl": {"out": 8}, "arm_sr": {"out": 8}}
    if t < b("steve_plan"):
        p = gp(E, NOOB0)
        c = E.crack_at - p
        yc = math.degrees(math.atan2(c.x, -c.y))
        s = gp(E, STEVE0) - p
        ys = math.degrees(math.atan2(s.x, -s.y))
        yaw = lerp(yc - 40, ys, ss(b("look_up") + 0.2, b("look_up") + 0.7, t))
        pz["head_nod"] = -26 * (1 - ss(b("look_up") + 0.2, b("look_up") + 0.7, t))
        # during the rule (off screen) he wanders to where he watches the building from
        w = ss(b("steve_rule") + 0.4, b("steve_rule", 1) + 0.4, t)
        if w > 0:
            p = gp(E, NOOB0.lerp(NOOB_WATCH, w))
            dd = NOOB_WATCH - NOOB0
            yaw = lerp(math.degrees(math.atan2(dd.x, -dd.y)), -25.0, ss(b("steve_rule", 1), b("steve_rule", 1) + 0.5, t))
        face = dict(NF["worried"]) if t < b("look_up") + 0.6 else dict(NF["neutral"])
    elif t < b("noob_this"):
        # he watches the building, delighted; then he wanders over to where the button appears
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
        look_btn = ss(7.9, 8.2, t) * (1 - ss(w0 - 0.2, w0, t))           # Steve points at it: he looks
        if look_btn > 0:
            bd = gp(E, PILLAR + Vector((0.5, 0.5, 0))) - p
            pz["head_turn"] = max(-60.0, min(60.0, _wrap(math.degrees(math.atan2(bd.x, -bd.y)) - yaw))) * look_btn
            pz["head_nod"] = -10 + 12 * look_btn
            face = dict(NF["happy"])
            face.update({"both_h": 1.5 + 0.3 * look_btn, "both_bm": 0.35})
    elif t < b("portal_open"):
        # "This one?": his hand over the button, the toy smile to us; the press
        p = gp(E, NOOB_BTN)
        yaw = -90.0 + 25 * (1 - ss(b("steve_dont"), b("steve_dont") + 0.2, t))
        hover = ss(b("noob_this"), b("noob_this") + 0.3, t)
        up = ss(b("press") - 0.3, b("press") - 0.08, t)                    # the wind-up
        down = ss(b("press") - 0.06, b("press") + 0.02, t)                 # the slam (lands on the click)
        bounce = math.exp(-((t - b("press") - 0.12) / 0.06) ** 2)
        pz["arm_sr"] = {"fwd": 75 * hover + 28 * up * (1 - down) - 14 * down + 6 * bounce, "out": -4}
        pz["chest_lean"] = 8 * down * (1 - ss(b("press") + 0.2, b("press") + 0.45, t))
        pz["head_turn"] = 28 * (1 - ss(b("steve_dont"), b("steve_dont") + 0.25, t))
        face = dict(NF["happy"])
        face.update({"both_h": 1.6})
    elif t < b("hit"):
        # the portal opens: he cheers
        p = gp(E, NOOB_BTN)
        d = gp(E, PORTAL) - p
        yp = math.degrees(math.atan2(d.x, -d.y))
        cy = math.degrees(math.atan2(1.6 - p.x, -(-8.6 - p.y)))
        yaw = lerp(-90.0, yp + _wrap(cy - yp) * 0.45, ss(b("portal_open"), b("portal_open") + 0.4, t))
        k = ss(b("portal_open") + 0.25, b("portal_open") + 0.5, t)
        bounce = abs(math.sin((t - b("portal_open")) * 7.0)) * (1 - ss(b("portal_open") + 1.2, b("portal_open") + 1.6, t))
        pz = {"arm_sl": {"out": 40 + 120 * k, "fwd": 10}, "arm_sr": {"out": 40 + 120 * k, "fwd": 10}, "chest_lean": -6 * k}
        p = p + Vector((0, 0, 0.1 * bounce * k))
        face = dict(NF["happy"])
        if t >= b("pour"):
            # each zombie that steps out gets a delighted point and a hop; his head follows it
            zs = [zombie_state(E, i, t) for i in range(3)]
            near = [z_ for z_ in zs if z_ is not None]
            hop = sum(math.exp(-((t - (b("pour") + 0.4 + 1.0 * i + 0.25)) / 0.12) ** 2) for i in range(3))
            pz = {"arm_sl": {"out": 60 + 25 * math.sin(t * 5.0), "fwd": 25}, "arm_sr": {"out": 40, "fwd": 70 + 20 * hop},
                  "head_nod": -4, "chest_lean": -4 * hop}
            if near:
                zd = near[-1]["p"] - p
                pz["head_turn"] = max(-60.0, min(60.0, _wrap(math.degrees(math.atan2(zd.x, -zd.y)) - yaw)))
            p = p + Vector((0, 0, 0.12 * hop))
            face = dict(NF["happy"])
            face.update({"both_h": 1.8, "m_o": 0.5, "both_bm": 0.3})
    elif t < b("respawn"):
        # the hit: he bursts
        p = gp(E, NOOB_BTN)
        d = gp(E, PORTAL) - p
        yaw = math.degrees(math.atan2(d.x, -d.y))
        face = dict(NF["shock"])
        pz = {"arm_sl": {"out": 70, "fwd": 20}, "arm_sr": {"out": 70, "fwd": 20}}
        M.set_noob(E, p, yaw, alive(pz, t, 7), face, t)
        _burst_apply(E, t - b("hit") - 0.03)
        return
    elif t < b("approach"):
        # the respawn on the pad: pops up, cheers; then watches the chaos from there
        p = E.pad_at.copy()
        dt = t - b("respawn")
        pop = ss(0.0, 0.15, dt)
        s = 0.4 + 0.6 * pop + 0.12 * math.sin(math.pi * min(1.0, dt / 0.25))
        d = gp(E, PORTAL) - p
        yaw = lerp(-15.0, math.degrees(math.atan2(d.x, -d.y)), ss(b("noob_fine", 1), b("noob_fine", 1) + 0.6, t))
        k = ss(b("noob_fine"), b("noob_fine") + 0.3, t) * (1 - ss(b("noob_fine", 1) + 0.2, b("noob_fine", 1) + 0.7, t))
        pz = {"arm_sl": {"out": 30 + 130 * k, "fwd": 10}, "arm_sr": {"out": 30 + 130 * k, "fwd": 10}, "chest_lean": -5 * k}
        face = dict(NF["happy"])
        face.update({"both_ps": 1.1})                                    # dazed: small pupils
        if t >= b("noob_fine", 1) + 0.5:
            face = dict(NF["awe"]) if t < b("suck", 1) else dict(NF["neutral"])
            # watching the chaos: body half to us, head on the nearest zombie, a cheer now and then, a flinch at
            # the lunge; at the suck he leans away from the pull, ducks with his arms over his head, then peeks
            cy = math.degrees(math.atan2(1.6 - p.x, -(-8.6 - p.y)))
            yaw = lerp(yaw, yaw + _wrap(cy - yaw) * 0.5, ss(b("noob_fine", 1), b("noob_fine", 1) + 0.6, t))
            zs = [zombie_state(E, i, t) for i in range(3)]
            near = [z_ for z_ in zs if z_ is not None]
            if near:
                zn = min(near, key=lambda z_: (z_["p"] - p).length)
                zd = zn["p"] - p
                pz["head_turn"] = max(-65.0, min(65.0, _wrap(math.degrees(math.atan2(zd.x, -zd.y)) - yaw)))
            cheer = max(0.0, math.sin((t - b("chaos")) * 2.6)) * ss(b("chaos"), b("chaos") + 0.3, t) * (1 - ss(b("suck") - 0.3, b("suck"), t))
            flinch = math.exp(-((t - (b("chaos") + 1.45)) / 0.15) ** 2)
            duck = ss(b("suck") + 0.1, b("suck") + 0.5, t) * (1 - ss(b("suck", 1) - 0.4, b("suck", 1) + 0.3, t))
            pull = ss(b("suck"), b("suck") + 0.2, t) * (1 - duck)
            pz = {"arm_sl": {"out": 30 + 100 * cheer + 40 * pull * math.sin(t * 13), "fwd": 10 + 150 * duck},
                  "arm_sr": {"out": 30 + 100 * cheer - 20 * flinch + 40 * pull * math.sin(t * 11 + 1), "fwd": 10 + 40 * flinch + 150 * duck},
                  "chest_lean": -6 * cheer + 10 * flinch + 25 * duck - 10 * pull, "head_turn": pz.get("head_turn", 0) * (1 - duck),
                  "head_nod": 20 * duck}
            face = dict(NF["happy"]) if cheer > 0.3 else dict(NF["awe"])
            if flinch > 0.3:
                face = dict(NF["shock"])
            if duck > 0.2:
                face = dict(NF["scared"])
            if t >= b("suck", 1):
                face = dict(NF["neutral"])
        M.set_noob(E, p, yaw, alive(pz, t, 7), face, t)
        sc = E.noob_scale0 * s
        E.N.root.scale = (sc, sc, sc)
        return
    elif t < b("noob_hi"):
        # he wanders to the dark portal, curious; he notices something inside
        u = ss(b("approach"), b("approach", 1) - 0.4, t)
        p = E.pad_at.lerp(gp(E, NOOB_PORTAL), u)
        p.z = E.ground(p.x, p.y)
        d = gp(E, NOOB_PORTAL) - E.pad_at
        yaw = lerp(math.degrees(math.atan2(d.x, -d.y)), 165.0, ss(b("approach", 1) - 0.6, b("approach", 1), t))
        if u < 1:
            ph = (t - b("approach")) * 1.25 * 2 * math.pi
            sw = math.sin(ph) * (1 - ss(b("approach", 1) - 0.6, b("approach", 1) - 0.4, t))
            pz.update({"arm_sl": {"fwd": -22 * sw}, "arm_sr": {"fwd": 22 * sw}, "leg_sl": {"fwd": 24 * sw},
                       "leg_sr": {"fwd": -24 * sw}})
            p += Vector((0, 0, 0.03 * abs(sw)))
        pz["head_tilt"] = 12 * ss(b("approach", 1) - 0.5, b("approach", 1), t)
        face = dict(NF["confused"]) if t > b("approach", 1) - 0.5 else dict(NF["neutral"])
    else:
        # "Hi!": he waves at it; it waves back; "...Steve? It waved back." (he turns to us, uneasy); the snap
        p = gp(E, NOOB_PORTAL)
        pc = gp(E, PORTAL) - p
        y_portal = math.degrees(math.atan2(pc.x, -pc.y))
        mc = MIRROR_CAM - p
        y_side = y_portal + 0.3 * _wrap(math.degrees(math.atan2(mc.x, -mc.y)) - y_portal)   # half to us
        wc = WAVED_CAM - p
        y_cam = math.degrees(math.atan2(wc.x, -wc.y))
        a_, c_ = b("noob_waved") - 0.35, b("noob_waved") + 0.55
        yaw = y_side + _wrap(y_cam - y_side) * ss(a_, c_, t)
        head_lead = _wrap(y_cam - y_side) * (ss(a_ - 0.15, c_ - 0.25, t) - ss(a_, c_, t))
        if a_ < t < c_:
            pz.update({"leg_sl": {"fwd": 14 * math.sin(math.pi * ss(a_ + 0.1, a_ + 0.45, t))},
                       "leg_sr": {"fwd": 14 * math.sin(math.pi * ss(a_ + 0.4, a_ + 0.75, t))}})
        wave = ss(b("noob_hi") - 0.15, b("noob_hi") + 0.1, t) * (1 - 0.5 * ss(b("mirror") + 1.2, b("mirror") + 2.2, t))
        wv = math.sin((t - b("noob_hi")) * 9.0) * (1 - ss(b("mirror") + 0.8, b("mirror") + 1.4, t))
        pz["arm_sr"] = {"out": 150 * wave + 10 * wv * wave, "fwd": 10}
        if t >= b("snap"):
            pz["arm_sr"] = {"out": 75, "fwd": 10}                         # frozen, arm still half up
        face = dict(NF["happy"]) if t < b("mirror") + 0.8 else dict(NF["confused"])
        if t >= b("noob_waved"):
            face = dict(NF["worried"])
        if t >= b("snap"):
            face = dict(NF["shock"])
            face.update({"m_o": 0.3})
        pz["head_turn"] = head_lead + (-22.0) * (1 - ss(a_, c_, t)) * ss(b("noob_hi") - 0.3, b("noob_hi"), t)
    M.set_noob(E, p, yaw, alive(pz, t, 7), face, t)


def _burst_reset(E):
    if not hasattr(E, "noob_scale0"):
        E.noob_scale0 = E.N.root.scale[0]
    E.N.root.scale = (E.noob_scale0,) * 3
    for k, o in E.burst_parts.items():
        loc, mode, q = E.burst_home[k]
        o.location = loc
    E.dark_cube.location = (0, 0, -300)
    E.N.root.hide_render = False
    for ob in E.N.root.children_recursive:
        ob.hide_render = False


def _burst_apply(E, dt):
    if dt < 0:
        return
    k = E.N.root.scale[0]
    for name, o in E.burst_parts.items():
        loc, mode, q = E.burst_home[name]
        v = E.burst_v[name] * 9.0
        o.location = loc + Vector((v.x * dt, v.y * dt, v.z * dt - 0.5 * 9.81 / k * dt * dt * 0.6))
        o.rotation_quaternion = Quaternion(q) @ Quaternion(Vector((1, 0.4, 0.2)).normalized(), 9.0 * dt * (1 if name < "n" else -1))
    hide = dt > 0.55
    for ob in E.N.root.children_recursive:
        ob.hide_render = hide
    c = Vector(E.N.root.location) + Vector((0, 0, 1.2))
    if dt < 0.75:
        # Null's cell: it hangs a moment in the burst, turning, toward us, then is gone (not explained)
        toward = Vector((0.76, -0.64, 0)) * 0.35 * ss(0.0, 0.2, dt)
        E.dark_cube.location = c + toward + Vector((0, 0, 0.1 * dt - 0.4 * dt * dt))
        E.dark_cube.rotation_euler = (dt * 2, dt * 3.5, dt * 1.5)
        s = min(1.0, dt / 0.06) * (1 - ss(0.55, 0.75, dt))
        E.dark_cube.scale = (s, s, s)


def hit_cube(E, t):
    t1 = b("hit") + 0.03
    t0 = t1 - 0.5
    ob = E.hit_cube
    if not (t0 <= t < t1 + 0.6):
        ob.location = (0, 0, -300)
        return
    mouth = portal_mouth(E)
    tgt = gp(E, NOOB_BTN) + Vector((0, 0, 1.3))
    if t < t1:
        u = (t - t0) / (t1 - t0)
        ob.location = mouth.lerp(tgt, u) + Vector((0, 0, 1.2 * math.sin(math.pi * u)))
        ob.rotation_euler = (u * 7, u * 4, 0)
    else:
        dt = t - t1
        land = tgt + Vector((1.0, -0.6, 0))
        land.z = E.ground(land.x, land.y) + 0.21
        p = tgt + Vector((1.6 * dt, -1.0 * dt, 2.0 * dt - 4.9 * dt * dt))
        p.z = max(p.z, land.z)
        ob.location = p
        ob.rotation_euler = (7 + dt * 5, 4, 0)


def figure(E, t):
    """The figure in the room behind the dark surface: it waves back; it walks closer."""
    F = E.fig
    if not (b("noob_hi") <= t < b("snap") + 0.04):
        F.root.location = (0, 0, -300)
        return
    root = gp(E, PORTAL)
    depth = lerp(5.0, 1.6, ss(b("noob_waved") + 0.6, b("snap") - 0.1, t))
    F.root.location = root + Vector((-0.4, depth, 1.0 - 0.05))
    F.root.rotation_euler = (0, 0, 0)                                  # facing out of the portal, toward -y
    wave = ss(b("mirror") - 0.1, b("mirror") + 0.6, t)
    wv = math.sin((t - b("mirror")) * 4.5)
    if hasattr(F, "arms") and "sr" in F.arms:
        F.arms["sr"].rotation_mode = "XYZ"
        F.arms["sr"].rotation_euler = (0, math.radians(-(120 * wave + 18 * wv * wave)), 0)
    sway = 0.04 * math.sin(t * 3.0) if t > b("noob_waved") + 0.6 else 0.0
    F.root.location += Vector((sway, 0, 0))


def apply(E, t):
    from ep09_new import NF, SF  # noqa: F401
    name, t0, t1 = which(t)
    light(E, t)
    portal(E, t)
    pad(E, t)
    junk(E, t)
    zombies(E, t)
    hit_cube(E, t)
    figure(E, t)
    steve(E, t)
    noob(E, t)
    camera(E, t, name, t0, t1)


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
    if shot == "react":
        # the camera stands by the portal: its violet would light their faces head-on (an orange Noob, a pink
        # Steve). Keep a violet rim, the faces in their own colours
        E.PP.light.data.energy *= 0.2
        E.key.data.energy *= 1.4


def _wide(E, t, t0, t1, lens=20):
    """The wide on the portal, the meadow, the button and the pad (shots 7, 10, 14)."""
    c = Vector((-1.2, 0.6, E.ground(-1.2, 0.6) + 2.6))
    loc = Vector((1.6, -8.6, E.ground(1.6, -8.6) + 1.3))
    return loc, c, lens


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus or None, handheld)"""
    u = ss(t0, t1, t) if t1 < 1e8 else 0.0
    if shot == "eye":
        # chapter 1's last angle exactly: the crack framed wide, the eye in it looking round
        sp = gp(E, STEVE0)
        d = (E.crack_at - sp)
        d = Vector((d.x, d.y, 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        loc = sp + d * 1.6 - side * 1.8 + Vector((0, 0, 1.8))
        loc = loc.lerp(E.crack_at, 0.06 * ss(0.0, 2.1, t))           # a slow push in on the eye (from chapter 1's frame)
        snap = b("eye") + 2.1
        return loc, E.crack_at, 28, 64.0, None, 0.04 + 0.5 * math.exp(-((t - snap - 0.03) / 0.08) ** 2)
    if shot == "lookup":
        # the two still staring up under the floating oak, then at each other
        c = Vector((-0.6, 1.0, E.ground(-0.6, 1.0) + 1.7))
        loc = Vector((-4.6, -0.2, E.ground(-4.6, -0.2) + 0.6))
        return loc, c, 22, 64.0, None, 0.04
    if shot == "rule":
        # Steve chest-up at the right third, the meadow and the floating oak soft behind him
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE0) + Vector((-1.0, -2.6, 1.78))           # at his eye height: his eyes on us
        return loc, hs + Vector((-0.45, 0, -0.18)), 36, 2.8, None, 0.05
    if shot == "build":
        # low and wide: the frame rising block by block, Steve placing, the button's stone at the right
        c = Vector((-3.4, 2.7, E.ground(-3.4, 2.7) + 2.6))
        loc = gp(E, BUILD_CAM) + Vector((0, 0, 1.2)) + Vector((-0.3, 0.4, 0)) * u
        c = Vector((-1.2, 2.2, E.ground(-1.2, 2.2) + 2.6))
        return loc, c, 20, 64.0, None, 0.04
    if shot == "this":
        # the Noob and the button, low and close; the empty frame behind
        hn = M.P6._head(E.N.face)
        c = hn.lerp(gp(E, PILLAR + Vector((0.5, 0.5, 0))) + Vector((0, 0, 1.0)), 0.45)
        loc = Vector((-0.2, -2.0, c.z - 0.35))
        return loc, c, 28, 3.2, None, 0.05
    if shot == "dont":
        # Steve medium, his arm shooting out toward the Noob (off frame right)
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE_DONT) + Vector((0.6, -2.8, 1.35))
        return loc, hs + Vector((0.3, -0.3, -0.45)), 30, 3.2, None, 0.08
    if shot == "press":
        # the insert: the hand coming down on the button
        top = gp(E, PILLAR + Vector((0.5, 0.5, 0))) + Vector((0, 0, 1.08))
        # from the side, at button height: the whole button, the hand slamming down on it
        loc = top + Vector((-0.9, -1.7, 0.2))
        jolt = 0.1 + 0.9 * math.exp(-((t - b("press") - 0.03) / 0.05) ** 2)
        return loc, top + Vector((0.1, 0.0, 0.18)), 40, 5.0, None, jolt
    if shot in ("open", "chaos", "suck"):
        loc, c, lens = _wide(E, t, t0, t1)
        if shot == "open":
            loc = loc + Vector((0.0, 0.5, 0.0)) * u
        if shot == "chaos":
            return loc, c, lens, 64.0, None, 0.25
        sh = 0.06 + (0.6 * math.exp(-((t - b("portal_open") - 0.08) / 0.15) ** 2) if shot == "open" else 0.3)
        return loc, c, lens, 64.0, None, sh
    if shot == "react":
        # their faces as the zombies come out: from the portal's right side, the two of them looking at it,
        # a zombie shuffling past at the side of the frame
        mid = 0.5 * (gp(E, STEVE_DONT) + gp(E, NOOB_BTN))
        loc = Vector((1.0, 3.4, E.ground(1.0, 3.4) + 1.45))
        return loc, mid + Vector((0, 0, 1.2)), 24, 64.0, None, 0.08
    if shot == "hit":
        # side on, the Noob in the middle: the cube flies in from the portal and smacks him; his parts fly
        n = gp(E, NOOB_BTN)
        loc = n + Vector((0.4, 2.7, 1.45))
        return loc, n + Vector((-0.1, 0, 1.15)), 24, 64.0, None, 0.08 + 0.6 * math.exp(-((t - b("hit") - 0.15) / 0.1) ** 2)
    if shot == "respawn":
        # the pad, low: the Noob pops in, arms up
        pd = E.pad_at
        loc = pd + Vector((-1.0, -3.6, 0.6))
        return loc, pd + Vector((0.1, 0, 1.1)), 26, 4.0, None, 0.05
    if shot == "planb":
        # Steve chest-up at the right, the portal swirling at the left of the frame
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE_DODGE) + Vector((2.0, -1.0, 1.45))
        return loc, hs + Vector((-0.3, 0.4, -0.25)), 30, 3.2, None, 0.12
    if shot == "dash":
        # he dashes across the frame toward the button, the portal swirling behind him
        # he charges toward us at the button, the portal swirling behind him
        s = Vector(E.S.holder.location)
        loc = Vector((0.4, 2.0, E.ground(0.4, 2.0) + 1.4))
        return loc, s + Vector((0.0, 0, 1.2)), 24, 64.0, None, 0.15
    if shot == "smash":
        # low past the button up at him; the sun behind him
        # side on from the south: Steve at the left, the button at the right, the pickaxe's whole arc in frame
        hit = b("smash") + 0.35
        loc = Vector((0.2, -3.6, E.ground(0.2, -3.6) + 1.2))
        look = Vector((0.15, -0.55, E.ground(0.15, -0.55) + 1.45))
        return loc, look, 24, 64.0, None, 0.08 + 1.0 * math.exp(-((t - hit - 0.05) / 0.12) ** 2)
    if shot == "quiet":
        # the meadow settling; the dark portal; Steve breathing out at the right
        c = Vector((-2.0, 1.8, E.ground(-2.0, 1.8) + 2.2))
        loc = Vector((-0.8, -6.6, E.ground(-0.8, -6.6) + 1.0))
        return loc, c, 24, 64.0, None, 0.03
    if shot == "never":
        # Steve centre-right, tired; the dark portal at the left behind him
        hs = M.P6._head(E.S.face, E.S.holder)
        loc = gp(E, STEVE_TIRED) + Vector((0.6, -2.8, 1.45))
        return loc, hs + Vector((-0.6, 0, -0.35)), 30, 3.2, None, 0.04
    if shot == "approach":
        # the Noob wandering up to the dark portal
        n = Vector(E.N.root.location)
        # tracking ahead of him, at his right: his face as he wanders up to the portal; Steve by the oak behind
        d = gp(E, NOOB_PORTAL) - E.pad_at
        d = Vector((d.x, d.y, 0)).normalized()
        left = Vector((-d.y, d.x, 0))
        # from by the portal's right side, looking back down his way: he comes toward us, Steve resting at the side
        loc = Vector((-4.4, 1.8, E.ground(-4.4, 1.8) + 1.3))
        return loc, n + Vector((0, 0, 1.1)), 26, 64.0, None, 0.04
    if shot == "mirror":
        # from the front-right, low: the dark portal filling the right; the Noob at the left waving
        # from the front-left, low: the dark portal at the left, the Noob at its right waving into it
        n = gp(E, NOOB_PORTAL)
        loc = Vector((MIRROR_CAM.x, MIRROR_CAM.y, E.ground(MIRROR_CAM.x, MIRROR_CAM.y) + 1.4))
        c = gp(E, PORTAL) + Vector((0.0, 0, 2.4))
        return loc, c.lerp(n + Vector((0, 0, 1.3)), 0.5), 22, 64.0, None, 0.03
    if shot == "waved":
        # the Noob three-quarter to us at the left, the portal filling the right two-thirds; the figure closer
        # the Noob three-quarter to us at the right, the portal filling the left; the figure closer
        # closer now: the Noob turning to us at the right, the dark portal behind at the left, the figure nearer
        n = gp(E, NOOB_PORTAL)
        loc = gp(E, WAVED_CAM) + Vector((0, 0, 1.45))
        hn = M.P6._head(E.N.face)
        c = gp(E, PORTAL) + Vector((0.4, 0, 2.2))
        return loc, c.lerp(hn, 0.6), 28, 4.0, (hn - loc).length, 0.03
    if shot == "snap":
        # the flash and the snap; then the empty frame, the quiet meadow seen through it, the Noob frozen
        n = gp(E, NOOB_PORTAL)
        loc = Vector((-3.6, -5.4, E.ground(-3.6, -5.4) + 1.8))
        c = gp(E, PORTAL) + Vector((-0.6, 0, 2.6))
        return loc, c, 24, 64.0, None, 0.04 + 0.7 * math.exp(-((t - b("snap") - 0.05) / 0.1) ** 2)
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
    E.cuts = sorted(t0 for _, t0 in shot_bounds()) + [b("hit") + 0.12, b("smash") + 0.35, b("snap") + 0.04]
    M._render(E, frames, out, apply, M.finish_forest)


if __name__ == "__main__":
    main()
