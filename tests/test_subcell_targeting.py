"""
Test subcell targeting functionality.

This test verifies that commands can target specific subcells within command cells,
not just the command cell centers.
"""

from server.game.engine import Game, GameConfig
from unit.unit import UnitModel


def test_subcell_targeting():
    """Test that units can be targeted to specific subcells within command cells."""
    config = GameConfig(width=1000, height=1000, seed=42, radio_latency_ticks=1)
    game = Game(config)
    
    # Add a test unit with higher speed
    game.add_unit(UnitModel(
        unit_id="TestUnit",
        speed_cells_per_second=50.0,  # Much faster for testing
        position=(10.5, 10.5),
        side="A"
    ))
    
    # Test traditional command cell targeting
    traditional_order = {
        "units": ["TestUnit"],
        "intent": "move",
        "waypoints": ["D3"]
    }
    
    assert game.enqueue_order(traditional_order)
    game.tick(5)  # Let it process
    
    # Test subcell targeting
    subcell_order = {
        "units": ["TestUnit"],
        "intent": "move",
        "waypoints": [{
            "commandCell": "D3",
            "subcell": {"x": 25, "y": 75}  # Target 25% from left, 75% from top
        }]
    }
    
    assert game.enqueue_order(subcell_order)
    game.tick(100)  # Run more ticks to let unit reach target
    
    # Verify the unit moved
    final_pos = game.units["TestUnit"].position
    print(f"Final position after subcell targeting: {final_pos}")
    
    # The unit should be in command cell D3, closer to the specified subcell
    # D3 corresponds to column 3, row 3 in the command grid
    # With subcell (25, 75), it should be in the lower-left area of D3
    assert 300 <= final_pos[0] <= 400  # D3 x bounds
    assert 300 <= final_pos[1] <= 400  # D3 y bounds


def test_mixed_waypoint_types():
    """Test orders with both command cell and subcell waypoints."""
    config = GameConfig(width=1000, height=1000, seed=42, radio_latency_ticks=1)
    game = Game(config)
    
    game.add_unit(UnitModel(
        unit_id="MixedUnit",
        speed_cells_per_second=30.0,  # Faster for testing
        position=(5.5, 5.5),
        side="A"
    ))
    
    # Order with mixed waypoint types
    mixed_order = {
        "units": ["MixedUnit"],
        "intent": "move",
        "waypoints": [
            "B1",  # Traditional command cell
            {
                "commandCell": "C2",
                "subcell": {"x": 50, "y": 50}  # Center of C2
            },
            "D3"  # Back to traditional
        ]
    }
    
    assert game.enqueue_order(mixed_order)
    game.tick(200)  # Run more ticks to let unit reach final waypoint
    
    # Unit should have moved through the waypoints
    final_pos = game.units["MixedUnit"].position
    print(f"Final position after mixed waypoints: {final_pos}")
    
    # Should end up in D3
    assert 300 <= final_pos[0] <= 400
    assert 300 <= final_pos[1] <= 400


def test_subcell_validation():
    """Test that subcell coordinates are properly validated."""
    from schemas.validate import validate_order
    
    # Valid subcell order
    valid_order = {
        "units": ["TestUnit"],
        "intent": "move",
        "waypoints": [{
            "commandCell": "A0",
            "subcell": {"x": 0, "y": 0}
        }]
    }
    
    is_valid, error = validate_order(valid_order)
    assert is_valid, f"Valid subcell order rejected: {error}"
    
    # Invalid subcell coordinates
    invalid_order = {
        "units": ["TestUnit"],
        "intent": "move",
        "waypoints": [{
            "commandCell": "A0",
            "subcell": {"x": 150, "y": 50}  # x > 100
        }]
    }
    
    is_valid, error = validate_order(invalid_order)
    assert not is_valid, "Invalid subcell order should be rejected"
    
    # Missing required fields
    incomplete_order = {
        "units": ["TestUnit"],
        "intent": "move",
        "waypoints": [{
            "commandCell": "A0",
            "subcell": {"x": 50}  # Missing y
        }]
    }
    
    is_valid, error = validate_order(incomplete_order)
    assert not is_valid, "Incomplete subcell order should be rejected"


if __name__ == "__main__":
    test_subcell_targeting()
    test_mixed_waypoint_types()
    test_subcell_validation()
    print("All subcell targeting tests passed!")
