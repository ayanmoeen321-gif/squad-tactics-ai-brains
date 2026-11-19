import json
import random
import time
from pathlib import Path

from brains.hero_bots import ORDER, make_bot
from engine.game import Game

SCHEMA_VERSION = 1
MAX_LOOPS = 40


class RunnerError(RuntimeError):
    """A run must stop, for example because a hero bot recorded an error."""


def hero_start_order(seed):
    """Shuffled hero start tiles. Own RNG stream, separate from the bot and engine RNGs."""
    order = list(ORDER)
    random.Random(f"start:{seed}").shuffle(order)
    return tuple(order)


class LoggingBrain:
    """Wraps a brain: times every decision and writes one log line for it.
    Later fields (state text, probabilities, fallback) are added only when they exist."""

    def __init__(self, brain, context, sink=None):
        self.brain = brain
        self.context = context
        self.sink = sink
        self.name = getattr(brain, "name", type(brain).__name__)
        self.calls = 0
        self.total_time = 0.0
        self.worst = 0.0
        self.positions = {}

    def choose(self, state, monster, options, plans):
        start = time.perf_counter()
        chosen = self.brain.choose(state, monster, options, plans)
        latency = time.perf_counter() - start
        ids = [o["id"] for o in options]  # in the order they were presented
        position = ids.index(chosen) if chosen in ids else -1
        self.calls += 1
        self.total_time += latency
        self.worst = max(self.worst, latency)
        self.positions[position] = self.positions.get(position, 0) + 1
        if self.sink:
            self.sink({**self.context, "round": state.round, "monster": monster.id,
                       "options": ids, "chosen": chosen, "position": position,
                       "latency": round(latency, 6)})
        return chosen


def round_flags(state, events, plans):
    """(focus_fire, flanking, protecting) for one monster phase, after execution.
    Attack events count whether normal, fallback or taunted.
    Focus fire: one hero attacked by 2+ monsters. Flanking: one hero attacked by melee
    monsters from 2+ different sides. Protecting: a protect plan whose monster ended
    on its planned tile."""
    by_target = {}
    for e in events:
        if e["type"] == "attack":
            by_target.setdefault(e["target"], []).append(e["attacker"])
    focus = any(len(a) >= 2 for a in by_target.values())
    flank = False
    for target, attackers in by_target.items():
        hero = state.units[target]
        sides = set()
        for aid in attackers:
            m = state.units[aid]
            if m.range == 1:
                sides.add((m.pos[0] - hero.pos[0], m.pos[1] - hero.pos[1]))
        if len(sides) >= 2:
            flank = True
    protect = any(p["kind"] == "protect"
                  and state.units[p["monster"]].alive
                  and state.units[p["monster"]].pos == p["dest"]
                  for p in plans)
    return focus, flank, protect


def _play(level, seed, brain, hero_bot, swap_starts, decision_sink):
    started = time.perf_counter()
    brain_name = getattr(brain, "name", type(brain).__name__)
    game_id = f"{brain_name}-{hero_bot}-L{level}-S{seed}"
    order = hero_start_order(seed) if swap_starts else None
    context = {"schema_version": SCHEMA_VERSION, "game_id": game_id, "seed": seed,
               "level": level, "brain": brain_name, "bot": hero_bot,
               "swap_order": list(order) if order else None}
    wrapped = LoggingBrain(brain, context, decision_sink)
    game = Game(level, seed, wrapped, hero_start_order=order)
    bot = make_bot(hero_bot, seed)

    monster_rounds = focus_rounds = flank_rounds = protect_rounds = taunts = 0
    loops = 0
    while not game.result:
        loops += 1
        if loops > MAX_LOOPS:
            raise RunnerError(f"{game_id}: game did not finish")
        events = bot.play(game.phase)
        if bot.errors:
            raise RunnerError(f"{game_id}: hero bot errors: {bot.errors}")
        taunts += sum(1 for e in events if e["type"] == "taunt")
        if game.phase.result() == "win":
            game.result = "win"
            break
        live_plans = [dict(p) for p in game.plans
                      if game.state.units[p["monster"]].alive]
        round_events = game.end_turn()
        monster_rounds += 1
        focus, flank, protect = round_flags(game.state, round_events, live_plans)
        focus_rounds += focus
        flank_rounds += flank
        protect_rounds += protect

    state = game.state
    return {
        **context,
        "brain_version": getattr(brain, "version", None),
        "outcome": game.result,
        "rounds": state.round,
        "heroes_alive": len(state.heroes()),
        "hero_hp": sum(h.hp for h in state.heroes()),
        "monsters_alive": len(state.monsters()),
        "monster_rounds": monster_rounds,
        "focus_fire_rounds": focus_rounds,
        "flanking_rounds": flank_rounds,
        "protecting_rounds": protect_rounds,
        "taunt_count": taunts,
        "decisions": wrapped.calls,
        "position_counts": wrapped.positions,
        "model_time": round(wrapped.total_time, 6),
        "worst_decision": round(wrapped.worst, 6),
        "wall_time": round(time.perf_counter() - started, 6),
    }


def run_game(level, seed, brain, hero_bot, log_dir=None, swap_starts=True):
    """Plays one full headless game. Returns the summary dict.
    With log_dir: appends decision lines and one summary line (JSON) there."""
    decisions = games = None
    try:
        sink = None
        if log_dir is not None:
            folder = Path(log_dir)
            folder.mkdir(parents=True, exist_ok=True)
            decisions = open(folder / "decisions.jsonl", "a", encoding="utf-8", newline="\n")
            games = open(folder / "games.jsonl", "a", encoding="utf-8", newline="\n")

            def sink(record):
                decisions.write(json.dumps(record) + "\n")

        summary = _play(level, seed, brain, hero_bot, swap_starts, sink)
        if games:
            games.write(json.dumps(summary) + "\n")
        return summary
    finally:
        for f in (decisions, games):
            if f:
                f.close()