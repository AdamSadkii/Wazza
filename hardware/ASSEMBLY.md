# Wazza assembly instructions

## What you need

- Fabricated PCB from `hardware/gerbers/` (JLCPCB / PCBWay / similar)
- Enclosure STEP: `hardware/cad/Wand3.step`
- Parts from `BOM.md`
- USB-C cable, LiPo cell, 8 ohm speaker, NeoPixel strip (optional)

## Board fit

PCB outline is **155 mm × 26 mm** (rounded ends), sized to fit the Wand3 STEP mid-cavity (~51 × 169 mm usable) with wall clearance.  
Confirm fit in CAD before ordering a large panel.

## Solder order

1. SOT-23-5 parts U1 (MCP73831) and U2 (AP2112K-3.3)  
2. 0805 passives (R1–R3, R10, R13–R15, C1, C3, C4)  
3. QFN amp U12 (MAX98357A) and IMU U13  
4. WS2812B (D1)  
5. Buttons SW2 / SW3  
6. USB-C receptacle J1  
7. ESP32-S3-WROOM-1 module U9 (watch antenna keepout, no copper under antenna)  
8. Headers: battery BT1, OLED U14, speaker LS1, mic MK2, LED strip J2  

## First power-up

1. No battery yet. USB-C only.  
2. Check +3V3 to GND is about 3.3 V.  
3. Measure no shorts on VBUS / VBAT / +3V3.  
4. Flash firmware (`firmware/`, PlatformIO env `wazza_s3`).  
5. Connect battery only after 3.3 V rail looks good.  

## Enclosure

1. Import `hardware/cad/Wand3.step` into your CAD tool.  
2. Seat PCB in the pocket with USB-C at the handle opening.  
3. Route speaker / mic / LED strip wires to the tip cavity.  
4. Close shell; keep antenna end clear of metal.

## Wiring reference

See `hardware/WIRING.md` and `hardware/wiring/wazza_schematic.pdf`.

## Accuracy note

Original GitHub journal had PCB screenshots, not the source `.kicad_pcb`.  
This board recreates that placement and STEP fit. Full copper routing still needs a pass in KiCad before a production spin.
