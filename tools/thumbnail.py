"""
Series thumbnail, base image: a still staged in the episode's own scene (not
a video frame). Null towers over the bridge, both heroes run at the camera,
scared. The title goes on top with tools/thumb_text.py, so each episode only
changes the text.

    python tools/thumbnail.py episodes/ep00_the_end.json build/timeline.json build/tex \
        out.png [--res 3840] [--samples 64]
"""

import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import build_episode                      # noqa: E402
import scene_poc                          # noqa: E402
from kit.blocks import aim, box, image, material   # noqa: E402

MOMENT = "null_1+1.0"                     # dusk, Null risen, debris orbiting
NULL_AT = (19.0, 0.45, -3.5)
POSES = {
    "steve": {"loc": (1.2, 1.2, 0), "yaw": -1.5708, "tilt": (0.0, -0.12),
              "leg_r": (0.75, 0, 0), "leg_l": (-0.6, 0, 0),
              "arm_r": (0.3, 2.0, 0), "arm_l": (0.9, -0.3, 0), "head": (-0.08, 0, 0.12)},
    "noob": {"loc": (1.5, -0.35, 0), "yaw": -1.5708, "tilt": (0.0, -0.1),
             "leg_r": (-0.7, 0, 0), "leg_l": (0.75, 0, 0),
             "arm_r": (0.4, 1.05, 0), "arm_l": (0.0, -2.45, 0), "head": (-0.1, 0, -0.15)},
    "null": {"loc": NULL_AT, "yaw": -1.5708,
             "arm_r": (-1.35, 0.75, 0), "arm_l": (-1.35, -0.75, 0), "head": (0.2, 0.1, 0)},
}
CAMERA = {"loc": (-1.6, 0.45, 0.42), "look": (8.0, 0.45, 5.0), "lens": 19}


def unanimate(ob):
    for o in [ob] + list(ob.children_recursive):
        o.animation_data_clear()


def swap_face(mat_name, tex_path):
    m = bpy.data.materials[mat_name]
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE":
            n.image = image(tex_path)


