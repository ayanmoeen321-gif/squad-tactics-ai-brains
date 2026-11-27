import json

import pytest

from brains.hero_bots import BOTS
from brains.lookahead2_brain import Lookahead2Brain
from brains.scripted_brain import ScriptedBrain
from eval.make_dagger_data import DAGGER_SEED_START, generate, play_dagger
from eval.make_laya_data import _play


class AlwaysLast:
    def choose(self, state, monster, options, plans):
        return options[-1]["id"]


def test_the_game_follows_the_student():
    style = sorted(BOTS)[0]
    rec = play_dagger(1, DAGGER_SEED_START, style, ScriptedBrain(), Lookahead2Brain())
    ref = [r for r in _play(1, DAGGER_SEED_START, style, "scripted") if len(r["questions"]["action"]["criteria"]) >= 2]
    assert rec.rows and len(rec.rows) == len(ref)
    assert [r["state"] for r in rec.rows] == [r["state"] for r in ref]
    assert [r["questions"] for r in rec.rows] == [r["questions"] for r in ref]


def test_labels_are_the_teacher_choices():
    rec = play_dagger(1, DAGGER_SEED_START, sorted(BOTS)[0], ScriptedBrain(), AlwaysLast())
    assert rec.rows
    for r in rec.rows:
        options = list(r["questions"]["action"]["criteria"])
        assert len(options) >= 2 and r["expected"]["action"] == options[-1]


def test_resume_and_target(tmp_path):
    out = str(tmp_path / "rows.jsonl")
    s1 = generate(ScriptedBrain(), AlwaysLast(), out, 60, log=lambda *_: None)
    a = open(out, encoding="utf-8").read().splitlines()
    assert len(a) >= 60 and s1["rows"] == len(a)
    s2 = generate(ScriptedBrain(), AlwaysLast(), out, 60, log=lambda *_: None)
    assert open(out, encoding="utf-8").read().splitlines() == a and s2["rows"] == len(a)
    generate(ScriptedBrain(), AlwaysLast(), out, len(a) + 60, log=lambda *_: None)
    b = open(out, encoding="utf-8").read().splitlines()
    assert len(b) >= len(a) + 60 and b[:len(a)] == a
    json.loads(b[-1])


def test_refuses_seeds_below_the_dagger_start(tmp_path):
    with pytest.raises(ValueError):
        generate(ScriptedBrain(), AlwaysLast(), str(tmp_path / "x.jsonl"), 10, start_seed=1000)