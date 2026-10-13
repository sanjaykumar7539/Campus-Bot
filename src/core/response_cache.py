from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict


class ResponseCache:
    """Bounded TTL cache. Values are copied so callers cannot mutate cached data."""

    def __init__(self, ttl_seconds: int, max_entries: int):
        self.ttl = max(1, int(ttl_seconds))
        self.max_entries = max(1, int(max_entries))
        self._items = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def key(query: str, language: str) -> str:
        return f"{language.lower()}:{' '.join(query.lower().split())}"

    def get(self, key: str, now: float | None = None):
        current = time.monotonic() if now is None else now
        with self._lock:
            item = self._items.get(key)
            if not item:
                return None
            expires, value = item
            if expires <= current:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return copy.deepcopy(value)

    def set(self, key: str, value, now: float | None = None):
        current = time.monotonic() if now is None else now
        with self._lock:
            self._items[key] = (current + self.ttl, copy.deepcopy(value))
            self._items.move_to_end(key)
            while len(self._items) > self.max_entries:
                self._items.popitem(last=False)

    def clear(self):
        with self._lock:
            self._items.clear()
