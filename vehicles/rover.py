import math
from config import *
from player.inventory import Inventory

class Rover:
    r = 22
    def __init__(self):
        self.pos = [BASE_POS[0] - 270.0, BASE_POS[1] + 175.0]
        self.angle, self.battery, self.integ = 0.0, 60.0, 55.0
        self.inv = Inventory(ROVER_INVENTORY_CAPACITY)
        self.driven = False
        self.v = [0.0, 0.0]
        self.moving = False

    def circle(self): return (self.pos[0], self.pos[1], self.r)

    def can_drive(self): return self.battery > 0 and self.integ >= 20

    def drive(self, g, dx, dy, dt):
        self.moving = False
        if not self.can_drive():
            g.warn("rover_dead", "ROVER: " + ("BATTERY DEPLETED" if self.battery <= 0 else "ENGINE FAILURE") + " - exit (E).", 10, "warn")
            dx = dy = 0
        n = math.hypot(dx, dy)
        sp = ROVER_SPEED * (0.6 + 0.4 * self.integ / 100) * (1 - 0.25 * g.env["storm"])
        if "dust_trap" in g.world.hazards_at(*self.pos): sp *= 0.55
        tx, ty = (dx / n * sp, dy / n * sp) if n else (0, 0)
        k = min(1.0, dt * 4)
        self.v[0] += (tx - self.v[0]) * k
        self.v[1] += (ty - self.v[1]) * k
        spd = math.hypot(*self.v)
        if spd > 5:
            self.moving = True
            self.angle = math.atan2(self.v[1], self.v[0])
            hit = g.world.move(self.pos, self.v[0] * dt, self.v[1] * dt, self.r)
            self.battery = max(0.0, self.battery - ROVER_BATTERY_DRAIN * (1 + 0.3 * self.inv.weight() / self.inv.capacity) * (1 + 0.3 * g.env["storm"]) * dt)
            if hit and spd > 150:
                self.integ = max(0.0, self.integ - 4 * dt)
                g.warn("rover_hit", "Rover hull strike!", 8, "warn")
        return spd

    def to_dict(self):
        return dict(pos=self.pos, angle=self.angle, battery=self.battery, integ=self.integ, inv=self.inv.to_dict(), driven=self.driven)

    def load(self, d):
        self.pos, self.angle, self.battery, self.integ, self.driven = d["pos"], d["angle"], d["battery"], d["integ"], d["driven"]
        self.inv.load(d["inv"])
