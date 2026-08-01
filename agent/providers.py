"""LLM provider adapters — OpenAI and Ollama."""

from __future__ import annotations

import os
from typing import Any

import httpx

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
MAX_TOKENS = int(os.environ.get("WAZZA_MAX_TOKENS", "160"))
TEMPERATURE = float(os.environ.get("WAZZA_TEMPERATURE", "0.8"))


class ProviderError(RuntimeError):
    pass


def active_provider() -> str:
    return "openai" if OPENAI_KEY else "ollama"


async def chat(
    messages: list[dict[str, str]],
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """Send a chat completion to the configured provider."""
    max_tokens = max_tokens if max_tokens is not None else MAX_TOKENS
    temperature = temperature if temperature is not None else TEMPERATURE
    try:
        if OPENAI_KEY:
            return await _openai(messages, max_tokens, temperature)
        return await _ollama(messages, max_tokens, temperature)
    except Exception as exc:  # noqa: BLE001 — surface soft failure to wand
        raise ProviderError(f"{active_provider()} failed: {type(exc).__name__}: {exc}") from exc


async def _openai(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(
            f"{OPENAI_BASE.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            json={
                "model": OPENAI_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data["choices"][0]["message"]["content"].strip()


async def _ollama(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            f"{OLLAMA_URL.rstrip('/')}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data["message"]["content"].strip()


async def healthcheck() -> dict[str, Any]:
    """Quick reachability probe for the active provider."""
    provider = active_provider()
    try:
        reply = await chat(
            [
                {"role": "system", "content": "Reply with the single word: ok"},
                {"role": "user", "content": "ping"},
            ],
            max_tokens=8,
            temperature=0,
        )
        return {"ok": True, "provider": provider, "sample": reply[:40]}
    except ProviderError as exc:
        return {"ok": False, "provider": provider, "error": str(exc)}
