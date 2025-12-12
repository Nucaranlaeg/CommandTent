# Command Tent

A voice-controlled military simulation game where players command WWII infantry units through natural language voice commands.

## Features

- **Voice Control**: All commands issued through speech-to-text
- **Unit AI**: Units respond with natural language via text-to-speech
- **Minimal UI**: Clean map view with command grid and unit icons
- **Real-time Simulation**: 10Hz server-authoritative game loop
- **Procedural Maps**: Generated terrain with roads, forests, and obstacles
- **Radio Communication**: Units report status, contacts, and casualties

## Quick Start

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Demo**:

   ```bash
   python demo_ui.py
   ```

3. **Controls**:
   - **SPACE**: Toggle Push-to-Talk voice interface
   - **Mouse**: Click and drag unit icons
   - **ESC/Close**: Exit

## Game Design

- **Map**: 10x10 command grid (A-J, 0-9) with 1000x1000 subcell simulation
- **Units**: WWII infantry platoon (20 men) organized into fireteams
- **Objective**: Destroy enemy command tent
- **Voice Commands**: Natural language like "Red move to A3 via forest in A4"
- **Radio Reports**: Units acknowledge orders and report status

## Architecture

```
client/
├── audio/          # Speech-to-text and text-to-speech
├── ui/             # Pygame-based user interface
server/
├── game/           # Core game engine
├── orders/         # Command parsing and execution
├── radio/          # Communication system
├── sim/            # Simulation loop
map/                # Terrain generation and pathfinding
unit/               # Unit models and combat
schemas/            # Data validation
tests/              # Comprehensive test suite
```

## Development

Run tests:

```bash
python -m pytest
```

Run specific test categories:

```bash
python -m pytest tests/test_ui_components.py
python -m pytest tests/test_stt_integration.py
python -m pytest tests/test_tts_integration.py
```

## Voice Commands

Examples of supported commands:

- "Red move to A3"
- "Blue weapons free, crouch down"
- "Alpha move to B4 via forest in A4"
- "Red, move to A3 then B4"
- "All units hold position"

## Technical Details

- **Simulation**: 10Hz deterministic server loop
- **Pathfinding**: A\* algorithm with terrain costs
- **Voice**: Faster-Whisper STT + simulated TTS
- **UI**: Pygame with 60 FPS rendering
- **Testing**: 58+ unit tests with 100% core coverage
