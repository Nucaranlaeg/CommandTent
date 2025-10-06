import map.terrain as terrain_module
from map.terrain import Terrain
import unit.unit as unit_module
from unit.unit import Unit
import inspect

terrain_types: list[type[Terrain]] = [
	getattr(terrain_module, attr) for attr in dir(terrain_module)
	if inspect.isclass(getattr(terrain_module, attr))  # Ensure it's a class
	and attr != "Terrain"  # Exclude the base Terrain class
	and issubclass(getattr(terrain_module, attr), Terrain)  # Check subclass
]

unit_types: list[type[Unit]] = [
	getattr(unit_module, attr) for attr in dir(unit_module)
	if inspect.isclass(getattr(unit_module, attr))  # Ensure it's a class
	and attr != "Unit"  # Exclude the base Unit class
	and issubclass(getattr(unit_module, attr), Unit)  # Check subclass
]

for terrain in terrain_types:
	print(f"Terrain: {terrain.__name__}")
	for unit in unit_types:
		print(f"  Unit: {unit.__name__.ljust(16)} - Move Speed: {unit().move_speed(terrain(0, 0))}")