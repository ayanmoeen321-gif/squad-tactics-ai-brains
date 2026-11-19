from engine.movement import manhattan
from engine.options import legal_options, make_plan, planned_damage, wait_plan
from engine.state import new_game


def scene(level, alive):
    """alive: unit id -> (row, col). Every other unit is dead."""
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


def test_attack_advance_flank_with_closest_tile():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    opts = legal_options(s, s.units["goblin_1"], [])
    assert ids(opts) == ["attack_tank", "advance", "flank_tank"]
    assert by_id(opts, "attack_tank")["dest"] == (5, 6)
    assert by_id(opts, "advance")["dest"] == (5, 6)


def test_reserved_tile_is_avoided():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (11, 11), "tank": (5, 5)})
    plans = [plan("goblin_2", "attack_tank", "attack", "tank", (5, 6))]
    opts = legal_options(s, s.units["goblin_1"], plans)
    assert by_id(opts, "attack_tank")["dest"] == (4, 5)


def test_unplanned_ally_blocks_its_tile():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (5, 6), "tank": (5, 5)})
    opts = legal_options(s, s.units["goblin_1"], [])
    assert by_id(opts, "attack_tank")["dest"] == (4, 5)
    assert by_id(opts, "flank_tank")["dest"] == (4, 5)


def test_planned_ally_frees_its_tile():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (5, 6), "tank": (5, 5)})
    plans = [plan("goblin_2", "attack_tank", "attack", "tank", (6, 5))]
    opts = legal_options(s, s.units["goblin_1"], plans)
    assert by_id(opts, "attack_tank")["dest"] == (5, 6)


def test_overkill_block_removes_attack_option():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (6, 9),
                  "archer": (5, 5), "tank": (7, 8)})
    s.units["archer"].hp = 2
    free = legal_options(s, s.units["goblin_1"], [])
    assert "attack_archer" in ids(free)
    plans = [plan("goblin_2", "attack_archer", "attack", "archer", (5, 6))]
    blocked = legal_options(s, s.units["goblin_1"], plans)
    assert "attack_archer" not in ids(blocked)
    assert "attack_tank" in ids(blocked)


def test_planned_damage_counts_cover_for_ranged_only():
    s = scene(1, {"archer": (4, 5), "archer_1": (4, 9), "goblin_1": (4, 6)})
    plans = [plan("archer_1", "attack_archer", "attack", "archer", (4, 9)),
             plan("goblin_1", "attack_archer", "attack", "archer", (4, 6))]
    hero = s.units["archer"]
    assert planned_damage(s, hero, plans) == 4
    hero.pos = (5, 5)
    assert planned_damage(s, hero, plans) == 5


def test_no_advance_when_already_adjacent():
    s = scene(1, {"goblin_1": (5, 6), "tank": (5, 5)})
    opts = legal_options(s, s.units["goblin_1"], [])
    assert ids(opts) == ["attack_tank", "flank_tank"]


def test_ranged_monsters_do_not_flank():
    s = scene(1, {"archer_1": (5, 9), "tank": (5, 5)})
    opts = legal_options(s, s.units["archer_1"], [])
    assert ids(opts) == ["attack_tank", "advance"]
    assert by_id(opts, "attack_tank")["dest"] == (5, 9)


def test_hold_chokepoint_goes_to_the_doorway():
    s = scene(2, {"goblin_1": (5, 8), "tank": (5, 4)})
    opts = legal_options(s, s.units["goblin_1"], [])
    assert by_id(opts, "hold_chokepoint")["dest"] == (5, 6)


def test_never_ends_on_lava():
    s = scene(2, {"goblin_1": (8, 10), "tank": (8, 8)})
    s.grid.tiles[8][9] = "#"
    s.grid.tiles[9][8] = "#"
    opts = legal_options(s, s.units["goblin_1"], [])
    assert "attack_tank" not in ids(opts)
    assert "flank_tank" not in ids(opts)
    assert all(s.grid.tile(*o["dest"]) != "L" for o in opts)


def test_retreat_only_below_half_hp():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    g = s.units["goblin_1"]
    g.hp = 2
    assert "retreat" not in ids(legal_options(s, g, []))
    g.hp = 1
    assert "retreat" in ids(legal_options(s, g, []))


def test_retreat_moves_far_from_heroes():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    g = s.units["goblin_1"]
    g.hp = 1
    r = by_id(legal_options(s, g, []), "retreat")
    assert manhattan(r["dest"], (5, 5)) == 7
    assert r["steps"] <= 4


def test_protect_needs_a_weak_ally():
    s = scene(1, {"goblin_1": (3, 8), "brute_1": (5, 10), "tank": (5, 5)})
    g = s.units["goblin_1"]
    assert not any(i.startswith("protect") for i in ids(legal_options(s, g, [])))
    s.units["brute_1"].hp = 5
    assert "protect_brute_1" in ids(legal_options(s, g, []))


def test_protect_stands_between_ally_and_hero():
    s = scene(1, {"goblin_1": (3, 8), "archer_1": (5, 10), "tank": (5, 5)})
    opts = legal_options(s, s.units["goblin_1"], [])
    assert by_id(opts, "protect_archer_1")["dest"] == (5, 8)


def test_heal_lowest_hp_first_and_max_three():
    s = scene(2, {"healer_1": (5, 11), "goblin_1": (4, 8), "goblin_2": (5, 8),
                  "goblin_3": (6, 8), "brute_1": (3, 9), "tank": (5, 4)})
    s.units["goblin_1"].hp = 1
    s.units["goblin_2"].hp = 2
    s.units["goblin_3"].hp = 3
    s.units["brute_1"].hp = 5
    opts = legal_options(s, s.units["healer_1"], [])
    heals = [i for i in ids(opts) if i.startswith("heal_")]
    assert heals == ["heal_goblin_1", "heal_goblin_2", "heal_goblin_3"]


def test_heal_rules():
    s = scene(2, {"healer_1": (5, 11), "goblin_1": (5, 8), "tank": (5, 4)})
    healer, goblin = s.units["healer_1"], s.units["goblin_1"]
    assert not any(i.startswith("heal_") for i in ids(legal_options(s, healer, [])))
    goblin.hp = 2
    assert "heal_goblin_1" in ids(legal_options(s, healer, []))
    assert not any(i.startswith("heal_") for i in ids(legal_options(s, goblin, [])))
    healer.hp = 3
    assert "heal_healer_1" not in ids(legal_options(s, healer, []))


def test_option_order_is_fixed():
    s = scene(2, {"goblin_1": (5, 7), "archer_1": (5, 9), "tank": (5, 5)})
    g = s.units["goblin_1"]
    g.hp = 1
    assert ids(legal_options(s, g, [])) == [
        "attack_tank", "advance", "flank_tank",
        "hold_chokepoint", "protect_archer_1", "retreat"]


def test_boxed_in_monster_has_no_options():
    s = scene(1, {"goblin_1": (0, 0), "tank": (5, 5)})
    s.grid.tiles[0][1] = "#"
    s.grid.tiles[1][0] = "#"
    assert legal_options(s, s.units["goblin_1"], []) == []


def test_plan_records():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    g = s.units["goblin_1"]
    opt = legal_options(s, g, [])[0]
    assert make_plan(g, opt) == {"monster": "goblin_1", "option": "attack_tank",
                                 "kind": "attack", "target": "tank", "dest": (5, 6)}
    assert wait_plan(g) == {"monster": "goblin_1", "option": "wait", "kind": "wait",
                            "target": None, "dest": (5, 8)}