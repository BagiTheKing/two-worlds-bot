"""Apply the episode grade (assemble.grade) to a still: python grade.py in.png out.png [sun_x sun_y]"""
import sys
import os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from PIL import Image
import assemble
im = Image.open(sys.argv[1]).convert("RGB")
assemble.W, assemble.H = im.size
import os
o = {"saturation": float(os.environ.get("SAT", "1.1")), "glow": 0.5, "threshold": 0.7}
if len(sys.argv) > 4:
    o["sun"] = [float(sys.argv[3]), float(sys.argv[4])]
assemble.grade(im, o, 0, 0, None)
im.save(sys.argv[2])
