# -*- coding: utf-8 -*-
import time
import hashlib
import threading
from typing import Any, Dict, Optional, List


class ScrapperCache:
    def __init__(self, ttl: int = 3600, max_size: int = 500, cleanup_interval: int = 120):
        self.ttl = ttl
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.cleanup_interval = cleanup_interval
        self._stop_event = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()

    def _make_key(self, query: str, limit: int, subreddits: Optional[List[str]]) -> str:
        normalized_subs = ",".join(sorted(subreddits)) if subreddits else ""
        raw_key = f"{query}:{limit}:{normalized_subs}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def _cleanup_expired(self):
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if v["expires"] <= now]
        for k in expired_keys:
            del self.cache[k]

    def _enforce_size_limit(self):
        if len(self.cache) <= self.max_size:
            return
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1]["last_access"])
        for k, _ in sorted_items[: len(self.cache) - self.max_size]:
            del self.cache[k]

    def _background_cleanup(self):
        while not self._stop_event.is_set():
            time.sleep(self.cleanup_interval)
            with self.lock:
                self._cleanup_expired()
                self._enforce_size_limit()

    def stop(self):
        self._stop_event.set()
        self._cleanup_thread.join()

    def get(self, query: str, limit: int, subreddits: Optional[List[str]]) -> Optional[Any]:
        key = self._make_key(query, limit, subreddits)
        with self.lock:
            entry = self.cache.get(key)
            if entry and entry["expires"] > time.time():
                entry["last_access"] = time.time()
                return entry["value"]
            if key in self.cache:
                del self.cache[key]
        return None

    def set(self, query: str, limit: int, subreddits: Optional[List[str]], value: Any):
        key = self._make_key(query, limit, subreddits)
        with self.lock:
            self.cache[key] = {
                "value": value,
                "expires": time.time() + self.ttl,
                "last_access": time.time()
            }
            self._enforce_size_limit()

    def clear(self):
        with self.lock:
            self.cache.clear()

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "items": len(self.cache),
                "ttl": self.ttl,
                "max_size": self.max_size
            }
