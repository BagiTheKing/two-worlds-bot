"""Roblox parts and the Studio building tool, for the Noob's BTool build.

Parts are smooth plastic boxes (or cylinders) with studs on their top faces,
in Roblox's classic BrickColors. The tool's look is Roblox Studio's: a part
being placed is outlined in selection blue, with move arrows (red X, green
up, blue Z) while it slides, resize handles while it grows, and a white flash
when it snaps into place.

    mat = plastic_material()
    ob = make_part(col, "p1", (4, 2, 0.4), "Bright red", mat, shape="box")
    G = Gizmos(col); G.draw([gizmo spec, ...]) every frame
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector

STUD = 0.4                                   # one Roblox stud: the Noob (5 studs tall) is 2 m

BRICK = {                                    # Roblox's classic BrickColors (sRGB)
    "Bright red": (196, 40, 28), "Bright blue": (13, 105, 172), "Bright yellow": (245, 205, 48),
    "Dark green": (40, 127, 71), "Bright green": (75, 151, 75), "Bright orange": (218, 133, 65),
    "Lime green": (164, 189, 71), "Medium stone grey": (163, 162, 165), "Institutional white": (248, 248, 248),
    "Bright violet": (107, 50, 124), "Teal": (18, 238, 212), "Hot pink": (255, 0, 191),
    "Really black": (17, 17, 17), "Dark stone grey": (99, 95, 98), "Pastel blue": (128, 187, 219),
}
RAINBOW = ["Bright red", "Bright orange", "Bright yellow", "Bright green", "Bright blue", "Bright violet"]
SELECT = (0, 162, 255)                       # Studio's selection blue


def lin(c):
    return tuple(((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c)


def plastic_material():
    """Shiny toy plastic, the colour from each object's colour; studs on top faces
    (a bump of round bosses on a stud grid, with a soft ring of shade round each)."""
    m = bpy.data.materials.get("rbx_plastic")
    if m:
        return m
    m = bpy.data.materials.new("rbx_plastic")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes.new, nt.links.new
    b = nt.nodes["Principled BSDF"]
    oi = N("ShaderNodeObjectInfo")
    tc = N("ShaderNodeTexCoord")
    geo = N("ShaderNodeNewGeometry")
    # top-facing mask (object space normal z)
    vt = N("ShaderNodeVectorTransform")
    vt.vector_type, vt.convert_from, vt.convert_to = "NORMAL", "WORLD", "OBJECT"
    L(geo.outputs["Normal"], vt.inputs[0])
    sn = N("ShaderNodeSeparateXYZ")
    L(vt.outputs[0], sn.inputs[0])
    up = N("ShaderNodeMath")
    up.operation = "GREATER_THAN"
    up.inputs[1].default_value = 0.9
    L(sn.outputs["Z"], up.inputs[0])
    # the stud grid in object space
    sp = N("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sp.inputs[0])

    def cell(sock):
        d = N("ShaderNodeMath")
        d.operation = "DIVIDE"
        d.inputs[1].default_value = STUD
        L(sock, d.inputs[0])
        f = N("ShaderNodeMath")
        f.operation = "FRACT"
        L(d.outputs[0], f.inputs[0])
        s = N("ShaderNodeMath")
        s.operation = "SUBTRACT"
        s.inputs[1].default_value = 0.5
        L(f.outputs[0], s.inputs[0])
        return s.outputs[0]
    cx, cy = cell(sp.outputs["X"]), cell(sp.outputs["Y"])
    cc = N("ShaderNodeCombineXYZ")
    L(cx, cc.inputs[0])
    L(cy, cc.inputs[1])
    ln = N("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    L(cc.outputs[0], ln.inputs[0])
    # boss: 1 inside r < 0.3 (of a stud), falling off to 0 at 0.34
    boss = N("ShaderNodeMapRange")
    boss.interpolation_type = "SMOOTHSTEP"
    boss.inputs["From Min"].default_value = 0.34
    boss.inputs["From Max"].default_value = 0.29
    L(ln.outputs["Value"], boss.inputs["Value"])
    ring = N("ShaderNodeMapRange")                          # a soft shade just outside each stud
    ring.interpolation_type = "SMOOTHSTEP"
    ring.inputs["From Min"].default_value = 0.42
    ring.inputs["From Max"].default_value = 0.34
    L(ln.outputs["Value"], ring.inputs["Value"])
    h = N("ShaderNodeMath")
    h.operation = "MULTIPLY"
    L(boss.outputs["Result"], h.inputs[0])
    L(up.outputs[0], h.inputs[1])
    bump = N("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.9
    bump.inputs["Distance"].default_value = 0.05
    L(h.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], b.inputs["Normal"])
    shade = N("ShaderNodeMath")                              # the ring, darker
    shade.operation = "MULTIPLY"
    L(ring.outputs["Result"], shade.inputs[0])
    L(up.outputs[0], shade.inputs[1])
    s2 = N("ShaderNodeMath")
    s2.operation = "SUBTRACT"
    L(shade.outputs[0], s2.inputs[1])
    L(h.outputs[0], s2.inputs[0])                            # (boss - ring): bright boss, shaded rim
    s3 = N("ShaderNodeMath")
    s3.operation = "MULTIPLY_ADD"
    s3.inputs[1].default_value = 0.18
    s3.inputs[2].default_value = 1.0
    L(s2.outputs[0], s3.inputs[0])
    col = N("ShaderNodeVectorMath")
    col.operation = "SCALE"
    L(oi.outputs["Color"], col.inputs[0])
    L(s3.outputs[0], col.inputs["Scale"])
    L(col.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.58
    b.inputs["Specular IOR Level"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 0.0
    b.inputs["Coat Roughness"].default_value = 0.15
    # a flash when it snaps: emission from the object's alpha (pass_index unused); see set_flash
    em = N("ShaderNodeAttribute")
    em.attribute_type = "OBJECT"
    em.attribute_name = "flash"
    L(em.outputs["Fac"], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1)
    return m


def make_part(col, name, size, color, mat, shape="box"):
    """A part centred on its object origin. size = (x, y, z) in metres."""
    sx, sy, sz = size
    bm = bmesh.new()
    if shape == "cyl":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.5, radius2=0.5, depth=1.0)
    else:
        bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bev = min(0.018, 0.2 * min(sx, sy, sz))
    edges = [e for e in bm.edges if shape != "cyl" or abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-4]
    bmesh.ops.bevel(bm, geom=edges, offset=bev, segments=2, affect="EDGES", profile=0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = shape == "cyl"
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.color = (*lin(BRICK[color]), 1)
    ob["flash"] = 0.0
    ob["size"] = tuple(size)
    return ob


# ------------------------------------------------------------------ gizmos
def _gizmo_materials():
    out = {}
    for name, rgb, power in (("sel", SELECT, 4.0), ("red", (230, 40, 40), 2.5), ("green", (60, 220, 60), 2.5),
                             ("blue", (40, 110, 255), 2.5), ("handle", (255, 170, 30), 2.5),
                             ("white", (255, 255, 255), 9.0)):
        m = bpy.data.materials.get("gz_" + name)
        if not m:
            m = bpy.data.materials.new("gz_" + name)
            m.use_nodes = True
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (*lin(rgb), 1)
            b.inputs["Emission Color"].default_value = (*lin(rgb), 1)
            b.inputs["Emission Strength"].default_value = power
        out[name] = m
    return out


class Gizmos:
    """One mesh, rebuilt every frame, with every gizmo on screen.
    spec: {"m": matrix_world of the part, "size": (x, y, z), "mode": "move"|"resize"|"snap",
           "k": 0..1 (the snap flash), "w": line width}"""
    ORDER = ["sel", "red", "green", "blue", "handle", "white"]

    def __init__(self, col):
        self.me = bpy.data.meshes.new("gizmos")
        self.ob = bpy.data.objects.new("gizmos", self.me)
        col.objects.link(self.ob)
        mats = _gizmo_materials()
        for n in self.ORDER:
            self.me.materials.append(mats[n])
        self.ob.visible_shadow = False
        try:
            self.ob.cycles.use_motion_blur = False
        except Exception:
            pass

    def draw(self, specs):
        verts, faces, mi = [], [], []

        def box(c, hx, hy, hz, m_, mat):
            i = len(verts)
            for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                               (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
                verts.append(m_ @ Vector((c[0] + dx * hx, c[1] + dy * hy, c[2] + dz * hz)))
            for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                faces.append([i + k for k in f])
                mi.append(self.ORDER.index(mat))

        def cone(base, axis, length, radius, m_, mat, seg=10):
            axis = axis.normalized()
            u = axis.orthogonal().normalized()
            v = axis.cross(u)
            i = len(verts)
            tip = base + axis * length
            verts.append(m_ @ tip)
            for k in range(seg):
                a = 2 * math.pi * k / seg
                verts.append(m_ @ (base + (u * math.cos(a) + v * math.sin(a)) * radius))
            for k in range(seg):
                faces.append([i, i + 1 + k, i + 1 + (k + 1) % seg])
                mi.append(self.ORDER.index(mat))
            faces.append([i + 1 + k for k in range(seg)][::-1])
            mi.append(self.ORDER.index(mat))

        for s in specs:
            m_ = s["m"]
            sx, sy, sz = (v / 2 for v in s["size"])
            w = s.get("w", 0.035)
            mat = "white" if s["mode"] == "snap" and s.get("k", 0) > 0.5 else "sel"
            # the selection box: 12 edges, a little outside the part
            ex, ey, ez = sx + w, sy + w, sz + w
            for yy in (-ey, ey):
                for zz in (-ez, ez):
                    box((0, yy, zz), ex, w / 2, w / 2, m_, mat)
            for xx in (-ex, ex):
                for zz in (-ez, ez):
                    box((xx, 0, zz), w / 2, ey, w / 2, m_, mat)
            for xx in (-ex, ex):
                for yy in (-ey, ey):
                    box((xx, yy, 0), w / 2, w / 2, ez, m_, mat)
            if s["mode"] == "move":                          # move arrows, out of each face
                L_ = 0.55
                for ax, mat_ in ((Vector((1, 0, 0)), "red"), (Vector((0, 0, 1)), "green"), (Vector((0, 1, 0)), "blue")):
                    for sg in (1, -1):
                        d = ax * sg
                        o = Vector((d.x * (sx + 0.15), d.y * (sy + 0.15), d.z * (sz + 0.15)))
                        st = o + d * L_ * 0.5
                        box(tuple(st), *(L_ * 0.5 if abs(c) > 0.5 else 0.03 for c in d), m_, mat_)
                        cone(o + d * L_, d, 0.28, 0.11, m_, mat_)
            if s["mode"] == "resize":                        # resize handles: a ball on each face
                for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)),
                          Vector((0, 0, 1)), Vector((0, 0, -1))):
                    c = Vector((d.x * (sx + 0.22), d.y * (sy + 0.22), d.z * (sz + 0.22)))
                    box(tuple(c), 0.09, 0.09, 0.09, m_, "handle")
        self.me.clear_geometry()
        if verts:
            self.me.from_pydata([tuple(v) for v in verts], [], faces)
            for p, k in zip(self.me.polygons, mi):
                p.material_index = k
        self.me.update()
