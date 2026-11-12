"""Episode 10 (the finale), part 9: the death of Null.

"I never came back for you guys... sorry." Inside Null, the cells hear it: the
Noobs of every loop, in their glass pixels, cry (their faces fall, black pixel
tears run). Outside, Null's face breaks like a program error: his copied smile
and an upset mouth flicker against each other, faster and faster, his pixels
jitter and tear, black pixel tears run from his eyes and break into cubes, a
sob comes out of him in pieces. The three of them watch, his light strobing on
their faces. Then, seen from far off, he blows apart: every pixel of him (a
cell, a face) flies out through the void in slow motion and goes out, one by
one, like dying stars; his great checkered head is left, and falls, slowly,
turning, its smile fading, down into the void.

The set is part 7's (the island, the soul); the explosion moves every cube of
his body mesh on its own (the meshes are cubes of 8 vertices each).

    python src/lookdev/ep10_p9_death.py TIMELINE VOICE TEX ASSETS OUT [--shard k/n] [--res 1080] [--times ...]
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import ep10_p7_reveal as P7                                          # noqa: E402
import ep10_p4_build as P4                                           # noqa: E402
from ep10_entrance import FPS, lerp, ss, back_out                    # noqa: E402

T = {"cells_cry": 0.0, "null_glitch": 2.6, "heroes": 5.8, "boom": 6.8, "drift": 7.6, "fall": 10.2,
     "end": 13.6, "length": 14.6}
P7_TL = {"beats": {"a": [0.0, 0.25], "patch_look": [0.25, 3.23], "see": [3.33, 4.73], "steve_you": [4.73, 8.75],
                   "dive": [8.75, 12.8], "end": [12.8, 13.0]}, "lines": [], "length": 13.0}
UPSET = ["..##....##..", "..##....##..", "..##....##..", "..##....##..", "............", "...######...",
         "..########..", ".##......##.", ".#........#."]


# ------------------------------------------------------------------ shots
def shots():
    return [("CELLS", T["null_glitch"]), ("FACE", T["heroes"]), ("HEROES", T["boom"]), ("FAR", T["fall"]),
            ("FALL", 1e9)]


def which(t):
    t0 = -1.0
    for name, t1 in shots():
        if t < t1:
            return name, t0, t1
        t0 = t1
    return "FALL", t0, 1e9


# ------------------------------------------------------------------ build
def build(tl, tex_dir, assets, res, samples):
    P7.align(P7_TL)
    E = P7.build(P7_TL, tex_dir, assets, res, samples)
    E.mouth = {}
    rng = random.Random(9)
    _upset_face(E)
    _cell_tears(E, rng)
    _explosion_setup(E, rng)
    # his own light on them (strobing as he breaks)
    L = bpy.data.lights.new("null_strobe", "POINT")
    L.color = (1.0, 0.25, 0.9)
    L.shadow_soft_size = 3.0
    E.strobe = bpy.data.objects.new("null_strobe", L)
    E.sc.collection.objects.link(E.strobe)
    # his black tears: a pool of small dark cubes (placed per frame)
    E.ntears = []
    m = bpy.data.materials.new("null_tear")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.004, 0.003, 0.006, 1)
    b.inputs["Roughness"].default_value = 0.15
    b.inputs["Specular IOR Level"].default_value = 0.9
    for k in range(60):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -900))
        ob = bpy.context.active_object
        ob.name = f"null_tear_{k}"
        ob.data.materials.append(m)
        ob.hide_render = True
        E.ntears.append(ob)
    E.ntear_specs = []
    for k in range(60):
        side = -1 if k % 2 else 1
        E.ntear_specs.append((side, rng.uniform(0, 1), rng.uniform(0.4, 1.0), rng.uniform(-0.15, 0.15)))
    return E


def _upset_face(E):
    """A second drawing on his face (the copied smile turned upside down), and a switch between them."""
    m = bpy.data.materials["null_head"]
    nt = m.node_tree
    st = next(n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and n.image.name.startswith("null_smile"))
    px = np.zeros((38, 31, 4), np.float32)
    px[..., 3] = 1
    for r, row in enumerate(UPSET):
        for c, ch in enumerate(row):
            if ch != ".":
                px[9 + 2 * r:11 + 2 * r, 3 + 2 * c:5 + 2 * c, 0] = 1.0
    im = bpy.data.images.new("null_upset", 31, 38, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(px[::-1].ravel())
    im.pack()
    up = nt.nodes.new("ShaderNodeTexImage")
    up.image, up.interpolation, up.extension = im, "Closest", "CLIP"
    nt.links.new(st.inputs["Vector"].links[0].from_socket, up.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "FLOAT"
    mx.inputs[0].default_value = 0.0
    out_link = st.outputs["Color"].links[0]
    dest = out_link.to_socket
    nt.links.new(st.outputs["Color"], mx.inputs[2])
    nt.links.new(up.outputs["Color"], mx.inputs[3])
    nt.links.new(mx.outputs[0], dest)
    m["upset"] = mx.name


def null_upset(amount):
    m = bpy.data.materials["null_head"]
    m.node_tree.nodes[m["upset"]].inputs[0].default_value = amount


def _cell_tears(E, rng):
    """In every cell's head, two black pixel tears under the eyes (shared by every copy of that head)."""
    from faceplate import NOOB_EYES
    E.cell_tears = []
    m = bpy.data.materials.get("null_tear") or bpy.data.materials.new("cell_tear")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.004, 0.003, 0.006, 1)
    b.inputs["Roughness"].default_value = 0.15
    for st_col, face in zip(E.styles, E.style_faces):
        me = face.data
        uvs = me.uv_layers.active.data
        for e in NOOB_EYES:
            cx = NOOB_EYES[e]
            cy = face.get(f"{e}_cy", 4.5) - 1.0
            best, bi = 1e9, 0
            for lp in me.loops:
                uv = uvs[lp.index].uv
                d = (uv.x * 8 - cx) ** 2 + (uv.y * 8 - cy) ** 2
                if d < best:
                    best, bi = d, lp.vertex_index
            p = face.matrix_world @ me.vertices[bi].co
            n = (face.matrix_world.to_3x3() @ me.vertices[bi].normal).normalized()
            for j in range(3):
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=p)
                ob = bpy.context.active_object
                ob.name = f"cell_tear_{st_col.name}_{e}_{j}"
                ob.data.materials.append(m)
                for c_ in ob.users_collection:
                    c_.objects.unlink(ob)
                st_col.objects.link(ob)
                hs = 0.05 * face.matrix_world.to_scale().x
                ob.scale = (hs, hs * 0.6, hs)
                E.cell_tears.append((ob, p.copy(), n, j, hs))


