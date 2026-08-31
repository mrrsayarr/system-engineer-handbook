"""Educational single-flight cache; standard library only."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass
class Entry(Generic[T]):
    value: T
    expires_at: float
    stale_until: float


class SingleFlightCache(Generic[T]):
    def __init__(self, origin: Callable[[], T], ttl: float = 2.0, stale_for: float = 5.0):
        self._origin = origin
        self._ttl = ttl
        self._stale_for = stale_for
        self._entry: Entry[T] | None = None
        self._refreshing = False
        self._condition = threading.Condition()

    def get(self) -> T:
        now = time.monotonic()
        with self._condition:
            entry = self._entry
            if entry and now < entry.expires_at:
                return entry.value
            if entry and now < entry.stale_until:
                if not self._refreshing:
                    self._refreshing = True
                    threading.Thread(target=self._refresh, daemon=True).start()
                return entry.value
            if self._refreshing:
                self._condition.wait(timeout=1.0)
                if self._entry and time.monotonic() < self._entry.stale_until:
                    return self._entry.value
            self._refreshing = True
        return self._refresh_blocking()

    def _refresh_blocking(self) -> T:
        try:
            value = self._origin()
            now = time.monotonic()
            with self._condition:
                self._entry = Entry(value, now + self._ttl, now + self._ttl + self._stale_for)
            return value
        finally:
            with self._condition:
                self._refreshing = False
                self._condition.notify_all()

    def _refresh(self) -> None:
        try:
            self._refresh_blocking()
        except Exception:
            # Keep stale data until its explicit stale deadline; do not hide errors
            # from callers once the stale window has expired.
            pass


if __name__ == "__main__":
    calls = 0

    def origin() -> str:
        global calls
        calls += 1
        time.sleep(0.1)
        return f"origin-value-{calls}"

    cache = SingleFlightCache(origin)
    print([cache.get() for _ in range(5)])
    time.sleep(2.1)
    print([cache.get() for _ in range(5)])
    print(f"origin_calls={calls} (expected 2 or fewer for this sequential demo)")
