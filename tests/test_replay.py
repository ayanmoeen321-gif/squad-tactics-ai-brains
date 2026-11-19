import pytest

from engine.render import render
from engine.replay import random_playout
from engine.state import new_game


def test_render_size():
    lines = render(new_game(1)).splitlines()
    assert len(lines) == 12
    assert all(len(line) == 12 for line in lines)


def test_render_counts():
    text = render(new_game(1))
    assert (text.count("g"), text.count("b"), text.count("a")) == (3, 1, 1)
    assert all(text.count(ch) == 1 for ch in "123")


def test_render_hides_dead_units():
    s = new_game(1)
    s.units["tank"].hp = 0
    assert "1" not in render(s)


def test_render_shows_lava():
    assert "L" in render(new_game(2))


def test_same_seed_same_game():
    assert random_playout(1, seed=5) == random_playout(1, seed=5)


def test_different_seed_different_game():
    assert random_playout(1, seed=1) != random_playout(1, seed=2)


@pytest.mark.parametrize("n", [1, 2, 3])
def test_replay_on_every_level(n):
    assert random_playout(n, seed=11) == random_playout(n, seed=11)