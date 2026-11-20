import json

from brains.scripted_brain import ScriptedBrain
from engine.game import Game
from eval.laya_export import to_laya_row


class Rec:
    def __init__(self):
        self.inner = ScriptedBrain()
        self.rows = []
        self.option_ids = []

    def choose(self, state, monster, options, plans):
        cid = self.inner.choose(state, monster, options, plans)
        self.rows.append(to_laya_row(state, monster, options, plans, cid))
        self.option_ids.append([o["id"] for o in options])
        return cid


def _rows(level=3, rounds=4):
    rec = Rec()
    game = Game(level, 0, rec)
    for _ in range(rounds):
        if game.result:
            break
        game.end_turn()
    return rec


def test_row_has_laya_shape_and_expected_is_an_option():
    rec = _rows()
    assert rec.rows
    for row, ids in zip(rec.rows, rec.option_ids):
        q = row["questions"]["action"]
        assert q["type"] == "choice"
        assert list(q["criteria"]) == ids
        assert row["expected"]["action"] in ids
        assert row["state"].startswith("Round")


def test_row_without_choice_has_no_label():
    game = Game(1, 0, ScriptedBrain())
    m = game.state.monsters()[0]
    row = to_laya_row(game.state, m, [], [], None)
    assert "expected" not in row and "gold" not in row


def test_rows_are_json_serializable():
    for row in _rows().rows:
        json.dumps(row)