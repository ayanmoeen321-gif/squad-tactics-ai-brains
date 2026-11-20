from brains.lookahead_brain import INF, LookaheadBrain, score
from brains.scripted_brain import ScriptedBrain
from engine.game import Game
from engine.state import new_game
from eval.runner import run_game


def _after(state):
    return state.copy()


def test_score_hero_damage_and_kill():
    before = new_game(1, 0)
    after = _after(before)
    after.units["tank"].hp -= 5
    assert score(before, after, None) == 5
    after.units["archer"].hp = 0
    assert score(before, after, None) == 5 + 10 + 6


def test_score_monster_losses_and_results():
    before = new_game(1, 0)
    after = _after(before)
    after.units["goblin_1"].hp -= 1
    assert score(before, after, None) == -3
    after.units["goblin_1"].hp = 0
    assert score(before, after, None) == -12 - 2
    assert score(before, after, "lose") == INF
    assert score(before, after, "win") == -INF


def test_choice_is_legal_and_does_not_change_the_real_state():
    class Spy:
        def __init__(self):
            self.inner = LookaheadBrain()
            self.checked = 0

        def choose(self, state, monster, options, plans):
            snap = ({u: (v.hp, v.pos, v.cooldown) for u, v in state.units.items()},
                    state.rng.getstate(), [dict(p) for p in plans])
            chosen = self.inner.choose(state, monster, options, plans)
            after = ({u: (v.hp, v.pos, v.cooldown) for u, v in state.units.items()},
                     state.rng.getstate(), [dict(p) for p in plans])
            assert snap == after
            assert chosen in [o["id"] for o in options]
            self.checked += 1
            return chosen

    spy = Spy()
    Game(2, 0, spy)
    assert spy.checked > 0


def test_single_option_needs_no_rollout():
    brain = LookaheadBrain()
    brain._try = None  # would crash if called
    game = Game(1, 0, ScriptedBrain())
    m = game.state.monsters()[0]
    opt = {"id": "only", "kind": "advance", "target": None, "dest": m.pos, "steps": 0}
    assert brain.choose(game.state, m, [opt], []) == "only"


def test_full_game_runs_and_is_repeatable():
    keys = ("outcome", "rounds", "hero_hp", "monsters_alive")
    a = run_game(2, 0, LookaheadBrain(), "focus")
    b = run_game(2, 0, LookaheadBrain(), "focus")
    assert a["outcome"] in ("win", "lose")
    assert [a[k] for k in keys] == [b[k] for k in keys]