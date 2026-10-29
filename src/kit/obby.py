"""
Episode 3's obby (the Noob's world, mid-air) and what happens to it:

  course        plastic platforms over the void, from a list: bright colours,
                kill bricks (neon red), platforms that slide back and forth
  flag          a checkpoint flag on its pole
  smash_near    platforms (or anything named) that shatter into flying
                pieces at the moment an actor (the dragon) passes through
  wall          Steve's wall: blocks pop in one by one, then burst apart
  cages         the frozen avatars' glitch cubes, which shatter on a moment
  flicker       an actor flashing to the missing-texture look (a glitch)

Everything is keyed from the timeline, like the rest of the kit.
"""

import math
import random

import bpy

from kit.actions import add, ss
from kit.blocks import box, empty, material, show_between
from kit.props import PLASTIC, _ballistic, _key_scale
from kit.rigs import srgb
from kit.timeref import spread

COLOURS = {"red": (232, 64, 64), "orange": (245, 150, 40), "yellow": (245, 210, 50),
           "green": (90, 200, 80), "blue": (60, 150, 240), "purple": (150, 90, 230),
           "pink": (240, 100, 190), "white": (236, 236, 240), "grey": (150, 155, 165)}


def _pieces(ctx, name, centre, size, mat, t, push, n=8, seed=1, life=1.6):
    """A block breaking: n chunks of it fly off along `push` and fall."""
    rnd = random.Random(seed)
    sx, sy, sz = size
    for k in range(n):
        s = (sx * rnd.uniform(0.2, 0.4), sy * rnd.uniform(0.2, 0.4), max(sz, 0.2) * rnd.uniform(0.5, 1.0))
        ob = box(f"{name}_piece_{k}", s, (0, 0, 0), {"default": mat}, bevel=0.02)
        p0 = (centre[0] + rnd.uniform(-sx, sx) * 0.35, centre[1] + rnd.uniform(-sy, sy) * 0.35,
              centre[2] + rnd.uniform(-0.2, 0.2))
        v = (push[0] * rnd.uniform(0.5, 1.2) + rnd.uniform(-2.5, 2.5),
             push[1] * rnd.uniform(0.5, 1.2) + rnd.uniform(-2.5, 2.5),
             push[2] * rnd.uniform(0.5, 1.2) + rnd.uniform(1.0, 4.0))
        show_between(ob, ctx.F(t), ctx.F(t + life))
        _ballistic(ob, ctx, p0, v, t, t + life, ground=-60, half=0.1,
                   spin=[rnd.uniform(-10, 10) for _ in range(3)])


def course(ctx, platforms):
    """platforms: [{"name", "at": [x, y, top_z], "size": [w, d] or [w, d, h],
    "colour": name or [r, g, b], "kill": bool, "slide": [dx, dy, dz, seconds]}]
    Returns {name: {"ob", "centre", "size", "mat"}}."""
    out = {}
    neon = material("obby_kill", srgb((255, 40, 40)), rough=0.25, spec=0.6, coat=0.4,
                    emission=srgb((255, 30, 30)), strength=1.6)
    for i, p in enumerate(platforms):
        name = p.get("name", f"plat_{i}")
        w, d = p["size"][:2]
        h = p["size"][2] if len(p["size"]) > 2 else 0.6
        col = p.get("colour", "blue")
        col = COLOURS[col] if isinstance(col, str) else tuple(col)
        mat = neon if p.get("kill") else material(f"obby_{name}", srgb(col), **PLASTIC)
        x, y, z = p["at"]
        ob = box(f"obby_{name}", (w, d, h), (0, 0, -h / 2), {"default": mat}, bevel=0.08)
        ob.location = (x, y, z)
        if p.get("slide"):
            dx, dy, dz, period = p["slide"]
            for f in range(1, ctx.F(ctx.end) + 1, 2):
                k = math.sin(2 * math.pi * (f - 1) / ctx.fps / period)
                ob.location = (x + dx * k, y + dy * k, z + dz * k)
                ob.keyframe_insert("location", frame=f)
        out[name] = {"ob": ob, "centre": (x, y, z - h / 2), "size": (w, d, h), "mat": mat}
    return out


