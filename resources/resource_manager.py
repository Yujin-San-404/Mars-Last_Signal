"""Requirement helpers: counts across several inventories, group keys (e.g. METAL)."""
from data.resources import RESOURCES, GROUPS, GROUP_NAMES

def members(key):
    return GROUPS[key] if key in GROUPS else {key: 1}

def key_name(key):
    return GROUP_NAMES.get(key) or RESOURCES[key]["name"]

def available(conts, key):
    return sum(c.count(r) * u for c in conts for r, u in members(key).items())

def consume(conts, key, amount):
    need = amount
    for r, u in members(key).items():
        for c in conts:
            while need > 0 and c.count(r) > 0:
                c.remove(r, 1)
                need -= u
    return need <= 0

def status(conts, reqs):
    return [(k, available(conts, k), n) for k, n in reqs.items()]

def affordable(conts, reqs):
    return all(h >= n for _, h, n in status(conts, reqs))

def pay(conts, reqs):
    for k, n in reqs.items():
        consume(conts, k, n)

def missing_text(conts, reqs):
    return ", ".join(f"{key_name(k).upper()} {h}/{n}" for k, h, n in status(conts, reqs) if h < n)
