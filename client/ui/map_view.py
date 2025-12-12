from __future__ import annotations

import pygame
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from map.map import Map
from unit.unit import UnitModel
from schemas.types import TerrainType
from unit.combat import detect_enemy


@dataclass
class UIConfig:
    window_width: int = 1200
    window_height: int = 800
    map_width: int = 800
    map_height: int = 600
    cell_size: int = 60  # Size of each command cell in pixels
    grid_color: tuple = (100, 100, 100)
    background_color: tuple = (50, 50, 50)


class MapView:
    """Main map view with command grid and terrain display."""
    
    def __init__(self, config: UIConfig, game_map: Map):
        self.config = config
        self.game_map = game_map
        self.screen = None
        self.clock = None
        self.running = False
        
        # Terrain colors
        self.terrain_colors = {
            TerrainType.ROAD: (150, 150, 150),
            TerrainType.OPEN: (100, 150, 100),
            TerrainType.FOREST: (50, 100, 50),
            TerrainType.BUILDING: (120, 80, 60),
            TerrainType.WATER: (50, 100, 200),
        }
        
        # Unit icons (simple colored circles for now)
        self.unit_icons = {}
        self.dragged_unit = None
        self.drag_offset = (0, 0)
        self.dragged_unit_old_pos = None  # Store previous position for efficient redraw
        
        # Tent placement state (pre-match)
        self.placement_mode: Optional[str] = None  # 'friendly' or 'enemy'
        self.friendly_tent: Optional[Tuple[float, float]] = None
        self.enemy_tent: Optional[Tuple[float, float]] = None

        # Debug overlay
        self.debug_enabled: bool = False
        self.debug_show_paths: bool = False
        self.debug_show_los: bool = False
        self.last_fps: float = 0.0
        
    def initialize(self) -> None:
        """Initialize Pygame and create the main window."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.config.window_width, self.config.window_height))
        pygame.display.set_caption("Command Tent")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)  # Cache font for performance
        self.running = True
        
    def cleanup(self) -> None:
        """Clean up Pygame resources."""
        if self.screen:
            pygame.quit()
            
    def world_to_screen(self, world_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        x, y = world_pos
        # Map world coordinates to screen, accounting for command cell size
        screen_x = int(x * self.config.cell_size)
        screen_y = int(y * self.config.cell_size)
        return screen_x, screen_y
        
    def screen_to_world(self, screen_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        screen_x, screen_y = screen_pos
        world_x = screen_x / self.config.cell_size
        world_y = screen_y / self.config.cell_size
        return world_x, world_y
        
    def draw_terrain(self) -> None:
        """Draw the terrain background with detailed features."""
        # For MVP, we'll show a simplified terrain view with detailed features
        # In production, this would render the actual map terrain
        for y in range(10):  # Command grid rows
            for x in range(10):  # Command grid columns
                cell_label = f"{chr(ord('A') + x)}{y}"
                bounds = self.game_map.command_cell_bounds(cell_label)
                
                # Get dominant terrain type in this command cell
                terrain_type = self._get_dominant_terrain(bounds)
                color = self.terrain_colors.get(terrain_type, (100, 100, 100))
                
                # Draw command cell
                rect = pygame.Rect(
                    x * self.config.cell_size,
                    y * self.config.cell_size,
                    self.config.cell_size,
                    self.config.cell_size
                )
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw detailed terrain features
                self._draw_terrain_features(bounds, rect)
                
                # Draw grid lines
                pygame.draw.rect(self.screen, self.config.grid_color, rect, 1)
                
                # Draw cell label
                font = pygame.font.Font(None, 24)
                text = font.render(cell_label, True, (255, 255, 255))
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)
        
        # Draw tent allowed zones overlay if in placement mode
        if self.placement_mode:
            overlay = pygame.Surface((self.config.map_width, self.config.map_height), pygame.SRCALPHA)
            width_px = self.config.map_width
            height_px = self.config.map_height
            zone_color = (255, 255, 0, 60)
            if self.placement_mode == 'friendly':
                # Left 30%
                rect = pygame.Rect(0, 0, int(width_px * 0.3), height_px)
                pygame.draw.rect(overlay, zone_color, rect)
            elif self.placement_mode == 'enemy':
                # Right 30%
                rect = pygame.Rect(int(width_px * 0.7), 0, int(width_px * 0.3), height_px)
                pygame.draw.rect(overlay, zone_color, rect)
            self.screen.blit(overlay, (0, 0))
                
    def _get_dominant_terrain(self, bounds: Tuple[int, int, int, int]) -> TerrainType:
        """Get the dominant terrain type in a command cell."""
        x0, y0, x1, y1 = bounds
        terrain_counts = {}
        
        for y in range(y0, min(y1 + 1, len(self.game_map.map))):
            for x in range(x0, min(x1 + 1, len(self.game_map.map[0]))):
                terrain_name = self.game_map.map[y][x].__class__.__name__.lower()
                terrain_counts[terrain_name] = terrain_counts.get(terrain_name, 0) + 1
        
        if not terrain_counts:
            return TerrainType.OPEN
            
        dominant = max(terrain_counts.items(), key=lambda x: x[1])[0]
        
        # Map terrain names to TerrainType
        terrain_map = {
            'road': TerrainType.ROAD,
            'plain': TerrainType.OPEN,
            'forest': TerrainType.FOREST,
            'mountain': TerrainType.BUILDING,  # Use building color for mountains
        }
        
        return terrain_map.get(dominant, TerrainType.OPEN)
        
    def _draw_terrain_features(self, bounds: Tuple[int, int, int, int], cell_rect: pygame.Rect) -> None:
        """Draw specific terrain features like trees, buildings, roads within a command cell."""
        x0, y0, x1, y1 = bounds
        
        # Sample terrain types within the cell
        terrain_features = []
        for y in range(y0, min(y1 + 1, len(self.game_map.map))):
            for x in range(x0, min(x1 + 1, len(self.game_map.map[0]))):
                terrain_name = self.game_map.map[y][x].__class__.__name__.lower()
                terrain_features.append(terrain_name)
        
        # Draw roads (lines)
        if 'road' in terrain_features:
            self._draw_road_features(cell_rect, terrain_features)
            
        # Draw trees (small circles)
        if 'forest' in terrain_features:
            self._draw_forest_features(cell_rect, terrain_features)
            
        # Draw buildings (rectangles)
        if 'mountain' in terrain_features:
            self._draw_building_features(cell_rect, terrain_features)
            
    def _draw_road_features(self, cell_rect: pygame.Rect, terrain_features: List[str]) -> None:
        """Draw road features within a command cell."""
        road_color = (200, 200, 200)
        
        # Draw horizontal road if road terrain is present
        if terrain_features.count('road') > len(terrain_features) // 3:
            # Draw horizontal road line
            road_y = cell_rect.centery
            pygame.draw.line(self.screen, road_color, 
                           (cell_rect.left + 5, road_y), 
                           (cell_rect.right - 5, road_y), 3)
            
    def _draw_forest_features(self, cell_rect: pygame.Rect, terrain_features: List[str]) -> None:
        """Draw forest features (trees) within a command cell."""
        tree_color = (34, 139, 34)
        tree_count = min(terrain_features.count('forest'), 6)  # Max 6 trees per cell
        
        for i in range(tree_count):
            # Random-ish positions based on cell size
            tree_x = cell_rect.left + (i * cell_rect.width // tree_count) + cell_rect.width // (tree_count * 2)
            tree_y = cell_rect.top + (i % 2) * cell_rect.height // 2 + cell_rect.height // 4
            
            # Draw small tree (circle)
            pygame.draw.circle(self.screen, tree_color, (int(tree_x), int(tree_y)), 3)
            
    def _draw_building_features(self, cell_rect: pygame.Rect, terrain_features: List[str]) -> None:
        """Draw building features within a command cell."""
        building_color = (139, 69, 19)
        
        if 'mountain' in terrain_features:
            # Draw a building rectangle
            building_w = cell_rect.width // 3
            building_h = cell_rect.height // 3
            building_x = cell_rect.centerx - building_w // 2
            building_y = cell_rect.centery - building_h // 2
            
            building_rect = pygame.Rect(building_x, building_y, building_w, building_h)
            pygame.draw.rect(self.screen, building_color, building_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), building_rect, 1)
        
    def draw_unit_icon(self, unit: UnitModel, screen_pos: Tuple[int, int]) -> None:
        """Draw a unit icon at the given screen position."""
        # Simple colored circle based on unit type/team
        color = (255, 0, 0) if unit.side == "A" else (0, 0, 255)
        radius = 15
        
        # Draw circle with border for better visibility
        pygame.draw.circle(self.screen, color, screen_pos, radius)
        pygame.draw.circle(self.screen, (255, 255, 255), screen_pos, radius, 2)
        
        # Draw unit ID (only if font is available)
        if self.font:
            text = self.font.render(unit.unit_id, True, (255, 255, 255))
            text_rect = text.get_rect(center=screen_pos)
            self.screen.blit(text, text_rect)
        
    def draw_units(self, units: Dict[str, UnitModel]) -> None:
        """Draw all units on the map."""
        for unit in units.values():
            world_pos = unit.position
            screen_pos = self.world_to_screen(world_pos)
            self.draw_unit_icon(unit, screen_pos)
        
        # Draw tents if set
        tent_radius = 10
        if self.friendly_tent:
            pygame.draw.circle(self.screen, (255, 255, 0), self.world_to_screen(self.friendly_tent), tent_radius)
        if self.enemy_tent:
            pygame.draw.circle(self.screen, (255, 165, 0), self.world_to_screen(self.enemy_tent), tent_radius)
            
    def handle_mouse_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse click and return clicked unit ID if any."""
        # Tent placement click handling
        if self.placement_mode:
            world_pos = self.screen_to_world(pos)
            if self._is_valid_tent_position(world_pos, side=self.placement_mode):
                if self.placement_mode == 'friendly':
                    self.friendly_tent = world_pos
                else:
                    self.enemy_tent = world_pos
                # Exit placement mode after placing
                self.placement_mode = None
                return None
            # If invalid, ignore and remain in placement mode
            return None

        # Check if click is on a unit
        for unit_id, unit in self.unit_icons.items():
            unit_pos = self.world_to_screen(unit.position)
            distance = ((pos[0] - unit_pos[0]) ** 2 + (pos[1] - unit_pos[1]) ** 2) ** 0.5
            if distance <= 15:  # Unit radius
                return unit_id
        return None
        
    def handle_mouse_drag(self, pos: Tuple[int, int]) -> None:
        """Handle mouse drag for unit icons."""
        if self.dragged_unit:
            # Store old position before updating
            if self.dragged_unit in self.unit_icons:
                self.dragged_unit_old_pos = self.world_to_screen(self.unit_icons[self.dragged_unit].position)
            
            # Apply drag offset for smooth dragging
            adjusted_pos = (pos[0] - self.drag_offset[0], pos[1] - self.drag_offset[1])
            world_pos = self.screen_to_world(adjusted_pos)
            # Update unit position (this is non-authoritative, just for UI)
            self.unit_icons[self.dragged_unit].position = world_pos
            
    def start_drag(self, unit_id: str, pos: Tuple[int, int]) -> None:
        """Start dragging a unit icon."""
        if unit_id in self.unit_icons:
            self.dragged_unit = unit_id
            unit_pos = self.world_to_screen(self.unit_icons[unit_id].position)
            self.drag_offset = (pos[0] - unit_pos[0], pos[1] - unit_pos[1])
            
    def end_drag(self) -> None:
        """End dragging a unit icon."""
        self.dragged_unit = None
        self.drag_offset = (0, 0)
        self.dragged_unit_old_pos = None
        
    def update_units(self, units: Dict[str, UnitModel]) -> None:
        """Update the unit icons with current unit positions."""
        self.unit_icons = units.copy()

    def start_tent_placement(self, side: str) -> None:
        """Begin pre-match tent placement for 'friendly' or 'enemy'."""
        if side not in ('friendly', 'enemy'):
            return
        self.placement_mode = side

    def _is_valid_tent_position(self, world_pos: Tuple[float, float], side: str) -> bool:
        """Validate tent position: left 30% for friendly, right 30% for enemy."""
        x, y = world_pos
        width_cells = self.config.map_width / self.config.cell_size
        height_cells = self.config.map_height / self.config.cell_size
        if not (0 <= x <= width_cells and 0 <= y <= height_cells):
            return False
        if side == 'friendly':
            return x <= width_cells * 0.3
        else:
            return x >= width_cells * 0.7
        
    def render(self) -> None:
        """Render the map view."""
        if not self.screen:
            return
            
        # Clear screen
        self.screen.fill(self.config.background_color)
        
        # Draw terrain
        self.draw_terrain()
        
        # Draw units
        self.draw_units(self.unit_icons)
        
        # Draw debug extras
        if self.debug_enabled and self.debug_show_paths:
            self._draw_unit_paths(self.unit_icons)
        if self.debug_enabled and self.debug_show_los:
            self._draw_los_lines(self.unit_icons)
        
        # Debug overlay
        if self.debug_enabled:
            self._draw_debug_overlay()

        # Update display
        pygame.display.flip()

    def render_dragged_unit_only(self) -> None:
        """Efficiently render only the dragged unit for smooth dragging."""
        if not self.screen or not self.dragged_unit or not self.dragged_unit_old_pos:
            return
            
        # Get the dragged unit
        dragged_unit = self.unit_icons.get(self.dragged_unit)
        if not dragged_unit:
            return
            
        # Clear the area where the unit was previously drawn
        old_pos = self.dragged_unit_old_pos
        clear_rect = pygame.Rect(old_pos[0] - 20, old_pos[1] - 20, 40, 40)
        
        # Redraw the terrain in the cleared area
        self._redraw_terrain_area(clear_rect)
        
        # Draw the dragged unit at its new position
        new_pos = self.world_to_screen(dragged_unit.position)
        self.draw_unit_icon(dragged_unit, new_pos)
        
        # Update only the affected area
        pygame.display.update(clear_rect)

    def _redraw_terrain_area(self, rect: pygame.Rect) -> None:
        """Redraw terrain in a specific rectangular area."""
        # Convert screen coordinates to world coordinates
        world_x = rect.x / self.config.cell_size
        world_y = rect.y / self.config.cell_size
        world_w = rect.width / self.config.cell_size
        world_h = rect.height / self.config.cell_size
        
        # Draw terrain cells that intersect with the rectangle
        for y in range(int(world_y), int(world_y + world_h) + 1):
            for x in range(int(world_x), int(world_x + world_w) + 1):
                if 0 <= x < 10 and 0 <= y < 10:  # Command grid bounds
                    cell_label = f"{chr(65 + x)}{y}"
                    bounds = self.game_map.command_cell_bounds(cell_label)
                    terrain_type = self._get_dominant_terrain(bounds)
                    color = self.terrain_colors.get(terrain_type, (100, 150, 100))
                    
                    # Draw command cell
                    cell_rect = pygame.Rect(
                        x * self.config.cell_size,
                        y * self.config.cell_size,
                        self.config.cell_size,
                        self.config.cell_size
                    )
                    pygame.draw.rect(self.screen, color, cell_rect)
                    pygame.draw.rect(self.screen, self.config.grid_color, cell_rect, 1)
                    
                    # Draw cell label
                    if self.font:
                        text = self.font.render(cell_label, True, (255, 255, 255))
                        text_rect = text.get_rect(center=cell_rect.center)
                        self.screen.blit(text, text_rect)

    def _draw_debug_overlay(self) -> None:
        """Draw debug info: FPS, unit count, tent positions."""
        if not self.screen:
            return
        overlay_font = pygame.font.Font(None, 22)
        lines = []
        lines.append(f"FPS: {self.last_fps:.1f}")
        lines.append(f"Units: {len(self.unit_icons)}")
        if self.friendly_tent:
            fx, fy = self.friendly_tent
            lines.append(f"Friendly Tent: ({fx:.1f}, {fy:.1f})")
        if self.enemy_tent:
            ex, ey = self.enemy_tent
            lines.append(f"Enemy Tent: ({ex:.1f}, {ey:.1f})")
        y = 10
        for line in lines:
            surf = overlay_font.render(line, True, (255, 255, 255))
            self.screen.blit(surf, (10, y))
            y += 18

    def _draw_unit_paths(self, units: Dict[str, UnitModel]) -> None:
        """Draw planned paths for units if available."""
        for unit in units.values():
            path = getattr(unit, 'path', None)
            if not path:
                continue
            points = [self.world_to_screen((float(px), float(py))) for (px, py) in path]
            if len(points) >= 2:
                pygame.draw.lines(self.screen, (0, 255, 255), False, points, 2)

    def _draw_los_lines(self, units: Dict[str, UnitModel]) -> None:
        """Draw LOS lines between opposing units where detection is true."""
        ids = list(units.keys())
        for i in range(len(ids)):
            a = units[ids[i]]
            for j in range(i + 1, len(ids)):
                b = units[ids[j]]
                if a.side == b.side:
                    continue
                try:
                    if detect_enemy(self.game_map, a, b):
                        pygame.draw.line(self.screen, (255, 0, 0), self.world_to_screen(a.position), self.world_to_screen(b.position), 1)
                    if detect_enemy(self.game_map, b, a):
                        pygame.draw.line(self.screen, (255, 0, 0), self.world_to_screen(b.position), self.world_to_screen(a.position), 1)
                except Exception:
                    # Be resilient in UI debug
                    continue
