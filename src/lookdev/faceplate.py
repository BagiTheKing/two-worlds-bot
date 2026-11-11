"""Steve's face plate: a thin layer over the front of the head that draws his
skin, eyes and mouth with a shader, every shape set by animatable values.

Modelled on the reference animation's face (studied frame by frame):
  eyes   white openings bounded by a top lid and a bottom lid, each lid a
         curve through three heights (outer corner, middle, inner corner), so
         one eye can be wide, angry (inner top low), suspicious (top flat and
         low), smug (bottom raised), happy (bottom arched up), sad (outer top
         low), closed...; a soft shadow under the top lid (the white sits
         inside the head); a square pupil with a thin brown rim and a white
         catchlight, cut off by the lids, free to look anywhere.
  mouth  a dark opening: width, how open, smile/frown of the corners,
         roundness (square to O), how far the bottom drops, top and bottom
         teeth, tongue, side shift; closed it is a thin curved line.

All values live as custom properties on the plate object (keyframe them to
animate); px units, origin at the bottom-left of the face, 8 x 8 px.
"""
import bpy

# ----------------------------------------------------------------- node maths
class N:
    """A shader-node value with operators, so the face can be written as maths."""
    nt = None

    def __init__(self, sock):
        self.s = sock

    @staticmethod
    def _sock(x):
        return x.s if isinstance(x, N) else x

    @classmethod
    def math(cls, op, a, b=None, c=None):
        node = cls.nt.nodes.new("ShaderNodeMath")
        node.operation = op
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            x = cls._sock(x)
            if isinstance(x, (int, float)):
                node.inputs[i].default_value = float(x)
            else:
                cls.nt.links.new(x, node.inputs[i])
        return N(node.outputs[0])

    def __add__(self, o): return N.math("ADD", self, o)
    def __radd__(self, o): return N.math("ADD", o, self)
    def __sub__(self, o): return N.math("SUBTRACT", self, o)
    def __rsub__(self, o): return N.math("SUBTRACT", o, self)
    def __mul__(self, o): return N.math("MULTIPLY", self, o)
    def __rmul__(self, o): return N.math("MULTIPLY", o, self)
    def __truediv__(self, o): return N.math("DIVIDE", self, o)
    def __neg__(self): return N.math("MULTIPLY", self, -1.0)


def gt(a, b): return N.math("GREATER_THAN", a, b)          # 1 where a > b
def lt(a, b): return N.math("LESS_THAN", a, b)
def mn(a, b): return N.math("MINIMUM", a, b)
def mx(a, b): return N.math("MAXIMUM", a, b)
def ab(a): return N.math("ABSOLUTE", a)
def clamp01(a): return mx(mn(a, 1.0), 0.0)


def mix(fac, c0, c1):
    """Colour c0 where fac is 0, c1 where 1 (colours: tuples or colour sockets)."""
    node = N.nt.nodes.new("ShaderNodeMix")
    node.data_type = "RGBA"
    N.nt.links.new(N._sock(fac), node.inputs["Factor"])
    for name, c in (("A", c0), ("B", c1)):
        c = N._sock(c)
        if isinstance(c, tuple):
            node.inputs[name].default_value = (*c, 1.0)
        else:
            N.nt.links.new(c, node.inputs[name])
    return N(node.outputs["Result"])


def prop(name):
    a = N.nt.nodes.new("ShaderNodeAttribute")
    a.attribute_type = "OBJECT"
    a.attribute_name = name
    return N(a.outputs["Fac"])


def lerp3(s, o, m, i):
    """The curve through (s=-1, o), (0, m), (1, i)."""
    return m + (i - o) * 0.5 * s + ((i + o) * 0.5 - m) * s * s


# ------------------------------------------------------------------ defaults
EYE_DEFAULTS = {"cx": 0.0, "cy": 3.85, "w": 2.3, "h": 1.55, "open": 1.0,
                "to": 0.0, "tm": 0.0, "ti": 0.0, "bo": 0.0, "bm": 0.0, "bi": 0.0,
                "px": 0.0, "py": 0.0, "ps": 1.0}
EYES = {"eR": 2.3, "eL": 5.7}                 # on screen left (his right) and right
MOUTH_DEFAULTS = {"m_cx": 4.0, "m_cy": 1.5, "m_k": 1.18, "m_w": 1.9, "m_o": 0.0, "m_arch": 0.06, "m_up": 0.7,
                  "m_r": 0.3, "m_vee": 0.0, "m_tilt": 0.0, "m_tu": 0.0, "m_tl": 0.0, "m_tg": 0.0}

