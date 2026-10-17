"""
Effects. Each takes the build context (`ctx`: frame converter F, time
resolver T, the timeline) plus its own parameters, and keys everything it
needs. Timing always comes from the timeline, so effects stay on the sound.
"""

import math
import random

import bpy
from mathutils import Vector

from kit.actions import lerp, ss, yaw_towards
from kit.blocks import aim, box, empty, hide_at, material, show_between, voxels
from kit.rigs import srgb

POC_SUN = (0.3, 0.75, -0.6)                  # episode 2's sun, for the shared shot


# ------------------------------------------------------------ sky and light

def sky(ctx, sun_dir, keys):
    """World (episode 2's sky above the horizon, the void below it), a sun
    lamp and a visible square sun. keys: [(t, sun_energy, sky_strength,
    sun_dir or None)] in seconds."""
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
    el.new(0.22).color = (0.75, 0.68, 0.72, 1)
    below = nt.nodes.new("ShaderNodeMapRange")
    below.inputs["From Min"].default_value = -0.12
    below.inputs["From Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], below.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(below.outputs["Result"], mix.inputs["Factor"])
    mix.inputs["A"].default_value = (0.03, 0.01, 0.06, 1)          # the void
    nt.links.new(ramp.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"])

    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    bpy.context.scene.collection.objects.link(sun)
    sun.data.color = (1.0, 0.88, 0.7)
    sun.data.angle = math.radians(2.5)
    d = Vector(sun_dir).normalized()
    # a square sun (block-world style) with two soft glow layers, so it
    # reads as the sun and not as a white box
    glows = []
    for k, (size, strength, alpha) in enumerate(((34, 12, 1.0), (60, 1.6, 0.35), (100, 0.6, 0.15))):
        m = material(f"sun_glow_{k}", (1, 1, 1), emission=(1.0, 0.86, 0.55), strength=strength)
        if alpha < 1:
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Alpha"].default_value = alpha
            if hasattr(m, "surface_render_method"):
                m.surface_render_method = "BLENDED"
        disc = box(f"sun_disc_{k}", (size, size, 0.1), (0, 0, 0), {"default": m})
        disc.location = -d * (320 + k * 2)
        disc.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        glows.append((m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], strength))
    strength = bg.inputs["Strength"]
    for t, energy, sky_s, direction in keys:
        f = ctx.F(t)
        sun.data.energy = energy
        sun.data.keyframe_insert("energy", frame=f)
        strength.default_value = sky_s
        strength.keyframe_insert("default_value", frame=f)
        aim(sun, direction or sun_dir)
        sun.keyframe_insert("rotation_euler", frame=f)
        for sock, base in glows:                 # the visible sun dims with the light
            sock.default_value = base * min(1.0, energy / 5.0) ** 2
            sock.keyframe_insert("default_value", frame=f)
    return sun


def backlight(ctx, location, direction, t_on, t_off, color=(0.7, 0.25, 1.0), energy=25000):
    lamp = bpy.data.objects.new("backlight", bpy.data.lights.new("backlight", "AREA"))
    bpy.context.scene.collection.objects.link(lamp)
    lamp.data.size = 25
    lamp.data.color = color
    lamp.location = location
    aim(lamp, direction)
    for t, e in ((0, 0), (t_on, 0), (t_on + 0.8, energy), (t_off - 0.01, energy), (t_off, 0)):
        lamp.data.energy = e
        lamp.data.keyframe_insert("energy", frame=ctx.F(max(t, 0)))


# ------------------------------------------------- things that stop moving

def drifting_clouds(ctx, freeze_at, n=10, seed=4, speed=2.0, z=44):
    rnd = random.Random(seed)
    m = material("seam_cloud", (1, 1, 1), rough=1.0, emission=(1, 1, 1), strength=0.35)
    for i in range(n):
        w, d = rnd.randint(8, 16), rnd.randint(4, 9)
        cells = {(dx, dy, 0): "c" for dx in range(w) for dy in range(d)
                 if not ((dx in (0, w - 1)) and (dy in (0, d - 1)))}
        ob = voxels(f"scloud_{i}", cells, {"c": {"side": m}},
                    location=(rnd.uniform(-70, 80), rnd.uniform(-50, 70), z + rnd.uniform(-3, 3)))
        x0 = ob.location.x
        for t in (0, freeze_at):
            ob.location.x = x0 + speed * t
            ob.keyframe_insert("location", frame=ctx.F(t))


def birds(ctx, freeze_at, spots, seed=6, end=None):
    """Small flapping birds that hang motionless in the air from `freeze_at`."""
    rnd = random.Random(seed)
    m = material("bird", (0.05, 0.05, 0.06), rough=0.9)
    for i, (x, y, z) in enumerate(spots):
        b = empty(f"bird_{i}", (x, y, z))
        box(f"bird_body_{i}", (0.18, 0.5, 0.14), (0, 0, 0), {"default": m}, b)
        wings = []
        for side in (-1, 1):
            hinge = empty(f"bird_wing_{i}_{side}", (0.08 * side, 0, 0), b)
            box(f"bird_wingbox_{i}_{side}", (0.7, 0.26, 0.04), (0.35 * side, 0, 0), {"default": m}, hinge)
            wings.append((hinge, side))
        vel = (rnd.uniform(1.5, 3.0), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.2, 0.2))
        b.rotation_euler = (0, 0, yaw_towards(vel[0], vel[1]) + math.pi)
        ph = rnd.uniform(0, 6)
        last = ctx.F(end) if end else ctx.F(freeze_at) + 1
        for f in range(1, ctx.F(freeze_at) + 1):
            t = (f - 1) / ctx.fps
            b.location = (x + vel[0] * t, y + vel[1] * t, z + vel[2] * t + 0.15 * math.sin(3 * t + ph))
            b.keyframe_insert("location", frame=f)
            for hinge, side in wings:
                hinge.rotation_euler = (0, side * 0.7 * math.sin(13 * t + ph), 0)
                hinge.keyframe_insert("rotation_euler", frame=f)
        _ = last


