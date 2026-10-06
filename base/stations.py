"""Reusable interaction logic for base consoles, plots, tank, processor, comms."""
import math, random
from config import *
from base import layout
from data.systems import *
from data.resources import RESOURCES
from resources import resource_manager as RM

def conts(g): return [g.player.inv, g.base.storage]

def nearby(g):
    x, y = g.player.ipos
    best, bd = None, 1e9
    for st in layout.INTERACTABLES:
        if st["kind"] == "plot" and not (st["idx"] < len(g.base.plots)): continue
        d = math.hypot(x - st["x"], y - st["y"])
        if d < st["r"] and d < bd:
            best, bd = st, d
    return best

def reqs_for(g, st):
    """Return (title, [(key, have, need)]) shown as a floating marker, or None."""
    b, c, k = g.base, conts(g), st["kind"]
    if k == "sys":
        if b.sys[st["sys"]] < 99:
            return "REPAIR " + SYSTEMS[st["sys"]]["name"].upper(), RM.status(c, SYSTEMS[st["sys"]]["repair"])
        if st["sys"] == "solar" and b.panels < MAX_PANELS:
            return "[E] INSTALL PANEL", RM.status(c, PANEL_INSTALL)
    elif k == "comms":
        if b.comm_fault: return "FIX TRANSCEIVER FAULT", RM.status(c, COMM_FAULT_FIX)
        if b.stage < 7 and not b.job:
            s = STAGES[b.stage]
            return f"STAGE {b.stage + 1}/7: {s['name'].upper()}", RM.status(c, s["reqs"]) if s["reqs"] else []
    elif k == "plot" and not b.plots[st["idx"]].unlocked:
        return "UNLOCK PLOT", RM.status(c, PLOT_UNLOCK)
    elif k == "processor":
        if not b.processor: return "BUILD REGOLITH PROCESSOR", RM.status(c, PROCESSOR_BUILD)
        return "PROCESS REGOLITH (+%d L water)" % PROCESS_WATER, RM.status(c, PROCESS_COST)
    return None

def prompts(g, st):
    b, k = g.base, st["kind"]
    out = []
    if k == "sys":
        out.append(("J", f"Repair {SYSTEMS[st['sys']]['name']} ({b.sys[st['sys']]:.0f}%)" if b.sys[st["sys"]] < 99 else
                    ("Install solar panel" if st["sys"] == "solar" and b.panels < MAX_PANELS else f"{SYSTEMS[st['sys']]['name']} OK")))
        if st["sys"] == "solar" and b.sys["solar"] < 99 and b.panels < MAX_PANELS: out.append(("E", "Install solar panel"))
        if st["sys"] == "oxygen_gen" and b.leak > 0: out.append(("E", "Patch oxygen leak (1 Polymer)"))
    elif k == "save": out.append(("J", "Save game"))
    elif k == "assistant": out.append(("J", "Toggle AI assistant"))
    elif k == "tank": out.append(("J", f"Drink ({b.tank:.0f} L in tank)"))
    elif k == "chest": out.append(("J", "Open storage"))
    elif k == "exit": out.append(("J", "Exit base")); 
    elif k == "comms": out.append(("J", "Communications console"))
    elif k == "processor": out.append(("J", "Process regolith" if b.processor else "Build processor"))
    elif k == "plot":
        p = b.plots[st["idx"]]
        out.append(("J", "Unlock plot" if not p.unlocked else "Plant (selected seed)" if not p.crop else "Harvest" if p.prog >= 1 else f"Check crop ({p.prog * 100:.0f}%)"))
    if k == "exit": out.append(("E", "Exit base"))
    return out

def give(g, rid, qty):
    n = g.player.inv.add(rid, qty)
    if n < qty:
        m = g.base.storage.add(rid, qty - n)
        if m: g.notify(f"Carry limit: {m} x {RESOURCES[rid]['name']} sent to base storage.", "info")
    return n

