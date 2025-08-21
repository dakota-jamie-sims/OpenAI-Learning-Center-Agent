import time
from collections import OrderedDict
from typing import Any, Hashable, Tuple

class Cache:
    """Simple TTL-based LRU cache."""
    def __init__(self, maxsize: int = 128, ttl: int = 300) -> None:
        self.maxsize = maxsize
        self.ttl = ttl
        self._store: OrderedDict[Hashable, Tuple[Any, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: Hashable) -> Any:
        now = time.time()
        if key in self._store:
            value, timestamp = self._store[key]
            if now - timestamp < self.ttl:
                self._store.move_to_end(key)
                self.hits += 1
                return value
            else:
                del self._store[key]
        self.misses += 1
        return None

    def set(self, key: Hashable, value: Any) -> None:
        if key in self._store:
            del self._store[key]
        elif len(self._store) >= self.maxsize:
            self._store.popitem(last=False)
        self._store[key] = (value, time.time())

    def clear(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0