"""In-game AI assistant: reads real game state, offers options + a plan. Never forces anything."""
import math
from config import *
from data.systems import SYSTEMS, STAGES, CROPS
from data.resources import RESOURCES
from resources import resource_manager as RM
from exploration.discoveries import compass, fmt_dist
from player import survival

W = {"oxygen_gen": 1.6, "solar": 1.3, "water_recycler": 1.2, "heating": 1.1, "airlock": 0.8, "greenhouse": 0.8}

def stock(g, rid): return sum(c.count(rid) for c in (g.player.inv, g.base.storage, g.rover.inv))

def food_days(g):
    pct = g.player.stats["hunger"] + FOOD_RATION_HUNGER * stock(g, "food_ration") + PRODUCE_HUNGER * stock(g, "fresh_produce")
    return pct / (HUNGER_RATE * SOL_LENGTH)

def water_days(g):
    b = g.base
    eff = (RECYCLE_BASE_EFF + RECYCLE_SCALE * b.f("water_recycler")) if b.f("water_recycler") > 0 else 0
    pct = g.player.stats["hydration"] + PCT_PER_LITER * (b.tank + WATER_CANISTER_L * stock(g, "water"))
    return pct / (WATER_RATE * SOL_LENGTH * (1 - 0.9 * eff))

def safe_minutes(g):
    return g.player.stats["oxygen"] / (OXYGEN_CONSUMPTION_RATE * (1 + 0.5 * g.player.weight_factor()) * 60)

def known_sources(g, key):
    """Nearest known nodes holding resource `key` (or group)."""
    mem = RM.members(key)
    px, py = g.player.wpos
    out = []
    for n in g.world.nodes.values():
        if g.world.known_node(n) and any(i[0] in mem for i in n["items"]):
            out.append((math.hypot(n["x"] - BASE_POS[0], n["y"] - BASE_POS[1]), n))
    return sorted(out, key=lambda t: t[0])

def where(g, n):
    dx, dy = n["x"] - BASE_POS[0], n["y"] - BASE_POS[1]
    return f"{n['label']}, {fmt_dist(math.hypot(dx, dy))} {compass(dx, dy)} of base"

