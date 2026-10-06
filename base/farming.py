"""Greenhouse plots: planting consumes seed + medium + water; growth depends on power/climate."""
from config import SOL_LENGTH
from data.systems import CROPS

class Plot:
    def __init__(self, unlocked=False):
        self.unlocked, self.crop, self.prog, self.blight = unlocked, None, 0.0, 0.0

    def to_dict(self):
        return dict(u=self.unlocked, c=self.crop, p=self.prog, b=self.blight)

    @staticmethod
    def from_dict(d):
        p = Plot(d["u"]); p.crop, p.prog, p.blight = d["c"], d["p"], d["b"]
        return p

def growth_factor(base):
    tf = max(0.0, min(1.0, (base.indoor - 4) / 10.0))
    return base.f("greenhouse") * base.supply * tf

def update(base, dt, g):
    gf = growth_factor(base)
    for i, p in enumerate(base.plots):
        if not p.crop or p.prog >= 1:
            continue
        p.prog = min(1.0, p.prog + dt * gf / (CROPS[p.crop]["sols"] * SOL_LENGTH))
        if gf < 0.3:
            p.blight += dt * 0.6
        elif gf > 0.6 and p.blight > 0:
            p.blight = max(0.0, p.blight - 0.25 * dt)
        if p.blight >= 100:
            g.notify(f"CROP LOST: {CROPS[p.crop]['name']} on plot {i + 1} died (greenhouse unpowered or too cold).", "bad")
            p.crop, p.prog, p.blight = None, 0.0, 0.0
