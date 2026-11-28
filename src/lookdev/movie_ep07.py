"""The movie, chapter 7 ("Patch Remembered Another World": the Memory Grid), in the new look and in 16:9.

The creator's blueprint and fixes (2026-11-27, story/movie/ep07_shots.md). It picks up Ep6's last instant: the
cyan-white flash of Patch's emergency warp. The flash fades down onto the Memory Grid: an endless translucent blue
floor of glowing cyan lines over fainter layers below, in deep navy-cyan fog. Steve (empty-handed), the Noob (no
hammer) and Patch tumble out of the warp. A hologram of the Noob dies on a red kill-brick and leaves a dark cube
behind each time; the cubes rain down into a dark corrupted core far below (no figure, no face: Null stays unseen);
the recorded past loop; the infinite pullback over hundreds of varied cells, each with its void fissure; Patch's
"...I stopped counting."; "I don't want to be deleted."; the void cracks the archive (REALITY 52 -> 30) and Patch
warps them out (a white-cyan flash into Ep8). Sound and timing: episodes/movie_ep07_another_world.json (movie/ep07).

    python src/lookdev/movie_ep07.py TIMELINE VOICE TEX_DIR ASSETS OUT_DIR [--times 1.0,5.0] [--res 720]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import movie_ep00 as M                                                # noqa: E402
import movie_ep02 as E2                                               # noqa: E402
import movie_ep03 as E3                                               # noqa: E402
import movie_ep06 as E6                                               # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402

B = M.B
_yaw, _wrap, _clamp = E2._yaw, E2._wrap, E2._clamp
life = E2.life
_face_to, _look, _run = E3._face_to, E3._look, E3._run
EP6_TL = os.path.join(HERE, "..", "..", "movie", "ep06", "timeline.json")
FAR = Vector((0, 0, -900))


def b(name, i=0):
    return B[name][i]


def _hash(*a):
    return E6._hash(*a)


# ------------------------------------------------------------------ the place (metres, z up; the cameras look +y)
S_LAND = Vector((-0.9, -0.3, 0.0))       # Steve lands (one knee), facing +y
N_LAND = Vector((0.9, -0.1, 0.0))        # the Noob lands flat on his back
P_HOME = Vector((0.15, 0.75, 2.55))         # Patch steadies here
S_STAND = Vector((-1.0, 0.2, 0.0))       # Steve after he rises
N_STAND = Vector((0.7, 0.4, 0.0))        # the Noob after he hops up
PAD_R = Vector((3.6, 3.6, 0.0))          # the replay pad
GHOST0 = PAD_R + Vector((0.0, -1.7, 0.0))  # the ghost spawns here, walks +y
BRICK = PAD_R + Vector((0.0, 0.9, 0.0))  # the red kill-brick
CUBES = [PAD_R + Vector((-0.55, 1.75, 0.0)), PAD_R + Vector((0.5, 1.6, 0.0)), PAD_R + Vector((0.0, 2.25, 0.0))]
N_EDGE = Vector((2.0, 1.6, 0.0))         # the Noob leans over the pad's edge ("...Where does it go?")
CORE = Vector((5.0, 9.0, -30.0))         # the dark core far below
CELL_P = Vector((-6.5, 8.0, 0.0))        # the recorded past loop
FISSURE_P = CELL_P + Vector((0.6, 3.2, 0.0))
CUBE_S = 0.34
P_WEIGHT = Vector((-0.6, 2.2, 2.4))
P_BREACH = Vector((-0.3, -0.3, 2.3))   # Patch in the breach: in front of them, high, clear of the Noob's arms   # Patch for '...I stopped counting.' (clear of them)
LOOK_OUT = Vector((10.0, 12.0, 0.5))   # where the Noob looks out over the ghosts


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    t6 = json.load(open(EP6_TL))
    E = E6.build(t6, tex_dir, assets, res, samples)               # the rigs, Patch, the lens wash (cyan), the warp
    E.B7 = {k: tuple(v) for k, v in tl["beats"].items()}
    E.T6 = t6["length"]
    _hide_world(E)
    E_COL[0] = E.sc.collection
    _sky(E)
    _floor(E)
    _pads(E)
    _brick(E)
    _cubes(E)
    _core(E)
    _snow(E)
    _ghost(E)
    _fissure_mesh(E)
    _cracks(E)
    _lights(E)
    _patch_screen(E)
    E.prepped7 = False
    return E


def _use(E):
    B.clear()
    B.update(E.B7)


def _top(o):
    while o.parent:
        o = o.parent
    return o


def _hide_world(E):
    """Nothing of the obby comes along: only the three of them, the camera and its lens wash, the warp."""
    keep = {E.S.holder, E.N.root, E.PA.root, E.cam}
    rig = set(E.S.rig.all_objects) if hasattr(E.S.rig, "all_objects") else set()
    sw, sr, sl = E.warp6
    for ob in bpy.data.objects:
        if ob in rig or _top(ob) in keep or ob in (sw, sr, sl):
            continue
        ob.hide_render = True
        ob.hide_viewport = True
    for ob in list(E.ham_parts) + [E.ham, getattr(E, "ham_light", None)] + [o for o in bpy.data.objects if o.name.startswith("hammer")]:
        if ob is not None:
            ob.hide_render = True
            ob.hide_viewport = True
    for ob in bpy.data.objects:                                   # Steve's pickaxe: erased in Ep6
        if ob.name.startswith("item_"):
            ob.hide_render = True
            ob.hide_viewport = True
    E.PA.beam.hide_render = True


def _nt(m):
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    return nt


def _hex(h):
    c = tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


HORIZON = _hex("#0A2438")
ZENITH = _hex("#030B14")


def _sky(E):
    """A deep abyssal blue-teal: dark overhead, the cyan-navy mist at the horizon (the far grid fades into it)."""
    w = bpy.data.worlds.new("memory_world")
    nt = _nt(w)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.15
    mr.inputs["From Max"].default_value = 0.55
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*HORIZON, 1)
    ramp.color_ramp.elements[1].color = (*ZENITH, 1)
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    w.mist_settings.start = 5.0
    w.mist_settings.depth = 85.0
    w.mist_settings.falloff = "QUADRATIC"
    E.sc.world = w
    E.sky_bg = bg.inputs["Strength"]


def _grid_mat(name, strength, step=3.0, width=0.035, tint=1.0, base=0.06):
    """A floor of glowing cyan grid lines (every `step` m) on faint translucent blue glass."""
    m = bpy.data.materials.new(name)
    nt = _nt(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    lines = []
    for ax in ("X", "Y"):
        d = nt.nodes.new("ShaderNodeMath")
        d.operation = "DIVIDE"
        nt.links.new(sep.outputs[ax], d.inputs[0])
        d.inputs[1].default_value = step
        fr = nt.nodes.new("ShaderNodeMath")
        fr.operation = "PINGPONG"
        nt.links.new(d.outputs[0], fr.inputs[0])
        fr.inputs[1].default_value = 0.5
        ln = nt.nodes.new("ShaderNodeMath")
        ln.operation = "LESS_THAN"
        nt.links.new(fr.outputs[0], ln.inputs[0])
        ln.inputs[1].default_value = width / step
        lines.append(ln)
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    nt.links.new(lines[0].outputs[0], mx.inputs[0])
    nt.links.new(lines[1].outputs[0], mx.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.15 * tint, 0.85 * tint, 1.0 * tint, 1)
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "MULTIPLY_ADD"
    nt.links.new(mx.outputs[0], st.inputs[0])
    st.inputs[1].default_value = strength
    st.inputs[2].default_value = base
    nt.links.new(st.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.75, 0.9, 1.0, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (0.4, 0.8, 1.0, 1)
    gl.inputs["Roughness"].default_value = 0.08
    fr_ = nt.nodes.new("ShaderNodeLayerWeight")
    fr_.inputs["Blend"].default_value = 0.2
    m1 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr_.outputs["Fresnel"], m1.inputs[0])
    nt.links.new(tr.outputs[0], m1.inputs[1])
    nt.links.new(gl.outputs[0], m1.inputs[2])
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(m1.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    return m, st


def _plane(name, size, z, mat, cut=None):
    bpy.ops.mesh.primitive_plane_add(size=size)
    ob = bpy.context.active_object
    ob.name = name
    ob.location = (0, 0, z)
    ob.data.materials.append(mat)
    ob.visible_shadow = False
    return ob


def _floor(E):
    m, st = _grid_mat("mg_floor", 4.0, step=3.0, width=0.06, base=0.0)
    E.floor = _plane("mg_floor", 600, 0.0, m)
    E.floor_em = st
    E.layers = []
    for i, (z, s, step) in enumerate(((-9.0, 1.4, 6.0), (-19.0, 0.9, 9.0), (-34.0, 0.6, 12.0))):
        mi, sti = _grid_mat(f"mg_layer{i}", s, step=step, width=0.06 * (i + 1), tint=0.8, base=0.02)
        E.layers.append((_plane(f"mg_layer{i}", 600, z, mi), sti))


def _glass_mat(name, edge=(0.2, 0.9, 1.0), strength=2.5, alpha=0.18):
    """The memory pads: thin glass (IOR 1.15) with a clean Fresnel edge glow."""
    m = bpy.data.materials.new(name)
    nt = _nt(m)
    gs = nt.nodes.new("ShaderNodeBsdfGlass")
    gs.inputs["IOR"].default_value = 1.15
    gs.inputs["Roughness"].default_value = 0.05
    gs.inputs["Color"].default_value = (0.7, 0.92, 1.0, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = alpha
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gs.outputs[0], mx.inputs[2])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.12
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*edge, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(lw.outputs["Fresnel"], mul.inputs[0])
    mul.inputs[1].default_value = strength
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mx.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    return m


def _wire_mat(name, rgb=(0.3, 0.95, 1.0), strength=5.0):
    m, _, em = E3._emit_mat(name, rgb, strength)
    return m, em


def _box_mesh(name, size):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    return me


def _slab(name, size, loc, mat, wire=None, col=None):
    """A box (its size in the mesh, scale 1); `wire`: a thin glowing border (its edges as a 2.5 cm wireframe)."""
    col = col or E_COL[0]
    ob = bpy.data.objects.new(name, _box_mesh(name, size))
    ob.location = loc
    ob.data.materials.append(mat)
    ob.visible_shadow = False
    col.objects.link(ob)
    w = None
    if wire is not None:
        w = bpy.data.objects.new(name + "_wire", ob.data.copy())
        w.data.materials.clear()
        w.data.materials.append(wire)
        w.location = loc
        md = w.modifiers.new("wire", "WIREFRAME")
        md.thickness = 0.025
        md.use_relative_offset = False
        md.use_even_offset = True
        w.visible_shadow = False
        col.objects.link(w)
    return ob, w


E_COL = [None]


def _pads(E):
    E.pad_mat = _glass_mat("mg_pad")
    E.pad_wire, E.pad_wire_em = _wire_mat("mg_pad_wire", rgb=(0.2, 0.85, 1.0), strength=2.5)
    E.pad_a = _slab("mg_pad_a", (5.0, 4.4, 0.18), (0, 0.1, -0.09), E.pad_mat, E.pad_wire)
    E.pad_r = _slab("mg_pad_r", (2.6, 6.2, 0.18), PAD_R + Vector((0, 0.4, -0.09)), E.pad_mat, E.pad_wire)
    E.pad_p = _slab("mg_pad_p", (5.0, 5.0, 0.18), CELL_P + Vector((0, 1.0, -0.09)), E.pad_mat, E.pad_wire)
    # a few empty pads around them (the archive goes on)
    E.pad_deco = []
    for i, (x, y, z) in enumerate(((-9.5, -1.0, -0.6), (9.5, 9.0, -0.4), (-2.0, 14.0, 0.8), (12.0, -2.0, 0.3))):
        E.pad_deco.append(_slab(f"mg_pad_d{i}", (4.0, 4.0, 0.18), (x, y, z), E.pad_mat, E.pad_wire))


def _brick(E):
    m = bpy.data.materials.new("mg_killbrick")
    nt = _nt(m)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.08, 0.1, 1)
    em.inputs["Strength"].default_value = 1.6
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.45
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    E.brick_em = em.inputs["Strength"]
    E.brick, _ = _slab("mg_killbrick", (1.6, 1.0, 0.14), BRICK + Vector((0, 0, 0.07)), m)


def _dark_mat(name):
    """Pitch-black, glossy, a faint scatter of stars inside (the residue of a respawn)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.004, 0.003, 0.008, 1)
    bs.inputs["Roughness"].default_value = 0.55
    for nm in ("Specular IOR Level", "Specular"):
        if nm in bs.inputs:
            bs.inputs[nm].default_value = 0.15
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 28.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    nt.links.new(vo.outputs["Distance"], lt.inputs[0])
    lt.inputs[1].default_value = 0.06
    mu = nt.nodes.new("ShaderNodeMix")
    mu.data_type = "RGBA"
    nt.links.new(lt.outputs[0], mu.inputs[0])
    mu.inputs[6].default_value = (0, 0, 0, 1)
    mu.inputs[7].default_value = (0.8, 0.5, 1.0, 1)
    nt.links.new(mu.outputs[2], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 2.0
    lw = nt.nodes.new("ShaderNodeLayerWeight")                 # a faint magenta rim: it reads on the navy
    lw.inputs["Blend"].default_value = 0.08
    rim = nt.nodes.new("ShaderNodeMix")
    rim.data_type = "RGBA"
    rim.blend_type = "ADD"
    nt.links.new(lw.outputs["Fresnel"], rim.inputs[0])
    nt.links.new(mu.outputs[2], rim.inputs[6])
    rim.inputs[7].default_value = (0.25, 0.02, 0.2, 1)
    nt.links.new(rim.outputs[2], bs.inputs["Emission Color"])
    return m


def _cube(name, mat, s=CUBE_S):
    bpy.ops.mesh.primitive_cube_add(size=s)
    ob = bpy.context.active_object
    ob.name = name
    bv = ob.modifiers.new("bevel", "BEVEL")
    bv.width = 0.012
    bv.segments = 2
    ob.data.materials.append(mat)
    ob.location = FAR
    return ob


def _cubes(E):
    E.dark = _dark_mat("mg_dark")
    E.res_cubes = [_cube(f"mg_residue{i}", E.dark) for i in range(3)]


def _crack_mat(name):
    """Black corrupted blocks with faint magenta cracks glowing inside."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.003, 0.002, 0.006, 1)
    bs.inputs["Roughness"].default_value = 0.7
    for nm in ("Specular IOR Level", "Specular"):
        if nm in bs.inputs:
            bs.inputs[nm].default_value = 0.1
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 1.3
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    nt.links.new(vo.outputs["Distance"], lt.inputs[0])
    lt.inputs[1].default_value = 0.02
    nz = nt.nodes.new("ShaderNodeTexNoise")                         # cracks only here and there
    nz.inputs["Scale"].default_value = 1.6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    nt.links.new(nz.outputs["Fac"], gt.inputs[0])
    gt.inputs[1].default_value = 0.56
    both = nt.nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    nt.links.new(lt.outputs[0], both.inputs[0])
    nt.links.new(gt.outputs[0], both.inputs[1])
    mu = nt.nodes.new("ShaderNodeMix")
    mu.data_type = "RGBA"
    nt.links.new(both.outputs[0], mu.inputs[0])
    mu.inputs[6].default_value = (0, 0, 0, 1)
    mu.inputs[7].default_value = (1.0, 0.1, 0.75, 1)
    nt.links.new(mu.outputs[2], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 8.0
    E_ = bs.inputs["Emission Strength"]
    return m, E_


N_CORE = 260


def _core(E):
    """The churning core: a dense swirl of pitch-black corrupted blocks, magenta cracks pulsing; no figure."""
    E.core_mat, E.core_em = _crack_mat("mg_core")
    me = bpy.data.meshes.new("mg_core_block")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(E.core_mat)
    r = random.Random(7)
    E.core_blocks = []
    for i in range(N_CORE):
        ob = bpy.data.objects.new(f"mg_core{i}", me)
        E.sc.collection.objects.link(ob)
        rad = 5.0 * r.random() ** 0.6
        E.core_blocks.append((ob, rad, r.uniform(0, 2 * math.pi), r.uniform(-1, 1), r.uniform(0.25, 0.9),
                              r.uniform(0.3, 1.0), r.uniform(0, 6.3)))
        ob.location = FAR
    # a glow at its heart: the black blocks read as a swirl against it
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2.6, segments=32, ring_count=16)
    gl = bpy.context.active_object
    gl.name = "mg_core_glow"
    gm = bpy.data.materials.new("mg_core_glow")
    gnt = _nt(gm)
    lw = gnt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inv = gnt.nodes.new("ShaderNodeMath")
    inv.operation = "POWER"
    fr = gnt.nodes.new("ShaderNodeMath")
    fr.operation = "SUBTRACT"
    fr.inputs[0].default_value = 1.0
    nt_link = gnt.links.new
    nt_link(lw.outputs["Facing"], fr.inputs[1])
    nt_link(fr.outputs[0], inv.inputs[0])
    inv.inputs[1].default_value = 4.0
    em = gnt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.1, 0.7, 1)
    em.inputs["Strength"].default_value = 1.6
    tr = gnt.nodes.new("ShaderNodeBsdfTransparent")
    mx = gnt.nodes.new("ShaderNodeMixShader")
    nt_link(inv.outputs[0], mx.inputs[0])
    nt_link(tr.outputs[0], mx.inputs[1])
    nt_link(em.outputs[0], mx.inputs[2])
    out = gnt.nodes.new("ShaderNodeOutputMaterial")
    nt_link(mx.outputs[0], out.inputs["Surface"])
    gl.data.materials.append(gm)
    gl.visible_shadow = False
    gl.location = FAR
    E.core_glow = gl
    L = bpy.data.lights.new("mg_core_light", "POINT")
    L.color = (1.0, 0.15, 0.75)
    L.energy = 0.0
    L.shadow_soft_size = 3.0
    E.core_light = bpy.data.objects.new("mg_core_light", L)
    E.sc.collection.objects.link(E.core_light)
    E.core_light.location = CORE


N_SNOW = 70


def _snow(E):
    """The dark snow: residue cubes from every loop falling through the layers into the core."""
    r = random.Random(3)
    E.snow = []
    me = bpy.data.meshes.new("mg_snow")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=CUBE_S)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(E.dark)
    for i in range(N_SNOW):
        ob = bpy.data.objects.new(f"mg_snow{i}", me)
        E.sc.collection.objects.link(ob)
        ob.location = FAR
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(4.0, 22.0)
        E.snow.append((ob, Vector((CORE.x + d * math.cos(a), CORE.y + d * math.sin(a), r.uniform(-2, 14))),
                       r.uniform(0, 1), r.uniform(0.7, 1.3), r.uniform(0, 6.3)))


# -------- the holograms
def _holo_mat(name, rgb=(0.25, 0.9, 1.0), strength=3.0, alpha=0.65):
    """A recorded memory: a clean Fresnel edge glow, horizontal scanlines (a wave texture) mixed with transparency,
    a faint fill so the shape reads."""
    m = bpy.data.materials.new(name)
    nt = _nt(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Window"], sep.inputs[0])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "Y"
    wv.inputs["Scale"].default_value = 60.0
    nt.links.new(tc.outputs["Window"], wv.inputs["Vector"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    sc_ = nt.nodes.new("ShaderNodeMath")
    sc_.operation = "MULTIPLY_ADD"
    nt.links.new(wv.outputs["Fac"], sc_.inputs[0])
    sc_.inputs[1].default_value = 0.35
    sc_.inputs[2].default_value = 0.2
    edge = nt.nodes.new("ShaderNodeMath")
    edge.operation = "ADD"
    nt.links.new(lw.outputs["Fresnel"], edge.inputs[0])
    nt.links.new(sc_.outputs[0], edge.inputs[1])
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    nt.links.new(edge.outputs[0], gain.inputs[0])
    gain.inputs[1].default_value = strength
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    nt.links.new(gain.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    op = nt.nodes.new("ShaderNodeMath")                    # opacity: the edge and the scanlines
    op.operation = "MULTIPLY"
    nt.links.new(edge.outputs[0], op.inputs[0])
    op.inputs[1].default_value = alpha
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(op.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m, gain


def _override(ob, mat):
    if ob.type != "MESH":
        return
    if not ob.material_slots:
        ob.data.materials.append(mat)
    for sl in ob.material_slots:
        sl.link = "OBJECT"
        sl.material = mat
    ob.visible_shadow = False


def _ghost(E):
    """The replay: a second Noob, all hologram; his limbs as glowing wireframes when he breaks."""
    from noob import build_noob
    col = bpy.data.collections.new("mg_ghost")
    E.sc.collection.children.link(col)
    E.holo, E.holo_gain = _holo_mat("mg_holo")
    G = build_noob(col, name="ghost")
    for ob in col.objects:
        _override(ob, E.holo)
    G.root.location = FAR
    G.arm_len = E.N.arm_len if hasattr(E.N, "arm_len") else 0.6
    E.G = G
    E.ghost_parts = [o for o in col.objects if o.type == "MESH" and o.name != "ghost_face"]
    for o in col.objects:
        if o.name == "ghost_face":
            o.hide_render = True
    # the break: each limb a wireframe copy that drifts apart and fades
    E.wire_mat, E.wire_em = _wire_mat("mg_ghost_wire", strength=2.5)
    E.ghost_bits = []
    for o in E.ghost_parts:
        w = bpy.data.objects.new(o.name + "_bit", o.data)
        E.sc.collection.objects.link(w)
        md = w.modifiers.new("wire", "WIREFRAME")
        md.thickness = 0.018
        md.use_relative_offset = False
        _override(w, E.wire_mat)
        w.location = FAR
        E.ghost_bits.append((o, w))


def _fissure_mesh(E):
    """A jagged void fissure: a tall translucent black slab, its torn edge glowing magenta."""
    r = random.Random(5)
    bm = bmesh.new()
    H, n = 4.2, 9
    left, right = [], []
    for i in range(n + 1):
        z = H * i / n
        w = 0.55 * math.sin(math.pi * i / n) ** 0.7 + 0.08
        left.append(bm.verts.new((-w * r.uniform(0.6, 1.4), 0, z)))
        right.append(bm.verts.new((w * r.uniform(0.6, 1.4), 0, z)))
    for i in range(n):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    me = bpy.data.meshes.new("mg_fissure")
    bm.to_mesh(me)
    bm.free()
    m = bpy.data.materials.new("mg_fissure")
    nt = _nt(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    # the edge: |x - 0.5| near 0.5 (generated x runs 0..1 across the slab)
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    nt.links.new(sep.outputs["X"], sub.inputs[0])
    sub.inputs[1].default_value = 0.5
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    nt.links.new(sub.outputs[0], ab.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    nt.links.new(ab.outputs[0], gt.inputs[0])
    gt.inputs[1].default_value = 0.38
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.1, 0.8, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(gt.outputs[0], mul.inputs[0])
    mul.inputs[1].default_value = 4.0
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    dk = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dk.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.8
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(dk.outputs[0], mx.inputs[2])
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mx.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    E.fissure_me = me


def _cracks(E):
    """The breach: jagged black-and-magenta cracks spidering across the floor from under them (revealed by time)."""
    r = random.Random(11)
    bm = bmesh.new()
    E.crack_segs = []
    origin = Vector((0.4, 0.6, 0.0))
    for k in range(9):
        a = 2 * math.pi * k / 9 + r.uniform(-0.25, 0.25)
        p = origin.copy()
        d0 = 0.0
        for j in range(7):
            a += r.uniform(-0.5, 0.5)
            L = r.uniform(0.9, 2.4)
            q = p + Vector((math.cos(a) * L, math.sin(a) * L, 0))
            w = 0.09 * (1 - j / 8)
            nrm = Vector((-math.sin(a), math.cos(a), 0)) * w
            vs = [bm.verts.new(p - nrm), bm.verts.new(q - nrm * 0.6), bm.verts.new(q + nrm * 0.6), bm.verts.new(p + nrm)]
            f = bm.faces.new(vs)
            E.crack_segs.append(d0)
            d0 += L
            p = q
    me = bpy.data.meshes.new("mg_cracks")
    bm.to_mesh(me)
    bm.free()
    m = bpy.data.materials.new("mg_cracks")
    nt = _nt(m)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.08, 0.7, 1)
    em.inputs["Strength"].default_value = 6.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    E.cracks = bpy.data.objects.new("mg_cracks", me)
    E.sc.collection.objects.link(E.cracks)
    E.cracks.location = FAR
    E.cracks_em = em.inputs["Strength"]
    E.crack_origin = origin


def _lights(E):
    """The grid's own light: a cyan glow from below through the floor, a soft cool key, a rim."""
    up = bpy.data.lights.new("mg_under", "AREA")
    up.size = 14.0
    up.color = (0.3, 0.85, 1.0)
    up.energy = 350.0
    E.under = bpy.data.objects.new("mg_under", up)
    E.sc.collection.objects.link(E.under)
    E.under.location = (1.0, 2.0, -3.0)
    E.under.rotation_euler = (math.pi, 0, 0)
    rim = bpy.data.lights.new("mg_rim", "AREA")
    rim.size = 6.0
    rim.color = (0.35, 0.9, 1.0)
    rim.energy = 500.0
    E.rim = bpy.data.objects.new("mg_rim", rim)
    E.sc.collection.objects.link(E.rim)
    E.rim.location = (1.0, 9.0, 4.5)
    E.rim.rotation_euler = (Vector((0.5, 0.5, 1.2)) - Vector(E.rim.location)).to_track_quat("-Z", "Y").to_euler()
    E.key.hide_render = False
    E.key.hide_viewport = False
    E.key.data.color = (0.85, 0.95, 1.0)
    E.breach_light = bpy.data.objects.new("mg_breach", bpy.data.lights.new("mg_breach", "POINT"))
    E.sc.collection.objects.link(E.breach_light)
    E.breach_light.data.color = (1.0, 0.12, 0.7)
    E.breach_light.data.energy = 0.0
    E.breach_light.data.shadow_soft_size = 2.0
    E.breach_light.location = (0.4, 0.6, 0.05)


def _patch_screen(E):
    """Patch's eye: dimmable, and an amber tint for his panic on the breach (this chapter's material only)."""
    m = E.PA.screen.active_material
    nt = m.node_tree
    bs = next(n_ for n_ in nt.nodes if n_.type == "BSDF_PRINCIPLED")
    E.eye_strength = bs.inputs["Emission Strength"]
    E.eye_strength0 = E.eye_strength.default_value
    link = bs.inputs["Emission Color"].links[0]
    src = link.from_socket
    nt.links.remove(link)
    bw = nt.nodes.new("ShaderNodeRGBToBW")                          # the eye's shape as brightness...
    nt.links.new(src, bw.inputs[0])
    am = nt.nodes.new("ShaderNodeMix")                              # ...in amber
    am.data_type = "RGBA"
    am.blend_type = "MULTIPLY"
    am.inputs[0].default_value = 1.0
    nt.links.new(bw.outputs[0], am.inputs[6])
    am.inputs[7].default_value = (1.6, 0.62, 0.04, 1)
    mu = nt.nodes.new("ShaderNodeMix")
    mu.data_type = "RGBA"
    mu.blend_type = "MIX"
    nt.links.new(src, mu.inputs[6])
    nt.links.new(am.outputs[2], mu.inputs[7])
    mu.inputs[0].default_value = 0.0
    nt.links.new(mu.outputs[2], bs.inputs["Emission Color"])
    E.eye_amber = mu.inputs[0]


# ------------------------------------------------------------------ snapshots (static holograms of posed rigs)
def _snapshot(E, col, objs, xf):
    """Static copies of posed rig parts (evaluated meshes), transformed by xf, into collection col."""
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in objs:
        if ob.type != "MESH" or ob.hide_render or ob.name.endswith("_face") or "beam" in ob.name:
            continue
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        cp = bpy.data.objects.new(ob.name + "_holo", me)
        col.objects.link(cp)
        mw = ob.matrix_world.copy()
        if ob in E.steve_objs:
            mw = E.S.holder.matrix_world @ mw
        cp.matrix_world = xf @ mw
        _override(cp, E.holo_field)


def _steve_objs(E):
    rig = list(E.S.rig.all_objects) if hasattr(E.S.rig, "all_objects") else []
    return [o for o in rig if o.type == "MESH" and not o.name.startswith("item_")]


POSES = ("wave", "shield", "run", "reach")


def _pose_group(E, kind):
    """One recorded loop: Steve, the Noob and Patch, posed (the field's four variations), as hologram copies."""
    from ep09_new import NF, SF
    o = Vector((0, 0, 0))
    if kind == "wave":
        M.set_steve(E, o + Vector((-1.0, 0, 0)), 15, {"arm_sr": {"fwd": 20, "out": 20}}, dict(SF["neutral"]), 0.0)
        M.set_noob(E, o + Vector((0.9, 0, 0)), -10, {"arm_sr": {"fwd": 160, "out": 30, "elbow": 20}}, dict(NF["happy"]), 0.0)
        pp = o + Vector((0.0, 0.4, 2.1))
    elif kind == "shield":
        M.set_steve(E, o + Vector((0.0, 0.6, 0)), 0, {"arm_sr": {"fwd": 80, "out": 60, "elbow": 10},
                                                       "arm_sl": {"fwd": 70, "out": 40, "elbow": 20}, "chest_lean": 10},
                    dict(SF["scared"]), 0.0)
        M.set_noob(E, o + Vector((0.3, -0.9, 0)), 0, {"arm_sl": {"fwd": 40, "out": 30, "elbow": 40},
                                                       "arm_sr": {"fwd": 40, "out": 30, "elbow": 40}, "chest_lean": -10},
                   dict(NF["scared"]), 0.0)
        pp = o + Vector((-1.3, 0.2, 2.3))
    elif kind == "run":
        pz = M.run_cycle(0.9, 1.0, steve=True)
        M.set_steve(E, o + Vector((-0.8, 0.3, 0)), 90, pz, dict(SF["scared"]), 0.0)
        M.set_noob(E, o + Vector((0.8, -0.3, 0)), 90, M.run_cycle(2.4, 1.0, steve=False), dict(NF["scared"]), 0.0)
        pp = o + Vector((0.0, 0.8, 2.0))
    else:
        M.set_steve(E, o + Vector((-1.1, 0.1, 0)), 25, {"arm_sr": {"fwd": 35, "out": 15}}, dict(SF["worried"]), 0.0)
        M.set_noob(E, o + Vector((0.8, 0.2, 0)), 20, {"arm_sr": {"fwd": 95, "out": 10, "elbow": 5}, "chest_lean": 22,
                                                       "arm_sl": {"fwd": 20, "out": 20}}, dict(NF["neutral"]), 0.0)
        pp = o + Vector((0.2, -0.6, 2.2))
    E.PA.root.location = pp
    E.PA.root.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    col = bpy.data.collections.new("mg_loop_" + kind)
    objs = E.steve_objs + [o_ for o_ in bpy.data.objects if _top(o_) in (E.N.root, E.PA.root)]
    _snapshot(E, col, objs, Matrix.Identity(4))
    # its fissure behind it
    f = bpy.data.objects.new("mg_fis_" + kind, E.fissure_me)
    col.objects.link(f)
    f.location = (0.3, 3.0, 0)
    f.scale = (1.4, 1, 1.15)
    return col


def _field(E):
    """The infinite archive: cells on jittered points out to ~150 m, each a pad and one of the four recorded loops,
    turned 0/90/180/270 at random; a gap where they stand."""
    E.holo_field, _ = _holo_mat("mg_holo_field", strength=2.4, alpha=0.55)
    E.groups = {k: _pose_group(E, k) for k in POSES}
    r = random.Random(17)
    E.cells = []
    pad_col = bpy.data.collections.new("mg_cellpad")
    pad, wire = _slab("mg_cellpad", (5.0, 5.0, 0.16), (0, 0, -0.08), E.pad_mat, E.pad_wire, col=pad_col)
    step = 12.0
    for i in range(-12, 13):
        for j in range(-6, 14):
            x = i * step + r.uniform(-2.5, 2.5)
            y = j * step + r.uniform(-2.5, 2.5)
            z = r.uniform(-1.5, 1.5)
            if abs(x) < 10 and -6 < y < 14:                       # where they stand, the replay, the past loop
                continue
            if math.hypot(x, y) > 150:
                continue
            k = POSES[r.randrange(4)]
            rot = r.randrange(4) * math.pi / 2
            for c in (E.groups[k], pad_col):
                e = bpy.data.objects.new(f"mg_cell_{i}_{j}_{c.name}", None)
                e.instance_type = "COLLECTION"
                e.instance_collection = c
                e.location = (x, y, z)
                e.rotation_euler = (0, 0, rot)
                E.sc.collection.objects.link(e)
                E.cells.append(e)
    # the recorded loop in cell P (shot 6): the trio reaching toward its fissure
    E.past = bpy.data.objects.new("mg_past", None)
    E.past.instance_type = "COLLECTION"
    E.past.instance_collection = E.groups["reach"]
    E.past.location = CELL_P
    E.past.rotation_euler = (0, 0, 0)
    E.sc.collection.objects.link(E.past)


# ------------------------------------------------------------------ prepare (every shard, first frame)
def prepare(E):
    if E.prepped7:
        return
    E.prepped7 = True
    _use(E)
    E.steve_objs = _steve_objs(E)
    _field(E)
    # where the ghost's limbs are when he breaks (posed once per death)
    E.break_mw = {}
    for k in range(2):
        tb = _death_t(k)
        ghost(E, tb - 1e-3)
        bpy.context.view_layer.update()
        E.break_mw[k] = {o.name: o.matrix_world.copy() for o, _ in E.ghost_bits}
    E.G.root.location = FAR


# ------------------------------------------------------------------ the shots
SHOTS = [("s1", "wash", 0), ("s2", "replay", 0), ("s3", "steve_what", -0.15), ("s4", "residue", 0),
         ("s5", "drop", 0), ("s6", "past", 0), ("s7", "noob_us", -0.2), ("s8", "pull", 0), ("s9a", "weight", 0),
         ("s9b", "look", 0), ("s10", "breach", -0.1)]


def shot_bounds():
    return [(name, b(beat) + off) for name, beat, off in SHOTS]


def which(t):
    bs = shot_bounds()
    for i, (name, t0) in enumerate(bs):
        t1 = bs[i + 1][1] if i + 1 < len(bs) else 1e9
        if t < t1:
            return name, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


# ------------------------------------------------------------------ the replay
def _spawn_t(k):                     # the ghost pops up on the pad: the first at spot+0.4, then after each death
    return (b("spot") + 0.4, b("replay") + 1.7, b("replay2") + 1.95)[k]


def _death_t(k):
    return (b("replay") + 0.6, b("replay2") + 0.85)[k]


def _cube_land_t(k):                 # the residue cube thuds down (k 0, 1); cube 2 was there from an earlier loop
    return (b("replay") + 1.15, b("replay2") + 1.4)[k]


def ghost(E, t):
    """Pops up on the pad, walks cheerfully to the red brick, hops on it: breaks (wireframe limbs drift apart)."""
    from ep09_new import NF
    G = E.G
    k = 0
    while k + 1 < 3 and t >= _spawn_t(k + 1):
        k += 1
    t0 = _spawn_t(k)
    td = _death_t(k) if k < 2 else 1e9
    for o, w in E.ghost_bits:
        w.location = FAR
    if t < t0 or (t >= td) or t >= b("residue"):
        G.root.location = FAR
        if k < 2 and td <= t < td + 1.0 and E.prepped7 and k in E.break_mw:
            u = (t - td) / 1.0
            for i, (o, w) in enumerate(E.ghost_bits):
                mw = E.break_mw[k][o.name]
                loc, rot, scl = mw.decompose()
                out = loc - (BRICK + Vector((0, 0, 1.0)))
                out.z = abs(out.z) + 0.3
                spin = Quaternion((1, 0, 0) if i % 2 else (0, 1, 0), u * 2.5 * (1 if i % 3 else -1))
                s = 1.0 - 0.7 * u
                w.matrix_world = Matrix.LocRotScale(loc + out.normalized() * 0.9 * u, rot @ spin, scl * s)
            E.wire_em.inputs["Strength"].default_value = 2.5 * (1 - u)
        return
    # the pop (squash and stretch), the walk, the hop onto the brick
    pop = ss(t0, t0 + 0.25, t)
    walk_end = td - 0.35
    u = ss(t0 + 0.35, walk_end, t)
    p = GHOST0.lerp(BRICK - Vector((0, 0.55, 0)), u)
    pz = {"arm_sl": {"fwd": 10, "out": 12}, "arm_sr": {"fwd": 10, "out": 12}}
    if t0 + 0.35 < t < walk_end:
        E2._walk(pz, t, t0 + 0.35, 1.8, amp=0.0)
        sw = math.sin((t - t0 - 0.35) * 1.8 * 2 * math.pi)
        pz["arm_sl"] = {"fwd": 25 * sw, "out": 10}
        pz["arm_sr"] = {"fwd": -25 * sw, "out": 10}
        pz["leg_sl"] = {"fwd": 25 * sw}
        pz["leg_sr"] = {"fwd": -25 * sw}
    if t >= walk_end:                                            # the cheerful hop onto the brick
        h = (t - walk_end) / 0.35
        p = (BRICK - Vector((0, 0.55, 0))).lerp(BRICK, min(1.0, h)) + Vector((0, 0, 0.5 * math.sin(math.pi * min(1.0, h))))
        pz["arm_sl"] = {"fwd": 40, "out": 40}
        pz["arm_sr"] = {"fwd": 40, "out": 40}
    M.set_noob(E, p, 0.0, pz, dict(NF["happy"]), t, N=G)
    sq = 1.0 + 0.25 * math.sin(math.pi * pop) * (pop < 1)
    G.root.scale = (E.G_scale / sq ** 0.5, E.G_scale / sq ** 0.5, E.G_scale * sq * pop) if pop < 1 else (E.G_scale,) * 3


# ------------------------------------------------------------------ props
def residue(E, t):
    """The cubes on the replay pad: one already there, one thud per death (a small bounce), trembling."""
    for i, ob in enumerate(E.res_cubes):
        if i == 2:
            t_land = -1.0
        else:
            t_land = _cube_land_t(i)
        if t < t_land - 0.45 or t >= b("drop") + 0.6:
            ob.location = FAR
            continue
        c = CUBES[i] + Vector((0, 0, CUBE_S / 2))
        if t < t_land:                                          # dropping out of the break
            u = (t - (t_land - 0.45)) / 0.45
            c = c + Vector((0, -0.8 * (1 - u), 1.2 * (1 - u * u)))
        else:
            d = t - t_land
            c = c + Vector((0, 0, 0.12 * abs(math.sin(d * 9)) * math.exp(-d * 6)))
        tr = 0.012 * (math.sin(t * 37 + i * 2) + math.sin(t * 23 + i))     # trembling
        if t >= b("drop"):                                      # they sink through the glass, down to the core
            u = ss(b("drop"), b("drop") + 0.6, t)
            c = c + Vector((0, 0, -3.0 * u * u))
        ob.location = c + Vector((tr, tr * 0.7, 0))
        ob.rotation_euler = (0, 0, 0.3 * i + tr * 4)


def core(E, t):
    vis = b("drop") - 0.2 <= t < b("noob_us")
    E.core_light.data.energy = 600.0 * (0.7 + 0.3 * math.sin(t * 5)) if vis else 0.0
    E.core_em.default_value = 8.0 * (0.6 + 0.4 * math.sin(t * 7.0) * math.sin(t * 2.3))
    E.core_glow.location = CORE if vis else FAR
    for ob, rad, a0, h, s, w, ph in E.core_blocks:
        if not vis:
            ob.location = FAR
            continue
        a = a0 + t * w * (1.2 / max(0.6, rad))
        rr = rad * (1 + 0.06 * math.sin(t * 2 + ph))
        ob.location = CORE + Vector((rr * math.cos(a), rr * math.sin(a), h * rad * 0.8))
        ob.rotation_euler = (t * w + ph, t * 0.7 * w, a)
        ob.scale = (s * 1.4, s * 1.4, s * 1.4)


def snow(E, t):
    vis = b("drop") <= t < b("noob_us")
    for ob, p0, ph, sp, rot in E.snow:
        if not vis:
            ob.location = FAR
            continue
        u = ((t - b("drop")) * 0.22 * sp + ph) % 1.0               # fall, spiralling in, then start again above
        p = p0.lerp(CORE, u ** 1.4)
        a = u * 3.0
        d = p - CORE
        p = CORE + Vector((d.x * math.cos(a) - d.y * math.sin(a), d.x * math.sin(a) + d.y * math.cos(a), d.z))
        p.z = lerp(p0.z + 10.0, CORE.z, u)
        ob.location = p
        ob.rotation_euler = (t * 2 + rot, t * 1.3, rot)


def fx(E, t):
    """The pullback's field only when seen; the breach (cracks, cells dissolving), the warp, the flash."""
    far_vis = t >= b("past") - 0.3
    for e in E.cells:
        e.hide_render = not far_vis
    E.past.hide_render = not (b("past") - 0.3 <= t)
    # the breach: cracks grow out from under them; near cells dissolve (sink, gone)
    br = b("breach")
    if t >= br:
        E.cracks.location = (0, 0, 0.012)
        g = ss(br, br + 1.4, t)
        E.cracks.scale = (0.15 + 0.85 * g, 0.15 + 0.85 * g, 1)
        E.cracks_em.default_value = 3.5 + 2.0 * math.sin(t * 30) ** 2
        E.breach_light.data.energy = 40.0 * g
        for e in E.cells:
            d = Vector(e.location).length
            k_ = ss(br + 0.2 + d * 0.03, br + 0.8 + d * 0.03, t)
            if k_ > 0.98:
                e.hide_render = True
            else:
                e.scale = (1, 1, 1 - k_)
        for i, (sl, w) in enumerate(E.pad_deco):
            f = ss(br + 0.15 + 0.15 * i, br + 1.6 + 0.15 * i, t)
            for o in (sl, w):
                if o is None:
                    continue
                if "p0" not in o:
                    o["p0"] = tuple(o.location)
                p0 = Vector(o["p0"])
                o.location = p0 + Vector((0, 0, -9.0 * f * f))
                o.rotation_euler = (0.9 * f * (1 if i % 2 else -1), 0.6 * f, 0)
                o.hide_render = f > 0.98
        E.floor_em.inputs[1].default_value = 4.0 * (1 - 0.5 * ss(br, br + 1.0, t)) * (0.85 + 0.15 * math.sin(t * 40))
    else:
        E.cracks.location = FAR
        E.breach_light.data.energy = 0.0
        E.floor_em.inputs[1].default_value = 4.0
        for e in E.cells:
            e.scale = (1, 1, 1)
        for (sl, w) in E.pad_deco:
            for o in (sl, w):
                if o is None:
                    continue
                if "p0" in o:
                    o.location = Vector(o["p0"])
                o.rotation_euler = (0, 0, 0)
                o.hide_render = False
    E.brick.hide_render = not (b("spot") <= t < b("drop") + 0.2)
    E.brick_em.default_value = 1.6 + 1.2 * math.exp(-((t - _death_t(0)) / 0.1) ** 2) + 1.2 * math.exp(-((t - _death_t(1)) / 0.1) ** 2)


def warp(E, t):
    """Patch's emergency warp: the cyan sphere and ring expanding round all three."""
    sp, ring, lo = E.warp6
    w0 = b("warp")
    if t < w0 - 0.2:
        sp.location = ring.location = FAR
        lo.data.energy = 0.0
        return
    c = Vector(E.PA.root.location)
    u = ss(w0 - 0.2, b("flash"), t)
    sp.location = c
    sp.scale = (0.3 + 3.2 * u,) * 3
    ring.location = c
    ring.scale = (0.5 + 4.2 * u,) * 3
    ring.rotation_euler = (math.radians(75), 0, t * 3)
    lo.location = c
    lo.data.energy = 2500.0 * u


# ------------------------------------------------------------------ the cast
def _arrive(t, delay, h0):
    """Falling out of the warp: (height, tumble angle, landed fraction)."""
    t0 = b("tumble") + delay
    T = t0 - 0.05                     # falling from the first frames (nobody hangs in the air)
    if t < t0 - T:
        return h0, 1.0, 0.0
    if t < t0:
        u = (t - (t0 - T)) / T
        return h0 * (1 - u * u), 1.0 - u, 0.0
    return 0.0, 0.0, min(1.0, (t - t0) / 0.25)


def _noob_breach_pos(E, t):
    """Where the Noob is during the breach (time only: Steve reads it before the Noob is posed)."""
    p0 = Vector((0.9, 0.9, 0.0))
    away = p0 - E.crack_origin
    away.z = 0.0
    away.normalize()
    return p0 + away * 0.45 * ss(b("breach") + 0.05, b("breach") + 0.75, t)


def patch_pos(E, t):
    if t < b("tumble") + 1.0:                                     # wobbling out of the warp
        u = ss(0.0, b("tumble") + 1.0, t)
        return P_HOME + Vector((0.6 * (1 - u), -0.4 * (1 - u), 0.9 * (1 - u))) + \
            Vector((0.12 * math.sin(t * 13), 0.0, 0.08 * math.sin(t * 9))) * (1 - u)
    if t < b("residue"):
        return P_HOME
    if t < b("drop"):                                             # drifts in beside the cubes
        u = ss(b("residue"), b("residue") + 1.3, t)
        return P_HOME.lerp(PAD_R + Vector((-1.4, 1.2, 1.3)), u)
    if t < b("past"):
        return PAD_R + Vector((-1.6, 0.6, 1.6))
    if t < b("weight"):
        u = ss(b("past"), b("past") + 1.5, t)
        return (PAD_R + Vector((-1.6, 0.6, 1.6))).lerp(P_WEIGHT, u)
    if t < b("breach"):
        return P_WEIGHT
    u = ss(b("breach") + 0.2, b("patch_archive"), t)
    return P_WEIGHT.lerp(P_BREACH, u)


def patch(E, t):
    from patch import set_patch
    P = E.PA
    p = patch_pos(E, t)
    bob = 0.05 * math.sin(t * 2.4) + 0.02 * math.sin(t * 5.3 + 1)
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.3))
    S_ = Vector(E.S.holder.location) + Vector((0, 0, 1.4))
    tgt = (N_ + S_) / 2
    if b("spot") <= t < b("residue"):
        tgt = GHOST0 + Vector((0, 1.5, 1.0))
    if b("residue") <= t < b("past"):
        tgt = CUBES[1] + Vector((0, 0, 0.2)) if t < b("patch_behind") else N_
    if b("weight") <= t < b("look") or b("breach") + 0.2 <= t:
        tgt = Vector(E.cam_loc_now)
    to = tgt - p
    yaw = _yaw(Vector((to.x, to.y, 0)))
    pitch = -math.degrees(math.atan2(to.z, max(0.3, Vector((to.x, to.y, 0)).length))) * 0.5
    roll = 0.0
    if t < b("tumble") + 1.0:                                     # wobbling, steadying
        k = 1 - ss(0.0, b("tumble") + 1.0, t)
        roll = 25 * k * math.sin(t * 11)
        pitch += 18 * k * math.sin(t * 7 + 1)
    vals = {"open": 1.0, "look_x": 0.0, "look_y": 0.0, "squint": 0.0, "wide": 0.6, "glitch": 0.0, "scan": 0.0,
            "smile": 0.0, "sad": 0.0}
    per = 2.8
    ph = (t + 0.9) % per
    blink = math.exp(-((ph - 0.06) / 0.04) ** 2)
    vals["open"] = max(0.05, 1 - blink)
    bright = 1.0
    if b("residue") <= t < b("weight"):
        vals.update({"wide": 0.3})
    if b("weight") <= t < b("look"):                             # "...I stopped counting.": dims, one flicker, down
        k = ss(b("weight") + 0.3, b("patch_count") + 0.4, t)
        bright = 1.0 - 0.8 * k
        fl = b("patch_count") + 0.75
        if fl <= t < fl + 0.08:
            bright *= 0.15
        vals.update({"wide": 0.0, "sad": 0.0, "squint": 0.0, "look_y": -0.45 * k})
        pitch += 5.0 * k
        vals["open"] = max(0.05, 1 - blink) * (1 - 0.2 * k)
    if b("look") <= t < b("breach"):
        bright = 0.35
        vals.update({"look_y": -0.3})
    amber = 0.0
    if b("breach") <= t:                                          # panic: amber, wide
        vals.update({"wide": 1.0, "sad": 0.0, "squint": 0.0, "open": 1.0, "look_y": 0.0})
        amber = ss(b("breach") + 0.1, b("breach") + 0.3, t) * (1 - ss(b("warp") - 0.3, b("warp"), t))
        if b("patch_archive") <= t < b("warp"):
            vals["glitch"] = 0.3 if int(t * FPS) % 3 == 0 else 0.0
        bright = 1.2 + 1.5 * ss(b("warp"), b("flash"), t)
    P.root.location = p + Vector((0, 0, bob))
    P.root.rotation_euler = (math.radians(pitch), math.radians(roll), math.radians(yaw))
    P.root.scale = (1, 1, 1)
    for side_, sx in (("l", -1), ("r", 1)):
        P.fins[side_].rotation_euler = (math.radians(8 * math.sin(t * 9 + sx) + pitch * 0.6), 0, 0)
    set_patch(P, vals)
    E.eye_strength.default_value = E.eye_strength0 * bright
    E.eye_amber.default_value = amber
    P.glow.data.energy = 8.0 * bright + 60.0 * ss(b("warp"), b("flash"), t)


