import src.utils.cache as cache_module


def test_cache_ttl_expiry(monkeypatch):
    cache = cache_module.Cache(maxsize=2, ttl=1)
    monkeypatch.setattr(cache_module.time, "time", lambda: 0)
    cache.set("a", "value")
    # Retrieve within TTL
    monkeypatch.setattr(cache_module.time, "time", lambda: 0.5)
    assert cache.get("a") == "value"
    # After TTL expires
    monkeypatch.setattr(cache_module.time, "time", lambda: 2)
    assert cache.get("a") is None
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_lru_eviction(monkeypatch):
    cache = cache_module.Cache(maxsize=2, ttl=100)
    monkeypatch.setattr(cache_module.time, "time", lambda: 0)
    cache.set("a", 1)
    cache.set("b", 2)
    # Use 'a' so 'b' becomes least recently used
    cache.get("a")
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_cache_hit_miss_counters(monkeypatch):
    cache = cache_module.Cache(maxsize=2, ttl=100)
    monkeypatch.setattr(cache_module.time, "time", lambda: 0)
    cache.set("x", 10)
    assert cache.get("x") == 10
    assert cache.hits == 1
    assert cache.misses == 0
    assert cache.get("y") is None
    assert cache.hits == 1
    assert cache.misses == 1
