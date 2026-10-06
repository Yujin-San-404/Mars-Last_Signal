"""Centralised, data-driven resource definitions."""
def _r(name, weight, rarity, cat, color, desc, uses):
    return dict(name=name, weight=weight, rarity=rarity, category=cat, color=color, desc=desc, uses=uses)

RESOURCES = {
 "iron_scrap": _r("Iron Scrap", 2.0, "common", "metal", (150, 118, 105), "Corroded structural iron.",
                  ["METAL: oxygen, water, solar, heating, airlock, rover, antenna repairs", "Greenhouse plot expansion"]),
 "aluminum": _r("Aluminum", 1.2, "common", "metal", (185, 190, 200), "Light alloy panels and struts.",
                ["METAL: same uses as iron scrap", "Lighter to carry"]),
 "copper": _r("Copper", 1.0, "uncommon", "conductor", (205, 125, 70), "Wiring and busbars.",
              ["Solar + heating repairs", "Antenna and power feed", "Transceiver fault fix"]),
 "electronics": _r("Electronics", 0.8, "uncommon", "electronic", (90, 200, 140), "Salvaged control boards.",
                   ["ELECTRONICS: oxygen, water, heating, greenhouse repairs", "Comms power feed", "Regolith processor"]),
 "circuit_board": _r("Circuit Board", 0.5, "rare", "electronic", (60, 230, 200), "Intact high-grade board (counts as 2 electronics).",
                     ["Counts as 2 ELECTRONICS", "Can serve as a calibration part"]),
 "polymer": _r("Polymer", 1.0, "common", "material", (200, 200, 215), "Sealant and plastics.",
               ["Water, greenhouse, airlock repairs", "Plot expansion", "Patch oxygen leaks"]),
 "glass": _r("Glass", 1.2, "uncommon", "material", (150, 215, 235), "Optical-grade panes.",
             ["Greenhouse controls repair"]),
 "battery": _r("Battery", 3.0, "uncommon", "power", (240, 210, 70), "Charged cell pack.",
               ["K near rover: +40% rover charge", "K inside base: +20% base power"]),
 "water": _r("Water Canister", 2.0, "uncommon", "consumable", (80, 150, 255), "5 litres of water.",
             ["K outside: drink (+40% hydration)", "K at base tank: refill 5 L tank"]),
 "food_ration": _r("Food Ration", 0.5, "uncommon", "consumable", (230, 170, 80), "Sealed emergency ration.",
                   ["K: restores 40% hunger"]),
 "fresh_produce": _r("Fresh Produce", 0.6, "common", "consumable", (130, 220, 90), "Greenhouse-grown food.",
                     ["K: restores 22% hunger"]),
 "seeds_potato": _r("Potato Seeds", 0.1, "rare", "seed", (200, 170, 100), "Hardy, slow, high yield.",
                    ["Plant in a greenhouse plot (J)"]),
 "seeds_bean": _r("Bean Seeds", 0.1, "rare", "seed", (170, 120, 80), "Medium growth, good seed return.",
                  ["Plant in a greenhouse plot (J)"]),
 "seeds_lettuce": _r("Lettuce Seeds", 0.1, "rare", "seed", (120, 220, 120), "Fast, low water, small yield.",
                     ["Plant in a greenhouse plot (J)"]),
 "growing_medium": _r("Growing Medium", 3.0, "uncommon", "farming", (110, 80, 60), "Prepared soil substrate.",
                      ["Needed to plant a crop (may be recovered)"]),
 "regolith": _r("Regolith", 2.0, "common", "raw", (190, 120, 90), "Raw Martian dust. Toxic perchlorates.",
                ["Processed into Growing Medium (Regolith Processor)"]),
 "oxygen_tank": _r("Oxygen Tank", 4.0, "uncommon", "consumable", (120, 220, 255), "Spare suit oxygen.",
                   ["K: +60% suit oxygen"]),
 "solar_component": _r("Solar Component", 2.0, "uncommon", "power", (255, 220, 90), "Photovoltaic cells.",
                       ["Solar array repair", "Install an extra panel"]),
 "mechanical_parts": _r("Mechanical Parts", 1.5, "uncommon", "mechanical", (170, 170, 190), "Gears, actuators, seals.",
                        ["Rover + airlock repairs", "Regolith processor"]),
 "tools": _r("Tool Kit", 2.0, "rare", "equipment", (255, 150, 60), "Precision tools.",
             ["Antenna install", "Regolith processor build"]),
 "medical": _r("Medical Supplies", 0.5, "uncommon", "medical", (255, 110, 120), "Med-kit.",
               ["K: +40 health, -15 radiation"]),
 "comm_component": _r("Comm Component", 1.0, "rare", "comms", (120, 170, 255), "Transceiver module.",
                      ["Antenna array", "Can serve as a calibration part"]),
 "rare_science": _r("Rare Sci. Component", 1.0, "very_rare", "science", (255, 120, 220), "Reference oscillator.",
                    ["Counts as 2 calibration parts"]),
 "map_fragment": _r("Map Fragment", 0.1, "rare", "navigation", (230, 230, 150), "Partial survey chart.",
                    ["K: reveals the nearest unknown site"]),
}
# generic requirement keys that accept several concrete resources (key -> {resource: units})
GROUPS = {
    "metal": {"iron_scrap": 1, "aluminum": 1},
    "electronic": {"electronics": 1, "circuit_board": 2},
    "calibrator": {"circuit_board": 1, "comm_component": 1, "rare_science": 2},
}
GROUP_NAMES = {"metal": "Metal", "electronic": "Electronics", "calibrator": "Calibration Parts"}
RARITY_COLOR = {"common": (210, 200, 170), "uncommon": (130, 230, 160), "rare": (90, 200, 255), "very_rare": (255, 120, 230)}
RARITY_ORDER = ["common", "uncommon", "rare", "very_rare"]
