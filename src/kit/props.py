"""
Set pieces from episode 2 on, each built and keyed from the timeline:

  portal_machine  Steve's portal: obsidian blocks that pop in one by one,
                  a swirling surface that bursts open, goes dark, and snaps
                  shut with a flash
  button          the big red button (pressed, then smashed)
  spawn_pad       the Noob's respawn pad, leaking in from his world
  hazards         the obby pouring out: kill bricks and a spinning bar
  burst           the Noob breaking into his parts
  dark_cube       the small dark cube a death leaves behind (the series'
                  secret: never in frame centre, never mentioned)
  void_room       what is on the other side of a portal: a dark void with
                  floating debris, for a shot looking through a portal

Times that the soundtrack also needs (block placements, brick launches)
come from `spread`, which audio.py uses too.
"""

import math
import random

import bpy

from kit.actions import lerp, ss
from kit.blocks import box, empty, material, show_between
from kit.rigs import srgb

PLASTIC = dict(rough=0.32, spec=0.5, coat=0.3)
G = 9.0                                         # cartoon gravity


from kit.timeref import spread                                # noqa: E402,F401


def _key_scale(ob, ctx, keys):
    for t, s in keys:
        ob.scale = s if isinstance(s, tuple) else (s, s, s)
        ob.keyframe_insert("scale", frame=ctx.F(t))


def _cylinder(name, radius, depth, location, mat, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def _ballistic(ob, ctx, p0, v, t0, t1, ground=0.0, half=0.25, spin=(0, 0, 0), bounce=0.45):
    """Key a thrown object from t0 to t1: gravity, a couple of damped bounces."""
    x, y, z = p0
    vx, vy, vz = v
    dt = 1 / ctx.fps
    for f in range(ctx.F(t0), ctx.F(t1) + 1):
        t = (f - 1) / ctx.fps
        ob.location = (x, y, z)
        ob.rotation_euler = tuple(w * (t - t0) for w in spin)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
        vz -= G * dt
        x, y, z = x + vx * dt, y + vy * dt, z + vz * dt
        if z < ground + half:
            z = ground + half
            vz = -vz * bounce if abs(vz) > 1.0 else 0.0
            vx, vy = vx * 0.7, vy * 0.7
            spin = tuple(w * 0.6 for w in spin)


# ------------------------------------------------------------ the portal

def portal_machine(ctx, tex, origin, w=5, h=6, build=None, open_at=None, dark_at=None,
                   snap_at=None, name="portal"):
    """origin: the frame's bottom-left block corner. The frame is w x h blocks
    in the x-z plane, one block deep; it faces -y."""
    ox, oy, oz = origin
    obsidian = material(f"{name}_obsidian", tex=tex["obsidian"], rough=0.3, spec=0.6)
    ring = [(i, 0) for i in range(w)] + [(w - 1, j) for j in range(1, h)] + \
           [(i, h - 1) for i in range(w - 2, -1, -1)] + [(0, j) for j in range(h - 2, 0, -1)]
    times = spread(*build, len(ring)) if build else None
    blocks = []
    for k, (i, j) in enumerate(ring):
        b = box(f"{name}_block_{k}", (1, 1, 1), (0, 0, 0), {"default": obsidian})
        b.location = (ox + i + 0.5, oy + 0.5, oz + j + 0.5)
        if times:
            t = times[k]
            _key_scale(b, ctx, ((0, 0.001), (t - 0.01, 0.001), (t + 0.06, 1.15), (t + 0.14, 1.0)))
        blocks.append(b)
    center = (ox + w / 2, oy + 0.5, oz + h / 2)
    out = {"blocks": blocks, "center": center, "times": times}
    if open_at is None:
        return out

    # the surface: swirling emission, from noise drifting over time
    m = bpy.data.materials.new(f"{name}_surface")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Distortion"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.35, (0.35, 0.0, 0.7, 1)
    el[1].position, el[1].color = 0.65, (0.9, 0.05, 0.6, 1)
    el.new(0.5).color = (0.0, 0.55, 0.9, 1)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = (0.05, 0.0, 0.09, 1)      # gone dark: the void
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["A"])
    nt.links.new(mix.outputs["Result"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], outn.inputs["Surface"])
    surf = box(f"{name}_surface", (w - 2, 0.1, h - 2), (0, 0, 0), {"default": m})
    surf.location = center
    end = snap_at if snap_at is not None else ctx.end
    for t, wv in ((0, 0.0), (end + 1, (end + 1) * 1.3)):          # the swirl keeps moving
        noise.inputs["W"].default_value = wv
        noise.inputs["W"].keyframe_insert("default_value", frame=ctx.F(t))
    strength, dark = emit.inputs["Strength"], mix.inputs["Factor"]
    keys = [(0, 1.6, 0.0), (open_at, 5.0, 0.0), (open_at + 0.35, 1.6, 0.0)]
    if dark_at is not None:
        keys += [(dark_at, 1.6, 0.0), (dark_at + 0.35, 1.2, 1.0)]
    if snap_at is not None:
        keys += [(snap_at - 1 / ctx.fps, 1.2 if dark_at is not None else 1.6, 1.0 if dark_at is not None else 0.0),
                 (snap_at, 40.0, 0.0)]
    for t, s, d in keys:
        strength.default_value = s
        strength.keyframe_insert("default_value", frame=ctx.F(t))
        dark.default_value = d
        dark.keyframe_insert("default_value", frame=ctx.F(t))
    sk = [(0, 0.001), (open_at, 0.001), (open_at + 0.12, (1.12, 1, 1.12)), (open_at + 0.3, 1.0)]
    if snap_at is not None:
        sk += [(snap_at, 1.0), (snap_at + 0.05, (1.15, 1, 1.15)), (snap_at + 0.16, 0.001)]
    _key_scale(surf, ctx, sk)

    lamp = bpy.data.objects.new(f"{name}_light", bpy.data.lights.new(f"{name}_light", "POINT"))
    bpy.context.scene.collection.objects.link(lamp)
    lamp.data.color = (1.0, 0.3, 0.9)
    lamp.data.shadow_soft_size = 1.5
    lamp.location = (center[0], center[1] - 1.2, center[2])
    lk = [(0, 0), (open_at, 0), (open_at + 0.1, 4000), (open_at + 0.5, 900)]
    if dark_at is not None:
        lk += [(dark_at, 900), (dark_at + 0.35, 120)]
    if snap_at is not None:
        lk += [(snap_at - 1 / ctx.fps, 120 if dark_at is not None else 900), (snap_at, 9000), (snap_at + 0.25, 0)]
    for t, e in lk:
        lamp.data.energy = e
        lamp.data.keyframe_insert("energy", frame=ctx.F(t))
    out.update(surface=surf, light=lamp)
    return out


