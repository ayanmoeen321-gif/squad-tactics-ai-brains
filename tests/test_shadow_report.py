from eval.shadow_report import summarize

ROWS = [
    {"level": 3, "round": 1, "kind": "goblin", "student": "advance", "teacher": "attack_tank", "regret": 10.0},
    {"level": 3, "round": 2, "kind": "brute", "student": "attack_tank", "teacher": "attack_tank", "regret": 0.0},
    {"level": 4, "round": 7, "kind": "archer", "student": "retreat", "teacher": "attack_archer", "regret": 500.0},
    {"level": 3, "game": True, "seed": 350},
]


def test_summarize_numbers():
    s = summarize(ROWS)
    assert s["decisions"] == 3
    assert s["all"]["agree_pct"] == 33.3
    assert s["all"]["mean_regret"] == 170.0
    assert s["all"]["decisive"] == 1
    assert s["by_level"][3]["n"] == 2
    assert s["by_round"]["6-10"]["n"] == 1
    assert s["pairs"][("advance", "attack")]["n"] == 1


def test_summarize_empty():
    assert summarize([{"game": True}])["decisions"] == 0