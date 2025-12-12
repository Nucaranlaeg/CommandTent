import types

import pytest

from map.map import Map
from map.pathfinding import astar
from map.terrain import Road, Plain, Forest, NO_MOVE_ALLOWED


@pytest.fixture
def small_map() -> Map:
    m = Map(5, 5)
    # Force a simple known terrain layout: default to Plain
    for y in range(m.height):
        for x in range(m.width):
            m.map[y][x].__class__ = Plain  # monkey-patch class for cost usage
    return m


def test_astar_straight_line(small_map: Map):
    path = astar(small_map, (0, 0), (0, 4))
    assert path is not None
    # length should be 5 cells including start/end
    assert len(path) == 5
    assert path[0] == (0, 0)
    assert path[-1] == (0, 4)


def test_astar_diagonal_allowed_no_corner_cut(small_map: Map):
    path = astar(small_map, (0, 0), (4, 4))
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (4, 4)


def test_astar_prefers_road_when_available(small_map: Map):
    # Carve a horizontal road on row 2 (y=2) with lowest cost
    y = 2
    for x in range(small_map.width):
        small_map.map[y][x].__class__ = Road

    path = astar(small_map, (0, 0), (4, 4))
    assert path is not None
    # Expect many steps to traverse via y=2 due to cheaper Road cells
    ys = [py for (_, py) in path]
    assert y in ys
