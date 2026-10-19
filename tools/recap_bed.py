"""
The sound under episode 1's recap: Null's theme and his rise, exactly as
they played in episode 0 from a given moment, without episode 0's other
sound effects (the ledge, the plunge) or voices. The screams are added by
the episode itself, from their cached takes.

    python tools/recap_bed.py assets/clips/ep00_recap_bed.wav
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import audio                                                  # noqa: E402
import music                                                  # noqa: E402

SR = audio.SR
EP0 = os.path.join(HERE, "..", "build", "ep00_g7", "timeline.json")


def excerpt(x, at, sec):
    a = int(at * SR)
    y = np.zeros(int(sec * SR))
    piece = x[a:a + len(y)]
    y[:len(piece)] = piece
    return y


def main(out, start=36.917, sec=2.0):
    """start: the moment of episode 0 the recap opens on."""
    b = json.load(open(EP0))["beats"]
    # as in episode 0: Null's theme (cue 2, seed 2) from "darken" to "black",
    # the rise rumble over "null_rise"; same gains as episode 0's mix
    m0, m1 = b["darken"][0], b["black"][0]
    theme = music.render("null", m1 - m0, seed=2)
    r0, r1 = b["null_rise"]
    rumble = audio.sfx_rumble_rise(r1 - r0)
    bed = 0.2 * excerpt(theme, start - m0, sec) + 0.7 * excerpt(rumble, start - r0, sec)
    f = int(0.02 * SR)
    bed[:f] *= np.linspace(0, 1, f)
    f = int(0.15 * SR)
    bed[-f:] *= np.linspace(1, 0, f)                       # into the forest's whoosh
    sf.write(out, np.stack([bed, bed], 1).astype(np.float32), SR)
    print("wrote", out, round(len(bed) / SR, 2), "s, peak", round(float(np.abs(bed).max()), 2))


if __name__ == "__main__":
    main(sys.argv[1])
