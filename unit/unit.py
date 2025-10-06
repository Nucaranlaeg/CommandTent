import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from map.terrain import Terrain

class Unit:
	def __init__(self, name: str, health: float, attack: float, defense: int, vision: int, stealth: int, range: int, move_difficulty: float, movement: int) -> None:
		self.name: str = name
		self.health: float = health
		self.attack: float = attack
		self.defense: int = defense
		self.vision: int = vision
		self.stealth: int = stealth
		self.range: int = range
		self.move_difficulty: float = move_difficulty
		self.movement: int = movement

	def calculate_attack_power(self, distance: float, elevation: float, target_defense: int) -> float:
		# NO GOOD
		range: float = self.range
		if elevation > 0:
			distance += elevation * 0.1  # Slightly increase distance when firing downward
		elif elevation < 0:
			range -= elevation * 0.1  # Decrease effective range when firing upward

		x: float = distance / range
		hit_chance: float = -0.445331 * x**3 - 0.235704 * x**2 + 0.183937 * x + 0.926451
		hit_chance = min(0.95, max(0.0, hit_chance))  # Clamp hit chance between 0 and 0.95

		if random.random() > hit_chance:
			return 0.0

		# Calculate damage with a small decrease based on adjusted distance
		distance_factor: float = max(0.8, 1 - (distance / (2 * range)))  # Damage decreases slightly with distance
		random_factor: float = random.uniform(0.8, 1.2)  # Random factor between 80% and 120%
		attack_power: float = self.attack * distance_factor * random_factor

		damage: float = attack_power - max(min(attack_power / 2, target_defense), target_defense / 2)
		return 0 if damage <= 0 else damage ** 2 / target_defense

	def make_attack(self, target: "Unit", distance: float, elevation: float) -> str:
		damage: float = self.calculate_attack_power(distance, elevation, target.defense)
		target.health -= damage
		return f"{self.name} attacks {target.name} for {damage:.2f} damage!"

	def is_alive(self) -> bool:
		return self.health > 0
	
	def move_speed(self, terrain: "Terrain") -> float:
		cost: float = terrain.move_cost ** self.move_difficulty
		return self.movement / max(1, cost)

	def __str__(self) -> str:
		return (f"{self.name} (Health: {self.health}, Base Attack: {self.attack}, "
				f"Defense: {self.defense}, Vision: {self.vision}, Stealth: {self.stealth}, Range: {self.range})")


class LightInfantry(Unit):
	def __init__(self, name: str = "Light Infantry") -> None:
		super().__init__(name, health=30, attack=4, defense=2, vision=5, stealth=6, range=3, move_difficulty=1, movement=1)


class HeavyInfantry(Unit):
	def __init__(self, name: str = "Heavy Infantry") -> None:
		super().__init__(name, health=30, attack=6, defense=2, vision=4, stealth=4, range=3, move_difficulty=1.1, movement=1)


class SelfPropelledGun(Unit):
	def __init__(self, name: str = "Self-Propelled Gun") -> None:
		super().__init__(name, health=1000, attack=25, defense=8, vision=2, stealth=1, range=10, move_difficulty=3, movement=6)


class Armour(Unit):
	def __init__(self, name: str = "Armour") -> None:
		super().__init__(name, health=4000, attack=20, defense=15, vision=2, stealth=1, range=6, move_difficulty=3, movement=10)

class Truck(Unit):
	def __init__(self, name: str = "Halftrack") -> None:
		super().__init__(name, health=500, attack=0, defense=5, vision=3, stealth=1, range=1, move_difficulty=4, movement=12)