def flag(ctx, at, colour="green", name="checkpoint"):
    """A checkpoint flag: white pole, a flag that ripples a little."""
    x, y, z = at
    white = material(f"{name}_pole", srgb((240, 240, 240)), **PLASTIC)
    cloth = material(f"{name}_flag", srgb(COLOURS[colour]), **PLASTIC)
    box(f"{name}_pole", (0.14, 0.14, 2.6), (x, y, z + 1.3), {"default": white}, bevel=0.03)
    hinge = empty(f"{name}_hinge", (x + 0.07, y, z + 2.25))
    box(f"{name}_cloth", (0.9, 0.06, 0.6), (0.45, 0, 0), {"default": cloth}, hinge, bevel=0.02)
    for f in range(1, ctx.F(ctx.end) + 1, 3):
        hinge.rotation_euler = (0, 0, 0.18 * math.sin(f * 0.35))
        hinge.keyframe_insert("rotation_euler", frame=f)


def smash_near(ctx, actor, targets, items, radius=3.5, early=0.0, push=6.0):
    """Each target shatters the first time `actor` comes within `radius` of
    it (or at its own "at" time, which may be before the episode starts, so
    the first frame already has pieces in the air)."""
    for tgt in targets:
        name = tgt["name"] if isinstance(tgt, dict) else tgt
        it = items[name]
        c = it["centre"]
        t_hit = tgt.get("at") if isinstance(tgt, dict) else None
        if t_hit is None:
            t_hit = next((t / ctx.fps for t in range(0, int(ctx.end * ctx.fps))
                          if math.dist(actor.state_at(t / ctx.fps)["loc"], c) < radius), None)
            if t_hit is None:
                print(f"smash_near: {actor.name} never reaches {name}")
                continue
            t_hit -= early
        # pieces fly the way the actor was going
        a, b = actor.state_at(t_hit - 0.05)["loc"], actor.state_at(t_hit + 0.05)["loc"]
        d = [b[i] - a[i] for i in range(3)]
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        v = (d[0] / n * push, d[1] / n * push, d[2] / n * push)
        ob = it["ob"]
        f = ctx.F(t_hit)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=1)
        if f > 1:
            ob.keyframe_insert("hide_render", frame=f - 1)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=max(1, f))
        _pieces(ctx, f"smash_{name}", c, it["size"], it["mat"], t_hit, v, n=10, seed=hash(name) % 97)


def wall(ctx, tex, origin, cols, rows, build, smash_at, push=(0, -7, 2), name="wall"):
    """Steve's wall, cols x rows of 1 m blocks centred on origin (x, y, z of
    its bottom middle), built one block at a time over build=(t0, t1), then
    burst apart at smash_at."""
    m = material(f"{name}_stone", tex=tex["stone"])
    x0, y0, z0 = origin
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    times = spread(build[0], build[1], len(cells))
    rnd = random.Random(7)
    for (c, r), t in zip(cells, times):
        cx, cz = x0 + c - (cols - 1) / 2, z0 + r + 0.5
        ob = box(f"{name}_{c}_{r}", (1, 1, 1), (0, 0, 0), {"default": m})
        ob.location = (cx, y0, cz)
        _key_scale(ob, ctx, ((0, 0.001), (t, 0.001), (t + 0.06, 1.12), (t + 0.12, 1.0)))
        f = ctx.F(smash_at)
        ob.keyframe_insert("location", frame=f)
        v = (push[0] + (cx - x0) * 2.5 + rnd.uniform(-1, 1), push[1] * rnd.uniform(0.7, 1.3),
             push[2] + r * 1.2 + rnd.uniform(0, 2))
        _ballistic(ob, ctx, (cx, y0, cz), v, smash_at, smash_at + 1.4, ground=-60, half=0.5,
                   spin=[rnd.uniform(-7, 7) for _ in range(3)])
        show_between(ob, ctx.F(t), ctx.F(smash_at + 1.4))


