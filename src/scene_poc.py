"""
Proof-of-concept episode: "A Roblox Noob Punched a Minecraft Tree".

Builds the whole Short in Blender from build/timeline.json (made by
audio.py), so every action lands on the dialogue and sound, then renders a
frame range on the CPU (Cycles). Choreography is plain functions of time:
pose = f(t), keyed on every frame.

    python src/scene_poc.py build/timeline.json build/tex build/frames \
        [--first N --last M] [--res 720] [--samples 16]
"""

import argparse
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit.blocks import aim, box, empty, material, voxels   # noqa: E402
from kit.rigs import make_noob, make_steve, srgb        # noqa: E402

FPS = 24
NOOB_LAND = (0.2, -0.4)
NOOB_SPOT = (1.15, 0.5)
STEVE_SPOT = (-0.9, 0.5)
STEVE_START = (-7.0, 0.5)
TREE = (2, 0)                        # the hero tree's trunk column
PORTAL_Z = 14.0


# ------------------------------------------------------------------ helpers

def F(t):
    return int(round(t * FPS)) + 1


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ss(a, b, t):
    """Smoothstep from 0 at a to 1 at b."""
    if b == a:
        return 1.0 if t >= b else 0.0
    x = clamp((t - a) / (b - a))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    if isinstance(a, tuple):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u


def bump(t, a, b, ramp=0.25):
    """0 outside [a, b], eases to 1 inside."""
    return ss(a, a + ramp, t) * (1 - ss(b - ramp, b, t))


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


class TL:
    def __init__(self, path):
        d = json.load(open(path))
        self.d = d
        self.beats = d["beats"]
        self.length = d["length"]
        self.lines = d["lines"]
        self.impacts = d["impacts"]

    def __getitem__(self, k):
        return self.beats[k]

    def talking(self, who, t):
        """0..1 envelope while `who` speaks, for head bobs."""
        for ln in self.lines:
            if ln["who"] == who and ln["start"] - 0.05 <= t <= ln["end"]:
                return bump(t, ln["start"] - 0.05, ln["end"], 0.08)
        return 0.0


def talk_head(tl, who, t, phase=0.0):
    e = tl.talking(who, t)
    return (0.07 * e * math.sin(2 * math.pi * 5.2 * t + phase),
            0.04 * e * math.sin(2 * math.pi * 2.3 * t + phase), 0.0)


def walk_cycle(t, t0, rate=2.2, amp=0.6):
    ph = 2 * math.pi * rate * (t - t0)
    s = math.sin(ph)
    return {"leg_r": (amp * s, 0, 0), "leg_l": (-amp * s, 0, 0),
            "arm_r": (-amp * 0.8 * s, 0, 0), "arm_l": (amp * 0.8 * s, 0, 0),
            "bob": 0.035 * abs(math.sin(ph))}


# ------------------------------------------------------------- choreography

