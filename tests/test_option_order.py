from brains.laya_brain import LayaBrain
from engine.game import Game
from eval.compare import make_brain
from eval.option_order import OrderProbe, ReversedBrain


class FakeAgent:
    def __init__(self, pick):
        self.pick = pick

    def predict(self, state, questions):
        ids = list(questions["action"]["criteria"])
        c = self.pick(ids)
        return {"answers": {"action": {"choice": c, "probabilities": {k: float(k == c) for k in ids}}},
                "usage": {"input_tokens": 1}}


class Recorder:
    last_info = None

    def __init__(self):
        self.seen = []

    def choose(self, state, monster, options, plans):
        self.seen.append([o["id"] for o in options])
        return options[0]["id"]


def play(brain, rounds=2):
    g = Game(2, 340, brain)
    for _ in range(rounds):
        if g.result:
            break
        g.end_turn()


def test_probe_sees_a_position_biased_model_change_its_answer():
    probe = OrderProbe(LayaBrain(FakeAgent(lambda ids: ids[0]), name="t", version="1"))
    play(probe)
    assert probe.n > 0 and probe.same == 0


def test_probe_sees_an_order_independent_model_stay_the_same():
    probe = OrderProbe(LayaBrain(FakeAgent(lambda ids: sorted(ids)[0]), name="t", version="1"))
    play(probe)
    assert probe.n > 0 and probe.same == probe.n


def test_reversed_brain_shows_the_inner_brain_reversed_options():
    rec = Recorder()
    out = ReversedBrain(rec).choose(None, None, [{"id": "a"}, {"id": "b"}, {"id": "c"}], [])
    assert rec.seen == [["c", "b", "a"]] and out == "c"


def test_compare_knows_laya_rev():
    assert isinstance(make_brain("laya_rev", 0, FakeAgent(lambda ids: ids[0])), ReversedBrain)