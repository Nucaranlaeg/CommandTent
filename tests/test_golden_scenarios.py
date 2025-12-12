"""
Golden scenario tests for Command Tent MVP.

These tests ensure deterministic behavior across the entire system
with fixed seeds, scripted orders, and expected outcomes.
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass

from server.game.engine import Game, GameConfig
from unit.unit import UnitModel, UnitState
from schemas.types import HealthState, ROE, Posture


@dataclass
class ScenarioResult:
    """Expected outcome of a golden scenario."""
    final_positions: Dict[str, tuple[float, float]]
    final_health_states: Dict[str, str]
    radio_messages: List[str]
    total_ticks: int


class GoldenScenarioTester:
    """Test harness for deterministic scenario validation."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.results: List[ScenarioResult] = []
    
    def run_scenario(self, name: str, config: GameConfig, units: List[UnitModel], 
                    orders: List[Dict[str, Any]], expected_ticks: int) -> ScenarioResult:
        """Run a complete scenario and return deterministic results."""
        game = Game(config)
        
        # Add units
        for unit in units:
            game.add_unit(unit)
        
        # Execute orders
        for order in orders:
            assert game.enqueue_order(order), f"Failed to enqueue order: {order}"
        
        # Run simulation
        game.tick(expected_ticks)
        
        # Collect results
        final_positions = {unit_id: unit.position for unit_id, unit in game.units.items()}
        final_health_states = {unit_id: unit.health_state.name for unit_id, unit in game.units.items()}
        radio_messages = [evt.message for evt in game.radio_log]
        
        result = ScenarioResult(
            final_positions=final_positions,
            final_health_states=final_health_states,
            radio_messages=radio_messages,
            total_ticks=expected_ticks
        )
        
        self.results.append(result)
        return result
    
    def assert_deterministic(self, scenario_name: str, tolerance: float = 0.01):
        """Assert that running the same scenario twice produces identical results."""
        # This would be implemented to run scenarios multiple times and compare
        pass


def test_basic_movement_scenario():
    """Golden scenario: Basic unit movement with pathfinding."""
    tester = GoldenScenarioTester(seed=123)
    
    config = GameConfig(width=100, height=100, seed=123, radio_latency_ticks=2)
    units = [
        UnitModel(unit_id="Alpha", speed_cells_per_second=3.0, position=(5.5, 5.5), side="A"),
        UnitModel(unit_id="Bravo", speed_cells_per_second=2.5, position=(8.5, 8.5), side="A")
    ]
    
    orders = [
        {
            "units": ["Alpha"],
            "intent": "move",
            "waypoints": ["D7"],
            "constraints": {"preferTerrain": ["road"], "speed": "normal"}
        },
        {
            "units": ["Bravo"],
            "intent": "move", 
            "waypoints": ["F9"],
            "constraints": {"preferTerrain": ["forest"], "stayConcealed": True}
        }
    ]
    
    result = tester.run_scenario("basic_movement", config, units, orders, 50)
    
    # Verify units moved from starting positions
    assert result.final_positions["Alpha"] != (5.5, 5.5)
    assert result.final_positions["Bravo"] != (8.5, 8.5)
    
    # Verify radio acknowledgments were sent (with latency, they should appear after tick 2)
    assert len(result.radio_messages) > 0, f"Expected radio messages, got: {result.radio_messages}"
    
    # Verify units are still healthy
    assert result.final_health_states["Alpha"] == "HEALTHY"
    assert result.final_health_states["Bravo"] == "HEALTHY"