def noob_pose(tl, t):
    po0, _ = tl["portal_open"]
    f0, f1 = tl["fall"]
    l0, l1 = tl["land"]
    la0, _ = tl["look_around"]
    _, n1e = tl["noob_1"]
    w0, w1 = tl["walk_to_tree"]
    n2s, n2e = tl["noob_2"]
    p0, p1 = tl["punch"]
    s1s, _ = tl["steve_1"]
    n3s, n3e = tl["noob_3"]
    fl0, fl1 = tl["flurry"]
    b0, b1 = tl["break"]
    n4s, n4e = tl["noob_4"]
    s2s, s2e = tl["steve_2"]
    c0, _ = tl["crack"]

    idle = 0.05 * math.sin(2 * math.pi * 0.6 * t)
    pose = {"loc": (*NOOB_LAND, 0.0), "yaw": 0.0, "scale": (1, 1, 1),
            "arm_r": (idle, 0, 0), "arm_l": (-idle, 0, 0),
            "head": talk_head(tl, "noob", t)}

    if t < f0:                                   # still inside the portal
        pose["loc"] = (*NOOB_LAND, PORTAL_Z - 0.5)
        pose["scale"] = (0.001,) * 3
        return pose
    if t < l0:                                   # falling, flailing
        u = (t - f0) / (l0 - f0)
        pose["loc"] = (*NOOB_LAND, (PORTAL_Z - 0.5) * (1 - u * u))
        pose["yaw"] = 0.9 * math.sin(u * math.pi)
        pose["arm_r"] = (-2.8 + 0.35 * math.sin(26 * t), 0, 0.3)
        pose["arm_l"] = (-2.8 + 0.35 * math.sin(26 * t + 1.3), 0, -0.3)
        pose["leg_r"] = (0.5 * math.sin(21 * t), 0, 0)
        pose["leg_l"] = (-0.5 * math.sin(21 * t), 0, 0)
        pose["head"] = (-0.3, 0, 0)
        return pose
    if t < w0:                                   # landed: squash, look around
        k = math.exp(-(t - l0) * 7) * math.cos((t - l0) * 22)
        pose["scale"] = (1 + 0.22 * k, 1 + 0.22 * k, 1 - 0.32 * k)
        drop = 1 - ss(l0, l0 + 0.25, t)
        pose["arm_r"] = (-2.8 * drop + idle, 0, 0.3 * drop)
        pose["arm_l"] = (-2.8 * drop - idle, 0, -0.3 * drop)
        look = 0.6 * math.sin(2 * math.pi * (t - la0) / 1.5) * ss(la0, la0 + 0.2, t) \
            * (1 - ss(n1e - 0.2, n1e + 0.1, t))
        pose["head"] = add(talk_head(tl, "noob", t), (0, 0, look))
        return pose

    # from here on he is at or walking to the tree
    if t < w1:
        u = ss(w0, w1, t)
        x, y = lerp(NOOB_LAND, NOOB_SPOT, u)
        wc = walk_cycle(t, w0)
        pose.update({k: wc[k] for k in ("leg_r", "leg_l", "arm_r", "arm_l")})
        pose["loc"] = (x, y, wc["bob"])
        pose["yaw"] = lerp(0.0, math.pi / 2, ss(w0, w0 + 0.3, t))
        return pose

    pose["loc"] = (*NOOB_SPOT, 0.0)
    yaw = math.pi / 2
    # "Okay. A tree..." half-turned to camera, swagger
    yaw -= 0.9 * bump(t, n2s, n2e + 0.05, 0.3)
    # turns to answer Steve, then back to the tree for the flurry
    turn = ss(s1s + 0.3, s1s + 0.7, t) * (1 - ss(fl0 - 0.12, fl0 + 0.02, t))
    yaw = lerp(yaw, -1.1, turn)
    # arms akimbo while bragging
    akimbo = bump(t, n3s, n3e + 0.05, 0.2)
    pose["arm_r"] = add(pose["arm_r"], (0.3 * akimbo, 0.55 * akimbo, 0))
    pose["arm_l"] = add(pose["arm_l"], (0.3 * akimbo, -0.55 * akimbo, 0))

    # the first punch: wind-up, strike, then a stinging hand
    hit = p0 + 0.18
    if p0 <= t < p1:
        if t < p0 + 0.08:
            a = 0.5 * ss(p0, p0 + 0.08, t)
            pose["arm_r"] = (a, 0, 0)
        elif t < hit + 0.12:
            e = ss(p0 + 0.08, hit, t)
            pose["arm_r"] = (lerp(0.5, -1.57, e), 0, 0.55 * e)
        else:
            e = 1 - ss(hit + 0.12, hit + 0.45, t)
            shake = 0.25 * math.sin(42 * t) * (1 - ss(hit + 0.2, p1, t))
            pose["arm_r"] = (-1.57 * e + shake, 0, 0.55 * e)
            pose["head"] = add(pose["head"], (0, 0, 0.15 * math.sin(30 * t) * e))
        recoil = 0.1 * bump(t, hit, p1, 0.08)
        pose["loc"] = (NOOB_SPOT[0] - recoil, NOOB_SPOT[1], 0)

    # the flurry: alternate fists on every impact time
    if fl0 - 0.1 <= t < b0 + 0.05:
        hits = [h for h in tl.impacts if fl0 <= h <= fl1]
        for i, h in enumerate(hits):
            e = ss(h - 0.07, h, t) * (1 - ss(h + 0.02, h + 0.11, t))
            side = "arm_r" if i % 2 == 0 else "arm_l"
            zz = 0.55 if side == "arm_r" else -0.55
            if e > 0:
                pose[side] = (lerp(-0.25, -1.57, e), 0, zz * e)
        pose["loc"] = (NOOB_SPOT[0] + 0.03 * math.sin(60 * t), NOOB_SPOT[1], 0)

    # the block breaks: arms up, a little jump
    if b0 <= t < n4s:
        up = bump(t, b0 + 0.08, n4s, 0.12)
        pose["arm_r"] = (-2.8 * up, 0, 0.25 * up)
        pose["arm_l"] = (-2.8 * up, 0, -0.25 * up)
        j = (t - b0 - 0.1) / 0.42
        if 0 <= j <= 1:
            pose["loc"] = (*NOOB_SPOT, 0.4 * math.sin(math.pi * j))

    # "Why is it floating?" looking up at the tree, then glancing at Steve
    look_up = ss(n4s - 0.1, n4s + 0.2, t) * (1 - ss(c0, c0 + 0.3, t))
    glance = ss(s2s, s2s + 0.2, t) * (1 - ss(s2e + 0.15, s2e + 0.4, t))
    pose["head"] = add(pose["head"], (-0.4 * look_up * (1 - glance), 0, -0.9 * glance))

    # the crack: turn to face the sky
    if t >= c0:
        u = ss(c0 + 0.25, c0 + 0.8, t)
        yaw = lerp(yaw, math.pi, u)
        pose["head"] = add(talk_head(tl, "noob", t), (-0.5 * u, 0, 0))
        fear = -0.5 * u
        pose["arm_r"] = (fear, 0, 0.15 * u)
        pose["arm_l"] = (fear, 0, -0.15 * u)
    pose["yaw"] = yaw
    return pose


