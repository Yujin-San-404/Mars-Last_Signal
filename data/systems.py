"""Base systems, comm stages, crops and action costs."""
from config import EARTH_SIGNAL_DELAY

SYSTEMS = {
 "oxygen_gen": dict(name="Oxygen Generator", start=42, repair={"metal": 3, "electronic": 2},
                    effect="Makes breathable air. At 0 the base air runs out."),
 "water_recycler": dict(name="Water Recycler", start=60, repair={"metal": 2, "electronic": 1, "polymer": 2},
                        effect="Recovers drinking water. Never 100% efficient."),
 "solar": dict(name="Solar Array", start=75, repair={"solar_component": 1, "metal": 2, "copper": 1},
               effect="All base power. Night and dust storms cut it."),
 "heating": dict(name="Heating System", start=72, repair={"copper": 2, "metal": 1, "electronic": 1},
                 effect="Keeps the base livable at night."),
 "greenhouse": dict(name="Greenhouse Controls", start=60, repair={"polymer": 2, "glass": 2, "electronic": 1},
                    effect="Crop growth speed and climate."),
 "airlock": dict(name="Airlock Seals", start=55, repair={"metal": 2, "mechanical_parts": 1, "polymer": 1},
                 effect="Leaking seals bleed base oxygen."),
}
STAGES = [
 dict(name="Run diagnostics", kind="timed", time=10, power=15, sky=False, reqs={},
      done="Diagnostics: antenna array destroyed, power feed burnt out, transceiver needs calibration."),
 dict(name="Install antenna array", kind="repair", time=0, power=0, sky=False,
      reqs={"metal": 4, "copper": 2, "comm_component": 2, "tools": 1}, done="Antenna array installed."),
 dict(name="Restore power feed", kind="repair", time=0, power=40, sky=False,
      reqs={"electronic": 3, "copper": 2}, done="Comms power feed restored."),
 dict(name="Calibrate transceiver", kind="timed", time=25, power=30, sky=True,
      reqs={"calibrator": 2}, done="Transceiver calibrated."),
 dict(name="Establish uplink", kind="timed", time=30, power=35, sky=True, reqs={},
      done="Uplink to Earth relay established."),
 dict(name="Send emergency signal", kind="timed", time=10, power=30, sky=False, reqs={},
      done="Emergency signal transmitted. Waiting for Earth..."),
 dict(name="Await Earth confirmation", kind="auto", time=EARTH_SIGNAL_DELAY, power=20, sky=False, reqs={},
      done="Earth has responded."),
]
CROPS = {
 "seeds_potato": dict(name="Potato", sols=2.2, water=6, out=(3, 4), seed_back=0.45),
 "seeds_bean": dict(name="Beans", sols=1.5, water=4, out=(2, 3), seed_back=0.60),
 "seeds_lettuce": dict(name="Lettuce", sols=0.9, water=3, out=(1, 2), seed_back=0.30),
}
PLOT_UNLOCK = {"polymer": 2, "metal": 1}
PANEL_INSTALL = {"solar_component": 2, "metal": 1}
ROVER_REPAIR = {"metal": 2, "mechanical_parts": 1}
PROCESSOR_BUILD = {"electronic": 2, "mechanical_parts": 2, "metal": 2, "tools": 1}
PROCESS_COST = {"regolith": 3}
PROCESS_WATER = 4.0
COMM_FAULT_FIX = {"electronic": 1, "copper": 1}
LEAK_PATCH = {"polymer": 1}
