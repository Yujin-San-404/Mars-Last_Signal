"""Survival model. Every number on the HUD is produced here."""
import math
from config import *

def range_info(g):
    p = g.player
    d = math.hypot(p.wpos[0] - BASE_POS[0], p.wpos[1] - BASE_POS[1])
    ex = max(0.0, d - SAFE_RANGE)
    mult = 1 + 3 * ex / 1500 + 10 * max(0.0, d - MAX_RANGE) / 500
    return d, ex, mult

def o2_rate(g, moving=True, sprint=False):
    """Suit oxygen % per second outside, with every modifier applied."""
    p = g.player
    d, ex, rm = range_info(g)
    act = OXY_SPRINT if sprint else (OXY_WALK if moving else OXY_REST)
    r = OXYGEN_CONSUMPTION_RATE * act * (1 + 0.5 * p.weight_factor()) * rm * (1 + 0.25 * g.env["storm"])
    return r * (ROVER_O2_FACTOR if p.in_rover else 1.0)

def update(g, dt):
    p, s, b, env = g.player, g.player.stats, g.base, g.env
    d, ex, rm = range_info(g)
    p.dist = d
    for k in list(p.dmg):
        p.dmg[k] *= max(0.0, 1 - 0.1 * dt)
    thirst = WATER_RATE * dt
    if p.inside:
        if s["oxygen"] < 100 and b.o2 > 1:
            amt = min(100 - s["oxygen"], SUIT_REFILL_RATE * dt)
            cost = amt * BASE_O2_PER_SUIT_PCT
            if b.o2 >= cost:
                s["oxygen"] += amt; b.o2 -= cost
        if b.o2 <= 1:
            s["oxygen"] -= 0.6 * dt
            g.warn("baseair", "BASE AIR FAILURE: suit reserve is draining!", 15, "bad")
        if b.indoor > 8: s["warmth"] += 2.0 * dt
        else: s["warmth"] -= (8 - b.indoor) * 0.004 * dt * 10
        s["radiation"] = max(0.0, s["radiation"] - RADIATION_RECOVER * dt) + RADIATION_INSIDE * env["rad_mult"] * dt
        s["stamina"] += STAMINA_REGEN * 2.0 * dt
        rover_cold = 1.0
    else:
        s["oxygen"] -= o2_rate(g, p.moving, p.sprinting) * dt
        hz = g.world.hazards_at(*p.wpos)
        amb = env["ambient"] - (25 if "cold" in hz else 0) - ex / 1500 * 10
        cold = max(0.0, -amb - COLD_FREE) * COLD_RATE * (ROVER_COLD_FACTOR if p.in_rover else 1.0)
        s["warmth"] -= cold * dt
        rad = RADIATION_RATE * env["rad_mult"] * (4 if "radiation" in hz else 1) * (1 + ex / 1500) * (ROVER_RAD_FACTOR if p.in_rover else 1.0)
        s["radiation"] += rad * dt
        thirst *= OUTSIDE_THIRST_MULT
        if "radiation" in hz: g.warn("hz_rad", "RADIATION HOT ZONE: exposure rising fast.", 12, "warn")
        if "cold" in hz: g.warn("hz_cold", "COLD SINK: temperature dropping fast.", 12, "warn")
        regen = STAMINA_REGEN * (0.5 if p.weight_factor() > 0.8 else 1.0)
        s["stamina"] += (regen * (0.4 if p.moving else 1.4)) * dt
        # range warnings
        if d > MAX_RANGE: g.warn("range3", "BEYOND RECOVERY RANGE - TURN BACK NOW!", 6, "bad")
        elif d > SAFE_RANGE: g.warn("range1", "WARNING: SAFE RETURN RANGE EXCEEDED.", 20, "bad")
        need = (d / (ROVER_SPEED if p.in_rover else PLAYER_SPEED)) * o2_rate(g, True, False)
        if s["oxygen"] < need + 8 and d > 400:
            g.warn("o2return", "OXYGEN RESERVE CRITICAL. Return to base!", 12, "bad")
    if p.sprinting:
        s["stamina"] -= STAMINA_SPRINT_DRAIN * dt
    s["hunger"] -= HUNGER_RATE * dt
    s["hydration"] -= thirst
    for k in s:
        s[k] = max(0.0, min(100.0, s[k]))
    if s["hunger"] <= 0: p.hurt("STARVATION", STARVE_DMG * dt)
    if s["hydration"] <= 0: p.hurt("DEHYDRATION", DEHYDRATE_DMG * dt)
    if s["oxygen"] <= 0:
        src = "BASE FAILURE (atmosphere lost)" if p.inside else ("ENVIRONMENTAL FAILURE (beyond recovery range)" if d > MAX_RANGE else "OXYGEN DEPLETION")
        p.hurt(src, SUFFOCATE_DMG * dt)
    if s["warmth"] <= 0: p.hurt("EXTREME TEMPERATURE", COLD_DMG * 2 * dt)
    elif s["warmth"] < 15: p.hurt("EXTREME TEMPERATURE", COLD_DMG * 0.5 * dt)
    if s["radiation"] >= 100: p.hurt("RADIATION SICKNESS", 2 * dt)
    elif s["radiation"] > 75: p.hurt("RADIATION SICKNESS", RADIATION_DMG * dt)
    if min(s["hunger"], s["hydration"], s["oxygen"], s["warmth"]) > 35 and s["radiation"] < 60:
        s["health"] = min(100.0, s["health"] + HEALTH_REGEN * dt)
    for k, thr, txt in (("oxygen", 25, "OXYGEN LOW"), ("hunger", 20, "Hunger critical - eat (K)"), ("hydration", 20, "Dehydration - drink"),
                        ("warmth", 25, "Body temperature falling - get warm"), ("health", 35, "HEALTH CRITICAL")):
        if s[k] < thr: g.warn("low_" + k, txt, 25, "bad")
    if s["radiation"] > 60: g.warn("high_rad", "High radiation exposure. Stay inside / use medical supplies.", 30, "warn")
    if s["health"] <= 0:
        g.die(p.worst_cause())

def temp_label(w):
    return ("SAFE", (120, 220, 140)) if w > 60 else ("COOL", (200, 220, 120)) if w > 35 else ("COLD", (255, 180, 80)) if w > 15 else ("FREEZING", (255, 80, 80))
