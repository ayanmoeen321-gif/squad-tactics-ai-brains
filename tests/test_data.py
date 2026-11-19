from engine.data import load_heroes, load_monsters

HERO_KEYS = {"name", "symbol", "hp", "move", "range", "damage", "los", "skill"}
MONSTER_KEYS = {"name", "symbol", "hp", "move", "range", "damage", "los", "heal"}


def test_heroes_match_spec():
    h = load_heroes()
    assert set(h) == {"tank", "archer", "healer"}
    assert (h["tank"]["hp"], h["tank"]["move"], h["tank"]["damage"]) == (20, 3, 4)
    assert (h["archer"]["hp"], h["archer"]["range"]) == (10, 4)
    assert (h["healer"]["hp"], h["healer"]["skill"]["amount"]) == (12, 5)


def test_monsters_match_spec():
    m = load_monsters()
    assert set(m) == {"goblin", "brute", "archer", "healer"}
    assert (m["goblin"]["hp"], m["goblin"]["move"]) == (4, 4)
    assert (m["brute"]["hp"], m["brute"]["damage"]) == (12, 3)
    assert m["healer"]["heal"] == {"amount": 3, "range": 3}


def test_all_entries_have_required_keys():
    for hero in load_heroes().values():
        assert set(hero) == HERO_KEYS
    for mon in load_monsters().values():
        assert set(mon) == MONSTER_KEYS