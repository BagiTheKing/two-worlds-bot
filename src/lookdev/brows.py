"""Steve's eyebrows as the reference draws them: thick dark-brown bars standing
a little off the face, rounded at the ends, gently arched, a touch thicker at
the inner end. Each brow is one small mesh with shape keys (animatable, also
negative):
  raise    up 1 px            tilt   inner end down / outer up (angry; - worried)
  arch     middle up 0.5 px   curl   outer end bends down (the reference's curved brows)
  squeeze  toward the nose 0.5 px (a frown)
In px on the face plate (8 x 8, origin bottom-left), in the Head bone's space."""
import bmesh
import bpy

from faceplate import EYES, EYE_DEFAULTS

P = 0.1
LEN = 2.2                         # short enough to leave a clear gap over the nose
T_IN, T_OUT = 0.6, 0.52            # not heavy at the inner end: a friendly face
DEPTH = 0.17
BASE_Y = 4.85                    # the brow's centre line, just above the eyes
ARCH0 = 0.16                      # a gentle arch at rest
REST_LIFT = 0.14                  # inner ends a touch higher than the outer: open, likable
N = 12


def _brow_mesh(name, cx, inner_dir):
    """Vertices along the brow from the outer end (k=0) to the inner (k=N)."""
    bm = bmesh.new()
    cols = []
    for k in range(N + 1):
        t = k / N                                      # 0 outer .. 1 inner
        x = cx + (t - 0.5) * LEN * inner_dir
        s = 2 * t - 1
        yc = BASE_Y + ARCH0 * (1 - s * s) + REST_LIFT * t
        th = T_OUT + (T_IN - T_OUT) * t
        col = []
        for dy in (-th / 2, th / 2):
            for d in (0.0, DEPTH):
                # bone space: x = out of the face (negative), y = up, z = screen right
                col.append(bm.verts.new((-0.4 - 0.004 - d * P - 0.001, (yc + dy) * P, (x - 4) * P)))
        cols.append(col)
    faces = []
    for k in range(N):
        a, b = cols[k], cols[k + 1]
        # vertex order in a column: 0 bottom-back, 1 bottom-front, 2 top-back, 3 top-front
        faces += [(a[1], b[1], b[3], a[3]),            # front
                  (a[2], b[2], b[0], a[0]),            # back
                  (a[3], b[3], b[2], a[2]),            # top
                  (a[0], b[0], b[1], a[1])]            # bottom
    faces += [(cols[0][0], cols[0][1], cols[0][3], cols[0][2]),
              (cols[N][2], cols[N][3], cols[N][1], cols[N][0])]
    for f in faces:
        bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _keys(ob, cx, inner_dir):
    ob.shape_key_add(name="Basis")
    me = ob.data
    base = [v.co.copy() for v in me.vertices]

    def add(name, fn, lo=-1.5, hi=1.5):
        kb = ob.shape_key_add(name=name, from_mix=False)
        kb.slider_min, kb.slider_max = lo, hi
        for i, co in enumerate(base):
            x_px = co.z / P + 4                       # back to face px
            t = ((x_px - cx) * inner_dir) / LEN + 0.5  # 0 outer .. 1 inner
            du, dx = fn(t)
            kb.data[i].co = (co.x, co.y + du * P, co.z + dx * inner_dir * P)
        return kb

    add("raise", lambda t: (1.0, 0.0))
    add("tilt", lambda t: (-(t - 0.5) * 1.0, 0.0))                 # +1: inner 0.5 px down, outer 0.5 up
    add("arch", lambda t: (0.5 * (1 - (2 * t - 1) ** 2), 0.0))
    add("curl", lambda t: (-0.55 * max(0.0, 0.45 - t) ** 2 / 0.2025, 0.0))
    add("squeeze", lambda t: (0.0, 0.5))


def brow_material(name="steve_brow"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = (44, 25, 14)
    b.inputs["Base Color"].default_value = tuple(((v / 255 + 0.055) / 1.055) ** 2.4 for v in c) + (1,)
    b.inputs["Roughness"].default_value = 0.62
    b.inputs["Specular IOR Level"].default_value = 0.22
    return m


def build_brows(arm, lattice=None, bone="Head"):
    from mathutils import Matrix
    mat = brow_material()
    out = {}
    for e, inner_dir in (("eR", 1.0), ("eL", -1.0)):
        cx = EYES[e] + EYE_DEFAULTS["cx"] - 0.26 * inner_dir     # toward the outside: the brows never meet
        name = "brow_" + e
        ob = bpy.data.objects.new(name, _brow_mesh(name, cx, inner_dir))
        ob.data.materials.append(mat)
        for col in arm.users_collection:
            col.objects.link(ob)
        ob.parent = arm
        ob.parent_type = "BONE"
        ob.parent_bone = bone
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.location = (0, -arm.data.bones[bone].length, 0)
        _keys(ob, cx, inner_dir)
        bv = ob.modifiers.new("round", "BEVEL")
        bv.width = 0.018
        bv.segments = 3
        bv.limit_method = "NONE"
        if lattice is not None:
            ob.modifiers.new("head_lattice", "LATTICE").object = lattice
        out[e] = ob
    return out


def set_brows(brows, values):
    """values: {"bR_raise": 0.3, "bb_tilt": 0.6, ...} (bR = on-screen left brow, bL right, bb both)."""
    for k, v in values.items():
        side, key = k.split("_", 1)
        targets = {"bR": ["eR"], "bL": ["eL"], "bb": ["eR", "eL"]}.get(side)
        if targets is None:
            continue
        for e in targets:
            kb = brows[e].data.shape_keys.key_blocks.get(key)
            if kb is not None:
                kb.value = v
