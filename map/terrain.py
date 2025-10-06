from abc import ABC

NO_MOVE_ALLOWED: int = 1000
MAX_SIGHT: int = 10


class Terrain(ABC):
	vision_block: int = 0

	x: int
	y: int
	move_cost: float

	def __init__(self, x: int, y: int) -> None:
		self.x = x
		self.y = y


class Forest(Terrain):
	move_cost = 2

	def __repr__(self) -> str:
		return "Forest"


class Mountain(Terrain):
	vision_block: int = MAX_SIGHT
	move_cost = 5

	def __repr__(self) -> str:
		return "Mountain"


class Plain(Terrain):
	move_cost = 1.2

	def __repr__(self) -> str:
		return "Plain"


class Road(Terrain):
	move_cost = 1

	def __repr__(self) -> str:
		return "Road"
