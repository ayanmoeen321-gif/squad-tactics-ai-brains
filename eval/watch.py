import sys

from brains.hero_bots import make_bot
from brains.random_brain import RandomBrain
from brains.scripted_brain import ScriptedBrain
from engine.game import Game
from engine.render import render
from eval.runner import hero_start_order


def describe(e):
    t = e["type"]
    if t == "move":
        return f"{e['unit']} moves {e['from']} -> {e['to']}"
    if t == "attack":
        extra = " (fallback)" if e.get("fallback") else ""
        extra += " (taunted)" if e.get("taunted") else ""
        kill = " KILLED" if e["killed"] else ""
        return f"{e['attacker']} hits {e['target']} for {e['damage']}{kill}{extra}"
    if t == "piercing_shot":
        kill = " KILLED" if e["killed"] else ""
        return f"{e['attacker']} shoots {e['target']} for {e['damage']}{kill}"
    if t == "heal":
        return f"{e['healer']} heals {e['target']} (+{e['restored']})"
    if t == "lava":
        return f"lava hits {e['target']} for {e['damage']}"
    if t == "taunt":
        return f"{e['unit']} taunts {e['affected']}"
    return str(e)


def hp_line(state):
    heroes = " ".join(f"{h.id}:{h.hp}" for h in state.heroes())
    monsters = " ".join(f"{m.id}:{m.hp}" for m in state.monsters())
    return f"HEROES {heroes}\nMONSTERS {monsters}"


def watch(level, seed, bot_style, brain_name="scripted"):
    brain = ScriptedBrain() if brain_name == "scripted" else RandomBrain(seed)
    game = Game(level, seed, brain, hero_start_order=hero_start_order(seed))
    bot = make_bot(bot_style, seed)
    print(f"Level {level}, seed {seed}, bot {bot_style}, brain {brain_name}")
    for _ in range(35):
        if game.result:
            break
        state = game.state
        print(f"\n=== ROUND {state.round} ===")
        print(hp_line(state))
        print("Monster plans:")
        for p in game.plans:
            print(f"  {p['monster']}: {p['option']} -> {p['dest']}")
        events = bot.play(game.phase)
        print("Heroes do:")
        for e in events:
            print("  " + describe(e))
        print(render(state))
        if game.phase.result() == "win":
            game.result = "win"
            break
        for e in game.end_turn():
            print("  " + describe(e))
        if bot.errors:
            print("BOT ERRORS:", bot.errors)
            return
    print(f"\nRESULT: {game.result} after round {game.state.round}")


if __name__ == "__main__":
    watch(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])