WHITE = (0.98, 0.95, 0.98)
WHITE_SHADE = (0.62, 0.54, 0.6)
PUPIL = (0.012, 0.01, 0.01)
IRIS = (0.2, 0.085, 0.03)
SHINE = (1.0, 1.0, 1.0)
CAVITY = (0.008, 0.003, 0.003)
TEETH = (0.96, 0.95, 0.94)
TONGUE = (0.55, 0.16, 0.16)
LIDLINE = (0.12, 0.05, 0.03)


GLOSSY_EYES = False                               # the Noob's eyes as wet glass domes that mirror the world (part 7)
EYEMASK = []
GLOW = []                                         # (mask, colour) pairs the face adds as a faint glow


def _eye(X, Y, e, inner_dir, base):
    """Colour of one eye drawn over `base`; returns the new colour socket."""
    P = {k: prop(f"{e}_{k}") for k in EYE_DEFAULTS}
    cx = P["cx"] + EYES[e]
    hw = P["w"] * 0.5
    s = (X - cx) / hw * inner_dir                 # -1 outer corner .. +1 inner corner
    yy = Y - P["cy"]
    half = P["h"] * 0.5 * P["open"]
    top = half + lerp3(s, P["to"], P["tm"], P["ti"]) * P["open"]
    bot = -half + lerp3(s, P["bo"], P["bm"], P["bi"]) * P["open"]
    inside = lt(ab(s), 1.0) * gt(top, yy) * gt(yy, bot)
    # rounded corners (radius r): cut where near a side and near the top or bottom lid
    r = 0.26
    d_side = (1.0 - ab(s)) * hw
    for d_lid in (top - yy, yy - bot):
        a_ = mx(r - d_side, 0.0)
        b_ = mx(r - d_lid, 0.0)
        inside = inside * lt(a_ * a_ + b_ * b_, r * r)
    # the white: shaded just under the top lid (it sits inside the head) and a touch at the bottom
    shade = clamp01((top - yy) / 0.26)
    col = mix(shade, WHITE_SHADE, WHITE)
    # pupil: a square, thin brown rim, a catchlight up and toward the outside of the frame
    pxc = cx + P["px"]
    pyc = P["cy"] + P["py"] + 0.02
    pr = P["ps"] * 0.39
    dx = ab(X - pxc)
    dy = ab(Y - pyc)
    in_p = lt(dx, pr) * lt(dy, pr * 1.18)
    in_core = lt(dx, pr - 0.065) * lt(dy, pr * 1.18 - 0.065)
    pc = mix(in_core, IRIS, PUPIL)
    sx = X - (pxc + pr * 0.42)
    sy = Y - (pyc + pr * 0.62)
    in_shine = lt(ab(sx), 0.12 * P["ps"]) * lt(ab(sy), 0.12 * P["ps"])
    pc = mix(in_shine * in_core, pc, SHINE)
    col = mix(in_p, col, pc)
    GLOW.append(inside * (1.0 - in_p) * clamp01((top - yy) / 0.3))
    above = lt(ab(s), 1.02) * gt(yy, top) * lt(yy - top, 0.09) * (1.0 - inside)
    out = mix(above * 0.55, base, (0.16, 0.08, 0.05))
    out = mix(inside, out, col)
    # closed: a thin lid line where the eye was
    shut = lt(P["open"], 0.12) * lt(ab(s), 0.95) * lt(ab(yy + 0.08), 0.07)
    return mix(shut, out, LIDLINE)


NOOB_EYES = {"eR": 2.8, "eL": 5.2}
NOOB_EYE_DEFAULTS = {"cx": 0.0, "cy": 4.5, "w": 0.95, "h": 1.65, "open": 1.0,
                     "to": 0.0, "tm": 0.0, "ti": 0.0, "bo": 0.0, "bm": 0.0, "bi": 0.0,
                     "px": 0.0, "py": 0.0, "ps": 1.0}
NOOB_MOUTH = {"m_cy": 2.45, "m_w": 1.85, "m_arch": -0.36, "m_k": 1.25}
NOOB_EYE = (0.012, 0.01, 0.01)


