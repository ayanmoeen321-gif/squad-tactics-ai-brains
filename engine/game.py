from engine.combat import ActionError
from engine.execution import execute_round
from engine.planning import plan_round
from engine.player import PlayerPhase
from engine.state import new_game

HERO_IDS = ("tank", "archer", "healer")


class Game:
    """One full game: rounds of plan, player phase, execution."""

    def __init__(self, level, seed, brain, hero_start_order=None):
        self.state = new_game(level, seed)
        self.brain = brain
        self.result = None
        self.plans = []
        self.phase = None
        if hero_start_order is not None:
            self._swap_starts(hero_start_order)
        self._start_round()

    def _swap_starts(self, order):
        """order[i] = the hero whose start tile the i-th hero (tank, archer, healer) takes."""
        if sorted(order) != sorted(HERO_IDS):
            raise ValueError(f"bad hero start order: {order!r}")
        original = {h: self.state.units[h].pos for h in HERO_IDS}
        for hero_id, source in zip(HERO_IDS, order):
            self.state.units[hero_id].pos = original[source]

    def _start_round(self):
        for hero in self.state.heroes():
            if hero.cooldown > 0:
                hero.cooldown -= 1
        self.plans = plan_round(self.state, self.brain)
        self.phase = PlayerPhase(self.state, self.plans)

    def end_turn(self):
        """Ends the player phase, plays out the monsters, starts the next round.
        Returns the events. Sets self.result to 'win' or 'lose' when the game ends."""
        if self.result:
            raise ActionError("the game is over")
        events, result = self.phase.end()
        if not result:
            more, result = execute_round(self.state, self.plans)
            events += more
        if result:
            self.result = result
            self.phase = None
            return events
        self.state.round += 1
        self._start_round()
        return events