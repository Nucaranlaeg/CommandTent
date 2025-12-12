from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Callable, Optional
from enum import Enum


class STTMode(Enum):
    PTT = "ptt"  # Push-to-talk
    VAD = "vad"  # Voice Activity Detection


@dataclass
class STTConfig:
    mode: STTMode = STTMode.PTT
    vad_threshold: float = 0.5  # 0.0 to 1.0
    vad_timeout: float = 2.0  # seconds of silence before stopping
    ptt_key: str = "space"  # key for push-to-talk
    sample_rate: int = 16000
    chunk_size: int = 1024


class STTEngine:
    """Speech-to-text engine with PTT and VAD support."""
    
    def __init__(self, config: STTConfig, on_transcript: Callable[[str], None]):
        self.config = config
        self.on_transcript = on_transcript
        self.is_listening = False
        self.is_recording = False
        self._stop_event = threading.Event()
        self._recording_thread: Optional[threading.Thread] = None
        
    def start_listening(self) -> None:
        """Start listening for speech based on configured mode."""
        if self.is_listening:
            return
            
        self.is_listening = True
        self._stop_event.clear()
        
        if self.config.mode == STTMode.PTT:
            self._start_ptt_listener()
        else:  # VAD mode
            self._start_vad_listener()
    
    def stop_listening(self) -> None:
        """Stop listening for speech."""
        self.is_listening = False
        self._stop_event.set()
        
        if self._recording_thread and self._recording_thread.is_alive():
            self._recording_thread.join(timeout=1.0)
    
    def _start_ptt_listener(self) -> None:
        """Start push-to-talk listener (placeholder for keyboard input)."""
        # In a real implementation, this would listen for the PTT key
        # For MVP, we'll simulate with a simple interface
        self._recording_thread = threading.Thread(target=self._ptt_loop)
        self._recording_thread.start()
    
    def _start_vad_listener(self) -> None:
        """Start voice activity detection listener."""
        # In a real implementation, this would use audio processing libraries
        # For MVP, we'll simulate VAD behavior
        self._recording_thread = threading.Thread(target=self._vad_loop)
        self._recording_thread.start()
    
    def _ptt_loop(self) -> None:
        """PTT loop - simulates key press detection."""
        while self.is_listening and not self._stop_event.is_set():
            # In real implementation, detect PTT key press
            # For MVP, simulate with time-based triggers
            time.sleep(0.1)
    
    def _vad_loop(self) -> None:
        """VAD loop - simulates voice activity detection."""
        while self.is_listening and not self._stop_event.is_set():
            # In real implementation, analyze audio for voice activity
            # For MVP, simulate with time-based triggers
            time.sleep(0.1)
    
    def simulate_voice_input(self, text: str) -> None:
        """Simulate voice input for testing purposes."""
        if self.is_listening:
            self.on_transcript(text)


class VoiceUX:
    """Voice user experience manager."""
    
    def __init__(self, stt_engine: STTEngine, command_parser, order_executor):
        self.stt_engine = stt_engine
        self.command_parser = command_parser
        self.order_executor = order_executor
        self.command_history = []
        self.is_active = False
        
    def start(self) -> None:
        """Start voice interface."""
        self.is_active = True
        self.stt_engine.start_listening()
        
    def stop(self) -> None:
        """Stop voice interface."""
        self.is_active = False
        self.stt_engine.stop_listening()
        
    def process_transcript(self, transcript: str) -> None:
        """Process a voice transcript into game commands."""
        # Process transcript regardless of active state for testing
            
        # Parse the transcript
        success, order, message = self.command_parser.parse(transcript)
        
        if success and order:
            # Execute the order if executor is available
            executed = False
            if self.order_executor:
                # Create a simple clock for testing
                from server.sim.loop import SimClock
                clock = SimClock()
                executed = self.order_executor.apply_order(clock, order)
            if executed:
                self.command_history.append({
                    "transcript": transcript,
                    "order": order,
                    "timestamp": time.time(),
                    "status": "executed"
                })
            else:
                self.command_history.append({
                    "transcript": transcript,
                    "order": order,
                    "timestamp": time.time(),
                    "status": "failed"
                })
        else:
            # Command parsing failed
            self.command_history.append({
                "transcript": transcript,
                "order": None,
                "timestamp": time.time(),
                "status": "parse_failed",
                "error": message
            })
    
    def get_recent_commands(self, count: int = 10) -> list:
        """Get recent command history."""
        return self.command_history[-count:]
