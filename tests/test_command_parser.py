from server.orders.parser import CommandParser
from schemas.validate import validate_order


def test_parser_basic_movement():
    parser = CommandParser()
    success, order, msg = parser.parse("Red move to A3")
    
    assert success
    assert order["units"] == ["Red"]
    assert order["intent"] == "move"
    assert order["waypoints"] == ["A3"]
    assert order["roe"] == "return_fire"
    assert order["posture"] == "stand"


def test_parser_complex_command():
    parser = CommandParser()
    success, order, msg = parser.parse("Blue advance to D5 via roads, weapons tight, stay concealed")
    
    assert success
    assert order["units"] == ["Blue"]
    assert order["intent"] == "move"
    assert order["waypoints"] == ["D5"]
    assert order["constraints"]["preferTerrain"] == ["road"]
    assert order["constraints"]["stayConcealed"] == True
    assert order["roe"] == "hold"


def test_parser_multiple_units_and_waypoints():
    parser = CommandParser()
    success, order, msg = parser.parse("Red and Blue move to A3 then B4")
    
    assert success
    assert "Red" in order["units"] and "Blue" in order["units"]
    assert order["waypoints"] == ["A3", "B4"]


def test_parser_non_movement_intents():
    parser = CommandParser()
    
    # Hold command
    success, order, msg = parser.parse("Red hold position")
    assert success
    assert order["intent"] == "hold"
    
    # Attack command
    success, order, msg = parser.parse("Blue attack enemy")
    assert success
    assert order["intent"] == "attack"


def test_parser_disambiguation_failure():
    parser = CommandParser()
    
    # No valid units
    success, order, msg = parser.parse("move to A3")
    assert not success
    assert "No valid units found" in msg
    
    # No valid command
    success, order, msg = parser.parse("Red do something")
    assert not success
    assert "No valid command found" in msg


def test_parser_validates_output():
    parser = CommandParser()
    success, order, msg = parser.parse("Red move to A3")
    
    assert success
    # Ensure the output validates against our schema
    valid, schema_msg = validate_order(order)
    assert valid, f"Schema validation failed: {schema_msg}"
