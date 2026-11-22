from brains.scripted_brain import ScriptedBrain
from engine.grid import load_level
from eval.runner import run_game


def test_level0_parses_with_four_goblins():
    grid = load_level(0)
    assert grid.rows == 12 and grid.cols == 12
    assert len(grid.monster_starts) == 4


def test_level0_plays_to_an_end():
    s = run_game(0, 5, ScriptedBrain(), "aggressive")
    assert s["outcome"] in ("win", "lose")