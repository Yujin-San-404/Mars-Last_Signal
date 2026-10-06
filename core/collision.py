"""Circle-vs-circle / circle-vs-rect push-out used by every moving thing."""
import math

def resolve(pos, r, circles=(), rects=()):
    hit = False
    for cx, cy, cr in circles:
        dx, dy = pos[0] - cx, pos[1] - cy
        d2 = dx * dx + dy * dy
        mn = r + cr
        if d2 < mn * mn:
            if d2 == 0:
                dx, dy, d = 1.0, 0.0, 1.0
            else:
                d = math.sqrt(d2)
            pos[0] = cx + dx / d * mn
            pos[1] = cy + dy / d * mn
            hit = True
    for rc in rects:
        px = min(max(pos[0], rc.left), rc.right)
        py = min(max(pos[1], rc.top), rc.bottom)
        dx, dy = pos[0] - px, pos[1] - py
        d2 = dx * dx + dy * dy
        if d2 < r * r:
            if d2 > 0:
                d = math.sqrt(d2)
                pos[0] = px + dx / d * r
                pos[1] = py + dy / d * r
            else:
                m = min(pos[0] - rc.left, rc.right - pos[0], pos[1] - rc.top, rc.bottom - pos[1])
                if m == pos[0] - rc.left: pos[0] = rc.left - r
                elif m == rc.right - pos[0]: pos[0] = rc.right + r
                elif m == pos[1] - rc.top: pos[1] = rc.top - r
                else: pos[1] = rc.bottom + r
            hit = True
    return hit
