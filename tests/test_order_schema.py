import json
from pathlib import Path

from schemas.validate import validate_order


def test_order_valid_minimal():
    order = {
        "units": ["Red"],
        "intent": "move",
        "waypoints": ["A3"],
        "ack": True,
    }
    ok, msg = validate_order(order)
    assert ok, msg


def test_order_invalid_bad_cell():
    order = {
        "units": ["Red"],
        "intent": "move",
        "waypoints": ["Z99"],
    }
    ok, msg = validate_order(order)
    assert not ok
    assert "waypoints" in msg