# -------------------------------------------------------------- the erasure

def erase(ctx, item, t, flash_frames=2):
    f = ctx.F(t)
    if item.get("flash") is not None:
        show_between(item["flash"], f, f + flash_frames)
    hide_at(item["ob"], f + (flash_frames if item.get("flash") is not None else 0))


def erasure(ctx, items, times, origin=(70.0, 0.0)):
    """Items vanish in order of distance from `origin`: the corruption sweeps
    towards the heroes. `times` (from the timeline) are the pops in the
    soundtrack; items share them evenly."""
    items = sorted(items, key=lambda it: math.hypot(it["center"][0] - origin[0],
                                                     it["center"][1] - origin[1]))
    n = len(times)
    for i, it in enumerate(items):
        erase(ctx, it, times[min(n - 1, int(i * n / len(items)))])


def bridge_ripple(ctx, blocks, times, flash_mat, sign=None):
    """The bridge deletes from the far end towards the cliff."""
    for ob, t in zip(reversed(blocks), times):
        twin = None
        if ob.type == "MESH":
            twin = ob.copy()
            bpy.context.scene.collection.objects.link(twin)
            for slot in twin.material_slots:
                slot.link = "OBJECT"
                slot.material = flash_mat
            twin["is_flash"] = 1
        erase(ctx, {"ob": ob, "flash": twin}, t, flash_frames=1)
        if sign is not None and ob.name == "bridge_3":
            hide_at(sign, ctx.F(t))


