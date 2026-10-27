"""
The animation library: named, parameterised actions that an episode lists as
clips, e.g.

    {"who": "noob", "do": "run", "from": "erasure+3.8", "to": "run.end",
     "dest": [1.2, 0.2]}

Each actor's pose at time t is built in two layers:

  where it is   locomotion clips (walk, run, fall, rise, hang, dangle, set,
                face) run in order; each starts from where the previous one
                left the actor, and its end state persists after it ends.
  what it does  every clip may also pose body parts; active clips blend over
                the idle pose with short fades, so actions flow into each
                other instead of snapping.

Dialogue adds a head bob automatically while the actor's cast member speaks.
Characters face -Y at rest; yaw turns them about Z.
"""

import math
import random
import zlib

from kit.timeref import resolve

FADE = 0.12


# ----------------------------------------------------------------- maths

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ss(a, b, t):
    if b <= a:
        return 1.0 if t >= b else 0.0
    x = clamp((t - a) / (b - a))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def yaw_towards(dx, dy):
    """Yaw that points the character's front (-Y at rest) along (dx, dy)."""
    return math.atan2(dx, -dy)


def lerp_angle(a, b, u):
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + d * u


# ------------------------------------------------------------- the actions
# Each action: fn(clip, t, state) -> (state, parts). `state` is
# {"loc": (x, y, z), "yaw": float, "tilt": (x, y)}; parts maps a body part
# to a rotation (or None if the action does not pose the body).

def _cycle(t, t0, rate, amp):
    ph = 2 * math.pi * rate * (t - t0)
    s = math.sin(ph)
    return {"leg_r": (amp * s, 0, 0), "leg_l": (-amp * s, 0, 0),
            "arm_r": (-amp * 0.8 * s, 0, 0), "arm_l": (amp * 0.8 * s, 0, 0)}, abs(math.sin(ph))


def travel(raw, e=0.2):
    """0..1 progress with eased start/stop and constant speed between."""
    raw = clamp(raw)
    v = 1 / (1 - e)
    if raw < e:
        return 0.5 * v / e * raw * raw
    if raw > 1 - e:
        return 1 - 0.5 * v / e * (1 - raw) ** 2
    return v * (raw - e / 2)


def a_move(c, t, st, rate, amp, bob):
    t0, t1 = c["t0"], c["t1"]
    start = st["loc"]
    dest = c["dest"]
    dest = (dest[0], dest[1], dest[2] if len(dest) > 2 else start[2])
    u = travel((t - t0) / (t1 - t0), c.get("ease", 0.2))
    loc = lerp(start, dest, u)
    face = c.get("yaw", yaw_towards(dest[0] - start[0], dest[1] - start[1]))
    yaw = lerp_angle(st["yaw"], face, ss(t0, t0 + 0.2, t))
    parts, b = _cycle(t, t0, rate, amp)
    moving = t < t1
    loc = (loc[0], loc[1], loc[2] + (bob * b if moving else 0))
    return dict(st, loc=loc, yaw=yaw), (parts if moving else None)


def walk(c, t, st, actor=None):
    return a_move(c, t, st, c.get("rate", 2.2), 0.6, 0.035)


def run(c, t, st, actor=None):
    return a_move(c, t, st, c.get("rate", 3.4), 1.05, 0.08)


def set_(c, t, st, actor=None):
    out = dict(st)
    if "at" in c:
        a = c["at"]
        out["loc"] = (a[0], a[1], a[2] if len(a) > 2 else 0.0)
    if "yaw" in c:
        out["yaw"] = c["yaw"]
    if "tilt" in c:
        out["tilt"] = tuple(c["tilt"])
    return out, None


def face(c, t, st, actor=None):
    target = c.get("yaw")
    if target is None:
        x, y = c["towards"][:2]
        target = yaw_towards(x - st["loc"][0], y - st["loc"][1])
    return dict(st, yaw=lerp_angle(st["yaw"], target, ss(c["t0"], c["t1"], t))), None


