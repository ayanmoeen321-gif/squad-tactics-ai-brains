from collections import Counter

from engine.grid import load_level
from engine.state import new_game
from eval.compare import compare


def test_level4_loads_and_is_valid():
    load_level(4)  # parse_map checks size, unit counts, lava, and that every hero start reaches every monster start


def test_level4_units():
    state = new_game(4, 340)
    assert len(state.heroes()) == 3
    kinds = Counter(m.id.rsplit("_", 1)[0] for m in state.monsters())
    assert kinds == {"goblin": 3, "brute": 2, "archer": 2, "healer": 1}


def test_level4_can_be_played_headless():
    results = compare(["scripted"], None, seeds=[340], levels=(4,))
    assert len(results[("scripted", 4)]) >= 1