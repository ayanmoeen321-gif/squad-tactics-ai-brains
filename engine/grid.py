from collections import deque

from engine.data import DATA_DIR

SIZE = 12
TILES = {".", "#", "C", "L"}
HERO_SYMBOLS = {"1": "tank", "2": "archer", "3": "healer"}
MONSTER_SYMBOLS = {"g": "goblin", "b": "brute", "a": "archer", "h": "healer"}
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class MapError(ValueError):
    pass


class Grid:
    def __init__(self, tiles, hero_starts, monster_starts):
        self.tiles = tiles
        self.hero_starts = hero_starts
        self.monster_starts = monster_starts
        self.rows = len(tiles)
        self.cols = len(tiles[0])

    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def tile(self, r, c):
        return self.tiles[r][c]

    def is_walkable(self, r, c):
        return self.in_bounds(r, c) and self.tiles[r][c] != "#"

    def reachable_from(self, start):
        seen = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nxt = (r + dr, c + dc)
                if nxt not in seen and self.is_walkable(*nxt):
                    seen.add(nxt)
                    queue.append(nxt)
        return seen


def parse_map(text, size=SIZE):
    lines = text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) != size:
        raise MapError(f"expected {size} rows, got {len(lines)}")

    tiles = []
    hero_starts = {}
    monster_starts = []
    for r, line in enumerate(lines):
        if len(line) != size:
            raise MapError(f"row {r} has width {len(line)}, expected {size}")
        row = []
        for c, ch in enumerate(line):
            if ch in TILES:
                row.append(ch)
            elif ch in HERO_SYMBOLS:
                name = HERO_SYMBOLS[ch]
                if name in hero_starts:
                    raise MapError(f"duplicate hero start: {name}")
                hero_starts[name] = (r, c)
                row.append(".")
            elif ch in MONSTER_SYMBOLS:
                monster_starts.append((MONSTER_SYMBOLS[ch], (r, c)))
                row.append(".")
            else:
                raise MapError(f"unknown symbol {ch!r} at ({r},{c})")
        tiles.append(row)

    missing = set(HERO_SYMBOLS.values()) - set(hero_starts)
    if missing:
        raise MapError(f"missing hero starts: {sorted(missing)}")
    if not monster_starts:
        raise MapError("no monster starts")

    grid = Grid(tiles, hero_starts, monster_starts)
    for hero, hpos in hero_starts.items():
        reach = grid.reachable_from(hpos)
        for mtype, mpos in monster_starts:
            if mpos not in reach:
                raise MapError(f"{mtype} at {mpos} is not reachable from {hero}")
    return grid


def load_level(n):
    path = DATA_DIR / "levels" / f"level{n}.txt"
    return parse_map(path.read_text(encoding="utf-8"))