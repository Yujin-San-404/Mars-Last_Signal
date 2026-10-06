"""Random Mars event definitions. kind: hazard | boon. 'warn'/'dur' define warning + active phases."""
import random
from config import *
from exploration.discoveries import compass, fmt_dist

def _dir(d, b):
    import math
    r = math.radians(b)
    return f"{fmt_dist(d)} {compass(math.sin(r), -math.cos(r))}"

def _sysdmg(g, amt, only=None):
    from data.systems import SYSTEMS
    sid = only or random.choice(list(SYSTEMS))
    g.base.sys[sid] = max(0.0, g.base.sys[sid] - amt)
    return SYSTEMS[sid]["name"]

def e_solar(g, em):
    g.base.sys["solar"] = max(0.0, g.base.sys["solar"] - random.uniform(20, 35))
    g.notify("SOLAR PANEL FAILURE: array integrity dropped.", "bad")

def e_water(g, em):
    g.base.sys["water_recycler"] = max(0.0, g.base.sys["water_recycler"] - 30); g.base.tank = max(0.0, g.base.tank - 5)
    g.notify("WATER SYSTEM FAILURE: recycler seal blown, 5 L lost.", "bad")

def e_surge(g, em):
    g.base.battery = max(0.0, g.base.battery - BATTERY_CAP * 0.15)
    n = _sysdmg(g, 10)
    g.notify(f"POWER SURGE: battery bank -15%, {n} damaged.", "bad")

def e_comm(g, em):
    g.base.comm_fault = True
    g.notify("COMMUNICATION FAILURE: transceiver fault. Fix at the comms console.", "bad")

def e_crop(g, em):
    gr = [p for p in g.base.plots if p.crop and p.prog < 1]
    random.choice(gr).blight += 70
    g.notify("CROP PROBLEM: blight detected in the greenhouse. Keep it warm and powered.", "warn")

def e_rover(g, em):
    g.rover.integ = max(5.0, g.rover.integ - 25)
    g.notify("ROVER BREAKDOWN: drivetrain damaged. Repair it (J at the rover).", "bad")

def e_malf(g, em):
    g.notify(f"EQUIPMENT MALFUNCTION: {_sysdmg(g, 15)} integrity -15.", "bad")

def e_meteor(g, em):
    b = random.uniform(0, 360); d = random.uniform(1500, 3200)
    g.world.spawn_site("Meteorite Fragments", "crater", b, d, [[("iron_scrap", random.randint(2, 4))], [random.choice([("aluminum", 2), ("copper", 1), ("rare_science", 1)])]], "Fresh impact debris.")
    msg = f"METEORITE IMPACT {_dir(d, b)} of base: fragments detected."
    if random.random() < 0.35: msg += f" Shockwave: {_sysdmg(g, 15)} -15."
    g.notify(msg, "warn")

def _site(name, kind, lo, hi, tables, desc, g, msg):
    b = random.uniform(0, 360); d = random.uniform(lo, hi)
    g.world.spawn_site(name, kind, b, d, random.choice(tables), desc)
    g.notify(msg.format(where=_dir(d, b)), "good")

def e_cache(g, em):
    _site("Supply Container", "cache", 450, 900, [[[("food_ration", 2), ("water", 1)], [("battery", 1)]], [[("water", 2)], [("medical", 1), ("polymer", 2)]]],
          "Container from the failed shipment.", g, "SUPPLY CONTAINER from the failed shipment located {where} of base.")

def e_unexpected(g, em):
    _site("Surface Anomaly", "event", 1200, 3000, [[[("copper", 2), ("electronics", 1)]], [[("mechanical_parts", 2), ("solar_component", 1)]], [[("battery", 1), ("glass", 2)]]],
          "Unusual metallic return.", g, "Surface scan: metallic anomaly {where} of base.")

def e_abandoned(g, em):
    _site("Abandoned Equipment", "event", 1500, 3600, [[[("tools", 1)], [("electronics", 2)]], [[("battery", 2)], [("mechanical_parts", 1), ("aluminum", 2)]]],
          "Equipment left by an earlier crew.", g, "Abandoned equipment spotted {where} of base.")

