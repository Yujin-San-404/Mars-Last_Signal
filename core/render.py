"""World + interior drawing (simple shapes only)."""
import math, pygame
from config import *
from ui import draw as D
from data.resources import RESOURCES, RARITY_COLOR, RARITY_ORDER
from base import layout
from base import stations
from exploration.discoveries import rarity_of

PAL = [(150, 72, 48), (156, 76, 51), (146, 70, 47), (160, 80, 54), (142, 68, 45), (153, 74, 50), (148, 71, 49), (158, 78, 53)]
HZ = {"radiation": (170, 60, 220), "cold": (90, 150, 255), "dust_trap": (210, 180, 110)}
_hz_cache, _vig = {}, None

def on(x, y, cam, m=120):
    return -m < x - cam[0] < SCREEN_W + m and -m < y - cam[1] < SCREEN_H + m

def terrain(s, g, cam):
    w, T = g.world, 160
    x0, y0 = int(cam[0] // T), int(cam[1] // T)
    for ix in range(x0, x0 + SCREEN_W // T + 2):
        for iy in range(y0, y0 + SCREEN_H // T + 2):
            h = (ix * 73856093 ^ iy * 19349663) & 7
            px, py = ix * T - cam[0], iy * T - cam[1]
            far = math.hypot(ix * T + T / 2 - BASE_POS[0], iy * T + T / 2 - BASE_POS[1]) > WORLD_RADIUS
            pygame.draw.rect(s, (22, 10, 12) if far else PAL[h], (px, py, T + 1, T + 1))
            if not far and h % 3 == 0: pygame.draw.circle(s, (130, 60, 40), (px + 40 + h * 9, py + 60 + h * 7), 3)
    for v in w.valleys:
        pts = [(x - cam[0], y - cam[1]) for x, y in v]
        if any(-300 < p[0] < SCREEN_W + 300 and -300 < p[1] < SCREEN_H + 300 for p in pts): pygame.draw.polygon(s, (128, 58, 40), pts)
    for x, y, r in w.craters:
        if on(x, y, cam, r + 20):
            sx, sy = x - cam[0], y - cam[1]
            pygame.draw.circle(s, (126, 58, 40), (sx, sy), r); pygame.draw.circle(s, (176, 96, 66), (sx, sy), r, 5)
            pygame.draw.circle(s, (112, 50, 34), (sx + r * 0.1, sy + r * 0.1), r * 0.6)
    for x, y, rx, ry, sh in w.hills:
        if on(x, y, cam, rx):
            c = (166 + sh, 90 + sh, 62 + sh)
            pygame.draw.ellipse(s, c, (x - cam[0] - rx, y - cam[1] - ry, rx * 2, ry * 2)); pygame.draw.ellipse(s, (130, 64, 44), (x - cam[0] - rx, y - cam[1] - ry, rx * 2, ry * 2), 3)
    for i, hz in enumerate(w.hazards):
        if on(hz["x"], hz["y"], cam, hz["r"]):
            if i not in _hz_cache:
                r = int(hz["r"]); sf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(sf, HZ[hz["type"]] + (55,), (r, r), r); pygame.draw.circle(sf, HZ[hz["type"]] + (140,), (r, r), r, 3)
                _hz_cache[i] = sf
            sf = _hz_cache[i]
            s.blit(sf, (hz["x"] - cam[0] - sf.get_width() / 2, hz["y"] - cam[1] - sf.get_height() / 2))
            if w.explored and (int(hz["x"] // 300), int(hz["y"] // 300)) in w.explored:
                D.text(s, hz["type"].replace("_", " ").upper(), (hz["x"] - cam[0], hz["y"] - cam[1]), 12, HZ[hz["type"]], True, "center")

def node_color(n):
    return RESOURCES[n["items"][0][0]]["color"] if n["items"] else (200, 200, 200)

def nodes(s, g, cam):
    t = g.real_t
    for n in g.world.nodes.values():
        if not on(n["x"], n["y"], cam, 40): continue
        x, y = n["x"] - cam[0], n["y"] - cam[1]
        if n["hidden"] and not n["revealed"]:
            pygame.draw.ellipse(s, (170, 90, 62), (x - 14, y - 6, 28, 12)); continue
        rar = rarity_of(n["items"]) if n["items"] else "common"
        col = node_color(n)
        pulse = 0.5 + 0.5 * math.sin(t * 3 + n["x"])
        if n["kind"] in ("crate", "vault"):
            pygame.draw.rect(s, (70, 76, 90) if n["kind"] == "crate" else (110, 60, 60), (x - 12, y - 10, 24, 20))
            pygame.draw.rect(s, col, (x - 12, y - 10, 24, 20), 2); pygame.draw.line(s, col, (x - 12, y), (x + 12, y), 1)
            gl = RARITY_COLOR[rar] if n["kind"] == "crate" else (255, 90, 90)
            pygame.draw.rect(s, tuple(int(c * (0.45 + 0.4 * pulse)) for c in gl), (x - 16, y - 14, 32, 28), 2, border_radius=4)
        else:
            sz = 6 + int(RESOURCES[n["items"][0][0]]["weight"] * 2)
            pygame.draw.polygon(s, col, [(x - sz, y + sz // 2), (x - sz // 2, y - sz), (x + sz, y - sz // 2), (x + sz // 2, y + sz)])
            if rar != "common":
                gl = RARITY_COLOR[rar]; pygame.draw.circle(s, tuple(int(c * (0.4 + 0.45 * pulse)) for c in gl), (x, y), sz + 5 + int(pulse * 2), 2)
        if g.player.pos is g.player.wpos and math.hypot(g.player.wpos[0] - n["x"], g.player.wpos[1] - n["y"]) < 130 and not g.player.in_rover:
            if n["kind"] == "vault" and n["cost"]:
                from resources import resource_manager as RM
                D.text(s, "SEALED: " + (RM.missing_text([g.player.inv], n["cost"]) or "READY"), (x, y - 26), 12, (255, 120, 120), True, "center")

def structs(s, g, cam):
    for rc, lid in g.world.structs:
        if on(rc.centerx, rc.centery, cam, rc.w + 40):
            r = rc.move(-cam[0], -cam[1])
            pygame.draw.rect(s, (84, 88, 100), r); pygame.draw.rect(s, (40, 44, 54), r, 3)
            pygame.draw.line(s, (60, 64, 74), r.topleft, r.bottomright, 2)

def base_ext(s, g, cam):
    br = g.world.base_rect
    if not on(br.centerx, br.centery, cam, 500): return
    for i in range(g.base.panels):
        x, y = BASE_POS[0] + 235 + (i % 2) * 62 - cam[0], BASE_POS[1] - 110 + (i // 2) * 52 - cam[1]
        pygame.draw.rect(s, (30, 50, 110), (x, y, 54, 44)); pygame.draw.rect(s, (110, 150, 230), (x, y, 54, 44), 2); pygame.draw.line(s, (110, 150, 230), (x + 27, y), (x + 27, y + 44), 1)
    r = br.move(-cam[0], -cam[1])
    pygame.draw.rect(s, (96, 102, 116), r, border_radius=14); pygame.draw.rect(s, (40, 46, 60), r, 4, border_radius=14)
    pygame.draw.rect(s, (70, 76, 90), r.inflate(-60, -50), border_radius=8)
    for k in range(4): pygame.draw.circle(s, (130, 190, 220), (r.x + 60 + k * 85, r.y + 40), 12, 2)
    dx, dy = g.world.door[0] - cam[0], g.world.door[1] - cam[1]
    pygame.draw.rect(s, (200, 170, 60), (dx - 26, r.bottom - 6, 52, 14)); D.text(s, "AIRLOCK", (dx, r.bottom + 22), 12, (230, 200, 90), True, "center")
    D.text(s, "MARS BASE", (r.centerx, r.centery), 18, (170, 190, 215), True, "center")
    pygame.draw.line(s, (200, 200, 210), (r.x + 40, r.y), (r.x + 40, r.y - 50), 3); pygame.draw.circle(s, (230, 70, 70), (r.x + 40, r.y - 50), 5)

def rocks(s, g, cam):
    px, py = cam[0] + SCREEN_W / 2, cam[1] + SCREEN_H / 2
    cx, cy = int(px // 400), int(py // 400)
    for i in range(-2, 3):
        for j in range(-2, 3):
            for x, y, r, _ in g.world.rgrid.get((cx + i, cy + j), ()):
                if on(x, y, cam, 40):
                    pygame.draw.circle(s, (92, 52, 42), (x - cam[0] + 2, y - cam[1] + 3), r); pygame.draw.circle(s, (120, 80, 64), (x - cam[0], y - cam[1]), r)
                    pygame.draw.circle(s, (150, 106, 86), (x - cam[0] - r * 0.3, y - cam[1] - r * 0.3), r * 0.4)

def rover_draw(s, g, cam):
    r = g.rover
    c, a = math.cos(r.angle), math.sin(r.angle)
    def P(x, y): return (r.pos[0] - cam[0] + x * c - y * a, r.pos[1] - cam[1] + x * a + y * c)
    for wx, wy in ((-16, -15), (16, -15), (-16, 15), (16, 15)): pygame.draw.circle(s, (30, 30, 36), P(wx, wy), 7)
    pygame.draw.polygon(s, (210, 200, 180) if r.integ > 30 else (150, 130, 120), [P(-24, -13), P(24, -13), P(24, 13), P(-24, 13)])
    pygame.draw.polygon(s, (60, 130, 170), [P(6, -9), P(20, -9), P(20, 9), P(6, 9)])
    pygame.draw.polygon(s, (90, 90, 100), [P(-24, -13), P(24, -13), P(24, 13), P(-24, 13)], 2)
    if r.driven: pygame.draw.circle(s, (90, 255, 140), P(-18, 0), 3)

def player_draw(s, g, cam, pos):
    p = g.player
    x, y = pos[0] - cam[0], pos[1] - cam[1]
    pygame.draw.ellipse(s, (60, 36, 30), (x - 11, y + 6, 22, 9))
    pygame.draw.circle(s, (225, 228, 235), (x, y), 11); pygame.draw.circle(s, (120, 125, 140), (x, y), 11, 2)
    fx, fy = p.facing
    pygame.draw.circle(s, (240, 150, 40), (x + fx * 5, y + fy * 5), 5)
    pygame.draw.rect(s, (160, 165, 180), (x - fx * 12 - 4, y - fy * 12 - 4, 8, 8))

def weather(s, g, cam):
    global _vig
    env = g.env
    light = 0.12 + 0.88 * env["daylight"]
    st = env["storm"]
    if st > 0.02:
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); ov.fill((170, 100, 60, int(150 * st))); s.blit(ov, (0, 0))
        for i in range(int(40 + 60 * st)):
            x = (i * 97 + g.real_t * (300 + i * 3)) % (SCREEN_W + 100) - 50; y = (i * 53 + g.real_t * 40) % SCREEN_H
            pygame.draw.line(s, (220, 170, 120), (x, y), (x - 18, y + 4), 1)
    if light < 0.95:
        if not hasattr(weather, "n"): weather.n = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        n = weather.n; a = int(165 * (1 - light))
        n.fill((6, 10, 32, a))
        cxp, cyp = SCREEN_W // 2, SCREEN_H // 2
        for r, k in ((300, 0.8), (230, 0.55), (170, 0.3), (110, 0.1)):
            pygame.draw.circle(n, (6, 10, 32, int(a * k)), (cxp, cyp), r)
        s.blit(n, (0, 0))

def vignette(s, g):
    global _vig
    st = g.player.stats
    danger = max(st["oxygen"] < 25, st["health"] < 35, st["warmth"] < 15, st["radiation"] > 80, st["hunger"] <= 0, st["hydration"] <= 0)
    over = not g.player.inside and g.player.dist > SAFE_RANGE
    if not (danger or over): return
    if _vig is None:
        _vig = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for i in range(14): pygame.draw.rect(_vig, (255, 20, 20, 10 + i * 6), (i * 4, i * 4, SCREEN_W - i * 8, SCREEN_H - i * 8), 4)
    _vig.set_alpha(int(120 + 110 * math.sin(g.real_t * 6)) if danger else 120)
    s.blit(_vig, (0, 0))

def exterior(s, g):
    p = g.player
    cx, cy = (g.rover.pos if p.in_rover else p.wpos)
    cam = (cx - SCREEN_W / 2, cy - SCREEN_H / 2)
    terrain(s, g, cam); structs(s, g, cam); base_ext(s, g, cam); nodes(s, g, cam); rocks(s, g, cam)
    rover_draw(s, g, cam)
    if not p.in_rover: player_draw(s, g, cam, p.wpos)
    # rover/door markers
    if not p.in_rover and math.hypot(p.wpos[0] - g.rover.pos[0], p.wpos[1] - g.rover.pos[1]) < 140:
        D.text(s, f"ROVER  BAT {g.rover.battery:.0f}%  HULL {g.rover.integ:.0f}%", (g.rover.pos[0] - cam[0], g.rover.pos[1] - cam[1] - 40), 12, (230, 220, 170), True, "center")
    if math.hypot(cx - g.world.door[0], cy - g.world.door[1]) < 260:
        bob = math.sin(g.real_t * 5) * 4
        pygame.draw.polygon(s, (255, 210, 70), [(g.world.door[0] - cam[0] - 8, g.world.door[1] - cam[1] + 22 + bob), (g.world.door[0] - cam[0] + 8, g.world.door[1] - cam[1] + 22 + bob), (g.world.door[0] - cam[0], g.world.door[1] - cam[1] + 34 + bob)])
    weather(s, g, cam)

def interior(s, g):
    s.fill((14, 18, 24))
    p = g.player
    ox, oy = SCREEN_W / 2 - 600, SCREEN_H / 2 - 350
    ox = min(0, max(SCREEN_W - 1200, SCREEN_W / 2 - p.ipos[0])); oy = min(0, max(SCREEN_H - 700, SCREEN_H / 2 - p.ipos[1]))
    for name, rc, col in layout.ROOMS:
        r = rc.move(ox, oy); pygame.draw.rect(s, col, r)
        for gx in range(rc.x, rc.right, 40): pygame.draw.line(s, tuple(c - 6 for c in col), (gx + ox, r.y), (gx + ox, r.bottom))
        if name != "CORRIDOR": D.text(s, name, (r.x + 8, r.y + 6), 12, (150, 170, 190), True)
    for w in layout.WALLS: pygame.draw.rect(s, (110, 118, 134), w.move(ox, oy))
    b = g.base
    cols = {"sys": (110, 160, 190), "save": (90, 200, 120), "assistant": (120, 140, 255), "comms": (140, 120, 220), "chest": (170, 140, 90), "tank": (70, 130, 255), "processor": (200, 130, 70), "exit": (230, 190, 60)}
    near = stations.nearby(g)
    for st in layout.STATIONS:
        x, y = st["x"] + ox, st["y"] + oy
        c = cols.get(st["kind"], (150, 150, 150))
        if st["kind"] == "sys":
            v = b.sys[st["sys"]]; c = (220, 80, 70) if v < 15 else (230, 180, 70) if v < 60 else (90, 210, 130)
        if st["kind"] == "exit": pygame.draw.rect(s, c, (x - 50, y - 6, 100, 12)); 
        else: pygame.draw.rect(s, (40, 46, 58), (x - 22, y - 22, 44, 44)); pygame.draw.rect(s, c, (x - 22, y - 22, 44, 44), 3)
        if st["kind"] == "tank": pygame.draw.rect(s, (70, 130, 255), (x - 18, y + 18 - int(36 * b.tank / TANK_CAP), 36, int(36 * b.tank / TANK_CAP)))
        if st["kind"] == "sys": D.text(s, f"{b.sys[st['sys']]:.0f}%", (x, y), 13, (240, 240, 240), True, "center")
        if st["kind"] == "processor" and not b.processor: D.text(s, "OFFLINE", (x, y), 10, (255, 150, 90), True, "center")
        D.text(s, st["label"], (x, y + 32), 11, (190, 205, 220), False, "center")
    for i, pl in enumerate(layout.PLOTS):
        x, y = pl["x"] + ox, pl["y"] + oy; q = b.plots[i]
        rc = pygame.Rect(x - 34, y - 32, 68, 64)
        pygame.draw.rect(s, (70, 50, 38) if q.unlocked else (30, 34, 40), rc, border_radius=6); pygame.draw.rect(s, (110, 170, 110) if q.unlocked else (80, 80, 90), rc, 2, border_radius=6)
        if not q.unlocked: D.text(s, "LOCKED", (x, y), 11, (150, 150, 160), True, "center")
        elif q.crop:
            from data.systems import CROPS
            h = int(8 + 22 * q.prog); col = (230, 200, 90) if q.prog >= 1 else (90, 200, 90)
            pygame.draw.circle(s, col, (x, y - 4), h // 2 + 4); pygame.draw.rect(s, (60, 130, 60), (x - 1, y - 4, 3, 22))
            D.bar(s, pygame.Rect(x - 28, y + 22, 56, 5), q.prog, col)
            if q.blight > 5: D.bar(s, pygame.Rect(x - 28, y + 28, 56, 3), q.blight / 100, (200, 60, 200))
            if q.prog >= 1: D.text(s, "READY", (x, y - 26), 10, (255, 240, 120), True, "center")
        else: D.text(s, "EMPTY", (x, y), 11, (150, 130, 110), False, "center")
    # markers for requirements
    for st in (layout.STATIONS + layout.PLOTS):
        if st["kind"] == "plot" and st["idx"] >= len(b.plots): continue
        if math.hypot(p.ipos[0] - st["x"], p.ipos[1] - st["y"]) > 150: continue
        rq = stations.reqs_for(g, st)
        if not rq: continue
        title, lst = rq
        x, y = st["x"] + ox, st["y"] + oy - 38 - 14 * len(lst)
        bob = math.sin(g.real_t * 5) * 3
        wd = max(190, 10 * len(title) // 1 + 20)
        D.panel(s, pygame.Rect(x - wd // 2, y - 6 + bob, wd, 22 + 15 * len(lst)), 215, (255, 200, 80))
        D.text(s, title, (x, y + 2 + bob), 11, (255, 210, 100), True, "center")
        from resources import resource_manager as RM
        for k, (key, have, need) in enumerate(lst):
            D.text(s, f"[{RM.key_name(key).upper()}] {have} / {need}", (x, y + 18 + 15 * k + bob), 12, (110, 230, 130) if have >= need else (255, 120, 110), True, "center")
    player_draw(s, g, (-ox, -oy), p.ipos)
    if b.o2 < 30: D.text(s, "BASE AIR LOW", (SCREEN_W // 2, 130), 22, (255, 80, 80), True, "center")

def scene(s, g):
    if g.player.inside: interior(s, g)
    else: exterior(s, g)
