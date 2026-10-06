"""Game orchestrator: states, input, simulation step, save/load, endings."""
import math, random
import pygame
from config import *
from core import save_system, render
from core.clock import Clock
from core.world import World
from core.collision import resolve
from core.event_manager import EventManager
from player.player import Player
from player import survival
from vehicles.rover import Rover
from base.base import Base
from base import layout, stations
from ai.assistant import Assistant
from data.resources import RESOURCES
from data.systems import ROVER_REPAIR
from resources import resource_manager as RM
from exploration.discoveries import compass, fmt_dist
from ui import draw as D, hud, panels, menus, audio
from ui.menus import Menu

HINTS = [
 ("move", lambda g: g.sim_t > 0.5, "WASD to move, SHIFT to sprint. Watch the left panel: oxygen, food, water, temperature, radiation."),
 ("station", lambda g: g.player.inside and stations.nearby(g) is not None, "J interacts with consoles, plots and crates. Floating markers show what a repair needs (have / required)."),
 ("inv", lambda g: g.player.inv.weight() > 0 and g.sim_t > 8, "Q / R select an item, K uses it. I opens inventory; next to storage or the rover you can move items between them."),
 ("assist", lambda g: g.sim_t > 35, "TAB opens the AI assistant. It suggests priorities and plans, but you always decide."),
 ("food", lambda g: g.player.stats["hunger"] < 80, "Hunger and thirst fall steadily. Select a ration (Q/R) and press K to eat. Drink at the Water Tank (J) in Life Support."),
 ("outside", lambda g: not g.player.inside, "OUTSIDE: suit oxygen drains and radiation builds. Inside the base the suit refills. Watch RANGE and RETURN COST."),
 ("farm", lambda g: g.player.inside and any(math.hypot(g.player.ipos[0] - x, g.player.ipos[1] - y) < 90 for x, y in layout.PLOT_POS), "Farming: select seeds (Q/R), stand at an empty plot, press J. Each crop uses water, a growing medium, power and time."),
 ("rover", lambda g: not g.player.inside and not g.player.in_rover and math.hypot(g.player.wpos[0] - g.rover.pos[0], g.player.wpos[1] - g.rover.pos[1]) < 200, "Rover: E to drive, E again to exit. Its cargo is separate from your 25 kg. It drains battery; recharge at base."),
 ("explore", lambda g: not g.player.inside and g.player.dist > 900, "Glowing outlines are collectible: J to take. Rarer things glow in other colours. M opens the map."),
 ("wear", lambda g: g.clock.sol >= 2, "Base systems wear out over time. Stand at a console to see what a repair costs; the same parts are needed everywhere."),
]

