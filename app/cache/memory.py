import time
from collections import OrderedDict
from dataclasses import dataclass

from app.config import settings


@dataclass
class MemoryEntry:
    score: int
    details: str
    expires_at: float


class MemoryCache:
    """Thread-safe in-process LRU cache for hot-path lookups."""

    def __init__(self, max_size: int | None = None, ttl: int | None = None):
        self._max_size = max_size or settings.memory_cache_max_size
        self._ttl = ttl or settings.cache_ttl_seconds
        self._store: OrderedDict[str, MemoryEntry] = OrderedDict()

    def get(self, url: str) -> MemoryEntry | None:
        entry = self._store.get(url)
        if entry is None:
            return None
        if time.time() > entry.expires_at:
            self._store.pop(url, None)
            return None
        self._store.move_to_end(url)
        return entry

    def put(self, url: str, score: int, details: str) -> None:
        if url in self._store:
            self._store.move_to_end(url)
        self._store[url] = MemoryEntry(
            score=score,
            details=details,
            expires_at=time.time() + self._ttl,
        )
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)
