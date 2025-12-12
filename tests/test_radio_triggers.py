from server.game.engine import Game, GameConfig
from unit.unit import UnitModel
from unit.combat import WeaponProfile, resolve_shot
from schemas.types import HealthState


def collect_msgs(game):
    return [e.message for e in game.radio_log]


def test_waypoint_report():
    g = Game(GameConfig(width=100, height=100, seed=3, radio_latency_ticks=1))
    u = UnitModel(unit_id="Red", speed_cells_per_second=10.0, position=(10.5, 10.5), fireteam_name="Red")
    g.add_unit(u)

    g.enqueue_order({"units": ["Red"], "intent": "move", "waypoints": ["A0"]})
    # Run enough ticks to arrive
    for _ in range(50):
        g.tick(1)
    msgs = collect_msgs(g)
    assert any("At waypoint." in m for m in msgs)


def test_contact_report():
    g = Game(GameConfig(width=100, height=100, seed=4, radio_latency_ticks=1))
    # Clear LOS blockers to ensure contact
    for row in g.game_map.map:
        for cell in row:
            cell.vision_block = 0
    a = UnitModel(unit_id="Red", speed_cells_per_second=0.0, position=(10.5, 10.5), fireteam_name="Red", side="A")
    b = UnitModel(unit_id="Blue", speed_cells_per_second=0.0, position=(12.5, 12.5), fireteam_name="Blue", side="B")
    g.add_unit(a)
    g.add_unit(b)

    g.tick(2)
    msgs = collect_msgs(g)
    assert any("Contact, enemy spotted" in m for m in msgs)


def test_casualty_report():
    g = Game(GameConfig(width=100, height=100, seed=5, radio_latency_ticks=1))
    s = UnitModel(unit_id="S", speed_cells_per_second=0.0, position=(10.5, 10.5), side="A")
    t = UnitModel(unit_id="T", speed_cells_per_second=0.0, position=(10.5, 11.5), side="B")
    g.add_unit(s)
    g.add_unit(t)

    prof = WeaponProfile(near=1.0, medium=1.0, far=1.0)
    resolve_shot(g.game_map, s, t, prof, g.sim.rng)
    g.tick(2)
    msgs = collect_msgs(g)
    assert any("WOUNDED" in m or "KIA" in m for m in msgs)