def steve_pose(tl, t):
    w0, _ = tl["walk_to_tree"]
    s1s, s1e = tl["steve_1"]
    n3s, n3e = tl["noob_3"]
    b0, _ = tl["break"]
    s2s, s2e = tl["steve_2"]
    c0, _ = tl["crack"]
    arrive = s1s - 0.35

    idle = 0.04 * math.sin(2 * math.pi * 0.5 * t + 1.0)
    pose = {"loc": (*STEVE_SPOT, 0.0), "yaw": math.pi / 2,
            "arm_l": (-0.3, 0, 0), "arm_r": (idle, 0, 0),
            "head": talk_head(tl, "steve", t, 1.0)}
    if t < arrive:
        u = clamp((t - w0) / (arrive - w0))
        x, y = lerp(STEVE_START, STEVE_SPOT, u)
        wc = walk_cycle(t, w0, rate=1.9, amp=0.55)
        moving = 0 < u < 1
        pose["loc"] = (x, y, wc["bob"] if moving else 0)
        if moving:
            pose.update({k: wc[k] for k in ("leg_r", "leg_l", "arm_r")})
            pose["arm_l"] = (-0.3 + wc["arm_l"][0] * 0.3, 0, 0)
        return pose

    # "You need a tool." raises the pickaxe
    show = bump(t, s1s + 0.55, s1e + 0.25, 0.2)
    pose["arm_l"] = (-0.3 - 0.95 * show, 0, 0)
    # unimpressed head tilt while the Noob brags
    tilt = bump(t, n3s, n3e, 0.3)
    # watches the floating tree, then the deadpan look to camera
    look_up = ss(b0 + 0.3, b0 + 0.6, t) * (1 - ss(s2s - 0.1, s2s + 0.15, t))
    deadpan = ss(s2s - 0.1, s2s + 0.15, t) * (1 - ss(c0, c0 + 0.25, t))
    pose["head"] = add(pose["head"], (-0.35 * look_up, 0.15 * tilt, -1.1 * deadpan))

    if t >= c0:
        u = ss(c0 + 0.1, c0 + 0.6, t)
        pose["yaw"] = lerp(math.pi / 2, math.pi, u)
        pose["head"] = add(talk_head(tl, "steve", t, 1.0), (-0.55 * u, 0, 0))
    return pose


# --------------------------------------------------------------- the world

