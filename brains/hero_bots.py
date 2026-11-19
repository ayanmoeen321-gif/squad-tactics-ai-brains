import random

from engine.combat import ActionError, in_attack_range, skill_ready
from engine.movement import is_chokepoint, manhattan, walk_distances
from engine.taunt import apply_taunt

ORDER = ("tank", "archer", "healer")
SHOT_DIRS = (("up", (-1, 0)), ("down", (1, 0)), ("left", (0, -1)), ("right", (0, 1)))
FAR = 10 ** 9


class HeroBot:
    """Plays all living heroes for one player phase. Subclasses set `style`.
    Errors are loud: an ActionError is recorded in `self.errors` (the hero then waits)."""

    style = "base"

    def __init__(self, seed=0):
        self.rng = random.Random(f"{self.style}:{seed}")  # separate from the engine RNG
        self.errors = []
        self.target_id = None

    def _tie(self):
        return self.rng.random()

    # ---- public -------------------------------------------------------
    def play(self, phase):
        """Plays one full player phase (without calling end). Returns the events."""
        events = []
        self.target_id = None
        for hid in ORDER:
            hero = phase.state.units.get(hid)
            if hero is None or not hero.alive or phase.result():
                continue
            events += self._play_hero(phase, hero)
        return events

    def _play_hero(self, phase, hero):
        events = []
        try:
            events += self._move(phase, hero)
            events += self._act(phase, hero)
        except ActionError as err:
            self.errors.append(f"{hero.id}: {err}")
        if hero.alive and not phase.status[hero.id]["acted"]:
            try:
                phase.wait(hero.id)
            except ActionError as err:
                self.errors.append(f"{hero.id} wait: {err}")
        return events

    # ---- helpers ------------------------------------------------------
    def _monsters(self, phase):
        return phase.state.monsters()

    def _reach(self, phase, hero):
        return [hero.pos] + sorted(phase.reachable(hero.id))

    def _tile_value(self, phase, hero, tile):
        """Lower is better. Never prefer lava."""
        return 1 if phase.state.grid.tile(*tile) == "L" else 0

    def _targets_from(self, phase, hero, tile):
        old = hero.pos
        hero.pos = tile
        try:
            return [m for m in self._monsters(phase)
                    if in_attack_range(phase.state, hero, m)]
        finally:
            hero.pos = old

    def _move_to(self, phase, hero, tile):
        if tile != hero.pos and tile in phase.reachable(hero.id):
            return phase.move(hero.id, tile)
        return []

    def _nearest_monster(self, phase, hero):
        dist = walk_distances(phase.state.grid, hero.pos)
        ms = [m for m in self._monsters(phase) if m.pos in dist]
        if not ms:
            return None
        return min(ms, key=lambda m: (dist[m.pos], m.order))

    def _approach(self, phase, hero, target):
        """Move to a tile that can hit the target, else walk toward it."""
        reach = self._reach(phase, hero)
        hitting = [t for t in reach
                   if any(m.id == target.id for m in self._targets_from(phase, hero, t))]
        if hitting:
            tile = min(hitting, key=lambda t: (self._tile_value(phase, hero, t),
                                               manhattan(t, hero.pos), self._tie()))
            return self._move_to(phase, hero, tile)
        dist = walk_distances(phase.state.grid, target.pos)
        tile = min(reach, key=lambda t: (self._tile_value(phase, hero, t),
                                         dist.get(t, FAR), self._tie()))
        return self._move_to(phase, hero, tile)

    # ---- to override --------------------------------------------------
    def _move(self, phase, hero):
        raise NotImplementedError

    def _act(self, phase, hero):
        return self._default_act(phase, hero)

    def _choose_target(self, phase, hero, candidates):
        return min(candidates, key=lambda m: (m.hp, m.order))

    # ---- actions ------------------------------------------------------
    def _default_act(self, phase, hero):
        if hero.id == "healer" and skill_ready(hero):
            hurt = [h for h in phase.state.heroes()
                    if h.id != hero.id and h.hp * 100 < h.max_hp * 60
                    and manhattan(hero.pos, h.pos) <= hero.skill["range"]]
            if hurt:
                target = min(hurt, key=lambda h: (h.hp, ORDER.index(h.id)))
                return phase.heal(hero.id, target.id)
        if hero.id == "tank" and skill_ready(hero):
            trial = [dict(p) for p in phase.plans]
            if len(apply_taunt(phase.state, hero, trial)) >= 2:
                return phase.taunt(hero.id)
        if hero.id == "archer" and skill_ready(hero):
            direction = self._best_shot(phase, hero)
            if direction:
                return phase.piercing_shot(hero.id, direction)
        targets = [m for m in self._monsters(phase)
                   if in_attack_range(phase.state, hero, m)]
        if targets:
            return phase.attack(hero.id, self._choose_target(phase, hero, targets).id)
        return []

    def _best_shot(self, phase, hero):
        best, best_dir = 1, None
        for name, (dr, dc) in SHOT_DIRS:
            hits, r, c = 0, hero.pos[0], hero.pos[1]
            for _ in range(hero.range):
                r, c = r + dr, c + dc
                if not phase.state.grid.is_walkable(r, c):
                    break
                u = phase.state.unit_at((r, c))
                if u is not None and u.side == "monster":
                    hits += 1
            if hits > best:
                best, best_dir = hits, name
        return best_dir


class AggressiveBot(HeroBot):
    style = "aggressive"

    def _move(self, phase, hero):
        target = self._nearest_monster(phase, hero)
        if target is None:
            return []
        return self._approach(phase, hero, target)


class DefensiveBot(HeroBot):
    style = "defensive"

    def _move(self, phase, hero):
        grid = phase.state.grid

        def key(t):
            safe = 0 if grid.tile(*t) == "C" or is_chokepoint(grid, *t) else 1
            can_hit = 0 if self._targets_from(phase, hero, t) else 1
            return (self._tile_value(phase, hero, t), can_hit, safe,
                    manhattan(t, hero.pos), self._tie())

        return self._move_to(phase, hero, min(self._reach(phase, hero), key=key))


class FocusFireBot(HeroBot):
    style = "focus"

    def _move(self, phase, hero):
        target = self._focus(phase)
        if target is None:
            return []
        return self._approach(phase, hero, target)

    def _focus(self, phase):
        """One shared target per turn: the lowest-HP monster that at least one hero
        that has not acted yet can hit this turn. Re-picked if the target dies."""
        if self.target_id:
            t = phase.state.units.get(self.target_id)
            if t is not None and t.alive:
                return t
        monsters = self._monsters(phase)
        if not monsters:
            return None
        acting = [h for h in phase.state.heroes() if not phase.status[h.id]["acted"]]
        hittable = {}
        for hero in acting:
            for tile in self._reach(phase, hero):
                for m in self._targets_from(phase, hero, tile):
                    hittable[m.id] = m
        if hittable:
            target = min(hittable.values(), key=lambda m: (m.hp, m.order))
        else:
            maps = [walk_distances(phase.state.grid, h.pos) for h in acting]

            def closest(m):
                return min((d.get(m.pos, FAR) for d in maps), default=FAR)

            target = min(monsters, key=lambda m: (closest(m), m.hp, m.order))
        self.target_id = target.id
        return target

    def _choose_target(self, phase, hero, candidates):
        for m in candidates:
            if m.id == self.target_id:
                return m
        return super()._choose_target(phase, hero, candidates)


BOTS = {"aggressive": AggressiveBot, "defensive": DefensiveBot, "focus": FocusFireBot}


def make_bot(style, seed=0):
    return BOTS[style](seed)