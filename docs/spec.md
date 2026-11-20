# Spec: Squad Tactics vs. a Team of Fast AI Brains

Status: **Approved (v2) + build decisions in section 17.** Date: 2026-11-18. Author: Ayan.
No code is written until this spec is approved.

---

## 1. Summary

A playable, turn-based 2D tactics game in the browser. The player controls a squad of 3 heroes. Up to 10 monsters fight back as a team. Monsters plan one by one, and each monster sees what the earlier monsters chose. The plans are shown as arrows before they happen, and the player can react before they play out.

Code does the thinking: distances, line of sight, legal actions, pathfinding, damage. A "System 1" decision model only picks one action from a short legal list. We compare six monster brains on win rate, teamwork, speed, compute time, and playtester ratings.

## 2. Goals and limits

**Goals**
- A game that works, is fun to play, and can be shared with a link.
- A fair comparison of monster brains, with real numbers and honest results.
- A project that is easy to explain on a CV.

**Limits**
- Cost target: $0. Every model is open and runs on your own computer or the university computers. Jev (hosted and paid) is cut.
- This is a first game project. Scope grows only after the core works.
- No deadline is set yet. The cut list (section 13) is how we react if one appears.
- No claims of "first ever". A negative result ("beats scripted at X, fails at Y") is a valid finding.

**Honest note on novelty.** Telegraphed enemy plans are not new (Into the Breach). Small-model game AI and System 1 benchmarks already exist (for example System1-Arena, which includes closed-loop environments). What may be less explored is a team of about 10 monsters planning together with System 1 models, compared fairly against scripted and random baselines, with real playtest data. Read the existing papers before making any novelty claim.

---

## 3. Heroes (the player side)

Three heroes, all controlled by the player. Stats live in `data/heroes.json`, not in code.

| Hero | HP | Move | Range | Damage | Skill | Cooldown |
|---|---|---|---|---|---|---|
| Tank | 20 | 3 | 1 (adjacent) | 4 | **Taunt** | 3 turns |
| Archer | 10 | 4 | 4 (needs line of sight) | 4 | **Piercing Shot**: hits every monster in a straight line, 4 damage each | 3 turns |
| Healer | 12 | 3 | 3 (needs line of sight) | 2 | **Heal**: restore 5 HP to one other hero within 3 tiles | 2 turns |

**Rules**
- Each hero gets **1 move + 1 action** per turn. The hero moves first (up to its Move), then does one action: attack, use the skill, or wait. A hero may skip the move.
- A hero's move can be **undone** until that hero attacks or uses a skill. Attacks and skills cannot be undone.
- Damage is **fixed**. There are no dice.
- The Healer cannot heal herself. Healing never goes above max HP.
- Heroes cannot walk onto a tile that a monster has reserved (section 6).
- **Taunt:** when used, every living monster within 3 tiles (walk distance) of the Tank that can reach the Tank this round attacks the Tank during this round's execution. It may walk to any free tile from which the Tank is in range, using the fewest steps. Its reserved tile is released. The preview arrows update at once.
- **Win:** all monsters are dead. **Lose:** all heroes are dead, or 30 rounds pass with monsters still alive (a timeout is a loss). The limit of 30 can be tuned.
- Later extension (not in this version): add a Mage and let the player pick 3 of 4 heroes. Because stats are data, this means adding one entry.

---

## 4. Monsters

Four types. Stats live in `data/monsters.json`.

| Monster | HP | Move | Range | Damage | Special |
|---|---|---|---|---|---|
| Goblin | 4 | 4 | 1 | 2 | Fast, weak melee |
| Brute | 12 | 2 | 1 | 3 | Tough blocker, melee |
| Archer | 5 | 3 | 4 (line of sight) | 3 | Ranged, fragile |
| Healer | 6 | 3 | 3 (line of sight) | 1 | **Heal**: restore 3 HP to one hurt ally within 3 tiles, no cooldown |

**Monsters per level** (stored in `data/levels/levelN.json`)

| Level | Total | Mix |
|---|---|---|
| 1 (easy) | 5 | 3 Goblins, 1 Brute, 1 Archer |
| 2 (medium) | 8 | 3 Goblins, 2 Brutes, 2 Archers, 1 Healer |
| 3 (hard) | 10 | 4 Goblins, 2 Brutes, 3 Archers, 1 Healer |

**Action list.** On its turn each monster picks exactly one action. The code builds the list, and it only shows actions that are legal and make sense right now.

| Action (option id) | What the code does | Shown only when |
|---|---|---|
| Attack a hero (`attack_<hero>`) | Move if needed to the best tile, then hit that hero | That hero can be attacked this turn (it is "in reach") and earlier plans do not already kill it |
| Advance (`advance`) | Walk toward the nearest hero | A path to a hero exists |
| Flank a hero (`flank_<hero>`) | Walk to a free tile next to that hero, on a side no ally occupies or plans to use | Melee monsters only. Such a tile exists and is reachable |
| Hold chokepoint (`hold_chokepoint`) | Move to or stay on a chokepoint tile | A chokepoint tile is reachable this turn |
| Protect ally (`protect_<ally>`) | Move between a weak ally and the nearest hero | A weak ally exists (see assumptions) |
| Retreat (`retreat`) | Walk away from the heroes | The monster's HP is below 50% |
| Heal an ally (`heal_<ally>`) | Move if needed, then heal that ally | Healer monster only. A hurt ally can be reached to be within range. At most 3 options (lowest HP first) |

