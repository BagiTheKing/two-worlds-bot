"""Builders for the new look, shared by the look tests and the episode renderer.

    from stage import build_steve, build_noob_char, build_patch_char, build_null_char, char_light
    S = build_steve(sc)            # S.holder (move/turn), S.arm (pose bones), S.face, S.brows, S.rig (collection)
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RIGS = os.path.join(REPO, "assets", "rigs")
STEVE_K = 2.0 / 3.215                      # the rig file stands 3.215 tall; Steve is 2 blocks


class Char:
    pass


def build_steve(sc, name="steve", hair=True):
    """The BlendSwap Steve with our face, brows, hair and skin, as a collection
    instance (S.holder) so his rig works as in its file. Pose with pose.pose(S.arm, ...)."""
    from brows import build_brows
    from faceplate import build_faceplate, flatten_face
    from hair import build_hair
    from skin_face import make_face_skin
    with bpy.data.libraries.load(os.path.join(RIGS, "steve_blendswap.blend"), link=False) as (src, dst):
        dst.collections = ["Rig"]
    rig = dst.collections[0]
    sc.collection.children.link(rig)
    skin = bpy.data.images.load(os.path.join(RIGS, "steve_skin_v2.png"), check_existing=True)
    for m in bpy.data.materials:
        if m.name.startswith("Skin") and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image and n.image.name.startswith("Steve"):
                    n.image = skin
            b = m.node_tree.nodes.get("Principled BSDF")
            if b and "Subsurface Weight" in b.inputs:
                b.inputs["Subsurface Weight"].default_value = 0.12
                b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
                b.inputs["Subsurface Scale"].default_value = 0.03
    for c in bpy.data.collections:
        if c.name.startswith("Head_Layers"):
            c.hide_render = True
    for idb in list(bpy.data.objects) + list(bpy.data.armatures) + list(bpy.data.shape_keys):
        ad = getattr(idb, "animation_data", None)
        if ad:
            for d in ad.drivers:
                d.is_valid = True
                d.driver.is_valid = True
    arm = bpy.data.objects["Thomas_rig"]
    if hair:
        build_hair(arm, lattice=bpy.data.objects["Head"])
    head = bpy.data.objects["Head_NoDeform"]
    for i, m in enumerate(head.data.materials):
        if m and m.name in ("Eyes.001", "Mouth"):
            head.data.materials[i] = head.data.materials[0]
    for n in ("Eyes", "Eyebrows", "Eyebrows.001", "Top_teeth", "Bottom_teeth", "Tongue"):
        bpy.data.objects[n].hide_render = True
    flatten_face(head, arm)
    lat = bpy.data.objects["Head"]
    S = Char()
    S.face = build_faceplate(arm, bpy.data.images.load(make_face_skin(os.path.join(HERE, "_faceskin.png"))), lattice=lat)
    S.brows = build_brows(arm, lattice=lat)
    arm.pose.bones["Eyes_UP_DOWN"].location = (0, -0.1, 0)
    for key in bpy.data.shape_keys:
        kb = key.key_blocks.get("EyebrowThikness")
        if kb is None:
            continue
        if key.animation_data:
            for d in list(key.animation_data.drivers):
                if "EyebrowThikness" in d.data_path:
                    key.animation_data.drivers.remove(d)
        kb.value = 1.0
    for m in bpy.data.materials:
        if m.name.startswith("steve_face") and m.node_tree:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b and "Subsurface Weight" in b.inputs:
                b.inputs["Subsurface Weight"].default_value = 0.12
                b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
                b.inputs["Subsurface Scale"].default_value = 0.03
    # the rig file switches meshes on and off with drivers (Alex arms, layers, a second
    # head): fix the set we use and drop those drivers, so visibility is ours to animate
    keep = {"Body", "R.leg", "L.Leg", "R.steve_arm", "L.Steve_arm", "Head_NoDeform"}
    for o in list(rig.all_objects):
        ad = o.animation_data
        if ad:
            for d in ad.drivers:
                if d.data_path in ("hide_render", "hide_viewport"):
                    d.mute = True
        if o.type in ("MESH", "CURVE"):
            mine = o.name in keep or o.name.startswith(("steve_hair", "steve_faceplate", "brow_"))
            o.hide_render = not mine
            o.hide_viewport = False
    bpy.context.view_layer.update()
    sc.collection.children.unlink(rig)
    holder = bpy.data.objects.new(name, None)
    holder.instance_type = "COLLECTION"
    holder.instance_collection = rig
    sc.collection.objects.link(holder)
    holder.scale = (STEVE_K,) * 3
    S.holder, S.arm, S.rig = holder, arm, rig
    S.parts = steve_parts(rig)
    return S


def steve_parts(rig):
    """The rig's visible meshes sorted into legs / body / arms / head (for the upgrade)."""
    parts = {"legs": [], "body": [], "arms": [], "head": []}
    for o in rig.all_objects:
        if o.type not in ("MESH", "CURVE") or o.hide_render:
            continue
        if any(c.hide_render for c in o.users_collection):
            continue
        n = o.name.lower()
        if "leg" in n or "foot" in n or "shoe" in n:
            parts["legs"].append(o)
        elif "arm" in n or "finger" in n or "hand" in n or o.name.startswith(("item_",)):
            parts["arms"].append(o)
        elif ("head" in n or "hair" in n or "face" in n or "brow" in n or "lash" in n or "eye" in n
              or o.name.startswith(("steve_", "brow_"))):
            parts["head"].append(o)
        else:
            parts["body"].append(o)
    return parts


