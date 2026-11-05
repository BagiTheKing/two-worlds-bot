"""
Pieces for gags in the block world, made to the quality bar of the
reference animations (see story/playbook.md, "The quality bar"):

    punch_block   a log that cracks under punches, bursts into debris and
                  drops a small spinning item that flies into the hand
    falling_tree  a tree that creaks, then topples (accelerating, a bounce)
                  and throws up a burst of leaves and dust where it lands
    motes         warm specks floating in the air, catching the sun
    haze          layers of soft, see-through air between the near and the far
"""

import math
import random

import bpy

from kit.actions import ss
from kit.blocks import box, empty, material, show_between
from kit.props import _ballistic, _key_scale
from kit.rigs import srgb
from scene_poc import tree_cells


def _log_mats(tex, name):
    side = material(f"{name}_log_side", tex=tex["log_side"])
    top = material(f"{name}_log_top", tex=tex["log_top"])
    leaves = material(f"{name}_leaves", tex=tex["leaves"])
    return side, top, leaves


def _camera_only(ob):
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission",
                 "visible_volume_scatter", "visible_shadow"):
        if hasattr(ob, attr):
            setattr(ob, attr, False)


def _key_hide(ob, keys):
    for f, h in keys:
        ob.hide_render = h
        ob.keyframe_insert("hide_render", frame=max(1, f))


def punch_block(ctx, tex, at, hits, item_to, item_at, name="punched"):
    """A log block centred at `at`. Each time in `hits` it shows a further
    crack stage; on the last it bursts: debris flies and a small copy of the
    block pops out, bobs and spins (as dropped items do), then flies to
    `item_to` at `item_at` and is gone (picked up)."""
    side, top, _ = _log_mats(tex, name)
    blk = box(f"{name}_block", (1, 1, 1), tuple(at), {"top": top, "bottom": top, "default": side})
    t_break = hits[-1]
    _key_hide(blk, [(1, False), (ctx.F(t_break), True)])
    for k in range(1, 4):                           # the crack stages, one per hit before the last
        if k > len(hits) - 1:
            break
        m = material(f"{name}_crack_{k}", tex=tex[f"crack_{k}"], alpha_tex=True)
        cr = box(f"{name}_crack_{k}", (1.012, 1.012, 1.012), tuple(at), {"default": m})
        end = hits[k] if k < len(hits) - 1 else t_break
        _key_hide(cr, [(1, True), (ctx.F(hits[k - 1]), False), (ctx.F(end), True)])
    rnd = random.Random(5)
    for i in range(14):                             # debris
        s = rnd.uniform(0.08, 0.16)
        d = box(f"{name}_debris_{i}", (s, s, s), (0, 0, 0), {"default": side})
        v = (rnd.uniform(-2.2, 2.2), rnd.uniform(-2.6, -0.6), rnd.uniform(1.0, 3.4))
        _ballistic(d, ctx, tuple(at), v, t_break, t_break + 0.9, ground=0.0, half=s / 2,
                   spin=(rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9)))
        _key_scale(d, ctx, ((t_break - 0.05, 1.0), (t_break + 0.45, 1.0), (t_break + 0.85, 0.001)))
        show_between(d, ctx.F(t_break), ctx.F(t_break + 0.9))
    item = empty(f"{name}_item", tuple(at))
    box(f"{name}_item_box", (0.26, 0.26, 0.26), (0, 0, 0), {"top": top, "bottom": top, "default": side}, item)
    ix, iy, iz = at
    for f in range(ctx.F(t_break), ctx.F(item_at) + 2):
        t = (f - 1) / ctx.fps
        u = t - t_break
        k = ss(item_at - 0.25, item_at, t)
        rest = (ix, iy - 0.25, 0.35 + 0.08 * math.sin(4.5 * u) + 0.9 * max(0.0, 0.25 - u) * 3)
        item.location = tuple(rest[j] + (item_to[j] - rest[j]) * k for j in range(3))
        item.rotation_euler = (0, 0, 3.0 * u)
        s = max(0.001, min(1.0, u / 0.12) * (1 - k))
        item.scale = (s, s, s)
        for path in ("location", "rotation_euler", "scale"):
            item.keyframe_insert(path, frame=f)
    show_between(item, ctx.F(t_break), ctx.F(item_at) + 1)
    return blk


def tree(ctx, tex, x, y, height=5, gap=None, seed=42, name="tree"):
    """A forest tree as one object per block, under a pivot at its base;
    gap: the trunk level left empty (a punched-out block, the rest floats)."""
    side, top, leaves = _log_mats(tex, name)
    pivot = empty(f"{name}_pivot", (x, y, 0))
    cells = tree_cells(0, 0, 0, height, random.Random(seed))
    for i, ((cx, cy, cz), kind) in enumerate(sorted(cells.items())):
        if kind == "log" and cz == gap:
            continue
        mats = {"top": top, "bottom": top, "default": side} if kind == "log" else {"default": leaves}
        box(f"{name}_{i}", (1, 1, 1), (cx, cy, cz + 0.5), mats, pivot)
    return pivot


