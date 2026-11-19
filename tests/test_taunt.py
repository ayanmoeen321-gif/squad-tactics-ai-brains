import pytest

from engine.combat import ActionError
from engine.execution import execute_round
from engine.movement import manhattan
from engine.player import PlayerPhase
from engine.state import new_game


def scene(level, alive):
    s = new_game(level)
    for u in s.units.values():
        if u.id in alive:
            u.pos = alive[u.id]
        else:
            u.hp = 0
    return s


def adv(monster, dest):
    return {"monster": monster, "option": "advance", "kind": "advance",
            "target": None, "dest": dest}


def test_monster_in_radius_switches_to_attack_the_tank():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8)})
    plans = [adv("goblin_1", (5, 7))]
    events = PlayerPhase(s, plans).taunt("tank")
    assert events == [{"type": "taunt", "unit": "tank", "affected": ["goblin_1"]}]
    assert plans[0]["kind"] == "attack" and plans[0]["target"] == "tank"
    assert plans[0]["dest"] == (5, 6) and plans[0]["taunted"]
    assert s.units["tank"].cooldown == 3


def test_monster_outside_radius_keeps_its_plan():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8), "goblin_2": (5, 9)})
    plans = [adv("goblin_1", (5, 7)), adv("goblin_2", (5, 8))]
    PlayerPhase(s, plans).taunt("tank")
    assert plans[0]["taunted"]
    assert plans[1] == adv("goblin_2", (5, 8))


def test_monster_that_cannot_reach_the_tank_keeps_its_plan():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8), "goblin_2": (11, 11)})
    for c in range(5, 9):
        s.grid.tiles[4][c] = "#"
        s.grid.tiles[6][c] = "#"
    s.grid.tiles[5][4] = "#"
    plans = [adv("goblin_1", (5, 7)), adv("goblin_2", (5, 6))]
    before = [dict(p) for p in plans]
    events = PlayerPhase(s, plans).taunt("tank")
    assert events[0]["affected"] == []
    assert plans == before


def test_two_taunted_monsters_get_different_tiles_next_to_the_tank():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8), "goblin_2": (4, 7)})
    plans = [adv("goblin_1", (5, 7)), adv("goblin_2", (4, 6))]
    PlayerPhase(s, plans).taunt("tank")
    dests = [p["dest"] for p in plans]
    assert len(set(dests)) == 2
    assert all(manhattan(d, (5, 5)) == 1 for d in dests)
    assert all(p["kind"] == "attack" and p["target"] == "tank" for p in plans)


def test_ranged_monster_attacks_from_where_it_stands():
    s = scene(1, {"tank": (5, 5), "archer_1": (5, 8)})
    plans = [adv("archer_1", (5, 7))]
    PlayerPhase(s, plans).taunt("tank")
    assert plans[0]["kind"] == "attack" and plans[0]["dest"] == (5, 8)


def test_dead_monsters_plan_is_left_alone():
    s = scene(1, {"tank": (5, 5)})
    plans = [adv("goblin_1", (5, 7))]
    events = PlayerPhase(s, plans).taunt("tank")
    assert events[0]["affected"] == []
    assert plans == [adv("goblin_1", (5, 7))]


def test_taunt_uses_the_tanks_position_after_moving():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 8)})
    plans = [adv("goblin_1", (5, 9))]
    p = PlayerPhase(s, plans)
    p.move("tank", (5, 6))
    events = p.taunt("tank")
    assert events[0]["affected"] == ["goblin_1"]
    assert plans[0]["dest"] == (5, 7)


def test_taunt_uses_the_action_and_cannot_repeat():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8)})
    p = PlayerPhase(s, [adv("goblin_1", (5, 7))])
    p.taunt("tank")
    with pytest.raises(ActionError):
        p.taunt("tank")
    with pytest.raises(ActionError):
        p.attack("tank", "goblin_1")
    with pytest.raises(ActionError):
        p.move("tank", (5, 4))


def test_taunt_respects_cooldown():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8)})
    s.units["tank"].cooldown = 2
    with pytest.raises(ActionError):
        PlayerPhase(s, [adv("goblin_1", (5, 7))]).taunt("tank")


def test_only_the_tank_can_taunt():
    s = scene(1, {"tank": (5, 5), "archer": (5, 3), "goblin_1": (5, 8)})
    with pytest.raises(ActionError):
        PlayerPhase(s, [adv("goblin_1", (5, 7))]).taunt("archer")


def test_taunted_plan_plays_out_in_execution():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8)})
    plans = [adv("goblin_1", (5, 7))]
    PlayerPhase(s, plans).taunt("tank")
    events, result = execute_round(s, plans)
    assert [e["type"] for e in events] == ["move", "attack"]
    assert s.units["goblin_1"].pos == (5, 6)
    assert s.units["tank"].hp == 18
    assert result is None