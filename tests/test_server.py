from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def _new(level=1, seed=0):
    r = client.post("/new", json={"level": level, "seed": seed})
    assert r.status_code == 200
    return r.json()


def test_new_game_state_has_parts():
    s = _new()
    assert s["round"] == 1 and s["result"] is None
    assert len(s["grid"]) == 12 and len(s["grid"][0]) == 12
    assert {"tank", "archer", "healer"} <= set(s["heroes"])
    assert s["plans"]


def test_move_then_end_turn_advances_round():
    s = _new()
    dest = s["heroes"]["tank"]["reachable"][0]
    r = client.post("/move", json={"hero": "tank", "to": dest})
    assert r.status_code == 200
    assert r.json()["events"][0]["type"] == "move"
    for hero in ("tank", "archer", "healer"):
        assert client.post("/wait", json={"hero": hero}).status_code == 200
    r = client.post("/end_turn")
    assert r.status_code == 200
    assert r.json()["state"]["round"] == 2


def test_bad_move_is_400_not_crash():
    _new()
    r = client.post("/move", json={"hero": "tank", "to": [0, 0]})
    assert r.status_code == 400
    assert "cannot move" in r.json()["detail"]


def test_bad_direction_is_400():
    _new()
    r = client.post("/piercing_shot", json={"hero": "archer", "direction": "north"})
    assert r.status_code == 400


def test_piercing_shot_valid_direction_works():
    _new()
    r = client.post("/piercing_shot", json={"hero": "archer", "direction": "right"})
    assert r.status_code == 200
    assert client.get("/state").json()["heroes"]["archer"]["acted"] is True


def test_same_seed_same_start():
    assert _new(2, 5)["plans"] == _new(2, 5)["plans"]


def test_no_game_is_400():
    import server.app as m
    m.G["game"] = None
    assert client.get("/state").status_code == 400

def test_random_brain_can_be_chosen():
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "random"})
    assert r.status_code == 200


def test_unknown_brain_is_400():
    r = client.post("/new", json={"level": 1, "seed": 0, "brain": "nope"})
    assert r.status_code == 400

def test_state_has_attack_and_heal_lists():
    s = _new()
    for h in ("tank", "archer", "healer"):
        assert isinstance(s["heroes"][h]["can_attack"], list)
        assert isinstance(s["heroes"][h]["can_heal"], list)
        assert isinstance(s["heroes"][h]["skill_ready"], bool)