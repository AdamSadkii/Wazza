# Wazza hardware wiring

Source of truth for nets: KiCad schematics in `hardware/kicad/`.
PDF export: `hardware/wiring/wazza_schematic.pdf`.

## Consolidated MCU map (matches firmware)

| Net | ESP32-S3 pin | Goes to |
|-----|--------------|---------|
| SCL | IO4 | MPU-6050, OLED, 4.7k pull-up to +3V3 |
| SDA | IO5 | MPU-6050, OLED, 4.7k pull-up to +3V3 |
| BTN_BOOT | IO0 | SW3 to GND, 10k pull-up to +3V3 |
| BTN_ACTION | IO8 | SW2 to GND, 10k pull-up to +3V3 |
| LED_DIN | IO18 | WS2812B DIN, then DOUT to strip header J2 |
| I2S_LRCLK | IO21 | MAX98357A LRCLK, mic WS |
| I2S_BCLK | IO26 | MAX98357A BCLK, mic BCLK |
| AMP_DIN | IO33 | MAX98357A DIN |
| MIC_DOUT | IO34 | SPH0645 DATA |
| +3V3 / GND | module rails | all ICs |

## Power path

USB-C VBUS -> MCP73831 -> VBAT / LiPo -> AP2112K-3.3 -> +3V3  
CC1/CC2 each have 5.1k to GND. PROG uses 2k to GND.

## Sheet map

1. `01_power` – USB-C, charger, battery, 3.3V LDO  
2. `02_mcu` – ESP32-S3 module + GPIO globals  
3. `03_sensors` – MPU-6050 + OLED + I2C pull-ups  
4. `04_audio` – MAX98357A + mic + speaker  
5. `05_leds_buttons` – WS2812B, strip header, buttons  

## Fabrication outputs

Gerbers + drill: `hardware/gerbers/`  
PCB preview: `hardware/wiring/pcb_preview.png`
