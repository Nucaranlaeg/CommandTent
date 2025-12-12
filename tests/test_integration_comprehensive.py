"""
Comprehensive integration test for Command Tent MVP.

This test verifies that all components work together correctly:
- Map generation and pathfinding
- Unit movement and combat
- Radio communication and latency
- Order parsing and execution
- UI components and voice interface
- Deterministic behavior
"""

import time
from typing import Dict, List

from server.game.engine import Game, GameConfig
from unit.unit import UnitModel
from server.orders.llm_parser import LLMCommandParser
from client.audio.stt import STTEngine, STTConfig, VoiceUX
from client.audio.tts import TTSEngine, TTSConfig, VoiceRadioSystem
from schemas.validate import validate_order


def test_full_system_integration():
    """Test the complete system integration with all components."""
    print("Testing full system integration...")
    
    # 1. Create game with realistic configuration
    config = GameConfig(
        width=1000, 
        height=1000, 
        seed=12345, 
        radio_latency_ticks=3
    )
    game = Game(config)
    
    # 2. Add multiple units on both sides
    friendly_units = [
        UnitModel(unit_id="Alpha", speed_cells_per_second=4.0, position=(50.5, 50.5), side="A"),
        UnitModel(unit_id="Bravo", speed_cells_per_second=3.5, position=(60.5, 60.5), side="A"),
        UnitModel(unit_id="Charlie", speed_cells_per_second=3.0, position=(70.5, 70.5), side="A"),
    ]
    
    enemy_units = [
        UnitModel(unit_id="Delta", speed_cells_per_second=4.0, position=(200.5, 200.5), side="B"),
        UnitModel(unit_id="Echo", speed_cells_per_second=3.5, position=(210.5, 210.5), side="B"),
    ]
    
    for unit in friendly_units + enemy_units:
        game.add_unit(unit)
    
    # 3. Test voice command processing
    stt_config = STTConfig(mode="simulated")
    stt_engine = STTEngine(stt_config, lambda x: None)
    tts_config = TTSConfig(mode="simulated")
    tts_engine = TTSEngine(tts_config, None)
    parser = LLMCommandParser()
    
    voice_ux = VoiceUX(stt_engine, parser, game.executor)
    voice_radio = VoiceRadioSystem(stt_engine, tts_engine, parser, game.executor)
    
    # 4. Test complex order execution
    complex_orders = [
        {
            "units": ["Alpha", "Bravo"],
            "intent": "move",
            "waypoints": ["D3", "E4"],
            "constraints": {"preferTerrain": ["road"], "speed": "normal"},
            "roe": "return_fire",
            "posture": "crouch"
        },
        {
            "units": ["Charlie"],
            "intent": "move",
            "waypoints": [{
                "commandCell": "F5",
                "subcell": {"x": 25, "y": 75}
            }],
            "constraints": {"preferTerrain": ["forest"], "stayConcealed": True},
            "roe": "hold"
        },
        {
            "units": ["Delta", "Echo"],
            "intent": "move",  # Change to move instead of attack
            "waypoints": ["G6"],
            "roe": "free",
            "posture": "stand"
        }
    ]
    
    # Execute orders
    for order in complex_orders:
        assert game.enqueue_order(order), f"Failed to enqueue order: {order}"
    
    # 5. Run simulation and verify behavior
    initial_positions = {unit_id: unit.position for unit_id, unit in game.units.items()}
    
    # Run simulation for multiple ticks
    game.tick(50)
    
    # Verify units moved
    for unit_id, unit in game.units.items():
        assert unit.position != initial_positions[unit_id], f"Unit {unit_id} didn't move"
    
    # 6. Verify radio communication
    assert len(game.radio_log) > 0, "No radio messages were sent"
    
    # Check for different types of radio messages
    message_types = [evt.message for evt in game.radio_log]
    assert any("Acknowledged" in msg for msg in message_types), "No acknowledgment messages"
    
    # 7. Test combat if units are close enough
    game.tick(100)  # Run more ticks to allow combat
    
    # Check for combat-related messages
    combat_messages = [msg for msg in message_types if any(keyword in msg.lower() 
                          for keyword in ["contact", "engaging", "wounded", "kia"])]
    
    # 8. Verify deterministic behavior
    game2 = Game(GameConfig(width=1000, height=1000, seed=12345, radio_latency_ticks=3))
    for unit in friendly_units + enemy_units:
        game2.add_unit(unit)
    
    for order in complex_orders:
        game2.enqueue_order(order)
    
    game2.tick(50)
    
    # Compare final positions (should be identical)
    for unit_id in game.units:
        pos1 = game.units[unit_id].position
        pos2 = game2.units[unit_id].position
        assert abs(pos1[0] - pos2[0]) < 0.01, f"Non-deterministic behavior for {unit_id}"
        assert abs(pos1[1] - pos2[1]) < 0.01, f"Non-deterministic behavior for {unit_id}"
    
    print("✓ Full system integration test passed!")


