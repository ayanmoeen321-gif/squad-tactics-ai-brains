import pytest

from brains.hero_bots import BOTS, AggressiveBot, make_bot
from brains.scripted_brain import ScriptedBrain
from engine.combat import ActionError
from engine.game import Game
from engine.planning import plan_round
from engine.replay import snapshot


def setup(level, alive):
    g = Game(level, 1, ScriptedBrain())
    for u in g.state.units.values():
        if u.id in alive:
            u.pos = alive[u.id]
        else:
            u.hp = 0
    g.plans[:] = plan_round(g.state, g.brain)
    return g


def play_game(level, seed, style):
    g = Game(level, seed, ScriptedBrain())
    bot = make_bot(style, seed)
    rounds = 0
    while not g.result and rounds < 40:
        bot.play(g.phase)
        if g.phase.result() == "win":
            g.result = "win"
            break
        g.end_turn()
        rounds += 1
    return g, bot


class BrokenBot(AggressiveBot):
    def _act(self, phase, hero):
        raise ActionError("boom")


@pytest.mark.parametrize("style", sorted(BOTS))
@pytest.mark.parametrize("level", [1, 2, 3])
def test_bot_games_always_finish_without_errors(style, level):
    g, bot = play_game(level, 1, style)
    assert g.result in ("win", "lose")
    assert g.state.round <= 30
    assert bot.errors == []


@pytest.mark.parametrize("style", sorted(BOTS))
def test_same_seed_same_game(style):
    a, _ = play_game(2, 7, style)
    b, _ = play_game(2, 7, style)
    assert snapshot(a.state) == snapshot(b.state)
    assert a.state.round == b.state.round and a.result == b.result


@pytest.mark.parametrize("style", sorted(BOTS))
def test_bot_never_breaks_the_rules(style):
    for seed in range(5):
        g = Game(3, seed, ScriptedBrain())
        bot = make_bot(style, seed)
        for _ in range(30):
            if g.result:
                break
            bot.play(g.phase)
            if g.phase.result() == "win":
                break
            g.end_turn()
        tiles = [u.pos for u in g.state.living()]
        assert len(tiles) == len(set(tiles))
        assert bot.errors == []


def test_aggressive_bot_attacks_when_a_monster_is_in_reach():
    g = setup(1, {"tank": (5, 3), "archer": (4, 1), "healer": (6, 1), "goblin_1": (5, 4)})
    events = make_bot("aggressive", 1).play(g.phase)
    assert any(e["type"] == "attack" and e["attacker"] == "tank" for e in events)


def test_every_hero_ends_its_turn_acted():
    g = Game(1, 1, ScriptedBrain())
    bot = make_bot("defensive", 1)
    bot.play(g.phase)
    assert all(st["acted"] for st in g.phase.status.values())
    assert bot.errors == []


def test_errors_are_recorded_not_hidden():
    g = Game(1, 1, ScriptedBrain())
    bot = BrokenBot(1)
    bot.play(g.phase)
    assert len(bot.errors) == 3
    assert all("boom" in e for e in bot.errors)
    assert all(st["acted"] for st in g.phase.status.values())


def test_focus_fire_heroes_pick_the_same_target():
    g = setup(2, {"tank": (5, 3), "archer": (5, 1), "brute_1": (4, 3), "brute_2": (5, 4)})
    g.state.units["brute_2"].hp = 9
    g.state.units["tank"].cooldown = 3
    events = make_bot("focus", 1).play(g.phase)
    attacks = [e for e in events if e["type"] == "attack"]
    assert [e["target"] for e in attacks] == ["brute_2", "brute_2"]


def test_bot_rng_is_separate_from_engine_rng():
    g = Game(1, 4, ScriptedBrain())
    before = g.state.rng.getstate()
    bot = make_bot("defensive", 4)
    bot.play(g.phase)
    assert g.state.rng.getstate() == before
    assert bot.rng is not g.state.rng


def test_bot_rng_depends_on_style_and_seed():
    a = make_bot("aggressive", 3).rng.random()
    assert a == make_bot("aggressive", 3).rng.random()
    assert a != make_bot("aggressive", 4).rng.random()
    assert a != make_bot("defensive", 3).rng.random()


def test_tank_taunts_when_two_monsters_would_be_affected():
    g = setup(1, {"tank": (5, 5), "goblin_1": (5, 7), "goblin_2": (4, 7)})
    events = make_bot("aggressive", 1)._default_act(g.phase, g.state.units["tank"])
    assert [e["type"] for e in events] == ["taunt"]
    assert sorted(events[0]["affected"]) == ["goblin_1", "goblin_2"]


def test_tank_attacks_instead_when_only_one_monster_is_affected():
    g = setup(1, {"tank": (5, 5), "goblin_1": (5, 6)})
    events = make_bot("aggressive", 1)._default_act(g.phase, g.state.units["tank"])
    assert [e["type"] for e in events] == ["attack"]