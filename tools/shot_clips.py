"""
Each contiguous run of rendered frames becomes shot_<first frame>.mp4,
1080x1920, with no overlays or captions (e.g. to quote one episode in
another).

    python tools/shot_clips.py build/frames out_dir
"""

import os
import subprocess
import sys


def main(frames_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    fs = sorted(int(n[:-4]) for n in os.listdir(frames_dir) if n.endswith(".png"))
    runs = []
    for f in fs:
        if runs and f == runs[-1][1] + 1:
            runs[-1][1] = f
        else:
            runs.append([f, f])
    for a, b in runs:
        # renders are 9:16 rounded down (607 px wide at 1080): scale to the Short's size
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-start_number", str(a),
                        "-i", os.path.join(frames_dir, "%04d.png"), "-frames:v", str(b - a + 1),
                        "-vf", "scale=1080:1920:flags=lanczos",
                        "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                        os.path.join(out_dir, f"shot_{a:04d}.mp4")], check=True)
        print("shot", a, b)


if __name__ == "__main__":
    main(*sys.argv[1:3])
