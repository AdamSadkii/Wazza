# Wazza - Magic in The Air

Wazza is a fully open-source, gesture-controlled AI wand that translates physical hand motions into real-time digital commands. By tracking movement via an internal MPU-6050 6-axis IMU, the onboard ESP32-S3 Mini microcontroller processes gesture vectors, coordinates peripheral systems, and streams telemetry data to an onboard OLED screen alongside audio feedback through an integrated I2S speaker interface.

## Key Features

- 1 x ESP32-S3-MINI-1 Microcontroller (Main Brain)
- 1 x MPU-6050 6-Axis Motion Sensor (IMU)
- 1 x MAX98357A I2S Audio Amplifier & 2W Speaker
- 1 x SPH0645 I2S MEMS Microphone
- 1 x 18650 LiPo Battery Cell
- 1 x TP4056 USB-C Battery Charger Module
- 1 x Tactile Push Button (Momentary switch)
- 1 x WS2812B RGB LED Strip (15-20 LEDs)
- 10 x Resistors (For the required I2C data/clock pull-ups)
- 3 x Electrolytic Capacitors

## How to get the code (not on Vercel)

This is not hosted on Vercel. You grab it from GitHub and run it on your PC.

1. Go to https://github.com/AdamSadkii/Wazza
2. Hit the green Code button
3. Click Download ZIP (or clone it if you use git)
4. Unzip it
5. Open the folder in VS Code / Cursor (or open `Wazza.code-workspace`)

Folders you care about:
- `frontend/` = dashboard
- `backend/` = python server + AI
- `firmware/` = ESP32 code

## Run it on your PC

1. Open a terminal in `backend`
2. Make a venv: `python -m venv .venv`
3. Activate it: `.\.venv\Scripts\Activate.ps1`
4. Install deps: `pip install -r requirements.txt`
5. Run it: `python server.py`
6. Open http://localhost:8000 in your browser

Optional AI:
- set `OPENAI_API_KEY` or run Ollama locally

## Flash the wand

1. Copy `firmware/src/secrets.example.h` to `firmware/src/secrets.h`
2. Put your wifi name/password in there
3. Put your PC IP in `BACKEND_HOST` (port 8765)
4. Open `firmware/` in PlatformIO
5. Build + upload to the ESP32-S3
6. Keep `python server.py` running so the wand can connect

## Schematic

<img width="711" height="301" alt="image" src="https://github.com/user-attachments/assets/1569244d-4e65-4fde-bfbe-05a0b9a3806f" />
<img width="802" height="427" alt="image" src="https://github.com/user-attachments/assets/81efa213-27a1-4943-a675-421c33ea0701" />
<img width="796" height="388" alt="image" src="https://github.com/user-attachments/assets/ba185da1-e040-45e8-b859-ee668cf3fa19" />
<img width="586" height="562" alt="image" src="https://github.com/user-attachments/assets/6b969f1c-960b-40bd-b3f9-83a89c678b7d" />
<img width="402" height="288" alt="image" src="https://github.com/user-attachments/assets/c82b7383-9072-4c87-ab0c-248d76ed9dbc" />
<img width="743" height="483" alt="image" src="https://github.com/user-attachments/assets/945cc301-dc71-436d-98f5-64e68c29ae68" />

The schematic composes a well organized layout of each system in the device, ranging from power management to the microcontroller itself. This lays the ideal blueprint for the PCB.

The power system (powered by a USB-C component, is the base component of the whole project. A user plugs in a wire in order to actually connect to the code itself, and allow the Ai to run within itself. That way the user can just prompt using the commanded gestures it follows.

## PCB

<img width="1043" height="316" alt="image" src="https://github.com/user-attachments/assets/0a058ee3-334f-4758-b856-4e73d7dcc238" />
<img width="922" height="218" alt="image" src="https://github.com/user-attachments/assets/4057eefd-50d1-4266-bf20-1f22564cc0ae" />


## Future Enhancements

Potential improvements include on-device machine learning for gesture recognition to reduce API latency, integration with additional sensors like IMUs or proximity detectors, wireless charging capability, and support for custom gesture training. The modular design allows for easy hardware upgrades without redesigning the entire system.

## Files and Documentation

The project includes complete KiCAD schematic files organized by functional module, PCB layout files for fabrication, Arduino firmware source code with gesture templates, and assembly instructions with wiring diagrams. All code is open source and available for modification and redistribution.

## CADDED Module

<img width="1037" height="531" alt="image" src="https://github.com/user-attachments/assets/d108678b-4a3c-4225-8fda-f0c08227013a" />

## Thank you.
A big thanks to Nesh, Keam, and Yahya for being part of the process the whole way. Without them I don't think I would've been able to make it as far.
deduct 2 hrs

## License: MIT

Copyright 2026

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
