"""Schedules random events, tracks active ones and exposes their environmental modifiers."""
import random
from config import *
from events.events import EVENTS

class EventManager:
    def __init__(self, g):
        self.g, self.active, self.next_in = g, [], 75.0
        self.storm, self.cold_delta, self.rad_mult, self.pressure = 0.0, 0.0, 1.0, 1.0
        self.first, self.last = True, ""

    def start(self, typ, warn, dur, **kw):
        self.active.append(dict(type=typ, phase="warning" if warn > 0 else "active", t=warn if warn > 0 else dur, dur=dur, **kw))

    def end(self, typ):
        self.active = [e for e in self.active if e["type"] != typ]

    def update(self, dt):
        g = self.g
        target, cold, rad, leak = 0.0, 0.0, 1.0, 0.0
        for e in list(self.active):
            e["t"] -= dt
            if e["phase"] == "warning":
                if e["type"] in ("dust_storm", "severe_storm"): target = max(target, 0.15)
                if e["t"] <= 0:
                    e["phase"], e["t"] = "active", e["dur"]
                    g.notify({"dust_storm": "DUST STORM: visibility and solar output dropping.", "severe_storm": "SEVERE DUST STORM: take shelter!",
                              "cold_snap": "COLD SNAP: temperatures plunging.", "radiation_storm": "SOLAR PARTICLE EVENT: radiation spiking."}.get(e["type"], "Event active."), "bad")
                continue
            if e["type"] in ("dust_storm", "severe_storm"): target = max(target, e["sev"])
            elif e["type"] == "cold_snap": cold = -22.0
            elif e["type"] == "radiation_storm": rad = 3.0
            elif e["type"] == "oxygen_leak": leak = max(leak, e["rate"])
            if e["t"] <= 0:
                self.active.remove(e)
                g.notify({"dust_storm": "Dust storm subsiding.", "severe_storm": "Severe storm passing.", "cold_snap": "Cold snap ending.",
                          "radiation_storm": "Radiation levels returning to normal.", "oxygen_leak": "Leak sealed itself."}.get(e["type"], "Event over."), "info")
        step = 0.05 * dt
        self.storm += max(-step, min(step, target - self.storm))
        self.cold_delta, self.rad_mult = cold, rad
        g.base.leak = leak
        self.next_in -= dt
        if self.next_in <= 0:
            self.fire()

    def fire(self):
        g = self.g
        sol = g.clock.t / SOL_LENGTH
        self.next_in = max(EVENT_MIN_INTERVAL, random.uniform(*EVENT_INTERVAL) / (1 + 0.03 * sol) / self.pressure)
        if self.first:
            self.first = False
            ev = next(e for e in EVENTS if e[0] == "cache")
        else:
            pool = [e for e in EVENTS if sol >= e[4] and (e[5] is None or e[5](g))]
            ev = random.choices(pool, weights=[e[3] for e in pool])[0]
        self.last = ev[1]
        g.log_event(f"EVENT: {ev[1]}")
        ev[6](g, self)

    def banners(self):
        out = []
        for e in self.active:
            nm = e["type"].replace("_", " ").upper()
            out.append((f"{nm} {'INBOUND' if e['phase'] == 'warning' else 'ACTIVE'} {max(0, e['t']):.0f}s", e["phase"] == "active"))
        return out

    def to_dict(self):
        return dict(active=self.active, next_in=self.next_in, storm=self.storm, pressure=self.pressure, first=self.first)

    def load(self, d):
        self.active, self.next_in, self.storm, self.pressure, self.first = d["active"], d["next_in"], d["storm"], d["pressure"], d["first"]
