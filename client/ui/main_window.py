from __future__ import annotations

import pygame
import time
from typing import Dict

from client.ui.map_view import MapView, UIConfig
from client.ui.command_panel import UIController
from client.audio.stt import STTEngine, STTConfig, VoiceUX
from client.audio.tts import TTSEngine, TTSConfig, VoiceRadioSystem
from server.orders.llm_parser import LLMCommandParser
from server.game.engine import Game, GameConfig
from unit.unit import UnitModel


class CommandTentUI:
    """Main UI application for Command Tent."""
    
    def __init__(self):
        self.config = UIConfig()
        self.game = None
        self.ui_controller = None
        self.voice_ux = None
        self.voice_radio = None
        self.running = False
        
    def initialize(self) -> None:
        """Initialize the game and UI."""
        # Create game
        self.game = Game(GameConfig(width=1000, height=1000, seed=42))
        
        # Add some test units
        self.game.add_unit(UnitModel(
            unit_id="Red", 
            speed_cells_per_second=5.0, 
            position=(10.5, 10.5), 
            fireteam_name="Red",
            side="A"
        ))
        self.game.add_unit(UnitModel(
            unit_id="Blue", 
            speed_cells_per_second=4.0, 
            position=(15.5, 15.5), 
            fireteam_name="Blue",
            side="A"
        ))
        
        # Create voice interface
        stt_config = STTConfig(mode="ptt")
        stt_engine = STTEngine(stt_config, self._on_transcript)
        tts_config = TTSConfig(mode="simulated")
        tts_engine = TTSEngine(tts_config, None)
        parser = LLMCommandParser()
        
        self.voice_ux = VoiceUX(stt_engine, parser, self.game.executor)
        self.voice_radio = VoiceRadioSystem(stt_engine, tts_engine, parser, self.game.executor)
        
        # Create UI controller
        self.ui_controller = UIController(self.config, self.game.game_map, self.voice_ux)
        self.ui_controller.initialize()
        
        # Show pre-match hint in radio/status panel
        self.ui_controller.add_radio_message("Pre-match: Press F to place friendly tent (left 30%).")
        self.ui_controller.add_radio_message("Pre-match: Press E to place enemy tent (right 30%).")
        self.ui_controller.add_radio_message("Press Enter to start when both tents are placed.")
        
        self.running = True
        
    def _on_transcript(self, transcript: str) -> None:
        """Handle voice transcript from STT."""
        self.voice_ux.process_transcript(transcript)
        
        # Generate TTS response
        if self.voice_ux.command_history:
            last_command = self.voice_ux.command_history[-1]
            if last_command["status"] == "executed":
                # Generate acknowledgment
                unit = last_command["order"]["units"][0] if last_command["order"]["units"] else "Unit"
                self.voice_radio.process_radio_event("acknowledgment", unit, action="command received")
            elif last_command["status"] == "parse_failed":
                # Generate error response
                self.voice_radio.process_radio_event("unable_to_comply", "System", reason="command not understood")
                
    def run(self) -> None:
        """Main game loop."""
        if not self.running:
            return
            
        clock = pygame.time.Clock()
        last_sim_time = 0
        sim_interval = 100  # Run simulation every 100ms (10Hz)
        
        while self.running:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            if not self.ui_controller.handle_events():
                self.running = False
                break
                
            # Update game simulation at 10Hz
            if current_time - last_sim_time >= sim_interval:
                self.game.tick(1)
                last_sim_time = current_time
                
                # Update UI with new unit positions
                self.ui_controller.update(self.game.units)
                
                # If pre-match finished and tents set on UI, store in game
                if not self.ui_controller.prematch_mode:
                    if self.ui_controller.map_view.friendly_tent:
                        self.game.set_friendly_tent(self.ui_controller.map_view.friendly_tent)
                    if self.ui_controller.map_view.enemy_tent:
                        self.game.set_enemy_tent(self.ui_controller.map_view.enemy_tent)
                
                # Simulate some radio messages for demo
                if current_time % 5000 < 100:  # Every 5 seconds
                    self.ui_controller.add_radio_message("Red reporting position A3")
            
            # Render at high FPS for smooth dragging
            self.ui_controller.render()
            
            # No FPS cap for maximum responsiveness
            clock.tick(0)  # Unlimited FPS
            # Store FPS for debug overlay
            if self.ui_controller and self.ui_controller.map_view:
                self.ui_controller.map_view.last_fps = clock.get_fps()
            
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.ui_controller:
            self.ui_controller.cleanup()
        self.running = False


def main():
    """Main entry point for the UI."""
    app = CommandTentUI()
    
    try:
        app.initialize()
        app.run()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
