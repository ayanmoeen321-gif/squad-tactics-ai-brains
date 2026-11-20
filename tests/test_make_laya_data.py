import pytest

from eval.make_laya_data import TRAIN_SEED_START, make_rows


def test_reaches_target_and_labels_are_options():
    rows, stats = make_rows(60)
    assert len(rows) >= 60
    assert stats["games"] >= 1
    for row in rows:
        crit = row["questions"]["action"]["criteria"]
        assert row["expected"]["action"] in crit


def test_same_call_gives_same_rows():
    a, _ = make_rows(40)
    b, _ = make_rows(40)
    assert a == b


def test_evaluation_seeds_are_refused():
    with pytest.raises(ValueError):
        make_rows(10, start_seed=0)
    with pytest.raises(ValueError):
        make_rows(10, start_seed=TRAIN_SEED_START - 1)

def test_min_options_filter_removes_single_option_rows():
    rows, _ = make_rows(60, min_options=2)
    assert len(rows) >= 60
    for row in rows:
        assert len(row["questions"]["action"]["criteria"]) >= 2