"""Episode 10 (the finale), part 7: what Null is made of.

They hang from the bridge's stub where part 6 left them. Patch, quiet for once,
his beam on Null: "No... look at what he is made of..." Steve, annoyed, turns,
looks, and the annoyance falls off his face. "Noob... that's you... Every time
you respawn..." While he says it the camera goes to the Noob, who has turned to
look too, and pushes into his eye: Null is mirrored in it. The pupil fills the
frame, the mirror becomes Null himself, we fly at his chest, through his dark
pixels, and inside: every pixel of him is a cell, a smoked glass cube, and in
every cell is a Noob's head (the Noobs of all the loops: today's, the plastic
one, the boxy one, Episode 0's own, the faded ones), smiling, too wide, all
turning to watch us go by; the tunnel opens into a dome of them, and they all
say "Hi!" at once. Black.

The eye is a wet glass dome (faceplate.GLOSSY_EYES), so the reflection is the
real one, traced. The inside of Null (the "soul") is its own set, far under the
world; the shots between are joined by dissolves rendered from both sides.

    python src/lookdev/ep10_p7_reveal.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_p6_fall as P6                                            # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

T = {"a": 0.0, "patch_look": 0.25, "patch_look_end": 3.23, "see": 3.33, "steve_you": 4.73, "steve_you_end": 8.19,
     "dive": 8.19, "end": 12.24, "length": 12.85}
# part 6's own marks (its approved timeline), so the world is where part 6 left it
P6_BEATS = {"a": [0.0, 0.35], "noob_wake": [0.35, 3.1], "run": [3.1, 3.85], "drop": [3.85, 4.75],
            "catch": [4.75, 5.3], "hang": [5.3, 6.3], "patch_omg": [6.3, 9.23], "steve_seen": [9.73, 10.91],
            "steve_delete": [11.06, 13.59], "end": [13.59, 14.09]}
SOUL = Vector((0.0, 0.0, -3000.0))           # inside Null: its own set, far under the world
HI = 11.64                                   # every head: "Hi!" (the chorus's "Hi!", set in align)


# ------------------------------------------------------------------ shots
def t_m():
    """The match: the pupil fills the frame, and Null in it becomes Null in front of him."""
    return T["dive"] + 0.05


def t_f():
    """Into his body (the dark), on into the cells."""
    return t_m() + 1.15


def shots():
    return [("R1", T["patch_look"] + 1.8), ("R2", T["see"] + 0.55), ("R3", T["steve_you"]),
            ("R4", T["steve_you"] + 1.15), ("R5", t_m()), ("F", t_f()),
            ("S1", T["end"]), ("BLACK", 1e9)]


DISSOLVES = [("R5", "F", lambda: (t_m() - 0.1, t_m() + 0.12)),
             ("F", "S1", lambda: (t_f() - 0.12, t_f() + 0.1))]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "BLACK", t0, 1e9


def layers(t):
    """[(shot, weight)] to render and blend at t."""
    for a, b, win in DISSOLVES:
        t0, t1 = win()
        if t0 <= t < t1:
            u = ss(t0, t1, t)
            return [(a, 1 - u), (b, u)]
    return [(which(t)[0], 1.0)]


def span(name):
    t0 = -1.0
    for n, t1 in shots():
        if n == name:
            return t0, t1
        t0 = t1
    return t0, 1e9


# ------------------------------------------------------------------ the build
def build(tl, tex_dir, assets, res, samples):
    import faceplate
    faceplate.GLOSSY_EYES = True
    P6.align({"beats": P6_BEATS, "length": 14.09})
    E = P6.build({}, tex_dir, assets, res, samples)
    E.mouth = {}
    E.t6 = P6_BEATS["end"][1] + 0.4                         # part 6 is over: the world as it left it
    E.tau6 = P6.clock(E.t6)
    for p in E.pieces + E.rainbow:                         # the bridge is gone
        p.place(E.tau6)
    for ob in E.bits + E.px:
        ob.hide_render = True
    E.giz.draw([])
    E.island_world = E.sc.world
    E.force_shot = "R5"
    E.mouth = {}
    cast(E, t_m() - 1e-3)
    bpy.context.view_layer.update()
    loc, look, lens, *_ = camera(E, t_m() - 1e-3, "R5")
    P_, n_ = noob_eye(E), noob_eye_normal(E)
    d_ = (look - loc).normalized()
    E.mirror = {"loc": loc - 2 * (loc - P_).dot(n_) * n_, "dir": (d_ - 2 * d_.dot(n_) * n_).normalized(), "lens": lens}
    E.force_shot = None
    _soul(E, tex_dir)
    return E


def _soul(E, tex_dir):
    """Inside Null: a tunnel of cells opening into a dome of them. Each cell is a
    smoked glass cube with glowing edges (one of his pixels), a Noob head inside."""
    import bmesh
    from noob import build_noob
    from kit.rigs import make_noob
    sc = E.sc
    rng = random.Random(412)
    col = bpy.data.collections.new("soul")
    sc.collection.children.link(col)
    src = bpy.data.collections.new("soul_src")
    sc.collection.children.link(src)
    E.soul_objs = []
    # ---- the heads: one collection per make of him, its origin at the head's centre
    far = Vector((0, 0, -9000))
    E.styles = []
    E.style_faces = []
    E.style_face_mats = []
    makes = [("today", {}), ("plastic", {"finish": "plastic"}), ("box", {"head": "box"}),
             ("faded", {"finish": "plastic"})]
    for k, (nm, kw) in enumerate(makes):
        c = bpy.data.collections.new(f"cell_{nm}")
        src.children.link(c)
        n = build_noob(c, height=2.0, name=f"cellnoob_{nm}", **kw)
        n.root.location = far + Vector((k * 6.0, 0, 0))
        bpy.context.view_layer.update()
        for o in [n.root] + list(n.root.children_recursive):
            if o.type == "MESH" and o is not n.head_mesh and o is not n.face:
                o.hide_render = True
        bb = [n.head_mesh.matrix_world @ Vector(v) for v in n.head_mesh.bound_box]
        hc = sum(bb, Vector()) / 8
        c.instance_offset = hc
        E.style_scale = getattr(E, "style_scale", []) + [0.62 / (max(v.z for v in bb) - min(v.z for v in bb))]
        if nm == "faded":
            P6_ghost = __import__("ep10_p5_dejavu")._ghostify
            P6_ghost([n.head_mesh])
        E.styles.append(c)
        E.style_faces.append(n.face)
        fm = n.face.data.materials[0]
        fm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.4
        n.face_kind = "noob"
    tex = {os.path.splitext(f)[0]: os.path.join(tex_dir, f) for f in os.listdir(tex_dir)}
    old = make_noob(tex, name="cellnoob_old", faces=False)    # Episode 0's own Noob: his painted smile
    c = bpy.data.collections.new("cell_old")
    src.children.link(c)
    old.root.location = far + Vector((30.0, 0, 0))
    bpy.context.view_layer.update()
    head = old.parts["head"]
    for o in head.users_collection:
        pass
    c.objects.link(head)
    for o in old.root.children_recursive:
        if o is not head and o.type == "MESH" and o not in head.children_recursive:
            o.hide_render = True
    for o in head.children_recursive:
        if o.name not in c.objects:
            c.objects.link(o)
    meshes = [o for o in [head] + list(head.children_recursive) if o.type == "MESH"]
    print("OLD HEAD", head.name, head.type, [o.name for o in meshes], flush=True)
    bb = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
    hc = sum(bb, Vector()) / len(bb)
    c.instance_offset = hc
    E.style_scale.append(0.62 / (max(v.z for v in bb) - min(v.z for v in bb)))
    E.styles.append(c)
    print("STYLE SCALES", [round(x, 3) for x in E.style_scale], flush=True)
    E.head_h = 0.62                                         # a head in its cell (m): set by scaling the instances
    # ---- where the cells are: a tunnel along +y, then a dome around its end
    pts = []
    S_ = 1.25
    NT = 14
    for iy in range(0, NT):
        for ix in range(-6, 7):
            for iz in range(-6, 7):
                x, z = ix * S_, iz * S_
                r = math.hypot(x, z)
                if r < 1.3 or r > 5.2:
                    continue
                keep = 0.85 if r < 4 else 0.6
                if rng.random() > keep:
                    continue
                pts.append(Vector((x + rng.uniform(-0.06, 0.06), iy * S_ + rng.uniform(-0.06, 0.06), z)))
    C = Vector((0, NT * S_ + 5.5, 0))
    E.dome_c = C
    for R, dens in ((5.6, 1.0), (6.85, 0.7), (8.1, 0.45)):
        n = int(4 * math.pi * R * R / (S_ * S_) * dens)
        for i in range(n):
            yy = 1 - 2 * (i + 0.5) / n
            rr = math.sqrt(1 - yy * yy)
            th = math.pi * (3 - math.sqrt(5)) * i
            d = Vector((rr * math.cos(th), yy, rr * math.sin(th)))
            # the tunnel's mouth: a hole facing -y
            d2 = Vector((d.x, d.y, d.z))
            if d2.y < -0.86:
                continue
            pts.append(C + Vector((d.x, d.y, d.z)) * R)
    # one cell sits right in the way, just after the way in: the first face we meet
    pts.append(Vector((0.95, 2.6, 0.2)))
    E.first_cell = len(pts) - 1
    E.cells = []
    # ---- the glass cubes (one mesh) and the heads (instances)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    h = 0.5
    for p in pts:
        vs = [bm.verts.new((p.x + dx * h, p.y + dy * h, p.z + dz * h))
              for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                 (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            fc = bm.faces.new([vs[i] for i in f])
            for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                lp[uvl].uv = uv
    me = bpy.data.meshes.new("soul_cells")
    bm.to_mesh(me)
    bm.free()
    cubes = bpy.data.objects.new("soul_cells", me)
    col.objects.link(cubes)
    cubes.location = SOUL
    me.materials.append(_cell_material())
    E.soul_objs.append(cubes)
    for i, p in enumerate(pts):
        st = rng.choices(range(len(E.styles)), weights=(4, 2, 2, 0.6, 2.4))[0]
        if i == E.first_cell:
            st = 0
        em = bpy.data.objects.new(f"cellhead_{i}", None)
        em.instance_type = "COLLECTION"
        em.instance_collection = E.styles[st]
        col.objects.link(em)
        em.location = SOUL + p
        k = E.style_scale[st]
        em.scale = (k, k, k)
        em.rotation_mode = "QUATERNION"
        E.cells.append((em, SOUL + p, rng.uniform(0, 6.28), st))
        E.soul_objs.append(em)
    # ---- light inside him
    E.soul_lights = []

    def lamp(name, kind, loc, power, colr, size=1.0):
        L = bpy.data.lights.new(name, kind)
        L.energy = power
        L.color = colr
        if kind == "AREA":
            L.size = size
        else:
            L.shadow_soft_size = size
        ob = bpy.data.objects.new(name, L)
        col.objects.link(ob)
        ob.location = loc
        E.soul_lights.append(ob)
        E.soul_light_base[name] = power
        return ob
    E.soul_light_base = {}
    E.soul_key = lamp("soul_key", "POINT", SOUL, 240.0, (1.0, 0.88, 0.95), 0.5)
    E.soul_under = lamp("soul_under", "POINT", SOUL, 160.0, (1.0, 0.35, 0.8), 0.6)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        lamp(f"soul_rim_{k}", "POINT", SOUL + C + Vector((5.0 * math.cos(a), rng.uniform(-3, 3), 5.0 * math.sin(a))),
             500.0, (1.0, 0.2, 0.85) if k % 2 else (0.25, 0.85, 1.0), 1.5)
    for k in range(5):
        a = k / 5 * 2 * math.pi + 0.4
        lamp(f"soul_fill_{k}", "POINT", SOUL + C + Vector((1.6 * math.cos(a), -2.5, 1.6 * math.sin(a) - 1.2)),
             1400.0, (1.0, 0.85, 0.7), 1.0)
    for k in range(6):
        lamp(f"soul_tun_{k}", "POINT", SOUL + Vector((rng.uniform(-1, 1), 3 + k * 2.8, rng.uniform(-1, 1))),
             260.0, (1.0, 0.25, 0.85) if k % 2 else (0.3, 0.8, 1.0), 1.0)
    # ---- his own dark (the world inside him)
    w = bpy.data.worlds.new("soul_world")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.006, 0.002, 0.012, 1)
    bg.inputs["Strength"].default_value = 1.0
    w.mist_settings.start = 1.5
    w.mist_settings.depth = 30.0
    E.soul_world = w
    _creepy_faces(E)


def _cell_material():
    """Smoked glass: nearly clear face-on, dark and glossy at grazing angles, its edges glowing faintly."""
    m = bpy.data.materials.new("soul_cell")
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.02, 0.01, 0.03, 1)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Specular IOR Level"].default_value = 0.8
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.86, 0.76, 0.92, 1)
    fr = nt.nodes.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.45
    mxs = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs["Facing"], mxs.inputs[0])
    nt.links.new(tr.outputs[0], mxs.inputs[1])
    nt.links.new(b.outputs[0], mxs.inputs[2])
    # the edges: from the face's UV, near any border
    uv = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])

    def mth(op, a, b_=None):
        n_ = nt.nodes.new("ShaderNodeMath")
        n_.operation = op
        for i, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n_.inputs[i].default_value = v
            else:
                nt.links.new(v, n_.inputs[i])
        return n_.outputs[0]
    u, v = sep.outputs["X"], sep.outputs["Y"]
    d = mth("MINIMUM", mth("MINIMUM", u, mth("SUBTRACT", 1.0, u)), mth("MINIMUM", v, mth("SUBTRACT", 1.0, v)))
    edge = mth("LESS_THAN", d, 0.022)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.18, 0.8, 1)
    em.inputs["Strength"].default_value = 1.3
    mx2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(edge, mx2.inputs[0])
    nt.links.new(mxs.outputs[0], mx2.inputs[1])
    nt.links.new(em.outputs[0], mx2.inputs[2])
    nt.links.new(mx2.outputs[0], out.inputs["Surface"])
    return m


CREEPY = {"both_open": 1.0, "both_h": 1.75, "both_w": 1.12, "both_ps": 0.06, "both_to": 0.12, "both_ti": 0.05,
          "m_w": 3.0, "m_arch": -0.85, "m_o": 0.42, "m_k": 1.35}
HI_FACE = {"m_o": 1.0, "m_w": 2.4, "m_arch": -0.55, "both_h": 1.9, "both_to": 0.0}


def _creepy_faces(E, hi=0.0):
    from faceplate import NOOB_EYES
    vals = dict(CREEPY)
    for k, v in HI_FACE.items():
        vals[k] = lerp(CREEPY.get(k, v), v, hi)
    for f in E.style_faces:
        for k, v in vals.items():
            if k.startswith("both_"):
                for e in NOOB_EYES:
                    f[f"{e}_{k[5:]}"] = v
            else:
                f[k] = v


# ------------------------------------------------------------------ the world per shot
def set_world(E, inside):
    sc = E.sc
    sc.world = E.soul_world if inside else E.island_world
    E.I.void.hide_render = inside
    E.I.sun.hide_render = inside
    for o in E.soul_lights:
        o.hide_render = not inside
    E.key.hide_render = inside


# ------------------------------------------------------------------ per frame
def apply(E, t, shot=None):
    shot = shot or E.force_shot or layers(t)[0][0]
    inside = shot in ("S1", "BLACK")
    set_world(E, inside)
    cast(E, t)
    if inside:
        soul(E, t)
    return camera_set(E, t, shot)


def cast(E, t):
    """Steve and the Noob hanging (one hand each now), Patch and his beam, Null."""
    from pose import pose
    from noob import pose_noob
    from faceplate import set_face, EYES, EYE_DEFAULTS, MOUTH_DEFAULTS, NOOB_EYES, NOOB_EYE_DEFAULTS, NOOB_MOUTH
    from brows import set_brows
    from ep09_new import SF, NF, talk, flat, unflat
    from patch import DEFAULTS as PD, set_patch
    from stage import place_null_lights
    from null import null_smile
    S, N, X, Pt = E.S, E.N, E.X, E.Pt
    deck, XE = E.deck, E.XE
    f_render = int(round(t * FPS)) if getattr(E, "lip_frame", None) is None else E.lip_frame
    lib = json.load(open(os.path.join(HERE, "poses_lib.json")))
    # ------------------------------------------------ Null
    X.root.scale = (1.6,) * 3
    X.root.location = (XE - 26.0, E.Y0 + 7.0, deck - 8.0)
    X.root.rotation_euler = (math.radians(12), 0, math.radians(-90 + 180 + 15))
    X.arms["sl"].rotation_euler = (math.radians(-95), math.radians(10), 0)
    X.forearms["sl"].rotation_euler = (math.radians(-15), 0, 0)
    X.arms["sr"].rotation_euler = (math.radians(-70), math.radians(-10), 0)
    X.orbit.rotation_euler = (math.radians(-10), math.radians(-16), 0.9 * (t + 20))
    X.orbit2.rotation_euler = (math.radians(-12), math.radians(14), -0.6 * (t + 20))
    place_null_lights(X, fade=1.0)
    null_smile(1.0)
    see = ss(T["see"] - 0.05, T["see"] + 0.75, t)
    # ------------------------------------------------ Steve: one hand on the stub, turned out; he turns to Null
    sp = flat(lib["idle (Benly 2.2)"])
    p = json.loads(json.dumps(P6.HANG_S))
    p["arm_sr"] = {"fwd": 172, "out": 4, "elbow": 4}
    p["arm_sl"] = {"fwd": lerp(30, 8, ss(0.0, 1.0, t)), "out": 14, "elbow": 20}
    p["head_nod"] = lerp(-4, -14, see)
    p["head_turn"] = lerp(0, -34, see) if getattr(E, "steve_head", None) is None else E.steve_head[0]
    if getattr(E, "steve_head", None) is not None:
        p["head_nod"] = E.steve_head[1]
    p["chest_lean"] = -6
    p["foot_sl"] = {"y": 0.03 * math.sin(t * 1.3), "z": 0.0}
    p["foot_sr"] = {"y": -0.1, "z": 0.05}
    for k, v in flat(p).items():
        sp[k] = v
    pose(S.arm, unflat(sp))
    sway = 0.012 * math.sin(t * 1.7)
    yaw = 90 - 125 - 22 * see
    S.holder.rotation_euler = (0, 0, math.radians(yaw))
    grip = Vector((E.grip_x, E.lane["S"], deck + 0.07))
    S.holder.location = Vector((XE - 0.3, E.lane["S"], deck - 2.0))
    bpy.context.view_layer.update()
    hc = P6._steve_hand(S, "sr")
    S.holder.location = S.holder.location + (grip - hc) + Vector((0, sway, 0))
    if (E.force_shot or which(t)[0]) in ("R5", "F"):
        S.holder.location = S.holder.location + Vector((0, 0, -60))     # out of the eye's close-up (and its mirror)
    # his face: annoyed (Patch again), then it falls off him
    annoyed = {"both_to": 0.4, "both_tm": 0.42, "both_ti": 0.5, "both_ps": 0.78, "both_py": 0.0,
               "bb_tilt": 0.45, "bb_raise": -0.2, "m_arch": 0.12, "m_w": 1.6}
    horror = {"both_to": -0.25, "both_tm": -0.3, "both_ti": -0.2, "both_ps": 0.5, "both_py": 0.05,
              "bb_tilt": -0.7, "bb_raise": 0.9, "bb_arch": 0.4, "m_arch": 0.32, "m_w": 1.5, "m_o": 0.35}
    face = P6._mixf(annoyed, horror, ss(T["see"] + 0.15, T["see"] + 0.75, t))
    if getattr(E, "steve_face", None) is not None:          # a later part's own face for him
        face = E.steve_face
    fs = {f"{e}_{k}": v for e in EYES for k, v in EYE_DEFAULTS.items()}
    fs.update(MOUTH_DEFAULTS)
    for k, v in face.items():
        if k.startswith("both_"):
            for e in EYES:
                fs[f"{e}_{k[5:]}"] = v
        elif not k.startswith("bb_"):
            fs[k] = v
    # a tremble in the pupils once he sees
    tr = see * 0.04 * math.sin(t * 37.0)
    for e in EYES:
        fs[f"{e}_px"] = fs.get(f"{e}_px", 0.0) + tr
    talk(fs, E.mouth.get("steve", {}).get(f_render))
    set_face(S.face, fs)
    for ob_ in S.brows.values():
        for kb in ob_.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    set_brows(S.brows, {k: v for k, v in face.items() if k.startswith("bb_")})
    # ------------------------------------------------ the Noob: both hands, then one, turned out to look
    q = 1.0                                                # turned out already (part 6), on his left hand
    npz = json.loads(json.dumps(P6.HANG_N))
    npz["arm_sl"] = {"fwd": lerp(172, 10, q), "out": lerp(4, 14, q)}
    npz["arm_sr"] = {"fwd": lerp(172, 218, q), "out": 6}            # turned out: the arm up and back over his head
    npz["head_turn"] = lerp(0, -20, q) if getattr(E, "noob_head", None) is None else E.noob_head[0]
    npz["head_nod"] = lerp(-20, -10, q) if getattr(E, "noob_head", None) is None else E.noob_head[1]
    npz["chest_lean"] = lerp(-8, -4, q)
    npz["leg_sl"] = {"fwd": 4 * math.sin(t * 1.9)}
    npz["leg_sr"] = {"fwd": -4 * math.sin(t * 1.9 + 1)}
    npz["root_yaw"] = 90 + 150 * q
    pose_noob(N, npz)
    gripn = Vector((E.grip_x, E.lane["N"], deck + 0.07))
    N.root.location = Vector((XE - 0.3, E.lane["N"], deck - 2.0))
    bpy.context.view_layer.update()
    sides = ("sl", "sr") if q < 0.05 else ("sr",)
    hn = sum((P6._noob_hand(N, sd) for sd in sides), Vector()) / len(sides)
    N.root.location = N.root.location + (gripn - hn)
    # the eye's close-up: him alone, a step out from the wall, looking straight at Null (his gripping arm up out of frame)
    if E.force_shot == "R5" or (E.force_shot is None and which(t)[0] == "R5"):
        P_eye = Vector((XE - 1.0, E.lane["N"] - 0.2, deck - 0.5))
        npz["head_turn"] = 0.0
        for _ in range(4):
            pose_noob(N, npz)
            bpy.context.view_layer.update()
            N.root.location = N.root.location + (P_eye - noob_eye(E))
            bpy.context.view_layer.update()
            nrm = noob_eye_normal(E)
            v = (null_head(E) - noob_eye(E)).normalized()
            dyaw = math.atan2(v.y, v.x) - math.atan2(nrm.y, nrm.x)
            dyaw = (dyaw + math.pi) % (2 * math.pi) - math.pi
            dpitch = math.asin(max(-1, min(1, v.z))) - math.asin(max(-1, min(1, nrm.z)))
            npz["root_yaw"] += math.degrees(dyaw)
            npz["head_nod"] = max(-40.0, min(30.0, npz["head_nod"] - math.degrees(dpitch)))
            if os.environ.get("AIMDBG"):
                print("AIM", round(npz["root_yaw"], 1), round(math.degrees(N.root.rotation_euler.z), 1),
                      tuple(round(x_, 2) for x_ in nrm), tuple(round(x_, 2) for x_ in v), flush=True)
        pose_noob(N, npz)
        bpy.context.view_layer.update()
        N.root.location = N.root.location + (P_eye - noob_eye(E))
    if E.force_shot == "F" or (E.force_shot is None and which(t)[0] == "F"):
        N.root.location = N.root.location + Vector((0, 0, -80))     # the mirror's own view: not in it
    fn = {f"{e}_{k}": v for e in NOOB_EYES for k, v in NOOB_EYE_DEFAULTS.items()}
    fn.update(MOUTH_DEFAULTS)
    fn.update(NOOB_MOUTH)
    nf = dict(NF["scared"])
    if t >= T["steve_you"] + 0.6:                          # he understands: wide, still, the shine small (the mirror clear)
        u = ss(T["steve_you"] + 0.6, T["steve_you"] + 1.6, t)
        nf = P6._mixf(nf, {"both_h": 1.9, "both_ps": 0.35, "both_open": 1.0, "m_arch": 0.25, "m_w": 1.4, "m_o": 0.1}, u)
    for k, v in nf.items():
        if k.startswith("both_"):
            for e in NOOB_EYES:
                fn[f"{e}_{k[5:]}"] = v
        else:
            fn[k] = v
    if t > t_m() - 0.9:
        for e in NOOB_EYES:
            fn[f"{e}_ps"] = lerp(fn.get(f"{e}_ps", 0.35), 0.06, ss(t_m() - 0.9, t_m() - 0.4, t))
    for e in NOOB_EYES:                                    # looking up at Null
        fn[f"{e}_py"] = 0.25 * q
        fn[f"{e}_px"] = 0.15 * q
    if getattr(E, "noob_face_hook", None) is not None:      # a later part's own face for him
        fn = E.noob_face_hook(fn)
    set_face(N.face, fn)
    # ------------------------------------------------ Patch: by them, his beam on Null
    XEv = Vector((XE, 0, 0))
    home = Vector((XE - 1.75, E.Y0 + 0.5 - 0.2, deck - 0.75))
    loc = home + Vector((0, 0, 0.05 * math.sin(t * 3.0)))
    to_null = (null_head(E) - loc).normalized()
    Pt.root.location = loc
    Pt.root.rotation_euler = (math.radians(-12), 0, math.atan2(-to_null.x, to_null.y) + math.pi)
    for o in Pt.col.objects:
        o.hide_render = False
    vals = dict(PD)
    vals.update({"open": 1.0, "sad": 0.0, "squint": 0.25, "wide": 0.0, "smile": 0.0, "scan": 1.0})
    set_patch(Pt, vals)
    Pt.beam.hide_render = False
    Pt.beam.rotation_euler = (math.radians(E.beam_pitch + 6 * math.sin(t * 2.1)), 0, math.radians(8 * math.sin(t * 1.3)))
    for side in ("l", "r"):
        Pt.fins[side].rotation_euler = (math.radians(14 * math.sin(t * 12.0)), 0, 0)
    E.patch_at = loc


def null_head(E):
    return E.X.head.matrix_world @ (sum((Vector(v) for v in E.X.head.bound_box), Vector()) / 8)


def null_chest(E):
    return E.X.torso.matrix_world.translation + Vector((0, 0, 0)) if hasattr(E.X, "torso") else E.X.root.location


# ------------------------------------------------------------------ the soul
def soul_path(t):
    """The camera's way through him (in the soul's own space): in through the
    tunnel fast, slowing, out into the dome's middle, stopping."""
    t0, t1 = t_f() - 0.14, T["end"] - 0.3
    v = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    y0, y_end = -9.0, 14 * 1.25 + 5.5
    k = 1 - (1 - v) ** 2.6                                   # the flight's speed, bleeding off to a stop
    y = y0 + (y_end - y0) * k
    x = 0.05 + 0.3 * math.sin(v * 6.0) * (1 - v) ** 1.5
    z = 0.12 + 0.18 * math.sin(v * 4.2 + 0.5) * (1 - v) ** 1.5
    return Vector((x, y, z))


