import argparse
import json
import os
import time

from brains.hero_bots import BOTS
from brains.laya_brain import LayaBrain
from brains.lookahead2_brain import Lookahead2Brain
from brains.shadow_brain import ShadowBrain
from eval.runner import run_game


def done_games(path):
    done = set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if r.get("game"):
                done.add((r["level"], r["bot"], r["seed"]))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", help="Laya checkpoint folder (the student)")
    ap.add_argument("--levels", default="3,4")
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--first-seed", type=int, default=350, help="dev seeds only: 0 to 49 stay reserved for the final evaluation")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.first_seed < 340:
        ap.error("use dev seeds from 340 up (0 to 49 are for the final evaluation)")
    import laya
    agent = laya.load(a.checkpoint, device=a.device)
    done = done_games(a.out)
    started, n = time.time(), 0
    with open(a.out, "a", encoding="utf-8") as f:
        for level in (int(x) for x in a.levels.split(",")):
            for bot in sorted(BOTS):
                for seed in range(a.first_seed, a.first_seed + a.seeds):
                    if (level, bot, seed) in done:
                        continue
                    brain = ShadowBrain(LayaBrain(agent, name="laya_d", version="run_d"), Lookahead2Brain())
                    summary = run_game(level, seed, brain, bot)
                    ctx = {"level": level, "bot": bot, "seed": seed}
                    for r in brain.records:
                        f.write(json.dumps({**ctx, **r}) + "\n")
                    f.write(json.dumps({**ctx, "game": True, "summary": summary}, default=str) + "\n")
                    f.flush()
                    n += 1
                    if n % 10 == 0:
                        print(f"{n} games, {time.time() - started:.0f} s", flush=True)
    print(f"done: {n} new games, {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()