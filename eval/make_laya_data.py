import json
import sys
from pathlib import Path

from brains.hero_bots import BOTS, make_bot
from brains.scripted_brain import ScriptedBrain
from engine.game import Game
from eval.laya_export import to_laya_row
from eval.runner import hero_start_order

TRAIN_SEED_START = 1000  # evaluation seeds are 0..49; training seeds never overlap
MAX_LOOPS = 40


def make_teacher(name):
    if name == "scripted":
        return ScriptedBrain()
    if name == "lookahead2":
        from brains.lookahead2_brain import Lookahead2Brain
        return Lookahead2Brain()
    raise ValueError(f"unknown teacher {name!r}")


class _Rec:
    def __init__(self, teacher="scripted"):
        self.inner = make_teacher(teacher)
        self.rows = []

    def choose(self, state, monster, options, plans):
        chosen = self.inner.choose(state, monster, options, plans)
        self.rows.append(to_laya_row(state, monster, options, plans, chosen))
        return chosen


def _play(level, seed, style, teacher="scripted"):
    rec = _Rec(teacher)
    game = Game(level, seed, rec, hero_start_order=hero_start_order(seed))
    bot = make_bot(style, seed)
    loops = 0
    while not game.result:
        loops += 1
        if loops > MAX_LOOPS:
            raise RuntimeError(f"L{level} S{seed} {style}: game did not finish")
        bot.play(game.phase)
        if bot.errors:
            raise RuntimeError(f"L{level} S{seed} {style}: hero bot errors {bot.errors}")
        game.end_turn()
    return rec.rows


def make_rows(target, start_seed=TRAIN_SEED_START, min_options=1, teacher="scripted"):
    """Scripted-brain decisions as Laya rows, until at least `target` rows exist.
    Returns (rows, stats). Order: for each seed, levels 1-3, bots in sorted order."""
    if start_seed < TRAIN_SEED_START:
        raise ValueError(f"training seeds start at {TRAIN_SEED_START}, got {start_seed}")
    rows, games, by_level = [], 0, {1: 0, 2: 0, 3: 0}
    seed = start_seed
    while len(rows) < target:
        for level in (1, 2, 3):
            for style in sorted(BOTS):
                new = _play(level, seed, style, teacher)
                new = [r for r in new if len(r["questions"]["action"]["criteria"]) >= min_options]
                rows += new
                by_level[level] += len(new)
                games += 1
                if len(rows) >= target:
                    return rows, {"games": games, "last_seed": seed, "rows_by_level": by_level}
        seed += 1
    return rows, {"games": games, "last_seed": seed, "rows_by_level": by_level}


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "logs/laya_a_train.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    min_options = int(sys.argv[sys.argv.index("--min-options") + 1]) if "--min-options" in sys.argv else 1
    teacher = sys.argv[sys.argv.index("--teacher") + 1] if "--teacher" in sys.argv else "scripted"
    rows, stats = make_rows(target, min_options=min_options, teacher=teacher)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(len(rows), "rows ->", out)
    print(stats)