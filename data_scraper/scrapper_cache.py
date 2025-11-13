# -*- coding: utf-8 -*-
import time
import hashlib
from typing import Any, Dict, Optional


class ScrapperCache:
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _make_key(self, query: str, limit: int, subreddits: Optional[list]) -> str:
        raw_key = f"{query}:{limit}:{','.join(subreddits or [])}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, query: str, limit: int, subreddits: Optional[list]) -> Optional[Any]:
        key = self._make_key(query, limit, subreddits)
        entry = self.cache.get(key)
        if entry and entry["expires"] > time.time():
            return entry["value"]
        if key in self.cache:
            del self.cache[key]
        return None

    def set(self, query: str, limit: int, subreddits: Optional[list], value: Any):
        key = self._make_key(query, limit, subreddits)
        self.cache[key] = {"value": value, "expires": time.time() + self.ttl}
