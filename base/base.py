"""Base state: systems, power, oxygen, water, climate, comms job. All HUD numbers come from here."""
import math
from config import *
from data.systems import SYSTEMS, STAGES
from player.inventory import Inventory
from base import farming
from base.farming import Plot

def clamp(v, a, b): return max(a, min(b, v))

START_STORAGE = {"iron_scrap": 4, "aluminum": 2, "copper": 1, "electronics": 2, "polymer": 2, "glass": 1, "food_ration": 5, "water": 2,
                 "growing_medium": 5, "seeds_potato": 3, "seeds_bean": 2, "seeds_lettuce": 2, "battery": 1, "medical": 1,
                 "oxygen_tank": 1, "tools": 1}

class Base:
    def __init__(self):
        self.sys = {k: float(v["start"]) for k, v in SYSTEMS.items()}
        self.storage = Inventory(BASE_STORAGE_CAPACITY)
        self.storage.items = dict(START_STORAGE)
        self.battery = BATTERY_CAP * 0.7
        self.o2, self.tank, self.waste, self.indoor = 85.0, START_TANK, 0.0, 14.0
        self.panels = 4
        self.plots = [Plot(i < START_PLOTS) for i in range(MAX_PLOTS)]
        self.stage, self.job, self.comm_fault, self.processor = 0, None, False, False
        self.rescue_time = None
        self.flow, self.supply, self.leak, self.charge_load = 0.0, 1.0, 0.0, 0.0
        self.solar_now, self.demand = 0.0, 0.0
        self.loads = {}

    def f(self, k):
        v = self.sys[k]
        return 0.0 if v < 15 else v / 100.0

    def power_pct(self):
        return 100.0 * self.battery / BATTERY_CAP

    def condition(self):
        return sum(self.sys.values()) / len(self.sys)

    def comm_progress(self):
        return 100.0 * self.stage / len(STAGES)

    def update(self, dt, env, g):
        amb, day, storm = env["ambient"], env["daylight"], env["storm"]
        self.solar_now = PANEL_PEAK * self.panels * self.f("solar") * day * (1 - SOLAR_STORM_LOSS * storm)
        growing = sum(1 for p in self.plots if p.crop)
        he = self.f("heating")
        self.loads = {
            "Oxygen": LOAD_O2 if (self.f("oxygen_gen") > 0 and self.o2 < 99.5) else 0.08,
            "Water": LOAD_WATER if (self.waste > 0.01 and self.f("water_recycler") > 0) else 0.05,
            "Heating": (0.2 + 0.008 * max(0, TARGET_TEMP - amb)) * (0.4 + 0.6 * he) if he > 0 else 0.0,
            "Greenhouse": (LOAD_GREENHOUSE + LOAD_PLOT * growing) if self.f("greenhouse") > 0 else 0.0,
            "Comms": LOAD_COMMS if self.stage >= 2 else 0.0,
            "Lights": LOAD_LIGHTS, "Rover": self.charge_load}
        self.demand = sum(self.loads.values())
        if self.battery > 0.5 or self.demand <= 0:
            self.supply = 1.0
        else:
            self.supply = min(1.0, self.solar_now / self.demand)
        net = self.solar_now - self.demand * self.supply
        self.battery = clamp(self.battery + net * dt, 0, BATTERY_CAP)
        self.flow += ((self.solar_now - self.demand) - self.flow) * min(1.0, dt / 20.0)
        sup = self.supply
        # oxygen
        self.o2 = clamp(self.o2 + (BASE_O2_PROD * self.f("oxygen_gen") * sup - BASE_O2_USE
                                    - BASE_O2_LEAK * (1 - self.f("airlock")) - self.leak) * dt, 0, 100)
        # water recycling (lossy)
        eff = RECYCLE_BASE_EFF + RECYCLE_SCALE * self.f("water_recycler")
        proc = min(self.waste, WATER_RECYCLE_RATE * self.f("water_recycler") * sup * dt)
        self.waste -= proc
        self.tank = min(TANK_CAP, self.tank + proc * eff)
        # climate
        heat = min(1.0, he * sup * 1.4)
        target = amb + (TARGET_TEMP - amb) * heat
        self.indoor += (target - self.indoor) * min(1.0, dt / 40.0)
        for k in self.sys:
            self.sys[k] = max(0.0, self.sys[k] - SYSTEM_WEAR * dt)
        farming.update(self, dt, g)
        self._comms(dt, env, g)

    def job_ok(self, st, storm):
        if self.comm_fault: return False, "TRANSCEIVER FAULT"
        if self.power_pct() < st["power"]: return False, f"NEEDS {st['power']}% POWER"
        if st["sky"] and storm > 0.25: return False, "DUST STORM INTERFERENCE"
        return True, ""

    def _comms(self, dt, env, g):
        j = self.job
        if not j:
            return
        st = STAGES[j["stage"]]
        ok, why = self.job_ok(st, env["storm"])
        j["why"] = why
        if ok:
            j["left"] -= dt
        if j["left"] > 0:
            return
        self.stage = j["stage"] + 1
        self.job = None
        g.notify(f"COMMS: {st['done']}", "good")
        g.decide(f"Comms: {st['name']}")
        if self.stage == 6:
            self.job = dict(stage=6, left=STAGES[6]["time"], why="")
        elif self.stage >= 7:
            self.rescue_time = g.clock.t + RESCUE_SOLS * SOL_LENGTH
            g.notify(f"RESCUE MISSION CONFIRMED. Estimated arrival: {RESCUE_SOLS} Sols. SURVIVE.", "good")
            g.events.pressure = 1.3
            g.priority = dict(id="survive", label="Survive until rescue")

    def to_dict(self):
        return dict(sys=self.sys, storage=self.storage.to_dict(), battery=self.battery, o2=self.o2, tank=self.tank, waste=self.waste,
                    indoor=self.indoor, panels=self.panels, plots=[p.to_dict() for p in self.plots], stage=self.stage, job=self.job,
                    fault=self.comm_fault, processor=self.processor, rescue=self.rescue_time, flow=self.flow)

    def load(self, d):
        self.sys.update(d["sys"]); self.storage.load(d["storage"])
        self.battery, self.o2, self.tank, self.waste = d["battery"], d["o2"], d["tank"], d["waste"]
        self.indoor, self.panels, self.stage, self.job = d["indoor"], d["panels"], d["stage"], d["job"]
        self.plots = [Plot.from_dict(p) for p in d["plots"]]
        self.comm_fault, self.processor, self.rescue_time, self.flow = d["fault"], d["processor"], d["rescue"], d.get("flow", 0.0)