def noob(E, t):
    from ep09_new import NF
    N = E.N
    S_ = Vector(E.S.holder.location) + Vector((0, 0, 1.4))
    face = dict(NF["shock"])
    pz = {"arm_sl": {"fwd": 15, "out": 20}, "arm_sr": {"fwd": 15, "out": 20}}
    p, yaw = N_STAND.copy(), 20.0
    look_at = GHOST0 + Vector((0, 1.0, 1.0))
    lie = 0.0
    h, tum, land = _arrive(t, 0.75, 2.6)
    worried = {"both_to": -0.6, "both_ti": 0.35, "both_h": 1.7, "m_arch": 0.3, "m_o": 0.0}
    if t < b("settle") + 0.9:                                     # out of the warp, flat on his back, then springs up
        t_l = b("tumble") + 0.75                                  # touchdown (the thud)
        p = N_LAND + Vector((0, 0, h))
        yaw = -30.0 + 200 * tum
        look_at = p + Vector((0, 0, 6))
        face = dict(NF["shock"])
        if t < t_l:                                               # falling, turning onto his back
            lie = 0.2 + 0.8 * (1 - tum)
            pz = {"arm_sl": {"fwd": 30 + 60 * tum, "out": 60}, "arm_sr": {"fwd": 30 + 60 * tum, "out": 60},
                  "leg_sl": {"fwd": 30 * tum}, "leg_sr": {"fwd": -20 * tum}}
        else:
            a0, a1 = b("settle") + 0.1, b("settle") + 0.35        # the tuck (anticipation), then the spring
            s1 = b("settle") + 0.8
            d = t - t_l
            bounce = 0.12 * abs(math.sin(d * 10)) * math.exp(-d * 7)      # the bump on landing
            tuck = ss(a0, a1, t) * (1 - ss(a1, a1 + 0.2, t))
            spring = ss(a1, s1, t)
            lie = 1.0 - spring
            hop = math.sin(math.pi * spring) * 0.55
            p = N_LAND.lerp(N_STAND, spring) + Vector((0, 0, bounce + hop))
            arms_up = tuck * (1 - spring)
            pz = {"arm_sl": {"fwd": lerp(lerp(20, 150, arms_up), 25, spring), "out": lerp(45, 30, spring), "elbow": 20},
                  "arm_sr": {"fwd": lerp(lerp(20, 150, arms_up), 25, spring), "out": lerp(45, 30, spring), "elbow": 20},
                  "leg_sl": {"fwd": 70 * tuck + 20 * math.sin(math.pi * spring)},
                  "leg_sr": {"fwd": 70 * tuck - 10 * math.sin(math.pi * spring)}}
            if t >= s1:                                           # lands on his feet: arms fling out, a wobble
                w = math.exp(-(t - s1) * 8)
                pz["arm_sl"] = {"fwd": 25 + 20 * w, "out": 30 + 35 * w, "elbow": 15}
                pz["arm_sr"] = {"fwd": 25 + 20 * w, "out": 30 + 35 * w, "elbow": 15}
                pz["chest_lean"] = 12 * w * math.cos((t - s1) * 18)
            look_at = p + Vector((0, 2.0, 6.0 * (1 - spring) + 1.4))
            if spring > 0.5:
                face = dict(NF["awe"])
    elif t < b("replay"):                                         # fascinated, turning; spots his hologram
        yaw = lerp(-30.0, _face_to(N_STAND, GHOST0), ss(b("settle") + 1.0, b("spot") + 0.6, t))
        look_at = GHOST0 + Vector((0, 0.5 * ss(b("spot"), b("replay"), t), 1.0)) if t >= b("spot") else N_STAND + Vector((-3, 6, 2.5))
        face = dict(NF["awe"])
        pz["chest_lean"] = -4
    elif t < b("steve_what"):                                     # the replay: delight, he points ("Hey, that's me!")
        yaw = _face_to(N_STAND, GHOST0 + Vector((0, 2, 0)))
        look_at = GHOST0 + Vector((0, 1.6, 1.0))
        face = dict(NF["awe"])
        if b("noob_me") - 0.3 <= t < b("noob_me", 1) + 0.4:
            face = {"both_py": 0.45, "both_h": 1.85, "m_arch": -0.2, "m_o": 0.0}         # raised brows, lip-sync
            k = ss(b("noob_me") - 0.3, b("noob_me") + 0.1, t)
            pz["arm_sr"] = {"fwd": 15 + 75 * k, "out": 20 - 10 * k, "elbow": 5}
        if t >= _death_t(1) - 0.1:
            face = dict(worried)
    elif t < b("drop"):                                           # worried: the cubes, Patch
        yaw = _face_to(N_STAND, CUBES[1])
        look_at = CUBES[1] if t < b("patch_behind") else Vector(E.PA.root.location)
        face = dict(worried)
    elif t < b("past"):                                           # leans over the pad's edge: "...Where does it go?"
        k = ss(b("drop") + 0.2, b("drop") + 1.4, t)
        p = N_STAND.lerp(N_EDGE, k)
        yaw = _face_to(p, Vector((N_EDGE.x + 1.0, N_EDGE.y + 3.0, 0)))
        if 0.05 < k < 0.95:
            _run(pz, t, b("drop") + 0.2, 1.2, k=0.25, steve=False)
        look_at = p + Vector((1.0, 3.0, -4.0))
        pz["chest_lean"] = 20 * k
        pz["arm_sl"] = {"fwd": 25, "out": 20, "elbow": 20}
        pz["arm_sr"] = {"fwd": 25, "out": 20, "elbow": 20}
        face = dict(worried)
    else:
        p = N_EDGE.lerp(Vector((0.9, 0.9, 0)), ss(b("past") - 0.2, b("past") + 1.2, t))
        yaw = _face_to(p, CELL_P)
        look_at = CELL_P + Vector((0, 0.8, 1.2))
        face = dict(worried)
        if b("noob_us") - 0.2 <= t < b("pull"):                  # "That's... us?" / "From last time.": a slow blink
            face = {"both_to": -0.6, "both_ti": 0.35, "both_h": 1.65, "both_ps": 0.85, "m_arch": 0.32, "m_o": 0.0}
            bl = math.exp(-((t - (b("noob_us") + 0.6)) / 0.12) ** 2)
            face["both_h"] = lerp(face["both_h"], 0.15, bl)
        if b("look") <= t:                                        # looks out over the ghosts, hands lowering
            yaw = _face_to(p, LOOK_OUT)
            look_at = LOOK_OUT
            k = ss(b("look"), b("noob_deleted") + 0.5, t)
            pz["arm_sl"] = {"fwd": 30 * (1 - k) + 5, "out": 12, "elbow": 40 * (1 - k)}
            pz["arm_sr"] = {"fwd": 30 * (1 - k) + 5, "out": 12, "elbow": 40 * (1 - k)}
            pz["chest_lean"] = 6 * k
            pz["head_nod"] = 6 * k
            face = {"both_to": -0.62, "both_ti": 0.38, "both_h": 1.6, "both_ps": 0.8, "m_arch": 0.34, "m_o": 0.0}
        if b("breach") <= t:                                      # the floor cracks under him: he stumbles back
            br = b("breach")
            yaw = _face_to(p, E.crack_origin + Vector((0, -1, 0)))
            p = _noob_breach_pos(E, t)
            look_at = E.crack_origin
            face = dict(NF["scared"])
            if br + 0.05 < t < br + 0.75:
                _run(pz, t, br + 0.05, 1.7, k=0.3 * (1 - ss(br + 0.55, br + 0.75, t)), steve=False)
            wob = math.exp(-max(0.0, t - br - 0.6) * 1.2)                 # arms windmilling for balance, settling
            pz["arm_sl"] = {"fwd": 55 + 35 * math.sin(t * 9.0) * wob, "out": 45 + 15 * math.sin(t * 7.0), "elbow": 20}
            pz["arm_sr"] = {"fwd": 55 - 35 * math.sin(t * 9.0 + 0.6) * wob, "out": 45 + 15 * math.sin(t * 6.3), "elbow": 20}
            pz["chest_lean"] = -10 + 8 * math.sin(t * 5.0) * wob
            if b("warp") - 0.2 <= t:                              # shields his eyes from the warp
                k = ss(b("warp") - 0.2, b("warp") + 0.3, t)
                pz["arm_sl"] = {"fwd": lerp(55, 125, k), "out": lerp(45, 15, k), "elbow": lerp(20, 70, k)}
                pz["chest_lean"] = lerp(-10, 12, k)
            if b("patch_archive") <= t:
                look_at = Vector(E.PA.root.location)
    tl, nd = _look(yaw, p, look_at, h=1.4, lim=75)
    pz["head_turn"], pz["head_nod"] = tl, nd + pz.get("head_nod", 0)
    pz = life(E, "noob", pz, face, t, 1.6)
    M.set_noob(E, p, yaw, pz, face, t)
    if lie > 0.001:                                               # on his back: the body pivots up at his feet
        N.root.rotation_euler = (math.radians(-88 * lie), 0, math.radians(yaw))
        N.root.location = p + Vector((0, 0, 0.18 * lie))
    if tum > 0:
        N.root.rotation_euler = (math.radians(-88 * lie - 140 * tum), math.radians(30 * tum), math.radians(yaw))


