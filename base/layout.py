"""Base interior geometry (separate map layer, 1200x700) and interactable stations."""
from pygame import Rect
from config import MAX_PLOTS

T = 12
def _h(y, x0, x1, gaps):
    out, x = [], x0
    for g0, g1 in sorted(gaps):
        if g0 > x: out.append(Rect(x, y, g0 - x, T))
        x = g1
    if x < x1: out.append(Rect(x, y, x1 - x, T))
    return out

WALLS = [Rect(48, 38, 1104, T), Rect(48, 650, 1104, T), Rect(48, 38, T, 624), Rect(1140, 38, T, 624)]
WALLS += _h(300, 60, 1140, [(180, 280), (550, 650), (920, 1020)])
WALLS += _h(368, 60, 1140, [(130, 230), (375, 475), (625, 725), (920, 1020)])
WALLS += [Rect(394, 50, T, 250), Rect(794, 50, T, 250)]
WALLS += [Rect(x - 6, 380, T, 270) for x in (300, 550, 800)]

ROOMS = [("LIVING QUARTERS", Rect(60, 50, 340, 250), (46, 56, 74)), ("GREENHOUSE", Rect(400, 50, 400, 250), (40, 66, 52)),
         ("COMMUNICATIONS", Rect(800, 50, 340, 250), (50, 52, 78)), ("CORRIDOR", Rect(60, 312, 1080, 56), (52, 54, 60)),
         ("AIRLOCK", Rect(60, 380, 240, 270), (70, 60, 48)), ("STORAGE", Rect(300, 380, 250, 270), (58, 56, 52)),
         ("WORKSHOP", Rect(550, 380, 250, 270), (62, 54, 46)), ("LIFE SUPPORT", Rect(800, 380, 340, 270), (44, 58, 62))]

EXIT = (180, 622)
SPAWN = (180, 585)

def _s(id, kind, x, y, label, sys=None, solid=True, r=75):
    return dict(id=id, kind=kind, x=x, y=y, label=label, sys=sys, solid=solid, r=r)

STATIONS = [
    _s("save", "save", 150, 110, "Save Terminal"), _s("assistant", "assistant", 310, 110, "AI Assistant Console"),
    _s("gh", "sys", 770, 100, "Greenhouse Controls", "greenhouse"), _s("comms", "comms", 970, 130, "Communications Console", r=85),
    _s("airlock", "sys", 110, 440, "Airlock Seals", "airlock"), _s("exit", "exit", EXIT[0], EXIT[1], "Airlock Door", solid=False, r=60),
    _s("chest", "chest", 425, 470, "Base Storage"), _s("processor", "processor", 650, 450, "Regolith Processor"),
    _s("o2", "sys", 860, 430, "Oxygen Generator", "oxygen_gen"), _s("water", "sys", 960, 430, "Water Recycler", "water_recycler"),
    _s("tank", "tank", 1060, 430, "Water Tank"), _s("solar", "sys", 880, 580, "Power Bus / Solar Array", "solar"),
    _s("heat", "sys", 1010, 580, "Heating System", "heating"),
]
PLOT_POS = [(450 + i * 95, 115 + j * 110) for j in range(2) for i in range(4)]
PLOTS = [dict(id=f"plot{i}", kind="plot", idx=i, x=x, y=y, label=f"Plot {i + 1}", sys=None, solid=False, r=52) for i, (x, y) in enumerate(PLOT_POS)][:MAX_PLOTS]
INTERACTABLES = STATIONS + PLOTS
SOLIDS = [Rect(s["x"] - 22, s["y"] - 22, 44, 44) for s in STATIONS if s["solid"]]
