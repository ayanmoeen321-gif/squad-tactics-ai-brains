import copy
import random
from dataclasses import dataclass

from engine.data import load_heroes, load_monsters
from engine.grid import load_level

MAX_ROUNDS = 30


@dataclass
class Unit:
    id: str
    label: str
    side: str  # "hero" or "monster"
    kind: str
    hp: int
    max_hp: int
    pos: tuple
    move: int
    range: int
    damage: int
    los: bool
    skill: dict = None  # hero skill data
    heal: dict = None  # monster heal data
    cooldown: int = 0  # rounds left before the skill is ready
    order: int = 0  # tie-break order (lower first)

    @property
    def alive(self):
        return self.hp > 0


class GameState:
    def __init__(self, grid, units, seed=0, round_no=1, rng=None):
        self.grid = grid
        self.units = units  # dict: id -> Unit
        self.seed = seed
        self.round = round_no
        self.rng = rng if rng is not None else random.Random(seed)

    def living(self, side=None):
        return [u for u in self.units.values()
                if u.alive and (side is None or u.side == side)]

    def heroes(self):
        return self.living("hero")

    def monsters(self):
        return self.living("monster")

    def unit_at(self, pos):
        for u in self.units.values():
            if u.alive and u.pos == pos:
                return u
        return None

    def occupied(self):
        return {u.pos for u in self.units.values() if u.alive}

    def copy(self):
        rng = random.Random()
        rng.setstate(self.rng.getstate())
        units = {uid: copy.copy(u) for uid, u in self.units.items()}
        return GameState(self.grid, units, self.seed, self.round, rng)


def new_game(level, seed=0):
    grid = load_level(level)
    hero_data = load_heroes()
    monster_data = load_monsters()
    units = {}
    for kind, pos in grid.hero_starts.items():
        d = hero_data[kind]
        units[kind] = Unit(
            id=kind, label=d["name"], side="hero", kind=kind,
            hp=d["hp"], max_hp=d["hp"], pos=pos, move=d["move"],
            range=d["range"], damage=d["damage"], los=d["los"],
            skill=dict(d["skill"]),
        )
    counts = {}
    for order, (kind, pos) in enumerate(grid.monster_starts, start=1):
        d = monster_data[kind]
        counts[kind] = counts.get(kind, 0) + 1
        uid = f"{kind}_{counts[kind]}"
        units[uid] = Unit(
            id=uid, label=f"{d['name']} {counts[kind]}", side="monster",
            kind=kind, hp=d["hp"], max_hp=d["hp"], pos=pos, move=d["move"],
            range=d["range"], damage=d["damage"], los=d["los"],
            heal=dict(d["heal"]) if d["heal"] else None, order=order,
        )
    return GameState(grid, units, seed=seed)