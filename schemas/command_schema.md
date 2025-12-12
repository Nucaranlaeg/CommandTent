# Command Schema - Complete Reference for LLM Parsing

This document provides a complete specification of the command schema for parsing natural language military commands into structured orders. Use this as a reference when implementing LLM-based command parsing.

## Overview

All commands must include at minimum:
- `units`: Array of unit identifiers (required)
- `intent`: The primary action to perform (required)

All other fields are optional and have sensible defaults.

## Field Specifications

### `units` (required)
**Type:** `array` of `string`  
**Min Items:** 1  
**Description:** List of unit identifiers (fireteam names or individual soldier names) that will execute this order.

**Valid Unit Names:**
- Fireteams: `"Red"`, `"Blue"`, `"Green"`, `"Gold"`, `"Brown"`
- Individual Soldiers (NATO alphabet): `"Alpha"`, `"Bravo"`, `"Charlie"`, `"Delta"`, `"Echo"`, etc.

**Natural Language Patterns:**
- "Red, move to A3" → `["Red"]`
- "Red and Blue, advance" → `["Red", "Blue"]`
- "Alpha, Bravo, and Charlie hold position" → `["Alpha", "Bravo", "Charlie"]`
- "All fireteams" → `["Red", "Blue", "Green", "Gold", "Brown"]` (if contextually appropriate)

**Example:**
```json
"units": ["Red", "Blue"]
```

---

### `intent` (required)
**Type:** `string` (enum)  
**Description:** The primary action or command type.

**Valid Values:**
- `"move"` - Move to specified waypoints
- `"hold"` - Maintain current position, no movement
- `"attack"` - Engage enemy targets
- `"observe"` - Watch/monitor an area
- `"support"` - Provide support to other units
- `"retreat"` - Withdraw from current position
- `"cancel"` - Cancel previous order

**Natural Language Patterns:**
- `"move"`: "move", "go", "advance", "proceed", "head to", "travel to", "march", "push forward"
- `"hold"`: "hold", "stop", "halt", "wait", "stay", "remain", "hold position", "stand by"
- `"attack"`: "attack", "fire", "engage", "shoot", "strike", "assault", "open fire"
- `"observe"`: "observe", "watch", "look", "scan", "monitor", "recon", "reconnaissance"
- `"support"`: "support", "help", "assist", "backup", "reinforce"
- `"retreat"`: "retreat", "withdraw", "fall back", "pull back", "retire"
- `"cancel"`: "cancel", "abort", "disregard", "ignore", "scrub"

**Example:**
```json
"intent": "move"
```

---

### `waypoints` (optional)
**Type:** `array`  
**Min Items:** 1 (if provided)  
**Description:** Ordered list of destination points. Units will move through these in sequence.

**Waypoint Format Options:**

1. **Simple Command Cell** (string):
   - Format: `"[A-J][0-9]"`
   - Examples: `"A3"`, `"B7"`, `"J0"`
   - Description: Coarse command grid coordinate

2. **Precise Subcell** (object):
   - Format:
     ```json
     {
       "commandCell": "A3",
       "subcell": {
         "x": 45,
         "y": 67
       }
     }
     ```
   - Description: Precise position within a command cell (0-99 for both x and y)

**Natural Language Patterns:**
- "move to A3" → `["A3"]`
- "go to B6 then C7" → `["B6", "C7"]`
- "advance through A3, A4, then B4" → `["A3", "A4", "B4"]`
- "move to the forest in A4" → `["A4"]` (terrain preference handled in constraints)
- "proceed to A3, then continue to B4" → `["A3", "B4"]`

**Sequence Indicators:**
- "then", "next", "after", "through", "via", "passing through"

**Example:**
```json
"waypoints": ["A3", "B4", "C5"]
```

**Note:** `waypoints` is required for `intent: "move"` but optional for other intents (may be empty array).

---

### `constraints` (optional)
**Type:** `object`  
**Description:** Movement and behavior constraints.

**Properties:**

#### `preferTerrain` (optional)
**Type:** `array` of `string` (enum)  
**Unique Items:** true  
**Description:** Terrain types to prefer when pathfinding.

**Valid Values:**
- `"road"` - Prefer roads for faster movement
- `"open"` - Prefer open terrain
- `"forest"` - Prefer forest for concealment
- `"building"` - Prefer buildings for cover