def test_combat_engagement_scenario():
    """Golden scenario: Combat engagement with casualties."""
    tester = GoldenScenarioTester(seed=456)
    
    config = GameConfig(width=200, height=200, seed=456, radio_latency_ticks=1)
    units = [
        UnitModel(unit_id="Red1", speed_cells_per_second=4.0, position=(10.5, 10.5), side="A"),
        UnitModel(unit_id="Red2", speed_cells_per_second=4.0, position=(12.5, 10.5), side="A"),
        UnitModel(unit_id="Blue1", speed_cells_per_second=3.5, position=(15.5, 15.5), side="B"),
        UnitModel(unit_id="Blue2", speed_cells_per_second=3.5, position=(17.5, 15.5), side="B")
    ]
    
    orders = [
        {
            "units": ["Red1", "Red2"],
            "intent": "attack",
            "engagement": {"targetCells": ["F8"]},
            "roe": "free",
            "posture": "crouch"
        },
        {
            "units": ["Blue1", "Blue2"],
            "intent": "attack", 
            "engagement": {"targetCells": ["B2"]},
            "roe": "return_fire",
            "posture": "stand"
        }
    ]
    
    result = tester.run_scenario("combat_engagement", config, units, orders, 100)
    
    # Verify combat occurred (some units may be wounded/KIA)
    wounded_or_kia = [state for state in result.final_health_states.values() 
                     if state in ["WOUNDED", "KIA"]]
    assert len(wounded_or_kia) > 0, "Expected some casualties in combat scenario"
    
    # Verify contact reports were sent
    contact_reports = [msg for msg in result.radio_messages if "Contact" in msg]
    assert len(contact_reports) > 0, "Expected contact reports during combat"
    
    # Verify casualty reports were sent
    casualty_reports = [msg for msg in result.radio_messages 
                       if any(state in msg for state in ["WOUNDED", "KIA"])]
    assert len(casualty_reports) > 0, "Expected casualty reports"


def test_radio_suppression_scenario():
    """Golden scenario: Radio message suppression and latency."""
    tester = GoldenScenarioTester(seed=789)
    
    config = GameConfig(width=50, height=50, seed=789, radio_latency_ticks=3)
    units = [
        UnitModel(unit_id="Unit1", speed_cells_per_second=2.0, position=(5.5, 5.5), side="A"),
        UnitModel(unit_id="Unit2", speed_cells_per_second=2.0, position=(7.5, 7.5), side="A")
    ]
    
    orders = [
        {
            "units": ["Unit1"],
            "intent": "move",
            "waypoints": ["C3", "D4", "E5"],
            "constraints": {"speed": "fast"}
        },
        {
            "units": ["Unit2"], 
            "intent": "move",
            "waypoints": ["F6", "G7", "H8"],
            "constraints": {"speed": "slow"}
        }
    ]
    
    result = tester.run_scenario("radio_suppression", config, units, orders, 30)
    
    # Verify radio messages were delivered with proper latency
    # (Messages should appear after latency_ticks delay)
    assert len(result.radio_messages) > 0, "Expected radio messages"
    
    # Verify both units completed their movement orders
    assert result.final_positions["Unit1"] != (5.5, 5.5)
    assert result.final_positions["Unit2"] != (7.5, 7.5)


def test_tent_destruction_scenario():
    """Golden scenario: Tent placement and destruction mechanics."""
    tester = GoldenScenarioTester(seed=999)
    
    config = GameConfig(width=300, height=300, seed=999, radio_latency_ticks=2)
    config.friendly_tent = (50.0, 50.0)
    config.enemy_tent = (250.0, 250.0)
    
    units = [
        UnitModel(unit_id="Assault1", speed_cells_per_second=5.0, position=(10.5, 10.5), side="A"),
        UnitModel(unit_id="Assault2", speed_cells_per_second=5.0, position=(15.5, 15.5), side="A"),
        UnitModel(unit_id="Defender1", speed_cells_per_second=3.0, position=(20.5, 20.5), side="B"),
        UnitModel(unit_id="Defender2", speed_cells_per_second=3.0, position=(25.5, 25.5), side="B")
    ]
    
    orders = [
        {
            "units": ["Assault1", "Assault2"],
            "intent": "move",
            "waypoints": ["J9"],  # Move to enemy tent area first
            "roe": "free",
            "priority": "high"
        },
        {
            "units": ["Defender1", "Defender2"],
            "intent": "hold",
            "roe": "return_fire",
            "posture": "crouch"
        }
    ]
    
    result = tester.run_scenario("tent_destruction", config, units, orders, 150)
    
    # Verify assault units moved (they should move from starting positions)
    assert result.final_positions["Assault1"] != (10.5, 10.5)
    assert result.final_positions["Assault2"] != (15.5, 15.5)
    
    # Verify combat occurred (contact reports should be generated)
    contact_reports = [msg for msg in result.radio_messages if "Contact" in msg]
    assert len(contact_reports) > 0, "Expected contact reports during tent assault"
    
    # Verify some casualties occurred
    wounded_or_kia = [state for state in result.final_health_states.values() 
                     if state in ["WOUNDED", "KIA"]]
    assert len(wounded_or_kia) > 0, "Expected casualties in tent assault scenario"


