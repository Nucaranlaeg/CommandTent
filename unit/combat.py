from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from map.map import Map
from map.terrain import MAX_SIGHT
from unit.unit import UnitModel
from schemas.types import HealthState


@dataclass
class WeaponProfile:
    near: float  # hit chance at near range
    medium: float
    far: float


def distance_cells(a: tuple[float, float], b: tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    return max(abs(ax - bx), abs(ay - by))


def has_los(game_map: Map, a: tuple[float, float], b: tuple[float, float]) -> bool:
    ax, ay = int(a[0]), int(a[1])
    bx, by = int(b[0]), int(b[1])
    source = game_map.map[ay][ax]
    target = game_map.map[by][bx]
    sight = game_map.determine_sight(source_cell=source, target_cell=target)
    return sight > 0


def detect_enemy(game_map: Map, observer: UnitModel, target: UnitModel) -> bool:
    if not has_los(game_map, observer.position, target.position):
        return False
    d = distance_cells(observer.position, target.position)
    return d <= MAX_SIGHT


def accuracy_for_range(profile: WeaponProfile, d: float) -> float:
    if d <= 2.0:
        return profile.near
    if d <= 4.0:
        return profile.medium
    return profile.far


def resolve_shot(game_map: Map, shooter: UnitModel, target: UnitModel, profile: WeaponProfile, rng) -> Optional[HealthState]:
    if target.health_state == HealthState.KIA:
        return None
    if not detect_enemy(game_map, shooter, target):
        return None

    d = distance_cells(shooter.position, target.position)
    p_hit = accuracy_for_range(profile, d)

    # Cover approximation using terrain vision block
    tx, ty = int(target.position[0]), int(target.position[1])
    terrain_block = game_map.map[ty][tx].vision_block
    if terrain_block > 0:
        p_hit *= 0.7

    if rng.random() <= p_hit:
        # If already wounded, higher chance to become KIA
        if target.health_state == HealthState.WOUNDED:
            kia_prob = 0.6
        else:
            kia_prob = 0.3
        if rng.random() < kia_prob:
            target.health_state = HealthState.KIA
        else:
            target.health_state = HealthState.WOUNDED
        return target.health_state

    return None
