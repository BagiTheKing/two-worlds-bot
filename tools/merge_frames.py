"""
Merge the two renderers' frames into one folder.

    python tools/merge_frames.py episode.json timeline.json downloaded_dir out_dir

downloaded_dir holds one folder per artifact: frames-<shard> (the episode
kit, build_episode.py) and frames-new-<shard> (the episode's new-look
renderer). Inside the episode's "skip_render" ranges the kit draws nothing on
purpose, so there the new look's frame is used. Everywhere else the kit's
frame wins, and the new look only fills frames the kit has none for. The two
overlap by a frame at each boundary, and a kit render made before a
skip_render fix can still hold frames the new look owns.
"""

import glob
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kit.timeref import resolve                                       # noqa: E402
import json                                                           # noqa: E402


def main(episode, timeline, src, out):
    ep, tl = json.load(open(episode)), json.load(open(timeline))
    fps, end = tl["fps"], tl["length"] + 0.4
    F = lambda ref: int(round(resolve(tl["beats"], ref, end) * fps)) + 1  # noqa: E731
    skip = [(F(a), F(b)) for a, b in ep.get("skip_render", [])]
    kit, new = {}, {}
    for d in sorted(glob.glob(os.path.join(src, "frames-*"))):
        into = new if os.path.basename(d).startswith("frames-new-") else kit
        for p in glob.glob(os.path.join(d, "[0-9]*.png")):
            into[int(os.path.basename(p)[:-4])] = p
    os.makedirs(out, exist_ok=True)
    took = {"kit": 0, "new": 0}
    for f in sorted(set(kit) | set(new)):
        owned = any(s0 <= f < s1 for s0, s1 in skip)
        use_new = f in new and (owned or f not in kit)
        shutil.copyfile(new[f] if use_new else kit[f], os.path.join(out, f"{f:04d}.png"))
        took["new" if use_new else "kit"] += 1
    print(f"skip_render frames {skip}: {took['kit']} kit frames, {took['new']} new-look frames")


if __name__ == "__main__":
    main(*sys.argv[1:5])
