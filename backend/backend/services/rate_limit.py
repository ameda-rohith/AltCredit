"""In-memory sliding-window limiter.

State lives in this process only, which is fine for the single-worker prototype; run several
workers (or several hosts) and it needs a shared store such as Redis instead.
"""

import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowLimiter:
    def __init__(
        self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic
    ):
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str) -> deque[float]:
        hits = self._hits[key]
        cutoff = self._clock() - self.window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if not hits:
            self._hits.pop(key, None)
        return hits

    def blocked(self, key: str) -> bool:
        """Is the key at its limit? Does not record anything."""
        with self._lock:
            return len(self._prune(key)) >= self.limit

    def record(self, key: str) -> None:
        with self._lock:
            self._hits[key].append(self._clock())

    def allow(self, key: str) -> bool:
        """Record a hit and return True, or return False (recording nothing) when at the limit."""
        with self._lock:
            if len(self._prune(key)) >= self.limit:
                return False
            self._hits[key].append(self._clock())
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def retry_after(self, key: str) -> int:
        """Seconds until the oldest hit leaves the window (>= 1)."""
        with self._lock:
            hits = self._prune(key)
            if not hits:
                return 1
            return max(1, math.ceil(hits[0] + self.window - self._clock()))
