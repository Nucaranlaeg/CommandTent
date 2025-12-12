from __future__ import annotations

from typing import Dict, List

from map.map import Map
from schemas.validate import validate_order
from unit.unit import UnitModel
from server.radio.bus import RadioBus


class OrderExecutor:
    def __init__(self, game_map: Map, units: Dict[str, UnitModel], radio: RadioBus) -> None:
        self.map = game_map
        self.units = units
        self.radio = radio

    def apply_order(self, clock, order: dict) -> bool:
        ok, msg = validate_order(order)
        if not ok:
            return False

        intent = order.get("intent")
        unit_names: List[str] = order.get("units", [])
        waypoints: List[str] = order.get("waypoints", [])
        constraints = order.get("constraints", {})
        prefer = list(constraints.get("preferTerrain", []) or [])
        if constraints.get("stayConcealed") and "forest" not in prefer:
            prefer.append("forest")
        roe = order.get("roe")
        posture = order.get("posture")

        # Apply ROE/Posture updates immediately
        for name in unit_names:
            u = self.units.get(name)
            if not u:
                continue
            if roe:
                try:
                    from schemas.types import ROE as ROEEnum
                    u.roe = ROEEnum(roe)
                except Exception:
                    pass
            if posture:
                try:
                    from schemas.types import Posture as PostureEnum
                    u.posture = PostureEnum(posture)
                except Exception:
                    pass

        # Movement handling: last waypoint decides the command cell destination
        if intent == "move" and waypoints:
            last_waypoint = waypoints[-1]
            
            # Handle both command cell strings and subcell objects
            if isinstance(last_waypoint, str):
                # Traditional command cell format (e.g., "D3")
                cell_label = last_waypoint
                bounds = self.map.command_cell_bounds(cell_label)
                station = self.map.choose_station_within_bounds(bounds, prefer=prefer)
            elif isinstance(last_waypoint, dict) and "commandCell" in last_waypoint and "subcell" in last_waypoint:
                # New subcell format
                cell_label = last_waypoint["commandCell"]
                subcell = last_waypoint["subcell"]
                bounds = self.map.command_cell_bounds(cell_label)
                
                # Convert subcell coordinates to world coordinates
                x0, y0, x1, y1 = bounds
                subcell_x = x0 + (subcell["x"] / 100.0) * (x1 - x0)
                subcell_y = y0 + (subcell["y"] / 100.0) * (y1 - y0)
                station = (subcell_x, subcell_y)
            else:
                # Fallback to command cell center
                cell_label = str(last_waypoint)
                bounds = self.map.command_cell_bounds(cell_label)
                station = self.map.choose_station_within_bounds(bounds, prefer=prefer)
            
            for name in unit_names:
                u = self.units.get(name)
                if not u:
                    continue
                goal_cell = (int(station[0]), int(station[1]))
                if u.set_move_target(self.map, goal_cell):
                    ack = f"Acknowledged. Moving to {cell_label}. ROE={u.roe.value}, Posture={u.posture.value}"
                    self.radio.send(clock, channel=name, message=ack)
            return True

        # Hold/observe/support can be further implemented
        if intent in ("hold", "observe", "support", "retreat", "attack", "cancel"):
            # MVP: Acknowledge only
            for name in unit_names:
                self.radio.send(clock, channel=name, message=f"Acknowledged. Intent {intent}.")
            return True

        return False
