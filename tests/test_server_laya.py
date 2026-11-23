from fastapi.testclient import TestClient

from server import app as appmod

client = TestClient(appmod.app)
calls = []


class FakeAgent:
    def __init__(self, url, model="squad", timeout=3.0):
        self.model = model

    def predict(self, state, questions):
        calls.append(1)
        choice = next(iter(questions["action"]["criteria"]))
        return {"answers": {"action": {"choice": choice, "probabilities": {choice: 1.0}}},
                "usage": {"input_tokens": 1}}


def test_laya_brain_unreachable_server_is_a_clear_400(monkeypatch):
    def boom(url):
        raise OSError("no server")

    monkeypatch.setattr(appmod, "_laya_health", boom)
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "laya"})
    assert r.status_code == 400 and "not reachable" in r.json()["detail"]


def test_laya_brain_model_not_loaded_is_a_clear_400(monkeypatch):
    monkeypatch.setattr(appmod, "_laya_health", lambda url: ["other"])
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "laya"})
    assert r.status_code == 400 and "no model named" in r.json()["detail"]


def test_laya_brain_asks_the_remote_agent(monkeypatch, tmp_path):
    monkeypatch.setenv("LIVE_LOG_DIR", str(tmp_path))
    calls.clear()
    monkeypatch.setattr(appmod, "_laya_health", lambda url: ["squad"])
    monkeypatch.setattr(appmod, "RemoteAgent", FakeAgent)
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "laya"})
    assert r.status_code == 200 and r.json()["round"] == 1
    assert len(calls) > 0

def test_laya_game_reports_stats_and_writes_a_log(monkeypatch, tmp_path):
    monkeypatch.setenv("LIVE_LOG_DIR", str(tmp_path))
    monkeypatch.setattr(appmod, "_laya_health", lambda url: ["squad"])
    monkeypatch.setattr(appmod, "RemoteAgent", FakeAgent)
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "laya"})
    stats = r.json()["brain_stats"]
    assert stats["name"] == "laya" and stats["decisions"] > 0 and stats["fallbacks"] == 0
    lines = (tmp_path / "live_decisions.jsonl").read_text().splitlines()
    assert len(lines) == stats["decisions"]


def test_scripted_game_has_no_brain_stats():
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "scripted"})
    assert r.json()["brain_stats"] is None