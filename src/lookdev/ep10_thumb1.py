"""FINALE 1/5's thumbnail, rendered from part 3's own scene: Steve and the Noob
side by side, frozen and terrified, and Null risen behind them, leaning over
them with his widest grin. No text (added on top with tools/thumb_title.py).

    python src/lookdev/ep10_thumb1.py TIMELINE TEX ASSETS out.png [--res 1920] [--samples 64]
        [--cam '[{"loc": [..], "look": [..], "lens": 20}]']

The scene, lights, sky and grade are part 3's (frame `--at`, the frozen
two-shot); this file only stages the still: Null moved round behind them and
turned to the camera, the two facing us, held faces, and its own camera.
"""
import argparse
import json
import math
import os
import sys

import bpy  # noqa: F401  (first: it brings mathutils)
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_entrance as EN                                         # noqa: E402
import ep10_p3_run as P3                                           # noqa: E402

CAM = {"loc": (0.05, -0.4, 0.75), "look": (0.0, -9.0, 8.5), "lens": 18, "fstop": 2.8, "fill": 420}
DY = 1.0                         # the two, brought this much closer to the camera
NULL = {"neck": (0.0, -11.5, 12.5), "k": 1.6, "lean": 24.0, "yaw": 180.0}


def stage(E):
    """Everything the still changes after part 3 has set its frame."""
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from ep09_new import SF, NF
    from ep10_entrance import draw_face
    G = E.G
    # Null: behind them, turned to us, leaning in over them
    n, k = Vector(NULL["neck"]), NULL["k"]
    rot = Matrix.Rotation(math.radians(NULL["yaw"]), 3, "Z") @ Matrix.Rotation(math.radians(NULL["lean"]), 3, "X")
    G.root.scale = (k, k, k)
    G.root.rotation_euler = rot.to_euler()
    G.root.location = n - rot @ (Vector((0, -0.35, 9.25)) * k)
    G.neck.rotation_euler = (0.0, 0.0, math.radians(-8))
    for side, sgn in (("sl", 1), ("sr", -1)):                  # arms open wide over them
        G.arms[side].rotation_euler = (math.radians(-62), math.radians(sgn * 34), 0)
    draw_face(E.face_im, smile=1.0, eyes=1.0, wide=1.0, open_=0.4)
    # the two: turned to us (their backs to him), frozen
    E.S.holder.rotation_euler = (0, 0, math.radians(180))
    E.S.holder.location = (P3.STEVE_AT.x + 0.35, P3.STEVE_AT.y + DY, 0.0)
    from noob import pose_noob, NOOB_POSES
    from ep09_new import flat, unflat
    npz = flat(NOOB_POSES["scared"])
    npz.update({"head_nod": -4, "head_tilt": -6, "chest_lean": -6, "arm_sl.fwd": 60, "arm_sr.fwd": 60, "root_yaw": 180.0})
    pose_noob(E.N, unflat(npz))
    E.N.root.location = (P3.NOOB_AT.x - 0.35, P3.NOOB_AT.y - 0.1 + DY, 0.0)
    fs = {f"{e}_{kk}": v for e in EYES for kk, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    sf = dict(SF["scared"], m_o=0.8, m_w=1.6, both_py=0.12, both_px=0.2, both_ps=0.6, bb_raise=0.7, bb_tilt=-0.9)
    for kk, v in sf.items():
        if kk.startswith("both_"):
            for e in EYES:
                fs[f"{e}_{kk[5:]}"] = v
        elif not kk.startswith("bb_"):
            fs[kk] = v
    set_face(E.S.face, fs)
    set_brows(E.S.brows, {kk: v for kk, v in sf.items() if kk.startswith("bb_")})
    fn = {f"{e}_{kk}": v for e in NOOB_EYES for kk, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    for kk, v in dict(NF["shock"], both_py=0.1, both_px=-0.15).items():
        if kk.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{kk[5:]}"] = v
        else:
            fn[kk] = v
    set_face(E.N.face, fn)
    # Patch: between and above them, eyes wide
    from patch import DEFAULTS as PD, set_patch
    E.Pt.root.location = (0.0, P3.STEVE_AT.y + DY - 0.4, 2.45)
    E.Pt.root.rotation_euler = (0, 0, math.radians(180))
    set_patch(E.Pt, dict(PD, wide=1.0, look_y=0.6))
    for ob in E.dust:
        ob.hide_render = True


def camera(E, c):
    loc, look = Vector(c["loc"]), Vector(c["look"])
    E.cam.rotation_mode = "QUATERNION"
    E.cam.location = loc
    E.cam.rotation_quaternion = (look - loc).to_track_quat("-Z", "Y")
    E.cam.data.lens = c.get("lens", 19)
    E.cam.data.dof.aperture_fstop = c.get("fstop", 2.8)
    hs = Vector((0.05, P3.STEVE_AT.y + DY, 1.7))          # between their faces
    E.cam.data.dof.focus_distance = (hs - loc).length
    E.face_fill.location = loc + Vector((0, 0.3, 0.9))
    E.face_fill.data.spot_size = math.radians(70)
    E.face_fill.rotation_euler = (hs - E.face_fill.location).to_track_quat("-Z", "Y").to_euler()
    E.sc.render.motion_blur_shutter = 0.0
    if "fill" in c:
        E.face_fill.data.energy = c["fill"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("tex_dir")
    ap.add_argument("assets")
    ap.add_argument("out")
    ap.add_argument("--res", type=int, default=1920)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--at", type=float, default=1.0)       # the frozen two-shot
    ap.add_argument("--cam", help="json list of CAM overrides: one still each (framing tests)")
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    P3.align(tl)
    E = P3.build(tl, a.assets, a.res, a.samples)
    E.env = lambda t: 0.7
    E.mouth = {}
    sc = E.sc
    sc.render.resolution_x, sc.render.resolution_y = a.res * 9 // 16, a.res
    out = os.path.abspath(a.out)
    mist_dir = os.path.join(os.path.dirname(out), "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"
    f = int(round(a.at * EN.FPS)) + 1
    sc.frame_set(f)
    P3.apply(E, a.at)
    stage(E)
    cams = [dict(CAM, **c) for c in json.loads(a.cam)] if a.cam else [CAM]
    for i, c in enumerate(cams):
        camera(E, c)
        bpy.context.view_layer.update()
        dst = out if len(cams) == 1 else out.replace(".png", f"_{i}.png")
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        EN.finish(dst, cand[-1] if cand else "")
        for x in cand:
            os.remove(x)
        print("STILL", dst, flush=True)


if __name__ == "__main__":
    main()
