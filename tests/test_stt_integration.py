from client.audio.stt import STTEngine, STTConfig, STTMode, VoiceUX
from server.orders.llm_parser import LLMCommandParser
from server.orders.executor import OrderExecutor
from server.game.engine import Game, GameConfig
from server.sim.loop import Simulation
from unit.unit import UnitModel


def test_stt_engine_creation():
    config = STTConfig(mode=STTMode.PTT, vad_threshold=0.7)
    transcript_callback = lambda text: None
    engine = STTEngine(config, transcript_callback)
    
    assert engine.config.mode == STTMode.PTT
    assert engine.config.vad_threshold == 0.7
    assert not engine.is_listening


def test_voice_ux_integration():
    # Create a minimal game setup
    game = Game(GameConfig(width=100, height=100, seed=1))
    game.add_unit(UnitModel(unit_id="Red", speed_cells_per_second=5.0, position=(10.5, 10.5), fireteam_name="Red"))
    
    # Create STT and voice UX
    config = STTConfig(mode=STTMode.PTT)
    engine = STTEngine(config, lambda text: None)
    parser = LLMCommandParser()
    voice_ux = VoiceUX(engine, parser, game.executor)
    
    # Test command processing
    voice_ux.process_transcript("Red move to A3")
    
    # Check command history
    history = voice_ux.get_recent_commands(1)
    assert len(history) == 1
    assert history[0]["transcript"] == "Red move to A3"
    assert history[0]["order"] is not None
    assert history[0]["status"] in ["executed", "failed"]


def test_voice_ux_command_history():
    config = STTConfig(mode=STTMode.VAD)
    engine = STTEngine(config, lambda text: None)
    parser = LLMCommandParser()
    voice_ux = VoiceUX(engine, parser, None)  # No executor for this test
    
    # Process multiple commands
    voice_ux.process_transcript("Red move to A3")
    voice_ux.process_transcript("Blue hold position")
    voice_ux.process_transcript("invalid command")
    
    history = voice_ux.get_recent_commands(3)
    assert len(history) == 3
    assert history[0]["transcript"] == "Red move to A3"
    assert history[1]["transcript"] == "Blue hold position"
    assert history[2]["transcript"] == "invalid command"
    assert history[2]["status"] == "parse_failed"


def test_stt_simulation():
    """Test STT simulation for development/testing."""
    config = STTConfig(mode=STTMode.PTT)
    transcripts = []
    
    def capture_transcript(text):
        transcripts.append(text)
    
    engine = STTEngine(config, capture_transcript)
    engine.start_listening()
    
    # Simulate voice input
    engine.simulate_voice_input("Red move to A3")
    engine.simulate_voice_input("Blue hold fire")
    
    engine.stop_listening()
    
    assert len(transcripts) == 2
    assert "Red move to A3" in transcripts
    assert "Blue hold fire" in transcripts


def test_voice_ux_start_stop():
    config = STTConfig(mode=STTMode.PTT)
    engine = STTEngine(config, lambda text: None)
    voice_ux = VoiceUX(engine, LLMCommandParser(), None)
    
    assert not voice_ux.is_active
    
    voice_ux.start()
    assert voice_ux.is_active
    
    voice_ux.stop()
    assert not voice_ux.is_active
