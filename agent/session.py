"""Session bag — wand online flag, last IMU, agent handles."""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SessionState:
    wand_online: bool = False
    last_imu: dict[str, float] = field(default_factory=dict)
    last_gesture: str | None = None
    last_spell: str | None = None
    last_ai_reply: str | None = None
    prompts_total: int = 0
    spells_total: int = 0
    started_at: float = field(default_factory=time.time)

    def mark_wand(self, online: bool) -> None:
        self.wand_online = online

    def update_imu(self, msg: dict[str, Any]) -> None:
        self.last_imu = {
            k: float(msg[k])
            for k in ("ax", "ay", "az", "gx", "gy", "gz")
            if k in msg
        }

    def note_gesture(self, gesture: str, spell: str | None) -> None:
        self.last_gesture = gesture
        if spell:
            self.last_spell = spell
            self.spells_total += 1

    def note_ai(self, reply: str) -> None:
        self.last_ai_reply = reply
        self.prompts_total += 1

    def snapshot(self) -> dict[str, Any]:
        data = asdict(self)
        data["uptime_sec"] = round(time.time() - self.started_at, 1)
        return data
