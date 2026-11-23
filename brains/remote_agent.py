import httpx


class RemoteAgent:
    """Same predict() as a local Laya agent, but asks a Laya server over HTTP (/v1/systemone)."""

    def __init__(self, url="http://127.0.0.1:8100", model="squad", timeout=10.0, client=None):
        self.url = url.rstrip("/")
        self.model = model
        self.client = client or httpx.Client(timeout=timeout)

    def predict(self, state, questions):
        resp = self.client.post(self.url + "/v1/systemone",
                                json={"state": state, "questions": questions, "model": self.model})
        resp.raise_for_status()
        return resp.json()