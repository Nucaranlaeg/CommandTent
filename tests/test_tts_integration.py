from client.audio.tts import TTSConfig, TTSMode, TTSEngine, RadioResponseGenerator, VoiceRadioSystem
from client.audio.stt import STTEngine, STTConfig, VoiceUX
from server.orders.llm_parser import LLMCommandParser


def test_tts_engine_creation():
    config = TTSConfig(mode=TTSMode.SIMULATED, voice_rate=1.2)
    generator = RadioResponseGenerator()
    engine = TTSEngine(config, generator)
    
    assert engine.config.mode == TTSMode.SIMULATED
    assert engine.config.voice_rate == 1.2
    assert not engine.is_speaking


def test_response_generator():
    generator = RadioResponseGenerator()
    
    # Test acknowledgment
    response = generator.generate_acknowledgment("Red", "moving to A3")
    assert "Red" in response
    assert "moving to A3" in response or "acknowledging" in response
    
    # Test waypoint reached
    response = generator.generate_waypoint_reached("Blue", "A3")
    assert "Blue" in response
    assert "A3" in response or "waypoint" in response
    
    # Test contact report
    response = generator.generate_contact_report("Alpha", "B4")
    assert "Alpha" in response
    assert "B4" in response or "contact" in response


def test_tts_simulation():
    """Test TTS simulation mode."""
    config = TTSConfig(mode=TTSMode.SIMULATED, enabled=True)
    generator = RadioResponseGenerator()
    engine = TTSEngine(config, generator)
    
    # Capture output
    import io
    import sys
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        engine.speak("Red acknowledging. Moving to A3.")
    
    output = f.getvalue()
    assert "[TTS]" in output
    assert "Red acknowledging" in output


def test_voice_radio_system():
    """Test complete voice radio system."""
    stt_config = STTConfig()
    stt_engine = STTEngine(stt_config, lambda text: None)
    tts_config = TTSConfig(mode=TTSMode.SIMULATED)
    generator = RadioResponseGenerator()
    tts_engine = TTSEngine(tts_config, generator)
    parser = LLMCommandParser()
    
    voice_radio = VoiceRadioSystem(stt_engine, tts_engine, parser, None)
    
    # Test radio event processing
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        voice_radio.process_radio_event("acknowledgment", "Red", action="moving to A3")
    
    output = f.getvalue()
    assert "[TTS]" in output
    assert "Red" in output


def test_simulate_unit_responses():
    """Test simulating multiple unit responses."""
    stt_config = STTConfig()
    stt_engine = STTEngine(stt_config, lambda text: None)
    tts_config = TTSConfig(mode=TTSMode.SIMULATED)
    generator = RadioResponseGenerator()
    tts_engine = TTSEngine(tts_config, generator)
    parser = LLMCommandParser()
    
    voice_radio = VoiceRadioSystem(stt_engine, tts_engine, parser, None)
    
    # Simulate radio events
    events = [
        {"type": "acknowledgment", "unit": "Red", "data": {"action": "moving to A3"}},
        {"type": "waypoint_reached", "unit": "Blue", "data": {"location": "B4"}},
        {"type": "contact", "unit": "Alpha", "data": {"location": "C5"}}
    ]
    
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        voice_radio.simulate_unit_responses(events)
    
    output = f.getvalue()
    assert "[TTS]" in output
    assert "Red" in output
    assert "Blue" in output
    assert "Alpha" in output


def test_tts_disabled():
    """Test TTS when disabled."""
    config = TTSConfig(enabled=False)
    generator = RadioResponseGenerator()
    engine = TTSEngine(config, generator)
    
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        engine.speak("This should not be spoken")
    
    output = f.getvalue()
    assert output == ""  # No output when disabled
