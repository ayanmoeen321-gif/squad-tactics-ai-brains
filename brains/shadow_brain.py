from brains.hero_bots import BOTS
from engine.planning import plan_order


class ShadowBrain:
    """The student brain plays. At every decision with 2 or more options the teacher (lookahead2) also scores
    each option on the SAME state; the game follows the student, the teacher only watches.
    records: one dict per such decision. regret = the teacher's best score minus the teacher's score for the
    student's pick (0 = equal value). Scores are the teacher's own estimates; a game win or loss counts 1000."""
    name = "shadow"
    version = "1"

    def __init__(self, student, teacher):
        self.student = student
        self.teacher = teacher
        self.records = []
        self.last_info = None

    def teacher_scores(self, state, monster, options, plans):
        order = [m.id for m in plan_order(state)]
        scores = {}
        for option in options:
            total = sum(self.teacher._try(state, monster, option, plans, order, style)
                        for style in sorted(BOTS))
            scores[option["id"]] = total / len(BOTS)
        return scores

    def choose(self, state, monster, options, plans):
        chosen = self.student.choose(state, monster, options, plans)
        info = getattr(self.student, "last_info", None) or {}
        self.last_info = info or None
        if len(options) < 2:
            return chosen
        scores = self.teacher_scores(state, monster, options, plans)
        best_id, best = options[0]["id"], None
        for option in options:
            s = scores[option["id"]]
            if best is None or s > best:
                best_id, best = option["id"], s
        self.records.append({
            "round": state.round, "monster": monster.id, "kind": monster.kind,
            "options": [o["id"] for o in options], "student": chosen, "teacher": best_id,
            "scores": {k: round(v, 3) for k, v in scores.items()},
            "regret": round(best - scores[chosen], 3) if chosen in scores else None,
            "fallback": bool(info.get("fallback")),
            "probabilities": info.get("probabilities"),
        })
        return chosen