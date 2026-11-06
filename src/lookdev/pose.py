"""Posing the BlendSwap Steve in plain terms (angles in degrees, distances in
rig units; the rig stands 3.2 tall, facing -y; "sl"/"sr" = the side on the
screen's left / right when he faces the camera, i.e. his right / his left).

    pose(arm, {
        "root_yaw": -10,                       # whole body turn (+ = toward screen left)
        "hips_drop": 0.0,                      # lower the hips (knees bend, feet stay)
        "chest_lean": 3,                       # + forward
        "chest_side": 0, "chest_twist": 4,
        "head_turn": 8, "head_tilt": 6, "head_nod": 0,   # nod + = down
        "arm_sl": {"out": 9, "fwd": 6, "twist": 0, "elbow": 12},
        "arm_sr": {...},
        "foot_sl": {"x": 0, "y": 0, "z": 0, "yaw": 0},   # offsets from under the hip
        "foot_sr": {...},
    })

Every rotation is given in the body's own frame and applied on top of where
the rig puts the bone (the rig's helper bones and constraints rotate some
parents), measured live: basis = M0^-1 . Q . M0, with M0 the bone's current
orientation and Q the wanted rotation in armature space.
"""
import math

import bpy
from mathutils import Quaternion, Vector

ARM = {"sl": ("R.arm", "R.arm_elbow"), "sr": ("L.arm", "L.arm_elbow")}
FOOT = {"sl": "FootCtrl.L.002", "sr": "FootCtrl.L.001"}
RESET = ["R.arm", "L.arm", "R.arm_elbow", "L.arm_elbow", "R.Arm_Upper", "L.Arm_Upper",
         "Upper_Body", "Lower_body", "Root2", "Head", "Waist"]
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)


def _q(axis, deg):
    return Quaternion(Vector(axis).normalized(), math.radians(deg))


def _upd():
    bpy.context.view_layer.update()


def _apply(arm, name, q_arm):
    """Rotate bone `name` by armature-space quaternion q_arm, on top of its current pose."""
    _upd()
    pb = arm.pose.bones[name]
    m0 = (arm.pose.bones[name].matrix).to_quaternion()
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = m0.inverted() @ q_arm @ m0


def _in_frame(frame, q):
    return frame @ q @ frame.inverted()


def _loc_world(pb, delta):
    pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(delta)


def reset(arm):
    for name in RESET + list(FOOT.values()):
        pb = arm.pose.bones[name]
        pb.location = (0, 0, 0)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)


def pose(arm, P):
    reset(arm)
    pb = arm.pose.bones
    body = _q(Z, P.get("root_yaw", 0))
    if P.get("root_yaw"):
        _apply(arm, "Root2", body)
    if P.get("hips_drop"):
        _loc_world(pb["Lower_body"], (0, 0, -P["hips_drop"]))
    chest_local = _q(Z, P.get("chest_twist", 0)) @ _q(Y, -P.get("chest_side", 0)) @ _q(X, P.get("chest_lean", 0))
    _apply(arm, "Upper_Body", _in_frame(body, chest_local))
    frame = body @ chest_local                          # arms and head move with the chest
    head_local = _q(Z, P.get("head_turn", 0)) @ _q(Y, -P.get("head_tilt", 0)) @ _q(X, P.get("head_nod", 0))
    _apply(arm, "Head", _in_frame(frame, head_local))
    for side, (shoulder, elbow) in ARM.items():
        a = P.get("arm_" + side, {})
        s = 1 if side == "sl" else -1                   # out = toward -x for the screen-left arm
        sh = _q(Z, a.get("twist", 0) * s) @ _q(X, -a.get("fwd", 0)) @ _q(Y, a.get("out", 0) * s)
        _apply(arm, shoulder, _in_frame(frame, sh))
        # the elbow bends forward in the arm's own frame
        _apply(arm, elbow, _in_frame(frame @ sh, _q(X, -a.get("elbow", 0))))
    for side, name in FOOT.items():
        f = P.get("foot_" + side, {})
        _loc_world(pb[name], (f.get("x", 0), f.get("y", 0), f.get("z", 0)))
        if f.get("yaw"):
            _apply(arm, name, _q(Z, f["yaw"]))
    _upd()
