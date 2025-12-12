from server.orders.llm_parser import LLMCommandParser
from schemas.validate import validate_order


def test_complex_terrain_waypoint_association():
    parser = LLMCommandParser()
    
    # Test the complex case you mentioned
    success, order, msg = parser.parse("Red move to A3 via forest in A4")
    
    assert success
    assert order["units"] == ["Red"]
    assert order["intent"] == "move"
    assert "A3" in order["waypoints"]
    assert "A4" in order["waypoints"]
    assert "forest" in order["constraints"]["preferTerrain"]


def test_multiple_units_with_conjunctions():
    parser = LLMCommandParser()
    
    # Test various conjunction formats
    test_cases = [
        "Red and Blue move to A3",
        "Alpha, Bravo advance to B4",
        "Red or Blue hold position"
    ]
    
    for text in test_cases:
        success, order, msg = parser.parse(text)
        assert success
        assert len(order["units"]) >= 1


def test_sequence_indicators():
    parser = LLMCommandParser()
    
    # Test sequence indicators
    success, order, msg = parser.parse("Red move through A3 then B4")
    assert success
    assert order["waypoints"] == ["A3", "B4"]
    
    success, order, msg = parser.parse("Blue advance to A3, next B4")
    assert success
    assert "A3" in order["waypoints"] and "B4" in order["waypoints"]


def test_enhanced_roe_and_posture():
    parser = LLMCommandParser()
    
    # Test enhanced ROE phrases
    success, order, msg = parser.parse("Red hold fire and go prone")
    assert success
    assert order["roe"] == "hold"
    assert order["posture"] == "prone"
    
    success, order, msg = parser.parse("Blue weapons free, crouch down")
    assert success
    assert order["roe"] == "free"
    assert order["posture"] == "crouch"


def test_complex_constraints():
    parser = LLMCommandParser()
    
    success, order, msg = parser.parse("Red move to A3 via roads, stay concealed, go slow")
    assert success
    assert "road" in order["constraints"]["preferTerrain"]
    assert order["constraints"]["stayConcealed"] == True
    assert order["constraints"]["speed"] == "slow"


def test_llm_parser_validates_output():
    parser = LLMCommandParser()
    success, order, msg = parser.parse("Red and Blue move to A3 via forest")
    
    assert success
    # Ensure the output validates against our schema
    valid, schema_msg = validate_order(order)
    assert valid, f"Schema validation failed: {schema_msg}"


def test_fallback_to_enhanced_rules():
    """Test that the parser falls back to enhanced rules when no LLM is available."""
    parser = LLMCommandParser(llm_client=None)  # No LLM client
    success, order, msg = parser.parse("Red move to A3")
    
    assert success
    assert order["units"] == ["Red"]
    assert order["intent"] == "move"
    assert order["waypoints"] == ["A3"]