def steve(E, t):
    from ep09_new import SF
    S = E.S
    lib = E.lib
    face = dict(SF["flat"])
    pz = {"arm_sr": {"fwd": 10, "out": 12, "elbow": 15}, "arm_sl": {"fwd": 8, "out": 12, "elbow": 15}}
    p, yaw = S_STAND.copy(), 0.0
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.3))
    look_at = N_
    h, tum, land = _arrive(t, 0.45, 2.4)
    if t < b("settle") + 1.2:                                     # lands, drops to one knee, looks round, rises
        p = S_LAND + Vector((0, 0, h))
        yaw = 0.0 + 120 * tum
        t_l = b("tumble") + 0.45                                  # touchdown (the thud)
        if t >= t_l - 0.02:
            imp = math.exp(-max(0.0, t - t_l) * 7) * ss(t_l - 0.02, t_l + 0.04, t)   # the impact dip
            k = ss(t_l - 0.04, t_l + 0.12, t) * (1 - ss(b("settle") + 0.05, b("settle") + 0.85, t))
            pz = _kneel(lib, k, imp)
            # breathing, then a look round the place from his knee
            br = 0.5 + 0.5 * math.sin((t - t_l) * 4.2)
            pz["chest_lean"] = pz.get("chest_lean", 0) + 3 * br * k
            look_at = p + Vector((0.4, 2.0, -0.6))
            g = ss(t_l + 0.45, t_l + 0.9, t)
            if g > 0:
                sweep = math.sin(ss(t_l + 0.45, b("settle") + 0.2, t) * math.pi * 1.3)
                look_at = look_at.lerp(p + Vector((4.0 * sweep - 1.0, 6.0, 1.6)), g)
        else:
            pz = {"arm_sr": {"fwd": 70 * tum, "out": 50, "elbow": 30}, "arm_sl": {"fwd": 70 * tum, "out": 50, "elbow": 30}}
            look_at = p + Vector((2.0, 6.0, 1.2))
        p = p.lerp(S_STAND, ss(b("settle") + 0.6, b("settle") + 1.2, t))
        if b("settle") + 0.8 < t < b("settle") + 1.15:            # a step as he settles
            _run(pz, t, b("settle") + 0.8, 1.4, k=0.12 * (1 - ss(b("settle") + 1.0, b("settle") + 1.15, t)), steve=True)
        face = dict(SF["stunned"])
    elif t < b("replay"):
        yaw = _face_to(p, GHOST0 + Vector((0, 1, 0)))
        look_at = N_ if t < b("spot") else GHOST0 + Vector((0, 1.0, 1.0))
        face = dict(SF["stunned"])
    elif t < b("residue"):                                        # watches; "What are those?": looking DOWN at the cubes
        yaw = _face_to(p, CUBES[0])
        look_at = GHOST0 + Vector((0, 2.0, 1.0))
        face = dict(SF["worried"])
        if b("replay2") + 1.0 <= t:
            look_at = CUBES[0] + Vector((0, 0, 0.1))
            pz["head_nod"] = 14
            face["both_py"] = -0.6                                # the eyes down too, never the lens
    elif t < b("past"):
        yaw = _face_to(p, CUBES[1])
        look_at = Vector(E.PA.root.location) if t < b("drop") else Vector(E.N.root.location) + Vector((0, 0, 1.0))
        face = dict(SF["worried"])
        if b("drop") <= t:
            p = S_STAND.lerp(Vector((0.0, 0.5, 0)), ss(b("drop"), b("drop") + 1.5, t))
    else:
        p = Vector((0.0, 0.5, 0)).lerp(Vector((-0.9, 0.6, 0)), ss(b("past") - 0.2, b("past") + 1.2, t))
        yaw = _face_to(p, CELL_P)
        look_at = CELL_P + Vector((0, 0.8, 1.2))
        face = dict(SF["worried"])
        if b("steve_times") - 0.2 <= t < b("weight"):
            face = {"both_to": -0.35, "both_ti": 0.2, "bb_tilt": -0.9, "bb_raise": 0.3, "m_arch": 0.2}
        if b("weight") <= t:
            look_at = Vector(E.PA.root.location)
        if b("look") <= t:                                        # a guilty glance at the Noob, then away, down
            g = ss(b("look") + 0.3, b("look") + 0.8, t) * (1 - ss(b("noob_deleted") + 1.2, b("noob_deleted") + 1.8, t))
            look_at = LOOK_OUT.lerp(Vector(E.N.root.location) + Vector((0, 0, 1.3)), g)
            dn = ss(b("noob_deleted") + 1.2, b("noob_deleted") + 2.1, t)
            look_at = look_at.lerp(Vector((-1.0, 3.0, 0.0)), dn)
            face = {"both_to": -0.3, "both_ti": 0.1, "bb_tilt": -0.5, "bb_raise": 0.0, "m_arch": 0.15}
        if b("breach") <= t:                                      # he steps in and grabs the Noob's arm
            br = b("breach")
            n_ = _noob_breach_pos(E, t)
            go = ss(br + 0.3, br + 1.1, t)
            p = p.lerp(n_ + Vector((-1.05, 0.15, 0)), go)
            yaw = lerp(_face_to(p, E.crack_origin), _face_to(p, n_), go)
            look_at = E.crack_origin if t < br + 0.5 else n_ + Vector((0, 0, 1.2))
            face = dict(SF["scared"])
            face["m_o"] = 0.2
            if br + 0.3 < t < br + 1.1:
                _run(pz, t, br + 0.3, 1.8, k=0.35 * (1 - ss(br + 0.9, br + 1.1, t)), steve=True)
            pz["arm_sr"] = {"fwd": 70 + 10 * go, "out": 60 - 35 * go, "elbow": 10}       # a hand out, then on his arm
            pz["arm_sl"] = {"fwd": 30, "out": 30, "elbow": 20}
            pz["hips_drop"] = 0.2 * ss(br + 1.0, br + 1.6, t)                          # braced
            pz["chest_lean"] = 8 * ss(br + 1.0, br + 1.6, t)
            if b("warp") - 0.2 <= t:                              # a forearm up against the flash
                k = ss(b("warp") - 0.2, b("warp") + 0.3, t)
                pz["arm_sl"] = {"fwd": lerp(30, 120, k), "out": lerp(30, 10, k), "elbow": lerp(20, 80, k)}
            if b("patch_archive") <= t:
                look_at = Vector(E.PA.root.location)
    tl, nd = _look(yaw, p, look_at, h=1.55, lim=80)
    if b("look") <= t < b("breach"):                              # the head leads, the shoulders follow
        pz["chest_twist"] = pz.get("chest_twist", 0) + 0.35 * tl
        tl *= 0.65
    pz["head_turn"], pz["head_nod"] = tl, nd + pz.get("head_nod", 0)
    pz = life(E, "steve", pz, face, t, 2.3)
    M.set_steve(E, p, yaw, pz, face, t)
    if tum > 0:                                                   # tumbling out of the warp
        S.holder.rotation_euler = (math.radians(70 * tum), math.radians(-40 * tum), math.radians(yaw))


