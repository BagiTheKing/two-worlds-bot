"""Noob lab: the Noob in the warm studio, one render per variant, on one sheet.
Usage: python noob_lab.py variants.json out.jpg [tile_px] [samples]
variants: [{"label": "...", "head": "classic"|"box", "face": {...}, "pose": {...},
            "cam": {"az": 0, "el": 0, "dist": 6, "tz": 1.6, "lens": 60}}]"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from faceplate import set_face  # noqa: E402
from noob import build_noob, pose_noob  # noqa: E402

VAR = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
TILE = int(sys.argv[3]) if len(sys.argv) > 3 else 300
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 16

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
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


sun("key", (-0.45, 0.75, -0.5), 4.0, (1.0, 0.9, 0.8))
sun("rim", (0.8, -0.4, -0.3), 2.5, (1.0, 0.85, 0.65))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = TILE
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = -0.2

heads = {}
for h in sorted({v.get("head", "classic") for v in VAR}):
    col = bpy.data.collections.new("noob_" + h)
    sc.collection.children.link(col)
    heads[h] = (col, build_noob(col, head=h, height=2.0, name="noob_" + h))

tiles = []
for i, v in enumerate(VAR):
    h = v.get("head", "classic")
    for k, (col, n) in heads.items():
        col.hide_render = k != h
    col, n = heads[h]
    from faceplate import NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH, MOUTH_DEFAULTS
    for e in NOOB_EYES:
        for k_, d_ in NOOB_EYE_DEFAULTS.items():
            n.face[f"{e}_{k_}"] = d_
    for k_, d_ in {**MOUTH_DEFAULTS, **NOOB_MOUTH}.items():
        n.face[k_] = d_
    set_face(n.face, v.get("face", {}))
    n.face.update_tag()
    pose_noob(n, v.get("pose", {}))
    for ob_ in list(bpy.data.objects):
        if ob_.name.startswith("item_"):
            bpy.data.objects.remove(ob_, do_unlink=True)
    for pr in v.get("props", []):
        from props import sprite_item
        from noob import noob_hold
        ITEMS = os.environ.get("TWB_ASSETS", "/home/user/assets") + "/mcprep/resourcepacks/mcprep_default/assets/minecraft/textures/item"
        noob_hold(n, sprite_item(pr["item"], ITEMS), pr.get("side", "sl"), up=pr.get("up", -15), face=pr.get("face", 55))
    c = {"az": 0, "el": 2, "dist": 2.6, "tz": 1.77, "lens": 70, **v.get("cam", {})}
    a, e_ = math.radians(c["az"]), math.radians(c["el"])
    tgt = Vector((0, 0, c["tz"]))
    cam.location = tgt + Vector((math.sin(a) * math.cos(e_), -math.cos(a) * math.cos(e_), math.sin(e_))) * c["dist"]
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = c["lens"]
    p = os.path.join(HERE, f"_nlab_{i}.png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    tiles.append((p, v.get("label", str(i))))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
cols = min(6, len(tiles))
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * TILE, rows * (TILE + 30)), (18, 18, 22))
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
for k, (p, label) in enumerate(tiles):
    x, y = (k % cols) * TILE, (k // cols) * (TILE + 30)
    sheet.paste(Image.open(p).convert("RGB"), (x, y + 30))
    d.text((x + 6, y + 5), label, fill="white", font=f)
    os.remove(p)
sheet.save(OUT, quality=90)
print("SHEET", OUT, sheet.size)
