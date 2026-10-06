from config import *
from player.inventory import Inventory
from base.layout import SPAWN

class Player:
    def __init__(self):
        self.wpos = [BASE_POS[0], BASE_POS[1] + 160.0]
        self.ipos = [float(SPAWN[0]), float(SPAWN[1])]
        self.inside, self.in_rover = True, False
        self.inv = Inventory(PLAYER_INVENTORY_CAPACITY)
        self.inv.items = {"food_ration": 1, "water": 1}
        self.sel = 0
        self.stats = dict(health=100.0, oxygen=100.0, hunger=85.0, hydration=85.0, warmth=100.0, radiation=0.0, stamina=100.0)
        self.dmg = {}
        self.moving = self.sprinting = False
        self.facing = [0.0, 1.0]
        self.dist = 0.0

    @property
    def pos(self):
        return self.ipos if self.inside else self.wpos

    def selected_id(self):
        order = self.inv.order()
        if not order: return None
        self.sel = max(0, min(self.sel, len(order) - 1))
        return order[self.sel]

    def cycle(self, d):
        n = len(self.inv.order())
        if n: self.sel = (self.sel + d) % n

    def hurt(self, src, amt):
        self.stats["health"] -= amt
        self.dmg[src] = self.dmg.get(src, 0) + amt

    def worst_cause(self):
        return max(self.dmg, key=self.dmg.get) if self.dmg else "UNKNOWN"

    def weight_factor(self):
        return self.inv.weight() / self.inv.capacity

    def to_dict(self):
        return dict(wpos=self.wpos, ipos=self.ipos, inside=self.inside, in_rover=self.in_rover, inv=self.inv.to_dict(), sel=self.sel, stats=self.stats, dmg=self.dmg)

    def load(self, d):
        self.wpos, self.ipos, self.inside, self.in_rover = d["wpos"], d["ipos"], d["inside"], d["in_rover"]
        self.inv.load(d["inv"]); self.sel = d["sel"]; self.stats.update(d["stats"]); self.dmg = d.get("dmg", {})
