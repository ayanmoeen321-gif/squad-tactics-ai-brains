from collections import deque

from engine.grid import DIRECTIONS


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def walk_distances(grid, start, blocked=frozenset(), max_steps=None):
    """Steps from start to every tile reachable. Units in `blocked` cannot be entered."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if max_steps is not None and dist[cur] >= max_steps:
            continue
        for dr, dc in DIRECTIONS:
            nxt = (cur[0] + dr, cur[1] + dc)
            if nxt in dist or nxt in blocked or not grid.is_walkable(*nxt):
                continue
            dist[nxt] = dist[cur] + 1
            queue.append(nxt)
    return dist


def reachable_tiles(grid, start, move, blocked=frozenset()):
    """Tiles a unit can stand on after moving up to `move` steps (includes start)."""
    return walk_distances(grid, start, blocked, max_steps=move)


def shortest_path(grid, start, goal, blocked=frozenset()):
    """List of tiles from start to goal (both included), or None. Ties: fixed direction order."""
    if start == goal:
        return [start]
    prev = {start: None}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for dr, dc in DIRECTIONS:
            nxt = (cur[0] + dr, cur[1] + dc)
            if nxt in prev or nxt in blocked or not grid.is_walkable(*nxt):
                continue
            prev[nxt] = cur
            if nxt == goal:
                path = [nxt]
                while prev[path[-1]] is not None:
                    path.append(prev[path[-1]])
                return path[::-1]
            queue.append(nxt)
    return None


def has_line_of_sight(grid, a, b):
    """Straight line between tile centers. Walls block; units do not."""
    if a == b:
        return True
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    for i in range(1, n):
        r = round(a[0] + (b[0] - a[0]) * i / n)
        c = round(a[1] + (b[1] - a[1]) * i / n)
        if grid.tile(r, c) == "#":
            return False
    return True


def is_chokepoint(grid, r, c):
    """Floor tile with walls on two opposite sides."""
    if not grid.in_bounds(r, c) or grid.tile(r, c) == "#":
        return False

    def wall(rr, cc):
        return grid.in_bounds(rr, cc) and grid.tile(rr, cc) == "#"

    return (wall(r - 1, c) and wall(r + 1, c)) or (wall(r, c - 1) and wall(r, c + 1))