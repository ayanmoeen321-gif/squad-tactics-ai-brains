from engine.combat import damage_against
from engine.movement import has_line_of_sight, is_chokepoint, manhattan, walk_distances

HERO_ORDER = ("tank", "archer", "healer")
WEAK_KINDS = ("archer", "healer")
MAX_PROTECT_OPTIONS = 2
MAX_HEAL_OPTIONS = 3
FAR = 10 ** 9


def make_plan(monster, option):
    return {"monster": monster.id, "option": option["id"], "kind": option["kind"],
            "target": option["target"], "dest": option["dest"]}


def wait_plan(monster):
    return {"monster": monster.id, "option": "wait", "kind": "wait",
            "target": None, "dest": monster.pos}


def effective_pos(unit, plans):
    """Where the unit will stand: its planned tile if it has planned, else where it is."""
    for p in plans:
        if p["monster"] == unit.id:
            return p["dest"]
    return unit.pos


def planned_damage(state, hero, plans):
    total = 0
    for p in plans:
        if p["kind"] == "attack" and p["target"] == hero.id:
            attacker = state.units[p["monster"]]
            total += damage_against(state, hero, attacker.damage, attacker.range > 1)
    return total


def _blocked(state, monster, plans):
    planned = {p["monster"] for p in plans}
    blocked = {p["dest"] for p in plans}
    for u in state.living():
        if u.id != monster.id and (u.side == "hero" or u.id not in planned):
            blocked.add(u.pos)
    return blocked


def _reachable(state, monster, plans):
    steps = walk_distances(state.grid, monster.pos, _blocked(state, monster, plans),
                           max_steps=monster.move)
    return {t: s for t, s in steps.items() if state.grid.tile(*t) != "L"}


def _pick(state, tiles, steps):
    return min(tiles, key=lambda t: (steps[t], state.grid.tile(*t) != "C", t[0], t[1]))


def _option(oid, kind, target, dest, steps):
    return {"id": oid, "kind": kind, "target": target, "dest": dest, "steps": steps[dest]}


def _can_hit_from(state, monster, tile, target):
    if manhattan(tile, target.pos) > monster.range:
        return False
    if monster.los and not has_line_of_sight(state.grid, tile, target.pos):
        return False
    return True


def _nearest_hero(state, pos, dist=None):
    if dist is None:
        dist = walk_distances(state.grid, pos)
    heroes = [h for h in state.heroes() if h.pos in dist]
    if not heroes:
        return None
    return min(heroes, key=lambda h: (dist[h.pos], HERO_ORDER.index(h.id)))


def _attack_options(state, monster, plans, reach):
    out = []
    for hid in HERO_ORDER:
        hero = state.units.get(hid)
        if hero is None or not hero.alive:
            continue
        if planned_damage(state, hero, plans) >= hero.hp:
            continue
        tiles = [t for t in reach if _can_hit_from(state, monster, t, hero)]
        if tiles:
            out.append(_option(f"attack_{hid}", "attack", hid, _pick(state, tiles, reach), reach))
    return out


def _advance_option(state, monster, reach):
    here = walk_distances(state.grid, monster.pos)
    near = _nearest_hero(state, monster.pos, here)
    if near is None:
        return None
    d = walk_distances(state.grid, near.pos)
    best = min(reach, key=lambda t: (d.get(t, FAR), reach[t],
                                     state.grid.tile(*t) != "C", t[0], t[1]))
    if d.get(best, FAR) >= d[monster.pos]:
        return None
    return _option("advance", "advance", None, best, reach)


def _flank_options(state, monster, reach):
    if monster.range != 1:
        return []
    out = []
    for hid in HERO_ORDER:
        hero = state.units.get(hid)
        if hero is None or not hero.alive:
            continue
        tiles = [t for t in reach if t != monster.pos and manhattan(t, hero.pos) == 1]
        if tiles:
            out.append(_option(f"flank_{hid}", "flank", hid, _pick(state, tiles, reach), reach))
    return out


def _hold_option(state, reach):
    tiles = [t for t in reach if is_chokepoint(state.grid, *t)]
    if not tiles:
        return None
    return _option("hold_chokepoint", "hold", None, _pick(state, tiles, reach), reach)


def _protect_options(state, monster, plans, reach):
    allies = [u for u in state.monsters()
              if u.id != monster.id and (u.hp * 2 < u.max_hp or u.kind in WEAK_KINDS)]
    allies.sort(key=lambda u: (u.hp, u.order))
    out = []
    for ally in allies:
        if len(out) == MAX_PROTECT_OPTIONS:
            break
        apos = effective_pos(ally, plans)
        hero = _nearest_hero(state, apos)
        if hero is None:
            continue
        gap = manhattan(apos, hero.pos)
        tiles = [t for t in reach
                 if t != apos and manhattan(t, apos) + manhattan(t, hero.pos) == gap]
        if tiles:
            out.append(_option(f"protect_{ally.id}", "protect", ally.id,
                               _pick(state, tiles, reach), reach))
    return out


def _retreat_option(state, monster, reach):
    if monster.hp * 2 >= monster.max_hp:
        return None
    maps = [walk_distances(state.grid, h.pos) for h in state.heroes()]
    if not maps:
        return None

    def away(t):
        return min(m.get(t, FAR) for m in maps)

    best = min(reach, key=lambda t: (-away(t), reach[t],
                                     state.grid.tile(*t) != "C", t[0], t[1]))
    if away(best) <= away(monster.pos):
        return None
    return _option("retreat", "retreat", None, best, reach)


def _heal_options(state, monster, plans, reach):
    if monster.heal is None:
        return []
    hurt = [u for u in state.monsters() if u.id != monster.id and u.hp < u.max_hp]
    hurt.sort(key=lambda u: (u.hp, u.order))
    out = []
    for ally in hurt:
        if len(out) == MAX_HEAL_OPTIONS:
            break
        apos = effective_pos(ally, plans)
        tiles = [t for t in reach if manhattan(t, apos) <= monster.heal["range"]]
        if tiles:
            out.append(_option(f"heal_{ally.id}", "heal", ally.id,
                               _pick(state, tiles, reach), reach))
    return out


def legal_options(state, monster, plans):
    """Legal options in the fixed order: attack, advance, flank, hold, protect, retreat, heal."""
    reach = _reachable(state, monster, plans)
    if not reach:
        return []
    options = _attack_options(state, monster, plans, reach)
    for single in (_advance_option(state, monster, reach),):
        if single:
            options.append(single)
    options += _flank_options(state, monster, reach)
    hold = _hold_option(state, reach)
    if hold:
        options.append(hold)
    options += _protect_options(state, monster, plans, reach)
    retreat = _retreat_option(state, monster, reach)
    if retreat:
        options.append(retreat)
    options += _heal_options(state, monster, plans, reach)
    return options