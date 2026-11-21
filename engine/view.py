from engine.combat import skill_ready
from engine.movement import has_line_of_sight, manhattan, walk_distances
from engine.options import HERO_ORDER, _can_hit_from, _reachable
from engine.state import MAX_ROUNDS

ROLE = {"goblin": "fast, weak melee", "brute": "tough melee blocker",
        "archer": "fragile ranged", "healer": "support healer"}
LEGEND = ("straight = tiles in a line, ignoring walls. "
          "walk = steps you would really walk, around walls. In reach uses walk.")


def _hp(u):
    return f"{u.hp}/{u.max_hp}"


def _plan_text(state, p):
    kind, target = p["kind"], p["target"]
    if kind in ("attack", "flank", "heal", "protect"):
        return f"{kind} {state.units[target].label}"
    if kind == "hold":
        return f"hold chokepoint {p['dest']}"
    return kind


def _option_text(state, o, plans):
    kind, target = o["kind"], o["target"]
    if kind == "attack":
        hero = state.units[target]
        cover = ", on cover" if state.grid.tile(*hero.pos) == "C" else ""
        also = [state.units[p["monster"]].label for p in plans
                if p["kind"] == "attack" and p["target"] == target]
        tail = f" {', '.join(also)} also attacking." if also else ""
        return f"hit the {hero.label} (HP {_hp(hero)}{cover}).{tail}"
    if kind == "advance":
        return "walk toward the nearest hero."
    if kind == "flank":
        return f"go to a free side of the {state.units[target].label}."
    if kind == "hold":
        return f"hold the doorway at {o['dest']}."
    if kind == "protect":
        ally = state.units[target]
        return f"guard {ally.label} (HP {_hp(ally)})."
    if kind == "retreat":
        return "walk away from the heroes."
    ally = state.units[target]
    return f"heal {ally.label} (HP {_hp(ally)})."


def threats_at(state, tile):
    """Heroes that could hit `tile` next turn (walk up to their move, then attack).
    Uses only positions and stats, never the player's choices."""
    names = []
    for hid in HERO_ORDER:
        h = state.units.get(hid)
        if h is None or not h.alive:
            continue
        blocked = {u.pos for u in state.living() if u.id != h.id}
        steps = walk_distances(state.grid, h.pos, blocked, max_steps=h.move)
        for t in steps:
            if t == tile or manhattan(t, tile) > h.range:
                continue
            if h.los and not has_line_of_sight(state.grid, t, tile):
                continue
            names.append(h.label)
            break
    return names


def build_monster_view(state, monster, options, plans):
    """State + question text for one monster. Returns a dict with the parts."""
    walk = walk_distances(state.grid, monster.pos)
    reach = _reachable(state, monster, plans)
    lines = [f"Round {state.round} of {MAX_ROUNDS}. You are {monster.label}: "
             f"{ROLE.get(monster.kind, monster.kind)}. HP {_hp(monster)}. Tile {monster.pos}.",
             "Heroes:"]
    for hid in HERO_ORDER:
        h = state.units.get(hid)
        if h is None or not h.alive:
            continue
        w = walk.get(h.pos)
        in_reach = any(_can_hit_from(state, monster, t, h) for t in reach)
        lines.append(
            f"- {h.label}: HP {_hp(h)}, straight {manhattan(monster.pos, h.pos)}, "
            f"walk {w if w is not None else 'none'}, "
            f"{'in reach' if in_reach else 'not in reach'}, "
            f"{'on cover' if state.grid.tile(*h.pos) == 'C' else 'no cover'}, "
            f"skill {'ready' if skill_ready(h) else 'not ready'}")
    thr = threats_at(state, monster.pos)
    lines.append("Heroes that can hit you here next turn: " + (", ".join(thr) if thr else "none") + ".")
    if plans:
        lines.append("Earlier plans this round:")
        for p in plans:
            u = state.units[p["monster"]]
            lines.append(f"- {u.label} (HP {_hp(u)}): {_plan_text(state, p)}")
    state_text = "\n".join(lines)
    opt_lines = [(o["id"], _option_text(state, o, plans)) for o in options]
    question = "\n".join([f"Which action should {monster.label} take?", LEGEND, "Options:"]
                         + [f"{oid}: {txt}" for oid, txt in opt_lines])
    return {"state": state_text, "question": question, "options": opt_lines,
            "text": f"STATE\n{state_text}\n\nQUESTION\n{question}"}


def rough_tokens(text):
    """Rough proxy (3 characters per token, on the safe side). The real tokenizer count
    comes in the Laya smoke test."""
    return len(text) / 3