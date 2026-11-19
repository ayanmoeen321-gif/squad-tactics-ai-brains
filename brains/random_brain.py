import random


class RandomBrain:
    """Picks a random legal option. Seeded, so the same seed gives the same choices."""

    name = "random"

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def choose(self, state, monster, options, plans):
        return self.rng.choice(options)["id"]