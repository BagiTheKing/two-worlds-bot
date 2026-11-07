"""Finish a still: aerial haze from the depth pass (when <in>_depth.png exists
beside <in>_raw.png), then the episode grade (assemble.grade: richer colour,
glow, warm light, optional sun rays).
Usage: python grade.py in_raw.png out.png [sun_x sun_y]      (sun position as frame fractions)
Env: SAT (saturation), HAZE_L (haze distance), HAZE_MAX, HAZE_START, NOHAZE=1."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import assemble  # noqa: E402

FAR = 600.0                       # world.render_depth's scale


def haze(img, depth_path, sun=None):
    """Far things fade into pale blue: f = HMAX * (1 - exp(-(d - d0) / L)).
    The haze colour runs from the sky's blue (top of frame) to its pale horizon,
    warmer around the sun."""
    a = np.asarray(img, dtype=np.float32) / 255.0
    dimg = Image.open(depth_path)
    d = np.asarray(dimg.resize(img.size, Image.BILINEAR), dtype=np.float32)
    if d.ndim == 3:
        d = d[..., 0]
    d = d / (65535.0 if d.max() > 255 else 255.0)
    dist = d * FAR
    sky = d > 0.995
    L = float(os.environ.get("HAZE_L", "140"))
    d0 = float(os.environ.get("HAZE_START", "18"))
    hmax = float(os.environ.get("HAZE_MAX", "0.78"))
    f = hmax * (1 - np.exp(-np.maximum(dist - d0, 0) / L))
    f[sky] = 0.0
    h, w = d.shape
    yy = np.linspace(0, 1, h)[:, None, None]
    top = np.array((150, 196, 250), np.float32) / 255
    low = np.array((214, 230, 250), np.float32) / 255
    col = np.broadcast_to(top * (1 - yy) + low * yy, (h, w, 3)).copy()
    if sun:                                             # warmer near the sun
        sx, sy = sun
        xx = np.linspace(0, 1, w)[None, :]
        g = np.exp(-(((xx - sx) * w / h) ** 2 + (yy[..., 0] - sy) ** 2) / 0.12)[..., None] * 0.6
        col = col * (1 - g) + np.array((1.0, 0.92, 0.9), np.float32) * g
    a = a * (1 - f[..., None]) + col * f[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


if __name__ == "__main__":
    im = Image.open(sys.argv[1]).convert("RGB")
    sun = [float(sys.argv[3]), float(sys.argv[4])] if len(sys.argv) > 4 else None
    dp = sys.argv[1].replace("_raw.png", "_depth.png")
    if dp != sys.argv[1] and os.path.exists(dp) and os.environ.get("NOHAZE") != "1":
        im = haze(im, dp, sun)
    assemble.W, assemble.H = im.size
    o = {"saturation": float(os.environ.get("SAT", "1.28")), "glow": 0.5, "threshold": 0.7}
    if sun:
        o["sun"] = sun
    assemble.grade(im, o, 0, 0, None)
    im.save(sys.argv[2])