# ------------------------------------------------------------ the button

def button(ctx, at, press_at=None, smash_at=None, name="button"):
    x, y = at[:2]
    grey = material(f"{name}_base", srgb((150, 155, 165)), **PLASTIC)
    red = material(f"{name}_red", srgb((235, 30, 40)), rough=0.2, spec=0.7, coat=0.6,
                   emission=srgb((235, 30, 40)), strength=0.25)
    base = box(f"{name}_pedestal", (0.7, 0.7, 0.6), (0, 0, 0.3), {"default": grey}, bevel=0.05)
    base.location = (x, y, 0)
    cap = _cylinder(f"{name}_cap", 0.27, 0.18, (x, y, 0.69), red)
    if press_at is not None:
        for t, dz in ((0, 0), (press_at - 0.02, 0), (press_at + 0.05, -0.09), (press_at + 0.3, -0.09),
                      (press_at + 0.45, 0)):
            cap.location = (x, y, 0.69 + dz)
            cap.keyframe_insert("location", frame=ctx.F(t))
    if smash_at is not None:
        f = ctx.F(smash_at)
        for ob in (base, cap):
            for fr, hid in ((1, False), (f - 1, False), (f, True)):
                ob.hide_render = hid
                ob.keyframe_insert("hide_render", frame=fr)
        rnd = random.Random(21)
        for k in range(10):
            s = rnd.uniform(0.1, 0.22)
            sh = box(f"{name}_shard_{k}", (s, s, s), (0, 0, 0), {"default": red if k % 2 else grey})
            a = rnd.uniform(0, 2 * math.pi)
            v = (math.cos(a) * rnd.uniform(1.5, 3.5), math.sin(a) * rnd.uniform(1.5, 3.5), rnd.uniform(2.5, 5))
            show_between(sh, f, ctx.F(smash_at + 0.9))
            _ballistic(sh, ctx, (x, y, 0.6), v, smash_at, smash_at + 0.9, half=s / 2,
                       spin=[rnd.uniform(-12, 12) for _ in range(3)])
    return {"base": base, "cap": cap}


