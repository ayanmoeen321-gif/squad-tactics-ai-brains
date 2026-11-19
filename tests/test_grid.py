from collections import Counter

import pytest

from engine.grid import MapError, load_level, parse_map

COUNTS = {
    1: {"goblin": 3, "brute": 1, "archer": 1},
    2: {"goblin": 3, "brute": 2, "archer": 2, "healer": 1},
    3: {"goblin": 4, "brute": 2, "archer": 3, "healer": 1},
}


def make_map(overrides=None):
    rows = [["."] * 12 for _ in range(12)]
    cells = {(0, 0): "1", (0, 1): "2", (0, 2): "3", (11, 11): "g"}
    cells.update(overrides or {})
    for (r, c), ch in cells.items():
        rows[r][c] = ch
    return "\n".join("".join(row) for row in rows)


@pytest.mark.parametrize("n", [1, 2, 3])
def test_level_is_12x12(n):
    g = load_level(n)
    assert (g.rows, g.cols) == (12, 12)


@pytest.mark.parametrize("n", [1, 2, 3])
def test_monster_counts(n):
    g = load_level(n)
    assert Counter(t for t, _ in g.monster_starts) == Counter(COUNTS[n])


@pytest.mark.parametrize("n", [1, 2, 3])
def test_hero_starts(n):
    g = load_level(n)
    assert set(g.hero_starts) == {"tank", "archer", "healer"}
    for r, c in g.hero_starts.values():
        assert g.in_bounds(r, c)
        assert g.tile(r, c) == "."


def test_level1_has_no_lava():
    g = load_level(1)
    assert all(ch != "L" for row in g.tiles for ch in row)


def test_level2_lava_count():
    g = load_level(2)
    assert sum(ch == "L" for row in g.tiles for ch in row) == 3


def test_monster_order_is_reading_order():
    g = load_level(1)
    positions = [p for _, p in g.monster_starts]
    assert positions == sorted(positions)


def test_walkable_rules():
    g = load_level(1)
    assert g.is_walkable(0, 0)
    assert not g.is_walkable(2, 6)
    assert not g.is_walkable(-1, 0)
    assert not g.is_walkable(12, 5)


def test_bad_size():
    with pytest.raises(MapError):
        parse_map("....\n....")


def test_unknown_symbol():
    with pytest.raises(MapError):
        parse_map(make_map({(5, 5): "X"}))


def test_missing_hero():
    with pytest.raises(MapError):
        parse_map(make_map({(0, 2): "."}))


def test_duplicate_hero():
    with pytest.raises(MapError):
        parse_map(make_map({(0, 3): "1"}))


def test_unreachable_monster():
    with pytest.raises(MapError):
        parse_map(make_map({(10, 11): "#", (11, 10): "#"}))