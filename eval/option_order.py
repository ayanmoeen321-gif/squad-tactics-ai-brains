import argparse


class ReversedBrain:
    """Plays like the inner brain, but the inner brain sees the options in reverse order. The game still gets an option id."""

    def __init__(self, inner):
        self.inner = inner
        self.name = getattr(inner, "name", "reversed")
        self.version = getattr(inner, "version", "1")
        self.last_info = None

    def choose(self, state, monster, options, plans):
        self.inner.last_info = None
        chosen = self.inner.choose(state, monster, list(reversed(options)), plans)
        self.last_info = getattr(self.inner, "last_info", None)
        return chosen


class OrderProbe:
    """The game follows the normal order. At every decision with 2 or more options the inner brain is asked again
    with the options reversed; counts how often it picks the same option id both times."""
    name = "order_probe"
    version = "1"

    def __init__(self, inner):
        self.inner = inner
        self.n = 0
        self.same = 0
        self.last_info = None

    def choose(self, state, monster, options, plans):
        self.inner.last_info = None
        first = self.inner.choose(state, monster, options, plans)
        self.last_info = getattr(self.inner, "last_info", None)
        if len(options) >= 2:
            second = self.inner.choose(state, monster, list(reversed(options)), plans)
            self.n += 1
            self.same += first == second
        return first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", help="Laya checkpoint folder")
    ap.add_argument("--levels", default="2,3")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    import laya
    from brains.hero_bots import BOTS
    from brains.laya_brain import LayaBrain
    from eval.runner import run_game
    agent = laya.load(a.checkpoint, device=a.device)
    total_n = total_same = 0
    for level in (int(x) for x in a.levels.split(",")):
        n = same = 0
        for bot in sorted(BOTS):
            for seed in range(a.seeds):
                probe = OrderProbe(LayaBrain(agent, name="laya_probe", version="probe"))
                run_game(level, seed, probe, bot)
                n += probe.n
                same += probe.same
        total_n += n
        total_same += same
        print(f"level {level}: {n} decisions with 2+ options, same choice in both orders: {100 * same / n:.1f}%")
    print(f"all levels: {total_n} decisions, same choice in both orders: {100 * total_same / total_n:.1f}%")


if __name__ == "__main__":
    main()