"""Steve's face skin, painted pixel by pixel after the reference (an 8 x 8 grid
read straight off its frontal close-up): pink-salmon upper face, lighter
cheeks, a slightly darker pair of nose pixels, and a beard: the mouth row and
the chin row step down into darker red-brown, darkest at the chin corners.
Each pixel varies a little, as a hand-made skin does.
Also: make_head_skin() turns the rest of the head's skin the same pink tone."""
import random

from PIL import Image
import numpy as np

S = (204, 116, 110)          # skin
S_SIDE = (192, 107, 101)      # a touch darker at the sides
CHEEK = (214, 124, 118)
NOSE = (182, 97, 92)
B1 = (160, 80, 72)           # beard: the mouth row
B1_SIDE = (148, 73, 66)
B2 = (126, 60, 52)           # the chin row
B2_CORNER = (108, 51, 44)
HAIR = (70, 44, 26)

ROWS = [                     # top (row 0) to bottom (row 7), left to right on screen
    [HAIR] * 8,
    [HAIR] * 8,
    [S_SIDE, S, S, S, S, S, S, S_SIDE],
    [S_SIDE, S, S, S, S, S, S, S_SIDE],
    [S_SIDE, S, S, S, S, S, S, S_SIDE],
    [S_SIDE, CHEEK, S, NOSE, NOSE, S, CHEEK, S_SIDE],
    [B1_SIDE, B1, B1, B1, B1, B1, B1, B1_SIDE],
    [B2_CORNER, B2, B2, B2, B2, B2, B2, B2_CORNER],
]


def make_face_skin(path, seed=7, jitter=0.035):
    rnd = random.Random(seed)
    im = Image.new("RGB", (8, 8))
    for r, row in enumerate(ROWS):
        for c, col in enumerate(row):
            k = 1 + rnd.uniform(-jitter, jitter)
            im.putpixel((c, r), tuple(max(0, min(255, int(v * k))) for v in col))
    im.save(path)
    return path


def make_head_skin(src, dst):
    """The BlendSwap skin's skin pixels shifted to the face's pink tone."""
    a = np.asarray(Image.open(src).convert("RGBA")).astype(np.float32)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    skin = (r > g) & (g > b) & (r - b > 35) & (lum > 70) & (al > 0)
    tgt = np.array(S, np.float32)
    cur = a[skin][:, :3]
    mean = cur.mean(axis=0)
    a[skin, :3] = np.clip(cur / mean * tgt, 0, 255)       # keep each pixel's shading, move the tone
    Image.fromarray(a.astype(np.uint8)).save(dst)
    return dst


SHIRT = (0, 158, 172)        # the classic, vivid cyan of the reference
PANTS = (78, 62, 188)        # violet-blue
SHOES = (118, 118, 122)
NECK = (112, 56, 42)         # the dark V at the collar


def make_body_skin(src, dst):
    """The whole skin in the reference's palette: each part recoloured while
    keeping its pixel-to-pixel shading (the arms' blotches softened)."""
    a = np.asarray(Image.open(src).convert("RGBA")).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    vis = al > 0
    shirt = vis & (g > r + 30) & (b > r + 25) & (g > 70)
    pants = vis & (b > r + 35) & (b > g + 35)
    shoes = vis & (np.abs(r - g) < 14) & (np.abs(g - b) < 14) & (r > 110)
    skin = vis & (r > g) & (g > b) & (r - b > 35) & (lum > 70)
    rng = np.random.default_rng(5)
    for mask, tgt, contrast, noise in ((shirt, SHIRT, 0.9, 0.07), (pants, PANTS, 0.9, 0.06),
                                       (shoes, SHOES, 0.6, 0.05), (skin, S, 0.75, 0.05)):
        if not mask.any():
            continue
        cur = rgb[mask]
        l = (0.3 * cur[:, 0] + 0.59 * cur[:, 1] + 0.11 * cur[:, 2])
        k = 1 + (l / l.mean() - 1) * contrast              # each pixel's shade, scaled
        k = k * (1 + rng.uniform(-noise, noise, size=k.shape))   # and the hand-drawn pixel variation of a skin
        rgb[mask] = np.clip(np.array(tgt, np.float32)[None, :] * k[:, None], 0, 255)
    # the collar V on the torso front (x 20..28, y 20..32): skin there goes dark
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    v = skin & (xx >= 20) & (xx < 28) & (yy >= 20) & (yy < 24)
    rgb[v] = np.array(NECK, np.float32)
    a[..., :3] = rgb
    Image.fromarray(a.astype(np.uint8)).save(dst)
    return dst
