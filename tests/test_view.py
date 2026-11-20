from brains.scripted_brain import ScriptedBrain
from engine.game import Game
from engine.view import build_monster_view, rough_tokens


class Recorder:
    def __init__(self):
        self.inner = ScriptedBrain()
        self.calls = []

    def choose(self, state, monster, options, plans):
        self.calls.append((build_monster_view(state, monster, options, plans), options))
        return self.inner.choose(state, monster, options, plans)


def _record(level, rounds=6):
    rec = Recorder()
    game = Game(level, 0, rec)
    for _ in range(rounds):
        if game.result:
            break
        game.end_turn()
    return rec.calls


def test_view_has_parts_and_round():
    view, _ = _record(1, rounds=0)[0]
    assert view["text"].startswith("STATE\nRound 1 of 30.")
    assert "QUESTION" in view["text"] and "Options:" in view["text"]


def test_first_monster_has_no_earlier_plans_and_later_ones_do():
    calls = _record(2, rounds=0)
    assert "Earlier plans" not in calls[0][0]["state"]
    assert "Earlier plans" in calls[-1][0]["state"]


def test_option_ids_match_options_in_order():
    for level in (1, 2, 3):
        for view, options in _record(level):
            assert [oid for oid, _ in view["options"]] == [o["id"] for o in options]


def test_text_stays_under_token_budget_on_every_level():
    for level in (1, 2, 3):
        worst = max(rough_tokens(v["text"]) for v, _ in _record(level, rounds=10))
        assert worst < 400, (level, worst)