def _kneel(lib, k, imp=0.0):
    """Steve on one knee (his right knee down, his left foot planted in front), k 0..1; imp: the landing's dip."""
    pz = _crouch(lib, k)
    pz["hips_drop"] = (0.95 + 0.12 * imp) * k
    pz["chest_lean"] = (22 + 14 * imp) * k
    pz["head_nod"] = (10 + 14 * imp) * k
    pz["foot_sl"] = {"x": -0.12 * k, "y": -0.6 * k, "z": 0.0}
    pz["foot_sr"] = {"x": 0.14 * k, "y": 0.78 * k, "z": 0.0, "pitch": -55 * k}
    pz["arm_sl"] = {"fwd": 30 * k, "out": 18, "elbow": 45 * k}          # a hand on the front knee
    pz["arm_sr"] = {"fwd": (25 + 15 * imp) * k, "out": 26, "elbow": 15}  # the other hand down to the floor
    return pz


def _crouch(lib, k):
    from ep09_new import flat, unflat
    c = flat(lib["crouch"])
    i = flat(lib["idle (Benly 2.2)"])
    out = {key: lerp(i.get(key, 0.0), v, k) if isinstance(v, (int, float)) else v for key, v in c.items()}
    return unflat(out)


# ------------------------------------------------------------------ apply
def apply(E, t):
    _use(E)
    prepare(E)
    E._t_now = t
    name, t0, t1 = which(t)
    E.cam_loc_now = _cam(E, t, name, t0, t1)[0]
    fx(E, t)
    patch(E, t)
    steve(E, t)
    noob(E, t)
    ghost(E, t)
    residue(E, t)
    core(E, t)
    snow(E, t)
    bpy.context.view_layer.update()
    warp(E, t)
    camera(E, t, name, t0, t1)
    E.PA.beam.hide_render = True
    # the wash: Ep6's cyan-white flash fading down at the start; Patch's flash at the end
    w = 1.0 - ss(0.0, b("wash", 1) + 0.15, t)
    w = max(w, ss(b("flash") - 0.12, b("flash") + 0.02, t))
    E2.set_wash(E, w)
    WASH[0] = w


