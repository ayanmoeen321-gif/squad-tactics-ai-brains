from brains.laya_brain import LayaBrain
from eval.compare import make_brain


class DummyAgent:
    def predict(self, state, questions):
        raise RuntimeError("not called in this test")


def test_kev_brain_wraps_the_given_agent():
    brain = make_brain("kev_zero", 0, DummyAgent())
    assert isinstance(brain, LayaBrain)