# ⚔️ Squad Tactics

**Three heroes. A whole team of monsters that plan together. You get to see their plans, and then you get one turn to ruin them.**

A turn-based tactics game that runs in your browser. The monsters don't just run at you one by one: each monster looks at what the monsters before it decided, and picks a move that fits the team. Before you act, you can see every plan as an arrow on the board.

<!-- Add screenshots later: docs/images/menu.png and docs/images/game.png -->

## 🎮 How a round works

1. **The monsters plan.** Arrows show where each monster will walk and who it will hit.
2. **You move.** Each hero gets one move and one action. You can undo a move until the hero acts.
3. **You press End turn.** The monsters' plans play out, and a new round starts.

**You win** by killing every monster. **You lose** if all your heroes die, or if 30 rounds pass.

## 🛡️ Your squad

| Hero | HP | Move | Range | Special skill |
|---|---|---|---|---|
| Tank | 20 | 3 | adjacent | **Taunt**: nearby monsters must attack the Tank this round |
| Archer | 10 | 4 | 4 tiles | **Piercing Shot**: hits every monster in a straight line |
| Healer | 12 | 3 | 3 tiles | **Heal**: restore 5 HP to another hero |

Watch the ground: **lava** (orange) burns anyone who ends their turn on it, **cover** (green) reduces ranged damage by 1, and **walls** (grey) block movement and line of sight.

## 👹 The monsters

Goblins (fast, weak), Brutes (tough blockers), Archers (fragile, ranged), and Healers (they patch up their friends). There are four levels to play:

| Level | Monsters | Feel |
|---|---|---|
| Tutorial | 6 goblins | The game holds your hand. Skippable, and it teaches every skill. |
| 1 | 5 | Open room. Learn the basics. |
| 2 | 8 | A split room with one doorway. Hold it, or get flanked. |
| 3 | 10 | Two doors, lava, two groups. Teamwork matters most. |

## 🚀 Play it

**You need:** Python (tested on 3.14, on Windows). That's it, if the `web/dist` folder is in the repo.

~~~powershell
git clone https://github.com/ayanmoeen321-gif/squad-tactics-ai-brains.git
cd squad-tactics-ai-brains
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
~~~

Then open **http://127.0.0.1:8000** in your browser and pick the Tutorial.

**No `web/dist` folder?** Then build the web page once. This needs [Node.js](https://nodejs.org) (tested with v26):

~~~powershell
cd web
npm install
npm run build
cd ..
~~~

Then run `python run.py` again.

Mac and Linux are untested. The same steps should work, with `source .venv/bin/activate` instead of the activation line.

## 🧠 The monster brains

The game has swappable monster "brains". The menu lets you pick **Scripted** (hand-made rules, the default) or **Random** (easy mode).

The research side of the project trains small open "System 1" models ([Laya](https://github.com/convaiinnovations/laya)) to play the monsters. They don't write text: for each monster they pick one action from a short list of legal moves. Code does all the thinking about distances and line of sight; the model only chooses.

Results so far, on held-out test games against scripted hero bots (hero win rate, lower means stronger monsters):

| Level | Scripted brain | Trained Laya model | Lookahead teacher |
|---|---|---|---|
| 2 | 80.7% | 59.3% | 57.3% |
| 3 | 24.7% | 13.3% | 3.3% |

These are test games with bots, not human players, and one training run each. The trained model is **not plugged into the live game yet**: on a laptop CPU it takes about 4 to 5 seconds per decision, which is too slow. On a GPU it takes about 30 ms. The Kev model comparison and a blind human playtest are still to do.

## 🧪 Run the tests

~~~powershell
pytest -q
~~~

## 🗂️ What's inside

~~~
engine/   game rules (Python, no web code)
brains/   random, scripted, lookahead teachers, Laya
server/   FastAPI backend
web/      Phaser + Vite browser game
data/     heroes, monsters, level maps
eval/     headless test runner and training data tools
tests/    pytest tests
docs/     the full design spec
~~~

All the rules live in Python. The browser only draws the board and sends your clicks.

## 📜 Status

Work in progress. The full plan, decisions and results are in [docs/spec.md](docs/spec.md).