**Natural Language Patterns:**
- "via roads", "use roads", "stick to roads" → `["road"]`
- "through the forest", "stay in forest", "prefer forest" → `["forest"]`
- "use buildings", "take cover in buildings" → `["building"]`
- "via roads and forest" → `["road", "forest"]`
- "stay in the forest if possible" → `["forest"]`

**Example:**
```json
"preferTerrain": ["road", "forest"]
```

#### `avoidCells` (optional)
**Type:** `array` of `string`  
**Unique Items:** true  
**Format:** `"[A-J][0-9]"`  
**Description:** Command cells to avoid during pathfinding.

**Natural Language Patterns:**
- "avoid C3", "stay away from C3" → `["C3"]`
- "avoid C column", "don't go through C" → `["C0", "C1", "C2", ...]` (if contextually clear)
- "bypass A3 and A4" → `["A3", "A4"]`
- "don't go through B5" → `["B5"]`

**Example:**
```json
"avoidCells": ["C3", "C4"]
```

#### `stayConcealed` (optional)
**Type:** `boolean`  
**Default:** `false`  
**Description:** Prefer paths and positions that maintain concealment.

**Natural Language Patterns:**
- "stay concealed", "remain hidden", "keep stealth" → `true`
- "stay in cover", "maintain concealment" → `true`
- "sneak", "move stealthily" → `true`

**Example:**
```json
"stayConcealed": true
```

#### `speed` (optional)
**Type:** `string` (enum)  
**Default:** `"normal"`  
**Description:** Movement speed preference.

**Valid Values:**
- `"slow"` - Cautious, careful movement
- `"normal"` - Standard movement speed
- `"fast"` - Rapid movement, may reduce accuracy/concealment

**Natural Language Patterns:**
- `"slow"`: "slow", "careful", "cautious", "crawl", "creep"
- `"normal"`: (default, often implicit)
- `"fast"`: "fast", "quick", "hurry", "rush", "sprint", "double time", "move quickly"

**Example:**
```json
"speed": "fast"
```

**Complete Example:**
```json
"constraints": {
  "preferTerrain": ["road", "forest"],
  "avoidCells": ["C3"],
  "stayConcealed": true,
  "speed": "normal"
}
```

---

### `roe` (optional)
**Type:** `string` (enum)  
**Default:** `"return_fire"`  
**Description:** Rules of Engagement - when units are allowed to fire.

**Valid Values:**
- `"hold"` - Do not fire unless directly threatened (weapons tight)
- `"return_fire"` - Only fire when fired upon (default)
- `"free"` - Fire at will on any valid target

**Natural Language Patterns:**
- `"hold"`: "hold fire", "weapons tight", "don't fire", "no fire", "cease fire", "weapons hold"
- `"return_fire"`: "return fire", "fire back", "defensive fire", "only if fired upon"
- `"free"`: "fire at will", "weapons free", "open fire", "engage freely", "weapons hot"

**Example:**
```json
"roe": "hold"
```

---

### `posture` (optional)
**Type:** `string` (enum)  
**Default:** `"stand"`  
**Description:** Physical posture affecting movement speed, concealment, and accuracy.

**Valid Values:**
- `"stand"` - Upright, fastest movement, least concealment
- `"crouch"` - Moderate speed, better concealment and accuracy
- `"prone"` - Slowest movement, best concealment and accuracy

**Natural Language Patterns:**
- `"stand"`: "stand", "upright", "on feet", "standing"
- `"crouch"`: "crouch", "crouched", "duck", "squat", "crouch down"
- `"prone"`: "prone", "lie down", "go prone", "flat", "get down" (if not crouch context)

**Example:**
```json
"posture": "crouch"
```

---

### `engagement` (optional)
**Type:** `object`  
**Description:** Targeting and engagement specifications.

**Properties:**

#### `targetCells` (optional)
**Type:** `array` of `string`  
**Unique Items:** true  
**Format:** `"[A-J][0-9]"`  
**Description:** Command cells containing targets to engage.

**Natural Language Patterns:**
- "engage B6", "fire on B6", "target B6" → `["B6"]`
- "suppress C3 and C4" → `["C3", "C4"]` (with `suppressOnly: true`)
- "attack units in B5" → `["B5"]`

