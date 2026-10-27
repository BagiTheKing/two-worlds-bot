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


def face_plates(tex, who, name, head, size, center, smooth=False, alpha=False, **shade):
    """One thin plate per expression on the front of the head, all hidden but
    one (build_episode keys which). Marked so actor visibility keys skip them."""
    plates = {}
    prefix = f"{who}_face_"
    for key in sorted(k for k in tex if k.startswith(prefix)):
        expr = key[len(prefix):]
        m = material(f"{name}_{key}", tex=tex[key], smooth_tex=smooth, alpha_tex=alpha, **shade)
        ob = box(f"{name}_plate_{expr}", size, center, {"default": m}, head)
        ob["face_plate"] = 1
        plates[expr] = ob
    return plates


def make_steve(tex, name="steve", faces=False):
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
    rig = Rig(name, root, parts, {})
    if faces:          # the pixel face, swappable: just in front of the skull's front
        rig.faces = face_plates(tex, "steve", name, parts["head"], (0.5, 0.002, 0.5), (0, -0.2512, 0.25))
    return rig


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
              skin=None, s=1.0, faces=False):
    from textures import NOOB_YELLOW
    plastic = dict(rough=0.32, spec=0.5, coat=0.35)
    skin = material(f"{name}_skin", srgb(skin or NOOB_YELLOW), **plastic)
    # with acting faces, the head is plain and a plate always carries the features
    face = skin if faces else material(f"{name}_face", tex=tex["noob_face"], smooth_tex=True, **plastic)
    top = material(f"{name}_shirt", srgb(shirt), **plastic)
    bottom = material(f"{name}_pants", srgb(pants), **plastic)
    rig = make_r6(name, {"torso": top, "head": skin, "face": face, "arm_r": skin,
                         "arm_l": skin, "leg_r": bottom, "leg_l": bottom}, s)
    if faces:          # on the flat part of the bevelled head (the textures are cropped to it)
        rig.faces = face_plates(tex, "noob", name, rig.parts["head"], (0.36 * s, 0.002, 0.30 * s),
                                (0, -0.2315 * s, 0.24 * s), smooth=True, alpha=True, **plastic)
        rig.rest_face = "neutral"              # the plain head needs a face between expressions
    return rig


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


class DragonRig(Rig):
    """A flying dragon. The root sits at the middle of the body; the wings,
    neck and tail move on their own (flapping, a travelling wave down the
    tail), driven by the pose's time "t", so freezing time freezes them too.
    Pose keys: "head", "jaw" (open, 0, 0), "neck" (bend, 0, turn),
    "flap" (amplitude, beats per second, 0), "tail" (droop, 0, sway)."""
    NECK, TAIL = 3, 5

    def key_pose(self, frame, pose):
        import math
        t = pose.get("t", (frame - 1) / 24)
        amp, rate = pose.get("flap", self.rest["flap"])[:2]
        # the beat's phase adds up frame by frame, so a change of speed
        # (or a freeze, where time stops) never jumps the wings
        last = getattr(self, "_t", None)
        self._ph = getattr(self, "_ph", 0.0) + (2 * math.pi * rate * (t - last) if last is not None else 0.0)
        self._t = t
        ph = self._ph
        r = self.root
        x, y, z = pose.get("loc", (0, 0, 0))
        r.location = (x, y, z - 0.22 * self.s * amp * math.sin(ph))   # the body rises on each downstroke
        tx, ty = pose.get("tilt", (0.0, 0.0))
        r.rotation_euler = (tx, ty, pose.get("yaw", 0.0))
        r.scale = pose.get("scale", (1, 1, 1))
        for path in ("location", "rotation_euler", "scale"):
            r.keyframe_insert(path, frame=frame)

        down = amp * math.sin(ph)
        lag = amp * math.sin(ph - 0.9)
        rot = {"wing_r": (0, 0.12 + 0.7 * down, 0), "wing_l": (0, -(0.12 + 0.7 * down), 0),
               "wing_r_tip": (0, 0.1 + 0.45 * lag, 0), "wing_l_tip": (0, -(0.1 + 0.45 * lag), 0),
               "head": pose.get("head", (0, 0, 0)), "jaw": pose.get("jaw", (0, 0, 0))}
        bend, _, turn = pose.get("neck", (0, 0, 0))
        for i in range(self.NECK):
            rot[f"neck_{i}"] = (bend / self.NECK + 0.03 * math.sin(1.7 * t + i),
                                0, turn / self.NECK + 0.04 * math.sin(1.1 * t + i))
        droop, _, sway = pose.get("tail", (0, 0, 0))
        for i in range(self.TAIL):
            rot[f"tail_{i}"] = (droop / self.TAIL + 0.05 * math.sin(2 * math.pi * 0.8 * t - 0.8 * i),
                                0, sway / self.TAIL + 0.2 * math.sin(2 * math.pi * 0.6 * t - 0.7 * i))
        for k, v in rot.items():
            ob = self.parts[k]
            ob.rotation_euler = v
            ob.keyframe_insert("rotation_euler", frame=frame)


