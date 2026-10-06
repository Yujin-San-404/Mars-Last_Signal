# MARS: LAST SIGNAL (prototype)

Install: `pip install pygame`  |  Run: `python main.py`  |  Developer keys: `python main.py --debug`
Headless self-test: `python tools/smoke_test.py`

## Controls
WASD move, SHIFT sprint, J interact/collect, K use selected item, Q/R select item, I inventory (transfer near storage or rover),
E contextual (enter/exit base, drive/exit rover, secondary station action), M map, TAB AI assistant (1-4 pick priority, 0 clear),
ESC menu, F5 quick save, F9 quick load. Debug (--debug): F3 overlay, F6 add items, F7 time warp, F8 refill, F10 storm, F11 next event.

## Goal
Repair comms (7 stages) -> contact Earth -> survive the rescue countdown (10 sols). Tune everything in `config.py`.
