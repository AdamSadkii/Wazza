"""In-memory event ring for debugging / future UI replay."""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Deque

class EventStore:
    def __init__(self, maxLen: int = 500) -> None:
        self._events: Deque[dict[str, Any]] = deque(maxlen=maxLen)

    def add(self, event: dict[str, Any]) -> None:
        item = dict(event)
        item.setdefault("_ts", time.time())
        self._events.append(item)

    def recent(self, n: int = 50) -> list[dict[str, Any]]:
        items = list(self._events)
        return items[-n:]

    def clear(self) -> None:
        self._events.clear()
