// MAIN AI WAND BRAIN.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from . import providers
from .intents import intent, classify_intent, spell_catalog_hint
from .memory import WandMemory
from .personality import Personality
from .prompts import build_system_prompt, gesture_prompt, help_text
from .safety import RateLimiter, clamp_reply, scrub_user_text
from .sessio import SessionState
from .spellbook import list_spells, spell_by_gesture, spell_by_name
from .tools import WandToolKit, extract_action_json, hex_to_rgb

SendFn = Callable[[dict[str, Any]], Awaitable[None]]

@dataclass
class AgentReply:
    text: str
    source: str
    intent: str = "chat"
    spell: str | None = None
    tool: dict[str, Any] | None = None
    mood: str = "playful"
    provider: str = "ollama" 
    latency_ms: int = 0

    def to_event(self, prompt: str = "") -> dict[str, Any]:
        return {
            "type": "ai",
            "prompt": prompt,
            "reply": self.text,
            "source": self.source,
            "intent": self.intent, 
            "spell": self.spell,
            "tool": self.tool,
            "mood": self.mood,
            "provider": self.provider,
            "latency_ms": self.latency_ms,
        }

@dataclass
class WazzaAgent:
    send_wand: SendFn
    memory: WandMemory = field(default_factory=WandMemory)
    personality: Personality = field(default_factory=Personality)
    session: SessionState = field(default_factory = SessionState)
    limiter: RateLimiter = field(default_factory = lambda: RateLimiter(30, 60))
    use_lim_intent: bool = True

    def __post_init__(self) -> None:
        self.tools = WandToolKit(self.send_wand)

        // API

async def handle_prompt(self, text: str, source: str = "dashboard") -> AgentReply:
        t0 = time.perf_counter()
        safe = scrub_user_text(text)
        if not safe.ok:
             return self._reply(
                  "The wand refuses that whisper.",
                  source,
                  intent = "blocked",
                  t0 = t0,
             )
        if not self.limiter.allow():
             return self._reply(
                  "Too many spells at once - let it cool.",
                  source,
                  intent ="rate_limited",
                  t0=t0,
             )

        intent = await classify_intent(safe.cleaned, use_llm=self.use_lim_intent)
        self.memory.add_turn("user", safe.cleaned, source=source, intent=intent.intent)
        self.personality.on_chat()
        self.session.note_ai("")

        if intent.intent=="help":
             text_out =  help_text() + " " + spell_catalog_hint()
             return await self._finish(text_out, source, intent, t0)

        if intent.intent == "clear_memory":
             self.memory.clear_chat()
             return await self._finish("Chat mist cleared. I still remember our bond.", source, intent, t0)

        if intent.intent=="ask status":
             text_out = self.personality.status_line()
             if self.session.wand_online:
                  text_out += " The shaft is awake."
            else:
                  text_out += " The shaft is offline."
            return await self._finish(text_out, source, intent, t0)

        if intent.intent == "set_mood" and intent.mood:
             self.personality.set_mood(intent.mood)
             return await self._finish(
                  f"Mood shifted to {intent.mood}.",
                  source,
                  intent,
                  t0,
             )

        if intent.intent == "set_color" and intent.color_hex:
             rgb = hex_to_rgb(intent.color_hex)
             tool = None
             if rgb:
                  result = await self.tools.led(*rgb)
                  tool = {"action": result.action, "detail": result.detail, "cmd": result.cmd}
            narr = await self._lim_chat(
                 f"The wizard painted the wand {intent.color_hex}. React briefly."
            )
            return await self._finish(narr, source, intent, t0, tool=tool)

        if intent.intent == "cast_spell" and intent.spell_name:
             return await self._cast_and_narrate(intent.spell_name, source, intent, t0, via="voice")

        # default: conversational LLM with memory + optional tool JSON
        reply = await self._llm_chat(safe.cleaned)
        cleaned,action = extract_action_json(reply)
        tool = None
        if action:
             result = await self.tools.apply_action_dict(action)
             tool = {"action": result.action, "detail": result.detail, "ok": result.ok, "cmd": result.cmd}

