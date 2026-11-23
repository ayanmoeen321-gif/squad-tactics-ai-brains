from concurrent.futures import ThreadPoolExecutor

from brains.scripted_brain import ScriptedBrain
from eval.laya_export import to_laya_row


class LayaBrain:
    """Asks a loaded Laya agent. Takes the top option every time.
    One option: no model call. Error or timeout: retry once, then scripted fallback."""

    def __init__(self, agent, name="laya", version=None, timeout=3.0, fallback=None):
        self.agent = agent
        self.name = name
        self.version = version
        self.timeout = timeout
        self.fallback = fallback or ScriptedBrain()
        self.last_info = None
        self._pool = ThreadPoolExecutor(max_workers=2)

    def _ask(self, row):
        out = self.agent.predict(row["state"], row["questions"])
        ans = out["answers"]["action"]
        return ans["choice"], ans["probabilities"], out.get("usage", {}).get("input_tokens")

    def choose(self, state, monster, options, plans):
        ids = [o["id"] for o in options]
        if len(ids) == 1:
            self.last_info = {"fallback": False, "retry": False}
            return ids[0]
        row = to_laya_row(state, monster, options, plans)
        reason = None
        for attempt in (0, 1):
            try:
                future = self._pool.submit(self._ask, row)
                choice, probs, tokens = future.result(timeout=self.timeout)
                if choice in ids:
                    self.last_info = {"probabilities": probs, "tokens": tokens,
                                      "retry": attempt == 1, "fallback": False}
                    return choice
                reason = "invalid_choice"
            except Exception as err:
                reason = f"{type(err).__name__}"
        self.last_info = {"retry": True, "fallback": True, "fallback_reason": reason}
        return self.fallback.choose(state, monster, options, plans)