def make_dragon(tex, name="dragon", s=1.0):
    """A big blocky dragon from the survival world (our own design): black
    scales, violet eyes, a spiked back, two-part bat wings and a long tail.
    Faces -Y like the cast; about 16 units nose to tail at s=1."""
    hide = material(f"{name}_hide", tex=tex["dragon_hide"], rough=0.75)
    bone = material(f"{name}_bone", srgb((70, 66, 78)), rough=0.7)
    wing = material(f"{name}_wing", tex=tex["dragon_wing"], rough=0.85)
    eye = material(f"{name}_eye", tex=tex["dragon_eye"], emit_tex=True, strength=6.0)
    mouth = material(f"{name}_mouth", srgb((60, 14, 40)), rough=0.6)
    tooth = material(f"{name}_tooth", srgb((200, 196, 186)), rough=0.5)
    nostril = material(f"{name}_nostril", srgb((8, 6, 10)), rough=0.9)

    def b(n, size, center, parent, m=hide):
        return box(f"{name}_{n}", tuple(v * s for v in size), tuple(v * s for v in center),
                   {"default": m}, parent)

    root = empty(name)
    parts = {}
    body = empty(f"{name}_body", (0, 0, 0), root)
    b("chest", (2.4, 5.0, 2.0), (0, 0, 0), body)
    b("belly", (2.0, 3.6, 0.4), (0, 0.2, -1.15), body, bone)
    for i, yy in enumerate((-0.6, 0.3, 1.2, 2.0)):           # the spiked back (a gap at the shoulders to ride in)
        b(f"spike_{i}", (0.28, 0.6, 0.55), (0, yy, 1.27), body, bone)
    for i, (xx, yy) in enumerate(((-0.8, -1.6), (0.8, -1.6), (-0.8, 1.6), (0.8, 1.6))):
        leg = empty(f"{name}_leg_{i}", (xx * s, yy * s, -0.9 * s), body)   # legs tucked back in flight
        leg.rotation_euler = (-0.9, 0, 0)
        b(f"leg_{i}_box", (0.6, 0.6, 1.4), (0, 0, -0.7), leg)
        b(f"claw_{i}", (0.7, 0.9, 0.25), (0, -0.2, -1.45), leg, bone)

    # neck: a chain of blocks from the front of the chest, each joint bending a share
    prev, at = body, (0, -2.4, 0.4)
    for i in range(DragonRig.NECK):
        j = empty(f"{name}_neck_{i}", tuple(v * s for v in at), prev)
        parts[f"neck_{i}"] = j
        b(f"neck_{i}_box", (1.1 - 0.1 * i, 1.5, 1.1 - 0.1 * i), (0, -0.65, 0.05 * i), j)
        b(f"neck_spike_{i}", (0.22, 0.5, 0.4), (0, -0.6, 0.7 - 0.03 * i), j, bone)
        prev, at = j, (0, -1.3, 0.1)
    head = empty(f"{name}_head", (0, -1.3 * s, 0.2 * s), prev)
    parts["head"] = head
    b("skull", (1.8, 1.9, 1.3), (0, -0.7, 0.15), head)
    b("snout", (1.3, 1.6, 0.75), (0, -2.3, -0.02), head)
    for side in (-1, 1):
        b(f"horn_{side}", (0.25, 0.9, 0.25), (0.55 * side, 0.15, 0.95), head, bone)
        b(f"eye_{side}", (0.08, 0.5, 0.22), (0.92 * side, -1.05, 0.38), head, eye)
        b(f"eye_front_{side}", (0.5, 0.06, 0.2), (0.58 * side, -1.67, 0.5), head, eye)   # seen head-on
        b(f"brow_{side}", (0.4, 0.6, 0.15), (0.72 * side, -1.05, 0.62), head)
        b(f"nostril_{side}", (0.2, 0.12, 0.12), (0.35 * side, -3.08, 0.25), head, nostril)
    b("gum", (1.15, 1.5, 0.1), (0, -2.3, -0.42), head, mouth)
    jaw = empty(f"{name}_jaw", (0, -0.7 * s, -0.35 * s), head)
    parts["jaw"] = jaw
    b("jaw_box", (1.25, 2.4, 0.4), (0, -1.25, -0.2), jaw)
    b("tongue", (0.9, 2.0, 0.08), (0, -1.15, 0.03), jaw, mouth)
    for i in range(4):
        for side in (-1, 1):
            b(f"tooth_{i}_{side}", (0.12, 0.12, 0.22), (0.5 * side, -2.25 + 0.4 * i, 0.12), jaw, tooth)

    # wings: shoulder at the top of the chest; arm bone with membrane trailing
    # behind it, then the tip joint with the outer bone and membrane
    for tag, sx in (("wing_r", -1), ("wing_l", 1)):
        w = empty(f"{name}_{tag}", (1.15 * sx * s, -1.2 * s, 0.75 * s), body)
        parts[tag] = w
        b(f"{tag}_arm", (4.6, 0.38, 0.38), (2.3 * sx, 0, 0), w, bone)
        b(f"{tag}_skin", (4.6, 3.6, 0.07), (2.3 * sx, 1.8, -0.05), w, wing)
        tip = empty(f"{name}_{tag}_tip", (4.6 * sx * s, 0, 0), w)
        parts[f"{tag}_tip"] = tip
        b(f"{tag}_tip_arm", (4.4, 0.3, 0.3), (2.2 * sx, 0, 0), tip, bone)
        b(f"{tag}_tip_skin", (2.6, 3.0, 0.07), (1.3 * sx, 1.5, -0.05), tip, wing)
        b(f"{tag}_tip_skin2", (1.8, 1.8, 0.07), (3.5 * sx, 0.9, -0.05), tip, wing)
        b(f"{tag}_claw", (0.2, 0.5, 0.2), (4.4 * sx, -0.3, 0), tip, bone)

    prev, at = body, (0, 2.4, 0.2)
    for i in range(DragonRig.TAIL):
        j = empty(f"{name}_tail_{i}", tuple(v * s for v in at), prev)
        parts[f"tail_{i}"] = j
        w_ = 1.2 - 0.18 * i
        b(f"tail_{i}_box", (w_, 1.6, w_ * 0.85), (0, 0.8, 0), j)
        b(f"tail_spike_{i}", (0.18, 0.5, 0.35), (0, 0.8, w_ * 0.42 + 0.15), j, bone)
        prev, at = j, (0, 1.55, 0)
    b("tail_tip", (0.9, 0.9, 0.1), (0, 1.9, 0), prev, bone)

    rig = DragonRig(name, root, parts, {"flap": (1.0, 1.3, 0)})
    rig.s = s
    return rig


