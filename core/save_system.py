import json, os
DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")

def _p(slot): return os.path.join(DIR, slot + ".json")
def exists(slot="save1"): return os.path.exists(_p(slot))

def save(data, slot="save1"):
    os.makedirs(DIR, exist_ok=True)
    tmp = _p(slot) + ".tmp"
    with open(tmp, "w") as f: json.dump(data, f)
    os.replace(tmp, _p(slot))

def load(slot="save1"):
    try:
        with open(_p(slot)) as f: return json.load(f)
    except (OSError, ValueError):
        return None