def setup_render(res, samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.04
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 0
    sc.cycles.volume_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 4
    sc.render.use_persistent_data = True
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.render.resolution_x = res * 9 // 16
    sc.render.resolution_y = res
    sc.render.fps = FPS
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Punchy", "Punchy", "AgX - Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue


def sky(tl):
    w = bpy.data.worlds.new("sky")
    bpy.context.scene.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (0.95, 0.66, 0.42, 1)
    el[1].position, el[1].color = 0.6, (0.14, 0.33, 0.85, 1)
    mid = el.new(0.22)
    mid.color = (0.75, 0.68, 0.72, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    c0 = tl["crack"][0]
    s = bg.inputs["Strength"]
    for t, v in ((0, 1.25), (c0, 1.25), (c0 + 0.5, 0.4)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=F(t))

    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    bpy.context.scene.collection.objects.link(sun)
    sun.data.color = (1.0, 0.86, 0.68)
    sun.data.angle = math.radians(2.5)
    aim(sun, (0.3, 0.75, -0.6))
    for t, v in ((0, 5.0), (c0, 5.0), (c0 + 0.5, 1.2)):
        sun.data.energy = v
        sun.data.keyframe_insert("energy", frame=F(t))


def terrain(mats, rnd):
    cells = {}
    heights = {}
    for x in range(-32, 32):
        for y in range(-32, 32):
            d = math.hypot(x - 1, y - 1)
            if d < 9:
                h = 0
            else:
                w = min(1.0, (d - 9) / 6)
                h = (d - 9) * 0.13 * (1 + 0.5 * math.sin(x * 0.4) * math.cos(y * 0.3)) \
                    + 1.3 * (math.sin(x / 5.0) + math.cos(y / 6.0)) * w
                h = max(0, int(round(h)))
            heights[(x, y)] = h
            for z in range(-3, h):
                cells[(x, y, z)] = "grass" if z == h - 1 else ("dirt" if z >= h - 3 else "stone")
    voxels("terrain", cells, {
        "grass": {"top": mats["grass_top"], "side": mats["grass_side"], "bottom": mats["dirt"]},
        "dirt": {"side": mats["dirt"]},
        "stone": {"side": mats["stone"]},
    })
    return heights


def tree_cells(x, y, base, height, rnd):
    cells = {}
    for z in range(height):
        cells[(x, y, base + z)] = "log"
    top = base + height
    for z in range(top - 3, top + 1):
        r = 2 if z < top - 1 else 1
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if (x + dx, y + dy, z) in cells:
                    continue
                corner = abs(dx) == r and abs(dy) == r
                if corner and (z == top or rnd.random() < 0.6):
                    continue
                cells[(x + dx, y + dy, z)] = "leaves"
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        cells[(x + dx, y + dy, top + 1)] = "leaves"
    return cells


def forest(mats, heights, rnd):
    def blocked(x, y):
        if math.hypot(x - 1, y - 1) < 7.5:
            return True
        if -8 <= x <= 10 and -14 <= y <= 3:      # where the cameras stand
            return True
        if -7 <= x <= 9 and 3 <= y <= 15:        # the sky the last shot looks at
            return True
        return False

    cells, placed = {}, []
    tries = 0
    while len(placed) < 48 and tries < 3000:
        tries += 1
        x, y = rnd.randint(-28, 28), rnd.randint(-28, 28)
        if blocked(x, y) or any(abs(x - a) + abs(y - b) < 5 for a, b in placed):
            continue
        placed.append((x, y))
        cells.update(tree_cells(x, y, heights[(x, y)], rnd.randint(4, 6), rnd))
    log = {"top": mats["log_top"], "side": mats["log_side"], "bottom": mats["log_top"]}
    voxels("forest", cells, {"log": log, "leaves": {"side": mats["leaves"]}})


def hero_tree(mats, rnd):
    """The tree the Noob punches, in three pieces: stump, target block, and
    everything above it (which stays floating)."""
    log = {"top": mats["log_top"], "side": mats["log_side"], "bottom": mats["log_top"]}
    pal = {"log": log, "leaves": {"side": mats["leaves"]}}
    x, y = TREE
    stump = voxels("stump", {(x, y, 0): "log"}, pal)
    target = voxels("target", {(0, 0, 0): "log"}, pal, location=(x, y, 1))
    upper = tree_cells(x, y, 2, 5, random.Random(42))
    voxels("upper_tree", upper, pal)
    return target


def portal(tl, mats):
    p0, p1 = tl["portal_open"]
    l0, l1 = tl["land"]
    root = empty("portal", (*NOOB_LAND, PORTAL_Z))
    ring = {}
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) == 2 or abs(j) == 2:
                ring[(i, j, 0)] = "null"
    r = voxels("portal_ring", ring, {"null": {"side": mats["null"]}})
    r.location = (-0.5, -0.5, 0)
    r.parent = root

    m = bpy.data.materials.new("portal_glow")
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n != out:
            nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.25, 0.02, 0.6, 1)
    ramp.color_ramp.elements[1].color = (0.85, 0.5, 1.0, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 6.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    w = noise.inputs["W"]
    for f in range(1, F(l1 + 0.5) + 1):
        w.default_value = f * 0.06
        w.keyframe_insert("default_value", frame=f)
    box("portal_core", (3, 3, 0.05), (0, 0, 0.5), {"default": m}, root)

    light = bpy.data.objects.new("portal_light", bpy.data.lights.new("portal_light", "POINT"))
    bpy.context.scene.collection.objects.link(light)
    light.location = (*NOOB_LAND, PORTAL_Z - 1.2)
    light.data.color = (0.7, 0.3, 1.0)
    light.data.shadow_soft_size = 1.5
    for t, s, e in ((0, 0.001, 0), (p1, 1.0, 2500), (l0 + 0.2, 1.0, 2500), (l1 + 0.35, 0.001, 0)):
        root.scale = (s, s, s)
        root.keyframe_insert("scale", frame=F(t))
        light.data.energy = e
        light.data.keyframe_insert("energy", frame=F(t))


def sky_crack(tl):
    c0, c1 = tl["crack"]
    root = empty("crack", (-5.0, 40.0, 26.0))
    root.scale = (2.0, 2.0, 2.0)
    root.rotation_euler = (math.radians(70), 0, 0)   # face the low camera
    core = material("crack_core", (1, 1, 1), emission=(0.92, 0.75, 1.0), strength=30)
    glow = material("crack_glow", (0, 0, 0), emission=(0.45, 0.1, 1.0), strength=12)
    rnd = random.Random(3)
    pts = [(-11.0, 0.0)]
    while pts[-1][0] < 11:
        x, z = pts[-1]
        pts.append((x + rnd.uniform(1.4, 2.6), z + rnd.uniform(-1.8, 1.8)))
    segs = list(zip(pts, pts[1:]))
    # two branches off the main line
    for i in (3, 6):
        (x, z), _ = segs[i]
        segs.append(((x, z), (x + rnd.uniform(0.5, 1.5), z + rnd.uniform(2, 3.5))))
    order = sorted(range(len(segs)), key=lambda i: abs(segs[i][0][0]))
    for rank, i in enumerate(order):
        (x0, z0), (x1, z1) = segs[i]
        L = math.hypot(x1 - x0, z1 - z0)
        seg = empty(f"crack_{i}", (x0, 0, z0), root)
        seg.rotation_euler = (0, -math.atan2(z1 - z0, x1 - x0), 0)
        box(f"crack_core_{i}", (L, 0.1, 0.22), (L / 2, 0, 0), {"default": core}, seg)
        box(f"crack_glow_{i}", (L + 0.3, 0.05, 0.75), (L / 2, 0.1, 0), {"default": glow}, seg)
        start = c0 + 0.15 + rank * 0.06
        for t, s in ((0, 0.0), (start, 0.0), (start + 0.12, 1.0)):
            seg.scale = (max(s, 0.001),) + ((1, 1) if s else (0.001, 0.001))
            seg.keyframe_insert("scale", frame=F(t))
    # flicker
    b = glow.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f in range(F(c0), F(tl.length + 0.5)):
        b.default_value = 9 + 6 * rnd.random()
        b.keyframe_insert("default_value", frame=f)


def clouds(rnd):
    m = material("cloud", (1, 1, 1), rough=1.0, emission=(1, 1, 1), strength=0.35)
    for i in range(9):
        cx, cy = rnd.randint(-40, 40), rnd.randint(10, 60)
        cells = {}
        w, d = rnd.randint(8, 14), rnd.randint(4, 8)
        for dx in range(w):
            for dy in range(d):
                corner = (dx in (0, w - 1)) and (dy in (0, d - 1))
                if not corner:
                    cells[(dx, dy, 0)] = "c"
        voxels(f"cloud_{i}", cells, {"c": {"side": m}}, location=(cx, cy, 42))


def debris(tl, mats, rnd):
    """Wood chips when the block breaks: simple ballistics with a bounce."""
    b0 = tl["break"][0]
    x, y = TREE
    chips = []
    for i in range(16):
        s = rnd.uniform(0.1, 0.18)
        ob = box(f"chip_{i}", (s, s, s), (0, 0, 0), {"default": mats["log_side"]})
        v = (rnd.uniform(-3.5, 1.0), rnd.uniform(-2.5, 2.5), rnd.uniform(2.5, 5.5))
        p = (x + 0.5 + rnd.uniform(-0.3, 0.3), y + 0.5 + rnd.uniform(-0.3, 0.3), 1.5)
        spin = (rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(-12, 12))
        chips.append((ob, v, p, spin, s))
    for ob, v, p, spin, s in chips:
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=F(b0))
        # time to hit the ground: p.z + v.z t - 7 t^2 = s/2
        tland = (v[2] + math.sqrt(v[2] ** 2 + 28 * (p[2] - s / 2))) / 14
        for f in range(F(b0), F(b0 + 1.4)):
            t = (f - F(b0)) / FPS
            if t < tland:
                z = p[2] + v[2] * t - 7 * t * t
            else:
                after = t - tland
                z = s / 2 + 0.25 * abs(math.sin(after * 9)) * math.exp(-after * 6)
                t = tland + 0.15 * (1 - math.exp(-after * 6))
            ob.location = (p[0] + v[0] * t, p[1] + v[1] * t, z)
            ob.rotation_euler = tuple(w * t for w in spin)
            k = 1 - ss(b0 + 0.9, b0 + 1.35, b0 + (f - F(b0)) / FPS)
            ob.scale = (max(k, 0.001),) * 3
            for path in ("location", "rotation_euler", "scale"):
                ob.keyframe_insert(path, frame=f)


