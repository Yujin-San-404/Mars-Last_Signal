import math, pygame
from config import *
from ui import draw as D
from data.resources import RESOURCES
from player import survival
from base import stations
from exploration.discoveries import fmt_dist

COL = {"info": (220, 230, 240), "good": (120, 235, 150), "warn": (255, 210, 90), "bad": (255, 100, 100)}

def draw(g, s):
    p, st, b, t = g.player, g.player.stats, g.base, g.real_t
    tl, tc = survival.temp_label(st["warmth"])
    r = pygame.Rect(10, 10, 262, 232); D.panel(s, r, 200)
    rows = [("HEALTH", "heart", st["health"], (230, 80, 90), False, None), ("OXYGEN", "lungs", st["oxygen"], (90, 190, 255), False, None),
            ("HUNGER", "food", st["hunger"], (235, 175, 75), False, None), ("WATER", "drop", st["hydration"], (80, 150, 255), False, None),
            ("TEMP", "therm", st["warmth"], tc, False, tl), ("RAD", "rad", st["radiation"], (190, 230, 70), True, None),
            ("STAMINA", "stam", st["stamina"], (120, 220, 140), False, None)]
    for i, (lab, ic, v, col, inv, txt) in enumerate(rows):
        y = r.y + 8 + i * 31
        bad = v >= 65 if inv else v <= 25
        c = (240, 70, 70) if bad else col
        D.icon(s, ic, r.x + 18, y + 12, c)
        D.text(s, lab, (r.x + 36, y), 12, (165, 185, 205))
        D.bar(s, pygame.Rect(r.x + 36, y + 14, 148, 9), v / 100, c, flash=(bad and v < 12 and not inv) or (inv and v > 85), t=t)
        D.text(s, txt or f"{v:.0f}%", (r.right - 10, y + 13), 14, c, True, "midright")
    r2 = pygame.Rect(10, 250, 262, 66); D.panel(s, r2, 200)
    w, cap = p.inv.weight(), p.inv.capacity
    D.text(s, f"INVENTORY {w:.1f} / {cap:.0f} KG", (r2.x + 8, r2.y + 5), 12, (165, 185, 205))
    D.bar(s, pygame.Rect(r2.x + 8, r2.y + 21, 246, 8), w / cap, (240, 90, 80) if w / cap > 0.85 else (200, 190, 140))
    sid = p.selected_id()
    D.text(s, ("> " + RESOURCES[sid]["name"] + f" x{p.inv.count(sid)}  [K] use") if sid else "No items", (r2.x + 8, r2.y + 36), 13, (235, 235, 200))
    D.text(s, "[Q/R] select item", (r2.x + 8, r2.y + 51), 10, (120, 140, 160))
    D.text(s, "PRIORITY: " + (g.priority["label"] if g.priority else "none (TAB: assistant)"), (12, 322), 13, (255, 220, 120), True)
    # right panel
    r3 = pygame.Rect(SCREEN_W - 252, 10, 242, 178); D.panel(s, r3, 200)
    D.text(s, f"SOL {g.clock.sol}", (r3.x + 10, r3.y + 6), 22, (255, 200, 120), True)
    D.text(s, g.clock.time_str(), (r3.right - 10, r3.y + 6), 22, (255, 200, 120), True, "topright")
    amb = g.env["ambient"]
    D.text(s, f"{amb:.0f} C   {'DAY' if g.env['daylight'] > 0.05 else 'NIGHT'}   SUN {g.env['daylight'] * 100:.0f}%", (r3.x + 10, r3.y + 36), 12, (180, 200, 220))
    pp = b.power_pct()
    D.icon(s, "bolt", r3.x + 18, r3.y + 66, (255, 220, 80))
    D.text(s, f"BASE POWER {pp:.0f}%  ({'+' if b.flow >= 0 else ''}{b.flow:.1f}/s)", (r3.x + 34, r3.y + 54), 12, (255, 225, 110))
    D.bar(s, pygame.Rect(r3.x + 34, r3.y + 70, 196, 8), pp / 100, (255, 210, 60) if pp > 25 else (240, 70, 70))
    D.text(s, f"BASE AIR {b.o2:.0f}%   WATER {b.tank:.0f} L", (r3.x + 10, r3.y + 86), 12, (170, 210, 240))
    D.text(s, f"COMMS {b.comm_progress():.0f}%", (r3.x + 10, r3.y + 102), 12, (170, 190, 255))
    D.bar(s, pygame.Rect(r3.x + 10, r3.y + 118, 222, 6), b.comm_progress() / 100, (120, 150, 255))
    if b.rescue_time: D.text(s, f"RESCUE IN {max(0, (b.rescue_time - g.clock.t) / SOL_LENGTH):.1f} SOLS", (r3.x + 10, r3.y + 130), 14, (120, 255, 160), True)
    if b.job: D.text(s, f"JOB: {b.job['left']:.0f}s {b.job.get('why', '')}", (r3.x + 10, r3.y + 148), 11, (255, 190, 100))
    D.text(s, "STORM" if g.env["storm"] > 0.3 else "", (r3.x + 10, r3.y + 160), 12, (255, 160, 90), True)
    y = 196
    for txt, act in g.events.banners():
        D.text(s, txt, (SCREEN_W - 12, y), 13, (255, 110, 90) if act else (255, 210, 90), True, "topright"); y += 17
    # range
    if not p.inside:
        d, ex, _ = survival.range_info(g)
        col = (255, 90, 90) if d > SAFE_RANGE else (170, 200, 220)
        D.text(s, f"RANGE {fmt_dist(d)} / SAFE {fmt_dist(SAFE_RANGE)}", (SCREEN_W // 2, SCREEN_H - 118), 13, col, True, "center")
        need = (d / (ROVER_SPEED if p.in_rover else PLAYER_SPEED)) * survival.o2_rate(g, True)
        D.text(s, f"RETURN COST ~{need:.0f}% O2   (have {st['oxygen']:.0f}%)", (SCREEN_W // 2, SCREEN_H - 102), 12, (255, 90, 90) if need > st["oxygen"] * 0.7 else (150, 180, 200), False, "center")
        if p.in_rover: D.text(s, f"ROVER BAT {g.rover.battery:.0f}%  HULL {g.rover.integ:.0f}%  CARGO {g.rover.inv.weight():.0f}/{g.rover.inv.capacity:.0f}kg", (SCREEN_W // 2, SCREEN_H - 134), 13, (230, 220, 170), True, "center")
    # prompts
    y = SCREEN_H - 84
    for key, txt in g.prompts()[:3]:
        D.text(s, f"[{key}] {txt}", (SCREEN_W // 2, y), 15, (255, 235, 150), True, "center"); y += 18
    D.text(s, "WASD move  SHIFT sprint  J interact  K use  E enter/drive  I inventory  M map  TAB assistant  ESC menu", (SCREEN_W // 2, SCREEN_H - 14), 11, (120, 140, 160), False, "center")
    # notes
    y = 12
    for txt, lvl, ttl in g.notes[-5:]:
        img = D.font(15, True).render(txt, True, COL[lvl])
        a = min(255, int(ttl * 255))
        img.set_alpha(a)
        s.blit(img, (SCREEN_W // 2 - img.get_width() // 2, y)); y += 20
    if g.hint and g.settings["hints"]:
        lines = D.wrap(g.hint, 14, 560)
        rc = pygame.Rect(SCREEN_W // 2 - 290, SCREEN_H - 200 - 18 * len(lines), 580, 18 * len(lines) + 14)
        D.panel(s, rc, 210, (120, 190, 230), None)
        for i, l in enumerate(lines): D.text(s, l, (rc.x + 10, rc.y + 7 + i * 18), 14, (210, 235, 255))
    if g.assist_open: assistant_panel(g, s)
    if g.debug_on: debug(g, s)

def assistant_panel(g, s):
    r = pygame.Rect(SCREEN_W - 430, 220, 420, 400); D.panel(s, r, 225, (110, 160, 255), "AI ASSISTANT  TAB close  1-4 pick  0 clear")
    y = r.y + 24
    for lab, val, bad in g.assistant.situation(g):
        D.text(s, f"{lab}:", (r.x + 10, y), 12, (150, 170, 190)); D.text(s, val, (r.x + 150, y), 12, (255, 120, 110) if bad else (200, 230, 210)); y += 15
    y += 6; D.text(s, "Recommended priorities (you decide):", (r.x + 10, y), 12, (120, 190, 230), True); y += 17
    for i, o in enumerate(g.assist_opts):
        sel = g.priority and g.priority["id"] == o["id"]
        D.text(s, f"[{i + 1}] {o['label']}", (r.x + 10, y), 13, (120, 255, 160) if sel else (235, 235, 235), True); y += 15
        for l in D.wrap(o["why"], 11, 395)[:2]: D.text(s, l, (r.x + 24, y), 11, (150, 165, 185)); y += 12
    if g.priority:
        note, steps = g.assistant.plan(g, g.priority["id"])
        y += 4; D.text(s, "Suggested plan (ignore it any time):", (r.x + 10, y), 12, (255, 220, 120), True); y += 16
        rc = g.assistant.react(g, g.priority["id"])
        for l in D.wrap(rc or note, 11, 395)[:3]:
            D.text(s, l, (r.x + 10, y), 11, (170, 210, 255)); y += 12
        for i, st in enumerate(steps[:6]):
            for j, l in enumerate(D.wrap(st, 11, 385)[:2]):
                D.text(s, (f"{i + 1}. " if j == 0 else "   ") + l, (r.x + 10, y), 11, (215, 220, 225)); y += 12

def debug(g, s):
    p, b = g.player, g.base
    lines = [f"DEBUG  pos {p.pos[0]:.0f},{p.pos[1]:.0f}  inside={p.inside}  sol {g.clock.sol} {g.clock.time_str()}  warp={g.warp}",
             "stats " + " ".join(f"{k[:3]}={v:.0f}" for k, v in p.stats.items()),
             f"power {b.battery:.0f}/{BATTERY_CAP:.0f} solar {b.solar_now:.1f} demand {b.demand:.1f} supply {b.supply:.2f} o2 {b.o2:.0f} tank {b.tank:.0f} waste {b.waste:.1f} indoor {b.indoor:.0f}C",
             "sys " + " ".join(f"{k[:5]}={v:.0f}" for k, v in b.sys.items()),
             f"rover {g.rover.pos[0]:.0f},{g.rover.pos[1]:.0f} bat {g.rover.battery:.0f} integ {g.rover.integ:.0f} cargo {g.rover.inv.items}",
             f"comms stage {b.stage} job {b.job} fault {b.comm_fault}  event: {g.events.last}  next {g.events.next_in:.0f}s  storm {g.events.storm:.2f}",
             f"carry {p.inv.items}", "F6 give items  F7 warp  F8 refill  F10 storm  F11 skip to next event"]
    D.panel(s, pygame.Rect(280, SCREEN_H - 150, 800, 112), 200, (255, 150, 60))
    for i, l in enumerate(lines): D.text(s, l[:120], (288, SCREEN_H - 146 + i * 13), 11, (255, 200, 140))
