# Game Design doc

## Overview

Command Tent is a voice-first tactics game. Players command WWII-era infantry by speaking naturally; units respond over radio, simulating a commander receiving updates from the field. The UI is minimal and non-authoritative; the simulation is server-authoritative.

Unit command understanding is LLM-assisted: player speech is transcribed and mapped to a constrained, structured order format that drives deterministic in-engine behaviors.

## Win Condition and Setup

- Each side has a command tent. If a hostile unit capable of firing engages the tent, it has a high chance to immediately destroy it. No hit points are tracked or displayed for tents.
- Before a match begins, each player places their command tent on the map via the GUI, subject to placement rules (within own deployment zone, minimum distance from map edges and objectives).
- Friendly fire is disabled.

## Information Model (Radio-Only Awareness)

- There is no visual indication of actual unit positions on the primary UI. The map shows terrain and player-maintained markers/icons only.
- Situational awareness flows via radio. All unit-to-player and unit-to-unit coordination occurs over the radio network with modeled latency; unit-to-unit comms do not need to be audibly rendered to the player but incur timing effects.
- A separate debug UI can reveal ground-truth positions, LOS, and state for development and testing.

### Radio Latency

- Fixed MVP radio latency (e.g., 300–800 ms) applied to acknowledgements, contact reports, and unit-to-unit relays.
- Later: vary by distance, interference, or net congestion.

### Radio Report Triggers (MVP)

Units may proactively report over radio when:

- Addressed by the player (acknowledgement, readback of parsed order).
- Answering direct queries (e.g., "Status?", "Location?", "Ammo?" if modeled).
- A nearby friendly becomes Wounded or KIA.
- Enemy contact is made (first sight/first fire) or contact is lost.
- An engaged enemy is neutralized or retreats ("enemy down" / "no movement").
- Reaching waypoints, beginning/ending actions (move complete, setting up, observing).
- Unable to comply (blocked path, denied by ROE/constraints, out of range).

Spam suppression rules collapse similar events within a short window.

## Map and Terrain

- Command Grid: Orders use a coarse reference grid A–J × 0–9 for clarity in voice commands.
- Simulation Grid: The underlying map is more granular (e.g., 100×100 subcells). Terrain features (forests, roads, buildings) can partially occupy a command cell; a unit inside a command cell may or may not be within that feature depending on its subcell position.
- Terrain Types (MVP): road, open, forest, building, water (impassable), hill (optional for elevation later).
- Movement Cost: per-terrain multipliers; roads are faster even if path is longer.
- Concealment/Cover: terrain confers concealment (spotting difficulty) and cover (hit reduction).
- LOS: MVP uses binary LOS without elevation; terrain may block LOS.
- Spawn/Placement: players place command tents pre-match; unit spawns are auto-placed within the deployment zone.

## UI Components

- Minimal 2D map with terrain shading and command grid labels.
- Player-managed unit/enemy icons are draggable for personal tracking; these are non-authoritative and purely for the player's bookkeeping.
- Voice Input: push-to-talk or VAD; transcript/parsed command panel with confirmations.
- Command History: list of issued orders, statuses, and outcomes; undo/cancel last order.
- Debug UI (dev only): true positions, paths, LOS, state machines, and logs.
- Text chat between opponents.

## Units

- Roster: Each player controls 20 soldiers, default organized into 5 fireteams of 4. Fireteam names default to "Red", "Blue", "Green", "Gold", "Brown". Individual soldiers use NATO alphabet names (Alpha, Bravo, Charlie, ...).
- Archetypes (configurable): Rifleman (baseline), Heavy Weapons (2), Sniper (1).
- Attributes:
  - Health State: Healthy, Wounded, KIA (no finer granularity). Wounded units may have reduced performance; KIA are removed from play.
  - Movement: base speed with terrain/posture multipliers.
  - Weapons: effective range bands, accuracy curve, rate of fire, reload time (ammo may be abstracted in MVP).
  - Sensing: sight range, spotting difficulty; concealment reduces detection probability.
  - Posture: stand, crouch, prone; posture affects speed, concealment, and accuracy.
- Formation (MVP-simple): fireteam cohesion radius around a leader; no complex formations initially.

## Gameplay and Orders

- Players issue voice commands using natural language. Example: "Red, move to B6 via roads. Weapons tight. Stay in the forest if possible."
- The system transcribes speech and maps it into a structured order. Units then execute deterministically.
- Rules of Engagement: hold fire, return fire, fire at will.
- Movement Behavior: path prefers roads if requested; can honor constraints like "avoid C column" or "stay concealed" when possible.
- Engagement: units do not fire on friendlies (friendly fire disabled). ROE gates firing behavior.
- Victory: destroy the enemy command tent (binary resolution on effective fire).

### Structured Command Schema (MVP)

```json
{
  "units": ["Red"],
  "intent": "move",
  "waypoints": ["A3"],
  "constraints": {
    "preferTerrain": ["road", "forest"],
    "avoidCells": ["C3", "C4"],
    "stayConcealed": true,
    "speed": "normal"
  },
  "roe": "return_fire",
  "posture": "crouch",
  "engagement": {
    "targetCells": ["B6"],
    "suppressOnly": false
  },
  "priority": "normal",
  "ack": true
}
```

## Simulation Model

- Tick Rate: 10 Hz deterministic tick.
- Pathfinding: A\* over subcells with terrain costs; optional diagonal with corner-cut avoidance.
- Detection: sight range vs concealment, LOS blocking; posture and movement modify spotting and being spotted.
- Fire Resolution: accuracy by range band and posture; cover reduces hit chance; outcomes map to Healthy/Wounded/KIA.
- Suppression/Morale: simple suppression reducing accuracy and movement (optional later; keep minimal for MVP).
- Order Latency: radio latency applied to acknowledgements and some coordination behaviors.

## NLP and AI Layer

- Pipeline: Speech-to-text → intent/entity extraction (LLM constrained to schema) → validation → order issuance.
- Disambiguation: If multiple interpretations exist (e.g., "move to the forest near B6" with two candidates), request a clarification via radio with latency.
- Safety: LLM is advisory; the engine validates orders against map, units, and ROE.

## Networking and Architecture (MVP)

- Server-authoritative simulation. Client handles voice input, UI, and receives state snapshots.
- Local 1v1 for MVP (single process or localhost client/server). Later: lobbies and netcode.

## Content and Configuration

- Data-driven JSON/YAML: unit archetypes, terrain weights, ROE enums, command synonyms.
- Map generation is seeded and reproducible; seeds embedded in match records.

## Testing and Telemetry

- Headless deterministic runs with fixed seeds and scripted orders for regression.
- Event logs for radio reports, contacts, and KIA/Wounded.

## MVP Scope Checklist

- Coarse command grid A–J × 0–9; finer simulation grid underneath.
- 1v1 local match; pre-match command tent placement.
- 20 units/player (riflemen + 2 heavy + 1 sniper archetypes).
- Binary tent destruction upon effective hostile fire; no tent HP.
- No visual unit positions on main UI; radio-only awareness with latency.
- Radio report triggers as listed; spam suppression.
- ROE: hold fire / return fire / fire at will; no friendly fire.
- LOS without elevation; concealment and simple cover.
- Voice → structured orders → deterministic behaviors.
- Minimal map UI, command history, text chat; optional debug UI.