def target_block(tl, target):
    b0 = tl["break"][0]
    x, y = TREE
    for f in range(1, F(b0) + 1):
        t = (f - 1) / FPS
        j = sum(math.exp(-(t - h) * 30) for h in tl.impacts if 0 <= t - h < 0.2)
        target.location = (x + 0.05 * j * math.sin(80 * t), y + 0.04 * j * math.cos(70 * t), 1)
        target.keyframe_insert("location", frame=f)
    target.hide_render = False
    target.keyframe_insert("hide_render", frame=1)
    target.hide_render = True
    target.keyframe_insert("hide_render", frame=F(b0))


# ----------------------------------------------------------------- cameras

def camera(name, lens, path, look, t0, t1, dof=None, shake=0.012, seed=0):
    """path/look: lists of (t, (x, y, z)), eased between keys."""
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36
    cam.data.clip_end = 400
    tgt = empty(name + "_aim")
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    if dof:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = tgt
        cam.data.dof.aperture_fstop = dof

    def at(keys, t):
        if callable(keys):
            return keys(t)
        if t <= keys[0][0]:
            return keys[0][1]
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if t <= tb:
                return lerp(a, b, ss(ta, tb, t))
        return keys[-1][1]

    for f in range(F(t0) - 1, F(t1) + 2):
        t = (f - 1) / FPS
        loc = at(path, t)
        n = (shake * math.sin(2 * math.pi * 0.7 * t + seed),
             shake * math.sin(2 * math.pi * 0.53 * t + 2 + seed),
             shake * math.sin(2 * math.pi * 0.61 * t + 4 + seed))
        cam.location = add(loc, n)
        cam.keyframe_insert("location", frame=f)
        tgt.location = at(look, t)
        tgt.keyframe_insert("location", frame=f)
    return cam


