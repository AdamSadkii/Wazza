# Wazza backend

import asyncio
import http.server
import json
import threading
from functools import partial
from pathlib import Path

import websockets

from ai import ask_ai

WS_PORT = 8765
HTTP_PORT = 8000
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

wand = None
dashboards = set()

# Spells
SPELLS = {
    "flick": {"name": "Sparks", "cmd": {"cmd": "flash", "r": 255, "g": 180, "b": 0, "times": 3}},
    "swipe_left": {"name": "Frost", "cmd": {"cmd": "led", "r": 0, "g": 120, "b": 255}},
    "swipe_right": {"name": "Ember", "cmd": {"cmd": "led", "r": 255, "g": 40, "b": 0}},
}


def oled_lines(text: str):
    words = text.split()
    line1, line2 = "", ""
    for w in words:
        if len(line1) + len(w) < 21:
            line1 = f"{line1} {w}".strip()
        elif len(line2) + len(w) < 21:
            line2 = f"{line2} {w}".strip()
        else:
            break
    return line1, line2


async def broadcast_dashboards(message: dict):
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


async def ai_respond(prompt: str, source: str):
    reply = await ask_ai(prompt)
    line1, line2 = oled_lines(reply)
    await send_to_wand({"cmd": "oled", "line1": line1, "line2": line2})
    await broadcast_dashboards({"type": "ai", "prompt": prompt, "reply": reply, "source": source})


async def handle_wand_message(msg: dict):
    if msg.get("type") == "gesture":
        spell = SPELLS.get(msg.get("value"))
        if spell:
            await send_to_wand(spell["cmd"])
            msg["spell"] = spell["name"]
            asyncio.create_task(
                ai_respond(f"The wizard cast {spell['name']} with a {msg['value']} gesture.", "gesture")
            )
    await broadcast_dashboards(msg)


# WebSocket
async def handler(ws):
    global wand
    role = "dashboard"
    dashboards.add(ws)
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "hello" and msg.get("value") == "wazza-wand":
                role = "wand"
                wand = ws
                dashboards.discard(ws)
                await broadcast_dashboards({"type": "status", "wand": "online"})
                print("Wand connected")
                continue

            if role == "wand":
                await handle_wand_message(msg)
            elif msg.get("type") == "prompt" and msg.get("text"):
                asyncio.create_task(ai_respond(msg["text"], "dashboard"))
            elif "cmd" in msg:
                await send_to_wand(msg)
    finally:
        dashboards.discard(ws)
        if ws is wand:
            wand = None
            await broadcast_dashboards({"type": "status", "wand": "offline"})
            print("Wand disconnected")


# HTTP
def serve_frontend():
    handler_cls = partial(
        http.server.SimpleHTTPRequestHandler, directory=str(FRONTEND_DIR)
    )
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), handler_cls)
    print(f"Dashboard:  http://localhost:{HTTP_PORT}")
    httpd.serve_forever()


async def main():
    threading.Thread(target=serve_frontend, daemon=True).start()
    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        print(f"WebSocket:  ws://0.0.0.0:{WS_PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye")
