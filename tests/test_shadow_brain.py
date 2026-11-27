from brains.lookahead2_brain import Lookahead2Brain
from brains.scripted_brain import ScriptedBrain
from brains.shadow_brain import ShadowBrain
from engine.game import Game


class Checked:
    """Plays a ShadowBrain and checks its teacher choice against a real Lookahead2Brain on every decision."""
    name = "checked"
    version = "1"

    def __init__(self, student):
        self.shadow = ShadowBrain(student, Lookahead2Brain())
        self.reference = Lookahead2Brain()
        self.checked = 0
        self.last_info = None

    def choose(self, state, monster, options, plans):
        before = len(self.shadow.records)
        out = self.shadow.choose(state, monster, options, plans)
        if len(options) > 1:
            assert len(self.shadow.records) == before + 1
            assert self.shadow.records[-1]["teacher"] == self.reference.choose(state, monster, options, plans)
            self.checked += 1
        else:
            assert len(self.shadow.records) == before
        return out


def play(brain, rounds=2, level=2, seed=340):
    g = Game(level, seed, brain)
    for _ in range(rounds):
        if g.result:
            break
        g.end_turn()


def test_teacher_choice_matches_lookahead2():
    brain = Checked(ScriptedBrain())
    play(brain)
    assert brain.checked > 0


def test_regret_is_zero_for_the_teacher_itself_and_never_negative():
    same = ShadowBrain(Lookahead2Brain(), Lookahead2Brain())
    play(same)
    assert same.records
    assert all(r["student"] == r["teacher"] and r["regret"] == 0 for r in same.records)
    other = ShadowBrain(ScriptedBrain(), Lookahead2Brain())
    play(other)
    assert other.records
    assert all(r["regret"] >= 0 for r in other.records)
    assert {"round", "monster", "kind", "options", "student", "teacher", "scores", "regret"} <= set(other.records[0])