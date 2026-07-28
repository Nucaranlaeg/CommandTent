"""Command parser tests use ``config/llm.yaml`` (see ``command_llm_parser`` in conftest)."""

from __future__ import annotations

from server.orders.llm_parser import LLMCommandParser
from schemas.validate import validate_order


def test_complex_terrain_waypoint_association(command_llm_parser):
    success, order, msg = command_llm_parser.parse("Red move to A3 via forest in A4")

    assert success, msg
    assert "Red" in order["units"]
    assert order["intent"] == "move"
    assert "A3" in order["waypoints"] and "A4" in order["waypoints"]
    assert order["waypoints"].index("A4") < order["waypoints"].index("A3")
    assert "forest" in order["constraints"]["preferTerrain"]


def test_multiple_units_with_conjunctions(command_llm_parser):
    success, order, _ = command_llm_parser.parse("Red and Blue move to A3")
    assert success
    assert set(order["units"]) == {"Red", "Blue"}

    success, order, _ = command_llm_parser.parse("Alpha, Bravo advance to B4")
    assert success
    assert set(order["units"]) == {"Alpha", "Bravo"}
    assert "B4" in order["waypoints"]

    success, order, _ = command_llm_parser.parse("Red or Blue hold position")
    assert success
    assert set(order["units"]) == {"Red", "Blue"}
    assert order["intent"] == "hold"
    assert "waypoints" not in order


def test_sequence_indicators(command_llm_parser):
    success, order, msg = command_llm_parser.parse("Red move through A3 then B4")
    assert success, msg
    assert order["waypoints"] == ["A3", "B4"]

    success, order, msg = command_llm_parser.parse("Blue advance to A3, next B4")
    assert success, msg
    assert "Blue" in order["units"]
    assert "A3" in order["waypoints"] and "B4" in order["waypoints"]


def test_enhanced_roe_and_posture(command_llm_parser):
    success, order, msg = command_llm_parser.parse("Red hold fire and go prone")
    assert success, msg
    assert order["roe"] == "hold"
    assert order["posture"] == "prone"

    success, order, msg = command_llm_parser.parse("Blue weapons free, crouch down")
    assert success, msg
    assert order["roe"] == "free"
    assert order["posture"] == "crouch"


def test_complex_constraints(command_llm_parser):
    success, order, msg = command_llm_parser.parse(
        "Red move to A3 via roads, stay concealed, go slow"
    )
    assert success, msg
    assert "road" in order["constraints"]["preferTerrain"]
    assert order["constraints"]["stayConcealed"] is True
    assert order["constraints"]["speed"] == "slow"


def test_llm_parser_validates_output(command_llm_parser):
    success, order, msg = command_llm_parser.parse("Red and Blue move to A3 via forest")

    assert success, msg
    valid, schema_msg = validate_order(order)
    assert valid, f"Schema validation failed: {schema_msg}"


def test_hold_output_validates_without_empty_waypoints(command_llm_parser):
    success, order, msg = command_llm_parser.parse("Red hold fire and go prone")
    assert success, msg
    assert "waypoints" not in order
    valid, schema_msg = validate_order(order)
    assert valid, schema_msg


def test_parse_failure_empty_transcript_never_calls_llm():
    """Blank input is rejected before inference (no GGUF required)."""

    class _Never:
        def complete(self, prompt: str) -> str:
            raise AssertionError("LLM must not run for empty transcript")

    parser = LLMCommandParser(llm_client=_Never())
    success, order, msg = parser.parse("")
    assert not success and order is None

    success, order, msg = parser.parse("   ")
    assert not success and order is None
