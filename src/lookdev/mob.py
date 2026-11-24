"""Minecraft mobs in the new look: a jointed block body skinned from the game's own 64x64 entity texture.

The boxes and their UVs follow the game's player-style layout (head 8x8x8, body 8x12x4, arms and legs
4x12x4), so the skin reads exactly as in the game; pixel-sharp sampling, the same soft world light as
the rest of the set. Used for the zombies of Episode 2 (and any player-shaped mob later).

    Z = build_mob(sc, "zombie_1", skin_png, height=2.0)
    pose_mob(Z, {"root_yaw": 0, "head_turn": 10, "arm_r": {"fwd": 90}, "arm_l": {"fwd": 85}, "leg_r": {"fwd": 20}})
    Z.root.location = (x, y, z)

The mob faces -y at yaw 0 (as the Noob and Steve). Its right side is -x.
"""
import math

import bpy
from mathutils import Quaternion, Vector

PX = 1.0 / 16.0           # one skin pixel, in blocks, at a 2-block-tall mob (scaled by `height`)

# texture origin (u, v) and box size (w, h, d) in pixels, the player-style 64x64 layout
PARTS = {
    "head":  ((0, 0), (8, 8, 8)),
    "body":  ((16, 16), (8, 12, 4)),
    "arm_r": ((40, 16), (4, 12, 4)),
    "arm_l": ((32, 48), (4, 12, 4)),
    "leg_r": ((0, 16), (4, 12, 4)),
    "leg_l": ((16, 48), (4, 12, 4)),
}
# where each part hangs from (its pivot, in pixels from its parent's pivot) and where its box sits from it.
# The head and arms hang from the body (so the upper body leans and twists as one); the body and legs
# from the hips.
PIVOT = {"head": (0, 0, 12), "body": (0, 0, 12), "arm_r": (-6, 0, 10), "arm_l": (6, 0, 10),
         "leg_r": (-2, 0, 12), "leg_l": (2, 0, 12)}
PARENT = {"head": "body", "arm_r": "body", "arm_l": "body"}
BOX_FROM_PIVOT = {"head": (0, 0, 4), "body": (0, 0, 6), "arm_r": (0, 0, -4), "arm_l": (0, 0, -4),
                  "leg_r": (0, 0, -6), "leg_l": (0, 0, -6)}


class Mob:
    pass


def _regions(u, v, w, h, d):
    """The six face rectangles (x0, y0, w, h) in skin pixels."""
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
            "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
            "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}


def _box_mesh(name, origin, size, tex_w=64, tex_h=64, inflate=0.0, mirror=False):
    (u, v), (w, h, d) = origin, size
    hx, hy, hz = w / 2 + inflate, d / 2 + inflate, h / 2 + inflate
    X0, X1, Y0, Y1, Z0, Z1 = -hx, hx, -hy, hy, -hz, hz
    # corners as seen from outside: bottom-left, bottom-right, top-right, top-left
    quads = {
        "front": [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y0, Z1), (X0, Y0, Z1)],
        "back": [(X1, Y1, Z0), (X0, Y1, Z0), (X0, Y1, Z1), (X1, Y1, Z1)],
        "right": [(X0, Y1, Z0), (X0, Y0, Z0), (X0, Y0, Z1), (X0, Y1, Z1)],      # the mob's right is -x
        "left": [(X1, Y0, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X1, Y0, Z1)],
        "top": [(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)],
        "bottom": [(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y0, Z0), (X0, Y0, Z0)],
    }
    reg = _regions(u, v, w, h, d)
    if mirror:                         # the game's old layout: a left limb is the right one mirrored
        reg["left"], reg["right"] = reg["right"], reg["left"]
    verts, faces, uvs = [], [], []
    for k, q in quads.items():
        i = len(verts)
        verts += [Vector(p) * PX for p in q]
        faces.append((i, i + 1, i + 2, i + 3))
        x0, y0, rw, rh = reg[k]
        # bottom-left, bottom-right, top-right, top-left in UV (V up, the image's y down)
        xa, xb = (x0 + rw, x0) if mirror else (x0, x0 + rw)
        uvs += [(xa / tex_w, 1 - (y0 + rh) / tex_h), (xb / tex_w, 1 - (y0 + rh) / tex_h),
                (xb / tex_w, 1 - y0 / tex_h), (xa / tex_w, 1 - y0 / tex_h)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], faces)
    uv = me.uv_layers.new()
    for li, loop in enumerate(me.loops):
        uv.data[li].uv = uvs[loop.vertex_index]
    me.update()
    return me


