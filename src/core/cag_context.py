from __future__ import annotations

import copy
import re
import time
from collections import OrderedDict
from threading import RLock


class ContextCache:
    """TTL/LRU cache for already-grounded retrieval bundles (CAG-style context reuse)."""

    def __init__(self, ttl_seconds: int = 1800, max_entries: int = 500):
        self.ttl = max(1, int(ttl_seconds))
        self.max_entries = max(1, int(max_entries))
        self._data = OrderedDict()
        self._lock = RLock()

    @staticmethod
    def normalize(query: str) -> str:
        return re.sub(r"\s+", " ", (query or "").strip().lower())

    def get(self, query: str):
        key = self.normalize(query)
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            expires, value = item
            if expires <= now:
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            out = copy.deepcopy(value)
            out["cag_cache_hit"] = True
            return out

    def set(self, query: str, value: dict):
        key = self.normalize(query)
        if not key:
            return
        with self._lock:
            stored = copy.deepcopy(value)
            stored["cag_cache_hit"] = False
            self._data[key] = (time.time() + self.ttl, stored)
            self._data.move_to_end(key)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)
