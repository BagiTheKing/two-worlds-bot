"""
Pixel textures for the block world and the cast, drawn from code with Pillow.

Everything here is original: seeded noise over our own palettes, so the
world reads as "blocky survival game" without reusing any game's assets.
Block textures are 16x16 and rendered with nearest-neighbour filtering; the
Noob's face is drawn smooth at a higher resolution, because the Roblox side
of the cast is meant to look like moulded plastic, not pixels.

    python src/textures.py out_dir
"""

import os
import random
import sys

from PIL import Image, ImageDraw


def _jitter(rgb, amount, rnd):
    d = rnd.randint(-amount, amount)
    return tuple(max(0, min(255, c + d)) for c in rgb)


def _noise(w, h, base, amount, seed, specks=None):
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _jitter(base, amount, rnd)
            if specks and rnd.random() < specks[1]:
                c = _jitter(specks[0], 10, rnd)
            px[x, y] = c
    return img


GRASS = (98, 162, 58)
DIRT = (128, 90, 62)
STONE = (122, 122, 126)
BARK = (104, 80, 50)
WOOD = (176, 140, 88)
LEAF = (58, 128, 44)


def grass_top():
    return _noise(16, 16, GRASS, 14, 1, specks=((78, 138, 44), 0.18))


def dirt():
    return _noise(16, 16, DIRT, 12, 2, specks=((100, 70, 48), 0.15))


def grass_side():
    img = dirt()
    px = img.load()
    rnd = random.Random(3)
    for x in range(16):
        depth = 3 + (rnd.random() < 0.45) + (rnd.random() < 0.2)
        for y in range(depth):
            px[x, y] = _jitter(GRASS, 12, rnd)
    return img


def stone():
    return _noise(16, 16, STONE, 10, 4, specks=((96, 96, 100), 0.2))


def log_side():
    rnd = random.Random(5)
    img = Image.new("RGB", (16, 16))
    px = img.load()
    stripes = [rnd.randint(-14, 14) for _ in range(16)]
    for y in range(16):
        for x in range(16):
            px[x, y] = _jitter(tuple(c + stripes[x] for c in BARK), 6, rnd)
    return img


