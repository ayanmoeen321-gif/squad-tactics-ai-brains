import json

from brains.scripted_brain import ScriptedBrain
from eval.runner import run_game


class InfoBrain:
    """Scripted choices; sets last_info on the first call only, or on every call."""
    name = "info"

    def __init__(self, every_call=False):
        self.inner = ScriptedBrain()
        self.every_call = every_call
        self.calls = 0
        self.last_info = None

    def choose(self, state, monster, options, plans):
        self.calls += 1
        if self.every_call or self.calls == 1:
            self.last_info = {"probabilities": {options[0]["id"]: 1.0}, "tokens": 123,
                              "retry": False, "fallback": True,
                              "fallback_reason": "timeout", "ignored": 1}
        return self.inner.choose(state, monster, options, plans)


def _lines(folder):
    text = (folder / "decisions.jsonl").read_text(encoding="utf-8")
    return [json.loads(x) for x in text.splitlines()]


def test_plain_brain_lines_have_no_optional_fields(tmp_path):
    summary = run_game(1, 0, ScriptedBrain(), "aggressive", log_dir=tmp_path)
    for line in _lines(tmp_path):
        for key in ("probabilities", "tokens", "retry", "fallback", "state_text"):
            assert key not in line
    assert summary["fallbacks"] == 0


def test_brain_info_is_logged_once_and_does_not_leak(tmp_path):
    run_game(1, 0, InfoBrain(), "aggressive", log_dir=tmp_path)
    lines = _lines(tmp_path)
    assert lines[0]["tokens"] == 123 and lines[0]["fallback_reason"] == "timeout"
    assert "ignored" not in lines[0]
    assert all("probabilities" not in line for line in lines[1:])


def test_fallbacks_are_counted_in_the_summary(tmp_path):
    summary = run_game(1, 0, InfoBrain(every_call=True), "aggressive", log_dir=tmp_path)
    assert summary["fallbacks"] == summary["decisions"] > 0


def test_state_text_only_when_asked(tmp_path):
    run_game(1, 0, ScriptedBrain(), "aggressive", log_dir=tmp_path / "a", log_text=True)
    assert all(line["state_text"].startswith("STATE") for line in _lines(tmp_path / "a"))
    run_game(1, 0, ScriptedBrain(), "aggressive", log_dir=tmp_path / "b")
    assert all("state_text" not in line for line in _lines(tmp_path / "b"))