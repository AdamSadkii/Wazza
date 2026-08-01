# Wazza backend — WebSocket bridge + AI wand agent

import asyncio
import http.server
import json
import threading
from functools import partial
from pathlib import Path

import websockets

from ai import bind_wand_sender, get_agent, healthcheck, list_spells
from event_store import EventStore
from imu_buffer import ImuBuffer
from logging_setup import setup_logging
from protocol import validate_inbound

WS_PORT = 8765
HTTP_PORT = 8000
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

log = setup_logging()
imu_buf = ImuBuffer()
events = EventStore()

wand = None
dashboards = set()


async def broadcast_dashboards(message: dict):
    events.add(message)
    if not dashboards:
        return
    data = json.dumps(message)
    await asyncio.gather(
        *(ws.send(data) for ws in dashboards), return_exceptions=True
    )


async def send_to_wand(command: dict):
    if wand is not None:
        try:
            await wand.send(json.dumps(command))
        except websockets.ConnectionClosed:
            pass


# Bind agent → wand output once at import/startup helpers
agent = bind_wand_sender(send_to_wand)


async def emit_ai_reply(reply, prompt: str = ""):
    event = reply.to_event(prompt)
    await broadcast_dashboards(event)


async def ai_respond(prompt: str, source: str):
    reply = await agent.handle_prompt(prompt, source=source)
    await emit_ai_reply(reply, prompt)


async def handle_wand_message(msg: dict):
    mtype = msg.get("type")

    if mtype == "imu":
        agent.session.update_imu(msg)
        imu_buf.add(msg)
        await broadcast_dashboards(msg)
        return

    if mtype == "gesture":
        gesture = msg.get("value") or ""
        reply = await agent.handle_gesture(gesture, imu=agent.session.last_imu)
        if reply and reply.spell:
            msg["spell"] = reply.spell
        await broadcast_dashboards(msg)
        if reply:
            await emit_ai_reply(reply, prompt=f"gesture:{gesture}")
        return

    if mtype == "button":
        # Map action button → Pulse spell narration
        value = msg.get("value")
        await broadcast_dashboards(msg)
        if value == "action":
            reply = await agent.cast_named("Pulse", source="button")
            await emit_ai_reply(reply, prompt="button:action")
        return

    await broadcast_dashboards(msg)


async def handle_dashboard_message(msg: dict):
    mtype = msg.get("type")

    if mtype == "prompt" and msg.get("text"):
        asyncio.create_task(ai_respond(msg["text"], "dashboard"))
        return

    if mtype == "cast" and msg.get("spell"):
        reply = await agent.cast_named(msg["spell"], source="dashboard")
        await emit_ai_reply(reply, prompt=f"cast:{msg['spell']}")
        return

    if mtype == "mood" and msg.get("value"):
        ok = agent.personality.set_mood(str(msg["value"]))
        await broadcast_dashboards(
            {
                "type": "agent_status",
                "ok": ok,
                "status": agent.status(),
            }
        )
        return

    if mtype == "clear_memory":
        agent.memory.clear_chat()
        await broadcast_dashboards({"type": "agent_status", "status": agent.status()})
        return

    if mtype == "get_status":
        await broadcast_dashboards({"type": "agent_status", "status": agent.status()})
        return

    if mtype == "list_spells":
        await broadcast_dashboards({"type": "spellbook", "spells": list_spells()})
        return

    if mtype == "health":
        result = await healthcheck()
        await broadcast_dashboards({"type": "ai_health", **result})
        return

    if "cmd" in msg:
        await send_to_wand(msg)


async def handler(ws):
    global wand
    role = "dashboard"
    dashboards.add(ws)
    try:
        # greet dashboard with agent snapshot
        await ws.send(
            json.dumps(
                {
                    "type": "agent_status",
                    "status": get_agent().status(),
                    "wand": "online" if wand is not None else "offline",
                }
            )
        )
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not validate_inbound(msg):
                continue

            if msg.get("type") == "hello" and msg.get("value") == "wazza-wand":
                role = "wand"
                wand = ws
                dashboards.discard(ws)
                agent.session.mark_wand(True)
                await broadcast_dashboards({"type": "status", "wand": "online"})
                log.info("Wand connected")
                continue

            if role == "wand":
                await handle_wand_message(msg)
            else:
                await handle_dashboard_message(msg)
    finally:
        dashboards.discard(ws)
        if ws is wand:
            wand = None
            agent.session.mark_wand(False)
            await broadcast_dashboards({"type": "status", "wand": "offline"})
            log.info("Wand disconnected")


def serve_frontend():
    handler_cls = partial(
        http.server.SimpleHTTPRequestHandler, directory=str(FRONTEND_DIR)
    )
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), handler_cls)
    log.info("Dashboard: http://localhost:%s", HTTP_PORT)
    httpd.serve_forever()


async def idle_personality_decay():
    while True:
        await asyncio.sleep(45)
        agent.personality.decay()


async def main():
    threading.Thread(target=serve_frontend, daemon=True).start()
    asyncio.create_task(idle_personality_decay())
    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        log.info("WebSocket: ws://0.0.0.0:%s", WS_PORT)
        log.info("AI provider: %s", agent.status()["provider"])
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bye")
