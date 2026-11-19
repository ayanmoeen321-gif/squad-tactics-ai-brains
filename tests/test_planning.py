import pytest

from brains.random_brain import RandomBrain
from engine.planning import plan_order, plan_round
from engine.replay import snapshot
from engine.state import new_game


def scene(level, alive):
    s = new_game(level)
    for u in s.units.values():
        if u.id in alive:
            u.pos = alive[u.id]
        else:
            u.hp = 0
    return s


class FirstBrain:
    def choose(self, state, monster, options, plans):
        return options[0]["id"]


class BadBrain:
    def choose(self, state, monster, options, plans):
        return "nonsense"


def test_order_closest_first():
    s = scene(1, {"goblin_1": (5, 9), "goblin_2": (5, 7), "tank": (5, 5)})
    assert [m.id for m in plan_order(s)] == ["goblin_2", "goblin_1"]


def test_order_ties_by_lower_number():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (4, 7), "tank": (5, 5)})
    assert [m.id for m in plan_order(s)] == ["goblin_1", "goblin_2"]


def test_one_plan_per_living_monster():
    s = new_game(2)
    s.units["goblin_1"].hp = 0
    plans = plan_round(s, RandomBrain(1))
    assert len(plans) == 7
    assert len({p["monster"] for p in plans}) == 7
    assert "goblin_1" not in {p["monster"] for p in plans}


def test_tiles_are_reserved():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (4, 8), "goblin_3": (6, 8),
                  "tank": (5, 5)})
    plans = plan_round(s, FirstBrain())
    assert all(p["option"] == "attack_tank" for p in plans)
    assert len({p["dest"] for p in plans}) == 3


def test_overkill_blocks_later_attack():
    s = scene(1, {"goblin_1": (5, 8), "goblin_2": (5, 9),
                  "archer": (5, 5), "healer": (8, 9)})
    s.units["archer"].hp = 2
    plans = plan_round(s, FirstBrain())
    assert (plans[0]["monster"], plans[0]["target"]) == ("goblin_1", "archer")
    assert (plans[1]["monster"], plans[1]["target"]) == ("goblin_2", "healer")


def test_boxed_in_monster_waits():
    s = scene(1, {"goblin_1": (0, 0), "tank": (5, 5)})
    s.grid.tiles[0][1] = "#"
    s.grid.tiles[1][0] = "#"
    plans = plan_round(s, FirstBrain())
    assert len(plans) == 1
    assert plans[0]["kind"] == "wait" and plans[0]["dest"] == (0, 0)


def test_random_brain_same_seed_same_plans():
    a = plan_round(new_game(3), RandomBrain(4))
    b = plan_round(new_game(3), RandomBrain(4))
    assert a == b
    assert len(a) == 10


@pytest.mark.parametrize("level", [1, 2, 3])
def test_plans_never_share_tiles(level):
    for seed in range(10):
        s = new_game(level)
        plans = plan_round(s, RandomBrain(seed))
        dests = [p["dest"] for p in plans]
        assert len(set(dests)) == len(dests)
        hero_tiles = {h.pos for h in s.heroes()}
        assert not hero_tiles & set(dests)


def test_planning_does_not_change_state():
    s = new_game(3)
    before = snapshot(s)
    plan_round(s, RandomBrain(2))
    assert snapshot(s) == before


def test_bad_choice_raises():
    with pytest.raises(ValueError):
        plan_round(new_game(1), BadBrain())