# /// script
# requires-python = ">=3.13"
# dependencies = ["pygame-ce>=2.5,<2.6"]
# ///
"""PROTOTYPE, throwaway. Never merged.

Answers: what does Hot Lapper look like? Resolution, palette, road and
scenery, cockpit/dashboard layout, start lights, off-road countdown, car
pictures and circuit maps (ticket #12).

Three structurally different variants (layout + resolution), and three
palettes you can apply to any of them. Everything is drawn as palette
indices on an 8-bit canvas, then scaled up by a whole number.

Run:  uv run prototypes/look_spike.py
      uv run prototypes/look_spike.py --shots DIR   (write PNGs and exit)

Keys (prototype only)
  Left / Right   previous / next variant      P      next palette
  Tab            race / car select / circuit select
  Up / Down      choose car (car select)      F11    fullscreen on/off
  Space          autopilot on/off             T      replay start lights
  C              cycle condition: new / worn / critical
  X              faults (puncture + holed tank) on/off
  O              show a pit stop              Esc    quit
Race keys
  A / S / D / F  fast left / left / right / fast right
  I / K          accelerator / brake          J / L  gear down / up
"""

import math
import os
import sys

import pygame

# ---------------------------------------------------------------- palette

ROLES = (
    "TRANSPARENT BLACK WHITE SKY SKY_LOW SKYLINE GRASS_L GRASS_D ROAD_L ROAD_D "
    "RUMBLE_A RUMBLE_B COWL COWL_HI PANEL RED GREEN AMBER FOLIAGE TRUNK GREY "
    "TYRE CAR1 CAR1_HI CAR2 CAR2_HI CAR3 CAR3_HI WATER OIL BUILDING ROOF"
).split()
for _i, _r in enumerate(ROLES):
    globals()[_r] = _i
CAR_COLOURS = ((CAR1, CAR1_HI), (CAR2, CAR2_HI), (CAR3, CAR3_HI))  # noqa: F821

_N, _B = 0xD8, 0xFF
_k, _blu, _red, _mag = (0, 0, 0), (0, 0, _N), (_N, 0, 0), (_N, 0, _N)
_grn, _cyn, _yel, _wht = (0, _N, 0), (0, _N, _N), (_N, _N, 0), (_N, _N, _N)
_Bblu, _Bred, _Bgrn = (0, 0, _B), (_B, 0, 0), (0, _B, 0)
_Bcyn, _Byel, _Bwht = (0, _B, _B), (_B, _B, 0), (_B, _B, _B)

PALETTES = {
    "Primary (8 hues, 2 brightnesses)": dict(
        BLACK=_k, WHITE=_Bwht, SKY=_Bcyn, SKY_LOW=_wht, SKYLINE=_blu,
        GRASS_L=_Bgrn, GRASS_D=_grn, ROAD_L=_blu, ROAD_D=_k,
        RUMBLE_A=_Bred, RUMBLE_B=_Bwht, COWL=_k, COWL_HI=_blu, PANEL=_k,
        RED=_Bred, GREEN=_Bgrn, AMBER=_Byel, FOLIAGE=_grn, TRUNK=_red,
        GREY=_wht, TYRE=_k, CAR1=_cyn, CAR1_HI=_Bcyn, CAR2=_red,
        CAR2_HI=_Bred, CAR3=_yel, CAR3_HI=_Byel, WATER=_Bblu, OIL=_mag,
        BUILDING=_wht, ROOF=_red,
    ),
    "Earthy": dict(
        BLACK=(20, 18, 28), WHITE=(236, 236, 224), SKY=(110, 170, 226),
        SKY_LOW=(196, 220, 236), SKYLINE=(48, 62, 100),
        GRASS_L=(100, 168, 64), GRASS_D=(70, 132, 48),
        ROAD_L=(120, 118, 124), ROAD_D=(98, 96, 104),
        RUMBLE_A=(206, 48, 40), RUMBLE_B=(236, 236, 224),
        COWL=(20, 18, 28), COWL_HI=(48, 62, 100), PANEL=(20, 18, 28),
        RED=(206, 48, 40), GREEN=(100, 168, 64), AMBER=(238, 180, 44),
        FOLIAGE=(36, 90, 50), TRUNK=(120, 78, 46), GREY=(170, 170, 176),
        TYRE=(20, 18, 28), CAR1=(40, 160, 150), CAR1_HI=(170, 170, 176),
        CAR2=(206, 48, 40), CAR2_HI=(238, 180, 44), CAR3=(40, 110, 200),
        CAR3_HI=(110, 170, 226), WATER=(40, 110, 200), OIL=(20, 18, 28),
        BUILDING=(170, 170, 176), ROOF=(206, 48, 40),
    ),
    "Dusk": dict(
        BLACK=(14, 12, 22), WHITE=(248, 244, 236), SKY=(64, 72, 150),
        SKY_LOW=(236, 140, 96), SKYLINE=(40, 30, 70),
        GRASS_L=(74, 128, 70), GRASS_D=(56, 104, 60),
        ROAD_L=(92, 90, 104), ROAD_D=(78, 76, 90),
        RUMBLE_A=(220, 60, 60), RUMBLE_B=(236, 232, 220),
        COWL=(28, 26, 36), COWL_HI=(70, 66, 86), PANEL=(10, 10, 14),
        RED=(255, 60, 48), GREEN=(80, 240, 110), AMBER=(255, 190, 40),
        FOLIAGE=(40, 82, 58), TRUNK=(92, 60, 44), GREY=(150, 150, 160),
        TYRE=(22, 20, 24), CAR1=(40, 170, 160), CAR1_HI=(130, 230, 210),
        CAR2=(200, 36, 48), CAR2_HI=(255, 120, 110), CAR3=(250, 200, 30),
        CAR3_HI=(255, 240, 150), WATER=(90, 150, 230), OIL=(34, 30, 46),
        BUILDING=(170, 150, 140), ROOF=(130, 60, 60),
    ),
}
IDENTITY = [(i, i, i) for i in range(256)]


def rgb_list(pal):
    out = [(255, 0, 255)] * 256
    for name, rgb in pal.items():
        out[ROLES.index(name)] = rgb
    return out


def colour_count(pal):
    return len(set(pal.values()))


def surface(w, h):
    s = pygame.Surface((max(1, w), max(1, h)), 0, 8)
    s.set_palette(IDENTITY)
    s.fill(TRANSPARENT)  # noqa: F821
    s.set_colorkey(TRANSPARENT)  # noqa: F821
    return s


# ---------------------------------------------------------------- 5x7 font

