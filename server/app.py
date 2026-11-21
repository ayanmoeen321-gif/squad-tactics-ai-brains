from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from brains.random_brain import RandomBrain
from brains.scripted_brain import ScriptedBrain
from engine.combat import ActionError, in_attack_range, skill_ready
from engine.game import Game

app = FastAPI(title="Squad Tactics")
G = {"game": None}


class NewGame(BaseModel):
    level: int = 1
    seed: int = 0
    brain: str = "scripted"


class Move(BaseModel):
    hero: str
    to: list[int]


class Hero(BaseModel):
    hero: str


class Shot(BaseModel):
    hero: str
    direction: str


class Target(BaseModel):
    hero: str
    target: str


def _game():
    if G["game"] is None:
        raise HTTPException(400, "no game, call /new first")
    return G["game"]


def _unit(u):
    return {"id": u.id, "label": u.label, "side": u.side, "kind": u.kind,
            "hp": u.hp, "max_hp": u.max_hp, "pos": list(u.pos), "move": u.move,
            "range": u.range, "damage": u.damage, "cooldown": u.cooldown,
            "alive": u.alive, "skill": u.skill["name"] if u.skill else None}


def _view(game):
    s = game.state
    phase = game.phase
    heroes = {}
    if phase is not None:
        for h in s.heroes():
            can_attack = [m.id for m in s.monsters() if m.alive and in_attack_range(s, h, m)]
            can_heal = [o.id for o in s.heroes() if h.skill and h.skill["name"] == "heal" and skill_ready(h) and o.id != h.id and o.alive and o.hp < o.max_hp and abs(o.pos[0] - h.pos[0]) + abs(o.pos[1] - h.pos[1]) <= h.range]
            heroes[h.id] = {"can_attack": can_attack, "can_heal": can_heal, "skill_ready": skill_ready(h), "reachable": sorted([list(t) for t in phase.reachable(h.id)]),
                            "moved": phase.status[h.id]["moved"],
                            "acted": phase.status[h.id]["acted"]}
    return {"round": s.round, "result": game.result,
            "grid": ["".join(row) for row in s.grid.tiles],
            "units": [_unit(u) for u in s.units.values()],
            "plans": [{"monster": p["monster"], "kind": p["kind"],
                       "target": p["target"], "dest": list(p["dest"])} for p in game.plans],
            "heroes": heroes}


def _do(fn, *args):
    game = _game()
    if game.result:
        raise HTTPException(400, "the game is over")
    try:
        events = fn(*args)
    except ActionError as e:
        raise HTTPException(400, str(e))
    return {"events": events, "state": _view(game)}


@app.post("/new")
def new(body: NewGame):
    if body.brain == "scripted":
        brain = ScriptedBrain()
    elif body.brain == "random":
        brain = RandomBrain(body.seed)
    else:
        raise HTTPException(400, f"unknown brain {body.brain!r}")
    G["game"] = Game(body.level, body.seed, brain)
    return _view(G["game"])


@app.get("/state")
def state():
    return _view(_game())


@app.post("/move")
def move(b: Move):
    return _do(lambda: _game().phase.move(b.hero, tuple(b.to)))


@app.post("/undo")
def undo(b: Hero):
    return _do(lambda: _game().phase.undo(b.hero))


@app.post("/attack")
def attack(b: Target):
    return _do(lambda: _game().phase.attack(b.hero, b.target))


@app.post("/heal")
def heal(b: Target):
    return _do(lambda: _game().phase.heal(b.hero, b.target))


@app.post("/piercing_shot")
def piercing_shot(b: Shot):
    return _do(lambda: _game().phase.piercing_shot(b.hero, b.direction))


@app.post("/wait")
def wait(b: Hero):
    return _do(lambda: _game().phase.wait(b.hero))


@app.post("/taunt")
def taunt(b: Hero):
    return _do(lambda: _game().phase.taunt(b.hero))


@app.post("/end_turn")
def end_turn():
    return _do(lambda: _game().end_turn())