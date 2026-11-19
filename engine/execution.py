from engine.combat import ActionError, apply_lava, attack, heal, in_attack_range, outcome
from engine.movement import manhattan, shortest_path, walk_distances
from engine.options import HERO_ORDER


def _walk(state, monster, dest):
    """Tiles actually walked, start included. Stops before any blocker."""
    if dest == monster.pos:
        return [monster.pos]
    blocked = state.occupied() - {monster.pos}
    dist = walk_distances(state.grid, monster.pos, blocked, max_steps=monster.move)
    if dest in dist:
        return shortest_path(state.grid, monster.pos, dest, blocked)
    path = shortest_path(state.grid, monster.pos, dest)
    if path is None:
        return [monster.pos]
    walked = [monster.pos]
    for tile in path[1:1 + monster.move]:
        if tile in blocked:
            break
        walked.append(tile)
    return walked


def _move(state, monster, dest):
    walked = _walk(state, monster, dest)
    if len(walked) < 2:
        return []
    start = monster.pos
    monster.pos = walked[-1]
    return [{"type": "move", "unit": monster.id, "from": start,
             "to": monster.pos, "path": walked}]


def _fallback_attack(state, monster):
    heroes = [h for h in state.heroes() if in_attack_range(state, monster, h)]
    if not heroes:
        return []
    target = min(heroes, key=lambda h: (manhattan(monster.pos, h.pos),
                                        HERO_ORDER.index(h.id)))
    event = attack(state, monster, target)
    event["fallback"] = True
    return [event]


def _act(state, monster, plan):
    kind = plan["kind"]
    target = state.units.get(plan["target"]) if plan["target"] else None
    if kind == "attack":
        if target is not None and in_attack_range(state, monster, target):
            return [attack(state, monster, target)]
        return _fallback_attack(state, monster)
    if kind == "heal":
        if (target is not None and target.alive and monster.heal
                and target.hp < target.max_hp
                and manhattan(monster.pos, target.pos) <= monster.heal["range"]):
            try:
                return [heal(state, monster, target)]
            except ActionError:
                pass
        return _fallback_attack(state, monster)
    return []


def execute_round(state, plans):
    """Plays out the plans in order. Returns (events, result). Result: 'win', 'lose' or None."""
    events = []
    for plan in plans:
        monster = state.units[plan["monster"]]
        if not monster.alive:
            continue
        new = _move(state, monster, plan["dest"])
        new += _act(state, monster, plan)
        if plan.get("taunted"):
            for event in new:
                event["taunted"] = True
        events += new
        result = outcome(state)
        if result:
            return events, result
    events += apply_lava(state, "monster")
    return events, outcome(state, round_over=True)