import math, pygame
_f = {}
def font(sz=16, bold=False):
    k = (sz, bold)
    if k not in _f:
        _f[k] = pygame.font.SysFont("consolas,couriernew,dejavusansmono,liberationmono,monospace", sz, bold=bold)
    return _f[k]

def text(s, txt, pos, sz=16, col=(220, 230, 240), bold=False, anchor="topleft", shadow=True):
    f = font(sz, bold)
    img = f.render(str(txt), True, col)
    r = img.get_rect(**{anchor: pos})
    if shadow: s.blit(f.render(str(txt), True, (0, 0, 0)), r.move(1, 1))
    s.blit(img, r)
    return r

def panel(s, rect, alpha=190, border=(70, 120, 150), title=None):
    sf = pygame.Surface(rect.size, pygame.SRCALPHA); sf.fill((8, 14, 22, alpha)); s.blit(sf, rect.topleft)
    pygame.draw.rect(s, border, rect, 1)
    if title: text(s, title, (rect.x + 8, rect.y + 4), 13, (120, 190, 230), True)

def bar(s, rect, frac, col, flash=False, t=0.0):
    frac = max(0.0, min(1.0, frac))
    pygame.draw.rect(s, (20, 26, 34), rect)
    c = (255, 255, 255) if flash and int(t * 4) % 2 else col
    pygame.draw.rect(s, c, (rect.x, rect.y, int(rect.w * frac), rect.h))
    pygame.draw.rect(s, (70, 90, 110), rect, 1)

def wrap(txt, sz, width):
    f, lines = font(sz), []
    for para in str(txt).split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if f.size(t)[0] <= width: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def icon(s, kind, cx, cy, col, z=8):
    if kind == "heart":
        pygame.draw.circle(s, col, (cx - z // 2, cy - 2), z // 2 + 1); pygame.draw.circle(s, col, (cx + z // 2, cy - 2), z // 2 + 1)
        pygame.draw.polygon(s, col, [(cx - z, cy), (cx + z, cy), (cx, cy + z)])
    elif kind == "lungs":
        pygame.draw.ellipse(s, col, (cx - z, cy - z, z, z * 2)); pygame.draw.ellipse(s, col, (cx, cy - z, z, z * 2))
    elif kind == "food":
        pygame.draw.circle(s, col, (cx, cy + 1), z - 1); pygame.draw.rect(s, col, (cx - 1, cy - z, 3, 5))
    elif kind == "drop":
        pygame.draw.polygon(s, col, [(cx, cy - z), (cx - z + 2, cy + 2), (cx + z - 2, cy + 2)]); pygame.draw.circle(s, col, (cx, cy + 2), z - 2)
    elif kind == "therm":
        pygame.draw.rect(s, col, (cx - 2, cy - z, 5, z + 2)); pygame.draw.circle(s, col, (cx, cy + z - 3), 5)
    elif kind == "rad":
        pygame.draw.circle(s, col, (cx, cy), z, 2); pygame.draw.circle(s, col, (cx, cy), 3)
        for a in (90, 210, 330):
            r = math.radians(a); pygame.draw.line(s, col, (cx, cy), (cx + math.cos(r) * z, cy - math.sin(r) * z), 2)
    elif kind == "bolt":
        pygame.draw.polygon(s, col, [(cx + 2, cy - z), (cx - z // 2, cy + 1), (cx, cy + 1), (cx - 2, cy + z), (cx + z // 2, cy - 1), (cx, cy - 1)])
    elif kind == "stam":
        for k in (-4, 3): pygame.draw.polygon(s, col, [(cx - 6, cy + k), (cx, cy + k - 5), (cx + 6, cy + k)], 2)
    else:
        pygame.draw.rect(s, col, (cx - z, cy - z, z * 2, z * 2), 2)
