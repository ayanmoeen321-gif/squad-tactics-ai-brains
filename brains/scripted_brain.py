from engine.combat import damage_against
from engine.options import HERO_ORDER, planned_damage

RETREATERS = ("archer", "healer")


class ScriptedBrain:
    """Hand-coded rules. Deterministic. Reads earlier plans, so it also coordinates.
    Frozen before any training data is made. Bump `version` if a rule changes."""

    name = "scripted"
    version = "1"

    def choose(self, state, monster, options, plans):
        by_kind = {}
        for o in options:
            by_kind.setdefault(o["kind"], []).append(o)

        if "heal" in by_kind:
            return by_kind["heal"][0]["id"]  # lowest absolute HP, then map order
        if "retreat" in by_kind and monster.kind in RETREATERS:
            return by_kind["retreat"][0]["id"]
        if "attack" in by_kind:
            return self._pick_attack(state, monster, by_kind["attack"], plans)["id"]
        if "flank" in by_kind:
            return self._pick_flank(by_kind["flank"], plans)["id"]
        if monster.kind == "brute" and "hold" in by_kind:
            return by_kind["hold"][0]["id"]
        if "advance" in by_kind:
            return by_kind["advance"][0]["id"]
        return options[0]["id"]

    def _pick_attack(self, state, monster, attacks, plans):
        def key(o):
            hero = state.units[o["target"]]
            planned = planned_damage(state, hero, plans)
            own = damage_against(state, hero, monster.damage, monster.range > 1)
            kills = planned + own >= hero.hp
            return (not kills, planned == 0, hero.hp, HERO_ORDER.index(hero.id))

        return min(attacks, key=key)

    def _pick_flank(self, flanks, plans):
        def crowd(o):
            return sum(1 for p in plans
                       if p["kind"] in ("attack", "flank") and p["target"] == o["target"])

        return min(flanks, key=lambda o: (crowd(o), HERO_ORDER.index(o["target"])))