def _explosion_setup(E, rng):
    """Every cube of his body, as data: its 8 vertices, its centre, where it flies, how it turns, when it goes out."""
    X = E.X
    E.boom_parts = []
    for ob in X.root.children_recursive:
        if ob.type != "MESH" or not ob.name.startswith(("null_torso_vox", "null_upper_", "null_fore_",
                                                          "null_head_noise", "null_streaks")):
            continue
        me = ob.data
        n = len(me.vertices)
        if n % 8:
            continue
        co = np.zeros(n * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 8, 3)
        cen = co.mean(axis=1)
        k = len(cen)
        r = np.random.default_rng(abs(hash(ob.name)) % 2 ** 32)
        E.boom_parts.append({"ob": ob, "co": co.copy(), "cen": cen, "dir": r.normal(0, 1, (k, 3)).astype(np.float32),
                             "speed": r.uniform(0.6, 1.0, k).astype(np.float32) ** 2,
                             "axis": r.normal(0, 1, (k, 3)).astype(np.float32),
                             "spin": r.uniform(1.0, 6.0, k).astype(np.float32),
                             "die": r.uniform(0.0, 1.0, k).astype(np.float32)})
    print("BOOM cubes", sum(len(p["cen"]) for p in E.boom_parts), flush=True)


# ------------------------------------------------------------------ per frame
def apply(E, t):
    shot = which(t)[0]
    inside = shot == "CELLS"
    for o in (getattr(E.X, "orbit", None), getattr(E.X, "orbit2", None)):     # the orbits out of his close-up
        if o is not None and t < T["boom"]:
            for ch in o.children_recursive:
                ch.hide_render = shot == "FACE"
    P7.set_world(E, inside)
    E.force_shot = "R1"                                    # where they hang (not the eye's close-up staging)
    P7.cast(E, P7.T["dive"] - 2.6)                         # the island, the three of them, Patch: as part 8 left them
    E.force_shot = None
    E.Pt.beam.hide_render = True
    null(E, t)
    if inside:
        cells(E, t)
    return camera_set(E, t, shot)


