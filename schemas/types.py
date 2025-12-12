from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class TerrainType(str, Enum):
    ROAD = "road"
    OPEN = "open"
    FOREST = "forest"
    BUILDING = "building"
    WATER = "water"


class HealthState(str, Enum):
    HEALTHY = "Healthy"
    WOUNDED = "Wounded"
    KIA = "KIA"


class Posture(str, Enum):
    STAND = "stand"
    CROUCH = "crouch"
    PRONE = "prone"


class ROE(str, Enum):
    HOLD = "hold"
    RETURN_FIRE = "return_fire"
    FREE = "free"


class Intent(str, Enum):
    MOVE = "move"
    HOLD = "hold"
    ATTACK = "attack"
    OBSERVE = "observe"
    SUPPORT = "support"
    RETREAT = "retreat"
    CANCEL = "cancel"


class Speed(str, Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class TerrainCell:
    terrain: TerrainType
    movement_multiplier: float
    concealment: float
    cover: float
    walkable: bool = True
    blocks_los: bool = False


@dataclass
class MapGrid:
    seed: int
    command_cols: List[str]  # ["A".."J"]
    command_rows: List[int]  # [0..9]
    subcell_size: Tuple[int, int]  # (width, height), e.g., (100, 100)


@dataclass
class Unit:
    unit_id: str
    archetype: str
    fireteam: Optional[str]
    position_subcell: Tuple[int, int]
    posture: Posture
    health: HealthState


@dataclass
class EngagementSpec:
    target_cells: List[str] = field(default_factory=list)
    suppress_only: bool = False


@dataclass
class Constraints:
    prefer_terrain: List[TerrainType] = field(default_factory=list)
    avoid_cells: List[str] = field(default_factory=list)
    stay_concealed: bool = False
    speed: Speed = Speed.NORMAL


@dataclass
class Order:
    units: List[str]
    intent: Intent
    waypoints: List[str] = field(default_factory=list)
    constraints: Constraints = field(default_factory=Constraints)
    roe: ROE = ROE.RETURN_FIRE
    posture: Posture = Posture.STAND
    engagement: EngagementSpec = field(default_factory=EngagementSpec)
    priority: Priority = Priority.NORMAL
    ack: bool = True
