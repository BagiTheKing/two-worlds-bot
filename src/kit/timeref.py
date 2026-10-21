"""
Time references used throughout an episode file.

    "erasure"          start of the beat or line named "erasure"
    "erasure.end"      its end
    "erasure+1.5"      1.5 s after its start
    "noob_2.end-0.2"   0.2 s before the end of the Noob's second line
    "end"              the end of the episode
    4.2                an absolute time in seconds
"""

import re

_REF = re.compile(r"^([A-Za-z_][\w]*?)(\.end)?([+-]\d+(?:\.\d+)?)?$")


def resolve(beats, ref, length=None):
    if isinstance(ref, (int, float)):
        return float(ref)
    if ref == "end":
        return float(length)
    m = _REF.match(ref.strip())
    if not m or m.group(1) not in beats:
        raise KeyError(f"unknown time reference {ref!r}")
    a, b = beats[m.group(1)]
    t = b if m.group(2) else a
    return t + float(m.group(3) or 0)


def spread(t0, t1, n):
    """n moments evenly from t0 to t1, both included (block placements, brick
    launches: the picture and the soundtrack both use this)."""
    return [t0] if n == 1 else [t0 + (t1 - t0) * k / (n - 1) for k in range(n)]
