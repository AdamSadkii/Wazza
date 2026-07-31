#pragma once

// I2C SDA and SCL. (MPU-6050 & OLED)
#define PIN_I2C_SDA 5
#define PIN_I2C_SCL 4

// WS2812 LEDs.
#define PIN_WS2812_DIN 18
#define NUM_LEDS 16
#define LED_BRIGHTNESS 80

// Buttons.
#define PIN_BTN_BOOT 0
#define PIN_BTN_ACTION 8
#define BTN_ACTIVE_HIGH 0

// I2S pins. (Audio)
#define PIN_I2S_BCLK 26
#define PIN_I2S_LRCLK 21
#define PIN_I2S_AMP_DIN 33
#define PIN_I2S_MIC_DOUT 34

// OLED display.
#define OLED_WIDTH 128
#define OLED_HEIGHT 32
#define OLED_I2C_ADDRESS 0x3C

// Gestures (Motion detection thresholds and timing)
#define PIN_GESTURE_SAMPLE_HZ 100
#define FLICK_THRESHOLD 12.0f
#define FLICK_HARD_THRESHOLD 18.0f
#define SWIPE_THRESHOLD 5.0f
#define SHAKE_THRESHOLD 15.0f
#define CIRCLE_GYRO_MIN 4.0f
#define GESTURE_COOLDOWN_MS 500
#define HOLD_MS 900

// Telemetry / Net
#define TELEMETRY_INTERVAL_MS 100
#define WS_RECONNECT_MS 2000
#define WIFI_CONNECT_TIMEOUT_MS 20000

// Features
#define ENABLE_AUDIO 1
#define ENABLE_OLED 1
#define ENABLE_LEDS 1
#define ENABLE_IMU 1