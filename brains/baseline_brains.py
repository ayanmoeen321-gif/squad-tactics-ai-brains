from brains.scripted_brain import ScriptedBrain
from engine.options import HERO_ORDER


class AlwaysAttackBrain:
    """Baseline: if an attack option exists, hit the lowest-HP hero (ties: Tank, Archer,
    Healer). Otherwise the scripted brain decides."""
    name = "always_attack"
    version = "1"

    def __init__(self):
        self.inner = ScriptedBrain()

    def choose(self, state, monster, options, plans):
        attacks = [o for o in options if o["kind"] == "attack"]
        if not attacks:
            return self.inner.choose(state, monster, options, plans)
        best = min(attacks, key=lambda o: (state.units[o["target"]].hp,
                                           HERO_ORDER.index(o["target"])))
        return best["id"]