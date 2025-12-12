from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from map.map import Map
from server.sim.loop import Simulation, TICK_DT
from server.radio.bus import RadioBus, RadioEvent
from server.orders.executor import OrderExecutor
from unit.unit import UnitModel, UnitState
from unit.combat import detect_enemy


@dataclass
class GameConfig:
    width: int = 1000
    height: int = 1000
    seed: int = 1
    radio_latency_ticks: int = 3
    # Optional pre-match tent positions in world/subcell coords (x, y)
    friendly_tent: Optional[tuple[float, float]] = None
    enemy_tent: Optional[tuple[float, float]] = None


@dataclass
class Game:
    config: GameConfig
    game_map: Map = field(init=False)
    units: Dict[str, UnitModel] = field(default_factory=dict)
    radio: RadioBus = field(init=False)
    sim: Simulation = field(init=False)
    executor: OrderExecutor = field(init=False)
    radio_log: List[RadioEvent] = field(default_factory=list)
    friendly_tent: Optional[tuple[float, float]] = None
    enemy_tent: Optional[tuple[float, float]] = None

    def __post_init__(self) -> None:
        self.game_map = Map(self.config.width, self.config.height, seed=self.config.seed)
        self.radio = RadioBus(latency_ticks=self.config.radio_latency_ticks)
        self.sim = Simulation(seed=self.config.seed)
        self.executor = OrderExecutor(self.game_map, self.units, self.radio)
        # Initialize tent positions from config if provided
        self.friendly_tent = self.config.friendly_tent
        self.enemy_tent = self.config.enemy_tent

    def add_unit(self, unit: UnitModel) -> None:
        self.units[unit.unit_id] = unit

    def enqueue_order(self, order: dict) -> bool:
        return self.executor.apply_order(self.sim.clock, order)

    def set_friendly_tent(self, pos: tuple[float, float]) -> None:
        self.friendly_tent = pos
        self.config.friendly_tent = pos

    def set_enemy_tent(self, pos: tuple[float, float]) -> None:
        self.enemy_tent = pos
        self.config.enemy_tent = pos

    def _radio_handler(self, evt: RadioEvent) -> None:
        self.radio_log.append(evt)

    def _maybe_report_waypoint(self, unit: UnitModel) -> None:
        if unit.state == UnitState.IDLE and unit.target is None:
            self.radio.send(self.sim.clock, unit.unit_id, "At waypoint.")

    def _maybe_report_contacts(self) -> None:
        # For each pair of opposing units, if detection newly true, report contact
        ids = list(self.units.keys())
        for i in range(len(ids)):
            a = self.units[ids[i]]
            for j in range(i + 1, len(ids)):
                b = self.units[ids[j]]
                if a.side == b.side:
                    continue
                if detect_enemy(self.game_map, a, b):
                    self.radio.send(self.sim.clock, a.unit_id, f"Contact, enemy spotted near ({int(b.position[0])},{int(b.position[1])}).")
                if detect_enemy(self.game_map, b, a):
                    self.radio.send(self.sim.clock, b.unit_id, f"Contact, enemy spotted near ({int(a.position[0])},{int(a.position[1])}).")

    def _maybe_report_casualties(self) -> None:
        for u in self.units.values():
            if u.health_state.name in ("WOUNDED", "KIA"):
                self.radio.send(self.sim.clock, u.unit_id, f"{u.health_state.name}.")

    def _execute_combat(self) -> None:
        """Execute combat between opposing units."""
        from unit.combat import resolve_shot, WeaponProfile
        
        # Create weapon profiles for different unit types
        rifleman_profile = WeaponProfile(near=0.35, medium=0.2, far=0.05)
        
        unit_list = list(self.units.values())
        for i, shooter in enumerate(unit_list):
            if shooter.health_state.name == "KIA":
                continue
                
            # Only shoot if ROE allows it
            if shooter.roe.name == "HOLD":
                continue
                
            for j, target in enumerate(unit_list):
                if i == j or target.side == shooter.side:
                    continue
                if target.health_state.name == "KIA":
                    continue
                    
                # Check if shooter can engage target
                if shooter.roe.name == "RETURN_FIRE" and not self._has_been_fired_at(shooter):
                    continue
                    
                # Execute shot
                result = resolve_shot(self.game_map, shooter, target, rifleman_profile, self.sim.rng)
                if result:
                    self.radio.send(self.sim.clock, shooter.unit_id, 
                                  f"Engaging enemy at ({int(target.position[0])},{int(target.position[1])}).")

    def _has_been_fired_at(self, unit: UnitModel) -> bool:
        """Check if unit has been fired at recently (simplified for MVP)."""
        # For MVP, assume units can return fire if they detect enemies
        return True

    def tick(self, num_ticks: int = 1) -> None:
        for _ in range(num_ticks):
            self.sim.step()
            for unit in self.units.values():
                unit.tick_move(TICK_DT)
                self._maybe_report_waypoint(unit)
            self._execute_combat()
            self._maybe_report_contacts()
            self._maybe_report_casualties()
            self.radio.deliver(self.sim.clock, self._radio_handler)
