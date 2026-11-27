"""
Time references used throughout an episode file.

    "erasure"          start of the beat or line named "erasure"
    "erasure.end"      its end
    "erasure+1.5"      1.5 s after its start
    "noob_2.end-0.2"   0.2 s before the end of the Noob's second line
    "spree+0.15+3.0"   offsets add up
    "end"              the end of the episode
    4.2                an absolute time in seconds
"""

import re

_REF = re.compile(r"^([A-Za-z_][\w]*?)(\.end)?((?:[+-]\d+(?:\.\d+)?)*)$")


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
    return t + sum(float(x) for x in re.findall(r"[+-]\d+(?:\.\d+)?", m.group(3) or ""))


def spread(t0, t1, n):
    """n moments evenly from t0 to t1, both included (block placements, brick
    launches: the picture and the soundtrack both use this)."""
    return [t0] if n == 1 else [t0 + (t1 - t0) * k / (n - 1) for k in range(n)]


def resolve_overlays(ep_overlays, beats, length):
    """An episode's overlays with their times resolved ("from"/"to" become
    "start"/"end" in seconds). beats: name -> (start, end). A "to" of exactly
    "end" means the last frame: the video runs 0.4 s past the last beat."""
    R = lambda ref: resolve(beats, ref, length)  # noqa: E731
    out = []
    for o in ep_overlays:
        o = dict(o)
        o["start"] = round(R(o.pop("from")), 3)
        to = o.pop("to")
        o["end"] = round(length + 0.4 if to == "end" else R(to), 3)
        for key in ("grow", "full", "hl_start", "src_from", "src_to"):     # extra moments an overlay keys on
            if key in o:
                o[key] = round(R(o[key]), 3)
        if "step_at" in o:                            # a readout that counts at given moments
            o["_steps"] = sorted(round(R(x), 3) for x in o.pop("step_at"))
        if o.get("type") == "chat":                   # each message at its own moment
            o["lines"] = [dict(m, at=round(R(m["at"]), 3)) for m in o["lines"]]
        if "clips" in o:                              # a holo screen switching clips
            o["clips"] = [dict(c, at=round(R(c["at"]), 3)) for c in o["clips"]]
        out.append(o)
    return out


if __name__ == "__main__":
    # Re-resolve a timeline's overlays from its episode file, keeping its timing
    # (an overlay fix without new voices): timeref.py episode.json timeline.json
    import json
    import sys
    ep, tl = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
    tl["overlays"] = resolve_overlays(ep.get("overlays", []), tl["beats"], tl["length"])
    looks = {e["name"]: {k: e[k] for k in ("caption_size", "caption_y") if e.get(k)}
             for e in ep.get("events", []) if e.get("line")}
    for ln in tl["lines"]:                                   # caption looks set in the episode file since
        ln.update(looks.get(ln["name"], {}))
    with open(sys.argv[2], "w") as f:
        json.dump(tl, f, indent=1)
    print(f"{len(tl['overlays'])} overlays re-resolved")
