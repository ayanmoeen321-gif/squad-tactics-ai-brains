from engine.execution import execute_round
from engine.player import PlayerPhase
from engine.state import new_game


def scene(level, alive):
    s = new_game(level)
    for u in s.units.values():
        if u.id in alive:
            u.pos = alive[u.id]
        else:
            u.hp = 0
    return s


def adv(monster, dest):
    return {"monster": monster, "option": "advance", "kind": "advance",
            "target": None, "dest": dest}


def test_monster_that_cannot_reach_keeps_its_old_reservation():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8), "goblin_2": (4, 7)})
    for r, c in ((4, 5), (6, 5), (5, 4)):
        s.grid.tiles[r][c] = "#"
    plans = [adv("goblin_1", (5, 7)), adv("goblin_2", (4, 6))]
    events = PlayerPhase(s, plans).taunt("tank")
    assert events[0]["affected"] == ["goblin_1"]
    assert plans[0]["dest"] == (5, 6)
    assert plans[1] == adv("goblin_2", (4, 6))


def test_cover_tile_wins_the_tie():
    s = scene(1, {"tank": (5, 5), "goblin_1": (6, 7)})
    s.grid.tiles[6][5] = "C"
    plans = [adv("goblin_1", (6, 6))]
    PlayerPhase(s, plans).taunt("tank")
    assert plans[0]["dest"] == (6, 5)


def test_taunted_flag_is_on_the_events():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8)})
    plans = [adv("goblin_1", (5, 7))]
    PlayerPhase(s, plans).taunt("tank")
    events, _ = execute_round(s, plans)
    assert [e["type"] for e in events] == ["move", "attack"]
    assert all(e["taunted"] for e in events)


def test_taunted_flag_is_on_the_fallback_attack():
    s = scene(1, {"tank": (5, 5), "archer": (6, 6), "goblin_1": (5, 8)})
    plans = [adv("goblin_1", (5, 7))]
    PlayerPhase(s, plans).taunt("tank")
    s.units["tank"].pos = (9, 5)
    events, _ = execute_round(s, plans)
    assert events[-1]["target"] == "archer"
    assert events[-1]["fallback"] and events[-1]["taunted"]


def test_normal_plans_have_no_taunted_flag():
    s = scene(1, {"tank": (5, 5), "goblin_1": (5, 8)})
    plans = [{"monster": "goblin_1", "option": "attack_tank", "kind": "attack",
              "target": "tank", "dest": (5, 6)}]
    events, _ = execute_round(s, plans)
    assert all("taunted" not in e for e in events)