def _eye_noob(X, Y, e, inner_dir, base):
    """The Noob's eye, Roblox style: a glossy black oval with a white shine;
    lids (his yellow skin) can cut it from the top and the bottom along the same
    three-point curves as Steve's (outer, middle, inner), so it can squint, glare,
    look sad or happy; gaze moves the whole oval a little."""
    P = {k: prop(f"{e}_{k}") for k in NOOB_EYE_DEFAULTS}
    cx = P["cx"] + NOOB_EYES[e] + P["px"] * 0.28
    cy = P["cy"] + P["py"] * 0.22
    rx = P["w"] * 0.5
    ry = P["h"] * 0.5
    dx = (X - cx) / rx
    dy = (Y - cy) / ry
    oval = lt(dx * dx + dy * dy, 1.0)
    s = dx * inner_dir                                  # -1 outer .. +1 inner
    top = cy - ry + 2 * ry * P["open"] + lerp3(s, P["to"], P["tm"], P["ti"]) * P["open"]
    bot = cy - ry + lerp3(s, P["bo"], P["bm"], P["bi"]) * P["open"]
    inside = oval * gt(top, Y) * gt(Y, bot)
    col = mix(clamp01((top - Y) / 0.25), (0.06, 0.05, 0.05), NOOB_EYE)
    # the shine: a white oval up and toward the outside of the frame, and a small dot under it
    hx = (X - (cx + rx * 0.32)) / (0.16 * P["ps"])
    hy = (Y - (cy + ry * 0.45)) / (0.22 * P["ps"])
    shine = lt(hx * hx + hy * hy, 1.0)
    h2x = (X - (cx - rx * 0.25)) / (0.07 * P["ps"])
    h2y = (Y - (cy - ry * 0.35)) / (0.07 * P["ps"])
    shine = mx(shine, lt(h2x * h2x + h2y * h2y, 1.0))
    col = mix(shine, col, (0.95, 0.95, 0.95))
    GLOW.append(inside * shine)
    if GLOSSY_EYES:
        EYEMASK.append((inside, dx, dy))
    out = mix(inside, base, col)
    # closed: a thin dark curve
    shut = lt(P["open"], 0.12) * lt(ab(dx), 0.95) * lt(ab(Y - (cy - ry * 0.35) - 0.12 * (1 - dx * dx)), 0.06)
    return mix(shut, out, (0.03, 0.025, 0.02))


def _mouth(X, Y):
    """The reference's mouth: an opening cut into the face, built from arcs.
    m_w width; m_o how open (px at the centre); m_arch bends the whole mouth
    (+ frown, centre up; - smile, centre down); m_up how much of the opening
    is above the line (1 = flat bottom and domed top, as when shouting;
    0.5 = a lens); m_r corner shape (0 pointed lens, 1 round); m_tilt lifts one
    corner (smirk); m_tu / m_tl top / bottom teeth showing; m_tg tongue.
    Closed, it is a thin dark line tapering at the corners."""
    M = {k: prop(k) for k in MOUTH_DEFAULTS}
    hw = M["m_w"] * 0.5 * M["m_k"]
    s = (X - M["m_cx"]) / hw
    s2 = s * s
    edge = clamp01(1.0 - s2)
    root = N.math("POWER", edge, 0.5)
    st = s                                                       # (kept for the teeth span)
    a4 = s2 * s2
    loaf = N.math("POWER", clamp01(1.0 - a4), 0.25)            # flat top, rounded shoulders
    ramp = clamp01((1.0 - ab(s)) / mx(M["m_vee"], 0.04))         # sides sloping in to the corners
    prof = (1.0 - M["m_r"]) * edge + M["m_r"] * mn(loaf, ramp)
    profb = (1.0 - M["m_r"]) * edge + M["m_r"] * root
    base = M["m_cy"] + M["m_arch"] * edge + M["m_tilt"] * s
    line = 0.055 * N.math("POWER", edge, 0.35)                  # the closed line's half thickness, tapering
    up = base + M["m_o"] * M["m_k"] * M["m_up"] * prof + line
    lo = base - M["m_o"] * M["m_k"] * (1.0 - M["m_up"]) * profb - line
    inside = lt(ab(s), 1.0) * gt(up, Y) * gt(Y, lo)
    height = up - lo
    col = mix(clamp01((up - Y) / 0.3), (0.03, 0.01, 0.01), CAVITY)
    # teeth: thin slivers following the lips, as in the reference (clenched, they fill the gap)
    teeth_u = lt(up - Y, M["m_tu"] * 0.13) * lt(ab(st), 1.0 - mx(M["m_vee"], 0.12) - 0.12)
    teeth_l = lt(Y - lo, M["m_tl"] * 0.11) * lt(ab(s), 0.9)
    tcol = mix(clamp01((up - Y) / 0.06), (0.7, 0.68, 0.7), TEETH)
    col = mix(mx(teeth_u, teeth_l), col, tcol)
    # tongue: a flat pink band resting on the bottom lip
    tx = (X - M["m_cx"]) / mx(hw * 0.72, 0.01)
    ty = (Y - lo) / mx(0.26 * M["m_tg"], 0.001)
    in_tongue = gt(M["m_tg"], 0.01) * lt(tx * tx + ty * ty, 1.0) * (1.0 - teeth_l) * (1.0 - teeth_u)
    col = mix(in_tongue, col, mix(clamp01(ty), (0.45, 0.12, 0.13), TONGUE))
    # the rim: a faint shadow around the opening, so it reads cut into the face
    rim = lt(ab(s), 1.04) * (1.0 - inside) * lt(Y - up, 0.06) * gt(Y - lo, -0.06)
    GLOW.append(inside * mx(teeth_u, teeth_l) * 0.8)
    return inside, rim, col