def cast_heroes(E, t):
    """Back where they hang (not the eye's close-up staging): both one-handed, turned out to Null."""
    pass


def null(E, t):
    """His face breaking, his tears, the jitter; then the explosion and the head's fall."""
    from null import null_smile, cells_look
    X = E.X
    g0, g1 = T["null_glitch"], T["boom"]
    err = ss(g0 + 0.3, g1, t)                                # how far gone the error is
    # the error loop: smile / upset, faster and faster (a program stuck between two states)
    if t < g0 + 0.25:
        up = 0.0
    elif t < g1:
        f = lerp(1.5, 16.0, err ** 1.5)
        ph = (t - g0) * f + 3.0 * math.sin(t * 3.7) * err
        up = 1.0 if (ph % 1.0) > lerp(0.75, 0.5, err) else 0.0
        if (t * 41.3) % 1.0 < 0.08 * err:                    # a dropped frame: neither
            up = 0.5
    else:
        up = 1.0
    null_upset(up)
    smile = 1.0 if t < T["boom"] + 2.0 else 1.0 - ss(T["fall"], T["end"] - 0.6, t)
    null_smile(smile)
    if t >= T["boom"]:
        cells_look(near=70.0, far=170.0, power=2.6)
    else:
        cells_look()
    # his arms hang (he's crying), out of his own close-up
    for sd, sg in (("sl", 1), ("sr", -1)):
        X.arms[sd].rotation_euler = (math.radians(-35 - 6 * math.sin(t * 1.3)), math.radians(sg * 14), 0)
        X.forearms[sd].rotation_euler = (math.radians(-25), 0, 0)
    # his whole body judders as it fails
    jit = 0.06 * err ** 2 if t < g1 else 0.0
    X.root.location = Vector((E.XE - 26.0, E.Y0 + 7.0, E.deck - 8.0)) + Vector((
        jit * math.sin(t * 61.0), jit * math.sin(t * 47.0 + 1), 0.5 * jit * math.sin(t * 53.0 + 2)))
    if t < g1:
        X.head.rotation_euler = (math.radians(-3 + 4 * err * math.sin(t * 37.0)), math.radians(3 * err * math.sin(t * 29.0)), 0)
    elif X.head.parent is not None:
        X.head.rotation_euler = (math.radians(-3), 0, 0)
    # the strobe: his light flickering on the three of them
    E.strobe.location = P7.null_head(E) + Vector((6.0, -4.0, -2.0))
    fl = 0.5 + 0.5 * math.sin(t * 45.0) * math.sin(t * 17.0 + 1)
    E.strobe.data.energy = 0.0 if t < g0 else (2.0e4 * err * fl if t < g1 else 0.0)
    # his tears: black pixels from both eyes, running, breaking into smaller ones as they fall
    _null_tears(E, t)
    # the explosion
    _explode(E, t)