def scary_skin(skin_png, out_dir, seed=3):
    """The movie's zombies (the creator, 2026-11-24: "tall, hunched, ragged skin, glowing red eyes"): the
    game's skin made rotten (darker, sicklier green, blotched, torn: dark rents and raw red flesh in the skin
    and the shirt) and its eyes red. Returns (skin png, glow png: the eyes, white on black)."""
    import os
    import random
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(skin_png).convert("RGBA")
    px = im.load()
    W, H = im.size
    rnd = random.Random(seed)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gp_ = glow.load()
    eyes = {(9, 12), (10, 12), (13, 12), (14, 12)}         # the face's dark eye pixels (front of the head: 8..16)
    for y in range(H):
        for x in range(W):
            r, g, b_, a = px[x, y]
            if a == 0:
                continue
            if (x, y) in eyes:
                px[x, y] = (255, 36, 18, 255)
                gp_[x, y] = (255, 255, 255)
                continue
            # rotten: darker, the green pulled toward a sick grey-olive
            k = 0.62 + 0.12 * rnd.random()
            grey = (r + g + b_) / 3
            r2, g2, b2 = [(c * 0.55 + grey * 0.45) * k for c in (r, g, b_)]
            g2 *= 1.04
            r2 += 6
            px[x, y] = (int(r2), int(g2), int(b2), 255)
    # blotches and rents: dark rot, and raw flesh at some of them (not on the eyes)
    for _ in range(70):
        x, y = rnd.randrange(W), rnd.randrange(H)
        if px[x, y][3] == 0 or (x, y) in eyes or (8 <= x < 16 and 11 <= y < 14):
            continue
        n = rnd.choice((1, 2, 2, 3))
        raw = rnd.random() < 0.35
        for dx in range(n):
            for dy in range(rnd.choice((1, 2))):
                xx, yy = min(W - 1, x + dx), min(H - 1, y + dy)
                if px[xx, yy][3] == 0 or (xx, yy) in eyes:
                    continue
                px[xx, yy] = (118, 22, 18, 255) if raw and dx == n // 2 else (22, 26, 16, 255)
    sp = os.path.join(out_dir, "zombie_scary.png")
    gp2 = os.path.join(out_dir, "zombie_scary_glow.png")
    im.save(sp)
    glow.save(gp2)
    return sp, gp2