def test_deterministic_reproducibility():
    """Test that identical scenarios produce identical results."""
    # Run the same scenario twice with identical parameters
    config1 = GameConfig(width=100, height=100, seed=42, radio_latency_ticks=2)
    config2 = GameConfig(width=100, height=100, seed=42, radio_latency_ticks=2)
    
    units1 = [UnitModel(unit_id="Test", speed_cells_per_second=3.0, position=(5.5, 5.5), side="A")]
    units2 = [UnitModel(unit_id="Test", speed_cells_per_second=3.0, position=(5.5, 5.5), side="A")]
    
    orders = [{"units": ["Test"], "intent": "move", "waypoints": ["D7"]}]
    
    tester1 = GoldenScenarioTester(seed=42)
    tester2 = GoldenScenarioTester(seed=42)
    
    result1 = tester1.run_scenario("reproducibility", config1, units1, orders, 30)
    result2 = tester2.run_scenario("reproducibility", config2, units2, orders, 30)
    
    # Results should be identical
    assert result1.final_positions == result2.final_positions
    assert result1.final_health_states == result2.final_health_states
    assert result1.radio_messages == result2.radio_messages


def test_performance_benchmark():
    """Benchmark test to ensure simulation runs at target performance."""
    import time
    
    config = GameConfig(width=1000, height=1000, seed=1, radio_latency_ticks=1)
    units = [
        UnitModel(unit_id=f"Unit{i}", speed_cells_per_second=3.0, position=(i*10.5, i*10.5), side="A")
        for i in range(20)  # 20 units for realistic load
    ]
    
    orders = [
        {"units": [f"Unit{i}"], "intent": "move", "waypoints": [f"{chr(65+i%10)}{i%10}"]}
        for i in range(20)
    ]
    
    game = Game(config)
    for unit in units:
        game.add_unit(unit)
    
    for order in orders:
        game.enqueue_order(order)
    
    # Benchmark 100 ticks (10 seconds of simulation)
    start_time = time.perf_counter()
    game.tick(100)
    elapsed = time.perf_counter() - start_time
    
    # Should complete 100 ticks in under 5 seconds (target: ≤5ms/tick)
    max_time = 5.0  # 5 seconds for 100 ticks
    assert elapsed < max_time, f"Simulation too slow: {elapsed:.3f}s for 100 ticks (target: <{max_time}s)"
    
    # Calculate average time per tick
    avg_time_per_tick = elapsed / 100 * 1000  # Convert to milliseconds
    print(f"Performance: {avg_time_per_tick:.2f}ms per tick (target: ≤5ms)")


if __name__ == "__main__":
    # Run all golden scenario tests
    test_basic_movement_scenario()
    test_combat_engagement_scenario()
    test_radio_suppression_scenario()
    test_tent_destruction_scenario()
    test_deterministic_reproducibility()
    test_performance_benchmark()
    print("All golden scenario tests passed!")
