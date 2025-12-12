from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from schemas.types import Intent, ROE, Posture, Speed


class LLMCommandParser:
    """LLM-based command parser for complex natural language commands."""
    
    def __init__(self, llm_client=None):
        # For MVP, we'll use a rule-based fallback that's more sophisticated
        # In production, this would use an actual LLM API
        self.llm_client = llm_client
        self.unit_names = {"Red", "Blue", "Green", "Gold", "Brown", "Alpha", "Bravo", "Charlie", "Delta", "Echo"}
        self.cell_pattern = re.compile(r'\b([A-J])([0-9])\b', re.IGNORECASE)
        
    def parse(self, text: str) -> Tuple[bool, Optional[dict], str]:
        """Parse complex natural language command into structured order."""
        text = text.strip()
        
        # For MVP, use enhanced rule-based parsing
        # In production, this would call the LLM with a structured prompt
        if self.llm_client:
            return self._llm_parse(text)
        else:
            return self._enhanced_rule_parse(text)
    
    def _llm_parse(self, text: str) -> Tuple[bool, Optional[dict], str]:
        """Parse using actual LLM (placeholder for production).
        
        For full command schema specification, see schemas/command_schema.md
        This document contains complete field definitions, enum values, natural language
        patterns, examples, and parsing guidelines for LLM-based command parsing.
        """
        # This would be the real LLM implementation
        # In production, load the schema from schemas/command_schema.md and include
        # it in the prompt for comprehensive parsing guidance.
        
        prompt = f"""
        Parse this military command into JSON format following the command schema.
        Command: "{text}"
        
        Extract:
        - units: list of unit names (Red, Blue, Green, Gold, Brown, Alpha, Bravo, etc.)
        - intent: move, hold, attack, observe, support, retreat, cancel
        - waypoints: list of command cells (A0-J9 format) or precise subcell coordinates
        - constraints: object with preferTerrain, stayConcealed, speed, avoidCells
        - roe: hold, return_fire, free
        - posture: stand, crouch, prone
        - engagement: object with targetCells and suppressOnly (for attack intent)
        - priority: low, normal, high
        - ack: boolean (default true)
        
        Handle complex cases like:
        - "Red move to A3 via forest in A4" -> waypoints: ["A3", "A4"], preferTerrain: ["forest"]
        - "Blue advance through A3 then B4, stay concealed" -> waypoints: ["A3", "B4"], stayConcealed: true
        - "Alpha and Bravo hold position, weapons tight" -> units: ["Alpha", "Bravo"], intent: "hold", roe: "hold"
        
        Return only valid JSON matching the command schema, no other text.
        For complete schema specification, see schemas/command_schema.md
        """
        
        # Placeholder - would call actual LLM here
        # For now, fall back to enhanced rules
        return self._enhanced_rule_parse(text)
    
    def _enhanced_rule_parse(self, text: str) -> Tuple[bool, Optional[dict], str]:
        """Enhanced rule-based parsing for complex commands."""
        text_lower = text.lower()
        
        # Extract units
        units = self._extract_units_enhanced(text_lower)
        if not units:
            return False, None, "No valid units found. Use Red, Blue, Green, Gold, Brown, or Alpha, Bravo, etc."
        
        # Extract intent and waypoints with better logic
        intent, waypoints = self._extract_movement_enhanced(text_lower)
        if not intent:
            intent, waypoints = self._extract_other_intents_enhanced(text_lower)
        
        # If no explicit intent but we have ROE/posture changes, treat as hold
        if not intent:
            roe = self._extract_roe_enhanced(text_lower)
            posture = self._extract_posture_enhanced(text_lower)
            if roe or posture:
                intent = Intent.HOLD
                waypoints = []
        
        if not intent:
            return False, None, "No valid command found. Try 'move', 'hold', 'attack', etc."
        
        # Extract constraints with better terrain/waypoint association
        constraints = self._extract_constraints_enhanced(text_lower, waypoints)
        
        # Extract ROE and posture
        roe = self._extract_roe_enhanced(text_lower)
        posture = self._extract_posture_enhanced(text_lower)
        
        order = {
            "units": units,
            "intent": intent.value,
            "waypoints": waypoints,
            "constraints": constraints,
            "roe": roe.value if roe else "return_fire",
            "posture": posture.value if posture else "stand"
        }
        
        return True, order, "Command parsed successfully"
    
    def _extract_units_enhanced(self, text: str) -> List[str]:
        """Enhanced unit extraction with better conjunctions."""
        found = []
        
        # Handle "Red and Blue", "Alpha, Bravo", "Red or Blue"
        conjunctions = [" and ", ", ", " or "]
        for conj in conjunctions:
            if conj in text:
                parts = text.split(conj)
                for part in parts:
                    for name in self.unit_names:
                        if name.lower() in part:
                            found.append(name)
                return found
        
        # Single unit
        for name in self.unit_names:
            if name.lower() in text:
                found.append(name)
        
        return found
    
    def _extract_movement_enhanced(self, text: str) -> Tuple[Optional[Intent], List[str]]:
        """Enhanced movement parsing with better waypoint extraction."""
        if not any(word in text for word in ["move", "go", "advance", "proceed", "head", "travel"]):
            return None, []
        
        # Find all command cells
        cells = self.cell_pattern.findall(text)
        waypoints = [f"{col.upper()}{row}" for col, row in cells]
        
        # Try to determine order from context
        if waypoints:
            # Look for sequence indicators
            if any(word in text for word in ["then", "next", "after", "through"]):
                # Keep original order as it likely indicates sequence
                pass
            elif any(word in text for word in ["to", "toward", "destination"]):
                # If "to" is mentioned, the last cell is likely the destination
                pass
            else:
                # Default: assume first mentioned is primary destination
                pass
            
            return Intent.MOVE, waypoints
        
        return None, []
    
    def _extract_other_intents_enhanced(self, text: str) -> Tuple[Optional[Intent], List[str]]:
        """Enhanced non-movement intent extraction."""
        if any(word in text for word in ["hold", "stop", "halt", "wait", "stay", "remain"]):
            return Intent.HOLD, []
        if any(word in text for word in ["attack", "fire", "engage", "shoot", "strike"]):
            return Intent.ATTACK, []
        if any(word in text for word in ["observe", "watch", "look", "scan", "monitor"]):
            return Intent.OBSERVE, []
        if any(word in text for word in ["support", "help", "assist", "backup"]):
            return Intent.SUPPORT, []
        if any(word in text for word in ["retreat", "withdraw", "fall back", "pull back"]):
            return Intent.RETREAT, []
        if any(word in text for word in ["cancel", "abort", "disregard", "ignore"]):
            return Intent.CANCEL, []
        return None, []
    
    def _extract_constraints_enhanced(self, text: str, waypoints: List[str]) -> dict:
        """Enhanced constraint extraction with terrain/waypoint association."""
        constraints = {}
        
        # Terrain preferences with better context
        prefer_terrain = []
        
        # Look for terrain mentions near waypoints
        if "road" in text or "roads" in text:
            prefer_terrain.append("road")
        if "forest" in text or "forests" in text or "trees" in text or "wood" in text:
            prefer_terrain.append("forest")
        if "building" in text or "buildings" in text or "structure" in text:
            prefer_terrain.append("building")
        if "open" in text or "field" in text or "clear" in text:
            prefer_terrain.append("open")
        
        if prefer_terrain:
            constraints["preferTerrain"] = prefer_terrain
        
        # Concealment
        if any(word in text for word in ["concealed", "hidden", "stealth", "sneak", "cover"]):
            constraints["stayConcealed"] = True
        
        # Speed
        if any(word in text for word in ["slow", "careful", "cautious", "crawl"]):
            constraints["speed"] = "slow"
        elif any(word in text for word in ["fast", "quick", "hurry", "rush", "sprint"]):
            constraints["speed"] = "fast"
        else:
            constraints["speed"] = "normal"
        
        # Avoid cells (basic implementation)
        avoid_indicators = ["avoid", "stay away", "don't go", "bypass"]
        if any(indicator in text for indicator in avoid_indicators):
            # This would need more sophisticated parsing to extract specific cells
            pass
        
        return constraints
    
    def _extract_roe_enhanced(self, text: str) -> Optional[ROE]:
        """Enhanced ROE extraction."""
        if any(phrase in text for phrase in ["hold fire", "weapons tight", "don't fire", "no fire", "cease fire"]):
            return ROE.HOLD
        if any(phrase in text for phrase in ["fire at will", "weapons free", "open fire", "engage freely", "weapons free"]):
            return ROE.FREE
        if any(phrase in text for phrase in ["return fire", "fire back", "defensive fire"]):
            return ROE.RETURN_FIRE
        return None
    
    def _extract_posture_enhanced(self, text: str) -> Optional[Posture]:
        """Enhanced posture extraction."""
        # Check for specific phrases first to avoid conflicts
        if any(phrase in text for phrase in ["crouch down", "crouched down"]):
            return Posture.CROUCH
        if any(phrase in text for phrase in ["lie down", "go prone"]):
            return Posture.PRONE
        if any(word in text for word in ["crouch", "crouched", "duck", "squat"]):
            return Posture.CROUCH
        if any(word in text for word in ["prone", "flat"]):
            return Posture.PRONE
        if any(word in text for word in ["down"]) and "crouch" not in text:
            return Posture.PRONE
        if any(word in text for word in ["stand", "upright", "on feet"]):
            return Posture.STAND
        return None
