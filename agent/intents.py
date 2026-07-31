"""Intent parsing — rule-based first, LLM classifier fallback."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from typing import Any

from . import providers
from .prompts import INTENT_CLASSIFIER
from .spellbook import SPELLBOOK, spell_by_name
from .tools import hex_to_rgb

COLOR_WORDS = {
    "red": "#ff0000",
    "green": "#00ff00",
    "blue": "#0080ff",
    "gold": "#ffb400",
    "purple": "#a78bfa",
    "white": "#ffffff",
    "cyan": "#28e0ff",
    "orange": "#ff6a00",
    "pink": "#ff6bcb",
    "violet": "#a020f0",
}

MOODS = {"calm", "playful", "fierce", "sleepy", "curious"}


@dataclass
class Intent:
    intent: str
    spell_name: str | None = None
    color_hex: str | None = None
    mood: str | None = None
    raw: str = ""
    confidence: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CAST_RE = re.compile(
    r"\b(?:cast|use|invoke|fire|unleash)\s+(?:the\s+)?([a-zA-Z][\w\s-]{0,24})",
    re.I,
)
MOOD_RE = re.compile(r"\b(?:mood|vibe|mode)\s+(?:to\s+|as\s+)?([a-zA-Z]+)", re.I)
COLOR_HEX_RE = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
COLOR_WORD_RE = re.compile(
    r"\b(?:make|set|paint|glow|color|colour)\b.*\b("
    + "|".join(COLOR_WORDS.keys())
    + r")\b",
    re.I,
)
CLEAR_RE = re.compile(r"\b(?:clear|forget|reset)\b.*\b(?:memory|chat|history)\b", re.I)
HELP_RE = re.compile(r"^\s*(help|commands|\?)\s*$", re.I)
STATUS_RE = re.compile(r"\b(?:status|how are you|what(?:'s| is) your mood)\b", re.I)


def parse_intent_rules(text: str) -> Intent | None:
    raw = text.strip()
    if not raw:
        return Intent("unknown", raw=raw, confidence=0.0)

    if HELP_RE.search(raw):
        return Intent("help", raw=raw, confidence=0.95)
    if CLEAR_RE.search(raw):
        return Intent("clear_memory", raw=raw, confidence=0.9)
    if STATUS_RE.search(raw):
        return Intent("ask_status", raw=raw, confidence=0.85)

    m = MOOD_RE.search(raw)
    if m:
        mood = m.group(1).lower()
        if mood in MOODS:
            return Intent("set_mood", mood=mood, raw=raw, confidence=0.9)

    m = CAST_RE.search(raw)
    if m:
        found = spell_by_name(m.group(1))
        if found:
            return Intent("cast_spell", spell_name=found[0], raw=raw, confidence=0.92)

    # bare spell name
    found = spell_by_name(raw)
    if found and len(raw.split()) <= 3:
        return Intent("cast_spell", spell_name=found[0], raw=raw, confidence=0.8)

    hx = COLOR_HEX_RE.search(raw)
    if hx:
        return Intent("set_color", color_hex="#" + hx.group(1), raw=raw, confidence=0.88)

    cw = COLOR_WORD_RE.search(raw)
    if cw:
        word = cw.group(1).lower()
        return Intent("set_color", color_hex=COLOR_WORDS[word], raw=raw, confidence=0.86)

    for word, hexv in COLOR_WORDS.items():
        if re.search(rf"\bturn\s+(?:it\s+)?{word}\b", raw, re.I):
            return Intent("set_color", color_hex=hexv, raw=raw, confidence=0.84)

    return None


async def classify_intent(text: str, use_llm: bool = True) -> Intent:
    ruled = parse_intent_rules(text)
    if ruled and ruled.confidence >= 0.8:
        return ruled

    if not use_llm:
        return ruled or Intent("chat", raw=text, confidence=0.55)

    try:
        reply = await providers.chat(
            [
                {"role": "system", "content": INTENT_CLASSIFIER},
                {"role": "user", "content": text},
            ],
            max_tokens=60,
            temperature=0,
        )
        data = _extract_json(reply)
        intent = Intent(
            intent=str(data.get("intent") or "chat"),
            spell_name=data.get("spell_name"),
            color_hex=data.get("color_hex"),
            mood=data.get("mood"),
            raw=text,
            confidence=0.7,
        )
        if intent.spell_name:
            found = spell_by_name(intent.spell_name)
            intent.spell_name = found[0] if found else None
            if not intent.spell_name and intent.intent == "cast_spell":
                intent.intent = "chat"
        if intent.mood and intent.mood not in MOODS:
            intent.mood = None
        if intent.color_hex and not hex_to_rgb(intent.color_hex):
            intent.color_hex = None
        return intent
    except Exception:  # noqa: BLE001
        return ruled or Intent("chat", raw=text, confidence=0.5)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def spell_catalog_hint() -> str:
    names = ", ".join(SPELLBOOK.keys())
    return f"Known spells: {names}."
