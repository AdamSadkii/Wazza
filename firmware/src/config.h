#pragma once

// I2C
#define PIN_I2C_SDA 21
#define PIN_I2C_SCL 5

// LEDs
#define PIN_WS2812_DIN 16
#define NUM_LEDS 8

// Buttons
#define PIN_BTN_BOOT 0
#define PIN_BTN_ACTION 4

// I2S
#define PIN_I2S_BCLK 15
#define PIN_I2S_LRCLK 26
#define PIN_I2S_AMP_DIN 33
#define PIN_I2S_MIC_DOUT 35

// OLED
#define OLED_WIDTH 128
#define OLED_HEIGHT 32
#define OLED_ADDR 0x3C

// Gestures
#define GESTURE_SAMPLE_HZ 100
#define FLICK_THRESHOLD 12.0f
#define SWIPE_THRESHOLD 5.0f
#define GESTURE_COOLDOWN_MS 400

// Telemetry
#define TELEMETRY_INTERVAL_MS 100