def _null_tears(E, t):
    X = E.X
    g0, g1 = T["null_glitch"], T["boom"]
    hm = X.head.matrix_world
    for ob, (side, ph, sp, dx) in zip(E.ntears, E.ntear_specs):
        if not (g0 + 0.4 <= t < g1 + 0.1):
            ob.hide_render = True
            continue
        u = ((t - g0) * 0.45 * sp + ph) % 1.0
        # in the head's own space: from under the eye (x = +-0.55, z = 2.5) down the face, then off it
        loc = Vector((side * 0.62 + dx, -1.62, 2.55 - 3.6 * u ** 1.6))
        s = 0.11 * (1 - 0.6 * u) * (0.6 if u > 0.55 else 1.0)
        ob.location = hm @ loc
        ob.rotation_euler = (u * 3.0, u * 2.0, 0)
        ob.scale = (s * 1.6, s * 1.6, s * 1.6)
        ob.hide_render = False


def _explode(E, t):
    b = T["boom"]
    for P in E.boom_parts:
        ob = P["ob"]
        me = ob.data
        if t < b:
            # before: the pixels tear away a little as the error grows (more and more loose)
            err = ss(T["null_glitch"] + 0.3, b, t)
            if err <= 0:
                co = P["co"]
            else:
                r = np.sin(P["die"] * 91.0 + t * 37.0)[:, None, None]
                sel = (P["die"] < 0.25 * err)[:, None, None]
                co = P["co"] + sel * r * P["dir"][:, None, :] * 0.25 * err
            me.vertices.foreach_set("co", co.ravel())
            me.update()
            continue
        s = t - b                                             # seconds since the blast (slow motion: it drifts)
        # out from his chest, fast then easing (the void is thick); each cube turning on its own axis
        chest = np.array([0.0, 0.0, 6.0], np.float32)
        out = P["cen"] - chest[None, :]
        out /= np.linalg.norm(out, axis=1, keepdims=True) + 1e-6
        d = out * 0.7 + P["dir"] * 0.45
        tau = 1.4
        dist = (2.5 + 9.0 * P["speed"])[:, None] * tau * (1 - math.exp(-s / tau)) + 0.25 * s
        cen = P["cen"] + d * dist
        cen[:, 2] -= 0.15 * s * s                              # a slow sink
        ang = P["spin"] * s
        ax = P["axis"] / (np.linalg.norm(P["axis"], axis=1, keepdims=True) + 1e-6)
        rel = P["co"] - P["cen"][:, None, :]
        c, sn = np.cos(ang)[:, None, None], np.sin(ang)[:, None, None]
        axv = ax[:, None, :]
        rot = rel * c + np.cross(axv, rel) * sn + axv * np.sum(axv * rel, axis=2, keepdims=True) * (1 - c)
        # going out, one by one: each shrinks to nothing at its own moment
        life = 1.0 - np.clip((s - (0.6 + P["die"] * 4.2)) / 0.35, 0, 1)
        co = cen[:, None, :] + rot * life[:, None, None]
        me.vertices.foreach_set("co", co.astype(np.float32).ravel())
        me.update()
    # the orbits fly off and are gone; the head falls
    X = E.X
    if t >= b:
        s = t - b
        k = 1 + 2.5 * (1 - math.exp(-s / 0.8))
        for o in (getattr(X, "orbit", None), getattr(X, "orbit2", None)):
            if o is not None:
                o.scale = (k, k, k)
                for ch in o.children_recursive:
                    ch.hide_render = s > 1.6
        _head_fall(E, t)


def _head_fall(E, t):
    """Left alone, the head: a moment hanging there, then down, slowly, turning, into the void."""
    X = E.X
    if not hasattr(E, "head_m0"):
        E.head_m0 = X.head.matrix_world.copy()
        X.head.parent = None
        X.head.matrix_world = E.head_m0
    s = max(0.0, t - (T["boom"] + 1.2))
    m0 = E.head_m0
    loc, rot, scl = m0.decompose()
    drop = 1.7 * s * s / (1 + 0.22 * s)                     # it gathers speed, the void slows it
    tilt = Quaternion((1, 0, 0), -0.32 * (1 - math.exp(-s / 2.0))) @ Quaternion((0, 1, 0), 0.18 * math.sin(s * 0.9))
    out = 24.0 * (1 - math.exp(-s / 2.6))                  # out over the void (past the island's edge)
    X.head.matrix_world = Matrix.LocRotScale(loc + Vector((0.3 * s, -out, -drop)), tilt @ rot, scl)