def soul(E, t):
    """The heads turn to watch the camera: each looks where the camera was a moment ago."""
    hi = math.exp(-((t - (HI + 0.12)) / 0.16) ** 2) if t < HI + 0.12 else math.exp(-((t - (HI + 0.12)) / 0.3) ** 2)
    _creepy_faces(E, hi)
    up = ss(t_f() - 0.05, t_f() + 0.9, t)
    for ob in E.soul_lights:
        ob.data.energy = E.soul_light_base[ob.name] * (0.08 + 0.92 * up)
    for i, (em, p, ph, st) in enumerate(E.cells):
        d = p.length if False else 0.0
        lag = 0.28 + 0.12 * math.sin(ph)
        target = SOUL + soul_path(t - lag)
        v = target - p
        if v.length < 1e-4:
            continue
        # face along -y in the instance's own frame (the Noob faces -y): turn -y onto v
        q = Vector((0, -1, 0)).rotation_difference(v.normalized())
        tilt = Quaternion((0, 1, 0), 0.26 * math.sin(ph * 3.7) + 0.04 * math.sin(t * 0.7 + ph))
        em.rotation_quaternion = q @ tilt


# ------------------------------------------------------------------ cameras
def camera_set(E, t, shot):
    from ep10_p2_omg import handheld
    bpy.context.view_layer.update()
    loc, look, lens, fstop, focus, amp, roll = camera(E, t, shot)
    y1, p1, r1 = handheld(t, amp)
    q = P6.look_quat(look - loc) @ Quaternion((0, 1, 0), math.radians(y1)) \
        @ Quaternion((1, 0, 0), math.radians(p1)) @ Quaternion((0, 0, 1), math.radians(r1 + roll))
    E.cam.location = loc
    E.cam.rotation_mode = "QUATERNION"
    E.cam.rotation_quaternion = q
    E.cam.data.lens = lens
    E.cam.data.dof.focus_distance = (look - loc).length if focus is None else focus
    E.cam.data.dof.aperture_fstop = fstop
    E.cam.data.clip_start = 0.01 if shot in ("R5",) else 0.05
    if shot not in ("S1", "BLACK"):
        E.key.location = loc + Vector((0.4, 0.0, 1.2))
        E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    else:
        fwd = (look - loc).normalized()
        E.soul_key.location = loc + Vector((0.3, -0.2, 0.5)) + fwd * 0.4
        E.soul_under.location = loc + Vector((0, 0, -0.9)) + fwd * 1.2
    return {"shot": shot}


