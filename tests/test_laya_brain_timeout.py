import time

from brains import laya_brain
from brains.laya_brain import LayaBrain


class SlowFirst:
    def __init__(self):
        self.n = 0

    def predict(self, state, questions):
        self.n += 1
        if self.n == 1:
            time.sleep(0.6)
        return {"answers": {"action": {"choice": "a", "probabilities": {"a": 1.0}}},
                "usage": {"input_tokens": 1}}


class Fallback:
    def choose(self, state, monster, options, plans):
        return "b"


def test_a_timed_out_call_does_not_block_the_retry(monkeypatch):
    monkeypatch.setattr(laya_brain, "to_laya_row", lambda *a: {"state": "S", "questions": {}})
    brain = LayaBrain(SlowFirst(), timeout=0.1, fallback=Fallback())
    pick = brain.choose(None, None, [{"id": "a"}, {"id": "b"}], [])
    assert pick == "a"
    assert brain.last_info["fallback"] is False
    assert brain.last_info["retry"] is True