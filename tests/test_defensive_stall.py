from brains.hero_bots import DefensiveBot
from brains.random_brain import RandomBrain
from engine.game import Game
from engine.movement import walk_distances


def test_idle_stays_zero_when_a_monster_can_be_hit():
    game = Game(3, 0, RandomBrain(0))
    bot = DefensiveBot(0)
    bot.play(game.phase)
    assert bot.idle == 0
    assert bot.errors == []


def test_idle_counts_up_when_nothing_can_be_hit():
    game = Game(3, 0, RandomBrain(0))
    bot = DefensiveBot(0)
    bot._targets_from = lambda phase, hero, tile: []
    bot.play(game.phase)
    assert bot.idle == 1
    assert bot.errors == []


def test_stalled_defensive_bot_walks_toward_nearest_monster():
    game = Game(3, 0, RandomBrain(0))
    tank = game.state.units["tank"]
    before = min(walk_distances(game.state.grid, tank.pos)[m.pos]
                 for m in game.state.monsters())
    bot = DefensiveBot(0)
    bot.idle = DefensiveBot.STALL_ROUNDS
    bot.play(game.phase)
    after = min(walk_distances(game.state.grid, tank.pos)[m.pos]
                for m in game.state.monsters())
    assert after < before
    assert bot.errors == []