def fall(c, t, st, actor=None):
    t0, t1 = c["t0"], c["t1"]
    u = clamp((t - t0) / (t1 - t0))
    a, b = st["loc"], c["dest"]
    loc = (lerp(a[0], b[0], u), lerp(a[1], b[1], u), a[2] + (b[2] - a[2]) * u * u)
    f = 26
    parts = {"arm_r": (-2.7 + 0.4 * math.sin(f * t), 0, 0.35),
             "arm_l": (-2.7 + 0.4 * math.sin(f * t + 1.3), 0, -0.35),
             "leg_r": (0.5 * math.sin(f * 0.8 * t), 0, 0),
             "leg_l": (-0.5 * math.sin(f * 0.8 * t), 0, 0), "head": (-0.3, 0, 0)}
    return dict(st, loc=loc), (parts if t < t1 else None)


def rise(c, t, st, actor=None):
    u = ss(c["t0"], c["t1"], t)
    a = st["loc"]
    return dict(st, loc=(a[0], a[1], lerp(a[2], c["z"], u))), None


def hang(c, t, st, actor=None):
    """Hands on `grip`, body hanging below it, facing the wall (`yaw`)."""
    gx, gy, gz = c["grip"]
    yaw = c.get("yaw", st["yaw"])
    reach = c.get("reach", 2.25)
    away = c.get("away", 0.22)
    fx, fy = math.sin(yaw), -math.cos(yaw)          # facing direction
    sway = 0.05 * math.sin(2 * math.pi * 0.45 * (t - c["t0"])) * math.exp(-(t - c["t0"]) * 0.3)
    loc = (gx - fx * away, gy - fy * away, gz - reach)
    parts = {"arm_r": (-math.pi + 0.08, 0, 0.12), "arm_l": (-math.pi + 0.08, 0, -0.12),
             "leg_r": (0.15 + sway * 2, 0, 0), "leg_l": (0.05 - sway * 2, 0, 0)}
    return dict(st, loc=loc, yaw=yaw, tilt=(sway, 0)), parts


def dangle(c, t, st, actor=None):
    """Holds on to another actor's feet and dangles below them."""
    other = actor.actors[c["from_actor"]]
    o = other.state_at(t)["loc"]
    off = c.get("offset", (0, 0))
    reach = c.get("reach", 2.45)
    loc = (o[0] + off[0], o[1] + off[1], o[2] - reach)
    k = t - c["t0"]
    kick = 0.35 * math.sin(2 * math.pi * 1.6 * k) * math.exp(-k * 0.25)
    parts = {"arm_r": (-math.pi + 0.05, 0, 0.18), "arm_l": (-math.pi + 0.05, 0, -0.18),
             "leg_r": (kick, 0, 0), "leg_l": (-kick, 0, 0)}
    yaw = c.get("yaw", st["yaw"])
    return dict(st, loc=loc, yaw=yaw), parts


# Body-only actions (no locomotion)

def look(c, t, st, actor=None):
    return st, {"head": tuple(c.get("head", (0, 0, 0)))}


def pose(c, t, st, actor=None):
    return st, {k: tuple(v) for k, v in c["parts"].items()}


def shock(c, t, st, actor=None):
    k = ss(c["t0"], c["t0"] + 0.15, t)
    # arms thrown out to the sides, head back: readable from any angle
    return st, {"arm_r": (-0.35 * k, 1.0 * k, 0), "arm_l": (-0.35 * k, -1.0 * k, 0),
                "head": (-0.12 * k, 0, 0)}


def raise_arm(c, t, st, actor=None):
    arm = c.get("arm", "arm_r")
    k = ss(c["t0"], c["t0"] + c.get("ease", 0.5), t)
    side = 1 if arm == "arm_r" else -1
    return st, {arm: (-2.4 * k, 0, 0.25 * side * k)}


def flail(c, t, st, actor=None):
    return st, {
        "arm_r": (-2.6 + 0.5 * math.sin(24 * t), 0, 0.4),
        "arm_l": (-2.6 + 0.5 * math.sin(24 * t + 1.1), 0, -0.4)}


def bounce(c, t, st, actor=None):
    """Happy hopping on the spot (the Noob at play)."""
    k = t - c["t0"]
    h = c.get("height", 0.6)
    rate = c.get("rate", 1.6)
    z = h * abs(math.sin(math.pi * rate * k))
    base = st["loc"]
    arms = -2.6 * abs(math.sin(math.pi * rate * k))
    parts = {"arm_r": (arms, 0, 0.3), "arm_l": (arms, 0, -0.3),
             "leg_r": (0.3 * math.sin(2 * math.pi * rate * k), 0, 0),
             "leg_l": (-0.3 * math.sin(2 * math.pi * rate * k), 0, 0)}
    return dict(st, loc=(base[0], base[1], base[2] + (z if t < c["t1"] else 0))), parts


