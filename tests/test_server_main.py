from fastapi.testclient import TestClient

from server.main import root

client = TestClient(root)


def test_api_is_mounted_under_api():
    r = client.post("/api/new", json={"level": 1, "seed": 0})
    assert r.status_code == 200
    assert client.get("/api/state").json()["round"] == 1