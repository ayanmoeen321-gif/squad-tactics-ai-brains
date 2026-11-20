from eval.compare import compare, fallback_reasons, make_brain, report, wilson
from tests.test_laya_brain import FakeAgent


def test_make_brain_names_and_unknown():
    for name in ("random", "scripted", "always_attack"):
        assert make_brain(name, 0).choose is not None
    try:
        make_brain("nope", 0)
        assert False
    except ValueError:
        pass


def test_compare_runs_and_reports(capsys):
    results = compare(["scripted", "always_attack"], seeds=range(2), levels=(1,))
    assert len(results[("scripted", 1)]) == 2 * 3
    report(results)
    assert "always_attack" in capsys.readouterr().out


def test_random_brain_is_reproducible():
    keys = ("outcome", "rounds", "hero_hp", "monsters_alive")
    a = compare(["random"], seeds=range(3), levels=(2,))[("random", 2)]
    b = compare(["random"], seeds=range(3), levels=(2,))[("random", 2)]
    assert [[r[k] for k in keys] for r in a] == [[r[k] for k in keys] for r in b]


def test_laya_rows_show_difference_to_baselines(capsys):
    results = compare(["always_attack", "scripted", "laya_a"], FakeAgent(),
                      seeds=range(2), levels=(1,))
    report(results)
    out = capsys.readouterr().out
    assert " pp" in out and "vs always_attack" in out and "vs scripted" in out


def test_fallback_reasons_are_separated(tmp_path):
    compare(["laya_a"], FakeAgent("error"), seeds=range(1), levels=(1,), log_dir=tmp_path / "a")
    assert fallback_reasons(tmp_path / "a", "laya_a")["RuntimeError"] > 0
    compare(["laya_a"], FakeAgent("invalid"), seeds=range(1), levels=(1,), log_dir=tmp_path / "b")
    assert fallback_reasons(tmp_path / "b", "laya_a")["invalid_choice"] > 0


def test_wilson_interval_is_sane():
    lo, hi = wilson(75, 150)
    assert 0.4 < lo < 0.5 < hi < 0.6
    assert wilson(0, 0) == (0.0, 0.0)