def cages(ctx, spots, free_at, name="cage"):
    """A glitch cube around each frozen avatar: see-through, with magenta
    and cyan edges that shimmer. At free_at they shatter."""
    glass = material(f"{name}_glass", (0.6, 0.2, 0.9), rough=0.1)
    bsdf = glass.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Alpha"].default_value = 0.22
    bsdf.inputs["Emission Color"].default_value = (0.7, 0.1, 1.0, 1)
    bsdf.inputs["Emission Strength"].default_value = 0.5
    if hasattr(glass, "surface_render_method"):
        glass.surface_render_method = "BLENDED"
    edges = [material(f"{name}_edge_{k}", (0, 0, 0), emission=c, strength=5)
             for k, c in enumerate(((1.0, 0.1, 0.8), (0.1, 0.9, 1.0)))]
    for i, (x, y, z) in enumerate(spots):
        g = empty(f"{name}_{i}", (x, y, z + 1.15))
        box(f"{name}_{i}_box", (1.5, 1.2, 2.3), (0, 0, 0), {"default": glass}, g)
        for k, (ex, ey) in enumerate(((-0.75, -0.6), (0.75, -0.6), (-0.75, 0.6), (0.75, 0.6))):
            box(f"{name}_{i}_edge_{k}", (0.07, 0.07, 2.3), (ex, ey, 0), {"default": edges[k % 2]}, g)
        for k, ez in enumerate((-1.15, 1.15)):
            for j, ey in enumerate((-0.6, 0.6)):
                box(f"{name}_{i}_rim_{k}_{j}", (1.5, 0.07, 0.07), (0, ey, ez), {"default": edges[(k + j) % 2]}, g)
        # a shimmer: the cube jitters a hair now and then
        rnd = random.Random(30 + i)
        for f in range(1, ctx.F(free_at) + 1, 2):
            jit = 0.03 if rnd.random() < 0.15 else 0.0
            g.location = (x + rnd.uniform(-jit, jit), y, z + 1.15)
            g.keyframe_insert("location", frame=f)
        f = ctx.F(free_at)
        for ob in [g] + list(g.children_recursive):
            for fr, hid in ((1, False), (f - 1, False), (f, True)):
                ob.hide_render = hid
                ob.keyframe_insert("hide_render", frame=max(1, fr))
        _pieces(ctx, f"{name}_{i}", (x, y, z + 1.15), (1.5, 1.2, 2.3), edges[i % 2], free_at,
                (0, -2.5, 2.0), n=10, seed=50 + i, life=1.2)


def flicker(ctx, rig, mat, t0, t1, seed=8, rate=0.45, skip=()):
    """The actor glitches: on random frames between t0 and t1 every part of
    it is drawn in `mat` (the magenta/black missing texture). No glitch
    inside the `skip` time ranges (shots where the actor is hidden)."""
    from kit.worlds import flash_copy
    rnd = random.Random(seed)
    frames = [f for f in range(ctx.F(t0), ctx.F(t1)) if rnd.random() < rate]
    frames = [f for f in frames if not any(ctx.F(a) - 1 <= f <= ctx.F(b) for a, b in skip)]
    for ob in [rig.root] + list(rig.root.children_recursive):
        if ob.type != "MESH":
            continue
        twin = flash_copy(ob, mat)
        twin.parent = ob.parent
        twin.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
        if ob.animation_data and ob.animation_data.action:
            twin.animation_data_create()
            twin.animation_data.action = ob.animation_data.action
        for o, base in ((twin, True), (ob, False)):
            o.hide_render = base
            o.keyframe_insert("hide_render", frame=1)
        for f in frames:
            for o, on in ((twin, False), (ob, True)):        # twin shown, original hidden
                o.hide_render = on
                o.keyframe_insert("hide_render", frame=f)
                o.hide_render = not on
                o.keyframe_insert("hide_render", frame=f + 1)


def glitch_block(ctx, tex, at, size, pulses, grow=0.25, kick=0.35, drop=None, name="odd_block"):
    """The block that shouldn't exist (episode 4): a hovering cube in the
    missing texture that turns slowly, jitters now and then, and on each
    pulse (a Noob respawn) flashes, swells and stays a little bigger.
    drop=(p0, t0, t1): it first falls from p0 (t0) and lands at t1."""
    kick_amp = kick
    m = material(name, tex=tex["missing"], emit_tex=True, strength=1.2)
    em = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    ob = box(name, (size, size, size), (0, 0, 0), {"default": m})
    rnd = random.Random(17)
    pulses = sorted(pulses)
    for f in range(1, ctx.F(ctx.end) + 1):
        t = (f - 1) / ctx.fps
        done = sum(1 for p in pulses if p <= t)
        base = 1.0 + grow * done
        kick = max((math.exp(-(t - p) * 7) * math.sin(min(math.pi, (t - p) * 14)) for p in pulses if p <= t),
                   default=0.0)
        s = base + kick_amp * kick
        jit = 0.04 if rnd.random() < 0.06 else 0.0
        ob.location = (at[0] + rnd.uniform(-jit, jit), at[1], at[2] + 0.08 * math.sin(2 * math.pi * 0.5 * t))
        if drop and t < drop[2]:                # still falling: from p0 at t0, landing at t1, speeding up
            p0, t0, t1 = drop
            u = max(0.0, min(1.0, (t - t0) / (t1 - t0))) ** 2
            ob.location = tuple(p0[i] + (at[i] - p0[i]) * u for i in range(3))
        ob.rotation_euler = (0.25 * t, 0.4 * t, 0.15 * t)
        ob.scale = (s, s, s)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
        ob.keyframe_insert("scale", frame=f)
        em.default_value = 1.2 + 6.0 * max(0.0, kick)
        em.keyframe_insert("default_value", frame=f)
    return ob


