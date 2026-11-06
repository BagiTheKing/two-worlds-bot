"""Face lab: the BlendSwap Steve's head in a simple warm studio, rendered once
per variant so face shapes can be compared on one sheet.
Usage: python face_lab.py variants.json out.jpg [tile_px] [samples]
variants.json: [{"label": "...", "loc": {"bone": [x, y, z]}, "rot": {"bone": [w, x, y, z]},
                 "keys": {"shape key name": value}, "view": "front"|"q"}]"""
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

VAR = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
TILE = int(sys.argv[3]) if len(sys.argv) > 3 else 300
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 16
HERE_ = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE_, "..", ".."))
A = os.environ.get("TWB_ASSETS", "/home/user/assets")            # MCprep pack (not in the repo)
RIGS = os.path.join(REPO, "assets", "rigs")                       # the Steve rig and its skins
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

bpy.context.preferences.filepaths.use_scripts_auto_execute = True
bpy.ops.wm.open_mainfile(filepath=RIGS + "/steve_blendswap.blend", load_ui=False, use_scripts=True)
sc = bpy.context.scene
for o in list(sc.objects):                      # keep only the rig's own collection
    if not any(c.name == "Rig" or c.name.startswith("Head_Layers") for c in o.users_collection):
        o.hide_render = True
for c in bpy.data.collections:
    if c.name.startswith("Head_Layers"):
        c.hide_render = True
skin = bpy.data.images.load(os.environ.get("SKIN", RIGS + "/steve_skin_v2.png"), check_existing=True)
for m in bpy.data.materials:
    if m.name.startswith("Skin") and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and n.image.name.startswith("Steve"):
                n.image = skin
for idb in list(bpy.data.objects) + list(bpy.data.armatures) + list(bpy.data.shape_keys):
    ad = getattr(idb, "animation_data", None)
    if ad:
        for d in ad.drivers:
            d.is_valid = True
            d.driver.is_valid = True
arm = bpy.data.objects["Thomas_rig"]
if os.environ.get("BLANK"):                          # remove the rig's own eyes, brows and mouth
    head = bpy.data.objects["Head_NoDeform"]
    skin_mat = head.data.materials[0]
    for i, m in enumerate(head.data.materials):
        if m and m.name in ("Eyes.001", "Mouth"):
            head.data.materials[i] = skin_mat
    for n_ in ("Eyes", "Eyebrows", "Eyebrows.001", "Top_teeth", "Bottom_teeth", "Tongue"):
        bpy.data.objects[n_].hide_render = True
if os.environ.get("FACE"):
    from skin_face import make_face_skin
    make_face_skin(os.path.join(HERE, "_faceskin.png"))
    from faceplate import build_faceplate, set_face, flatten_face
    flatten_face(bpy.data.objects["Head_NoDeform"], arm)
    FACEPLATE = build_faceplate(arm, bpy.data.images.load(os.path.join(HERE, "_faceskin.png")),
                                lattice=bpy.data.objects["Head"])
    from brows import build_brows, set_brows
    BROWS = build_brows(arm, lattice=bpy.data.objects["Head"])
from hair import build_hair  # noqa: E402
build_hair(arm, lattice=bpy.data.objects["Head"])
# our defaults: eyes and brows lower, brows thick, head straight
DEFAULT_LOC = {"Eyes_UP_DOWN": (0, -0.1, 0)}
arm.pose.bones["Head"].rotation_quaternion = (1, 0, 0, 0)
for key in bpy.data.shape_keys:
    kb = key.key_blocks.get("EyebrowThikness")
    if kb is not None:
        if key.animation_data:
            for d in list(key.animation_data.drivers):
                if "EyebrowThikness" in d.data_path:
                    key.animation_data.drivers.remove(d)
        kb.value = 1.0

# studio: warm key from the front right, soft sky fill, a rim
w = bpy.data.worlds.new("studio")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.55, 0.75, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9


def sun(name, toward, e, col):
    s = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
    sc.collection.objects.link(s)
    s.data.energy, s.data.color, s.data.angle = e, col, math.radians(3)
    s.rotation_euler = Vector(toward).normalized().to_track_quat("-Z", "Y").to_euler()


