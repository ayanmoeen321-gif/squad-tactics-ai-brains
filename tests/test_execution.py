from engine.execution import execute_round
from engine.state import MAX_ROUNDS, new_game


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


def test_valid_attack_plays_out():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    events, result = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert types(events) == ["move", "attack"]
    assert events[0]["to"] == (5, 6)
    assert s.units["goblin_1"].pos == (5, 6)
    assert s.units["tank"].hp == 18
    assert result is None
    assert "fallback" not in events[1]


def test_broken_plan_falls_back_to_nearest_hero_in_range():
    s = scene(1, {"goblin_1": (5, 8), "tank": (9, 5), "archer": (6, 6)})
    events, _ = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert types(events) == ["move", "attack"]
    assert events[1]["target"] == "archer" and events[1]["fallback"]
    assert s.units["archer"].hp == 8


def test_broken_plan_with_nobody_in_range_only_moves():
    s = scene(1, {"goblin_1": (5, 8), "tank": (9, 5)})
    events, _ = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert types(events) == ["move"]
    assert s.units["tank"].hp == 20


def test_same_target_still_in_range_is_kept():
    s = scene(1, {"goblin_1": (5, 8), "tank": (4, 6), "archer": (6, 6)})
    events, _ = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert events[-1]["target"] == "tank"
    assert "fallback" not in events[-1]
    assert s.units["archer"].hp == 10


def test_blocked_destination_stops_before_the_blocker():
    s = scene(1, {"goblin_1": (5, 9), "tank": (5, 7)})
    events, _ = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert s.units["goblin_1"].pos == (5, 8)
    assert events[-1]["type"] == "attack" and events[-1]["target"] == "tank"
    assert s.units["tank"].hp == 18


def test_monster_on_lava_takes_damage_at_end():
    s = scene(2, {"goblin_1": (7, 7), "tank": (0, 0)})
    events, result = execute_round(s, [plan("goblin_1", "wait", None, (7, 7))])
    assert types(events) == ["lava"]
    assert s.units["goblin_1"].hp == 1
    assert result is None


def test_execution_stops_when_all_heroes_are_dead():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (4, 8), "tank": (5, 5)})
    s.units["tank"].hp = 1
    plans = [plan("goblin_1", "attack", "tank", (5, 6)),
             plan("goblin_2", "attack", "tank", (4, 5))]
    events, result = execute_round(s, plans)
    assert result == "lose"
    assert s.units["goblin_2"].pos == (4, 8)
    assert [e["type"] for e in events].count("attack") == 1


def test_timeout_is_a_loss_only_at_round_30():
    s = scene(1, {"goblin_1": (5, 8), "tank": (0, 0)})
    s.round = MAX_ROUNDS - 1
    assert execute_round(s, [plan("goblin_1", "wait", None, (5, 8))])[1] is None
    s.round = MAX_ROUNDS
    assert execute_round(s, [plan("goblin_1", "wait", None, (5, 8))])[1] == "lose"


def test_dead_monster_plan_is_skipped():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    s.units["goblin_1"].hp = 0
    events, _ = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert events == []
    assert s.units["tank"].hp == 20


def test_monster_heal_plays_out():
    s = scene(2, {"healer_1": (5, 11), "goblin_1": (5, 9), "tank": (0, 0)})
    s.units["goblin_1"].hp = 1
    events, _ = execute_round(s, [plan("healer_1", "heal", "goblin_1", (5, 11))])
    assert types(events) == ["heal"]
    assert s.units["goblin_1"].hp == 4


def test_broken_heal_falls_back_to_attack():
    s = scene(2, {"healer_1": (5, 11), "goblin_1": (4, 11), "tank": (5, 8)})
    events, _ = execute_round(s, [plan("healer_1", "heal", "goblin_1", (5, 11))])
    assert types(events) == ["attack"]
    assert events[0]["fallback"]
    assert s.units["tank"].hp == 19


def test_monster_that_stays_put_has_no_move_event():
    s = scene(1, {"goblin_1": (5, 6), "tank": (5, 5)})
    events, _ = execute_round(s, [plan("goblin_1", "attack", "tank", (5, 6))])
    assert types(events) == ["attack"]