def build_noob_char(sc, name="noob", head="classic"):
    from noob import build_noob
    col = bpy.data.collections.new(name)
    sc.collection.children.link(col)
    n = build_noob(col, head=head, height=2.0, name=name)
    n.col = col
    n.parts = {"legs": [o for o in col.objects if "_leg_" in o.name and o.type == "MESH"],
               "body": [o for o in col.objects if o.name.endswith("_torso_mesh")],
               "arms": [o for o in col.objects if "_arm_" in o.name and o.type == "MESH"],
               "head": [o for o in col.objects if o.name.endswith(("_head_mesh", "_face"))]}
    return n


def build_patch_char(sc, name="patch", size=0.34):
    from patch import build_patch
    col = bpy.data.collections.new(name)
    sc.collection.children.link(col)
    P = build_patch(col, size=size, name=name)
    P.col = col
    return P


def build_null_char(sc, assets, height=15.0, name="null"):
    from null import build_null
    col = bpy.data.collections.new(name)
    sc.collection.children.link(col)
    N = build_null(col, assets, height=height, name=name)
    N.col = col
    N.height = height
    return N


def null_lights(sc, N):
    """Pink and cyan rim lights and the cold back-glow (the thumbnail's look);
    they follow N.root (call place_null_lights after moving him)."""
    out = []
    for n, loc, c, p in (("null_rim_pink", (-8, 6, 9), (1.0, 0.35, 0.85), 9000),
                         ("null_rim_cyan", (8, 6, 8), (0.45, 0.85, 1.0), 8000)):
        L = bpy.data.lights.new(n, "AREA")
        L.color, L.size = c, 5
        o = bpy.data.objects.new(n, L)
        sc.collection.objects.link(o)
        o["base_power"], o["rel"] = p, loc
        out.append(o)
    gm = bpy.data.materials.new("null_backglow")
    gm.use_nodes = True
    gt = gm.node_tree
    for n_ in list(gt.nodes):
        gt.nodes.remove(n_)
    go = gt.nodes.new("ShaderNodeOutputMaterial")
    gg = gt.nodes.new("ShaderNodeTexGradient")
    gg.gradient_type = "SPHERICAL"
    gtc = gt.nodes.new("ShaderNodeTexCoord")
    gsc = gt.nodes.new("ShaderNodeVectorMath")
    gsc.operation = "SCALE"
    gsc.inputs["Scale"].default_value = 2.0
    gt.links.new(gtc.outputs["Object"], gsc.inputs[0])
    gt.links.new(gsc.outputs[0], gg.inputs["Vector"])
    gp = gt.nodes.new("ShaderNodeMath")
    gp.operation = "POWER"
    gp.inputs[1].default_value = 1.8
    gt.links.new(gg.outputs["Fac"], gp.inputs[0])
    gs = gt.nodes.new("ShaderNodeMath")
    gs.operation = "MULTIPLY"
    gs.inputs[1].default_value = 3.0
    gt.links.new(gp.outputs[0], gs.inputs[0])
    ge = gt.nodes.new("ShaderNodeEmission")
    ge.inputs["Color"].default_value = (0.62, 0.74, 0.98, 1)
    gt.links.new(gs.outputs[0], ge.inputs["Strength"])
    gtr = gt.nodes.new("ShaderNodeBsdfTransparent")
    gad = gt.nodes.new("ShaderNodeAddShader")
    gt.links.new(gtr.outputs["BSDF"], gad.inputs[0])
    gt.links.new(ge.outputs["Emission"], gad.inputs[1])
    gt.links.new(gad.outputs["Shader"], go.inputs["Surface"])
    me = bpy.data.meshes.new("null_backglow")
    me.from_pydata([(-0.5, 0, -0.5), (0.5, 0, -0.5), (0.5, 0, 0.5), (-0.5, 0, 0.5)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    me.materials.append(gm)
    gl = bpy.data.objects.new("null_backglow", me)
    sc.collection.objects.link(gl)
    for a in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_shadow"):
        setattr(gl, a, False)
    N.lights, N.glow, N.glow_strength = out, gl, gs.inputs[1]
    return N


def place_null_lights(N, fade=1.0):
    hz = N.height / 10.0 * N.root.scale.x / (N.height / 10.0)
    hz = N.root.scale.x
    rz = Matrix.Rotation(N.root.rotation_euler.z, 3, "Z")
    base = Vector(N.root.location)
    for o in N.lights:
        o.location = base + rz @ (Vector(o["rel"]) * hz)
        o.rotation_euler = (base + Vector((0, 0, 5.5 * hz)) - o.location).to_track_quat("-Z", "Y").to_euler()
        o.data.energy = o["base_power"] * hz * hz * fade
    N.glow.location = base + rz @ (Vector((0.4, 5.0, 6.4)) * hz)
    N.glow.rotation_euler = (0, 0, N.root.rotation_euler.z)
    N.glow.scale = (24 * hz, 1, 24 * hz)
    N.glow_strength.default_value = 3.0 * fade


def char_light(sc, name, loc, power, color, aim=(0, 0, 1.55), cone=26, size=0.25):
    L = bpy.data.lights.new(name, "SPOT")
    L.energy, L.color = power, color
    L.spot_size = math.radians(cone)
    L.spot_blend = 0.35
    L.shadow_soft_size = size
    ob = bpy.data.objects.new(name, L)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def aim(ob, at):
    ob.rotation_euler = (Vector(at) - Vector(ob.location)).to_track_quat("-Z", "Y").to_euler()
