"""The movie's REALITY meter (16:9): a readout that feels like something running out.

It is only on screen while reality is changing (the creator: "if the bar
isn't moving hide it with the number, and when it appears it should make a
scene"). It glitches in when the first drop of a wave comes (torn into
sliding scanlines, a hard colour split, a white flash, a pop), stays while
the drops go on, and glitches out a moment after the last one. Its first
appearance is at the freeze, REALITY 100%, when reality stops.

While it is up: REALITY, the percentage, and a bar of 20 cells. On every
drop (an erasure tick in the soundtrack):
  - the readout pops: a small swell (1.3x, the creator's choice), shaking,
    with a magenta/cyan colour split, settling back over about a second;
  - the number drains: it counts down to its new value instead of jumping;
  - the bar's cells that are lost break off as black-and-magenta pixels that
    hop off the bar and fade in the top corner (never over the faces), the
    same erasure the world suffers;
  - a faint red pulse at the frame's edges, stronger at most once a second
    when a burst of drops adds up to 10 points or more.
Quick drops in a row keep it swollen, so a wave of erasure reads as a drain.
The colour goes white, then amber under 60%, then red under 30%; under 10%
it blinks like a dying battery.

    from movie_hud import Meter
    m = Meter(steps=[13.88, 14.11, ...], start=11.61, end=48.52, count_from=100, count_to=3)
    m.draw(img, t)          # img: an RGB PIL image of any size (16:9 expected)
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "InterDisplay-Black.otf")
MONO = os.path.join(HERE, "..", "fonts", "FreeMonoBold.ttf")

CELLS = 20
GROW = 0.3                 # extra scale at the peak of a drop (1.3x, the creator's choice)
SWELL = 0.11               # seconds to swell up
SETTLE = 0.9               # seconds to settle back
GAP = 1.6                  # drops closer than this are one wave (it stays up between them)
LEAD = 0.30                # it glitches in this long before the wave's first drop
HOLD = 1.6                 # and stays this long after the wave's last drop
ENTER, EXIT = 0.45, 0.30   # the entrance and the exit


def _ease_out(u):
    return 1 - (1 - u) ** 3


class Meter:
    def __init__(self, steps, start, end, count_from=100, count_to=3, fade=0.25):
        self.steps = sorted(steps)
        self.start, self.end = start, end
        self.a, self.b = count_from, count_to
        self.fade = fade
        self._fonts = {}
        # when it is on screen: one window per wave; the freeze's first appearance joins the first wave
        win = []
        for x in self.steps:
            if win and x - win[-1][1] < GAP:
                win[-1][1] = x
            else:
                win.append([x, x])
        self.windows = [[a - LEAD, b + HOLD] for a, b in win]
        if self.steps and self.windows and self.windows[0][0] - start < 3.0:
            self.windows[0][0] = start
        elif not self.steps:
            self.windows = [[start, start + 2.5]]
        if self.windows:
            self.windows[-1][1] = max(self.windows[-1][1], self.steps[-1] + 2.5 if self.steps else 0)
        self.windows = [[max(a, start), min(b, end)] for a, b in self.windows]

    def presence(self, t):
        """(on screen 0..1, entering 0..1 where 1 = just started, leaving 0..1) for the window holding t."""
        for a, b in self.windows:
            if a <= t < b:
                e = max(0.0, 1 - (t - a) / ENTER)
                x = max(0.0, 1 - (b - t) / EXIT)
                return 1.0, e, x
        return 0.0, 0.0, 0.0

    # ---------------------------------------------------------------- state
    def value(self, k):
        n = max(1, len(self.steps))
        return self.a - (self.a - self.b) * k / n

    def state(self, t):
        """(shown percentage, swell 0..1, the latest drop's size, seconds since it)"""
        k = sum(1 for x in self.steps if x <= t)
        if k == 0:
            return float(self.a), 0.0, 0.0, 99.0
        last = self.steps[k - 1]
        s = t - last
        old, new = self.value(k - 1), self.value(k)
        shown = old + (new - old) * _ease_out(min(1.0, s / 0.12))        # it drains, it doesn't jump (fast enough to keep up with a wave)
        swell = 0.0
        for x in self.steps[:k]:
            d = t - x
            if d < SWELL:
                e = math.sin(0.5 * math.pi * d / SWELL)
            elif d < SWELL + SETTLE:
                e = 1 - _ease_out((d - SWELL) / SETTLE) ** 0.7
            else:
                continue
            swell = max(swell, e)
        # the drops close together count as one big one (the waves hit harder)
        burst = sum(self.value(i) - self.value(i + 1) for i, x in enumerate(self.steps[:k]) if t - 0.35 <= x <= t)
        return shown, swell, burst, s

    # ---------------------------------------------------------------- drawing
    def font(self, path, size):
        key = (path, size)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(path, size)
        return self._fonts[key]

    def colour(self, pct):
        if pct < 30:
            return (255, 70, 110)
        if pct < 60:
            return (255, 190, 60)
        return (245, 245, 245)

    def draw(self, img, t):
        if t < self.start or t >= self.end:
            return
        on, enter, leave = self.presence(t)
        if on <= 0:
            return
        W, H = img.size
        u = H / 1080.0                                   # 1 at 1080p
        vis = min(1.0, (t - self.start) / self.fade, (self.end - t) / self.fade)
        shown, swell, drop, since = self.state(t)
        pct = max(0, int(round(shown)))                  # the published meter's numbers (round), every rest value matches
        rnd = random.Random(int(t * 24))
        # a dying battery: under 10% it blinks
        if pct < 10 and since < 2.5 and int(t * 4) % 2 == 1 and swell < 0.2:
            vis *= 0.45                                  # a few blinks, then it holds (the faces keep the attention)
        # the entrance: a pop that overshoots and settles; the exit: it shrinks a little as it tears away
        pop = math.sin(math.pi * min(1.0, (1 - enter) / 0.6)) * 0.35 * (1 if enter > 0 else 0)
        scale = 1.0 + GROW * swell + pop - 0.15 * leave
        vis *= min(1.0, (1 - enter) / 0.12) * (1 - leave)
        col = self.colour(pct)
        # the edge glow on big drops, and a red pulse every drop
        if since < 0.6 or enter > 0:
            k = max((1 - since / 0.6) ** 2 if since < 0.6 else 0.0, enter)
            strong = drop >= 10 and self._strong_ok(t - since)
            strength = (0.5 if strong else 0.2) * k            # strong only on the heaviest bursts, once a second at most
            self._edge_glow(img, strength)
        # the panel, drawn at 1x on its own layer, then scaled
        pw, ph = int(600 * u), int(150 * u)
        layer = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        a = int(255 * vis)
        d.text((int(4 * u), int(4 * u)), "REALITY", font=self.font(MONO, int(34 * u)), fill=(*col, int(a * 0.85)))
        big = self.font(FONT, int(76 * u))
        num = f"{pct}%"
        nx, ny = int(4 * u), int(38 * u)
        # the colour split grows with the swell, and is hard as it arrives or leaves
        split = int((3 + 9 * swell + 26 * enter + 18 * leave) * u)
        for dx, c in ((-split, (255, 0, 200)), (split, (0, 230, 255))):
            d.text((nx + dx, ny), num, font=big, fill=(*c, int(a * (0.55 + 0.4 * swell))))
        d.text((nx, ny), num, font=big, fill=(*col, a), stroke_width=int(4 * u), stroke_fill=(0, 0, 0, int(a * 0.85)))
        # the bar: cells left, and the cell that just went, falling apart
        bx, by, cw, chh, gap = int(250 * u), int(76 * u), int(13 * u), int(30 * u), int(3 * u)
        left = shown / 100.0 * CELLS
        for i in range(CELLS):
            x0 = bx + i * (cw + gap)
            if i < int(left):
                d.rectangle((x0, by, x0 + cw, by + chh), fill=(*col, a))
            elif i < left:
                f = left - i
                d.rectangle((x0, by + int(chh * (1 - f)), x0 + cw, by + chh), fill=(*col, a))
            else:
                d.rectangle((x0, by, x0 + cw, by + chh), outline=(*col, int(a * 0.2)), width=max(1, int(u)))
        # arriving or leaving: torn into scanlines that slide sideways, and a white flash as it lands
        tear = max(enter, leave)
        if tear > 0:
            layer = self._tear(layer, tear, int(t * 24), u)
        if 0 < enter and enter > 0.72:
            flash = Image.new("RGBA", layer.size, (255, 255, 255, 0))
            flash.putalpha(layer.split()[3].point(lambda v: int(v * 0.9)))
            layer = Image.alpha_composite(layer, flash)
        # grow out of the corner, shaking while it's swollen
        if abs(scale - 1.0) > 0.001:
            layer = layer.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
        jx = int(rnd.uniform(-1, 1) * 9 * u * max(swell, enter))
        jy = int(rnd.uniform(-1, 1) * 6 * u * max(swell, enter))
        ox, oy = int(56 * u) + jx, int(40 * u) + jy
        shadow = layer.split()[3].filter(ImageFilter.GaussianBlur(6 * u * scale))
        img.paste((0, 0, 0), (ox + int(3 * u), oy + int(3 * u)), shadow.point(lambda v: int(v * 0.5)))
        img.paste(layer, (ox, oy), layer)
        # the lost cells break off: pixels fly out of the bar and fall down the frame, fading
        self._debris(img, t, bx, by, cw, chh, gap, u, vis)

    def _debris(self, img, t, bx, by, cw, chh, gap, u, vis):
        """Each drop's pixels leave the bar where it was at that drop (its own swell), then fly on their
        own: a short hop and fall that stays in the top corner, fading out above the characters."""
        d = ImageDraw.Draw(img, "RGBA")
        k = sum(1 for x in self.steps if x <= t)
        floor_y = 330 * u                                    # nothing falls below this (the faces are lower)
        for i in range(max(0, k - 12), k):
            born = self.steps[i] + SWELL                     # when the cell visibly goes (the swell has peaked)
            s = t - born
            if s < 0 or s > 0.75:
                continue
            sw = self.state(born)[1]
            scale = 1.0 + GROW * sw
            ox, oy = 56 * u, 40 * u
            hi, lo = self.value(i) / 100.0 * CELLS, self.value(i + 1) / 100.0 * CELLS
            pr = random.Random(i * 7919)
            for _ in range(10):
                cell = pr.uniform(lo, hi)
                # where it left the bar, in the frame, at the swell it had then
                x0 = ox + (bx + cell * (cw + gap) + pr.uniform(0, cw)) * scale
                y0 = oy + (by + pr.uniform(0, chh)) * scale
                vx, vy = pr.uniform(-60, 140) * u, pr.uniform(-180, -40) * u
                x = x0 + vx * s
                y = y0 + vy * s + 0.5 * 600 * u * s * s
                if y > floor_y:
                    continue
                sz = pr.uniform(6, 11) * u
                fa = int(255 * vis * max(0.0, 1 - s / 0.75) * min(1.0, (floor_y - y) / (60 * u)))
                c = (255, 0, 200) if pr.random() < 0.55 else (14, 0, 20)
                d.rectangle((x, y, x + sz, y + sz), fill=(*c, fa))

    def _tear(self, layer, amount, seed, u):
        """Cut the panel into horizontal strips and slide them sideways (a broken display)."""
        out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        r = random.Random(seed)
        h = max(2, int(7 * u))
        for y in range(0, layer.size[1], h):
            if r.random() < 0.25 * amount:
                continue                                         # a strip that drops out
            dx = int(r.uniform(-1, 1) * 140 * u * amount)
            out.paste(layer.crop((0, y, layer.size[0], min(layer.size[1], y + h))), (dx, y))
        return out

    def _strong_ok(self, t_drop):
        """A strong flash at this drop only if none of the drops in the second before it had one."""
        if not hasattr(self, "_strong"):
            self._strong = []
            for i, x in enumerate(self.steps):
                burst = sum(self.value(j) - self.value(j + 1) for j, y in enumerate(self.steps[:i + 1]) if x - 0.35 <= y <= x)
                if burst >= 10 and all(x - y >= 1.0 for y in self._strong):
                    self._strong.append(x)
        return any(abs(t_drop - y) < 1e-6 for y in self._strong)

    def _edge_glow(self, img, strength):
        W, H = img.size
        key = ("edge", W, H)
        if key not in self._fonts:
            m = Image.new("L", (W, H), 0)
            d = ImageDraw.Draw(m)
            steps = 40
            for i in range(steps):
                v = int(255 * (1 - i / steps) ** 2.2)
                inset = int(i * min(W, H) * 0.006)
                d.rectangle((inset, inset, W - 1 - inset, H - 1 - inset), outline=v, width=max(1, int(min(W, H) * 0.006)))
            self._fonts[key] = m.filter(ImageFilter.GaussianBlur(min(W, H) * 0.02))
        m = self._fonts[key].point(lambda v: int(v * strength))
        img.paste((230, 20, 60), (0, 0), m)