def face_material(skin_image, name="steve_face", style="steve"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N.nt = nt
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    uv = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    X = N(sep.outputs["X"]) * 8.0
    Y = N(sep.outputs["Y"]) * 8.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = skin_image
    tex.interpolation = "Closest"
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    col = N(tex.outputs["Color"])
    eye = _eye_noob if style == "noob" else _eye
    col = eye(X, Y, "eR", 1.0, col)
    col = eye(X, Y, "eL", -1.0, col)
    m_in, m_rim, m_col = _mouth(X, Y)
    col = mix(m_rim * 0.35, col, (0.36, 0.26, 0.03) if style == "noob" else (0.2, 0.09, 0.06))
    col = mix(m_in, col, m_col)
    nt.links.new(col.s, bsdf.inputs["Base Color"])
    glow = GLOW[0]
    for g_ in GLOW[1:]:
        glow = mx(glow, g_)
    GLOW.clear()
    nt.links.new(mix(glow, (0, 0, 0), (1.0, 0.96, 1.0)).s, bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.22
    if style == "noob":                               # smooth plastic; the eyes and mouth glossier still
        bsdf.inputs["Roughness"].default_value = 0.32
        bsdf.inputs["Specular IOR Level"].default_value = 0.5
        if EYEMASK:                                   # the eyes: mirror-smooth domes (the world curves across them)
            m_ = None
            h_ = None
            for ins, dx_, dy_ in EYEMASK:
                dome = N.math("SQRT", clamp01(1.0 - dx_ * dx_ - dy_ * dy_)) * ins
                m_ = ins if m_ is None else mx(m_, ins)
                h_ = dome if h_ is None else mx(h_, dome)
            nt.links.new((0.32 - 0.31 * m_).s, bsdf.inputs["Roughness"])
            nt.links.new((0.5 + 0.5 * m_).s, bsdf.inputs["Specular IOR Level"])
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.25
            bump.inputs["Distance"].default_value = 0.06
            nt.links.new(h_.s, bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
            # and a real mirror over the pupils (a dark dielectric alone reflects too little head-on)
            gl = nt.nodes.new("ShaderNodeBsdfGlossy")
            gl.inputs["Color"].default_value = (0.62, 0.6, 0.66, 1)
            gl.inputs["Roughness"].default_value = 0.03
            nt.links.new(bump.outputs["Normal"], gl.inputs["Normal"])
            out_ = nt.nodes["Material Output"]
            mxs = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new((m_ * 0.7).s, mxs.inputs[0])
            nt.links.new(bsdf.outputs["BSDF"], mxs.inputs[1])
            nt.links.new(gl.outputs["BSDF"], mxs.inputs[2])
            nt.links.new(mxs.outputs[0], out_.inputs["Surface"])
            EYEMASK.clear()
    EYEMASK.clear()
    return m


def build_faceplate(arm, skin_image, lattice=None, bone="Head", name="steve_faceplate"):
    """A subdivided quad just in front of the face, in the Head bone's space
    (bone x = back, y = up, z = toward screen right; the face is at x = -0.4)."""
    import bmesh
    from mathutils import Matrix
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    n = 16
    vs = {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = i / n, j / n
            vs[i, j] = bm.verts.new((-0.4 - 0.004, v * 0.8, -0.4 + u * 0.8))
    for i in range(n):
        for j in range(n):
            f = bm.faces.new([vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]])
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uvl].uv = (a / n, b / n)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:                                  # face the camera side (-x in bone space)
        if f.normal.x > 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(face_material(skin_image, name + "_mat"))
    ob = bpy.data.objects.new(name, me)
    for col in arm.users_collection:
        col.objects.link(ob)
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.location = (0, -arm.data.bones[bone].length, 0)
    for e in EYES:
        for k, v in EYE_DEFAULTS.items():
            ob[f"{e}_{k}"] = v
    for k, v in MOUTH_DEFAULTS.items():
        ob[k] = v
    if lattice is not None:
        ob.modifiers.new("head_lattice", "LATTICE").object = lattice
    return ob


def set_face(ob, values):
    """values: {"eR_ti": -0.5, "both_ti": ..., "m_o": 1.0, ...}; "both_" sets both eyes."""
    for k, v in values.items():
        if k.startswith("both_"):
            for e in EYES:
                ob[f"{e}_{k[5:]}"] = v
        else:
            ob[k] = v


def flatten_face(head, arm, bone="Head", plane=-0.4005, name="flatten_face"):
    """The rig's old lips and mouth pocket poke out of the face: press anything
    in front of the face plane back onto it (in the Head bone's space), right
    after the armature, so the head lattice still squashes everything alike."""
    from mathutils import Matrix
    ref = bpy.data.objects.new(name + "_ref", None)
    for col in arm.users_collection:
        col.objects.link(ref)
    ref.parent = arm
    ref.parent_type = "BONE"
    ref.parent_bone = bone
    ref.matrix_parent_inverse = Matrix.Identity(4)
    ref.location = (0, -arm.data.bones[bone].length, 0)
    g = bpy.data.node_groups.new(name, "GeometryNodeTree")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nd = g.nodes
    gi, go = nd.new("NodeGroupInput"), nd.new("NodeGroupOutput")
    oi = nd.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = ref
    oi.transform_space = "RELATIVE"
    inv = nd.new("FunctionNodeInvertMatrix")
    pos = nd.new("GeometryNodeInputPosition")
    to_b = nd.new("FunctionNodeTransformPoint")
    sep = nd.new("ShaderNodeSeparateXYZ")
    mxn = nd.new("ShaderNodeMath")
    mxn.operation = "MAXIMUM"
    mxn.inputs[1].default_value = plane
    com = nd.new("ShaderNodeCombineXYZ")
    back = nd.new("FunctionNodeTransformPoint")
    sp = nd.new("GeometryNodeSetPosition")
    L = g.links.new
    L(oi.outputs["Transform"], inv.inputs["Matrix"])
    L(pos.outputs["Position"], to_b.inputs["Vector"])
    L(inv.outputs["Matrix"], to_b.inputs["Transform"])
    L(to_b.outputs["Vector"], sep.inputs[0])
    L(sep.outputs["X"], mxn.inputs[0])
    L(mxn.outputs[0], com.inputs["X"])
    # and nothing of the face may hang below the head (the old jaw): lift it to the bottom
    front = nd.new("ShaderNodeMath"); front.operation = "LESS_THAN"; front.inputs[1].default_value = -0.3
    below = nd.new("ShaderNodeMath"); below.operation = "SUBTRACT"; below.inputs[0].default_value = -0.002
    pos_ = nd.new("ShaderNodeMath"); pos_.operation = "MAXIMUM"; pos_.inputs[1].default_value = 0.0
    lift = nd.new("ShaderNodeMath"); lift.operation = "MULTIPLY"
    newy = nd.new("ShaderNodeMath"); newy.operation = "ADD"
    L(sep.outputs["X"], front.inputs[0])
    L(sep.outputs["Y"], below.inputs[1])
    L(below.outputs[0], pos_.inputs[0])
    L(pos_.outputs[0], lift.inputs[0])
    L(front.outputs[0], lift.inputs[1])
    L(sep.outputs["Y"], newy.inputs[0])
    L(lift.outputs[0], newy.inputs[1])
    L(newy.outputs[0], com.inputs["Y"])
    L(sep.outputs["Z"], com.inputs["Z"])
    L(com.outputs[0], back.inputs["Vector"])
    L(oi.outputs["Transform"], back.inputs["Transform"])
    L(gi.outputs[0], sp.inputs["Geometry"])
    L(back.outputs["Vector"], sp.inputs["Position"])
    L(sp.outputs["Geometry"], go.inputs[0])
    md = head.modifiers.new(name, "NODES")
    md.node_group = g
    arm_i = next(i for i, m in enumerate(head.modifiers) if m.type == "ARMATURE")
    head.modifiers.move(len(head.modifiers) - 1, arm_i + 1)
    return md