def log_top():
    rnd = random.Random(6)
    img = Image.new("RGB", (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            r = max(abs(x - 7.5), abs(y - 7.5))
            if r > 6.5:
                c = BARK
            elif int(r) % 2:
                c = WOOD
            else:
                c = tuple(v - 22 for v in WOOD)
            px[x, y] = _jitter(c, 6, rnd)
    return img


def leaves():
    return _noise(16, 16, LEAF, 16, 7, specks=((34, 88, 28), 0.22))


def null_block():
    """The corruption: near-black with violet and cyan flecks."""
    rnd = random.Random(8)
    img = _noise(16, 16, (22, 12, 34), 8, 8)
    px = img.load()
    for _ in range(14):
        px[rnd.randrange(16), rnd.randrange(16)] = rnd.choice(
            [(170, 60, 255), (60, 230, 255)])
    return img


def cloud():
    return _noise(16, 16, (246, 246, 250), 4, 9)


# ---------------------------------------------------------------- the cast

SKIN = (196, 140, 104)
HAIR = (70, 46, 28)
SHIRT = (28, 168, 170)
PANTS = (58, 64, 150)
SHOE = (90, 90, 96)


def steve_face():
    """8x8 front of the Engineer's head (our own drawing)."""
    rnd = random.Random(10)
    img = _noise(8, 8, SKIN, 6, 10)
    px = img.load()
    for x in range(8):
        px[x, 0] = _jitter(HAIR, 6, rnd)
        px[x, 1] = _jitter(HAIR, 6, rnd) if x in (0, 1, 6, 7) else px[x, 1]
    px[0, 2] = px[7, 2] = HAIR
    for x, c in ((1, (250, 250, 250)), (2, (60, 70, 160)),
                 (5, (60, 70, 160)), (6, (250, 250, 250))):
        px[x, 4] = c
    px[3, 5] = px[4, 5] = (150, 98, 72)
    for x in (2, 3, 4, 5):
        px[x, 6] = (120, 70, 56)
    return img


def steve_head_side():
    img = _noise(8, 8, SKIN, 6, 11)
    px = img.load()
    rnd = random.Random(11)
    for y in range(3):
        for x in range(8):
            if y < 2 or x > 3:
                px[x, y] = _jitter(HAIR, 6, rnd)
    return img


def hair():
    return _noise(8, 8, HAIR, 8, 12)


def shirt():
    img = _noise(8, 12, SHIRT, 8, 13)
    px = img.load()
    px[3, 0] = px[4, 0] = SKIN
    return img


def steve_arm():
    rnd = random.Random(14)
    img = _noise(4, 12, SKIN, 6, 14)
    px = img.load()
    for y in range(4):
        for x in range(4):
            px[x, y] = _jitter(SHIRT, 8, rnd)
    return img


def steve_leg():
    rnd = random.Random(15)
    img = _noise(4, 12, PANTS, 8, 15)
    px = img.load()
    for y in range(10, 12):
        for x in range(4):
            px[x, y] = _jitter(SHOE, 6, rnd)
    return img


NOOB_YELLOW = (245, 205, 48)


def noob_face():
    """Smooth, toy-like face: two oval eyes and a wide smile."""
    s = 256
    img = Image.new("RGB", (s, s), NOOB_YELLOW)
    d = ImageDraw.Draw(img)
    d.ellipse((78, 70, 104, 122), fill=(20, 20, 20))
    d.ellipse((152, 70, 178, 122), fill=(20, 20, 20))
    d.arc((62, 92, 194, 196), start=20, end=160, fill=(20, 20, 20), width=12)
    return img


def planks():
    rnd = random.Random(16)
    img = Image.new("RGB", (16, 16))
    px = img.load()
    for y in range(16):
        row = y // 4
        shade = (-10, 6, -4, 10)[row]
        for x in range(16):
            c = tuple(v + shade for v in (164, 128, 78))
            if y % 4 == 3 or (x == (5 + row * 7) % 16):
                c = (110, 82, 48)
            px[x, y] = _jitter(c, 6, rnd)
    return img


def missing():
    """The "missing texture" checkerboard: Null's face."""
    img = Image.new("RGB", (8, 8))
    px = img.load()
    for y in range(8):
        for x in range(8):
            px[x, y] = (255, 0, 220) if (x // 2 + y // 2) % 2 == 0 else (0, 0, 0)
    return img


def steve_face_scared():
    """Wide eyes, raised brows, open mouth."""
    img = steve_face()
    px = img.load()
    for x in range(1, 7):
        px[x, 2] = SKIN
    px[1, 3] = px[2, 3] = px[5, 3] = px[6, 3] = HAIR          # brows raised
    px[1, 4], px[2, 4] = (250, 250, 250), (60, 70, 160)
    px[5, 4], px[6, 4] = (60, 70, 160), (250, 250, 250)
    px[1, 5] = px[6, 5] = (250, 250, 250)                       # wider eyes
    px[3, 5] = px[4, 5] = (150, 98, 72)
    for x in (2, 3, 4, 5):
        px[x, 6] = (70, 30, 30)                                 # open mouth
    px[3, 7] = px[4, 7] = (70, 30, 30)
    return img


def noob_face_scared():
    """The toy face, terrified: round eyes, worried brows, open mouth."""
    s = 256
    img = Image.new("RGB", (s, s), NOOB_YELLOW)
    d = ImageDraw.Draw(img)
    d.ellipse((70, 72, 110, 128), fill=(20, 20, 20))
    d.ellipse((146, 72, 186, 128), fill=(20, 20, 20))
    d.ellipse((84, 84, 96, 98), fill=(250, 250, 250))
    d.ellipse((160, 84, 172, 98), fill=(250, 250, 250))
    d.line((62, 62, 108, 46), fill=(20, 20, 20), width=10)       # worried brows
    d.line((194, 62, 148, 46), fill=(20, 20, 20), width=10)
    d.ellipse((100, 150, 156, 214), fill=(40, 10, 10))
    d.ellipse((112, 186, 144, 210), fill=(200, 60, 70))
    return img


def obsidian():
    """The portal frame: near-black volcanic glass with violet glints."""
    rnd = random.Random(31)
    img = _noise(16, 16, (24, 16, 36), 7, 31, specks=((52, 30, 78), 0.16))
    px = img.load()
    for _ in range(6):
        px[rnd.randrange(16), rnd.randrange(16)] = (120, 70, 190)
    return img


ZOMBIE_SKIN = (92, 146, 74)
ZOMBIE_SHIRT = (52, 104, 104)
ZOMBIE_PANTS = (60, 52, 104)


def zombie_face():
    """8x8 front of a blocky zombie's head (our own drawing): hollow eyes,
    a dark slack mouth."""
    rnd = random.Random(32)
    img = _noise(8, 8, ZOMBIE_SKIN, 8, 32)
    px = img.load()
    for x in range(8):
        px[x, 0] = _jitter((60, 104, 50), 6, rnd)
    for x in (1, 2, 5, 6):
        px[x, 3] = (14, 14, 14)
    px[2, 4] = px[5, 4] = (14, 14, 14)
    for x in (2, 3, 4, 5):
        px[x, 6] = (40, 60, 34)
    return img


def zombie_shirt():
    """Torn: skin shows through at the hem."""
    rnd = random.Random(33)
    img = _noise(8, 12, ZOMBIE_SHIRT, 8, 33)
    px = img.load()
    for x in range(8):
        for y in range(9 + rnd.randint(0, 2), 12):
            px[x, y] = _jitter(ZOMBIE_SKIN, 6, rnd)
    return img


def zombie_arm():
    rnd = random.Random(34)
    img = _noise(4, 12, ZOMBIE_SKIN, 8, 34)
    px = img.load()
    for y in range(3):
        for x in range(4):
            px[x, y] = _jitter(ZOMBIE_SHIRT, 8, rnd)
    return img


def zombie_leg():
    return _noise(4, 12, ZOMBIE_PANTS, 8, 35)


def dragon_hide():
    """The dragon's scales: near-black with dusky violet and grey flecks, a
    few darker scale rows so the big flat sides still read as blocks."""
    rnd = random.Random(41)
    img = _noise(16, 16, (30, 28, 36), 6, 41, specks=((58, 50, 70), 0.14))
    px = img.load()
    for y in (3, 8, 13):
        for x in range(16):
            if rnd.random() < 0.7:
                px[x, y] = _jitter((20, 18, 26), 4, rnd)
    return img


def dragon_wing():
    """Wing membrane: dark slate with faint vein lines."""
    rnd = random.Random(42)
    img = _noise(16, 16, (52, 48, 62), 5, 42)
    px = img.load()
    for x0 in (2, 7, 12):
        for y in range(16):
            x = min(15, x0 + y // 6)
            px[x, y] = _jitter((34, 30, 42), 4, rnd)
    return img


def dragon_eye():
    """A glowing violet eye with a hot centre."""
    img = Image.new("RGB", (4, 4), (180, 60, 255))
    px = img.load()
    px[1, 1] = px[2, 1] = px[1, 2] = px[2, 2] = (245, 200, 255)
    return img


# ------------------------------------------------------------ faces that act
# Each expression is a whole face, swapped in frame by frame (kit.rigs face
# plates): "<who>_face_<expression>", and "<expression>_talk" with the mouth
# open, which alternates with the closed one while the character speaks.

EYE_W, EYE_B, MOUTH, LID = (250, 250, 250), (60, 70, 160), (120, 70, 56), (176, 122, 92)


def _steve16(draw):
    """Steve's face at twice the pixels (each original pixel is 2x2), so
    lids and brows can move by half a pixel. draw(px) paints the features."""
    rnd = random.Random(10)
    img = _noise(8, 8, SKIN, 6, 10)
    px = img.load()
    for x in range(8):
        px[x, 0] = _jitter(HAIR, 6, rnd)
        px[x, 1] = _jitter(HAIR, 6, rnd) if x in (0, 1, 6, 7) else px[x, 1]
    px[0, 2] = px[7, 2] = HAIR
    px[3, 5] = px[4, 5] = (150, 98, 72)                       # the nose
    img = img.resize((16, 16), Image.NEAREST)
    draw(img.load())
    return img


def _box(px, x0, y0, x1, y1, c):
    for x in range(x0, x1):
        for y in range(y0, y1):
            px[x, y] = c


def _steve_eyes(px, top=8, bottom=10, lid=0):
    """Eyes in rows top..bottom; `lid` rows of skin-coloured lid from the top."""
    for x0, (a, b) in ((2, (EYE_W, EYE_B)), (10, (EYE_B, EYE_W))):
        _box(px, x0, top, x0 + 2, bottom, a)
        _box(px, x0 + 2, top, x0 + 4, bottom, b)
        _box(px, x0, top, x0 + 4, top + lid, LID)


def _steve_mouth(px, open_=False, shape="line"):
    if shape == "o":                                   # a small round "oh"
        _box(px, 6, 12, 10, 15 if open_ else 14, (70, 30, 30))
    elif open_:
        _box(px, 4, 12, 12, 14, (70, 30, 30))
        _box(px, 5, 14, 11, 15, (70, 30, 30))
    else:
        _box(px, 4, 12, 12, 13, MOUTH)


def steve_faces():
    def neutral(o):
        return lambda px: (_steve_eyes(px), _steve_mouth(px, o))

    def unimpressed(o):                                # half lids, flat mouth: "really?"
        return lambda px: (_steve_eyes(px, lid=1), _box(px, 2, 7, 6, 8, HAIR), _box(px, 10, 7, 14, 8, HAIR),
                           _steve_mouth(px, o) if o else _box(px, 5, 12, 11, 13, MOUTH))

    def surprised(o):                                  # brows up, tall eyes, "oh"
        return lambda px: (_box(px, 2, 5, 6, 6, HAIR), _box(px, 10, 5, 14, 6, HAIR),
                           _steve_eyes(px, top=7, bottom=10), _steve_mouth(px, o, "o"))

    def scared(o):                                     # worried brows, wide eyes, open mouth
        return lambda px: (_box(px, 2, 6, 4, 7, HAIR), _box(px, 4, 5, 6, 6, HAIR),
                           _box(px, 12, 6, 14, 7, HAIR), _box(px, 10, 5, 12, 6, HAIR),
                           _steve_eyes(px, top=7, bottom=10),
                           _box(px, 4, 12, 12, 14 if o else 13, (70, 30, 30)))

    def blink(px):
        _box(px, 2, 9, 6, 10, (110, 72, 52))
        _box(px, 10, 9, 14, 10, (110, 72, 52))
        _steve_mouth(px)

    out = {"blink": _steve16(blink)}
    for name, fn in (("neutral", neutral), ("unimpressed", unimpressed), ("surprised", surprised),
                     ("scared", scared)):
        out[name] = _steve16(fn(False))
        out[name + "_talk"] = _steve16(fn(True))
    return out


INK = (20, 20, 20)


def _noob(draw):
    """Only the features, on a transparent background: the plate shows the
    head's own plastic around them, so the face looks painted on, not stuck on."""
    s = 256
    img = Image.new("RGBA", (s, s), (*NOOB_YELLOW, 0))
    draw(ImageDraw.Draw(img))
    return img


def noob_faces():
    def eyes(d, h=26, w=13, y=96):                     # the toy's oval eyes
        for cx in (91, 165):
            d.ellipse((cx - w, y - h, cx + w, y + h), fill=INK)

    def smile(d, open_):
        if open_:
            d.chord((70, 110, 186, 200), start=0, end=180, fill=(40, 10, 10))
            d.chord((104, 168, 152, 198), start=0, end=180, fill=(200, 60, 70))
        else:
            d.arc((62, 92, 194, 196), start=20, end=160, fill=INK, width=12)

    def happy(d, open_):                               # ^ ^ eyes, big grin
        for cx in (91, 165):
            d.arc((cx - 22, 82, cx + 22, 122), start=200, end=340, fill=INK, width=11)
        if open_:
            d.chord((62, 104, 194, 214), start=0, end=180, fill=(40, 10, 10))
            d.chord((96, 170, 160, 212), start=0, end=180, fill=(200, 60, 70))
        else:
            d.arc((56, 84, 200, 200), start=15, end=165, fill=INK, width=15)

    def surprised(d, open_):                           # big round eyes with shine, "O"
        for cx in (91, 165):
            d.ellipse((cx - 20, 66, cx + 20, 124), fill=INK)
            d.ellipse((cx - 8, 78, cx + 2, 92), fill=(250, 250, 250))
        r = 26 if open_ else 18
        d.ellipse((128 - r, 176 - r, 128 + r, 176 + r), fill=(40, 10, 10))

    def scared(d, open_):
        for cx in (91, 165):
            d.ellipse((cx - 20, 72, cx + 20, 128), fill=INK)
            d.ellipse((cx - 6, 84, cx + 6, 98), fill=(250, 250, 250))
        d.line((62, 62, 108, 46), fill=INK, width=10)
        d.line((194, 62, 148, 46), fill=INK, width=10)
        d.ellipse((100, 150 if open_ else 166, 156, 214), fill=(40, 10, 10))

    def blink(d):
        for cx in (91, 165):
            d.arc((cx - 18, 84, cx + 18, 112), start=20, end=160, fill=INK, width=9)
        smile(d, False)

    out = {"blink": _noob(blink)}
    for name, fn in (("neutral", lambda d, o: (eyes(d), smile(d, o))), ("happy", happy),
                     ("surprised", surprised), ("scared", scared)):
        out[name] = _noob(lambda d, fn=fn: fn(d, False))
        out[name + "_talk"] = _noob(lambda d, fn=fn: fn(d, True))
    return out


FACE_SETS = {"steve": steve_faces, "noob": noob_faces}


ALL = {
    "grass_top": grass_top, "grass_side": grass_side, "dirt": dirt,
    "stone": stone, "log_side": log_side, "log_top": log_top,
    "leaves": leaves, "null": null_block, "cloud": cloud,
    "steve_face": steve_face, "steve_head_side": steve_head_side,
    "hair": hair, "shirt": shirt, "steve_arm": steve_arm,
    "steve_leg": steve_leg, "noob_face": noob_face,
    "planks": planks, "missing": missing,
    "steve_face_scared": steve_face_scared, "noob_face_scared": noob_face_scared,
    "obsidian": obsidian, "zombie_face": zombie_face, "zombie_shirt": zombie_shirt,
    "zombie_arm": zombie_arm, "zombie_leg": zombie_leg,
    "dragon_hide": dragon_hide, "dragon_wing": dragon_wing, "dragon_eye": dragon_eye,
}


def save_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for name, fn in ALL.items():
        p = os.path.join(out_dir, name + ".png")
        fn().save(p)
        paths[name] = p
    for who, fn in FACE_SETS.items():
        for expr, img in fn().items():
            if who == "noob":          # the flat part of the bevelled head: 72% wide, 68% tall
                img = img.crop((36, 41, 220, 215))
            name = f"{who}_face_{expr}"
            p = os.path.join(out_dir, name + ".png")
            img.save(p)
            paths[name] = p
    return paths


if __name__ == "__main__":
    print(save_all(sys.argv[1] if len(sys.argv) > 1 else "build/tex"))
