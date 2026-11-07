"""Patch lab: Patch in a warm studio, one render per variant, on one sheet.
Usage: python patch_lab.py variants.json out.jpg [tile_px] [samples]
variants: [{"label": "...", "face": {...}, "cam": {"az": 0, "el": 5, "dist": 2.2}, "fins": 0}]"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from patch import DEFAULTS, build_patch, set_patch  # noqa: E402

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
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
for nm, toward, e, c in (("key", (-0.45, 0.75, -0.5), 4.0, (1.0, 0.9, 0.8)), ("rim", (0.8, -0.4, -0.3), 2.5, (1.0, 0.85, 0.65))):
    s_ = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN"))
    sc.collection.objects.link(s_)
    s_.data.energy, s_.data.color = e, c
    s_.rotation_euler = Vector(toward).normalized().to_track_quat("-Z", "Y").to_euler()
col = bpy.data.collections.new("patch")
sc.collection.children.link(col)
P = build_patch(col, size=0.42)
P.root.location = (0, 0, 1.0)
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
tiles = []
for i, v in enumerate(VAR):
    set_patch(P, {**DEFAULTS, **v.get("face", {})})
    for side, pv in P.fins.items():
        pv.rotation_euler = (math.radians(v.get("fins", 0)) * (1 if side == "l" else -1), 0, 0)
    P.root.rotation_euler = (0, 0, math.radians(v.get("yaw", 0)))
    c = {"az": 0, "el": 5, "dist": 1.35, "lens": 60, **v.get("cam", {})}
    a, e = math.radians(c["az"]), math.radians(c["el"])
    tgt = Vector((0, 0, 1.0 + c.get("tz", 0)))
    cam.location = tgt + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * c["dist"]
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = c["lens"]
    p = os.path.join(HERE, f"_plab_{i}.png")
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
print("SHEET", OUT)