def cells(E, t):
    """Inside: the cells cry. Their faces fall; black pixel tears run; the light is cold."""
    from faceplate import NOOB_EYES
    u = ss(T["cells_cry"] + 0.2, T["cells_cry"] + 1.2, t)
    vals = {"both_open": 1.0, "both_h": lerp(1.75, 1.3, u), "both_w": 1.12, "both_ps": 0.06,
            "both_to": lerp(0.12, 0.55, u), "both_tm": lerp(0.0, 0.25, u), "both_ti": lerp(0.05, -0.1, u),
            "m_w": lerp(3.0, 1.8, u), "m_arch": lerp(-0.85, 0.55, u), "m_o": lerp(0.42, 0.18 + 0.06 * math.sin(t * 19), u),
            "m_k": 1.35}
    for f in E.style_faces:
        for k, v in vals.items():
            if k.startswith("both_"):
                for e in NOOB_EYES:
                    f[f"{e}_{k[5:]}"] = v
            else:
                f[k] = v
    # tears: three drops per eye, running down one after another
    for ob, p, n, j, hs in E.cell_tears:
        k = ((t - T["cells_cry"] - 0.5) * 0.55 + j / 3.0) % 1.0 if t > T["cells_cry"] + 0.5 else -1
        if k < 0:
            ob.hide_render = True
            continue
        ob.hide_render = False
        ob.location = p + Vector((0, 0, -0.55 * k * hs / 0.05 * 0.6)) + n * 0.01
        s = hs * (1 - 0.5 * k)
        ob.scale = (s, s * 0.6, s)
    # heads: still turned to where the camera rests, a slow sway; the light colder and dimmer
    for i, (em, p, ph, st) in enumerate(E.cells):
        v = (P7.SOUL + P7.soul_path(P7.T["end"]) - p)
        if v.length > 1e-4:
            q = Vector((0, -1, 0)).rotation_difference(v.normalized())
            em.rotation_quaternion = q @ Quaternion((0, 1, 0), 0.26 * math.sin(ph * 3.7)) \
                @ Quaternion((1, 0, 0), 0.12 * u + 0.03 * math.sin(t * 0.8 + ph))
    for ob in E.soul_lights:
        base = E.soul_light_base[ob.name]
        ob.data.energy = base * (0.7 if "fill" in ob.name else 0.5)
        if "rim" in ob.name:
            ob.data.color = (0.3, 0.75, 1.0)


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
    if shot == "CELLS":
        fwd = (look - loc).normalized()
        E.soul_key.location = loc + Vector((0.3, -0.2, 0.5)) + fwd * 0.4
        E.soul_under.location = loc + Vector((0, 0, -0.9)) + fwd * 1.2
    else:
        E.key.location = loc + Vector((0.4, 0.0, 1.2))
        E.key.rotation_euler = (look - E.key.location).to_track_quat("-Z", "Y").to_euler()
    return {"shot": shot}


