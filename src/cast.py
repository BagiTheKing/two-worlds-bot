"""
The cast as Blender rigs: every part is a box with its pivot at the joint
(neck, shoulders, hips), parented to a root empty at the feet. Characters
face -Y at rest. A pose is a plain dict, and `key_pose` writes one per frame,
so choreography is ordinary Python maths over time.

Two deliberately different looks:
  steve  matte, pixel-textured, hard edges (the Minecraft side)
  noob   smooth bevelled plastic with a clear-coat shine (the Roblox side)
"""

from blocks import box, empty, material

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
        r.rotation_euler = (0, 0, pose.get("yaw", 0.0))
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


def make_noob(tex, name="noob"):
    from textures import NOOB_YELLOW
    yellow = srgb(NOOB_YELLOW)
    plastic = dict(rough=0.32, spec=0.5, coat=0.35)
    face = material(f"{name}_face", tex=tex["noob_face"], smooth_tex=True, **plastic)
    skin = material(f"{name}_yellow", yellow, **plastic)
    shirt = material(f"{name}_blue", srgb((30, 100, 220)), **plastic)
    pants = material(f"{name}_green", srgb((96, 182, 50)), **plastic)

    root = empty(name)
    parts = {}
    parts["torso"] = empty(f"{name}_torso", (0, 0, 0.8), root)
    box(f"{name}_body", (0.8, 0.4, 0.8), (0, 0, 0.4), {"default": shirt},
        parts["torso"], bevel=0.035)
    parts["head"] = empty(f"{name}_head", (0, 0, 1.6), root)
    box(f"{name}_skull", (0.5, 0.46, 0.44), (0, 0, 0.24), {"front": face, "default": skin},
        parts["head"], bevel=0.07)
    for tag, x in (("arm_r", -0.6), ("arm_l", 0.6)):
        parts[tag] = empty(f"{name}_{tag}", (x, 0, 1.6), root)
        box(f"{name}_{tag}_box", (0.4, 0.4, 0.8), (0, 0, -0.4), {"default": skin},
            parts[tag], bevel=0.035)
    for tag, x in (("leg_r", -0.2), ("leg_l", 0.2)):
        parts[tag] = empty(f"{name}_{tag}", (x, 0, 0.8), root)
        box(f"{name}_{tag}_box", (0.4, 0.4, 0.8), (0, 0, -0.4), {"default": pants},
            parts[tag], bevel=0.035)
    return Rig(name, root, parts, {})
