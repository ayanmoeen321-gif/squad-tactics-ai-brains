from brains.scripted_brain import ScriptedBrain
from engine.grid import load_level
from eval.runner import run_game


def test_level0_parses_with_two_goblins():
    grid = load_level(0)
    assert grid.rows == 12 and grid.cols == 12
    assert [k for k, _ in grid.monster_starts] == ["g", "g"] or \
        [k for k, _ in grid.monster_starts] == ["goblin", "goblin"]


def test_level0_plays_to_an_end():
    s = run_game(0, 5, ScriptedBrain(), "aggressive")
    assert s["outcome"] in ("win", "lose")