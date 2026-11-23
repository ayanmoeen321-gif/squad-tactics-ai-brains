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


def test_laya_brain_asks_the_remote_agent(monkeypatch):
    calls.clear()
    monkeypatch.setattr(appmod, "_laya_health", lambda url: ["squad"])
    monkeypatch.setattr(appmod, "RemoteAgent", FakeAgent)
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "laya"})
    assert r.status_code == 200 and r.json()["round"] == 1
    assert len(calls) > 0