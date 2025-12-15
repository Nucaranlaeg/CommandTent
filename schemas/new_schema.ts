/**
 * This document is intended to contain what is necessary/allowed for each order.
 * That it's a ts file is intended to make it easier to read.
 */

type TerrainType = "Forest" | "Mountain" | "Plain" | "Road";

type Cell = [
  "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J",
  0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9,
  [number, number][]? // Subcell coordinates, [0-99, 0-99]
];

interface Order {
  Target: {
    // At least one of `cell` or `feature` must be provided

    /**
     * Grid cell identifier, e.g. "A5"
     */
    cell?: Cell;

    /**
     * Natural language description, e.g. "top of the hill"
     * If present, gets decoded when the command starts (by LLM, along with map details) into `cell`
     * and potentially `subCell`.
     */
    feature?: string;

    /**
     * Where in the cell the actual target is. If it's not present, assigned randomly.
     */
    subCell?: [number, number];
  };

  Conveyance: {
    /**
     * The possible movement speeds.
     * Could instead be a number, and these will map to numbers.
     */
    speed?: "cautious" | "walk" | "jog" | "run" | "sprint";

    /**
     * This influences which subcells the unit will enter, and how likely it is to take a longer route
     * to avoid being seen.
     */
    stealth?: "hidden" | "normal" | "overt";

    /**
     * The actual path that unit will take.  Not populated by LLM.
     */
    path?: Cell[];

    /**
     * Numbers [1-100] of pathfinding cost for each terrain type.
     * Does not consider how difficult the terrain is to cross - it's the willingness of the unit to enter that type of terrain
     * based solely on the order given.
     * Units prefer lower numbers.
     */
    pathPreferences?: {
      [K in TerrainType]: number;
    };
  };

  Start:
    | "No other orders"
    | "Immediately"
    | "Enemy seen"
    | "Fired upon"
    | "On signal" // This might need some extra consideration
    | "No enemies visible"
    | "";
}
