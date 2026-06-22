import time

from app.cache.memory import MemoryCache, MemoryEntry


def test_memory_cache_put_and_get():
    cache = MemoryCache(max_size=10, ttl=60)
    cache.put("http://a.com", 95, "")
    entry = cache.get("http://a.com")
    assert entry is not None
    assert entry.score == 95


def test_memory_cache_miss():
    cache = MemoryCache(max_size=10, ttl=60)
    assert cache.get("http://missing.com") is None


def test_memory_cache_expiry():
    cache = MemoryCache(max_size=10, ttl=1)
    cache.put("http://a.com", 80, "old")
    cache._store["http://a.com"] = MemoryEntry(score=80, details="old", expires_at=time.time() - 1)
    assert cache.get("http://a.com") is None


def test_memory_cache_eviction():
    cache = MemoryCache(max_size=2, ttl=60)
    cache.put("http://a.com", 90, "")
    cache.put("http://b.com", 80, "")
    cache.put("http://c.com", 70, "")
    assert cache.get("http://a.com") is None
    assert cache.get("http://b.com") is not None
    assert cache.get("http://c.com") is not None
