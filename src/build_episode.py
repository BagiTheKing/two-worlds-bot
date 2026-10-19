"""
Build any episode from its file and its timeline, then render.

    python src/build_episode.py episodes/ep01_the_end.json build/timeline.json \
        build/tex build/frames [--first N --last M] [--res 720] [--samples 16] \
        [--stills 10,200,400]

The episode file declares sets (locations), actors and their clips, effects
and shots; the timeline (from audio.py) says when every beat and line
happens. Frames inside "skip_render" ranges (e.g. under a full-black title
card) are not rendered; assemble.py draws those.
"""

import argparse
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import fx, worlds                                   # noqa: E402
from kit.actions import Actor, add                           # noqa: E402
from kit.cameras import shot                                 # noqa: E402
from kit.rigs import make_noob, make_null, make_steve        # noqa: E402
from kit.timeref import resolve                              # noqa: E402
import scene_poc                                             # noqa: E402

FPS = 24


class Ctx:
    def __init__(self, tl):
        self.tl = tl
        self.fps = tl["fps"]
        self.beats = tl["beats"]
        self.length = tl["length"]
        self.end = self.length + 0.4

    def F(self, t):
        return int(round(t * self.fps)) + 1

    def T(self, ref):
        return resolve(self.beats, ref, self.end)


RIGS = {"steve": make_steve, "noob": make_noob, "null": make_null}


