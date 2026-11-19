from engine.movement import has_line_of_sight, manhattan
from engine.state import MAX_ROUNDS

LAVA_DAMAGE = 3
COVER_REDUCTION = 1
LINE_DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


class ActionError(ValueError):
    pass


def skill_ready(unit):
    return unit.skill is not None and unit.cooldown == 0


def in_attack_range(state, attacker, target):
    if not (attacker.alive and target.alive):
        return False
    if attacker.side == target.side:
        return False
    if manhattan(attacker.pos, target.pos) > attacker.range:
        return False
    if attacker.los and not has_line_of_sight(state.grid, attacker.pos, target.pos):
        return False
    return True


def damage_against(state, target, base, ranged):
    """Cover cuts ranged damage by 1 (minimum 1). Melee ignores cover."""
    if ranged and state.grid.tile(*target.pos) == "C":
        return max(1, base - COVER_REDUCTION)
    return base


def _hurt(unit, amount):
    dealt = min(unit.hp, amount)
    unit.hp -= dealt
    return dealt


def attack(state, attacker, target):
    if not in_attack_range(state, attacker, target):
        raise ActionError(f"{attacker.id} cannot attack {target.id}")
    dmg = damage_against(state, target, attacker.damage, attacker.range > 1)
    dealt = _hurt(target, dmg)
    return {"type": "attack", "attacker": attacker.id, "target": target.id,
            "damage": dealt, "killed": not target.alive}


def piercing_shot(state, hero, direction):
    if (not hero.alive or hero.side != "hero" or not hero.skill
            or hero.skill["name"] != "piercing_shot"):
        raise ActionError(f"{hero.id} cannot use piercing shot")
    if direction not in LINE_DIRS:
        raise ActionError(f"bad direction {direction!r}")
    if not skill_ready(hero):
        raise ActionError("piercing shot is on cooldown")
    dr, dc = LINE_DIRS[direction]
    r, c = hero.pos
    events = []
    for _ in range(hero.range):
        r, c = r + dr, c + dc
        if not state.grid.is_walkable(r, c):
            break
        target = state.unit_at((r, c))
        if target is not None and target.side == "monster":
            dmg = damage_against(state, target, hero.skill["damage"], True)
            dealt = _hurt(target, dmg)
            events.append({"type": "piercing_shot", "attacker": hero.id,
                           "target": target.id, "damage": dealt,
                           "killed": not target.alive})
    hero.cooldown = hero.skill["cooldown"]
    return events


def heal(state, healer, target):
    if not healer.alive or not target.alive:
        raise ActionError("dead units cannot heal or be healed")
    if healer.side != target.side or healer.id == target.id:
        raise ActionError("can only heal another ally")
    if healer.side == "hero":
        if not healer.skill or healer.skill["name"] != "heal":
            raise ActionError(f"{healer.id} cannot heal")
        if not skill_ready(healer):
            raise ActionError("heal is on cooldown")
        amount, rng = healer.skill["amount"], healer.skill["range"]
    else:
        if not healer.heal:
            raise ActionError(f"{healer.id} cannot heal")
        amount, rng = healer.heal["amount"], healer.heal["range"]
    if manhattan(healer.pos, target.pos) > rng:
        raise ActionError("target out of heal range")
    restored = min(amount, target.max_hp - target.hp)
    target.hp += restored
    if healer.side == "hero":
        healer.cooldown = healer.skill["cooldown"]
    return {"type": "heal", "healer": healer.id, "target": target.id,
            "restored": restored}


def apply_lava(state, side):
    events = []
    for u in state.living(side):
        if state.grid.tile(*u.pos) == "L":
            dealt = _hurt(u, LAVA_DAMAGE)
            events.append({"type": "lava", "target": u.id, "damage": dealt,
                           "killed": not u.alive})
    return events


def outcome(state, round_over=False):
    """'win', 'lose' or None. Timeout is a loss, checked only at the end of a round."""
    if not state.heroes():
        return "lose"
    if not state.monsters():
        return "win"
    if round_over and state.round >= MAX_ROUNDS:
        return "lose"
    return None