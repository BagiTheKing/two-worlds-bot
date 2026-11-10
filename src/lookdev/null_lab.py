"""Null in the thumbnail's storm: violet-pink sky, a bright glow behind him,
pink and cyan rim light, the camera low looking up.
Usage: python null_lab.py out.png [res_x] [samples] [cam: thumb|low|side]"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from null import build_null, cells_look  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
RES = int(sys.argv[2]) if len(sys.argv) > 2 else 540
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 24
CAM = sys.argv[4] if len(sys.argv) > 4 else "thumb"
A = os.environ.get("TWB_ASSETS", "/home/user/assets")


def lin(c):
    return (*(((v / 255 + 0.055) / 1.055) ** 2.4 for v in c), 1)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
col = bpy.data.collections.new("null")
sc.collection.children.link(col)
N = build_null(col, A, height=10.0)
cells_look(near=float(os.environ.get("NEAR", 6.0)), far=float(os.environ.get("FAR", 16.0)),
           power=float(os.environ.get("POWER", 1.0)), awake=float(os.environ.get("AWAKE", 1.0)))            # (the lab's Null is 10 tall; the episodes' is 15)

# the storm sky: dark navy above, violet, pink low; a bright cold glow behind him
w = bpy.data.worlds.new("storm")
sc.world = w
w.use_nodes = True
nt = w.node_tree
bg = nt.nodes["Background"]
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
cr = ramp.color_ramp
cr.elements[0].position, cr.elements[0].color = 0.0, lin((214, 140, 206))
cr.elements[1].position, cr.elements[1].color = 0.6, lin((30, 24, 52))
e = cr.elements.new(0.22)
e.color = lin((128, 92, 160))
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0
glow_m = bpy.data.materials.new("glow")
glow_m.use_nodes = True
gt = glow_m.node_tree
for n in list(gt.nodes):
    gt.nodes.remove(n)
o = gt.nodes.new("ShaderNodeOutputMaterial")
gr = gt.nodes.new("ShaderNodeTexGradient")
gr.gradient_type = "SPHERICAL"
tcg = gt.nodes.new("ShaderNodeTexCoord")
gt.links.new(tcg.outputs["Object"], gr.inputs["Vector"])
em = gt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = lin((188, 214, 250))
pw = gt.nodes.new("ShaderNodeMath")
pw.operation = "POWER"
pw.inputs[1].default_value = 2.2
gt.links.new(gr.outputs["Fac"], pw.inputs[0])
ms = gt.nodes.new("ShaderNodeMath")
ms.operation = "MULTIPLY"
ms.inputs[1].default_value = 2.4
gt.links.new(pw.outputs[0], ms.inputs[0])
gt.links.new(ms.outputs[0], em.inputs["Strength"])
tr = gt.nodes.new("ShaderNodeBsdfTransparent")
add = gt.nodes.new("ShaderNodeAddShader")
gt.links.new(tr.outputs["BSDF"], add.inputs[0])
gt.links.new(em.outputs["Emission"], add.inputs[1])
gt.links.new(add.outputs["Shader"], o.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0.6, 9.0, 4.6), rotation=(math.radians(90), 0, 0))
gp = bpy.context.active_object
gp.scale = (9, 9, 1)
gp.data.materials.append(glow_m)
gp.visible_shadow = False
for attr in ("visible_diffuse", "visible_glossy"):
    setattr(gp, attr, False)


# the storm: dark smoke clouds around and behind him (a volume), lit pink on one side and cyan on the other
import random as _r  # noqa: E402
rr = _r.Random(3)
sm = bpy.data.materials.new("smoke")
sm.use_nodes = True
st = sm.node_tree
for n_ in list(st.nodes):
    st.nodes.remove(n_)
so = st.nodes.new("ShaderNodeOutputMaterial")
vp = st.nodes.new("ShaderNodeVolumePrincipled")
vp.inputs["Color"].default_value = lin((60, 46, 80))
nz = st.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 0.12
nz.inputs["Detail"].default_value = 6
tcs = st.nodes.new("ShaderNodeNewGeometry")               # world position: the noise varies across the storm
st.links.new(tcs.outputs["Position"], nz.inputs["Vector"])
cr2 = st.nodes.new("ShaderNodeValToRGB")
cr2.color_ramp.elements[0].position = 0.42
cr2.color_ramp.elements[1].position = 0.68
st.links.new(nz.outputs["Fac"], cr2.inputs["Fac"])
mul = st.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = 0.22
st.links.new(cr2.outputs["Color"], mul.inputs[0])
st.links.new(mul.outputs[0], vp.inputs["Density"])
st.links.new(vp.outputs["Volume"], so.inputs["Volume"])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 6, 5))
smoke = bpy.context.active_object
smoke.scale = (34, 10, 22)
smoke.data.materials.append(sm)


def light(name, kind, loc, aim, power, color, size=2.0):
    L = bpy.data.lights.new(name, kind)
    L.energy, L.color = power, color[:3]
    if kind == "AREA":
        L.size = size
    ob = bpy.data.objects.new(name, L)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


light("rim_pink", "AREA", (-7, 6, 7), (0, 0, 5.5), 7000, lin((255, 110, 230)), 4)
light("rim_cyan", "AREA", (7, 6, 6), (0, 0, 5.0), 8000, lin((120, 230, 255)), 4)
light("fill", "AREA", (0, -12, 3), (0, 0, 5.5), 700, lin((170, 140, 220)), 8)
light("top", "AREA", (0, 2, 16), (0, 0, 7), 3000, lin((230, 200, 255)), 6)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
C = {"thumb": ((0.3, -17.5, 2.8), (0.2, 0, 5.9), 30), "front": ((0.0, -24.0, 6.5), (0.0, 0, 6.0), 40), "hand": ((4.6, -11.0, 1.4), (4.6, 0, 1.4), 60), "low": ((1.5, -11, 0.6), (0, 0, 6.0), 22),
     "cells": ((0.9, -4.6, 6.9), (0.5, 0, 6.5), 34), "cells_x": ((1.0, -2.6, 6.6), (0.9, 0, 6.45), 50),
     "claw": ((4.3, -4.4, 1.6), (4.5, -1.0, 1.3), 38), "mid": ((0.6, -9.5, 5.2), (0.3, 0, 6.6), 30),
     "side": ((-10, -12, 4), (0, 0, 5), 32)}[CAM]
cam.location = C[0]
cam.rotation_euler = (Vector(C[1]) - Vector(C[0])).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = C[2]
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = RES
sc.render.resolution_y = RES * 16 // 9
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = 0.0
sc.cycles.volume_step_rate = 4.0
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("SAVED", OUT)