- **Focus fire is not an action.** The attack option carries a tag such as "Goblin 1 also attacking". The code counts focus fire from the logs.
- **Overkill block:** the code adds up planned damage on each hero (including cover). When earlier plans already kill a hero, `attack_<hero>` is removed from later lists.
- If a monster's list is empty, it waits.
- **Tile choice is done by code**, never by the model. Tie-breaks, in order: fewest steps, cover tile, lowest row, lowest column. Monsters never choose a lava tile as a destination.
- **Option order is fixed:** attack options first, then advance, flank, hold chokepoint, protect, retreat, heal.

---

## 5. Map

- **Size:** 12 x 12 for all three levels. Coordinates are `(row, col)`, counted from 0 at the top left. The map edge blocks movement. There is no forced border wall.
- **Movement:** 4 directions (up, down, left, right). Units block movement, and there is one unit per tile.
- **Tiles**

| Symbol | Tile | Rule |
|---|---|---|
| `.` | Floor | Walkable |
| `#` | Wall | Blocks walking and line of sight |
| `C` | Cover | A unit standing on it takes 1 less damage from ranged attacks (minimum damage 1) |
| `L` | Lava | A unit that **ends its phase** on lava takes 3 damage. Passing through is free. Applies to both sides. |
| `1` `2` `3` | Hero starts | 1 = Tank, 2 = Archer, 3 = Healer |
| `g` `b` `a` `h` | Monster starts | Goblin, Brute, Archer, Healer |

- **Chokepoints** are not drawn. The code finds them: a floor tile with walls on two opposite sides, like a doorway.
- Maps are text files: `data/levels/level1.txt`, `level2.txt`, `level3.txt`. The game checks each map when it loads (right size, right unit counts, no unit on lava, every hero start can reach every monster start).
- Note: this spec uses `1 2 3` and `g b a h` instead of the interview symbols `H` and `M`, so nothing has to be guessed.
- Later extras: pit and collapsing floor. Tile types are data, so they can be added without rewriting the game.

**Level 1: open room.** No lava. Teaches the controls and basic fighting.
```
............
............
......#.....
......#..g..
.2...C..C...
...1.....gb.
.3.........a
.....C..C...
......#..g..
......#.....
............
............
```

**Level 2: split room.** One doorway (a chokepoint) at `(5,6)` and one small lava patch near the door on the monster side. Hold the doorway, or get flanked once they pass it.
```
......#.....
......#.....
......#.C...
......#..b..
..2.C.#.g.a.
....1...g..h
..3...#.g.a.
....C.#LLb..
......#L....
......#.C...
......#.....
......#.....
```

**Level 3: two doors.** Doorways at `(3,6)` and `(8,6)`, several cover tiles, lava near the middle, and monsters in two groups. Monsters can attack from two sides, so teamwork matters most.
```
......#.....
......#..C..
......#.g.a.
....C..b..h.
...C..#.gC..
.2...L#LL...
...1.L#LL...
.3.C..#.gC..
....C..b..a.
......#.g.a.
......#..C..
......#.....
```

---

## 6. Turn flow

One round has these steps, in this order. This is a **telegraph** design: monsters plan first, the player sees the plan, the player counters, then the plan plays out.

1. **Start of round.** Hero cooldowns go down by 1.
2. **Monster planning** (on the server).
   - Order: closest to the nearest hero first (walk distance). Ties go to the lower monster ID. The order is always the same, so any game can be replayed exactly.
   - Each monster gets its state text and question, and the model picks one option (section 7 and 8). The code then chooses the tile and **reserves** it. Later monsters cannot use reserved tiles.
   - A tile that an earlier monster plans to leave can be reserved by a later monster.
   - The overkill block applies (section 4).
3. **Preview.** The plans are drawn as arrows.
4. **Player phase.** Each hero moves, then acts. The player can undo moves (section 3). Heroes cannot enter reserved tiles. The player presses End Turn.
5. **End of player phase.** Lava damage to heroes on lava. Check win or lose.
6. **Monster execution**, in the same order as planning. Each plan is re-checked first.
   - **Plan still valid:** it plays out as planned.
   - **Plan broken** (for example the target moved away or died): the monster walks to its planned tile, then attacks the same target if still in range. If not, it attacks the nearest hero in range. If none, it does nothing more.
   - If the planned tile is occupied or the path is blocked, the monster stops on the nearest free tile along its path.
7. **End of monster phase.** Lava damage to monsters on lava. Check win or lose. If round 30 ends with monsters alive, the heroes lose.

Win and lose are also checked after every attack.

---

## 7. Game state to text

The hardest function in the project. It lives in `engine/` as `build_monster_view()`. Each monster gets **two parts**, the way System 1 models expect: a **state** and a **question**.

