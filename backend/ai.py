"""
Wazza AI facade.

Keeps the old `ask_ai(prompt)` API working, and exposes the full agent.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from agent.core import AgentReply, WazzaAgent, get_agent
from agent.providers import active_provider, healthcheck
from agent.spellbook import SPELLBOOK, list_spells, spell_by_gesture, spell_by_name

SendFn = Callable[[dict[str, Any]], Awaitable[None]]


async def ask_ai(prompt: str) -> str:
    """Backward-compatible one-shot ask (no wand side effects beyond OLED)."""
    agent = get_agent()
    reply = await agent.handle_prompt(prompt, source="legacy")
    return reply.text


async def ask_agent(
    prompt: str,
    source: str = "dashboard",
    send_wand: SendFn | None = None,
) -> AgentReply:
    agent = get_agent(send_wand)
    return await agent.handle_prompt(prompt, source=source)


def bind_wand_sender(send_wand: SendFn) -> WazzaAgent:
    return get_agent(send_wand)


__all__ = [
    "ask_ai",
    "ask_agent",
    "bind_wand_sender",
    "get_agent",
    "WazzaAgent",
    "AgentReply",
    "SPELLBOOK",
    "list_spells",
    "spell_by_gesture",
    "spell_by_name",
    "active_provider",
    "healthcheck",
]