**Example:**
```json
"targetCells": ["B6", "B7"]
```

#### `suppressOnly` (optional)
**Type:** `boolean`  
**Default:** `false`  
**Description:** If true, focus on suppression fire rather than elimination.

**Natural Language Patterns:**
- "suppress", "suppressing fire", "lay down suppressive fire" → `true`
- "pin down", "keep their heads down" → `true`

**Example:**
```json
"suppressOnly": true
```

**Complete Example:**
```json
"engagement": {
  "targetCells": ["B6"],
  "suppressOnly": false
}
```

**Note:** `engagement` is typically used with `intent: "attack"` but can be combined with other intents.

---

### `priority` (optional)
**Type:** `string` (enum)  
**Default:** `"normal"`  
**Description:** Order priority affecting execution urgency.

**Valid Values:**
- `"low"` - Low priority, can be delayed
- `"normal"` - Standard priority (default)
- `"high"` - High priority, execute immediately

**Natural Language Patterns:**
- `"low"`: "low priority", "when convenient", "eventually"
- `"normal"`: (default, often implicit)
- `"high"`: "urgent", "immediately", "priority", "asap", "right away"

**Example:**
```json
"priority": "high"
```

---

### `ack` (optional)
**Type:** `boolean`  
**Default:** `true`  
**Description:** Whether units should acknowledge this order over radio.

**Natural Language Patterns:**
- Usually implicit (defaults to true)
- "no ack", "silent", "no response" → `false`

**Example:**
```json
"ack": true
```

---

## Complete Command Examples

### Example 1: Simple Movement
**Natural Language:** "Red, move to B6 via roads. Weapons tight."

**Structured Order:**
```json
{
  "units": ["Red"],
  "intent": "move",
  "waypoints": ["B6"],
  "constraints": {
    "preferTerrain": ["road"]
  },
  "roe": "hold"
}
```

### Example 2: Complex Movement with Constraints
**Natural Language:** "Red and Blue, advance through A3 then B4. Stay concealed and avoid C column. Crouch down."

**Structured Order:**
```json
{
  "units": ["Red", "Blue"],
  "intent": "move",
  "waypoints": ["A3", "B4"],
  "constraints": {
    "avoidCells": ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"],
    "stayConcealed": true
  },
  "posture": "crouch"
}
```

### Example 3: Attack Order
**Natural Language:** "Alpha, attack B6. Suppress only. Weapons free."

**Structured Order:**
```json
{
  "units": ["Alpha"],
  "intent": "attack",
  "engagement": {
    "targetCells": ["B6"],
    "suppressOnly": true
  },
  "roe": "free"
}
```

### Example 4: Hold with ROE Change
**Natural Language:** "All fireteams, hold position. Weapons tight."

**Structured Order:**
```json
{
  "units": ["Red", "Blue", "Green", "Gold", "Brown"],
  "intent": "hold",
  "roe": "hold"
}
```

### Example 5: Retreat
**Natural Language:** "Red, fall back to A1. Fast. Stay in the forest if possible."

**Structured Order:**
```json
{
  "units": ["Red"],
  "intent": "retreat",
  "waypoints": ["A1"],
  "constraints": {
    "preferTerrain": ["forest"],
    "speed": "fast"
  }
}
```

### Example 6: Observe
**Natural Language:** "Bravo, observe B6. Stay prone and concealed."

**Structured Order:**
```json
{
  "units": ["Bravo"],
  "intent": "observe",
  "waypoints": ["B6"],
  "constraints": {
    "stayConcealed": true
  },
  "posture": "prone"
}
```

---

## Field Dependencies and Rules

1. **`waypoints` and `intent`**:
   - Required for `intent: "move"`, `intent: "retreat"`
   - Optional but allowed for `intent: "observe"`, `intent: "support"`
   - Not typically used for `intent: "hold"`, `intent: "cancel"`

2. **`engagement`**:
   - Most commonly used with `intent: "attack"`
   - Can be combined with movement intents to specify targets while moving

3. **`constraints.avoidCells`**:
   - Only meaningful with movement intents
   - Pathfinding will attempt to route around these cells

4. **`constraints.preferTerrain`**:
   - Pathfinding will prefer these terrain types when multiple valid paths exist
   - Does not guarantee exclusive use of preferred terrain

