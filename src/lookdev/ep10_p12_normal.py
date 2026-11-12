"""Episode 10 (the finale), part 12: back to normal.

Through Steve's eyes, in slow motion: the Noob falling away into the void on his
back, the cell held in both hands against his chest, smaller and smaller. Close
on the cell at his chest as he falls: "Now I can bring everything back to
normal." He presses it into his heart; it sinks in; light comes out of him,
more and more, until it swallows him. And the world comes back: a ring of light
races out, and behind it the world rises block by block out of the void (the
world of the upgrade episode, ep09_new / world.build_world, with its own
upgrade wave), the sky going gold.

    python src/lookdev/ep10_p12_normal.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_p10_player as P10                                        # noqa: E402
import ep10_p7_reveal as P7                                          # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

G = 9.81
T = {"pov": 0.0, "cu": 3.2, "noob_normal": 3.6, "noob_normal_end": 6.4, "insert": 6.6, "respawn": 8.4,
     "end": 13.0, "length": 13.6}
WORLD_AT = Vector((0.0, 0.0, -1500.0))                        # the world that comes back: its own place, far under


def shots():
    return [("POV", T["cu"]), ("CU", T["insert"] + 1.25), ("LIGHT", T["respawn"]), ("RESPAWN", 1e9)]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "RESPAWN", t0, 1e9


def clock(t):
    """Slow motion through the fall (the world at 0.4), real time from the light on."""
    return 0.4 * t


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    E = P10.build(tl, tex_dir, assets, res, samples)
    sc = E.sc
    E.island_world = sc.world
    # the world that comes back (the upgrade episode's), far under everything, with its wave
    from world import build_world, add_world_fx, SKY_GOLDEN, set_sky, set_sun
    island_objs = set(bpy.data.objects)
    cfg = {"seed": 7, "sun": (140, 16)}
    E.W = W = build_world(sc, assets, cfg)
    E.world_objs = [o for o in bpy.data.objects if o not in island_objs and o.parent is None]
    for o in E.world_objs:
        o.location = o.location + WORLD_AT
    _void_fx(W)
    E.respawn_world = sc.world
    sc.world = E.island_world
    gold = dict(SKY_GOLDEN, fill=1.1, fill_col=(176, 204, 240))
    set_sky(W, gold)
    set_sun(W, 140, 16, 6.2, (1.0, 0.76, 0.5))
    W.sun.hide_render = True
    E.wave_ring = _ring(sc)
    # the light in him: a glow inside his chest, and a star that swallows him
    L = bpy.data.lights.new("heart_light", "POINT")
    L.color = (1.0, 0.85, 0.55)
    L.shadow_soft_size = 0.2
    L.energy = 0.0
    E.heart = bpy.data.objects.new("heart_light", L)
    sc.collection.objects.link(E.heart)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(0, 0, -900))
    E.star = bpy.context.active_object
    E.star.name = "heart_star"
    m = bpy.data.materials.new("heart_star")
    m.use_nodes = True
    nt = m.node_tree
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.86, 0.6, 1)
    em.inputs["Strength"].default_value = 30.0
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    E.star.data.materials.append(m)
    E.star.visible_shadow = False
    # his fall: from where part 11 left him (just under the stub, out from the wall), on his back
    E.fall0 = Vector((E.XE - 1.6, E.lane["N"] + 0.6, E.deck - 2.6))
    return E


def _ring(sc):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=96, radius1=1.0, radius2=1.0, depth=0.25)
    me = bpy.data.meshes.new("respawn_ring")
    bm.to_mesh(me)
    bm.free()
    m = bpy.data.materials.new("respawn_ring")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.82, 0.45, 1)
    b.inputs["Emission Strength"].default_value = 8.0
    me.materials.append(m)
    ob = bpy.data.objects.new("respawn_ring", me)
    sc.collection.objects.link(ob)
    ob.visible_shadow = False
    ob.hide_render = True
    return ob


def _void_fx(W):
    """The upgrade wave, from nothing: inside R the world stands whole; a band Wd wide rises into place;
    outside it there is no world at all (the void)."""
    g = bpy.data.node_groups.new("respawn_fx", "GeometryNodeTree")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nme in ("R", "Wd", "Cx", "Cy", "veg"):
        g.interface.new_socket(nme, in_out="INPUT", socket_type="NodeSocketFloat")
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nd, L = g.nodes, g.links.new
    gi, go = nd.new("NodeGroupInput"), nd.new("NodeGroupOutput")

    def m_(op, a, b=None):
        n = nd.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    pos = nd.new("GeometryNodeInputPosition").outputs[0]
    sep = nd.new("ShaderNodeSeparateXYZ")
    L(pos, sep.inputs[0])
    X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    ta = nd.new("GeometryNodeInputNamedAttribute")
    ta.data_type = "FLOAT"
    ta.inputs["Name"].default_value = "top"
    top = ta.outputs["Attribute"]
    # block by block: the distance of the block's own column (x, y floored), not of each vertex
    bx = m_("ADD", m_("FLOOR", m_("SUBTRACT", X, 0.001)), 0.5)
    by = m_("ADD", m_("FLOOR", m_("SUBTRACT", Y, 0.001)), 0.5)
    dx = m_("SUBTRACT", bx, gi.outputs["Cx"])
    dy = m_("SUBTRACT", by, gi.outputs["Cy"])
    d = m_("SQRT", m_("ADD", m_("MULTIPLY", dx, dx), m_("MULTIPLY", dy, dy)))
    f = m_("DIVIDE", m_("SUBTRACT", gi.outputs["R"], d), m_("MAXIMUM", gi.outputs["Wd"], 0.01))
    f = m_("MINIMUM", m_("MAXIMUM", f, 0.0), 1.0)
    f = m_("MULTIPLY", m_("MULTIPLY", f, f), m_("SUBTRACT", 3.0, m_("MULTIPLY", f, 2.0)))
    # rising: the ground comes up from below its place (by its own height, plus 6 m), vegetation grows
    lift = m_("ADD", top, 6.0)
    z_terr = m_("SUBTRACT", Z, m_("MULTIPLY", lift, m_("SUBTRACT", 1.0, f)))
    z_veg = m_("MULTIPLY", Z, f)
    vw = gi.outputs["veg"]
    z_new = m_("ADD", m_("MULTIPLY", z_terr, m_("SUBTRACT", 1.0, vw)), m_("MULTIPLY", z_veg, vw))
    com = nd.new("ShaderNodeCombineXYZ")
    L(X, com.inputs[0])
    L(Y, com.inputs[1])
    L(z_new, com.inputs[2])
    cap = nd.new("GeometryNodeCaptureAttribute")
    cap.domain = "FACE"
    L(gi.outputs["Geometry"], cap.inputs["Geometry"])
    try:
        cap.capture_items.new("FLOAT", "gone")
    except Exception:
        pass
    L(m_("LESS_THAN", f, 0.004), cap.inputs["gone"])
    sp = nd.new("GeometryNodeSetPosition")
    L(cap.outputs["Geometry"], sp.inputs["Geometry"])
    L(com.outputs[0], sp.inputs["Position"])
    dg = nd.new("GeometryNodeDeleteGeometry")
    dg.domain = "FACE"
    L(sp.outputs[0], dg.inputs["Geometry"])
    L(cap.outputs["gone"], dg.inputs["Selection"])
    L(dg.outputs[0], go.inputs[0])
    ids = {it.name: it.identifier for it in g.interface.items_tree if it.item_type == "SOCKET" and it.in_out == "INPUT"}
    W.vfx = []
    for ob, veg in ((W.terrain, 0), (W.logs, 1), (W.leaves, 1), (W.far, 0), (W.plants, 1)):
        md = ob.modifiers.new("respawn_fx", "NODES")
        md.node_group = g
        W.vfx.append((ob, md, veg))
    W.vfx_ids = ids


def void_fx_set(W, R, Wd, cx, cy):
    for ob, md, veg in W.vfx:
        ins = md.properties.inputs
        for k, v in (("R", R), ("Wd", Wd), ("Cx", cx), ("Cy", cy), ("veg", veg)):
            getattr(ins, W.vfx_ids[k]).value = float(v)
        ob.update_tag()


# ------------------------------------------------------------------ per frame
def noob_fall(E, t):
    """On his back, the cell at his chest in both hands; down and away from Steve, slowly turning."""
    from noob import pose_noob
    N = E.N
    tau = clock(t)
    ins = ss(T["insert"], T["insert"] + 0.9, t)
    pz = {"chest_lean": 0, "head_nod": lerp(-18, -8, ins), "arm_sl": {"fwd": lerp(70, 40, ins), "out": -12},
          "arm_sr": {"fwd": lerp(70, 40, ins), "out": -12}, "leg_sl": {"fwd": 22 + 6 * math.sin(t * 0.9)},
          "leg_sr": {"fwd": 8 + 6 * math.sin(t * 0.9 + 1.4)}, "root_yaw": 0}
    pose_noob(N, pz)
    yaw = math.radians(20 + 6 * t)
    N.root.rotation_euler = (math.radians(-78 + 4 * math.sin(t * 0.6)), math.radians(8 * math.sin(t * 0.4)), yaw)
    drop = 0.5 * G * (tau + 0.35) ** 2 - 0.5 * G * 0.35 ** 2
    N.root.location = E.fall0 + Vector((-0.6 * tau, 0.25 * tau, -drop))
    bpy.context.view_layer.update()
    # the cell between his hands, at his chest; into him on the insert
    hl, hr = P7.P6._noob_hand(N, "sl"), P7.P6._noob_hand(N, "sr")
    chest = N.torso.matrix_world @ Vector((0, 0, 1.2))
    held = 0.5 * (hl + hr)
    c = held.lerp(chest, ins)
    k = (1 - ins) + 0.0001
    E.cell.location = c
    E.cell.scale = (k, k, k)
    E.cell.rotation_quaternion = Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), math.radians(-78))
    E.cell_head.location = c
    hs_ = E.style_scale[0] * P10.CELL_K * k
    E.cell_head.scale = (hs_, hs_, hs_)
    E.cell_head.rotation_quaternion = Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), math.radians(-78 + 90))
    E.cell.hide_render = E.cell_head.hide_render = ins >= 0.999
    E.cell_glow.location = c
    E.cell_glow.data.energy = 5.0 * (1 - ins)
    # the light in him
    glow = ss(T["insert"] + 0.4, T["respawn"], t)
    E.heart.location = chest + Vector((0, 0, 0.2))
    E.heart.data.energy = 4000.0 * glow ** 2
    r = 0.05 + 3.5 * glow ** 3
    E.star.location = chest
    E.star.scale = (r, r, r)
    E.star.hide_render = glow < 0.02
    E.chest = chest


def faces(E, t):
    from faceplate import NOOB_EYES
    from ep09_new import talk
    f_render = int(round(t * FPS))
    calm = {"both_h": 1.5, "both_ps": 1.0, "both_to": 0.35, "both_tm": 0.3, "both_ti": 0.2, "m_arch": -0.45,
            "m_w": 1.9, "m_o": 0.0}
    closed = dict(calm, both_open=lerp(1.0, 0.0, ss(T["insert"] + 0.3, T["insert"] + 0.8, t)))

    def hook(fn):
        for k, v in closed.items():
            if k.startswith("both_"):
                for e in NOOB_EYES:
                    fn[f"{e}_{k[5:]}"] = v
            else:
                fn[k] = v
        for e in NOOB_EYES:
            fn[f"{e}_py"] = 0.3
        talk(fn, E.mouth.get("noob", {}).get(f_render))
        return fn
    E.noob_face_hook = hook
    E.noob_head = (0, -10)
    E.steve_face = {"both_to": -0.35, "both_tm": -0.35, "both_ti": -0.3, "both_ps": 0.45, "bb_tilt": -0.9,
                    "bb_raise": 1.0, "m_arch": 0.3, "m_w": 1.5, "m_o": 0.3}
    E.steve_head = (-30, 30)


def apply(E, t):
    shot = which(t)[0]
    respawn = shot == "RESPAWN"
    faces(E, t)
    E.force_shot = "R1"
    E.lip_frame = int(round(t * FPS))
    P7.cast(E, P7.T["dive"] - 2.6)
    E.force_shot = None
    E.X.root.location = (0, 0, -3000.0)
    E.X.root.scale = (0.001,) * 3
    E.Pt.root.location = (0, 0, -500)
    for o in E.Pt.col.objects:
        o.hide_render = True
    noob_fall(E, t)
    for ob, p0, v, w in E.drifters:
        ob.hide_render = respawn
    # the world: the island's own sky and void until the light; then the world that comes back
    E.sc.world = E.respawn_world if respawn else E.island_world
    E.I.sun.hide_render = respawn
    E.W.sun.hide_render = not respawn
    E.I.void.hide_render = respawn
    s = max(0.0, t - T["respawn"])
    u = s / 4.0
    R = 1.5 + 260.0 * u ** 1.9 if u < 1 else 1e5
    void_fx_set(E.W, R, 4.0 + 0.1 * min(R, 400), WORLD_AT.x, WORLD_AT.y)
    E.wave_ring.hide_render = not respawn or u >= 1
    if not E.wave_ring.hide_render:
        E.wave_ring.scale = (R, R, 1.0)
        E.wave_ring.location = WORLD_AT + Vector((0, 0, 9.0))
    if hasattr(E.W, "water"):
        E.W.water.hide_render = not respawn or R < 60
    for ob in getattr(E.W, "particles", []):
        ob.hide_render = not respawn or R < 30
    if hasattr(E.W, "clouds"):
        E.W.clouds.hide_render = not respawn
    return camera_set(E, t, shot)


# ------------------------------------------------------------------ cameras
def camera_set(E, t, shot):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    loc, look, lens, fstop, focus, amp, roll = camera(E, t, shot)
    y1, p1, r1 = handheld(t, amp)
    q = P7.P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1 + roll))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.cam.data.clip_end = 5000
    E.key.location = loc + Vector((0.4, 0.0, 1.2))
    E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    return {"shot": shot}


def camera(E, t, shot):
    N = E.N
    hs = P7.P6._head(E.S.face, E.S.holder)
    t0, t1 = which(t)[1:]
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, T["end"], t)
    chest = getattr(E, "chest", N.root.location)
    if shot == "POV":
        # his eyes: down past the stub's face at the Noob, falling away on his back
        eye = hs + Vector((-0.28, 0.0, 0.05))
        return eye, chest, lerp(32, 45, u), 6.0, (chest - eye).length, 0.25, 0.0
    if shot == "CU":
        # with him, close over his chest: the cell in his hands, his face beyond; then into him, the light
        head = P7.P6._head(N.face)
        up = Vector((0, 0, 1))                               # he lies on his back: his front is up
        toh = (head - chest)
        toh = Vector((toh.x, toh.y, 0)).normalized()
        side = toh.cross(up).normalized()
        loc = chest + up * lerp(1.75, 1.5, u) - toh * 0.2 + side * 0.45
        look = chest.lerp(head, 0.45)
        return loc, look, 34, 2.6, (look - loc).length, 0.06, 0.0
    if shot == "LIGHT":
        # Steve's eyes again: far below now, the light in him growing until it swallows everything
        eye = hs + Vector((-0.28, 0.0, 0.05))
        return eye, chest, lerp(45, 60, u), 6.0, (chest - eye).length, 0.15, 0.0
    # RESPAWN: high over the world coming back, the ring racing out, the land rising behind it
    c = WORLD_AT + Vector((0, 0, 10))
    loc = c + Vector((-30.0 + 6 * u, -70.0 + 8 * u, 46.0 - 8 * u))
    return loc, c + Vector((0, 12.0 * u, 0)), 30, 16.0, None, 0.03, 0.0


# ------------------------------------------------------------------ the look
def finish(path, mist_path, shot, t):
    import numpy as np
    from PIL import Image
    P4.finish(path, mist_path)
    # the light swallows the picture before the world comes back; it fades out of white after
    w_in = ss(T["respawn"] - 0.9, T["respawn"], t) if t < T["respawn"] else 0.0
    w_out = 1 - ss(T["respawn"], T["respawn"] + 0.9, t) if t >= T["respawn"] else 0.0
    w = max(w_in, w_out)
    if w > 0:
        im = Image.open(path).convert("RGB")
        a = np.asarray(im, np.float32) / 255.0
        a = a + (np.array([1.0, 0.95, 0.85], np.float32) - a) * w
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    for k in ("pov", "cu", "insert", "respawn", "end"):
        if k in b:
            T[k] = b[k][0]
    if "noob_normal" in b:
        T["noob_normal"], T["noob_normal_end"] = b["noob_normal"]
    if b:
        T["length"] = tl["length"] + 0.4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("voice")
    ap.add_argument("tex_dir")
    ap.add_argument("assets")
    ap.add_argument("out_dir")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--res", type=int, default=1080)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--times")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    tl = {"length": T["length"] - 0.4, "beats": {}, "lines": []} if a.timeline == "-" else json.load(open(a.timeline))
    align(tl)
    n_frames = int(round(T["length"] * FPS)) + 1
    if a.list:
        print(json.dumps({"frames": list(range(1, n_frames + 1)), "count": n_frames}))
        return
    E = build(tl, a.tex_dir, a.assets, a.res, a.samples)
    E.force_shot = None
    E.mouth = {}
    if a.timeline != "-" and os.path.exists(a.voice):
        from ep09_new import _lipsync
        E.mouth = _lipsync(tl, a.voice)
    sc = E.sc
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    mist_dir = os.path.join(out, "_mist")
    os.makedirs(mist_dir, exist_ok=True)
    of = sc.compositing_node_group.nodes[sc["mist_node"]]
    of.directory = mist_dir + os.sep
    of.file_name = "m"

    def handler(scene, depsgraph=None):
        apply(E, (scene.frame_current + scene.frame_subframe - 1) / FPS)

    bpy.app.handlers.frame_change_pre.append(handler)
    if a.times:
        frames = [int(round(float(x) * FPS)) + 1 for x in a.times.split(",")]
    else:
        frames = list(range(1, n_frames + 1))
        k, n = (int(x) for x in a.shard.split("/"))
        per = (len(frames) + n - 1) // n
        frames = frames[k * per:(k + 1) * per]
    print("rendering", len(frames), "frames")
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not a.times:
            continue
        t = (f - 1) / FPS
        sc.frame_set(f)
        look = apply(E, t)
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True)
        cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
        finish(dst, cand[-1] if cand else "", look["shot"], t)
        for x in cand:
            os.remove(x)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
