import httpx

from brains.remote_agent import RemoteAgent


def test_remote_agent_posts_to_systemone_with_the_model_name():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = request.read()
        return httpx.Response(200, json={"answers": {"action": {"choice": "advance", "probabilities": {"advance": 1.0}}},
                                         "usage": {"input_tokens": 5}})

    agent = RemoteAgent("http://x:1/", client=httpx.Client(transport=httpx.MockTransport(handler)))
    out = agent.predict("S", {"action": {"type": "choice"}})
    assert seen["url"] == "http://x:1/v1/systemone"
    assert b'"model":"squad"' in seen["body"].replace(b" ", b"")
    assert out["answers"]["action"]["choice"] == "advance"


def test_remote_agent_raises_on_server_error():
    import pytest

    def handler(request):
        return httpx.Response(500, json={"detail": "inference failed"})

    agent = RemoteAgent("http://x:1", client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(httpx.HTTPStatusError):
        agent.predict("S", {})