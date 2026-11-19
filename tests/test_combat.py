import pytest

from engine.combat import (ActionError, apply_lava, attack, damage_against, heal,
                           in_attack_range, outcome, piercing_shot, skill_ready)
from engine.state import MAX_ROUNDS, new_game


def test_melee_needs_adjacent():
    s = new_game(1)
    tank, g = s.units["tank"], s.units["goblin_1"]
    tank.pos, g.pos = (5, 5), (5, 6)
    assert in_attack_range(s, tank, g)
    g.pos = (5, 7)
    assert not in_attack_range(s, tank, g)


def test_same_side_cannot_attack():
    s = new_game(1)
    assert not in_attack_range(s, s.units["tank"], s.units["archer"])


def test_ranged_needs_line_of_sight():
    s = new_game(1)
    a, g = s.units["archer"], s.units["goblin_1"]
    a.pos, g.pos = (1, 1), (1, 5)
    assert in_attack_range(s, a, g)
    s.grid.tiles[1][3] = "#"
    assert not in_attack_range(s, a, g)


def test_ranged_out_of_range():
    s = new_game(1)
    a, g = s.units["archer"], s.units["goblin_1"]
    a.pos, g.pos = (1, 1), (1, 6)
    assert not in_attack_range(s, a, g)


def test_attack_deals_damage_and_kills():
    s = new_game(1)
    tank, g = s.units["tank"], s.units["goblin_1"]
    tank.pos, g.pos = (5, 5), (5, 6)
    ev = attack(s, tank, g)
    assert ev["damage"] == 4 and ev["killed"]
    assert not g.alive


def test_cover_reduces_ranged_damage():
    s = new_game(1)
    a, g = s.units["archer"], s.units["goblin_1"]
    a.pos, g.pos = (4, 1), (4, 5)
    assert s.grid.tile(4, 5) == "C"
    ev = attack(s, a, g)
    assert ev["damage"] == 3
    assert g.hp == 1


def test_cover_does_not_reduce_melee():
    s = new_game(1)
    tank, g = s.units["tank"], s.units["goblin_1"]
    tank.pos, g.pos = (4, 4), (4, 5)
    assert attack(s, tank, g)["damage"] == 4


def test_cover_minimum_damage_is_one():
    s = new_game(1)
    g = s.units["goblin_1"]
    g.pos = (4, 5)
    assert damage_against(s, g, 1, True) == 1
    assert damage_against(s, g, 2, True) == 1
    assert damage_against(s, g, 2, False) == 2


def test_dead_target_cannot_be_attacked():
    s = new_game(1)
    tank, g = s.units["tank"], s.units["goblin_1"]
    tank.pos, g.pos = (5, 5), (5, 6)
    g.hp = 0
    assert not in_attack_range(s, tank, g)


def test_illegal_attack_raises():
    s = new_game(1)
    with pytest.raises(ActionError):
        attack(s, s.units["tank"], s.units["goblin_1"])


def test_piercing_shot_hits_all_in_line():
    s = new_game(1)
    a = s.units["archer"]
    a.pos = (1, 1)
    s.units["goblin_1"].pos = (1, 3)
    s.units["goblin_2"].pos = (1, 5)
    s.units["goblin_3"].pos = (1, 6)
    ev = piercing_shot(s, a, "right")
    assert len(ev) == 2
    assert not s.units["goblin_1"].alive
    assert not s.units["goblin_2"].alive
    assert s.units["goblin_3"].hp == 4
    assert a.cooldown == 3


def test_piercing_shot_stopped_by_wall():
    s = new_game(1)
    a = s.units["archer"]
    a.pos = (1, 1)
    s.grid.tiles[1][4] = "#"
    s.units["goblin_1"].pos = (1, 3)
    s.units["goblin_2"].pos = (1, 5)
    piercing_shot(s, a, "right")
    assert not s.units["goblin_1"].alive
    assert s.units["goblin_2"].hp == 4


def test_piercing_shot_respects_cover():
    s = new_game(1)
    a = s.units["archer"]
    a.pos = (4, 1)
    s.units["brute_1"].pos = (4, 5)
    piercing_shot(s, a, "right")
    assert s.units["brute_1"].hp == 9


