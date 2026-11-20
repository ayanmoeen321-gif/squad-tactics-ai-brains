from engine.view import build_monster_view


def to_laya_row(state, monster, options, plans, chosen_id=None):
    """One {state, questions, gold/expected} row for Laya from one monster decision."""
    view = build_monster_view(state, monster, options, plans)
    question = {
        "type": "choice",
        "instructions": view["question"].split("\nOptions:")[0],
        "criteria": {oid: txt for oid, txt in view["options"]},
    }
    row = {"state": view["state"], "questions": {"action": question}}
    if chosen_id is not None:
        row["expected"] = {"action": chosen_id}
    return row