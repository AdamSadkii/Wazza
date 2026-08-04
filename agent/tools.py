"""Wand tools the AI can request — LED, OLED, spells, status."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from .spellbook import spell_by_name

SendFn = Callable[[dict[str, Any]], Awaitable[None]]

ACTION_JSON_RE = re.compile(
    r"\{[^{}]*\"action\"\s*:\s*\"(led|flash|oled|spell|led_off)\"[^{}]*\}",
    re.IGNORECASE,
)


@dataclass
class ToolResult:
    ok: bool
    action: str
    detail: str
    cmd: dict[str, Any] | None = None


@dataclass
class WandToolkit:
    """Execute physical wand effects from parsed AI / user intents."""

    send: SendFn
    last_cmds: list[dict[str, Any]] = field(default_factory=list)

    async def led(self, r: int, g: int, b: int) -> ToolResult:
        cmd = {"cmd": "led", "r": _clamp(r), "g": _clamp(g), "b": _clamp(b)}
        return await self._run("led", cmd, f"LEDs set to rgb({cmd['r']},{cmd['g']},{cmd['b']})")

    async def flash(
        self,
        r: int = 255,
        g: int = 255,
        b: int = 255,
        times: int = 2,
    ) -> ToolResult:
        cmd = {
            "cmd": "flash",
            "r": _clamp(r),
            "g": _clamp(g),
            "b": _clamp(b),
            "times": max(1, min(int(times), 8)),
        }
        return await self._run("flash", cmd, f"Flashed {cmd['times']}x")

    async def led_off(self) -> ToolResult:
        cmd = {"cmd": "led_off"}
        return await self._run("led_off", cmd, "LEDs extinguished")

    async def oled(self, line1: str, line2: str = "") -> ToolResult:
        cmd = {
            "cmd": "oled",
            "line1": (line1 or "")[:21],
            "line2": (line2 or "")[:21],
        }
        return await self._run("oled", cmd, "OLED updated")

    async def cast_spell(self, name: str) -> ToolResult:
        found = spell_by_name(name)
        if not found:
            return ToolResult(False, "spell", f"Unknown spell: {name}")
        title, data = found
        cmd = data["cmd"]
        await self.send(cmd)
        self.last_cmds.append(cmd)
        return ToolResult(True, "spell", f"Cast {title}", cmd)

    async def apply_action_dict(self, action: dict[str, Any]) -> ToolResult:
        kind = str(action.get("action", "")).lower()
        args = action.get("args") or {}
        if kind == "led":
            return await self.led(args.get("r", 0), args.get("g", 0), args.get("b", 0))
        if kind == "flash":
            return await self.flash(
                args.get("r", 255),
                args.get("g", 255),
                args.get("b", 255),
                args.get("times", 2),
            )
        if kind == "led_off":
            return await self.led_off()
        if kind == "oled":
            return await self.oled(args.get("line1", ""), args.get("line2", ""))
        if kind == "spell":
            return await self.cast_spell(str(args.get("name", "")))
        return ToolResult(False, kind or "unknown", "Unsupported action")

    async def _run(self, action: str, cmd: dict[str, Any], detail: str) -> ToolResult:
        await self.send(cmd)
        self.last_cmds.append(cmd)
        if len(self.last_cmds) > 50:
            self.last_cmds = self.last_cmds[-50:]
        return ToolResult(True, action, detail, cmd)


def extract_action_json(text: str) -> tuple[str, dict[str, Any] | None]:
    """Strip a trailing/inline action JSON object from model output."""
    match = ACTION_JSON_RE.search(text)
    if not match:
        return text.strip(), None
    raw = match.group(0)
    try:
        action = json.loads(raw)
    except json.JSONDecodeError:
        return text.strip(), None
    cleaned = (text[: match.start()] + text[match.end() :]).strip()
    return cleaned, action


def hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    h = value.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def _clamp(v: Any) -> int:
    try:
        return max(0, min(255, int(v)))
    except (TypeError, ValueError):
        return 0
    