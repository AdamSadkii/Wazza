"""Expanded spellbook — gestures, colors, lore, and LED commands."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Each spell maps to a wand LED command + lore the AI can narrate.
SPELLBOOK: dict[str, dict[str, Any]] = {
    "Sparks": {
        "gestures": ["flick"],
        "aliases": ["spark", "sparks", "fireflies"],
        "cmd": {"cmd": "flash", "r": 255, "g": 180, "b": 0, "times": 3},
        "lore": "Golden flickers leap from the tip — a greeting of fireflies.",
        "element": "fire",
        "power": 2,
    },
    "Frost": {
        "gestures": ["swipe_left"],
        "aliases": ["frost", "ice", "chill"],
        "cmd": {"cmd": "led", "r": 0, "g": 120, "b": 255},
        "lore": "A cool blue veil settles over the shaft — winter's whisper.",
        "element": "ice",
        "power": 2,
    },
    "Ember": {
        "gestures": ["swipe_right"],
        "aliases": ["ember", "flame", "coal"],
        "cmd": {"cmd": "led", "r": 255, "g": 40, "b": 0},
        "lore": "Warm crimson wakes in the crystals — hearth-fire restless.",
        "element": "fire",
        "power": 2,
    },
    "Shield": {
        "gestures": ["circle"],
        "aliases": ["shield", "ward", "barrier"],
        "cmd": {"cmd": "led", "r": 180, "g": 220, "b": 255},
        "lore": "A pale ward hums around the grip — protect the bearer.",
        "element": "arcane",
        "power": 3,
    },
    "Pulse": {
        "gestures": ["tap", "button"],
        "aliases": ["pulse", "heartbeat", "thrum"],
        "cmd": {"cmd": "flash", "r": 200, "g": 80, "b": 255, "times": 2},
        "lore": "The core beats once — heartbeat of the wand itself.",
        "element": "arcane",
        "power": 1,
    },
    "Nova": {
        "gestures": ["flick_hard", "shake"],
        "aliases": ["nova", "star", "burst"],
        "cmd": {"cmd": "flash", "r": 255, "g": 255, "b": 255, "times": 4},
        "lore": "A white-hot burst — starlight compressed into a breath.",
        "element": "light",
        "power": 4,
    },
    "Mirage": {
        "gestures": ["figure8"],
        "aliases": ["mirage", "illusion", "haze"],
        "cmd": {"cmd": "led", "r": 160, "g": 60, "b": 220},
        "lore": "Soft violet haze — illusions dance at the edge of sight.",
        "element": "shadow",
        "power": 3,
    },
    "Thunder": {
        "gestures": ["stab", "thrust"],
        "aliases": ["thunder", "storm", "bolt"],
        "cmd": {"cmd": "flash", "r": 40, "g": 220, "b": 255, "times": 3},
        "lore": "A sharp cyan crackle — storm bottled in wood and wire.",
        "element": "storm",
        "power": 4,
    },
    "Extinguish": {
        "gestures": ["hold"],
        "aliases": ["off", "dark", "extinguish", "quiet"],
        "cmd": {"cmd": "led_off"},
        "lore": "Light folds inward. The shaft rests.",
        "element": "void",
        "power": 0,
    },
}


def _norm(name: str) -> str:
    return "".join(ch for ch in name.lower().strip() if ch.isalnum() or ch.isspace()).strip()


def spell_by_name(name: str) -> tuple[str, dict[str, Any]] | None:
    needle = _norm(name)
    if not needle:
        return None
    for title, data in SPELLBOOK.items():
        if _norm(title) == needle:
            return title, deepcopy(data)
        for alias in data.get("aliases", []):
            if _norm(alias) == needle:
                return title, deepcopy(data)
    # fuzzy contains
    for title, data in SPELLBOOK.items():
        if needle in _norm(title):
            return title, deepcopy(data)
        for alias in data.get("aliases", []):
            if needle in _norm(alias):
                return title, deepcopy(data)
    return None


def spell_by_gesture(gesture: str) -> tuple[str, dict[str, Any]] | None:
    g = gesture.strip().lower()
    for title, data in SPELLBOOK.items():
        if g in [x.lower() for x in data.get("gestures", [])]:
            return title, deepcopy(data)
    return None


def list_spells() -> list[dict[str, Any]]:
    out = []
    for title, data in SPELLBOOK.items():
        out.append(
            {
                "name": title,
                "gestures": data["gestures"],
                "aliases": data["aliases"],
                "element": data["element"],
                "power": data["power"],
                "lore": data["lore"],
            }
        )
    return out


def gesture_map() -> dict[str, str]:
    """gesture -> spell name"""
    mapping: dict[str, str] = {}
    for title, data in SPELLBOOK.items():
        for g in data.get("gestures", []):
            mapping[g] = title
    return mapping
