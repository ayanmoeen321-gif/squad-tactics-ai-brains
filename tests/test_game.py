import pytest

from brains.random_brain import RandomBrain
from engine.combat import ActionError
from engine.game import Game
from engine.replay import snapshot


def make(level=1, seed=1):
    return Game(level, seed, RandomBrain(seed))


def test_new_game_is_ready_with_plans():
    g = make()
    assert g.state.round == 1
    assert g.result is None
    assert g.phase is not None
    assert len(g.plans) == 5


def test_end_turn_starts_the_next_round():
    g = make()
    g.end_turn()
    assert g.state.round == 2
    assert g.result is None
    assert len(g.plans) == len(g.state.monsters())


def test_cooldowns_tick_down_at_round_start():
    g = make()
    g.state.units["tank"].cooldown = 3
    g.end_turn()
    assert g.state.units["tank"].cooldown == 2


def test_cooldown_never_goes_below_zero():
    g = make()
    g.end_turn()
    assert g.state.units["tank"].cooldown == 0


def test_killing_all_monsters_is_a_win():
    g = make()
    for m in g.state.monsters():
        m.hp = 0
    g.end_turn()
    assert g.result == "win"
    assert g.phase is None


def test_all_heroes_dead_is_a_loss():
    g = make()
    for h in g.state.heroes():
        h.hp = 0
    g.end_turn()
    assert g.result == "lose"


def test_timeout_at_round_30_is_a_loss():
    g = make()
    g.state.round = 30
    g.end_turn()
    assert g.result == "lose"
    assert g.state.round == 30


def test_end_turn_after_the_game_is_over_raises():
    g = make()
    for m in g.state.monsters():
        m.hp = 0
    g.end_turn()
    with pytest.raises(ActionError):
        g.end_turn()


def test_same_seed_same_game():
    a, b = make(2, 5), make(2, 5)
    for _ in range(4):
        a.end_turn()
        b.end_turn()
    assert snapshot(a.state) == snapshot(b.state)
    assert a.state.round == b.state.round


@pytest.mark.parametrize("level", [1, 2, 3])
def test_idle_heroes_game_always_finishes(level):
    g = make(level, 3)
    for _ in range(30):
        if g.result:
            break
        g.end_turn()
    assert g.result in ("win", "lose")
    assert g.state.round <= 30