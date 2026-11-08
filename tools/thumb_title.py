"""Put the title on a rendered thumbnail, in the episodes' subtitle font.

    python tools/thumb_title.py in.png out.png "UPGRADED?!" [--y 0.08]

Yellow letters with a thick black outline and a soft shadow, centred, sized
to fill most of the width.
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "InterDisplay-Black.otf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("text")
    ap.add_argument("--y", type=float, default=0.06, help="top of the text, as a fraction of the height")
    ap.add_argument("--width", type=float, default=0.86, help="text width, as a fraction of the image width")
    a = ap.parse_args()
    im = Image.open(a.src).convert("RGBA")
    W, H = im.size
    size = 200
    font = ImageFont.truetype(FONT, size)
    w = font.getbbox(a.text)[2]
    size = int(size * a.width * W / w)
    font = ImageFont.truetype(FONT, size)
    x0, y0, x1, y1 = font.getbbox(a.text)
    x = (W - (x1 - x0)) // 2 - x0
    y = int(a.y * H) - y0
    stroke = max(4, size // 9)
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((x + stroke // 2, y + stroke), a.text, font=font, fill=(0, 0, 0, 200),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, shadow.filter(ImageFilter.GaussianBlur(stroke)))
    ImageDraw.Draw(im).text((x, y), a.text, font=font, fill=(255, 221, 0, 255),
                            stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    im.convert("RGB").save(a.dst)
    print(a.dst, f"{size}px")


if __name__ == "__main__":
    main()
