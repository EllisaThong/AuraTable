from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent

def asset_root():
    os.chdir(ROOT)

def update_quality(state):
    welcome = state.get("welcome_score", 20 if state.get("order_choice") == "Spicy Bowl" else 15)
    state["quality_score"] = min(100, max(0, welcome + state.get("prep_score", 0) + round(state.get("cook_score", 0) * .75) + round(state.get("plate_score", 0) / 3)))
    return state["quality_score"]

def reset_from(state, scene):
    keys = ["prep_score", "cook_score", "plate_score"]
    for key in keys[keys.index(scene + "_score"):]:
        state[key] = 0
    if scene in ("prep", "cook"):
        state.pop("has_burned", None)
    update_quality(state)
