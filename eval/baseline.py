import sys
from collections import defaultdict

from brains.hero_bots import BOTS
from brains.random_brain import RandomBrain
from brains.scripted_brain import ScriptedBrain
from eval.runner import run_game

BRAINS = {"random": RandomBrain, "scripted": lambda seed: ScriptedBrain()}


def rate(rows):
    return f"{100 * sum(r['outcome'] == 'win' for r in rows) / len(rows):5.1f}% (n={len(rows)})"


def main(seeds=20, log_dir="logs/baseline"):
    rows = []
    for brain_name, make in BRAINS.items():
        for level in (1, 2, 3):
            for bot in sorted(BOTS):
                for seed in range(seeds):
                    rows.append(run_game(level, seed, make(seed), bot, log_dir=log_dir))

    def table(title, keyfn, only=None):
        groups = defaultdict(list)
        for r in rows:
            if only is None or only(r):
                groups[keyfn(r)].append(r)
        print(f"\n{title}")
        for key in sorted(groups):
            print(f"  {str(key):42s} {rate(groups[key])}")

    scripted = lambda r: r["brain"] == "scripted"
    table("Hero win rate by brain and level", lambda r: (r["brain"], r["level"]))
    table("Hero win rate by brain and hero bot", lambda r: (r["brain"], r["bot"]))
    table("Hero win rate by level and start order (scripted)",
          lambda r: (r["level"], tuple(r["swap_order"])), only=scripted)
    avg = sum(r["rounds"] for r in rows) / len(rows)
    print(f"\nAverage rounds per game: {avg:.1f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)