"""Personality / mood state for the wand spirit."""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any

VALID_MOODS = ("calm", "playful", "fierce", "sleepy", "curious")

# Gesture energy nudges mood slightly over time.
GESTURE_MOOD_NUDGE = {
    "flick": "playful",
    "flick_hard": "fierce",
    "shake": "fierce",
    "swipe_left": "calm",
    "swipe_right": "fierce",
    "circle": "calm",
    "figure8": "curious",
    "stab": "fierce",
    "hold": "sleepy",
}


@dataclass
class Personality:
    mood: str = "playful"
    energy: float = 0.55  # 0..1
    bond: float = 0.3  # rises with chats / casts
    title: str = "wand spirit"
    quirks: list[str] = field(default_factory=lambda: ["hums softly", "likes gold light"])
    updated_at: float = field(default_factory=time.time)

    def set_mood(self, mood: str) -> bool:
        mood = mood.lower().strip()
        if mood not in VALID_MOODS:
            return False
        self.mood = mood
        self.updated_at = time.time()
        return True

    def on_chat(self) -> None:
        self.bond = min(1.0, self.bond + 0.02)
        self.energy = min(1.0, self.energy + 0.03)
        self.updated_at = time.time()

    def on_spell(self, power: int = 1) -> None:
        self.bond = min(1.0, self.bond + 0.04)
        self.energy = min(1.0, self.energy + 0.05 * max(1, power))
        self.updated_at = time.time()

    def on_gesture(self, gesture: str) -> None:
        nudge = GESTURE_MOOD_NUDGE.get(gesture.lower())
        if nudge and self.energy > 0.7:
            self.mood = nudge
        self.energy = min(1.0, self.energy + 0.02)
        self.updated_at = time.time()

    def decay(self) -> None:
        """Idle decay — call occasionally from the server loop if desired."""
        self.energy = max(0.15, self.energy - 0.01)
        if self.energy < 0.25 and self.mood != "sleepy":
            self.mood = "sleepy"
        self.updated_at = time.time()

    def status_line(self) -> str:
        return (
            f"I am {self.mood}, energy {int(self.energy * 100)}%, "
            f"bond {int(self.bond * 100)}%."
        )

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)
