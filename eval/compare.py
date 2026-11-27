import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from brains.baseline_brains import AlwaysAttackBrain
from brains.hero_bots import BOTS
from brains.random_brain import RandomBrain
from brains.scripted_brain import ScriptedBrain
from eval.runner import run_game

EVAL_SEEDS = range(50)


def make_brain(name, seed, laya_agent=None):
    if name == "random":
        return RandomBrain(seed)  # seeded per game, so reruns are identical
    if name == "scripted":
        return ScriptedBrain()
    if name == "always_attack":
        return AlwaysAttackBrain()
    if name == "lookahead2":
        from brains.lookahead2_brain import Lookahead2Brain
        return Lookahead2Brain()
    if name == "laya_b":
        from brains.laya_brain import LayaBrain
        return LayaBrain(laya_agent, name="laya_b", version="run_b_e4")
    if name == "lookahead":
        from brains.lookahead_brain import LookaheadBrain
        return LookaheadBrain()
    if name == "laya_a":
        from brains.laya_brain import LayaBrain
        return LayaBrain(laya_agent, name="laya_a", version="run_e4")
    if name == "kev_zero":
        from brains.laya_brain import LayaBrain
        return LayaBrain(laya_agent, name="kev_zero", version="remote")
    if name == "laya_rev":
        from brains.laya_brain import LayaBrain
        from eval.option_order import ReversedBrain
        return ReversedBrain(LayaBrain(laya_agent, name="laya_rev", version="reversed"))
    raise ValueError(name)


def compare(names, laya_agent=None, seeds=EVAL_SEEDS, levels=(1, 2, 3), log_dir=None):
    """Same seeds, shuffled starts and hero bots for every brain."""
    results = defaultdict(list)
    for name in names:
        for level in levels:
            for bot in sorted(BOTS):
                for seed in seeds:
                    brain = make_brain(name, seed, laya_agent)
                    results[(name, level)].append(
                        run_game(level, seed, brain, bot, log_dir=log_dir))
    return results


def wilson(wins, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return centre - half, centre + half


def rate(results, name, level=None):
    rs = [r for (n, lv), v in results.items()
          if n == name and (level is None or lv == level) for r in v]
    return sum(r["outcome"] == "win" for r in rs), len(rs)


def fallback_reasons(log_dir, name):
    path = Path(log_dir) / "decisions.jsonl"
    counts = Counter()
    if not path.exists():
        return counts
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["brain"] == name and d.get("fallback"):
                counts[d.get("fallback_reason", "unknown")] += 1
    return counts


def report(results, log_dir=None):
    print("Hero win rate (lower = better monsters). 95% interval in brackets.")
    print(f"{'brain':14} {'level':5} {'games':>5} {'hero win%':>9} {'95% CI':>13} "
          f"{'fallback%':>9} {'ms/dec':>7} {'wall s':>7}")
    for (name, level), rs in sorted(results.items()):
        wins = sum(r["outcome"] == "win" for r in rs)
        lo, hi = wilson(wins, len(rs))
        dec = sum(r["decisions"] for r in rs)
        fb = sum(r["fallbacks"] for r in rs)
        ms = 1000 * sum(r["model_time"] for r in rs) / max(dec, 1)
        wall = sum(r["wall_time"] for r in rs)
        print(f"{name:14} {level:<5} {len(rs):>5} {100 * wins / len(rs):>8.1f}% "
              f"[{100 * lo:4.1f},{100 * hi:5.1f}] {100 * fb / max(dec, 1):>8.1f}% "
              f"{ms:>7.2f} {wall:>7.1f}")
    names = {n for n, _ in results}
    model = next((n for n in ("laya_a", "laya_b") if n in names), None)
    if model:
        print("\nModel minus baseline, in percentage points of hero win rate "
              "(negative = the model is better for the monsters):")
        for level in sorted({lv for _, lv in results}) + [None]:
            w, n = rate(results, model, level)
            if n == 0:
                continue
            parts = []
            for base in ("always_attack", "scripted", "lookahead2", "random"):
                bw, bn = rate(results, base, level)
                if bn:
                    parts.append(f"vs {base} {100 * (w / n - bw / bn):+.1f} pp")
            print(f"  level {level if level else 'all'}: " + ", ".join(parts))
        if log_dir:
            reasons = fallback_reasons(log_dir, model)
            print(f"\n{model} fallbacks by reason:",
                  dict(reasons) if reasons else "none")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", nargs="?", help="Laya checkpoint folder (adds laya_a, or the brain named by --as)")
    ap.add_argument("--as", dest="brain", default="laya_a", help="name for the checkpoint brain: laya_a or laya_b")
    ap.add_argument("--brains", default="random,scripted,always_attack", help="comma list of non-model brains")
    ap.add_argument("--seeds", type=int, default=50)
    ap.add_argument("--levels", default="1,2,3")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--remote", default=None, help="URL of a System One server (Kev or Laya); plays that model instead of loading a checkpoint")
    ap.add_argument("--remote-model", default="kev-latest", help="model name sent to the server")
    ap.add_argument("--log-dir", default=None)
    a = ap.parse_args()
    log_dir = a.log_dir or time.strftime("logs/compare_%Y%m%d_%H%M%S")
    names = a.brains.split(",")
    agent = None
    if a.remote:
        from brains.remote_agent import RemoteAgent
        agent = RemoteAgent(a.remote, model=a.remote_model)
        names.append(a.brain)
    elif a.checkpoint:
        import laya
        agent = laya.load(a.checkpoint, device=a.device)
        names.append(a.brain)
    levels = tuple(int(x) for x in a.levels.split(","))
    started = time.time()
    res = compare(names, agent, seeds=range(a.seeds), levels=levels, log_dir=log_dir)
    report(res, log_dir)
    print(f"\ntotal seconds: {time.time() - started:.0f}  logs: {log_dir}")