def e_damaged(g, em):
    _site("Damaged Structure", "event", 2200, 4200, [[[("iron_scrap", 3), ("aluminum", 2)], [("electronics", 2), ("circuit_board", 1)], [("polymer", 2), ("glass", 1)]]],
          "Collapsed shelter, partly salvageable.", g, "Damaged structure discovered {where} of base.")

def e_signal(g, em):
    _site("Emergency Beacon", "event", 1800, 3600, [[[("comm_component", 1), ("battery", 1)], [("food_ration", 2), ("oxygen_tank", 1)]], [[("water", 2), ("medical", 1)], [("circuit_board", 1), ("map_fragment", 1)]]],
          "An old emergency beacon still pinging.", g, "An old emergency beacon has been detected {where} of base.")

def storm_start(sev, warn, dur, name):
    def f(g, em):
        if any(e["type"] in ("dust_storm", "severe_storm") for e in em.active): return
        em.start(name, warn, dur, sev=sev)
        g.notify(("SEVERE " if sev >= 1 else "") + f"DUST STORM FRONT detected. Arrival in {warn:.0f}s - solar output, visibility and oxygen use will suffer. Consider returning to base.", "warn")
    return f

def hz(name, warn, dur, msg, **kw):
    def f(g, em):
        if any(e["type"] == name for e in em.active): return
        em.start(name, warn, dur, **kw); g.notify(msg, "warn")
    return f

def oxygen_leak(g, em):
    if any(e["type"] == "oxygen_leak" for e in em.active): return
    em.start("oxygen_leak", 0, 90, rate=0.30)
    g.notify("OXYGEN LEAK: pressure dropping. Patch at the Oxygen Generator (E, 1 Polymer) or wait it out.", "bad")

# id, name, kind, weight, min_sol, condition, fn
EVENTS = [
 ("dust_storm", "Dust Storm", "hazard", 10, 2.0, None, storm_start(0.65, 45, 90, "dust_storm")),
 ("severe_storm", "Severe Dust Storm", "hazard", 4, 8.0, None, storm_start(1.0, 80, 150, "severe_storm")),
 ("cold_snap", "Temperature Drop", "hazard", 5, 2.0, None, hz("cold_snap", 30, 90, "TEMPERATURE DROP forecast: severe cold front in 30s. Heating demand will spike.")),
 ("radiation", "Radiation Increase", "hazard", 5, 3.0, None, hz("radiation_storm", 25, 80, "SOLAR PARTICLE EVENT forecast in 25s. Radiation exposure outside will triple. Stay inside.")),
 ("solar_fail", "Solar Panel Failure", "hazard", 5, 3.0, None, e_solar),
 ("oxygen_leak", "Oxygen Leak", "hazard", 5, 3.0, None, oxygen_leak),
 ("water_fail", "Water System Failure", "hazard", 4, 4.0, None, e_water),
 ("surge", "Power Surge", "hazard", 4, 4.0, None, e_surge),
 ("comm_fail", "Communication Failure", "hazard", 3, 5.0, lambda g: g.base.stage >= 3 and not g.base.comm_fault and g.base.stage < 7, e_comm),
 ("crop", "Crop Problem", "hazard", 4, 3.0, lambda g: any(p.crop and p.prog < 1 for p in g.base.plots), e_crop),
 ("rover", "Rover Breakdown", "hazard", 4, 4.0, None, e_rover),
 ("meteor", "Meteorite Impact", "hazard", 4, 3.0, None, e_meteor),
 ("malf", "Equipment Malfunction", "hazard", 5, 3.0, None, e_malf),
 ("cache", "Resource Cache", "boon", 6, 0.0, None, e_cache),
 ("unexpected", "Unexpected Resource Discovery", "boon", 6, 0.0, None, e_unexpected),
 ("abandoned", "Abandoned Equipment Discovery", "boon", 5, 0.5, None, e_abandoned),
 ("damaged", "Damaged Structure Discovery", "boon", 4, 1.5, None, e_damaged),
 ("signal", "Emergency Signal", "boon", 5, 1.0, None, e_signal),
]
