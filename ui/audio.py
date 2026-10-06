"""Tiny synthesized beeps (no asset files). Silently disabled if the mixer is unavailable."""
import array, math
import pygame
enabled, _ok, _cache = True, False, {}

def init():
    global _ok
    try:
        pygame.mixer.init(22050, -16, 1, 512); _ok = True
    except Exception:
        _ok = False

def beep(freq=660, ms=110, vol=0.2):
    if not (_ok and enabled): return
    try:
        k = (freq, ms)
        if k not in _cache:
            n = int(22050 * ms / 1000)
            a = array.array("h", [int(32767 * math.sin(2 * math.pi * freq * i / 22050) * (1 - i / n)) for i in range(n)])
            _cache[k] = pygame.mixer.Sound(buffer=a.tobytes())
        snd = _cache[k]; snd.set_volume(vol); snd.play()
    except Exception:
        pass