def camera(E, t, shot):
    XE, deck = E.XE, E.deck
    hs = P6._head(E.S.face, E.S.holder)
    hn = P6._head(E.N.face)
    t0, t1 = span(shot)
    u = ss(t0, t1, t) if t1 < 1e8 else 0.0
    nh = null_head(E)
    if os.environ.get("DBGCAM") and shot not in ("S1", "BLACK"):
        c = Vector((XE - 0.4, E.Y0 + 0.5, deck - 0.8))
        v = {"1": Vector((-4.0, -1.5, 1.2)), "2": Vector((-1.0, 0.0, 6.0))}[os.environ["DBGCAM"]]
        return c + v, c, 28, 16.0, None, 0.0, 0.0
    if shot == "R1":
        # past Patch's shoulder... in front of him, between him and Null: his face and the beam toward us,
        # the two of them hanging on the wall behind him
        pa = E.patch_at
        to_null = (nh - pa).normalized()
        side = to_null.cross(Vector((0, 0, 1))).normalized()
        loc = pa + to_null * (1.25 - 0.15 * u) + side * 0.55 + Vector((0, 0, 0.12))
        look = pa.lerp(hs, 0.35) + Vector((0, 0, -0.05))
        return loc, look, 32, 4.0, (pa - loc).length, 0.25, 0.0
    if shot == "R2":
        # Steve close: annoyed, then he turns to look, and it falls off his face; a slow push
        d = (nh - hs).normalized()
        d = Vector((d.x, d.y, 0)).normalized()
        side = d.cross(Vector((0, 0, 1))).normalized()
        loc = hs + d * lerp(1.15, 0.85, u) - side * 0.35 + Vector((0, 0, -0.05))
        return loc, hs + Vector((0, 0, -0.04)), 45, 2.2, None, 0.18 + 0.4 * ss(T["see"] + 0.2, T["see"] + 0.5, t), 0.0
    if shot == "R3":
        # what he sees: Null in the beam, from beside Steve
        loc = hs + Vector((-0.45, -1.05, 0.55))
        look = nh.lerp(E.X.root.location, 0.25)
        return loc, look, lerp(30, 38, u), 8.0, (look - loc).length, 0.22, 0.0
    if shot == "R4":
        # Steve: "Noob... that's you."
        d = (nh - hs).normalized()
        d = Vector((d.x, d.y, 0)).normalized()
        side = d.cross(Vector((0, 0, 1))).normalized()
        if side.y > 0:                                     # from the side away from the Noob
            side = -side
        loc = hs + d * lerp(0.75, 0.66, u) + side * 0.3 + Vector((0, 0, 0.02))
        return loc, hs + Vector((0, 0, -0.04)), 50, 2.0, None, 0.25, 0.0
    if shot == "R5":
        # the Noob: from Null's side, then in, and in, to his eye; Null mirrored in it
        eye = noob_eye(E)
        d = noob_eye_normal(E)                              # he looks at Null: we stand between, Null behind us
        side = d.cross(Vector((0, 0, 1))).normalized()
        k = ss(t0, t1 + 0.05, t) ** 1.8
        dist = lerp(0.85, 0.035, k)
        off = side * lerp(0.28, 0.006, k) + Vector((0, 0, lerp(-0.05, 0.004, k)))
        loc = eye + d * dist + off
        look = eye.lerp(hn, 0.6 * (1 - k))
        return loc, look, lerp(40, 70, k), lerp(2.8, 22.0, k ** 2), (eye - loc).length, 0.15 * (1 - k), 0.0
    if shot == "F":
        # the mirror's camera: Null in the eye is Null in front of him; then like a bee, faster and faster,
        # weaving a little, straight into his chest
        M = E.mirror
        chest = E.X.root.matrix_world @ Vector((0, -0.4, 7.2))
        s_ = max(0.0, (t - t_m()) / (t_f() - t_m()))
        e = s_ ** 1.75
        start = M["loc"]
        end = chest + (chest - start).normalized() * 1.2
        mid = start.lerp(end, 0.5) + Vector((0, 0, 4.0))          # up and over his builds
        loc = (1 - e) ** 2 * start + 2 * (1 - e) * e * mid + e * e * end
        side = (end - start).normalized().cross(Vector((0, 0, 1))).normalized()
        loc = loc + side * (0.55 * math.sin(math.pi * s_) * math.sin(2.6 * math.pi * s_)) \
            + Vector((0, 0, 0.3 * math.sin(math.pi * s_) * math.sin(1.8 * math.pi * s_ + 0.6)))
        dch = (chest - loc).normalized() if (chest - loc).length > 0.5 else (end - start).normalized()
        d = M["dir"].lerp(dch, ss(0.0, 0.45, s_)).normalized()
        return loc, loc + d * 5.0, lerp(M["lens"], 24, ss(0.0, 0.55, s_)), 16.0, 30.0, 0.0, 0.0
    if shot == "S1":
        p = SOUL + soul_path(t)
        ahead = SOUL + soul_path(t + 0.35) + Vector((0, 1.2, 0))
        settle = ss(T["end"] - 1.2, T["end"] - 0.3, t)
        look = ahead.lerp(p + Vector((0.0, 4.0, 0.3)), settle)
        lens = lerp(24, 30, settle)
        return p, look, lens, 8.0, lerp(3.0, 5.5, settle), 0.0, 4.0 * (1 - settle) * math.sin(t * 1.3)
    # black
    return SOUL + Vector((0, -50, 0)), SOUL + Vector((0, -60, 0)), 30, 9.0, None, 0.0, 0.0


