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
from kit import fx, props, worlds                            # noqa: E402
from kit.actions import Actor, add                           # noqa: E402
from kit.cameras import shot                                 # noqa: E402
from kit.rigs import make_dragon, make_noob, make_null, make_steve, make_zombie  # noqa: E402
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


RIGS = {"steve": make_steve, "noob": make_noob, "null": make_null, "zombie": make_zombie,
        "dragon": make_dragon}


def snap_jumps(ob, threshold=0.4):
    """Instant moves (a cut, a respawn) jump instead of sliding: otherwise
    motion blur smears the character along the path between the two spots."""
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    a = ad.action
    cb = a.layers[0].strips[0].channelbag(ad.action_slot or a.slots[0])
    for fc in cb.fcurves:
        if fc.data_path != "location":
            continue
        pts = fc.keyframe_points
        jumps = [(pts[i + 1].co[0], pts[i + 1].co[1]) for i in range(len(pts) - 1)
                 if abs(pts[i + 1].co[1] - pts[i].co[1]) > threshold]
        for f, v in jumps:
            # jump 0.3 frame early, so the shutter (open around each frame)
            # never catches both places
            k = fc.keyframe_points.insert(f - 0.3, v, options={"FAST"})
            k.interpolation = "LINEAR"
        fc.update()
        for i in range(len(pts) - 1):
            if abs(pts[i + 1].co[1] - pts[i].co[1]) > threshold:
                pts[i].interpolation = "CONSTANT"


def visible(ctx, rig, ranges):
    """Show an actor only inside the given [from, to] time ranges."""
    obs = [rig.root] + list(rig.root.children_recursive)
    keys = [(1, True)]
    for a, b in ranges:
        keys += [(ctx.F(ctx.T(a)), False), (ctx.F(ctx.T(b)), True)]
    for ob in obs:
        for f, hid in keys:
            ob.hide_render = hid
            ob.keyframe_insert("hide_render", frame=max(1, f))


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
        rig = RIGS[spec.get("rig", name)](tex, name=name, **({"s": spec["s"]} if "s" in spec else {}))
        clips = [dict(c, impacts=tl.get("impacts", [])) if c["do"] in ("punch", "flurry") else c
                 for c in ep.get("clips", []) if c["who"] == name]
        actors[name] = Actor(name, rig, spec, clips, ctx.beats, ctx.end, tl["lines"], actors)
        if spec.get("visible"):
            visible(ctx, rig, spec["visible"])

    for e in ep.get("fx", []):
        k = e["kind"]
        if k == "sky":
            keys = [(ctx.T(r), en, st, fx.POC_SUN if (len(rest) and rest[0] == "poc") else None)
                    for r, en, st, *rest in e["keys"]]
            fx.sky(ctx, tuple(e["sun_dir"]), keys, below=e.get("below", "void"))
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
            close = ctx.T(e["close"]) if e.get("close") is not None else None
            fx.sky_tear(ctx, ctx.T(e["at"]), ctx.T(e["eye_at"]), ctx.T(e.get("end", "end")),
                        center=tuple(e.get("center", (-5.0, 40.0, 26.0))), scale=e.get("scale", 2.0),
                        gaze=[tuple(g) for g in e["gaze"]] if e.get("gaze") else None,
                        lock=tuple(e.get("lock", (2.2, 2.5))), close_at=close)
            if e.get("tint", True):              # the tear's magenta light on the scene
                fx.fill(ctx, (0.1, -0.86, -0.5), ctx.T(e["at"]),
                        (close + 0.2) if close is not None else ctx.T(e.get("end", "end")) + 1,
                        color=(1.0, 0.25, 0.85), energy=1.3)
        elif k == "tree_broken":                 # episode 1's tree: the punched block is gone
            t = bpy.data.objects["target"]
            t.hide_render = True
            t.keyframe_insert("hide_render", frame=1)
        elif k == "portal_machine":
            props.portal_machine(ctx, tex, tuple(e["origin"]), e.get("w", 5), e.get("h", 6),
                                 build=(ctx.T(e["build"][0]), ctx.T(e["build"][1])) if e.get("build") else None,
                                 open_at=ctx.T(e["open"]) if e.get("open") else None,
                                 dark_at=ctx.T(e["dark"]) if e.get("dark") else None,
                                 snap_at=ctx.T(e["snap"]) if e.get("snap") else None,
                                 flicker=(ctx.T(e["flicker"][0]), ctx.T(e["flicker"][1])) if e.get("flicker") else None,
                                 see=e.get("see", 1.0), reveal=ctx.T(e["reveal"]) if e.get("reveal") else None)
            if e.get("behind"):                  # what stands on the other side
                b = e["behind"]
                props.room_behind(ctx, tex, tuple(e["origin"]), (ctx.T(b["show"][0]), ctx.T(b["show"][1])),
                                  e.get("w", 5), e.get("h", 6), depth=b.get("depth", 4.5))
        elif k == "button":
            props.button(ctx, tuple(e["at"]), ctx.T(e["press"]) if e.get("press") else None,
                         ctx.T(e["smash"]) if e.get("smash") else None)
        elif k == "spawn_pad":
            props.spawn_pad(ctx, tuple(e["at"]), ctx.T(e["appear"]))
        elif k == "hazards":
            hit = None
            if e.get("hit"):
                h = e["hit"]
                th = ctx.T(h["at"])
                a = actors[h["actor"]].state_at(th)["loc"]
                hit = {"t": th, "target": add(a, (0, 0, 1.3)), "flight": h.get("flight", 0.55)}
            bar = None
            if e.get("bar"):
                b = e["bar"]
                tp = ctx.T(b["pass"])
                bar = {"t": ctx.T(b["from"]), "at": tuple(b["at"]), "pass_t": tp,
                       "pass_at": actors[b["actor"]].state_at(tp)["loc"], "rate": b.get("rate", 0.8)}
            props.hazards(ctx, tuple(e["src"]), ctx.T(e["from"]), ctx.T(e["to"]), ctx.T(e["clear"]),
                          n=e.get("n", 9), seed=e.get("seed", 4), hit=hit, bar=bar,
                          suck=(ctx.T(e["suck"][0]), ctx.T(e["suck"][1])) if e.get("suck") else None)
        elif k == "burst":
            t = ctx.T(e["at"])
            props.burst(ctx, actors[e["actor"]].state_at(t)["loc"], t)
        elif k == "dark_cube":
            t = ctx.T(e["from"])
            props.dark_cube(ctx, tex, add(actors[e["actor"]].state_at(t)["loc"], tuple(e.get("offset", (0, 0, 1.2)))),
                            t, ctx.T(e["to"]))
        elif k == "void_room":
            props.void_room(ctx, tex, tuple(e["frame"]), (ctx.T(e["show"][0]), ctx.T(e["show"][1])),
                            tuple(e["null_at"]))
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
    for a in actors.values():
        snap_jumps(a.rig.root)

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
