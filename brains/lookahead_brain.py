from brains.scripted_brain import ScriptedBrain
from engine.execution import execute_round
from engine.options import legal_options, make_plan, wait_plan
from engine.planning import plan_order

INF = float("inf")
HERO_KILL = 6
MONSTER_HP = 3
MONSTER_KILL = 2


def _side(state, side):
    units = [u for u in state.units.values() if u.side == side]
    return sum(max(0, u.hp) for u in units), sum(1 for u in units if u.alive)


def score(before, after, result):
    """Monster point of view, higher is better. Result is from the heroes' side:
    'lose' = monsters win (+inf), 'win' = heroes win (-inf).
    Otherwise: hero HP lost + 6 per hero killed - 3 per monster HP lost - 2 per monster killed."""
    if result == "lose":
        return INF
    if result == "win":
        return -INF
    hero_hp_b, heroes_b = _side(before, "hero")
    hero_hp_a, heroes_a = _side(after, "hero")
    mon_hp_b, mons_b = _side(before, "monster")
    mon_hp_a, mons_a = _side(after, "monster")
    return ((hero_hp_b - hero_hp_a) + HERO_KILL * (heroes_b - heroes_a)
            - MONSTER_HP * (mon_hp_b - mon_hp_a) - MONSTER_KILL * (mons_b - mons_a))


class LookaheadBrain:
    """For each option: copy the state, plan the later monsters with scripted v1,
    play the monster phase (heroes stand still), score the result. Best score wins;
    ties go to the first option in the fixed order."""
    name = "lookahead"
    version = "1"

    def __init__(self):
        self.rollout = ScriptedBrain()
        self.last_info = None

    def _try(self, state, monster, option, plans, order):
        sim = state.copy()
        trial = [dict(p) for p in plans] + [make_plan(monster, option)]
        for mid in order[order.index(monster.id) + 1:]:
            m = sim.units[mid]
            opts = legal_options(sim, m, trial)
            if not opts:
                trial.append(wait_plan(m))
                continue
            chosen = self.rollout.choose(sim, m, opts, trial)
            trial.append(make_plan(m, next(o for o in opts if o["id"] == chosen)))
        _, result = execute_round(sim, trial)
        return score(state, sim, result)

    def choose(self, state, monster, options, plans):
        if len(options) == 1:
            return options[0]["id"]
        order = [m.id for m in plan_order(state)]
        best_id, best = options[0]["id"], None
        for option in options:
            s = self._try(state, monster, option, plans, order)
            if best is None or s > best:
                best_id, best = option["id"], s
        return best_id