"""Headless smoke test: python tools/smoke_test.py  (no window needed)."""
import os, sys, math
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
pygame.init()
from config import *
from core.game import Game
from base import layout, stations

def main():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    g = Game(screen, debug=True)
    for _ in range(5): g.update(0.03); g.draw()   # title screen before any game exists
    g.reset(); g.state = "play"
    def run(sec, dt=1 / 30):
        for _ in range(int(sec / dt)):
            g.update(dt); g.draw()
            if g.state != "play": break
    run(5)
    # repair oxygen generator
    st = next(s for s in layout.STATIONS if s["id"] == "o2")
    g.player.ipos = [st["x"], st["y"] + 40.0]
    before = g.base.sys["oxygen_gen"]; g.act_j()
    assert g.base.sys["oxygen_gen"] == 100.0 > before, "repair failed"
    # storage + inventory transfer
    ch = next(s for s in layout.STATIONS if s["id"] == "chest"); g.player.ipos = [ch["x"], ch["y"] + 40.0]
    g.open_inventory(); assert g.container is g.base.storage
    g.inv_pane = 1; g.inv_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j, unicode="j")); g.panel = None
    # plant a seed
    pl = layout.PLOTS[0]; g.player.ipos = [pl["x"], pl["y"]]
    g.player.inv.add("seeds_potato", 1); g.player.sel = g.player.inv.order().index("seeds_potato"); g.act_j()
    assert g.base.plots[0].crop == "seeds_potato", "plant failed"
    # exit base, walk, collect, save/load
    g.player.ipos = [layout.EXIT[0], layout.EXIT[1] - 10.0]; g.act_j(); assert not g.player.inside
    n = next(iter(g.world.nodes.values())); g.player.wpos = [n["x"] - 20, n["y"]]; n0 = len(n["items"]); g.act_j()
    g.save_game(); t0, o0 = g.clock.t, g.player.stats["oxygen"]; run(3)
    assert g.load_game(); assert abs(g.clock.t - t0) < 1e-6 and abs(g.player.stats["oxygen"] - o0) < 1e-6
    # rover
    g.state = "play"; g.player.wpos = [g.rover.pos[0] + 40, g.rover.pos[1]]; g.act_e(); assert g.player.in_rover
    g.rover.battery = 100; run(2); g.act_e(); assert not g.player.in_rover
    # every event fires without error
    from events.events import EVENTS
    g.clock.t = SOL_LENGTH * 9
    for ev in EVENTS:
        if ev[5] is None or ev[5](g): ev[6](g, g.events)
    run(5)
    # range death
    g.player.wpos = [BASE_POS[0] + MAX_RANGE + 200, BASE_POS[1]]; g.player.inside = False; g.player.in_rover = False
    run(120)
    assert g.state == "over" and not g.ending["won"], g.state
    print("SMOKE OK:", g.ending["lines"][0], "| notes:", len(g.log))

if __name__ == "__main__":
    main()
