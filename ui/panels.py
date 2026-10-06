import math, pygame
from config import *
from ui import draw as D
from data.resources import RESOURCES, RARITY_COLOR
from exploration.discoveries import fmt_dist

def inventory(g, s):
    p = g.player
    D.panel(s, pygame.Rect(0, 0, SCREEN_W, SCREEN_H), 150, (0, 0, 0))
    r = pygame.Rect(150, 70, 800, 540); D.panel(s, r, 240, (110, 170, 210), "INVENTORY   W/S select  A/D switch side  J move (SHIFT = stack)  K use  I/ESC close")
    cont = g.container
    cols = [("CARRIED", p.inv)] + ([(g.container_name, cont)] if cont else [])
    for ci, (title, inv) in enumerate(cols):
        x = r.x + 14 + ci * 392
        act = (g.inv_pane == ci)
        D.text(s, f"{title}  {inv.weight():.1f}/{inv.capacity:.0f} kg", (x, r.y + 28), 14, (255, 225, 120) if act else (170, 190, 205), True)
        D.bar(s, pygame.Rect(x, r.y + 48, 372, 7), inv.weight() / inv.capacity, (200, 190, 140))
        order = inv.order()
        cur = p.sel if ci == 0 else g.inv_cur
        cur = max(0, min(cur, len(order) - 1)) if order else 0
        top = max(0, cur - 11)
        for i, rid in enumerate(order[top:top + 12]):
            idx = top + i; y = r.y + 64 + i * 22
            if act and idx == cur: pygame.draw.rect(s, (50, 80, 110), (x - 2, y - 1, 376, 21))
            d = RESOURCES[rid]
            pygame.draw.rect(s, d["color"], (x + 2, y + 3, 12, 12))
            D.text(s, d["name"], (x + 22, y), 14, RARITY_COLOR[d["rarity"]])
            D.text(s, f"x{inv.items[rid]}", (x + 250, y), 14); D.text(s, f"{d['weight'] * inv.items[rid]:.1f}kg", (x + 372, y), 13, (150, 165, 180), False, "topright")
        if not order: D.text(s, "(empty)", (x + 10, r.y + 70), 14, (110, 120, 130))
    inv = cols[min(g.inv_pane, len(cols) - 1)][1]
    order = inv.order()
    if order:
        cur = p.sel if g.inv_pane == 0 else g.inv_cur
        rid = order[max(0, min(cur, len(order) - 1))]; d = RESOURCES[rid]
        y = r.y + 345
        D.text(s, f"{d['name']}   {d['weight']} kg each   [{d['rarity'].upper().replace('_', ' ')}]   {d['category']}", (r.x + 14, y), 15, RARITY_COLOR[d["rarity"]], True)
        D.text(s, d["desc"], (r.x + 14, y + 22), 13, (200, 210, 220))
        D.text(s, "USES:", (r.x + 14, y + 44), 13, (120, 190, 230), True)
        for i, u in enumerate(d["uses"]): D.text(s, "- " + u, (r.x + 24, y + 62 + i * 16), 13, (210, 220, 215))

def map_panel(g, s):
    D.panel(s, pygame.Rect(0, 0, SCREEN_W, SCREEN_H), 170, (0, 0, 0))
    r = pygame.Rect(40, 30, 640, 640); D.panel(s, r, 245, (110, 170, 210), "MAP   M/ESC close")
    sc = 600 / WORLD_SIZE
    ox, oy = r.x + 20, r.y + 28
    pygame.draw.rect(s, (14, 10, 12), (ox, oy, 600, 600))
    cell = FOG * sc
    for cx, cy in g.world.explored:
        pygame.draw.rect(s, (118, 62, 46), (ox + cx * cell, oy + cy * cell, cell + 1, cell + 1))
    pygame.draw.circle(s, (60, 70, 90), (ox + BASE_POS[0] * sc, oy + BASE_POS[1] * sc), SAFE_RANGE * sc, 1)
    pygame.draw.circle(s, (160, 60, 60), (ox + BASE_POS[0] * sc, oy + BASE_POS[1] * sc), MAX_RANGE * sc, 1)
    for h in g.world.hazards:
        if (int(h["x"] // FOG), int(h["y"] // FOG)) in g.world.explored:
            pygame.draw.circle(s, {"radiation": (170, 60, 220), "cold": (90, 150, 255), "dust_trap": (210, 180, 110)}[h["type"]], (ox + h["x"] * sc, oy + h["y"] * sc), max(3, h["r"] * sc), 1)
    for l in g.world.locations:
        if l["discovered"]:
            x, y = ox + l["x"] * sc, oy + l["y"] * sc
            left = len(g.world.loc_remaining(l["id"]))
            pygame.draw.polygon(s, (255, 210, 80) if left else (110, 110, 110), [(x, y - 6), (x + 6, y + 5), (x - 6, y + 5)])
            D.text(s, l["name"], (x + 8, y - 6), 11, (235, 225, 190) if left else (130, 130, 130))
    bx, by = ox + BASE_POS[0] * sc, oy + BASE_POS[1] * sc
    pygame.draw.rect(s, (110, 220, 255), (bx - 5, by - 5, 10, 10)); D.text(s, "BASE", (bx + 8, by - 6), 11, (110, 220, 255), True)
    rx, ry = ox + g.rover.pos[0] * sc, oy + g.rover.pos[1] * sc
    pygame.draw.circle(s, (240, 230, 160), (rx, ry), 3)
    px, py = ox + (g.rover.pos[0] if g.player.in_rover else g.player.wpos[0]) * sc, oy + (g.rover.pos[1] if g.player.in_rover else g.player.wpos[1]) * sc
    if not g.player.inside:
        pygame.draw.circle(s, (255, 90, 90), (px, py), 5); pygame.draw.circle(s, (255, 255, 255), (px, py), 8, 1)
    x = r.right + 20
    D.text(s, "LEGEND / SITES", (x, 40), 15, (120, 190, 230), True)
    y = 66
    known = [l for l in g.world.locations if l["discovered"]]
    for l in sorted(known, key=lambda l: math.hypot(l["x"] - BASE_POS[0], l["y"] - BASE_POS[1])):
        d = math.hypot(l["x"] - BASE_POS[0], l["y"] - BASE_POS[1])
        D.text(s, f"{l['name']}", (x, y), 12, (235, 225, 190)); D.text(s, f"{fmt_dist(d)}  {len(g.world.loc_remaining(l['id']))} left", (x, y + 13), 11, (150, 165, 180)); y += 30
        if y > 560: break
    D.text(s, f"{len(known)} sites known. Explore to reveal more;", (x, 600), 11, (150, 165, 180))
    D.text(s, "Map Fragments reveal hidden sites.", (x, 614), 11, (150, 165, 180))
    D.text(s, "Rings: grey = safe range, red = recovery limit", (x, 634), 11, (150, 165, 180))
