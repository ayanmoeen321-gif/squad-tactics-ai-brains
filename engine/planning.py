from engine.movement import walk_distances
from engine.options import legal_options, make_plan, wait_plan

FAR = 10 ** 9


def plan_order(state):
    """Closest to the nearest hero first (walk distance). Ties: lower monster number."""
    def key(monster):
        dist = walk_distances(state.grid, monster.pos)
        near = [dist[h.pos] for h in state.heroes() if h.pos in dist]
        return (min(near) if near else FAR, monster.order)

    return sorted(state.monsters(), key=key)


def plan_round(state, brain):
    """One planning phase. Returns the plans in order. The state is not changed."""
    plans = []
    for monster in plan_order(state):
        options = legal_options(state, monster, plans)
        if not options:
            plans.append(wait_plan(monster))
            continue
        chosen = brain.choose(state, monster, options, plans)
        option = next((o for o in options if o["id"] == chosen), None)
        if option is None:
            raise ValueError(f"{monster.id}: brain chose {chosen!r}, not a legal option")
        plans.append(make_plan(monster, option))
    return plans