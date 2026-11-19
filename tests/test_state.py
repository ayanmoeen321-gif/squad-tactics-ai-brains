import pytest

from engine.state import new_game


def test_level1_units():
    s = new_game(1)
    assert len(s.heroes()) == 3
    assert len(s.monsters()) == 5


@pytest.mark.parametrize("n,total", [(1, 5), (2, 8), (3, 10)])
def test_monster_totals(n, total):
    assert len(new_game(n).monsters()) == total


def test_hero_stats_from_data():
    s = new_game(1)
    assert s.units["tank"].hp == 20
    assert s.units["archer"].range == 4
    assert s.units["healer"].skill["amount"] == 5


def test_monster_ids_labels_and_order():
    s = new_game(2)
    ms = sorted(s.monsters(), key=lambda u: u.order)
    assert [m.order for m in ms] == list(range(1, 9))
    assert s.units["goblin_1"].label == "Goblin 1"
    assert s.units["goblin_3"].label == "Goblin 3"
    assert s.units["healer_1"].heal == {"amount": 3, "range": 3}


def test_unit_at_and_occupied():
    s = new_game(1)
    tank = s.units["tank"]
    assert s.unit_at(tank.pos) is tank
    assert s.unit_at((0, 0)) is None
    assert tank.pos in s.occupied()
    assert len(s.occupied()) == 8


def test_dead_units_free_their_tile():
    s = new_game(1)
    tank = s.units["tank"]
    tank.hp = 0
    assert not tank.alive
    assert s.unit_at(tank.pos) is None
    assert len(s.heroes()) == 2


def test_copy_is_independent():
    s = new_game(1)
    c = s.copy()
    c.units["tank"].hp = 1
    c.units["tank"].pos = (0, 0)
    c.round = 9
    assert s.units["tank"].hp == 20
    assert s.units["tank"].pos != (0, 0)
    assert s.round == 1


def test_copy_shares_grid():
    s = new_game(1)
    assert s.copy().grid is s.grid


def test_same_seed_same_random_numbers():
    a = new_game(1, seed=7)
    b = new_game(1, seed=7)
    assert [a.rng.random() for _ in range(5)] == [b.rng.random() for _ in range(5)]


def test_copy_continues_the_random_stream():
    s = new_game(1, seed=3)
    s.rng.random()
    c = s.copy()
    assert s.rng.random() == c.rng.random()