# ------------------------------------------------- episode 5: build tools

# the Noob's creations, as boxes: (size, centre, colour) relative to the
# creation's base point, listed in the order they appear
DUCK = [((2.4, 3.0, 1.6), (0, 0.2, 0.8), "yellow"), ((2.0, 2.4, 0.5), (0, 0.4, 1.75), "yellow"),
        ((1.4, 1.4, 1.4), (0, -1.0, 2.4), "yellow"), ((0.9, 0.7, 0.35), (0, -2.0, 2.2), "orange"),
        ((0.22, 0.05, 0.28), (-0.4, -1.72, 2.65), "black"), ((0.22, 0.05, 0.28), (0.4, -1.72, 2.65), "black"),
        ((0.5, 0.8, 0.5), (0, 1.9, 1.5), "yellow")]
CASTLE = [((4.0, 3.0, 1.2), (0, 0, 0.6), "pink"), ((3.2, 2.4, 1.0), (0, 0, 1.7), "blue"),
          ((1.0, 1.0, 2.6), (-1.6, -1.1, 1.3), "yellow"), ((1.0, 1.0, 2.6), (1.6, -1.1, 1.3), "yellow"),
          ((1.0, 1.0, 2.6), (-1.6, 1.1, 1.3), "green"), ((1.0, 1.0, 2.6), (1.6, 1.1, 1.3), "green"),
          ((1.2, 0.2, 1.0), (0, -1.55, 0.5), "red"),
          ((0.6, 0.6, 0.6), (-1.6, -1.1, 2.9), "red"), ((0.6, 0.6, 0.6), (1.6, -1.1, 2.9), "red")]
PIZZA = [((2.4, 2.4, 0.3), (0, 0, 0.15 + 0.42 * k), "orange" if k % 2 == 0 else "yellow") for k in range(9)] + \
        [((0.35, 0.35, 0.06), (x, y, 0.33 + 0.42 * k), "red")
         for k in range(0, 9, 2) for x, y in ((-0.6, -0.5), (0.5, 0.3), (-0.2, 0.6))]
DOOR = [((0.25, 0.3, 2.6), (-0.65, 0, 1.3), "white"), ((0.25, 0.3, 2.6), (0.65, 0, 1.3), "white"),
        ((1.55, 0.3, 0.25), (0, 0, 2.72), "white")]
SHAPES = {"duck": DUCK, "castle": CASTLE, "pizza": PIZZA, "door": DOOR}
EXTRA = {"black": (24, 24, 30)}


def selection(ctx, name, lo, hi, t0, t1):
    """The build tools' selection box: thin glowing blue edges around a
    creation while it is being built."""
    glow = material(f"{name}_sel", (0, 0, 0), emission=(0.2, 0.6, 1.0), strength=6)
    g = empty(f"{name}_sel", (0, 0, 0))
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    w, d, h, e = x1 - x0, y1 - y0, z1 - z0, 0.05
    for x in (x0, x1):
        for y in (y0, y1):
            box(f"{name}_sel_z_{x}_{y}", (e, e, h), (x, y, cz), {"default": glow}, g)
        for z in (z0, z1):
            box(f"{name}_sel_y_{x}_{z}", (e, d, e), (x, cy, z), {"default": glow}, g)
    for y in (y0, y1):
        for z in (z0, z1):
            box(f"{name}_sel_x_{y}_{z}", (w, e, e), (cx, y, z), {"default": glow}, g)
    show_between(g, ctx.F(t0), ctx.F(t1))
    return g


