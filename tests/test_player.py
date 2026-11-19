import pytest

from engine.combat import ActionError
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


def reserve(monster, dest):
    return {"monster": monster, "option": "advance", "kind": "advance",
            "target": None, "dest": dest}


def test_move_within_range_only():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    p = PlayerPhase(s, [])
    assert (5, 3) not in p.reachable("tank")
    assert (5, 6) in p.reachable("tank")
    assert (5, 7) not in p.reachable("tank")
    events = p.move("tank", (5, 6))
    assert events == [{"type": "move", "unit": "tank", "from": (5, 3), "to": (5, 6)}]
    assert s.units["tank"].pos == (5, 6)


def test_cannot_move_onto_a_unit():
    s = scene(1, {"tank": (5, 3), "archer": (4, 1), "goblin_1": (5, 9)})
    with pytest.raises(ActionError):
        PlayerPhase(s, []).move("tank", (4, 1))


def test_reserved_tile_is_blocked_until_that_monster_dies():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    p = PlayerPhase(s, [reserve("goblin_1", (5, 5))])
    assert (5, 4) in p.reachable("tank")
    assert (5, 5) not in p.reachable("tank")
    s.units["goblin_1"].hp = 0
    assert (5, 5) in p.reachable("tank")


def test_reserved_tile_blocks_the_path():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    p = PlayerPhase(s, [reserve("goblin_1", (5, 4))])
    assert (5, 5) not in p.reachable("tank")


def test_cannot_move_twice():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    p = PlayerPhase(s, [])
    p.move("tank", (5, 4))
    with pytest.raises(ActionError):
        p.move("tank", (5, 5))


def test_cannot_move_after_acting():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    p = PlayerPhase(s, [])
    p.wait("tank")
    with pytest.raises(ActionError):
        p.move("tank", (5, 4))


def test_undo_restores_position_and_allows_a_new_move():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    p = PlayerPhase(s, [])
    p.move("tank", (5, 5))
    p.undo("tank")
    assert s.units["tank"].pos == (5, 3)
    p.move("tank", (6, 3))
    assert s.units["tank"].pos == (6, 3)


def test_undo_not_allowed_after_attack():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 5)})
    p = PlayerPhase(s, [])
    p.move("tank", (5, 4))
    p.attack("tank", "goblin_1")
    with pytest.raises(ActionError):
        p.undo("tank")
    assert s.units["tank"].pos == (5, 4)


def test_undo_without_a_move_raises():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    with pytest.raises(ActionError):
        PlayerPhase(s, []).undo("tank")


def test_attack_out_of_range_raises_and_hero_can_still_act():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    p = PlayerPhase(s, [])
    with pytest.raises(ActionError):
        p.attack("tank", "goblin_1")
    assert not p.status["tank"]["acted"]
    p.wait("tank")


def test_one_action_per_turn():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 4), "goblin_2": (4, 3)})
    p = PlayerPhase(s, [])
    p.attack("tank", "goblin_1")
    with pytest.raises(ActionError):
        p.attack("tank", "goblin_2")


def test_killing_the_last_monster_is_a_win():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 4)})
    p = PlayerPhase(s, [])
    events = p.attack("tank", "goblin_1")
    assert events[0]["killed"]
    assert p.result() == "win"


def test_cannot_attack_an_ally():
    s = scene(1, {"tank": (5, 3), "archer": (5, 4), "goblin_1": (5, 9)})
    with pytest.raises(ActionError):
        PlayerPhase(s, []).attack("tank", "archer")


def test_piercing_shot_uses_the_action_and_cooldown():
    s = scene(1, {"archer": (1, 1), "goblin_1": (1, 3)})
    p = PlayerPhase(s, [])
    events = p.piercing_shot("archer", "right")
    assert len(events) == 1 and events[0]["killed"]
    assert s.units["archer"].cooldown == 3
    with pytest.raises(ActionError):
        p.piercing_shot("archer", "right")


def test_hero_heal_uses_the_action():
    s = scene(1, {"tank": (5, 3), "healer": (6, 1), "goblin_1": (5, 9)})
    s.units["tank"].hp = 10
    p = PlayerPhase(s, [])
    events = p.heal("healer", "tank")
    assert events[0]["restored"] == 5
    assert s.units["tank"].hp == 15
    with pytest.raises(ActionError):
        p.wait("healer")


def test_end_applies_lava_to_heroes():
    s = scene(2, {"tank": (7, 7), "goblin_1": (0, 0)})
    events, result = PlayerPhase(s, []).end()
    assert [e["type"] for e in events] == ["lava"]
    assert s.units["tank"].hp == 17
    assert result is None


def test_dead_hero_cannot_act():
    s = scene(1, {"tank": (5, 3), "goblin_1": (5, 9)})
    s.units["archer"].hp = 0
    with pytest.raises(ActionError):
        PlayerPhase(s, []).move("archer", (4, 2))