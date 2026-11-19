import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def load_heroes():
    return _load("heroes.json")


def load_monsters():
    return _load("monsters.json")