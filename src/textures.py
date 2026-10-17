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


ALL = {
    "grass_top": grass_top, "grass_side": grass_side, "dirt": dirt,
    "stone": stone, "log_side": log_side, "log_top": log_top,
    "leaves": leaves, "null": null_block, "cloud": cloud,
    "steve_face": steve_face, "steve_head_side": steve_head_side,
    "hair": hair, "shirt": shirt, "steve_arm": steve_arm,
    "steve_leg": steve_leg, "noob_face": noob_face,
    "planks": planks, "missing": missing,
    "steve_face_scared": steve_face_scared, "noob_face_scared": noob_face_scared,
}


def save_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for name, fn in ALL.items():
        p = os.path.join(out_dir, name + ".png")
        fn().save(p)
        paths[name] = p
    return paths


if __name__ == "__main__":
    print(save_all(sys.argv[1] if len(sys.argv) > 1 else "build/tex"))