def shots(tl, noob_at):
    end = tl.length + 0.4
    la0 = tl["look_around"][0]
    w0 = tl["walk_to_tree"][0]
    s1s = tl["steve_1"][0]
    n3s = tl["noob_3"][0]
    fl0 = tl["flurry"][0]
    b0 = tl["break"][0]
    n4s = tl["noob_4"][0]
    c0 = tl["crack"][0]
    f0 = tl["fall"][0]

    def follow_fall(t):
        z = noob_at(t)[2]
        return (NOOB_LAND[0], NOOB_LAND[1], max(1.4, z * 0.9 + 1.0)) if t >= f0 \
            else (NOOB_LAND[0], NOOB_LAND[1], PORTAL_Z - 1)

    head = (STEVE_SPOT[0], STEVE_SPOT[1], 1.72)
    plan = [
        (0, camera("camA", 16, [(0, (-4.4, -9.2, 0.7)), (tl["land"][0], (-2.4, -5.4, 0.8)), (la0, (-2.2, -5.1, 0.85))],
                   follow_fall, 0, la0)),
        (la0, camera("camB", 30, [(la0, (0.95, -3.7, 1.45)), (w0, (0.8, -3.2, 1.5))],
                     [(la0, (0.2, -0.4, 1.6))], la0, w0, dof=4.0)),
        (w0, camera("camB2", 24, [(w0, (3.3, -2.6, 1.45)), (s1s, (3.4, -1.2, 1.45))],
                    [(w0, (0.5, -0.2, 1.3)), (w0 + 1.0, (1.1, 0.35, 1.35))], w0, s1s, dof=4.0, seed=1)),
        (s1s, camera("camC", 38, [(s1s, (0.7, -1.35, 1.85)), (n3s, (0.55, -1.15, 1.85))],
                     [(s1s, head)], s1s, n3s, dof=2.8, seed=2)),
        (n3s, camera("camD", 22, [(n3s, (0.9, -7.4, 2.0)), (n4s, (0.9, -6.4, 2.1))],
                     [(n3s, (0.9, 0.5, 2.4))], n3s, n4s, seed=3)),
        (fl0, camera("camD2", 20, [(fl0, (3.4, -1.5, 0.9)), (b0 + 0.45, (3.3, -1.3, 0.85))],
                     [(fl0, (1.5, 0.4, 1.5))], fl0, b0 + 0.45, shake=0.03, seed=4)),
        (b0 + 0.45, "camD"),
        (n4s, camera("camE", 19, [(n4s, (4.4, -2.7, 0.35)), (c0, (4.2, -2.5, 0.4))],
                     [(n4s, (1.6, 0.5, 2.6))], n4s, c0, seed=5)),
        (c0, camera("camF", 17, [(c0, (-0.2, -3.4, 0.55)), (end, (-0.2, -3.0, 0.5))],
                    [(c0, (-2.8, 12, 6.5)), (end, (-2.8, 12, 9.0))], c0, end, seed=6)),
    ]
    sc = bpy.context.scene
    cams = {}
    for t, cam in plan:
        if isinstance(cam, str):
            cam = cams[cam]
        cams[cam.name] = cam
        m = sc.timeline_markers.new(cam.name, frame=F(t))
        m.camera = cam
    sc.camera = cams["camA"]


