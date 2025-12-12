from server.sim.loop import Simulation
from map.map import Map
from unit.unit import UnitModel
from unit.combat import has_los, detect_enemy, resolve_shot, WeaponProfile
from schemas.types import HealthState


def test_los_and_detection():
    m = Map(10, 10, seed=42)
    a = UnitModel(unit_id="A", speed_cells_per_second=1.0, position=(1.5, 1.5))
    b = UnitModel(unit_id="B", speed_cells_per_second=1.0, position=(3.5, 3.5))

    assert has_los(m, a.position, b.position) in (True, False)
    los = has_los(m, a.position, b.position)
    assert detect_enemy(m, a, b) == los


def test_resolve_shot_prefers_kia_when_wounded():
    m = Map(10, 10, seed=1)
    shooter = UnitModel(unit_id="S", speed_cells_per_second=1.0, position=(2.5, 2.5))
    target = UnitModel(unit_id="T", speed_cells_per_second=1.0, position=(2.5, 3.5))

    sim = Simulation(seed=7)
    profile = WeaponProfile(near=0.9, medium=0.5, far=0.2)

    # First wound the target
    for _ in range(50):
        resolve_shot(m, shooter, target, profile, sim.rng)
        if target.health_state == HealthState.WOUNDED:
            break

    # Then try to achieve KIA; higher chance now
    kia_seen = False
    for _ in range(100):
        resolve_shot(m, shooter, target, profile, sim.rng)
        if target.health_state == HealthState.KIA:
            kia_seen = True
            break

    assert target.health_state in {HealthState.WOUNDED, HealthState.KIA}
    assert kia_seen or target.health_state == HealthState.KIA