def build(episode_path, timeline_path, tex_dir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ep = json.load(open(episode_path))
    tl = json.load(open(timeline_path))
    ctx = Ctx(tl)
    tex_dir = os.path.abspath(tex_dir)
    tex = {os.path.splitext(n)[0]: os.path.join(tex_dir, n) for n in os.listdir(tex_dir)}
    mats = worlds.block_mats(tex)

    sets = {}
    for s in ep.get("sets", []):
        if s["kind"] == "seam":
            sets["seam"] = worlds.seam(tex, mats, s.get("seed", 3))
        elif s["kind"] == "forest_valley":
            sets["forest_valley"] = worlds.forest_valley(tex_dir, tuple(s["origin"]))

    actors = {}
    for name, spec in ep.get("actors", {}).items():
        rig = RIGS[spec.get("rig", name)](tex, name=name)
        clips = [dict(c, impacts=tl.get("impacts", [])) if c["do"] in ("punch", "flurry") else c
                 for c in ep.get("clips", []) if c["who"] == name]
        actors[name] = Actor(name, rig, spec, clips, ctx.beats, ctx.end, tl["lines"], actors)

    for e in ep.get("fx", []):
        k = e["kind"]
        if k == "sky":
            keys = [(ctx.T(r), en, st, fx.POC_SUN if (len(rest) and rest[0] == "poc") else None)
                    for r, en, st, *rest in e["keys"]]
            fx.sky(ctx, tuple(e["sun_dir"]), keys)
        elif k == "clouds":
            fx.drifting_clouds(ctx, ctx.T(e["freeze"]))
        elif k == "birds":
            fx.birds(ctx, ctx.T(e["freeze"]), [tuple(p) for p in e["spots"]])
        elif k == "void_debris":
            worlds.void_debris(tex, mats, frames=ctx.F(ctx.end))
        elif k == "erasure":
            beats = e.get("beats") or [e["beat"]]
            fx.erasure(ctx, sets["seam"]["erasable"], sum((tl["fx_times"][b] for b in beats), []))
        elif k == "obby_run":
            rigs = [make_noob(tex, name=f"avatar_{i}", shirt=tuple(a["shirt"]), pants=tuple(a["pants"]))
                    for i, a in enumerate(e["avatars"])]
            fx.obby_run(ctx, sets["seam"]["obby"], rigs, ctx.T(e["from"]), ctx.T(e["to"]),
                        mats["missing"])
        elif k == "bridge":
            fx.bridge_ripple(ctx, sets["seam"]["bridge"], tl["fx_times"][e["beat"]], mats["missing"],
                             sign=sets["seam"].get("sign"))
        elif k == "backlight":
            fx.backlight(ctx, tuple(e["at"]), tuple(e["dir"]), ctx.T(e["from"]), ctx.T(e["to"]))
        elif k == "fill":
            fx.fill(ctx, tuple(e["dir"]), ctx.T(e["from"]), ctx.T(e["to"]))
        elif k == "erase_named":
            fx.erase_named(ctx, sets["seam"]["protected"] + sets["seam"]["erasable"],
                           set(e["names"]), ctx.T(e["at"]))
        elif k == "forest_portal":
            fx.forest_portal(ctx, sets["forest_valley"], ctx.T(e["open"]), ctx.T(e["land"]), mats)
        elif k in ("poc_portal", "poc_crack", "poc_tree"):
            # episode 1's hand-built effects, driven by this timeline
            poc_tl = scene_poc.TL(timeline_path)
            if k == "poc_portal":
                scene_poc.portal(poc_tl, mats)
            elif k == "poc_crack":
                scene_poc.sky_crack(poc_tl)
            else:
                scene_poc.target_block(poc_tl, bpy.data.objects["target"])
                import random as _r
                scene_poc.debris(poc_tl, mats, _r.Random(11))
        elif k == "sky_tear":
            fx.sky_tear(ctx, ctx.T(e["at"]), ctx.T(e["eye_at"]), ctx.T(e.get("end", "end")),
                        center=tuple(e.get("center", (-5.0, 40.0, 26.0))), scale=e.get("scale", 2.0))
            if e.get("tint", True):              # the tear's magenta light on the scene
                fx.fill(ctx, (0.1, -0.86, -0.5), ctx.T(e["at"]), ctx.T(e.get("end", "end")) + 1,
                        color=(1.0, 0.25, 0.85), energy=1.3)
        elif k == "orbit":
            a = actors[e["actor"]]
            off = tuple(e.get("offset", (0, 0, 0)))
            fx.orbit(ctx, lambda t: add(a.state_at(t)["loc"], off), ctx.T(e["from"]),
                     ctx.T(e["to"]), tex, mats)

    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, ctx.F(ctx.end)
    for f in range(1, sc.frame_end + 1):
        t = (f - 1) / ctx.fps
        for a in actors.values():
            a.rig.key_pose(f, a.pose(t))

    cams = [shot(ctx, s, actors, i) for i, s in enumerate(ep["shots"])]
    sc.camera = cams[0]
    skip = [(ctx.F(ctx.T(a)), ctx.F(ctx.T(b))) for a, b in ep.get("skip_render", [])]
    return ctx, skip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("timeline")
    ap.add_argument("tex_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--first", type=int)
    ap.add_argument("--last", type=int)
    ap.add_argument("--res", type=int, default=720)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--stills")
    ap.add_argument("--save-blend")
    ap.add_argument("--shots", help="comma-separated shot names: render only their frames "
                                    "(the rest are reused from an earlier render)")
    a = ap.parse_args()

    ctx, skip = build(a.episode, a.timeline, a.tex_dir)
    scene_poc.setup_render(a.res, a.samples)
    sc = bpy.context.scene
    sc.render.film_transparent = False
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    if a.stills:
        for f in (int(x) for x in a.stills.split(",")):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(out, f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    first, last = a.first or 1, a.last or sc.frame_end
    frames = [f for f in range(first, last + 1) if not any(s0 <= f < s1 for s0, s1 in skip)]
    if a.shots:
        wanted = set(a.shots.split(","))
        spans = [(ctx.F(ctx.T(s["from"])), ctx.F(ctx.T(s["to"])))
                 for s in json.load(open(a.episode))["shots"] if s.get("name") in wanted]
        missing = wanted - {s.get("name") for s in json.load(open(a.episode))["shots"]}
        if missing:
            raise SystemExit(f"unknown shot names: {sorted(missing)}")
        frames = [f for f in frames if any(s0 - 1 <= f <= s1 + 1 for s0, s1 in spans)]
        print("re-rendering", len(frames), "frames of shots", sorted(wanted))
    # render contiguous runs so persistent data is reused within each
    runs, start = [], None
    for f in frames:
        if start is None:
            start = prev = f
        elif f != prev + 1:
            runs.append((start, prev))
            start = f
        prev = f
    if start is not None:
        runs.append((start, prev))
    sc.render.filepath = os.path.join(out, "")
    for s0, s1 in runs:
        sc.frame_start, sc.frame_end = s0, s1
        bpy.ops.render.render(animation=True)
    print("rendered", runs)


if __name__ == "__main__":
    main()
