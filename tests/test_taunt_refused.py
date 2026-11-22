import pytest

from brains.scripted_brain import ScriptedBrain
from engine.combat import ActionError
from engine.game import Game


def test_taunt_with_no_monster_in_reach_is_refused():
    game = Game(0, 1, ScriptedBrain())
    tank = game.state.units["tank"]
    with pytest.raises(ActionError):
        game.phase.taunt("tank")
    assert tank.cooldown == 0
    assert game.phase.status["tank"]["acted"] is False