5. **`roe`**:
   - Applies to all units in the order
   - Overrides any previous ROE for those units

6. **`posture`**:
   - Applies to all units in the order
   - Affects movement speed, concealment, and combat effectiveness

---

## Parsing Guidelines for LLMs

1. **Extract all mentioned units**: Look for fireteam names and NATO alphabet names. Handle conjunctions ("and", "or", commas).

2. **Determine intent from action verbs**: Map natural language verbs to the intent enum. Consider context (e.g., "advance" usually means "move").

3. **Extract waypoints in order**: Preserve sequence when multiple waypoints are mentioned. Look for sequence indicators ("then", "next", "after").

4. **Parse constraints from modifiers**: 
   - Terrain preferences from phrases like "via roads", "through forest"
   - Speed from adverbs like "quickly", "carefully"
   - Concealment from words like "stealth", "concealed", "hidden"

5. **Extract ROE from weapons language**: Look for phrases about firing rules, not just "fire" (which might indicate attack intent).

6. **Infer posture from body position language**: Distinguish between "crouch" and "prone" carefully.

7. **Handle engagement targets**: Extract target cells from attack/suppress commands.

8. **Use defaults wisely**: Only include optional fields if explicitly mentioned or strongly implied. Don't over-specify.

9. **Validate output**: Ensure all enum values match exactly, coordinate formats are correct (A-J, 0-9), and required fields are present.

10. **Handle ambiguity**: If multiple interpretations exist, prefer the most specific one. If truly ambiguous, flag for clarification.

---

## Common Parsing Challenges

### Challenge 1: Multiple Units
- "Red and Blue" → `["Red", "Blue"]`
- "Red, Blue, and Green" → `["Red", "Blue", "Green"]`
- "All fireteams" → Context-dependent, may need to expand to all five fireteams

### Challenge 2: Waypoint Sequence
- "A3 then B4" → `["A3", "B4"]`
- "through A3 to B4" → `["A3", "B4"]` (A3 is intermediate, B4 is destination)
- "A3 and B4" → Could be either `["A3", "B4"]` or two separate orders; prefer sequence

### Challenge 3: Terrain Association
- "move to the forest in A4" → waypoint: `["A4"]`, preferTerrain: `["forest"]`
- "move via forest to A4" → waypoint: `["A4"]`, preferTerrain: `["forest"]`

### Challenge 4: ROE vs Intent
- "fire on B6" → intent: `"attack"`, engagement.targetCells: `["B6"]`
- "weapons free" → roe: `"free"` (doesn't change intent if already moving)

### Challenge 5: Posture Ambiguity
- "get down" → Could be crouch or prone; prefer prone if in combat context
- "down" alone → Usually prone, but check context

---

## Output Format

The LLM should output **only valid JSON** matching this schema. No explanatory text, no markdown code blocks (unless the API requires it), just the raw JSON object.

**Valid Output Example:**
```json
{"units": ["Red"], "intent": "move", "waypoints": ["B6"], "constraints": {"preferTerrain": ["road"]}, "roe": "hold"}
```

**Invalid Output Examples:**
- Including explanatory text: "Here's the parsed command: {...}"
- Using markdown: \`\`\`json {...} \`\`\`
- Missing required fields
- Invalid enum values
- Malformed coordinates

---

## Validation Checklist

Before returning a parsed command, verify:

- [ ] `units` array is present and non-empty
- [ ] `intent` is one of the valid enum values
- [ ] All unit names are valid (fireteam or NATO alphabet)
- [ ] All waypoint coordinates match pattern `[A-J][0-9]`
- [ ] All terrain types in `preferTerrain` are valid enum values
- [ ] All cells in `avoidCells` match coordinate pattern
- [ ] `roe` is one of: "hold", "return_fire", "free"
- [ ] `posture` is one of: "stand", "crouch", "prone"
- [ ] `speed` is one of: "slow", "normal", "fast"
- [ ] `priority` is one of: "low", "normal", "high"
- [ ] If `engagement` is present, `targetCells` contains valid coordinates
- [ ] JSON is valid and parseable

---

## Version

This schema corresponds to the JSON schema defined in `schemas/order.schema.json` and the Python types in `schemas/types.py`.

Last Updated: 2024

