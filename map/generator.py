from __future__ import annotations

import random
from typing import Callable, List, Tuple, Type

from map.terrain import Forest, Mountain, Plain, Road, Terrain

TerrainClass = Type[Terrain]


def generate(width: int, height: int, seed: int) -> List[List[Terrain]]:
    rng = random.Random(seed)

    # Start with plains
    grid: List[List[Terrain]] = [[Plain(x, y) for x in range(width)] for y in range(height)]

    # Lay roads (simple horizontal and vertical spines with branches)
    hrow = rng.randrange(0, height)
    for x in range(width):
        grid[hrow][x] = Road(x, hrow)
    vcol = rng.randrange(0, width)
    for y in range(height):
        grid[y][vcol] = Road(vcol, y)

    # Branches
    for _ in range(max(1, (width + height) // 6)):
        y = rng.randrange(0, height)
        limit = rng.randrange(0, width)
        for x in range(limit):
            if rng.random() < 0.2:
                grid[y][x] = Road(x, y)

    # Scatter forests (clusters) - scale sublinearly for performance on large maps
    # Aim for O((W+H)) clusters rather than O(W*H)
    base_clusters = (width + height) // 2
    num_clusters = max(1, min(base_clusters, 2000))  # cap to avoid extremes
    max_radius = max(2, min(25, min(width, height) // 20))
    for _ in range(num_clusters):
        cx = rng.randrange(0, width)
        cy = rng.randrange(0, height)
        radius = rng.randrange(1, max_radius)
        r2 = radius * radius
        y_start = max(0, cy - radius)
        y_end = min(height - 1, cy + radius)
        for y in range(y_start, y_end + 1):
            dy = y - cy
            # compute x span for circle row to reduce inner iterations
            dx_max2 = r2 - dy * dy
            if dx_max2 < 0:
                continue
            dx_max = int(dx_max2 ** 0.5)
            x_start = max(0, cx - dx_max)
            x_end = min(width - 1, cx + dx_max)
            for x in range(x_start, x_end + 1):
                if not isinstance(grid[y][x], Road):
                    grid[y][x] = Forest(x, y)

    # Mountains as impassable LOS blockers (sparse)
    for _ in range(max(1, (width + height) // 8)):
        nx = rng.randrange(0, width)
        ny = rng.randrange(0, height)
        if not isinstance(grid[ny][nx], Road):
            grid[ny][nx] = Mountain(nx, ny)

    return grid
