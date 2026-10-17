"""
The cast as Blender rigs: every part is a box with its pivot at the joint
(neck, shoulders, hips), parented to a root empty at the feet. Characters
face -Y at rest. A pose is a plain dict, and `key_pose` writes one per frame,
so choreography is ordinary Python maths over time.

Two deliberately different looks:
  steve  matte, pixel-textured, hard edges (the Minecraft side)
  noob   smooth bevelled plastic with a clear-coat shine (the Roblox side)
"""

from kit.blocks import box, empty, material

PARTS = ("torso", "head", "arm_r", "arm_l", "leg_r", "leg_l")


def srgb(c):
    """0-255 sRGB to linear 0-1, so plain colours match the textures."""
    def one(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(one(v) for v in c)


class Rig:
    def __init__(self, name, root, parts, rest):
        self.name, self.root, self.parts, self.rest = name, root, parts, rest

    def key_pose(self, frame, pose):
        r = self.root
        r.location = pose.get("loc", (0, 0, 0))
        tx, ty = pose.get("tilt", (0.0, 0.0))
        r.rotation_euler = (tx, ty, pose.get("yaw", 0.0))
        r.scale = pose.get("scale", (1, 1, 1))
        for path in ("location", "rotation_euler", "scale"):
            r.keyframe_insert(path, frame=frame)
        for p in PARTS:
            ob = self.parts[p]
            ob.rotation_euler = pose.get(p, (0, 0, 0))
            ob.keyframe_insert("rotation_euler", frame=frame)


def make_steve(tex, name="steve"):
    from textures import SKIN, HAIR, SHIRT, PANTS, SHOE
    face = material(f"{name}_face", tex=tex["steve_face"])
    side = material(f"{name}_head_side", tex=tex["steve_head_side"])
    hair = material(f"{name}_hair", tex=tex["hair"])
    skin = material(f"{name}_skin", srgb(SKIN))
    shirt_t = material(f"{name}_shirt_tex", tex=tex["shirt"])
    shirt = material(f"{name}_shirt", srgb(SHIRT))
    arm = material(f"{name}_arm", tex=tex["steve_arm"])
    leg = material(f"{name}_leg", tex=tex["steve_leg"])
    pants = material(f"{name}_pants", srgb(PANTS))
    shoe = material(f"{name}_shoe", srgb(SHOE))

    root = empty(name)
    parts = {}
    parts["torso"] = empty(f"{name}_torso", (0, 0, 0.75), root)
    box(f"{name}_body", (0.5, 0.25, 0.75), (0, 0, 0.375),
        {"front": shirt_t, "default": shirt}, parts["torso"])
    parts["head"] = empty(f"{name}_head", (0, 0, 1.5), root)
    box(f"{name}_skull", (0.5, 0.5, 0.5), (0, 0, 0.25),
        {"front": face, "left": side, "right": side, "back": hair, "top": hair,
         "bottom": skin, "default": skin}, parts["head"])
    for tag, x in (("arm_r", -0.375), ("arm_l", 0.375)):
        parts[tag] = empty(f"{name}_{tag}", (x, 0, 1.5), root)
        box(f"{name}_{tag}_box", (0.25, 0.25, 0.75), (0, 0, -0.375),
            {"top": shirt, "bottom": skin, "default": arm}, parts[tag])
    for tag, x in (("leg_r", -0.125), ("leg_l", 0.125)):
        parts[tag] = empty(f"{name}_{tag}", (x, 0, 0.75), root)
        box(f"{name}_{tag}_box", (0.25, 0.25, 0.75), (0, 0, -0.375),
            {"top": pants, "bottom": shoe, "default": leg}, parts[tag])

    # pickaxe in the left hand (the side away from most cameras), tilted forward and up
    stick = material(f"{name}_stick", srgb((120, 86, 50)))
    metal = material(f"{name}_pick", srgb((150, 190, 200)), rough=0.4, spec=0.6)
    tool = empty(f"{name}_pickaxe", (0, -0.05, -0.68), parts["arm_l"])
    tool.rotation_euler = (1.05, 0, 0)
    box(f"{name}_handle", (0.07, 0.07, 0.7), (0, 0, 0.12), {"default": stick}, tool)
    for i, (y, z) in enumerate(((0, 0.47), (-0.1, 0.46), (0.1, 0.46), (-0.2, 0.43),
                                (0.2, 0.43), (-0.28, 0.38), (0.28, 0.38))):
        box(f"{name}_pick_{i}", (0.07, 0.1, 0.08), (0, y, z), {"default": metal}, tool)
    return Rig(name, root, parts, {})


def make_r6(name, mats, s=1.0, bevel=0.035, head_bevel=0.07):
    """Roblox-style blocky body (2-stud legs and torso, 1-stud arms), `s`
    times the Noob's size. mats: torso, head, face, arm_r, arm_l, leg_r,
    leg_l, and optionally torso_l (a left half with its own material)."""
    root = empty(name)
    parts = {}
    parts["torso"] = empty(f"{name}_torso", (0, 0, 0.8 * s), root)
    if "torso_l" in mats:
        box(f"{name}_body_r", (0.4 * s, 0.4 * s, 0.8 * s), (-0.2 * s, 0, 0.4 * s),
            {"default": mats["torso"]}, parts["torso"], bevel=bevel * s)
        box(f"{name}_body_l", (0.4 * s, 0.4 * s, 0.8 * s), (0.2 * s, 0, 0.4 * s),
            {"default": mats["torso_l"]}, parts["torso"], bevel=bevel * s)
    else:
        box(f"{name}_body", (0.8 * s, 0.4 * s, 0.8 * s), (0, 0, 0.4 * s),
            {"default": mats["torso"]}, parts["torso"], bevel=bevel * s)
    parts["head"] = empty(f"{name}_head", (0, 0, 1.6 * s), root)
    box(f"{name}_skull", (0.5 * s, 0.46 * s, 0.44 * s), (0, 0, 0.24 * s),
        {"front": mats["face"], "default": mats["head"]}, parts["head"], bevel=head_bevel * s)
    for tag, x in (("arm_r", -0.6), ("arm_l", 0.6)):
        parts[tag] = empty(f"{name}_{tag}", (x * s, 0, 1.6 * s), root)
        box(f"{name}_{tag}_box", (0.4 * s, 0.4 * s, 0.8 * s), (0, 0, -0.4 * s),
            {"default": mats[tag]}, parts[tag], bevel=bevel * s)
    for tag, x in (("leg_r", -0.2), ("leg_l", 0.2)):
        parts[tag] = empty(f"{name}_{tag}", (x * s, 0, 0.8 * s), root)
        box(f"{name}_{tag}_box", (0.4 * s, 0.4 * s, 0.8 * s), (0, 0, -0.4 * s),
            {"default": mats[tag]}, parts[tag], bevel=bevel * s)
    return Rig(name, root, parts, {})


def make_noob(tex, name="noob", shirt=(30, 100, 220), pants=(96, 182, 50),
              skin=None, s=1.0):
    from textures import NOOB_YELLOW
    plastic = dict(rough=0.32, spec=0.5, coat=0.35)
    skin = material(f"{name}_skin", srgb(skin or NOOB_YELLOW), **plastic)
    face = material(f"{name}_face", tex=tex["noob_face"], smooth_tex=True, **plastic)
    top = material(f"{name}_shirt", srgb(shirt), **plastic)
    bottom = material(f"{name}_pants", srgb(pants), **plastic)
    return make_r6(name, {"torso": top, "head": skin, "face": face, "arm_r": skin,
                          "arm_l": skin, "leg_r": bottom, "leg_l": bottom}, s)


def make_null(tex, name="null", s=9.0):
    """Half pixel-block, half plastic, with a missing-texture face. Built
    from the Noob's own proportions (it is made of him)."""
    pixel = material(f"{name}_pixel", tex=tex["null"], rough=0.8,
                     emit_tex=True, strength=0.7)
    plastic = material(f"{name}_plastic", srgb((12, 10, 18)), rough=0.3, spec=0.6, coat=0.5)
    face = material(f"{name}_face", tex=tex["missing"], emit_tex=True, strength=0.9)
    return make_r6(name, {"torso": plastic, "torso_l": pixel, "head": plastic,
                          "face": face, "arm_r": plastic, "arm_l": pixel,
                          "leg_r": plastic, "leg_l": pixel}, s,
                   bevel=0.03, head_bevel=0.05)
