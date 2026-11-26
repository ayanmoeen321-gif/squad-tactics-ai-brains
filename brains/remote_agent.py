import httpx


class RemoteAgent:
    """Same predict() as a local Laya agent, but asks a System One server (Laya or Kev) over HTTP (/v1/systemone)."""

    def __init__(self, url="http://127.0.0.1:8100", model="squad", timeout=10.0, client=None, api_key=None):
        self.url = url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.client = client or httpx.Client(timeout=timeout)

    def predict(self, state, questions):
        kwargs = {"json": {"state": state, "questions": questions, "model": self.model}}
        if self.api_key:
            kwargs["headers"] = {"Authorization": "Bearer " + self.api_key}
        resp = self.client.post(self.url + "/v1/systemone", **kwargs)
        resp.raise_for_status()
        return resp.json()