# Wazza — Bill of Materials

All parts as placed on the Wazza PCB (KiCad refs included).

## Main Components

| Ref | Part | Description | Qty | Link |
|-----|------|-------------|-----|------|
| U9 | ESP32-S3-MINI-1-N8 | Wi-Fi + BLE MCU module, main brain | 1 | [LCSC](https://www.lcsc.com/product-detail/WiFi-Modules_Espressif-Systems-ESP32-S3-MINI-1-N8_C2913206.html) · [Espressif](https://www.espressif.com/en/module/esp32-s3-mini-1-en) |
| U13 | MPU-6050 | 6-axis IMU (accelerometer + gyro), gesture tracking | 1 | [Adafruit](https://www.adafruit.com/product/3886) |
| U14 | SSD1306 OLED 0.91" | 128x32 I2C display | 1 | [Adafruit](https://www.adafruit.com/product/931) |
| U12 | MAX98357A | I2S 3W Class-D audio amplifier | 1 | [Adafruit](https://www.adafruit.com/product/3006) |
| MK2 / MK3 | SPH0645LM4H | I2S MEMS microphone (populate one only) | 1 | [Adafruit](https://www.adafruit.com/product/3421) |
| U1 | MCP73831-2 | LiPo charge controller, SOT-23-5 | 1 | [Microchip](https://www.microchip.com/en-us/product/mcp73831) |
| U2 | AP2112K-3.3 | 3.3V 600mA LDO regulator, SOT-23-5 | 1 | [Diodes Inc](https://www.diodes.com/part/view/AP2112) |
| D1 | WS2812B | Addressable RGB LED, 5050 | 1 | [DigiKey search](https://www.digikey.com/en/products/result?keywords=WS2812B) |
| J2 | WS2812B LED strip | External addressable strip, 15–20 LEDs | 1 | [Adafruit NeoPixel strip](https://www.adafruit.com/product/1376) |
| LS1 | Speaker | 8 ohm ~1W mini speaker | 1 | [Adafruit](https://www.adafruit.com/product/3968) |

## Power & Connectors

| Ref | Part | Description | Qty | Link |
|-----|------|-------------|-----|------|
| J1 | USB-C receptacle | USB 2.0 16-pin (TYPE-C-31-M-12) | 1 | [LCSC](https://www.lcsc.com/product-detail/USB-Connectors_Korean-Hroparts-Elec-TYPE-C-31-M-12_C165948.html) |
| BT1 | JST-EH 2-pin | Battery connector (S2B-EH) | 1 | [DigiKey search](https://www.digikey.com/en/products/result?keywords=S2B-EH) |
| — | LiPo battery | 3.7V single cell | 1 | [Adafruit 2000mAh](https://www.adafruit.com/product/328) |

## Small Parts

| Ref | Part | Description | Qty | Link |
|-----|------|-------------|-----|------|
| SW2, SW3 | Tactile switch | Momentary push button (action + boot) | 2 | [Adafruit 20-pack](https://www.adafruit.com/product/367) |
| R1–R15 | Resistors | 0805 SMD (I2C pull-ups, CC resistors, PROG set, etc.) | ~10 | [DigiKey 0805 resistors](https://www.digikey.com/en/products/filter/chip-resistor-surface-mount/52) |
| C1–C5 | Capacitors | Decoupling / bulk caps | 5 | [DigiKey MLCC](https://www.digikey.com/en/products/filter/ceramic-capacitors/60) |

## Notes

- MK2 and MK3 are the same microphone footprint in two positions — populate **one only**.
- Resistor and capacitor values are in the KiCad schematic; buy a 0805 assortment kit if unsure.
- The bare WS2812B (D1) is on-board; J2 is the header for the external strip in the wand shaft.
