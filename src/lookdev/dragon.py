"""The dragon in the new look: the game's Ender Dragon model, built from its own 256x256 texture, jointed
for life: a five-part neck and a twelve-part tail that ripple with a lag, two-part wings whose tips
trail and fold on the upstroke, a body that heaves with each downstroke, a jaw, glowing eyes, legs
that tuck in flight.

    D = build_dragon(sc, assets, scale=0.5)          # scale 1 is the game's size (~16 blocks long)
    pose_dragon(D, t, flap=phase_in_cycles, amp=1.0, ...)
    D.root.location / rotation_euler (yaw about z; pitch, bank)

Coordinates: the parts are placed in the game model's own units (pixels; y down, -z forward) and turned
into ours (z up, -y forward) by mc(); at scale 1 one pixel is 1/16 block.
"""
import math
import os

import bpy
from mathutils import Euler, Vector

from mob import _box_mesh

PX = 1.0 / 16.0


def mc(v):
    """A game-model vector (x, y down, z back) in ours (x, z up, y back)."""
    x, y, z = v
    return Vector((x, z, -y)) * PX


class Dragon:
    pass


def _material(assets):
    m = bpy.data.materials.get("dragon_skin")
    if m:
        return m
    base = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures",
                        "entity", "enderdragon")
    m = bpy.data.materials.new("dragon_skin")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(base, "dragon.png"), check_existing=True)
    t.interpolation = "Closest"
    # the game's dragon is near black; lift it a little so its scales read in daylight
    lift = nt.nodes.new("ShaderNodeMix")
    lift.data_type = "RGBA"
    lift.blend_type = "SCREEN"
    lift.inputs[0].default_value = 0.12
    lift.inputs[7].default_value = (0.42, 0.36, 0.5, 1)
    nt.links.new(t.outputs["Color"], lift.inputs[6])
    nt.links.new(lift.outputs[2], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.45
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.55                     # scales catch the light
    e = nt.nodes.new("ShaderNodeTexImage")
    e.image = bpy.data.images.load(os.path.join(base, "dragon_eyes.png"), check_existing=True)
    e.interpolation = "Closest"
    nt.links.new(e.outputs["Color"], b.inputs["Emission Color"])
    es = nt.nodes.new("ShaderNodeMath")
    es.operation = "MULTIPLY"
    es.inputs[1].default_value = 6.0
    nt.links.new(e.outputs["Alpha"], es.inputs[0])
    nt.links.new(es.outputs[0], b.inputs["Emission Strength"])
    m["eyes"] = es.name
    return m


def _plane_mesh(name, u, v, w, d, mirror=False):
    """A wing's skin: a flat sheet w x d (pixels) in the x-y plane, both sides the texture's top region."""
    x0, y0 = u + d, v                                   # the top face region of a zero-height box
    tw = th = 256
    me = bpy.data.meshes.new(name)
    X0, X1, Y0, Y1 = -w / 2, w / 2, -d / 2, d / 2
    verts = [Vector(p) * PX for p in ((X0, Y0, 0), (X1, Y0, 0), (X1, Y1, 0), (X0, Y1, 0))]
    me.from_pydata([tuple(p) for p in verts], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    xa, xb = (x0 + w, x0) if mirror else (x0, x0 + w)
    # the top region's lower edge (v + d) is the leading edge; the sheet's y0 edge is the bone
    co = [(xa / tw, 1 - (y0 + d) / th), (xb / tw, 1 - (y0 + d) / th), (xb / tw, 1 - y0 / th), (xa / tw, 1 - y0 / th)]
    co = [co[3], co[2], co[1], co[0]]
    for li, loop in enumerate(me.loops):
        uv.data[li].uv = co[loop.vertex_index]
    me.update()
    return me


def build_dragon(sc, assets, scale=0.5, name="dragon", collection=None):
    col = collection or sc.collection
    mat = _material(assets)
    D = Dragon()
    D.name = name
    D.mat = mat
    D.root = bpy.data.objects.new(name, None)
    col.objects.link(D.root)
    D.root.scale = (scale,) * 3
    D.root.rotation_mode = "XYZ"
    D.parts = {}

    def pivot(key, parent, at):
        ob = bpy.data.objects.new(f"{name}_{key}", None)
        col.objects.link(ob)
        ob.parent = parent
        ob.location = mc(at)
        ob.rotation_mode = "XYZ"
        D.parts[key] = ob
        return ob

    def box(key, parent, b, tex, mirror=False, bevel=True):
        x, y, z, w, h, d = b
        if h == 0:
            me = _plane_mesh(f"{name}_{key}", tex[0], tex[1], w, d, mirror)
        else:
            me = _box_mesh(f"{name}_{key}", tex, (w, h, d), 256, 256, mirror=mirror)
        me.materials.append(mat)
        ob = bpy.data.objects.new(f"{name}_{key}", me)
        col.objects.link(ob)
        ob.parent = parent
        ob.location = mc((x + w / 2, y + h / 2, z + d / 2))
        if bevel and h > 0:
            bv = ob.modifiers.new("bevel", "BEVEL")
            bv.width = 0.02 / max(scale, 1e-3) * PX * 16 * 0.4
            bv.segments = 2
        return ob

    # the body (its pivot at the shoulders' height, the game's body pivot)
    body = pivot("body", D.root, (0, 4, 8))
    box("body_box", body, (-12, 0, -16, 24, 24, 64), (0, 0))
    for k, z in enumerate((-10, 10, 30)):
        box(f"body_scale_{k}", body, (-1, -6, z, 2, 6, 12), (220, 53))
    # the neck: five segments forward from the chest, each hanging from the one behind it
    prev, at = D.root, (0, 12, -10)
    D.neck = []
    for i in range(5):
        p = pivot(f"neck_{i}", prev, at)
        box(f"neck_box_{i}", p, (-5, -5, -5, 10, 10, 10), (192, 104))
        box(f"neck_scale_{i}", p, (-1, -9, -3, 2, 4, 6), (48, 0))
        D.neck.append(p)
        prev, at = p, (0, 0, -10)
    # the head and its jaw
    head = pivot("head", prev, (0, 0, -6))
    box("upper_lip", head, (-6, -1, -24, 12, 5, 16), (176, 44))
    box("upper_head", head, (-8, -8, -10, 16, 16, 16), (112, 30))
    box("head_scale_l", head, (-5, -12, -4, 2, 4, 6), (0, 0), mirror=True)
    box("head_scale_r", head, (3, -12, -4, 2, 4, 6), (0, 0))
    box("nostril_l", head, (-5, -3, -22, 2, 2, 4), (112, 0), mirror=True)
    box("nostril_r", head, (3, -3, -22, 2, 2, 4), (112, 0))
    jaw = pivot("jaw", head, (0, 4, -8))
    box("jaw_box", jaw, (-6, 0, -16, 12, 4, 16), (176, 65))
    D.head, D.jaw = head, jaw
    # the tail: twelve segments back from the hips
    prev, at = D.root, (0, 10, 58)
    D.tail = []
    for i in range(12):
        p = pivot(f"tail_{i}", prev, at)
        box(f"tail_box_{i}", p, (-5, -5, -5, 10, 10, 10), (192, 104))
        box(f"tail_scale_{i}", p, (-1, -9, -3, 2, 4, 6), (48, 0))
        D.tail.append(p)
        prev, at = p, (0, 0, 10)
    # the wings: a bone with its skin, and a tip with its own, on each side (the right one mirrored)
    D.wing, D.tip = {}, {}
    for side, sx in (("l", 1), ("r", -1)):
        mir = side == "r"
        w = pivot(f"wing_{side}", body, (-12 * sx, 1, -6))
        box(f"wing_bone_{side}", w, (-56 if sx > 0 else 0, -4, -4, 56, 8, 8), (112, 88), mirror=mir)
        box(f"wing_skin_{side}", w, (-56 if sx > 0 else 0, 0, 2, 56, 0, 56), (-56, 88), mirror=mir)
        tp = pivot(f"tip_{side}", w, (-56 * sx, 0, 0))
        box(f"tip_bone_{side}", tp, (-56 if sx > 0 else 0, -2, -2, 56, 4, 4), (112, 136), mirror=mir)
        box(f"tip_skin_{side}", tp, (-56 if sx > 0 else 0, 0, 2, 56, 0, 56), (-56, 144), mirror=mir)
        D.wing[side], D.tip[side] = w, tp
    # the legs: hip, knee, foot
    D.legs = {}
    for side, sx in (("l", 1), ("r", -1)):
        mir = side == "r"
        f = pivot(f"fleg_{side}", body, (-12 * sx, 16, -6))
        box(f"fleg_box_{side}", f, (-4, -4, -4, 8, 24, 8), (112, 104), mirror=mir)
        ft = pivot(f"fleg_tip_{side}", f, (0, 20, -1))
        box(f"fleg_tip_box_{side}", ft, (-3, -1, -3, 6, 24, 6), (226, 138), mirror=mir)
        ff = pivot(f"ffoot_{side}", ft, (0, 23, 0))
        box(f"ffoot_box_{side}", ff, (-4, 0, -12, 8, 4, 16), (144, 104), mirror=mir)
        r = pivot(f"rleg_{side}", body, (-16 * sx, 12, 34))
        box(f"rleg_box_{side}", r, (-8, -4, -8, 16, 32, 16), (0, 0), mirror=mir)
        rt = pivot(f"rleg_tip_{side}", r, (0, 32, -4))
        box(f"rleg_tip_box_{side}", rt, (-6, -2, 0, 12, 32, 12), (196, 0), mirror=mir)
        rf = pivot(f"rfoot_{side}", rt, (0, 31, 4))
        box(f"rfoot_box_{side}", rf, (-9, 0, -20, 18, 6, 24), (112, 0), mirror=mir)
        D.legs[side] = (f, ft, ff, r, rt, rf)
    for ob in D.root.children_recursive:
        if ob.type == "MESH":
            ob["dragon"] = True
    return D


def _rad(*a):
    return [math.radians(x) for x in a]


def pose_dragon(D, t, flap=None, amp=1.0, glide=0.0, neck_pitch=0.0, neck_yaw=0.0, head_pitch=0.0, head_yaw=0.0,
                jaw=0.0, tail_pitch=0.0, tail_yaw=0.0, legs=1.0, frozen=None, turn=0.0):
    """One frame of the dragon's body.
    flap: the wingbeat in cycles (None: wings held as glide says); amp: the beat's size;
    glide 0..1: wings spread and still (a glide) instead of beating; neck/head/tail bends in degrees,
    spread along the chain; jaw 0..1 (a roar); legs 1 tucked back (flying) .. 0 hanging (landing);
    turn: degrees per second it is turning (the neck leads into the turn, the tail swings out);
    frozen: a time to hold everything at (the freeze: nothing ripples).
    Returns the body's heave (blocks, at scale 1) for the caller to add."""
    if frozen is not None:
        t = frozen
    ph = 2 * math.pi * (flap if flap is not None else 0.0)
    beat = (1 - glide) * amp
    # the stroke: a quicker, stronger downstroke (the wave skewed); the tip lags and folds going up
    w = math.sin(ph + 0.35 * math.sin(ph))
    up = max(0.0, -math.cos(ph))
    for side, sx in (("l", 1), ("r", -1)):
        roll = (-38 * w * beat + 6 * glide) * sx                 # + raises the wing (about the body's axis)
        sweep = (6 * math.cos(ph) * beat - 4 * glide) * sx
        D.wing[side].rotation_euler = Euler(_rad(0, roll, sweep), "XYZ")
        tw = math.sin(ph - 1.0 + 0.35 * math.sin(ph - 1.0))
        troll = (-30 * tw * beat - 10 * up * beat + 4 * glide) * sx
        tsweep = (14 * up * beat) * sx
        D.tip[side].rotation_euler = Euler(_rad(0, troll, tsweep), "XYZ")
    heave = 0.55 * beat * math.cos(ph)                          # up on the downstroke (pixels, in the model's units)
    # the body pitches a little with each beat; the neck counters it, so the head stays steady
    D.parts["body"].rotation_euler = Euler(_rad(-3 * beat * math.sin(ph - 0.4), 0, 0), "XYZ")
    for i, p in enumerate(D.neck):
        k = (i + 1) / len(D.neck)
        wave = 3.5 * beat * math.sin(ph - 0.6 - 0.5 * i)
        sway = 3.0 * math.sin(t * 0.9 - 0.5 * i) * (1 - 0.6 * glide)
        p.rotation_euler = Euler(_rad(neck_pitch / 5 + wave, 0, neck_yaw / 5 + sway + turn * 0.04 * k), "XYZ")
    D.head.rotation_euler = Euler(_rad(head_pitch - 3.5 * beat * math.sin(ph - 3.4), 0, head_yaw), "XYZ")
    D.jaw.rotation_euler = Euler(_rad(32 * jaw + 2 * math.sin(t * 2.3), 0, 0), "XYZ")
    for i, p in enumerate(D.tail):
        k = (i + 1) / len(D.tail)
        swing = (5.0 + 4.0 * k) * math.sin(t * 1.5 - 0.55 * i)
        lift = 3.0 * beat * math.sin(ph - 1.2 - 0.4 * i)
        p.rotation_euler = Euler(_rad(tail_pitch / 12 + lift, 0, tail_yaw / 12 + swing * 0.5 - turn * 0.03 * k), "XYZ")
    for side, sx in (("l", 1), ("r", -1)):
        f, ft, ff, r, rt, rf = D.legs[side]
        dang = 2.5 * math.sin(t * 1.9 + sx)
        # tucked: the thighs swing back along the belly, the shins fold forward under them, the feet trail
        f.rotation_euler = Euler(_rad(lerp(-10, 60, legs) + dang, 0, 0), "XYZ")
        ft.rotation_euler = Euler(_rad(lerp(15, -50, legs), 0, 0), "XYZ")
        ff.rotation_euler = Euler(_rad(lerp(-15, 45, legs), 0, 0), "XYZ")
        r.rotation_euler = Euler(_rad(lerp(-10, 72, legs) + dang, 0, 0), "XYZ")
        rt.rotation_euler = Euler(_rad(lerp(15, -55, legs), 0, 0), "XYZ")
        rf.rotation_euler = Euler(_rad(lerp(-20, 50, legs), 0, 0), "XYZ")
    return heave * PX * D.root.scale[0]


def lerp(a, b, u):
    return a + (b - a) * u
