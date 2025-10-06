from typing import Generator, Optional
import map.terrain as terrain_module
from map.terrain import MAX_SIGHT, Terrain
import re
import inspect

# Extract terrain classes from the terrain_types module
terrain_types: list[type[Terrain]] = [
	getattr(terrain_module, attr) for attr in dir(terrain_module)
	if inspect.isclass(getattr(terrain_module, attr))  # Ensure it's a class
	and attr != "Terrain"  # Exclude the base Terrain class
	and issubclass(getattr(terrain_module, attr), Terrain)  # Check subclass
]

class Map:
	def __init__(self, width: int, height: int):
		self.width = width
		self.height = height
		self.generate_map()

	def generate_map(self) -> None:
		self.map: list[list[Terrain]] = []
		for y in range(self.height):
			row: list[Terrain] = []
			for x in range(self.width):
				# Randomly select a terrain type
				terrain_type: type[Terrain] = terrain_types[(x + y) % len(terrain_types)]
				row.append(terrain_type(x, y))
			self.map.append(row)

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

game_map = Map(10, 10)
