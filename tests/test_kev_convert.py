import json

import pytest

from eval.kev_convert import convert, to_kev_row

ROW = {
    "state": "STATE text",
    "questions": {"action": {"type": "choice", "instructions": "Which?",
                             "criteria": {"attack_tank": "hit", "advance": "walk"}}},
    "expected": {"action": "advance"},
}


def test_label_replaces_expected():
    out = to_kev_row(ROW)
    assert out["questions"]["action"]["label"] == "advance"
    assert "expected" not in out
    assert out["questions"]["action"]["criteria"] == ROW["questions"]["action"]["criteria"]


def test_row_without_expected_is_refused():
    with pytest.raises(ValueError):
        to_kev_row({"state": "x", "questions": {}})


def test_convert_file(tmp_path):
    src = tmp_path / "in.jsonl"
    dst = tmp_path / "out.jsonl"
    src.write_text(json.dumps(ROW) + "\n\n" + json.dumps(ROW) + "\n", encoding="utf-8")
    assert convert(str(src), str(dst)) == 2
    rows = [json.loads(l) for l in dst.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2 and rows[0]["questions"]["action"]["label"] == "advance"