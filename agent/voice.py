"""Optional voice / transcript helpers for future mic pipeline.

The firmware already has I2S mic pins; this module prepares prompt
building from speech transcripts once audio→text is wired up.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field


WAKE_WORDS = ("hey wazza", "ok wazza", "wazza", "listen wand")


@dataclass
class TranscriptChunk:
    text: str
    confidence: float = 1.0
    ts: float = field(default_factory=time.time)
    is_final: bool = True


def normalize_transcript(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9#\s\-']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_wake_word(text: str) -> tuple[bool, str]:
    norm = normalize_transcript(text)
    for wake in WAKE_WORDS:
        if norm.startswith(wake):
            return True, norm[len(wake) :].strip(" ,.-")
        if wake in norm:
            # allow mid-utterance wake
            idx = norm.find(wake)
            return True, norm[idx + len(wake) :].strip(" ,.-")
    return False, norm


def transcript_to_prompt(chunk: TranscriptChunk, require_wake: bool = False) -> str | None:
    if chunk.confidence < 0.35:
        return None
    woke, body = strip_wake_word(chunk.text)
    if require_wake and not woke:
        return None
    body = body.strip()
    return body or None


def is_noise(text: str) -> bool:
    norm = normalize_transcript(text)
    if len(norm) < 2:
        return True
    if norm in {"uh", "um", "ah", "hmm", "huh"}:
        return True
    return False
