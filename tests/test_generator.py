from map.map import Map
from map.terrain import Forest, Mountain, Road


def snapshot_types(m: Map):
    return [[cell.__class__.__name__ for cell in row] for row in m.map]


def test_seed_determinism():
    m1 = Map(10, 10, seed=123)
    m2 = Map(10, 10, seed=123)
    assert snapshot_types(m1) == snapshot_types(m2)


def test_seed_variability():
    m1 = Map(10, 10, seed=123)
    m2 = Map(10, 10, seed=456)
    assert snapshot_types(m1) != snapshot_types(m2)


def test_generator_includes_features():
    m = Map(10, 10, seed=789)
    names = {cell.__class__.__name__ for row in m.map for cell in row}
    assert "Road" in names
    assert ("Forest" in names) or ("Mountain" in names)


def test_command_cell_bounds_and_station_selection():
    m = Map(1000, 1000, seed=101)
    # D3 bounds (0-indexed rows/cols; D is 3rd index from A=0)
    x0, y0, x1, y1 = m.command_cell_bounds("D3")
    assert (x1 - x0 + 1) == 100
    assert (y1 - y0 + 1) == 100

    # Prefer forest when selecting station
    sx, sy = m.choose_station_within_bounds((x0, y0, x1, y1), prefer=["forest"])
    assert x0 <= int(sx) <= x1
    assert y0 <= int(sy) <= y1