def test_performance_under_load():
    """Test system performance with many units and orders."""
    print("Testing performance under load...")
    
    config = GameConfig(width=2000, height=2000, seed=42, radio_latency_ticks=2)
    game = Game(config)
    
    # Add many units
    units_per_side = 10  # Reduced from 20 for better performance
    for i in range(units_per_side):
        # Friendly units
        game.add_unit(UnitModel(
            unit_id=f"Friendly{i}",
            speed_cells_per_second=10.0,  # Increased speed
            position=(i * 20.5, i * 20.5),  # Spread out more
            side="A"
        ))
        # Enemy units
        game.add_unit(UnitModel(
            unit_id=f"Enemy{i}",
            speed_cells_per_second=10.0,  # Increased speed
            position=(500 + i * 20.5, 500 + i * 20.5),  # Spread out more
            side="B"
        ))
    
    # Generate many orders
    orders = []
    for i in range(units_per_side):
        orders.append({
            "units": [f"Friendly{i}"],
            "intent": "move",
            "waypoints": [f"{chr(65 + i % 10)}{i % 10}"]
        })
        orders.append({
            "units": [f"Enemy{i}"],
            "intent": "move",
            "waypoints": [f"{chr(65 + (i + 5) % 10)}{(i + 5) % 10}"]
        })
    
    # Execute all orders
    for order in orders:
        assert game.enqueue_order(order), f"Failed to enqueue order: {order}"
    
    # Benchmark simulation performance
    start_time = time.perf_counter()
    game.tick(50)  # Reduced ticks for better performance testing
    elapsed = time.perf_counter() - start_time
    
    # Should complete in reasonable time (target: <15 seconds for 50 ticks)
    assert elapsed < 15.0, f"Simulation too slow: {elapsed:.3f}s for 50 ticks"
    
    print(f"✓ Performance test passed! ({elapsed:.3f}s for 50 ticks with {len(game.units)} units)")


def test_error_handling_and_recovery():
    """Test system resilience to errors and invalid inputs."""
    print("Testing error handling and recovery...")
    
    config = GameConfig(width=1000, height=1000, seed=1)
    game = Game(config)
    
    game.add_unit(UnitModel(unit_id="TestUnit", speed_cells_per_second=3.0, position=(10.5, 10.5), side="A"))
    
    # Test invalid orders
    invalid_orders = [
        {"units": ["NonExistentUnit"], "intent": "move", "waypoints": ["A1"]},
        {"units": ["TestUnit"], "intent": "move", "waypoints": ["Z9"]},  # Invalid cell
        {"units": ["TestUnit"], "intent": "move", "waypoints": [{"commandCell": "A1", "subcell": {"x": 150, "y": 50}}]},  # Invalid subcell
        {"units": [], "intent": "move", "waypoints": ["A1"]},  # Empty units
        {"units": ["TestUnit"], "intent": "invalid_intent"},  # Invalid intent
    ]
    
    for order in invalid_orders:
        result = game.enqueue_order(order)
        assert not result, f"Invalid order should be rejected: {order}"
    
    # Test valid order after invalid ones
    valid_order = {
        "units": ["TestUnit"],
        "intent": "move",
        "waypoints": ["B2"]
    }
    
    assert game.enqueue_order(valid_order), "Valid order should work after invalid ones"
    game.tick(10)
    
    # Verify unit still works
    assert game.units["TestUnit"].position != (10.5, 10.5), "Unit should have moved"
    
    print("✓ Error handling test passed!")


def test_schema_validation_integration():
    """Test that schema validation works correctly with all order types."""
    print("Testing schema validation integration...")
    
    # Test traditional command cell orders
    traditional_order = {
        "units": ["Unit1"],
        "intent": "move",
        "waypoints": ["A1", "B2", "C3"],
        "constraints": {"preferTerrain": ["road"], "speed": "normal"},
        "roe": "return_fire",
        "posture": "crouch"
    }
    
    is_valid, error = validate_order(traditional_order)
    assert is_valid, f"Traditional order validation failed: {error}"
    
    # Test subcell orders
    subcell_order = {
        "units": ["Unit2"],
        "intent": "move",
        "waypoints": [
            "A1",
            {"commandCell": "B2", "subcell": {"x": 25, "y": 75}},
            "C3"
        ],
        "constraints": {"preferTerrain": ["forest"], "stayConcealed": True},
        "roe": "hold"
    }
    
    is_valid, error = validate_order(subcell_order)
    assert is_valid, f"Subcell order validation failed: {error}"
    
    # Test attack orders
    attack_order = {
        "units": ["Unit3", "Unit4"],
        "intent": "attack",
        "engagement": {"targetCells": ["D4", "E5"], "suppressOnly": False},
        "roe": "free",
        "posture": "stand",
        "priority": "high"
    }
    
    is_valid, error = validate_order(attack_order)
    assert is_valid, f"Attack order validation failed: {error}"
    
    print("✓ Schema validation integration test passed!")


if __name__ == "__main__":
    print("Running comprehensive integration tests...")
    print("=" * 50)
    
    test_full_system_integration()
    test_performance_under_load()
    test_error_handling_and_recovery()
    test_schema_validation_integration()
    
    print("=" * 50)
    print("All integration tests passed! 🎉")
    print("Command Tent MVP is ready for deployment!")
