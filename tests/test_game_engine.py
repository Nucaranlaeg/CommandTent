from server.game.engine import Game, GameConfig
from unit.unit import UnitModel, UnitState


def test_game_headless_order_and_movement():
    g = Game(GameConfig(width=1000, height=1000, seed=10, radio_latency_ticks=1))
    g.add_unit(UnitModel(unit_id="Red", speed_cells_per_second=5.0, position=(10.5, 10.5), fireteam_name="Red"))

    order = {
        "units": ["Red"],
        "intent": "move",
        "waypoints": ["D3"],
        "constraints": {"preferTerrain": ["forest"]},
    }

    assert g.enqueue_order(order)
    # First tick: deliver ack
    g.tick(1)
    assert any(evt.channel == "Red" for evt in g.radio_log)

    # Advance multiple ticks, expect movement toward target
    start_pos = g.units["Red"].position
    g.tick(10)
    assert g.units["Red"].position != start_pos
