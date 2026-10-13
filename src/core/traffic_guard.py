"""Production traffic protection for expensive CampusMind inference.

The guard deliberately limits only expensive cache-miss work. Cached FAQ answers can
still be served immediately. This prevents a sudden college-wide traffic spike from
starting an unbounded number of local LLM generations and exhausting RAM/CPU.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass
class TrafficSnapshot:
    active: int
    waiting: int
    max_concurrent: int
    max_waiting: int


class TrafficGuard:
    def __init__(self, max_concurrent: int = 2, max_waiting: int = 64, queue_timeout: float = 12.0):
        self.max_concurrent = max(1, int(max_concurrent))
        self.max_waiting = max(0, int(max_waiting))
        self.queue_timeout = max(0.1, float(queue_timeout))
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._state_lock = asyncio.Lock()
        self._active = 0
        self._waiting = 0

    async def snapshot(self) -> TrafficSnapshot:
        async with self._state_lock:
            return TrafficSnapshot(self._active, self._waiting, self.max_concurrent, self.max_waiting)

    async def acquire(self) -> float | None:
        """Acquire an inference slot and return queue wait seconds; None means overload/timeout."""
        async with self._state_lock:
            # If every worker is busy, bound the number of requests allowed to wait.
            if self._active >= self.max_concurrent:
                if self._waiting >= self.max_waiting:
                    return None
                self._waiting += 1
                queued = True
            else:
                queued = False

        started = time.monotonic()
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.queue_timeout)
        except asyncio.TimeoutError:
            if queued:
                async with self._state_lock:
                    self._waiting = max(0, self._waiting - 1)
            return None

        async with self._state_lock:
            if queued:
                self._waiting = max(0, self._waiting - 1)
            self._active += 1
        return time.monotonic() - started

    async def release(self):
        async with self._state_lock:
            self._active = max(0, self._active - 1)
        self._semaphore.release()
