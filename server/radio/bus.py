from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Deque, List, Optional, Tuple
from collections import deque

from server.sim.loop import SimClock


@dataclass
class RadioEvent:
    tick_emit: int
    channel: str
    message: str


class RadioBus:
    def __init__(self, latency_ticks: int = 3, suppress_window_ticks: int = 5) -> None:
        self.latency_ticks = latency_ticks
        self.suppress_window_ticks = suppress_window_ticks
        self._queue: Deque[RadioEvent] = deque()
        self._recent: List[Tuple[int, str, str]] = []  # (tick, channel, message)
        self._delivered: List[RadioEvent] = []

    def send(self, clock: SimClock, channel: str, message: str) -> None:
        # Spam suppression: if identical message on same channel recently, drop
        for tick, ch, msg in self._recent:
            if ch == channel and msg == message and (clock.tick - tick) <= self.suppress_window_ticks:
                return
        self._recent.append((clock.tick, channel, message))
        self._queue.append(RadioEvent(clock.tick + self.latency_ticks, channel, message))
        # Trim recent
        cutoff = clock.tick - self.suppress_window_ticks
        self._recent = [r for r in self._recent if r[0] >= cutoff]

    def deliver(self, clock: SimClock, handler: Callable[[RadioEvent], None]) -> None:
        # Deliver all whose tick_emit <= current tick
        while self._queue and self._queue[0].tick_emit <= clock.tick:
            evt = self._queue.popleft()
            handler(evt)
            self._delivered.append(evt)

    @property
    def delivered(self) -> List[RadioEvent]:
        return list(self._delivered)
