"""
Blender building blocks: materials, a voxel mesher, and textured boxes.

The voxel mesher turns {(x, y, z): block} into one mesh that has only the
faces you can see, so a 64x64 landscape stays light enough for the CPU
renderer. Boxes are the same idea for character parts: any size, any pivot,
a material per side.
"""

import bpy
from mathutils import Vector

# Corner order per side: bottom-left, bottom-right, top-right, top-left as
# seen from outside, so UVs come out upright and normals point outward.
SIDES = {
    "right":  ((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))),
    "left":   ((-1, 0, 0), ((0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1))),
    "back":   ((0, 1, 0), ((1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1))),
    "front":  ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))),
    "top":    ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))),
    "bottom": ((0, 0, -1), ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0))),
}
UV = ((0, 0), (1, 0), (1, 1), (0, 1))

_images = {}


def image(path, smooth=False):
    key = (path, smooth)
    if key not in _images:
        img = bpy.data.images.load(path)
        _images[key] = img
    return _images[key]


def material(name, color=(0.8, 0.8, 0.8), tex=None, rough=0.9, smooth_tex=False,
             emission=None, strength=0.0, spec=0.2, coat=0.0, emit_tex=False, alpha_tex=False):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.25
    if tex:
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = image(tex)
        n.interpolation = "Linear" if smooth_tex else "Closest"
        nt.links.new(n.outputs["Color"], b.inputs["Base Color"])
        if alpha_tex:                              # see-through where the image is
            nt.links.new(n.outputs["Alpha"], b.inputs["Alpha"])
            if hasattr(m, "surface_render_method"):
                m.surface_render_method = "DITHERED"
        if emit_tex:
            nt.links.new(n.outputs["Color"], b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = strength
    if emission and not emit_tex:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def _mesh_object(name, verts, faces, face_mats, materials, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for i, poly in enumerate(me.polygons):
        poly.material_index = face_mats[i]
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = UV[k]
    me.update()
    for m in materials:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def voxels(name, cells, palette, location=(0, 0, 0), solid=None):
    """cells: {(x, y, z): block}. palette: {block: {"top": mat, "side": mat,
    "bottom": mat}} (missing keys fall back to "side"). solid: the cells that
    hide faces (default: cells itself); pass a chunk's own cells so its sides
    stay closed when a neighbouring chunk is deleted."""
    solid = cells if solid is None else solid
    mats, index = [], {}

    def slot(m):
        if m.name not in index:
            index[m.name] = len(mats)
            mats.append(m)
        return index[m.name]

    verts, faces, fmats = [], [], []
    for (x, y, z), block in cells.items():
        p = palette[block]
        for side, (n, corners) in SIDES.items():
            if (x + n[0], y + n[1], z + n[2]) in solid:
                continue
            key = side if side in ("top", "bottom") else "side"
            m = p.get(key, p["side"])
            base = len(verts)
            verts += [(x + c[0], y + c[1], z + c[2]) for c in corners]
            faces.append((base, base + 1, base + 2, base + 3))
            fmats.append(slot(m))
    ob = _mesh_object(name, verts, faces, fmats, mats)
    ob.location = location
    return ob


def box(name, size, center, mats, parent=None, bevel=0.0):
    """A box of `size` whose centre sits at `center` relative to the object's
    origin (so the origin is the pivot). mats: {"front": m, ..., "default": m}."""
    sx, sy, sz = size
    cx, cy, cz = center
    verts, faces, fmats, used = [], [], [], []
    for side, (n, corners) in SIDES.items():
        m = mats.get(side, mats["default"])
        if m not in used:
            used.append(m)
        base = len(verts)
        verts += [(cx + (c[0] - 0.5) * sx, cy + (c[1] - 0.5) * sy, cz + (c[2] - 0.5) * sz)
                  for c in corners]
        faces.append((base, base + 1, base + 2, base + 3))
        fmats.append(used.index(m))
    ob = _mesh_object(name, verts, faces, fmats, used, parent)
    if bevel:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob


def empty(name, location=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    if parent:
        ob.parent = parent
    return ob


def aim(ob, direction):
    """Rotate a light/camera so its -Z axis points along `direction`."""
    ob.rotation_euler = (-Vector(direction)).to_track_quat("Z", "Y").to_euler()


def hide_at(ob, frame, hidden=True, before=None):
    """Key render visibility: `before` the frame it is the opposite."""
    obs = [ob] + list(ob.children_recursive)
    for o in obs:
        if o.get("is_flash"):                # flash twins keep their own keys
            continue
        o.hide_render = not hidden
        o.keyframe_insert("hide_render", frame=1)
        o.hide_render = not hidden
        o.keyframe_insert("hide_render", frame=max(1, frame - 1))
        o.hide_render = hidden
        o.keyframe_insert("hide_render", frame=frame)


def show_between(ob, f0, f1):
    """Visible only for frames f0..f1-1."""
    for o in [ob] + list(ob.children_recursive):
        for f, h in ((1, True), (f0, False), (f1, True)):
            o.hide_render = h
            o.keyframe_insert("hide_render", frame=max(1, f))
