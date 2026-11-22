from brains.scripted_brain import ScriptedBrain
from engine.game import Game
from server.app import _view


def test_incoming_counts_planned_attack_and_skips_dead_monsters():
    game = Game(1, 0, ScriptedBrain())
    s = game.state
    tank = s.units["tank"]
    m = s.units["goblin_1"]
    m.pos = (tank.pos[0], tank.pos[1] + 1)
    game.plans[:] = [{"monster": "goblin_1", "option": "attack_tank", "kind": "attack",
                      "target": "tank", "dest": m.pos}]
    heroes = _view(game)["heroes"]
    assert heroes["tank"]["incoming"] == 2
    assert heroes["tank"]["attackers"] == ["goblin_1"]
    assert heroes["archer"]["incoming"] == 0
    m.hp = 0
    heroes = _view(game)["heroes"]
    assert heroes["tank"]["incoming"] == 0
    assert heroes["tank"]["attackers"] == []