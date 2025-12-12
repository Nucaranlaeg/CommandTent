from client.ui.map_view import MapView, UIConfig
from client.ui.command_panel import CommandPanel, StatusPanel
from client.audio.stt import STTEngine, STTConfig, VoiceUX
from server.orders.llm_parser import LLMCommandParser
from map.map import Map
from map.generator import generate
from unit.unit import UnitModel


def test_map_view_creation():
    """Test MapView can be created."""
    config = UIConfig()
    game_map = Map(100, 100, 42)
    map_view = MapView(config, game_map)
    
    assert map_view.config == config
    assert map_view.game_map == game_map
    assert map_view.screen is None
    assert not map_view.running


def test_command_panel_creation():
    """Test CommandPanel can be created."""
    stt_config = STTConfig()
    stt_engine = STTEngine(stt_config, lambda text: None)
    parser = LLMCommandParser()
    voice_ux = VoiceUX(stt_engine, parser, None)
    
    panel = CommandPanel(0, 0, 400, 300, voice_ux)
    
    assert panel.rect.width == 400
    assert panel.rect.height == 300
    assert panel.voice_ux == voice_ux


def test_status_panel_creation():
    """Test StatusPanel can be created."""
    panel = StatusPanel(0, 0, 400, 300)
    
    assert panel.rect.width == 400
    assert panel.rect.height == 300
    assert len(panel.radio_messages) == 0


def test_status_panel_add_message():
    """Test adding radio messages to status panel."""
    panel = StatusPanel(0, 0, 400, 300)
    
    panel.add_radio_message("Red reporting position A3")
    assert len(panel.radio_messages) == 1
    assert panel.radio_messages[0] == "Red reporting position A3"
    
    # Test max messages limit
    for i in range(20):
        panel.add_radio_message(f"Message {i}")
    
    assert len(panel.radio_messages) == panel.max_messages


def test_coordinate_conversion():
    """Test world/screen coordinate conversion."""
    config = UIConfig(cell_size=60)
    game_map = Map(100, 100, 42)
    map_view = MapView(config, game_map)
    
    # Test world to screen
    screen_pos = map_view.world_to_screen((10.5, 15.5))
    expected_x = int(10.5 * 60)
    expected_y = int(15.5 * 60)
    assert screen_pos == (expected_x, expected_y)
    
    # Test screen to world
    world_pos = map_view.screen_to_world((300, 450))
    expected_world_x = 300 / 60
    expected_world_y = 450 / 60
    assert world_pos == (expected_world_x, expected_world_y)


def test_unit_icon_management():
    """Test unit icon management."""
    config = UIConfig()
    game_map = Map(100, 100, 42)
    map_view = MapView(config, game_map)
    
    # Create test units
    units = {
        "Red": UnitModel("Red", 5.0, (10.5, 10.5), "Red", "A"),
        "Blue": UnitModel("Blue", 4.0, (15.5, 15.5), "Blue", "A")
    }
    
    # Update units
    map_view.update_units(units)
    assert len(map_view.unit_icons) == 2
    assert "Red" in map_view.unit_icons
    assert "Blue" in map_view.unit_icons


def test_mouse_interaction():
    """Test mouse interaction with units."""
    config = UIConfig()
    game_map = Map(100, 100, 42)
    map_view = MapView(config, game_map)
    
    # Add a unit
    units = {
        "Red": UnitModel("Red", 5.0, (10.5, 10.5), "Red", "A")
    }
    map_view.update_units(units)
    
    # Test clicking on unit
    unit_screen_pos = map_view.world_to_screen((10.5, 10.5))
    clicked_unit = map_view.handle_mouse_click(unit_screen_pos)
    assert clicked_unit == "Red"
    
    # Test clicking away from unit
    empty_pos = (0, 0)
    clicked_unit = map_view.handle_mouse_click(empty_pos)
    assert clicked_unit is None