def spawn_pad(ctx, at, appear_at, name="spawn"):
    x, y = at[:2]
    grey = material(f"{name}_pad", srgb((120, 124, 132)), **PLASTIC)
    glow = material(f"{name}_ring", (0, 0, 0), emission=(0.2, 0.9, 1.0), strength=6)
    pad = _cylinder(f"{name}_disc", 0.75, 0.12, (x, y, 0.06), grey)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.035, location=(x, y, 0.13))
    ring = bpy.context.active_object
    ring.name = f"{name}_glow"
    ring.data.materials.append(glow)
    for ob in (pad, ring):
        _key_scale(ob, ctx, ((0, 0.001), (appear_at, 0.001), (appear_at + 0.1, 1.2), (appear_at + 0.22, 1.0)))
    em = glow.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f in range(ctx.F(appear_at), ctx.F(ctx.end) + 1, 3):
        em.default_value = 5 + 3 * math.sin(f * 0.5)
        em.keyframe_insert("default_value", frame=f)
    return {"pad": pad, "ring": ring}


# ------------------------------------------------------------ the obby's hazards

def hazards(ctx, src, t0, t1, clear_at, n=9, seed=4, hit=None, bar=None):
    """Kill bricks flung out of `src` at n evenly spread moments from t0 to t1,
    one of them (hit) aimed to land on a target at a given time; and a
    spinning red-and-white bar that lands at bar["at"] and sweeps under
    bar["pass_at"] (where someone has to jump) at bar["pass_t"]."""
    rnd = random.Random(seed)
    neon = material("kill_brick", srgb((255, 40, 40)), rough=0.25, spec=0.6, coat=0.4,
                    emission=srgb((255, 30, 30)), strength=2.5)
    objs = []
    for k, tl in enumerate(spread(t0, t1, n)):
        b = box(f"kill_brick_{k}", (0.5, 0.5, 0.5), (0, 0, 0), {"default": neon}, bevel=0.04)
        v = (rnd.uniform(-2.2, 2.6), -rnd.uniform(3.0, 5.5), rnd.uniform(2.5, 5.0))
        show_between(b, ctx.F(tl), ctx.F(clear_at))
        _ballistic(b, ctx, src, v, tl, clear_at, spin=[rnd.uniform(-8, 8) for _ in range(3)])
        objs.append(b)
    if hit:
        th, tgt = hit["t"], hit["target"]
        dt = hit.get("flight", 0.55)
        b = box("kill_brick_hit", (0.5, 0.5, 0.5), (0, 0, 0), {"default": neon}, bevel=0.04)
        v = tuple((tgt[i] - src[i]) / dt for i in range(3))
        v = (v[0], v[1], v[2] + 0.5 * G * dt)
        show_between(b, ctx.F(th - dt), ctx.F(clear_at))
        _ballistic(b, ctx, src, v, th - dt, th, spin=(9, 4, 0))
        # bounces off the Noob and drops
        _ballistic(b, ctx, tgt, (-v[0] * 0.2, -v[1] * 0.15, 2.5), th + 1 / ctx.fps, clear_at, spin=(5, 9, 2))
        objs.append(b)
    if bar:
        pivot = empty("spin_bar")
        red = material("bar_red", srgb((235, 40, 50)), **PLASTIC)
        white = material("bar_white", srgb((240, 240, 240)), **PLASTIC)
        L, seg = bar.get("length", 4.8), 8
        for k in range(seg):
            box(f"spin_bar_{k}", (L / seg + 0.002, 0.3, 0.3), (-L / 2 + (k + 0.5) * L / seg, 0, 0),
                {"default": red if k % 2 == 0 else white}, pivot, bevel=0.03)
        hub = box("spin_bar_hub", (0.45, 0.45, 0.6), (0, 0, -0.1), {"default": white}, pivot, bevel=0.06)
        land = bar["at"]
        rate = bar.get("rate", 0.8)
        px, py = bar["pass_at"][:2]
        a0 = math.atan2(py - land[1], px - land[0])
        tb, tp = bar["t"], bar["pass_t"]
        show_between(pivot, ctx.F(tb), ctx.F(clear_at))
        for f in range(ctx.F(tb), ctx.F(clear_at) + 1):
            t = (f - 1) / ctx.fps
            u = ss(tb, tb + 0.45, t)
            pivot.location = (lerp(src[0], land[0], u), lerp(src[1], land[1], u),
                              lerp(src[2], land[2], u) + 0.6 * math.sin(math.pi * u))
            pivot.rotation_euler = (0, 0, a0 + 2 * math.pi * rate * (t - tp))
            pivot.keyframe_insert("location", frame=f)
            pivot.keyframe_insert("rotation_euler", frame=f)
        objs.append(pivot)
    # cleared: everything pops away
    for ob in objs:
        _key_scale(ob, ctx, ((clear_at - 0.01, 1.0), (clear_at + 0.08, 1.3), (clear_at + 0.14, 0.001)))
    return objs