_GLYPHS = """
0 .###. #...# #..## #.#.# ##..# #...# .###.
1 ..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.
2 .###. #...# ....# ...#. ..#.. .#... #####
3 ##### ...#. ..#.. ...#. ....# #...# .###.
4 ...#. ..##. .#.#. #..#. ##### ...#. ...#.
5 ##### #.... ####. ....# ....# #...# .###.
6 ..##. .#... #.... ####. #...# #...# .###.
7 ##### ....# ...#. ..#.. .#... .#... .#...
8 .###. #...# #...# .###. #...# #...# .###.
9 .###. #...# #...# .#### ....# ...#. .##..
A .###. #...# #...# ##### #...# #...# #...#
B ####. #...# #...# ####. #...# #...# ####.
C .###. #...# #.... #.... #.... #...# .###.
D ####. #...# #...# #...# #...# #...# ####.
E ##### #.... #.... ####. #.... #.... #####
F ##### #.... #.... ####. #.... #.... #....
G .###. #...# #.... #.### #...# #...# .####
H #...# #...# #...# ##### #...# #...# #...#
I .###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.
J ..### ...#. ...#. ...#. ...#. #..#. .##..
K #...# #..#. #.#.. ##... #.#.. #..#. #...#
L #.... #.... #.... #.... #.... #.... #####
M #...# ##.## #.#.# #.#.# #...# #...# #...#
N #...# #...# ##..# #.#.# #..## #...# #...#
O .###. #...# #...# #...# #...# #...# .###.
P ####. #...# #...# ####. #.... #.... #....
Q .###. #...# #...# #...# #.#.# #..#. .##.#
R ####. #...# #...# ####. #.#.. #..#. #...#
S .#### #.... #.... .###. ....# ....# ####.
T ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# #...# #...# .###.
V #...# #...# #...# #...# #...# .#.#. ..#..
W #...# #...# #...# #.#.# #.#.# #.#.# .#.#.
X #...# #...# .#.#. ..#.. .#.#. #...# #...#
Y #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
Z ##### ....# ...#. ..#.. .#... #.... #####
: ..... ..#.. ..#.. ..... ..#.. ..#.. .....
. ..... ..... ..... ..... ..... .##.. .##..
- ..... ..... ..... .###. ..... ..... .....
/ ....# ....# ...#. ..#.. .#... #.... #....
> .#... ..#.. ...#. ....# ...#. ..#.. .#...
< ...#. ..#.. .#... #.... .#... ..#.. ...#.
% ##..# ##..# ...#. ..#.. .#... #..## #..##
"""
GLYPHS = {}
for _line in _GLYPHS.strip().splitlines():
    _ch, *_rows = _line.split()
    GLYPHS[_ch] = _rows


def text(c, s, x, y, col, scale=1):
    for ch in s.upper():
        rows = GLYPHS.get(ch)
        if rows:
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "#":
                        c.fill(col, (x + rx * scale, y + ry * scale, scale, scale))
        x += 6 * scale
    return x


def text_w(s, scale=1):
    return len(s) * 6 * scale - scale


