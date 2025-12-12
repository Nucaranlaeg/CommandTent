from typing import Generator, Optional
import map.terrain as terrain_module
from map.terrain import MAX_SIGHT, Terrain
import re
import inspect

from map.generator import generate as generate_seeded

# Extract terrain classes from the terrain_types module
terrain_types: list[type[Terrain]] = [
	getattr(terrain_module, attr) for attr in dir(terrain_module)
	if inspect.isclass(getattr(terrain_module, attr))  # Ensure it's a class
	and attr != "Terrain"  # Exclude the base Terrain class
	and issubclass(getattr(terrain_module, attr), Terrain)  # Check subclass
]

class Map:
	def __init__(self, width: int, height: int, seed: Optional[int] = None):
		self.width = width
		self.height = height
		self.generate_map(seed)

	def generate_map(self, seed: Optional[int] = None) -> None:
		self.map: list[list[Terrain]] = []
		if seed is not None:
			self.map = generate_seeded(self.width, self.height, seed)
			return
		for y in range(self.height):
			row: list[Terrain] = []
			for x in range(self.width):
				terrain_type: type[Terrain] = terrain_types[(x + y) % len(terrain_types)]
				row.append(terrain_type(x, y))
			self.map.append(row)

	def command_cell_size(self) -> tuple[int, int]:
		"""Return the size in base cells of each command cell (assumes 10x10 command grid)."""
		return max(1, self.width // 10), max(1, self.height // 10)

	def command_cell_bounds(self, cell: str) -> tuple[int, int, int, int]:
		"""Compute inclusive [x0,y0] to inclusive [x1,y1] bounds for a command grid label like "D3" (A-J, 0-9)."""
		if not cell or len(cell) < 2:
			raise ValueError("Invalid command cell label")
		col_letter = cell[0].upper()
		if col_letter < 'A' or col_letter > 'J':
			raise ValueError("Column out of range")
		try:
			row_idx = int(cell[1])
		except ValueError:
			raise ValueError("Row must be 0-9")
		if row_idx < 0 or row_idx > 9:
			raise ValueError("Row out of range")
		col_idx = ord(col_letter) - ord('A')
		cw, ch = self.command_cell_size()
		x0 = col_idx * cw
		y0 = row_idx * ch
		x1 = min(self.width - 1, x0 + cw - 1)
		y1 = min(self.height - 1, y0 + ch - 1)
		return x0, y0, x1, y1

	def choose_station_within_bounds(self, bounds: tuple[int, int, int, int], prefer: list[str] | None = None) -> tuple[float, float]:
		"""Pick a station point within bounds, preferring terrain types (by class name) if provided. Returns subcell center coords (x+0.5, y+0.5)."""
		x0, y0, x1, y1 = bounds
		# Try preferred terrains in order
		if prefer:
			pref_set = [p.lower() for p in prefer]
			for p in pref_set:
				for y in range(y0, y1 + 1):
					for x in range(x0, x1 + 1):
						name = self.map[y][x].__class__.__name__.lower()
						if p in name:
							return x + 0.5, y + 0.5
		# Fallback to approximate center of the command cell
		cx = (x0 + x1) / 2.0
		cy = (y0 + y1) / 2.0
		return cx + 0.0, cy + 0.0

	def find_cell(self, loc_string: str) -> Terrain:
		"""
		Finds a cell in the map based on a string location (e.g., "A1", "B2").
		Returns the Terrain object at that location.
		"""
		row_match = re.findall(r"[A-Za-z]+", loc_string)
		col_match = re.findall(r"\d+", loc_string)
		if row_match and col_match:
			row = ord(row_match[0].upper()) - ord('A')
			col = int(col_match[0]) - 1
			if 0 <= row < self.height and 0 <= col < self.width:
				return self.map[row][col]
		raise ValueError(f"Invalid location: {loc_string}")
	
	def determine_sight(
			self,
			source: Optional[str] = None,
			target: Optional[str] = None,
			source_cell: Optional[Terrain] = None,
			target_cell: Optional[Terrain] = None
		) -> int:
		"""
		Determines if there's an open sightline from the source to the target.
		Returns the lowest sight value of the intervening spaces.
		"""
		if source_cell is None:
			if source is None:
				raise ValueError("Either source or source_cell must be provided.")
			source_cell = self.find_cell(source)
		if target_cell is None:
			if target is None:
				raise ValueError("Either target or target_cell must be provided.")
			target_cell = self.find_cell(target)

		x1, y1 = source_cell.x, source_cell.y
		x2, y2 = target_cell.x, target_cell.y

		current_sight: int = MAX_SIGHT

		for cell in self.line_cells(x1, y1, x2, y2):
			if (cell.x == x1 and cell.y == y1) or (cell.x == x2 and cell.y == y2):
				continue
			current_sight -= cell.vision_block
			if current_sight <= 0:
				return 0

		return current_sight

	def line_cells(self, x1: int, y1: int, x2: int, y2: int) -> Generator[Terrain, None, None]:
		"""
		Generator function that yields cells along the line from (x1, y1) to (x2, y2).
		"""
		dx = abs(x2 - x1)
		dy = abs(y2 - y1)
		sx = 1 if x1 < x2 else -1
		sy = 1 if y1 < y2 else -1
		err = dx - dy

		while x1 != x2 or y1 != y2:
			yield self.map[y1][x1]
			e2 = 2 * err
			if e2 > -dy:
				err -= dy
				x1 += sx
			if e2 < dx:
				err += dx
				y1 += sy
		yield self.map[y2][x2]  # Yield the last cell

# Keep a small default map for tests/examples
game_map = Map(10, 10)
