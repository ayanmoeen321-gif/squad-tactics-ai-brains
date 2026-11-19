from engine.combat import attack, in_attack_range, outcome
from engine.movement import reachable_tiles
from engine.state import new_game


def snapshot(state):
    return tuple(sorted((u.id, u.hp, u.pos, u.cooldown) for u in state.units.values()))


def random_playout(level, seed, steps=40):
    """Random moves and attacks driven only by the seeded RNG. Used to test replay."""
    state = new_game(level, seed)
    for _ in range(steps):
        if outcome(state):
            break
        unit = state.rng.choice(sorted(state.living(), key=lambda u: u.id))
        blocked = state.occupied() - {unit.pos}
        tiles = sorted(reachable_tiles(state.grid, unit.pos, unit.move, blocked))
        unit.pos = state.rng.choice(tiles)
        targets = sorted((t for t in state.living() if in_attack_range(state, unit, t)),
                         key=lambda u: u.id)
        if targets:
            attack(state, unit, state.rng.choice(targets))
    return snapshot(state)