def _skin_material(name, skin_png, glow_png=None, glow=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(skin_png, check_existing=True)
    t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    if glow_png:                                   # the eyes glow: a mask times a strength (a value node, to animate)
        g = nt.nodes.new("ShaderNodeTexImage")
        g.image = bpy.data.images.load(glow_png, check_existing=True)
        g.image.colorspace_settings.name = "Non-Color"
        g.interpolation = "Closest"
        v = nt.nodes.new("ShaderNodeValue")
        v.name = "glow"
        v.outputs[0].default_value = glow
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(g.outputs["Color"], sep.inputs[0])
        nt.links.new(sep.outputs[0], mul.inputs[0])
        nt.links.new(v.outputs[0], mul.inputs[1])
        b.inputs["Emission Color"].default_value = (1.0, 0.02, 0.005, 1)
        nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Roughness"].default_value = 0.78
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.25
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    return m


def build_mob(sc, name, skin_png, height=2.0, collection=None, glow_png=None, glow=0.0):
    """A player-shaped mob, 32 skin pixels tall scaled to `height` blocks. glow_png: an emission mask (the
    zombies' red eyes), its strength in M.glow (a value node) and a small red light in front of the face."""
    col = collection or sc.collection
    mat = _skin_material(f"{name}_skin", skin_png, glow_png, glow)
    M = Mob()
    M.name = name
    M.root = bpy.data.objects.new(name, None)
    col.objects.link(M.root)
    M.root.scale = (height / 2.0,) * 3
    M.pivots, M.boxes = {}, {}
    from PIL import Image
    skin = Image.open(skin_png).convert("RGBA")
    tw, th = skin.size
    order = ["body", "leg_r", "leg_l", "head", "arm_r", "arm_l"]
    for part in order:
        origin, size = PARTS[part]
        mirror = False
        if part in ("arm_l", "leg_l"):
            u, v = origin
            w, h, d = size
            if th < 64 or skin.crop((u, v, u + 2 * (w + d), v + h + d)).getextrema()[3][1] == 0:
                origin, mirror = PARTS[part.replace("_l", "_r")][0], True
        pv = bpy.data.objects.new(f"{name}_{part}_pivot", None)
        col.objects.link(pv)
        pv.parent = M.pivots[PARENT[part]] if part in PARENT else M.root
        pv.location = Vector(PIVOT[part]) * PX
        pv.rotation_mode = "QUATERNION"
        me = _box_mesh(f"{name}_{part}", origin, size, tw, th, mirror=mirror)
        me.materials.append(mat)
        ob = bpy.data.objects.new(f"{name}_{part}", me)
        col.objects.link(ob)
        ob.parent = pv
        ob.location = Vector(BOX_FROM_PIVOT[part]) * PX
        bev = ob.modifiers.new("bevel", "BEVEL")                  # the soft block edge of the new look
        bev.width = 0.012
        bev.segments = 2
        bev.harden_normals = False
        M.pivots[part], M.boxes[part] = pv, ob
    M.root.rotation_mode = "XYZ"
    M.glow = mat.node_tree.nodes.get("glow")
    M.eye_light = None
    if glow_png:
        lt = bpy.data.objects.new(f"{name}_eyes", bpy.data.lights.new(f"{name}_eyes", "POINT"))
        col.objects.link(lt)
        lt.data.color = (1.0, 0.06, 0.02)
        lt.data.energy = 0.0
        lt.data.shadow_soft_size = 0.05
        lt.data.use_shadow = False
        lt.parent = M.pivots["head"]
        lt.location = Vector((0, -6.5, 4.6)) * PX                 # just in front of the eyes
        lt.visible_glossy = False
        M.eye_light = lt
    return M


def _q(axis, deg):
    return Quaternion(Vector(axis), math.radians(deg))


def pose_mob(M, P):
    """root_yaw/pitch/roll (the whole body: pitch + leans forward, roll + to its left), chest_lean/twist/side
    (the upper body at the hips), head_turn/nod/tilt, arm_r/l {fwd, out, twist} and leg_r/l {fwd, out},
    in degrees."""
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    M.root.rotation_euler = (math.radians(P.get("root_pitch", 0)), math.radians(P.get("root_roll", 0)),
                             math.radians(P.get("root_yaw", 0)))
    M.pivots["body"].rotation_quaternion = _q(Z, P.get("chest_twist", 0)) @ _q(Y, -P.get("chest_side", 0)) \
        @ _q(X, P.get("chest_lean", 0))
    M.pivots["head"].rotation_quaternion = _q(Z, P.get("head_turn", 0)) @ _q(Y, -P.get("head_tilt", 0)) \
        @ _q(X, P.get("head_nod", 0))
    for part in ("arm_r", "arm_l", "leg_r", "leg_l"):
        a = P.get(part, {})
        s = -1 if part.endswith("_r") else 1
        # fwd lifts the limb toward -y (the front); out swings it away from the body
        M.pivots[part].rotation_quaternion = _q(Z, a.get("twist", 0) * s) @ _q(X, -a.get("fwd", 0)) \
            @ _q(Y, -a.get("out", 0) * s)


# ------------------------------------------------------------------ the zombie's motion
class Persona:
    """What makes one zombie move unlike the others."""
    def __init__(self, seed, speed=1.0, limp=0.0, tilt=0.0, reach=88.0, droop=0.0):
        self.seed, self.speed, self.limp, self.tilt, self.reach, self.droop = seed, speed, limp, tilt, reach, droop


def _n(t, f, seed):
    """Smooth noise, -1..1 (a few sines at odd ratios)."""
    return (math.sin(t * f + seed) * 0.6 + math.sin(t * f * 2.31 + seed * 1.7) * 0.3
            + math.sin(t * f * 4.07 + seed * 2.9) * 0.1)


def zombie_pose(per, t, phase=None, arms_up=1.0, lean=0.0, look=0.0, lunge=0.0, flail=0.0):
    """A zombie's pose: a heavy, lurching shuffle (phase in cycles; None standing), arms raised by
    arms_up (0 hanging .. 1 reaching), a body lean (+ forward), a head turn toward `look` (degrees,
    reached with a lag the caller supplies), a lunge 0..1 and a flail 0..1 (the suck).
    Returns (pose dict, the body's lift in blocks)."""
    sd = per.seed
    walk = phase is not None
    ph = 2 * math.pi * (phase or 0.0)
    sw = math.sin(ph) if walk else 0.0
    # the limp: one leg's step is shorter and lands harder (a hitch in the bob)
    stride_r, stride_l = 26 * (1 - 0.45 * per.limp), 30
    bob = (0.045 * abs(math.sin(ph)) + 0.03 * per.limp * max(0.0, math.sin(ph))) if walk else 0.0
    idle = 0.0 if walk else 1.0
    breathe = math.sin(t * 1.7 + sd) * idle
    sway = _n(t, 0.9, sd)
    pz = {
        "root_pitch": 4 + lean + 3 * per.limp * max(0.0, math.sin(ph)) + 10 * lunge,
        "root_roll": (5 * sw + 3 * per.limp * math.sin(ph)) if walk else 2.5 * sway,
        "chest_lean": 6 + 3 * abs(sw) + 2 * breathe + 8 * lunge,
        "chest_twist": -9 * sw + 4 * sway * idle,
        "chest_side": 3 * math.sin(ph + 0.6) if walk else 2 * sway,
        "head_turn": look + 7 * _n(t, 0.7, sd + 3),
        "head_nod": 6 + 4 * per.droop + 5 * abs(math.sin(ph + 0.8)) * (1 if walk else 0) - 6 * lunge + 3 * breathe,
        "head_tilt": per.tilt + 6 * _n(t, 0.5, sd + 5) + (4 * math.sin(ph + 1.2) if walk else 0),
        "leg_r": {"fwd": stride_r * sw, "out": 3},
        "leg_l": {"fwd": -stride_l * sw, "out": 3},
    }
    reach = per.reach * arms_up + 6 * (1 - arms_up)
    for side, k in (("arm_r", 1), ("arm_l", -1)):
        # the arms don't swing like a walker's: they bob with the steps, lagging the body, and drift apart
        lag = math.sin(ph - 0.9 + (0.0 if k > 0 else math.pi)) if walk else 0.0
        drift = _n(t, 0.8, sd + 7 * k)
        f = reach + 6 * lag * arms_up + 5 * drift * arms_up - 8 * per.droop * (k > 0) + 22 * lunge
        o = 5 + 4 * drift + 6 * (1 - arms_up)
        pz[side] = {"fwd": f, "out": o, "twist": 6 * drift}
    if flail > 0:
        for side, k in (("arm_r", 1), ("arm_l", -1)):
            pz[side] = {"fwd": 120 + 60 * flail * math.sin(t * 13 + k * 1.9 + sd),
                        "out": 35 + 30 * flail * math.sin(t * 11 + k + sd), "twist": 20 * k}
        pz["leg_r"] = {"fwd": 35 * flail * math.sin(t * 12 + sd), "out": 10}
        pz["leg_l"] = {"fwd": -35 * flail * math.sin(t * 12 + sd + 0.7), "out": 10}
        pz["head_nod"] = -18 * flail
        pz["head_turn"] = look + 30 * flail * math.sin(t * 7 + sd)
    return pz, bob


def skin_path(assets, mob="zombie", kind="zombie"):
    import os
    return os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures",
                        "entity", mob, f"{kind}.png")
