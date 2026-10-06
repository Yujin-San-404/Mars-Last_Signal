"""Loot tables for scattered salvage, plus small navigation helpers."""
import math, random
from data.resources import RESOURCES

# (resource, weight, (min_qty, max_qty))
ZONES = {
 "near": [("iron_scrap",30,(1,2)),("aluminum",20,(1,2)),("polymer",16,(1,2)),("regolith",18,(1,3)),("glass",4,(1,1)),
          ("copper",3,(1,1)),("food_ration",3,(1,1)),("water",3,(1,1)),("electronics",3,(1,1))],
 "mid":  [("iron_scrap",14,(1,3)),("aluminum",12,(1,2)),("copper",11,(1,2)),("electronics",11,(1,2)),("mechanical_parts",10,(1,2)),
          ("polymer",8,(1,2)),("glass",7,(1,2)),("battery",6,(1,1)),("solar_component",5,(1,1)),("water",6,(1,1)),
          ("food_ration",6,(1,2)),("oxygen_tank",5,(1,1)),("medical",4,(1,1)),("tools",3,(1,1)),("regolith",6,(1,3)),
          ("growing_medium",3,(1,1)),("seeds_lettuce",1,(1,1)),("seeds_potato",1,(1,1))],
 "far":  [("circuit_board",9,(1,1)),("copper",10,(1,2)),("electronics",9,(1,2)),("tools",6,(1,1)),("battery",7,(1,1)),
          ("medical",4,(1,1)),("oxygen_tank",5,(1,1)),("mechanical_parts",8,(1,2)),("solar_component",5,(1,1)),
          ("food_ration",5,(1,2)),("water",5,(1,2)),("rare_science",2,(1,1)),("comm_component",2,(1,1)),
          ("map_fragment",3,(1,1)),("growing_medium",3,(1,2)),("seeds_bean",2,(1,1))],
}
BURIED = [("tools",1,(1,1)),("electronics",3,(1,2)),("mechanical_parts",2,(1,2)),("battery",2,(1,1)),("circuit_board",2,(1,1)),("copper",2,(1,2))]

def pick(rng, table):
    tot = sum(w for _, w, _ in table)
    x = rng.uniform(0, tot)
    for rid, w, q in table:
        x -= w
        if x <= 0:
            return rid, rng.randint(*q)
    return table[0][0], 1

def bearing_pos(base, bearing, dist):
    b = math.radians(bearing)
    return base[0] + dist * math.sin(b), base[1] - dist * math.cos(b)

def compass(dx, dy):
    ang = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
    return ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"][int((ang + 22.5) // 45) % 8]

def fmt_dist(px):
    from config import PX_TO_M
    m = px * PX_TO_M
    return f"{m:.0f} m" if m < 1000 else f"{m/1000:.1f} km"

def rarity_of(items):
    from data.resources import RARITY_ORDER
    best = 0
    for rid, _ in items:
        best = max(best, RARITY_ORDER.index(RESOURCES[rid]["rarity"]))
    return RARITY_ORDER[best]
