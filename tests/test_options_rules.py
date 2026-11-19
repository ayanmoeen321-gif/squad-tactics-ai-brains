from engine.options import legal_options
from engine.state import new_game


def scene(level, alive):
    s = new_game(level)
    for u in s.units.values():
        if u.id in alive:
            u.pos = alive[u.id]
        else:
            u.hp = 0
    return s


def plan(monster, option, kind, target, dest):
    return {"monster": monster, "option": option, "kind": kind,
            "target": target, "dest": dest}


def ids(options):
    return [o["id"] for o in options]


def by_id(options, oid):
    return next(o for o in options if o["id"] == oid)


def wall_column(s, col, rows=range(12), gap_row=None):
    for r in rows:
        if r != gap_row:
            s.grid.tiles[r][col] = "#"


def test_protect_cap_is_two_lowest_hp_then_lower_number():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (3, 9), "brute_1": (5, 10),
                  "archer_1": (7, 9), "tank": (5, 5)})
    s.units["goblin_2"].hp = 1
    s.units["brute_1"].hp = 5
    opts = legal_options(s, s.units["goblin_1"], [])
    protects = [i for i in ids(opts) if i.startswith("protect_")]
    assert protects == ["protect_goblin_2", "protect_brute_1"]


def test_flank_never_uses_the_current_tile():
    s = scene(1, {"goblin_1": (5, 6), "tank": (5, 5)})
    opts = legal_options(s, s.units["goblin_1"], [])
    assert by_id(opts, "attack_tank")["dest"] == (5, 6)
    assert by_id(opts, "flank_tank")["dest"] != (5, 6)


def test_ranged_attack_needs_line_of_sight_from_the_tile():
    open_s = scene(1, {"archer_1": (5, 9), "tank": (5, 5)})
    assert "attack_tank" in ids(legal_options(open_s, open_s.units["archer_1"], []))
    walled = scene(1, {"archer_1": (5, 9), "tank": (5, 5)})
    wall_column(walled, 7, rows=range(3, 8))
    assert "attack_tank" not in ids(legal_options(walled, walled.units["archer_1"], []))


def test_reserved_tile_blocks_the_path_not_only_the_destination():
    def build():
        s = scene(1, {"goblin_1": (5, 9), "goblin_2": (11, 11), "tank": (5, 5)})
        wall_column(s, 7, gap_row=5)
        return s

    free = build()
    free_opts = legal_options(free, free.units["goblin_1"], [])
    assert by_id(free_opts, "attack_tank")["dest"] == (5, 6)

    s = build()
    plans = [plan("goblin_2", "advance", "advance", None, (5, 7))]
    opts = legal_options(s, s.units["goblin_1"], plans)
    assert "attack_tank" not in ids(opts)
    assert by_id(opts, "advance")["dest"] == (5, 8)