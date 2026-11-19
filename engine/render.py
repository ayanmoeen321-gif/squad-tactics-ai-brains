HERO_CHARS = {"tank": "1", "archer": "2", "healer": "3"}
MONSTER_CHARS = {"goblin": "g", "brute": "b", "archer": "a", "healer": "h"}


def render(state):
    rows = [list(row) for row in state.grid.tiles]
    for u in state.living():
        chars = HERO_CHARS if u.side == "hero" else MONSTER_CHARS
        r, c = u.pos
        rows[r][c] = chars[u.kind]
    return "\n".join("".join(row) for row in rows)