def glow_disc(loc, size, color, strength):
    """A soft radial glow (behind Null), drawn as an emissive, fading disc."""
    m = bpy.data.materials.new("thumb_glow")
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n != out:
            nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (0, 0, 0)
    mapping.inputs["Scale"].default_value = (2.0 / size,) * 3
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], pw.inputs[0])
    nt.links.new(pw.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    em.inputs["Strength"].default_value = strength
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    disc = bpy.context.object
    disc.data.materials.append(m)
    return disc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("timeline")
    ap.add_argument("tex_dir")
    ap.add_argument("out")
    ap.add_argument("--res", type=int, default=3840)
    ap.add_argument("--samples", type=int, default=64)
    a = ap.parse_args()
    tex_dir = os.path.abspath(a.tex_dir)

    ctx, _ = build_episode.build(a.episode, a.timeline, tex_dir)
    scene_poc.setup_render(a.res, a.samples)
    sc = bpy.context.scene
    sc.render.use_motion_blur = False
    sc.frame_set(ctx.F(ctx.T(MOMENT)))

    # darker, scarier sky; the sun stays down
    w = sc.world
    if w.node_tree.animation_data:
        w.node_tree.animation_data_clear()
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    sun = bpy.data.objects["sun"]
    sun.data.animation_data_clear()
    sun.data.energy = 0.35

    for ob in bpy.data.objects:
        if ob.name.startswith("bridge_") and ob.parent is None and not ob.get("is_flash"):
            unanimate(ob)
            for o in [ob] + list(ob.children_recursive):
                o.hide_render = False
        if ob.name == "sign" or ob.name.startswith(("sun_disc", "scloud_")):
            unanimate(ob)
            for o in [ob] + list(ob.children_recursive):
                o.hide_render = True

    from kit.rigs import PARTS
    for name, pose in POSES.items():
        root = bpy.data.objects[name]
        unanimate(root)
        root.location = pose["loc"]
        tx, ty = pose.get("tilt", (0, 0))
        root.rotation_euler = (tx, ty, pose["yaw"])
        root.scale = (1, 1, 1)
        for p in PARTS:
            bpy.data.objects[f"{name}_{p}"].rotation_euler = pose.get(p, (0, 0, 0))
    swap_face("steve_face", os.path.join(tex_dir, "steve_face_scared.png"))
    swap_face("noob_face", os.path.join(tex_dir, "noob_face_scared.png"))

    # Null's orbiting debris follows it to its new spot, plus magenta checker cubes
    chest = Vector(NULL_AT) + Vector((0, 0, 11))
    rnd = random.Random(5)
    for ob in bpy.data.objects:
        if ob.name.startswith("orbit_") and ob.type == "MESH" and ob.parent is None:
            ob.animation_data_clear()
            ob.hide_render = False
            side = rnd.choice((-1, 1))                # around Null, never across its face
            ob.location = chest + Vector((rnd.uniform(-3, 4), side * rnd.uniform(5, 13), rnd.uniform(-8, 10)))
    missing = bpy.data.materials["missing_flash"]
    for i in range(16):
        s = rnd.uniform(0.35, 0.95)
        c = box(f"thumb_glitch_{i}", (s, s, s), (0, 0, 0), {"default": missing})
        side = rnd.choice((-1, 1))
        c.location = chest + Vector((rnd.uniform(-4, 3), side * rnd.uniform(4, 11), rnd.uniform(-7, 11)))
        c.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))
    # embers drifting up from the void
    for i in range(90):
        hot = rnd.random() < 0.5
        m = material(f"ember_{i}", (0, 0, 0), emission=(1.0, 0.45, 0.1) if hot else (1.0, 0.1, 0.8),
                     strength=rnd.uniform(6, 14))
        s = rnd.uniform(0.04, 0.12)
        e = box(f"thumb_ember_{i}", (s, s, s), (0, 0, 0), {"default": m})
        e.location = (rnd.uniform(2.5, 22), rnd.uniform(-9, 9), rnd.uniform(-2, 16))

    # a violet glow behind Null, and lights for a phone screen
    g = glow_disc(chest + Vector((10, 0, 2)), 64, (0.6, 0.1, 1.0), 11.0)
    aim(g, (-1, 0, 0))

    def lamp(name, kind, loc, target, color, energy, size=2.0):
        l = bpy.data.objects.new(name, bpy.data.lights.new(name, kind))
        sc.collection.objects.link(l)
        l.location = loc
        aim(l, tuple(t - s for t, s in zip(target, loc)))
        l.data.color, l.data.energy = color, energy
        if kind == "AREA":
            l.data.size = size
    lamp("thumb_key", "AREA", (-1.0, -1.6, 2.2), (1.3, 0.5, 1.5), (0.85, 0.92, 1.0), 110, 2.5)
    lamp("thumb_rim", "AREA", (4.5, 0.5, 2.8), (1.3, 0.5, 1.2), (1.0, 0.2, 0.85), 380, 4.0)
    lamp("thumb_null", "AREA", (4.0, -3.0, 9.0), tuple(chest), (0.75, 0.5, 1.0), 2200, 6.0)

    cam = bpy.data.objects.new("thumb_cam", bpy.data.cameras.new("thumb_cam"))
    sc.collection.objects.link(cam)
    cam.data.lens = CAMERA["lens"]
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36
    cam.data.clip_end = 600
    cam.location = CAMERA["loc"]
    aim(cam, tuple(t - s for t, s in zip(CAMERA["look"], CAMERA["loc"])))
    for m in list(sc.timeline_markers):
        sc.timeline_markers.remove(m)
    sc.camera = cam
    sc.render.filepath = os.path.abspath(a.out)
    bpy.ops.render.render(write_still=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
