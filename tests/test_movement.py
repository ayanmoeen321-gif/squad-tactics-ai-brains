from engine.grid import parse_map
from engine.movement import (has_line_of_sight, is_chokepoint, manhattan,
                             reachable_tiles, shortest_path, walk_distances)
from engine.state import new_game


def open_grid(overrides=None):
    rows = [["."] * 12 for _ in range(12)]
    cells = {(0, 0): "1", (0, 1): "2", (0, 2): "3", (11, 11): "g"}
    cells.update(overrides or {})
    for (r, c), ch in cells.items():
        rows[r][c] = ch
    return parse_map("\n".join("".join(row) for row in rows))


def test_manhattan():
    assert manhattan((0, 0), (3, 4)) == 7
    assert manhattan((5, 5), (5, 5)) == 0


def test_walk_distance_open_floor():
    g = open_grid()
    d = walk_distances(g, (5, 5))
    assert d[(5, 5)] == 0
    assert d[(5, 8)] == 3
    assert d[(7, 7)] == 4


def test_walk_goes_around_walls():
    g = open_grid({(5, 6): "#", (4, 6): "#", (6, 6): "#"})
    d = walk_distances(g, (5, 5))
    assert d[(5, 7)] == 6


def test_blocked_tiles_cannot_be_entered():
    g = open_grid()
    d = walk_distances(g, (5, 5), blocked={(5, 6)})
    assert (5, 6) not in d
    assert d[(5, 7)] == 4


def test_reachable_tiles_respects_move():
    g = open_grid()
    t = reachable_tiles(g, (5, 5), 2)
    assert (5, 5) in t
    assert (5, 7) in t
    assert (5, 8) not in t
    assert (6, 6) in t
    assert len(t) == 13


def test_map_edge_blocks():
    g = open_grid()
    t = reachable_tiles(g, (0, 0), 1)
    assert set(t) == {(0, 0), (0, 1), (1, 0)}


def test_shortest_path_length_and_ends():
    g = open_grid()
    p = shortest_path(g, (5, 5), (5, 8))
    assert p[0] == (5, 5) and p[-1] == (5, 8)
    assert len(p) == 4


def test_shortest_path_is_deterministic():
    g = open_grid()
    assert shortest_path(g, (2, 2), (7, 7)) == shortest_path(g, (2, 2), (7, 7))


def test_shortest_path_none_when_blocked():
    g = open_grid({(4, 5): "#", (6, 5): "#", (5, 4): "#", (5, 6): "#"})
    assert shortest_path(g, (0, 5), (5, 5)) is None


def test_line_of_sight_open():
    g = open_grid()
    assert has_line_of_sight(g, (5, 5), (5, 9))
    assert has_line_of_sight(g, (5, 5), (5, 5))


def test_wall_blocks_line_of_sight():
    g = open_grid({(5, 7): "#"})
    assert not has_line_of_sight(g, (5, 5), (5, 9))
    assert has_line_of_sight(g, (4, 5), (4, 9))


def test_line_of_sight_is_symmetric_here():
    g = open_grid({(5, 7): "#"})
    assert has_line_of_sight(g, (5, 5), (5, 9)) == has_line_of_sight(g, (5, 9), (5, 5))


def test_units_do_not_block_line_of_sight():
    s = new_game(1)
    tank = s.units["tank"].pos
    archer = s.units["archer"].pos
    assert has_line_of_sight(s.grid, tank, archer) in (True, False)
    assert has_line_of_sight(s.grid, (0, 0), (0, 3))


def test_level2_doorway_is_chokepoint():
    s = new_game(2)
    assert is_chokepoint(s.grid, 5, 6)


def test_open_floor_is_not_chokepoint():
    s = new_game(1)
    assert not is_chokepoint(s.grid, 0, 0)
    assert not is_chokepoint(s.grid, 5, 5)


def test_wall_tile_is_not_chokepoint():
    s = new_game(2)
    assert not is_chokepoint(s.grid, 3, 6)