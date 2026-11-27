from collections import defaultdict

from brains.hero_bots import BOTS
from brains.scripted_brain import ScriptedBrain
from eval.runner import run_game

rows = defaultdict(list)
for level in (1, 2, 3):
    for bot in sorted(BOTS):
        for seed in range(50):
            rows[level].append(run_game(level, seed, ScriptedBrain(), bot))

for level, rs in rows.items():
    wins = [r for r in rs if r["outcome"] == "win"]
    losses = [r for r in rs if r["outcome"] == "lose"]
    timeouts = [r for r in losses if r["rounds"] >= 30]
    print(f"\nLevel {level}: {len(wins)} wins, {len(losses)} losses ({len(timeouts)} timeouts)")
    if wins:
        print(f"  wins:   avg rounds {sum(r['rounds'] for r in wins)/len(wins):.1f}, "
              f"avg hero HP left {sum(r['hero_hp'] for r in wins)/len(wins):.1f}")
    if losses:
        print(f"  losses: avg rounds {sum(r['rounds'] for r in losses)/len(losses):.1f}, "
              f"avg monsters left {sum(r['monsters_alive'] for r in losses)/len(losses):.1f}")