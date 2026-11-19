from engine.movement import walk_distances
from engine.options import _can_hit_from, _option, _pick, _reachable, make_plan


def apply_taunt(state, tank, plans):
    """Re-plans nearby monsters to attack the Tank. Changes `plans` in place.
    Returns the ids of the monsters that were affected."""
    near = walk_distances(state.grid, tank.pos, max_steps=tank.skill["radius"])
    affected = []
    for i, plan in enumerate(plans):
        monster = state.units[plan["monster"]]
        if not monster.alive or monster.pos not in near:
            continue
        others = [p for j, p in enumerate(plans)
                  if j != i and state.units[p["monster"]].alive]
        reach = _reachable(state, monster, others)
        tiles = [t for t in reach if _can_hit_from(state, monster, t, tank)]
        if not tiles:
            continue
        option = _option(f"attack_{tank.id}", "attack", tank.id,
                         _pick(state, tiles, reach), reach)
        new_plan = make_plan(monster, option)
        new_plan["taunted"] = True
        plans[i] = new_plan
        affected.append(monster.id)
    return affected