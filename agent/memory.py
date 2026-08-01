"""Conversation, gesture, and spell memory for the wand agent."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Any, Deque, Iterable


@dataclass
class Turn:
    role: str  # system | user | assistant | wand
    content: str
    source: str = "dashboard"
    ts: float = field(default_factory=time.time)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_llm(self) -> dict[str, str]:
        role = self.role if self.role in ("system", "user", "assistant") else "user"
        return {"role": role, "content": self.content}


@dataclass
class GestureEvent:
    gesture: str
    spell: str | None
    ts: float = field(default_factory=time.time)
    ax: float | None = None
    ay: float | None = None
    az: float | None = None


class WandMemory:
    """Rolling memory of chat turns, gestures, and cast spells."""

    def __init__(
        self,
        max_turns: int = 40,
        max_gestures: int = 80,
        max_spells: int = 40,
    ) -> None:
        self.max_turns = max_turns
        self.turns: Deque[Turn] = deque(maxlen=max_turns)
        self.gestures: Deque[GestureEvent] = deque(maxlen=max_gestures)
        self.spell_casts: Deque[dict[str, Any]] = deque(maxlen=max_spells)
        self.facts: dict[str, str] = {}
        self.created_at = time.time()

    def add_turn(
        self,
        role: str,
        content: str,
        source: str = "dashboard",
        **meta: Any,
    ) -> Turn:
        turn = Turn(role=role, content=content.strip(), source=source, meta=meta)
        self.turns.append(turn)
        return turn

    def add_gesture(
        self,
        gesture: str,
        spell: str | None = None,
        imu: dict[str, float] | None = None,
    ) -> GestureEvent:
        imu = imu or {}
        event = GestureEvent(
            gesture=gesture,
            spell=spell,
            ax=imu.get("ax"),
            ay=imu.get("ay"),
            az=imu.get("az"),
        )
        self.gestures.append(event)
        if spell:
            self.spell_casts.append(
                {"spell": spell, "gesture": gesture, "ts": event.ts}
            )
        return event

    def remember_fact(self, key: str, value: str) -> None:
        self.facts[key.strip().lower()] = value.strip()

    def forget_fact(self, key: str) -> bool:
        return self.facts.pop(key.strip().lower(), None) is not None

    def clear_chat(self) -> None:
        self.turns.clear()

    def clear_all(self) -> None:
        self.turns.clear()
        self.gestures.clear()
        self.spell_casts.clear()
        self.facts.clear()

    def recent_messages(self, limit: int = 12) -> list[dict[str, str]]:
        items = list(self.turns)[-limit:]
        return [t.to_llm() for t in items if t.role in ("user", "assistant", "system")]

    def summary_blob(self) -> str:
        facts = ", ".join(f"{k}={v}" for k, v in self.facts.items()) or "none"
        last_spells = [s["spell"] for s in list(self.spell_casts)[-5:]]
        last_gestures = [g.gesture for g in list(self.gestures)[-5:]]
        return (
            f"Known facts: {facts}. "
            f"Recent spells: {', '.join(last_spells) or 'none'}. "
            f"Recent gestures: {', '.join(last_gestures) or 'none'}."
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "turns": [asdict(t) for t in self.turns],
            "gestures": [asdict(g) for g in self.gestures],
            "spell_casts": list(self.spell_casts),
            "facts": dict(self.facts),
            "created_at": self.created_at,
            "turn_count": len(self.turns),
        }

    def iter_assistant_replies(self) -> Iterable[str]:
        for t in self.turns:
            if t.role == "assistant":
                yield t.content
