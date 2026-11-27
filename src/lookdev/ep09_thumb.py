"""Episode 9's thumbnail, rendered from the episode's own new-look scene: the
upgraded Steve and Noob, shoulder to shoulder and terrified, Patch between
them, Null risen in the purple storm behind. No text (added on top later).

    python src/lookdev/ep09_thumb.py build/timeline.json build/tex ASSETS out.png \
        [--res 1920] [--samples 64] [--at rise+2.0]

The scene, lights, sky and grade are ep09_new's; this file only stages the
still: closer positions, a held pose and face, and its own camera.
"""
import argparse
import json
import os
import sys

import bpy  # noqa: F401  (first: it brings mathutils)
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep09_new as M                                          # noqa: E402

# a tight two-shot: the two closer together than in the episode
M.STEVE_AT = Vector((-0.46, 0.0, 0.0))
M.NOOB_AT = Vector((0.6, 0.2, 0.0))
M.PATCH_AT = Vector((0.06, 0.55, 2.45))

CAM = {"loc": (0.02, -2.6, 1.3), "look": (-0.3, 30.0, 18.0), "lens": 28, "fstop": 2.2, "fill": 60}
KEY_BOOST = 2.2                  # the faces read warm against the purple storm

STEVE_FACE = dict(M.SF["scared"], m_o=0.85, m_w=1.7, both_py=0.32, both_ps=0.62, bb_raise=0.6, bb_tilt=-0.85)
NOOB_FACE = dict(M.NF["shock"], both_py=0.3)
STEVE_POSE = {"head_nod": -9, "head_turn": 6, "chest_lean": -6,              # the rise's recoil
              "arm_sl": {"out": 22, "fwd": 18, "elbow": 40}, "arm_sr": {"out": 6, "fwd": 8, "elbow": 20}}
NOOB_POSE = {"head_nod": -10, "head_tilt": -6, "head_turn": -6,
             "arm_sl": {"out": 8}, "arm_sr": {"out": 8}}
PATCH_FACE = {"wide": 1.0, "look_y": 0.5, "look_x": 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("tex_dir")
    ap.add_argument("assets")
    ap.add_argument("out")
    ap.add_argument("--res", type=int, default=1920)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--at", default="delete+1.8")      # Null risen, the ground erased behind them
    ap.add_argument("--cam", help="json list of CAM overrides: one still each (framing tests)")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    import soundfile as sf                                    # no voices: the faces are held
    silent = os.path.join(os.path.dirname(os.path.abspath(a.out)), "_silent.wav")
    sf.write(silent, np.zeros(24000), 24000)
    E = M.build(tl, silent, a.tex_dir, a.assets, a.res, a.samples)
    E.mouth = {}
    M._acting(E.chor)
    C = E.chor
    C.steve_face = lambda t: STEVE_FACE
    C.noob_face = lambda t: NOOB_FACE
    C.patch_face = lambda t: PATCH_FACE
    C.steve_act = lambda t: STEVE_POSE
    C.noob_act = lambda t: NOOB_POSE
    C.facing = lambda t: 0.0
    t = E.T(a.at)
    sc = E.sc
    sc.render.use_motion_blur = False
    out = os.path.abspath(a.out)
    mist_dir = os.path.join(os.path.dirname(out), "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"
    print("null ground", round(E.null_ground, 2))
    f = int(round(t * M.FPS)) + 1
    sc.frame_set(f)
    fill = bpy.data.objects.new("thumb_fill", bpy.data.lights.new("thumb_fill", "AREA"))
    fill.data.size = 1.6
    fill.data.color = (1.0, 0.9, 0.8)
    sc.collection.objects.link(fill)
    for i, over in enumerate(json.loads(a.cam) if a.cam else [{}]):
        cam = dict(CAM, **over)
        loc, look = Vector(cam["loc"]), Vector(cam["look"])
        C.camera = lambda t: (loc, look, cam["lens"], (loc - Vector((0, 0, 1.7))).length, cam["fstop"], 0.0)
        look_state = M.apply(E, (f - 1) / M.FPS)
        E.key.data.energy *= KEY_BOOST
        E.key.data.color = (1.0, 0.86, 0.72)
        heads = Vector((0.0, 0.05, 1.72))                     # a soft front light on both faces
        fill.location = loc + Vector((0.3, 0.6, 0.35))
        fill.rotation_euler = (heads - fill.location).to_track_quat("-Z", "Y").to_euler()
        fill.data.energy = cam["fill"]
        dst = out if not a.cam else out.replace(".png", f"_{i}.png")
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        M.finish(dst, cand[-1] if cand else "", look_state)
        for x in cand:
            os.remove(x)
        print("THUMB", dst, "at", round(t, 2), "s")

if __name__ == "__main__":
    main()