**State** (facts the code worked out):
- Round number out of the limit.
- The monster's own name, type and role, HP, and tile.
- For each hero: HP, `straight` distance, `walk` distance, in reach or not, on cover or not, skill ready or not.
- All **earlier plans** this round, one short line each, with that ally's HP. Allies that have not planned yet are not listed.

**Question**: "Which action should this monster take?" The legal options are the answers, each with a label and one short line of facts and tags. A short legend defines the two distances once:
- `straight` = tiles in a line, ignoring walls (Manhattan distance).
- `walk` = steps the monster would really take, going around walls.
- "In reach" uses `walk`.

**Example**
```
STATE
Round 7 of 30. You are Goblin 2: fast, weak melee. HP 4/4. Tile (5,7).
Heroes:
- Archer: HP 10/10, straight 3, walk 3, in reach, on cover, skill ready
- Tank: HP 20/20, straight 4, walk 4, in reach, no cover, skill ready
- Healer: HP 12/12, straight 6, walk 8, not in reach, no cover, skill ready
Earlier plans this round:
- Goblin 1 (HP 4/4): attack Archer
- Brute 1 (HP 12/12): hold chokepoint (6,5)

QUESTION
Which action should Goblin 2 take?
straight = tiles in a line, ignoring walls. walk = steps you would really walk, around walls. In reach uses walk.
Options:
attack_archer: hit the Archer (HP 10/10, on cover). Goblin 1 also attacking.
attack_tank: hit the Tank (HP 20/20).
advance: walk toward the nearest hero.
flank_archer: go to a free side of the Archer.
```
(`retreat` is not listed because the Goblin's HP is full.)

**Rules**
- **Token budget:** the whole text (state + question) stays **under about 400 tokens**, even for the last monster on Level 3. Laya's English model has a 512-token limit, and its options share a fixed token budget (192 tokens on English, 256 on the 1024-context checkpoints). With 9 options that is only about 19 to 26 tokens per option, so option lines stay short, or we start from a 1024-context Laya checkpoint. Kev's validated context is 8,192 tokens. A test checks the length on every level. If the text is too long, shorten the wording first. Do not silently drop plan lines.
- The first version has no ASCII map. Later extras: an ASCII map, a shuffled option order, and a label-only test.

---

## 8. AI layer

**Six brains** compared (random, scripted, and four System 1 setups):

| Brain | What it is | Runs where | Cost |
|---|---|---|---|
| Random | Picks a random legal option (seeded) | Anywhere | $0 |
| Scripted | Hand-coded rules (draft below) | Anywhere | $0 |
| Laya-A | Open System 1 model (Laya, Apache 2.0), fine-tuned on scripted-brain choices | CPU is enough to play (about 1 GB RAM). Fine-tuning on the university GPU | $0 |
| Laya-B | Same model, fine-tuned on a stronger code teacher | Same | $0 |
| Kev (zero-shot) | Open System 1 model (Kev-4B, Apache-2.0), released checkpoint, no training | University GPU only (CUDA, ROCm or Apple MLX; CPU serving is not documented) | $0 |
| Kev-A | Same model, fine-tuned on scripted-brain choices (LoRA adapter) | University GPU only | $0 |

Optional extras: Kev-B (Kev fine-tuned on the lookahead teacher), a large LLM as a reference, and Jev (hosted and paid, cut for now).

**Interface.** Every brain implements the same function: `choose(monster_view) -> option id + probabilities`. Random and scripted return no probabilities. Laya and Kev both serve the same `/v1/systemone` wire protocol, so one System 1 client class serves both. A brain is picked by base URL and model name.

**How a choice is made.** The brain takes the **top option every time**, so the same input gives the same action. Later extras: sampling with a seed for variety, and a fallback to scripted when confidence is low.

**Scripted brain (draft, finalized in build step 3).** Priority order: heal a hurt ally (Healer), retreat when HP is under 50% (ranged and Healer), attack the hero that earlier plans are already focusing and can still be killed, otherwise attack the lowest-HP hero in reach, flank (melee), hold a chokepoint (Brutes), advance. It reads earlier plans, so it also coordinates. It must be final before any Laya data is made.

**Laya training**
- Laya out of the box is close to random (0.362 zero-shot on its own benchmark). Fine-tuning is required. The vendor says it is "a fast base to specialise".
- **Laya-A:** the scripted brain plays many games on training seeds. We save (state, question, chosen option) and fine-tune Laya on it. Best case: it matches scripted.
- **Laya-B:** a **lookahead teacher** written in code. For each legal option it simulates the rest of the round and picks the best outcome. It is free, deterministic, and must beat scripted in dev tests, or Laya-B is not meaningful and we report that.
- Training seeds are separate from evaluation seeds.
- Dataset size is decided in build step 5 from the first results. My rough estimate is 20,000 to 30,000 decisions, which is about 150 to 300 scripted games. Kev's authors saw no clear gain from 400 records, and clear gains from about 1,000 to 5,000.
- Start from a 1024-context checkpoint (`laya-typed-decisions` or `laya-multilingual`) or the English `laya`. A quick test in step 4 picks one.
- Laya fine-tuning uses `laya.train.finetune` on a JSONL file. The first thing to test (build step 4): that it accepts our custom per-call options. Its exact data format is not verified.

**Kev**
- Kev-4B (Qwen3.5-4B base + a small LoRA adapter, Apache-2.0). Fallback: Kev-0.8B, which needs only a 4 GB GPU. Not verified: Kev-4B on a 24 GB card. Its README lists L40S and H100 GPUs for serving and an H100 for its example fine-tune.
- **Kev (zero-shot)** uses the released checkpoint with no training. Its README reports 0.817 accuracy on new sources, measured by the authors (Jev scored 0.857 on the same suite).
- **Kev-A:** fine-tune from the released checkpoint with `kev.train --init_from jaredpalmer/kev-4b`, using the same scripted-brain data as Laya-A, written as JSONL with a label for each question. Use a small learning rate (the README suggests 2e-5 as a start). Starting from the base model instead throws away what Kev already knows.
- Context is validated to 8,192 tokens, so our text fits easily. A choice question takes 1 to 255 options.
- Kev runs as its own server (`python -m kev.serve`, default port 8009) in its own environment (Python 3.12 or 3.13, uv). The backend calls it over HTTP. CPU serving is not documented, so Kev cannot play on your laptop. Playtests with Kev need a university GPU computer.

**Jev** (hosted, paid) is cut. It may come back as an extra. It uses the same interface, so adding it later means one more brain, a pinned model version, a private `.env` key, and a cache.

**When a model call fails:** timeout is **3 seconds** for every brain. Retry once, then use the scripted brain for that one decision. Every fallback is logged. A game with too many fallbacks (default more than 5% of decisions) is marked "not a fair test of that brain".

---

## 9. Backend

- **Python + FastAPI.** It holds the rules and runs all brains. It also serves the built web page, so there is one link and one program.
- **Rules live in Python only.** The browser (Phaser) draws the board and sends clicks. Test games use the same engine with no browser.
- **Proposed endpoints:** new game, get state, hero move, hero action, undo, end turn (returns a list of events for the browser to animate), submit rating. FastAPI also gives a free test page for trying the rules.
- **Secrets:** none needed now, because every model is open and runs locally. If Jev is added later, its key lives only in a private `.env` file on the backend, with `.env` in `.gitignore`, and is never sent to the browser.
- **Logging:** every model decision is one JSON line in `logs/`: game id, seed, level, brain, hero bot, round, monster id, state text, options, probabilities, chosen option, latency, tokens, retry, fallback and reason. Each game also gets a summary line (outcome, rounds, heroes alive, teamwork counts, compute time).
- **Cache:** none. All models are local and free. A cache is only needed if Jev is added.
- **Hosting:** your laptop with a free tunnel link for playtests. A free cloud host later, if its limits allow. The web folder stays separate, so a separate page host is possible later. Laya, scripted and random can run on your laptop. Kev needs a GPU, so games that use Kev run on a university GPU computer.
- A 10-monster plan needs about 10 calls one after another, because each monster sees the earlier plans. Laya on a laptop CPU may take several seconds for 10 calls (my untested guess). On a GPU it should be well under a second. The UI shows a "monsters are planning" animation.

---

## 10. Evaluation

**Setup.** 6 brains x 3 levels x 3 hero bots x 50 seeds = **2,700 games**. Development runs use 20 seeds (1,080 games) to check that everything works. Games run headless, with no browser. Training seeds are separate from evaluation seeds.

**Hero bots** (kept in `data/hero_bots.json`)
- **Aggressive:** rushes the nearest monster and uses skills when ready.
- **Defensive:** stays near cover and doorways, attacks only what comes into range, heals.
- **Focus-fire:** all heroes attack the weakest monster in reach.
- Each bot gets small seeded changes: which hero starts on which start tile, and tie-breaks.
- Honest limit: bots are not humans. The playtest covers that.

**Metrics**

| Metric | Definition |
|---|---|
| Win rate | Share of games where the heroes kill all monsters. A timeout is a loss. Shown with a 95% confidence interval. |
| Survival time | Rounds until the game ends, and heroes alive at the end |
| Decision speed | Average and worst time per decision |
| Compute time per game | Total model time per game. All models are free, so the hardware used is written next to every number. |
| Reliability | Fallback rate, and how often each option position (1st, 2nd, ...) is picked, to check for position bias |
| Focus fire rate | % of rounds where one hero is attacked by 2 or more monsters |
| Flanking rate | % of rounds where one hero is attacked by 2 or more melee monsters from different sides (overlaps with focus fire on purpose) |
| Protecting rate | % of rounds where at least one monster carries out "protect ally" |

After the first results: a **payoff check**. Do rounds with coordination kill more heroes or deal more damage than rounds without?

**Option-order check (small).** Position bias is a known problem: Laya's authors measured it, and an outside probe of Jev saw the same effect. Each System 1 brain also plays a small set of games with the option order reversed (suggested 10 seeds per combination). We compare win rate and how often the top option changes.

**Playtest (blind comparison)**
- 8 to 10 friends and classmates.
- Each plays the same level twice against two different brains, in random order, without being told which is which.
- After each game they rate **fun**, **difficulty**, and **"did the monsters feel like a team?"** from 1 to 5, in a form inside the game. Ratings are saved with the game log. No names are stored.
- The decision log hides probabilities and brain names in playtest mode.
- Which level and which two brains are chosen after the final results. Kev needs a GPU, so a playtest that includes Kev must run on a university GPU computer. Laya, scripted and random can run on your laptop.
- The report calls these results **indicative**, not conclusive.

**Outputs:** result tables, charts (pandas + matplotlib), the logs, a short report, and a demo video.

---

## 11. UI

**Six screens:** Title, Level select (level + difficulty), Game, Result (outcome, stats, rating form in playtest mode), Tutorial (short rules), Settings (animation speed and sound only).

**Difficulty.** The names are Easy, Medium, Hard. The brain behind each is set **after the evaluation**, ranked by hero win rate, in `data/difficulty.json`. In blind playtests the game chooses the brain.

**Controls (mouse or tap only).** Click a hero, and its reachable tiles light up. Click a tile to move. Click a target to attack, or press the skill button. Buttons: End Turn and Undo (moves only). Keyboard shortcuts are a later extra.

**Board**
- Flat top-down square grid. Plain colored squares first. Each unit is a square with a letter and a thin health bar inside its own tile.
- Hover or tap a unit to see an **info card** (HP, move, range, damage, cooldown) and its reach highlighted. The card appears in a side panel and never covers the unit.
- **No overlapping:** one unit per tile. Health bars stay inside their tile and are drawn above the unit. Units animate one at a time, in plan order. Dead units are removed at once. Damage numbers appear one after another.
- **Preview arrows** are drawn under the units, thin and semi-transparent, offset and colored per monster so crossing arrows can still be followed. Readability is tested early on Level 3.
- **Decision log** (side panel): one simple line per monster, such as `Goblin 2 -> Attack Archer`. A config flag turns on probabilities for demos and debugging. It is locked off in playtests.

---

## 12. Tech

**Folders (one repository)**
```
engine/    game rules (Python, no web code)
brains/    random, scripted, laya, kev, lookahead teacher
server/    FastAPI
web/       Phaser + Vite (browser part)
data/      heroes.json, monsters.json, levels/, hero_bots.json, difficulty.json, config.json
eval/      test runner and result analysis
logs/      decision logs and playtest ratings
tests/     pytest rule tests
```

**Libraries:** Python 3.10 or newer, FastAPI, pytest, laya (pip), Phaser, Vite, pandas, matplotlib. Kev is installed from its GitHub repo with uv and needs Python 3.12 or 3.13, so it gets its own environment and runs as a separate server. The backend calls Laya and Kev over the same `/v1/systemone` protocol.

**Run:** one script (for example `python run.py`) starts the server and the web page. The README also lists the two separate commands.

**Deploy:** your laptop with a free tunnel for now. A free cloud host later if limits allow. Docker is a later extra (check that the university computers allow it).

**University computers:** code goes there through GitHub (`git clone`), and results come back by push or copy. You confirmed the network will not block it. You need in-person access and permission for long jobs.

**Art:** plain colored squares. Free packs (Kenney.nl, itch.io, OpenGameArt) are an extra. Check licenses.

---

## 13. Scope, build order, cut list

**Core (never cut):** Python engine, 3 levels, 3 heroes, 4 monster types, turn flow with preview, random and scripted brains, hero bots, headless runner, logging, state-to-text, Laya-A, the evaluation (up to 2,700 games), report.

**Standard (planned):** browser game with plain squares, preview arrows, info cards, 6 screens, Laya-B, Kev zero-shot, Kev-A, blind playtest, demo video.

**Extras (only if time):** art, Mage and 3-of-4 hero choice, pit and collapsing floor, ASCII map in the text, shuffled option order, label-only test, sampling and low-confidence fallback, large LLM brain, Jev (hosted, paid), Kev-B, payoff check, keyboard shortcuts, Docker, cloud host with a separate page, bigger online playtest, co-op mode, leaderboard.

**Build order**
1. **Engine core.** Grid, units, tiles, legal moves, pathfinding, line of sight, damage, lava, win and lose. Stats and maps in data files. pytest rule tests. The engine can copy a state and replay from a seed.
2. **Turn flow.** Planning, tile reservation, overkill block, execution with the fallback rule. Random and scripted brains. FastAPI test page.
3. **Hero bots, headless runner, logging.** First baseline results. Balance tuning. Scripted brain finalized.
4. **State-to-text and question builder.** Token check (under 400). A tiny Laya fine-tune smoke test and a Kev zero-shot smoke test on the university GPU, to find lab, install and data-format problems early.
5. **Laya-A.** Generate data, fine-tune, plug in, dev evaluation (20 seeds).
6. **Kev.** Run Kev zero-shot first (free, no training), then fine-tune Kev-A on the same data as Laya-A, plug in, dev evaluation.
7. **Laya-B.** Lookahead teacher, new data, fine-tune, plug in.
8. **Browser game.** Title, Level select, Game, Result. Board, controls, arrows, info cards, decision log, rating form. Arrow readability check on Level 3.
9. **Final evaluation.** 50 seeds for random, scripted, Kev zero-shot, Laya-A, Kev-A, Laya-B. Option-order check. Charts.
10. **Difficulty mapping and blind playtest.**
11. **Tutorial and Settings screens, report, demo video.**
12. **Extras**, including art if time allows. If art is promoted to Standard, it goes after step 10 so every tester sees the same version.

**Cut list** (drop in this order if time runs short)
1. Tutorial and Settings screens
2. Cloud hosting and the public link
3. Playtest size
4. Art (only if promoted to Standard)
5. Kev-A (Kev zero-shot stays as a baseline)
6. Laya-B

---

## 14. Risks and honest notes

1. **Laya may not learn well.** It is near random without fine-tuning, and calibration is poor. We do not yet know if `laya.train.finetune` accepts our custom options. Test in step 4.
2. **Imitation ceiling.** Laya-A can at best match scripted. Laya-B depends on the teacher being stronger. If it is not, say so.
3. **Training and test overlap.** The teacher and the test games use the same hero bot styles. Training seeds are separate, but the report must state this. Human playtests are the check.
4. **Kev needs a GPU and its fit is unconfirmed.** Kev-4B on a 24 GB card is not verified (fallback: Kev-0.8B). CPU serving is not documented, so playtests with Kev need a university GPU computer. Kev's numbers are author-reported.
5. **Novelty.** Related System 1 benchmarks exist. Do not claim "first".
6. **Scope.** Big for a first game, and no deadline means scope can grow. Use the cut list.
7. **University GPU.** All fine-tuning and large runs depend on it.
8. **Hero bots are not humans.**
9. **Arrow clutter** with 10 monsters on Level 3.
10. **Text length.** The 400-token cap is tight for the last monster on Level 3.
11. **Teacher approval.** The proposal is not confirmed yet. The engine, state-to-text, and model-comparison setup carry over to the racing benchmark if it is rejected. The security project stays as the fallback.
12. **Option order changes answers.** Laya's authors measured a position bias, and an outside probe saw the same effect in Jev. We log which option position is picked and run a small reversed-order check.

---

## 15. Assumptions I filled in (please check)

These were not decided in the interview.
1. Movement is 4-directional. Straight distance is Manhattan. Units block movement and line of sight ignores units.
2. Heroes move first, then act. Cooldowns tick down at the start of each round.
3. **Taunt** works as described in section 3 (it overrides the plans of nearby monsters for this round). The interview only said "monsters prefer the Tank for 1 turn".
4. Cover reduces all ranged damage by 1, with a minimum damage of 1. Piercing Shot goes in one of 4 directions, up to range 4, stopped by walls.
5. "Weak ally" for Protect means HP under 50%, or an Archer or Healer type. Flank is for melee monsters only.
6. Heal options are capped at 3. Healer monsters heal allies, not themselves.
7. Map symbols changed to `1 2 3` and `g b a h`. Levels 2 and 3 map designs are mine.
8. Flank rate overlaps with focus fire rate on purpose.
9. Fallback threshold is 5%. Seeds: training seeds are separate from evaluation seeds.
10. Plan lines in the state text only list allies that have already planned.
11. Kev-4B is the Kev size (fallback Kev-0.8B). Kev zero-shot counts as a brain, and Kev-A copies Laya-A's training data.
12. Laya starts from a 1024-context checkpoint or the English `laya`, picked by a quick test.
13. The small reversed-option-order check is in Standard (10 seeds per combination).
14. The training set is about 20,000 to 30,000 decisions (rough guess).
15. Jev is cut. The paid-model parts of the plan (key, cache, cost per game) were removed.

## 16. To-do for Ayan

- Talk to your teacher: proposal approval.
- Ask the lab admin: GPU account and permission for long jobs.
- Ask the lab admin: can the GPU computers run Kev (Python 3.12 or 3.13, uv), and is there a GPU with 24 GB or more?
- Tell your teacher that Jev is cut (cost) and that open System 1 models (Laya and Kev) are the plan. Your emailed proposal names Jev.
- Read System1-Arena and the related System 1 papers before claiming novelty.

---

**Approval:** reply "approved", or tell me what to change. After approval I make the build plan and start coding at build step 1.


---

## 17. Build decisions (made while coding; the code follows these)

**Monster options (`engine/options.py`)**
- Option order is fixed: attack, advance, flank, hold chokepoint, protect, retreat, heal. Hero targets are always listed Tank, Archer, Healer.
- Advance is shown only if the walk distance to the nearest hero gets smaller.
- Retreat is shown only if HP is below 50% AND the walk distance to the nearest hero gets bigger.
- Flank: melee monsters only. It never uses the tile the monster already stands on. A monster already next to a hero still has the Attack option.
- Protect: at most 2 options, ranked by lowest HP, then lower monster number. (The spec set no cap before.)
- Heal: at most 3 options, same ranking.
- Attack range uses straight distance plus line of sight (ranged monsters only), checked from the destination tile. Walk distance is used for movement only.
- Tiles reserved by earlier plans are blocked for later monsters, as a destination and as a path. A tile an earlier monster plans to leave is free, unless another plan reserves it.
- Distance-to-hero maps use walls only.

**Outcome**
- If all heroes and all monsters die at the same time, it counts as a loss.
- The timeout (round 30) is checked only at the end of a round.

**Execution (`engine/execution.py`)**
- Only attack and heal plans act after moving. Advance, flank, hold, protect and retreat only move.
- A broken attack or heal (target dead, out of range, or ally already at full HP) falls back to the nearest hero in range, else nothing. The fallback never hits an ally.
- If the path is blocked, the monster walks along its path and stops before the blocker, then uses the same fallback. Usual blockers: a hero standing on the path, or an earlier monster that was itself stopped short.
- Execution stops at once when all heroes are dead. Monster lava damage is applied only at the very end, so it is skipped after an early loss.
- Monsters can only die from lava, at the end of the phase. If lava kills the last monster, the result is a win.

**Player phase (`engine/player.py`)**
- A hero moves at most once, and only before it acts. After any action (including wait) it cannot move.
- Heroes cannot enter a tile a monster stands on, or a tile reserved by a living monster's plan (as a destination or as a path). A reserved tile is free again if that monster dies.
- Moving to the tile the hero already stands on is not a move; the player just skips the move.
- Undo puts the hero back on its start tile and allows a new move. It is not possible after any action.
- End of the player phase: lava damage to heroes, then the win/lose check.

**Taunt details**
- Tie-break for the Taunt tile: fewest steps, then a cover tile wins, then lowest row, then lowest column.
- Re-planning is one monster at a time, in plan order. A monster not yet re-planned keeps its old tile reserved, so there are never two monsters on one tile. Cost: an earlier monster cannot take the old tile of a later taunted monster.
- A monster that cannot reach a hitting tile keeps its old plan and its old reservation.
- Taunt ignores the overkill block on purpose: the forced attack is the point of the skill. The preview can therefore show more damage on the Tank than its HP.
- The `taunted` flag is on the plan and on every event of that monster's turn (move, attack, fallback attack). The logger must record it, so the evaluation can count Taunt effects.
- Extras list: the UI shows "affects N monsters" before the Taunt click, because skills cannot be undone.

**Round loop (`engine/game.py`)**
- Plans for a round are made as soon as the round starts, so the preview is ready at once.
- Hero cooldowns tick down by 1 at the start of each round. A skill used in round 1 with cooldown 3 is ready again in round 4 (Healer, cooldown 2: round 3).
- `end_turn` runs: player-phase end (lava on heroes), monster execution, then the next round. Calling it after the game is over is an error.

**Scripted brain, version 1 (`brains/scripted_brain.py`)**
- Priority: heal > retreat (Archers and Healers only) > attack > flank > hold chokepoint (Brutes only) > advance > first option.
- Heal: lowest absolute HP first (not percent). Ties go to the monster that comes first in the map's reading order.
- Attack choice, in order: a hero that earlier plans' damage plus this monster's damage would kill; then a hero earlier plans already attack; then lowest HP; then Tank, Archer, Healer order.
- Flank is reached mostly when Attack is blocked by the overkill block (a monster that can reach a flank tile normally also has an Attack option). Choice: the hero with the fewest earlier attack or flank plans, then hero order.
- Deterministic. It is the teacher for Laya-A and Kev-A, so it is frozen before any training data is made. Any rule change after that needs a new `version` and new data.
- Retreat stays in the option list for every monster, so the models may pick it; only the scripted brain ignores it for Goblins and Brutes.

**Hero bots (`brains/hero_bots.py`)**
- A bot plays all living heroes for one player phase through the public `PlayerPhase` methods, in the order Tank, Archer, Healer.
- Errors are loud: if an action raises `ActionError`, the bot records it in `bot.errors` and the hero waits so the game can continue. Tests fail if any error is recorded. The evaluation runner must abort a run if `bot.errors` is not empty.
- Each bot has its own RNG, seeded from "style:game seed". It is separate from the engine RNG and is used only to break ties between equal choices. Swapping which hero starts on which start tile is done by the runner, not by the bot.
- Tank uses Taunt when the real Taunt rule, tried on a copy of the plans, would affect 2 or more monsters. Archer uses Piercing Shot when it hits 2 or more monsters. Healer heals the lowest-HP other hero below 60% HP within range, never herself.
- Aggressive: moves to a tile from which it can hit the nearest monster, otherwise walks toward it.
- Defensive: prefers a tile from which it can hit, then cover or a chokepoint, with the smallest move.
- Focus-fire: one shared target per turn, the lowest-HP monster that at least one hero that has not acted can hit this turn (moving included). If none can be hit, the monster closest to the heroes. Heroes that cannot hit it move toward it. If the target dies mid-turn, a new one is picked by the same rule.
- All bots avoid ending on lava when a safe tile exists.
- Balance check: each bot's win rate against the scripted brain is checked in the build step 3 baseline runs and adjusted then if far off.

**Headless runner and logging (`eval/runner.py`)**
- `run_game(level, seed, brain, hero_bot, log_dir, swap_starts)` plays one full game and returns a summary. With `log_dir` it appends one JSON line per monster decision to `decisions.jsonl` and one summary line per game to `games.jsonl`.
- Every line carries `schema_version` (1), `game_id`, `seed`, `level`, `brain`, `bot`, and `swap_order`; decision lines also carry `round`, `monster`, the option ids in the order they were presented, the chosen option, its position and the latency. The summary has `rounds` instead of `round`. State text, probabilities, tokens, retry and fallback fields are added in build step 4 as optional fields, so older logs stay valid.
- The runner aborts (RunnerError) if a hero bot records an error, so a broken rule never turns into quiet "wait" moves in the results.
- Hero start tiles are shuffled only by the runner (`Game(..., hero_start_order=...)`), using its own RNG stream seeded from "start:" plus the game seed. The browser game never shuffles: the player always gets the map as designed. All evaluation results are therefore for shuffled starts. The baseline runs check win rates per start order, to catch a level that becomes unwinnable.
- Teamwork rates count monster phases after execution: focus fire = one hero attacked by 2+ monsters; flanking = one hero attacked by melee monsters from 2+ sides; protecting = a protect plan whose monster ended on its planned tile. Normal, fallback and taunted attacks all count. Heroes' own attacks are not counted.
- The summary also records taunt count, heroes alive, hero HP left, decision count, option position counts, model time and worst decision time.

**Scripted brain experiment (Nov 2026, not adopted)**
- Tested version 2: a Brute holds a chokepoint only if a hero is within walk distance 6, otherwise it advances. Result over 300 games per level: Level 2 stayed at 80.0% hero wins, Level 3 fell from 26.7% to 10.3%. Version 2 was dropped and version 1 stays the frozen teacher.
- Conclusion: the doorway jam seen in one Level 3 game was not the main cause of Level 3's difficulty. The real cause is not found yet. Do not retry this fix.
- Level difficulty is tuned through level data (monster counts, HP, damage), not by changing the teacher. A level where hero win rates sit well away from 0% and 100% separates brains best.

**Defensive bot stall rule (Nov 2026)**
- Found with `eval.diagnose` and `eval.watch`: on Level 3 all 23 timeouts (scripted brain v1, 150 games) were the defensive bot. The last hero sat on a cover tile while the monsters held their doorway, so nobody moved until round 30.
- Fix: `DefensiveBot` counts player phases in which no hero can hit any monster (`idle`). After `STALL_ROUNDS` (5, tunable) such phases in a row it walks toward the nearest monster like the aggressive bot. The counter resets as soon as a hit is possible.
- Result (50 seeds x 3 bots per level): timeouts 23 -> 0. Level 3 hero wins stayed 37 of 150, so the stalled games now end as hero deaths. Levels 1 and 2 are unchanged.
- Conclusion: Level 3 is hard because of attrition, not because of a stuck bot. The earlier baseline numbers for the defensive bot are out of date and must be re-run (`python -m eval.baseline 100`) before level tuning.

**Scripted brain v1 frozen (Nov 2026)**
- Scripted brain version 1 is frozen as the teacher for Laya-A and Kev-A. Any rule change needs a new version number and new data.
- Fresh baseline after the defensive bot fix (100 seeds x 3 bots = 300 games per level, shuffled starts): hero wins vs scripted L1 100%, L2 80.0%, L3 26.7%. Random: L1 100%, L2 99.3%, L3 94.7%. By hero bot vs scripted: aggressive 57.0%, defensive 74.3%, focus 75.3%.
- Level 3 by start order (scripted): the designed order (Tank, Archer, Healer) gives only 10.0% hero wins (n=60). Other orders give 14% to 56%. The browser always uses the designed order, so a human sees the hardest version.
- Decision: do not tune Level 3 now. Evaluation balance (shuffled starts, bots) and human difficulty are related but not the same. Build the game first.
- **Condition for build step 10 (playtest):** test Level 3 with the real browser start order before the blind playtest. If it is frustrating or unfair, adjust the level data then (monster counts, HP, damage), and re-run the evaluation numbers that depend on it.

**State-to-text builder (build step 4, part 1)**
- `engine/view.py`: `build_monster_view(state, monster, options, plans)` returns `state`, `question`, `options` (id and text, same order as the legal options) and `text` (STATE + QUESTION). `rough_tokens(text)` = characters / 3, a rough proxy only.
- Plan lines list only allies that already planned. Option lines are short; attack lines carry "X also attacking" tags.
- Token check (scripted brain, 45 whole games, 3 levels x 3 bots x 5 seeds): longest view L1 322, L2 305, L3 372 rough tokens, under the 400 cap. The margin is thin and the proxy is not Laya's tokenizer. Re-check with the real tokenizer in the Laya smoke test. If over, shorten wording first (for example plan-line HP), never drop plan lines.