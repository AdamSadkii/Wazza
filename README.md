# Wazza — Gesture-Controlled AI Wand

Firmware + software for **Wazza**, an ESP32-based magic wand with motion gestures,
an OLED display, addressable LEDs, and audio — paired with a Python AI backend
and a live web dashboard.

## Hardware (matches the `k` KiCad board)

| Part | Chip | Connection |
|------|------|------------|
| MCU | ESP32 module (U9) | — |
| IMU | MPU-6050 (U13) | I2C — SDA=IO21, SCL=IO5 |
| Display | 0.91" OLED SSD1306 128x32 (U14) | I2C (shared bus) |
| LED | WS2812B (D1) + strip header (J2) | IO16 |
| Buttons | SW3 (boot) IO0, SW2 (action) IO4 | active-low |
| Amp | MAX98357A I2S (U12) | BCLK=IO15, LRCLK=IO26, DIN=IO33 |
| Mic | SPH0645 I2S (MK2/MK3) | DOUT=IO35 (shares BCLK/LRCLK) |
| Power | LiPo + MCP73831 charger + AP2112K 3.3V LDO | — |

All pins live in `firmware/src/config.h` — change them there if the board revs.

## Repo layout

```
wazza/
  firmware/   ESP32 firmware (PlatformIO, Arduino framework)
  backend/    Python WebSocket server (gesture AI + wand control)
  frontend/   Web dashboard (plain HTML/JS, no build step)
```

## Quick start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python server.py
```

Runs a WebSocket server on `ws://0.0.0.0:8765` and serves the dashboard
on `http://localhost:8000`.

### 2. Frontend

Open `http://localhost:8000` in a browser (served by the backend), or open
`frontend/index.html` directly.

### 3. Firmware

1. Install [PlatformIO](https://platformio.org/) (VS Code extension or CLI).
2. Copy `firmware/src/secrets.example.h` to `firmware/src/secrets.h` and fill in
   your Wi-Fi credentials and the backend's IP address.
3. Build & flash:

```bash
cd firmware
pio run -t upload
pio device monitor
```

## How it works

```
[Wand: ESP32] --IMU samples / gesture events--> [Backend: Python WS server]
      ^                                                 |
      |<---- commands (LED color, OLED text) -----------|
                                                        |
[Dashboard: browser] <---- live telemetry + control ----+
```

- The wand streams IMU data and locally-detected gestures (flick, swipe, circle)
  over WebSocket.
- The backend interprets gestures into "spells", pushes LED/OLED commands back,
  and relays everything to the dashboard.
- The dashboard shows live motion data and lets you trigger effects manually.