def pop(c, t, st, actor=None):
    """Pops into existence (a respawn): from nothing, overshoot, settle."""
    u = (t - c["t0"]) / max(1e-6, c["t1"] - c["t0"])
    k = 0.0 if u <= 0 else (1.18 * ss(0, 0.55, u) - 0.18 * ss(0.55, 1, u) if u < 1 else 1.0)
    return dict(st, scale=(max(k, 0.001),) * 3), None


def _spline(pts, u):
    """Catmull-Rom through pts, u in 0..1 over the whole run."""
    n = len(pts) - 1
    k = min(int(u * n), n - 1)
    f = u * n - k
    p0, p1, p2, p3 = pts[max(k - 1, 0)], pts[k], pts[k + 1], pts[min(k + 2, n)]
    return tuple(0.5 * (2 * b + (-a + c) * f + (2 * a - 5 * b + 4 * c - d) * f * f
                        + (-a + 3 * b - 3 * c + d) * f ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def fly(c, t, st, actor=None):
    """Flight along a smooth curve from where the actor is through `path`
    (points [x, y, z]), at an even speed. It faces where it is going, noses
    up or down with the climb and banks into turns."""
    pts = [st["loc"]] + [tuple(p) for p in c["path"]]
    t0, t1 = c["t0"], c["t1"]
    u = travel((t - t0) / (t1 - t0), c.get("ease", 0.0))
    # arc-length table so the speed stays even between unevenly spaced points
    key = id(c)
    if c.get("_key") != key:
        samples = [_spline(pts, i / 200) for i in range(201)]
        acc = [0.0]
        for a, b in zip(samples, samples[1:]):
            acc.append(acc[-1] + math.dist(a, b))
        c["_arc"], c["_key"] = [x / (acc[-1] or 1) for x in acc], key

    def at(v):
        arc = c["_arc"]
        v = clamp(v)
        i = next((j for j in range(1, 201) if arc[j] >= v), 200)
        a = (v - arc[i - 1]) / max(arc[i] - arc[i - 1], 1e-9)
        return _spline(pts, (i - 1 + a) / 200)

    p, d = at(u), 0.01
    a, b = at(u - d), at(u + d)
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    yaw = yaw_towards(dx, dy) if abs(dx) + abs(dy) > 1e-6 else st["yaw"]
    pitch = -math.atan2(dz, math.hypot(dx, dy)) * c.get("pitch", 0.8)
    a2, b2 = at(u - 3 * d), at(u + 3 * d)
    turn = (yaw_towards(b2[0] - p[0], b2[1] - p[1]) - yaw_towards(p[0] - a2[0], p[1] - a2[1]))
    turn = (turn + math.pi) % (2 * math.pi) - math.pi
    # near either end of the path the look-ahead runs out: level the wings there
    bank = clamp(-turn * c.get("bank", 2.0), -0.7, 0.7) * ss(0, 0.08, u) * ss(0, 0.08, 1 - u)
    return dict(st, loc=p, yaw=yaw, tilt=(pitch, bank)), None


def _turn(v, tilt, yaw):
    """v rotated like a rig root: X by tilt[0], then Y by tilt[1], then Z by yaw."""
    x, y, z = v
    a, b = tilt
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    x, y = x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw)
    return (x, y, z)


def ride(c, t, st, actor=None):
    """Sits astride another actor (`on`) at `seat` in its own frame, moving,
    turning and tilting with it. Arms up: it is having the time of its life."""
    other = actor.actors[c["on"]].state_at(t)
    # the seat is where the rider's feet would be: hips (0.8 up) on the back
    seat = _turn(tuple(c.get("seat", (0, -1.6, 0.25))), other.get("tilt", (0, 0)), other["yaw"])
    loc = add(other["loc"], seat)
    k = t - c["t0"]
    whoop = 0.25 * math.sin(2 * math.pi * 1.8 * k)
    parts = {"leg_r": (-1.45, 0, 0.35), "leg_l": (-1.45, 0, -0.35),
             "arm_r": (-2.7 + whoop, 0, 0.3), "arm_l": (-2.7 - whoop, 0, -0.3)}
    return dict(st, loc=loc, yaw=other["yaw"], tilt=other.get("tilt", (0, 0))), parts


def leap(c, t, st, actor=None):
    """A big jump in an arc `height` above the straight line to `dest`, or
    onto another actor (`onto`, landing on its `seat` as it is at the end)."""
    t0, t1 = c["t0"], c["t1"]
    if c.get("onto"):
        o = actor.actors[c["onto"]].state_at(t1)
        dest = add(o["loc"], _turn(tuple(c.get("seat", (0, -1.6, 0.25))), o.get("tilt", (0, 0)), o["yaw"]))
    else:
        d = c["dest"]
        dest = (d[0], d[1], d[2] if len(d) > 2 else st["loc"][2])
    u = clamp((t - t0) / (t1 - t0))
    a = st["loc"]
    loc = lerp(a, dest, u)
    loc = (loc[0], loc[1], loc[2] + 4 * c.get("height", 1.5) * u * (1 - u))
    yaw = lerp_angle(st["yaw"], c.get("yaw", yaw_towards(dest[0] - a[0], dest[1] - a[1])), ss(t0, t0 + 0.15, t))
    tuck = math.sin(math.pi * u)
    parts = {"arm_r": (-2.8, 0, 0.4), "arm_l": (-2.8, 0, -0.4),
             "leg_r": (-0.9 * tuck, 0, 0), "leg_l": (-0.5 * tuck, 0, 0)}
    return dict(st, loc=loc, yaw=yaw), (parts if t < t1 else None)


LOCOMOTION = {"walk": walk, "run": run, "set": set_, "face": face, "fall": fall,
              "rise": rise, "hang": hang, "dangle": dangle, "bounce": bounce, "pop": pop,
              "fly": fly, "ride": ride, "leap": leap}
def punch(c, t, st, actor=None):
    """One punch: wind-up, strike landing on the timeline's impact, then a
    stinging hand. The fist lands on the first impact inside the clip."""
    arm = c.get("arm", "arm_r")
    side = 1 if arm == "arm_r" else -1
    hits = [h for h in c.get("impacts", []) if c["t0"] <= h <= c["t1"]]
    hit = hits[0] if hits else c["t0"] + 0.18
    t0 = c["t0"]
    if t < hit - 0.1:
        return st, {arm: (0.5 * ss(t0, hit - 0.1, t), 0, 0)}
    if t < hit + 0.12:
        e = ss(hit - 0.1, hit, t)
        return st, {arm: (lerp(0.5, -1.57, e), 0, 0.55 * e * side)}
    e = 1 - ss(hit + 0.12, hit + 0.45, t)
    shake = 0.25 * math.sin(42 * t) * (1 - ss(hit + 0.2, c["t1"], t))
    return st, {arm: (-1.57 * e + shake, 0, 0.55 * e * side),
                "head": (0, 0, 0.15 * math.sin(30 * t) * e)}


def flurry(c, t, st, actor=None):
    """Rapid alternating punches, one fist per impact in the timeline."""
    hits = [h for h in c.get("impacts", []) if c["t0"] - 0.05 <= h <= c["t1"]]
    parts = {"arm_r": (-0.25, 0, 0), "arm_l": (-0.25, 0, 0)}
    for i, h in enumerate(hits):
        e = ss(h - 0.07, h, t) * (1 - ss(h + 0.02, h + 0.11, t))
        if e > 0:
            arm = "arm_r" if i % 2 == 0 else "arm_l"
            parts[arm] = (lerp(-0.25, -1.57, e), 0, (0.55 if arm == "arm_r" else -0.55) * e)
    return st, parts


def cheer(c, t, st, actor=None):
    """Both arms up and a little jump."""
    k = ss(c["t0"], c["t0"] + 0.12, t)
    j = (t - c["t0"] - 0.05) / 0.42
    lift = 0.4 * math.sin(math.pi * j) if 0 <= j <= 1 else 0.0
    loc = st["loc"]
    return dict(st, loc=(loc[0], loc[1], loc[2] + lift)), {
        "arm_r": (-2.8 * k, 0, 0.25 * k), "arm_l": (-2.8 * k, 0, -0.25 * k)}


def wave(c, t, st, actor=None):
    """Arm up, hand waving side to side."""
    arm = c.get("arm", "arm_r")
    side = 1 if arm == "arm_r" else -1
    k = ss(c["t0"], c["t0"] + 0.25, t)
    w = c.get("rate", 2.2) * 2 * math.pi * (t - c["t0"])
    return st, {arm: (-2.7 * k, 0, side * k * (0.35 + 0.3 * math.sin(w)))}


def swing(c, t, st, actor=None):
    """Placing blocks: a quick forward arm swing on each of `times` (or every
    `every` seconds)."""
    arm = c.get("arm", "arm_r")
    if c.get("count"):                        # on the same moments as the blocks (spread)
        from kit.timeref import spread
        times = spread(c["t0"], c["t1"], c["count"])
    else:
        times = c.get("times") or [c["t0"] + i * c.get("every", 0.3)
                                   for i in range(int((c["t1"] - c["t0"]) / c.get("every", 0.3)) + 1)]
    e = max((ss(h - 0.08, h, t) * (1 - ss(h + 0.02, h + 0.14, t)) for h in times), default=0.0)
    return st, {arm: (lerp(-0.5, -1.7, e), 0, 0)}


def chop(c, t, st, actor=None):
    """A big overhead swing: the arm goes up behind the head, holds for a
    beat, then crashes down on `hit` seconds after the start."""
    arm = c.get("arm", "arm_l")
    hit = c["t0"] + c.get("hit", 0.4)
    if t < hit - 0.09:
        up = ss(c["t0"], hit - 0.18, t)
        return st, {arm: (-3.3 * up, 0, 0), "head": (-0.25 * up, 0, 0)}
    if t < hit:
        e = ss(hit - 0.09, hit, t)
        return st, {arm: (lerp(-3.3, -0.55, e), 0, 0), "head": (lerp(-0.25, 0.2, e), 0, 0)}
    k = 1 - ss(hit + 0.15, c["t1"], t)
    return st, {arm: (-0.55 * k, 0, 0), "head": (0.2 * k, 0, 0)}


def reach(c, t, st, actor=None):
    """Both arms straight out in front (a zombie's walk)."""
    k = ss(c["t0"], c["t0"] + 0.2, t)
    sway = 0.12 * math.sin(2 * math.pi * 1.1 * t)
    return st, {"arm_r": (-1.5 * k + sway, 0, 0), "arm_l": (-1.5 * k - sway, 0, 0),
                "head": (0.1 * k, 0, 0.15 * math.sin(2 * math.pi * 0.7 * t))}


def roar(c, t, st, actor=None):
    """The dragon's roar: head back, jaw wide, a shake at the peak."""
    k = ss(c["t0"], c["t0"] + 0.18, t) * (1 - ss(c["t1"] - 0.2, c["t1"], t))
    shake = 0.06 * math.sin(38 * t) * k
    return st, {"jaw": (0.75 * k, 0, 0), "head": (-0.35 * k + shake, 0, shake),
                "neck": (-0.25 * k, 0, 0)}


def glide(c, t, st, actor=None):
    """Wings held out, barely beating."""
    return st, {"flap": (c.get("amp", 0.15), c.get("rate", 0.6), 0)}


def scan(c, t, st, actor=None):
    """Patch's scanning beam on."""
    return st, {"scan": (1.0, 0, 0)}


def glitch_eye(c, t, st, actor=None):
    """Patch's eye flickers magenta: it has seen something it shouldn't."""
    return st, {"eye": (1.0, 0, 0)}


BODY = {"scan": scan, "glitch_eye": glitch_eye, "look": look, "pose": pose, "shock": shock, "raise_arm": raise_arm, "flail": flail,
        "punch": punch, "flurry": flurry, "cheer": cheer, "wave": wave, "swing": swing,
        "reach": reach, "chop": chop, "roar": roar, "glide": glide}


# --------------------------------------------------------------- the actor

def rnd_start(seed):
    return 0.6 + (seed % 1000) / 1000 * 1.8



class Actor:
    def __init__(self, name, rig, spec, clips, beats, length, lines, actors):
        self.name, self.rig = name, rig
        self.cast = spec.get("cast", name)
        at = spec.get("at", (0, 0, 0))
        self.start = {"loc": (at[0], at[1], at[2] if len(at) > 2 else 0.0),
                      "yaw": spec.get("yaw", 0.0), "tilt": (0.0, 0.0)}
        self.clips, self.exprs = [], []
        for c in clips:
            c = dict(c)
            c["t0"] = resolve(beats, c["from"], length)
            c["t1"] = resolve(beats, c.get("to", c["from"]), length)
            if c["do"] == "set":                # on the frame grid, like the camera cuts
                c["t0"] = c["t1"] = round(c["t0"] * 24) / 24
            (self.exprs if c["do"] == "expr" else self.clips).append(c)
        self.clips.sort(key=lambda c: c["t0"])
        self.lines = [ln for ln in lines if ln["who"] == self.cast and not ln.get("vo")]
        self.actors = actors
        self.idle_amp = spec.get("idle", 0.05)
        self.seed = zlib.crc32(name.encode())       # the same in every render process
        self.expr = spec.get("expr", "neutral")
        self.face_mode = spec.get("faces")
        rnd, t, self.blinks = random.Random(self.seed), rnd_start(self.seed), []
        while t < length + 1:                       # a blink every 2.2-4.6 s
            self.blinks.append(t)
            t += rnd.uniform(2.2, 4.6)
        # "freeze": from this moment the actor stops dead, mid-motion (a glitch)
        self.freeze = resolve(beats, spec["freeze"], length) if spec.get("freeze") is not None else None
        self._cache = {}

    @staticmethod
    def holds(c):
        return c["do"] in ("hang", "dangle") or c.get("hold", False)

    def state_at(self, t):
        if self.freeze is not None:
            t = min(t, self.freeze)
        key = round(t, 5)
        if key not in self._cache:
            st = dict(self.start)
            for c in self.clips:
                fn = LOCOMOTION.get(c["do"])
                if fn is None or t < c["t0"]:
                    continue
                st, _ = fn(c, min(t, c["t1"]), st, self)
            self._cache[key] = st
        return self._cache[key]

    def face_at(self, t):
        """Which face plate shows at t: the expression of the moment (an "expr"
        clip, else the actor's default), its open-mouth version on alternating
        moments while the actor speaks, or a blink now and then when silent.
        With "faces": "moments" the character keeps its usual face (None: no
        plate) except inside its expr clips."""
        expr = None if self.face_mode == "moments" else self.expr
        for c in self.exprs:
            if c["t0"] <= t < c["t1"]:
                expr = c["face"]
        if expr is None:
            return None
        talking = any(ln["start"] <= t < ln["end"] - 0.04 for ln in self.lines)
        if talking:
            chunk = int(t * 12)                      # the mouth moves in 1/12 s steps
            open_ = random.Random(self.seed + chunk).random() < 0.62
            return expr + "_talk" if open_ else expr
        if expr not in ("surprised", "scared") and any(b <= t < b + 0.125 for b in self.blinks):
            return "blink"
        return expr

    def talk(self, t):
        for ln in self.lines:
            if ln["start"] - 0.05 <= t <= ln["end"]:
                e = ss(ln["start"] - 0.05, ln["start"] + 0.03, t) * (1 - ss(ln["end"] - 0.08, ln["end"], t))
                return (0.07 * e * math.sin(2 * math.pi * 5.2 * t),
                        0.04 * e * math.sin(2 * math.pi * 2.3 * t), 0.0)
        return (0.0, 0.0, 0.0)

    def pose(self, t):
        if self.freeze is not None:
            t = min(t, self.freeze)
        st = self.state_at(t)
        idle = self.idle_amp * math.sin(2 * math.pi * 0.6 * t + self.seed % 7)
        parts = dict(self.rig.rest)          # a rig's own resting values (a dragon's wingbeat)
        parts.update({"arm_r": (idle, 0, 0), "arm_l": (-idle, 0, 0), "head": (0, 0, 0)})
        for c in self.clips:
            hold = self.holds(c)
            if t < c["t0"] - FADE or t > c["t1"] + FADE:
                continue
            tc = min(max(t, c["t0"]), c["t1"])
            fn = LOCOMOTION.get(c["do"]) or BODY[c["do"]]
            _, p = fn(c, tc, self.state_at(tc), self)
            if not p:
                continue
            w = ss(c["t0"] - FADE, c["t0"] + FADE * 0.5, t)
            # held poses (hanging, dangling) stay at full strength to the end
            w *= 1 - (ss(c["t1"], c["t1"] + FADE, t) if hold else ss(c["t1"] - FADE * 0.5, c["t1"] + FADE, t))
            for k, v in p.items():
                parts[k] = lerp(parts.get(k, (0, 0, 0)), v, w)
        parts["head"] = add(parts["head"], self.talk(t))
        out = {"loc": st["loc"], "yaw": st["yaw"], "tilt": st.get("tilt", (0, 0)),
               "scale": st.get("scale", (1, 1, 1)), "t": t}
        out.update(parts)
        return out
