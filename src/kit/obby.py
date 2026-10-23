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


def flicker(ctx, rig, mat, t0, t1, seed=8, rate=0.45):
    """The actor glitches: on random frames between t0 and t1 every part of
    it is drawn in `mat` (the magenta/black missing texture)."""
    from kit.worlds import flash_copy
    rnd = random.Random(seed)
    frames = [f for f in range(ctx.F(t0), ctx.F(t1)) if rnd.random() < rate]
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