def text_c(c, s, cx, y, col, scale=1):
    text(c, s, cx - text_w(s, scale) // 2, y, col, scale)


# ---------------------------------------------------------------- sprites


def make_sprites():
    sp = {}
    t = surface(16, 32)
    pygame.draw.rect(t, TRUNK, (7, 22, 3, 10))
    pygame.draw.ellipse(t, FOLIAGE, (1, 2, 14, 22))
    pygame.draw.ellipse(t, GRASS_D, (4, 5, 6, 8))
    sp["tree"] = (t, 4.0, 8.0)
    b = surface(16, 8)
    pygame.draw.ellipse(b, FOLIAGE, (0, 1, 16, 7))
    pygame.draw.ellipse(b, GRASS_D, (3, 2, 5, 3))
    sp["bush"] = (b, 3.0, 1.5)
    h = surface(32, 20)
    pygame.draw.polygon(h, ROOF, [(0, 8), (16, 0), (31, 8)])
    pygame.draw.rect(h, BUILDING, (2, 8, 28, 12))
    pygame.draw.rect(h, BLACK, (12, 12, 7, 8))
    pygame.draw.rect(h, SKYLINE, (4, 11, 5, 4))
    pygame.draw.rect(h, SKYLINE, (22, 11, 5, 4))
    sp["barn"] = (h, 10.0, 6.0)
    g = surface(48, 20)
    pygame.draw.polygon(g, ROOF, [(0, 4), (47, 0), (47, 4), (0, 7)])
    for row in range(5):
        pygame.draw.rect(g, GREY if row % 2 else BUILDING, (2, 8 + row * 2, 44, 2))
    for px in (2, 45):
        pygame.draw.rect(g, BLACK, (px, 4, 1, 16))
    sp["stand"] = (g, 24.0, 8.0)
    p = surface(6, 24)
    pygame.draw.rect(p, GREY, (2, 4, 2, 20))
    pygame.draw.rect(p, AMBER, (0, 0, 6, 5))
    sp["post"] = (p, 0.8, 4.0)
    a = surface(16, 14)
    pygame.draw.rect(a, BLACK, (2, 10, 2, 4))
    pygame.draw.rect(a, BLACK, (12, 10, 2, 4))
    pygame.draw.rect(a, AMBER, (0, 0, 16, 10))
    for ox in (2, 8):
        pygame.draw.polygon(a, BLACK, [(ox, 1), (ox + 3, 1), (ox + 6, 5), (ox + 3, 9), (ox, 9), (ox + 3, 5)])
    sp["arrow_r"] = (a, 2.4, 2.0)
    sp["arrow_l"] = (pygame.transform.flip(a, True, False), 2.4, 2.0)
    for s, _, _ in sp.values():
        s.set_palette(IDENTITY)
        s.set_colorkey(TRANSPARENT)
    return sp


def make_skyline(seed, w=640, h=24):
    s = surface(w, h)
    rnd = seed
    y = h // 2
    for x in range(w):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        y += (rnd >> 16) % 3 - 1
        y = max(4, min(h - 4, y))
        hh = y
        if (x // 40) % 5 == 2 and (x % 40) < 18:
            hh = 3 + (x // 40) % 4
        pygame.draw.line(s, SKYLINE, (x, hh), (x, h - 1))
    return s


# ---------------------------------------------------------------- circuit

SEG = 5.0
HALF = 6.0  # half the road width, metres
OUTER = HALF + 8.0
CURVE_K = 1.0  # fake-curve squash: real lateral offset per segment^2 times this
DRAW = 160
EYE = 1.0

SECTIONS = [  # (length or angle, radius, climb); radius 0 = straight; +ve = right
    (400, 0, 0),
    (90, 120, 0),
    (250, 0, 24),
    (-60, 80, 0),
    (150, 60, 0),
    (300, 0, -24),
    (60, 200, 0),
    (-45, 100, 0),
    (45, 100, 0),
    (350, 0, 0),
    (120, 150, 0),
]
HAZARDS = [  # kind, at (m), across (m), length, width
    ("oil", 520, -2.0, 12, 3),
    ("water", 900, 2.5, 20, 4),
    ("glass", 1300, 0.0, 6, 2),
    ("debris", 1700, -3.0, 8, 3),
    ("rocks", 2100, 3.0, 6, 2.5),
]
HAZARD_COL = dict(oil=OIL, water=WATER, glass=WHITE, debris=GREY, rocks=TRUNK)  # noqa: F821


class Seg:
    __slots__ = ("i", "curve", "y1", "y2", "sprites", "hazards", "marks")

    def __init__(self, i, curve):
        self.i, self.curve = i, curve
        self.y1 = self.y2 = 0.0
        self.sprites, self.hazards, self.marks = [], [], []


class Track:
    def __init__(self):
        segs, outline = [], []
        hx = hy = heading = 0.0
        height = 0.0
        for a, r, climb in SECTIONS:
            if r == 0:
                n, curve = int(a / SEG), 0.0
            else:
                n = int(abs(math.radians(a)) * r / SEG)
                curve = math.copysign(SEG * SEG / r, a) * CURVE_K
            for k in range(n):
                t0, t1 = k / n, (k + 1) / n
                ease = math.sin(math.pi * (k + 0.5) / n)
                ease = min(1.0, ease * 2.2)
                s = Seg(len(segs), curve * ease)
                e = lambda t: (1 - math.cos(math.pi * t)) / 2  # noqa: E731
                s.y1 = height + climb * e(t0)
                s.y2 = height + climb * e(t1)
                segs.append(s)
                if r:
                    heading += math.copysign(SEG / r, a)
                hx += math.sin(heading) * SEG
                hy -= math.cos(heading) * SEG
                if len(segs) % 4 == 0:
                    outline.append((hx, hy))
            height += climb
        self.segs = segs
        self.length = len(segs) * SEG
        ex, ey = outline[-1]
        m = len(outline)
        outline = [(x - ex * i / m, y - ey * i / m) for i, (x, y) in enumerate(outline)]
        xs, ys = [p[0] for p in outline], [p[1] for p in outline]
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        self.outline = [((x - min(xs)) / span, (y - min(ys)) / span) for x, y in outline]
        self.start_z = 150.0
        self._decorate()

    def seg_at(self, z):
        return self.segs[int(z % self.length // SEG)]

    def _decorate(self):
        n = len(self.segs)
        st = self.seg_at(self.start_z)
        st.marks.append(("start", (self.start_z % SEG) / SEG))
        for row in range(5):
            for side, back in ((-1, 0.0), (1, 4.0)):
                z = self.start_z - 8 - row * 8 - back
                self.seg_at(z).marks.append(("grid", side, (z % SEG) / SEG))
        for z in range(int(self.start_z + 20), int(self.start_z + 220), int(SEG)):
            self.seg_at(z).marks.append(("pit",))
        for kind, at, across, length, width in HAZARDS:
            for z in range(at, at + length, int(SEG)):
                self.seg_at(z).hazards.append((kind, across, width))
        kinds = ["tree", "tree", "bush", "barn", "post", "tree", "bush"]
        for s in self.segs:
            i = s.i
            if abs(s.curve) < 0.02 and i % 9 == 0:
                side = 1 if (i // 9) % 2 else -1
                kind = kinds[(i * 7) % len(kinds)]
                s.sprites.append((kind, side * (OUTER + 2 + (i % 5) * 3)))
            if i % 13 == 5:
                s.sprites.append(("tree", -(OUTER + 14 + (i % 7) * 4)))
        for i in range(int(self.start_z / SEG) - 10, int(self.start_z / SEG) + 20, 6):
            self.segs[i % n].sprites.append(("stand", -(OUTER + 14)))
        for i, s in enumerate(self.segs):
            nxt = self.segs[(i + 14) % n]
            prv = self.segs[(i + 13) % n]
            if abs(nxt.curve) > 0.15 and abs(prv.curve) <= 0.15:
                right = nxt.curve > 0
                for k in range(4):
                    seg = self.segs[(i - k * 3) % n]
                    seg.sprites.append(("arrow_r" if right else "arrow_l", (-1 if right else 1) * (HALF + 3)))


# ---------------------------------------------------------------- car / state

CARS = [  # name, automatic, pace, durability
    ("ROBUST AUTOMATIC", True, 0.45, 0.95),
    ("BALANCED MANUAL", False, 0.7, 0.6),
    ("FAST MANUAL", False, 0.95, 0.3),
]
RATIOS = [3.2, 2.2, 1.6, 1.25, 1.0]
RPM_K = 120.0
REDLINE, MAXREV = 10000, 11000
CONDITIONS = {"new": (0.05, 0.05, 0.0), "worn": (0.5, 0.6, 0.35), "critical": (0.88, 0.92, 0.8)}


class State:
    def __init__(self, track):
        self.track = track
        self.car = 1
        self.laps = 3
        self.cond = "new"
        self.faults = False
        self.autopilot = True
        self.screen = "race"
        self.pit_t = None
        self.sky_off = 0.0
        self.best = 77.40
        self.record = 74.85
        self.reset_start()

    def reset_start(self):
        self.z = self.track.start_z - 8
        self.x = -3.0
        self.v = 0.0
        self.gear = 0
        self.revs = 1500.0
        self.heat = 0.1
        self.fuel = 1.0
        self.steer = 0
        self.lap = 0
        self.lap_t = 0.0
        self.race_t = 0.0
        self.seq_t = 0.0
        self.offroad_t = 0.0
        self.stranded_t = 0.0

    @property
    def held(self):
        return self.seq_t < 3.0

    @property
    def lights(self):
        if self.seq_t < 3.0:
            return min(3, int(self.seq_t) + 1), False
        if self.seq_t < 4.5:
            return 3, True
        return 0, False

    @property
    def wear(self):
        return CONDITIONS[self.cond]


def update(st, keys, dt):
    tr = st.track
    st.seq_t += dt
    if st.pit_t is not None:
        st.pit_t += dt
        if st.pit_t > 6:
            st.pit_t = None
    if st.stranded_t > 0:
        st.stranded_t -= dt
        if st.stranded_t <= 0:
            st.x, st.v, st.offroad_t = 0.0, 0.0, 0.0
        return
    seg = tr.seg_at(st.z)
    auto = CARS[st.car][1]
    if st.autopilot:
        ahead = max((abs(tr.seg_at(st.z + k * SEG).curve) for k in range(4, 36)), default=0)
        target = 72.0 if ahead < 0.01 else min(72.0, math.sqrt(9.0 / (ahead * 0.006)))
        throttle, brake = st.v < target, st.v > target + 4
        want = seg.curve * st.v * st.v * 0.006 - st.x * 2.0
        st.steer = max(-2, min(2, round(want / 3.5)))
        steer_v = max(-7.0, min(7.0, want))
    else:
        throttle, brake = keys[pygame.K_i], keys[pygame.K_k]
        st.steer = (keys[pygame.K_f] * 2 or keys[pygame.K_d]) - (keys[pygame.K_a] * 2 or keys[pygame.K_s])
        steer_v = {0: 0.0, 1: 3.0, 2: 7.0}[abs(st.steer)] * (1 if st.steer > 0 else -1)
    if st.held:
        st.revs += (9000 if throttle else -6000) * dt
        st.revs = max(1500, min(MAXREV, st.revs))
        return
    if auto or st.autopilot:
        if st.revs > 9300 and st.gear < 4:
            st.gear += 1
        elif st.revs < 5200 and st.gear > 0:
            st.gear -= 1
    f = st.revs / MAXREV
    torque = max(0.0, 0.7 + 0.9 * f - 1.0 * f * f) if st.revs < MAXREV else 0.0
    a = (14.0 * torque * RATIOS[st.gear] / 3.2 if throttle else -1.0) - 0.0011 * st.v * st.v
    if brake:
        a = -14.0
    a -= 9.8 * math.sin(math.atan((seg.y2 - seg.y1) / SEG))
    st.v = max(0.0, st.v + a * dt)
    if st.faults:
        st.v = min(st.v, 13.4)
        st.x += math.sin(st.race_t * 9) * 0.6 * dt * 3
    st.revs = max(1500.0, st.v * RATIOS[st.gear] * RPM_K)
    st.heat = max(0.0, min(1.0, st.heat + (0.15 if st.revs > REDLINE else -0.02) * dt))
    if auto:
        st.heat = 0.0
    st.fuel = max(0.0, st.fuel - st.v * dt / 40000 * (2 if st.faults else 1))
    st.x += steer_v * min(1.0, st.v / 10) * dt
    st.x -= seg.curve * st.v * st.v * 0.006 * dt
    if abs(st.x) > HALF + 0.6:
        st.offroad_t += dt
        st.v *= 1 - 1.5 * dt
        if st.offroad_t > 5:
            st.stranded_t = 2.5
    else:
        st.offroad_t = 0.0
    st.x = max(-OUTER, min(OUTER, st.x))
    old = st.z
    st.z = (st.z + st.v * dt) % tr.length
    st.sky_off += seg.curve * st.v * dt * 1.4
    st.race_t += dt
    st.lap_t += dt
    if old < tr.start_z <= st.z:
        if st.lap:
            st.best = min(st.best, st.lap_t)
        st.lap = st.lap % st.laps + 1
        st.lap_t = 0.0


# ---------------------------------------------------------------- road renderer


def render_road(c, v, st, sprites, skyline):
    W, H, hz = c.get_width(), c.get_height(), v.horizon
    K = W / 2 * v.zoom
    tr = st.track
    n = len(tr.segs)
    base = int(st.z // SEG)
    frac = st.z - base * SEG
    seg0 = tr.segs[base % n]
    camy = seg0.y1 + (seg0.y2 - seg0.y1) * frac / SEG + EYE
    camx = st.x

    c.fill(SKY, (0, 0, W, hz))
    c.fill(SKY_LOW, (0, hz - 10, W, 10))
    sw = skyline.get_width()
    off = int(st.sky_off) % sw
    sy = hz - skyline.get_height()
    for xx in range(-off, W, sw):
        c.blit(skyline, (xx, sy))
    c.fill(GRASS_D, (0, hz, W, H - hz))

    dx = -seg0.curve * frac / SEG
    x = 0.0
    maxy = H
    queue = []
    for i in range(DRAW):
        seg = tr.segs[(base + i) % n]
        z1 = i * SEG - frac
        x1, x2 = x, x + dx
        x += dx
        dx += seg.curve

        def P(t, o, z1=z1, x1=x1, x2=x2, seg=seg):
            z = max(0.3, z1 + t * SEG)
            s = 1.0 / z
            xo = x1 + (x2 - x1) * t
            y = seg.y1 + (seg.y2 - seg.y1) * t
            return (W / 2 + s * (xo + o - camx) * K, hz + s * (camy - y) * K)

        if z1 + SEG <= 0.3:
            continue
        top = P(1, 0)[1]
        queue.append((seg, P, maxy))
        if top >= maxy:
            continue
        c.set_clip((0, 0, W, int(maxy)))
        bot = P(0, 0)[1]
        band = (seg.i // 3) % 2
        c.fill(GRASS_L if band else GRASS_D, (0, int(top), W, int(bot - top) + 1))
        quad = lambda a, b, t0=0, t1=1, P=P: [P(t0, a), P(t0, b), P(t1, b), P(t1, a)]  # noqa: E731
        c_r = RUMBLE_A if band else RUMBLE_B
        pygame.draw.polygon(c, c_r, quad(-HALF - 0.8, HALF + 0.8))
        pygame.draw.polygon(c, ROAD_L if band else ROAD_D, quad(-HALF, HALF))
        for kind, across, width in seg.hazards:
            pygame.draw.polygon(c, HAZARD_COL[kind], quad(across - width / 2, across + width / 2, 0.1, 0.9))
            if kind in ("glass", "rocks", "debris"):
                for k in range(3):
                    o = across - width / 2 + width * (k + 0.5) / 3
                    pygame.draw.polygon(c, BLACK if kind != "glass" else SKY, quad(o - 0.15, o + 0.15, 0.3 + k * 0.15, 0.4 + k * 0.15))
        for m in seg.marks:
            if m[0] == "start":
                t0 = m[1]
                for row in range(2):
                    for k in range(8):
                        a = -HALF + k * HALF / 4
                        col = WHITE if (k + row) % 2 else BLACK
                        pygame.draw.polygon(c, col, quad(a, a + HALF / 4, t0 + row * 0.12, t0 + row * 0.12 + 0.12))
            elif m[0] == "grid":
                _, side, t0 = m
                a, b = sorted((side * 0.6, side * (HALF - 0.6)))
                pygame.draw.polygon(c, WHITE, quad(a, b, t0, t0 + 0.08))
                for e in (a, b):
                    pygame.draw.polygon(c, WHITE, quad(e - 0.12, e + 0.12, t0, min(1, t0 + 0.6)))
            elif m[0] == "pit" and seg.i % 2:
                pygame.draw.polygon(c, AMBER, quad(1.6, 1.9))
        maxy = top
    c.set_clip(None)

    for seg, P, clip in reversed(queue):
        for kind, off in seg.sprites:
            img, wm, hm = sprites[kind]
            x0, y0 = P(0, off)
            s = (P(0, off + 1)[0] - x0)
            w, h = int(s * wm), int(s * hm)
            if w < 1 or h < 1 or w > W * 3:
                continue
            c.set_clip((0, 0, W, int(clip)))
            c.blit(pygame.transform.scale(img, (w, h)), (int(x0 - w / 2), int(y0 - h)))
    c.set_clip(None)


# ---------------------------------------------------------------- shared widgets


def fmt_time(t):
    if t is None:
        return "--:--.--"
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:05.2f}"


def bar(c, x, y, w, h, frac, col, bg=PANEL, frame=GREY):  # noqa: F821
    c.fill(frame, (x - 1, y - 1, w + 2, h + 2))
    c.fill(bg, (x, y, w, h))
    c.fill(col, (x, y, int(w * max(0, min(1, frac))), h))


def band_col(frac):
    return GREEN if frac < 0.4 else AMBER if frac < 0.75 else RED  # noqa: F821


def lamp(c, x, y, r, on, col):
    pygame.draw.circle(c, col if on else COWL_HI, (x, y), r)  # noqa: F821
    pygame.draw.circle(c, BLACK, (x, y), r, 1)  # noqa: F821


def dial(c, cx, cy, r, frac, red_from=None, label=None):
    pygame.draw.circle(c, GREY, (cx, cy), r + 1)
    pygame.draw.circle(c, PANEL, (cx, cy), r)
    a0, a1 = math.radians(225), math.radians(-45)
    for k in range(11):
        f = k / 10
        a = a0 + (a1 - a0) * f
        col = RED if red_from is not None and f >= red_from else WHITE
        p = (cx + math.cos(a) * (r - 1), cy - math.sin(a) * (r - 1))
        q = (cx + math.cos(a) * (r - 3), cy - math.sin(a) * (r - 3))
        pygame.draw.line(c, col, p, q)
    a = a0 + (a1 - a0) * max(0, min(1, frac))
    pygame.draw.line(c, AMBER, (cx, cy), (cx + math.cos(a) * (r - 2), cy - math.sin(a) * (r - 2)))
    if label:
        text_c(c, label, cx, cy + r // 3, GREY)


def countdown_big(c, st, cx, cy, scale):
    left = max(0, 5 - st.offroad_t)
    if st.stranded_t > 0:
        text_c(c, "STRANDED", cx, cy, RED, scale)
    elif st.offroad_t > 0 and int(st.offroad_t * 4) % 2 == 0:
        text_c(c, str(math.ceil(left)), cx, cy, RED, scale * 2)


# ---------------------------------------------------------------- variants


class VariantA:
    name = "Classic cowl, analogue dials"
    W, H, horizon, zoom = 256, 192, 82, 1.0
    car_scale = 2

    def cockpit(self, c, st):
        body, hi = CAR_COLOURS[st.car]
        W, H = self.W, self.H
        for side in (-1, 1):
            cx = W // 2 + side * 98
            pygame.draw.rect(c, TYRE, (cx - 22, 112, 44, 30), border_radius=6)
            pygame.draw.rect(c, GREY, (cx - 22, 116, 44, 2))
        pygame.draw.polygon(c, body, [(108, 142), (148, 142), (136, 112), (120, 112)])
        pygame.draw.line(c, hi, (128, 113), (128, 141))
        pygame.draw.polygon(c, COWL, [(0, 150), (40, 136), (216, 136), (256, 150), (256, 192), (0, 192)])
        pygame.draw.line(c, COWL_HI, (40, 136), (216, 136))
        dial(c, 128, 166, 22, st.revs / MAXREV, REDLINE / MAXREV, "RPM")
        text_c(c, f"{int(st.v * 2.237):3d}", 128, 152, WHITE)
        dial(c, 70, 166, 14, st.heat if not CARS[st.car][1] else 0, 0.8)
        text_c(c, "HEAT" if not CARS[st.car][1] else "", 70, 183, GREY)
        dial(c, 186, 166, 14, st.fuel)
        text_c(c, "FUEL", 186, 183, GREY)
        c.fill(PANEL, (220, 152, 20, 22))
        text_c(c, "A" if CARS[st.car][1] else str(st.gear + 1), 230, 155, AMBER, 2)
        ew, tw, bw = st.wear
        for k, (lab, f) in enumerate((("E", ew), ("T", tw), ("B", bw))):
            lamp(c, 22 + k * 10, 160, 4, True, band_col(f))
            text(c, lab, 20 + k * 10, 167, GREY)
        lamp(c, 24, 180, 3, st.faults, RED)
        lamp(c, 36, 180, 3, st.faults, AMBER)
        reds, green = st.lights
        for k in range(4):
            on = (k < 3 and reds > k and not green) or (k == 3 and green)
            lamp(c, 92 + k * 24, 145, 3, on, GREEN if k == 3 else RED)
        a = math.radians(st.steer * -14)
        for sx in (-1, 1):
            ang = a + (math.pi if sx < 0 else 0)
            p = (128 + math.cos(ang) * 30, 200 - math.sin(ang) * 30)
            pygame.draw.circle(c, BLACK, p, 6)

    def hud(self, c, st):
        c.fill(BLACK, (0, 0, self.W, 10))
        text(c, f"LAP {max(1, st.lap)}/{st.laps}", 2, 2, WHITE)
        text_c(c, fmt_time(st.race_t), 128, 2, AMBER)
        text(c, "BEST " + fmt_time(st.best), 254 - text_w("BEST 0:00.00"), 2, WHITE)
        if st.offroad_t > 0 or st.stranded_t > 0:
            text_c(c, "OFF THE ROAD", 128, 30, WHITE)
        countdown_big(c, st, 128, 42, 2)

    map_style = "line"


class VariantB:
    name = "Open wheels, instrument strip"
    W, H, horizon, zoom = 320, 180, 70, 1.15
    car_scale = 2

    def cockpit(self, c, st):
        body, hi = CAR_COLOURS[st.car]
        W, H = self.W, self.H
        wob = int(math.sin(st.race_t * 18) * 2) if st.faults else 0
        for side in (-1, 1):
            cx = W // 2 + side * 120
            pygame.draw.line(c, GREY, (W // 2 + side * 20, 150), (cx - side * 26, 140 + wob), 2)
            pygame.draw.line(c, GREY, (W // 2 + side * 20, 158), (cx - side * 26, 152 + wob), 2)
            pygame.draw.rect(c, TYRE, (cx - 30, 118 + wob, 60, 46), border_radius=10)
            for k in range(4):
                pygame.draw.line(c, COWL_HI, (cx - 28, 124 + k * 9 + wob), (cx + 28, 124 + k * 9 + wob))
        pygame.draw.polygon(c, body, [(130, 162), (190, 162), (172, 124), (148, 124)])
        pygame.draw.polygon(c, hi, [(156, 124), (164, 124), (166, 162), (154, 162)])
        c.fill(PANEL, (0, 162, W, 18))
        pygame.draw.line(c, GREY, (0, 162), (W, 162))
        text(c, f"{int(st.v * 2.237):3d}", 4, 164, WHITE, 2)
        text(c, "MPH", 42, 170, GREY)
        text(c, "A" if CARS[st.car][1] else str(st.gear + 1), 66, 164, AMBER, 2)
        x = 84
        if not CARS[st.car][1]:
            text(c, "HEAT", x, 165, GREY)
            bar(c, x, 173, 30, 4, st.heat, band_col(st.heat))
            x += 36
        text(c, "FUEL", x, 165, GREY)
        bar(c, x, 173, 30, 4, st.fuel, AMBER if st.fuel > 0.2 else RED)
        x += 40
        for lab, f in zip("ETB", st.wear):
            text(c, lab, x, 165, GREY)
            bar(c, x + 7, 166, 16, 5, 1 - f, band_col(f))
            x += 28
        if st.faults:
            text(c, "PUNCTURE", 250, 164, RED)
            text(c, "TANK", 250, 172, AMBER)
        revs = st.revs / MAXREV
        for k in range(20):
            f = (k + 0.5) / 20
            col = GREEN if f < 0.6 else AMBER if f < REDLINE / MAXREV else RED
            c.fill(col if revs >= f else COWL_HI, (60 + k * 10, 1, 8, 4))

    def hud(self, c, st):
        text(c, f"LAP {max(1, st.lap)}/{st.laps}", 4, 9, WHITE)
        text(c, fmt_time(st.race_t), 4, 18, AMBER)
        text(c, "BEST", 316 - text_w("BEST"), 9, WHITE)
        text(c, fmt_time(st.best), 316 - text_w("0:00.00"), 18, WHITE)
        reds, green = st.lights
        if reds or green:
            c.fill(BLACK, (112, 26, 96, 26))
            for k in range(4):
                on = (k < 3 and reds > k and not green) or (k == 3 and green)
                lamp(c, 124 + k * 24, 39, 9, on, GREEN if k == 3 else RED)
        if st.offroad_t > 0 and st.stranded_t <= 0:
            left = max(0.0, 1 - st.offroad_t / 5)
            if int(st.offroad_t * 4) % 2 == 0:
                pygame.draw.rect(c, AMBER, (0, 0, self.W, 162), 2)
            text_c(c, "OFF THE ROAD", 160, 60, AMBER)
            bar(c, 110, 70, 100, 5, left, RED)
        if st.stranded_t > 0:
            text_c(c, "STRANDED", 160, 60, RED, 2)

    map_style = "road"


class VariantC:
    name = "Steering-wheel display"
    W, H, horizon, zoom = 384, 216, 92, 1.0
    car_scale = 3

    def cockpit(self, c, st):
        body, hi = CAR_COLOURS[st.car]
        W, H = self.W, self.H
        pygame.draw.polygon(c, body, [(0, 150), (60, 176), (90, 216), (0, 216)])
        pygame.draw.polygon(c, body, [(W, 150), (W - 60, 176), (W - 90, 216), (W, 216)])
        pygame.draw.line(c, hi, (0, 152), (60, 178))
        pygame.draw.line(c, hi, (W, 152), (W - 60, 178))
        cx, cy = W // 2, 190
        a = math.radians(st.steer * 12)
        rot = lambda px, py: (cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a))  # noqa: E731
        wheel = [(-84, -24), (-60, -32), (60, -32), (84, -24), (88, 20), (70, 40), (-70, 40), (-88, 20)]
        pygame.draw.polygon(c, COWL, [rot(*p) for p in wheel])
        for sx in (-1, 1):
            grip = [(sx * 66, -26), (sx * 84, -20), (sx * 86, 18), (sx * 68, 34)]
            pygame.draw.polygon(c, COWL_HI, [rot(*p) for p in grip], 1)
        c.fill(PANEL, (cx - 48, cy - 26, 96, 42))
        revs = st.revs / MAXREV
        for k in range(15):
            f = (k + 0.5) / 15
            col = GREEN if f < 0.6 else AMBER if f < REDLINE / MAXREV else RED
            c.fill(col if revs >= f else COWL_HI, (cx - 44 + k * 6, cy - 22, 4, 3))
        text_c(c, "A" if CARS[st.car][1] else str(st.gear + 1), cx, cy - 16, AMBER, 3)
        text(c, f"{int(st.v * 2.237):3d}", cx - 44, cy - 14, WHITE)
        text(c, "MPH", cx - 44, cy - 5, GREY)
        if not CARS[st.car][1]:
            text(c, "H", cx + 22, cy - 14, GREY)
            bar(c, cx + 29, cy - 13, 14, 4, st.heat, band_col(st.heat))
        text(c, "F", cx + 22, cy - 5, GREY)
        bar(c, cx + 29, cy - 4, 14, 4, st.fuel, AMBER)
        reds, green = st.lights
        for k in range(4):
            on = (k < 3 and reds > k and not green) or (k == 3 and green)
            lamp(c, cx - 18 + k * 12, cy + 11, 3, on, GREEN if k == 3 else RED)

    def hud(self, c, st):
        text(c, f"LAP {max(1, st.lap)}/{st.laps}", 6, 6, WHITE, 2)
        text(c, fmt_time(st.lap_t), 6, 24, AMBER)
        s = "BEST " + fmt_time(st.best)
        text(c, s, 378 - text_w(s), 6, WHITE)
        s = "RACE " + fmt_time(st.race_t)
        text(c, s, 378 - text_w(s), 16, GREY)
        warnings = [n for n, f in zip(("ENGINE", "TYRES", "BODY"), st.wear) if f > 0.4]
        if st.faults:
            warnings += ["PUNCTURE", "HOLED TANK"]
        for k, w in enumerate(warnings):
            f = dict(zip(("ENGINE", "TYRES", "BODY"), st.wear)).get(w, 1.0)
            text_c(c, w, 192, 6 + k * 9, band_col(f))
        countdown_big(c, st, 192, 70, 3)

    map_style = "dots"


VARIANTS = [VariantA(), VariantB(), VariantC()]


# ---------------------------------------------------------------- other screens


def draw_car_side(c, x, y, kind, body, hi, s):
    shapes = [
        ([(4, 10), (6, 6), (16, 5), (22, 3), (28, 5), (44, 8), (46, 11), (4, 12)], [(2, 4), (7, 4), (7, 6), (2, 6)], None),
        ([(5, 10), (7, 7), (18, 6), (22, 4), (27, 6), (46, 9), (47, 11), (5, 11)], [(1, 3), (6, 3), (6, 5), (1, 5)], [(42, 11), (48, 11), (48, 12), (42, 12)]),
        ([(4, 10), (8, 8), (20, 7), (24, 5), (28, 7), (47, 10), (48, 11), (4, 11)], [(0, 0), (8, 0), (8, 3), (0, 3)], [(41, 11), (49, 11), (49, 13), (41, 13)]),
    ][kind]
    sc = lambda pts: [(x + px * s, y + py * s) for px, py in pts]  # noqa: E731
    hull, wing, front = shapes
    pygame.draw.polygon(c, body, sc(hull))
    pygame.draw.polygon(c, body, sc(wing))
    pygame.draw.line(c, BLACK, sc([(4, 5)])[0], sc([(6, 9)])[0], max(1, s // 2))
    if front:
        pygame.draw.polygon(c, body, sc(front))
    pygame.draw.line(c, hi, sc([(8, 9)])[0], sc([(44, 10)])[0], max(1, s // 2))
    pygame.draw.circle(c, WHITE, sc([(23, 4)])[0], 2 * s)
    pygame.draw.line(c, BLACK, sc([(22, 4)])[0], sc([(25, 4)])[0], max(1, s // 2))
    for wx, wy, r in ((10, 11, 4.5 if kind else 5.5), (39, 11, 3.5 if kind else 4.5)):
        pygame.draw.circle(c, TYRE, sc([(wx, wy)])[0], r * s)
        pygame.draw.circle(c, GREY, sc([(wx, wy)])[0], max(1, r * s / 3))


def car_select(c, v, st):
    W, H = v.W, v.H
    c.fill(BLACK)
    text_c(c, "CHOOSE YOUR CAR", W // 2, 4, WHITE)
    s = v.car_scale
    row = (H - 16) // 3
    for k, (name, auto, pace, dur) in enumerate(CARS):
        y = 14 + k * row
        if k == st.car:
            pygame.draw.rect(c, AMBER, (2, y, W - 4, row - 2), 1)
        body, hi = CAR_COLOURS[k]
        c.fill(GRASS_D, (6, y + 3, 50 * s + 4, row - 8))
        draw_car_side(c, 8, y + row - 6 - 17 * s, k, body, hi, s)
        tx = 50 * s + 18
        text(c, name, tx, y + 4, WHITE if k == st.car else GREY)
        text(c, "AUTOMATIC" if auto else "MANUAL", tx, y + 13, GREY)
        bw = W - tx - 70
        text(c, "PACE", tx, y + 24, GREY)
        bar(c, tx + 64, y + 25, bw, 5, pace, AMBER)
        text(c, "DURABILITY", tx, y + 33, GREY)
        bar(c, tx + 64, y + 34, bw, 5, dur, GREEN)


def circuit_select(c, v, st, t):
    W, H = v.W, v.H
    c.fill(BLACK)
    text_c(c, "< PROTOTYPE PARK >", W // 2, 4, WHITE)
    box = min(W - 20, H - 50)
    ox, oy = (W - box) // 2, 16
    pts = [(ox + 4 + x * (box - 8), oy + 4 + y * (box - 8)) for x, y in st.track.outline]
    if v.map_style == "line":
        pygame.draw.lines(c, WHITE, True, pts, 1)
    elif v.map_style == "road":
        pygame.draw.lines(c, RUMBLE_A, True, pts, 5)
        pygame.draw.lines(c, ROAD_L, True, pts, 3)
        for k in range(0, len(pts) - 1, 6):
            a, b = pts[k], pts[k + 1]
            pygame.draw.line(c, WHITE, a, b, 1)
    else:
        for k, p in enumerate(pts):
            if k % 2 == 0:
                c.fill(GREY, (int(p[0]) - 1, int(p[1]) - 1, 2, 2))
        k = int(t * 12) % len(pts)
        pygame.draw.circle(c, CAR_COLOURS[st.car][0], pts[k], 3)
    sx, sy = pts[0]
    for k in range(4):
        c.fill(WHITE if k % 2 else BLACK, (int(sx) - 4 + k * 2, int(sy) - 2, 2, 2))
        c.fill(BLACK if k % 2 else WHITE, (int(sx) - 4 + k * 2, int(sy), 2, 2))
    text_c(c, "LAP RECORD " + fmt_time(st.record), W // 2, H - 30, AMBER)
    text_c(c, f"LAPS  < {st.laps:2d} >", W // 2, H - 18, WHITE)


# ---------------------------------------------------------------- shell


BAR_H = 34


class App:
    def __init__(self, shots=None):
        self.vi, self.pi = 0, 0
        self.fullscreen = False
        self.shots = shots
        self.track = Track()
        self.st = State(self.track)
        self.sprites = make_sprites()
        self.skyline = make_skyline(7)
        self.t = 0.0
        self.screens = ["race", "car", "circuit"]
        self.font = pygame.font.SysFont("sans", 14, bold=True)
        self.set_mode()

    @property
    def v(self):
        return VARIANTS[self.vi]

    def set_mode(self):
        v = self.v
        self.canvas = surface(v.W, v.H)
        if self.shots:
            self.scale = 3
            self.win = pygame.Surface((v.W * 3, v.H * 3 + BAR_H))
            return
        info = pygame.display.get_desktop_sizes()[0]
        if self.fullscreen:
            self.win = pygame.display.set_mode(info, pygame.FULLSCREEN)
            self.scale = min(info[0] // v.W, info[1] // v.H)
        else:
            self.scale = max(1, min((info[0] - 80) // v.W, (info[1] - 140 - BAR_H) // v.H))
            self.win = pygame.display.set_mode((v.W * self.scale, v.H * self.scale + BAR_H))

    def draw(self):
        v, st, c = self.v, self.st, self.canvas
        pal_name = list(PALETTES)[self.pi]
        if st.screen == "race":
            render_road(c, v, st, self.sprites, self.skyline)
            v.cockpit(c, st)
            v.hud(c, st)
            if st.pit_t is not None:
                bw = v.W // 2
                x0, y0 = v.W // 4, v.horizon - 20
                c.fill(BLACK, (x0 - 4, y0 - 4, bw + 8, 40))
                text_c(c, "PIT STOP", v.W // 2, y0, WHITE)
                for k, job in enumerate(("FUEL", "TYRES", "BODY")):
                    f = max(0.0, min(1.0, st.pit_t / 2 - k))
                    text(c, job, x0, y0 + 10 + k * 8, GREY)
                    bar(c, x0 + 40, y0 + 11 + k * 8, bw - 44, 4, f, GREEN if f >= 1 else AMBER)
        elif st.screen == "car":
            car_select(c, v, st)
        else:
            circuit_select(c, v, st, self.t)
        c.set_palette(rgb_list(PALETTES[pal_name]))
        big = pygame.transform.scale(c, (v.W * self.scale, v.H * self.scale))
        c.set_palette(IDENTITY)
        ww, wh = self.win.get_size()
        self.win.fill((0, 0, 0))
        ox = (ww - big.get_width()) // 2
        oy = (wh - BAR_H - big.get_height()) // 2 if not self.fullscreen else (wh - big.get_height()) // 2
        self.win.blit(big, (ox, max(0, oy)))
        label = (f"<  {'ABC'[self.vi]}: {v.name}  |  {v.W}x{v.H} x{self.scale}  |  "
                 f"{pal_name.split(' (')[0]}, {colour_count(PALETTES[pal_name])} colours  >")
        img = self.font.render(label, True, (20, 20, 20))
        pill = pygame.Rect(0, 0, img.get_width() + 24, BAR_H - 8)
        pill.midbottom = (ww // 2, wh - 4)
        pygame.draw.rect(self.win, (255, 0, 160), pill, border_radius=12)
        self.win.blit(img, img.get_rect(center=pill.center))

    def key(self, k):
        st = self.st
        if k == pygame.K_RIGHT:
            self.vi = (self.vi + 1) % len(VARIANTS)
            self.set_mode()
        elif k == pygame.K_LEFT:
            self.vi = (self.vi - 1) % len(VARIANTS)
            self.set_mode()
        elif k == pygame.K_p:
            self.pi = (self.pi + 1) % len(PALETTES)
        elif k == pygame.K_TAB:
            st.screen = self.screens[(self.screens.index(st.screen) + 1) % 3]
        elif k == pygame.K_F11:
            self.fullscreen = not self.fullscreen
            self.set_mode()
        elif k == pygame.K_SPACE:
            st.autopilot = not st.autopilot
        elif k == pygame.K_t:
            st.reset_start()
        elif k == pygame.K_c:
            names = list(CONDITIONS)
            st.cond = names[(names.index(st.cond) + 1) % 3]
        elif k == pygame.K_x:
            st.faults = not st.faults
        elif k == pygame.K_o:
            st.pit_t = 0.0
        elif k in (pygame.K_UP, pygame.K_DOWN) and st.screen == "car":
            st.car = (st.car + (1 if k == pygame.K_DOWN else -1)) % 3
        elif k == pygame.K_j and st.gear > 0 and not CARS[st.car][1]:
            st.gear -= 1
        elif k == pygame.K_l and st.gear < 4 and not CARS[st.car][1]:
            st.gear += 1

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    return
                if e.type == pygame.KEYDOWN:
                    self.key(e.key)
            dt = clock.tick(60) / 1000
            self.t += dt
            if self.st.screen == "race":
                update(self.st, pygame.key.get_pressed(), dt)
            self.draw()
            pygame.display.flip()

    def take_shots(self):
        os.makedirs(self.shots, exist_ok=True)
        keys = pygame.key.get_pressed()
        def at(z, x=0.0, **kw):
            def setup(s):
                s.z, s.x, s.v, s.seq_t, s.lap, s.gear = z, x, 50.0, 9.0, 2, 3
                s.revs = s.v * RATIOS[s.gear] * RPM_K
                for k, val in kw.items():
                    setattr(s, k, val)
            return setup

        plan = [  # (label, seconds of autopilot from reset, setup)
            ("lights", 2.2, lambda s: None),
            ("grid", 0.0, at(110.0, -3.0, seq_t=9.0)),
            ("approach", 0.0, at(330.0)),
            ("corner", 0.0, at(430.0, -2.0)),
            ("hairpin", 0.0, at(930.0, 1.0)),
            ("hill", 0.0, at(640.0, cond="worn")),
            ("crest", 0.0, at(800.0)),
            ("hazards", 0.0, at(480.0)),
            ("offroad", 0.0, at(250.0, HALF + 3, offroad_t=2.1, faults=True)),
        ]
        for vi in range(len(VARIANTS)):
            self.vi = vi
            self.set_mode()
            for pi in range(len(PALETTES)):
                self.pi = pi
                for label, secs, setup in plan:
                    st = self.st = State(self.track)
                    for _ in range(int(secs * 60)):
                        update(st, keys, 1 / 60)
                    setup(st)
                    for k in range(int(st.z // SEG)):
                        st.sky_off += self.track.segs[k].curve * 40
                    self.draw()
                    pygame.image.save(self.win, f"{self.shots}/{'ABC'[vi]}{pi}_{label}.png")
                for scr in ("car", "circuit"):
                    self.st = State(self.track)
                    self.st.screen = scr
                    self.draw()
                    pygame.image.save(self.win, f"{self.shots}/{'ABC'[vi]}{pi}_{scr}.png")


def main():
    shots = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--shots" else None
    if shots:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    if shots:
        pygame.display.set_mode((1, 1))
        App(shots).take_shots()
    else:
        pygame.display.set_caption("Hot Lapper look prototype (throwaway)")
        App().run()
    pygame.quit()


if __name__ == "__main__":
    main()
