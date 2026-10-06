import math, random, pygame
from config import *
from ui import draw as D

class Menu:
    def __init__(self, title, items, sub=None, y0=330):
        self.title, self.items, self.sub, self.y0, self.sel, self.rects = title, items, sub, y0, 0, []

    def label(self, i):
        l = self.items[i][0]
        return l() if callable(l) else l

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w): self.sel = (self.sel - 1) % len(self.items)
            elif e.key in (pygame.K_DOWN, pygame.K_s): self.sel = (self.sel + 1) % len(self.items)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_j): self.items[self.sel][1]()
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos): self.sel = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos): self.sel = i; self.items[i][1](); break

    def draw(self, s):
        self.rects = []
        if self.title: D.text(s, self.title, (SCREEN_W // 2, self.y0 - 50), 28, (255, 200, 120), True, "center")
        for i in range(len(self.items)):
            on = i == self.sel
            r = D.text(s, ("> " if on else "  ") + self.label(i) + ("  <" if on else ""), (SCREEN_W // 2, self.y0 + i * 40), 24 if on else 21, (255, 235, 150) if on else (180, 190, 205), on, "center")
            self.rects.append(r.inflate(60, 10))
        if self.sub: D.text(s, self.sub, (SCREEN_W // 2, self.y0 + len(self.items) * 40 + 10), 14, (255, 150, 120), False, "center")

_stars = [(random.random() * SCREEN_W, random.random() * SCREEN_H, random.random() * 6.28) for _ in range(140)]

def title_bg(g, s):
    s.fill((6, 8, 18))
    for x, y, p in _stars:
        v = 120 + int(100 * math.sin(g.real_t * 1.5 + p)); pygame.draw.circle(s, (v, v, v), (x, y * 0.7), 1)
    pygame.draw.circle(s, (120, 52, 34), (SCREEN_W // 2, SCREEN_H + 560), 900); pygame.draw.circle(s, (190, 100, 64), (SCREEN_W // 2, SCREEN_H + 560), 900, 6)
    D.text(s, "MARS: LAST SIGNAL", (SCREEN_W // 2, 130), 54, (255, 190, 110), True, "center")
    D.text(s, "a survival simulation", (SCREEN_W // 2, 184), 16, (170, 180, 200), False, "center")

INTRO = ["You are alone.", "The last supply shipment never arrived.", "The base is damaged.", "Earth has not received your signal.", "Survive."]

def intro(g, s):
    s.fill((4, 5, 10))
    n = min(len(INTRO), int(g.intro_t / 1.7) + 1)
    for i in range(n):
        a = min(1.0, (g.intro_t - i * 1.7) / 1.0)
        c = int(230 * a)
        D.text(s, INTRO[i], (SCREEN_W // 2, 240 + i * 50), 28 if i == 4 else 22, (c, c, min(255, c + 20)), i == 4, "center", shadow=False)
    D.text(s, "press any key", (SCREEN_W // 2, SCREEN_H - 40), 13, (100, 110, 130), False, "center")

def dim(s):
    sf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); sf.fill((0, 0, 0, 170)); s.blit(sf, (0, 0))

def summary(g, s):
    dim(s)
    e = g.ending
    won = e["won"]
    D.text(s, "SURVIVAL COMPLETE" if won else "SURVIVAL FAILED", (SCREEN_W // 2, 50), 40, (120, 255, 160) if won else (255, 90, 90), True, "center")
    y = 100
    for lab, val in e["lines"]:
        D.text(s, lab, (SCREEN_W // 2 - 20, y), 15, (160, 180, 200), False, "topright"); D.text(s, val, (SCREEN_W // 2 + 4, y), 15, (240, 240, 230), True); y += 20
    y += 6; D.text(s, "Major decisions:", (SCREEN_W // 2 - 20, y), 15, (120, 190, 230), True, "topright")
    for d in e["decisions"][-8:]:
        D.text(s, "- " + d, (SCREEN_W // 2 + 4, y), 14, (210, 215, 220)); y += 18
