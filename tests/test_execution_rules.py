from engine.execution import execute_round
from engine.state import new_game


def scene(level, alive):
    s = new_game(level)
    for u in s.units.values():
        if u.id in alive:
            u.pos = alive[u.id]
        else:
            u.hp = 0
    return s


def plan(monster, kind, target, dest):
    option = f"{kind}_{target}" if target else kind
    return {"monster": monster, "option": option, "kind": kind,
            "target": target, "dest": dest}


def types(events):
    return [e["type"] for e in events]


def corridor(s):
    for c in range(6, 12):
        s.grid.tiles[4][c] = "#"
        s.grid.tiles[6][c] = "#"


def test_heal_on_dead_target_never_hits_an_ally():
    s = scene(2, {"healer_1": (5, 11), "tank": (0, 0)})
    events, _ = execute_round(s, [plan("healer_1", "heal", "goblin_1", (5, 11))])
    assert events == []


def test_heal_on_out_of_range_target_does_nothing():
    s = scene(2, {"healer_1": (5, 11), "goblin_1": (5, 6), "tank": (0, 0)})
    s.units["goblin_1"].hp = 1
    events, _ = execute_round(s, [plan("healer_1", "heal", "goblin_1", (5, 11))])
    assert events == []
    assert s.units["goblin_1"].hp == 1


def test_heal_on_full_hp_ally_does_nothing_without_a_hero_in_range():
    s = scene(2, {"healer_1": (5, 11), "goblin_1": (5, 9), "tank": (0, 0)})
    events, _ = execute_round(s, [plan("healer_1", "heal", "goblin_1", (5, 11))])
    assert events == []
    assert s.units["goblin_1"].hp == 4


def test_blocked_path_then_target_out_of_range_hits_nearest_hero():
    s = scene(1, {"goblin_1": (5, 10), "tank": (5, 5), "archer": (5, 8)})
    corridor(s)
    events, _ = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert s.units["goblin_1"].pos == (5, 9)
    assert types(events) == ["move", "attack"]
    assert events[1]["target"] == "archer" and events[1]["fallback"]
    assert s.units["archer"].hp == 8
    assert s.units["tank"].hp == 20


def test_earlier_monster_stopped_short_blocks_a_later_one():
    s = scene(1, {"goblin_1": (5, 10), "goblin_2": (5, 11),
                  "tank": (5, 5), "archer": (5, 8)})
    corridor(s)
    plans = [plan("goblin_1", "attack", "tank", (5, 6)),
             plan("goblin_2", "attack", "archer", (5, 9))]
    execute_round(s, plans)
    assert s.units["goblin_1"].pos == (5, 9)
    assert s.units["goblin_2"].pos == (5, 10)


def test_lava_killing_the_last_monster_is_a_win():
    s = scene(2, {"goblin_1": (7, 7), "tank": (0, 0)})
    s.units["goblin_1"].hp = 1
    events, result = execute_round(s, [plan("goblin_1", "wait", None, (7, 7))])
    assert types(events) == ["lava"] and events[0]["killed"]
    assert result == "win"


def test_no_lava_after_an_early_loss():
    s = scene(2, {"goblin_1": (5, 8), "goblin_2": (7, 7), "tank": (5, 5)})
    s.units["tank"].hp = 1
    plans = [plan("goblin_1", "attack", "tank", (5, 6)),
             plan("goblin_2", "wait", None, (7, 7))]
    events, result = execute_round(s, plans)
    assert result == "lose"
    assert "lava" not in types(events)
    assert s.units["goblin_2"].hp == 4