def obby_run(ctx, platforms, avatars, t0, t1, flash_mat, hop=0.42):
    """Avatars flee along the floating platforms; each platform is erased
    behind the last runner, and at `t1` the rest go and everyone falls."""
    tops = [p["top"] for p in platforms]
    n = len(tops)
    starts = [3.0, 1.6, 0.2][:len(avatars)]
    fall_at = t1

    def where(s):
        s = max(0.0, min(n - 1.0, s))
        k = min(int(s), n - 2)
        u = s - k
        a, b = tops[k], tops[k + 1]
        z = lerp(a[2], b[2], u) + 0.9 * math.sin(math.pi * u)
        return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), z), yaw_towards(b[0] - a[0], b[1] - a[1])

    erased = set()
    for i, (rig, s0) in enumerate(zip(avatars, starts)):
        fall_from = None
        for f in range(1, ctx.F(t1 + 1.6) + 1):
            t = (f - 1) / ctx.fps
            s = s0 + max(0.0, t - t0) / hop
            if t < fall_at and s < n - 1:
                loc, yaw = where(s)
                ph = 2 * math.pi * 1.4 * (t - t0)
                a = 1.0 * math.sin(ph)
                pose = {"loc": loc, "yaw": yaw, "leg_r": (a, 0, 0), "leg_l": (-a, 0, 0),
                        "arm_r": (-0.8 * a, 0, 0), "arm_l": (0.8 * a, 0, 0)}
            else:
                if fall_from is None:
                    fall_from = (t, where(min(s, n - 1.0))[0], where(min(s, n - 1.0))[1])
                tf, l0, yaw = fall_from
                k = t - tf
                loc = (l0[0] - 1.5 * k, l0[1] + 0.4 * k, l0[2] - 9 * k * k)
                fl = math.sin(24 * t + i)
                pose = {"loc": loc, "yaw": yaw, "arm_r": (-2.7 + 0.4 * fl, 0, 0.3),
                        "arm_l": (-2.7 - 0.4 * fl, 0, -0.3), "leg_r": (0.4 * fl, 0, 0),
                        "leg_l": (-0.4 * fl, 0, 0), "head": (-0.4, 0, 0)}
            rig.key_pose(f, pose)
    for rig in avatars:                       # gone into the void
        hide_at(rig.root, ctx.F(t1 + 1.6))
    # platforms vanish once the last runner is past them; the rest at t1
    last = min(starts)
    for k, p in enumerate(platforms):
        t_gone = t0 + (k + 1.3 - last) * hop
        t_gone = min(t_gone, fall_at) if t_gone > t0 else t0 + 0.05
        twin = p["ob"].copy()
        bpy.context.scene.collection.objects.link(twin)
        for slot in twin.material_slots:
            slot.link = "OBJECT"
            slot.material = flash_mat
        twin["is_flash"] = 1
        erase(ctx, {"ob": p["ob"], "flash": twin}, t_gone)
        erased.add(k)


# --------------------------------------------------------------------- Null

def orbit(ctx, center_of, t0, t1, tex, mats, n=30, seed=9):
    """Broken blocks orbiting a moving centre (Null's chest)."""
    rnd = random.Random(seed)
    choices = [mats["grass_side"], mats["dirt"], mats["null"], mats["log_side"], mats["planks"]] + \
        [material(f"orbit_plastic_{k}", srgb(c), rough=0.3, coat=0.3)
         for k, c in enumerate(((232, 64, 64), (60, 150, 240), (245, 210, 50)))]
    for i in range(n):
        s = rnd.uniform(0.6, 1.8)
        ob = box(f"orbit_{i}", (s, s, s), (0, 0, 0), {"default": rnd.choice(choices)})
        r = rnd.uniform(9, 17)
        w = rnd.uniform(0.25, 0.55) * rnd.choice((-1, 1))
        tilt = rnd.uniform(-0.5, 0.5)
        ph = rnd.uniform(0, 2 * math.pi)
        hz = rnd.uniform(-5, 5)
        spin = [rnd.uniform(-1.5, 1.5) for _ in range(3)]
        show_between(ob, ctx.F(t0), ctx.F(t1))
        for f in range(ctx.F(t0), ctx.F(t1) + 1):
            t = (f - 1) / ctx.fps
            c = center_of(t)
            a = ph + w * t
            x, y = r * math.cos(a), r * math.sin(a)
            ob.location = (c[0] + x, c[1] + y * math.cos(tilt), c[2] + hz + y * math.sin(tilt))
            ob.rotation_euler = tuple(k * t for k in spin)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)


def fill(ctx, direction, t_on, t_off, color=(0.45, 0.5, 1.0), energy=1.6):
    """A soft second sun for night scenes, so dark characters stay readable."""
    lamp = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
    bpy.context.scene.collection.objects.link(lamp)
    lamp.data.color = color
    lamp.data.angle = math.radians(10)
    aim(lamp, direction)
    for t, e in ((0, 0), (t_on, 0), (t_on + 0.8, energy), (t_off - 0.01, energy), (t_off, 0)):
        lamp.data.energy = e
        lamp.data.keyframe_insert("energy", frame=ctx.F(max(t, 0)))


def erase_named(ctx, items, names, t):
    """Erase specific chunks (e.g. the ledge the heroes hang from)."""
    for it in items:
        if it["ob"].name in names:
            erase(ctx, it, t)


def forest_portal(ctx, root, t_open, t_land, mats):
    """Episode 1's portal over the forest clearing, opening on cue."""
    import scene_poc as poc
    before = set(bpy.data.objects)
    beats = {"portal_open": [t_open, t_open + 0.6], "land": [t_land, t_land + 0.55]}
    poc.portal(beats, mats)
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None:
            ob.parent = root
