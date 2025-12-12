# Command Tent - MVP Task List

This breaks the MVP into concrete, verifiable tasks with acceptance criteria and dependencies.

## 1) Define data schemas: map, unit, order, visibility

- Output: `schemas/` with JSON/YAML and Python dataclasses/types for:
  - Map (command grid, subcell grid, terrain tiles, seed, metadata)
  - Unit (id, archetype, fireteam, subcell position, posture, state, health: Healthy/Wounded/KIA)
  - Order (structured command schema; ROE, constraints)
  - Visibility (per-side visible set, contact records)
- Acceptance:
  - Types import; schema JSON validates; round-trip (serialize/deserialize) works.
  - Unit tests cover schema validation and defaults.

## 2) Implement subcell map grid and A\* pathfinding with terrain costs

- Output: pathfinder over subcells (e.g., 100×100) with per-terrain movement multipliers; optional diagonals without corner-cut.
- Acceptance:
  - Deterministic paths for fixed seed/terrain.
  - Roads preferred when requested; impassables respected.
  - Unit tests for corridor, T-intersection, road vs open.
- Depends on: 1

## 3) Build procedural map generator with seeds and terrain placement

- Output: seeded generator for roads, forest, building, water; features can partially occupy command cells.
- Acceptance:
  - Stable output by seed; seed stored in match record.
  - Generated maps pass pathing sanity checks (connectivity across zones).
- Depends on: 2

## 4) Implement server-authoritative 10 Hz simulation loop

- Output: tick scheduler, deterministic RNG tied to match seed; state snapshots.
- Acceptance:
  - Headless sim advances deterministically across runs.
  - Snapshot diffing/interpolation stubs exist.
- Depends on: 1

## 5) Implement unit model, state machine, movement, cohesion

- Output: unit FSM (idle, moving, aiming, firing, reloading, downed); fireteam cohesion; posture speeds.
- Acceptance:
  - Units follow waypoints at correct speeds with terrain multipliers.
  - Cohesion radius maintained; regroup on straggle.
- Depends on: 2, 4

## 6) Implement combat: LOS, detection, accuracy, cover, casualties

- Output: LOS checks, detection (sight vs concealment), hit resolution; outcomes Healthy/Wounded/KIA; no friendly fire.
- Acceptance:
  - Reproducible engagements in golden tests.
  - Cover reduces hit chance; ROE gates firing.
- Depends on: 5

## 7) Implement radio model: latency, routing, spam suppression

- Output: radio event bus with fixed latency; unit-to-unit relays (timing only); de-duplication window.
- Acceptance:
  - Acks, contact, casualty, waypoint, and inability-to-comply reports delivered with configured delay.
  - Burst events collapse to summaries within a window.
- Depends on: 4, 5, 6

## 8) Implement structured command schema and validator

- Output: JSON schema and Python validator enforcing enums, ranges, and constraints.
- Acceptance:
  - Invalid orders rejected with actionable errors; valid orders enqueue.
  - Fuzz tests over schema fields.
- Depends on: 1

## 9) Implement command parser (LLM mapping) with disambiguation

- Output: transcript → schema-conformant orders; clarification prompts on ambiguity.
- Acceptance:
  - Test corpus of utterances maps to expected orders (≥90% for MVP set).
  - Clarification path triggers on ambiguous references.
- Depends on: 8

## 10) Integrate speech-to-text and voice UX with PTT/VAD

- Output: PTT binding, VAD thresholds, transcript pane; dev text fallback.
- Acceptance:
  - Commands captured reliably; offline STT option works.
  - Latency metrics logged.
- Depends on: 9

## 11) Build minimal client UI: map, grid, icons, command history

- Output: 2D map with terrain shading; A–J × 0–9 labels; draggable non-authoritative icons; command history and confirmations.
- Acceptance:
  - Player can track units manually; history shows parsed orders and statuses.
- Depends on: 4, 7

## 12) Build pre-match tent placement UI and rules

- Output: GUI for placing command tent within deployment zone; validates constraints.
- Acceptance:
  - Tent positions stored in match config; sim spawns tents accordingly.
- Depends on: 11

## 13) Build debug UI overlay: truth positions, paths, LOS, logs (dev)

- Output: toggleable overlay for development.
- Acceptance:
  - Shows server truth state, paths, and LOS; never leaks to main UI.
- Depends on: 4, 5, 6

## 14) Add configuration files for archetypes and terrain

- Output: `config/units.yaml`, `config/terrain.yaml`, `config/roe.yaml`.
- Acceptance:
  - Reload-on-start; validation on load.
- Depends on: 1

## 15) Create headless tests, seeds, and golden scenarios

- Output: scripted orders on fixed seeds; radio and outcome logs.
- Acceptance:
  - CI green determinism; regressions flagged by diffs.
- Depends on: 2, 3, 4, 6, 7

---

## Suggested directory layout

```
/schemas/
/config/
/server/
  sim/
  radio/
  orders/
/client/
  ui/
  audio/
/tests/
```

## Non-functional requirements

- Determinism: seed + command log fully reproduces a match.
- Performance: 10 Hz with ≤5 ms/tick on MVP maps.
- Telemetry: event logs for radio, casualties, contacts (JSONL).

## Definition of Done (MVP)

- All sections meet acceptance criteria on at least one scenario seed.
- Binary tent destruction works; tent placement flow complete.
- No friendly fire; radio report triggers with latency and de-duplication.

## Issues found by QA

- Fix performance issues with dragging.
- Draw more details within a command cell (e.g. trees, buildings, roads).
- Command tests should be placeable on a specific cell, not just a command cell.
