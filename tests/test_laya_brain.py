import time

from brains.baseline_brains import AlwaysAttackBrain
from brains.laya_brain import LayaBrain
from engine.game import Game
from eval.runner import run_game


class FakeAgent:
    def __init__(self, mode="first"):
        self.mode = mode
        self.calls = 0

    def predict(self, state, questions):
        self.calls += 1
        ids = list(questions["action"]["criteria"])
        if self.mode == "error":
            raise RuntimeError("boom")
        if self.mode == "slow":
            time.sleep(0.5)
        choice = "not_an_option" if self.mode == "invalid" else ids[0]
        return {"answers": {"action": {"choice": choice,
                                       "probabilities": {i: 1 / len(ids) for i in ids}}},
                "usage": {"input_tokens": 50}}


def _call(brain, level=3):
    game = Game(level, 0, brain)
    return game


def test_laya_brain_plays_a_full_game_and_logs_fields(tmp_path):
    summary = run_game(2, 0, LayaBrain(FakeAgent()), "focus", log_dir=tmp_path)
    assert summary["outcome"] in ("win", "lose")
    assert summary["fallbacks"] == 0


def test_error_falls_back_to_scripted_after_one_retry():
    agent = FakeAgent("error")
    brain = LayaBrain(agent)
    summary = run_game(2, 0, brain, "focus")
    assert summary["fallbacks"] > 0
    assert agent.calls == 2 * summary["fallbacks"]


def test_invalid_choice_and_timeout_fall_back():
    for mode in ("invalid", "slow"):
        brain = LayaBrain(FakeAgent(mode), timeout=0.05)
        summary = run_game(1, 0, brain, "aggressive")
        assert summary["fallbacks"] > 0, mode


def test_single_option_skips_the_model():
    from brains.scripted_brain import ScriptedBrain

    class Counter:
        def __init__(self):
            self.inner = ScriptedBrain()
            self.multi = 0
            self.single = 0

        def choose(self, state, monster, options, plans):
            if len(options) > 1:
                self.multi += 1
            else:
                self.single += 1
            return self.inner.choose(state, monster, options, plans)

    agent = FakeAgent()
    brain = LayaBrain(agent)
    counter = Counter()
    original = brain.choose

    def spy(state, monster, options, plans):
        counter.choose(state, monster, options, plans)
        return original(state, monster, options, plans)

    brain.choose = spy
    run_game(2, 0, brain, "focus")
    assert counter.single > 0
    assert agent.calls == counter.multi

def test_always_attack_prefers_attack_and_plays():
    summary = run_game(2, 0, AlwaysAttackBrain(), "defensive")
    assert summary["outcome"] in ("win", "lose")
    assert summary["brain"] == "always_attack"