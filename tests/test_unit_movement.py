from server.sim.loop import Simulation, TICK_DT
from map.map import Map
from unit.unit import UnitModel, UnitState, enforce_cohesion


def cell_of(pos):
    return (int(pos[0]), int(pos[1]))


def test_unit_moves_along_path():
    m = Map(5, 5, seed=123)
    u = UnitModel(unit_id="A", speed_cells_per_second=2.0, position=(0.5, 0.5))

    assert u.set_move_target(m, (0, 4))

    s = Simulation(seed=1)
    s.run_for_ticks(20, realtime=False)
    for _ in range(20):
        u.tick_move(TICK_DT)

    assert cell_of(u.position) == (0, 4)
    assert u.state == UnitState.IDLE


def test_cohesion_snap_back():
    m = Map(5, 5, seed=1)
    leader = UnitModel(unit_id="L", speed_cells_per_second=1.0, position=(2.5, 2.5), fireteam_name="Red", is_leader=True)
    follower = UnitModel(unit_id="F", speed_cells_per_second=1.0, position=(0.5, 0.5), fireteam_name="Red")

    enforce_cohesion(leader, follower)
    assert cell_of(follower.position) != (0, 0)
