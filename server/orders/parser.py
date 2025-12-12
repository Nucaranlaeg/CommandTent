from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from schemas.types import Intent, ROE, Posture, Speed


class CommandParser:
    def __init__(self) -> None:
        # Known unit/fireteam names
        self.unit_names = {"Red", "Blue", "Green", "Gold", "Brown", "Alpha", "Bravo", "Charlie", "Delta", "Echo"}
        # Command cell pattern: A-J followed by 0-9
        self.cell_pattern = re.compile(r'\b([A-J])([0-9])\b', re.IGNORECASE)
        
    def parse(self, text: str) -> Tuple[bool, Optional[dict], str]:
        """Parse natural language command into structured order.
        
        Returns (success, order_dict, message)
        """
        text = text.strip().lower()
        
        # Extract units/fireteams
        units = self._extract_units(text)
        if not units:
            return False, None, "No valid units found. Use Red, Blue, Green, Gold, Brown, or Alpha, Bravo, etc."
        
        # Extract intent and waypoints
        intent, waypoints = self._extract_movement(text)
        if not intent:
            intent, waypoints = self._extract_other_intents(text)
        
        if not intent:
            return False, None, "No valid command found. Try 'move', 'hold', 'attack', etc."
        
        # Extract constraints
        constraints = self._extract_constraints(text)
        
        # Extract ROE and posture
        roe = self._extract_roe(text)
        posture = self._extract_posture(text)
        
        order = {
            "units": units,
            "intent": intent.value,
            "waypoints": waypoints,
            "constraints": constraints,
            "roe": roe.value if roe else "return_fire",
            "posture": posture.value if posture else "stand"
        }
        
        return True, order, "Command parsed successfully"
    
    def _extract_units(self, text: str) -> List[str]:
        """Extract unit/fireteam names from text."""
        found = []
        for name in self.unit_names:
            if name.lower() in text:
                found.append(name)
        return found
    
    def _extract_movement(self, text: str) -> Tuple[Optional[Intent], List[str]]:
        """Extract movement intent and waypoints."""
        if not any(word in text for word in ["move", "go", "advance", "proceed"]):
            return None, []
        
        # Find command cells
        cells = self.cell_pattern.findall(text)
        waypoints = [f"{col.upper()}{row}" for col, row in cells]
        
        if waypoints:
            return Intent.MOVE, waypoints
        return None, []
    
    def _extract_other_intents(self, text: str) -> Tuple[Optional[Intent], List[str]]:
        """Extract non-movement intents."""
        if any(word in text for word in ["hold", "stop", "halt", "wait"]):
            return Intent.HOLD, []
        if any(word in text for word in ["attack", "fire", "engage", "shoot"]):
            return Intent.ATTACK, []
        if any(word in text for word in ["observe", "watch", "look", "scan"]):
            return Intent.OBSERVE, []
        if any(word in text for word in ["support", "help", "assist"]):
            return Intent.SUPPORT, []
        if any(word in text for word in ["retreat", "withdraw", "fall back"]):
            return Intent.RETREAT, []
        if any(word in text for word in ["cancel", "abort", "disregard"]):
            return Intent.CANCEL, []
        return None, []
    
    def _extract_constraints(self, text: str) -> dict:
        """Extract movement constraints."""
        constraints = {}
        
        # Terrain preferences
        prefer_terrain = []
        if "road" in text or "roads" in text:
            prefer_terrain.append("road")
        if "forest" in text or "forests" in text or "trees" in text:
            prefer_terrain.append("forest")
        if "building" in text or "buildings" in text:
            prefer_terrain.append("building")
        if prefer_terrain:
            constraints["preferTerrain"] = prefer_terrain
        
        # Concealment
        if any(word in text for word in ["concealed", "hidden", "stealth", "sneak"]):
            constraints["stayConcealed"] = True
        
        # Speed
        if any(word in text for word in ["slow", "careful", "cautious"]):
            constraints["speed"] = "slow"
        elif any(word in text for word in ["fast", "quick", "hurry", "rush"]):
            constraints["speed"] = "fast"
        else:
            constraints["speed"] = "normal"
        
        return constraints
    
    def _extract_roe(self, text: str) -> Optional[ROE]:
        """Extract Rules of Engagement."""
        if any(word in text for word in ["hold fire", "weapons tight", "don't fire", "no fire"]):
            return ROE.HOLD
        if any(word in text for word in ["fire at will", "weapons free", "open fire"]):
            return ROE.FREE
        return None  # Default to return_fire
    
    def _extract_posture(self, text: str) -> Optional[Posture]:
        """Extract posture commands."""
        if any(word in text for word in ["prone", "down", "lie down"]):
            return Posture.PRONE
        if any(word in text for word in ["crouch", "crouched", "duck"]):
            return Posture.CROUCH
        return None  # Default to stand
