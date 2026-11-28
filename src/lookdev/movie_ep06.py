"""The movie, chapter 6 ("The World Started Deleting Itself"), in the new look and in 16:9.

The creator's rewritten blueprint (2026-11-27, story/movie/ep06_shots.md). It picks up Episode 5's last instant (the
Noob on the blue terrace, scared, the hammer in his fist; Steve on the grey pad; Patch by the Noob; the dragon sealed
in crystal over the pad; the door open at the terrace's edge; REALITY 71%). An unseen Void Wall (no Null on screen)
rolls in from the east, beyond where Ep5's checkpoint stones vanished: a pitch-black hole in reality with a jagged,
crackling magenta-checker edge; its crest curls over the sky and erases the dragon tail to head. Steve's pickaxe,
the Noob's stone wall and the TNT are erased in turn (Ep5's one erase rule). Patch scans the edge ("it's
correcting"). The Noob's "...Hi?" into the black; the black answers in his own voice (a static ripple, no body, no
face). The wall surges over the grey pad and bites the terrace's corner; Patch warps them out in a cyan flash.
Sound and timing: episodes/movie_ep06_deleting_itself.json (movie/ep06).

    python src/lookdev/movie_ep06.py TIMELINE VOICE TEX_DIR ASSETS OUT_DIR [--times 1.0,5.0] [--res 720]
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
import movie_ep05 as E5                                               # noqa: E402
from ep10_entrance import FPS, lerp, ss                              # noqa: E402

B = M.B
_yaw, _wrap, _clamp, _cr = E2._yaw, E2._wrap, E2._clamp, E2._cr
life = E2.life
_face_to, _look, _run = E3._face_to, E3._look, E3._run
EP5_TL = os.path.join(HERE, "..", "..", "movie", "ep05", "timeline.json")
FAR = (0, 0, -300)

# ------------------------------------------------------------------ the place (metres, z up; the cameras look north)
N0 = Vector((-5.4, -1.3, 0.0))           # the Noob at Ep5's end (on the terrace)
S0 = Vector((-2.35, -1.2, 0.0))          # Steve at Ep5's end (the grey pad)
P0 = Vector((-7.1, -1.7, 2.57))          # Patch at Ep5's end
N_EDGE = Vector((-4.6, -1.0, 0.0))       # the Noob at the terrace's east edge, facing the void
N_BACK = Vector((-6.7, -0.7, 0.0))       # where he stumbles back to at the surge
S_T = Vector((-5.2, 1.0, 0.0))         # Steve on the terrace, beside the Noob (he hops the gap before the "...Hi?")
P_NEAR = Vector((-6.3, -2.35, 2.35))     # Patch hovering by them
P_SCAN = Vector((-3.4, -2.3, 2.7))       # Patch banked forward, scanning the void's edge
P_WARP = Vector((-5.6, -0.75, 1.95))     # Patch between them for the warp
BARRIER_C = Vector((2.55, -0.1, 1.5))    # the Noob's stone wall: on the grey pad's east edge (the edge facing the void)
BARRIER_S = (0.6, 4.6, 3.0)
DRAGON_C = Vector((-1.0, 0.8, 5.17))     # the sealed dragon (over the grey pad)


def b(name, i=0):
    return B[name][i]


# ------------------------------------------------------------------ the Void Wall's motion (time only)
def void_x(t):
    """The wall's foot (x of its face at y = 0): 8 m off the grey pad's east edge (x 3) at the start, drifting in; it
    lurches into the Noob's stone wall (x 2.9) on the glide and holds there, creeping; it surges over the grey pad at
    the end."""
    x = lerp(11.0, 8.6, ss(0.0, b("glide"), t))
    x = lerp(x, 3.05, ss(b("glide"), b("glide", 1), t))
    x = lerp(x, 2.55, ss(b("glide", 1), b("surge"), t))
    x = lerp(x, -3.2, ss(b("surge"), b("surge") + 0.6, t))
    return x


def void_top(t):
    """The height where the face turns into the crest: it rises out of the haze as it rolls in."""
    return lerp(-25.0, 13.0, ss(b("void_in") - 0.2, b("void_in", 1) + 0.2, t))


def void_reach(t):
    """How far the crest curls west over the sky from the face: out to the dragon, then held over the arena."""
    x0 = void_x(t)
    r = lerp(0.0, 6.0, ss(b("void_in") + 0.6, b("void_in", 1), t))
    r = lerp(r, x0 - 1.5, ss(b("void_in", 1) - 0.3, b("dragon_gone") + 0.35, t))   # its edge reaches the dragon
    r = lerp(r, max(2.0, x0 - 5.0), ss(b("dragon_gone", 1) - 0.2, b("noob_delete", 1), t))   # pulls back: overcast
    r = lerp(r, max(r, x0 + 1.5), ss(b("bank"), b("hush"), t))    # by the "...Hi?" the sky is almost gone
    return r


def void_droop(t):
    """The crest's tip dips to touch the dragon, then lifts back."""
    return 1.5 + 7.5 * ss(b("void_in", 1) - 0.3, b("dragon_gone") + 0.35, t) * (1 - ss(b("dragon_gone", 1) - 0.2, b("noob_delete", 1), t))


def void_bulge(y, t):
    """The surge's tongue: the wall bites further in at the terrace's front corner."""
    k = ss(b("surge") + 0.1, b("surge") + 0.7, t)
    return 1.0 * k * math.exp(-((y + 2.6) / 1.5) ** 2)


def _hash(*a):
    h = 0
    for v in a:
        h = (h * 1000003 + int(v) * 7919 + 12345) & 0xFFFFFFFF
    return ((h * 2654435761) & 0xFFFFFFFF) / 4294967295.0


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    t5 = json.load(open(EP5_TL))
    E = E5.build(t5, tex_dir, assets, res, samples)               # Episode 5's world, rigs and props
    E.B6 = {k: tuple(v) for k, v in tl["beats"].items()}
    E.T5 = t5["length"]
    _void(E)
    _debris(E)
    _ripple(E)
    _void_light(E)
    _barrier(E)
    _tnt(E, assets)
    _sparks(E)
    _warp6(E)
    L = bpy.data.lights.new("pick_light", "POINT")
    L.energy, L.color, L.shadow_soft_size = 60.0, (1.0, 0.92, 0.85), 0.3
    E.pick_light = bpy.data.objects.new("pick_light", L)
    E.sc.collection.objects.link(E.pick_light)
    E.pick_light.location = FAR
    _flash_colour(E)
    E.erasable = {}
    E.prepped6 = False
    return E


def _use(E, which):
    B.clear()
    B.update(E.B6 if which == 6 else E.B5)


# -------- the wall
NU, NV = 96, 64                           # columns along y, rows up the profile
Y0, Y1 = -26.0, 30.0
WRAP = 0.02                               # the face curves round the arena at both ends (its edges never show)


