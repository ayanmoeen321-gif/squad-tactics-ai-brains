import pytest

from brains.scripted_brain import ScriptedBrain
from engine.game import Game
from engine.movement import manhattan
from engine.options import legal_options
from engine.planning import plan_round
from engine.state import new_game


def scene(level, alive):
    s = new_game(level)
    for u in s.units.values():
        if u.id in alive:
            u.pos = alive[u.id]
        else:
            u.hp = 0
    return s


def choose(s, monster_id, plans=()):
    m = s.units[monster_id]
    plans = list(plans)
    return ScriptedBrain().choose(s, m, legal_options(s, m, plans), plans)


def atk(monster, target, dest):
    return {"monster": monster, "option": f"attack_{target}", "kind": "attack",
            "target": target, "dest": dest}


def test_attacks_lowest_hp_hero_in_reach():
    s = scene(1, {"goblin_1": (5, 7), "tank": (5, 5), "archer": (6, 8)})
    assert choose(s, "goblin_1") == "attack_archer"


def test_focuses_a_hero_earlier_plans_attack():
    s = scene(1, {"goblin_1": (5, 7), "goblin_2": (4, 7),
                  "tank": (5, 5), "archer": (6, 8)})
    assert choose(s, "goblin_1", [atk("goblin_2", "tank", (4, 5))]) == "attack_tank"


def test_finishing_a_kill_beats_focus():
    s = scene(1, {"goblin_1": (5, 7), "goblin_2": (4, 7),
                  "tank": (5, 5), "archer": (6, 8)})
    s.units["archer"].hp = 2
    assert choose(s, "goblin_1", [atk("goblin_2", "tank", (4, 5))]) == "attack_archer"


def test_archer_retreats_when_hurt():
    s = scene(1, {"archer_1": (5, 9), "tank": (5, 5)})
    s.units["archer_1"].hp = 2
    assert choose(s, "archer_1") == "retreat"


def test_hurt_goblin_does_not_retreat():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    s.units["goblin_1"].hp = 1
    assert "retreat" in [o["id"] for o in legal_options(s, s.units["goblin_1"], [])]
    assert choose(s, "goblin_1") == "attack_tank"


def test_heal_uses_absolute_hp_then_map_order():
    s = scene(2, {"healer_1": (5, 11), "goblin_1": (5, 9), "goblin_2": (6, 9),
                  "brute_1": (4, 10), "tank": (5, 1)})
    s.units["goblin_1"].hp = 3
    s.units["goblin_2"].hp = 3
    s.units["brute_1"].hp = 5
    assert choose(s, "healer_1") == "heal_goblin_1"


def test_brute_holds_the_chokepoint_when_it_cannot_attack():
    s = scene(2, {"brute_1": (5, 8), "tank": (5, 1)})
    assert choose(s, "brute_1") == "hold_chokepoint"


def test_goblin_advances_when_it_cannot_attack_or_flank():
    s = scene(2, {"goblin_1": (5, 11), "tank": (5, 1)})
    assert choose(s, "goblin_1") == "advance"


def test_flank_is_chosen_when_attack_is_blocked_by_overkill():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (4, 8), "tank": (5, 5)})
    s.units["tank"].hp = 2
    ids = [o["id"] for o in legal_options(s, s.units["goblin_1"],
                                          [atk("goblin_2", "tank", (4, 5))])]
    assert "attack_tank" not in ids and "flank_tank" in ids
    assert choose(s, "goblin_1", [atk("goblin_2", "tank", (4, 5))]) == "flank_tank"


def test_two_melee_monsters_use_different_flank_tiles():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (4, 8), "tank": (5, 5)})
    s.units["tank"].hp = 2
    plans = plan_round(s, ScriptedBrain())
    assert [p["kind"] for p in plans] == ["attack", "flank"]
    assert plans[0]["dest"] != plans[1]["dest"]
    assert all(manhattan(p["dest"], (5, 5)) == 1 for p in plans)


def test_last_resort_takes_the_first_option():
    s = scene(1, {"goblin_1": (5, 8), "tank": (5, 5)})
    only = [{"id": "protect_archer_1", "kind": "protect", "target": "archer_1",
             "dest": (5, 8), "steps": 0}]
    assert ScriptedBrain().choose(s, s.units["goblin_1"], only, []) == "protect_archer_1"


def test_choice_is_deterministic():
    for level in (1, 2, 3):
        a = plan_round(new_game(level), ScriptedBrain())
        b = plan_round(new_game(level), ScriptedBrain())
        assert a == b


@pytest.mark.parametrize("level", [1, 2, 3])
def test_full_game_with_scripted_brain_finishes(level):
    g = Game(level, 1, ScriptedBrain())
    for _ in range(30):
        if g.result:
            break
        g.end_turn()
    assert g.result in ("win", "lose")