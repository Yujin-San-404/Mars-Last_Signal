"""Central balance/tuning file for MARS: LAST SIGNAL. Every gameplay number lives here."""
SCREEN_W, SCREEN_H = 1100, 700
FPS = 60
TITLE = "MARS: LAST SIGNAL"

# ---- world (1 px = PX_TO_M metres, display only) ----
WORLD_SEED = 1977
WORLD_SIZE = 14000
BASE_POS = (7000, 7000)
PX_TO_M = 0.5
SAFE_RANGE = 4500      # beyond this the suit-return warning starts and O2 drain climbs
MAX_RANGE = 6400       # beyond this survival is nearly impossible
WORLD_RADIUS = 6900    # hard terrain limit

# ---- time (compressed Martian sol) ----
SOL_LENGTH = 300.0     # real seconds per sol
START_HOUR = 8.0
DAWN, DUSK = 6.0, 18.0
TIME_WARP = 8          # debug only
RESCUE_SOLS = 10
EARTH_SIGNAL_DELAY = 75.0

# ---- player / inventory ----
PLAYER_INVENTORY_CAPACITY = 25.0
ROVER_INVENTORY_CAPACITY = 100.0
BASE_STORAGE_CAPACITY = 250.0
PLAYER_SPEED = 150.0
SPRINT_MULT = 1.55
WEIGHT_SLOWDOWN = 0.30
PLAYER_RADIUS = 11

# ---- survival (per second) ----
OXYGEN_CONSUMPTION_RATE = 0.30     # % per second walking, empty hands, at base
OXY_REST, OXY_WALK, OXY_SPRINT = 0.6, 1.0, 1.6
HUNGER_RATE = 100.0 / (3.5 * SOL_LENGTH)
WATER_RATE = 100.0 / (2.5 * SOL_LENGTH)
OUTSIDE_THIRST_MULT = 1.15
COLD_FREE = 20.0                   # degC below zero that the suit tolerates for free
COLD_RATE = 0.0047
RADIATION_RATE = 0.04
RADIATION_RECOVER = 0.015
RADIATION_INSIDE = 0.002
STAMINA_SPRINT_DRAIN = 18.0
STAMINA_REGEN = 10.0
STARVE_DMG, DEHYDRATE_DMG, SUFFOCATE_DMG = 0.35, 0.6, 7.0
COLD_DMG, RADIATION_DMG, HEALTH_REGEN = 0.5, 0.15, 0.08
FOOD_RATION_HUNGER, PRODUCE_HUNGER = 40.0, 22.0
WATER_CANISTER_L = 5.0
MEDICAL_HEAL, MEDICAL_RAD = 40.0, 15.0
OXYGEN_TANK_REFILL = 60.0

# ---- rover ----
ROVER_SPEED = 330.0
ROVER_BATTERY_DRAIN = 0.9          # % per second while driving
ROVER_CHARGE_RATE = 4.0            # % per second at base
ROVER_CHARGE_LOAD = 3.0            # base power units/s while charging
ROVER_O2_FACTOR, ROVER_RAD_FACTOR, ROVER_COLD_FACTOR = 0.55, 0.5, 0.3

# ---- base ----
BATTERY_CAP = 600.0
PANEL_PEAK = 3.0
MAX_PANELS = 8
SOLAR_STORM_LOSS = 0.85
LOAD_O2, LOAD_WATER, LOAD_GREENHOUSE, LOAD_PLOT, LOAD_COMMS, LOAD_LIGHTS = 0.6, 0.35, 0.25, 0.15, 0.2, 0.15
TARGET_TEMP = 18.0
BASE_O2_PROD, BASE_O2_USE, BASE_O2_LEAK = 0.22, 0.10, 0.05
SUIT_REFILL_RATE = 4.0
BASE_O2_PER_SUIT_PCT = 0.08
TANK_CAP, START_TANK = 120.0, 40.0
WATER_RECYCLE_RATE = 0.06
RECYCLE_BASE_EFF, RECYCLE_SCALE = 0.50, 0.35   # never 100% efficient
PCT_PER_LITER = 8.0
SYSTEM_WEAR = 0.008                # integrity % lost per second
MAX_PLOTS, START_PLOTS = 8, 4

# ---- events ----
EVENT_INTERVAL = (70.0, 130.0)
EVENT_MIN_INTERVAL = 40.0