def repair_system(g, sid):
    b, s = g.base, SYSTEMS[sid]
    if b.sys[sid] >= 99:
        if sid == "solar": return install_panel(g)
        return g.notify(f"{s['name']} is at full integrity.", "info")
    c = conts(g)
    if not RM.affordable(c, s["repair"]):
        return g.notify(f"Cannot repair {s['name']}. Missing: {RM.missing_text(c, s['repair'])}", "warn")
    RM.pay(c, s["repair"])
    b.sys[sid] = 100.0
    g.stats["repairs"] += 1
    g.notify(f"{s['name']} repaired to 100%.", "good")
    g.decide(f"Repaired {s['name']}")

def install_panel(g):
    b, c = g.base, conts(g)
    if b.panels >= MAX_PANELS: return g.notify("Solar array is at maximum size.", "info")
    if not RM.affordable(c, PANEL_INSTALL): return g.notify(f"Cannot install panel. Missing: {RM.missing_text(c, PANEL_INSTALL)}", "warn")
    RM.pay(c, PANEL_INSTALL); b.panels += 1
    g.notify(f"Solar panel installed ({b.panels}/{MAX_PANELS}).", "good"); g.decide("Installed solar panel")

def drink_tank(g):
    b, s = g.base, g.player.stats
    if s["hydration"] >= 98: return g.notify("You are fully hydrated.", "info")
    amt = min(2.0, b.tank, (100 - s["hydration"]) / PCT_PER_LITER)
    if amt <= 0.05: return g.notify("WATER TANK EMPTY!", "bad")
    b.tank -= amt; b.waste += amt; s["hydration"] += amt * PCT_PER_LITER
    g.notify(f"Drank {amt:.1f} L. Tank: {b.tank:.0f} L", "info")

def plot_action(g, i):
    b, p = g.base, g.base.plots[i]
    c = conts(g)
    if not p.unlocked:
        if not RM.affordable(c, PLOT_UNLOCK): return g.notify(f"Cannot unlock plot. Missing: {RM.missing_text(c, PLOT_UNLOCK)}", "warn")
        RM.pay(c, PLOT_UNLOCK); p.unlocked = True
        g.notify(f"Plot {i + 1} unlocked.", "good"); g.decide("Expanded the farm"); return
    if p.crop is None:
        sid = g.player.selected_id()
        if sid not in CROPS: return g.notify("Select seeds with Q/R, then press J at an empty plot.", "warn")
        cr = CROPS[sid]
        if RM.available(c, "growing_medium") < 1: return g.notify("No Growing Medium. Process regolith at the workshop or find some.", "warn")
        if b.tank < cr["water"]: return g.notify(f"Not enough water: {cr['name']} needs {cr['water']} L (tank {b.tank:.0f} L).", "warn")
        g.player.inv.remove(sid, 1); RM.consume(c, "growing_medium", 1); b.tank -= cr["water"]
        p.crop, p.prog, p.blight = sid, 0.0, 0.0
        g.notify(f"Planted {cr['name']} (-{cr['water']} L water).", "good"); g.decide(f"Planted {cr['name']}")
    elif p.prog >= 1:
        cr, rng = CROPS[p.crop], random.Random()
        n = rng.randint(*cr["out"]); give(g, "fresh_produce", n)
        msg = f"Harvested {n} Fresh Produce"
        if rng.random() < cr["seed_back"]: give(g, p.crop, 1); msg += " + 1 seed"
        if rng.random() < 0.6: give(g, "growing_medium", 1); msg += " + medium recovered"
        g.notify(msg, "good"); g.stats["harvests"] += 1
        p.crop, p.prog, p.blight = None, 0.0, 0.0
    else:
        from base.farming import growth_factor
        gf = growth_factor(b)
        g.notify(f"{CROPS[p.crop]['name']}: {p.prog * 100:.0f}% grown, blight {p.blight:.0f}%. Growth rate x{gf:.2f}" + (" (greenhouse offline/cold!)" if gf < 0.3 else ""), "info")