class PatchRig(Rig):
    """Patch, the glitch detector: a small floating cube with one eye. It
    bobs on its own; pose "scan" (weight, 0, 0) shows its scanning beam,
    "eye" (weight, 0, 0) turns the eye from cyan to glitching magenta."""
    CYAN, MAGENTA = (0.15, 0.95, 1.0, 1), (1.0, 0.1, 0.8, 1)

    def key_pose(self, frame, pose):
        import math
        t = pose.get("t", (frame - 1) / 24)
        r = self.root
        x, y, z = pose.get("loc", (0, 0, 0))
        r.location = (x, y, z + 0.05 * math.sin(2 * math.pi * 0.7 * t))
        tx, ty = pose.get("tilt", (0.0, 0.0))
        r.rotation_euler = (tx + 0.04 * math.sin(2 * math.pi * 0.45 * t), ty, pose.get("yaw", 0.0))
        r.scale = pose.get("scale", (1, 1, 1))
        for path in ("location", "rotation_euler", "scale"):
            r.keyframe_insert(path, frame=frame)
        scan = pose.get("scan", (0, 0, 0))[0] > 0.5
        glitch = pose.get("eye", (0, 0, 0))[0] > 0.5 and frame % 3 != 0    # a flickering glitch
        if getattr(self, "_scan", None) != scan:
            for ob in self.beam:
                ob.hide_render = not scan
                ob.keyframe_insert("hide_render", frame=frame)
            self._scan = scan
        if getattr(self, "_glitch", None) != glitch:
            col = self.MAGENTA if glitch else self.CYAN
            for sock in self.eye_sockets:
                if frame > 1:                # hold the old colour up to here: no slow blend between keys
                    sock.default_value = self.CYAN if glitch else self.MAGENTA
                    sock.keyframe_insert("default_value", frame=frame - 1)
                sock.default_value = col
                sock.keyframe_insert("default_value", frame=frame)
            self._glitch = glitch


