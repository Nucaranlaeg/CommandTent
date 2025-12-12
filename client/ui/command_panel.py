from __future__ import annotations

import pygame
from dataclasses import dataclass
from typing import List, Optional, Callable

from client.audio.stt import VoiceUX
from client.ui.map_view import MapView, UIConfig


@dataclass
class CommandEntry:
    transcript: str
    order: Optional[dict]
    status: str  # "executed", "failed", "parse_failed"
    timestamp: float
    error: Optional[str] = None


class CommandPanel:
    """Command history and voice interface panel."""
    
    def __init__(self, x: int, y: int, width: int, height: int, voice_ux: VoiceUX):
        self.rect = pygame.Rect(x, y, width, height)
        self.voice_ux = voice_ux
        # Initialize fonts only if pygame is initialized
        if pygame.get_init():
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        else:
            self.font = None
            self.small_font = None
        self.scroll_offset = 0
        self.max_entries = 20
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.text_color = (255, 255, 255)
        self.success_color = (0, 255, 0)
        self.error_color = (255, 0, 0)
        self.warning_color = (255, 255, 0)
        
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the command panel."""
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)
        
        # Draw title
        if self.font:
            title_text = self.font.render("Command History", True, self.text_color)
            screen.blit(title_text, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw command entries
        self._draw_command_entries(screen)
        
        # Draw voice status
        self._draw_voice_status(screen)
        
    def _draw_command_entries(self, screen: pygame.Surface) -> None:
        """Draw the list of command entries."""
        entries = self.voice_ux.get_recent_commands(self.max_entries)
        y_offset = 40
        line_height = 25
        
        for i, entry in enumerate(entries):
            if y_offset + line_height > self.rect.height - 20:
                break
                
            # Determine color based on status
            if entry["status"] == "executed":
                color = self.success_color
            elif entry["status"] == "failed":
                color = self.error_color
            else:  # parse_failed
                color = self.warning_color
                
            # Draw transcript
            if self.small_font:
                transcript_text = self.small_font.render(entry["transcript"], True, color)
                screen.blit(transcript_text, (self.rect.x + 10, self.rect.y + y_offset))
                
                # Draw status
                status_text = self.small_font.render(f"[{entry['status']}]", True, color)
                screen.blit(status_text, (self.rect.x + 10, self.rect.y + y_offset + 15))
                
                # Draw error if any
                if entry.get("error"):
                    error_text = self.small_font.render(f"Error: {entry['error']}", True, self.error_color)
                    screen.blit(error_text, (self.rect.x + 10, self.rect.y + y_offset + 30))
                y_offset += 45
            else:
                y_offset += 35
                
    def _draw_voice_status(self, screen: pygame.Surface) -> None:
        """Draw voice interface status."""
        status_y = self.rect.bottom - 30
        
        # Voice active status
        if self.small_font:
            if self.voice_ux.is_active:
                status_text = self.small_font.render("Voice: ACTIVE", True, self.success_color)
            else:
                status_text = self.small_font.render("Voice: INACTIVE", True, self.error_color)
            screen.blit(status_text, (self.rect.x + 10, status_y))
            
            # Instructions
            instructions = self.small_font.render("Press SPACE for PTT", True, self.text_color)
            screen.blit(instructions, (self.rect.x + 10, status_y + 15))


class StatusPanel:
    """Unit status and radio messages panel."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        # Initialize fonts only if pygame is initialized
        if pygame.get_init():
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        else:
            self.font = None
            self.small_font = None
        self.radio_messages = []
        self.max_messages = 15
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.text_color = (255, 255, 255)
        self.radio_color = (0, 255, 255)
        
    def add_radio_message(self, message: str) -> None:
        """Add a radio message to the display."""
        self.radio_messages.append(message)
        if len(self.radio_messages) > self.max_messages:
            self.radio_messages.pop(0)
            
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the status panel."""
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)
        
        # Draw title
        if self.font:
            title_text = self.font.render("Radio Messages", True, self.text_color)
            screen.blit(title_text, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw radio messages
        y_offset = 40
        line_height = 20
        
        for message in self.radio_messages[-self.max_messages:]:
            if y_offset + line_height > self.rect.height - 20:
                break
                
            if self.small_font:
                message_text = self.small_font.render(message, True, self.radio_color)
                screen.blit(message_text, (self.rect.x + 10, self.rect.y + y_offset))
            y_offset += line_height


class UIController:
    """Main UI controller that coordinates all panels."""
    
    def __init__(self, config: UIConfig, game_map, voice_ux: VoiceUX):
        self.config = config
        self.game_map = game_map
        self.voice_ux = voice_ux
        
        # Create panels
        map_x, map_y = 0, 0
        command_x = self.config.map_width
        command_y = 0
        status_x = self.config.map_width
        status_y = self.config.window_height // 2
        
        self.map_view = MapView(config, game_map)
        self.command_panel = CommandPanel(
            command_x, command_y, 
            self.config.window_width - self.config.map_width, 
            self.config.window_height // 2,
            voice_ux
        )
        self.status_panel = StatusPanel(
            status_x, status_y,
            self.config.window_width - self.config.map_width,
            self.config.window_height // 2
        )
        
        self.running = False
        self.prematch_mode = True
        
    def initialize(self) -> None:
        """Initialize the UI."""
        self.map_view.initialize()
        self.running = True
        
    def cleanup(self) -> None:
        """Clean up UI resources."""
        self.map_view.cleanup()
        self.running = False
        
    def handle_events(self) -> bool:
        """Handle pygame events. Returns False if should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Toggle voice interface
                    if self.voice_ux.is_active:
                        self.voice_ux.stop()
                    else:
                        self.voice_ux.start()
                elif event.key == pygame.K_f and self.prematch_mode:
                    # Start friendly tent placement
                    self.map_view.start_tent_placement('friendly')
                elif event.key == pygame.K_e and self.prematch_mode:
                    # Start enemy tent placement
                    self.map_view.start_tent_placement('enemy')
                elif event.key == pygame.K_RETURN and self.prematch_mode:
                    # Finish pre-match if both tents placed
                    if self.map_view.friendly_tent and self.map_view.enemy_tent:
                        self.prematch_mode = False
                elif event.key == pygame.K_d:
                    # Toggle debug overlay
                    self.map_view.debug_enabled = not self.map_view.debug_enabled
                elif event.key == pygame.K_p:
                    # Toggle debug paths
                    self.map_view.debug_show_paths = not self.map_view.debug_show_paths
                elif event.key == pygame.K_l:
                    # Toggle LOS lines
                    self.map_view.debug_show_los = not self.map_view.debug_show_los
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    clicked_unit = self.map_view.handle_mouse_click(event.pos)
                    if clicked_unit:
                        self.map_view.start_drag(clicked_unit, event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    self.map_view.end_drag()
            elif event.type == pygame.MOUSEMOTION:
                if self.map_view.dragged_unit:
                    self.map_view.handle_mouse_drag(event.pos)
                    # Only render the dragged unit, not the entire map
                    self.map_view.render_dragged_unit_only()
                    
        return True
        
    def update(self, units: dict) -> None:
        """Update the UI with current game state."""
        self.map_view.update_units(units)
        
    def render(self) -> None:
        """Render the complete UI."""
        if not self.map_view.screen:
            return
            
        # Render map view
        self.map_view.render()
        
        # Render panels
        self.command_panel.draw(self.map_view.screen)
        self.status_panel.draw(self.map_view.screen)
        
    def add_radio_message(self, message: str) -> None:
        """Add a radio message to the status panel."""
        self.status_panel.add_radio_message(message)
