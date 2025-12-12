from __future__ import annotations

import heapq
from typing import Callable, Dict, List, Optional, Tuple

from map.map import Map
from map.terrain import NO_MOVE_ALLOWED, Road, Terrain

Coord = Tuple[int, int]


def _neighbors_no_corner_cut(game_map: Map, x: int, y: int) -> List[Coord]:
    w, h = game_map.width, game_map.height
    results: List[Coord] = []

    # 4-way
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h:
            results.append((nx, ny))

    # diagonals with no corner cutting
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nx, ny = x + dx, y + dy
        bx, by = x + dx, y  # side 1
        cx, cy = x, y + dy  # side 2
        if 0 <= nx < w and 0 <= ny < h:
            # only allow diagonal if both side cells are in bounds
            if 0 <= bx < w and 0 <= by < h and 0 <= cx < w and 0 <= cy < h:
                results.append((nx, ny))

    return results


def _heuristic(a: Coord, b: Coord) -> float:
    # Octile distance heuristic suitable for 8-directional grids
    (x1, y1), (x2, y2) = a, b
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    D = 1.0
    D2 = 1.41421356237
    return D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)


def _move_cost(cell: Terrain) -> float:
    if not hasattr(cell, "move_cost"):
        return NO_MOVE_ALLOWED
    return float(getattr(cell, "move_cost"))


def astar(
    game_map: Map,
    start: Coord,
    goal: Coord,
    neighbor_func: Callable[[Map, int, int], List[Coord]] = _neighbors_no_corner_cut,
) -> Optional[List[Coord]]:
    if start == goal:
        return [start]

    w, h = game_map.width, game_map.height
    sx, sy = start
    gx, gy = goal
    if not (0 <= sx < w and 0 <= sy < h and 0 <= gx < w and 0 <= gy < h):
        return None

    open_heap: List[Tuple[float, Coord]] = []
    heapq.heappush(open_heap, (0.0, start))

    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    g_score: Dict[Coord, float] = {start: 0.0}

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            # reconstruct path
            path: List[Coord] = []
            node: Optional[Coord] = current
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path

        cx, cy = current
        for nx, ny in neighbor_func(game_map, cx, cy):
            cell = game_map.map[ny][nx]
            cost = _move_cost(cell)
            if cost >= NO_MOVE_ALLOWED:
                continue
            tentative_g = g_score[current] + cost
            if tentative_g < g_score.get((nx, ny), float("inf")):
                came_from[(nx, ny)] = current
                g_score[(nx, ny)] = tentative_g
                f = tentative_g + _heuristic((nx, ny), goal)
                heapq.heappush(open_heap, (f, (nx, ny)))

    return None