def _void_mat():
    """Pure black (a hole in reality: no light comes off it), and near the crest's tip a crackling rim: pink-and-black
    checkerboard glowing (strength 3), torn with transparency."""
    m = bpy.data.materials.new("void_wall")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    N, L = nt.nodes.new, nt.links.new
    uv = N("ShaderNodeUVMap")
    sep = N("ShaderNodeSeparateXYZ")
    L(uv.outputs["UV"], sep.inputs[0])
    black = N("ShaderNodeBsdfPrincipled")
    black.inputs["Base Color"].default_value = (0, 0, 0, 1)
    black.inputs["Roughness"].default_value = 1.0
    black.inputs["Specular IOR Level"].default_value = 0.0
    geo = N("ShaderNodeNewGeometry")
    ck = N("ShaderNodeTexChecker")
    ck.inputs["Color1"].default_value = (1.0, 0.0, 0.85, 1)
    ck.inputs["Color2"].default_value = (0.02, 0.0, 0.02, 1)
    ck.inputs["Scale"].default_value = 1.6
    L(geo.outputs["Position"], ck.inputs["Vector"])
    em = N("ShaderNodeEmission")
    L(ck.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 3.0
    rim = N("ShaderNodeMath")
    rim.operation = "GREATER_THAN"
    L(sep.outputs["X"], rim.inputs[0])
    rim.inputs[1].default_value = 0.965
    mix = N("ShaderNodeMixShader")
    L(rim.outputs[0], mix.inputs[0])
    L(black.outputs[0], mix.inputs[1])
    L(em.outputs[0], mix.inputs[2])
    # torn: the outermost band is holed by blocky noise
    vox = N("ShaderNodeVectorMath")
    vox.operation = "SNAP"
    vox.inputs[1].default_value = (0.5, 0.5, 0.5)
    L(geo.outputs["Position"], vox.inputs[0])
    wn = N("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    L(vox.outputs[0], wn.inputs["Vector"])
    outer = N("ShaderNodeMath")
    outer.operation = "GREATER_THAN"
    L(sep.outputs["X"], outer.inputs[0])
    outer.inputs[1].default_value = 0.985
    holes = N("ShaderNodeMath")
    holes.operation = "LESS_THAN"
    L(wn.outputs["Value"], holes.inputs[0])
    holes.inputs[1].default_value = 0.55
    both = N("ShaderNodeMath")
    both.operation = "MULTIPLY"
    L(outer.outputs[0], both.inputs[0])
    L(holes.outputs[0], both.inputs[1])
    tr = N("ShaderNodeBsdfTransparent")
    mix2 = N("ShaderNodeMixShader")
    L(both.outputs[0], mix2.inputs[0])
    L(mix.outputs[0], mix2.inputs[1])
    L(tr.outputs[0], mix2.inputs[2])
    out = N("ShaderNodeOutputMaterial")
    L(mix2.outputs[0], out.inputs["Surface"])
    return m


def _void(E):
    me = bpy.data.meshes.new("void_wall")
    verts, faces = [], []
    for i in range(NU):
        for j in range(NV):
            verts.append((0.0, 0.0, 0.0))
    for i in range(NU - 1):
        for j in range(NV - 1):
            a = i * NV + j
            faces.append((a, a + NV, a + NV + 1, a + 1))
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            i, j = divmod(vi, NV)
            uvl.data[li].uv = (j / (NV - 1), i / (NU - 1))
    me.materials.append(_void_mat())
    ob = bpy.data.objects.new("void_wall", me)
    E.sc.collection.objects.link(ob)
    ob.visible_shadow = False                    # it is a hole, not a roof: the light is set by hand (void_light)
    for k in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        if hasattr(ob, k):
            setattr(ob, k, False)
    E.void = ob
    E.void_co = [0.0] * (NU * NV * 3)


def _profile(x0, ztop, reach, droop, s):
    """The wall's section at parameter s (0 the foot far below, 1 the crest's tip): straight up, a quarter turn of
    radius 3, then west along the sky, drooping toward the tip. Returns (x, z)."""
    R = 3.0
    zb = -45.0
    up = ztop - zb
    arc = math.pi * R / 2
    total = up + arc + max(0.01, reach)
    d = s * total
    if d <= up:
        return x0, zb + d
    d -= up
    if d <= arc:
        a = d / R
        return x0 - R + R * math.cos(a), ztop + R * math.sin(a)
    d -= arc
    u = d / max(0.01, reach)
    return x0 - R - d, ztop + R - droop * u * u


def void_shape(E, t):
    """Every vertex from time alone: the face at void_x (concave toward the arena, a little), the crest curling west,
    a blocky jagged tip that twitches every few frames, the surge's tongue."""
    if t < b("void_in") - 0.25:
        E.void.location = FAR
        return
    E.void.location = (0, 0, 0)
    x0, zt, rc = void_x(t), void_top(t), void_reach(t)
    step = int(t * FPS) // 3
    droop = void_droop(t)
    co = E.void_co
    for i in range(NU):
        y = Y0 + (Y1 - Y0) * i / (NU - 1)
        blk = math.floor((y + 100) / 1.1)
        jag = 1.6 * (_hash(blk, step // 2) - 0.5) + 0.8 * (_hash(blk * 3 + 1, step) - 0.5)
        xf = x0 - WRAP * y * y - void_bulge(y, t)
        r = max(0.01, rc + jag)
        far_y = ss(14.0, 30.0, abs(y - 2.0))                    # the crest lower toward the ends
        for j in range(NV):
            s = j / (NV - 1)
            x, z = _profile(xf, zt - 6.0 * far_y, r, droop + 3 * far_y, s)
            if j == NV - 1:                                       # the tip: blocky, stepped in z too
                z += 0.7 * (_hash(blk * 7, step) - 0.5)
            k = (i * NV + j) * 3
            co[k], co[k + 1], co[k + 2] = x, y, z
    E.void.data.vertices.foreach_set("co", co)
    E.void.data.update()


def void_look(t):
    """Where someone looking at the wall looks: high on its face, in front of them (never behind)."""
    return Vector((void_x(t) - 1.0, -1.0, 2.0 + 0.5 * void_top(t)))


def crest_tip(E, t, y=0.8):
    """Where the crest's tip is at a given y (for the dragon's erase, the debris, Patch's scan target)."""
    x0, zt, rc = void_x(t), void_top(t), void_reach(t)
    droop = void_droop(t)
    x, z = _profile(x0 - WRAP * y * y, zt, rc, droop, 1.0)
    return Vector((x, y, z))


def face_edge(E, t, y, z):
    """A point on the wall's face (its edge where it meets the arena, for the scan)."""
    return Vector((void_x(t) - WRAP * y * y - void_bulge(y, t) - 0.05, y, z))


# -------- debris, the ripple, the light
def _debris(E):
    """Cubes torn off at the edge: pink-and-black checker, glowing; they drift up and spin."""
    m = bpy.data.materials.new("void_debris")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Color1"].default_value = (1.0, 0.0, 0.85, 1)
    ck.inputs["Color2"].default_value = (0.02, 0.0, 0.02, 1)
    ck.inputs["Scale"].default_value = 2.0
    nt.links.new(tc.outputs["Generated"], ck.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 3.0
    nt.links.new(ck.outputs["Color"], em.inputs["Color"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    E.debris = []
    for k in range(70):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"void_debris_{k}"
        ob.data.materials.append(m)
        ob.visible_shadow = False
        ob.location = FAR
        E.debris.append(ob)


def debris(E, t):
    if t < b("void_in"):
        for ob in E.debris:
            ob.location = FAR
        return
    r = random.Random(11)
    for k, ob in enumerate(E.debris):
        life_ = r.uniform(2.0, 4.0)
        ph = r.uniform(0, life_)
        u = ((t + ph) % life_) / life_
        cyc = int((t + ph) // life_)
        rr = random.Random(k * 977 + cyc)
        y = rr.uniform(-14, 22)
        on_tip = k % 3 != 0
        if on_tip:                                                   # off the crest's tip, falling up and away
            p = crest_tip(E, t, y) + Vector((rr.uniform(-0.6, 0.6), 0, rr.uniform(-0.4, 0.4)))
            p += Vector((-0.5 * u, rr.uniform(-0.3, 0.3) * u, 1.6 * u))
        else:                                                        # off the face, near the pads, rising
            z = rr.uniform(-6, 6)
            p = face_edge(E, t, y, z) + Vector((-0.4 - 0.8 * u, 0, 2.2 * u))
        s = rr.uniform(0.12, 0.45) * math.sin(math.pi * min(1.0, u * 1.3)) ** 0.5
        ob.location = p
        ob.scale = (s, s, s)
        ob.rotation_euler = (t * 2 + k, t * 1.3 + k * 0.5, k)


def _ripple(E):
    """The static ripple in the black (the void's "...Hi?"): a thin sheet just in front of the wall's face, a
    stretched horizontal band of noisy lines, pale magenta and white; invisible except on the word."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = "void_ripple"
    m = bpy.data.materials.new("void_ripple")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    N, L = nt.nodes.new, nt.links.new
    tc = N("ShaderNodeTexCoord")
    mp = N("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 45.0, 1.0)
    L(tc.outputs["Generated"], mp.inputs["Vector"])
    wv = N("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "Y"
    wv.inputs["Scale"].default_value = 1.0
    wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 4.0
    L(mp.outputs["Vector"], wv.inputs["Vector"])
    nz = N("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 9.0
    L(mp.outputs["Vector"], nz.inputs["Vector"])
    mul = N("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    L(wv.outputs["Fac"], mul.inputs[0])
    L(nz.outputs["Fac"], mul.inputs[1])
    # a soft band in the middle (fades out to the sheet's edges)
    gr = N("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    mp2 = N("ShaderNodeMapping")
    mp2.inputs["Location"].default_value = (0.5, 0.5, 0)
    mp2.inputs["Scale"].default_value = (1.0, 7.0, 1.0)
    sub = N("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    L(tc.outputs["Generated"], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0)
    L(sub.outputs[0], mp2.inputs["Vector"])
    mp2.inputs["Location"].default_value = (0, 0, 0)
    L(mp2.outputs["Vector"], gr.inputs["Vector"])
    mul2 = N("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    L(mul.outputs[0], mul2.inputs[0])
    L(gr.outputs["Fac"], mul2.inputs[1])
    op = N("ShaderNodeValue")
    op.outputs[0].default_value = 0.0
    mul3 = N("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    L(mul2.outputs[0], mul3.inputs[0])
    L(op.outputs[0], mul3.inputs[1])
    clamp = N("ShaderNodeClamp")
    L(mul3.outputs[0], clamp.inputs["Value"])
    ramp = N("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (1.0, 0.35, 0.95, 1)
    ramp.color_ramp.elements[1].color = (1.0, 0.95, 1.0, 1)
    L(nz.outputs["Fac"], ramp.inputs["Fac"])
    em = N("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 4.0
    L(ramp.outputs["Color"], em.inputs["Color"])
    tr = N("ShaderNodeBsdfTransparent")
    mx = N("ShaderNodeMixShader")
    L(clamp.outputs[0], mx.inputs[0])
    L(tr.outputs[0], mx.inputs[1])
    L(em.outputs[0], mx.inputs[2])
    out = N("ShaderNodeOutputMaterial")
    L(mx.outputs[0], out.inputs["Surface"])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ob.location = FAR
    E.ripple = ob
    E.ripple_op = op.outputs[0]


def ripple(E, t):
    """Opacity 0 until the void's word; then 6-8 frames flickering unevenly between 0.2 and 0.7; back to 0."""
    w0 = b("void_hi") + 1.25                                       # the word (after the pre-echo)
    f = int(round((t - w0) * FPS))
    seq = [0.2, 0.7, 0.35, 0.65, 0.0, 0.55, 0.25, 0.6]
    if 0 <= f < len(seq):
        y, z = -1.0, 2.1
        E.ripple.location = face_edge(E, t, y, z) + Vector((-0.5, 0, 0))
        E.ripple.rotation_euler = (math.radians(90), 0, math.radians(90))
        E.ripple.scale = (9.0, 2.4, 1.0)
        E.ripple_op.default_value = seq[f] * 2.6
    else:
        E.ripple.location = FAR
        E.ripple_op.default_value = 0.0


def _void_light(E):
    """A soft magenta-violet light off the wall's edge onto the arena (the void's rim light on their faces)."""
    L = bpy.data.lights.new("void_light", "AREA")
    L.shape = "RECTANGLE"
    L.size, L.size_y = 14.0, 10.0
    L.color = (1.0, 0.25, 0.85)
    L.energy = 0.0
    ob = bpy.data.objects.new("void_light", L)
    E.sc.collection.objects.link(ob)
    E.vlight = ob


def light(E, t):
    """The sunlit sky eclipsed as the wall rolls over: the sun and sky down by half by the dragon's erase, more by the
    "...Hi?" (moody, the faces still readable); the magenta rim light growing as the wall comes closer."""
    k1 = ss(b("void_in"), b("dragon_gone", 1), t)
    k2 = ss(b("bank"), b("hush"), t)
    f = (1 - 0.5 * k1) * (1 - 0.3 * k2)
    E.sun.data.energy = E.sun_energy0 * 0.75 * f
    c0 = Vector(E.sun_col0).lerp(Vector((0.86, 0.9, 1.0)), 0.6)
    E.sun.data.color = tuple(c0.lerp(Vector((0.8, 0.82, 1.0)), 0.5 * k1))
    for n_, s0 in E.bgs:                                          # the sky seen and the fill it gives, both dimmed
        n_.inputs["Strength"].default_value = s0 * 0.85 * f
    x = void_x(t)
    E.vlight.location = (x - 1.0, -1.0, 4.5)
    E.vlight.rotation_euler = (0, math.radians(-90), 0)             # facing west, at the arena
    near = ss(12.0, 3.0, x - 3.0 + 12.0 * (1 - ss(b("void_in"), b("void_in", 1), t)))
    E.vlight.data.energy = 2200.0 * (0.25 + 0.75 * near) * ss(b("void_in"), b("void_in", 1), t)


# -------- the props
def _barrier(E):
    ob = E3.part(E, "void_barrier", BARRIER_C, BARRIER_S, "Dark stone grey", top=False)
    ob.location = FAR
    E.barrier = ob


def _face_uv_cube(name, mats):
    """A unit cube whose every face maps the whole texture (as a Minecraft block): mats = (side, top, bottom)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        n = f.normal
        f.material_index = 1 if n.z > 0.5 else 2 if n.z < -0.5 else 0
        # a square UV per face, upright on the sides
        ax = (0, 2) if abs(n.y) > 0.5 else (1, 2) if abs(n.x) > 0.5 else (0, 1)
        for lp in f.loops:
            co = lp.vert.co
            u = co[ax[0]] + 0.5
            v = co[ax[1]] + 0.5
            if abs(n.y) > 0.5 and n.y > 0 or abs(n.x) > 0.5 and n.x < 0:
                u = 1 - u
            lp[uv].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


def _block_mat(name, path):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(path)
    tx.interpolation = "Closest"
    nt.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.8
    bs.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    bs.inputs["Emission Strength"].default_value = 0.0
    return m, bs.inputs["Emission Strength"]


def _tnt(E, assets):
    d = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    side, e1 = _block_mat("tnt_side", os.path.join(d, "tnt_side.png"))
    top, e2 = _block_mat("tnt_top", os.path.join(d, "tnt_top.png"))
    bot, e3 = _block_mat("tnt_bottom", os.path.join(d, "tnt_bottom.png"))
    me = _face_uv_cube("tnt", (side, top, bot))
    ob = bpy.data.objects.new("tnt", me)
    E.sc.collection.objects.link(ob)
    ob.location = FAR
    E.tnt = ob
    E.tnt_glow = (e1, e2, e3)


def _sparks(E):
    m, mx, em = E3._emit_mat("tnt_spark", (1.0, 0.75, 0.25), 25.0)
    E.sparks6 = []
    for k in range(18):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"tnt_spark_{k}"
        ob.data.materials.append(m)
        ob.visible_shadow = False
        ob.location = FAR
        E.sparks6.append(ob)


def _warp6(E):
    """Patch's emergency warp: a cyan ring and a glowing sphere expanding from his chassis."""
    m = bpy.data.materials.new("warp6")
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.35, 0.95, 1.0, 1)
    em.inputs["Strength"].default_value = 6.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Fresnel"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16)
    sp = bpy.context.active_object
    sp.name = "warp6_sphere"
    sp.data.materials.append(m)
    sp.visible_shadow = False
    sp.location = FAR
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05, major_segments=64, minor_segments=8)
    ring = bpy.context.active_object
    ring.name = "warp6_ring"
    rm, _, _ = E3._emit_mat("warp6_ring", (0.4, 1.0, 1.0), 14.0)
    ring.data.materials.append(rm)
    ring.visible_shadow = False
    ring.location = FAR
    L = bpy.data.lights.new("warp6_light", "POINT")
    L.color = (0.35, 0.95, 1.0)
    L.energy = 0.0
    lo = bpy.data.objects.new("warp6_light", L)
    E.sc.collection.objects.link(lo)
    E.warp6 = (sp, ring, lo)


def _flash_colour(E):
    """Ep2's lens wash, recoloured cyan-white for the warp's flash (the chapter's last frames, which Ep7 opens on)."""
    m = bpy.data.materials.get("lens_wash")
    if not m:
        return
    for n_ in m.node_tree.nodes:
        if n_.type == "VALTORGB":
            n_.color_ramp.elements[0].color = (0.25, 0.9, 1.0, 1)
            n_.color_ramp.elements[1].color = (0.9, 1.0, 1.0, 1)
        if n_.type == "EMISSION":
            n_.inputs["Strength"].default_value = 1.6


# ------------------------------------------------------------------ the erase rule on anything
def _erasable(E, ob, axis):
    """Ep5's one erase rule on an object keeping its own look: its materials copied (object-level slots) with the
    checker front and the cut added along `axis` (world): where position . axis (+ a ragged noise) > e_hi it turns
    pink-and-black checkerboard (glowing), > e_cut it is gone. e_hi/e_cut are the object's properties."""
    key = (ob.name, tuple(round(a, 3) for a in axis))
    if key in E.erasable:
        return
    mats = []
    for s in ob.material_slots:
        m0 = s.material
        cache = f"{m0.name if m0 else 'none'}__er_{axis[0]:.2f}_{axis[1]:.2f}_{axis[2]:.2f}"
        m = bpy.data.materials.get(cache)
        if m is None:
            m = m0.copy() if m0 else bpy.data.materials.new(cache)
            m.name = cache
            m.use_nodes = True
            _add_erase(m, axis)
        mats.append(m)
    for s, m in zip(ob.material_slots, mats):
        s.link = "OBJECT"
        s.material = m
    ob["e_hi"], ob["e_cut"] = 1e4, 1e4
    E.erasable[key] = ob


def _add_erase(m, axis):
    nt = m.node_tree
    out = next((n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL" and n_.is_active_output), None) \
        or next((n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL"), None)
    if out is None:
        out = nt.nodes.new("ShaderNodeOutputMaterial")
    src = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
    N, L = nt.nodes.new, nt.links.new
    geo = N("ShaderNodeNewGeometry")
    dot = N("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    L(geo.outputs["Position"], dot.inputs[0])
    dot.inputs[1].default_value = axis
    nz = N("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    L(geo.outputs["Position"], nz.inputs["Vector"])
    rag = N("ShaderNodeMath")
    rag.operation = "MULTIPLY_ADD"
    L(nz.outputs["Fac"], rag.inputs[0])
    rag.inputs[1].default_value = 0.25
    rag.inputs[2].default_value = -0.125
    v = N("ShaderNodeMath")
    v.operation = "ADD"
    L(dot.outputs["Value"], v.inputs[0])
    L(rag.outputs[0], v.inputs[1])

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

    ck_mask = gt(v.outputs[0], attr("e_hi"))
    cut_mask = gt(v.outputs[0], attr("e_cut"))
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
    if src is not None:
        L(src, m1.inputs[1])
    L(em.outputs[0], m1.inputs[2])
    tr = N("ShaderNodeBsdfTransparent")
    m2 = N("ShaderNodeMixShader")
    L(cut_mask, m2.inputs[0])
    L(m1.outputs[0], m2.inputs[1])
    L(tr.outputs[0], m2.inputs[2])
    L(m2.outputs[0], out.inputs["Surface"])


def _span(ob, axis):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    ds = [p.dot(Vector(axis)) for p in pts]
    return min(ds), max(ds)


def erase_set(obs, axis, t, t0, dur, lo=None, hi=None, stop=None):
    """The erase rule over [t0, t0 + dur] along `axis` (from the high end to the low end): the checker front first,
    the cut trailing it. stop: the cut halts there (a bite, not the whole thing)."""
    for ob in obs:
        a, z = _span(ob, axis) if lo is None else (lo, hi)
        if stop is not None:
            a = stop
        h = z - a
        u = (t - t0) / dur
        if u < 0:
            ob["e_hi"], ob["e_cut"] = 1e4, 1e4
            continue
        ob["e_hi"] = z + 0.2 - (h + 0.35) * ss(0.0, 0.6, u)
        ob["e_cut"] = z + 0.35 - (h + 0.5) * ss(0.25, 1.0, u)


# ------------------------------------------------------------------ prepare (measured once, every shard)
X_AXIS = (1.0, 0.0, 0.0)
UP_AXIS = (0.0, 0.0, -1.0)                 # bottom to top (the dot is -z: the front rises)
DIAG = (0.7071, -0.7071, 0.0)              # the terrace's front-east corner


def prepare(E):
    if E.prepped6:
        return
    E.prepped6 = True
    _use(E, 5)
    E5.apply(E, E.T5)                                             # Ep5's last instant (its own prepare runs inside)
    _use(E, 6)
    by = {ob.name: ob for ob in bpy.data.objects}
    E.d_meshes = list(E.D.meshes)
    E.shells = [sh for sh, *_ in E.shell]
    for ob in E.d_meshes + E.shells:
        _erasable(E, ob, X_AXIS)
    E.pick6 = next(ob for ob in bpy.data.objects if ob.name.startswith("item_iron_pickaxe") and ob.parent is not None
                   and ob.parent.name == E.S.arm.name)
    _erasable(E, E.pick6, X_AXIS)
    _erasable(E, E.barrier, UP_AXIS)
    _erasable(E, E.tnt, X_AXIS)
    E.cobbles = [ob for ob in bpy.data.objects if ob.name.startswith("cobble_") and ob.type == "MESH"]
    for ob in E.cobbles:
        _erasable(E, ob, X_AXIS)
    w = bpy.context.scene.world
    E.bgs = [(n_, n_.inputs["Strength"].default_value) for n_ in w.node_tree.nodes if n_.type == "BACKGROUND"] if w else []
    E.pad_obs = [by[n] for n in by if n == "spawn" or n == "spawn_plate" or n.startswith("spawn_mark_")]
    for ob in E.pad_obs:
        _erasable(E, ob, X_AXIS)
    E.terrace = by["terrace"]
    _erasable(E, E.terrace, DIAG)
    for ob in E.ham_parts:
        _erasable(E, ob, DIAG)
    # the pickaxe's release: where it leaves his hand (posed once)
    t_rel = b("throw") + 0.14
    steve(E, t_rel)
    bpy.context.view_layer.update()
    E.pick_rel = E.pick6.matrix_world.copy()
    # the hammer's drop: where it leaves his fist
    t_drop = b("disbelief") + 0.05
    patch(E, t_drop)
    noob(E, t_drop)
    bpy.context.view_layer.update()
    E.ham_drop = E.ham.matrix_world.copy()
    E.ham_scale = E.ham.scale.copy()
    # the TNT's release
    t_tr = b("tnt_throw") + 0.18
    steve(E, t_tr)
    bpy.context.view_layer.update()
    E.tnt_rel = _steve_hand(E) + Vector((0, 0, 0.1))


def _steve_hand(E, side="sr"):
    return M.P6._steve_hand(E.S, side)


# ------------------------------------------------------------------ the shots
SHOTS = [("s1", "open", 0), ("s1n", "noob_delete", -0.1), ("s2", "resolve", 0), ("s3a", "windup", 0),
         ("s3b", "throw", 0.05), ("s3c", "blink", 0), ("s4", "raise", 0), ("s4s", "steve_nowall", -0.2),
         ("s5a", "tnt_pull", 0), ("s5b", "tnt_throw", 0.1), ("s6", "bank", 0), ("s7a", "hush", 0),
         ("s7b", "listen", 0), ("s8", "stare", 0.3)]


def shot_bounds():
    return [(name, b(beat) + off) for name, beat, off in SHOTS]


def which(t):
    bs = shot_bounds()
    for i, (name, t0) in enumerate(bs):
        t1 = bs[i + 1][1] if i + 1 < len(bs) else 1e9
        if t < t1:
            return name, t0, t1
    return bs[-1][0], bs[-1][1], 1e9


# ------------------------------------------------------------------ the dragon, the pads, the props
def dragon(E, t):
    """Sealed as Ep5 left it; the crest's edge touches its east end and it erases east to west (tail to head), dead
    pixels rising off it."""
    t0, dur = b("dragon_gone") + 0.1, 1.35
    _reassert(E, E.d_meshes + E.shells, X_AXIS)
    lo = min(_span(ob, X_AXIS)[0] for ob in E.d_meshes + E.shells)
    hi = max(_span(ob, X_AXIS)[1] for ob in E.d_meshes + E.shells)
    erase_set(E.d_meshes + E.shells, X_AXIS, t, t0, dur, lo, hi)
    _reassert(E, E.cobbles, X_AXIS)                               # the cobblestones that hung round it go with it
    vis = [ob for ob in E.cobbles if ob.location.z > -100]
    if vis:
        clo = min(_span(ob, X_AXIS)[0] for ob in vis)
        chi = max(_span(ob, X_AXIS)[1] for ob in vis)
        erase_set(vis, X_AXIS, t, t0 + 0.45, 1.1, clo, chi)
        if t >= t0 + 1.7:
            for ob in vis:
                ob.location = FAR
    if t >= t0 + dur + 0.1:
        E.D.root.location = FAR
        for sh in E.shells:
            sh.hide_render = True
    return lo, hi


def _reassert(E, obs, axis):
    """Ep5's frame code puts the dragon's own material back each frame: the erase copies go back on."""
    for ob in obs:
        for s in ob.material_slots:
            m = s.material
            if m and "__er_" not in m.name:
                cache = f"{m.name}__er_{axis[0]:.2f}_{axis[1]:.2f}_{axis[2]:.2f}"
                if cache in bpy.data.materials:
                    s.link = "OBJECT"
                    s.material = bpy.data.materials[cache]


def pads(E, t):
    """The surge: the grey pad goes (east to west, as the wall rolls over it), and the wall bites the terrace's
    front-east corner (the Noob stumbles back from it)."""
    t0 = b("surge") + 0.05
    erase_set(E.pad_obs, X_AXIS, t, t0, 0.6)
    a, z = _span(E.terrace, DIAG)
    erase_set([E.terrace], DIAG, t, t0 + 0.25, 0.55, a, z, stop=z - 1.3)


def pickaxe(E, t):
    """In his fist until the release; then along a crisp arc toward the wall, spinning (-720 degrees over 12 frames);
    a 4-frame hit-freeze at the wall's face; checkerboard; gone."""
    pk = E.pick6
    tr = b("throw") + 0.14
    if t < tr:
        pk.hide_render = False
        pk["e_hi"], pk["e_cut"] = 1e4, 1e4
        E.pick_light.location = FAR
        if hasattr(E, "pick_fly"):
            E.pick_fly.location = FAR
        return
    if not hasattr(E, "pick_fly"):
        E.pick_fly = pk.copy()
        E.sc.collection.objects.link(E.pick_fly)
        E.pick_fly.parent = None
    pk.hide_render = True
    f = E.pick_fly
    th = b("pick_gone")                                           # the hit
    fr = 4.0 / FPS
    dur = th - tr
    p = pick_path(E, t)
    spin = -720.0 * ((min(t, th) - tr) / (12.0 / FPS))
    rot = E.pick_rel.to_3x3() @ Matrix.Rotation(math.radians(spin), 3, "X")
    if t >= th:                                                   # the hit-freeze: held exactly where it struck
        spin = -720.0 * (dur / (12.0 / FPS))
        rot = E.pick_rel.to_3x3() @ Matrix.Rotation(math.radians(spin), 3, "X")
    f.matrix_world = Matrix.Translation(p) @ rot.to_4x4() @ Matrix.Diagonal(E.pick_rel.to_scale()).to_4x4()
    if t >= th + fr:
        erase_set([f], X_AXIS, t, th + fr, 0.3)
    else:
        f["e_hi"], f["e_cut"] = 1e4, 1e4
    E.pick_light.location = p if t < th + fr + 0.3 else FAR
    if t >= th + fr + 0.35:
        f.location = FAR


def pick_path(E, t):
    """The pickaxe's arc from the release to the wall's face (time only; the release measured in prepare)."""
    tr = b("throw") + 0.14
    th = b("pick_gone")
    p0 = E.pick_rel.to_translation()
    tgt = face_edge(E, th, p0.y + 0.2, 3.1)
    u = max(0.0, min(1.0, (min(t, th) - tr) / (th - tr)))
    return p0.lerp(tgt, u) + Vector((0, 0, 2.4 * 4 * u * (1 - u)))


def barrier(E, t):
    """The Noob's wall: a crisp cyan box snaps on the grey pad's east edge; the stone wall drops into it (a thud, dust);
    the void glides into it and it dissolves bottom to top in one sweep, nothing left floating."""
    tb = b("build_wall") + 0.3                                    # the hammer's contact
    ob = E.barrier
    if t < tb + 0.08:
        ob.location = FAR
        return
    drop = ss(tb + 0.08, tb + 0.3, t)
    sq = 1.0 + 0.06 * math.sin(math.pi * ss(tb + 0.3, tb + 0.45, t)) * (t < tb + 0.45)
    ob.location = BARRIER_C + Vector((0, 0, 2.5 * (1 - drop) ** 2))
    ob.scale = (1.0, 1.0, 1.0 / sq)
    lo, hi = BARRIER_C.z - BARRIER_S[2] / 2, BARRIER_C.z + BARRIER_S[2] / 2
    erase_set([ob], UP_AXIS, t, b("wall_gone"), 1.2, -hi, -lo)
    if t >= b("wall_gone") + 1.3:
        ob.location = FAR


def gizmo(E, t):
    tb = b("build_wall") + 0.3
    specs = []
    if tb - 0.25 <= t < tb + 0.45:
        k = 1.0 if t < tb - 0.25 + 1.0 / FPS else 0.0
        size = tuple(s * 1.06 for s in BARRIER_S)
        specs.append({"m": Matrix.Translation(BARRIER_C), "size": size, "mode": "snap", "k": k, "w": 0.035})
    E.giz.draw(specs)


def hammer(E, t):
    """In his right fist (Ep5's); slips from his hand in the disbelief after the wall goes, falls flat on the terrace
    (nothing at his hip, nothing in the later shots); the surge's bite takes it."""
    td = b("disbelief") + 0.05
    if t < td:                                                    # in his fist (as Ep5 left it: shards start anywhere)
        E.ham.parent = E.N.arms["sr"]
        E.ham.matrix_parent_inverse = Matrix.Identity(4)
        E.ham.location = (0, -0.05, -1.38)
        E.ham.rotation_euler = (0, 0, 0)
        E.ham.scale = (1, 1, 1)
        for ob in E.ham_parts:
            ob["e_hi"], ob["e_cut"] = 1e4, 1e4
        return
    if not hasattr(E, "ham_fly"):
        E.ham_fly = bpy.data.objects.new("hammer_dropped", None)
        E.sc.collection.objects.link(E.ham_fly)
    E.ham.parent = None
    u = min(1.0, (t - td) / 0.38)
    m0 = E.ham_drop
    p0 = m0.to_translation()
    p1 = Vector((p0.x + 0.15, p0.y - 0.1, 0.06))
    p = p0.lerp(p1, u * u)
    q0 = m0.to_quaternion()
    q1 = Quaternion((0, 0, 1), math.radians(40)) @ Quaternion((1, 0, 0), math.radians(90))
    q = q0.slerp(q1, ss(0, 1, u))
    if u >= 1:
        p = p1 + Vector((0, 0, 0.05 * abs(math.sin(min(1.0, (t - td - 0.38) / 0.2) * math.pi)) * (t < td + 0.6)))
    E.ham.matrix_world = Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Diagonal(E.ham_drop.to_scale()).to_4x4()
    a, z = _span(E.terrace, DIAG)
    erase_set(E.ham_parts, DIAG, t, b("surge") + 0.3, 0.5, a, z, stop=z - 1.3)
    E.ham_light.data.energy = 25.0


def tnt(E, t):
    """Pulled from his side (his inventory), lit (sparks, the block flashing white as lit TNT does), thrown overhand in
    a high lob toward the wall; swelling white at its peak; the void snatches it: checkerboard, gone, no boom."""
    tp = b("tnt_pull")
    th = b("tnt_gone")
    tr = b("tnt_throw") + 0.18
    ob = E.tnt
    if t < tp + 0.3 or t >= th + 0.2:
        ob.location = FAR
        for e_ in E.tnt_glow:
            e_.default_value = 0.0
        return
    s = 0.55
    if t < tr:
        p = _steve_hand(E) + Vector((0, -0.05, 0.12))
        rot = Matrix.Rotation(math.radians(_face_to(S0, face_edge(E, t, -1, 2))), 4, "Z")
    else:
        p0 = E.tnt_rel
        p1 = face_edge(E, th, p0.y + 0.3, 2.6)
        u = min(1.0, (t - tr) / (th - tr))
        p = p0.lerp(p1, u) + Vector((0, 0, 3.2 * 4 * u * (1 - u)))
        rot = Matrix.Rotation(math.radians(200 * (t - tr)), 4, "Y") @ Matrix.Rotation(math.radians(90 * (t - tr)), 4, "Z")
        s = s * (1 + 0.35 * ss(th - 0.35, th, t))                 # swelling, about to go off
    lit = t >= tp + 0.5
    blink = 0.5 + 0.5 * math.sin((t - tp) * 2 * math.pi * (2.0 + 6.0 * ss(tr, th, t)))
    white = (2.5 * blink if lit else 0.0) + 14.0 * ss(th - 0.2, th, t) * (t < th + 0.05)
    for e_ in E.tnt_glow:
        e_.default_value = white
    ob.location = p
    ob.matrix_world = Matrix.Translation(p) @ rot @ Matrix.Diagonal((s, s, s, 1.0))
    erase_set([ob], X_AXIS, t, th + 0.03, 0.15)
    E.tnt_now = p


def sparks(E, t):
    tp = b("tnt_pull")
    th = b("tnt_gone")
    r = random.Random(3)
    for k, ob in enumerate(E.sparks6):
        if not (tp + 0.5 <= t < th) or not hasattr(E, "tnt_now"):
            ob.location = FAR
            continue
        per = r.uniform(0.25, 0.45)
        ph = r.uniform(0, per)
        u = ((t + ph) % per) / per
        cyc = int((t + ph) // per)
        rr = random.Random(k * 31 + cyc)
        d = Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(0.6, 1.6))).normalized()
        ob.location = E.tnt_now + Vector((0, 0, 0.32)) + d * 0.5 * u + Vector((0, 0, -0.3 * u * u))
        s = 0.03 * (1 - u)
        ob.scale = (s, s, s)


def pixels(E, t, d_span):
    """Dead pixels rising off what the void erases (the dragon, the pickaxe, the wall, the TNT, the pad)."""
    pool = E.pix5
    used = 0
    rnd = random.Random(5)
    lo, hi = d_span
    jobs = [(b("dragon_gone") + 0.1, 1.35, lambda u_, r_: Vector((lerp(hi, lo, u_) + r_.uniform(-0.5, 0.5), DRAGON_C.y + r_.uniform(-2.0, 2.0),
                                                                     DRAGON_C.z + r_.uniform(-1.2, 1.6))), 26, 0.12),
            (b("wall_gone"), 1.2, lambda u_, r_: Vector((BARRIER_C.x + r_.uniform(-0.3, 0.3), BARRIER_C.y + r_.uniform(-2.2, 2.2),
                                                       lerp(0.0, 3.0, u_))), 16, 0.09)]
    if hasattr(E, "pick_fly"):
        pf = face_edge(E, b("pick_gone"), E.pick_rel.to_translation().y + 0.2, 3.1)
        jobs.append((b("pick_gone") + 4.0 / FPS, 0.3, lambda u_, r_, pf=pf: pf + Vector((0, r_.uniform(-0.3, 0.3), r_.uniform(-0.3, 0.3))), 8, 0.06))
    for t0, dur, where, n, sz in jobs:
        if not t0 <= t < t0 + dur + 1.0:
            continue
        for k in range(n):
            if used >= len(pool):
                break
            ob = pool[used]
            used += 1
            st = t0 + dur * rnd.uniform(0.0, 0.9)
            u = (t - st) / 1.0
            if not 0 <= u < 1:
                ob.location = FAR
                continue
            base = where((st - t0) / dur, rnd)
            E5._pix(ob, base + Vector((0, 0, 1.8 * u)), sz * (1 - u), k + t)
    for ob in pool[used:]:
        ob.location = FAR


def warp(E, t):
    """Patch charges: a cyan ring spreading from his chassis, a sphere of light expanding until it fills the frame."""
    sp, ring, lo = E.warp6
    t0, t1 = b("warp"), b("flash")
    if t < t0:
        for o in (sp, ring):
            o.location = FAR
        lo.data.energy = 0.0
        return
    c = Vector(E.PA.root.location)
    u = ss(t0, t1 + 0.1, t)
    r = 0.3 + 9.0 * u ** 2.2
    sp.location = c
    sp.scale = (r, r, r)
    ring.location = c
    rr = 0.4 + 14.0 * ss(t0 + 0.2, t1, t)
    ring.scale = (rr, rr, rr)
    ring.rotation_euler = (math.radians(90), 0, math.radians(20))
    lo.location = c
    lo.data.energy = 300.0 + 5000.0 * u ** 2


# ------------------------------------------------------------------ Patch
def _patch_keys():
    T = b
    return [
        (0.0, P0),
        (T("void_in") + 0.4, P0),
        (T("void_in") + 1.6, P_NEAR),
        (T("bank"), P_NEAR),
        (T("bank") + 0.55, P_SCAN),                                # banks sharply forward at the edge
        (T("patch_correct") + 1.4, P_SCAN),
        (T("patch_correct", 1) + 0.2, P_NEAR + Vector((0.6, 0.0, 0.1))),
        (T("surge") + 0.5, P_NEAR + Vector((0.6, 0.0, 0.1))),
        (T("noob_copy") + 0.6, P_WARP),                            # whips between them and the collapsing edge
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
    """Patch_ScanTarget: a point sliding along the wall's jagged magenta edge (its face, at the arena's height)."""
    s0 = b("bank") + 0.5
    y = -2.0 + 2.6 * math.sin((t - s0) * 0.9)
    z = 1.6 + 1.2 * math.sin((t - s0) * 1.7)
    return face_edge(E, t, y, z)


def patch(E, t):
    from patch import set_patch
    P = E.PA
    p = patch_pos(t)
    dt = 0.04
    v = (patch_pos(t + dt) - patch_pos(t - dt)) / (2 * dt)
    a = (patch_pos(t + dt) - 2 * p + patch_pos(t - dt)) / (dt * dt)
    bob = 0.05 * math.sin((E.T5 + t) * 2.4) + 0.02 * math.sin((E.T5 + t) * 5.3 + 1)
    cam = Vector(E.cam_loc_now)
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.3))
    scanning = b("bank") + 0.5 <= t < b("patch_correct") + 1.6
    tgt = N_
    if t < b("bank"):
        tgt = void_look(t)
        if b("steve_stop") <= t:
            tgt = N_
        if b("windup") <= t < b("blink"):
            tgt = getattr(E, "pick_fly", E.pick6).matrix_world.to_translation() if t >= b("throw") else Vector(E.S.holder.location) + Vector((0, 0, 1.4))
        if b("build_wall") <= t < b("disbelief"):
            tgt = BARRIER_C
        if b("tnt_throw") <= t < b("whip"):
            tgt = getattr(E, "tnt_now", N_)
    if scanning:
        tgt = scan_target(E, t)
    if b("patch_correct") + 1.6 <= t:                              # rotates back toward them
        tgt = N_
    if b("surge") <= t:
        tgt = face_edge(E, t, -2.0, 1.0) if t < b("noob_copy") + 0.3 else N_
    if v.length > 0.8:
        tgt = p + v * 2
    to = tgt - p
    yaw = _yaw(Vector((to.x, to.y, 0)))
    if not scanning and v.length <= 0.8:
        tc = cam - p
        yaw = yaw + _wrap(_yaw(Vector((tc.x, tc.y, 0))) - yaw) * 0.3
    fw = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0))
    side = Vector((-fw.y, fw.x, 0))
    pitch = _clamp(-a.dot(fw) * 0.9 - v.dot(fw) * 4.0, -20, 20)
    roll = _clamp(a.dot(side) * 0.9, -20, 20)
    if scanning:
        pitch += 10.0
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
    ph = (E.T5 + t + 0.9) % per
    blink = math.exp(-((ph - 0.06) / 0.04) ** 2)
    vals = {"open": max(0.05, 1 - blink), "look_x": 0.0, "look_y": 0.0, "squint": 0.0, "wide": 0.9, "glitch": 0.0,
            "scan": 0.0, "smile": 0.0, "sad": 0.0}
    if t >= b("tnt_gone"):
        vals.update({"wide": 0.6, "squint": 0.2})
    if scanning:
        vals.update({"scan": 1.0, "wide": 0.5, "squint": 0.35})
    if b("patch_correct") <= t:                                    # the eye narrows with dread
        vals.update({"squint": 0.55, "wide": 0.2, "sad": 0.25})
        vals["open"] = max(0.05, 1 - blink) * (0.8 + 0.12 * talk)
    if b("surge") <= t:                                            # dilates wide
        vals.update({"squint": 0.0, "wide": 1.0, "sad": 0.0, "open": 1.0})
    if b("warp") <= t:
        vals["glitch"] = 0.5 if f % 2 else 0.2
    set_patch(P, vals)
    P.glow.data.energy = 12.0 + 60.0 * ss(b("warp"), b("flash"), t)
    if scanning:
        bpy.context.view_layer.update()
        o = P.root.matrix_world @ Vector((0, -0.55 * 0.42, 0.02 * 0.42))
        d = scan_target(E, t) - o
        q = d.to_track_quat("-Y", "Z")
        L_ = 3.0 * 0.42 * 3
        k = d.length / L_
        P.beam.matrix_world = Matrix.Translation(o) @ q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(8), 4, "X") \
            @ Matrix.Diagonal((1.0, k, k, 1.0))


# ------------------------------------------------------------------ the Noob
def noob(E, t):
    from ep09_new import NF
    p, yaw = N0.copy(), _face_to(N0, Vector((4.0, -1.0, 0)))
    face = dict(NF["scared"])
    pz = {"arm_sl": {"out": 25, "fwd": 25}, "arm_sr": {"out": 20, "fwd": 20}, "chest_lean": -6}
    S_ = Vector(E.S.holder.location) + Vector((0, 0, 1.4))
    look_at = void_look(t) if t >= b("void_in") else Vector((10.0, -1.0, 3.0))
    lim = 75
    if t < b("void_in") + 0.5:                                     # Ep5's last instant: scared, to Steve
        yaw = _face_to(N0, Vector(E5.STEVE_D))
        look_at = S_
        k = ss(b("void_in"), b("void_in") + 0.5, t)
        yaw = lerp(yaw, _face_to(N0, Vector((4.0, -1.0, 0))), k)
    elif t < b("resolve"):                                         # up at the wall's crest and the dragon going
        look_at = void_look(t) if not (b("dragon_gone") <= t < b("noob_delete")) else DRAGON_C
        pz["chest_lean"] = -12
        pz["arm_sl"] = {"fwd": 40, "out": 35, "elbow": 20}
        pz["arm_sr"] = {"fwd": 30, "out": 25, "elbow": 10}
        if b("noob_delete") - 0.1 <= t < b("noob_delete", 1) + 0.1:
            face = dict(NF["shout"])
            pz["arm_sl"] = {"fwd": 70, "out": 40, "elbow": 10}
    elif t < b("raise"):                                           # watching Steve: the throw
        look_at = S_ if t < b("throw") else getattr(E, "pick_fly", E.pick6).matrix_world.to_translation()
        yaw = _face_to(N0, Vector(E.S.holder.location)) * 0.5 + _face_to(N0, Vector((4.0, -1.0, 0))) * 0.5
        face = dict(NF["worried"])
        if t >= b("pick_gone"):
            face = dict(NF["shock"])
        if t >= b("steve_pick"):
            look_at = S_
            face = dict(NF["worried"])
    else:
        # to the terrace's east edge; the hammer up: "Wall!"
        k = ss(b("raise") - 0.35, b("raise") + 0.25, t)
        p = N0.lerp(N_EDGE, k)
        yaw = _face_to(p, Vector((4.0, -0.5, 0)))
        if 0.05 < k < 0.95:
            _run(pz, t, b("raise") - 0.35, 2.0, k=0.35, steve=False)
        look_at = BARRIER_C + Vector((0, 0, 0.5))
        if t < b("wall_gone"):
            face = dict(NF["happy"]) if b("noob_wall") - 0.1 <= t else dict(NF["worried"])
            if t < b("build_wall"):                                # the hammer raised
                r_ = ss(b("raise"), b("noob_wall"), t)
                pz["arm_sr"] = {"fwd": 40 + 120 * r_, "out": 15, "elbow": 30 * r_}
                pz["chest_lean"] = -6 * r_
                if b("noob_wall") <= t:
                    face = dict(NF["shout"])
            else:
                E5._swing(pz, t, b("build_wall"))
                pz["chest_lean"] = pz.get("chest_lean", 0)
                face = dict(NF["happy"])
                if t >= b("glide"):                                 # the confident grin, then the void glides in
                    face = dict(NF["happy"]) if t < b("glide") + 0.35 else dict(NF["worried"])
        elif t < b("tnt_pull"):                                    # the grin drops to pure disbelief; the hammer slips
            face = dict(NF["shock"])
            pz["arm_sr"] = {"fwd": 25 * (1 - ss(b("disbelief"), b("disbelief") + 0.3, t)) + 8, "out": 12, "elbow": 5}
            pz["arm_sl"] = {"fwd": 15, "out": 15}
            pz["chest_lean"] = -4
            if b("steve_nowall") <= t:
                look_at = S_
                face = dict(NF["shock"])
        elif t < b("bank"):                                        # the TNT: watching it fly; it is snatched; to Steve
            face = dict(NF["worried"])
            look_at = getattr(E, "tnt_now", S_) if b("tnt_throw") <= t < b("tnt_gone") + 0.3 else S_
            if b("tnt_gone") <= t:
                face = dict(NF["shock"])
            if b("whip") <= t:                                     # whips his head to Steve (head, then shoulders)
                look_at = S_
                yaw = lerp(yaw, _face_to(p, Vector(E.S.holder.location)), ss(b("whip") + 0.1, b("whip") + 0.5, t) * 0.6)
                face = dict(NF["shout"]) if b("noob_boom") <= t < b("noob_boom", 1) else dict(NF["shock"])
                pz["arm_sl"] = {"fwd": 55, "out": 35, "elbow": 20}
                pz["arm_sr"] = {"fwd": 45, "out": 30, "elbow": 20}
        elif t < b("hush"):                                        # Patch's scan; listening, scared
            look_at = Vector(E.PA.root.location)
            yaw = _face_to(p, Vector((4.0, -0.5, 0)))
            face = dict(NF["worried"])
            pz["arm_sl"] = {"fwd": 15, "out": 15}
            pz["arm_sr"] = {"fwd": 15, "out": 15}
        elif t < b("surge"):                                       # leans to the abyss; a tiny wave: "...Hi?"
            ln = ss(b("hush") + 0.1, b("noob_hi"), t)
            yaw = _face_to(p, Vector((4.0, -1.0, 0)))
            look_at = face_edge(E, t, -1.0, 2.0)
            face = {"both_to": -0.45, "both_ti": 0.25, "both_h": 1.75, "both_ps": 0.8, "m_arch": 0.12, "m_o": 0.08}
            if b("noob_hi") - 0.1 <= t < b("noob_hi", 1):
                face["m_o"] = 0.22
            pz["chest_lean"] = 12 * ln
            pz["head_nod"] = -4 * ln
            pz["shoulders"] = 0.6
            wv = ss(b("hush") + 0.5, b("noob_hi") + 0.1, t) * (1 - ss(b("listen") + 0.6, b("listen") + 1.1, t))
            pz["arm_sr"] = {"fwd": 30 + 55 * wv + 4 * math.sin((t - b("noob_hi")) * 14) * wv, "out": 10 + 12 * wv,
                            "elbow": 95 * wv}
            pz["arm_sl"] = {"fwd": 12, "out": 10, "elbow": 15}
            if b("void_hi") + 1.2 <= t:                             # it answered: frozen, wide eyes
                face = {"both_to": -0.45, "both_ti": 0.3, "both_h": 1.9, "both_w": 1.05, "both_ps": 0.7, "m_arch": 0.2, "m_o": 0.15}
                pz["chest_lean"] = 6
        else:                                                      # the surge: he stumbles back; "It's copying me!"
            k = ss(b("surge") + 0.2, b("surge") + 0.9, t)
            p = N_EDGE.lerp(N_BACK, k)
            yaw = _face_to(p, Vector((4.0, -1.5, 0)))
            look_at = face_edge(E, t, -2.0, 1.0)
            if 0.05 < k < 0.95:
                _run(pz, t, b("surge") + 0.2, -1.6, k=0.45, steve=False)
            pz["chest_lean"] = -14
            pz["arm_sl"] = {"fwd": 60, "out": 40, "elbow": 20}
            pz["arm_sr"] = {"fwd": 50, "out": 35, "elbow": 20}
            face = dict(NF["scared"])
            if b("noob_copy") - 0.1 <= t < b("noob_copy", 1) + 0.1:
                face = dict(NF["shout"])
            if b("patch_hold") <= t:
                look_at = Vector(E.PA.root.location)
    tl, nd = _look(yaw, p, look_at, h=1.4, lim=lim)
    pz["head_turn"], pz["head_nod"] = tl, nd + pz.get("head_nod", 0)
    pz.pop("shoulders", None)
    pz = life(E, "noob", pz, face, t, 1.6)
    M.set_noob(E, p, yaw, pz, face, t)


# ------------------------------------------------------------------ Steve
def steve(E, t):
    from ep09_new import SF
    p = S0.copy()
    east = Vector((6.0, -1.0, 0))
    yaw = _face_to(p, east)
    face = dict(SF["scared"])
    look_at = void_look(t) if t >= b("void_in") else Vector(E.N.root.location) + Vector((0, 0, 1.0))
    pz = {"arm_sr": {"fwd": 25, "out": 25, "elbow": 20}, "arm_sl": {"fwd": 15, "out": 25, "elbow": 25}}
    lim = 80
    N_ = Vector(E.N.root.location) + Vector((0, 0, 1.0))
    if t < b("void_in") + 0.6:                                     # Ep5's end: to the Noob, then the wall turns his head
        yaw = lerp(_face_to(p, N_), _face_to(p, east), ss(b("void_in") + 0.2, b("void_in") + 0.9, t))
        face = dict(SF["flat"]) if t < b("void_in") else dict(SF["stunned"])
    elif t < b("resolve"):
        look_at = void_look(t) if not (b("dragon_gone") <= t < b("noob_delete")) else DRAGON_C
        face = dict(SF["scared"])
        pz["chest_lean"] = -6
    elif t < b("windup"):                                         # eyes track the last pixels down, then harden: stance
        dn = ss(b("resolve"), b("resolve") + 0.6, t)
        look_at = DRAGON_C.lerp(Vector((1.0, -0.5, 1.5)), dn)
        st = ss(b("resolve") + 0.5, b("steve_stop"), t)
        face = dict(SF["stunned"]) if t < b("resolve") + 0.5 else {"both_to": -0.3, "both_tm": -0.35, "both_ti": -0.25,
                                                                     "bb_raise": -0.25, "bb_tilt": 0.35, "m_arch": 0.1}
        pz["arm_sr"] = {"fwd": 25 + 25 * st, "out": 12, "elbow": 20 + 40 * st}
        pz["arm_sl"] = {"fwd": 15 + 40 * st, "out": 25 - 22 * st, "elbow": 25 + 50 * st}
        pz["hips_drop"] = 0.1 * st
        pz["chest_lean"] = 6 * st
        if t >= b("steve_stop"):
            look_at = face_edge(E, t, -1.0, 2.0)
    elif t < b("blink"):                                          # the wind-up, the twist, the overhand throw
        face = {"both_to": -0.3, "both_tm": -0.35, "both_ti": -0.25, "bb_raise": -0.25, "bb_tilt": 0.35, "m_arch": 0.1}
        look_at = face_edge(E, t, -1.0, 3.0)
        w = ss(b("windup"), b("windup") + 0.8, t)
        th = ss(b("throw") - 0.02, b("throw") + 0.2, t)
        fwd = lerp(lerp(50, 205, w), 70, th)
        pz["arm_sr"] = {"fwd": fwd, "out": 20, "elbow": lerp(lerp(60, 95, w), 5, th)}
        pz["arm_sl"] = {"fwd": lerp(55 - 30 * w, 80, th), "out": lerp(5 + 20 * w, 25, th), "elbow": lerp(75 * (1 - w), 10, th)}
        pz["chest_twist"] = lerp(lerp(0, -30, w), 18, th)
        pz["chest_lean"] = lerp(lerp(6, -10, w), 18, th)
        pz["hips_drop"] = 0.1 + 0.05 * th
        if t >= b("throw") + 0.6:                                  # the follow-through settles; he watches it
            k = ss(b("throw") + 0.6, b("pick_gone"), t)
            pz["chest_lean"] = lerp(18, 4, k)
            pz["chest_twist"] = lerp(18, 0, k)
            pz["arm_sr"] = {"fwd": lerp(70, 30, k), "out": 18, "elbow": 15}
            look_at = getattr(E, "pick_fly", E.pick6).matrix_world.to_translation() if hasattr(E, "pick_fly") else look_at
        if t >= b("pick_gone") + 0.2:
            face = dict(SF["stunned"])
    elif t < b("raise"):                                          # a stunned blink; down at his empty hands
        look_at = face_edge(E, t, -1.0, 3.0)
        face = dict(SF["stunned"])
        hd = ss(b("blink") + 0.4, b("steve_pick"), t)
        if hd > 0:
            look_at = look_at.lerp(p + Vector((0.6, -0.1, 0.9)), hd)
            pz["arm_sr"] = {"fwd": 45 * hd + 20, "out": 15, "elbow": 70 * hd}
            pz["arm_sl"] = {"fwd": 45 * hd + 15, "out": 15, "elbow": 70 * hd}
            face = {"both_to": -0.2, "both_ti": 0.1, "bb_raise": 0.05, "m_arch": 0.15}
        lim = 85
    elif t < b("tnt_pull"):                                       # the Noob's wall; "...No wall."
        look_at = N_ if t < b("build_wall") else BARRIER_C + Vector((0, 0, 0.5))
        yaw = lerp(_face_to(p, N_), _face_to(p, east), ss(b("build_wall") - 0.2, b("build_wall") + 0.3, t))
        face = dict(SF["flat"])
        if b("wall_gone") <= t:
            face = dict(SF["stunned"])
        if b("steve_nowall") - 0.2 <= t:                          # deadpan, to the Noob
            look_at = N_
            yaw = lerp(_face_to(p, east), _face_to(p, N_), 0.45)
            face = dict(SF["flat"])
    elif t < b("bank"):                                           # the TNT: from his side, lit, thrown overhand
        look_at = face_edge(E, t, -1.0, 2.5)
        face = {"both_to": -0.3, "both_tm": -0.35, "both_ti": -0.25, "bb_raise": -0.25, "bb_tilt": 0.35, "m_arch": 0.1}
        pull = ss(b("tnt_pull"), b("tnt_pull") + 0.3, t) * (1 - ss(b("tnt_pull") + 0.3, b("tnt_pull") + 0.6, t))
        hold_ = ss(b("tnt_pull") + 0.3, b("tnt_pull") + 0.6, t)
        w = ss(b("tnt_throw") - 0.15, b("tnt_throw") + 0.05, t)
        th = ss(b("tnt_throw") + 0.05, b("tnt_throw") + 0.25, t)
        fwd = lerp(lerp(-30 * pull + 60 * hold_, 200, w), 75, th)
        pz["arm_sr"] = {"fwd": fwd, "out": 22 + 10 * pull, "elbow": lerp(lerp(20 + 40 * hold_, 95, w), 5, th)}
        pz["arm_sl"] = {"fwd": 30 + 30 * hold_ * (1 - w), "out": 15, "elbow": 40 * hold_ * (1 - w)}
        pz["chest_twist"] = lerp(lerp(-10 * pull, -25, w), 15, th)
        pz["chest_lean"] = lerp(-8 * w, 14, th)
        if b("tnt_throw") + 0.4 <= t:
            k = ss(b("tnt_throw") + 0.4, b("tnt_throw") + 1.0, t)
            pz["arm_sr"] = {"fwd": lerp(75, 30, k), "out": 20, "elbow": 15}
            pz["chest_twist"] = lerp(15, 0, k)
            pz["chest_lean"] = lerp(14, 2, k)
            look_at = getattr(E, "tnt_now", look_at)
        if b("tnt_gone") <= t:
            face = dict(SF["stunned"])
            look_at = face_edge(E, t, -1.0, 3.0)
        if b("whip") + 0.2 <= t:
            look_at = N_
            face = dict(SF["flat"])
    else:                                                         # backs off the grey pad, hops onto the terrace
        hop = ss(b("bank") + 0.1, b("patch_stop") + 1.2, t)
        p = S0.lerp(S_T, hop) + Vector((0, 0, 0.35 * math.sin(math.pi * ss(0.35, 0.65, hop))))
        yaw = _face_to(p, east) if hop > 0.95 or hop < 0.05 else _face_to(S0, S_T)
        if 0.05 < hop < 0.95:
            _run(pz, t, b("bank") + 0.1, 1.9, k=0.5)
            yaw = lerp(_face_to(S0, S_T), _face_to(p, east), ss(0.7, 0.95, hop))
        face = dict(SF["worried"])
        look_at = Vector(E.PA.root.location)
        if b("patch_correct") <= t:
            look_at = Vector(E.PA.root.location) if t < b("patch_correct") + 1.6 else face_edge(E, t, -1.0, 2.0)
        if b("hush") <= t:                                         # the Noob leans to the abyss: a hand half out
            look_at = N_
            face = dict(SF["scared"])
            pz["arm_sl"] = {"fwd": 30, "out": 20, "elbow": 30}
        if b("void_hi") + 1.2 <= t:
            look_at = face_edge(E, t, -1.0, 2.0)
            face = dict(SF["scared"])
        if b("surge") <= t:                                        # braced, a hand out to the Noob
            look_at = N_ if t < b("patch_hold") else Vector(E.PA.root.location)
            pz["arm_sl"] = {"fwd": 60, "out": 30, "elbow": 15}
            pz["chest_lean"] = -6
            face = dict(SF["scared"])
    tl, nd = _look(yaw, p, look_at, lim=lim)
    pz["head_turn"], pz["head_nod"] = tl, nd + pz.get("head_nod", 0)
    pz = life(E, "steve", pz, face, t, 2.7)
    M.set_steve(E, p, yaw, pz, face, t)


# ------------------------------------------------------------------ one frame
def apply(E, t):
    prepare(E)
    _use(E, 5)
    E5.apply(E, E.T5)                                             # Ep5's last instant: the world as it was left
    _use(E, 6)
    E._t_now = t
    name, t0, t1 = which(t)
    E.cam_loc_now = _cam(E, t, name, t0, t1)[0]
    void_shape(E, t)
    light(E, t)
    d_span = dragon(E, t)
    pads(E, t)
    patch(E, t)
    steve(E, t)
    noob(E, t)
    bpy.context.view_layer.update()
    pickaxe(E, t)
    hammer(E, t)
    barrier(E, t)
    tnt(E, t)
    sparks(E, t)
    debris(E, t)
    ripple(E, t)
    warp(E, t)
    gizmo(E, t)
    E.scanp.location = FAR
    pixels(E, t, d_span)
    camera(E, t, name, t0, t1)
    E2.set_wash(E, 1.0 * ss(b("flash") - 0.12, b("flash") + 0.02, t))


# ------------------------------------------------------------------ the camera
def camera(E, t, shot, t0, t1):
    from ep10_p2_omg import handheld
    loc, look, lens, fstop, focus, shake = _cam(E, t, shot, t0, t1)
    shake += 0.5 * math.exp(-max(0.0, t - b("dragon_gone") - 1.4) * 4) * (t >= b("dragon_gone") + 1.4)
    tb = b("build_wall") + 0.6
    shake += 0.9 * math.exp(-max(0.0, t - tb) * 6) * (t >= tb)
    shake += 0.5 * math.exp(-max(0.0, t - b("pick_gone")) * 7) * (t >= b("pick_gone"))
    shake += 2.0 * ss(b("surge"), b("surge") + 0.3, t) * (1 - ss(b("surge") + 1.2, b("noob_copy", 1), t))
    shake += 1.4 * ss(b("warp"), b("flash"), t)
    y1, p1, r1 = handheld(E.T5 + t, shake)
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
    E.key.data.energy = 260.0 * (1 - 0.35 * ss(b("bank"), b("hush"), t))


def _c(x, y, z):
    return Vector((x, y, z))


def _cam(E, t, shot, t0, t1):
    """(location, look-at, lens mm, f-stop, focus or None, handheld). Time only (shards start anywhere)."""
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, t0 + 3, t)
    if shot == "s1":                                              # 28 mm, low, behind-beside them, up at the dragon: push-in
        return _c(-5.4, -7.6, 0.7).lerp(_c(-5.0, -6.6, 0.8), u), _c(-1.2, 0.8, 4.2).lerp(_c(-0.8, 0.8, 4.4), u), 28, 30, None, 0.2
    if shot == "s1n":                                             # the Noob looking up: "The world is DELETING itself!"
        return N0 + _c(2.9, -1.0, 1.0), N0 + _c(0, 0, 1.8), 35, 2.8, None, 0.3
    if shot == "s2":                                              # 50 mm MCU Steve, the void's rim on his face
        return S0 + _c(2.3, -1.9, 1.5), S0 + _c(0, 0, 1.55), 50, 2.6, None, 0.1
    if shot == "s3a":                                             # 35 mm three-quarter front: the wind-up
        return S0 + _c(2.6, -2.9, 1.25), S0 + _c(0.1, 0, 1.4), 35, 3.5, None, 0.15
    if shot == "s3b":                                             # 40 mm side tracking: the arc across to the wall
        pk = pick_path(E, min(t, b("pick_gone")))
        return pk + _c(-1.4, -4.6, -1.0), pk + _c(0.4, 0, 0.1), 32, 30, None, 0.12
    if shot == "s3c":                                             # Steve's stunned blink; "...My pickaxe."
        return S0 + _c(2.6, -2.1, 1.2), S0 + _c(0, 0, 1.6), 40, 2.6, None, 0.08
    if shot == "s4":                                              # 32 mm wide two-shot: the terrace left, the void right
        return _c(-1.8, -11.0, 2.2).lerp(_c(-1.6, -10.2, 2.1), u), _c(-1.2, 0.0, 1.7), 32, 30, None, 0.12
    if shot == "s4s":                                             # Steve, deadpan
        return S0 + _c(-1.5, -2.8, 1.45), S0 + _c(0, 0, 1.75), 38, 2.6, None, 0.06
    if shot == "s5a":                                             # 45 mm medium on Steve: the TNT
        return S0 + _c(2.4, -2.6, 1.35), S0 + _c(0.2, 0, 1.3), 45, 3.2, None, 0.12
    if shot == "s5b":                                             # 35 mm wide: the Noob left third, the TNT right
        return _c(-4.6, -10.4, 1.9), _c(-0.8, 0.0, 2.4), 32, 30, None, 0.12
    if shot == "s6":                                              # 40 mm: Patch front-left, them mid-left, the wall right
        return _c(-6.6, -9.6, 2.4).lerp(_c(-6.3, -9.2, 2.4), u), _c(-1.6, 0.0, 2.0), 36, 30, None, 0.1
    if shot == "s7a":                                             # 65 mm tight on the Noob leaning toward the black
        return N_EDGE + _c(3.1, -1.3, 1.5), N_EDGE + _c(0.1, 0, 1.6), 65, 2.2, None, 0.04
    if shot == "s7b":                                             # dead centre into the black: a slow push-in
        return _c(-3.9, -1.0, 1.9).lerp(_c(-2.6, -1.0, 1.95), u), _c(6.0, -1.0, 2.1), 35, 30, None, 0.03
    if shot == "s8":                                              # 28 mm wide pullback: the surge, the warp
        return _c(-8.0, -8.2, 2.3).lerp(_c(-9.2, -10.6, 2.9), ss(t0, b("flash"), t)), _c(-4.6, -0.6, 1.6), 28, 30, None, 0.15
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
    B.update(E.B6)
    E.force = bool(a.times)
    E.mouth = {}
    voice = a.voice if os.path.exists(a.voice) else os.path.join(os.path.dirname(a.voice), "audio.wav")
    if os.path.exists(voice):
        from ep09_new import _lipsync
        E.mouth = _lipsync(tl, voice)
    E.cuts = sorted(t0 for _, t0 in shot_bounds())
    M._render(E, frames, out, apply, finish_void)


def finish_void(path, mist_path):
    """The forest finish (the distance haze), except where the raw render is black: the void is a hole in reality,
    no haze sits on it."""
    import numpy as np
    from PIL import Image
    pre = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    M.finish_forest(path, mist_path)
    im = Image.open(path)
    post = np.asarray(im.convert("RGB")).astype(np.float32)
    if post.shape != pre.shape:
        return
    lum = pre.max(axis=2, keepdims=True)
    k = np.clip((10.0 - lum) / 6.0, 0.0, 1.0)                     # black (< 4/255) kept black, a soft edge to 10/255
    out = post * (1 - k) + pre * k
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(path)


if __name__ == "__main__":
    main()