sun("key", (-0.4, 0.8, -0.45), 4.0, (1.0, 0.86, 0.7))
sun("rim", (0.8, -0.4, -0.3), 3.0, (1.0, 0.8, 0.55))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
HEAD = Vector((0.0, 0.0, 2.82))
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = TILE
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Punchy"
except TypeError:
    pass
sc.view_settings.exposure = 0.3
sc.render.film_transparent = False

TOUCH_LOC = set(DEFAULT_LOC) | set(sum((list(x.get("loc", {})) for x in VAR), []))
TOUCH_ROT = set(sum((list(x.get("rot", {})) for x in VAR), []))
tiles = []
for i, v in enumerate(VAR):
    for b in TOUCH_LOC:                             # reset every control any variant uses
        arm.pose.bones[b].location = (0, 0, 0)
    for b in TOUCH_ROT:
        arm.pose.bones[b].rotation_mode = "QUATERNION"
        arm.pose.bones[b].rotation_quaternion = (1, 0, 0, 0)
    for b, val in DEFAULT_LOC.items():
        arm.pose.bones[b].location = val
    for b, val in v.get("loc", {}).items():
        arm.pose.bones[b].location = val
    for b, q in v.get("rot", {}).items():
        arm.pose.bones[b].rotation_quaternion = q
    if os.environ.get("FACE"):
        from faceplate import EYES, EYE_DEFAULTS, MOUTH_DEFAULTS
        for e in EYES:
            for k_, d_ in EYE_DEFAULTS.items():
                FACEPLATE[f"{e}_{k_}"] = d_
        for k_, d_ in MOUTH_DEFAULTS.items():
            FACEPLATE[k_] = d_
        set_face(FACEPLATE, v.get("face", {}))
        for ob_ in BROWS.values():
            for kb_ in ob_.data.shape_keys.key_blocks[1:]:
                kb_.value = 0.0
        set_brows(BROWS, v.get("brows", {}))
        FACEPLATE.update_tag()
    if "pose" in v:
        from pose import pose as _pose
        _pose(arm, v["pose"])
    view = v.get("view", "front")
    az = {"front": 0, "q": -28, "mouth": 0, "lower": 0, "body": 0, "body_q": -35, "body_side": -90}[view]
    a = math.radians(az)
    tgt = HEAD + Vector((0, 0, {"mouth": -0.24, "lower": -0.12}.get(view, 0.0)))
    dist = {"mouth": 1.25, "lower": 1.9}.get(view, 2.6)
    if view.startswith("body"):
        tgt, dist = Vector((0, 0, 1.62)), 8.2
    if "cam" in v:                                   # a free camera: az, el (deg), dist, target height
        c_ = v["cam"]
        a = math.radians(c_.get("az", 0))
        e_ = math.radians(c_.get("el", 0))
        tgt = Vector((0, 0, c_.get("tz", 1.62)))
        cam.location = tgt + Vector((math.sin(a) * math.cos(e_), -math.cos(a) * math.cos(e_), math.sin(e_))) * c_.get("dist", 8.2)
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = c_.get("lens", 70)
        dist = None
    if dist is not None:
        cam.location = tgt + Vector((math.sin(a), -math.cos(a), 0.02)) * dist
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 70
    p = os.path.join(HERE, f"_lab_{i}.png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    tiles.append((p, v.get("label", str(i))))

if os.environ.get("FRAMES_DIR"):                    # an animation: keep the frames, no sheet
    import shutil
    os.makedirs(os.environ["FRAMES_DIR"], exist_ok=True)
    for k, (p, _) in enumerate(tiles):
        shutil.move(p, os.path.join(os.environ["FRAMES_DIR"], f"f_{k:04d}.png"))
    print("FRAMES", len(tiles))
    sys.exit(0)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
cols = min(6, len(tiles))
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * TILE, rows * (TILE + 30)), (18, 18, 22))
d = ImageDraw.Draw(sheet)
try:
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except OSError:
    f = ImageFont.load_default()
for k, (p, label) in enumerate(tiles):
    x, y = (k % cols) * TILE, (k // cols) * (TILE + 30)
    sheet.paste(Image.open(p).convert("RGB"), (x, y + 30))
    d.text((x + 6, y + 5), label, fill="white", font=f)
    os.remove(p)
sheet.save(OUT, quality=90)
print("SHEET", OUT, sheet.size)