# ------------------------------------------------------------ death and respawn

NOOB_PARTS = (  # name, size, centre, colour
    ("head", (0.5, 0.46, 0.44), (0, 0, 1.84), (245, 205, 48)),
    ("torso", (0.8, 0.4, 0.8), (0, 0, 1.2), (30, 100, 220)),
    ("arm_r", (0.4, 0.4, 0.8), (-0.6, 0, 1.2), (245, 205, 48)),
    ("arm_l", (0.4, 0.4, 0.8), (0.6, 0, 1.2), (245, 205, 48)),
    ("leg_r", (0.4, 0.4, 0.8), (-0.2, 0, 0.4), (96, 182, 50)),
    ("leg_l", (0.4, 0.4, 0.8), (0.2, 0, 0.4), (96, 182, 50)),
)


def burst(ctx, at, t, parts=NOOB_PARTS, seed=5, name="burst"):
    """A character breaking into its parts, which fly apart and bounce."""
    rnd = random.Random(seed)
    for pn, size, c, col in parts:
        m = material(f"{name}_{pn}", srgb(col), **PLASTIC)
        ob = box(f"{name}_{pn}", size, (0, 0, 0), {"default": m}, bevel=0.03)
        p0 = (at[0] + c[0], at[1] + c[1], at[2] + c[2])
        d = (c[0] or rnd.uniform(-0.4, 0.4), rnd.uniform(-0.6, 0.6))
        v = (d[0] * 4 + rnd.uniform(-0.5, 0.5), d[1] * 3 - 1.0, rnd.uniform(2.5, 4.5))
        show_between(ob, ctx.F(t), ctx.F(t + 1.0))
        _ballistic(ob, ctx, p0, v, t, t + 1.0, half=min(size) / 2,
                   spin=[rnd.uniform(-9, 9) for _ in range(3)])
        _key_scale(ob, ctx, ((t + 0.8, 1.0), (t + 1.0, 0.001)))


def dark_cube(ctx, tex, start, t0, t1, drift=(0.32, 0.22, 0.5), name="dark_cube"):
    """Never comment on it, never put it in frame centre."""
    m = material(name, tex=tex["null"], rough=0.8, emit_tex=True, strength=0.4)
    ob = box(name, (0.17, 0.17, 0.17), (0, 0, 0), {"default": m})
    show_between(ob, ctx.F(t0), ctx.F(t1))
    for f in range(ctx.F(t0), ctx.F(t1) + 1):
        u = (f - 1) / ctx.fps - t0
        ob.location = (start[0] + drift[0] * u, start[1] + drift[1] * u,
                       start[2] + drift[2] * u + 0.05 * math.sin(3 * u))
        ob.rotation_euler = (0.7 * u, 1.1 * u, 0.4 * u)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)


# ------------------------------------------------------------ the other side