def falling_tree(ctx, tex, x, y, yaw, t_creak, t_fall, t_hit, height=5, seed=7, name="falling_tree"):
    """A tree that creaks (small shivers), then topples toward `yaw` (the way
    a character facing -y at yaw 0 would face): slow at first, then fast,
    a small bounce on landing and a burst of leaves and dust."""
    pivot = tree(ctx, tex, 0, 0, height, seed=seed, name=name)
    hinge = empty(f"{name}_hinge", (x, y, 0))
    pivot.parent = hinge
    pivot.location = (0, 0.5, 0)              # it tips over its front edge
    for f in range(1, ctx.F(t_hit + 1.0) + 1):
        t = (f - 1) / ctx.fps
        if t < t_creak:
            a = 0.0
        elif t < t_fall:                          # creak: little shivers, growing
            a = 0.018 * ss(t_creak, t_fall, t) * math.sin(38 * (t - t_creak))
        elif t < t_hit:
            u = (t - t_fall) / (t_hit - t_fall)
            a = (math.pi / 2) * u ** 2.3
        else:                                     # landed: a small bounce
            u = t - t_hit
            a = math.pi / 2 - 0.09 * math.exp(-u * 9) * abs(math.sin(u * 16))
        hinge.rotation_euler = (a, 0, yaw)
        hinge.keyframe_insert("rotation_euler", frame=f)
    rnd = random.Random(9)
    dust = material(f"{name}_dust", srgb((214, 196, 160)), rough=1.0)
    _, _, leaves = _log_mats(tex, name + "_burst")
    for i in range(30):                           # where it lands: leaves and dust
        d = rnd.uniform(1.0, height + 1.5)
        px, py = x + d * math.sin(yaw), y - d * math.cos(yaw)      # along the way it falls
        s = rnd.uniform(0.12, 0.3)
        ob = box(f"{name}_puff_{i}", (s, s, s), (0, 0, 0), {"default": dust if i % 2 else leaves})
        v = (rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5), rnd.uniform(1.5, 4.0))
        _ballistic(ob, ctx, (px, py, 0.4), v, t_hit, t_hit + 1.1, ground=0.0, half=s / 2,
                   spin=(rnd.uniform(-6, 6), rnd.uniform(-6, 6), 0))
        _key_scale(ob, ctx, ((t_hit, 1.0), (t_hit + 0.5, 1.0), (t_hit + 1.05, 0.001)))
        show_between(ob, ctx.F(t_hit), ctx.F(t_hit + 1.1))
    return hinge


def motes(ctx, center, size, n=70, seed=3, name="motes"):
    """Warm specks floating in the light (pollen, dust): they drift slowly
    and catch the sun. Seen by the camera only."""
    rnd = random.Random(seed)
    m = material(name, (0, 0, 0), emission=(1.0, 0.86, 0.55), strength=6.0)
    cx, cy, cz = center
    sx, sy, sz = size
    for i in range(n):
        s = rnd.uniform(0.018, 0.04)
        ob = box(f"{name}_{i}", (s, s, s), (0, 0, 0), {"default": m})
        _camera_only(ob)
        p0 = (cx + rnd.uniform(-sx, sx) / 2, cy + rnd.uniform(-sy, sy) / 2, cz + rnd.uniform(0, sz))
        w = [rnd.uniform(0.15, 0.4) for _ in range(3)]
        ph = [rnd.uniform(0, 6.3) for _ in range(3)]
        drift = rnd.uniform(0.05, 0.12)
        for f in range(1, ctx.F(ctx.end) + 2, 3):
            t = (f - 1) / ctx.fps
            ob.location = (p0[0] + 0.35 * math.sin(w[0] * t + ph[0]) + drift * t,
                           p0[1] + 0.35 * math.sin(w[1] * t + ph[1]),
                           p0[2] + 0.25 * math.sin(w[2] * t + ph[2]))
            ob.keyframe_insert("location", frame=f)


def haze(ctx, layers, x0, x1, z0, z1, color=(0.78, 0.86, 1.0), name="haze"):
    """Soft air: see-through glowing sheets facing the camera side (-y) at
    the given [(y, opacity), ...], so the far trees fade into light."""
    for i, (y, alpha) in enumerate(layers):
        m = bpy.data.materials.new(f"{name}_{i}")
        m.use_nodes = True
        nt = m.node_tree
        for n_ in list(nt.nodes):
            nt.nodes.remove(n_)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*color, 1)
        em.inputs["Strength"].default_value = 1.4
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = alpha
        nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        ob = box(f"{name}_{i}", (x1 - x0, 0.01, z1 - z0), ((x0 + x1) / 2, y, (z0 + z1) / 2), {"default": m})
        _camera_only(ob)