def noob_eye_normal(E):
    noob_eye(E)
    f = E.N.face
    n = (f.matrix_world.to_3x3() @ f.data.vertices[E._eye_vert].normal).normalized()
    hc = E.N.head_mesh.matrix_world @ (sum((Vector(v) for v in E.N.head_mesh.bound_box), Vector()) / 8)
    if n.dot(noob_eye(E) - hc) < 0:                        # outward, away from his head
        n = -n
    return n


def noob_eye(E):
    """The Noob's eye nearer the camera (his screen-left eye on the plate), in the world."""
    f = E.N.face
    from faceplate import NOOB_EYES, NOOB_EYE_DEFAULTS
    # the plate's UV 0..1 = the 8 x 8 face grid; the eye's centre in grid units
    cx = NOOB_EYES["eL"] + f.get("eL_px", 0.0) * 0.28
    cy = f.get("eL_cy", NOOB_EYE_DEFAULTS["cy"]) + f.get("eL_py", 0.0) * 0.22
    me = f.data
    # find the plate vertex whose UV is nearest the eye centre
    if not hasattr(E, "_eye_vert"):
        uvs = me.uv_layers.active.data
        best, bi = 1e9, 0
        for lp in me.loops:
            uv = uvs[lp.index].uv
            d = (uv.x * 8 - cx) ** 2 + (uv.y * 8 - cy) ** 2
            if d < best:
                best, bi = d, lp.vertex_index
        E._eye_vert = bi
    return f.matrix_world @ me.vertices[E._eye_vert].co