def camera(E, t, shot):
    XE, deck = E.XE, E.deck
    t0, t1 = which(t)[1:]
    u = ss(t0, t1, t) if t1 < 1e8 else ss(t0, T["end"] + 0.6, t)
    nh = P7.null_head(E)
    if shot == "CELLS":
        # in the dome where part 7 stopped; a slow push toward the nearest wall of them
        p = P7.SOUL + P7.soul_path(P7.T["end"])
        look = p + Vector((0.6, 4.0, 0.3))
        loc = p.lerp(look, 0.22 * u)
        return loc, look, lerp(30, 38, u), 7.0, (look - loc).length * 0.75, 0.0, 0.0
    if shot == "FACE":
        # his face, close, from where they hang: the error on it, his tears
        f = (E.X.head.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
        f = Vector((f.x, f.y, 0)).normalized()
        side = f.cross(Vector((0, 0, 1))).normalized()
        loc = nh + f * lerp(24.0, 19.0, u) + side * 3.0 + Vector((0, 0, -1.0))
        err = ss(T["null_glitch"] + 0.3, T["boom"], t)
        return loc, nh + Vector((0, 0, -0.8)), 50, 8.0, None, 0.2 + 1.2 * err ** 2, 0.0
    if shot == "HEROES":
        # the three of them, his strobe on their faces
        loc, look, lens, fstop, focus, amp, roll = P7.camera(E, P7.T["see"] + 0.2 + 0.5 * u, "R2")
        return loc, look, lens, fstop, focus, 0.5, roll
    if shot == "FAR":
        # far off, to the side: the island's edge, the void, and him: the blast, the cells drifting out
        c = Vector((XE - 26.0, E.Y0 + 7.0, deck + 1.0))
        loc = c + Vector((-26.0 + 3.0 * u, -52.0 + 5.0 * u, 17.0))
        return loc, c + Vector((0, 0, 3.0 - 2.5 * u)), 38, 16.0, None, 0.05 + 1.2 * math.exp(-((t - T["boom"]) / 0.25) ** 2), 0.0
    # FALL: the head, falling away from us into the void; we tilt down after it and let it go
    hc = E.X.head.matrix_world @ Vector((0, 0, 1.9))
    c0 = Vector((XE - 26.0, E.Y0 + 7.0, deck + 1.0))
    loc = c0 + Vector((-14.0, -44.0, 8.0 - 10.0 * u))
    return loc, hc, lerp(50, 70, u), 16.0, (hc - loc).length, 0.04, 0.0


# ------------------------------------------------------------------ the look
def finish(path, mist_path, shot, t):
    import numpy as np
    from PIL import Image
    if shot == "CELLS":
        P7._finish_soul(path, mist_path)
        return
    if shot in ("FAR", "FALL"):
        import grade as G
        import assemble
        im = Image.open(path).convert("RGB")
        if os.path.exists(mist_path):
            im = G.haze(im, mist_path, None, {"L": 260, "start": 60, "max": 0.12})
        assemble.W, assemble.H = im.size
        assemble.grade(im, {"saturation": 1.2, "glow": 0.55, "threshold": 0.7, "tint": [1.0, 0.97, 1.03]}, 0, 0, None)
        im.save(path)
    else:
        P4.finish(path, mist_path)
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, np.float32) / 255.0
    h, w = a.shape[:2]
    rnd = np.random.default_rng(int(t * 1000))
    if shot == "FACE":                                       # the error: colour split, torn lines
        err = ss(T["null_glitch"] + 0.3, T["boom"], t)
        burst = (math.sin(t * 23.0) > 0.4) * err
        sh = int(round((2 + 10 * burst) * w / 480))
        a[:, :, 0] = np.roll(a[:, :, 0], sh, 1)
        a[:, :, 2] = np.roll(a[:, :, 2], -sh, 1)
        for _ in range(int(2 + 14 * err)):
            y0 = int(rnd.integers(0, h - 14))
            hh = int(rnd.integers(3, 16))
            a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], int(rnd.integers(-60, 60) * err * w / 480), 1)
    if shot == "FAR":                                        # the flash of the blast
        fl = math.exp(-max(0.0, t - T["boom"]) / 0.22) if t >= T["boom"] else 0.0
        a = a + (1 - a) * 0.9 * fl
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ main
def align(tl):
    b = tl.get("beats", {})
    for k in ("cells_cry", "null_glitch", "heroes", "boom", "drift", "fall", "end"):
        if k in b:
            T[k] = b[k][0]
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
