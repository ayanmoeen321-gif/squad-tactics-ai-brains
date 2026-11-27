import argparse
import json
import os
import time

from brains.hero_bots import BOTS, make_bot
from brains.lookahead2_brain import Lookahead2Brain
from engine.game import Game
from eval.laya_export import to_laya_row
from eval.make_laya_data import MAX_LOOPS
from eval.runner import hero_start_order

# above every earlier training seed (1000 to 1064); evaluation seeds are 0 to 49, dev seeds 100 to 389
DAGGER_SEED_START = 2000


class _DaggerRec:
    """The student plays and the game follows the student. Every decision with 2 or more options is also
    labelled by the teacher on the same state, and that label is what the row teaches."""

    def __init__(self, student, teacher):
        self.student = student
        self.teacher = teacher
        self.rows = []
        self.fallbacks = 0
        self.agree = 0

    def choose(self, state, monster, options, plans):
        chosen = self.student.choose(state, monster, options, plans)
        if len(options) >= 2:
            if (getattr(self.student, "last_info", None) or {}).get("fallback"):
                self.fallbacks += 1
            label = self.teacher.choose(state, monster, options, plans)
            self.agree += label == chosen
            self.rows.append(to_laya_row(state, monster, options, plans, label))
        return chosen


def play_dagger(level, seed, style, student, teacher):
    rec = _DaggerRec(student, teacher)
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
    return rec


def games_in_order(start_seed):
    seed = start_seed
    while True:
        for level in (1, 2, 3):
            for style in sorted(BOTS):
                yield level, seed, style
        seed += 1


def _read_games(path):
    done = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                g = json.loads(line)
                done[(g["level"], g["seed"], g["style"])] = g
    return done


def summarize(games):
    s = {"games": len(games), "rows": sum(g["rows"] for g in games),
         "fallbacks": sum(g["fallbacks"] for g in games), "agree": sum(g["agree"] for g in games),
         "rows_by_level": {1: 0, 2: 0, 3: 0}}
    for g in games:
        s["rows_by_level"][g["level"]] += g["rows"]
    return s


def generate(student, teacher, out_path, target, start_seed=DAGGER_SEED_START, log=print):
    """Appends rows to out_path until at least `target` rows exist (whole games). Resumes from out_path.games."""
    if start_seed < DAGGER_SEED_START:
        raise ValueError(f"DAgger seeds start at {DAGGER_SEED_START}, got {start_seed}")
    games_path = out_path + ".games"
    done = _read_games(games_path)
    have = sum(1 for _ in open(out_path, encoding="utf-8")) if os.path.exists(out_path) else 0
    if have != sum(g["rows"] for g in done.values()):
        raise RuntimeError(f"{out_path} and {games_path} do not match: delete both and run again")
    used, total, new, started = [], 0, 0, time.time()
    for level, seed, style in games_in_order(start_seed):
        if total >= target:
            break
        key = (level, seed, style)
        if key not in done:
            rec = play_dagger(level, seed, style, student, teacher)
            with open(out_path, "a", encoding="utf-8", newline="\n") as f:
                for r in rec.rows:
                    f.write(json.dumps(r) + "\n")
            done[key] = {"level": level, "seed": seed, "style": style, "rows": len(rec.rows),
                         "fallbacks": rec.fallbacks, "agree": int(rec.agree)}
            with open(games_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(done[key]) + "\n")
            new += 1
            if new % 10 == 0:
                log(f"{new} new games, {total + done[key]['rows']} rows, {time.time() - started:.0f} s")
        used.append(done[key])
        total += done[key]["rows"]
    return summarize(used)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", help="Laya checkpoint folder (the student)")
    ap.add_argument("out")
    ap.add_argument("--target", type=int, default=8502)
    ap.add_argument("--start-seed", type=int, default=DAGGER_SEED_START)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    import laya
    from brains.laya_brain import LayaBrain
    agent = laya.load(a.checkpoint, device=a.device)
    student = LayaBrain(agent, name="laya_d", version="run_d")
    s = generate(student, Lookahead2Brain(), a.out, a.target, a.start_seed)
    print(json.dumps(s))
    print(f"student agrees with the teacher on {100 * s['agree'] / max(s['rows'], 1):.1f}% of {s['rows']} rows; "
          f"fallbacks {s['fallbacks']}")


if __name__ == "__main__":
    main()