def test_piercing_shot_cooldown():
    s = new_game(1)
    a = s.units["archer"]
    assert skill_ready(a)
    piercing_shot(s, a, "right")
    assert not skill_ready(a)
    with pytest.raises(ActionError):
        piercing_shot(s, a, "right")


def test_piercing_shot_ignores_heroes():
    s = new_game(1)
    a = s.units["archer"]
    a.pos = (1, 1)
    s.units["tank"].pos = (1, 3)
    piercing_shot(s, a, "right")
    assert s.units["tank"].hp == 20


def test_only_archer_has_piercing_shot():
    s = new_game(1)
    with pytest.raises(ActionError):
        piercing_shot(s, s.units["tank"], "right")


def test_hero_heal():
    s = new_game(1)
    tank, healer = s.units["tank"], s.units["healer"]
    tank.pos, healer.pos = (5, 3), (6, 1)
    tank.hp = 10
    ev = heal(s, healer, tank)
    assert ev["restored"] == 5
    assert tank.hp == 15
    assert healer.cooldown == 2


def test_heal_capped_at_max_hp():
    s = new_game(1)
    tank, healer = s.units["tank"], s.units["healer"]
    tank.pos, healer.pos = (5, 3), (6, 1)
    tank.hp = 18
    assert heal(s, healer, tank)["restored"] == 2
    assert tank.hp == 20


def test_healer_cannot_heal_self_or_far_or_enemy():
    s = new_game(1)
    tank, healer = s.units["tank"], s.units["healer"]
    healer.pos = (6, 1)
    tank.pos = (0, 11)
    tank.hp = 10
    with pytest.raises(ActionError):
        heal(s, healer, healer)
    with pytest.raises(ActionError):
        heal(s, healer, tank)
    with pytest.raises(ActionError):
        heal(s, healer, s.units["goblin_1"])


def test_heal_cooldown():
    s = new_game(1)
    tank, healer = s.units["tank"], s.units["healer"]
    tank.pos, healer.pos = (5, 3), (6, 1)
    tank.hp = 5
    heal(s, healer, tank)
    with pytest.raises(ActionError):
        heal(s, healer, tank)
    healer.cooldown = 0
    heal(s, healer, tank)
    assert tank.hp == 15


def test_monster_heal_no_cooldown():
    s = new_game(2)
    mh, brute = s.units["healer_1"], s.units["brute_1"]
    mh.pos, brute.pos = (5, 11), (5, 9)
    brute.hp = 2
    assert heal(s, mh, brute)["restored"] == 3
    assert heal(s, mh, brute)["restored"] == 3
    assert brute.hp == 8
    with pytest.raises(ActionError):
        heal(s, mh, s.units["tank"])


def test_lava_hits_only_given_side():
    s = new_game(2)
    tank, g = s.units["tank"], s.units["goblin_1"]
    tank.pos, g.pos = (7, 7), (7, 8)
    ev = apply_lava(s, "hero")
    assert len(ev) == 1
    assert tank.hp == 17
    assert g.hp == 4
    apply_lava(s, "monster")
    assert g.hp == 1
    assert apply_lava(s, "hero")[0]["damage"] == 3


def test_lava_can_kill():
    s = new_game(2)
    tank = s.units["tank"]
    tank.pos = (8, 7)
    tank.hp = 2
    ev = apply_lava(s, "hero")
    assert ev[0]["damage"] == 2 and ev[0]["killed"]
    assert not tank.alive


def test_outcome_win():
    s = new_game(1)
    assert outcome(s) is None
    for m in s.monsters():
        m.hp = 0
    assert outcome(s) == "win"


def test_outcome_lose_all_heroes():
    s = new_game(1)
    for h in s.heroes():
        h.hp = 0
    assert outcome(s) == "lose"


def test_outcome_timeout():
    s = new_game(1)
    s.round = MAX_ROUNDS - 1
    assert outcome(s, round_over=True) is None
    s.round = MAX_ROUNDS
    assert outcome(s) is None
    assert outcome(s, round_over=True) == "lose"