from brains.lookahead2_brain import Lookahead2Brain
from eval.runner import run_game


def test_choice_is_legal_and_real_state_is_untouched():
    class Spy:
        def __init__(self):
            self.inner = Lookahead2Brain()
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
    from engine.game import Game
    Game(2, 0, spy)
    assert spy.checked > 0


def test_full_game_runs_and_is_repeatable():
    keys = ("outcome", "rounds", "hero_hp", "monsters_alive")
    a = run_game(2, 0, Lookahead2Brain(), "focus")
    b = run_game(2, 0, Lookahead2Brain(), "focus")
    assert a["outcome"] in ("win", "lose")
    assert [a[k] for k in keys] == [b[k] for k in keys]