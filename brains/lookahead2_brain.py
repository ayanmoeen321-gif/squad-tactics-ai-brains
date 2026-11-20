from brains.hero_bots import BOTS, make_bot
from brains.lookahead_brain import INF, score
from brains.scripted_brain import ScriptedBrain
from engine.execution import execute_round
from engine.options import legal_options, make_plan, wait_plan
from engine.planning import plan_order
from engine.player import PlayerPhase

BIG = 1000  # a game win/loss, as a normal number so scores can be averaged


class Lookahead2Brain:
    """Like LookaheadBrain, but the heroes reply before the monsters act.
    The reply is played by each of the 3 hero bots on a copy; scores are averaged."""
    name = "lookahead2"
    version = "1"

    def __init__(self):
        self.rollout = ScriptedBrain()
        self.last_info = None

    def _plans(self, sim, monster, option, plans, order):
        trial = [dict(p) for p in plans] + [make_plan(monster, option)]
        for mid in order[order.index(monster.id) + 1:]:
            m = sim.units[mid]
            opts = legal_options(sim, m, trial)
            if not opts:
                trial.append(wait_plan(m))
                continue
            chosen = self.rollout.choose(sim, m, opts, trial)
            trial.append(make_plan(m, next(o for o in opts if o["id"] == chosen)))
        return trial

    def _try(self, state, monster, option, plans, order, style):
        sim = state.copy()
        trial = self._plans(sim, monster, option, plans, order)
        phase = PlayerPhase(sim, trial)
        make_bot(style, state.seed + state.round).play(phase)
        _, result = phase.end()
        if not result:
            _, result = execute_round(sim, trial)
        s = score(state, sim, result)
        return BIG if s == INF else -BIG if s == -INF else s

    def choose(self, state, monster, options, plans):
        if len(options) == 1:
            return options[0]["id"]
        order = [m.id for m in plan_order(state)]
        best_id, best = options[0]["id"], None
        for option in options:
            s = sum(self._try(state, monster, option, plans, order, style)
                    for style in sorted(BOTS)) / len(BOTS)
            if best is None or s > best:
                best_id, best = option["id"], s
        return best_id