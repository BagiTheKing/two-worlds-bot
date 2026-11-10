"""Finale look-dev: Null's entrance through the first portal, as stills.

    TWB_ASSETS=... python src/lookdev/ep10_entrance_lab.py out_dir [res] [samples] [shots: fingers,reveal,...]

One world build, then each shot poses Null and the camera and renders a still
(hazed and graded like the episode).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from portal import build_portal, drape  # noqa: E402
from stage import build_null_char, null_lights, place_null_lights, char_light  # noqa: E402
from null import cells_look, null_smile, build_hand  # noqa: E402
from world import build_world, add_world_fx, fx_set, set_sky, set_sun, SKY_GOLDEN, render_depth  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
RES = int(sys.argv[2]) if len(sys.argv) > 2 else 540
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 24
SHOTS = (sys.argv[4] if len(sys.argv) > 4 else "fingers,reveal").split(",")
A = os.environ["TWB_ASSETS"]
PORTAL_AT = Vector((0.0, 5.0, 0.0))
SUN = (float(os.environ.get("SUN_AZ", -34)), float(os.environ.get("SUN_EL", 25)))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cfg = {"seed": 7, "sun": SUN, "flat_box": [-7, 7, -40, 8], "plant_clear_box": [-2.2, 2.2, 2.5, 6.0],
       "keep_clear": [(0, -14, 8), (0, -26, 8), (0, 16, 5), (0, 24, 5)],
       "feature_trees": [(-6, 15, "big_oak"), (6, 15, "oak"), (-9, 21, "oak"), (9, 20, "big_oak"), (-4, 24, "birch"),
                         (4, 25, "oak"), (-12, 16, "cherry"), (12, 15, "cherry"), (-7, 29, "oak"), (8, 30, "cherry")],
       "particle_box": (-6, 6, -2, 9, 0.3, 6.0)}
W = build_world(sc, A, cfg)
add_world_fx(W)
fx_set(W, R=1e5, Wd=100.0, Cx=0.0, Cy=0.0, D=0.0, Nx=0.0, Ny=60.0, Dz=-1.0)
DUSK = {"glow": (255, 232, 190), "power": 26.0, "horizon": (255, 206, 176), "mid": (170, 168, 240), "zenith": (60, 96, 214),
        "fill": 1.0, "fill_col": (186, 196, 240)}            # a low sun: warm at the horizon, still a bright sky
set_sky(W, DUSK)
set_sun(W, SUN[0], SUN[1], 6.4, (1.0, 0.74, 0.46))
P = build_portal(sc, A, at=PORTAL_AT)
X = build_null_char(sc, A, height=10.0)
null_lights(sc, X)
HAND = build_hand(X.col)
for o in X.col.objects:                                    # the lab's Null has no orbit yet: it forms as he unfolds
    if "_orbit" in o.name or "_trail_" in o.name:
        o.hide_render = True

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.dof.use_dof = True
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.render.resolution_x = RES * 9 // 16
sc.render.resolution_y = RES
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = -0.1


def null_at(height, loc, yaw=0.0, lights=1.0):
    k = height / 10.0
    X.root.scale = (k, k, k)
    X.root.location = loc
    X.root.rotation_euler = (0, 0, math.radians(yaw))
    place_null_lights(X, fade=lights)
    cells_look(near=0.9 * height, far=2.4 * height)


def show(names=None):
    for o in X.col.objects:
        if "_orbit" in o.name or "_trail_" in o.name or o.name.startswith("null_hand"):
            continue
        o.hide_render = names is not None and not any(n in o.name for n in names)


def camera(loc, look, lens, fstop=2.8, focus=None):
    loc, look = Vector(loc), Vector(look)
    cam.location = loc
    cam.rotation_euler = (look - loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.focus_distance = focus or (look - loc).length
    cam.data.dof.aperture_fstop = fstop


def shot_fingers():
    """Frame 1: his hand already through the membrane, the skin stretched round the knuckles, the claws hanging out."""
    k = float(os.environ.get("HAND", 0.46))
    HAND.scale = (k, k, k)
    HAND.rotation_euler = (math.radians(-24), math.radians(-5), math.radians(6))
    HAND.location = PORTAL_AT + Vector((0.12, 0.12, 3.35))                # the wrist, just behind the membrane
    for o in [HAND] + list(HAND.children):
        o.hide_render = False
    null_at(4.0, tuple(PORTAL_AT + Vector((0, 30, -40))), lights=0.0)    # the rest of him is still on the other side
    show([])
    null_smile(0.0)
    cells_look(near=4.0, far=9.0, awake=0.0)
    X.glow.hide_render = True
    bpy.context.view_layer.update()
    drape(P, list(HAND.children))
    camera(PORTAL_AT + Vector((1.1, -4.1, 1.7)), PORTAL_AT + Vector((0.0, -0.2, 2.45)), 38, fstop=2.8)
    return {"haze": {"L": 260, "start": 25, "max": 0.7, "haze_warm": True}, "tint": [1.04, 0.98, 1.0]}


def shot_reveal():
    """The head rises into frame in 3/4, the low sun behind it, the portal's purple on the other side."""
    H = 7.5
    for s in ("sl", "sr"):
        X.arms[s].rotation_euler = (math.radians(-18), 0, 0)
        X.forearms[s].rotation_euler = (0, 0, 0)
    null_at(H, tuple(PORTAL_AT + Vector((0.3, -3.2, -1.6))), yaw=4, lights=0.55)
    show(None)
    for o in [HAND] + list(HAND.children):
        o.hide_render = True
    null_smile(1.0)
    cells_look(near=0.9 * H, far=2.4 * H, awake=0.0)      # the cells sleep until the ledge
    X.glow.hide_render = True
    bpy.context.view_layer.update()
    drape(P, [])
    head = Vector(X.neck.matrix_world.translation) + Vector((0, 0, 0.19 * H))
    camera(head + Vector((2.6, -8.2, -3.3)), head + Vector((0.0, 0.0, -0.9)), 30, fstop=4.0)
    return {"haze": {"L": 220, "start": 20, "max": 0.75, "haze_warm": True}, "tint": [1.08, 0.98, 0.94], "rays": 0.9}


def finish(path, look):
    from PIL import Image
    import grade as G
    import assemble
    raw = path.replace(".png", "_raw.png")
    os.replace(path, raw)
    dp = path.replace(".png", "_depth.png")
    render_depth(sc, dp)
    im = Image.open(raw).convert("RGB")
    im = G.haze(im, dp, None, look["haze"])
    assemble.W, assemble.H = im.size
    o = {"saturation": 1.28, "glow": 0.55, "threshold": 0.72, "tint": look["tint"]}
    from bpy_extras.object_utils import world_to_camera_view
    v = world_to_camera_view(sc, cam, cam.location + Vector(W.to_sun) * 1000)
    if look.get("rays") and v.z > 0 and -0.3 < v.x < 1.3 and -0.3 < v.y < 1.3:
        o["sun"], o["rays"] = [v.x, 1 - v.y], look["rays"]
    assemble.grade(im, o, 0, 0, None)
    im.save(path)
    os.remove(dp)


os.makedirs(OUT, exist_ok=True)
for name in SHOTS:
    look = globals()["shot_" + name]()
    dst = os.path.join(OUT, f"entrance_{name}.png")
    sc.render.filepath = dst
    bpy.ops.render.render(write_still=True)
    finish(dst, look)
    print("SAVED", dst, flush=True)
