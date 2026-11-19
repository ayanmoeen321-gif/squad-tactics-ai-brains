import json

import pytest

import eval.runner as runner
from brains.hero_bots import BOTS, ORDER, AggressiveBot
from brains.random_brain import RandomBrain
from brains.scripted_brain import ScriptedBrain
from engine.combat import ActionError
from engine.game import Game
from engine.state import new_game
from eval.runner import RunnerError, hero_start_order, round_flags, run_game

TIMING = ("model_time", "worst_decision", "wall_time")
BRAINS = {"random": lambda seed: RandomBrain(seed),
          "scripted": lambda seed: ScriptedBrain()}


def strip(summary):
    return {k: v for k, v in summary.items() if k not in TIMING}


def atk(attacker, target):
    return {"type": "attack", "attacker": attacker, "target": target, "damage": 1}


def duel():
    s = new_game(1)
    s.units["tank"].pos = (5, 5)
    s.units["goblin_1"].pos = (5, 6)
    s.units["goblin_2"].pos = (4, 5)
    return s


def test_summary_fields():
    s = run_game(1, 1, ScriptedBrain(), "aggressive")
    assert s["outcome"] in ("win", "lose")
    assert s["brain"] == "scripted" and s["bot"] == "aggressive"
    assert 1 <= s["rounds"] <= 30
    assert s["decisions"] > 0
    assert {"schema_version", "game_id", "seed", "level", "swap_order", "heroes_alive",
            "monster_rounds", "focus_fire_rounds", "flanking_rounds",
            "protecting_rounds", "taunt_count", "model_time",
            "worst_decision"} <= set(s)


def test_same_inputs_same_summary():
    a = run_game(2, 5, RandomBrain(5), "focus")
    b = run_game(2, 5, RandomBrain(5), "focus")
    assert strip(a) == strip(b)


def test_logs_are_written_and_read_by_themselves(tmp_path):
    s = run_game(2, 3, ScriptedBrain(), "focus", log_dir=tmp_path)
    lines = (tmp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    decisions = [json.loads(x) for x in lines]
    games = [json.loads(x) for x in
             (tmp_path / "games.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(games) == 1 and games[0]["game_id"] == s["game_id"]
    assert len(decisions) == s["decisions"]
    needed = {"schema_version", "seed", "brain", "level", "bot", "round", "monster",
              "options", "chosen", "position", "latency", "swap_order"}
    for d in decisions:
        assert needed <= set(d)
        assert d["schema_version"] == 1 and d["seed"] == 3 and d["level"] == 2
        assert d["options"][d["position"]] == d["chosen"]
    assert decisions[0]["round"] == 1


def test_hero_bot_error_aborts_the_run(monkeypatch):
    class Broken(AggressiveBot):
        def _act(self, phase, hero):
            raise ActionError("boom")

    monkeypatch.setattr(runner, "make_bot", lambda style, seed=0: Broken(seed))
    with pytest.raises(RunnerError):
        run_game(1, 1, ScriptedBrain(), "aggressive")


def test_start_order_is_a_permutation_and_varies():
    orders = {hero_start_order(s) for s in range(10)}
    assert all(sorted(o) == sorted(ORDER) for o in orders)
    assert len(orders) > 1
    assert hero_start_order(3) == hero_start_order(3)


def test_swap_order_is_written_to_the_summary():
    assert run_game(1, 4, ScriptedBrain(), "focus")["swap_order"] == list(hero_start_order(4))
    assert run_game(1, 4, ScriptedBrain(), "focus", swap_starts=False)["swap_order"] is None


def test_game_without_the_runner_keeps_the_map_as_designed():
    plain = new_game(1)
    g = Game(1, 1, RandomBrain(1))
    for hero in ORDER:
        assert g.state.units[hero].pos == plain.units[hero].pos


def test_swap_puts_heroes_on_other_start_tiles():
    plain = new_game(1)
    g = Game(1, 1, RandomBrain(1), hero_start_order=("archer", "tank", "healer"))
    assert g.state.units["tank"].pos == plain.units["archer"].pos
    assert g.state.units["archer"].pos == plain.units["tank"].pos
    assert g.state.units["healer"].pos == plain.units["healer"].pos
    with pytest.raises(ValueError):
        Game(1, 1, RandomBrain(1), hero_start_order=("tank", "tank", "healer"))


def test_flags_focus_and_flank():
    s = duel()
    assert round_flags(s, [atk("goblin_1", "tank"), atk("goblin_2", "tank")], []) == (True, True, False)
    assert round_flags(s, [atk("goblin_1", "tank")], []) == (False, False, False)


def test_flags_count_fallback_and_taunted_attacks():
    s = duel()
    events = [{**atk("goblin_1", "tank"), "fallback": True},
              {**atk("goblin_2", "tank"), "taunted": True}]
    assert round_flags(s, events, []) == (True, True, False)


def test_flags_ranged_attacker_is_not_a_flank():
    s = new_game(1)
    s.units["tank"].pos = (5, 5)
    s.units["goblin_1"].pos = (5, 6)
    s.units["archer_1"].pos = (5, 9)
    assert round_flags(s, [atk("goblin_1", "tank"), atk("archer_1", "tank")], []) == (True, False, False)


def test_protect_counts_only_if_the_monster_reached_its_tile():
    s = new_game(1)
    plans = [{"monster": "goblin_1", "option": "protect_archer_1", "kind": "protect",
              "target": "archer_1", "dest": (5, 8)}]
    s.units["goblin_1"].pos = (5, 8)
    assert round_flags(s, [], plans) == (False, False, True)
    s.units["goblin_1"].pos = (5, 9)
    assert round_flags(s, [], plans) == (False, False, False)


def test_metrics_stay_within_the_rounds_played():
    s = run_game(3, 2, ScriptedBrain(), "defensive")
    assert s["monster_rounds"] <= s["rounds"]
    for key in ("focus_fire_rounds", "flanking_rounds", "protecting_rounds"):
        assert 0 <= s[key] <= s["monster_rounds"]


@pytest.mark.parametrize("brain", sorted(BRAINS))
@pytest.mark.parametrize("style", sorted(BOTS))
@pytest.mark.parametrize("level", [1, 2, 3])
def test_every_combination_finishes(brain, style, level):
    s = run_game(level, 2, BRAINS[brain](2), style)
    assert s["outcome"] in ("win", "lose")