class Assistant:
    def situation(self, g):
        b, s = g.base, g.player.stats
        fd, wd = food_days(g), water_days(g)
        flow = b.flow
        lines = [("Oxygen system", f"{b.sys['oxygen_gen']:.0f}%  (base air {b.o2:.0f}%)", b.sys["oxygen_gen"] < 35 or b.o2 < 30),
                 ("Food", f"{fd:.1f} sols", fd < 3), ("Water", f"{wd:.1f} sols  (tank {b.tank:.0f} L)", wd < 3),
                 ("Power", f"{b.power_pct():.0f}%  ({'+' if flow >= 0 else ''}{flow:.1f}/s)", b.power_pct() < 25 or (flow < -0.5 and b.power_pct() < 50)),
                 ("Communication", f"{b.comm_progress():.0f}%  (stage {min(b.stage + 1, 7)}/7)", False)]
        if b.rescue_time: lines.append(("Rescue ETA", f"{max(0, (b.rescue_time - g.clock.t) / SOL_LENGTH):.1f} sols", False))
        st = g.events.storm
        lines.append(("Weather", "DUST STORM" if st > 0.3 else "Stable" + (" (front inbound)" if any(e["phase"] == "warning" and "storm" in e["type"] for e in g.events.active) else ""), st > 0.3))
        return lines

    def options(self, g):
        b, p = g.base, g.player
        c = []
        if b.rescue_time: c.append((90, "survive", "Survive until rescue", "Earth is sending help. Avoid unnecessary risks, protect food, water, oxygen and power."))
        if not p.inside and p.dist > 300:
            need = (p.dist / PLAYER_SPEED) * survival.o2_rate(g, True)
            if p.stats["oxygen"] < need * 1.6 + 10:
                c.append((100, "return", "Return to base", "Your oxygen reserve is close to what the trip back will cost."))
        for sid, sy in SYSTEMS.items():
            v = b.sys[sid]
            if v < 70:
                c.append(((100 - v) * W[sid] + (40 if v < 15 else 0), "repair:" + sid, f"Repair {sy['name']}", f"{sy['name']} is at {v:.0f}%. {sy['effect']}"))
        fd, wd = food_days(g), water_days(g)
        empty = sum(1 for q in b.plots if q.unlocked and not q.crop)
        seeds = sum(stock(g, k) for k in CROPS)
        if fd < 6 or (empty and seeds): c.append((55 + max(0, 6 - fd) * 8, "farm", "Expand Food Production", f"Food reserve is about {fd:.1f} sols. Farming is the only sustainable source."))
        if wd < 5: c.append((50 + (5 - wd) * 10, "water", "Secure Water", f"Water reserve is about {wd:.1f} sols; recycling is never 100% efficient."))
        if b.power_pct() < 30: c.append((60, "power", "Restore Power", "Battery is low. Repair or extend the solar array, or cut consumers."))
        if b.stage < 7:
            c.append((35 + b.stage * 3 + (15 if min(b.sys.values()) > 30 else 0), "comms", "Restore Earth Communications", f"Next stage: {STAGES[b.stage]['name']}. This is the only path to rescue."))
        near = [l for l in g.world.locations if l["discovered"] and g.world.loc_remaining(l["id"])]
        near.sort(key=lambda l: math.hypot(l["x"] - BASE_POS[0], l["y"] - BASE_POS[1]))
        for l in near[:2]:
            d = math.hypot(l["x"] - BASE_POS[0], l["y"] - BASE_POS[1])
            c.append((30 - d / 400, "explore:" + l["id"], f"Explore {l['name']}", f"{fmt_dist(d)} away, {len(g.world.loc_remaining(l['id']))} containers left."))
        if not near: c.append((25, "scout", "Scout for new sites", "No known sites with supplies. Explore outward in daylight."))
        c.sort(key=lambda t: -t[0])
        out, seen = [], set()
        for sc, pid, lab, why in c:
            if pid not in seen:
                seen.add(pid); out.append(dict(id=pid, label=lab, why=why))
            if len(out) == 4: break
        return out

    def _need_steps(self, g, reqs, steps):
        c = [g.player.inv, g.base.storage]
        for k, have, need in RM.status(c, reqs):
            if have >= need: continue
            src = known_sources(g, k)
            steps.append(f"Collect {need - have} more {RM.key_name(k)}" + (f" - nearest known: {where(g, src[0][1])}." if src else " - no known source yet; explore."))

    def plan(self, g, pid):
        b = g.base
        steps, note = [], ""
        if pid.startswith("repair:"):
            sid = pid.split(":")[1]; sy = SYSTEMS[sid]
            self._need_steps(g, sy["repair"], steps)
            steps.append("Return to base and stand at the " + sy["name"] + "; press J to repair.")
            note = f"Repairs consume {', '.join(f'{n} {RM.key_name(k)}' for k, n in sy['repair'].items())}. Those parts cannot be used elsewhere."
        elif pid == "farm":
            steps = [f"Water tank: {b.tank:.0f} L. Each crop costs 3-6 L.", "Select seeds (Q/R) and press J at an empty plot in the Greenhouse.",
                     "Crops need power, a warm greenhouse and one Growing Medium each.", "Harvest returns produce, sometimes seeds and medium."]
            note = f"Your water supports roughly {int(b.tank // 5)} more crop cycles, but drinking also needs it."
        elif pid == "water":
            steps = ["Repair the Water Recycler to recover more water.", "Search for Water Canisters (5 L each) at caches and outposts.", "Plant lettuce rather than potatoes: it uses half the water."]
            note = "Canisters poured at the tank (K) add water; recycled water is always partly lost."
        elif pid == "power":
            steps = ["Repair the Solar Array or install another panel (2 Solar Components + 1 Metal).", "Use a Battery item (K) inside the base for +20%.", "Avoid charging the rover until power recovers."]
        elif pid == "comms":
            st = STAGES[min(b.stage, 6)]
            if b.stage >= 7: steps = ["Communications are complete. Survive."]
            else:
                if st["reqs"]: self._need_steps(g, st["reqs"], steps)
                steps.append(f"At the Communications Console press J to {st['name'].lower()}.")
                if st["sky"]: steps.append("This stage needs a clear sky: a dust storm pauses it.")
                if st["power"]: steps.append(f"Keep base power above {st['power']}%.")
            note = "Comms parts compete with oxygen, rover and farm repairs for the same metal and electronics."
        elif pid.startswith("explore:"):
            l = g.world.loc_by_id(pid.split(":")[1])
            if l:
                dx, dy = l["x"] - BASE_POS[0], l["y"] - BASE_POS[1]; d = math.hypot(dx, dy)
                steps = [f"{l['name']}: {fmt_dist(d)} {compass(dx, dy)} of base.", f"Walking round trip costs about {d * 2 / PLAYER_SPEED * survival.o2_rate(g, True) * 0.9:.0f}% oxygen.",
                         "Charge the rover and take it if the site is far (cargo is separate from your 25 kg)." if d > 2000 else "Close enough to walk.",
                         "Carry a spare Oxygen Tank if the site lies beyond safe range." if d > SAFE_RANGE * 0.8 else "Return before oxygen drops under 35%."]
                if g.events.storm > 0.2 or any("storm" in e["type"] for e in g.events.active): steps.append("A dust storm is active or inbound. Risky.")
                note = f"Exploration is viable, but your oxygen currently allows about {safe_minutes(g):.0f} minutes of safe external activity."
        elif pid == "return":
            steps = [f"Head back to base: {fmt_dist(g.player.dist)} away.", "Drop heavy items, sprint only if oxygen allows."]
        elif pid == "survive":
            steps = ["Keep oxygen generator, power and water running.", "Eat and drink on schedule.", "Avoid expeditions unless a system needs parts."]
        else:
            steps = ["Explore outward in daylight; glowing outlines are collectible.", "Press M to see explored ground."]
        return note, steps

    def react(self, g, pid):
        if pid.startswith("explore") or pid == "scout":
            return f"Exploration is viable, but your oxygen reserve allows about {safe_minutes(g):.0f} minutes of safe external activity."
        if pid == "farm": return f"Your water reserve supports approximately {int(g.base.tank // 5)} additional crop cycles."
        return ""