# ------------------------------------------------------------------ the look
def finish(path, mist_path, shot, t=0.0):
    if shot == "F":
        import numpy as np
        from PIL import Image
        P4.finish(path, mist_path)
        im = Image.open(path).convert("RGB").transpose(Image.FLIP_LEFT_RIGHT)
        a = np.asarray(im, np.float32) / 255.0
        g = lerp(0.5, 1.0, ss(t_m(), t_m() + 0.55, t))
        a = a * np.array([g * 0.95, g * 0.93, g * 1.02], np.float32)
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)
    elif shot in ("S1",):
        _finish_soul(path, mist_path)
    elif shot == "BLACK":
        from PIL import Image
        im = Image.open(path)
        Image.new("RGB", im.size, (0, 0, 0)).save(path)
    else:
        P4.finish(path, mist_path)


def _finish_soul(path, mist_path):
    """Inside him: the far cells sink into a dark violet, a little bloom on the edges, grain."""
    import numpy as np
    from PIL import Image, ImageFilter
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, np.float32) / 255.0
    h, w = a.shape[:2]
    if os.path.exists(mist_path):
        m = np.asarray(Image.open(mist_path).convert("L").resize((w, h)), np.float32) / 255.0
        fog = np.clip((m - 0.05) / 0.5, 0, 1) ** 1.3
        a = a * (1 - 0.75 * fog[..., None]) + np.array([0.03, 0.006, 0.05], np.float32) * 0.75 * fog[..., None]
    hi = np.clip((a - 0.55) / 0.45, 0, 1)
    bl = np.asarray(Image.fromarray((hi * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(2, w // 70))),
                    np.float32) / 255.0
    a = a + 0.5 * bl
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    a *= (1 - 0.5 * np.clip((r - 0.45) / 0.7, 0, 1) ** 1.3)[..., None]
    a += np.random.default_rng(int(os.path.basename(path)[:4] or 0)).normal(0, 0.012, (h, w, 1)).astype(np.float32)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ main
def align(tl):
    global HI
    b = tl.get("beats", {})
    for k in ("a", "see", "dive", "end"):
        if k in b:
            T[k] = b[k][0]
    for ln in tl.get("lines", []):
        if ln.get("name") == "patch_look":
            T["patch_look"], T["patch_look_end"] = ln["start"], ln["end"]
        if ln.get("name") == "steve_you":
            T["steve_you"], T["steve_you_end"] = ln["start"], ln["end"]
    if "patch_look" in b:
        T["patch_look"], T["patch_look_end"] = b["patch_look"]
    if "steve_you" in b:
        T["steve_you"], T["steve_you_end"] = b["steve_you"]
    if b:
        T["length"] = tl["length"] + 0.4
    HI = T["steve_you_end"] - 1.0 + 4.45                     # the chorus starts 1 s before his line ends


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
    import numpy as np
    from PIL import Image
    for f in frames:
        dst = os.path.join(out, f"{f:04d}.png")
        if os.path.exists(dst) and not a.times:
            continue
        t = (f - 1) / FPS
        parts = []
        for shot, wgt in layers(t):
            if wgt < 0.003:
                continue
            if shot == "BLACK":
                parts.append((None, wgt))
                continue
            E.force_shot = shot
            sc.frame_set(f)
            apply(E, t, shot)
            p = dst if len(parts) == 0 and len(layers(t)) == 1 else dst[:-4] + f"_{shot}.png"
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            cand = sorted((os.path.join(mist_dir, x) for x in os.listdir(mist_dir)), key=os.path.getmtime)
            finish(p, cand[-1] if cand else "", shot, t)
            for x in cand:
                os.remove(x)
            parts.append((p, wgt))
        E.force_shot = None
        if len(parts) != 1 or parts[0][0] != dst:
            acc = None
            for p, wgt in parts:
                if p is None:
                    continue
                a_ = np.asarray(Image.open(p).convert("RGB"), np.float32)
                acc = a_ * wgt if acc is None else acc + a_ * wgt
                if p != dst:
                    os.remove(p)
            if acc is None:
                w_, h_ = sc.render.resolution_x, sc.render.resolution_y
                acc = np.zeros((h_, w_, 3), np.float32)
            Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).save(dst)
        print("FRAME", f, flush=True)


if __name__ == "__main__":
    main()
