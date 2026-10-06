"""Reusable weight-based inventory (player, rover, base storage)."""
from data.resources import RESOURCES

class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = {}

    def weight(self):
        return sum(RESOURCES[r]["weight"] * q for r, q in self.items.items())

    def free(self):
        return max(0.0, self.capacity - self.weight())

    def count(self, rid):
        return self.items.get(rid, 0)

    def max_addable(self, rid):
        w = RESOURCES[rid]["weight"]
        return 10 ** 6 if w <= 0 else int((self.free() + 1e-6) // w)

    def add(self, rid, qty):
        n = min(qty, self.max_addable(rid))
        if n > 0:
            self.items[rid] = self.count(rid) + n
        return max(0, n)

    def remove(self, rid, qty):
        n = min(qty, self.count(rid))
        if n > 0:
            self.items[rid] -= n
            if self.items[rid] <= 0:
                del self.items[rid]
        return n

    def order(self):
        return sorted(self.items, key=lambda r: (RESOURCES[r]["category"], RESOURCES[r]["name"]))

    def to_dict(self):
        return dict(self.items)

    def load(self, d):
        self.items = {k: int(v) for k, v in d.items() if k in RESOURCES}
