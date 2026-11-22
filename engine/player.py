from engine.combat import ActionError, apply_lava, attack, heal, outcome, piercing_shot, skill_ready
from engine.movement import reachable_tiles
from engine.taunt import apply_taunt


class PlayerPhase:
    """One player phase. Each hero: one move (optional, before acting), then one action."""

    def __init__(self, state, plans):
        self.state = state
        self.plans = plans
        self.status = {h.id: {"start": None, "moved": False, "acted": False}
                       for h in state.heroes()}

    def _hero(self, hero_id):
        hero = self.state.units.get(hero_id)
        if hero is None or hero.side != "hero" or not hero.alive:
            raise ActionError(f"{hero_id} is not a living hero")
        return hero

    def _free_to_act(self, hero_id):
        hero = self._hero(hero_id)
        if self.status[hero_id]["acted"]:
            raise ActionError(f"{hero_id} already acted")
        return hero

    def reserved(self):
        return {p["dest"] for p in self.plans if self.state.units[p["monster"]].alive}

    def reachable(self, hero_id):
        hero = self._hero(hero_id)
        st = self.status[hero_id]
        if st["moved"] or st["acted"]:
            return set()
        blocked = (self.state.occupied() | self.reserved()) - {hero.pos}
        tiles = reachable_tiles(self.state.grid, hero.pos, hero.move, blocked)
        return set(tiles) - {hero.pos}

    def move(self, hero_id, dest):
        hero = self._hero(hero_id)
        if dest not in self.reachable(hero_id):
            raise ActionError(f"{hero_id} cannot move to {dest}")
        start = hero.pos
        self.status[hero_id].update(start=start, moved=True)
        hero.pos = dest
        return [{"type": "move", "unit": hero_id, "from": start, "to": dest}]

    def undo(self, hero_id):
        hero = self._hero(hero_id)
        st = self.status[hero_id]
        if not st["moved"] or st["acted"]:
            raise ActionError(f"{hero_id} has no move to undo")
        current = hero.pos
        hero.pos = st["start"]
        st.update(start=None, moved=False)
        return [{"type": "undo", "unit": hero_id, "from": current, "to": hero.pos}]

    def attack(self, hero_id, target_id):
        hero = self._free_to_act(hero_id)
        target = self.state.units.get(target_id)
        if target is None or target.side != "monster":
            raise ActionError(f"{target_id} is not a monster")
        event = attack(self.state, hero, target)
        self.status[hero_id]["acted"] = True
        return [event]

    def piercing_shot(self, hero_id, direction):
        hero = self._free_to_act(hero_id)
        events = piercing_shot(self.state, hero, direction)
        self.status[hero_id]["acted"] = True
        return events

    def heal(self, hero_id, target_id):
        hero = self._free_to_act(hero_id)
        target = self.state.units.get(target_id)
        if target is None or target.side != "hero":
            raise ActionError(f"{target_id} is not a hero")
        event = heal(self.state, hero, target)
        self.status[hero_id]["acted"] = True
        return [event]

    def wait(self, hero_id):
        self._free_to_act(hero_id)
        self.status[hero_id]["acted"] = True
        return []

    def result(self):
        return outcome(self.state)

    def end(self):
        """End of the player phase: lava on heroes, then win/lose check."""
        events = apply_lava(self.state, "hero")
        return events, outcome(self.state)

    def taunt(self, hero_id):
        hero = self._free_to_act(hero_id)
        if not hero.skill or hero.skill["name"] != "taunt":
            raise ActionError(f"{hero_id} cannot taunt")
        if not skill_ready(hero):
            raise ActionError("taunt is on cooldown")
        affected = apply_taunt(self.state, hero, self.plans)
        if not affected:
            raise ActionError("No monster is close enough to taunt (within 3 steps and able to reach the Tank).")
        hero.cooldown = hero.skill["cooldown"]
        self.status[hero_id]["acted"] = True
        return [{"type": "taunt", "unit": hero_id, "affected": affected}]