def construct(ctx, name, shape, at, build, scale=1.0, yaw=0.0):
    """A creation built block by block over build=(t0, t1): each part pops in
    (overshoot, settle) while the selection box glows around it. Returns its
    objects, for vanish()."""
    root = empty(f"{name}_root", tuple(at))
    root.rotation_euler = (0, 0, yaw)
    root.scale = (scale, scale, scale)
    parts = SHAPES[shape]
    times = spread(build[0], build[1], len(parts))
    obs = []
    for i, ((size, centre, col), t) in enumerate(zip(parts, times)):
        rgb = EXTRA.get(col) or COLOURS[col]
        m = material(f"{name}_{i}", srgb(rgb), **PLASTIC)
        ob = box(f"{name}_{i}", size, centre, {"default": m}, root, bevel=0.05)
        ob.scale = (0.001,) * 3
        _key_scale(ob, ctx, ((build[0] - 1, 0.001), (t, 0.001), (t + 0.08, 1.15), (t + 0.16, 1.0)))
        obs.append(ob)
    # selection box around the whole thing, in world space
    xs = [c[0] for _, c, _ in parts]
    pts = [(c[0] + sx * s[0] / 2, c[1] + sy * s[1] / 2, c[2] + sz * s[2] / 2)
           for s, c, _ in parts for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    c, s_ = math.cos(yaw), math.sin(yaw)    # rotated: the box around the rotated corners
    pts = [(p[0] * c - p[1] * s_, p[0] * s_ + p[1] * c, p[2]) for p in pts]
    lo = tuple(at[i] + min(p[i] for p in pts) * scale - 0.1 for i in range(3))
    hi = tuple(at[i] + max(p[i] for p in pts) * scale + 0.1 for i in range(3))
    del xs
    selection(ctx, name, lo, hi, build[0], build[1] + 0.35)
    return obs + [root]


def door_swing(ctx, obs, at, t, name="door"):
    """The door in the frame swings open on its hinge at t."""
    m = material(f"{name}_leaf", srgb((150, 96, 60)), **PLASTIC)
    hinge = empty(f"{name}_hinge", (at[0] - 0.52, at[1], at[2]))
    box(f"{name}_leaf", (1.04, 0.12, 2.42), (0.52, 0, 1.21), {"default": m}, hinge, bevel=0.03)
    box(f"{name}_knob", (0.1, 0.12, 0.1), (0.9, -0.1, 1.2), {"default": material(f"{name}_knob", srgb((240, 200, 60)))}, hinge)
    _key_scale(hinge, ctx, ((0, 0.001), (t - 0.6, 0.001), (t - 0.5, 1.0)))
    for tt, a in ((t - 0.01, 0.0), (t + 0.35, -1.9), (t + 0.6, -1.75)):
        hinge.rotation_euler = (0, 0, a)
        hinge.keyframe_insert("rotation_euler", frame=ctx.F(tt))
    return [hinge] + list(hinge.children)


def own_flash_keys(twin):
    """A copied object shares its original's animation: the flash's own
    show/hide keys would land on the original too (and its show keys on the
    twin). Give the twin a copy without the visibility channel."""
    ad = twin.animation_data
    if not ad or not ad.action:
        return
    act = ad.action.copy()
    slot = ad.action_slot
    ad.action = act
    if slot is not None and slot.handle in [s.handle for s in act.slots]:
        ad.action_slot = next(s for s in act.slots if s.handle == slot.handle)
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in [fc for fc in cb.fcurves if fc.data_path == "hide_render"]:
                    cb.fcurves.remove(fc)


def vanish(ctx, obs, t, mat, flash=0.09):
    """Deleted: everything in obs (meshes, or roots whose meshes go too)
    flashes to the missing texture for a moment, then is gone."""
    from kit.worlds import flash_copy
    meshes = []
    for ob in obs:
        for o in [ob] + list(ob.children_recursive):
            if o.type == "MESH" and o not in meshes and not o.get("is_flash") and not o.get("face_plate"):
                meshes.append(o)
    f0, f1 = ctx.F(t), ctx.F(t + flash)
    for o in meshes:
        twin = flash_copy(o, mat)            # shares the mesh, drawn in the missing texture
        own_flash_keys(twin)
        for fr, hid in ((1, True), (f0, False), (f1, True)):
            twin.hide_render = hid
            twin.keyframe_insert("hide_render", frame=max(1, fr))
        for fr, hid in ((max(1, f0 - 1), False), (f0, True)):
            o.hide_render = hid
            o.keyframe_insert("hide_render", frame=fr)


def wand(ctx, rig, name="wand", arm="arm_r"):
    """The build wand in the Noob's hand: a short handle with a glowing blue
    tip, pointing the way his arm points."""
    hand = rig.parts[arm]
    s = 1.0
    grip = empty(f"{name}_grip", (0, -0.12, -0.78 * s), hand)
    grip.rotation_euler = (1.4, 0, 0)
    stick = material(f"{name}_stick", srgb((60, 64, 80)), rough=0.4, spec=0.5)
    tip = material(f"{name}_tip", (0, 0, 0), emission=(0.2, 0.6, 1.0), strength=7)
    box(f"{name}_handle", (0.08, 0.08, 0.5), (0, 0, 0.12), {"default": stick}, grip, bevel=0.02)
    box(f"{name}_tip", (0.16, 0.16, 0.16), (0, 0, 0.42), {"default": tip}, grip, bevel=0.03)
    return grip
