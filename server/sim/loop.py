from __future__ import annotations

import time
import random
from dataclasses import dataclass
from typing import Callable, Optional


TICKS_PER_SECOND = 10
TICK_DT = 1.0 / TICKS_PER_SECOND


@dataclass
class SimClock:
    tick_rate_hz: int = TICKS_PER_SECOND
    tick: int = 0
    time_seconds: float = 0.0

    def advance(self) -> None:
        self.tick += 1
        self.time_seconds = self.tick / float(self.tick_rate_hz)


class Simulation:
    def __init__(self, seed: int, on_tick: Optional[Callable[[SimClock, random.Random], None]] = None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.clock = SimClock()
        self.on_tick = on_tick
        self._running = False

    def step(self) -> None:
        if self.on_tick:
            self.on_tick(self.clock, self.rng)
        self.clock.advance()

    def run_for_ticks(self, num_ticks: int, realtime: bool = False) -> None:
        self._running = True
        for _ in range(num_ticks):
            start = time.perf_counter() if realtime else 0.0
            self.step()
            if realtime:
                elapsed = time.perf_counter() - start
                sleep_time = max(0.0, TICK_DT - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        self._running = False