# -------------------------------------------------------------------- main

def build(timeline_path, tex_dir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tl = TL(timeline_path)
    tex_dir = os.path.abspath(tex_dir)
    tex = {os.path.splitext(n)[0]: os.path.join(tex_dir, n) for n in os.listdir(tex_dir)}
    mats = {k: material(k, tex=v) for k, v in tex.items()
            if k in ("grass_top", "grass_side", "dirt", "stone", "log_side",
                     "log_top", "leaves", "null")}
    rnd = random.Random(11)

    sky(tl)
    heights = terrain(mats, rnd)
    forest(mats, heights, rnd)
    target = hero_tree(mats, rnd)
    target_block(tl, target)
    portal(tl, mats)
    sky_crack(tl)
    clouds(rnd)
    debris(tl, mats, rnd)

    noob = make_noob(tex)
    steve = make_steve(tex)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = F(tl.length + 0.4)
    for f in range(1, sc.frame_end + 1):
        t = (f - 1) / FPS
        noob.key_pose(f, noob_pose(tl, t))
        steve.key_pose(f, steve_pose(tl, t))
    shots(tl, lambda t: noob_pose(tl, t)["loc"])
    return tl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("tex_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--first", type=int)
    ap.add_argument("--last", type=int)
    ap.add_argument("--res", type=int, default=720, help="output height in pixels")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--save-blend")
    ap.add_argument("--stills", help="comma-separated frames to render as single images")
    a = ap.parse_args()

    build(a.timeline, a.tex_dir)
    setup_render(a.res, a.samples)
    sc = bpy.context.scene
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
    os.makedirs(a.out_dir, exist_ok=True)
    if a.stills:
        for f in (int(x) for x in a.stills.split(",")):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(os.path.abspath(a.out_dir), f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    sc.frame_start = a.first or sc.frame_start
    sc.frame_end = a.last or sc.frame_end
    os.makedirs(a.out_dir, exist_ok=True)
    sc.render.filepath = os.path.join(os.path.abspath(a.out_dir), "")
    bpy.ops.render.render(animation=True)
    print("rendered", sc.frame_start, "-", sc.frame_end)


if __name__ == "__main__":
    main()
