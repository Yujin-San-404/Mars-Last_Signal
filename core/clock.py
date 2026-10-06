"""Martian sol clock: day/night, daylight and ambient temperature."""
import math
from config import SOL_LENGTH, START_HOUR, DAWN, DUSK

class Clock:
    def __init__(self, t=None):
        self.t = SOL_LENGTH * START_HOUR / 24.0 if t is None else t

    @property
    def sol(self):
        return int(self.t // SOL_LENGTH) + 1

    @property
    def hour(self):
        return (self.t % SOL_LENGTH) / SOL_LENGTH * 24.0

    def time_str(self):
        h = self.hour
        return f"{int(h):02d}:{int((h % 1) * 60):02d}"

    def daylight(self):
        x = (self.hour - DAWN) / (DUSK - DAWN)
        return max(0.0, math.sin(math.pi * x)) ** 0.6 if 0 <= x <= 1 else 0.0

    def ambient(self):
        """Roughly -90C before dawn, -10C mid-afternoon."""
        return -50.0 + 40.0 * math.sin(2 * math.pi * (self.hour - 9.0) / 24.0)