def processor_action(g):
    b, c = g.base, conts(g)
    if not b.processor:
        if not RM.affordable(c, PROCESSOR_BUILD): return g.notify(f"Cannot build processor. Missing: {RM.missing_text(c, PROCESSOR_BUILD)}", "warn")
        RM.pay(c, PROCESSOR_BUILD); b.processor = True
        g.notify("Regolith Processor built: turns regolith + water into Growing Medium.", "good"); g.decide("Built Regolith Processor"); return
    if not RM.affordable(c, PROCESS_COST): return g.notify(f"Need {RM.missing_text(c, PROCESS_COST)}", "warn")
    if b.tank < PROCESS_WATER: return g.notify("Not enough water to wash regolith.", "warn")
    if b.battery < 30 or b.supply < 1: return g.notify("Not enough power.", "warn")
    RM.pay(c, PROCESS_COST); b.tank -= PROCESS_WATER; b.battery -= 25; give(g, "growing_medium", 1)
    g.notify("+1 Growing Medium (-3 regolith, -4 L water, -25 power)", "good")

def comms_action(g):
    b, c = g.base, conts(g)
    if b.comm_fault:
        if not RM.affordable(c, COMM_FAULT_FIX): return g.notify(f"Transceiver fault. Missing: {RM.missing_text(c, COMM_FAULT_FIX)}", "warn")
        RM.pay(c, COMM_FAULT_FIX); b.comm_fault = False; return g.notify("Transceiver fault cleared.", "good")
    if b.stage >= 7:
        left = max(0, (b.rescue_time - g.clock.t) / SOL_LENGTH)
        return g.notify(f"RESCUE MISSION CONFIRMED. Arrival in {left:.1f} Sols.", "good")
    if b.job:
        j = b.job
        return g.notify(f"{STAGES[j['stage']]['name']}: {max(0, j['left']):.0f}s left. {j.get('why', '')}", "info")
    st = STAGES[b.stage]
    if not RM.affordable(c, st["reqs"]): return g.notify(f"{st['name']}: missing {RM.missing_text(c, st['reqs'])}", "warn")
    if b.power_pct() < st["power"]: return g.notify(f"{st['name']} needs {st['power']}% base power (now {b.power_pct():.0f}%).", "warn")
    RM.pay(c, st["reqs"])
    if st["kind"] == "repair":
        b.stage += 1; g.notify(f"COMMS: {st['done']}", "good"); g.decide(f"Comms: {st['name']}")
    else:
        b.job = dict(stage=b.stage, left=float(st["time"]), why="")
        g.notify(f"{st['name']} started ({st['time']}s)." + (" Needs clear sky." if st["sky"] else ""), "info")

def interact(g, st):
    k = st["kind"]
    if k == "sys": repair_system(g, st["sys"])
    elif k == "save": g.save_game()
    elif k == "assistant": g.assist_open = not g.assist_open
    elif k == "tank": drink_tank(g)
    elif k == "chest": g.open_inventory()
    elif k == "plot": plot_action(g, st["idx"])
    elif k == "processor": processor_action(g)
    elif k == "comms": comms_action(g)
    elif k == "exit": g.exit_base()

def secondary(g, st):
    b = g.base
    if st["kind"] == "exit": return g.exit_base()
    if st["kind"] == "sys" and st["sys"] == "solar": return install_panel(g)
    if st["kind"] == "sys" and st["sys"] == "oxygen_gen" and b.leak > 0:
        c = conts(g)
        if not RM.affordable(c, LEAK_PATCH): return g.notify("Need 1 Polymer to patch the leak.", "warn")
        RM.pay(c, LEAK_PATCH); g.events.end("oxygen_leak"); g.notify("Leak patched.", "good")