# ------------------------------------------------------------------ the camera
def camera(E, t, shot, t0, t1):
    from ep10_p2_omg import handheld
    loc, look, lens, fstop, focus, shake = _cam(E, t, shot, t0, t1)
    land = b("tumble") + 0.45
    shake += 0.8 * math.exp(-max(0.0, t - land) * 6) * (t >= land)
    shake += 1.6 * ss(b("breach"), b("breach") + 0.3, t)
    y1, p1, r1 = handheld(t, shake)
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = M.P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1))
    E.cam.data.lens = lens
    E.cam.data.dof.use_dof = fstop < 30
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.cam.data.clip_end = 2000.0
    S_ = Vector(E.S.holder.location)
    N_ = Vector(E.N.root.location)
    tgt = (S_ + N_) / 2 + Vector((0, 0, 1.3))
    if shot in ("s9a",):
        tgt = Vector(E.PA.root.location)
    E.key.location = loc + (tgt - loc) * 0.35 + Vector((0.6, 0, 1.4))
    E.key.rotation_euler = (tgt - E.key.location).to_track_quat("-Z", "Y").to_euler()
    E.key.data.energy = 220.0


def _c(x, y, z):
    return Vector((x, y, z))


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus or None, handheld). Time only (shards start anywhere)."""
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, t0 + 3, t)
    if shot == "s1":                                              # 28 mm wide, low: the arrival; a slow push-in
        return _c(-1.2, -8.0, 1.1).lerp(_c(-0.6, -6.6, 1.2), u), _c(1.0, 2.0, 1.1), 28, 30, None, 0.15
    if shot == "s2":                                              # 35 mm medium-wide: the pair left, the replay right
        return _c(7.0, -5.6, 1.9), _c(1.7, 2.3, 1.05), 32, 30, None, 0.1
    if shot == "s3":                                              # 50 mm MCU Steve, front-left; he looks down
        s = S_STAND
        return s + _c(0.7, 3.3, 1.55), s + _c(0.1, 0, 1.4), 45, 2.8, None, 0.06
    if shot == "s4":                                              # 40 mm: a slow tilt down onto the cubes; Patch in
        c = CUBES[1]
        lk = (c + _c(0, 0, 1.4)).lerp(c + _c(-0.2, 0, 0.25), ss(t0, t0 + 2.2, t))
        return c + _c(-1.6, -3.4, 1.5), lk, 40, 4.0, None, 0.05
    if shot == "s5":                                              # 24 mm crane drop through the layers to the core
        k = ss(t0, t0 + 4.0, t)
        loc = _c(3.0, -1.5, 2.6).lerp(_c(6.5, 1.5, -24.0), k ** 1.3)
        lk = (N_EDGE + _c(1.0, 2.0, -0.5)).lerp(CORE, ss(t0, t0 + 1.6, t))
        if t >= b("noob_where") - 0.1:                            # up at the Noob leaning over the edge, through the glass
            loc = N_EDGE + _c(1.7, 3.3, -2.4)                    # under the glass, up at his face; then down to the core
            lk = (N_EDGE + _c(0, 0, 1.3)).lerp(CORE + _c(0, 0, 2.0), ss(b("core"), b("core") + 0.6, t))
        return loc, lk, 24, 30, None, 0.05
    if shot == "s6":                                              # 45 mm past the recorded trio toward its fissure
        return CELL_P + _c(-4.2, -6.4, 1.7).lerp(_c(-3.6, -5.6, 1.7), u), CELL_P + _c(0.3, 1.6, 1.4), 45, 5.0, None, 0.05
    if shot == "s7":                                              # 65 mm close-up on the Noob (the cell behind camera)
        n = Vector(E.N.root.location)
        n0 = Vector((0.9, 0.9, 0))
        d = (CELL_P - n0).normalized()
        return n0 + d * 3.4 + _c(0, 0, 1.85), n0 + _c(0, 0, 1.72), 65, 2.4, None, 0.04
    if shot == "s8":                                              # 24 mm: one continuous crane pullback, high and wide
        k = ss(t0, b("crowd", 1), t)
        loc = _c(-3.0, 3.8, 1.8).lerp(_c(-30.0, 34.0, 36.0), k ** 1.5)
        lk = _c(-0.4, 0.8, 1.3).lerp(_c(8.0, -12.0, 0.0), k)
        return loc, lk, 24, 30, None, 0.03
    if shot == "s9a":                                             # 85 mm, shallow focus: Patch alone, centred
        pp = P_WEIGHT
        return pp + _c(-0.8, -3.7, 0.1), pp, 85, 2.0, None, 0.02
    if shot == "s9b":                                             # 50 mm two-shot: the Noob looks out; Steve's glance
        return _c(3.6, 5.2, 1.6), _c(0.1, 0.7, 1.35), 50, 3.5, None, 0.04
    if shot == "s10":                                             # 28 mm wide, low: the breach, the warp
        return _c(-1.4, -6.0, 2.6).lerp(_c(-1.8, -7.2, 2.9), ss(t0, b("flash"), t)), _c(0.3, 0.9, 0.6), 28, 30, None, 0.12
    return _c(-1, -8, 2), _c(0, 1, 1), 28, 30, None, 0.1


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
    _use(E)
    E.G_scale = E.G.root.scale.x
    E.force = bool(a.times)
    E.mouth = {}
    voice = a.voice if os.path.exists(a.voice) else os.path.join(os.path.dirname(a.voice), "audio.wav")
    if os.path.exists(voice):
        from ep09_new import _lipsync
        E.mouth = _lipsync(tl, voice)
    E.cuts = sorted(t0 for _, t0 in shot_bounds())
    M._render(E, frames, out, apply, finish_grid)


WASH = [0.0]        # the lens wash this frame: the fog stays off it (the mist pass looks through the sheet)


def finish_grid(path, mist_path):
    """The depth fog: far things fade into the cyan-navy mist (the mist pass), then the movie's grade."""
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    if mist_path and os.path.exists(mist_path):
        m = np.asarray(Image.open(mist_path).convert("L").resize(im.size)).astype(np.float32) / 255.0
        fog = np.array([int(h, 16) for h in ("0E", "2C", "44")], np.float32)          # the mist (#0A2438, a touch lifted)
        k = np.clip(m, 0, 1)[..., None] ** 1.3 * 0.85 * (1.0 - WASH[0])
        a = a * (1 - k) + fog * k
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    import assemble
    assemble.W, assemble.H = im.size
    assemble.grade(im, {"saturation": 1.15, "glow": 0.6, "threshold": 0.65}, 0, 0, None)
    im.save(path)


if __name__ == "__main__":
    main()
