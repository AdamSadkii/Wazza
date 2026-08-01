"""Light safety rails — rate limits and simple content guards."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass


BLOCKLIST = (
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt",
    "jailbreak",
)


@dataclass
class SafetyDecision:
    ok: bool
    reason: str = ""
    cleaned: str = ""


class RateLimiter:
    def __init__(self, max_calls: int = 20, window_sec: float = 60.0) -> None:
        self.max_calls = max_calls
        self.window_sec = window_sec
        self._hits: deque[float] = deque()

    def allow(self) -> bool:
        now = time.time()
        while self._hits and now - self._hits[0] > self.window_sec:
            self._hits.popleft()
        if len(self._hits) >= self.max_calls:
            return False
        self._hits.append(now)
        return True

    def remaining(self) -> int:
        now = time.time()
        while self._hits and now - self._hits[0] > self.window_sec:
            self._hits.popleft()
        return max(0, self.max_calls - len(self._hits))


def scrub_user_text(text: str, max_len: int = 500) -> SafetyDecision:
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return SafetyDecision(False, "empty", "")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    low = cleaned.lower()
    for bad in BLOCKLIST:
        if bad in low:
            return SafetyDecision(False, "blocked_pattern", cleaned)
    return SafetyDecision(True, "", cleaned)


def clamp_reply(text: str, max_len: int = 400) -> str:
    text = " ".join((text or "").strip().split())
    if len(text) > max_len:
        return text[: max_len - 1].rstrip() + "…"
    return text