def void_room(ctx, tex, frame_origin, show, null_at, w=5, h=6, seed=12, name="void"):
    """Behind a (static) portal frame at frame_origin: a closed dark room the
    camera sees only through the frame, with stars, drifting obby debris,
    and dark cubes circling where Null stands."""
    rnd = random.Random(seed)
    ox, oy, oz = frame_origin
    portal_machine(ctx, tex, frame_origin, w, h, name=f"{name}_frame")
    wallm = bpy.data.materials.new(f"{name}_wall")
    wallm.use_nodes = True
    nt = wallm.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.08
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].color, el[1].color = (0.004, 0.0, 0.01, 1), (0.05, 0.0, 0.08, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], outn.inputs["Surface"])
    cx = ox + w / 2
    x0, x1, y0, y1, z0, z1 = cx - 16, cx + 16, oy + 1.05, oy + 30, -10, 22
    room = empty(f"{name}_room")
    for k, (size, c) in enumerate((((x1 - x0, 0.5, z1 - z0), (cx, y1, (z0 + z1) / 2)),
                                   ((0.5, y1 - y0, z1 - z0), (x0, (y0 + y1) / 2, (z0 + z1) / 2)),
                                   ((0.5, y1 - y0, z1 - z0), (x1, (y0 + y1) / 2, (z0 + z1) / 2)),
                                   ((x1 - x0, y1 - y0, 0.5), (cx, (y0 + y1) / 2, z0)),
                                   ((x1 - x0, y1 - y0, 0.5), (cx, (y0 + y1) / 2, z1)))):
        box(f"{name}_wall_{k}", size, c, {"default": wallm}, room)
    # the front: everything but the portal opening is closed too, so no sky leaks in
    for k, (size, c) in enumerate((((ox - x0, 0.3, z1 - z0), ((x0 + ox) / 2, y0, (z0 + z1) / 2)),
                                   ((x1 - ox - w, 0.3, z1 - z0), ((ox + w + x1) / 2, y0, (z0 + z1) / 2)),
                                   ((w, 0.3, oz - z0), (cx, y0, (z0 + oz) / 2)),
                                   ((w, 0.3, z1 - oz - h), (cx, y0, (oz + h + z1) / 2)))):
        box(f"{name}_front_{k}", size, c, {"default": wallm}, room)
    star = material(f"{name}_star", (0, 0, 0), emission=(0.9, 0.8, 1.0), strength=6)
    for k in range(70):
        s = rnd.uniform(0.05, 0.14)
        box(f"{name}_star_{k}", (s, s, s), (rnd.uniform(x0 + 1, x1 - 1), y1 - 0.4, rnd.uniform(z0 + 1, z1 - 1)),
            {"default": star}, room)
    cols = [(232, 64, 64), (245, 210, 50), (90, 200, 80), (60, 150, 240), (150, 90, 230)]
    debris = []
    for k in range(9):
        m = material(f"{name}_obby_{k}", srgb(rnd.choice(cols)), **PLASTIC)
        ob = box(f"{name}_obby_{k}", (rnd.uniform(0.8, 2.2), rnd.uniform(0.8, 1.6), 0.3), (0, 0, 0),
                 {"default": m}, bevel=0.04)
        debris.append((ob, (cx + rnd.uniform(-9, 9), oy + rnd.uniform(9, 24), rnd.uniform(-2, 9)),
                       [rnd.uniform(-0.3, 0.3) for _ in range(3)]))
    nx, ny, nz = null_at
    body = material(f"{name}_body", tex=tex["null"], rough=0.8, emit_tex=True, strength=0.5)
    cubes = []
    for k in range(16):
        ob = box(f"{name}_body_{k}", (0.22, 0.22, 0.22), (0, 0, 0), {"default": body})
        cubes.append((ob, rnd.uniform(1.6, 3.2), rnd.uniform(0, 2 * math.pi), rnd.uniform(0.6, 5.2),
                      rnd.uniform(0.3, 0.7) * rnd.choice((1, -1))))
    rim = bpy.data.objects.new(f"{name}_rim", bpy.data.lights.new(f"{name}_rim", "AREA"))
    bpy.context.scene.collection.objects.link(rim)
    rim.data.size = 6
    rim.data.color = (0.75, 0.3, 1.0)
    rim.data.energy = 6000
    rim.location = (nx, ny + 4, nz + 6)
    rim.rotation_euler = (math.radians(-150), 0, 0)
    fillp = bpy.data.objects.new(f"{name}_fill", bpy.data.lights.new(f"{name}_fill", "POINT"))
    bpy.context.scene.collection.objects.link(fillp)
    fillp.data.color = (1.0, 0.3, 0.85)
    fillp.data.energy = 150
    fillp.location = (cx, oy + 3, oz + h / 2)
    front = bpy.data.objects.new(f"{name}_front_light", bpy.data.lights.new(f"{name}_front_light", "POINT"))
    bpy.context.scene.collection.objects.link(front)
    front.data.color = (0.85, 0.6, 1.0)
    front.data.energy = 1800
    front.data.shadow_soft_size = 2.0
    front.location = (nx, ny - 4.5, nz + 5)
    f0, f1 = ctx.F(show[0]), ctx.F(show[1])
    for ob in [room, rim, fillp, front] + [d[0] for d in debris] + [c[0] for c in cubes]:
        show_between(ob, f0, f1)
    for f in range(f0, f1 + 1):
        t = (f - 1) / ctx.fps
        for ob, p, spin in debris:
            ob.location = (p[0] + 0.2 * t, p[1], p[2] + 0.3 * math.sin(0.7 * t + p[0]))
            ob.rotation_euler = tuple(w * t for w in spin)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)
        for ob, r, ph, z, wv in cubes:
            a = ph + wv * t
            ob.location = (nx + r * math.cos(a), ny + r * math.sin(a), nz + z + 0.2 * math.sin(2 * a))
            ob.rotation_euler = (a, 2 * a, 0)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)
