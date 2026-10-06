"""Large continuous Mars map: terrain, rocks, hazards, sites, collectible nodes, exploration state."""
import math, random
import pygame
from config import *
from data.resources import RESOURCES
from exploration import locations as L, discoveries as D
from core.collision import resolve

CELL = 400
FOG = 300

class World:
    def __init__(self, seed=WORLD_SEED):
        self.seed = seed
        self.hills, self.craters, self.valleys, self.hazards = [], [], [], []
        self.rocks, self.rgrid = [], {}
        self.structs = []            # (Rect, loc_id)
        self.locations, self.nodes = [], {}
        self.explored = set()
        self._nid = 0
        self._lid = 0
        self.base_rect = pygame.Rect(BASE_POS[0] - 190, BASE_POS[1] - 120, 380, 200)
        self.door = (BASE_POS[0], BASE_POS[1] + 116)
        self._terrain(random.Random(seed))
        self._locations(random.Random(seed + 1))
        self._scatter(random.Random(seed + 2))
        self._rocks(random.Random(seed + 3))

    # ---------------- generation ----------------
    def _rand_point(self, rng, rmin, rmax):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(rmin, rmax)
        return BASE_POS[0] + r * math.cos(a), BASE_POS[1] + r * math.sin(a)

    def _terrain(self, rng):
        for _ in range(40):
            x, y = self._rand_point(rng, 700, WORLD_RADIUS)
            self.hills.append((x, y, rng.uniform(200, 600), rng.uniform(150, 420), rng.randint(-10, 14)))
        for _ in range(30):
            x, y = self._rand_point(rng, 600, WORLD_RADIUS)
            self.craters.append((x, y, rng.uniform(100, 450)))
        for _ in range(12):
            x, y = self._rand_point(rng, 1500, WORLD_RADIUS - 500)
            a, ln, w = rng.uniform(0, math.pi), rng.uniform(1500, 3000), rng.uniform(150, 350)
            ux, uy = math.cos(a), math.sin(a)
            nx, ny = -uy, ux
            self.valleys.append([(x - ux * ln / 2 + nx * w / 2, y - uy * ln / 2 + ny * w / 2), (x + ux * ln / 2 + nx * w / 2, y + uy * ln / 2 + ny * w / 2),
                                 (x + ux * ln / 2 - nx * w / 2, y + uy * ln / 2 - ny * w / 2), (x - ux * ln / 2 - nx * w / 2, y - uy * ln / 2 - ny * w / 2)])
        for _ in range(7):
            x, y = self._rand_point(rng, 1500, 5800)
            self.hazards.append(dict(type="dust_trap", x=x, y=y, r=rng.uniform(200, 320)))
        for _ in range(2):
            x, y = self._rand_point(rng, 4800, 6200)
            self.hazards.append(dict(type="radiation", x=x, y=y, r=rng.uniform(280, 400)))

    def _locations(self, rng):
        for d in L.DEFS:
            x, y = D.bearing_pos(BASE_POS, d["bearing"], d["dist"])
            loc = dict(id=d["id"], name=d["name"], kind=d["kind"], x=x, y=y, radius=d["ring"] + 120, discovered=bool(d.get("known")),
                       desc=d["desc"], range=d["range"], dynamic=False)
            self.locations.append(loc)
            for dx, dy, w, h in d["structs"]:
                self.structs.append((pygame.Rect(int(x + dx - w / 2), int(y + dy - h / 2), w, h), d["id"]))
            n = len(d["crates"])
            off = rng.uniform(0, math.tau)
            for i, (items, cost) in enumerate(d["crates"]):
                a = off + i * math.tau / max(1, n)
                self.add_node(x + math.cos(a) * d["ring"], y + math.sin(a) * d["ring"], [list(t) for t in items],
                              kind="vault" if cost else "crate", label=d["name"], hidden=bool(d.get("hidden")), cost=cost, loc=d["id"])
            if d.get("hazard"):
                t, bo, bd, r = d["hazard"]
                hx, hy = D.bearing_pos((x, y), bo, bd)
                self.hazards.append(dict(type=t, x=hx, y=hy, r=r))

    def _scatter(self, rng):
        def place(zone, count, rmin, rmax):
            n = 0
            while n < count:
                x, y = self._rand_point(rng, rmin, rmax)
                if any(math.hypot(x - l["x"], y - l["y"]) < 160 for l in self.locations):
                    continue
                rid, q = D.pick(rng, D.ZONES[zone])
                self.add_node(x, y, [[rid, q]], kind="scrap", label=RESOURCES[rid]["name"])
                n += 1
        place("near", 55, 380, 1800)
        place("mid", 70, 1800, 4300)
        place("far", 40, 4300, 6300)
        for _ in range(6):                       # hidden buried caches, found by walking close
            x, y = self._rand_point(rng, 1500, 5000)
            items = [[*D.pick(rng, D.BURIED)] for _ in range(2)]
            self.add_node(x, y, items, kind="crate", label="Buried Equipment", hidden=True)

    def _rocks(self, rng):
        sx = [s for s, _ in self.structs]
        for _ in range(1700):
            x, y = self._rand_point(rng, 60, WORLD_RADIUS)
            r = rng.uniform(9, 36)
            if self.base_rect.inflate(160, 160).collidepoint(x, y) or math.hypot(x - self.door[0], y - self.door[1]) < 150:
                continue
            if any(math.hypot(x - n["x"], y - n["y"]) < 50 + r for n in self.nodes.values()):
                continue
            if any(rc.inflate(40, 40).collidepoint(x, y) for rc in sx):
                continue
            if math.hypot(x - BASE_POS[0] - 260, y - BASE_POS[1] - 170) < 110:
                continue
            self.rocks.append((x, y, r, rng.randint(0, 3)))
            self.rgrid.setdefault((int(x // CELL), int(y // CELL)), []).append((x, y, r, 0))

    # ---------------- nodes / sites ----------------
    def add_node(self, x, y, items, kind="crate", label="Supply Crate", hidden=False, cost=None, loc=None):
        nid = f"n{self._nid}"
        self._nid += 1
        self.nodes[nid] = dict(id=nid, x=x, y=y, items=items, kind=kind, label=label, hidden=hidden, revealed=False, cost=cost, loc=loc)
        return nid

    def spawn_site(self, name, kind, bearing, dist, crates, desc="", discovered=True):
        x, y = D.bearing_pos(BASE_POS, bearing, dist)
        d = math.hypot(x - BASE_POS[0], y - BASE_POS[1])
        if d > WORLD_RADIUS - 300:
            x = BASE_POS[0] + (x - BASE_POS[0]) * (WORLD_RADIUS - 300) / d
            y = BASE_POS[1] + (y - BASE_POS[1]) * (WORLD_RADIUS - 300) / d
        lid = f"ev{self._lid}"
        self._lid += 1
        loc = dict(id=lid, name=name, kind=kind, x=x, y=y, radius=160, discovered=discovered, desc=desc, range=900, dynamic=True)
        self.locations.append(loc)
        for i, items in enumerate(crates):
            a = i * math.tau / max(1, len(crates)) + 0.7
            self.add_node(x + math.cos(a) * 50, y + math.sin(a) * 50, [list(t) for t in items], kind="crate", label=name, loc=lid)
        return loc

    def remove_node(self, nid):
        self.nodes.pop(nid, None)

    def loc_by_id(self, lid):
        return next((l for l in self.locations if l["id"] == lid), None)

    def loc_remaining(self, lid):
        return [n for n in self.nodes.values() if n["loc"] == lid]

    def known_node(self, n):
        if n["hidden"] and not n["revealed"]:
            return False
        l = self.loc_by_id(n["loc"]) if n["loc"] else None
        if l and l["discovered"]:
            return True
        return (int(n["x"] // FOG), int(n["y"] // FOG)) in self.explored

    # ---------------- queries ----------------
    def rocks_near(self, x, y, r):
        cx, cy = int(x // CELL), int(y // CELL)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for rk in self.rgrid.get((cx + i, cy + j), ()):
                    yield rk[:3]

    def obstacles(self, x, y, r):
        circles = list(self.rocks_near(x, y, r))
        rects = [s for s, _ in self.structs if s.inflate(2 * r + 20, 2 * r + 20).collidepoint(x, y)]
        if self.base_rect.inflate(2 * r + 20, 2 * r + 20).collidepoint(x, y):
            rects.append(self.base_rect)
        return circles, rects

    def move(self, pos, dx, dy, r, circles=()):
        hit = False
        for ax, d in ((0, dx), (1, dy)):
            pos[ax] += d
            cs, rs = self.obstacles(pos[0], pos[1], r)
            if resolve(pos, r, list(cs) + list(circles), rs):
                hit = True
        ddx, ddy = pos[0] - BASE_POS[0], pos[1] - BASE_POS[1]
        dd = math.hypot(ddx, ddy)
        if dd > WORLD_RADIUS:
            pos[0] = BASE_POS[0] + ddx / dd * WORLD_RADIUS
            pos[1] = BASE_POS[1] + ddy / dd * WORLD_RADIUS
        return hit

    def hazards_at(self, x, y):
        return [h["type"] for h in self.hazards if (x - h["x"]) ** 2 + (y - h["y"]) ** 2 < h["r"] ** 2]

    # ---------------- exploration ----------------
    def update_discovery(self, px, py, sight=1.0):
        found = []
        R = 2 if sight > 0.6 else 1
        cx, cy = int(px // FOG), int(py // FOG)
        for i in range(-R, R + 1):
            for j in range(-R, R + 1):
                self.explored.add((cx + i, cy + j))
        for l in self.locations:
            if not l["discovered"] and math.hypot(px - l["x"], py - l["y"]) < l["range"] * sight:
                l["discovered"] = True
                found.append(l)
        for n in self.nodes.values():
            if n["hidden"] and not n["revealed"] and (px - n["x"]) ** 2 + (py - n["y"]) ** 2 < 100 ** 2:
                n["revealed"] = True
        return found

    def reveal_nearest_unknown(self):
        cand = [l for l in self.locations if not l["discovered"]]
        if not cand:
            return None
        l = min(cand, key=lambda l: math.hypot(l["x"] - BASE_POS[0], l["y"] - BASE_POS[1]))
        l["discovered"] = True
        cx, cy = int(l["x"] // FOG), int(l["y"] // FOG)
        for i in range(-2, 3):
            for j in range(-2, 3):
                self.explored.add((cx + i, cy + j))
        for n in self.nodes.values():
            if n["loc"] == l["id"]:
                n["revealed"] = True
        return l

    # ---------------- save ----------------
    def to_dict(self):
        return dict(nodes=list(self.nodes.values()), locations=self.locations, explored=[list(c) for c in self.explored], nid=self._nid, lid=self._lid)

    def load(self, d):
        self.nodes = {n["id"]: n for n in d["nodes"]}
        self.locations = d["locations"]
        self.explored = {tuple(c) for c in d["explored"]}
        self._nid, self._lid = d["nid"], d["lid"]
