"""The first portal, in the new look: an obsidian frame (separate blocks, so it
can crack apart) and a membrane that behaves like skin: whatever pushes at it
from the far side stretches it into a bulge, and tears through past a limit.

    P = build_portal(sc, assets, at=(0, 5, 0))      # faces -y (the camera side)
    drape(P, [objects pushing from +y])              # call after placing them, per frame
    P.root, P.blocks, P.membrane, P.light

Local frame: x across, z up, y = 0 the membrane, +y the other side.
"""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

RES = 0.02                 # the membrane's grid
LIMIT = 0.26               # how far it stretches before it tears
CONE = 55.0                # how steeply it falls away from what pushes it (per metre)


class Portal:
    pass


def _lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 for v in c)


def _frame_image(assets):
    """The first frame of the game's animated portal texture, as its own image."""
    im = bpy.data.images.get("portal_swirl")
    if im:
        return im
    from PIL import Image
    p = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block",
                     "nether_portal.png")
    src = np.asarray(Image.open(p).convert("RGBA").crop((0, 0, 16, 16)), np.float32) / 255.0
    im = bpy.data.images.new("portal_swirl", 16, 16, alpha=True)
    im.pixels.foreach_set(src[::-1].ravel())
    im.pack()
    return im


def _mat_membrane(assets):
    m = bpy.data.materials.new("portal_membrane")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes.new, nt.links.new
    b = nt.nodes["Principled BSDF"]
    # the game's pixels, drifting; two layers at different sizes so it swirls
    tc = N("ShaderNodeTexCoord")
    flow = N("ShaderNodeVectorMath")
    flow.operation = "ADD"
    L(tc.outputs["UV"], flow.inputs[0])
    m["flow"] = flow.name                                   # inputs[1]: the drift (animate it)
    t1 = N("ShaderNodeTexImage")
    t1.image = _frame_image(assets)
    t1.interpolation = "Closest"
    L(flow.outputs[0], t1.inputs["Vector"])
    nz = N("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 3.0
    L(flow.outputs[0], nz.inputs["Vector"])
    ramp = N("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.3, (*_lin((58, 10, 128)), 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.75, (*_lin((196, 92, 255)), 1)
    L(nz.outputs["Fac"], ramp.inputs["Fac"])
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.75
    L(ramp.outputs["Color"], mix.inputs[6])
    bright = N("ShaderNodeVectorMath")
    bright.operation = "SCALE"
    bright.inputs["Scale"].default_value = 1.25
    L(t1.outputs["Color"], bright.inputs[0])
    L(bright.outputs[0], mix.inputs[7])
    # stretched skin goes thin: paler, brighter
    st = N("ShaderNodeAttribute")
    st.attribute_name = "stretch"
    # what leans on it from the other side shows through as a dark shape (a face against glass)
    pr = N("ShaderNodeAttribute")
    pr.attribute_name = "press"
    dark = N("ShaderNodeMix")
    dark.data_type = "RGBA"
    L(pr.outputs["Fac"], dark.inputs[0])
    L(mix.outputs[2], dark.inputs[6])
    dark.inputs[7].default_value = (*_lin((22, 4, 40)), 1)
    thin = N("ShaderNodeMix")
    thin.data_type = "RGBA"
    half = N("ShaderNodeMath")
    half.operation = "MULTIPLY"
    half.inputs[1].default_value = 0.55
    L(st.outputs["Fac"], half.inputs[0])
    L(half.outputs[0], thin.inputs[0])
    L(dark.outputs[2], thin.inputs[6])
    thin.inputs[7].default_value = (*_lin((226, 120, 255)), 1)
    L(thin.outputs[2], b.inputs["Base Color"])
    L(thin.outputs[2], b.inputs["Emission Color"])
    es = N("ShaderNodeMath")
    es.operation = "MULTIPLY_ADD"
    L(st.outputs["Fac"], es.inputs[0])
    es.inputs[1].default_value = 0.3
    es.inputs[2].default_value = 0.27
    m["power"] = es.name                                    # inputs[2]: the membrane's own light
    L(es.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Roughness"].default_value = 0.22              # wet: the bulges catch the light
    b.inputs["Specular IOR Level"].default_value = 0.8
    return m


def build_portal(sc, assets, at=(0, 0, 0), w=4, h=5, name="portal"):
    from world import material
    P = Portal()
    P.w, P.h = w, h
    col = bpy.data.collections.new(name)
    sc.collection.children.link(col)
    P.col = col
    P.root = bpy.data.objects.new(name + "_root", None)
    col.objects.link(P.root)
    P.root.location = at
    B = os.path.join(assets, "mcprep", "resourcepacks", "mcprep_default", "assets", "minecraft", "textures", "block")
    obs = bpy.data.materials.get("w_obsidian") or material("w_obsidian", os.path.join(B, "obsidian.png"), rough=0.35, spec=0.6)
    cry = bpy.data.materials.get("w_crying") or material("w_crying", os.path.join(B, "crying_obsidian.png"), rough=0.35, spec=0.6)
    P.blocks = []
    cells = [(i, 0) for i in range(w)] + [(i, h - 1) for i in range(w)] + \
            [(0, j) for j in range(1, h - 1)] + [(w - 1, j) for j in range(1, h - 1)]
    for k, (i, j) in enumerate(cells):
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        for c_ in list(ob.users_collection):
            c_.objects.unlink(ob)
        col.objects.link(ob)
        ob.name = f"{name}_block_{k}"
        ob.data.materials.append(cry if k in (5, 11) else obs)      # two blocks weep purple: it's old
        ob.parent = P.root
        ob.location = (i - w / 2 + 0.5, 0, j + 0.5)
        ob["home"] = tuple(ob.location)
        P.blocks.append(ob)
    # the membrane: a fine grid across the opening
    x0, x1, z0, z1 = -w / 2 + 1, w / 2 - 1, 1.0, h - 1.0
    nx, nz = int(round((x1 - x0) / RES)) + 1, int(round((z1 - z0) / RES)) + 1
    xs, zs = np.linspace(x0, x1, nx), np.linspace(z0, z1, nz)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    verts = np.stack([X.ravel(), np.zeros(nx * nz), Z.ravel()], 1)
    idx = np.arange(nx * nz).reshape(nx, nz)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    me = bpy.data.meshes.new(name + "_membrane")
    me.from_pydata(verts.tolist(), [], faces.tolist())
    uv = me.uv_layers.new(name="uv")
    co = verts[np.array([v for f in faces for v in f])]
    uv.data.foreach_set("uv", np.stack([co[:, 0] - x0, co[:, 2] - z0], 1).ravel())     # one block = one tile
    me.attributes.new("stretch", "FLOAT", "POINT")
    me.attributes.new("press", "FLOAT", "POINT")
    for p_ in me.polygons:
        p_.use_smooth = True
    me.materials.append(_mat_membrane(assets))
    P.membrane = bpy.data.objects.new(name + "_membrane", me)
    col.objects.link(P.membrane)
    P.membrane.parent = P.root
    P.membrane.visible_shadow = False
    P.grid = (xs, zs, nx, nz)
    # its light: purple, spilling out of the opening onto whatever stands in front
    L_ = bpy.data.lights.new(name + "_light", "AREA")
    L_.shape, L_.size, L_.size_y = "RECTANGLE", x1 - x0, z1 - z0
    L_.color, L_.energy = (0.62, 0.25, 1.0), 650
    P.light = bpy.data.objects.new(name + "_light", L_)
    col.objects.link(P.light)
    P.light.parent = P.root
    P.light.location = (0, -0.25, h / 2)
    P.light.rotation_euler = (math.radians(90), 0, 0)
    return P


def drape(P, objs, limit=LIMIT, margin=0.035):
    """Stretch the membrane over whatever of `objs` has pushed past it (toward -y)."""
    xs, zs, nx, nz = P.grid
    dg = bpy.context.evaluated_depsgraph_get()
    inv = np.array(P.root.matrix_world.inverted())
    big = 9.0
    H = np.full((nx, nz), big, np.float32)
    N0 = np.full((nx, nz), big, np.float32)                 # the nearest thing behind (or through) each point
    for ob in objs:
        if ob.type != "MESH":
            continue
        me = ob.data
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = np.c_[co.reshape(-1, 3), np.ones(len(me.vertices), np.float32)]
        loc = co @ (inv @ np.array(ob.evaluated_get(dg).matrix_world)).T
        keep = (loc[:, 1] < 0.9) & (loc[:, 0] > xs[0]) & (loc[:, 0] < xs[-1]) & (loc[:, 2] > zs[0]) & (loc[:, 2] < zs[-1])
        loc = loc[keep]
        i = np.clip(np.round((loc[:, 0] - xs[0]) / RES).astype(int), 0, nx - 1)
        j = np.clip(np.round((loc[:, 2] - zs[0]) / RES).astype(int), 0, nz - 1)
        np.minimum.at(N0, (i, j), loc[:, 1])
        thru = loc[:, 1] < 0.1
        np.minimum.at(H, (i[thru], j[thru]), loc[thru, 1] - margin)
    K = int(0.2 / RES)
    for axis in (0, 1):                                    # the skin falls away from each point as a cone-ish bowl
        out = H.copy()
        for d in range(1, K + 1):
            pen = CONE * (d * RES) ** 2
            for sgn in (1, -1):
                sh = np.roll(H, sgn * d, axis)
                if axis == 0:
                    (sh[:d] if sgn > 0 else sh[-d:])[...] = big
                else:
                    (sh[:, :d] if sgn > 0 else sh[:, -d:])[...] = big
                out = np.minimum(out, sh + pen)
        H = out
    # held at the frame: it can't leave the edge
    ex = np.minimum(np.arange(nx), np.arange(nx)[::-1])[:, None] * RES
    ez = np.minimum(np.arange(nz), np.arange(nz)[::-1])[None, :] * RES
    hold = np.minimum(ex, ez)
    y = np.clip(np.minimum(H, 0.0), -limit, 0.0)
    y = np.maximum(y, -hold * 1.6)
    me = P.membrane.data
    co = np.empty(nx * nz * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co[:, 1] = y.ravel()
    me.vertices.foreach_set("co", co.ravel())
    me.attributes["stretch"].data.foreach_set("value", np.clip(-y.ravel() / limit, 0, 1) ** 1.6)
    press = np.clip((0.75 - N0) / 0.75, 0, 1)
    for _ in range(2):                                     # soften the shape's edge
        press = (press + np.roll(press, 1, 0) + np.roll(press, -1, 0) + np.roll(press, 1, 1) + np.roll(press, -1, 1)) / 5
    me.attributes["press"].data.foreach_set("value", press.ravel().astype(np.float32))
    me.update()
