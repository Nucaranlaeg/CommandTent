from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from enum import Enum


class TTSMode(Enum):
    SYNTHESIZED = "synthesized"  # Text-to-speech synthesis
    SIMULATED = "simulated"      # Console output for testing


@dataclass
class TTSConfig:
    mode: TTSMode = TTSMode.SIMULATED
    voice_rate: float = 1.0  # Speech rate multiplier
    voice_pitch: float = 1.0  # Voice pitch
    volume: float = 1.0  # Volume level
    enabled: bool = True


class RadioResponseGenerator:
    """Generates natural language responses from radio events and unit states."""
    
    def __init__(self):
        self.response_templates = {
            "acknowledgment": [
                "{unit} acknowledging. {action}.",
                "Roger, {unit} here. {action}.",
                "Copy that, {unit}. {action}."
            ],
            "waypoint_reached": [
                "{unit} at waypoint {location}.",
                "{unit} arrived at {location}.",
                "Position {location}, {unit}."
            ],
            "contact": [
                "Contact! {unit} reports enemy at {location}.",
                "{unit} spotted enemy near {location}.",
                "Enemy contact, {unit} at {location}."
            ],
            "casualty": [
                "{unit} {status}!",
                "{unit} is {status}.",
                "Casualty report: {unit} {status}."
            ],
            "unable_to_comply": [
                "{unit} unable to comply. {reason}.",
                "Negative, {unit}. {reason}.",
                "Cannot execute, {unit}. {reason}."
            ],
            "status_update": [
                "{unit} status: {status}.",
                "This is {unit}, {status}.",
                "{unit} reporting {status}."
            ]
        }
    
    def generate_response(self, event_type: str, unit: str, **kwargs) -> str:
        """Generate a natural language response for a radio event."""
        templates = self.response_templates.get(event_type, ["{unit} reporting."])
        
        # Select template based on unit personality/randomness
        import random
        template = random.choice(templates)
        
        # Fill in the template
        response = template.format(unit=unit, **kwargs)
        return response
    
    def generate_acknowledgment(self, unit: str, action: str) -> str:
        """Generate acknowledgment response."""
        return self.generate_response("acknowledgment", unit, action=action)
    
    def generate_waypoint_reached(self, unit: str, location: str) -> str:
        """Generate waypoint reached response."""
        return self.generate_response("waypoint_reached", unit, location=location)
    
    def generate_contact_report(self, unit: str, location: str) -> str:
        """Generate contact report."""
        return self.generate_response("contact", unit, location=location)
    
    def generate_casualty_report(self, unit: str, status: str) -> str:
        """Generate casualty report."""
        return self.generate_response("casualty", unit, status=status)
    
    def generate_status_update(self, unit: str, status: str) -> str:
        """Generate status update."""
        return self.generate_response("status_update", unit, status=status)


class TTSEngine:
    """Text-to-speech engine for unit responses."""
    
    def __init__(self, config: TTSConfig, response_generator: RadioResponseGenerator):
        self.config = config
        self.response_generator = response_generator
        self.is_speaking = False
        self.speech_queue: List[str] = []
        
    def speak(self, text: str) -> None:
        """Convert text to speech."""
        if not self.config.enabled:
            return
            
        if self.config.mode == TTSMode.SIMULATED:
            self._simulate_speech(text)
        else:
            self._synthesize_speech(text)
    
    def _simulate_speech(self, text: str) -> None:
        """Simulate speech output for testing."""
        print(f"[TTS] {text}")
        time.sleep(0.5)  # Simulate speech duration
    
    def _synthesize_speech(self, text: str) -> None:
        """Synthesize actual speech (placeholder for real TTS)."""
        # In production, this would use a TTS library like pyttsx3, gTTS, or Azure Speech
        print(f"[TTS] {text}")
        time.sleep(0.5)
    
    def speak_radio_event(self, event_type: str, unit: str, **kwargs) -> None:
        """Generate and speak a radio event response."""
        response = self.response_generator.generate_response(event_type, unit, **kwargs)
        self.speak(response)


class VoiceRadioSystem:
    """Complete voice radio system with TTS responses."""
    
    def __init__(self, stt_engine, tts_engine: TTSEngine, command_parser, order_executor):
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        self.command_parser = command_parser
        self.order_executor = order_executor
        self.response_generator = RadioResponseGenerator()
        
    def process_radio_event(self, event_type: str, unit: str, **kwargs) -> None:
        """Process a radio event and generate TTS response."""
        if event_type == "acknowledgment":
            action = kwargs.get("action", "command received")
            self.tts_engine.speak_radio_event("acknowledgment", unit, action=action)
        elif event_type == "waypoint_reached":
            location = kwargs.get("location", "position")
            self.tts_engine.speak_radio_event("waypoint_reached", unit, location=location)
        elif event_type == "contact":
            location = kwargs.get("location", "unknown")
            self.tts_engine.speak_radio_event("contact", unit, location=location)
        elif event_type == "casualty":
            status = kwargs.get("status", "down")
            self.tts_engine.speak_radio_event("casualty", unit, status=status)
        elif event_type == "status_update":
            status = kwargs.get("status", "operational")
            self.tts_engine.speak_radio_event("status_update", unit, status=status)
    
    def simulate_unit_responses(self, radio_events: List[Dict]) -> None:
        """Simulate unit responses for a list of radio events."""
        for event in radio_events:
            event_type = event.get("type", "status_update")
            unit = event.get("unit", "Unknown")
            self.process_radio_event(event_type, unit, **event.get("data", {}))
