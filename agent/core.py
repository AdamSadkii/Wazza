"""WazzaAgent — main AI wand brain."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from . import providers
from .intents import Intent, classify_intent, spell_catalog_hint
from .memory import WandMemory
from .personality import Personality
from .prompts import build_system_prompt, gesture_prompt, help_text
from .safety import RateLimiter, clamp_reply, scrub_user_text
from .session import SessionState
from .spellbook import list_spells, spell_by_gesture, spell_by_name
from .tools import WandToolkit, extract_action_json, hex_to_rgb

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
    session: SessionState = field(default_factory=SessionState)
    limiter: RateLimiter = field(default_factory=lambda: RateLimiter(30, 60))
    use_llm_intent: bool = True

    def __post_init__(self) -> None:
        self.tools = WandToolkit(self.send_wand)

    # ---------- public API ----------

    async def handle_prompt(self, text: str, source: str = "dashboard") -> AgentReply:
        t0 = time.perf_counter()
        safe = scrub_user_text(text)
        if not safe.ok:
            return self._reply(
                "The wand refuses that whisper.",
                source,
                intent="blocked",
                t0=t0,
            )
        if not self.limiter.allow():
            return self._reply(
                "Too many spells at once — let the tip cool.",
                source,
                intent="rate_limited",
                t0=t0,
            )

        intent = await classify_intent(safe.cleaned, use_llm=self.use_llm_intent)
        self.memory.add_turn("user", safe.cleaned, source=source, intent=intent.intent)
        self.personality.on_chat()
        self.session.note_ai("")  # count prompt; reply filled below

        if intent.intent == "help":
            text_out = help_text() + " " + spell_catalog_hint()
            return await self._finish(text_out, source, intent, t0)

        if intent.intent == "clear_memory":
            self.memory.clear_chat()
            return await self._finish("Chat mist cleared. I still remember our bond.", source, intent, t0)

        if intent.intent == "ask_status":
            text_out = self.personality.status_line()
            if self.session.wand_online:
                text_out += " The shaft is awake."
            else:
                text_out += " The shaft is offline — dashboard only."
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
            narr = await self._llm_chat(
                f"The wizard painted the wand {intent.color_hex}. React briefly."
            )
            return await self._finish(narr, source, intent, t0, tool=tool)

        if intent.intent == "cast_spell" and intent.spell_name:
            return await self._cast_and_narrate(intent.spell_name, source, intent, t0, via="voice")

        # default: conversational LLM with memory + optional tool JSON
        reply = await self._llm_chat(safe.cleaned)
        cleaned, action = extract_action_json(reply)
        tool = None
        if action:
            result = await self.tools.apply_action_dict(action)
            tool = {"action": result.action, "detail": result.detail, "ok": result.ok, "cmd": result.cmd}
        return await self._finish(cleaned, source, intent, t0, tool=tool)

    async def handle_gesture(
        self,
        gesture: str,
        imu: dict[str, float] | None = None,
    ) -> AgentReply | None:
        t0 = time.perf_counter()
        found = spell_by_gesture(gesture)
        spell_name = found[0] if found else None
        self.memory.add_gesture(gesture, spell_name, imu)
        self.personality.on_gesture(gesture)
        self.session.note_gesture(gesture, spell_name)

        if not found:
            # unknown gesture — light acknowledgment, no spell
            if not self.limiter.allow():
                return None
            text = await self._llm_chat(
                f"The wizard moved the wand ({gesture}) but no known spell mapped. React briefly.",
                force_short=True,
            )
            intent = Intent("unknown_gesture", raw=gesture)
            return await self._finish(text, "gesture", intent, t0)

        title, data = found
        result = await self.tools.cast_spell(title)
        self.personality.on_spell(int(data.get("power", 1)))
        prompt = gesture_prompt(title, gesture, data.get("lore"))
        text = await self._llm_narrate_gesture(prompt)
        tool = {"action": result.action, "detail": result.detail, "cmd": result.cmd}
        intent = Intent("cast_spell", spell_name=title, raw=gesture, confidence=1.0)
        return await self._finish(text, "gesture", intent, t0, tool=tool, spell=title)

    async def cast_named(self, name: str, source: str = "dashboard") -> AgentReply:
        t0 = time.perf_counter()
        intent = Intent("cast_spell", spell_name=name, raw=name, confidence=1.0)
        return await self._cast_and_narrate(name, source, intent, t0, via="manual")

    def status(self) -> dict[str, Any]:
        return {
            "provider": providers.active_provider(),
            "personality": self.personality.snapshot(),
            "session": self.session.snapshot(),
            "memory": {
                "turns": len(self.memory.turns),
                "gestures": len(self.memory.gestures),
                "spells": len(self.memory.spell_casts),
                "facts": dict(self.memory.facts),
                "summary": self.memory.summary_blob(),
            },
            "spells": list_spells(),
            "rate_remaining": self.limiter.remaining(),
        }

    # ---------- internals ----------

    async def _cast_and_narrate(
        self,
        name: str,
        source: str,
        intent: Intent,
        t0: float,
        via: str,
    ) -> AgentReply:
        found = spell_by_name(name)
        if not found:
            return await self._finish(f"I know no spell called {name}.", source, intent, t0)
        title, data = found
        result = await self.tools.cast_spell(title)
        self.personality.on_spell(int(data.get("power", 1)))
        self.memory.add_gesture(via, title)
        self.session.note_gesture(via, title)
        narr = await self._llm_narrate_gesture(
            gesture_prompt(title, via, data.get("lore"))
        )
        tool = {"action": result.action, "detail": result.detail, "cmd": result.cmd}
        return await self._finish(narr, source, intent, t0, tool=tool, spell=title)

    async def _llm_chat(self, user_text: str, force_short: bool = False) -> str:
        system = build_system_prompt(self.personality.mood, tools=True)
        messages = [{"role": "system", "content": system}]
        summary = self.memory.summary_blob()
        messages.append(
            {
                "role": "system",
                "content": f"Session notes: {summary} Personality: {self.personality.status_line()}",
            }
        )
        messages.extend(self.memory.recent_messages(10))
        messages.append({"role": "user", "content": user_text})
        try:
            raw = await providers.chat(
                messages,
                max_tokens=60 if force_short else 160,
                temperature=0.85,
            )
            return clamp_reply(raw)
        except providers.ProviderError as exc:
            return f"(the wand is silent: {exc})"

    async def _llm_narrate_gesture(self, prompt: str) -> str:
        system = build_system_prompt(self.personality.mood, tools=False)
        try:
            raw = await providers.chat(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=70,
                temperature=0.9,
            )
            return clamp_reply(raw)
        except providers.ProviderError as exc:
            return f"(the wand shivers: {exc})"

    async def _finish(
        self,
        text: str,
        source: str,
        intent: Intent,
        t0: float,
        tool: dict[str, Any] | None = None,
        spell: str | None = None,
    ) -> AgentReply:
        text = clamp_reply(text)
        self.memory.add_turn("assistant", text, source=source, intent=intent.intent)
        self.session.last_ai_reply = text
        # push short OLED preview
        line1, line2 = _oled_lines(text)
        try:
            await self.tools.oled(line1, line2)
        except Exception:  # noqa: BLE001
            pass
        reply = AgentReply(
            text=text,
            source=source,
            intent=intent.intent,
            spell=spell or intent.spell_name,
            tool=tool,
            mood=self.personality.mood,
            provider=providers.active_provider(),
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )
        return reply

    def _reply(
        self,
        text: str,
        source: str,
        intent: str,
        t0: float,
    ) -> AgentReply:
        return AgentReply(
            text=text,
            source=source,
            intent=intent,
            mood=self.personality.mood,
            provider=providers.active_provider(),
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )


def _oled_lines(text: str) -> tuple[str, str]:
    words = text.split()
    line1 = line2 = ""
    for w in words:
        if len(line1) + len(w) < 21:
            line1 = f"{line1} {w}".strip()
        elif len(line2) + len(w) < 21:
            line2 = f"{line2} {w}".strip()
        else:
            break
    return line1, line2


_agent: WazzaAgent | None = None


def get_agent(send_wand: SendFn | None = None) -> WazzaAgent:
    global _agent
    if _agent is None:
        if send_wand is None:
            async def _noop(_cmd: dict[str, Any]) -> None:
                return None

            send_wand = _noop
        _agent = WazzaAgent(send_wand=send_wand)
    elif send_wand is not None:
        _agent.send_wand = send_wand
        _agent.tools.send = send_wand
    return _agent