def make_patch(tex, name="patch", s=1.0):
    """The glitch detector (arrives in episode 4): a small pale cube, a dark
    face panel with one round cyan eye, two tiny side fins."""
    shell = material(f"{name}_shell", srgb((222, 228, 236)), rough=0.3, spec=0.5, coat=0.4)
    panel = material(f"{name}_panel", srgb((24, 28, 38)), rough=0.25, spec=0.6)
    eye = material(f"{name}_eye", (0, 0, 0), emission=PatchRig.CYAN[:3], strength=3.5)
    beam = material(f"{name}_beam", (0, 0, 0), emission=PatchRig.CYAN[:3], strength=2.5)
    b = beam.node_tree.nodes["Principled BSDF"]
    b.inputs["Alpha"].default_value = 0.6
    if hasattr(beam, "surface_render_method"):
        beam.surface_render_method = "BLENDED"
    root = empty(name)
    body = empty(f"{name}_body", (0, 0, 0), root)
    box(f"{name}_cube", (0.42 * s, 0.42 * s, 0.42 * s), (0, 0, 0), {"default": shell}, body, bevel=0.04 * s)
    box(f"{name}_face", (0.32 * s, 0.01, 0.26 * s), (0, -0.212 * s, 0.01 * s), {"default": panel}, body)
    box(f"{name}_eye", (0.13 * s, 0.012, 0.13 * s), (0, -0.219 * s, 0.02 * s), {"default": eye}, body, bevel=0.05 * s)
    for side in (-1, 1):
        box(f"{name}_fin_{side}", (0.04 * s, 0.18 * s, 0.12 * s), (0.23 * s * side, 0.02, 0), {"default": shell}, body)
    # the scanning beam: a thin line of light from the eye, forward and a little down
    fan = empty(f"{name}_fan", (0, -0.22 * s, 0.02 * s), body)
    fan.rotation_euler = (-0.35, 0, 0)
    beams = [box(f"{name}_beam", (0.025, 1.5 * s, 0.025), (0, -0.75 * s, 0), {"default": beam}, fan)]
    for ob in beams:
        ob.hide_render = True
    rig = PatchRig(name, root, {}, {})
    rig.beam = beams
    rig.eye_sockets = [eye.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]]
    return rig


def make_zombie(tex, name="zombie"):
    """A blocky zombie: the Engineer's build in green, with a torn shirt."""
    from textures import ZOMBIE_SKIN, ZOMBIE_SHIRT, ZOMBIE_PANTS
    face = material(f"{name}_face", tex=tex["zombie_face"])
    skin = material(f"{name}_skin", srgb(ZOMBIE_SKIN))
    top = material(f"{name}_shirt_tex", tex=tex["zombie_shirt"])
    shirt = material(f"{name}_shirt", srgb(ZOMBIE_SHIRT))
    arm = material(f"{name}_arm", tex=tex["zombie_arm"])
    leg = material(f"{name}_leg", tex=tex["zombie_leg"])
    pants = material(f"{name}_pants", srgb(ZOMBIE_PANTS))
    root = empty(name)
    parts = {}
    parts["torso"] = empty(f"{name}_torso", (0, 0, 0.75), root)
    box(f"{name}_body", (0.5, 0.25, 0.75), (0, 0, 0.375), {"front": top, "default": shirt}, parts["torso"])
    parts["head"] = empty(f"{name}_head", (0, 0, 1.5), root)
    box(f"{name}_skull", (0.5, 0.5, 0.5), (0, 0, 0.25), {"front": face, "default": skin}, parts["head"])
    for tag, x in (("arm_r", -0.375), ("arm_l", 0.375)):
        parts[tag] = empty(f"{name}_{tag}", (x, 0, 1.5), root)
        box(f"{name}_{tag}_box", (0.25, 0.25, 0.75), (0, 0, -0.375),
            {"top": shirt, "bottom": skin, "default": arm}, parts[tag])
    for tag, x in (("leg_r", -0.125), ("leg_l", 0.125)):
        parts[tag] = empty(f"{name}_{tag}", (x, 0, 0.75), root)
        box(f"{name}_{tag}_box", (0.25, 0.25, 0.75), (0, 0, -0.375),
            {"top": pants, "default": leg}, parts[tag])
    return Rig(name, root, parts, {})
