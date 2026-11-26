from brains.remote_agent import RemoteAgent


class FakeResp:
    def raise_for_status(self):
        pass

    def json(self):
        return {"answers": {}}


class FakeClient:
    def __init__(self):
        self.calls = []

    def post(self, url, json=None, headers=None):
        self.calls.append((url, json, headers))
        return FakeResp()


def test_api_key_is_sent_as_bearer_header():
    c = FakeClient()
    agent = RemoteAgent("http://x:1", model="m", api_key="secret", client=c)
    agent.predict("s", {"action": {}})
    assert c.calls[0][2] == {"Authorization": "Bearer secret"}


def test_no_key_sends_no_header():
    c = FakeClient()
    agent = RemoteAgent("http://x:1", model="m", client=c)
    agent.predict("s", {})
    assert c.calls[0][2] is None