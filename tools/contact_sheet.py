import sys, os, glob
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
fs = sorted(glob.glob(os.path.join(src, "[0-9]*.png")))
ims = [Image.open(f).convert("RGB") for f in fs]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im, (x, y))
    d = ImageDraw.Draw(sheet)
    fr = int(os.path.basename(f)[:-4])
    d.rectangle([x, y, x + 90, y + 16], fill=(0, 0, 0))
    d.text((x + 3, y + 2), "%d  %.2fs" % (fr, (fr - 1) / 24), fill=(255, 255, 0))
sheet.save(out)
print(out, sheet.size)
