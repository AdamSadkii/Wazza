# Wazza — Bill of Materials

All parts as placed on the Wazza PCB (KiCad refs included).

## Main Components

- **ESP32-S3-MINI-1-N8** (U9): Wi-Fi + BLE MCU module, main brain. Qty 1. [LCSC](https://www.lcsc.com/product-detail/WiFi-Modules_Espressif-Systems-ESP32-S3-MINI-1-N8_C2913206.html) or [Espressif](https://www.espressif.com/en/module/esp32-s3-mini-1-en)
- **MPU-6050** (U13): 6-axis IMU (accelerometer + gyro) for gesture tracking. Qty 1. [Adafruit](https://www.adafruit.com/product/3886)
- **SSD1306 OLED 0.91"** (U14): 128x32 I2C display. Qty 1. [Adafruit](https://www.adafruit.com/product/931)
- **MAX98357A** (U12): I2S 3W Class-D audio amplifier. Qty 1. [Adafruit](https://www.adafruit.com/product/3006)
- **SPH0645LM4H** (MK2/MK3): I2S MEMS microphone, populate one only. Qty 1. [Adafruit](https://www.adafruit.com/product/3421)
- **MCP73831-2** (U1): LiPo charge controller, SOT-23-5. Qty 1. [Microchip](https://www.microchip.com/en-us/product/mcp73831)
- **AP2112K-3.3** (U2): 3.3V 600mA LDO regulator, SOT-23-5. Qty 1. [Diodes Inc](https://www.diodes.com/part/view/AP2112)
- **WS2812B** (D1): Addressable RGB LED, 5050 package. Qty 1. [DigiKey search](https://www.digikey.com/en/products/result?keywords=WS2812B)
- **WS2812B LED strip** (J2): External addressable strip, 15 to 20 LEDs. Qty 1. [Adafruit NeoPixel strip](https://www.adafruit.com/product/1376)
- **Speaker** (LS1): 8 ohm ~1W mini speaker. Qty 1. [Adafruit](https://www.adafruit.com/product/3968)

## Power & Connectors

- **USB-C receptacle** (J1): USB 2.0 16-pin, TYPE-C-31-M-12. Qty 1. [LCSC](https://www.lcsc.com/product-detail/USB-Connectors_Korean-Hroparts-Elec-TYPE-C-31-M-12_C165948.html)
- **JST-EH 2-pin** (BT1): Battery connector, S2B-EH. Qty 1. [DigiKey search](https://www.digikey.com/en/products/result?keywords=S2B-EH)
- **LiPo battery**: 3.7V single cell. Qty 1. [Adafruit 2000mAh](https://www.adafruit.com/product/328)

## Small Parts

- **Tactile switches** (SW2, SW3): Momentary push buttons for action + boot. Qty 2. [Adafruit 20-pack](https://www.adafruit.com/product/367)
- **Resistors** (R1 to R15): 0805 SMD, I2C pull-ups, CC resistors, PROG set, etc. Qty ~10. [DigiKey 0805 resistors](https://www.digikey.com/en/products/filter/chip-resistor-surface-mount/52)
- **Capacitors** (C1 to C5): Decoupling and bulk caps. Qty 5. [DigiKey MLCC](https://www.digikey.com/en/products/filter/ceramic-capacitors/60)

## Notes

- MK2 and MK3 are the same microphone footprint in two positions, populate one only.
- Resistor and capacitor values are in the KiCad schematic; buy a 0805 assortment kit if unsure.
- The bare WS2812B is on-board; J2 is the header for the external strip in the wand shaft.
