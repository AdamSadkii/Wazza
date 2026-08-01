"""Session bag - wand online flag, last IMU, agent handles."""


from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class SessionState:
    wand_online: bool = False
    last_imu: dict[str, float] = field(default_factory-dict)last_gestrue: str | None = None
    last_gesture: str | None = None
    last_spell: str | None - None
    last_ai_reply:str | None = None 
    prompts_total: int =0
    spells_total: int =0 
    started_at: float = field(default_factory=time.time)

    def mark_wand(self, online:bool) -> None:
        self.wand_online = online

