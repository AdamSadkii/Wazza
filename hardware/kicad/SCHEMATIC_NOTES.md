# Wazza KiCad schematic notes

## What this is
Reconstructed KiCad 10 project from:
- GitHub journal schematic screenshots (Journalphotos.md)
- BOM.md reference designators
- Final hierarchical sheet labels (SDA/SCL/I2S_*/AMP_DIN/MIC_DOUT)

## Open in KiCad
1. Install KiCad 10
2. File -> Open Project -> `hardware/kicad/wazza.kicad_pro`
3. Open `wazza.kicad_sch`

Sheets are wired like the GitHub journal screenshots: orthogonal wires between parts, power ports on pins, global labels at sheet edges.

## Accuracy limits
GitHub does **not** include original `.kicad_sch` sources. Recreation is from screenshots.

Known conflicts between journal revisions:
- Some sheets show I2C on IO21/IO26, others use different GPIOs
- Audio sheet pin annotations disagree across captures
- Early sheets shorted button logic onto SDA (not copied; buttons are separate nets here)
- OLED numbered U15 in one sheet, BOM says U14
- LED rail shown as +5V in one capture, +3V3 in another

This project uses one consolidated MCU map so the hierarchy ERC can resolve:
- IO4 SCL, IO5 SDA
- IO0 BTN_BOOT, IO8 BTN_ACTION
- IO18 LED_DIN
- IO21 I2S_LRCLK, IO26 I2S_BCLK, IO33 AMP_DIN, IO34 MIC_DOUT

Power sheet topology matches the clear USB-C / MCP73831 / battery / AP2112K screenshot.

## Not included
- Full ESP32-S3-MINI-1 pinout (only used pins modeled)
- Exact PCB footprints for every connector
- Layout (`.kicad_pcb`) - ask if you want that next from screenshots

## Sheets
1. `01_power.kicad_sch`
2. `02_mcu.kicad_sch`
3. `03_sensors.kicad_sch`
4. `04_audio.kicad_sch`
5. `05_leds_buttons.kicad_sch`