class Game:
    def __init__(self, screen, debug=False):
        self.screen, self.debug, self.debug_on, self.running = screen, debug, False, True
        self.settings = dict(sound=True, hints=True)
        self.real_t, self.intro_t, self.state = 0.0, 0.0, "title"
        self.world = None
        self.ending = None
        self.notes, self.log, self.decisions, self.hint = [], [], [], None
        self.panel = None
        self.settings_back = "title"
        self.build_menus()

    # ------------------------------------------------ setup
    def reset(self):
        self.clock, self.world, self.player, self.rover = Clock(), World(), Player(), Rover()
        self.base, self.assistant = Base(), Assistant()
        self.events = EventManager(self)
        self.notes, self.log, self.decisions = [], [], []
        self.priority, self.assist_open, self.assist_opts, self.assist_t = None, False, [], 0.0
        self.stats = dict(collected=0, dist_px=0.0, harvests=0, repairs=0)
        self.panel, self.inv_pane, self.inv_cur, self.container, self.container_name = None, 0, 0, None, ""
        self.warned, self.hints_done, self.hint, self.hint_t, self.hint_check = {}, set(), None, 0.0, 0.0
        self.warp, self.ending, self.sim_t = False, None, 0.0
        self.env = self.make_env()

    def build_menus(self):
        def go(st, m=None): self.state = st; self.menu = self.menus[m or st]
        def new():
            self.reset(); self.intro_t = 0.0; self.state = "intro"
        def load():
            if self.load_game(): self.state = "play"
            else: self.menus["title"].sub = "No save found." if self.state == "title" else None; self.menus["pause"].sub = "No save found."
        def tog(k):
            self.settings[k] = not self.settings[k]; audio.enabled = self.settings["sound"]
        def fs(): pygame.display.toggle_fullscreen()
        def back(): go(self.settings_back)
        def to_settings(frm): self.settings_back = frm; go("settings")
        def to_title(): self.state = "title"; self.menu = self.menus["title"]; self.menus["title"].sub = None
        def resume(): self.state = "play"
        def save(): self.save_game(); resume()
        def quit_(): self.running = False
        onoff = lambda k: "ON" if self.settings[k] else "OFF"
        self.menus = dict(
            title=Menu(None, [("NEW SURVIVAL", new), ("LOAD SURVIVAL", load), ("SETTINGS", lambda: to_settings("title")), ("QUIT", quit_)], y0=300),
            settings=Menu("SETTINGS", [(lambda: f"SOUND: {onoff('sound')}", lambda: tog("sound")), (lambda: f"TUTORIAL HINTS: {onoff('hints')}", lambda: tog("hints")),
                                       ("TOGGLE FULLSCREEN", fs), ("BACK", back)], y0=300),
            pause=Menu("PAUSED", [("RESUME", resume), ("SAVE GAME", save), ("LOAD GAME", load), ("SETTINGS", lambda: to_settings("pause")), ("MAIN MENU", to_title), ("QUIT", quit_)], y0=260),
            over=Menu(None, [("LOAD SAVE", load), ("RESTART", new), ("MAIN MENU", to_title)], y0=560))
        self.menu = self.menus["title"]

    def make_env(self):
        cl, ev = self.clock, self.events
        day = cl.daylight()
        return dict(daylight=day, ambient=cl.ambient() + ev.cold_delta + ev.storm * (8 - 20 * day), storm=ev.storm, rad_mult=ev.rad_mult)

    # ------------------------------------------------ messaging
    def notify(self, text, level="info"):
        self.notes.append([text, level, 6.0]); self.notes = self.notes[-6:]
        self.log.append(f"Sol {self.clock.sol} {self.clock.time_str()}  {text}"); self.log = self.log[-40:]
        if level == "bad": audio.beep(330, 200, 0.25)
        elif level == "warn": audio.beep(520, 120, 0.18)
        elif level == "good": audio.beep(880, 90, 0.12)

    def warn(self, key, text, cooldown, level="warn"):
        if self.real_t - self.warned.get(key, -999) >= cooldown:
            self.warned[key] = self.real_t; self.notify(text, level)

    def decide(self, text):
        self.decisions.append(f"Sol {self.clock.sol}: {text}"); self.decisions = self.decisions[-30:]

    def log_event(self, text): self.log.append(f"Sol {self.clock.sol} {self.clock.time_str()}  {text}")

    # ------------------------------------------------ save / load
    def serialize(self):
        return dict(clock=self.clock.t, player=self.player.to_dict(), rover=self.rover.to_dict(), base=self.base.to_dict(), world=self.world.to_dict(),
                    events=self.events.to_dict(), priority=self.priority, stats=self.stats, decisions=self.decisions, log=self.log[-20:], hints=list(self.hints_done), sim_t=self.sim_t)

    def save_game(self):
        try:
            save_system.save(self.serialize()); self.notify("Game saved.", "good")
        except OSError as e:
            self.notify(f"Save failed: {e}", "bad")

    def load_game(self):
        d = save_system.load()
        if not d: return False
        try:
            self.reset()
            self.clock.t = d["clock"]; self.player.load(d["player"]); self.rover.load(d["rover"]); self.base.load(d["base"]); self.world.load(d["world"])
            self.events.load(d["events"]); self.priority = d["priority"]; self.stats = d["stats"]; self.decisions = d["decisions"]; self.log = d["log"]
            self.hints_done = set(d["hints"]); self.sim_t = d.get("sim_t", 100.0)
            self.env = self.make_env()
        except (KeyError, TypeError, ValueError):
            return False
        self.notify("Game loaded.", "good")
        return True

    # ------------------------------------------------ endings
    def _ending(self, won, cause=""):
        b, p = self.base, self.player
        lines = [("Cause", cause)] if not won else [("Communication restored", "YES"), ("Rescue survived", "YES")]
        lines += [("Sol survived", str(self.clock.sol)), ("Resources recovered", str(self.stats["collected"])),
                  ("Distance explored", f"{self.stats['dist_px'] * PX_TO_M / 1000:.1f} km"), ("Base condition", f"{b.condition():.0f}%"),
                  ("Communication", f"{b.comm_progress():.0f}%"), ("Farm", f"{sum(1 for q in b.plots if q.unlocked)} plots, {self.stats['harvests']} harvests"),
                  ("Repairs made", str(self.stats["repairs"]))]
        if won: lines.append(("Resources remaining", f"{sum(b.storage.items.values()) + sum(p.inv.items.values())} items; food {sum(b.storage.count(k) for k in ('food_ration', 'fresh_produce'))}"))
        self.ending = dict(won=won, lines=lines, decisions=list(self.decisions))
        self.state, self.menu, self.panel = "over", self.menus["over"], None
        audio.beep(220 if not won else 990, 500, 0.3)

    def die(self, cause):
        if self.state == "play": self._ending(False, cause)

    # ------------------------------------------------ interaction helpers
    def nearest_node(self, pos, reach):
        best, bd = None, reach
        for n in self.world.nodes.values():
            if n["hidden"] and not n["revealed"]: continue
            d = math.hypot(n["x"] - pos[0], n["y"] - pos[1])
            if d < bd: best, bd = n, d
        return best

    def collect(self, n, inv, who="inventory"):
        if n["cost"]:
            if not RM.affordable([self.player.inv], n["cost"]):
                return self.notify(f"Sealed vault. Needs {RM.missing_text([self.player.inv], n['cost'])}", "warn")
            RM.pay([self.player.inv], n["cost"]); n["cost"] = None; n["kind"] = "crate"
            return self.notify("Vault unlocked. Press J again.", "good")
        for it in n["items"]:
            got = inv.add(it[0], it[1])
            if got:
                it[1] -= got; self.stats["collected"] += got
                self.notify(f"+{got} {RESOURCES[it[0]]['name']}", "good"); break
        else:
            return self.notify(f"{who.capitalize()} full: {inv.free():.1f} kg free. Drop something or use the rover.", "warn")
        n["items"] = [i for i in n["items"] if i[1] > 0]
        if not n["items"]: self.world.remove_node(n["id"])

    def near_door(self, pos, r=85): return math.hypot(pos[0] - self.world.door[0], pos[1] - self.world.door[1]) < r
    def near_rover(self, r=100): return math.hypot(self.player.wpos[0] - self.rover.pos[0], self.player.wpos[1] - self.rover.pos[1]) < r

    def enter_base(self):
        p = self.player
        if p.in_rover: return self.notify("Exit the rover first (E).", "warn")
        p.inside = True; p.ipos = [float(layout.SPAWN[0]), float(layout.SPAWN[1])]
        self.notify("Airlock cycled. Inside the base: suit refilling from base air.", "info")

    def exit_base(self):
        p = self.player
        p.inside = False; p.wpos = [self.world.door[0], self.world.door[1] + 40.0]
        self.notify("Outside. Oxygen is draining. Mind the range.", "warn")

    def open_inventory(self):
        p = self.player
        self.container = None
        if p.inside:
            ch = next(s for s in layout.STATIONS if s["id"] == "chest")
            if math.hypot(p.ipos[0] - ch["x"], p.ipos[1] - ch["y"]) < 150: self.container, self.container_name = self.base.storage, "BASE STORAGE"
        elif p.in_rover or self.near_rover(140): self.container, self.container_name = self.rover.inv, "ROVER CARGO"
        self.panel, self.inv_pane, self.inv_cur = "inventory", 0, 0

    def act_j(self):
        p = self.player
        if p.inside:
            st = stations.nearby(self)
            return stations.interact(self, st) if st else self.notify("Nothing in reach.", "info")
        if p.in_rover:
            n = self.nearest_node(self.rover.pos, 100)
            return self.collect(n, self.rover.inv, "rover cargo") if n else self.notify("Nothing in reach of the rover.", "info")
        n = self.nearest_node(p.wpos, 70)
        if n: return self.collect(n, p.inv)
        if self.near_rover(95):
            r = self.rover
            if r.integ >= 99: return self.notify("Rover hull is intact. E to drive, I for cargo.", "info")
            cs = [p.inv, r.inv]
            if not RM.affordable(cs, ROVER_REPAIR): return self.notify(f"Cannot repair rover. Missing: {RM.missing_text(cs, ROVER_REPAIR)}", "warn")
            RM.pay(cs, ROVER_REPAIR); r.integ = 100.0; self.stats["repairs"] += 1
            self.notify("Rover repaired to 100%.", "good"); self.decide("Repaired the rover"); return
        if self.near_door(p.wpos): return self.enter_base()
        self.notify("Nothing in reach.", "info")

    def act_e(self):
        p = self.player
        if p.inside:
            st = stations.nearby(self)
            if st: stations.secondary(self, st)
        elif p.in_rover:
            r = self.rover; r.driven = p.in_rover = False; r.v = [0.0, 0.0]
            p.wpos = [r.pos[0] + 40.0, r.pos[1] + 10.0]; self.world.move(p.wpos, 0, 0, PLAYER_RADIUS, [r.circle()])
            self.notify("Left the rover.", "info")
        elif self.near_door(p.wpos): self.enter_base()
        elif self.near_rover(100):
            if not self.rover.can_drive(): self.notify("Rover cannot drive: " + ("battery empty." if self.rover.battery <= 0 else "engine damaged. Repair it (J)."), "warn")
            p.in_rover = self.rover.driven = True; p.wpos = list(self.rover.pos)
            self.notify("Driving. Cargo here does not count toward your carry weight.", "info")
        else: self.notify("Nothing to use here.", "info")

    def prompts(self):
        p, out = self.player, []
        if p.inside:
            st = stations.nearby(self)
            return stations.prompts(self, st) if st else []
        if p.in_rover:
            n = self.nearest_node(self.rover.pos, 100)
            if n: out.append(("J", f"Collect {RESOURCES[n['items'][0][0]]['name']} to rover cargo" if not n["cost"] else "Open sealed vault"))
            return out + [("E", "Exit rover")]
        n = self.nearest_node(p.wpos, 70)
        if n: out.append(("J", (f"Collect {RESOURCES[n['items'][0][0]]['name']} x{n['items'][0][1]}" if not n["cost"] else "Unlock vault") + ("" if len(n["items"]) < 2 else f" (+{len(n['items']) - 1} more)")))
        if self.near_rover(100): out += [("E", "Drive rover" + ("" if self.rover.integ >= 99 else " (J: repair)")), ("I", "Rover cargo")]
        if self.near_door(p.wpos): out += [("E", "Enter base")]
        return out

    # ------------------------------------------------ items
    def use_selected(self):
        p = self.player; rid = p.selected_id()
        if not rid: return self.notify("Nothing selected. Q/R cycles items.", "warn")
        if self.use_item(rid): p.inv.remove(rid, 1)

    def use_item(self, rid):
        p, s, b, r = self.player, self.player.stats, self.base, self.rover
        nm = RESOURCES[rid]["name"]
        if rid in ("food_ration", "fresh_produce"):
            if s["hunger"] > 92: self.notify("Not hungry.", "info"); return False
            s["hunger"] = min(100, s["hunger"] + (FOOD_RATION_HUNGER if rid == "food_ration" else PRODUCE_HUNGER)); self.notify(f"Ate {nm}.", "good"); return True
        if rid == "water":
            tank = next(x for x in layout.STATIONS if x["id"] == "tank")
            if p.inside and math.hypot(p.ipos[0] - tank["x"], p.ipos[1] - tank["y"]) < 150:
                if b.tank + WATER_CANISTER_L > TANK_CAP: self.notify("Tank is full.", "info"); return False
                b.tank += WATER_CANISTER_L; self.notify(f"Poured 5 L into the tank ({b.tank:.0f} L).", "good"); return True
            if s["hydration"] > 85: self.notify("Not thirsty. (Pour into the base tank with K at the tank.)", "info"); return False
            s["hydration"] = min(100, s["hydration"] + WATER_CANISTER_L * PCT_PER_LITER); b.waste += WATER_CANISTER_L * 0.8; self.notify("Drank a canister.", "good"); return True
        if rid == "medical":
            s["health"] = min(100, s["health"] + MEDICAL_HEAL); s["radiation"] = max(0, s["radiation"] - MEDICAL_RAD); self.notify("Medical treatment applied.", "good"); return True
        if rid == "oxygen_tank":
            if s["oxygen"] > 85: self.notify("Suit tank nearly full.", "info"); return False
            s["oxygen"] = min(100, s["oxygen"] + OXYGEN_TANK_REFILL); self.notify("Oxygen tank connected: +60% suit oxygen.", "good"); return True
        if rid == "battery":
            if not p.inside and math.hypot(p.wpos[0] - r.pos[0], p.wpos[1] - r.pos[1]) < 130 and r.battery < 95:
                r.battery = min(100, r.battery + 40); self.notify("Rover battery +40%.", "good"); return True
            if p.inside and b.battery < BATTERY_CAP * 0.9:
                b.battery = min(BATTERY_CAP, b.battery + BATTERY_CAP * 0.2); self.notify("Base battery bank +20%.", "good"); return True
            self.notify("Use near the rover (to charge it) or inside the base.", "info"); return False
        if rid == "map_fragment":
            l = self.world.reveal_nearest_unknown()
            if not l: self.notify("The chart shows nothing new.", "info"); return False
            dx, dy = l["x"] - BASE_POS[0], l["y"] - BASE_POS[1]
            self.notify(f"MAP UPDATED: {l['name']}, {fmt_dist(math.hypot(dx, dy))} {compass(dx, dy)} of base.", "good"); self.decide(f"Charted {l['name']}"); return True
        hints = {"seeds": "Plant seeds at a greenhouse plot (J).", "growing_medium": "Planting uses one Growing Medium.", "regolith": "Process it at the Workshop (needs the processor).",
                 "solar_component": "Install at the Power Bus (E).", "tools": "Used in antenna / processor builds.", "comm_component": "Used at the Communications Console."}
        self.notify(hints.get(RESOURCES[rid]["category"], hints.get(rid, f"{nm}: used in repairs at base consoles.")), "info")
        return False

    # ------------------------------------------------ input
    def handle_event(self, e):
        if e.type == pygame.QUIT: self.running = False; return
        st = self.state
        if st in ("title", "settings", "pause", "over"):
            if st in ("pause", "settings") and e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = "play" if st == "pause" else self.settings_back; self.menu = self.menus[self.state] if self.state != "play" else self.menu; return
            self.menu.handle(e); return
        if st == "intro":
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) and self.intro_t > 0.8: self.state = "play"
            return
        if e.type == pygame.MOUSEWHEEL and self.panel is None: self.player.cycle(-e.y); return
        if e.type != pygame.KEYDOWN: return
        k = e.key
        if self.panel == "inventory": return self.inv_key(e)
        if self.panel == "map":
            if k in (pygame.K_ESCAPE, pygame.K_m): self.panel = None
            return
        if k == pygame.K_ESCAPE: self.state, self.menu = "pause", self.menus["pause"]; self.menus["pause"].sub = None; self.menus["pause"].sel = 0
        elif k == pygame.K_j: self.act_j()
        elif k == pygame.K_e: self.act_e()
        elif k == pygame.K_k: self.use_selected()
        elif k == pygame.K_i: self.open_inventory()
        elif k == pygame.K_m: self.panel = "map"
        elif k == pygame.K_q: self.player.cycle(-1)
        elif k == pygame.K_r: self.player.cycle(1)
        elif k == pygame.K_TAB:
            self.assist_open = not self.assist_open
            if self.assist_open: self.assist_opts = self.assistant.options(self)
        elif k == pygame.K_F5: self.save_game()
        elif k == pygame.K_F9:
            if self.load_game(): pass
            else: self.notify("No save found.", "warn")
        elif self.assist_open and k in (pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            i = k - pygame.K_0
            if i == 0: self.priority = None; return
            if i <= len(self.assist_opts):
                o = self.assist_opts[i - 1]; self.priority = dict(id=o["id"], label=o["label"]); self.decide(f"Priority: {o['label']}")
                r = self.assistant.react(self, o["id"])
                if r: self.notify("AI: " + r, "info")
        elif self.debug:
            if k == pygame.K_F3: self.debug_on = not self.debug_on
            elif k == pygame.K_F6:
                for rid in RESOURCES: self.base.storage.add(rid, 5)
                self.notify("DEBUG: 5 of everything added to base storage.", "info")
            elif k == pygame.K_F7: self.warp = not self.warp
            elif k == pygame.K_F8:
                for key in self.player.stats: self.player.stats[key] = 0.0 if key == "radiation" else 100.0
                self.base.battery, self.base.o2 = BATTERY_CAP, 100.0
            elif k == pygame.K_F10: self.events.start("dust_storm", 5, 60, sev=0.8)
            elif k == pygame.K_F11: self.events.next_in = 0

    def inv_key(self, e):
        k, p = e.key, self.player
        shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
        if k in (pygame.K_ESCAPE, pygame.K_i): self.panel = None; return
        invs = [p.inv] + ([self.container] if self.container else [])
        pane = min(self.inv_pane, len(invs) - 1)
        cur = p.sel if pane == 0 else self.inv_cur
        order = invs[pane].order()
        if k in (pygame.K_w, pygame.K_UP): cur = max(0, cur - 1)
        elif k in (pygame.K_s, pygame.K_DOWN): cur = min(max(0, len(order) - 1), cur + 1)
        elif k in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT) and self.container: self.inv_pane = 1 - pane; return
        elif k == pygame.K_k and pane == 0: self.use_selected(); return
        elif k == pygame.K_j and order:
            if not self.container: return self.notify("Nothing to transfer to here. Open near storage or the rover.", "info")
            rid = order[min(cur, len(order) - 1)]; src, dst = invs[pane], invs[1 - pane]
            n = dst.add(rid, src.count(rid) if shift else 1)
            if n: src.remove(rid, n)
            else: self.notify(f"No capacity ({dst.free():.1f} kg free).", "warn")
            cur = min(cur, max(0, len(src.order()) - 1))
        if pane == 0: p.sel = cur
        else: self.inv_cur = cur

    # ------------------------------------------------ simulation
    def update(self, dt):
        self.real_t += dt
        if self.state == "intro":
            self.intro_t += dt
            if self.intro_t > 14: self.state = "play"
            return
        for n in self.notes: n[2] -= dt
        self.notes = [n for n in self.notes if n[2] > 0]
        if self.state != "play" or self.panel: return
        self.sim_t += dt
        self.sim(dt * (TIME_WARP if self.warp else 1))
        self.hint_check -= dt
        if self.hint:
            self.hint_t -= dt
            if self.hint_t <= 0: self.hint = None
        elif self.hint_check <= 0:
            self.hint_check = 0.5
            for hid, cond, txt in HINTS:
                if hid not in self.hints_done and cond(self):
                    self.hints_done.add(hid); self.hint, self.hint_t = txt, 9.0; break
        if self.assist_open:
            self.assist_t -= dt
            if self.assist_t <= 0: self.assist_opts = self.assistant.options(self); self.assist_t = 1.0

    def sim(self, dt):
        self.clock.t += dt
        self.events.update(dt)
        self.env = self.make_env()
        self.move_player(dt)
        r, b = self.rover, self.base
        near = math.hypot(r.pos[0] - BASE_POS[0], r.pos[1] - BASE_POS[1]) < 420 and not r.driven
        if near and r.battery < 100 and b.battery > 20:
            b.charge_load = ROVER_CHARGE_LOAD; r.battery = min(100.0, r.battery + ROVER_CHARGE_RATE * dt * b.supply)
        else: b.charge_load = 0.0
        b.update(dt, self.env, self)
        survival.update(self, dt)
        p = self.player
        if not p.inside:
            pos = r.pos if p.in_rover else p.wpos
            for l in self.world.update_discovery(pos[0], pos[1], 1 - 0.55 * self.env["storm"]):
                dx, dy = l["x"] - BASE_POS[0], l["y"] - BASE_POS[1]
                self.notify(f"DISCOVERED: {l['name']} - {fmt_dist(math.hypot(dx, dy))} {compass(dx, dy)} of base.", "good"); self.decide(f"Found {l['name']}")
        if b.rescue_time and self.clock.t >= b.rescue_time and self.state == "play": self._ending(True)

    def move_player(self, dt):
        p, keys = self.player, pygame.key.get_pressed()
        dx = int(keys[pygame.K_d]) - int(keys[pygame.K_a]); dy = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        n = math.hypot(dx, dy)
        s = p.stats
        if p.in_rover:
            r = self.rover; before = tuple(r.pos)
            r.drive(self, dx, dy, dt); p.wpos = list(r.pos); p.moving, p.sprinting = r.moving, False
            self.stats["dist_px"] += math.hypot(r.pos[0] - before[0], r.pos[1] - before[1]); return
        p.moving = n > 0
        p.sprinting = bool(keys[pygame.K_LSHIFT] and p.moving and s["stamina"] > 5)
        if not n: return
        dx, dy = dx / n, dy / n
        p.facing = [dx, dy]
        sp = PLAYER_SPEED * (1 - WEIGHT_SLOWDOWN * p.weight_factor()) * (SPRINT_MULT if p.sprinting else 1.0)
        if s["stamina"] < 15: sp *= 0.8
        if s["oxygen"] < 15: sp *= 0.85
        if p.inside:
            pos = p.ipos; before = tuple(pos)
            for ax, d in ((0, dx), (1, dy)):
                pos[ax] += d * sp * dt; resolve(pos, PLAYER_RADIUS, [], layout.WALLS + layout.SOLIDS)
        else:
            if "dust_trap" in self.world.hazards_at(*p.wpos): sp *= 0.55; s["stamina"] -= 4 * dt
            before = tuple(p.wpos)
            self.world.move(p.wpos, dx * sp * dt, dy * sp * dt, PLAYER_RADIUS, [] if self.rover.driven else [self.rover.circle()])
            self.stats["dist_px"] += math.hypot(p.wpos[0] - before[0], p.wpos[1] - before[1])

    # ------------------------------------------------ drawing
    def draw(self):
        s = self.screen
        if self.state in ("title", "settings"):
            menus.title_bg(self, s); self.menu.draw(s); return
        if self.state == "intro": menus.intro(self, s); return
        render.scene(s, self)
        render.vignette(s, self)
        hud.draw(self, s)
        if self.panel == "inventory": panels.inventory(self, s)
        elif self.panel == "map": panels.map_panel(self, s)
        if self.state == "pause": menus.dim(s); self.menu.draw(s)
        elif self.state == "over": menus.summary(self, s); self.menu.draw(s)
