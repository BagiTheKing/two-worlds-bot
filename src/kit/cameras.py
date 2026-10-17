"""
Shots. An episode lists them in order; each becomes a camera keyed only over
its own time range, with a timeline marker that cuts to it.

    {"name": "wide", "from": "erasure", "to": "erasure+3.2", "lens": 18,
     "path": [["erasure", [x, y, z]], ["erasure+3.2", [x, y, z]]],
     "look": [["erasure", [x, y, z]]],         # or "look_actor": "noob"
     "look_offset": [0, 0, 1.3], "dof": 4.0, "shake": 0.012}

Paths ease between keys. A small handheld drift is added unless shake is 0.
"""

import math

import bpy

from kit.actions import add, lerp, ss
from kit.blocks import empty
from kit.timeref import resolve


def _keys(spec, beats, length):
    return [(resolve(beats, r, length), tuple(p)) for r, p in spec]


def _at(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, a), (tb, b) in zip(keys, keys[1:]):
        if t <= tb:
            return lerp(a, b, ss(ta, tb, t))
    return keys[-1][1]


def shot(ctx, spec, actors, index):
    beats, length = ctx.beats, ctx.end
    t0 = resolve(beats, spec["from"], length)
    t1 = resolve(beats, spec["to"], length)
    name = spec.get("name", f"shot{index}")
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = spec.get("lens", 24)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36
    cam.data.clip_end = 600
    tgt = empty(name + "_aim")
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    if spec.get("dof"):
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = tgt
        cam.data.dof.aperture_fstop = spec["dof"]

    origin = tuple(spec.get("origin", (0, 0, 0)))
    path = _keys(spec["path"], beats, length)
    look = _keys(spec["look"], beats, length) if "look" in spec else None
    follow = actors.get(spec.get("look_actor")) if spec.get("look_actor") else None
    off = tuple(spec.get("look_offset", (0, 0, 1.2)))
    shake = spec.get("shake", 0.012)
    seed = index * 1.7
    for f in range(ctx.F(t0) - 1, ctx.F(t1) + 2):
        t = (f - 1) / ctx.fps
        p = add(_at(path, t), origin)
        n = (shake * math.sin(2 * math.pi * 0.7 * t + seed),
             shake * math.sin(2 * math.pi * 0.53 * t + 2 + seed),
             shake * math.sin(2 * math.pi * 0.61 * t + 4 + seed))
        cam.location = add(p, n)
        cam.keyframe_insert("location", frame=f)
        if follow is not None:
            aim_at = add(follow.state_at(t)["loc"], off)
            if look:
                aim_at = lerp(aim_at, add(_at(look, t), origin), spec.get("look_mix", 0.5))
        else:
            aim_at = add(_at(look, t), origin)
        tgt.location = aim_at
        tgt.keyframe_insert("location", frame=f)
    m = bpy.context.scene.timeline_markers.new(name, frame=ctx.F(t0))
    m.camera = cam
    return cam
