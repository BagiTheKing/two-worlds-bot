"""Clearance check for the movie's Episode 2 dragon: steps through the dragon's shots and reports every frame where
the dragon's parts (oriented boxes) touch the oak, the portal, Steve, the Noob or the ground.
    SCRATCH=<dir> python3 tools/clearance_ep02.py
Copy and adapt for other creatures and scenes."""
import sys, json
sys.argv = ["x"]
sys.path.insert(0, "src/lookdev"); sys.path.insert(0, "src")
import movie_ep02 as R
import bpy
from mathutils import Vector
import os
S = os.environ.get("SCRATCH", "build")      # holds b/tl_v6.json, b/tex and assets (the MCprep link)
tl = json.load(open(S + "/b/tl_v6.json"))
R.B.update({k: tuple(v) for k, v in tl["beats"].items()})
E = R.build(tl, S + "/b/tex", S + "/assets", 360, 8)
E.mouth = {}; E.force = True
def box(ob):
    cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))), Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
oak = [o for o in bpy.data.objects if o.type == "MESH" and ("oak" in o.name.lower() or "tree" in o.name.lower()) and o.location.z > -100]
print("oak objects", [o.name for o in oak][:8])
blocks = list(E.portal_order)
OAKPTS = {o.name: [o.matrix_world @ v.co for v in o.data.vertices][::3] for o in oak}
def inter(a, b):
    return all(a[0][i] < b[1][i] and b[0][i] < a[1][i] for i in range(3))
bad = []
t = R.b("dive")
while t < R.b("dive_after", 1):
    R.apply(E, t); bpy.context.view_layer.update()
    if E.D.root.location.z > -100:
        DPARTS = [o for o in E.D.root.children_recursive if o.type == "MESH"]
        dparts = [box(o) for o in DPARTS]
        for o in oak:
            mw = o.matrix_world
            pts = OAKPTS[o.name]
            hit = False
            for part in DPARTS:
                inv = part.matrix_world.inverted()
                bb = [Vector(c) for c in part.bound_box]
                lo_ = Vector((min(c.x for c in bb), min(c.y for c in bb), min(c.z for c in bb)))
                hi_ = Vector((max(c.x for c in bb), max(c.y for c in bb), max(c.z for c in bb)))
                for p in pts:
                    q = inv @ p
                    if lo_.x < q.x < hi_.x and lo_.y < q.y < hi_.y and lo_.z < q.z < hi_.z:
                        hit = (part.name, tuple(round(v, 1) for v in p)); break
                if hit: break
            if hit: bad.append((round(t, 2), "dragon-oak", hit))
        probes = {"portal": [Vector(bl.matrix_world.translation) + Vector((dx, 0, dz)) for bl in blocks for dx in (-0.4, 0.4) for dz in (-0.4, 0.4)]}
        for who, root in (("steve", E.S.holder), ("noob", E.N.root)):
            c = Vector(root.location)
            probes[who] = [c + Vector((dx, dy, dz)) for dx in (-0.3, 0.3) for dy in (-0.3, 0.3) for dz in (0.2, 1.0, 1.8)]
        for k_, pts in probes.items():
            for part in DPARTS:
                inv = part.matrix_world.inverted()
                bb = [Vector(c) for c in part.bound_box]
                lo_ = Vector((min(c.x for c in bb), min(c.y for c in bb), min(c.z for c in bb)))
                hi_ = Vector((max(c.x for c in bb), max(c.y for c in bb), max(c.z for c in bb)))
                if any(lo_.x < q.x < hi_.x and lo_.y < q.y < hi_.y and lo_.z < q.z < hi_.z for q in (inv @ p for p in pts)):
                    bad.append((round(t, 2), "dragon-" + k_, part.name)); break
        lo = min((part.matrix_world @ Vector(c)).z for part in DPARTS for c in part.bound_box)
        if lo < -0.05: bad.append((round(t, 2), "dragon-ground", round(lo, 2)))
    sd = (Vector(E.S.holder.location) - Vector(E.N.root.location)); sd.z = 0
    if sd.length < 0.8 and E.S.holder.location.z > -100 and E.N.root.location.z > -100: bad.append((round(t, 2), "steve-noob", round(sd.length, 2)))
    t += 0.1
from collections import OrderedDict
print("ISSUES", len(bad))
for x in bad[:60]: print("ISSUE", x)
